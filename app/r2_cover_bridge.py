import logging

from django.http import Http404, HttpResponse

from app.r2_presign import r2_configuration, r2_client
from app.r2_upload_http import _bucket
from app.r2_cover_delivery import authorized_r2_cover_response


logger = logging.getLogger(__name__)


def serve_private_r2_cover(request, track):
    """Resuelve la configuracion R2 y entrega la portada sin exponer URLs."""
    try:
        config = r2_configuration()
        if not isinstance(config, dict):
            raise ValueError("Configuracion R2 no disponible.")

        bucket = _bucket(config)
        if not isinstance(bucket, str) or not bucket.strip():
            raise ValueError("Bucket R2 no configurado.")

        client = r2_client(config)
        if client is None:
            raise ValueError("Cliente R2 no disponible.")
    except Exception:
        logger.exception("No fue posible iniciar la entrega de portada R2.")
        response = HttpResponse(
            "Almacenamiento temporalmente no disponible.",
            status=503,
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response

    try:
        return authorized_r2_cover_response(
            request,
            track,
            client=client,
            bucket=bucket,
        )
    except Http404:
        raise
    except Exception:
        logger.exception("Fallo la entrega de una portada R2.")
        response = HttpResponse(
            "Portada temporalmente no disponible.",
            status=503,
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
