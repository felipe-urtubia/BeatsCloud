"""Pruebas aisladas del validador Turnstile."""

import json
import os
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from .turnstile_verification import verify_registration_turnstile


class TurnstileVerificationTests(SimpleTestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {
            "TURNSTILE_SECRET_KEY": "secret-test-only",
            "TURNSTILE_ALLOWED_HOSTNAMES": "",
        })
        environment.start()
        self.addCleanup(environment.stop)

    def mock_response(self, value):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = (
            json.dumps(value).encode("utf-8")
        )
        return response

    def test_valid_token(self):
        with patch(
            "app.turnstile_verification.urlopen",
            return_value=self.mock_response({
                "success": True,
                "hostname": "example.com",
            }),
        ):
            self.assertTrue(
                verify_registration_turnstile("valid-token")
            )

    def test_invalid_token(self):
        with patch(
            "app.turnstile_verification.urlopen",
            return_value=self.mock_response({
                "success": False,
                "error-codes": ["invalid-input-response"],
            }),
        ):
            self.assertFalse(
                verify_registration_turnstile("bad-token")
            )

    def test_missing_token(self):
        with patch(
            "app.turnstile_verification.urlopen"
        ) as network:
            self.assertFalse(verify_registration_turnstile(""))
            network.assert_not_called()

    def test_oversized_token(self):
        with patch(
            "app.turnstile_verification.urlopen"
        ) as network:
            self.assertFalse(
                verify_registration_turnstile("x" * 2049)
            )
            network.assert_not_called()

    def test_missing_secret_fails_closed(self):
        with patch.dict(
            os.environ,
            {"TURNSTILE_SECRET_KEY": ""},
        ):
            with patch(
                "app.turnstile_verification.urlopen"
            ) as network:
                self.assertFalse(
                    verify_registration_turnstile("token")
                )
                network.assert_not_called()

    def test_network_failure_fails_closed(self):
        with patch(
            "app.turnstile_verification.urlopen",
            side_effect=OSError("network unavailable"),
        ):
            self.assertFalse(
                verify_registration_turnstile("token")
            )

    def test_unexpected_response_fails_closed(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = (
            b"not-json"
        )

        with patch(
            "app.turnstile_verification.urlopen",
            return_value=response,
        ):
            self.assertFalse(
                verify_registration_turnstile("token")
            )

    def test_wrong_hostname_is_rejected(self):
        with patch.dict(os.environ, {
            "TURNSTILE_ALLOWED_HOSTNAMES": "beatscloud.com",
        }):
            with patch(
                "app.turnstile_verification.urlopen",
                return_value=self.mock_response({
                    "success": True,
                    "hostname": "malicious.example",
                }),
            ):
                self.assertFalse(
                    verify_registration_turnstile("token")
                )

    def test_allowed_hostname_is_accepted(self):
        with patch.dict(os.environ, {
            "TURNSTILE_ALLOWED_HOSTNAMES": "beatscloud.com",
        }):
            with patch(
                "app.turnstile_verification.urlopen",
                return_value=self.mock_response({
                    "success": True,
                    "hostname": "beatscloud.com",
                }),
            ):
                self.assertTrue(
                    verify_registration_turnstile("token")
                )
