"""Stage 1 of D8: permissioned R2 direct-PUT URL issuance.

No object is trusted until a separate confirm endpoint verifies HEAD and ownership.
This endpoint remains disabled until R2 credentials are configured on the server.
"""
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
from uuid import uuid4

from django.core import signing
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect

from app.models import Usuario


ALLOWED = {
    "track": {
        ".wav": {"audio/wav", "audio/x-wav", "audio/wave"},
        ".flac": {"audio/flac", "audio/x-flac"},
        ".mp3": {"audio/mpeg"},
        ".m4a": {"audio/mp4", "audio/x-m4a"},
        ".aac": {"audio/aac"},
        ".ogg": {"audio/ogg"},
    },
    "stems": {
        ".zip": {"application/zip", "application/x-zip-compressed"},
        ".wav": {"audio/wav", "audio/x-wav", "audio/wave"},
        ".flac": {"audio/flac", "audio/x-flac"},
    },
}
MAX_BYTES = {"track": 750 * 1024 * 1024, "stems": 2 * 1024 * 1024 * 1024}
TOKEN_SALT = "beatcloud-r2-pending-v1"
URL_EXPIRY_SECONDS = 3600



def _load_r2_credentials_from_dotenv():
    from dotenv import dotenv_values

    env_path = Path(__file__).resolve().parent.parent / ".env"

    if not env_path.is_file():
        return

    values = dotenv_values(env_path)

    allowed = (
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME",
    )

    for name in allowed:
        value = values.get(name)

        if isinstance(value, str) and value.strip():
            os.environ.setdefault(name, value)


def r2_uploads_enabled():
    """Indica si se permiten nuevas subidas R2."""
    return os.environ.get("R2_UPLOADS_ENABLED", "").strip().lower() == "true"


