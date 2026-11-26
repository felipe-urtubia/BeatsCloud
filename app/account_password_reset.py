"""Recuperacion de password con proteccion de cuentas cerradas."""

from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Usuario


class BeatsCloudPasswordResetForm(PasswordResetForm):

    def get_users(self, email):

        for user in super().get_users(email):

            cerrada = Usuario.objects.filter(
                user_id=user.pk,
                cuenta_cerrada_en__isnull=False,
            ).exists()

            if not cerrada:
                yield user


class BeatsCloudPasswordResetConfirmView(PasswordResetConfirmView):

    """Protege la recuperacion de cuentas cerradas."""

    def dispatch(self, request, *args, **kwargs):

        with transaction.atomic():
            return super().dispatch(
                request, *args, **kwargs
            )

    def get_user(self, uidb64):

        user = super().get_user(uidb64)

        if user is None:
            return None

        user = (
            get_user_model().objects
            .select_for_update()
            .filter(pk=user.pk)
            .first()
        )

        if user is None:
            return None

        if not user.is_active:
            return None

        if not user.has_usable_password():
            return None

        if Usuario.objects.filter(
            user_id=user.pk,
            cuenta_cerrada_en__isnull=False,
        ).exists():
            return None

        return user
