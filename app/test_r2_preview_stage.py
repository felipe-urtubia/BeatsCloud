import io
import subprocess
import unittest
import wave
from types import SimpleNamespace
from unittest.mock import Mock, patch

from mutagen.mp3 import MP3

from app.r2_audio_stage import R2AudioStageError
from app.r2_presign import ALLOWED
from app.r2_preview_stage import (
    R2PreviewStageError,
    staged_r2_preview,
)


OWNER = 7
BUCKET = "bucket-ficticio"
KEY = "private/7/track/" + ("b" * 32) + ".wav"
MIME = sorted(ALLOWED["track"][".wav"])[0]


def crear_audio():
    memoria = io.BytesIO()

    with wave.open(memoria, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"\x00\x00" * 16000)

    return memoria.getvalue()


def cliente_ficticio(contenido):
    cliente = Mock()
    cuerpo = io.BytesIO(contenido)

    cliente.get_object.return_value = {
        "Body": cuerpo,
        "ContentLength": len(contenido),
        "ContentType": MIME,
    }

    return cliente, cuerpo


def preparar(cliente, contenido, **cambios):
    opciones = {
        "client": cliente,
        "bucket": BUCKET,
        "owner": OWNER,
        "private_key": KEY,
        "expected_size": len(contenido),
        "expected_mime": MIME,
    }

    opciones.update(cambios)

    return staged_r2_preview(**opciones)


class R2PreviewStageTests(unittest.TestCase):

    def test_genera_preview_mp3_y_limpia(self):
        contenido = crear_audio()
        cliente, cuerpo = cliente_ficticio(contenido)

        with preparar(cliente, contenido) as ruta:
            self.assertTrue(ruta.is_file())
            self.assertGreater(ruta.stat().st_size, 0)

            info = MP3(str(ruta)).info

            self.assertGreater(info.length, 1)
            self.assertLessEqual(info.length, 33)

            temporal = ruta
            carpeta = ruta.parent

        self.assertFalse(temporal.exists())
        self.assertFalse(carpeta.exists())
        self.assertTrue(cuerpo.closed)

    def test_rechaza_contenido_que_no_es_audio(self):
        contenido = b"Archivo ficticio sin audio"
        cliente, cuerpo = cliente_ficticio(contenido)

        with patch(
            "app.r2_preview_stage.subprocess.run"
        ) as proceso:
            with self.assertRaises(R2AudioStageError):
                with preparar(cliente, contenido):
                    pass

            proceso.assert_not_called()

        self.assertTrue(cuerpo.closed)

    def test_rechaza_otro_productor(self):
        contenido = crear_audio()
        cliente, _ = cliente_ficticio(contenido)

        with self.assertRaises(R2AudioStageError):
            with preparar(
                cliente,
                contenido,
                owner=9,
            ):
                pass

        cliente.get_object.assert_not_called()

    def test_rechaza_mime_incorrecto(self):
        contenido = crear_audio()
        cliente, _ = cliente_ficticio(contenido)

        with self.assertRaises(R2AudioStageError):
            with preparar(
                cliente,
                contenido,
                expected_mime="application/octet-stream",
            ):
                pass

        cliente.get_object.assert_not_called()

    def test_rechaza_audio_incompleto(self):
        contenido = crear_audio()
        cliente, cuerpo = cliente_ficticio(contenido)

        with self.assertRaises(R2AudioStageError):
            with preparar(
                cliente,
                contenido,
                expected_size=len(contenido) + 10,
            ):
                pass

        self.assertTrue(cuerpo.closed)

    def test_error_ffmpeg_no_publica_preview(self):
        contenido = crear_audio()
        cliente, cuerpo = cliente_ficticio(contenido)

        with patch(
            "app.r2_preview_stage.subprocess.run",
            return_value=SimpleNamespace(returncode=1),
        ):
            with self.assertRaises(R2PreviewStageError):
                with preparar(cliente, contenido):
                    pass

        self.assertTrue(cuerpo.closed)

    def test_timeout_ffmpeg_se_controla(self):
        contenido = crear_audio()
        cliente, cuerpo = cliente_ficticio(contenido)

        with patch(
            "app.r2_preview_stage.subprocess.run",
            side_effect=subprocess.TimeoutExpired(
                "ffmpeg", 90
            ),
        ):
            with self.assertRaises(R2PreviewStageError):
                with preparar(cliente, contenido):
                    pass

        self.assertTrue(cuerpo.closed)


if __name__ == "__main__":
    unittest.main()
