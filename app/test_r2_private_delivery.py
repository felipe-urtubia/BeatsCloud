import io
from types import SimpleNamespace
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase

from app.r2_private_delivery import (
    authorized_r2_audio_response,
)


class R2PrivateDeliveryTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.usuario = SimpleNamespace(
            is_authenticated=True,
            pk=22,
        )

        self.clave = (
            "private/11/track/"
            + ("a" * 32)
            + ".wav"
        )

        self.track = SimpleNamespace(
            pk=9,
            media_status="ready",
            storage_backend="r2",
            r2_object_key=self.clave,
            usuario=SimpleNamespace(user_id=11),
        )

        self.request = self.factory.get(
            "/api/track/9/reproducir/"
        )

        self.request.user = self.usuario

        self.cuerpo = io.BytesIO(b"audio-simulado")

        self.client = Mock()
        self.client.get_object.return_value = {
            "Body": self.cuerpo,
            "ContentLength": len(b"audio-simulado"),
        }

    def entregar(self, **cambios):
        datos = {
            "client": self.client,
            "bucket": "beatcloud-media",
        }

        datos.update(cambios)

        return authorized_r2_audio_response(
            self.request,
            self.track,
            **datos,
        )

    @patch(
        "app.api_shim._puede_escuchar_completo",
        return_value=True,
    )
    def test_audio_autorizado_entregado(self, autorizar):
        respuesta = self.entregar()

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            b"".join(respuesta.streaming_content),
            b"audio-simulado",
        )

        self.assertTrue(self.cuerpo.closed)
        self.assertEqual(
            respuesta["Cache-Control"],
            "private, no-store",
        )

        self.assertEqual(
            respuesta["Accept-Ranges"],
            "bytes",
        )

        self.client.get_object.assert_called_once_with(
            Bucket="beatcloud-media",
            Key=self.clave,
        )

        autorizar.assert_called_once()

    @patch(
        "app.api_shim._puede_escuchar_completo",
        return_value=False,
    )
    def test_sin_compra_no_consulta_r2(self, autorizar):
        respuesta = self.entregar()

        self.assertEqual(respuesta.status_code, 403)
        self.client.get_object.assert_not_called()

    @patch(
        "app.api_shim._puede_escuchar_completo"
    )
    def test_track_no_publicado_rechazado(self, autorizar):
        self.track.media_status = "processing"

        with self.assertRaises(Http404):
            self.entregar()

        autorizar.assert_not_called()
        self.client.get_object.assert_not_called()

    @patch(
        "app.api_shim._puede_escuchar_completo"
    )
    def test_cancion_local_no_consulta_r2(self, autorizar):
        self.track.storage_backend = "local"

        with self.assertRaises(Http404):
            self.entregar()

        autorizar.assert_not_called()
        self.client.get_object.assert_not_called()

    @patch(
        "app.api_shim._puede_escuchar_completo",
        return_value=True,
    )
    def test_clave_de_otro_productor_rechazada(self, _):
        self.track.r2_object_key = (
            "private/99/track/"
            + ("a" * 32)
            + ".wav"
        )

        with self.assertRaises(Http404):
            self.entregar()

        self.client.get_object.assert_not_called()

    @patch(
        "app.api_shim._puede_escuchar_completo",
        return_value=True,
    )
    def test_descarga_autorizada(self, _):
        respuesta = self.entregar(
            as_attachment=True
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertTrue(
            respuesta["Content-Disposition"].startswith(
                "attachment;"
            )
        )

        respuesta.close()

    @patch(
        "app.api_shim._puede_escuchar_completo"
    )
    def test_descarga_anonima_rechazada(self, autorizar):
        self.request.user = SimpleNamespace(
            is_authenticated=False,
        )

        respuesta = self.entregar(
            as_attachment=True
        )

        self.assertEqual(respuesta.status_code, 403)
        autorizar.assert_not_called()
        self.client.get_object.assert_not_called()

    @patch(
        "app.api_shim._puede_escuchar_completo",
        return_value=True,
    )
    def test_rango_parcial_valido(self, _):
        self.request = self.factory.get(
            "/api/track/9/reproducir/",
            HTTP_RANGE="bytes=2-5",
        )

        self.request.user = self.usuario

        self.client.get_object.return_value = {
            "Body": io.BytesIO(b"3456"),
            "ContentLength": 4,
            "ContentRange": "bytes 2-5/10",
        }

        respuesta = self.entregar()

        self.assertEqual(respuesta.status_code, 206)

        self.assertEqual(
            respuesta["Content-Range"],
            "bytes 2-5/10",
        )

        self.assertEqual(
            b"".join(respuesta.streaming_content),
            b"3456",
        )

        self.client.get_object.assert_called_once_with(
            Bucket="beatcloud-media",
            Key=self.clave,
            Range="bytes=2-5",
        )

    @patch(
        "app.api_shim._puede_escuchar_completo",
        return_value=True,
    )
    def test_rango_invalido_no_consulta_r2(self, _):
        self.request = self.factory.get(
            "/api/track/9/reproducir/",
            HTTP_RANGE="bytes=9-2",
        )

        self.request.user = self.usuario

        respuesta = self.entregar()

        self.assertEqual(respuesta.status_code, 416)
        self.client.get_object.assert_not_called()

    @patch(
        "app.api_shim._puede_escuchar_completo",
        return_value=True,
    )
    def test_objeto_inexistente_devuelve_404(self, _):
        self.client.get_object.side_effect = ClientError(
            {
                "Error": {
                    "Code": "NoSuchKey",
                    "Message": "No encontrado",
                }
            },
            "GetObject",
        )

        with self.assertRaises(Http404):
            self.entregar()

    @patch(
        "app.api_shim._puede_escuchar_completo",
        return_value=True,
    )
    def test_rango_no_confirmado_se_rechaza(self, _):
        self.request = self.factory.get(
            "/api/track/9/reproducir/",
            HTTP_RANGE="bytes=0-3",
        )

        self.request.user = self.usuario

        cuerpo = io.BytesIO(b"1234")

        self.client.get_object.return_value = {
            "Body": cuerpo,
            "ContentLength": 4,
        }

        with self.assertRaises(RuntimeError):
            self.entregar()

        self.assertTrue(cuerpo.closed)
