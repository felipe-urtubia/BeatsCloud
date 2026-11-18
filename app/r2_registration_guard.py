import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from django.core import signing

from app.r2_presign import (
    ALLOWED,
    MAX_BYTES,
    TOKEN_SALT,
    URL_EXPIRY_SECONDS,
    validate_original_filename,
)


class R2RegistrationGuardError(ValueError):
    pass


@dataclass(frozen=True)
class R2TrackAuthorization:
    owner: int
    pending_key: str
    expected_size: int
    expected_mime: str
    original_filename: str = ""


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

    campos_con_nombre = campos | {"filename"}

    # Los tokens anteriores siguen siendo aceptados.
    if not isinstance(datos, dict) or set(datos) not in (
        campos,
        campos_con_nombre,
    ):
        raise R2RegistrationGuardError(
            "Contenido del token invalido."
        )

    owner = datos["owner"]
    key = datos["key"]
    size = datos["size"]
    kind = datos["kind"]
    mime = datos["mime"]
    original_filename = datos.get("filename", "")

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

    if "filename" in datos:
        try:
            original_filename = validate_original_filename(
                original_filename,
                expected_extension=extension,
            )
        except ValueError as exc:
            raise R2RegistrationGuardError(
                "Nombre original no autorizado."
            ) from exc

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
        original_filename=original_filename,
    )

@dataclass(frozen=True)
class R2CoverAuthorization:
    owner: int
    pending_key: str
    expected_size: int
    expected_mime: str
    original_filename: str = ""


def validate_r2_cover_token(*, upload_token, user_id):
    """
    Valida un token firmado exclusivamente para una portada R2.

    No consulta PostgreSQL ni realiza conexiones a R2.
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
            "Token de portada invalido."
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
            "Token de portada invalido o caducado."
        ) from exc

    campos = {
        "owner",
        "key",
        "size",
        "kind",
        "mime",
    }

    campos_con_nombre = campos | {"filename"}

    if not isinstance(datos, dict) or set(datos) not in (
        campos,
        campos_con_nombre,
    ):
        raise R2RegistrationGuardError(
            "Contenido del token de portada invalido."
        )

    owner = datos["owner"]
    key = datos["key"]
    size = datos["size"]
    kind = datos["kind"]
    mime = datos["mime"]
    filename = datos.get("filename", "")

    if type(owner) is not int or owner != user_id:
        raise R2RegistrationGuardError(
            "La portada pertenece a otro usuario."
        )

    if kind != "cover":
        raise R2RegistrationGuardError(
            "El token no corresponde a una portada."
        )

    if not isinstance(key, str):
        raise R2RegistrationGuardError(
            "Clave temporal de portada invalida."
        )

    patron = (
        rf"pending/{owner}/cover/"
        r"[a-f0-9]{32}\.[a-z0-9]+"
    )

    if not re.fullmatch(patron, key):
        raise R2RegistrationGuardError(
            "Ruta temporal de portada no autorizada."
        )

    extension = PurePosixPath(key).suffix.lower()
    formatos = ALLOWED["cover"]

    if extension not in formatos:
        raise R2RegistrationGuardError(
            "Extension de portada no autorizada."
        )

    if (
        not isinstance(mime, str)
        or mime not in formatos[extension]
    ):
        raise R2RegistrationGuardError(
            "Formato MIME de portada no autorizado."
        )

    if "filename" in datos:
        try:
            filename = validate_original_filename(
                filename,
                expected_extension=extension,
            )
        except ValueError as exc:
            raise R2RegistrationGuardError(
                "Nombre original de portada no autorizado."
            ) from exc

    if (
        type(size) is not int
        or size <= 0
        or size > MAX_BYTES["cover"]
    ):
        raise R2RegistrationGuardError(
            "Tamano de portada no autorizado."
        )

    return R2CoverAuthorization(
        owner=owner,
        pending_key=key,
        expected_size=size,
        expected_mime=mime,
        original_filename=filename,
    )


from dataclasses import dataclass as _stems_dataclass

@_stems_dataclass(frozen=True)
class R2StemsAuthorization:
    owner: int
    pending_key: str
    expected_size: int
    expected_mime: str
    original_filename: str = ""


def validate_r2_stems_token(*, upload_token, user_id):
    """Valida un token R2 exclusivamente para un archivo STEMS."""
    import re as _re
    from pathlib import PurePosixPath as _PurePosixPath
    from django.core import signing as _signing
    from app.r2_presign import (
        ALLOWED as _ALLOWED,
        MAX_BYTES as _MAX_BYTES,
        TOKEN_SALT as _TOKEN_SALT,
        URL_EXPIRY_SECONDS as _URL_EXPIRY_SECONDS,
        validate_original_filename as _validate_original_filename,
    )

    if type(user_id) is not int or user_id <= 0:
        raise R2RegistrationGuardError("Usuario no valido.")
    if not isinstance(upload_token, str) or not upload_token or len(upload_token) > 4096:
        raise R2RegistrationGuardError("Token STEMS invalido.")
    try:
        data = _signing.loads(
            upload_token, salt=_TOKEN_SALT, max_age=_URL_EXPIRY_SECONDS
        )
    except (_signing.BadSignature, ValueError, TypeError, UnicodeDecodeError) as exc:
        raise R2RegistrationGuardError("Token STEMS invalido o caducado.") from exc

    fields = {"owner", "key", "size", "kind", "mime"}
    fields_with_name = fields | {"filename"}
    if not isinstance(data, dict) or set(data) not in (fields, fields_with_name):
        raise R2RegistrationGuardError("Contenido del token STEMS invalido.")

    owner, key, size, kind, mime = (
        data["owner"], data["key"], data["size"], data["kind"], data["mime"]
    )
    filename = data.get("filename", "")
    if type(owner) is not int or owner != user_id:
        raise R2RegistrationGuardError("El archivo STEMS pertenece a otro usuario.")
    if kind != "stems" or not isinstance(key, str):
        raise R2RegistrationGuardError("El token no corresponde a STEMS.")

    extension = _PurePosixPath(key).suffix.lower()
    if extension not in _ALLOWED["stems"]:
        raise R2RegistrationGuardError("Extension STEMS no permitida.")
    pattern = rf"pending/{owner}/stems/[a-f0-9]{{32}}{_re.escape(extension)}"
    if not _re.fullmatch(pattern, key):
        raise R2RegistrationGuardError("Ruta temporal STEMS no autorizada.")
    if type(size) is not int or size <= 0 or size > _MAX_BYTES["stems"]:
        raise R2RegistrationGuardError("Tamano STEMS no autorizado.")
    if not isinstance(mime, str) or mime not in _ALLOWED["stems"][extension]:
        raise R2RegistrationGuardError("Content-Type STEMS no autorizado.")
    if "filename" in data:
        try:
            filename = _validate_original_filename(
                filename, expected_extension=extension
            )
        except ValueError as exc:
            raise R2RegistrationGuardError("Nombre original STEMS no autorizado.") from exc

    return R2StemsAuthorization(
        owner=owner,
        pending_key=key,
        expected_size=size,
        expected_mime=mime,
        original_filename=filename,
    )
