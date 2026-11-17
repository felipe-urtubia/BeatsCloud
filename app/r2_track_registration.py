import re
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
from app.r2_registration_prepare import (
    R2RegistrationDraft,
    R2CoverDraft,
)
from app.r2_stems import R2StemsDraft
from app.metadata_validation import validate_d9_field


class R2TrackRegistrationError(ValueError):
    pass



def _normalizar_metadata(metadata):
    # Valida los metadatos persistidos para un Track R2.
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise R2TrackRegistrationError("Metadatos de cancion invalidos.")

    try:
        resource_type = validate_d9_field(
            "resource_type", metadata.get("resource_type", "instrumental")
        )
        bpm = validate_d9_field("bpm", metadata.get("bpm", 140))
        mood = validate_d9_field("mood", metadata.get("mood", "Oscuro"))
        has_stems = validate_d9_field(
            "has_stems", metadata.get("has_stems", False)
        )
    except Exception as exc:
        raise R2TrackRegistrationError(
            "Los metadatos musicales no son validos."
        ) from exc

    def texto(nombre, defecto, maximo):
        valor = metadata.get(nombre, defecto)
        if not isinstance(valor, str) or len(valor) > maximo:
            raise R2TrackRegistrationError(
                f"El campo {nombre} no es valido."
            )
        return valor.strip()

    def booleano(nombre, defecto):
        valor = metadata.get(nombre, defecto)
        if type(valor) is not bool:
            raise R2TrackRegistrationError(
                f"El campo {nombre} debe ser booleano."
            )
        return valor

    duration = metadata.get("duration", 30)
    if type(duration) is not int or not 1 <= duration <= 86400:
        raise R2TrackRegistrationError("La duracion de la cancion no es valida.")

    return {
        "descripcion": texto("descripcion", "", 500),
        "subgenre": texto("subgenre", "", 100),
        "resource_type": resource_type,
        "bpm": bpm,
        "scale_key": texto("scale_key", "Am", 20),
        "mood": mood,
        "has_stems": has_stems,
        "has_wav": booleano("has_wav", True),
        "has_midi": booleano("has_midi", False),
        "allow_free_download": booleano("allow_free_download", False),
        "has_watermark": booleano("has_watermark", True),
        "duration": duration,
    }


