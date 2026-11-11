from app.models import Genero_Musical, Track, Usuario
from app.r2_claim_service import (
    reserve_r2_upload,
    try_begin_r2_processing,
)
from app.r2_claim_lifecycle import mark_r2_claim_failed
from app.r2_registration_prepare import (
    prepare_r2_track_registration,
)
from app.r2_track_registration import (
    register_prepared_r2_track,
)


class R2UploadWorkflowError(ValueError):
    pass


class R2UploadWorkflowConflict(R2UploadWorkflowError):
    pass


def complete_r2_track_upload(
    *,
    client,
    bucket,
    user_id,
    upload_token,
    nombre_track,
    precio,
    genero_id,
):
    """
    Coordina la creacion de una cancion R2.

    La autenticacion HTTP debe realizarse en el endpoint.
    Este servicio vuelve a verificar el rol del productor.

    No concede reintentos automaticos a reservas fallidas.
    No elimina copias privadas de R2.
    """

    if type(user_id) is not int or user_id <= 0:
        raise R2UploadWorkflowError(
            "Identificador de usuario invalido."
        )

    if not Usuario.objects.filter(
        user_id=user_id,
        tipo_usu=Usuario.PRODUCTOR,
    ).exists():
        raise R2UploadWorkflowError(
            "Se requiere un perfil de productor."
        )

    if (
        not isinstance(nombre_track, str)
        or not nombre_track.strip()
        or len(nombre_track.strip())
        > Track._meta.get_field("nombre_track").max_length
    ):
        raise R2UploadWorkflowError(
            "Nombre de cancion invalido."
        )

    if (
        type(precio) is not int
        or precio < 0
        or precio > 2147483647
    ):
        raise R2UploadWorkflowError(
            "Precio de cancion invalido."
        )

    if (
        type(genero_id) is not int
        or genero_id <= 0
        or not Genero_Musical.objects.filter(
            pk=genero_id
        ).exists()
    ):
        raise R2UploadWorkflowError(
            "Genero musical invalido."
        )

    reserva = reserve_r2_upload(
        user_id=user_id,
        upload_token=upload_token,
    )

    if reserva.status != "reserved":
        raise R2UploadWorkflowConflict(
            "Esta subida ya fue procesada o esta en proceso."
        )

    if not try_begin_r2_processing(
        claim_id=reserva.claim_id,
        user_id=user_id,
    ):
        raise R2UploadWorkflowConflict(
            "Otra solicitud inicio el procesamiento."
        )

    try:
        with prepare_r2_track_registration(
            client=client,
            bucket=bucket,
            user_id=user_id,
            upload_token=upload_token,
        ) as preparado:
            cancion = register_prepared_r2_track(
                claim_id=reserva.claim_id,
                user_id=user_id,
                draft=preparado,
                nombre_track=nombre_track,
                precio=precio,
                genero_id=genero_id,
            )

        return cancion

    except Exception:
        mark_r2_claim_failed(
            claim_id=reserva.claim_id,
            user_id=user_id,
        )
        raise
