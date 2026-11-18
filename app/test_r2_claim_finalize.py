from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from app.models import Track, Usuario, Genero_Musical
from app.r2_claim import R2UploadClaim
from app.r2_claim_finalize import (
    R2ClaimFinalizationError,
    finalize_r2_claim,
)


class R2ClaimFinalizeTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="productor_finalizacion_r2"
        )

        self.perfil = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.genero = Genero_Musical.objects.create(
            descripcion="Genero de prueba R2"
        )

        self.privada = (
            f"private/{self.user.pk}/track/"
            + ("b" * 32)
            + ".wav"
        )

        pendiente = (
            f"pending/{self.user.pk}/track/"
            + ("a" * 32)
            + ".wav"
        )

        self.reserva = R2UploadClaim.objects.create(
            owner=self.user,
            pending_key=pendiente,
            expected_size=16044,
            expected_mime="audio/wav",
            status="processing",
            private_key=self.privada,
        )

        self.track = Track.objects.create(
            nombre_track="Cancion aislada R2",
            precio=1000,
            genero=self.genero,
            usuario=self.perfil,
            track="",
            preview="previews/prueba-aislada.mp3",
            storage_backend="r2",
            r2_object_key=self.privada,
            media_status="processing",
        )

    def finalizar(self, **cambios):
        datos = {
            "claim_id": self.reserva.pk,
            "user_id": self.user.pk,
            "track_id": self.track.pk,
        }
        datos.update(cambios)
        return finalize_r2_claim(**datos)

    def rechazar(self):
        with self.assertRaises(R2ClaimFinalizationError):
            self.finalizar()

    def comprobar_sin_publicar(self):
        self.reserva.refresh_from_db()
        self.track.refresh_from_db()

        self.assertEqual(self.reserva.status, "processing")
        self.assertIsNone(self.reserva.track_id)
        self.assertEqual(
            self.track.media_status, "processing"
        )

    def test_finaliza_ambos_registros(self):
        self.assertTrue(self.finalizar())

        self.reserva.refresh_from_db()
        self.track.refresh_from_db()

        self.assertEqual(self.reserva.status, "ready")
        self.assertEqual(self.reserva.track_id, self.track.pk)
        self.assertEqual(self.track.media_status, "ready")

    def test_repeticion_no_modifica_registros(self):
        self.assertTrue(self.finalizar())
        self.assertFalse(self.finalizar())

        self.assertEqual(
            R2UploadClaim.objects.count(), 1
        )
        self.assertEqual(Track.objects.count(), 1)

    def test_otro_usuario_no_finaliza(self):
        with self.assertRaises(R2ClaimFinalizationError):
            self.finalizar(user_id=99999)

        self.comprobar_sin_publicar()

    def test_track_de_otro_productor_no_finaliza(self):
        otro = get_user_model().objects.create_user(
            username="segundo_finalizador_r2"
        )

        perfil_ajeno = Usuario.objects.create(
            user=otro,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.track.usuario = perfil_ajeno
        self.track.save(update_fields=["usuario"])

        self.rechazar()
        self.comprobar_sin_publicar()

    def test_no_finaliza_track_local(self):
        self.track.storage_backend = "local"
        self.track.save(update_fields=["storage_backend"])

        self.rechazar()
        self.comprobar_sin_publicar()

    def test_no_finaliza_sin_preview(self):
        self.track.preview = ""
        self.track.save(update_fields=["preview"])

        self.rechazar()
        self.comprobar_sin_publicar()

    def test_no_finaliza_clave_distinta(self):
        self.track.r2_object_key = (
            f"private/{self.user.pk}/track/"
            + ("c" * 32)
            + ".wav"
        )
        self.track.save(update_fields=["r2_object_key"])

        self.rechazar()
        self.comprobar_sin_publicar()

    def test_no_finaliza_reserva_failed(self):
        self.reserva.status = "failed"
        self.reserva.save(update_fields=["status"])

        self.rechazar()

        self.reserva.refresh_from_db()
        self.track.refresh_from_db()

        self.assertEqual(self.reserva.status, "failed")
        self.assertEqual(
            self.track.media_status, "processing"
        )

    def test_no_finaliza_con_original_local(self):
        self.track.track = "canciones/original-local.wav"
        self.track.save(update_fields=["track"])

        self.rechazar()
        self.comprobar_sin_publicar()

    def test_transaccion_revierte_fallo_de_guardado(self):
        with patch.object(
            R2UploadClaim,
            "save",
            side_effect=RuntimeError(
                "Fallo simulado de persistencia."
            ),
        ):
            with self.assertRaises(RuntimeError):
                self.finalizar()

        self.comprobar_sin_publicar()

    def test_no_finaliza_track_vinculado_a_otra_reserva(self):
        R2UploadClaim.objects.create(
            owner=self.user,
            pending_key=(
                f"pending/{self.user.pk}/track/"
                + ("f" * 32)
                + ".wav"
            ),
            expected_size=16044,
            expected_mime="audio/wav",
            status="ready",
            track=self.track,
        )

        self.rechazar()
        self.comprobar_sin_publicar()
