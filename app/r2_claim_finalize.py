import re
from pathlib import PurePosixPath

from django.db import transaction
from django.utils import timezone

from app.models import Track
from app.r2_claim import R2UploadClaim
from app.r2_presign import ALLOWED


class R2ClaimFinalizationError(ValueError):
    pass


def finalize_r2_claim(*, claim_id, user_id, track_id):
    """
    Vincula un Track R2 preparado a su reserva.

    Solo modifica la base de datos y usa una transaccion.
    Requiere que el endpoint haya autenticado al productor,
    validado el audio y persistido la preview previamente.

    No comprueba la existencia fisica de la preview.
    No crea archivos ni accede a Cloudflare R2.
    """

    for valor in (claim_id, user_id, track_id):
        if type(valor) is not int or valor <= 0:
            raise R2ClaimFinalizationError(
                "Identificador invalido."
            )

    with transaction.atomic():
        reserva = (
            R2UploadClaim.objects
            .select_for_update()
            .filter(pk=claim_id, owner_id=user_id)
            .first()
        )

        if reserva is None:
            raise R2ClaimFinalizationError(
                "Reserva no autorizada o inexistente."
            )

        if (
            reserva.status == "ready"
            and reserva.track_id == track_id
        ):
            return False

        if (
            reserva.status != "processing"
            or reserva.track_id is not None
        ):
            raise R2ClaimFinalizationError(
                "Reserva no disponible para finalizar."
            )

        cancion = (
            Track.objects
            .select_for_update()
            .select_related("usuario")
            .filter(pk=track_id)
            .first()
        )

        if cancion is None:
            raise R2ClaimFinalizationError(
                "Cancion inexistente."
            )

        if cancion.usuario.user_id != user_id:
            raise R2ClaimFinalizationError(
                "La cancion pertenece a otro productor."
            )

        if (
            cancion.storage_backend != "r2"
            or cancion.media_status != "processing"
        ):
            raise R2ClaimFinalizationError(
                "La cancion no esta preparada para R2."
            )

        clave = reserva.private_key

        patron = (
            rf"private/{user_id}/track/"
            r"[a-f0-9]{32}\.[a-z0-9]+"
        )

        if (
            not isinstance(clave, str)
            or not re.fullmatch(patron, clave)
            or cancion.r2_object_key != clave
        ):
            raise R2ClaimFinalizationError(
                "La clave privada no coincide."
            )

        extension = PurePosixPath(clave).suffix.lower()

        if (
            extension not in ALLOWED["track"]
            or not reserva.pending_key.endswith(extension)
        ):
            raise R2ClaimFinalizationError(
                "Formato de la reserva inconsistente."
            )

        if cancion.track.name:
            raise R2ClaimFinalizationError(
                "La cancion R2 no debe usar un original local."
            )

        preview = cancion.preview.name or ""
        ruta = PurePosixPath(preview)

        if (
            not preview.startswith("previews/")
            or "\\" in preview
            or ".." in ruta.parts
            or ruta.suffix.lower() != ".mp3"
        ):
            raise R2ClaimFinalizationError(
                "Falta una referencia de preview valida."
            )

        if R2UploadClaim.objects.filter(
            track_id=track_id
        ).exclude(pk=claim_id).exists():
            raise R2ClaimFinalizationError(
                "La cancion ya tiene otra reserva."
            )

        cancion.media_status = "ready"
        cancion.save(update_fields=["media_status"])

        reserva.track = cancion
        reserva.status = "ready"
        reserva.updated_at = timezone.now()

        reserva.save(
            update_fields=["track", "status", "updated_at"]
        )

        return True
