from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django.test import RequestFactory, SimpleTestCase

from .api_shim import full_stream_api
from .track_audio_range import serve_local_track_audio


class LocalAudioRangeTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.payload = b"0123456789"

    def audio_response(self, range_header=None):
        headers = {}

        if range_header is not None:
            headers["HTTP_RANGE"] = range_header

        request = self.factory.get(
            "/api/track/3/reproducir/",
            **headers,
        )

        track = SimpleNamespace(
            track=ContentFile(
                self.payload,
                name="test_track.mp3",
            )
        )

        return serve_local_track_audio(request, track)

    def assert_audio(self, requested_range, expected, status=206):
        response = self.audio_response(requested_range)

        try:
            self.assertEqual(response.status_code, status)
            self.assertEqual(
                b"".join(response.streaming_content),
                expected,
            )
            self.assertEqual(
                response["Content-Length"],
                str(len(expected)),
            )
            self.assertEqual(
                response["Accept-Ranges"],
                "bytes",
            )
            self.assertEqual(
                response["Cache-Control"],
                "private, no-store",
            )
        finally:
            response.close()

    def test_complete_audio_without_range(self):
        self.assert_audio(None, self.payload, status=200)

    def test_explicit_byte_range(self):
        response = self.audio_response("bytes=2-5")

        try:
            self.assertEqual(response.status_code, 206)
            self.assertEqual(
                response["Content-Range"],
                "bytes 2-5/10",
            )
            self.assertEqual(
                b"".join(response.streaming_content),
                b"2345",
            )
        finally:
            response.close()

    def test_open_ended_range(self):
        self.assert_audio("bytes=7-", b"789")

    def test_suffix_range(self):
        self.assert_audio("bytes=-4", b"6789")

    def test_last_byte(self):
        self.assert_audio("bytes=9-9", b"9")

    def test_range_cannot_exceed_file(self):
        self.assert_audio("bytes=8-100", b"89")

    def test_out_of_bounds_returns_416(self):
        response = self.audio_response("bytes=100-")

        self.assertEqual(response.status_code, 416)
        self.assertEqual(
            response["Content-Range"],
            "bytes */10",
        )

    def test_malformed_range_returns_416(self):
        for header in (
            "bytes=5-2",
            "bytes=-0",
            "bytes=abc-def",
            "bytes=0-1,4-5",
        ):
            with self.subTest(header=header):
                response = self.audio_response(header)
                self.assertEqual(response.status_code, 416)

    def test_unauthorized_range_is_blocked(self):
        request = self.factory.get(
            "/api/track/3/reproducir/",
            HTTP_RANGE="bytes=2-5",
        )
        request.user = AnonymousUser()

        track = SimpleNamespace(
            track=ContentFile(
                self.payload,
                name="test_track.mp3",
            ),
            storage_backend="local",
        )

        with (
            patch(
                "app.api_shim.Track.objects.filter"
            ) as lookup,
            patch(
                "app.r2_visibility.is_media_ready",
                return_value=True,
            ),
            patch(
                "app.api_shim._puede_escuchar_completo",
                return_value=False,
            ),
        ):
            lookup.return_value.first.return_value = track

            response = full_stream_api(request, 3)

            self.assertEqual(response.status_code, 403)
