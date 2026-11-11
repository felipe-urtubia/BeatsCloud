import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from django.core import signing

from app.r2_presign import (
    ALLOWED,
    MAX_BYTES,
    TOKEN_SALT,
    URL_EXPIRY_SECONDS,
)


class R2RegistrationGuardError(ValueError):
    pass


@dataclass(frozen=True)
class R2TrackAuthorization:
    owner: int
    pending_key: str
    expected_size: int
    expected_mime: str


def validate_r2_track_token(*, upload_token, user_id):
    """
    Valida un token firmado para registrar un audio R2.

    No consulta PostgreSQL, no crea Track, no llama a R2.
    El llamante debe verificar la sesion autenticada y
    que el usuario tenga el rol de productor.

    Validar el token no comprueba el contenido del audio.
    """

    if type(user_id) is not int or user_id <= 0:
        raise R2RegistrationGuardError(
            "Usuario no valido."
        )

    if (
        not isinstance(upload_token, str)
        or not upload_token
        or len(upload_token) > 4096
    ):
        raise R2RegistrationGuardError(
            "Token de subida invalido."
        )

    try:
        datos = signing.loads(
            upload_token,
            salt=TOKEN_SALT,
            max_age=URL_EXPIRY_SECONDS,
        )
    except (
        signing.BadSignature,
        ValueError,
        TypeError,
        UnicodeDecodeError,
    ) as exc:
        raise R2RegistrationGuardError(
            "Token invalido o caducado."
        ) from exc

    campos = {
        "owner",
        "key",
        "size",
        "kind",
        "mime",
    }

    if not isinstance(datos, dict) or set(datos) != campos:
        raise R2RegistrationGuardError(
            "Contenido del token invalido."
        )

    owner = datos["owner"]
    key = datos["key"]
    size = datos["size"]
    kind = datos["kind"]
    mime = datos["mime"]

    if type(owner) is not int or owner != user_id:
        raise R2RegistrationGuardError(
            "El token pertenece a otro usuario."
        )

    if kind != "track":
        raise R2RegistrationGuardError(
            "El token no corresponde a una cancion."
        )

    if not isinstance(key, str):
        raise R2RegistrationGuardError(
            "Clave temporal invalida."
        )

    patron = (
        rf"pending/{owner}/track/"
        r"[a-f0-9]{32}\.[a-z0-9]+"
    )

    if not re.fullmatch(patron, key):
        raise R2RegistrationGuardError(
            "Ruta temporal no autorizada."
        )

    extension = PurePosixPath(key).suffix.lower()
    formatos = ALLOWED["track"]

    if (
        extension not in formatos
        or not isinstance(mime, str)
        or mime not in formatos[extension]
    ):
        raise R2RegistrationGuardError(
            "Formato de audio no autorizado."
        )

    if (
        type(size) is not int
        or size <= 0
        or size > MAX_BYTES["track"]
    ):
        raise R2RegistrationGuardError(
            "Tamano de audio no autorizado."
        )

    return R2TrackAuthorization(
        owner=owner,
        pending_key=key,
        expected_size=size,
        expected_mime=mime,
    )
