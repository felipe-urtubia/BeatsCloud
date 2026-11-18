"""Compatibility tests: FFmpeg is mocked, R2 and the actual database are not used."""
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from app.audio_utils import generar_preview_audio


class FakePreview:
    def __init__(self):
        self.name = ""
        self.data = None
        self.saved = False

    def save(self, name, stream, save=False):
        self.name = name
        self.data = stream.read()
        self.saved = save


class FakeRemoteTrackFile:
    name = "cloud/original.wav"

    @property
    def path(self):
        raise NotImplementedError("R2 no proporciona una ruta local")

    def open(self, mode):
        assert mode == "rb"
        return io.BytesIO(b"REMOTE_AUDIO_TEST")


class FakeLocalTrackFile:
    name = "canciones/local.wav"

    def __init__(self, path):
        self.path = str(path)

    def open(self, mode):
        raise AssertionError("Un archivo local no debe volver a copiarse")


class PreviewStorageTests(SimpleTestCase):
    def fake_ffmpeg(self, observed):
        def runner(command, **kwargs):
            source = command[command.index("-i") + 1]
            observed["source"] = str(source)
            observed["bytes"] = Path(source).read_bytes()
            observed["duration"] = command[command.index("-t") + 1]
            Path(command[-1]).write_bytes(b"FAKE_PREVIEW_MP3")
            return SimpleNamespace(returncode=0, stderr="")
        return runner

    def test_remote_storage_creates_30s_preview_without_path(self):
        observed = {}
        track = SimpleNamespace(pk=51, track=FakeRemoteTrackFile(), preview=FakePreview())
        with patch("app.audio_utils.subprocess.run", side_effect=self.fake_ffmpeg(observed)):
            preview = generar_preview_audio(track)
        self.assertIs(preview, track.preview)
        self.assertEqual(observed["bytes"], b"REMOTE_AUDIO_TEST")
        self.assertEqual(observed["duration"], "30")
        self.assertEqual(track.preview.data, b"FAKE_PREVIEW_MP3")
        self.assertEqual(track.preview.name, "track_51_preview.mp3")
        self.assertTrue(track.preview.saved)

    def test_local_storage_preserves_existing_path(self):
        observed = {}
        with TemporaryDirectory() as directory:
            path = Path(directory) / "local.wav"
            path.write_bytes(b"LOCAL_AUDIO_TEST")
            track = SimpleNamespace(pk=52, track=FakeLocalTrackFile(path), preview=FakePreview())
            with patch("app.audio_utils.subprocess.run", side_effect=self.fake_ffmpeg(observed)):
                generar_preview_audio(track)
            self.assertEqual(observed["source"], str(path))
            self.assertEqual(observed["bytes"], b"LOCAL_AUDIO_TEST")
            self.assertEqual(track.preview.data, b"FAKE_PREVIEW_MP3")
