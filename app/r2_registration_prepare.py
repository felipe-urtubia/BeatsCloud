import re
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from app.r2_registration_guard import (
    validate_r2_track_token,
    validate_r2_cover_token,
)
from app.r2_promotion import promote_pending_object
from app.r2_preview_stage import staged_r2_preview


class R2RegistrationPrepareError(RuntimeError):
    pass


@dataclass(frozen=True)
class R2RegistrationDraft:
    owner: int
    pending_key: str
    private_key: str
    expected_size: int
    expected_mime: str
    preview_path: Path
    original_filename: str = ""


@contextmanager
def prepare_r2_track_registration(
    *, client, bucket, user_id, upload_token
):
    """
    Prepara una cancion R2 sin crear ni publicar un Track.

    Precondicion: el endpoint verifica previamente la
    autenticacion y el rol de productor.

    La copia privada permanece despues de una preparacion
    correcta. El futuro registrador debe garantizar
    idempotencia, persistencia y compensacion de fallos.

    Nunca modifica originales locales ni elimina el
    objeto temporal pendiente.
    """

    autorizacion = validate_r2_track_token(
        upload_token=upload_token,
        user_id=user_id,
    )

    if not isinstance(bucket, str) or not bucket.strip():
        raise R2RegistrationPrepareError(
            "Bucket no valido."
        )

    try:
        promocion = promote_pending_object(
            client=client,
            bucket=bucket,
            owner=autorizacion.owner,
            kind="track",
            pending_key=autorizacion.pending_key,
            expected_size=autorizacion.expected_size,
            expected_mime=autorizacion.expected_mime,
        )
    except Exception as exc:
        raise R2RegistrationPrepareError(
            "No fue posible preparar la copia privada."
        ) from exc

    if not isinstance(promocion, dict):
        raise R2RegistrationPrepareError(
            "Respuesta de promocion invalida."
        )

    privada = promocion.get("private_key")

    patron = (
        rf"private/{autorizacion.owner}/track/"
        r"[a-f0-9]{32}\.[a-z0-9]+"
    )

    if not isinstance(privada, str) or not re.fullmatch(
        patron, privada
    ):
        raise R2RegistrationPrepareError(
            "La ruta privada no es valida."
        )

    with ExitStack() as temporales:
        try:
            if (
                promocion.get("kind") != "track"
                or promocion.get("size")
                != autorizacion.expected_size
                or promocion.get("content_type")
                != autorizacion.expected_mime
            ):
                raise R2RegistrationPrepareError(
                    "Metadatos de promocion incorrectos."
                )

            preview = temporales.enter_context(
                staged_r2_preview(
                    client=client,
                    bucket=bucket,
                    owner=autorizacion.owner,
                    private_key=privada,
                    expected_size=autorizacion.expected_size,
                    expected_mime=autorizacion.expected_mime,
                )
            )

            if not isinstance(preview, Path) or not preview.is_file():
                raise R2RegistrationPrepareError(
                    "La preview temporal no esta disponible."
                )

        except Exception as exc:
            try:
                client.delete_object(
                    Bucket=bucket,
                    Key=privada,
                )
            except Exception as limpieza:
                raise R2RegistrationPrepareError(
                    "Fallo la limpieza de la copia privada."
                ) from limpieza

            raise R2RegistrationPrepareError(
                "No se pudo validar la cancion R2."
            ) from exc

        yield R2RegistrationDraft(
            owner=autorizacion.owner,
            pending_key=autorizacion.pending_key,
            private_key=privada,
            expected_size=autorizacion.expected_size,
            expected_mime=autorizacion.expected_mime,
            preview_path=preview,
            original_filename=autorizacion.original_filename,
        )

@dataclass(frozen=True)
class R2CoverDraft:
    owner: int
    pending_key: str
    private_key: str
    expected_size: int
    expected_mime: str
    original_filename: str = ""


def prepare_r2_cover_upload(
    *,
    client,
    bucket,
    user_id,
    upload_token,
):
    """
    Promueve una portada R2 temporal a una clave privada.

    No crea Track ni consulta PostgreSQL.
    """

    autorizacion = validate_r2_cover_token(
        upload_token=upload_token,
        user_id=user_id,
    )

    if not isinstance(bucket, str) or not bucket.strip():
        raise R2RegistrationPrepareError(
            "Bucket no valido."
        )

    extension = PurePosixPath(
        autorizacion.pending_key
    ).suffix.lower()

    try:
        promocion = promote_pending_object(
            client=client,
            bucket=bucket,
            owner=autorizacion.owner,
            kind="cover",
            pending_key=autorizacion.pending_key,
            expected_size=autorizacion.expected_size,
            expected_mime=autorizacion.expected_mime,
        )
    except Exception as exc:
        raise R2RegistrationPrepareError(
            "No fue posible promover la portada privada."
        ) from exc

    if not isinstance(promocion, dict):
        raise R2RegistrationPrepareError(
            "Respuesta de promocion de portada invalida."
        )

    privada = promocion.get("private_key")

    patron = (
        rf"private/{autorizacion.owner}/cover/"
        rf"[a-f0-9]{{32}}{re.escape(extension)}"
    )

    if not isinstance(privada, str) or not re.fullmatch(
        patron, privada
    ):
        raise R2RegistrationPrepareError(
            "La ruta privada de portada no es valida."
        )

    try:
        if (
            promocion.get("kind") != "cover"
            or promocion.get("size") != autorizacion.expected_size
            or promocion.get("content_type") != autorizacion.expected_mime
        ):
            raise R2RegistrationPrepareError(
                "Los metadatos de la portada no coinciden."
            )

    except Exception as exc:
        try:
            client.delete_object(
                Bucket=bucket,
                Key=privada,
            )
        except Exception as limpieza:
            raise R2RegistrationPrepareError(
                "Fallo la limpieza de la portada privada."
            ) from limpieza

        raise R2RegistrationPrepareError(
            "No se pudo validar la portada promovida."
        ) from exc

    return R2CoverDraft(
        owner=autorizacion.owner,
        pending_key=autorizacion.pending_key,
        private_key=privada,
        expected_size=autorizacion.expected_size,
        expected_mime=autorizacion.expected_mime,
        original_filename=autorizacion.original_filename,
    )
