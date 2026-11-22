from io import StringIO
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError
from django.contrib.auth.models import User
from django.core.management import call_command, CommandError
from django.test import TestCase

from app.models import Genero_Musical, Track, Usuario


class R2PreviewRecoveryAuditTests(TestCase):

    def setUp(self):
        user = User.objects.create_user(
            username="auditoria_r2",
            password="password-de-prueba",
        )
        perfil = Usuario.objects.create(
            user=user,
            tipo_usu=Usuario.PRODUCTOR,
        )
        genero = Genero_Musical.objects.create(
            descripcion="Pop",
        )

        self.private_key = (
            f"private/{user.pk}/track/"
            + "a" * 32
            + ".wav"
        )
        self.preview_key = (
            "previews/r2-" + "b" * 32 + ".mp3"
        )

        self.track = Track.objects.create(
            nombre_track="Auditoria R2",
            precio=1000,
            usuario=perfil,
            genero=genero,
            storage_backend="r2",
            media_status="ready",
            r2_owner_user_id=user.pk,
            r2_object_key=self.private_key,
            preview="previews/antigua.mp3",
        )

        self.r2 = Mock()
        self.preview_error = None
        self.original_metadata = {
            "ContentLength": 100000,
            "ContentType": "audio/wav",
        }
        self.r2.head_object.side_effect = self._head

    def _head(self, **kwargs):
        self.assertEqual(
            kwargs["Bucket"], "bucket-prueba"
        )

        if kwargs["Key"] == self.private_key:
            return self.original_metadata

        if kwargs["Key"] == self.preview_key:
            if self.preview_error is not None:
                raise self.preview_error

            return {
                "ContentLength": 5000,
                "ContentType": "audio/mpeg",
            }

        raise AssertionError(
            "Se intento consultar un objeto inesperado."
        )

    def _ejecutar(self, *ids):
        salida = StringIO()
        argumentos = []

        for track_id in (ids or (self.track.pk,)):
            argumentos.extend([
                "--track-id", str(track_id)
            ])

        with patch(
            "app.management.commands.recuperar_previews_r2.r2_configuration",
            return_value={"R2_BUCKET_NAME": "bucket-prueba"},
        ), patch(
            "app.management.commands.recuperar_previews_r2.r2_client",
            return_value=self.r2,
        ):
            call_command(
                "recuperar_previews_r2",
                *argumentos,
                stdout=salida,
            )

        return salida.getvalue()

    def _sin_escrituras(self):
        self.r2.put_object.assert_not_called()
        self.r2.delete_object.assert_not_called()
        self.r2.get_object.assert_not_called()

    def test_preview_antigua_queda_pendiente(self):
        salida = self._ejecutar()

        self.assertIn("1 pendientes", salida)
        self.assertEqual(
            self.r2.head_object.call_count, 1
        )

        self.track.refresh_from_db()
        self.assertEqual(
            self.track.preview.name,
            "previews/antigua.mp3",
        )
        self._sin_escrituras()

    def test_preview_existente_se_conserva(self):
        self.track.preview = self.preview_key
        self.track.save(update_fields=["preview"])

        salida = self._ejecutar()

        self.assertIn("1 correctas", salida)
        self.assertEqual(
            self.r2.head_object.call_count, 2
        )

        self.track.refresh_from_db()
        self.assertEqual(
            self.track.preview.name,
            self.preview_key,
        )
        self._sin_escrituras()

    def test_preview_r2_faltante_queda_pendiente(self):
        self.track.preview = self.preview_key
        self.track.save(update_fields=["preview"])

        self.preview_error = ClientError(
            {"Error": {"Code": "404"}},
            "HeadObject",
        )

        salida = self._ejecutar()

        self.assertIn("1 pendientes", salida)
        self._sin_escrituras()

    def test_original_no_disponible_reporta_error(self):
        self.r2.head_object.side_effect = ClientError(
            {"Error": {"Code": "404"}},
            "HeadObject",
        )

        with self.assertRaises(CommandError):
            self._ejecutar()

        self._sin_escrituras()

    def test_propietario_incorrecto_se_rechaza(self):
        self.track.r2_owner_user_id += 1
        self.track.save(
            update_fields=["r2_owner_user_id"]
        )

        with self.assertRaises(CommandError):
            self._ejecutar()

        self.r2.head_object.assert_not_called()
        self._sin_escrituras()

    def test_error_permisos_preview_no_es_faltante(self):
        self.track.preview = self.preview_key
        self.track.save(update_fields=["preview"])

        self.preview_error = ClientError(
            {"Error": {"Code": "403"}},
            "HeadObject",
        )

        with self.assertRaises(CommandError):
            self._ejecutar()

        self._sin_escrituras()

    def test_metadatos_original_invalidos_se_rechazan(self):
        self.original_metadata = {
            "ContentLength": 0,
            "ContentType": "audio/wav",
        }

        with self.assertRaises(CommandError):
            self._ejecutar()

        self._sin_escrituras()
