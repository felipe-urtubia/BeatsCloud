import json
import os
import re

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from app.models import Track, Usuario
from app.metadata_validation import validate_d9_field
from app.r2_presign import (
    r2_configuration,
    r2_client,
    r2_uploads_enabled,
)
from app.r2_registration_guard import (
    R2RegistrationGuardError,
    validate_r2_cover_token,
    validate_r2_stems_token,
    validate_r2_track_token,
)
from app.r2_claim_service import R2ClaimConflict
from app.r2_registration_prepare import R2RegistrationPrepareError
from app.r2_upload_workflow import (
    R2UploadWorkflowConflict,
    R2UploadWorkflowError,
    complete_r2_track_upload,
)


def _error(mensaje, codigo):
    return JsonResponse(
        {"detail": mensaje},
        status=codigo,
    )


def _entero_positivo_o_cero(valor):
    if type(valor) is int:
        return valor

    if (
        isinstance(valor, str)
        and re.fullmatch(r"[0-9]{1,10}", valor)
    ):
        return int(valor)

    return None


def _booleano(valor, defecto):
    if valor is None:
        return defecto
    if isinstance(valor, bool):
        return valor
    if type(valor) is int and valor in (0, 1):
        return bool(valor)
    if isinstance(valor, str):
        normalizado = valor.strip().lower()
        if normalizado in ("true", "1", "on"):
            return True
        if normalizado in ("false", "0", "off", ""):
            return False
    return None


def _bucket(config):
    opciones = (
        config.get("R2_BUCKET_NAME"),
        config.get("R2_BUCKET"),
        config.get("bucket_name"),
        config.get("bucket"),
        os.getenv("R2_BUCKET_NAME"),
        os.getenv("R2_BUCKET"),
    )

    for opcion in opciones:
        if isinstance(opcion, str) and opcion.strip():
            return opcion.strip()

    return None


