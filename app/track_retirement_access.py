"""Acceso a tracks retirados para propietarios y compradores previos."""

from .models import HistorialCompra, HistorialVenta


def can_access_retired_track(user, track):
    if not user.is_authenticated:
        return False

    if track.usuario.user_id == user.pk:
        return True

    return (
        HistorialCompra.objects.filter(
            usuario__user_id=user.pk,
            track_id=track.pk,
        ).exists()
        or HistorialVenta.objects.filter(
            comprador_id=user.pk,
            track_id=track.pk,
        ).exists()
    )
