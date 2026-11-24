import json

from django.contrib.auth.models import User
from django.test import Client, TestCase


class AccountSwitchBaselineTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

        User.objects.create_user(
            username="artista_switch_test",
            password="ClaveSeguraArtista123!",
            is_active=True,
        )

        User.objects.create_user(
            username="productor_switch_test",
            password="ClaveSeguraProductor123!",
            is_active=True,
        )

    def login(self, username, password):
        csrf = self.client.get("/api/csrf/").json()["detail"]

        return self.client.post(
            "/api/auth/login/",
            data=json.dumps({
                "username": username,
                "password": password,
            }),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf,
        )

    def active_username(self):
        response = self.client.get("/api/session/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        return data["username"] if data else None

    def test_login_second_account_without_manual_logout(self):
        first = self.login(
            "artista_switch_test",
            "ClaveSeguraArtista123!",
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(
            self.active_username(),
            "artista_switch_test",
        )

        second = self.login(
            "productor_switch_test",
            "ClaveSeguraProductor123!",
        )
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            self.active_username(),
            "productor_switch_test",
        )

    def test_invalid_password_preserves_current_account(self):
        first = self.login(
            "artista_switch_test",
            "ClaveSeguraArtista123!",
        )
        self.assertEqual(first.status_code, 200)

        failed = self.login(
            "productor_switch_test",
            "ClaveIncorrecta",
        )
        self.assertEqual(failed.status_code, 401)

        self.assertEqual(
            self.active_username(),
            "artista_switch_test",
        )
