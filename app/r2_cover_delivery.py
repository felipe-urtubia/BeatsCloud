import re

from botocore.exceptions import ClientError
from django.http import Http404, HttpResponseNotAllowed, StreamingHttpResponse

from app.r2_visibility import is_media_ready


COVER_MIME_BY_EXTENSION = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}
MAX_COVER_BYTES = 10 * 1024 * 1024


def is_owned_r2_cover_key(user_id, key):
    """Comprueba que una clave de portada pertenezca al usuario indicado."""
    if type(user_id) is not int or user_id <= 0 or not isinstance(key, str):
        return False

    patron = (
        rf"private/{user_id}/cover/"
        r"[a-f0-9]{32}\.(?:jpg|jpeg|png|webp)"
    )
    return re.fullmatch(patron, key) is not None


def _iterar_bytes(cuerpo):
    try:
        while True:
            fragmento = cuerpo.read(64 * 1024)
            if not fragmento:
                break
            yield fragmento
    finally:
        cuerpo.close()


def authorized_r2_cover_response(request, track, *, client, bucket):
    """
    Sirve una portada privada de R2 a traves de Django.

    Las portadas de catalogo son publicas, pero el bucket y sus credenciales
    permanecen privados. La clave se obtiene exclusivamente desde Track.
    """
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    if not is_media_ready(track):
        raise Http404("Portada no disponible.")

    propietario = getattr(
        track,
        "r2_owner_user_id",
        None,
    )

    if propietario is None:
        propietario = getattr(
            getattr(track, "usuario", None),
            "user_id",
            None,
        )
    clave = getattr(track, "r2_cover_key", "")

    if not is_owned_r2_cover_key(propietario, clave):
        raise Http404("Portada no disponible.")

    extension = clave.rsplit(".", 1)[-1].lower()
    mime_esperado = COVER_MIME_BY_EXTENSION.get(extension)

    if (
        not mime_esperado
        or not isinstance(bucket, str)
        or not bucket.strip()
        or client is None
    ):
        raise ValueError("Configuracion de portada R2 invalida.")

    try:
        objeto = client.get_object(
            Bucket=bucket,
            Key=clave,
        )
    except ClientError as exc:
        codigo = str(
            exc.response.get("Error", {}).get("Code", "")
        )
        if codigo in {"NoSuchKey", "NotFound", "404"}:
            raise Http404("Portada no disponible.") from exc
        raise

    if not isinstance(objeto, dict):
        raise RuntimeError("Respuesta R2 de portada invalida.")

    cuerpo = objeto.get("Body")
    tamano = objeto.get("ContentLength")
    mime = objeto.get("ContentType")

    if (
        not callable(getattr(cuerpo, "read", None))
        or not callable(getattr(cuerpo, "close", None))
    ):
        raise RuntimeError("Cuerpo R2 de portada invalido.")

    if (
        type(tamano) is not int
        or not 0 < tamano <= MAX_COVER_BYTES
        or mime != mime_esperado
    ):
        cuerpo.close()
        raise RuntimeError("Metadatos R2 de portada invalidos.")

    respuesta = StreamingHttpResponse(
        _iterar_bytes(cuerpo),
        status=200,
        content_type=mime_esperado,
    )
    respuesta["Content-Length"] = str(tamano)
    respuesta["Content-Disposition"] = "inline"
    respuesta["Cache-Control"] = "private, no-store"
    respuesta["X-Content-Type-Options"] = "nosniff"
    return respuesta