@csrf_protect
@require_POST
def r2_finalize_upload_api(request):
    # Finaliza una subida R2 y registra el Track con sus metadatos.
    if not r2_uploads_enabled():
        return _error("Las subidas R2 estan desactivadas.", 503)

    usuario = request.user
    if not usuario.is_authenticated:
        return _error("Autenticacion requerida.", 401)
    if not usuario.is_active:
        return _error("Cuenta no habilitada.", 403)
    if not Usuario.objects.filter(
        user_id=usuario.pk,
        tipo_usu=Usuario.PRODUCTOR,
    ).exists():
        return _error("Solo los productores pueden subir pistas.", 403)

    content_type = (request.content_type or "").lower()
    if content_type not in ("application/json", "multipart/form-data"):
        return _error("Se requiere application/json o multipart/form-data.", 415)

    limite = 10 * 1024 * 1024 + 32768 if content_type == "multipart/form-data" else 8192
    foto = None

    if content_type == "application/json":
        try:
            cuerpo_json = request.body

            if len(cuerpo_json) > limite:
                return _error("Solicitud demasiado grande.", 413)

            datos = json.loads(cuerpo_json.decode("utf-8"))

        except (UnicodeDecodeError, ValueError):
            return _error("JSON invalido.", 400)

    else:
        # CSRF puede haber procesado request.POST previamente.
        # Nunca acceder a request.body en esta rama multipart.
        longitud = request.META.get("CONTENT_LENGTH")

        if longitud not in (None, "", "0"):
            try:
                tamano_solicitud = int(longitud)
            except (TypeError, ValueError):
                return _error("Longitud de solicitud invalida.", 400)

            if tamano_solicitud < 0:
                return _error("Longitud de solicitud invalida.", 400)

            if tamano_solicitud > limite:
                return _error("Solicitud demasiado grande.", 413)

        else:
            datos_post = request.POST
            archivos_post = request.FILES

            tamano_estimado = sum(
                len(valor.encode("utf-8"))
                for _, valores in datos_post.lists()
                for valor in valores
            ) + sum(
                getattr(archivo, "size", 0)
                for campo in archivos_post
                for archivo in archivos_post.getlist(campo)
            )

            if tamano_estimado > limite:
                return _error("Solicitud demasiado grande.", 413)

        datos = request.POST.dict()

        if set(request.FILES.keys()) - {"foto"}:
            return _error("Archivo no permitido.", 400)

        foto = request.FILES.get("foto")

    campos_requeridos = {"upload_token", "nombre_track", "precio", "genero_id"}
    campos_opcionales = {
        "descripcion", "subgenre", "resource_type", "bpm", "scale_key",
        "mood", "has_stems", "has_wav", "has_midi",
        "allow_free_download", "has_watermark", "duration",
        "cover_upload_token", "stems_upload_token",
    }
    permitidos = campos_requeridos | campos_opcionales

    if (
        not isinstance(datos, dict)
        or not campos_requeridos.issubset(datos)
        or not set(datos).issubset(permitidos)
    ):
        return _error("Campos de registro invalidos.", 400)

    token = datos.get("upload_token")
    nombre = datos.get("nombre_track")
    precio = _entero_positivo_o_cero(datos.get("precio"))
    genero_id = _entero_positivo_o_cero(datos.get("genero_id"))

    if not isinstance(token, str) or not 0 < len(token) <= 4096:
        return _error("Token invalido.", 400)
    if (
        not isinstance(nombre, str)
        or not nombre.strip()
        or len(nombre.strip()) > 200
    ):
        return _error("Nombre de cancion invalido.", 400)
    if (
        precio is None
        or precio > 2147483647
        or genero_id is None
        or genero_id <= 0
    ):
        return _error("Precio o genero invalido.", 400)

    descripcion = datos.get("descripcion", "")
    subgenre = datos.get("subgenre", "")
    scale_key = datos.get("scale_key", "Am")
    if (
        not isinstance(descripcion, str) or len(descripcion) > 500
        or not isinstance(subgenre, str) or len(subgenre) > 100
        or not isinstance(scale_key, str) or not scale_key.strip()
        or len(scale_key.strip()) > 20
    ):
        return _error("Descripcion, subgenero o tonalidad invalidos.", 400)

    bpm = _entero_positivo_o_cero(datos.get("bpm", 140))
    duration = _entero_positivo_o_cero(datos.get("duration", 30))
    if bpm is None or duration is None or not 1 <= duration <= 86400:
        return _error("BPM o duracion invalidos.", 400)

    try:
        resource_type = validate_d9_field(
            "resource_type", datos.get("resource_type", "instrumental")
        )
        bpm = validate_d9_field("bpm", bpm)
        mood = validate_d9_field("mood", datos.get("mood", "Oscuro"))
        has_stems = validate_d9_field(
            "has_stems", datos.get("has_stems", False)
        )
    except ValidationError:
        return _error("Los metadatos musicales no son validos.", 400)

    has_wav = _booleano(datos.get("has_wav"), True)
    has_midi = _booleano(datos.get("has_midi"), False)
    allow_free_download = _booleano(
        datos.get("allow_free_download"), False
    )
    has_watermark = _booleano(datos.get("has_watermark"), True)
    if None in (has_wav, has_midi, allow_free_download, has_watermark):
        return _error("Las opciones de descarga deben ser booleanas.", 400)

    if foto is not None:
        if getattr(foto, "size", 0) > 10 * 1024 * 1024:
            return _error("La portada supera el limite de 10 MB.", 413)
        try:
            foto = Track._meta.get_field("foto").clean(foto, None)
        except ValidationError:
            return _error("La portada no es una imagen valida.", 400)

    metadata = {
        "descripcion": descripcion.strip(),
        "subgenre": subgenre.strip(),
        "resource_type": resource_type,
        "bpm": bpm,
        "scale_key": scale_key.strip(),
        "mood": mood,
        "has_stems": has_stems,
        "has_wav": has_wav,
        "has_midi": has_midi,
        "allow_free_download": allow_free_download,
        "has_watermark": has_watermark,
        "duration": duration,
    }

    try:
        validate_r2_track_token(upload_token=token, user_id=usuario.pk)
    except R2RegistrationGuardError:
        return _error("La autorizacion de subida no es valida.", 400)

    cover_token = datos.get("cover_upload_token")

    if cover_token is not None:
        if foto is not None:
            return _error(
                "No se permite combinar portada local y portada R2.",
                400,
            )

        try:
            validate_r2_cover_token(
                upload_token=cover_token,
                user_id=usuario.pk,
            )
        except R2RegistrationGuardError:
            return _error(
                "La autorizacion de portada no es valida.",
                400,
            )

    try:
        config = r2_configuration()
        if not isinstance(config, dict):
            return _error("Configuracion R2 no disponible.", 503)
        bucket = _bucket(config)
        if not bucket:
            return _error("Bucket R2 no configurado.", 503)
        cliente = r2_client(config)
    except Exception:
        return _error("No se pudo iniciar el almacenamiento R2.", 503)

    stems_token = datos.get("stems_upload_token")
    if stems_token is not None:
        try:
            validate_r2_stems_token(upload_token=stems_token, user_id=usuario.pk)
        except R2RegistrationGuardError:
            return _error("La autorizacion STEMS no es valida.", 400)

    try:
        workflow_kwargs = {
            "client": cliente,
            "bucket": bucket,
            "user_id": usuario.pk,
            "upload_token": token,
            "nombre_track": nombre.strip(),
            "precio": precio,
            "genero_id": genero_id,
            "metadata": metadata,
            "foto": foto,
            "cover_upload_token": cover_token,
        }
        if stems_token is not None:
            workflow_kwargs["stems_upload_token"] = stems_token
        cancion = complete_r2_track_upload(**workflow_kwargs)
    except (R2UploadWorkflowConflict, R2ClaimConflict):
        return _error("La subida ya fue utilizada o esta en proceso.", 409)
    except (R2UploadWorkflowError, R2RegistrationGuardError, R2RegistrationPrepareError):
        return _error("No fue posible validar la subida.", 400)
    except Exception:
        return _error("No fue posible completar la subida.", 500)

    if isinstance(cancion, Track):
        from app.api_shim import ser_track
        payload = ser_track(cancion, usuario)
        payload.update({
            "storage_backend": "r2",
            "media_status": "ready",
        })
    else:
        # Compatibilidad con pruebas unitarias que simulan el modelo.
        payload = {
            "id_track": getattr(cancion, "pk", None),
            "storage_backend": "r2",
            "media_status": "ready",
        }

    return JsonResponse(payload, status=201)

# Estas rutas se usan solo en las pruebas aisladas.
# No estan incorporadas a app.urls.
urlpatterns = [
    path(
        "api/r2/finalize/",
        r2_finalize_upload_api,
        name="r2_finalize_test",
    ),
]
