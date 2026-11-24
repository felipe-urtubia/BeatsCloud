"""Cambio de cuentas previamente autenticadas durante una sesion Django."""

import json
import secrets

from django.conf import settings
from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    authenticate,
    get_user_model,
    login as auth_login,
)
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from .auth_throttle import reserve_attempt, clear_attempts


SESSION_KEY = "_bc_authorized_accounts_v1"
MAX_ACCOUNTS = 5


def error(message, status):
    return JsonResponse({"detail": message}, status=status)


def read_json(request):
    if len(request.body) > 4096:
        return None

    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return None

    return data if isinstance(data, dict) else None


def current_backend(request):
    backend = request.session.get(BACKEND_SESSION_KEY)

    if backend in settings.AUTHENTICATION_BACKENDS:
        return backend

    return settings.AUTHENTICATION_BACKENDS[0]


def valid_accounts(request):
    """Solo conserva cuentas activas con autorizacion aun valida."""
    raw = request.session.get(SESSION_KEY, [])
    entries = []
    seen = set()

    if isinstance(raw, list):
        for item in raw[:MAX_ACCOUNTS]:
            if not isinstance(item, dict):
                continue

            uid = item.get("id")
            auth_hash = item.get("auth_hash")
            backend = item.get("backend")

            if (
                type(uid) is not int
                or uid <= 0
                or not isinstance(auth_hash, str)
                or not isinstance(backend, str)
                or backend not in settings.AUTHENTICATION_BACKENDS
                or uid in seen
            ):
                continue

            user = get_user_model().objects.filter(
                pk=uid,
                is_active=True,
            ).first()

            if user is None:
                continue

            if not secrets.compare_digest(
                user.get_session_auth_hash(),
                auth_hash,
            ):
                continue

            entries.append({
                "id": user.pk,
                "auth_hash": auth_hash,
                "backend": backend,
            })
            seen.add(uid)

    # La identidad actualmente autenticada siempre puede permanecer
    # en la lista; Django ya valido su propia cookie de sesion.
    current = request.user

    if current.pk not in seen:
        entries.insert(0, {
            "id": current.pk,
            "auth_hash": current.get_session_auth_hash(),
            "backend": current_backend(request),
        })

    return entries[:MAX_ACCOUNTS]


def public_accounts(request, entries):
    ids = [entry["id"] for entry in entries]

    users = {
        user.pk: user
        for user in get_user_model().objects.filter(
            pk__in=ids,
            is_active=True,
        )
    }

    return [
        {
            "id": entry["id"],
            "username": users[entry["id"]].username,
            "is_current": entry["id"] == request.user.pk,
        }
        for entry in entries
        if entry["id"] in users
    ]


@never_cache
def account_list_api(request):
    if request.method != "GET":
        return error("Metodo no permitido.", 405)

    if not request.user.is_authenticated:
        return error("Autenticacion requerida.", 401)

    entries = valid_accounts(request)

    return JsonResponse({
        "accounts": public_accounts(request, entries),
        "active_user_id": request.user.pk,
    })


@never_cache
def account_add_api(request):
    if request.method != "POST":
        return error("Metodo no permitido.", 405)

    if not request.user.is_authenticated:
        return error("Autenticacion requerida.", 401)

    data = read_json(request)

    if data is None:
        return error("Solicitud JSON invalida.", 400)

    username = data.get("username")
    password = data.get("password")

    if (
        not isinstance(username, str)
        or not isinstance(password, str)
        or not username.strip()
        or not password
        or len(username) > 150
        or len(password) > 1024
    ):
        return error("Ingresa usuario y contrasena validos.", 400)

    limit_response = reserve_attempt(request, username.strip(), actor_scoped=True)
    if limit_response is not None:
        return limit_response

    user = authenticate(
        request,
        username=username.strip(),
        password=password,
    )

    if user is None or not user.is_active:
        return error("Credenciales incorrectas.", 401)

    entries = valid_accounts(request)
    entries = [item for item in entries if item["id"] != user.pk]

    if len(entries) >= MAX_ACCOUNTS:
        return error("Alcanzaste el limite de cuentas agregadas.", 409)

    backend = getattr(user, "backend", None)

    if backend not in settings.AUTHENTICATION_BACKENDS:
        return error("Backend de autenticacion no permitido.", 403)

    entries.append({
        "id": user.pk,
        "auth_hash": user.get_session_auth_hash(),
        "backend": backend,
    })

    request.session[SESSION_KEY] = entries
    clear_attempts(request, username.strip(), actor_scoped=True)

    # Autenticar una cuenta adicional NO cambia la identidad activa.
    return JsonResponse({
        "accounts": public_accounts(request, entries),
        "active_user_id": request.user.pk,
    })


@never_cache
def account_switch_api(request):
    if request.method != "POST":
        return error("Metodo no permitido.", 405)

    if not request.user.is_authenticated:
        return error("Autenticacion requerida.", 401)

    data = read_json(request)

    if data is None or type(data.get("user_id")) is not int:
        return error("Identificador de cuenta invalido.", 400)

    target_id = data["user_id"]
    entries = valid_accounts(request)

    selected = next(
        (item for item in entries if item["id"] == target_id),
        None,
    )

    if selected is None:
        return error("Cuenta no autorizada para esta sesion.", 403)

    target = get_user_model().objects.filter(
        pk=target_id,
        is_active=True,
    ).first()

    if target is None or not secrets.compare_digest(
        target.get_session_auth_hash(),
        selected["auth_hash"],
    ):
        return error("La autorizacion de esta cuenta expiro.", 403)

    # Django puede renovar la sesion o reemplazarla por completo
    # al cambiar de identidad. Restauramos SOLO las autorizaciones
    # validadas antes del cambio, nunca credenciales ni claves.
    auth_login(request, target, backend=selected["backend"])
    request.user = target
    request.session[SESSION_KEY] = entries

    return JsonResponse({
        "accounts": public_accounts(request, entries),
        "active_user_id": target.pk,
    })
