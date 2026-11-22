from django.http import Http404, HttpResponse, HttpResponseRedirect
from botocore.exceptions import ClientError

from app.r2_presign import r2_client, r2_configuration
from app.r2_preview_storage import (
    MAX_PREVIEW_BYTES,
    PREVIEW_KEY_PATTERN,
)


def _storage_unavailable():
    response = HttpResponse(
        "Almacenamiento temporalmente no disponible.",
        status=503,
    )
    response["Cache-Control"] = "no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def r2_preview_response(track):
    """
    Entrega una preview R2 mediante URL GET firmada.

    Solo permite claves del espacio previews/.
    Nunca firma claves del audio original privado.
    """

    key = getattr(track.preview, "name", "")

    if not isinstance(key, str) or not PREVIEW_KEY_PATTERN.fullmatch(key):
        raise Http404("Preview no disponible.")

    config = r2_configuration()

    if not config:
        return _storage_unavailable()

    try:
        bucket = config["R2_BUCKET_NAME"]
        client = r2_client(config)

        metadata = client.head_object(
            Bucket=bucket,
            Key=key,
        )

        size = int(metadata.get("ContentLength", 0))

        if not 0 < size <= MAX_PREVIEW_BYTES:
            raise Http404("Preview no disponible.")

        signed_url = client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket,
                "Key": key,
            },
            ExpiresIn=600,
            HttpMethod="GET",
        )

        if not isinstance(signed_url, str) or not signed_url.startswith("https://"):
            return _storage_unavailable()

    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))

        if code in ("404", "NoSuchKey", "NotFound"):
            raise Http404("Preview no disponible.") from exc

        return _storage_unavailable()

    except Http404:
        raise

    except Exception:
        return _storage_unavailable()

    response = HttpResponseRedirect(signed_url)
    response["Cache-Control"] = "no-store"
    response["X-Content-Type-Options"] = "nosniff"

    return response
