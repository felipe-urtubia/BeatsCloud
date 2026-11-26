"""Proteccion de publicacion local frente al cierre de cuentas."""

import io
import wave

from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory, override_settings

from app.models import Usuario, Track, Genero_Musical

from app.views import (
    upload_file,
    _seudonimizar_identidad_cuenta,
)

from app.api_shim import upload_api


class LocalUploadSecurityTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="d10_local_upload",
            password="Solo-Pruebas-Local-D10!",
        )

        self.perfil = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.genero, _ = Genero_Musical.objects.get_or_create(
            descripcion="Pop",
        )

        self.factory = RequestFactory()

        temporal = TemporaryDirectory()

        self.addCleanup(temporal.cleanup)

        configuracion = override_settings(
            MEDIA_ROOT=temporal.name,
            STORAGES={
                "default": {
                    "BACKEND":
                        "django.core.files.storage.FileSystemStorage",
                },
                "staticfiles": {
                    "BACKEND":
                        "django.contrib.staticfiles.storage.StaticFilesStorage",
                },
            },
        )

        configuracion.enable()

        self.addCleanup(configuracion.disable)

    def audio(self):

        memoria = io.BytesIO()

        with wave.open(memoria, "wb") as archivo:

            archivo.setnchannels(1)
            archivo.setsampwidth(2)
            archivo.setframerate(8000)
            archivo.writeframes(b"\\x00" * 16000)

        return SimpleUploadedFile(
            "d10-prueba.wav",
            memoria.getvalue(),
            content_type="audio/wav",
        )

    def solicitud(self):

        datos = {
            "nombre_track": "Publicacion local D10",
            "precio": "1000",
            "genero": str(self.genero.pk),
            "resource_type": "instrumental",
            "bpm": "140",
            "scale_key": "Am",
            "mood": "Oscuro",
            "duration": "30",
            "has_stems": "false",
            "has_wav": "true",
            "has_midi": "false",
            "allow_free_download": "false",
            "has_watermark": "true",
            "track": self.audio(),
        }

        request = self.factory.post(
            "/api/upload/",
            data=datos,
        )

        # Instancia autenticada antes del posible cierre.
        request.user = self.user

        # Exclusivamente para pruebas directas de la vista.
        request._dont_enforce_csrf_checks = True

        return request

    def comprobar_rechazo(
        self,
        endpoint,
        modulo,
        estado,
    ):

        with (
            patch(modulo + ".TrackForm") as formulario,
            patch(modulo + ".generar_preview_audio") as preview,
            patch("app.views.messages.error"),
        ):

            respuesta = endpoint(
                self.solicitud()
            )

        self.assertEqual(
            respuesta.status_code,
            estado,
        )

        formulario.assert_not_called()
        preview.assert_not_called()

        self.assertFalse(
            Track.objects.filter(
                usuario_id=self.perfil.pk,
            ).exists()
        )

    def test_cuenta_cerrada_no_publica_local(self):

        _seudonimizar_identidad_cuenta(
            self.perfil
        )

        # Incluso si is_active se restaura accidentalmente.
        User.objects.filter(
            pk=self.user.pk
        ).update(is_active=True)

        for endpoint, modulo in (
            (upload_file, "app.views"),
            (upload_api, "app.api_shim"),
        ):

            with self.subTest(endpoint=modulo):

                self.comprobar_rechazo(
                    endpoint,
                    modulo,
                    403,
                )

    def test_cuenta_inactiva_no_publica_local(self):

        User.objects.filter(
            pk=self.user.pk
        ).update(is_active=False)

        self.assertTrue(self.user.is_active)

        for endpoint, modulo in (
            (upload_file, "app.views"),
            (upload_api, "app.api_shim"),
        ):

            with self.subTest(endpoint=modulo):

                self.comprobar_rechazo(
                    endpoint,
                    modulo,
                    403,
                )

    def test_artista_no_publica_local(self):

        Usuario.objects.filter(
            pk=self.perfil.pk
        ).update(
            tipo_usu=Usuario.ARTISTA
        )

        self.comprobar_rechazo(
            upload_file,
            "app.views",
            302,
        )

        self.comprobar_rechazo(
            upload_api,
            "app.api_shim",
            403,
        )

    def comprobar_publicacion(
        self,
        endpoint,
        modulo,
        estado,
    ):

        with (
            patch(modulo + ".generar_preview_audio") as preview,
            patch("app.views.messages.success"),
        ):

            respuesta = endpoint(
                self.solicitud()
            )

        self.assertEqual(
            respuesta.status_code,
            estado,
            respuesta.content,
        )

        track = Track.objects.get(
            usuario_id=self.perfil.pk,
        )

        self.assertEqual(
            track.nombre_track,
            "Publicacion local D10",
        )

        self.assertEqual(track.precio, 1000)

        self.assertEqual(
            track.usuario_id,
            self.perfil.pk,
        )

        self.assertTrue(track.track)

        self.assertTrue(
            track.track.storage.exists(
                track.track.name
            )
        )

        self.assertFalse(track.is_retired)

        preview.assert_called_once()

        self.assertEqual(
            preview.call_args.args[0].pk,
            track.pk,
        )

    def test_productor_activo_publica_api(self):

        self.comprobar_publicacion(
            upload_api,
            "app.api_shim",
            201,
        )

    def test_productor_activo_publica_tradicional(self):

        self.comprobar_publicacion(
            upload_file,
            "app.views",
            302,
        )


    def comprobar_fallo_preview(self, endpoint, modulo):

        with (
            patch(
                modulo + ".generar_preview_audio",
                side_effect=RuntimeError("Fallo simulado"),
            ) as preview,
            patch("app.views.messages.success") as exito,
        ):

            respuesta = endpoint(self.solicitud())

        self.assertEqual(respuesta.status_code, 500)

        preview.assert_called_once()
        exito.assert_not_called()

        self.assertFalse(
            Track.objects.filter(
                usuario_id=self.perfil.pk
            ).exists()
        )

    def test_fallo_preview_api(self):

        self.comprobar_fallo_preview(
            upload_api,
            "app.api_shim",
        )

    def test_fallo_preview_tradicional(self):

        self.comprobar_fallo_preview(
            upload_file,
            "app.views",
        )
