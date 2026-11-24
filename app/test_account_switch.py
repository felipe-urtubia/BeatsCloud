import json

from django.contrib.auth.models import User
from django.test import Client, TestCase


class AccountSwitchTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

        self.artist = User.objects.create_user(
            username="switch_artista",
            password="ClaveArtista123!",
            is_active=True,
        )

        self.producer = User.objects.create_user(
            username="switch_productor",
            password="ClaveProductor123!",
            is_active=True,
        )

    def post_json(self, path, data, csrf=True):
        headers = {}

        if csrf:
            response = self.client.get("/api/csrf/")
            headers["HTTP_X_CSRFTOKEN"] = response.json()["detail"]

        return self.client.post(
            path,
            data=json.dumps(data),
            content_type="application/json",
            **headers,
        )

    def login_artist(self):
        response = self.post_json(
            "/api/auth/login/",
            {
                "username": "switch_artista",
                "password": "ClaveArtista123!",
            },
        )
        self.assertEqual(response.status_code, 200)

    def authorize_producer(self):
        return self.post_json(
            "/api/auth/accounts/add/",
            {
                "username": "switch_productor",
                "password": "ClaveProductor123!",
            },
        )

    def active_username(self):
        response = self.client.get("/api/session/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        return data["username"] if data else None

    def test_account_list_requires_login(self):
        response = self.client.get("/api/auth/accounts/")
        self.assertEqual(response.status_code, 401)

    def test_add_account_and_switch_both_directions(self):
        self.login_artist()

        response = self.authorize_producer()
        self.assertEqual(response.status_code, 200)

        # Agregar una cuenta no cambia la identidad activa.
        self.assertEqual(
            self.active_username(),
            "switch_artista",
        )

        accounts = self.client.get("/api/auth/accounts/")
        self.assertEqual(accounts.status_code, 200)

        account_ids = {
            account["id"]
            for account in accounts.json()["accounts"]
        }

        self.assertIn(self.artist.id, account_ids)
        self.assertIn(self.producer.id, account_ids)

        # Cambiar al productor sin volver a enviar su clave.
        response = self.post_json(
            "/api/auth/accounts/switch/",
            {"user_id": self.producer.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.active_username(),
            "switch_productor",
        )

        # Regresar al artista sin introducir otra contraseña.
        response = self.post_json(
            "/api/auth/accounts/switch/",
            {"user_id": self.artist.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.active_username(),
            "switch_artista",
        )

    def test_wrong_password_does_not_authorize_account(self):
        self.login_artist()

        response = self.post_json(
            "/api/auth/accounts/add/",
            {
                "username": "switch_productor",
                "password": "ClaveIncorrecta",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            self.active_username(),
            "switch_artista",
        )

        response = self.post_json(
            "/api/auth/accounts/switch/",
            {"user_id": self.producer.id},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.active_username(),
            "switch_artista",
        )

    def test_switch_requires_prior_authorization(self):
        self.login_artist()

        response = self.post_json(
            "/api/auth/accounts/switch/",
            {"user_id": self.producer.id},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.active_username(),
            "switch_artista",
        )

    def test_logout_revokes_added_accounts(self):
        self.login_artist()

        response = self.authorize_producer()
        self.assertEqual(response.status_code, 200)

        response = self.post_json(
            "/api/auth/logout/",
            {},
        )
        self.assertEqual(response.status_code, 200)

        # Una nueva sesión no hereda cuentas autorizadas.
        self.login_artist()

        response = self.post_json(
            "/api/auth/accounts/switch/",
            {"user_id": self.producer.id},
        )

        self.assertEqual(response.status_code, 403)

    def test_add_account_requires_csrf(self):
        self.login_artist()

        response = self.post_json(
            "/api/auth/accounts/add/",
            {
                "username": "switch_productor",
                "password": "ClaveProductor123!",
            },
            csrf=False,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.active_username(),
            "switch_artista",
        )

    def test_password_change_revokes_account_authorization(self):
        self.login_artist()

        self.assertEqual(
            self.authorize_producer().status_code,
            200,
        )

        self.producer.set_password("NuevaClaveProductor123!")
        self.producer.save()

        response = self.post_json(
            "/api/auth/accounts/switch/",
            {"user_id": self.producer.id},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.active_username(),
            "switch_artista",
        )
