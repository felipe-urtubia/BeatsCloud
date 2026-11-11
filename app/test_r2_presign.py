"""R2 URL-issuance tests: no network and no real cloud credentials."""
import json
import os
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import signing
from django.test import TestCase

from app.models import Usuario
from app.r2_presign import (
    TOKEN_SALT,
    MAX_BYTES,
    r2_configuration,
    r2_uploads_enabled,
)


class StubR2:
    def generate_presigned_url(self, operation, Params, ExpiresIn, HttpMethod):
        assert operation == "put_object" and HttpMethod == "PUT"
        assert Params["Key"].startswith("pending/")
        assert ExpiresIn == 3600
        return "https://r2.example.invalid/signed-put"


class R2ConfigurationTests(TestCase):

    def test_credenciales_disponibles_con_subidas_desactivadas(self):
        esperado = {
            "R2_ACCOUNT_ID": "a" * 32,
            "R2_BUCKET_NAME": "test-bucket",
            "R2_ACCESS_KEY_ID": "test-key",
            "R2_SECRET_ACCESS_KEY": "test-secret",
        }
        entorno = {
            **esperado,
            "R2_UPLOADS_ENABLED": "false",
        }
        with (
            patch("app.r2_presign._load_r2_credentials_from_dotenv"),
            patch.dict(os.environ, entorno),
        ):
            self.assertEqual(r2_configuration(), esperado)

    def test_solo_true_activa_nuevas_subidas(self):
        for valor in ("", "0", "false", "yes", "1"):
            with self.subTest(valor=valor):
                with patch.dict(os.environ, {"R2_UPLOADS_ENABLED": valor}):
                    self.assertFalse(r2_uploads_enabled())

        with patch.dict(os.environ, {"R2_UPLOADS_ENABLED": " true "}):
            self.assertTrue(r2_uploads_enabled())


class R2PresignTests(TestCase):
    def setUp(self):
        self.producer = User.objects.create_user(username="r2producer", password="sample-pass")
        Usuario.objects.create(user=self.producer, tipo_usu=Usuario.PRODUCTOR)
        self.artist = User.objects.create_user(username="r2artist", password="sample-pass")
        Usuario.objects.create(user=self.artist, tipo_usu=Usuario.ARTISTA)
        self.url = "/api/r2/presign/"
        self.payload = {"kind": "track", "filename": "beat.wav", "size": 500000, "content_type": "audio/wav"}

    def post(self, payload=None):
        return self.client.post(self.url, data=json.dumps(self.payload if payload is None else payload), content_type="application/json")

    def test_unauthenticated_and_wrong_role(self):
        self.assertEqual(self.post().status_code, 401)
        self.client.force_login(self.artist)
        self.assertEqual(self.post().status_code, 403)

    def test_wrong_method(self):
        self.client.force_login(self.producer)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_invalid_types_are_rejected(self):
        self.client.force_login(self.producer)

        with patch.dict(os.environ, {"R2_UPLOADS_ENABLED": "true"}):
            for change in (
                {"kind": "unknown"}, {"filename": "../beat.wav"},
                {"filename": "evil.exe"}, {"content_type": "application/octet-stream"},
                {"size": -10}, {"size": True}, {"size": MAX_BYTES["track"] + 1},
            ):
                with self.subTest(change=change):
                    self.assertEqual(
                        self.post({**self.payload, **change}).status_code,
                        400,
                    )

    def test_not_configured_fails_closed(self):
        self.client.force_login(self.producer)
        with patch.dict(os.environ, {"R2_UPLOADS_ENABLED": "0"}):
            self.assertEqual(self.post().status_code, 503)

    def test_valid_track_and_owner_bound_token(self):
        self.client.force_login(self.producer)
        env = {
            "R2_UPLOADS_ENABLED": "true",
            "R2_ACCOUNT_ID": "a" * 32,
            "R2_BUCKET_NAME": "test-bucket",
            "R2_ACCESS_KEY_ID": "test-key",
            "R2_SECRET_ACCESS_KEY": "test-secret",
        }
        with patch.dict(os.environ, env), patch("app.r2_presign.r2_client", return_value=StubR2()):
            response = self.post()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["method"], "PUT")
        self.assertEqual(response.json()["headers"], {"Content-Type": "audio/wav"})
        token = signing.loads(response.json()["upload_token"], salt=TOKEN_SALT, max_age=3600)
        self.assertEqual(token["owner"], self.producer.pk)
        self.assertEqual(token["size"], 500000)
        self.assertIn("/track/", token["key"])
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_stems_zip_is_supported(self):
        self.client.force_login(self.producer)
        env = {
            "R2_UPLOADS_ENABLED": "true", "R2_ACCOUNT_ID": "a" * 32,
            "R2_BUCKET_NAME": "test-bucket", "R2_ACCESS_KEY_ID": "test-key",
            "R2_SECRET_ACCESS_KEY": "test-secret",
        }
        payload = {"kind": "stems", "filename": "stems.zip", "size": 200000000,
                   "content_type": "application/zip"}
        with patch.dict(os.environ, env), patch("app.r2_presign.r2_client", return_value=StubR2()):
            response = self.post(payload)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn("upload_token", response.json())
