from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from app.r2_claim import R2UploadClaim
from app.r2_registration_guard import validate_r2_track_token


class R2ClaimConflict(ValueError):
    pass


@dataclass(frozen=True)
class R2ClaimReservation:
    claim_id: int
    created: bool
    status: str


def reserve_r2_upload(*, user_id, upload_token):
    """
    Reserva una clave temporal R2 una sola vez.

    Precondicion: el endpoint ya comprobo autenticacion,
    rol de productor y permisos de la solicitud.

    Una reserva repetida nunca activa procesamiento.
    No consulta R2, no crea canciones y no publica audio.
    """

    autorizacion = validate_r2_track_token(
        upload_token=upload_token,
        user_id=user_id,
    )

    with transaction.atomic():
        reserva, creada = R2UploadClaim.objects.get_or_create(
            pending_key=autorizacion.pending_key,
            defaults={
                "owner_id": autorizacion.owner,
                "expected_size": autorizacion.expected_size,
                "expected_mime": autorizacion.expected_mime,
                "status": "reserved",
            },
        )

        if (
            reserva.owner_id != autorizacion.owner
            or reserva.expected_size != autorizacion.expected_size
            or reserva.expected_mime != autorizacion.expected_mime
        ):
            raise R2ClaimConflict(
                "La clave ya posee una reserva incompatible."
            )

        return R2ClaimReservation(
            claim_id=reserva.pk,
            created=creada,
            status=reserva.status,
        )


def try_begin_r2_processing(*, claim_id, user_id):
    """
    Transicion atomica reserved -> processing.

    Solo una solicitud puede obtener True.
    No reintenta reservas processing, ready ni failed.
    El llamante debe validar permisos previamente.
    """

    if (
        type(claim_id) is not int
        or claim_id <= 0
        or type(user_id) is not int
        or user_id <= 0
    ):
        return False

    afectados = R2UploadClaim.objects.filter(
        pk=claim_id,
        owner_id=user_id,
        status="reserved",
    ).update(status="processing", updated_at=timezone.now())

    return afectados == 1
