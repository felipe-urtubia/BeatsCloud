from unittest.mock import Mock, patch

from django.core import signing
from django.test import SimpleTestCase

from app.r2_presign import TOKEN_SALT
from app.r2_registration_guard import R2RegistrationGuardError
from app.r2_registration_prepare import (
    R2CoverDraft,
    R2RegistrationPrepareError,
    prepare_r2_cover_upload,
)


class R2CoverPrepareTests(SimpleTestCase):

    def make_token(self, extension="jpg", mime="image/jpeg", **changes):
        payload = {
            "owner": 23,
            "key": (
                "pending/23/cover/"
                + "a" * 32
                + "." + extension
            ),
            "size": 500000,
            "kind": "cover",
            "mime": mime,
            "filename": "portada." + extension,
        }

        payload.update(changes)

        return signing.dumps(
            payload,
            salt=TOKEN_SALT,
        )

    def test_promotes_all_supported_cover_formats(self):
        casos = (
            ("jpg", "image/jpeg"),
            ("jpeg", "image/jpeg"),
            ("png", "image/png"),
            ("webp", "image/webp"),
        )

        for extension, mime in casos:
            with self.subTest(extension=extension):
                client = Mock()

                private_key = (
                    "private/23/cover/"
                    + "d" * 32
                    + "." + extension
                )

                with patch(
                    "app.r2_registration_prepare.promote_pending_object",
                    return_value={
                        "private_key": private_key,
                        "size": 500000,
                        "content_type": mime,
                        "kind": "cover",
                    },
                ) as promote:

                    resultado = prepare_r2_cover_upload(
                        client=client,
                        bucket="test-bucket",
                        user_id=23,
                        upload_token=self.make_token(
                            extension=extension,
                            mime=mime,
                        ),
                    )

                self.assertIsInstance(resultado, R2CoverDraft)
                self.assertEqual(resultado.owner, 23)
                self.assertEqual(resultado.private_key, private_key)
                self.assertEqual(resultado.expected_mime, mime)

                promote.assert_called_once_with(
                    client=client,
                    bucket="test-bucket",
                    owner=23,
                    kind="cover",
                    pending_key=(
                        "pending/23/cover/"
                        + "a" * 32
                        + "." + extension
                    ),
                    expected_size=500000,
                    expected_mime=mime,
                )

    def test_wrong_owner_does_not_call_cloud(self):
        token = self.make_token(owner=24)

        with patch(
            "app.r2_registration_prepare.promote_pending_object"
        ) as promote:

            with self.assertRaises(R2RegistrationGuardError):
                prepare_r2_cover_upload(
                    client=Mock(),
                    bucket="test-bucket",
                    user_id=23,
                    upload_token=token,
                )

            promote.assert_not_called()

    def test_invalid_metadata_deletes_private_copy(self):
        client = Mock()

        private_key = (
            "private/23/cover/"
            + "d" * 32
            + ".jpg"
        )

        with patch(
            "app.r2_registration_prepare.promote_pending_object",
            return_value={
                "private_key": private_key,
                "size": 500000,
                "content_type": "image/png",
                "kind": "cover",
            },
        ):

            with self.assertRaises(R2RegistrationPrepareError):
                prepare_r2_cover_upload(
                    client=client,
                    bucket="test-bucket",
                    user_id=23,
                    upload_token=self.make_token(),
                )

        client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=private_key,
        )

    def test_invalid_private_path_is_rejected(self):
        client = Mock()

        with patch(
            "app.r2_registration_prepare.promote_pending_object",
            return_value={
                "private_key": "private/24/cover/invalid.jpg",
                "size": 500000,
                "content_type": "image/jpeg",
                "kind": "cover",
            },
        ):

            with self.assertRaises(R2RegistrationPrepareError):
                prepare_r2_cover_upload(
                    client=client,
                    bucket="test-bucket",
                    user_id=23,
                    upload_token=self.make_token(),
                )

        client.delete_object.assert_not_called()

    def test_promotion_failure_is_controlled(self):
        with patch(
            "app.r2_registration_prepare.promote_pending_object",
            side_effect=RuntimeError("simulated"),
        ):

            with self.assertRaises(R2RegistrationPrepareError):
                prepare_r2_cover_upload(
                    client=Mock(),
                    bucket="test-bucket",
                    user_id=23,
                    upload_token=self.make_token(),
                )

    def test_invalid_bucket_is_rejected_before_cloud(self):
        with patch(
            "app.r2_registration_prepare.promote_pending_object"
        ) as promote:

            with self.assertRaises(R2RegistrationPrepareError):
                prepare_r2_cover_upload(
                    client=Mock(),
                    bucket="",
                    user_id=23,
                    upload_token=self.make_token(),
                )

            promote.assert_not_called()
