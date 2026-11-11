from django.http import HttpResponse

from app.r2_presign import (
    r2_configuration,
    r2_client,
)
from app.r2_upload_http import _bucket
from app.r2_private_delivery import (
    authorized_r2_audio_response,
)


def serve_private_r2_audio(
    request,
    track,
    *,
    as_attachment=False,
):
    """
    Conecta las rutas actuales con la entrega R2.

    El endpoint conserva sus comprobaciones de compra.
    El modulo privado vuelve a verificar los permisos.

    Desactivar nuevas subidas no bloquea canciones
    que ya estan almacenadas en R2.
    """

    try:
        config = r2_configuration()

        if not isinstance(config, dict):
            raise ValueError(
                "Configuracion R2 invalida."
            )

        bucket = _bucket(config)

        if not bucket:
            raise ValueError(
                "Bucket R2 no configurado."
            )

        client = r2_client(config)

        if client is None:
            raise ValueError(
                "Cliente R2 no disponible."
            )

    except Exception:
        respuesta = HttpResponse(
            "Almacenamiento temporalmente no disponible.",
            status=503,
        )

        respuesta["Cache-Control"] = "private, no-store"
        respuesta["X-Content-Type-Options"] = "nosniff"

        return respuesta

    return authorized_r2_audio_response(
        request,
        track,
        client=client,
        bucket=bucket,
        as_attachment=as_attachment,
    )
