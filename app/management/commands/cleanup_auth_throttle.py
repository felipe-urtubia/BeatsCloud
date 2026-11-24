"""Limpieza de registros antiguos del limitador de autenticacion."""

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from app.models import AuthAttemptThrottle


class Command(BaseCommand):
    help = "Elimina contadores de autenticacion vencidos y antiguos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--retention-hours",
            type=int,
            default=24,
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
        )

    def handle(self, *args, **options):
        hours = options["retention_hours"]

        if hours < 1:
            raise CommandError(
                "La retencion debe ser de al menos una hora."
            )

        cutoff = timezone.now() - timedelta(hours=hours)

        expired = AuthAttemptThrottle.objects.filter(
            reset_at__lt=cutoff
        )

        if options["dry_run"]:
            count = expired.count()
            self.stdout.write(
                f"Simulacion: {count} registros eliminables."
            )
            return

        deleted, _ = expired.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Limpieza completada: {deleted} registros eliminados."
            )
        )
