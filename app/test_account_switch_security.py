import json

from django.contrib.auth.models import User
from django.test import Client, TestCase


class AccountSwitchSecurityTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

        self.artist = User.objects.create_user(
            username="security_artista",
            password="ClaveArtista123!",
            is_active=True,
        )
        self.producer = User.objects.create_user(
            username="security_productor",
            password="ClaveProductor123!",
            is_active=True,
        )
        self.third = User.objects.create_user(
            username="security_tercero",
            password="ClaveTercero123!",
            is_active=True,
        )

    def post(self, path, data, client=None, with_csrf=True):
        client = client or self.client
        headers = {}

        if with_csrf:
            csrf = client.get("/api/csrf/").json()["detail"]
            headers["HTTP_X_CSRFTOKEN"] = csrf

        return client.post(
            path,
            data=json.dumps(data),
            content_type="application/json",
            **headers,
        )

    def login(self, username, password, client=None):
        response = self.post(
            "/api/auth/login/",
            {"username": username, "password": password},
            client=client,
        )
        self.assertEqual(response.status_code, 200)

    def prepare_accounts(self):
        self.login("security_artista", "ClaveArtista123!")

        response = self.post(
            "/api/auth/accounts/add/",
            {
                "username": "security_productor",
                "password": "ClaveProductor123!",
            },
        )
        self.assertEqual(response.status_code, 200)

    def active_username(self):
        data = self.client.get("/api/session/").json()
        return data["username"] if data else None

    def test_second_browser_cannot_use_authorized_account(self):
        self.prepare_accounts()

        other = Client(enforce_csrf_checks=True)

        self.login(
            "security_artista",
            "ClaveArtista123!",
            client=other,
        )

        response = self.post(
            "/api/auth/accounts/switch/",
            {"user_id": self.producer.id},
            client=other,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            other.get("/api/session/").json()["username"],
            "security_artista",
        )

    def test_switch_requires_csrf(self):
        self.prepare_accounts()

        response = self.post(
            "/api/auth/accounts/switch/",
            {"user_id": self.producer.id},
            with_csrf=False,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.active_username(),
            "security_artista",
        )

    def test_disabled_account_cannot_be_selected(self):
        self.prepare_accounts()

        self.producer.is_active = False
        self.producer.save()

        response = self.client.get("/api/auth/accounts/")
        ids = {
            account["id"]
            for account in response.json()["accounts"]
        }

        self.assertNotIn(self.producer.id, ids)

        response = self.post(
            "/api/auth/accounts/switch/",
            {"user_id": self.producer.id},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.active_username(),
            "security_artista",
        )

    def test_password_change_removes_authorization(self):
        self.prepare_accounts()

        self.producer.set_password("NuevaClaveProductor123!")
        self.producer.save()

        response = self.client.get("/api/auth/accounts/")
        ids = {
            account["id"]
            for account in response.json()["accounts"]
        }

        self.assertNotIn(self.producer.id, ids)

        response = self.post(
            "/api/auth/accounts/switch/",
            {"user_id": self.producer.id},
        )

        self.assertEqual(response.status_code, 403)

    def test_normal_login_revokes_previous_authorizations(self):
        self.prepare_accounts()

        self.login(
            "security_tercero",
            "ClaveTercero123!",
        )

        response = self.client.get("/api/auth/accounts/")
        ids = {
            account["id"]
            for account in response.json()["accounts"]
        }

        self.assertEqual(ids, {self.third.id})

        response = self.post(
            "/api/auth/accounts/switch/",
            {"user_id": self.producer.id},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.active_username(),
            "security_tercero",
        )

    def test_invalid_account_identifier_is_rejected(self):
        self.prepare_accounts()

        for invalid_id in ["2", True, None, -1]:
            response = self.post(
                "/api/auth/accounts/switch/",
                {"user_id": invalid_id},
            )

            expected = 400 if type(invalid_id) is not int else 403

            self.assertEqual(
                response.status_code,
                expected,
            )

        self.assertEqual(
            self.active_username(),
            "security_artista",
        )

    def test_account_list_exposes_no_credentials(self):
        self.prepare_accounts()

        response = self.client.get("/api/auth/accounts/")
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data["accounts"]), 2)

        for account in data["accounts"]:
            self.assertEqual(
                set(account.keys()),
                {"id", "username", "is_current"},
            )

        serialized = json.dumps(data)

        self.assertNotIn("ClaveArtista123!", serialized)
        self.assertNotIn("ClaveProductor123!", serialized)
        self.assertNotIn("auth_hash", serialized)

    def test_csrf_is_rotated_after_account_switch(self):
        self.prepare_accounts()

        old_csrf = self.client.get(
            "/api/csrf/"
        ).json()["detail"]

        response = self.client.post(
            "/api/auth/accounts/switch/",
            data=json.dumps({"user_id": self.producer.id}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=old_csrf,
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            self.active_username(),
            "security_productor",
        )

        # El token anterior no debe seguir autorizando solicitudes.
        response = self.client.post(
            "/api/auth/accounts/switch/",
            data=json.dumps({"user_id": self.artist.id}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=old_csrf,
        )
        self.assertEqual(response.status_code, 403)

        # Un token CSRF renovado permite volver al artista.
        response = self.post(
            "/api/auth/accounts/switch/",
            {"user_id": self.artist.id},
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            self.active_username(),
            "security_artista",
        )

    def test_normal_relogin_same_user_revokes_added_accounts(self):
        self.prepare_accounts()

        # Iniciar sesion de nuevo con el mismo artista.
        self.login(
            "security_artista",
            "ClaveArtista123!",
        )

        response = self.client.get("/api/auth/accounts/")
        self.assertEqual(response.status_code, 200)

        ids = {
            account["id"]
            for account in response.json()["accounts"]
        }

        self.assertEqual(ids, {self.artist.id})

        # Ya no puede utilizar la autorizacion anterior.
        response = self.post(
            "/api/auth/accounts/switch/",
            {"user_id": self.producer.id},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.active_username(),
            "security_artista",
        )

    def test_switch_response_identifies_new_active_account(self):
        self.prepare_accounts()

        response = self.post(
            "/api/auth/accounts/switch/",
            {"user_id": self.producer.id},
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            data["active_user_id"],
            self.producer.id,
        )

        current_ids = {
            account["id"]
            for account in data["accounts"]
            if account["is_current"]
        }

        self.assertEqual(
            current_ids,
            {self.producer.id},
        )

        self.assertEqual(
            self.active_username(),
            "security_productor",
        )
