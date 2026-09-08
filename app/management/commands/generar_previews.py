from django.core.management.base import BaseCommand
from django.db.models import Q

from app.audio_utils import generar_preview_audio
from app.models import Track


class Command(BaseCommand):
    help = "Genera previews faltantes para tracks existentes."

    def handle(self, *args, **options):
        tracks = Track.objects.filter(
            Q(preview__isnull=True) | Q(preview="")
        ).order_by("id_track")

        total = tracks.count()

        if total == 0:
            self.stdout.write(
                self.style.SUCCESS("No hay tracks sin preview.")
            )
            return

        generados = 0
        errores = 0

        for track in tracks:
            try:
                generar_preview_audio(track)
                generados += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Preview generado: {track.nombre_track}"
                    )
                )
            except Exception as exc:
                errores += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"Error en {track.nombre_track}: {exc}"
                    )
                )

        self.stdout.write(
            f"Proceso terminado. Generados: {generados}. Errores: {errores}."
        )
