"""Reglas de visibilidad para medios de BeatCloud."""


def only_ready_tracks(queryset):
    """Limita una consulta a canciones listas para publicarse.

    Requiere que la migracion del campo media_status
    este aplicada antes de conectarse a consultas reales.
    """
    return queryset.filter(media_status="ready")


def is_media_ready(track):
    """Solo permite medios con estado ready confirmado."""
    return getattr(track, "media_status", None) == "ready"
