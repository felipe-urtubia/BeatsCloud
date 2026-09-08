import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.files import File


def generar_preview_audio(track):
    """
    Genera una vista previa MP3 con los primeros 30 segundos del audio
    original y la guarda en track.preview.
    """
    if not track.track:
        raise ValueError("El track no tiene un archivo de audio original.")

    ffmpeg_path = getattr(settings, "FFMPEG_PATH", "ffmpeg")

    with tempfile.TemporaryDirectory() as temp_dir:
        salida = Path(temp_dir) / "preview.mp3"

        comando = [
            ffmpeg_path,
            "-y",
            "-i",
            track.track.path,
            "-t",
            "30",
            "-vn",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "4",
            str(salida),
        ]

        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if resultado.returncode != 0 or not salida.exists():
            detalle = resultado.stderr.strip() or "Error desconocido de FFmpeg."
            raise RuntimeError(
                f"No fue posible generar el preview del audio: {detalle}"
            )

        nombre_preview = f"track_{track.pk}_preview.mp3"

        with salida.open("rb") as archivo_preview:
            track.preview.save(
                nombre_preview,
                File(archivo_preview),
                save=True,
            )

    return track.preview
