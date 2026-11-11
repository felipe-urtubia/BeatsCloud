import mimetypes
import re

from botocore.exceptions import ClientError
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    StreamingHttpResponse,
)

from app.r2_presign import ALLOWED
from app.r2_visibility import is_media_ready


def _validar_clave_privada(track):
    propietario = getattr(
        getattr(track, "usuario", None),
        "user_id",
        None,
    )

    clave = getattr(track, "r2_object_key", None)

    if (
        type(propietario) is not int
        or propietario <= 0
        or not isinstance(clave, str)
    ):
        raise Http404("Audio no disponible.")

    patron = (
        rf"private/{propietario}/track/"
        r"[a-f0-9]{32}\.[a-z0-9]+"
    )

    if not re.fullmatch(patron, clave):
        raise Http404("Audio no disponible.")

    extension = "." + clave.rsplit(".", 1)[-1]

    if extension not in ALLOWED["track"]:
        raise Http404("Formato de audio no disponible.")

    return clave


def _validar_rango(request):
    valor = request.headers.get("Range")

    if valor is None:
        return None

    if len(valor) > 64:
        return False

    coincidencia = re.fullmatch(
        r"bytes=([0-9]*)-([0-9]*)",
        valor,
    )

    if coincidencia is None:
        return False

    inicio, final = coincidencia.groups()

    if not inicio and not final:
        return False

    if (
        len(inicio) > 18
        or len(final) > 18
    ):
        return False

    if inicio and final and int(final) < int(inicio):
        return False

    if not inicio and int(final) == 0:
        return False

    return valor


def _iterar_audio(cuerpo):
    try:
        while True:
            fragmento = cuerpo.read(64 * 1024)

            if not fragmento:
                break

            yield fragmento

    finally:
        cuerpo.close()


def authorized_r2_audio_response(
    request,
    track,
    *,
    client,
    bucket,
    as_attachment=False,
):
    """
    Entrega audio privado R2 despues de verificar permisos.

    Reutiliza la autorizacion existente de BeatCloud.
    No expone enlaces firmados ni credenciales.
    No modifica datos ni archivos locales.
    """

    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    if (
        not is_media_ready(track)
        or track.storage_backend != "r2"
    ):
        raise Http404("Audio no disponible.")

    if (
        as_attachment
        and not request.user.is_authenticated
    ):
        return HttpResponseForbidden(
            "Debes iniciar sesion para descargar."
        )

    from app.api_shim import _puede_escuchar_completo

    if not _puede_escuchar_completo(request, track):
        return HttpResponseForbidden(
            "No tienes permiso para acceder al audio completo."
        )

    clave = _validar_clave_privada(track)

    if (
        not isinstance(bucket, str)
        or not bucket.strip()
        or client is None
    ):
        raise ValueError(
            "Configuracion del almacenamiento invalida."
        )

    rango = _validar_rango(request)

    if rango is False:
        return HttpResponse(status=416)

    parametros = {
        "Bucket": bucket,
        "Key": clave,
    }

    if rango is not None:
        parametros["Range"] = rango

    try:
        objeto = client.get_object(**parametros)

    except ClientError as exc:
        codigo = str(
            exc.response.get(
                "Error", {}
            ).get("Code", "")
        )

        if codigo in (
            "NoSuchKey",
            "NotFound",
            "404",
        ):
            raise Http404(
                "Audio no disponible."
            ) from exc

        if codigo in (
            "InvalidRange",
            "416",
            "RequestedRangeNotSatisfiable",
        ):
            return HttpResponse(status=416)

        raise

    cuerpo = objeto["Body"]
    tamano = objeto.get("ContentLength")

    if (
        type(tamano) is not int
        or tamano < 0
        or not callable(getattr(cuerpo, "read", None))
        or not callable(getattr(cuerpo, "close", None))
    ):
        if callable(getattr(cuerpo, "close", None)):
            cuerpo.close()

        raise RuntimeError(
            "Respuesta R2 incompatible."
        )

    estado = 200
    contenido_rango = None

    if rango is not None:
        contenido_rango = objeto.get("ContentRange")

        coincidencia = (
            re.fullmatch(
                r"bytes ([0-9]+)-([0-9]+)/([0-9]+)",
                contenido_rango,
            )
            if isinstance(contenido_rango, str)
            else None
        )

        if (
            coincidencia is None
            or int(coincidencia.group(2))
            < int(coincidencia.group(1))
            or tamano != (
                int(coincidencia.group(2))
                - int(coincidencia.group(1))
                + 1
            )
        ):
            cuerpo.close()

            raise RuntimeError(
                "R2 no confirmo correctamente el rango."
            )

        estado = 206

    nombre = clave.rsplit("/", 1)[-1]

    tipo = (
        mimetypes.guess_type(nombre)[0]
        or "application/octet-stream"
    )

    respuesta = StreamingHttpResponse(
        _iterar_audio(cuerpo),
        status=estado,
        content_type=tipo,
    )

    respuesta["Content-Length"] = str(tamano)
    respuesta["Accept-Ranges"] = "bytes"
    respuesta["Cache-Control"] = "private, no-store"
    respuesta["X-Content-Type-Options"] = "nosniff"

    disposicion = (
        "attachment" if as_attachment else "inline"
    )

    respuesta["Content-Disposition"] = (
        f'{disposicion}; filename="{nombre}"'
    )

    if contenido_rango is not None:
        respuesta["Content-Range"] = contenido_rango

    return respuesta
