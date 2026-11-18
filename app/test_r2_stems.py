from django.core import signing
from django.test import SimpleTestCase

from app.r2_presign import TOKEN_SALT, MAX_BYTES
from app.r2_registration_guard import (
    R2RegistrationGuardError,
    validate_r2_stems_token,
)


class R2StemsTokenTests(SimpleTestCase):
    def token(self, **changes):
        payload = {
            "owner": 23,
            "key": "pending/23/stems/" + "a" * 32 + ".zip",
            "size": 1024,
            "kind": "stems",
            "mime": "application/zip",
            "filename": "pista_stems.zip",
        }
        payload.update(changes)
        return signing.dumps(payload, salt=TOKEN_SALT)

    def test_acepta_token_stems_valido(self):
        result = validate_r2_stems_token(
            upload_token=self.token(), user_id=23
        )
        self.assertEqual(result.owner, 23)
        self.assertEqual(result.expected_size, 1024)
        self.assertEqual(result.expected_mime, "application/zip")
        self.assertEqual(result.original_filename, "pista_stems.zip")

    def test_rechaza_otro_propietario(self):
        with self.assertRaises(R2RegistrationGuardError):
            validate_r2_stems_token(upload_token=self.token(), user_id=24)

    def test_rechaza_tipo_que_no_es_stems(self):
        with self.assertRaises(R2RegistrationGuardError):
            validate_r2_stems_token(
                upload_token=self.token(kind="track"), user_id=23
            )

    def test_rechaza_extension_no_permitida(self):
        with self.assertRaises(R2RegistrationGuardError):
            validate_r2_stems_token(
                upload_token=self.token(
                    key="pending/23/stems/" + "b" * 32 + ".exe",
                    filename="pista_stems.exe",
                    mime="application/zip",
                ),
                user_id=23,
            )

    def test_rechaza_archivo_mayor_al_limite(self):
        with self.assertRaises(R2RegistrationGuardError):
            validate_r2_stems_token(
                upload_token=self.token(size=MAX_BYTES["stems"] + 1),
                user_id=23,
            )
