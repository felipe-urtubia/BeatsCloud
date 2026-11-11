"""D8: contrato de campos y defaults seguros; sin acceso a R2 ni DB."""
from django.test import SimpleTestCase
from app.models import Track


class R2TrackFieldsTests(SimpleTestCase):
    def test_legacy_tracks_default_to_local_and_ready(self):
        track = Track()
        self.assertEqual(track.storage_backend, "local")
        self.assertEqual(track.media_status, "ready")
        self.assertEqual(track.r2_object_key, "")
        self.assertEqual(track.r2_stems_key, "")

    def test_r2_fields_are_optional(self):
        for field_name in ("r2_object_key", "r2_stems_key"):
            field = Track._meta.get_field(field_name)
            self.assertTrue(field.blank)
            self.assertEqual(field.max_length, 255)

    def test_only_defined_backend_and_status_choices(self):
        expected = {
            "storage_backend": {"local", "r2"},
            "media_status": {"pending", "processing", "ready", "failed"},
        }
        for field_name, values in expected.items():
            with self.subTest(field=field_name):
                field = Track._meta.get_field(field_name)
                self.assertEqual({value for value, _ in field.choices}, values)