class R2ConfirmTests(TestCase):
    def setUp(self):
        self.producer = User.objects.create_user(username="confirmproducer", password="test-only")
        Usuario.objects.create(user=self.producer, tipo_usu=Usuario.PRODUCTOR)
        self.other = User.objects.create_user(username="otherproducer", password="test-only")
        Usuario.objects.create(user=self.other, tipo_usu=Usuario.PRODUCTOR)
        self.artist = User.objects.create_user(username="confirmartist", password="test-only")
        Usuario.objects.create(user=self.artist, tipo_usu=Usuario.ARTISTA)
        self.key = "pending/{}/track/{}.wav".format(self.producer.pk, "a" * 32)
        self.payload = {
            "owner": self.producer.pk, "key": self.key, "size": 12345,
            "kind": "track", "mime": "audio/wav",
        }
        self.url = "/api/r2/confirm/"
        self.env = {
            "R2_UPLOADS_ENABLED": "true", "R2_ACCOUNT_ID": "a" * 32,
            "R2_BUCKET_NAME": "test-bucket", "R2_ACCESS_KEY_ID": "test-key",
            "R2_SECRET_ACCESS_KEY": "test-secret",
        }

    def post(self, token=None):
        if token is None:
            token = signing.dumps(self.payload, salt=TOKEN_SALT)
        return self.client.post(
            self.url, data=json.dumps({"upload_token": token}), content_type="application/json"
        )

    def test_requires_producer_and_post(self):
        self.assertEqual(self.post().status_code, 401)
        self.client.force_login(self.artist)
        self.assertEqual(self.post().status_code, 403)
        self.client.force_login(self.producer)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_rejects_forged_expired_and_wrong_owner_tokens(self):
        with patch.dict(os.environ, self.env):
            self.client.force_login(self.producer)
            self.assertEqual(self.post("inventado").status_code, 400)

            with patch(
                "django.core.signing.TimestampSigner.timestamp",
                return_value="0",
            ):
                expired_token = signing.dumps(
                    self.payload,
                    salt=TOKEN_SALT,
                )

            self.assertEqual(self.post(expired_token).status_code, 400)

            self.client.force_login(self.other)
            self.assertEqual(self.post().status_code, 400)

    def test_rejects_invalid_signed_object_key(self):
        self.client.force_login(self.producer)

        with patch.dict(os.environ, self.env):
            for key in (
                "../../secret.wav",
                "pending/999/track/" + "a" * 32 + ".wav",
            ):
                with self.subTest(key=key):
                    forged_payload = {**self.payload, "key": key}
                    token = signing.dumps(
                        forged_payload,
                        salt=TOKEN_SALT,
                    )
                    self.assertEqual(
                        self.post(token).status_code,
                        400,
                    )

    def test_disabled_by_default(self):
        self.client.force_login(self.producer)
        with patch.dict(os.environ, {"R2_UPLOADS_ENABLED": "0"}):
            self.assertEqual(self.post().status_code, 503)

    def test_matching_head_is_verified_only_as_pending(self):
        from unittest.mock import Mock
        self.client.force_login(self.producer)
        r2 = Mock()
        r2.head_object.return_value = {"ContentLength": 12345, "ContentType": "audio/wav"}
        with patch.dict(os.environ, self.env), patch("app.r2_presign.r2_client", return_value=r2):
            response = self.post()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()["verified"])
        self.assertIn("Pendiente", response.json()["detail"])
        r2.head_object.assert_called_once_with(Bucket="test-bucket", Key=self.key)

    def test_head_size_or_mime_mismatch_is_rejected(self):
        from unittest.mock import Mock
        self.client.force_login(self.producer)
        r2 = Mock()
        for metadata in (
            {"ContentLength": 12346, "ContentType": "audio/wav"},
            {"ContentLength": 12345, "ContentType": "application/octet-stream"},
        ):
            with self.subTest(metadata=metadata):
                r2.head_object.return_value = metadata
                with patch.dict(os.environ, self.env), patch("app.r2_presign.r2_client", return_value=r2):
                    response = self.post()
                self.assertEqual(response.status_code, 409)

    def test_head_failure_does_not_confirm(self):
        from unittest.mock import Mock
        self.client.force_login(self.producer)
        r2 = Mock()
        r2.head_object.side_effect = RuntimeError("network")
        with patch.dict(os.environ, self.env), patch("app.r2_presign.r2_client", return_value=r2):
            self.assertEqual(self.post().status_code, 503)
