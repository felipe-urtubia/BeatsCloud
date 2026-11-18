import io
import wave
import unittest
from unittest.mock import Mock

from app.r2_audio_stage import (
    R2AudioStageError,
    staged_verified_r2_audio,
)
from app.r2_presign import ALLOWED


OWNER = 7
BUCKET = "bucket-ficticio"
KEY = "private/7/track/" + ("a" * 32) + ".wav"
MIME = sorted(ALLOWED["track"][".wav"])[0]


def crear_wav():
    memoria = io.BytesIO()

    with wave.open(memoria, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 8000)

    return memoria.getvalue()


def cliente_ficticio(contenido, *, size=None, mime=MIME):
    cliente = Mock()
    cuerpo = io.BytesIO(contenido)

    cliente.get_object.return_value = {
        "Body": cuerpo,
        "ContentLength": (
            len(contenido) if size is None else size
        ),
        "ContentType": mime,
    }

    return cliente, cuerpo


def preparar(cliente, cantidad, **opciones):
    parametros = {
        "client": cliente,
        "bucket": BUCKET,
        "owner": OWNER,
        "private_key": KEY,
        "expected_size": cantidad,
        "expected_mime": MIME,
    }

    parametros.update(opciones)

    return staged_verified_r2_audio(**parametros)


class R2AudioStageTests(unittest.TestCase):

    def test_audio_wav_valido_y_limpieza(self):
        contenido = crear_wav()
        cliente, cuerpo = cliente_ficticio(contenido)

        with preparar(cliente, len(contenido)) as ruta:
            self.assertTrue(ruta.is_file())
            self.assertEqual(ruta.read_bytes(), contenido)
            temporal = ruta

        self.assertFalse(temporal.exists())
        self.assertTrue(cuerpo.closed)
        cliente.get_object.assert_called_once_with(
            Bucket=BUCKET,
            Key=KEY,
        )

    def test_rechaza_archivo_que_no_es_audio(self):
        contenido = b"Este archivo no es audio"
        cliente, cuerpo = cliente_ficticio(contenido)

        with self.assertRaises(R2AudioStageError):
            with preparar(cliente, len(contenido)):
                pass

        self.assertTrue(cuerpo.closed)

    def test_rechaza_metadatos_diferentes(self):
        contenido = crear_wav()
        cliente, cuerpo = cliente_ficticio(
            contenido,
            size=len(contenido) + 1,
        )

        with self.assertRaises(R2AudioStageError):
            with preparar(cliente, len(contenido)):
                pass

        self.assertTrue(cuerpo.closed)

    def test_rechaza_descarga_mas_grande(self):
        contenido = crear_wav()
        cliente, cuerpo = cliente_ficticio(
            contenido,
            size=len(contenido) - 1,
        )

        with self.assertRaises(R2AudioStageError):
            with preparar(cliente, len(contenido) - 1):
                pass

        self.assertTrue(cuerpo.closed)

    def test_rechaza_clave_de_otro_productor(self):
        contenido = crear_wav()
        cliente, _ = cliente_ficticio(contenido)

        with self.assertRaises(R2AudioStageError):
            with preparar(
                cliente,
                len(contenido),
                owner=8,
            ):
                pass

        cliente.get_object.assert_not_called()

    def test_rechaza_ruta_fuera_de_private(self):
        contenido = crear_wav()
        cliente, _ = cliente_ficticio(contenido)

        with self.assertRaises(R2AudioStageError):
            with preparar(
                cliente,
                len(contenido),
                private_key="pending/7/track/"
                + ("a" * 32)
                + ".wav",
            ):
                pass

        cliente.get_object.assert_not_called()


if __name__ == "__main__":
    unittest.main()
