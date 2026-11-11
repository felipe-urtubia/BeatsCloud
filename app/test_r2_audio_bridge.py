import io
from contextlib import contextmanager
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import Client, TestCase

from app.models import (
    Genero_Musical,
    Track,
    Usuario,
)


class R2AudioBridgeTests(TestCase):

    def setUp(self):
        self.autor = get_user_model().objects.create_user(
            username="autor_audio_bridge_r2",
        )

        self.perfil = Usuario.objects.create(
            user=self.autor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.genero = Genero_Musical.objects.create(
            descripcion="Genero puente aislado"
        )

        self.clave = (
            f"private/{self.autor.pk}/track/"
            + ("a" * 32)
            + ".wav"
        )

        self.track = Track.objects.create(
            nombre_track="Audio privado de prueba",
            precio=1500,
            genero=self.genero,
            usuario=self.perfil,
            track="",
            preview="previews/audio-prueba.mp3",
            storage_backend="r2",
            r2_object_key=self.clave,
            media_status="ready",
        )

        self.cliente = Client()
        self.cliente.force_login(self.autor)

        self.escuchar = (
            f"/api/track/{self.track.pk}/reproducir/"
        )

        self.descargar = (
            f"/api/track/{self.track.pk}/descargar/"
        )

    @contextmanager
    def simular_r2(self, audio=b"audio-privado-simulado"):
        cliente_r2 = Mock()

        def obtener(**_):
            return {
                "Body": io.BytesIO(audio),
                "ContentLength": len(audio),
            }

        cliente_r2.get_object.side_effect = obtener

        with (
            patch(
                "app.r2_audio_bridge.r2_configuration",
                return_value={
                    "R2_BUCKET_NAME": "beatcloud-media",
                },
            ),
            patch(
                "app.r2_audio_bridge.r2_client",
                return_value=cliente_r2,
            ) as cliente_creado,
        ):
            yield cliente_r2, cliente_creado

    def test_reproduccion_r2_autorizada(self):
        with self.simular_r2() as (
            cliente_r2, _
        ):
            respuesta = self.cliente.get(
                self.escuchar
            )

            self.assertEqual(
                respuesta.status_code, 200
            )

            contenido = b"".join(
                respuesta.streaming_content
            )

            self.assertEqual(
                contenido,
                b"audio-privado-simulado",
            )

            self.assertEqual(
                respuesta["Cache-Control"],
                "private, no-store",
            )

            cliente_r2.get_object.assert_called_once_with(
                Bucket="beatcloud-media",
                Key=self.clave,
            )

    def test_descarga_r2_autorizada(self):
        with self.simular_r2() as (
            cliente_r2, _
        ):
            respuesta = self.cliente.get(
                self.descargar
            )

            self.assertEqual(
                respuesta.status_code, 200
            )

            self.assertTrue(
                respuesta[
                    "Content-Disposition"
                ].startswith("attachment;")
            )

            self.assertEqual(
                b"".join(
                    respuesta.streaming_content
                ),
                b"audio-privado-simulado",
            )

            cliente_r2.get_object.assert_called_once()

    def test_usuario_sin_compra_no_escucha(self):
        visitante = (
            get_user_model().objects.create_user(
                username="visitante_sin_compra_r2"
            )
        )

        self.cliente.force_login(visitante)

        with self.simular_r2() as (
            cliente_r2, crear
        ):
            respuesta = self.cliente.get(
                self.escuchar
            )

            self.assertEqual(
                respuesta.status_code, 403
            )

            crear.assert_not_called()
            cliente_r2.get_object.assert_not_called()

    def test_usuario_sin_compra_no_descarga(self):
        visitante = (
            get_user_model().objects.create_user(
                username="visitante_sin_descarga_r2"
            )
        )

        self.cliente.force_login(visitante)

        with self.simular_r2() as (
            cliente_r2, crear
        ):
            respuesta = self.cliente.get(
                self.descargar
            )

            self.assertEqual(
                respuesta.status_code, 403
            )

            crear.assert_not_called()
            cliente_r2.get_object.assert_not_called()

    def test_descarga_anonima_rechazada(self):
        self.cliente.logout()

        with self.simular_r2() as (
            cliente_r2, crear
        ):
            respuesta = self.cliente.get(
                self.descargar
            )

            self.assertEqual(
                respuesta.status_code, 403
            )

            crear.assert_not_called()
            cliente_r2.get_object.assert_not_called()

    def test_cancion_processing_no_se_entrega(self):
        self.track.media_status = "processing"
        self.track.save(
            update_fields=["media_status"]
        )

        with self.simular_r2() as (
            cliente_r2, crear
        ):
            respuesta = self.cliente.get(
                self.escuchar
            )

            self.assertEqual(
                respuesta.status_code, 404
            )

            crear.assert_not_called()
            cliente_r2.get_object.assert_not_called()

    def test_clave_privada_ajena_no_se_entrega(self):
        self.track.r2_object_key = (
            "private/999999/track/"
            + ("a" * 32)
            + ".wav"
        )

        self.track.save(
            update_fields=["r2_object_key"]
        )

        with self.simular_r2() as (
            cliente_r2, _
        ):
            respuesta = self.cliente.get(
                self.escuchar
            )

            self.assertEqual(
                respuesta.status_code, 404
            )

            cliente_r2.get_object.assert_not_called()

    def test_reproduccion_con_rango(self):
        cliente_r2 = Mock()

        cliente_r2.get_object.return_value = {
            "Body": io.BytesIO(b"3456"),
            "ContentLength": 4,
            "ContentRange": "bytes 2-5/10",
        }

        with (
            patch(
                "app.r2_audio_bridge.r2_configuration",
                return_value={
                    "R2_BUCKET_NAME": "beatcloud-media"
                },
            ),
            patch(
                "app.r2_audio_bridge.r2_client",
                return_value=cliente_r2,
            ),
        ):
            respuesta = self.cliente.get(
                self.escuchar,
                HTTP_RANGE="bytes=2-5",
            )

            self.assertEqual(
                respuesta.status_code, 206
            )

            self.assertEqual(
                respuesta["Content-Range"],
                "bytes 2-5/10",
            )

            self.assertEqual(
                b"".join(
                    respuesta.streaming_content
                ),
                b"3456",
            )

            cliente_r2.get_object.assert_called_once_with(
                Bucket="beatcloud-media",
                Key=self.clave,
                Range="bytes=2-5",
            )

    def test_configuracion_r2_no_disponible(self):
        with (
            patch(
                "app.r2_audio_bridge.r2_configuration",
                side_effect=RuntimeError(
                    "Configuracion simulada ausente"
                ),
            ),
            patch(
                "app.r2_audio_bridge.r2_client"
            ) as crear,
        ):
            respuesta = self.cliente.get(
                self.escuchar
            )

            self.assertEqual(
                respuesta.status_code, 503
            )

            crear.assert_not_called()

    def test_cancion_local_sigue_funcionando(self):
        cancion_local = Track.objects.create(
            nombre_track="Cancion local de prueba",
            precio=1200,
            genero=self.genero,
            usuario=self.perfil,
            track="",
            storage_backend="local",
            media_status="ready",
        )

        cancion_local.track.save(
            "original-aislado.wav",
            ContentFile(b"audio-local-de-prueba"),
            save=True,
        )

        direccion = (
            f"/api/track/{cancion_local.pk}/reproducir/"
        )

        with patch(
            "app.r2_audio_bridge.r2_client"
        ) as crear:
            respuesta = self.cliente.get(
                direccion
            )

            self.assertEqual(
                respuesta.status_code, 200
            )

            self.assertEqual(
                b"".join(
                    respuesta.streaming_content
                ),
                b"audio-local-de-prueba",
            )

            crear.assert_not_called()
