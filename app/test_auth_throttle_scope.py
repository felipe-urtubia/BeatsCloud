from types import SimpleNamespace

from django.test import RequestFactory, TestCase

from .auth_throttle import (
    _bucket_key,
    reserve_attempt,
    clear_attempts,
)
from .models import AuthAttemptThrottle


class AuthThrottleActorScopeTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def make_request(
        self,
        actor_id,
        ip="192.0.2.10",
        forwarded=None,
    ):
        extra = {"REMOTE_ADDR": ip}

        if forwarded is not None:
            extra["HTTP_X_FORWARDED_FOR"] = forwarded

        request = self.factory.post(
            "/api/auth/accounts/add/",
            **extra,
        )

        request.user = SimpleNamespace(
            is_authenticated=actor_id is not None,
            pk=actor_id,
        )
        return request

    def test_different_actors_have_different_buckets(self):
        first = self.make_request(101)
        second = self.make_request(202)

        self.assertNotEqual(
            _bucket_key(first, "destino", actor_scoped=True),
            _bucket_key(second, "destino", actor_scoped=True),
        )

    def test_same_actor_keeps_bucket_across_ips(self):
        first = self.make_request(101, "192.0.2.10")
        second = self.make_request(101, "198.51.100.20")

        self.assertEqual(
            _bucket_key(first, "Destino", actor_scoped=True),
            _bucket_key(second, "destino", actor_scoped=True),
        )

    def test_forwarded_header_does_not_change_actor_bucket(self):
        first = self.make_request(
            101,
            forwarded="203.0.113.10",
        )
        second = self.make_request(
            101,
            forwarded="203.0.113.99",
        )

        self.assertEqual(
            _bucket_key(first, "destino", actor_scoped=True),
            _bucket_key(second, "destino", actor_scoped=True),
        )

    def test_anonymous_actor_is_rejected(self):
        request = self.make_request(None)

        with self.assertRaises(ValueError):
            _bucket_key(request, "destino", actor_scoped=True)

    def test_normal_login_still_uses_remote_address(self):
        first = self.make_request(
            None,
            ip="192.0.2.10",
            forwarded="203.0.113.99",
        )
        second = self.make_request(
            None,
            ip="192.0.2.10",
            forwarded="198.51.100.99",
        )
        third = self.make_request(
            None,
            ip="198.51.100.20",
        )

        self.assertEqual(
            _bucket_key(first, "destino"),
            _bucket_key(second, "destino"),
        )
        self.assertNotEqual(
            _bucket_key(first, "destino"),
            _bucket_key(third, "destino"),
        )

    def test_sixth_attempt_blocks_only_same_actor(self):
        first = self.make_request(101)
        second = self.make_request(202)

        for _ in range(5):
            self.assertIsNone(
                reserve_attempt(
                    first,
                    "destino",
                    actor_scoped=True,
                )
            )

        blocked = reserve_attempt(
            first,
            "destino",
            actor_scoped=True,
        )

        self.assertEqual(blocked.status_code, 429)
        self.assertIn("Retry-After", blocked)

        self.assertIsNone(
            reserve_attempt(
                second,
                "destino",
                actor_scoped=True,
            )
        )

        self.assertEqual(
            AuthAttemptThrottle.objects.count(),
            2,
        )

    def test_changing_ip_does_not_reset_actor_limit(self):
        first = self.make_request(
            101,
            ip="192.0.2.10",
        )
        second = self.make_request(
            101,
            ip="198.51.100.20",
        )

        for _ in range(5):
            self.assertIsNone(
                reserve_attempt(
                    first,
                    "destino",
                    actor_scoped=True,
                )
            )

        blocked = reserve_attempt(
            second,
            "destino",
            actor_scoped=True,
        )

        self.assertEqual(blocked.status_code, 429)

    def test_clear_attempts_only_clears_current_actor(self):
        first = self.make_request(101)
        second = self.make_request(202)

        reserve_attempt(first, "destino", actor_scoped=True)
        reserve_attempt(second, "destino", actor_scoped=True)

        clear_attempts(
            first,
            "destino",
            actor_scoped=True,
        )

        self.assertFalse(
            AuthAttemptThrottle.objects.filter(
                key=_bucket_key(
                    first,
                    "destino",
                    actor_scoped=True,
                )
            ).exists()
        )

        self.assertTrue(
            AuthAttemptThrottle.objects.filter(
                key=_bucket_key(
                    second,
                    "destino",
                    actor_scoped=True,
                )
            ).exists()
        )
