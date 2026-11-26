"""Coordinacion entre cargas R2 y cierre de cuentas."""

from django.contrib.auth import get_user_model
from django.db import transaction


def lock_r2_upload_owner(user_id):

    """Bloquea al propietario y comprueba su estado persistente."""

    from app.models import Usuario

    if not transaction.get_connection().in_atomic_block:

        raise RuntimeError(
            "Se requiere una transaccion activa."
        )

    if type(user_id) is not int or user_id <= 0:
        return False

    cuenta = (
        get_user_model().objects
        .select_for_update(no_key=True)
        .filter(pk=user_id)
        .first()
    )

    if cuenta is None or not cuenta.is_active:
        return False

    return not Usuario.objects.filter(
        user_id=user_id,
        cuenta_cerrada_en__isnull=False,
    ).exists()


def r2_upload_in_progress(user_id):

    """El llamante debe mantener bloqueado el usuario."""

    from app.r2_claim import R2UploadClaim

    return R2UploadClaim.objects.filter(
        owner_id=user_id,
        status="processing",
    ).exists()
