from app.models import Genero_Musical, Track, Usuario
from app.r2_claim_service import reserve_r2_upload, try_begin_r2_processing
from app.r2_claim_lifecycle import mark_r2_claim_failed
from app.r2_registration_guard import validate_r2_cover_token, validate_r2_stems_token
from app.r2_registration_prepare import prepare_r2_track_registration, prepare_r2_cover_upload
from app.r2_stems import prepare_r2_stems_upload
from app.r2_track_registration import register_prepared_r2_track


class R2UploadWorkflowError(ValueError):
    pass


class R2UploadWorkflowConflict(R2UploadWorkflowError):
    pass


def _delete_private_if_unattached(client, bucket, draft, track, field_name):
    if draft is None:
        return
    key = getattr(draft, "private_key", "")
    if not isinstance(key, str) or not key:
        return
    attached = False
    if track is not None and getattr(track, "pk", None):
        try:
            attached = Track.objects.filter(pk=track.pk, **{field_name: key}).exists()
        except Exception:
            attached = False
    if not attached:
        try:
            client.delete_object(Bucket=bucket, Key=key)
        except Exception:
            pass


def complete_r2_track_upload(
    *, client, bucket, user_id, upload_token, nombre_track, precio, genero_id,
    metadata=None, foto=None, cover_upload_token=None, stems_upload_token=None,
):
    """Coordina reserva, promocion privada y registro de una pista R2."""
    if type(user_id) is not int or user_id <= 0:
        raise R2UploadWorkflowError("Identificador de usuario invalido.")
    if not Usuario.objects.filter(user_id=user_id, tipo_usu=Usuario.PRODUCTOR).exists():
        raise R2UploadWorkflowError("Se requiere un perfil de productor.")
    if (
        not isinstance(nombre_track, str) or not nombre_track.strip()
        or len(nombre_track.strip()) > Track._meta.get_field("nombre_track").max_length
    ):
        raise R2UploadWorkflowError("Nombre de cancion invalido.")
    if type(precio) is not int or precio < 0 or precio > 2147483647:
        raise R2UploadWorkflowError("Precio de cancion invalido.")
    if (
        type(genero_id) is not int or genero_id <= 0
        or not Genero_Musical.objects.filter(pk=genero_id).exists()
    ):
        raise R2UploadWorkflowError("Genero musical invalido.")
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise R2UploadWorkflowError("Metadatos de cancion invalidos.")

    has_stems = metadata.get("has_stems", False)
    if type(has_stems) is not bool:
        raise R2UploadWorkflowError("El indicador STEMS debe ser booleano.")
    if has_stems != (stems_upload_token is not None):
        raise R2UploadWorkflowError(
            "Debes adjuntar el archivo STEMS cuando marques que esta incluido."
        )
    if foto is not None and cover_upload_token is not None:
        raise R2UploadWorkflowError("No se permite combinar portada local y portada R2.")
    if cover_upload_token is not None:
        validate_r2_cover_token(upload_token=cover_upload_token, user_id=user_id)
    if stems_upload_token is not None:
        validate_r2_stems_token(upload_token=stems_upload_token, user_id=user_id)

    reserva = reserve_r2_upload(user_id=user_id, upload_token=upload_token)
    if reserva.status != "reserved":
        raise R2UploadWorkflowConflict("Esta subida ya fue procesada o esta en proceso.")
    if not try_begin_r2_processing(claim_id=reserva.claim_id, user_id=user_id):
        raise R2UploadWorkflowConflict("Otra solicitud inicio el procesamiento.")

    portada_preparada = None
    stems_preparados = None
    cancion = None
    try:
        with prepare_r2_track_registration(
            client=client, bucket=bucket, user_id=user_id, upload_token=upload_token
        ) as preparado:
            if cover_upload_token is not None:
                portada_preparada = prepare_r2_cover_upload(
                    client=client, bucket=bucket, user_id=user_id,
                    upload_token=cover_upload_token,
                )
            if stems_upload_token is not None:
                stems_preparados = prepare_r2_stems_upload(
                    client=client, bucket=bucket, user_id=user_id,
                    upload_token=stems_upload_token,
                )

            kwargs = {
                "claim_id": reserva.claim_id, "user_id": user_id,
                "draft": preparado, "nombre_track": nombre_track,
                "client": client, "bucket": bucket,
                "precio": precio, "genero_id": genero_id,
                "metadata": metadata, "foto": foto,
                "cover_draft": portada_preparada,
            }
            if stems_preparados is not None:
                kwargs["stems_draft"] = stems_preparados
            cancion = register_prepared_r2_track(**kwargs)
        return cancion
    except Exception:
        _delete_private_if_unattached(client, bucket, stems_preparados, cancion, "r2_stems_key")
        _delete_private_if_unattached(client, bucket, portada_preparada, cancion, "r2_cover_key")
        try:
            mark_r2_claim_failed(claim_id=reserva.claim_id, user_id=user_id)
        except Exception:
            pass
        raise
