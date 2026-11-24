"""Pruebas del comando de limpieza de autenticacion."""

from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from app.models import AuthAttemptThrottle


class AuthThrottleCleanupTests(TestCase):

    def setUp(self):
        now = timezone.now()

        AuthAttemptThrottle.objects.create(
            key="a" * 64,
            attempts=5,
            reset_at=now - timedelta(days=3),
        )

        AuthAttemptThrottle.objects.create(
            key="b" * 64,
            attempts=2,
            reset_at=now - timedelta(hours=2),
        )

        AuthAttemptThrottle.objects.create(
            key="c" * 64,
            attempts=1,
            reset_at=now + timedelta(minutes=10),
        )

    def test_cleanup_removes_only_old_records(self):
        call_command(
            "cleanup_auth_throttle",
            retention_hours=24,
            stdout=StringIO(),
        )

        keys = set(
            AuthAttemptThrottle.objects.values_list(
                "key", flat=True
            )
        )

        self.assertEqual(keys, {"b" * 64, "c" * 64})

    def test_dry_run_does_not_delete(self):
        call_command(
            "cleanup_auth_throttle",
            dry_run=True,
            stdout=StringIO(),
        )

        self.assertEqual(
            AuthAttemptThrottle.objects.count(), 3
        )

    def test_invalid_retention_is_rejected(self):
        with self.assertRaises(CommandError):
            call_command(
                "cleanup_auth_throttle",
                retention_hours=0,
                stdout=StringIO(),
            )

        self.assertEqual(
            AuthAttemptThrottle.objects.count(), 3
        )
