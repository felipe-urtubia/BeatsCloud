import re
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from mutagen import File as MutagenFile

from app.r2_presign import ALLOWED, MAX_BYTES


class R2AudioStageError(ValueError):
    pass


@contextmanager
def staged_verified_r2_audio(
    *,
    client,
    bucket,
    owner,
    private_key,
    expected_size,
    expected_mime,
):
    """
    Descarga y valida temporalmente un original privado de R2.

    Precondicion: el llamante ha verificado la sesion, el token
    firmado y la promocion del objeto privado.

    No crea Track, no publica audio y no borra objetos R2.
    El archivo local temporal desaparece al salir del contexto.
    """

    if not isinstance(bucket, str) or not bucket.strip():
        raise R2AudioStageError("Bucket invalido.")

    if type(owner) is not int or owner <= 0:
        raise R2AudioStageError("Propietario invalido.")

    if not isinstance(private_key, str):
        raise R2AudioStageError("Clave privada invalida.")

    patron = (
        r"private/[1-9][0-9]*/track/"
        r"[a-f0-9]{32}\.[a-z0-9]+"
    )

    if not re.fullmatch(patron, private_key):
        raise R2AudioStageError("Ruta privada invalida.")

    if not private_key.startswith(
        f"private/{owner}/track/"
    ):
        raise R2AudioStageError("Propietario incorrecto.")

    extension = PurePosixPath(private_key).suffix.lower()
    formatos = ALLOWED["track"]

    if (
        extension not in formatos
        or not isinstance(expected_mime, str)
        or expected_mime not in formatos[extension]
    ):
        raise R2AudioStageError("Formato no permitido.")

    if (
        type(expected_size) is not int
        or expected_size <= 0
        or expected_size > MAX_BYTES["track"]
    ):
        raise R2AudioStageError("Tamano no permitido.")

    with tempfile.TemporaryDirectory(
        prefix="beatcloud_r2_audio_"
    ) as carpeta:
        archivo = Path(carpeta) / (
            "original" + extension
        )

        try:
            respuesta = client.get_object(
                Bucket=bucket,
                Key=private_key,
            )
        except Exception as exc:
            raise R2AudioStageError(
                "No se pudo obtener el audio privado."
            ) from exc

        cuerpo = (
            respuesta.get("Body")
            if isinstance(respuesta, dict)
            else None
        )

        try:
            if not isinstance(respuesta, dict):
                raise R2AudioStageError(
                    "Respuesta de almacenamiento invalida."
                )

            if (
                type(respuesta.get("ContentLength")) is not int
                or respuesta["ContentLength"] != expected_size
                or respuesta.get("ContentType") != expected_mime
            ):
                raise R2AudioStageError(
                    "Los metadatos del audio no coinciden."
                )

            if not callable(getattr(cuerpo, "read", None)):
                raise R2AudioStageError(
                    "El objeto no contiene un flujo valido."
                )

            recibido = 0

            with archivo.open("wb") as destino:
                while True:
                    bloque = cuerpo.read(1024 * 1024)

                    if not bloque:
                        break

                    if not isinstance(
                        bloque, (bytes, bytearray)
                    ):
                        raise R2AudioStageError(
                            "Contenido de audio invalido."
                        )

                    recibido += len(bloque)

                    if recibido > expected_size:
                        raise R2AudioStageError(
                            "El archivo supera el tamano autorizado."
                        )

                    destino.write(bloque)

            if recibido != expected_size:
                raise R2AudioStageError(
                    "El audio esta incompleto."
                )

        finally:
            cerrar = getattr(cuerpo, "close", None)

            if callable(cerrar):
                cerrar()

        try:
            audio = MutagenFile(str(archivo))
            informacion = getattr(audio, "info", None)
            duracion = getattr(
                informacion, "length", None
            )

            if (
                audio is None
                or not isinstance(duracion, (int, float))
                or not (0 < duracion < 1000000000)
            ):
                raise R2AudioStageError(
                    "El archivo no contiene audio valido."
                )

        except R2AudioStageError:
            raise

        except Exception as exc:
            raise R2AudioStageError(
                "No fue posible validar el audio."
            ) from exc

        yield archivo
