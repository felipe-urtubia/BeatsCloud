"""Pruebas unitarias de promocion R2; cliente simulado y ninguna red."""
from unittest.mock import Mock

from django.test import SimpleTestCase

from app.r2_promotion import R2PromotionError, promote_pending_object


class R2PromotionTests(SimpleTestCase):
    def setUp(self):
        self.client = Mock()
        self.owner = 23
        self.pending = f"pending/{self.owner}/track/" + "a" * 32 + ".wav"
        self.source = {
            "ContentLength": 12345,
            "ContentType": "audio/wav",
            "ETag": '"etag-source"',
        }
        self.destination = {
            "ContentLength": 12345,
            "ContentType": "audio/wav",
            "ETag": '"etag-private"',
        }
        self.client.head_object.side_effect = [self.source, self.destination]
        self.kwargs = dict(
            client=self.client, bucket="test-bucket", owner=self.owner,
            kind="track", pending_key=self.pending,
            expected_size=12345, expected_mime="audio/wav",
        )

    def test_copy_uses_source_etag_and_new_private_key(self):
        result = promote_pending_object(**self.kwargs)
        self.assertRegex(result["private_key"], r"^private/23/track/[a-f0-9]{32}\.wav$")
        self.assertNotEqual(result["private_key"], self.pending)
        self.client.copy_object.assert_called_once_with(
            Bucket="test-bucket", Key=result["private_key"],
            CopySource={"Bucket": "test-bucket", "Key": self.pending},
            CopySourceIfMatch='"etag-source"', MetadataDirective="COPY",
        )
        self.assertEqual(self.client.head_object.call_count, 2)
        self.client.delete_object.assert_not_called()

    def test_wrong_owner_and_path_rejected_before_r2(self):
        for change in (
            {"owner": 24},
            {"pending_key": "../../secret.wav"},
            {"pending_key": "private/23/track/" + "a" * 32 + ".wav"},
            {"kind": "stems"},
        ):
            with self.subTest(change=change):
                with self.assertRaises(R2PromotionError):
                    promote_pending_object(**{**self.kwargs, **change})
        self.client.head_object.assert_not_called()
        self.client.copy_object.assert_not_called()

    def test_wrong_size_or_mime_prevents_copy(self):
        for changed in (
            {"ContentLength": 12346, "ContentType": "audio/wav", "ETag": '"tag"'},
            {"ContentLength": 12345, "ContentType": "audio/mpeg", "ETag": '"tag"'},
        ):
            with self.subTest(changed=changed):
                client = Mock()
                client.head_object.return_value = changed
                with self.assertRaises(R2PromotionError):
                    promote_pending_object(**{**self.kwargs, "client": client})
                client.copy_object.assert_not_called()

    def test_missing_source_etag_prevents_copy(self):
        self.client.head_object.side_effect = None
        self.client.head_object.return_value = {
            "ContentLength": 12345, "ContentType": "audio/wav"
        }
        with self.assertRaises(R2PromotionError):
            promote_pending_object(**self.kwargs)
        self.client.copy_object.assert_not_called()

    def test_copy_failure_is_not_success(self):
        self.client.copy_object.side_effect = RuntimeError("PreconditionFailed")
        with self.assertRaises(R2PromotionError):
            promote_pending_object(**self.kwargs)
        self.assertEqual(self.client.head_object.call_count, 1)

    def test_private_head_size_mismatch_is_not_success(self):
        self.client.head_object.side_effect = [
            self.source,
            {"ContentLength": 99, "ContentType": "audio/wav", "ETag": '"private"'},
        ]
        with self.assertRaises(R2PromotionError):
            promote_pending_object(**self.kwargs)
        self.client.copy_object.assert_called_once()
        self.client.delete_object.assert_not_called()

    def test_stems_zip_supported(self):
        client = Mock()
        client.head_object.side_effect = [
            {"ContentLength": 100, "ContentType": "application/zip", "ETag": '"one"'},
            {"ContentLength": 100, "ContentType": "application/zip", "ETag": '"two"'},
        ]
        result = promote_pending_object(
            client=client, bucket="test-bucket", owner=self.owner,
            kind="stems", pending_key=f"pending/{self.owner}/stems/" + "b" * 32 + ".zip",
            expected_size=100, expected_mime="application/zip",
        )
        self.assertRegex(result["private_key"], r"^private/23/stems/[a-f0-9]{32}\.zip$")

    def test_invalid_declared_values_prevent_cloud_calls(self):
        for change in (
            {"expected_size": True},
            {"expected_size": 0},
            {"expected_mime": "application/octet-stream"},
            {"owner": False},
        ):
            with self.subTest(change=change):
                with self.assertRaises(R2PromotionError):
                    promote_pending_object(**{**self.kwargs, **change})
        self.client.head_object.assert_not_called()
