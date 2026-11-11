import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock, patch

from django.core import signing

from app.r2_presign import ALLOWED, TOKEN_SALT
from app.r2_registration_guard import R2RegistrationGuardError
from app.r2_registration_prepare import (
    R2RegistrationPrepareError,
    prepare_r2_track_registration,
)


OWNER = 7
BUCKET = "bucket-ficticio"
PENDING = "pending/7/track/" + ("c" * 32) + ".wav"
PRIVATE = "private/7/track/" + ("d" * 32) + ".wav"
MIME = sorted(ALLOWED["track"][".wav"])[0]
SIZE = 16044


def token_ficticio():
    return signing.dumps(
        {
            "owner": OWNER,
            "key": PENDING,
            "size": SIZE,
            "kind": "track",
            "mime": MIME,
        },
        salt=TOKEN_SALT,
    )


def promocion_ficticia(**cambios):
    resultado = {
        "private_key": PRIVATE,
        "size": SIZE,
        "content_type": MIME,
        "kind": "track",
    }
    resultado.update(cambios)
    return resultado


@contextmanager
def preview_ficticia(**argumentos):
    with tempfile.TemporaryDirectory() as carpeta:
        archivo = Path(carpeta) / "preview.mp3"
        archivo.write_bytes(b"preview-simulada")
        yield archivo


@contextmanager
def preview_fallida(**argumentos):
    raise RuntimeError("Fallo simulado")
    yield


class R2RegistrationPrepareTests(unittest.TestCase):

    def setUp(self):
        self.cliente = Mock()
        self.token = token_ficticio()

    def ejecutar(self, **cambios):
        argumentos = {
            "client": self.cliente,
            "bucket": BUCKET,
            "user_id": OWNER,
            "upload_token": self.token,
        }
        argumentos.update(cambios)
        return prepare_r2_track_registration(**argumentos)

    def test_prepara_audio_y_preview(self):
        with (
            patch(
                "app.r2_registration_prepare.promote_pending_object",
                return_value=promocion_ficticia(),
            ) as promover,
            patch(
                "app.r2_registration_prepare.staged_r2_preview",
                side_effect=preview_ficticia,
            ) as generar,
        ):
            with self.ejecutar() as preparado:
                self.assertEqual(preparado.owner, OWNER)
                self.assertEqual(preparado.pending_key, PENDING)
                self.assertEqual(preparado.private_key, PRIVATE)
                self.assertTrue(preparado.preview_path.is_file())
                temporal = preparado.preview_path

            self.assertFalse(temporal.exists())
            promover.assert_called_once()
            generar.assert_called_once()
            self.cliente.delete_object.assert_not_called()

    def test_rechaza_token_invalido_antes_de_promover(self):
        with patch(
            "app.r2_registration_prepare.promote_pending_object"
        ) as promover:
            with self.assertRaises(R2RegistrationGuardError):
                with self.ejecutar(upload_token="token-invalido"):
                    pass

            promover.assert_not_called()

    def test_rechaza_otro_propietario(self):
        with patch(
            "app.r2_registration_prepare.promote_pending_object"
        ) as promover:
            with self.assertRaises(R2RegistrationGuardError):
                with self.ejecutar(user_id=8):
                    pass

            promover.assert_not_called()

    def test_error_preview_limpia_copia_privada(self):
        with (
            patch(
                "app.r2_registration_prepare.promote_pending_object",
                return_value=promocion_ficticia(),
            ),
            patch(
                "app.r2_registration_prepare.staged_r2_preview",
                side_effect=preview_fallida,
            ),
        ):
            with self.assertRaises(R2RegistrationPrepareError):
                with self.ejecutar():
                    pass

            self.cliente.delete_object.assert_called_once_with(
                Bucket=BUCKET,
                Key=PRIVATE,
            )

    def test_metadatos_incorrectos_limpian_copia(self):
        with patch(
            "app.r2_registration_prepare.promote_pending_object",
            return_value=promocion_ficticia(size=SIZE + 1),
        ):
            with self.assertRaises(R2RegistrationPrepareError):
                with self.ejecutar():
                    pass

            self.cliente.delete_object.assert_called_once_with(
                Bucket=BUCKET,
                Key=PRIVATE,
            )

    def test_no_elimina_copia_si_promocion_falla(self):
        with patch(
            "app.r2_registration_prepare.promote_pending_object",
            side_effect=RuntimeError("Fallo simulado"),
        ):
            with self.assertRaises(R2RegistrationPrepareError):
                with self.ejecutar():
                    pass

            self.cliente.delete_object.assert_not_called()


if __name__ == "__main__":
    unittest.main()
