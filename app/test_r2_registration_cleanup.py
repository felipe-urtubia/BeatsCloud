import unittest
from unittest.mock import Mock, patch

from app.r2_registration_prepare import (
    R2RegistrationPrepareError,
    prepare_r2_track_registration,
)
from app.test_r2_registration_prepare import (
    OWNER,
    BUCKET,
    PRIVATE,
    token_ficticio,
    promocion_ficticia,
    preview_ficticia,
    preview_fallida,
)


class R2RegistrationCleanupTests(unittest.TestCase):

    def preparar(self, cliente):
        return prepare_r2_track_registration(
            client=cliente,
            bucket=BUCKET,
            user_id=OWNER,
            upload_token=token_ficticio(),
        )

    def test_fallo_posterior_preserva_copia_privada(self):
        cliente = Mock()

        with (
            patch(
                "app.r2_registration_prepare.promote_pending_object",
                return_value=promocion_ficticia(),
            ),
            patch(
                "app.r2_registration_prepare.staged_r2_preview",
                side_effect=preview_ficticia,
            ),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Registro simulado fallido",
            ):
                with self.preparar(cliente) as preparado:
                    self.assertTrue(
                        preparado.preview_path.is_file()
                    )
                    temporal = preparado.preview_path
                    raise RuntimeError(
                        "Registro simulado fallido"
                    )

        self.assertFalse(temporal.exists())
        cliente.delete_object.assert_not_called()

    def test_fallo_preparacion_elimina_copia_privada(self):
        cliente = Mock()

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
            with self.assertRaises(
                R2RegistrationPrepareError
            ):
                with self.preparar(cliente):
                    pass

        cliente.delete_object.assert_called_once_with(
            Bucket=BUCKET,
            Key=PRIVATE,
        )
