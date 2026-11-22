from contextlib import contextmanager, nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.db import OperationalError
from django.test import TestCase

from app.models import Genero_Musical, Track, Usuario
from app.r2_preview_recovery import (
    R2PreviewRecoveryError,
    recover_track_preview,
)
from app.r2_preview_storage import PREVIEW_KEY_PATTERN


class R2PreviewRecoveryEngineTests(TestCase):

    def setUp(self):
        user = User.objects.create_user(
            username="motor_recuperacion",
            password="password-prueba",
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
            + "a" * 32 + ".wav"
        )
        self.existing_key = (
            "previews/r2-" + "b" * 32 + ".mp3"
        )
        self.previous_key = "previews/antigua.mp3"

        self.track = Track.objects.create(
            nombre_track="Recuperacion segura",
            precio=1000,
            usuario=perfil,
            genero=genero,
            storage_backend="r2",
            media_status="ready",
            r2_owner_user_id=user.pk,
            r2_object_key=self.private_key,
            preview=self.previous_key,
        )

        self.client = Mock()
        self.client.head_object.side_effect = self._head

    def _head(self, **kwargs):
        self.assertEqual(
            kwargs["Bucket"], "bucket-prueba"
        )

        if kwargs["Key"] == self.private_key:
            return {
                "ContentLength": 100000,
                "ContentType": "audio/wav",
            }

        if kwargs["Key"] == self.existing_key:
            return {
                "ContentLength": 5000,
                "ContentType": "audio/mpeg",
            }

        raise AssertionError(
            "Se consulto un objeto R2 inesperado."
        )

    @contextmanager
    def _simular(self):
        with patch(
            "app.r2_preview_recovery.staged_r2_preview",
            return_value=nullcontext(Path("preview-simulada.mp3")),
        ) as generar, patch(
            "app.r2_preview_recovery.upload_r2_preview",
        ) as subir:
            yield generar, subir

    def _recuperar(self):
        return recover_track_preview(
            track_id=self.track.pk,
            client=self.client,
            bucket="bucket-prueba",
        )

    def _verificar_borrado_seguro(self):
        self.client.delete_object.assert_called_once()
        kwargs = self.client.delete_object.call_args.kwargs

        self.assertEqual(kwargs["Bucket"], "bucket-prueba")
        self.assertIsNotNone(
            PREVIEW_KEY_PATTERN.fullmatch(kwargs["Key"])
        )
        self.assertNotEqual(
            kwargs["Key"], self.private_key
        )

    def test_recuperacion_correcta(self):
        with self._simular() as (generar, subir):
            resultado = self._recuperar()

        self.assertEqual(resultado["status"], "recuperada")
        self.assertIsNotNone(
            PREVIEW_KEY_PATTERN.fullmatch(resultado["key"])
        )

        self.track.refresh_from_db()
        self.assertEqual(
            self.track.preview.name, resultado["key"]
        )
        self.assertEqual(
            self.track.r2_object_key, self.private_key
        )

        generar.assert_called_once()
        subir.assert_called_once()
        self.client.delete_object.assert_not_called()

    def test_preview_existente_no_se_reemplaza(self):
        self.track.preview = self.existing_key
        self.track.save(update_fields=["preview"])

        with self._simular() as (generar, subir):
            resultado = self._recuperar()

        self.assertEqual(resultado["status"], "correcta")
        self.assertEqual(resultado["key"], self.existing_key)
        generar.assert_not_called()
        subir.assert_not_called()
        self.client.delete_object.assert_not_called()

    def test_fallo_subida_limpia_preview_nueva(self):
        with self._simular() as (_, subir):
            subir.side_effect = OSError(
                "Fallo de subida simulado"
            )

            with self.assertRaises(OSError):
                self._recuperar()

        self.track.refresh_from_db()
        self.assertEqual(
            self.track.preview.name, self.previous_key
        )
        self._verificar_borrado_seguro()

    def test_cambio_concurrente_no_se_sobrescribe(self):
        nuevo_valor = "previews/cambio_externo.mp3"

        def cambio_concurrente(**kwargs):
            Track.objects.filter(
                pk=self.track.pk
            ).update(preview=nuevo_valor)

        with self._simular() as (_, subir):
            subir.side_effect = cambio_concurrente

            with self.assertRaises(
                R2PreviewRecoveryError
            ):
                self._recuperar()

        self.track.refresh_from_db()
        self.assertEqual(
            self.track.preview.name, nuevo_valor
        )
        self._verificar_borrado_seguro()

    def test_fallo_postgresql_limpia_preview(self):
        with self._simular() as (_, subir):
            with patch(
                "django.db.models.query.QuerySet.update",
                side_effect=OperationalError(
                    "Fallo de DB simulado"
                ),
            ):
                with self.assertRaises(OperationalError):
                    self._recuperar()

        subir.assert_called_once()
        self._verificar_borrado_seguro()

        self.track.refresh_from_db()
        self.assertEqual(
            self.track.preview.name, self.previous_key
        )

    def test_fallo_limpieza_se_reporta(self):
        self.client.delete_object.side_effect = OSError(
            "Fallo de limpieza simulado"
        )

        with self._simular() as (_, subir):
            subir.side_effect = OSError(
                "Fallo de subida simulado"
            )

            with self.assertRaisesRegex(
                R2PreviewRecoveryError,
                "revision manual",
            ):
                self._recuperar()

        self._verificar_borrado_seguro()

    def test_fallo_generacion_no_borra_original(self):
        with self._simular() as (generar, subir):
            generar.side_effect = OSError(
                "Fallo FFmpeg simulado"
            )

            with self.assertRaises(OSError):
                self._recuperar()

        subir.assert_not_called()
        self.client.delete_object.assert_not_called()

        self.track.refresh_from_db()
        self.assertEqual(
            self.track.preview.name, self.previous_key
        )
