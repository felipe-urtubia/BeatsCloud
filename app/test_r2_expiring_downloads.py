import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase

from app.r2_private_delivery import authorized_r2_audio_download_response


class R2ExpiringDownloadTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.usuario = SimpleNamespace(is_authenticated=True, id=22)
        self.clave = "private/11/track/" + ("a" * 32) + ".wav"
        self.track = SimpleNamespace(
            media_status="ready",
            storage_backend="r2",
            r2_object_key=self.clave,
            original_filename="BeatCloud prueba.wav",
            usuario=SimpleNamespace(user_id=11),
        )
        self.request = self.factory.get("/api/track/9/descargar/")
        self.request.user = self.usuario
        self.client = Mock()
        self.client.head_object.return_value = {"ContentLength": 1234}
        self.client.generate_presigned_url.return_value = (
            "https://abc123.r2.cloudflarestorage.com/"
            "beatcloud-media/audio.wav?X-Amz-Expires=300"
        )

    def emitir(self):
        return authorized_r2_audio_download_response(
            self.request,
            self.track,
            client=self.client,
            bucket="beatcloud-media",
        )

    @patch("app.api_shim._puede_escuchar_completo", return_value=True)
    def test_autorizado_recibe_url_get_de_300_segundos(self, _):
        respuesta = self.emitir()
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Cache-Control"], "private, no-store")
        self.assertEqual(respuesta["X-Content-Type-Options"], "nosniff")

        payload = json.loads(respuesta.content)
        self.assertEqual(payload["method"], "GET")
        self.assertEqual(payload["expires_in"], 300)
        self.assertEqual(payload["filename"], "BeatCloud prueba.wav")
        self.assertTrue(payload["url"].startswith("https://"))

        self.client.head_object.assert_called_once_with(
            Bucket="beatcloud-media", Key=self.clave
        )
        llamada = self.client.generate_presigned_url.call_args
        self.assertEqual(llamada.args[0], "get_object")
        self.assertEqual(llamada.kwargs["ExpiresIn"], 300)
        self.assertEqual(llamada.kwargs["HttpMethod"], "GET")
        self.assertEqual(llamada.kwargs["Params"]["Bucket"], "beatcloud-media")
        self.assertEqual(llamada.kwargs["Params"]["Key"], self.clave)
        self.assertIn(
            "attachment",
            llamada.kwargs["Params"]["ResponseContentDisposition"],
        )
        self.assertEqual(
            llamada.kwargs["Params"]["ResponseCacheControl"],
            "private, no-store",
        )

    @patch("app.api_shim._puede_escuchar_completo", return_value=False)
    def test_no_autorizado_recibe_403_sin_consultar_r2(self, autorizar):
        respuesta = self.emitir()
        self.assertEqual(respuesta.status_code, 403)
        autorizar.assert_called_once()
        self.client.head_object.assert_not_called()
        self.client.generate_presigned_url.assert_not_called()

    @patch("app.api_shim._puede_escuchar_completo")
    def test_anonimo_recibe_403_sin_consultar_r2(self, autorizar):
        self.request.user = SimpleNamespace(is_authenticated=False)
        respuesta = self.emitir()
        self.assertEqual(respuesta.status_code, 403)
        autorizar.assert_not_called()
        self.client.head_object.assert_not_called()
        self.client.generate_presigned_url.assert_not_called()

    @patch("app.api_shim._puede_escuchar_completo", return_value=True)
    def test_clave_de_otro_propietario_rechazada(self, _):
        self.track.r2_object_key = "private/99/track/" + ("a" * 32) + ".wav"
        with self.assertRaises(Http404):
            self.emitir()
        self.client.head_object.assert_not_called()
        self.client.generate_presigned_url.assert_not_called()

    @patch("app.api_shim._puede_escuchar_completo", return_value=True)
    def test_objeto_inexistente_devuelve_404(self, _):
        self.client.head_object.side_effect = ClientError(
            {
                "Error": {"Code": "NoSuchKey", "Message": "No encontrado"},
                "ResponseMetadata": {"HTTPStatusCode": 404},
            },
            "HeadObject",
        )
        with self.assertRaises(Http404):
            self.emitir()
        self.client.generate_presigned_url.assert_not_called()

    @patch("app.api_shim._puede_escuchar_completo")
    def test_metodo_distinto_de_get_devuelve_405(self, autorizar):
        self.request = self.factory.post("/api/track/9/descargar/")
        self.request.user = self.usuario
        respuesta = self.emitir()
        self.assertEqual(respuesta.status_code, 405)
        autorizar.assert_not_called()
        self.client.head_object.assert_not_called()

    @patch("app.api_shim._puede_escuchar_completo")
    def test_track_no_listo_devuelve_404(self, autorizar):
        self.track.media_status = "processing"
        with self.assertRaises(Http404):
            self.emitir()
        autorizar.assert_not_called()
        self.client.head_object.assert_not_called()
