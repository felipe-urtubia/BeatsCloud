import subprocess
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from app.models import Track, Usuario, Genero_Musical
from app.r2_claim import R2UploadClaim
from app.r2_registration_prepare import R2RegistrationDraft
from app.r2_track_registration import (
    R2TrackRegistrationError,
    register_prepared_r2_track,
)


class R2TrackRegistrationTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="productor_registro_integrado_r2",
        )

        self.perfil = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.genero = Genero_Musical.objects.create(
            descripcion="Genero aislado"
        )

        pendiente = (
            f"pending/{self.user.pk}/track/"
            + ("a" * 32)
            + ".wav"
        )

        privada = (
            f"private/{self.user.pk}/track/"
            + ("b" * 32)
            + ".wav"
        )

        self.reserva = R2UploadClaim.objects.create(
            owner=self.user,
            pending_key=pendiente,
            expected_size=16044,
            expected_mime="audio/wav",
            status="processing",
        )

        self.origen = (
            Path(settings.MEDIA_ROOT)
            / "preview-prueba.mp3"
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
                str(self.origen),
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )

        self.draft = R2RegistrationDraft(
            owner=self.user.pk,
            pending_key=pendiente,
            private_key=privada,
            expected_size=16044,
            expected_mime="audio/wav",
            preview_path=self.origen,
        )

    def registrar(self, **cambios):
        opciones = {
            "claim_id": self.reserva.pk,
            "user_id": self.user.pk,
            "draft": self.draft,
            "nombre_track": "Beat R2 de prueba",
            "precio": 1000,
            "genero_id": self.genero.pk,
        }

        opciones.update(cambios)

        return register_prepared_r2_track(**opciones)

    def test_registra_cancion_y_preview(self):
        cancion = self.registrar()

        self.reserva.refresh_from_db()
        cancion.refresh_from_db()

        self.assertEqual(cancion.storage_backend, "r2")
        self.assertEqual(cancion.media_status, "ready")
        self.assertEqual(cancion.track.name, "")
        self.assertEqual(
            cancion.r2_object_key,
            self.draft.private_key,
        )

        self.assertTrue(cancion.preview.name.startswith("previews/"))
        self.assertTrue(cancion.preview.storage.exists(
            cancion.preview.name
        ))

        self.assertEqual(self.reserva.status, "ready")
        self.assertEqual(self.reserva.track_id, cancion.pk)

    def test_no_registra_dos_veces(self):
        self.registrar()

        with self.assertRaises(R2TrackRegistrationError):
            self.registrar()

        self.assertEqual(Track.objects.count(), 1)
        self.assertEqual(R2UploadClaim.objects.count(), 1)

    def test_no_registra_otro_propietario(self):
        with self.assertRaises(R2TrackRegistrationError):
            self.registrar(user_id=99999)

        self.assertEqual(Track.objects.count(), 0)

    def test_rechaza_precio_invalido(self):
        with self.assertRaises(R2TrackRegistrationError):
            self.registrar(precio=-1)

        self.assertEqual(Track.objects.count(), 0)

    def test_rechaza_genero_inexistente(self):
        with self.assertRaises(R2TrackRegistrationError):
            self.registrar(genero_id=99999)

        self.assertEqual(Track.objects.count(), 0)

    def test_rechaza_reserva_incompatible(self):
        self.reserva.expected_size = 123
        self.reserva.save(update_fields=["expected_size"])

        with self.assertRaises(R2TrackRegistrationError):
            self.registrar()

        self.assertEqual(Track.objects.count(), 0)

    def test_rechaza_preview_invalida(self):
        self.origen.write_bytes(b"archivo-no-audio")

        with self.assertRaises(R2TrackRegistrationError):
            self.registrar()

        self.assertEqual(Track.objects.count(), 0)

    def test_fallo_finalizacion_revierte_registro(self):
        with patch(
            "app.r2_track_registration.finalize_r2_claim",
            side_effect=RuntimeError(
                "Fallo simulado de finalizacion."
            ),
        ):
            with self.assertRaises(RuntimeError):
                self.registrar()

        self.reserva.refresh_from_db()

        self.assertEqual(Track.objects.count(), 0)
        self.assertEqual(self.reserva.status, "failed")
        self.assertEqual(
            self.reserva.private_key,
            self.draft.private_key,
        )

        previews = list(
            (Path(settings.MEDIA_ROOT) / "previews")
            .glob("r2-*.mp3")
        )

        self.assertEqual(previews, [])
