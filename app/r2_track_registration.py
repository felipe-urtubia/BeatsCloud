import secrets
from pathlib import Path

from django.core.files import File
from django.db import transaction
from mutagen import File as MutagenFile

from app.models import Track, Usuario, Genero_Musical
from app.r2_claim import R2UploadClaim
from app.r2_claim_lifecycle import (
    attach_r2_private_key,
    mark_r2_claim_failed,
)
from app.r2_claim_finalize import finalize_r2_claim
from app.r2_registration_prepare import R2RegistrationDraft


class R2TrackRegistrationError(ValueError):
    pass


def register_prepared_r2_track(
    *,
    claim_id,
    user_id,
    draft,
    nombre_track,
    precio,
    genero_id,
):
    """
    Persiste una cancion R2 y su preview ya preparada.

    Debe llamarse dentro del contexto que genero el draft.
    El endpoint debe haber verificado autenticacion y permisos.

    No sube originales a R2 ni realiza conexiones externas.
    No sustituye la validacion completa del formulario HTTP.
    """

    if (
        type(claim_id) is not int
        or claim_id <= 0
        or type(user_id) is not int
        or user_id <= 0
        or type(genero_id) is not int
        or genero_id <= 0
    ):
        raise R2TrackRegistrationError(
            "Identificadores invalidos."
        )

    if not isinstance(draft, R2RegistrationDraft):
        raise R2TrackRegistrationError(
            "Preparacion R2 invalida."
        )

    if draft.owner != user_id:
        raise R2TrackRegistrationError(
            "El audio pertenece a otro usuario."
        )

    if (
        not isinstance(nombre_track, str)
        or not nombre_track.strip()
        or len(nombre_track.strip())
        > Track._meta.get_field("nombre_track").max_length
    ):
        raise R2TrackRegistrationError(
            "Nombre de cancion invalido."
        )

    if (
        type(precio) is not int
        or precio < 0
        or precio > 2147483647
    ):
        raise R2TrackRegistrationError(
            "Precio invalido."
        )

    origen = draft.preview_path

    if (
        not isinstance(origen, Path)
        or origen.suffix.lower() != ".mp3"
        or origen.is_symlink()
        or not origen.is_file()
    ):
        raise R2TrackRegistrationError(
            "Preview temporal no disponible."
        )

    if not 0 < origen.stat().st_size <= 20_000_000:
        raise R2TrackRegistrationError(
            "Tamano de preview invalido."
        )

    try:
        audio = MutagenFile(str(origen))
        duracion = getattr(
            getattr(audio, "info", None),
            "length",
            0,
        )

        if audio is None or duracion <= 0:
            raise ValueError("Audio sin duracion valida.")

    except Exception as exc:
        raise R2TrackRegistrationError(
            "La preview no contiene audio valido."
        ) from exc

    perfil = Usuario.objects.filter(
        user_id=user_id,
        tipo_usu=Usuario.PRODUCTOR,
    ).first()

    if perfil is None:
        raise R2TrackRegistrationError(
            "Perfil de productor no autorizado."
        )

    genero = Genero_Musical.objects.filter(
        pk=genero_id
    ).first()

    if genero is None:
        raise R2TrackRegistrationError(
            "Genero musical inexistente."
        )

    reserva = R2UploadClaim.objects.filter(
        pk=claim_id,
        owner_id=user_id,
        status="processing",
        track__isnull=True,
    ).first()

    if (
        reserva is None
        or reserva.pending_key != draft.pending_key
        or reserva.expected_size != draft.expected_size
        or reserva.expected_mime != draft.expected_mime
        or reserva.private_key
    ):
        raise R2TrackRegistrationError(
            "La reserva no esta disponible o es incompatible."
        )

    if not attach_r2_private_key(
        claim_id=claim_id,
        user_id=user_id,
        private_key=draft.private_key,
    ):
        raise R2TrackRegistrationError(
            "No fue posible asociar la copia privada."
        )

    nombre_preview = ""
    almacenamiento = Track._meta.get_field("preview").storage

    try:
        with transaction.atomic():
            cancion = Track(
                nombre_track=nombre_track.strip(),
                precio=precio,
                genero=genero,
                usuario=perfil,
                track="",
                storage_backend="r2",
                r2_object_key=draft.private_key,
                media_status="processing",
            )

            cancion.full_clean(
                exclude=["track", "preview"]
            )

            nombre_archivo = (
                "r2-"
                + secrets.token_hex(16)
                + ".mp3"
            )

            with origen.open("rb") as archivo:
                cancion.preview.save(
                    nombre_archivo,
                    File(archivo),
                    save=False,
                )

            nombre_preview = cancion.preview.name
            cancion.save()

            if not finalize_r2_claim(
                claim_id=claim_id,
                user_id=user_id,
                track_id=cancion.pk,
            ):
                raise R2TrackRegistrationError(
                    "La finalizacion no fue confirmada."
                )

        return cancion

    except Exception:
        estado = None

        try:
            estado = R2UploadClaim.objects.filter(
                pk=claim_id,
                owner_id=user_id,
            ).values(
                "status",
                "track_id",
            ).first()

        except Exception:
            pass

        if estado is not None and estado["status"] == "processing":
            mark_r2_claim_failed(
                claim_id=claim_id,
                user_id=user_id,
            )

            if nombre_preview and estado["track_id"] is None:
                almacenamiento.delete(nombre_preview)

        raise
