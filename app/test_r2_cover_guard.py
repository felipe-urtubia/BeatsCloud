from django.core import signing
from django.test import SimpleTestCase

from app.r2_presign import TOKEN_SALT
from app.r2_registration_guard import (
    R2RegistrationGuardError,
    validate_r2_cover_token,
)


class R2CoverGuardTests(SimpleTestCase):

    def make_token(self, **changes):
        payload = {
            "owner": 23,
            "key": "pending/23/cover/" + "a" * 32 + ".jpg",
            "size": 500000,
            "kind": "cover",
            "mime": "image/jpeg",
            "filename": "portada.jpg",
        }

        payload.update(changes)

        return signing.dumps(
            payload,
            salt=TOKEN_SALT,
        )

    def test_accepts_all_supported_cover_formats(self):
        casos = (
            ("jpg", "image/jpeg"),
            ("jpeg", "image/jpeg"),
            ("png", "image/png"),
            ("webp", "image/webp"),
        )

        for extension, mime in casos:
            with self.subTest(extension=extension):
                filename = "portada." + extension

                token = self.make_token(
                    key=(
                        "pending/23/cover/"
                        + "a" * 32
                        + "." + extension
                    ),
                    filename=filename,
                    mime=mime,
                )

                resultado = validate_r2_cover_token(
                    upload_token=token,
                    user_id=23,
                )

                self.assertEqual(resultado.owner, 23)
                self.assertEqual(resultado.expected_mime, mime)
                self.assertEqual(resultado.original_filename, filename)

    def test_rejects_wrong_owner_kind_path_and_mime(self):
        casos = (
            {"owner": 24},
            {"kind": "track"},
            {"key": "../../secret.jpg"},
            {"mime": "image/png"},
        )

        for cambio in casos:
            with self.subTest(cambio=cambio):
                token = self.make_token(**cambio)

                with self.assertRaises(R2RegistrationGuardError):
                    validate_r2_cover_token(
                        upload_token=token,
                        user_id=23,
                    )

    def test_rejects_invalid_extension_and_size(self):
        casos = (
            {
                "key": "pending/23/cover/" + "a" * 32 + ".svg",
                "filename": "portada.svg",
                "mime": "image/svg+xml",
            },
            {"size": 10 * 1024 * 1024 + 1},
            {"size": True},
            {"size": 0},
        )

        for cambio in casos:
            with self.subTest(cambio=cambio):
                token = self.make_token(**cambio)

                with self.assertRaises(R2RegistrationGuardError):
                    validate_r2_cover_token(
                        upload_token=token,
                        user_id=23,
                    )

    def test_rejects_mismatched_original_filename(self):
        token = self.make_token(
            filename="otra.png",
        )

        with self.assertRaises(R2RegistrationGuardError):
            validate_r2_cover_token(
                upload_token=token,
                user_id=23,
            )
