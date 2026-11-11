import math
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings
from mutagen.mp3 import MP3

from app.r2_audio_stage import staged_verified_r2_audio


MAX_PREVIEW_BYTES = 20 * 1024 * 1024


class R2PreviewStageError(RuntimeError):
    pass


@contextmanager
def staged_r2_preview(
    *,
    client,
    bucket,
    owner,
    private_key,
    expected_size,
    expected_mime,
):
    """
    Valida un audio privado de R2 y genera su preview temporal.

    No guarda modelos, no publica canciones, no sube
    objetos a R2 y no modifica archivos multimedia locales.

    El llamante debe persistir la preview validada mientras
    este dentro del contexto, en una futura fase controlada.
    """

    with staged_verified_r2_audio(
        client=client,
        bucket=bucket,
        owner=owner,
        private_key=private_key,
        expected_size=expected_size,
        expected_mime=expected_mime,
    ) as original:

        with tempfile.TemporaryDirectory(
            prefix="beatcloud_r2_preview_"
        ) as carpeta:
            preview = Path(carpeta) / "preview.mp3"

            ejecutable = getattr(
                settings,
                "FFMPEG_PATH",
                "ffmpeg",
            )

            if (
                not isinstance(ejecutable, str)
                or not ejecutable.strip()
            ):
                raise R2PreviewStageError(
                    "FFmpeg no esta configurado."
                )

            comando = [
                ejecutable,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                "-y",
                "-i",
                str(original),
                "-t",
                "30",
                "-vn",
                "-map",
                "0:a:0",
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "4",
                str(preview),
            ]

            try:
                resultado = subprocess.run(
                    comando,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=90,
                    check=False,
                )

            except subprocess.TimeoutExpired as exc:
                raise R2PreviewStageError(
                    "La generacion de preview excedio "
                    "el tiempo permitido."
                ) from exc

            except OSError as exc:
                raise R2PreviewStageError(
                    "No fue posible ejecutar FFmpeg."
                ) from exc

            if resultado.returncode != 0:
                raise R2PreviewStageError(
                    "FFmpeg no pudo generar la preview."
                )

            try:
                tamano = preview.stat().st_size

                if not (0 < tamano <= MAX_PREVIEW_BYTES):
                    raise R2PreviewStageError(
                        "Tamano de preview no permitido."
                    )

                informacion = MP3(str(preview)).info
                duracion = informacion.length

                if (
                    not isinstance(duracion, (int, float))
                    or not math.isfinite(duracion)
                    or not (0 < duracion <= 33)
                ):
                    raise R2PreviewStageError(
                        "Duracion de preview no valida."
                    )

            except R2PreviewStageError:
                raise

            except Exception as exc:
                raise R2PreviewStageError(
                    "La preview generada no es un MP3 valido."
                ) from exc

            yield preview