def r2_configuration():
    _load_r2_credentials_from_dotenv()
    names = ("R2_ACCOUNT_ID", "R2_BUCKET_NAME", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    config = {name: os.environ.get(name, "").strip() for name in names}
    if not all(config.values()):
        return None
    account = config["R2_ACCOUNT_ID"]
    if len(account) != 32 or not all(char in "0123456789abcdefABCDEF" for char in account):
        return None
    return config


def r2_client(config):
    import boto3
    from botocore.config import Config
    return boto3.client(
        "s3",
        endpoint_url="https://" + config["R2_ACCOUNT_ID"] + ".r2.cloudflarestorage.com",
        region_name="auto",
        aws_access_key_id=config["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=config["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def validate_upload(data):
    if not isinstance(data, dict):
        raise ValueError("El cuerpo debe ser un objeto JSON.")
    kind, filename, mime, size = (
        data.get("kind"), data.get("filename"), data.get("content_type"), data.get("size")
    )
    if not isinstance(kind, str) or kind not in ALLOWED:
        raise ValueError("El tipo de subida no es valido.")
    if not isinstance(filename, str) or not filename or len(filename) > 180:
        raise ValueError("Nombre de archivo no valido.")
    if filename in (".", "..") or "/" in filename or chr(92) in filename or chr(0) in filename:
        raise ValueError("Nombre de archivo no valido.")
    ext = PurePosixPath(filename).suffix.lower()
    if ext not in ALLOWED[kind] or not isinstance(mime, str) or mime not in ALLOWED[kind][ext]:
        raise ValueError("Formato o Content-Type no permitido.")
    if type(size) is not int or size <= 0 or size > MAX_BYTES[kind]:
        raise ValueError("Tamano de archivo no permitido.")
    return kind, ext, mime, size


@csrf_protect
def r2_presign_upload_api(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Metodo no permitido."}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Autenticacion requerida."}, status=401)
    if not Usuario.objects.filter(user=request.user, tipo_usu=Usuario.PRODUCTOR).exists():
        return JsonResponse({"detail": "Solo productores pueden subir archivos."}, status=403)
    if not r2_uploads_enabled():
        return JsonResponse({"detail": "Subidas R2 desactivadas."}, status=503)
    if request.content_type != "application/json" or len(request.body) > 4096:
        return JsonResponse({"detail": "Se requiere JSON valido."}, status=400)
    try:
        data = json.loads(request.body)
        kind, ext, mime, size = validate_upload(data)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": "Metadatos de archivo invalidos."}, status=400)
    config = r2_configuration()
    if config is None:
        return JsonResponse({"detail": "Subida R2 no configurada."}, status=503)
    key = "pending/{}/{}/{}{}".format(request.user.pk, kind, uuid4().hex, ext)
    try:
        url = r2_client(config).generate_presigned_url(
            "put_object",
            Params={"Bucket": config["R2_BUCKET_NAME"], "Key": key, "ContentType": mime},
            ExpiresIn=URL_EXPIRY_SECONDS,
            HttpMethod="PUT",
        )
    except Exception:
        # Never include SDK exceptions or credential data in a client response.
        return JsonResponse({"detail": "No fue posible autorizar la subida."}, status=503)
    token = signing.dumps(
        {"owner": request.user.pk, "key": key, "size": size, "kind": kind, "mime": mime},
        salt=TOKEN_SALT,
    )
    response = JsonResponse({
        "method": "PUT", "url": url, "headers": {"Content-Type": mime},
        "upload_token": token, "expires_in": URL_EXPIRY_SECONDS,
    })
    response["Cache-Control"] = "no-store"
    return response
@csrf_protect
def r2_confirm_upload_api(request):
    """Comprueba via HEAD un PUT temporal, sin asociarlo aun a un Track.

    No finaliza la subida: la URL PUT puede reutilizarse hasta expirar. La
    futura fase de registro debera promover una version verificada a un objeto
    permanente y validar el contenido multimedia real (no solo MIME declarado).
    """
    import re
    if request.method != "POST":
        return JsonResponse({"detail": "Metodo no permitido."}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Autenticacion requerida."}, status=401)
    if not Usuario.objects.filter(user=request.user, tipo_usu=Usuario.PRODUCTOR).exists():
        return JsonResponse({"detail": "Solo productores pueden confirmar archivos."}, status=403)
    if not r2_uploads_enabled():
        return JsonResponse({"detail": "Subidas R2 desactivadas."}, status=503)
    if request.content_type != "application/json" or len(request.body) > 8192:
        return JsonResponse({"detail": "Se requiere JSON valido."}, status=400)
    try:
        data = json.loads(request.body)
        token = data.get("upload_token") if isinstance(data, dict) else None
        if not isinstance(token, str) or not token or len(token) > 4096:
            raise ValueError("Token ausente")
        payload = signing.loads(token, salt=TOKEN_SALT, max_age=URL_EXPIRY_SECONDS)
        if not isinstance(payload, dict) or set(payload) != {"owner", "key", "size", "kind", "mime"}:
            raise ValueError("Token malformado")
        owner, key, kind, mime, size = (payload[k] for k in ("owner", "key", "kind", "mime", "size"))
        if type(owner) is not int or owner != request.user.pk:
            raise ValueError("Token no pertenece al usuario")
        if not isinstance(key, str) or not isinstance(kind, str) or kind not in ALLOWED:
            raise ValueError("Ruta incorrecta")
        if not re.fullmatch(r"pending/[0-9]+/(track|stems)/[a-f0-9]{32}\.[a-z0-9]+", key):
            raise ValueError("Ruta incorrecta")
        if not key.startswith(f"pending/{owner}/{kind}/"):
            raise ValueError("Ruta incorrecta")
        extension = PurePosixPath(key).suffix.lower()
        if not isinstance(mime, str) or mime not in ALLOWED[kind].get(extension, set()):
            raise ValueError("Tipo incorrecto")
        if type(size) is not int or size <= 0 or size > MAX_BYTES[kind]:
            raise ValueError("Tamano incorrecto")
    except (ValueError, TypeError, signing.BadSignature, UnicodeDecodeError):
        return JsonResponse({"detail": "Token de subida invalido o caducado."}, status=400)

    config = r2_configuration()
    if config is None:
        return JsonResponse({"detail": "Subida R2 no configurada."}, status=503)
    try:
        metadata = r2_client(config).head_object(Bucket=config["R2_BUCKET_NAME"], Key=key)
    except Exception as exc:
        # Los errores 404/NoSuchKey significan que el objeto aun no se encuentra.
        error_info = getattr(exc, "response", None)
        code = str(error_info.get("Error", {}).get("Code", "")) if isinstance(error_info, dict) else ""
        if code in {"404", "NoSuchKey", "NotFound"}:
            return JsonResponse({"detail": "El archivo aun no existe en R2."}, status=409)
        return JsonResponse({"detail": "No se pudo verificar el archivo en R2."}, status=503)
    if not isinstance(metadata, dict):
        return JsonResponse({"detail": "Respuesta de R2 no valida."}, status=503)
    if (type(metadata.get("ContentLength")) is not int
            or metadata["ContentLength"] != size
            or metadata.get("ContentType") != mime):
        return JsonResponse({"detail": "El archivo de R2 no coincide con la autorizacion."}, status=409)
    response = JsonResponse({
        "verified": True,
        "kind": kind,
        "size": size,
        "content_type": mime,
        "detail": "Objeto temporal comprobado. Pendiente de registro y validacion multimedia.",
    })
    response["Cache-Control"] = "no-store"
    return response
