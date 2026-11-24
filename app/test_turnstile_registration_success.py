"""Registro completo con Turnstile y base temporal."""

import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from .models import Usuario
from .views import RegistroUsuarioForm, registro


class TurnstileCompleteRegistrationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        env = patch.dict(
            os.environ,
            {"TURNSTILE_REGISTRATION_ENABLED": "1"},
        )
        env.start()
        self.addCleanup(env.stop)

        email = patch(
            "django.core.mail.EmailMultiAlternatives.send",
            return_value=1,
        )
        self.send_email = email.start()
        self.addCleanup(email.stop)

    def form_data(self, suffix):
        return {
            "username": f"ts_prueba_{suffix}",
            "email": f"ts_prueba_{suffix}@example.com",
            "first_name": "Prueba",
            "last_name": "Automatizada",
            "nombre_artistico": "Artista QA",
            "tipo_usu": "1",
            "password1": "BeatCloud-Test-2026!Seguro",
            "password2": "BeatCloud-Test-2026!Seguro",
        }

    def assert_valid_form(self, data):
        form = RegistroUsuarioForm(data=data)

        self.assertTrue(
            form.is_valid(),
            f"Formulario invalido: {form.errors.as_json()}",
        )

    def test_api_creates_inactive_user_with_valid_token(self):
        data = self.form_data("api")
        self.assert_valid_form(data)

        data["cf-turnstile-response"] = "token-api-valido"

        with patch(
            "app.turnstile_verification.verify_registration_turnstile",
            return_value=True,
        ) as verify:
            response = self.client.post(
                reverse("api_registro"),
                data=data,
            )

        self.assertEqual(response.status_code, 201)
        verify.assert_called_once_with("token-api-valido")

        user = get_user_model().objects.get(
            username=data["username"]
        )

        self.assertFalse(user.is_active)
        self.assertTrue(Usuario.objects.filter(user=user).exists())
        self.send_email.assert_called_once()

    def test_html_creates_inactive_user_with_valid_token(self):
        data = self.form_data("html")
        self.assert_valid_form(data)

        data["cf-turnstile-response"] = "token-html-valido"

        request = self.factory.post("/registro/", data=data)
        request.user = AnonymousUser()

        with patch(
            "app.turnstile_verification.verify_registration_turnstile",
            return_value=True,
        ) as verify:
            response = registro(request)

        self.assertEqual(response.status_code, 200)
        verify.assert_called_once_with("token-html-valido")

        user = get_user_model().objects.get(
            username=data["username"]
        )

        self.assertFalse(user.is_active)
        self.assertTrue(Usuario.objects.filter(user=user).exists())
        self.send_email.assert_called_once()

    def test_api_rejects_complete_form_without_token(self):
        data = self.form_data("rechazo_api")
        self.assert_valid_form(data)

        with patch(
            "app.turnstile_verification.verify_registration_turnstile",
            return_value=False,
        ) as verify:
            response = self.client.post(
                reverse("api_registro"),
                data=data,
            )

        self.assertEqual(response.status_code, 403)
        verify.assert_called_once_with("")
        self.assertFalse(
            get_user_model().objects.filter(
                username=data["username"]
            ).exists()
        )
        self.send_email.assert_not_called()

    def test_html_rejects_complete_form_without_token(self):
        data = self.form_data("rechazo_html")
        self.assert_valid_form(data)

        request = self.factory.post("/registro/", data=data)
        request.user = AnonymousUser()

        with patch(
            "app.turnstile_verification.verify_registration_turnstile",
            return_value=False,
        ) as verify:
            response = registro(request)

        self.assertEqual(response.status_code, 403)
        verify.assert_called_once_with("")
        self.assertFalse(
            get_user_model().objects.filter(
                username=data["username"]
            ).exists()
        )
        self.send_email.assert_not_called()
