"""Carga y entrega protegida de archivos STEMS en Cloudflare R2."""
import re
from dataclasses import dataclass

from botocore.exceptions import ClientError
from django.http import (
    Http404, HttpResponse, HttpResponseForbidden,
    HttpResponseNotAllowed, StreamingHttpResponse,
)
from django.utils.http import content_disposition_header

from app.r2_presign import ALLOWED, MAX_BYTES, r2_configuration, r2_client
from app.r2_promotion import promote_pending_object
from app.r2_registration_guard import validate_r2_stems_token
from app.r2_registration_prepare import R2RegistrationPrepareError
from app.r2_visibility import is_media_ready


@dataclass(frozen=True)
class R2StemsDraft:
    owner: int
    pending_key: str
    private_key: str
    expected_size: int
    expected_mime: str
    original_filename: str = ""


def prepare_r2_stems_upload(*, client, bucket, user_id, upload_token):
    """Promueve STEMS temporal a una clave privada e impredecible."""
    auth = validate_r2_stems_token(upload_token=upload_token, user_id=user_id)
    try:
        promoted = promote_pending_object(
            client=client, bucket=bucket, owner=auth.owner, kind="stems",
            pending_key=auth.pending_key, expected_size=auth.expected_size,
            expected_mime=auth.expected_mime,
        )
    except Exception as exc:
        raise R2RegistrationPrepareError(
            "No fue posible preparar el archivo STEMS."
        ) from exc

    private_key = promoted.get("private_key") if isinstance(promoted, dict) else None
    extension = auth.pending_key.rsplit(".", 1)[-1].lower()
    pattern = rf"private/{auth.owner}/stems/[a-f0-9]{{32}}\.{re.escape(extension)}"
    valid = (
        isinstance(private_key, str)
        and re.fullmatch(pattern, private_key) is not None
        and promoted.get("kind") == "stems"
        and promoted.get("size") == auth.expected_size
        and promoted.get("content_type") == auth.expected_mime
    )
    if not valid:
        if isinstance(private_key, str) and private_key.startswith(f"private/{auth.owner}/stems/"):
            try:
                client.delete_object(Bucket=bucket, Key=private_key)
            except Exception:
                pass
        raise R2RegistrationPrepareError(
            "La copia privada STEMS no coincide con la autorizacion."
        )

    return R2StemsDraft(
        owner=auth.owner, pending_key=auth.pending_key, private_key=private_key,
        expected_size=auth.expected_size, expected_mime=auth.expected_mime,
        original_filename=auth.original_filename,
    )


def _chunks(body):
    try:
        while True:
            chunk = body.read(64 * 1024)
            if not chunk:
                break
            yield chunk
    finally:
        body.close()


def r2_stems_download_api(request, track_id):
    """Entrega STEMS solo al productor propietario o comprador autorizado."""
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    if not request.user.is_authenticated:
        return HttpResponse("Autenticacion requerida.", status=401)

    from app.models import Track
    from app.api_shim import _puede_escuchar_completo

    track = Track.objects.select_related("usuario").filter(id_track=track_id).first()
    if (
        track is None or not is_media_ready(track)
        or getattr(track, "storage_backend", "") != "r2"
        or not getattr(track, "has_stems", False)
    ):
        raise Http404("STEMS no disponibles.")
    if not _puede_escuchar_completo(request, track):
        return HttpResponseForbidden("No tienes permiso para descargar los STEMS de esta pista.")

    owner = getattr(getattr(track, "usuario", None), "user_id", None)
    key = getattr(track, "r2_stems_key", "")
    if type(owner) is not int or owner <= 0 or not isinstance(key, str):
        raise Http404("STEMS no disponibles.")
    extension = "." + key.rsplit(".", 1)[-1].lower() if "." in key else ""
    pattern = rf"private/{owner}/stems/[a-f0-9]{{32}}{re.escape(extension)}"
    if extension not in ALLOWED["stems"] or not re.fullmatch(pattern, key):
        raise Http404("STEMS no disponibles.")

    config = r2_configuration()
    if not isinstance(config, dict) or not config.get("R2_BUCKET_NAME"):
        return HttpResponse("Almacenamiento R2 no disponible.", status=503)
    try:
        obj = r2_client(config).get_object(Bucket=config["R2_BUCKET_NAME"], Key=key)
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in ("NoSuchKey", "NotFound", "404"):
            raise Http404("STEMS no disponibles.") from exc
        return HttpResponse("No fue posible recuperar los STEMS.", status=503)
    except Exception:
        return HttpResponse("No fue posible conectar con R2.", status=503)

    body = obj.get("Body")
    size = obj.get("ContentLength")
    if (
        type(size) is not int or size <= 0 or size > MAX_BYTES["stems"]
        or not callable(getattr(body, "read", None))
        or not callable(getattr(body, "close", None))
    ):
        if callable(getattr(body, "close", None)):
            body.close()
        return HttpResponse("Archivo STEMS no valido.", status=502)

    mime = {".zip": "application/zip", ".wav": "audio/wav", ".flac": "audio/flac"}[extension]
    filename = f"BeatCloud_track_{track.pk}_STEMS{extension}"
    response = StreamingHttpResponse(_chunks(body), content_type=mime)
    response["Content-Length"] = str(size)
    response["Content-Disposition"] = content_disposition_header(True, filename)
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