def register_prepared_r2_track(
    *,
    claim_id,
    user_id,
    draft,
    nombre_track,
    precio,
    genero_id,
    metadata=None,
    foto=None,
    cover_draft=None,
    stems_draft=None,
):
    """
    Persiste una cancion R2 y su preview ya preparada.

    Debe llamarse dentro del contexto que genero el draft.
    El endpoint debe haber verificado autenticacion y permisos.

    No sube originales a R2 ni realiza conexiones externas.
    No sustituye la validacion completa del formulario HTTP.
    """

    metadata = _normalizar_metadata(metadata)

    if foto is not None:
        if not hasattr(foto, "read") or getattr(foto, "size", 0) > 10 * 1024 * 1024:
            raise R2TrackRegistrationError("La portada no es valida o supera 10 MB.")

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


    if cover_draft is not None:
        if not isinstance(cover_draft, R2CoverDraft):
            raise R2TrackRegistrationError(
                "Preparacion de portada invalida."
            )

        if (
            type(cover_draft.owner) is not int
            or cover_draft.owner != user_id
        ):
            raise R2TrackRegistrationError(
                "La portada pertenece a otro usuario."
            )

        if foto is not None:
            raise R2TrackRegistrationError(
                "No se permite combinar portada local y portada R2."
            )

        if (
            type(cover_draft.expected_size) is not int
            or not 0 < cover_draft.expected_size <= 10 * 1024 * 1024
        ):
            raise R2TrackRegistrationError(
                "Tamano de portada invalido."
            )

        patron = (
            rf"[a-f0-9]{{32}}\."
            rf"(?:jpg|jpeg|png|webp)"
        )

        if (
            not isinstance(cover_draft.pending_key, str)
            or not isinstance(cover_draft.private_key, str)
            or not re.fullmatch(
                rf"pending/{user_id}/cover/{patron}",
                cover_draft.pending_key,
            )
            or not re.fullmatch(
                rf"private/{user_id}/cover/{patron}",
                cover_draft.private_key,
            )
        ):
            raise R2TrackRegistrationError(
                "Ruta de portada R2 invalida."
            )

        extension = cover_draft.private_key.rsplit(".", 1)[-1]

        mime_esperado = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
        }.get(extension)

        if cover_draft.expected_mime != mime_esperado:
            raise R2TrackRegistrationError(
                "El MIME de la portada no coincide."
            )


    # El indicador has_stems debe corresponder a un archivo STEMS real.
    if metadata["has_stems"] != (stems_draft is not None):
        raise R2TrackRegistrationError(
            "El indicador STEMS no coincide con el archivo recibido."
        )

    if stems_draft is not None:
        from app.r2_presign import ALLOWED, MAX_BYTES
        if not isinstance(stems_draft, R2StemsDraft):
            raise R2TrackRegistrationError("Preparacion STEMS invalida.")
        if type(stems_draft.owner) is not int or stems_draft.owner != user_id:
            raise R2TrackRegistrationError("Los STEMS pertenecen a otro usuario.")
        if (
            type(stems_draft.expected_size) is not int
            or not 0 < stems_draft.expected_size <= MAX_BYTES["stems"]
        ):
            raise R2TrackRegistrationError("Tamano STEMS invalido.")
        extension = (
            "." + stems_draft.private_key.rsplit(".", 1)[-1].lower()
            if isinstance(stems_draft.private_key, str) and "." in stems_draft.private_key
            else ""
        )
        allowed_mimes = ALLOWED["stems"].get(extension)
        pending_pattern = rf"pending/{user_id}/stems/[a-f0-9]{{32}}{re.escape(extension)}"
        private_pattern = rf"private/{user_id}/stems/[a-f0-9]{{32}}{re.escape(extension)}"
        if (
            extension not in ALLOWED["stems"]
            or not isinstance(stems_draft.pending_key, str)
            or not isinstance(stems_draft.private_key, str)
            or not re.fullmatch(pending_pattern, stems_draft.pending_key)
            or not re.fullmatch(private_pattern, stems_draft.private_key)
            or stems_draft.expected_mime not in allowed_mimes
        ):
            raise R2TrackRegistrationError("Ruta o MIME STEMS invalido.")

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
    nombre_foto = ""
    cancion = None
    almacenamiento = Track._meta.get_field("preview").storage
    almacenamiento_foto = Track._meta.get_field("foto").storage

    try:
        with transaction.atomic():
            cancion = Track(
                nombre_track=nombre_track.strip(),
                original_filename=draft.original_filename,
                precio=precio,
                genero=genero,
                usuario=perfil,
                descripcion=metadata["descripcion"],
                subgenre=metadata["subgenre"],
                resource_type=metadata["resource_type"],
                bpm=metadata["bpm"],
                scale_key=metadata["scale_key"],
                mood=metadata["mood"],
                has_stems=metadata["has_stems"],
                has_wav=metadata["has_wav"],
                has_midi=metadata["has_midi"],
                allow_free_download=metadata["allow_free_download"],
                has_watermark=metadata["has_watermark"],
                duration=metadata["duration"],
                foto=foto,
                track="",
                storage_backend="r2",
                r2_object_key=draft.private_key,
                r2_cover_key=(
                    cover_draft.private_key
                    if cover_draft is not None
                    else ""
                ),
                r2_stems_key=(
                    stems_draft.private_key
                    if stems_draft is not None
                    else ""
                ),
                r2_owner_user_id=user_id,
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
            nombre_foto = cancion.foto.name if cancion.foto else ""

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

        if not nombre_foto and cancion is not None:
            try:
                nombre_foto = cancion.foto.name if cancion.foto else ""
            except Exception:
                nombre_foto = ""

        if estado is not None and estado["status"] == "processing":
            mark_r2_claim_failed(
                claim_id=claim_id,
                user_id=user_id,
            )

            if nombre_preview and estado["track_id"] is None:
                almacenamiento.delete(nombre_preview)
            if nombre_foto and estado["track_id"] is None:
                almacenamiento_foto.delete(nombre_foto)

        raise
