"""Pruebas RED de proteccion frente a intentos repetidos."""

import json

from django.contrib.auth.models import User
from django.test import Client, TestCase


class AuthenticationThrottleTests(TestCase):
    def setUp(self):
        self.artist = User.objects.create_user(
            username="throttle_artista",
            password="ClaveArtista123!",
        )

        self.producer = User.objects.create_user(
            username="throttle_productor",
            password="ClaveProductor123!",
        )

        self.client = Client(
            enforce_csrf_checks=True,
            REMOTE_ADDR="192.0.2.10",
        )

    def send(self, client, path, username, password):
        csrf_response = client.get("/api/csrf/")
        self.assertEqual(csrf_response.status_code, 200)

        return client.post(
            path,
            data=json.dumps({
                "username": username,
                "password": password,
            }),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_response.json()["detail"],
        )

    def test_repeated_login_failures_are_limited(self):
        for _ in range(5):
            response = self.send(
                self.client,
                "/api/auth/login/",
                "throttle_productor",
                "ClaveIncorrecta",
            )
            self.assertEqual(response.status_code, 401)

        blocked = self.send(
            self.client,
            "/api/auth/login/",
            "throttle_productor",
            "ClaveIncorrecta",
        )

        self.assertEqual(blocked.status_code, 429)
        self.assertIn("Retry-After", blocked)
        self.assertIsNone(
            self.client.get("/api/session/").json()
        )

    def test_repeated_account_add_failures_are_limited(self):
        response = self.send(
            self.client,
            "/api/auth/login/",
            "throttle_artista",
            "ClaveArtista123!",
        )
        self.assertEqual(response.status_code, 200)

        for _ in range(5):
            response = self.send(
                self.client,
                "/api/auth/accounts/add/",
                "throttle_productor",
                "ClaveIncorrecta",
            )
            self.assertEqual(response.status_code, 401)

        blocked = self.send(
            self.client,
            "/api/auth/accounts/add/",
            "throttle_productor",
            "ClaveIncorrecta",
        )

        self.assertEqual(blocked.status_code, 429)
        self.assertIn("Retry-After", blocked)

        active = self.client.get("/api/session/").json()
        self.assertEqual(
            active["username"],
            "throttle_artista",
        )

    def test_limit_does_not_block_other_ip(self):
        for _ in range(5):
            response = self.send(
                self.client,
                "/api/auth/login/",
                "throttle_productor",
                "ClaveIncorrecta",
            )
            self.assertEqual(response.status_code, 401)

        another_browser = Client(
            enforce_csrf_checks=True,
            REMOTE_ADDR="198.51.100.20",
        )

        response = self.send(
            another_browser,
            "/api/auth/login/",
            "throttle_productor",
            "ClaveProductor123!",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            another_browser.get("/api/session/").json()["username"],
            "throttle_productor",
        )
