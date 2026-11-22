import re
from pathlib import Path


MAX_PREVIEW_BYTES = 20 * 1024 * 1024

PREVIEW_KEY_PATTERN = re.compile(
    r"previews/r2-[a-f0-9]{32}\.mp3"
)


class R2PreviewStorageError(RuntimeError):
    pass


def upload_r2_preview(
    *,
    client,
    bucket,
    preview_path,
    key,
):
    """
    Guarda una preview MP3 validada en R2.

    El bucket permanece privado.
    No modifica modelos ni archivos originales.
    """

    if (
        not isinstance(bucket, str)
        or not bucket.strip()
    ):
        raise R2PreviewStorageError(
            "Bucket R2 invalido."
        )

    if (
        not isinstance(key, str)
        or not PREVIEW_KEY_PATTERN.fullmatch(key)
    ):
        raise R2PreviewStorageError(
            "Clave de preview no valida."
        )

    archivo = Path(preview_path)

    if not archivo.is_file():
        raise R2PreviewStorageError(
            "El archivo de preview no existe."
        )

    tamano = archivo.stat().st_size

    if not 0 < tamano <= MAX_PREVIEW_BYTES:
        raise R2PreviewStorageError(
            "Tamano de preview no permitido."
        )

    try:
        with archivo.open("rb") as contenido:
            client.put_object(
                Bucket=bucket,
                Key=key,
                Body=contenido,
                ContentLength=tamano,
                ContentType="audio/mpeg",
            )

        metadata = client.head_object(
            Bucket=bucket,
            Key=key,
        )

    except Exception as exc:
        raise R2PreviewStorageError(
            "No fue posible guardar o verificar la preview en R2."
        ) from exc

    if int(metadata.get("ContentLength", -1)) != tamano:
        raise R2PreviewStorageError(
            "El tamano almacenado en R2 no coincide."
        )

    return key
