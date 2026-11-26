"""Activacion de cuentas con validacion transaccional."""

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode


def activate_account_from_token(uidb64, token):
    """Activa una cuenta elegible sin reactivar cuentas cerradas."""

    if not isinstance(uidb64, str):
        return False

    if not isinstance(token, str):
        return False

    try:
        user_id = force_str(
            urlsafe_base64_decode(uidb64)
        )

        with transaction.atomic():

            user = (
                User.objects
                .select_for_update()
                .filter(pk=user_id)
                .first()
            )

            if user is None:
                return False

            from .models import Usuario

            # El estado de cierre prevalece sobre las credenciales.
            if Usuario.objects.filter(
                user_id=user.pk,
                cuenta_cerrada_en__isnull=False,
            ).exists():
                return False

            # Las cuentas cerradas tienen una clave inutilizable.
            if not user.has_usable_password():
                return False

            if not default_token_generator.check_token(
                user,
                token,
            ):
                return False

            if not user.is_active:

                user.is_active = True

                user.save(
                    update_fields=["is_active"]
                )

            return True

    except (
        TypeError,
        ValueError,
        OverflowError,
        UnicodeDecodeError,
    ):
        return False
