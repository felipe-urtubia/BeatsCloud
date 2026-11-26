"""Pruebas de limpieza conservadora de objetos R2."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import TestCase

from app.models import (
    Usuario,
    Track,
    Genero_Musical,
    R2UploadClaim,
)

from app.r2_upload_workflow import (
    _delete_private_if_unattached,
)


class R2CleanupSafetyTests(TestCase):

    def setUp(self):

        self.usuario = User.objects.create_user(
            username="d10_r2_cleanup",
            password="Solo-Pruebas-R2-D10!",
        )

        self.perfil = Usuario.objects.create(
            user=self.usuario,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.genero, _ = Genero_Musical.objects.get_or_create(
            descripcion="Pop"
        )

        self.key = (
            f"private/{self.usuario.pk}/covers/"
            + "a" * 32
            + ".jpg"
        )

        self.draft = SimpleNamespace(
            private_key=self.key
        )

        self.cloud = Mock()

        self.bucket = "bucket-exclusivo-de-pruebas"

    def limpiar(self, track=None):

        _delete_private_if_unattached(
            self.cloud,
            self.bucket,
            self.draft,
            track,
            "r2_cover_key",
        )

    def test_elimina_objeto_sin_referencias(self):

        self.limpiar()

        self.cloud.delete_object.assert_called_once_with(
            Bucket=self.bucket,
            Key=self.key,
        )

    def test_conserva_objeto_vinculado_a_otra_cancion(self):

        track = Track.objects.create(
            nombre_track="Contenido protegido D10",
            precio=1000,
            track="canciones/prueba.wav",
            genero=self.genero,
            usuario=self.perfil,
            r2_cover_key=self.key,
            media_status="ready",
        )

        # Incluso si no recibimos la instancia de la cancion,
        # la referencia existente debe impedir su eliminacion.
        self.limpiar(track=None)

        self.cloud.delete_object.assert_not_called()

        track.refresh_from_db()

        self.assertEqual(
            track.r2_cover_key,
            self.key,
        )

    def test_conserva_objeto_referenciado_por_reserva(self):

        reserva = R2UploadClaim.objects.create(
            owner=self.usuario,
            pending_key=(
                f"pending/{self.usuario.pk}/tracks/"
                + "b" * 32
                + ".wav"
            ),
            expected_size=1024,
            expected_mime="audio/wav",
            status="failed",
            private_key=self.key,
        )

        self.limpiar()

        self.cloud.delete_object.assert_not_called()

        reserva.refresh_from_db()

        self.assertEqual(
            reserva.private_key,
            self.key,
        )

    def test_error_postgresql_impide_eliminacion(self):

        for objetivo in (
            "app.r2_upload_workflow.Track.objects.filter",
            "app.models.R2UploadClaim.objects.filter",
        ):

            with self.subTest(objetivo=objetivo):

                with patch(
                    objetivo,
                    side_effect=DatabaseError(
                        "Fallo simulado PostgreSQL"
                    ),
                ):

                    self.limpiar()

                self.cloud.delete_object.assert_not_called()

    def test_no_elimina_claves_no_privadas(self):

        for key in (
            "",
            None,
            "pending/1/archivo.wav",
            "previews/archivo.mp3",
        ):

            with self.subTest(key=key):

                self.draft.private_key = key

                self.limpiar()

                self.cloud.delete_object.assert_not_called()
