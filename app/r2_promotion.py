"""Promocion controlada de objetos R2 pendientes a claves privadas.

Importante: este modulo NO es un endpoint ni registra tracks. La validacion
multimedia real y la persistencia/idempotencia se incorporaran por separado.
"""
import re
from pathlib import PurePosixPath
from uuid import uuid4

from app.r2_presign import ALLOWED, MAX_BYTES


class R2PromotionError(RuntimeError):
    """Error controlado al fijar una copia privada en R2."""


def _check_metadata(metadata, expected_size, expected_mime, *, require_etag):
    if not isinstance(metadata, dict):
        raise R2PromotionError("Respuesta de metadatos no valida.")
    if (type(metadata.get("ContentLength")) is not int
            or metadata["ContentLength"] != expected_size
            or metadata.get("ContentType") != expected_mime):
        raise R2PromotionError("El objeto no coincide con la autorizacion.")
    etag = metadata.get("ETag")
    if require_etag and (not isinstance(etag, str) or not etag.strip()):
        raise R2PromotionError("No se recibio ETag para fijar el origen.")
    return etag


def promote_pending_object(*, client, bucket, owner, kind, pending_key,
                           expected_size, expected_mime):
    """Copia en R2 un objeto temporal a una clave privada e impredecible.

    PRECONDICION: el llamante debe verificar un token firmado, la sesion y el
    propietario ANTES de usar esta funcion. No expone ni registra la copia.

    CopySourceIfMatch evita copiar un origen que haya cambiado desde HEAD.
    La ruta final NO se expone a clientes para PUT. No borra la temporal.
    Retorna una ruta candidata; NO implica audio validado ni track publicado.
    """
    if not isinstance(bucket, str) or not bucket.strip():
        raise R2PromotionError("Bucket no valido.")
    if type(owner) is not int or owner <= 0 or kind not in ALLOWED:
        raise R2PromotionError("Propietario o tipo no valido.")
    if (type(expected_size) is not int or expected_size <= 0
            or expected_size > MAX_BYTES[kind]):
        raise R2PromotionError("Tamano no valido.")
    if not isinstance(pending_key, str):
        raise R2PromotionError("Clave temporal no valida.")
    if not re.fullmatch(r"pending/[0-9]+/(track|stems)/[a-f0-9]{32}\.[a-z0-9]+", pending_key):
        raise R2PromotionError("Clave temporal no valida.")
    if not pending_key.startswith(f"pending/{owner}/{kind}/"):
        raise R2PromotionError("Clave temporal de otro propietario.")
    extension = PurePosixPath(pending_key).suffix.lower()
    if (extension not in ALLOWED[kind]
            or not isinstance(expected_mime, str)
            or expected_mime not in ALLOWED[kind][extension]):
        raise R2PromotionError("Formato no permitido.")

    try:
        source = client.head_object(Bucket=bucket, Key=pending_key)
    except Exception as exc:
        raise R2PromotionError("No fue posible consultar el archivo pendiente.") from exc
    etag = _check_metadata(source, expected_size, expected_mime, require_etag=True)

    # Clave nueva, exclusiva de backend, no alcanzable mediante el PUT firmado.
    private_key = f"private/{owner}/{kind}/{uuid4().hex}{extension}"
    try:
        client.copy_object(
            Bucket=bucket,
            Key=private_key,
            CopySource={"Bucket": bucket, "Key": pending_key},
            CopySourceIfMatch=etag,
            MetadataDirective="COPY",
        )
    except Exception as exc:
        raise R2PromotionError("No fue posible fijar el archivo privado.") from exc

    try:
        destination = client.head_object(Bucket=bucket, Key=private_key)
    except Exception as exc:
        raise R2PromotionError("No fue posible comprobar la copia privada.") from exc
    _check_metadata(destination, expected_size, expected_mime, require_etag=True)

    return {"private_key": private_key, "size": expected_size,
            "content_type": expected_mime, "kind": kind}
