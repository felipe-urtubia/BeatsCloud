"""Limitacion de intentos mediante una tabla compartida de Django."""

import hashlib
import hmac
import ipaddress
import math
import os
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone

from .models import AuthAttemptThrottle


MAX_ATTEMPTS = 5
WINDOW = timedelta(minutes=15)


def _request_ip_identity(request):
    """Identifica la IP sin confiar en proxies no configurados."""

    remote = request.META.get("REMOTE_ADDR", "")

    try:
        fallback = str(ipaddress.ip_address(remote))
    except (ValueError, TypeError):
        fallback = "unknown"

    # Solo habilitar si el servicio esta detras del
    # ingreso de confianza de Render/Cloudflare.
    trusted_render = (
        os.environ.get("AUTH_TRUST_RENDER_CF_IP") == "1"
        and bool(os.environ.get("RENDER_SERVICE_ID"))
    )

    if not trusted_render:
        return fallback

    forwarded = request.META.get(
        "HTTP_CF_CONNECTING_IP", ""
    )

    try:
        address = ipaddress.ip_address(forwarded)
    except (ValueError, TypeError):
        return fallback

    # No aceptar direcciones internas o reservadas
    # como identidad publica del visitante.
    if not address.is_global:
        return fallback

    return str(address)


def _bucket_key(request, username, *, actor_scoped=False):
    if actor_scoped:
        actor = getattr(request, "user", None)

        if (
            actor is None
            or not actor.is_authenticated
            or actor.pk is None
        ):
            raise ValueError(
                "Se requiere una cuenta autenticada."
            )

        identity = f"actor:{actor.pk}"
    else:
        identity = _request_ip_identity(request)

    normalized = username.strip().casefold()
    message = (
        f"auth-v1\0{identity}\0{normalized}"
    ).encode("utf-8")

    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()


def reserve_attempt(request, username, *, actor_scoped=False):
    """Reserva atomicamente un intento antes de autenticar.

    Los cinco primeros intentos de una ventana se permiten.
    El sexto devuelve 429, independientemente del password.
    Un login correcto elimina el contador mediante clear_attempts.
    """
    if not isinstance(username, str) or not username.strip():
        return None

    key = _bucket_key(request, username, actor_scoped=actor_scoped)

    with transaction.atomic():
        now = timezone.now()

        entry, _ = (
            AuthAttemptThrottle.objects
            .select_for_update()
            .get_or_create(
                key=key,
                defaults={
                    "attempts": 0,
                    "reset_at": now + WINDOW,
                },
            )
        )

        if entry.reset_at <= now:
            entry.attempts = 0
            entry.reset_at = now + WINDOW

        if entry.attempts >= MAX_ATTEMPTS:
            seconds = max(
                1,
                math.ceil((entry.reset_at - now).total_seconds()),
            )

            response = JsonResponse(
                {
                    "detail": (
                        "Demasiados intentos de autenticacion. "
                        "Intentalo mas tarde."
                    )
                },
                status=429,
            )
            response["Retry-After"] = str(seconds)
            return response

        entry.attempts += 1
        entry.save(update_fields=["attempts", "reset_at"])

    return None


def clear_attempts(request, username, *, actor_scoped=False):
    """Reinicia el contador despues de una autenticacion exitosa."""
    if not isinstance(username, str) or not username.strip():
        return

    AuthAttemptThrottle.objects.filter(
        key=_bucket_key(request, username, actor_scoped=actor_scoped)
    ).delete()
