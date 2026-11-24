"""Validacion de tokens Cloudflare Turnstile en el servidor."""

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SITEVERIFY_URL = (
    "https://challenges.cloudflare.com/turnstile/v0/siteverify"
)


def registration_turnstile_required():
    value = os.environ.get(
        "TURNSTILE_REGISTRATION_ENABLED", "0"
    ).strip().lower()

    if value in ("1", "true"):
        return True

    if value in ("0", "false"):
        return False

    raise ValueError(
        "TURNSTILE_REGISTRATION_ENABLED debe ser 0 o 1."
    )


def verify_registration_turnstile(token):
    """Devuelve True solo si Cloudflare valida el token."""

    if not isinstance(token, str):
        return False

    if not token or len(token) > 2048:
        return False

    secret = os.environ.get("TURNSTILE_SECRET_KEY", "").strip()

    # Sin credenciales no se permite omitir la verificacion.
    if not secret:
        return False

    payload = urlencode({
        "secret": secret,
        "response": token,
    }).encode("utf-8")

    request = Request(
        SITEVERIFY_URL,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=5) as response:
            result = json.loads(response.read(8192))
    except (OSError, ValueError, TypeError):
        return False

    if not isinstance(result, dict):
        return False

    if result.get("success") is not True:
        return False

    allowed = {
        name.strip().lower()
        for name in os.environ.get(
            "TURNSTILE_ALLOWED_HOSTNAMES", ""
        ).split(",")
        if name.strip()
    }

    if allowed:
        hostname = result.get("hostname")

        if not isinstance(hostname, str):
            return False

        if hostname.lower() not in allowed:
            return False

    return True
