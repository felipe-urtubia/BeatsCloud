"""Pruebas de integracion Turnstile para ambos registros."""

import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from . import views


class TurnstileRegistrationIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.initial_users = get_user_model().objects.count()

        config = patch.dict(
            os.environ,
            {"TURNSTILE_REGISTRATION_ENABLED": "1"},
        )
        config.start()
        self.addCleanup(config.stop)

        email_patch = patch(
            "django.core.mail.EmailMultiAlternatives.send"
        )
        self.email_send = email_patch.start()
        self.addCleanup(email_patch.stop)

    def assert_no_registration_side_effects(self):
        self.assertEqual(
            get_user_model().objects.count(),
            self.initial_users,
        )
        self.email_send.assert_not_called()

    def call_api(self, token=None, accepted=False):
        data = {}

        if token is not None:
            data["cf-turnstile-response"] = token

        with patch(
            "app.turnstile_verification.verify_registration_turnstile",
            return_value=accepted,
        ) as verifier:
            response = self.client.post(
                reverse("api_registro"),
                data=data,
            )

        return response, verifier

    def call_html(self, token=None, accepted=False):
        data = {}

        if token is not None:
            data["cf-turnstile-response"] = token

        request = self.factory.post(
            "/registro/",
            data=data,
        )
        request.user = AnonymousUser()

        with patch(
            "app.turnstile_verification.verify_registration_turnstile",
            return_value=accepted,
        ) as verifier:
            response = views.registro(request)

        return response, verifier

    def test_api_rejects_missing_token(self):
        response, verifier = self.call_api()

        self.assertEqual(response.status_code, 403)
        verifier.assert_called_once_with("")
        self.assert_no_registration_side_effects()

    def test_api_rejects_invalid_token(self):
        response, verifier = self.call_api("invalid-token")

        self.assertEqual(response.status_code, 403)
        verifier.assert_called_once_with("invalid-token")
        self.assert_no_registration_side_effects()

    def test_api_valid_token_reaches_form_validation(self):
        response, verifier = self.call_api(
            "valid-token",
            accepted=True,
        )

        # Faltan los campos obligatorios del formulario.
        self.assertEqual(response.status_code, 400)
        verifier.assert_called_once_with("valid-token")
        self.assert_no_registration_side_effects()

    def test_html_rejects_missing_token(self):
        response, verifier = self.call_html()

        self.assertEqual(response.status_code, 403)
        verifier.assert_called_once_with("")
        self.assert_no_registration_side_effects()

    def test_html_rejects_invalid_token(self):
        response, verifier = self.call_html("invalid-token")

        self.assertEqual(response.status_code, 403)
        verifier.assert_called_once_with("invalid-token")
        self.assert_no_registration_side_effects()

    def test_html_valid_token_reaches_form_validation(self):
        response, verifier = self.call_html(
            "valid-token",
            accepted=True,
        )

        # Un formulario HTML invalido vuelve a renderizarse.
        self.assertEqual(response.status_code, 200)
        verifier.assert_called_once_with("valid-token")
        self.assert_no_registration_side_effects()

    def test_api_disabled_does_not_require_turnstile(self):
        with patch.dict(
            os.environ,
            {"TURNSTILE_REGISTRATION_ENABLED": "0"},
        ):
            response, verifier = self.call_api()

        self.assertEqual(response.status_code, 400)
        verifier.assert_not_called()
        self.assert_no_registration_side_effects()

    def test_html_disabled_does_not_require_turnstile(self):
        with patch.dict(
            os.environ,
            {"TURNSTILE_REGISTRATION_ENABLED": "0"},
        ):
            response, verifier = self.call_html()

        self.assertEqual(response.status_code, 200)
        verifier.assert_not_called()
        self.assert_no_registration_side_effects()
