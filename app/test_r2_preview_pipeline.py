from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError
from django.http import Http404
from django.test import SimpleTestCase

from app.r2_preview_storage import (
    R2PreviewStorageError,
    upload_r2_preview,
)
from app.r2_preview_delivery import r2_preview_response


KEY = "previews/r2-" + "a" * 32 + ".mp3"


class R2PreviewPipelineTests(SimpleTestCase):

    def test_upload_preview(self):
        client = Mock()
        client.head_object.return_value = {
            "ContentLength": 4,
        }

        with TemporaryDirectory() as folder:
            archivo = Path(folder) / "preview.mp3"
            archivo.write_bytes(b"test")

            resultado = upload_r2_preview(
                client=client,
                bucket="bucket-prueba",
                preview_path=archivo,
                key=KEY,
            )

        self.assertEqual(resultado, KEY)
        client.put_object.assert_called_once()
        client.head_object.assert_called_once_with(
            Bucket="bucket-prueba",
            Key=KEY,
        )

    def test_rechaza_clave_privada(self):
        client = Mock()

        with TemporaryDirectory() as folder:
            archivo = Path(folder) / "preview.mp3"
            archivo.write_bytes(b"test")

            with self.assertRaises(R2PreviewStorageError):
                upload_r2_preview(
                    client=client,
                    bucket="bucket-prueba",
                    preview_path=archivo,
                    key="private/1/track/original.wav",
                )

        client.put_object.assert_not_called()

    def test_rechaza_tamano_incorrecto(self):
        client = Mock()
        client.head_object.return_value = {
            "ContentLength": 999,
        }

        with TemporaryDirectory() as folder:
            archivo = Path(folder) / "preview.mp3"
            archivo.write_bytes(b"test")

            with self.assertRaises(R2PreviewStorageError):
                upload_r2_preview(
                    client=client,
                    bucket="bucket-prueba",
                    preview_path=archivo,
                    key=KEY,
                )

    def test_redireccion_firmada(self):
        client = Mock()
        client.head_object.return_value = {
            "ContentLength": 1024,
        }
        client.generate_presigned_url.return_value = (
            "https://example.com/preview.mp3"
        )

        track = SimpleNamespace(
            preview=SimpleNamespace(name=KEY),
        )

        with patch(
            "app.r2_preview_delivery.r2_configuration",
            return_value={"R2_BUCKET_NAME": "bucket-prueba"},
        ), patch(
            "app.r2_preview_delivery.r2_client",
            return_value=client,
        ):
            response = r2_preview_response(track)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            "https://example.com/preview.mp3",
        )
        self.assertEqual(
            response["Cache-Control"],
            "no-store",
        )
        client.generate_presigned_url.assert_called_once()

        argumentos = client.generate_presigned_url.call_args
        self.assertEqual(argumentos.args[0], "get_object")
        self.assertEqual(
            argumentos.kwargs["Params"]["Key"],
            KEY,
        )

    def test_no_entrega_original_privado(self):
        track = SimpleNamespace(
            preview=SimpleNamespace(
                name="private/1/track/original.wav",
            ),
        )

        with self.assertRaises(Http404):
            r2_preview_response(track)

    def test_preview_inexistente_devuelve_404(self):
        client = Mock()
        client.head_object.side_effect = ClientError(
            {
                "Error": {
                    "Code": "404",
                    "Message": "Not Found",
                }
            },
            "HeadObject",
        )

        track = SimpleNamespace(
            preview=SimpleNamespace(name=KEY),
        )

        with patch(
            "app.r2_preview_delivery.r2_configuration",
            return_value={"R2_BUCKET_NAME": "bucket-prueba"},
        ), patch(
            "app.r2_preview_delivery.r2_client",
            return_value=client,
        ):
            with self.assertRaises(Http404):
                r2_preview_response(track)

    def test_configuracion_no_disponible(self):
        track = SimpleNamespace(
            preview=SimpleNamespace(name=KEY),
        )

        with patch(
            "app.r2_preview_delivery.r2_configuration",
            return_value=None,
        ):
            response = r2_preview_response(track)

        self.assertEqual(response.status_code, 503)
