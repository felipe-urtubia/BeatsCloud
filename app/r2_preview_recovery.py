import re
import secrets
from pathlib import PurePosixPath

from botocore.exceptions import ClientError
from django.db import transaction

from app.models import Track
from app.r2_presign import ALLOWED, MAX_BYTES
from app.r2_preview_stage import staged_r2_preview
from app.r2_preview_storage import (
    MAX_PREVIEW_BYTES,
    PREVIEW_KEY_PATTERN,
    upload_r2_preview,
)


class R2PreviewRecoveryError(RuntimeError):
    pass


def _is_missing(exc):
    code = str(
        exc.response.get("Error", {}).get("Code", "")
    )
    return code in {"404", "NoSuchKey", "NotFound"}


def recover_track_preview(*, track_id, client, bucket):
    """
    Recupera una sola preview R2.

    No elimina originales privados.
    No modifica otros campos del Track.
    No sobrescribe previews R2 existentes.
    """

    if type(track_id) is not int or track_id <= 0:
        raise R2PreviewRecoveryError("ID invalido.")

    if not isinstance(bucket, str) or not bucket.strip():
        raise R2PreviewRecoveryError("Bucket invalido.")

    track = Track.objects.filter(pk=track_id).first()

    if track is None:
        raise R2PreviewRecoveryError("Track inexistente.")

    if (
        track.storage_backend != "r2"
        or track.media_status != "ready"
    ):
        raise R2PreviewRecoveryError(
            "El track no esta listo para recuperacion R2."
        )

    owner = track.r2_owner_user_id
    private_key = track.r2_object_key

    if type(owner) is not int or owner <= 0:
        raise R2PreviewRecoveryError(
            "Propietario R2 invalido."
        )

    patron = (
        rf"private/{owner}/track/"
        r"[a-f0-9]{32}\.[a-z0-9]+"
    )

    if (
        not isinstance(private_key, str)
        or re.fullmatch(patron, private_key) is None
    ):
        raise R2PreviewRecoveryError(
            "Clave privada R2 invalida."
        )

    extension = PurePosixPath(private_key).suffix.lower()

    try:
        original = client.head_object(
            Bucket=bucket,
            Key=private_key,
        )

        size = original.get("ContentLength")
        mime = original.get("ContentType")

        if (
            type(size) is not int
            or not 0 < size <= MAX_BYTES["track"]
            or extension not in ALLOWED["track"]
            or mime not in ALLOWED["track"][extension]
        ):
            raise R2PreviewRecoveryError(
                "Metadatos del original incompatibles."
            )

    except R2PreviewRecoveryError:
        raise

    except Exception as exc:
        raise R2PreviewRecoveryError(
            "No fue posible verificar el original R2."
        ) from exc

    previous_name = getattr(track.preview, "name", None)
    previous_key = previous_name or ""

    if PREVIEW_KEY_PATTERN.fullmatch(previous_key):
        try:
            existing = client.head_object(
                Bucket=bucket,
                Key=previous_key,
            )

        except ClientError as exc:
            if not _is_missing(exc):
                raise R2PreviewRecoveryError(
                    "No fue posible verificar la preview actual."
                ) from exc

        except Exception as exc:
            raise R2PreviewRecoveryError(
                "No fue posible verificar la preview actual."
            ) from exc

        else:
            existing_size = existing.get("ContentLength")
            existing_mime = existing.get("ContentType")

            if (
                type(existing_size) is int
                and 0 < existing_size <= MAX_PREVIEW_BYTES
                and existing_mime == "audio/mpeg"
            ):
                return {
                    "status": "correcta",
                    "key": previous_key,
                }

    new_key = (
        "previews/r2-"
        + secrets.token_hex(16)
        + ".mp3"
    )

    upload_attempted = False

    try:
        with staged_r2_preview(
            client=client,
            bucket=bucket,
            owner=owner,
            private_key=private_key,
            expected_size=size,
            expected_mime=mime,
        ) as preview_path:

            upload_attempted = True

            upload_r2_preview(
                client=client,
                bucket=bucket,
                preview_path=preview_path,
                key=new_key,
            )

        with transaction.atomic():
            updated = Track.objects.filter(
                pk=track_id,
                storage_backend="r2",
                media_status="ready",
                r2_owner_user_id=owner,
                r2_object_key=private_key,
                preview=previous_name,
            ).update(preview=new_key)

            if updated != 1:
                raise R2PreviewRecoveryError(
                    "El track cambio durante la recuperacion."
                )

    except Exception:
        if upload_attempted:
            try:
                client.delete_object(
                    Bucket=bucket,
                    Key=new_key,
                )
            except Exception as cleanup_error:
                raise R2PreviewRecoveryError(
                    "Fallo la limpieza de la preview nueva. "
                    "Se requiere revision manual."
                ) from cleanup_error

        raise

    return {
        "status": "recuperada",
        "key": new_key,
    }
