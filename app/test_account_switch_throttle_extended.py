"""Pruebas extendidas de seguridad para autenticacion."""

import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from app.models import AuthAttemptThrottle


class AuthenticationThrottleExtendedTests(TestCase):

    def setUp(self):
        User.objects.create_user(
            username="extra_artista",
            password="ClaveArtista123!",
        )
        User.objects.create_user(
            username="extra_productor",
            password="ClaveProductor123!",
        )
        self.client = Client(
            enforce_csrf_checks=True,
            REMOTE_ADDR="192.0.2.10",
        )

    def send(self, path, username, password, **headers):
        csrf = self.client.get("/api/csrf/")
        self.assertEqual(csrf.status_code, 200)

        return self.client.post(
            path,
            data=json.dumps({
                "username": username,
                "password": password,
            }),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf.json()["detail"],
            **headers,
        )

    def login(self, username, password, **headers):
        return self.send(
            "/api/auth/login/",
            username,
            password,
            **headers,
        )

    def test_window_expiry_allows_new_attempt(self):
        for _ in range(5):
            response = self.login(
                "extra_productor", "Incorrecta"
            )
            self.assertEqual(response.status_code, 401)

        blocked = self.login(
            "extra_productor", "Incorrecta"
        )
        self.assertEqual(blocked.status_code, 429)

        entry = AuthAttemptThrottle.objects.get()
        entry.reset_at = timezone.now() - timedelta(seconds=1)
        entry.save(update_fields=["reset_at"])

        response = self.login(
            "extra_productor", "Incorrecta"
        )
        self.assertEqual(response.status_code, 401)

        entry.refresh_from_db()
        self.assertEqual(entry.attempts, 1)
        self.assertGreater(entry.reset_at, timezone.now())

    def test_successful_login_clears_counter(self):
        for _ in range(3):
            response = self.login(
                "extra_productor", "Incorrecta"
            )
            self.assertEqual(response.status_code, 401)

        success = self.login(
            "extra_productor", "ClaveProductor123!"
        )
        self.assertEqual(success.status_code, 200)
        self.assertEqual(
            AuthAttemptThrottle.objects.count(), 0
        )

        for _ in range(5):
            response = self.login(
                "extra_productor", "Incorrecta"
            )
            self.assertEqual(response.status_code, 401)

        blocked = self.login(
            "extra_productor", "Incorrecta"
        )
        self.assertEqual(blocked.status_code, 429)

    def test_forwarded_for_cannot_bypass_limit(self):
        for index in range(5):
            response = self.login(
                "extra_productor",
                "Incorrecta",
                HTTP_X_FORWARDED_FOR=f"198.51.100.{index + 1}",
            )
            self.assertEqual(response.status_code, 401)

        blocked = self.login(
            "extra_productor",
            "Incorrecta",
            HTTP_X_FORWARDED_FOR="203.0.113.99",
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("Retry-After", blocked)

    def test_login_and_account_add_have_separate_limits(self):
        # Tres intentos fallidos de login normal.
        for _ in range(3):
            response = self.login(
                "extra_productor", "Incorrecta"
            )
            self.assertEqual(response.status_code, 401)

        # Iniciar sesion con otra cuenta.
        success = self.login(
            "extra_artista", "ClaveArtista123!"
        )
        self.assertEqual(success.status_code, 200)

        # El selector tiene su propio limite.
        for _ in range(5):
            response = self.send(
                "/api/auth/accounts/add/",
                "extra_productor",
                "Incorrecta",
            )
            self.assertEqual(response.status_code, 401)

        blocked_add = self.send(
            "/api/auth/accounts/add/",
            "extra_productor",
            "Incorrecta",
        )
        self.assertEqual(blocked_add.status_code, 429)
        self.assertIn("Retry-After", blocked_add)

        # El limite del login sigue siendo independiente.
        for _ in range(2):
            response = self.login(
                "extra_productor", "Incorrecta"
            )
            self.assertEqual(response.status_code, 401)

        blocked_login = self.login(
            "extra_productor", "Incorrecta"
        )
        self.assertEqual(blocked_login.status_code, 429)
        self.assertIn("Retry-After", blocked_login)

        # Los intentos fallidos no cambian la cuenta activa.
        active = self.client.get("/api/session/").json()
        self.assertEqual(active["username"], "extra_artista")
