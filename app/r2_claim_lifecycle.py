import re
from pathlib import PurePosixPath

from django.utils import timezone

from app.r2_claim import R2UploadClaim
from app.r2_presign import ALLOWED


class R2ClaimStateError(ValueError):
    pass


def _identificador(valor):
    return type(valor) is int and valor > 0


def attach_r2_private_key(*, claim_id, user_id, private_key):
    """
    Asocia una copia privada a una reserva processing.

    No permite reemplazar una clave ya asociada.
    No consulta ni elimina objetos de Cloudflare R2.
    """

    if not _identificador(claim_id) or not _identificador(user_id):
        raise R2ClaimStateError("Identificadores invalidos.")

    if not isinstance(private_key, str):
        raise R2ClaimStateError("Clave privada invalida.")

    patron = (
        rf"private/{user_id}/track/"
        r"[a-f0-9]{32}\.[a-z0-9]+"
    )

    if not re.fullmatch(patron, private_key):
        raise R2ClaimStateError(
            "Ruta privada no autorizada."
        )

    extension = PurePosixPath(private_key).suffix.lower()

    if extension not in ALLOWED["track"]:
        raise R2ClaimStateError(
            "Extension no permitida."
        )

    afectados = R2UploadClaim.objects.filter(
        pk=claim_id,
        owner_id=user_id,
        status="processing",
        private_key="",
        pending_key__endswith=extension,
    ).update(
        private_key=private_key,
        updated_at=timezone.now(),
    )

    return afectados == 1


def mark_r2_claim_failed(*, claim_id, user_id):
    """
    Marca processing como failed.

    Conserva la clave privada para conciliacion.
    No elimina objetos ni modifica registros ready.
    """

    if not _identificador(claim_id) or not _identificador(user_id):
        raise R2ClaimStateError(
            "Identificadores invalidos."
        )

    afectados = R2UploadClaim.objects.filter(
        pk=claim_id,
        owner_id=user_id,
        status="processing",
    ).update(
        status="failed",
        updated_at=timezone.now(),
    )

    return afectados == 1
