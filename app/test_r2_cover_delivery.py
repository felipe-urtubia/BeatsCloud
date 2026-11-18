import io
from types import SimpleNamespace
from unittest.mock import Mock

from botocore.exceptions import ClientError
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase

from app.r2_cover_delivery import (
    authorized_r2_cover_response,
    is_owned_r2_cover_key,
)


class R2CoverDeliveryTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.key = (
            "private/11/cover/"
            + ("a" * 32)
            + ".png"
        )
        self.track = SimpleNamespace(
            media_status="ready",
            r2_cover_key=self.key,
            usuario=SimpleNamespace(user_id=11),
        )
        self.request = self.factory.get("/api/track/9/cover/")
        self.payload = b"\x89PNG\r\n\x1a\ncover"
        self.body = io.BytesIO(self.payload)
        self.client = Mock()
        self.client.get_object.return_value = {
            "Body": self.body,
            "ContentLength": len(self.payload),
            "ContentType": "image/png",
        }

    def entregar(self, request=None, track=None):
        return authorized_r2_cover_response(
            request or self.request,
            track or self.track,
            client=self.client,
            bucket="beatcloud-media",
        )

    def test_clave_de_portada_debe_pertenecer_al_usuario(self):
        self.assertTrue(is_owned_r2_cover_key(11, self.key))
        self.assertFalse(is_owned_r2_cover_key(12, self.key))
        self.assertFalse(is_owned_r2_cover_key(11, "../cover.png"))

    def test_entrega_portada_privada_sin_url_publica(self):
        response = self.entregar()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(response["Content-Length"], str(len(self.payload)))
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(
            b"".join(response.streaming_content),
            self.payload,
        )
        self.assertTrue(self.body.closed)
        self.client.get_object.assert_called_once_with(
            Bucket="beatcloud-media",
            Key=self.key,
        )

    def test_metodo_distinto_de_get_no_permitido(self):
        request = self.factory.post("/api/track/9/cover/")
        response = self.entregar(request=request)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "GET")
        self.client.get_object.assert_not_called()

    def test_track_no_listo_no_consulta_r2(self):
        self.track.media_status = "processing"

        with self.assertRaises(Http404):
            self.entregar()

        self.client.get_object.assert_not_called()

    def test_clave_de_otro_usuario_no_consulta_r2(self):
        self.track.r2_cover_key = (
            "private/99/cover/"
            + ("b" * 32)
            + ".png"
        )

        with self.assertRaises(Http404):
            self.entregar()

        self.client.get_object.assert_not_called()

    def test_portada_inexistente_devuelve_404(self):
        self.client.get_object.side_effect = ClientError(
            {
                "Error": {
                    "Code": "NoSuchKey",
                    "Message": "No encontrada",
                }
            },
            "GetObject",
        )

        with self.assertRaises(Http404):
            self.entregar()
