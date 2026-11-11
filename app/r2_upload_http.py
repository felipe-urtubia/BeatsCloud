import json
import os
import re

from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from app.models import Usuario
from app.r2_presign import (
    r2_configuration,
    r2_client,
    r2_uploads_enabled,
)
from app.r2_registration_guard import (
    R2RegistrationGuardError,
    validate_r2_track_token,
)
from app.r2_claim_service import R2ClaimConflict
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
    """
    Endpoint protegido para finalizar subidas R2.

    Esta ruta permanece fuera de app.urls hasta
    completar las pruebas de integracion.
    """

    if not r2_uploads_enabled():
        return _error(
            "Las subidas R2 estan desactivadas.",
            503,
        )

    usuario = request.user

    if not usuario.is_authenticated:
        return _error(
            "Autenticacion requerida.",
            401,
        )

    if not usuario.is_active:
        return _error(
            "Cuenta no habilitada.",
            403,
        )

    if not Usuario.objects.filter(
        user_id=usuario.pk,
        tipo_usu=Usuario.PRODUCTOR,
    ).exists():
        return _error(
            "Solo los productores pueden subir pistas.",
            403,
        )

    if request.content_type != "application/json":
        return _error(
            "Se requiere application/json.",
            415,
        )

    if len(request.body) > 8192:
        return _error(
            "Solicitud demasiado grande.",
            413,
        )

    try:
        datos = json.loads(
            request.body.decode("utf-8")
        )
    except (UnicodeDecodeError, ValueError):
        return _error(
            "JSON invalido.",
            400,
        )

    campos = {
        "upload_token",
        "nombre_track",
        "precio",
        "genero_id",
    }

    if (
        not isinstance(datos, dict)
        or set(datos) != campos
    ):
        return _error(
            "Campos de registro invalidos.",
            400,
        )

    token = datos["upload_token"]
    nombre = datos["nombre_track"]
    precio = _entero_positivo_o_cero(
        datos["precio"]
    )
    genero_id = _entero_positivo_o_cero(
        datos["genero_id"]
    )

    if (
        not isinstance(token, str)
        or not 0 < len(token) <= 4096
    ):
        return _error(
            "Token invalido.",
            400,
        )

    if (
        not isinstance(nombre, str)
        or not nombre.strip()
        or len(nombre.strip()) > 200
    ):
        return _error(
            "Nombre de cancion invalido.",
            400,
        )

    if (
        precio is None
        or precio > 2147483647
        or genero_id is None
        or genero_id <= 0
    ):
        return _error(
            "Precio o genero invalido.",
            400,
        )

    try:
        validate_r2_track_token(
            upload_token=token,
            user_id=usuario.pk,
        )
    except R2RegistrationGuardError:
        return _error(
            "La autorizacion de subida no es valida.",
            400,
        )

    try:
        config = r2_configuration()

        if not isinstance(config, dict):
            return _error(
                "Configuracion R2 no disponible.",
                503,
            )

        bucket = _bucket(config)

        if not bucket:
            return _error(
                "Bucket R2 no configurado.",
                503,
            )

        cliente = r2_client(config)

    except Exception:
        return _error(
            "No se pudo iniciar el almacenamiento R2.",
            503,
        )

    try:
        cancion = complete_r2_track_upload(
            client=cliente,
            bucket=bucket,
            user_id=usuario.pk,
            upload_token=token,
            nombre_track=nombre.strip(),
            precio=precio,
            genero_id=genero_id,
        )

    except (
        R2UploadWorkflowConflict,
        R2ClaimConflict,
    ):
        return _error(
            "La subida ya fue utilizada o esta en proceso.",
            409,
        )

    except (
        R2UploadWorkflowError,
        R2RegistrationGuardError,
    ):
        return _error(
            "No fue posible validar la subida.",
            400,
        )

    except Exception:
        return _error(
            "No fue posible completar la subida.",
            500,
        )

    return JsonResponse(
        {
            "id_track": cancion.pk,
            "storage_backend": "r2",
            "media_status": "ready",
        },
        status=201,
    )


# Estas rutas se usan solo en las pruebas aisladas.
# No estan incorporadas a app.urls.
urlpatterns = [
    path(
        "api/r2/finalize/",
        r2_finalize_upload_api,
        name="r2_finalize_test",
    ),
]
