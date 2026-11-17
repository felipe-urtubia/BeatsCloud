from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import encode_multipart

from app.api_shim import ser_track
from app.models import Genero_Musical, Track, Usuario
from app.r2_registration_guard import R2RegistrationGuardError


class R2CoverUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cover-producer",
            password="secret",
        )
        self.profile = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.PRODUCTOR,
        )
        self.genre = Genero_Musical.objects.create(
            descripcion="Pop",
        )
        self.track = Track.objects.create(
            nombre_track="Track de prueba",
            precio=1000,
            genero=self.genre,
            usuario=self.profile,
        )
        self.client.force_login(self.user)

    def patch_cover(self, data):
        # El boundary del cuerpo y el anunciado en Content-Type deben coincidir.
        boundary = "R2CoverBoundary"
        encoded = encode_multipart(boundary, data)
        return self.client.patch(
            f"/api/track/{self.track.pk}/",
            data=encoded,
            content_type=f"multipart/form-data; boundary={boundary}",
        )

    def test_serializador_devuelve_endpoint_para_portada_r2(self):
        self.track.r2_cover_key = (
            f"private/{self.user.pk}/cover/"
            + ("a" * 32)
            + ".png"
        )
        self.track.save(update_fields=["r2_cover_key"])

        payload = ser_track(self.track)

        self.assertEqual(
            payload["foto"],
            f"/api/track/{self.track.pk}/cover/",
        )
        self.assertNotIn("r2_cover_key", payload)

    def test_actualizacion_promueve_portada_y_limpia_la_anterior(self):
        old_key = (
            f"private/{self.user.pk}/cover/"
            + ("a" * 32)
            + ".png"
        )
        new_key = (
            f"private/{self.user.pk}/cover/"
            + ("b" * 32)
            + ".webp"
        )
        self.track.r2_cover_key = old_key
        self.track.save(update_fields=["r2_cover_key"])

        r2_client = Mock()
        draft = SimpleNamespace(private_key=new_key)

        with (
            patch("app.r2_presign.r2_uploads_enabled", return_value=True),
            patch(
                "app.r2_presign.r2_configuration",
                return_value={"R2_BUCKET_NAME": "beatcloud-test"},
            ),
            patch("app.r2_presign.r2_client", return_value=r2_client),
            patch("app.r2_upload_http._bucket", return_value="beatcloud-test"),
            patch("app.r2_registration_guard.validate_r2_cover_token"),
            patch(
                "app.r2_registration_prepare.prepare_r2_cover_upload",
                return_value=draft,
            ) as preparar,
        ):
            response = self.patch_cover(
                {
                    "nombre_track": "Track actualizado",
                    "cover_upload_token": "token-firmado",
                }
            )

        self.assertEqual(response.status_code, 200, response.content)
        self.track.refresh_from_db()
        self.assertEqual(self.track.nombre_track, "Track actualizado")
        self.assertEqual(self.track.r2_cover_key, new_key)
        self.assertEqual(
            response.json()["foto"],
            f"/api/track/{self.track.pk}/cover/",
        )
        preparar.assert_called_once()
        r2_client.delete_object.assert_called_once_with(
            Bucket="beatcloud-test",
            Key=old_key,
        )

    def test_token_invalido_no_actualiza_la_portada(self):
        original = self.track.r2_cover_key

        with (
            patch("app.r2_presign.r2_uploads_enabled", return_value=True),
            patch(
                "app.r2_registration_guard.validate_r2_cover_token",
                side_effect=R2RegistrationGuardError("token invalido"),
            ),
            patch(
                "app.r2_registration_prepare.prepare_r2_cover_upload"
            ) as preparar,
        ):
            response = self.patch_cover(
                {
                    "nombre_track": "No debe guardarse",
                    "cover_upload_token": "token-invalido",
                }
            )

        self.assertEqual(response.status_code, 400)
        self.track.refresh_from_db()
        self.assertEqual(self.track.nombre_track, "Track de prueba")
        self.assertEqual(self.track.r2_cover_key, original)
        preparar.assert_not_called()
