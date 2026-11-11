import subprocess
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.test import TestCase

from app.models import Genero_Musical, Track, Usuario
from app.r2_claim import R2UploadClaim
from app.r2_presign import ALLOWED, TOKEN_SALT
from app.r2_registration_guard import R2RegistrationGuardError
from app.r2_registration_prepare import R2RegistrationDraft
from app.r2_upload_workflow import (
    R2UploadWorkflowError,
    R2UploadWorkflowConflict,
    complete_r2_track_upload,
)


class R2UploadWorkflowTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="productor_flujo_r2"
        )

        Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.genero = Genero_Musical.objects.create(
            descripcion="Genero flujo aislado"
        )

        self.pendiente = (
            f"pending/{self.user.pk}/track/"
            + ("a" * 32)
            + ".wav"
        )

        self.privada = (
            f"private/{self.user.pk}/track/"
            + ("b" * 32)
            + ".wav"
        )

        self.mime = sorted(ALLOWED["track"][".wav"])[0]

        self.token = signing.dumps(
            {
                "owner": self.user.pk,
                "key": self.pendiente,
                "size": 16044,
                "kind": "track",
                "mime": self.mime,
            },
            salt=TOKEN_SALT,
        )

        self.preview = (
            Path(settings.MEDIA_ROOT) / "workflow-test.mp3"
        )

        ejecutable = getattr(
            settings,
            "FFMPEG_PATH",
            "ffmpeg",
        )

        subprocess.run(
            [
                ejecutable,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=0.5",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "128k",
                "-y",
                str(self.preview),
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )

        self.draft = R2RegistrationDraft(
            owner=self.user.pk,
            pending_key=self.pendiente,
            private_key=self.privada,
            expected_size=16044,
            expected_mime=self.mime,
            preview_path=self.preview,
        )

    def ejecutar(self, **cambios):
        datos = {
            "client": object(),
            "bucket": "beatcloud-media",
            "user_id": self.user.pk,
            "upload_token": self.token,
            "nombre_track": "Beat de flujo R2",
            "precio": 1000,
            "genero_id": self.genero.pk,
        }

        datos.update(cambios)

        return complete_r2_track_upload(**datos)

    def ejecutar_con_preparacion_simulada(self, **cambios):
        with patch(
            "app.r2_upload_workflow.prepare_r2_track_registration",
            return_value=nullcontext(self.draft),
        ):
            return self.ejecutar(**cambios)

    def test_flujo_completo_registra_cancion(self):
        cancion = self.ejecutar_con_preparacion_simulada()

        reserva = R2UploadClaim.objects.get(
            pending_key=self.pendiente
        )

        cancion.refresh_from_db()

        self.assertEqual(reserva.status, "ready")
        self.assertEqual(reserva.track_id, cancion.pk)
        self.assertEqual(cancion.media_status, "ready")
        self.assertEqual(cancion.storage_backend, "r2")
        self.assertEqual(cancion.r2_object_key, self.privada)

        self.assertTrue(
            cancion.preview.storage.exists(
                cancion.preview.name
            )
        )

    def test_segunda_solicitud_no_duplica(self):
        with patch(
            "app.r2_upload_workflow.prepare_r2_track_registration",
            return_value=nullcontext(self.draft),
        ) as preparar:
            self.ejecutar()

            with self.assertRaises(
                R2UploadWorkflowConflict
            ):
                self.ejecutar()

            preparar.assert_called_once()

        self.assertEqual(Track.objects.count(), 1)
        self.assertEqual(R2UploadClaim.objects.count(), 1)

    def test_token_invalido_no_crea_reserva(self):
        with self.assertRaises(R2RegistrationGuardError):
            self.ejecutar(upload_token="token-invalido")

        self.assertEqual(R2UploadClaim.objects.count(), 0)

    def test_rechaza_usuario_sin_perfil_productor(self):
        otro = get_user_model().objects.create_user(
            username="usuario_no_productor_r2"
        )

        with self.assertRaises(R2UploadWorkflowError):
            self.ejecutar(user_id=otro.pk)

        self.assertEqual(R2UploadClaim.objects.count(), 0)

    def test_precio_invalido_no_consume_reserva(self):
        with self.assertRaises(R2UploadWorkflowError):
            self.ejecutar(precio=-1)

        self.assertEqual(R2UploadClaim.objects.count(), 0)

    def test_fallo_preparacion_marca_failed(self):
        with patch(
            "app.r2_upload_workflow.prepare_r2_track_registration",
            side_effect=RuntimeError(
                "Fallo simulado en preparacion R2"
            ),
        ):
            with self.assertRaises(RuntimeError):
                self.ejecutar()

        reserva = R2UploadClaim.objects.get(
            pending_key=self.pendiente
        )

        self.assertEqual(reserva.status, "failed")
        self.assertEqual(Track.objects.count(), 0)

    def test_fallo_registro_marca_failed(self):
        with (
            patch(
                "app.r2_upload_workflow.prepare_r2_track_registration",
                return_value=nullcontext(self.draft),
            ),
            patch(
                "app.r2_upload_workflow.register_prepared_r2_track",
                side_effect=RuntimeError(
                    "Fallo simulado al registrar"
                ),
            ),
        ):
            with self.assertRaises(RuntimeError):
                self.ejecutar()

        reserva = R2UploadClaim.objects.get(
            pending_key=self.pendiente
        )

        self.assertEqual(reserva.status, "failed")
        self.assertEqual(Track.objects.count(), 0)

    def test_preview_invalida_no_publica(self):
        self.preview.write_bytes(b"no-es-un-mp3")

        with self.assertRaises(Exception):
            self.ejecutar_con_preparacion_simulada()

        reserva = R2UploadClaim.objects.get(
            pending_key=self.pendiente
        )

        self.assertEqual(reserva.status, "failed")
        self.assertEqual(Track.objects.count(), 0)
