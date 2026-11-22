import re
from pathlib import PurePosixPath

from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand, CommandError

from app.models import Track
from app.r2_presign import (
    ALLOWED,
    MAX_BYTES,
    r2_client,
    r2_configuration,
)
from app.r2_preview_storage import (
    MAX_PREVIEW_BYTES,
    PREVIEW_KEY_PATTERN,
)


MISSING_CODES = {"404", "NoSuchKey", "NotFound"}


def _is_missing(exc):
    code = str(
        exc.response.get("Error", {}).get("Code", "")
    )
    return code in MISSING_CODES


def _valid_private_key(owner, key):
    if type(owner) is not int or owner <= 0:
        return False
    if not isinstance(key, str):
        return False

    pattern = (
        rf"private/{owner}/track/"
        r"[a-f0-9]{32}\.[a-z0-9]+"
    )
    return re.fullmatch(pattern, key) is not None


class Command(BaseCommand):
    help = (
        "Audita previews R2 por ID. "
        "Por defecto solo audita; --apply requiere confirmacion."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--track-id",
            action="append",
            type=int,
            required=True,
            help="ID del track. Puede repetirse.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Habilita la recuperacion despues de auditar.",
        )
        parser.add_argument(
            "--confirm",
            default=None,
            help="Confirmacion explicita para aplicar cambios.",
        )

    def handle(self, *args, **options):
        ids = sorted(set(options["track_id"]))

        aplicar = bool(options["apply"])
        confirmacion = options["confirm"]

        if aplicar and confirmacion != "RECUPERAR_SOLO_PREVIEWS_R2":
            raise CommandError(
                "Falta la confirmacion explicita de recuperacion."
            )

        if not aplicar and confirmacion is not None:
            raise CommandError(
                "--confirm solo puede utilizarse con --apply."
            )

        if any(track_id <= 0 for track_id in ids):
            raise CommandError(
                "Todos los IDs deben ser positivos."
            )

        config = r2_configuration()
        if not config:
            raise CommandError(
                "R2 no esta configurado."
            )

        client = r2_client(config)
        bucket = config["R2_BUCKET_NAME"]

        pendientes = 0
        correctas = 0
        errores = 0
        pendientes_ids = []

        if aplicar:
            self.stdout.write(
                "MODO RECUPERACION: se procesaran las previews pendientes."
            )
        else:
            self.stdout.write(
                "MODO AUDITORIA: no se modificaran archivos "
                "ni registros de PostgreSQL."
            )

        tracks = {
            track.pk: track
            for track in Track.objects.filter(pk__in=ids)
        }

        for track_id in ids:
            track = tracks.get(track_id)

            if track is None:
                errores += 1
                self.stdout.write(
                    f"ID {track_id}: no existe en esta base de datos."
                )
                continue

            if (
                track.storage_backend != "r2"
                or track.media_status != "ready"
            ):
                errores += 1
                self.stdout.write(
                    f"ID {track_id}: no es un track R2 listo."
                )
                continue

            owner = track.r2_owner_user_id
            key = track.r2_object_key

            if not _valid_private_key(owner, key):
                errores += 1
                self.stdout.write(
                    f"ID {track_id}: clave privada o propietario invalido."
                )
                continue

            extension = PurePosixPath(key).suffix.lower()

            try:
                metadata = client.head_object(
                    Bucket=bucket,
                    Key=key,
                )

                size = metadata.get("ContentLength")
                mime = metadata.get("ContentType")

                if (
                    type(size) is not int
                    or not 0 < size <= MAX_BYTES["track"]
                    or extension not in ALLOWED["track"]
                    or mime not in ALLOWED["track"][extension]
                ):
                    raise ValueError("Metadatos incompatibles.")

            except (ClientError, ValueError, Exception):
                errores += 1
                self.stdout.write(
                    f"ID {track_id}: original R2 no verificable."
                )
                continue

            preview_key = (
                track.preview.name if track.preview else ""
            )

            if PREVIEW_KEY_PATTERN.fullmatch(preview_key):
                try:
                    preview_metadata = client.head_object(
                        Bucket=bucket,
                        Key=preview_key,
                    )

                except ClientError as exc:
                    if not _is_missing(exc):
                        errores += 1
                        self.stdout.write(
                            f"ID {track_id}: error consultando preview R2."
                        )
                        continue

                except Exception:
                    errores += 1
                    self.stdout.write(
                        f"ID {track_id}: error consultando preview R2."
                    )
                    continue

                else:
                    preview_size = preview_metadata.get(
                        "ContentLength"
                    )
                    preview_mime = preview_metadata.get(
                        "ContentType"
                    )

                    if (
                        type(preview_size) is int
                        and 0 < preview_size <= MAX_PREVIEW_BYTES
                        and preview_mime == "audio/mpeg"
                    ):
                        correctas += 1
                        self.stdout.write(
                            f"ID {track_id}: preview R2 existente y valida."
                        )
                        continue

            pendientes += 1
            pendientes_ids.append(track_id)
            self.stdout.write(
                f"ID {track_id}: original verificado; "
                "preview pendiente de recuperacion."
            )

        self.stdout.write(
            f"Resumen: {correctas} correctas, "
            f"{pendientes} pendientes, {errores} con problemas."
        )

        if errores:
            raise CommandError(
                "La auditoria detecto registros que requieren revision."
            )

        if not aplicar:
            self.stdout.write(
                "Auditoria finalizada. No se aplicaron cambios."
            )
            return

        if not pendientes_ids:
            self.stdout.write(
                "No hay previews pendientes de recuperacion."
            )
            return

        from app.r2_preview_recovery import recover_track_preview

        for track_id in pendientes_ids:
            try:
                resultado = recover_track_preview(
                    track_id=track_id,
                    client=client,
                    bucket=bucket,
                )
            except Exception as exc:
                raise CommandError(
                    f"ID {track_id}: recuperacion fallida. "
                    "Detener y revisar antes de reintentar."
                ) from exc

            self.stdout.write(
                f"ID {track_id}: {resultado['status']}."
            )

        self.stdout.write(
            "Recuperacion finalizada."
        )
