"""Autenticacion con proteccion de cuentas cerradas."""

from asgiref.sync import sync_to_async
from django.contrib.auth.backends import ModelBackend

from .models import Usuario


class BeatsCloudModelBackend(ModelBackend):

    def user_can_authenticate(self, user):

        if not super().user_can_authenticate(user):
            return False

        if Usuario.objects.filter(
            user_id=user.pk,
            cuenta_cerrada_en__isnull=False,
        ).exists():
            return False

        return True

    async def aauthenticate(
        self,
        request,
        username=None,
        password=None,
        **kwargs,
    ):

        """Reutiliza la autenticacion sincrona protegida."""

        return await sync_to_async(
            self.authenticate,
            thread_sensitive=True,
        )(
            request,
            username=username,
            password=password,
            **kwargs,
        )

    async def aget_user(self, user_id):

        """Recupera usuarios sin consultas sincronas directas."""

        return await sync_to_async(
            self.get_user,
            thread_sensitive=True,
        )(user_id)

    def _puede_consultar_permisos(self, user_obj):

        """Comprueba el estado persistente antes de usar permisos."""

        if user_obj.is_anonymous or user_obj.pk is None:
            return False

        return self.user_can_authenticate(user_obj)

    def _get_permissions(self, user_obj, obj, from_name):

        if obj is not None:
            return set()

        if not self._puede_consultar_permisos(user_obj):
            return set()

        return super()._get_permissions(
            user_obj,
            obj,
            from_name,
        )

    async def _aget_permissions(
        self,
        user_obj,
        obj,
        from_name,
    ):

        return await sync_to_async(
            self._get_permissions,
            thread_sensitive=True,
        )(
            user_obj,
            obj,
            from_name,
        )

    def get_all_permissions(self, user_obj, obj=None):

        if obj is not None:
            return set()

        # Comprobar el cierre antes de consultar _perm_cache.
        if not self._puede_consultar_permisos(user_obj):
            return set()

        return super().get_all_permissions(
            user_obj,
            obj,
        )

    async def aget_all_permissions(
        self,
        user_obj,
        obj=None,
    ):

        return await sync_to_async(
            self.get_all_permissions,
            thread_sensitive=True,
        )(
            user_obj,
            obj,
        )

    def with_perm(
        self,
        perm,
        is_active=True,
        include_superusers=True,
        obj=None,
    ):

        usuarios = super().with_perm(
            perm,
            is_active=is_active,
            include_superusers=include_superusers,
            obj=obj,
        )

        cuentas_cerradas = Usuario.objects.filter(
            cuenta_cerrada_en__isnull=False,
        ).values("user_id")

        return usuarios.exclude(
            pk__in=cuentas_cerradas
        )
