"""Proteccion administrativa de identidades cerradas D10."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db import connection, transaction

from .models import (
    Usuario,
    WebpayTransaction,
    HistorialVenta,
    R2UploadClaim,
)


class ClosedIdentityAdminMixin:

    def _cuenta_cerrada(self, obj):

        if obj is None or obj.pk is None:
            return False

        if isinstance(obj, User):
            consulta = Usuario.objects.filter(
                user_id=obj.pk
            )
        else:
            consulta = Usuario.objects.filter(
                pk=obj.pk
            )

        return consulta.filter(
            cuenta_cerrada_en__isnull=False
        ).exists()

    def has_change_permission(self, request, obj=None):

        if self._cuenta_cerrada(obj):
            return False

        return super().has_change_permission(
            request, obj
        )

    def has_delete_permission(self, request, obj=None):

        if self._cuenta_cerrada(obj):
            return False

        return super().has_delete_permission(
            request, obj
        )

    def get_actions(self, request):

        acciones = super().get_actions(request)

        # Evitar eliminaciones masivas de identidades.
        acciones.pop("delete_selected", None)

        return acciones

    def delete_queryset(self, request, queryset):

        raise PermissionDenied(
            "La eliminacion masiva de identidades esta deshabilitada."
        )

    def get_object(
        self, request, object_id, from_field=None
    ):

        obj = super().get_object(
            request, object_id, from_field
        )

        if obj is None:
            return None

        # Serializar escrituras administrativas con el cierre.
        if (
            request.method == "POST"
            and connection.in_atomic_block
        ):

            user_id = (
                obj.pk
                if isinstance(obj, User)
                else obj.user_id
            )

            cuenta = (
                User.objects.select_for_update()
                .filter(pk=user_id)
                .first()
            )

            if cuenta is None:
                return None

            # Volver a consultar despues del bloqueo.
            obj = super().get_object(
                request, object_id, from_field
            )

        return obj

    def changeform_view(
        self,
        request,
        object_id=None,
        form_url="",
        extra_context=None,
    ):

        with transaction.atomic():

            return super().changeform_view(
                request,
                object_id,
                form_url,
                extra_context,
            )

    def delete_view(
        self,
        request,
        object_id,
        extra_context=None,
    ):

        with transaction.atomic():

            return super().delete_view(
                request,
                object_id,
                extra_context,
            )

    def save_model(self, request, obj, form, change):

        if change and self._cuenta_cerrada(obj):

            raise PermissionDenied(
                "No se puede modificar una cuenta cerrada."
            )

        return super().save_model(
            request, obj, form, change
        )

    def _requiere_cierre_controlado(self, obj):

        if obj is None or obj.pk is None:
            return False

        # Todos los perfiles de la plataforma deben pasar
        # por el procedimiento controlado de cierre.
        if isinstance(obj, Usuario):
            return True

        if isinstance(obj, User):

            return (
                Usuario.objects.filter(
                    user_id=obj.pk
                ).exists()
                or WebpayTransaction.objects.filter(
                    user_id=obj.pk
                ).exists()
                or HistorialVenta.objects.filter(
                    comprador_id=obj.pk
                ).exists()
                or R2UploadClaim.objects.filter(
                    owner_id=obj.pk
                ).exists()
            )

        return False

    def get_deleted_objects(self, objs, request):

        objetos = list(objs)

        eliminados, cantidades, permisos, protegidos = (
            super().get_deleted_objects(
                objetos,
                request,
            )
        )

        protegidos = list(protegidos)

        for objeto in objetos:

            if self._requiere_cierre_controlado(objeto):

                protegidos.append(
                    "Identidad BeatsCloud protegida. "
                    "Requiere cierre controlado de cuenta."
                )

        return (
            eliminados,
            cantidades,
            permisos,
            protegidos,
        )

    def delete_model(self, request, obj):

        if self._cuenta_cerrada(obj):

            raise PermissionDenied(
                "No se puede eliminar una identidad cerrada."
            )

        if self._requiere_cierre_controlado(obj):

            raise PermissionDenied(
                "La identidad requiere cierre controlado."
            )

        return super().delete_model(
            request, obj
        )


class BeatsCloudUserAdmin(
    ClosedIdentityAdminMixin,
    UserAdmin,
):

    def user_change_password(
        self, request, id, form_url=""
    ):

        with transaction.atomic():

            obj = self.get_object(
                request,
                unquote(id),
            )

            if self._cuenta_cerrada(obj):

                raise PermissionDenied(
                    "No se puede cambiar la clave de una cuenta cerrada."
                )

            return super().user_change_password(
                request, id, form_url
            )


class BeatsCloudUsuarioAdmin(
    ClosedIdentityAdminMixin,
    admin.ModelAdmin,
):

    def get_readonly_fields(self, request, obj=None):

        campos = tuple(
            super().get_readonly_fields(request, obj)
        )

        campos += ("cuenta_cerrada_en",)

        # Una identidad existente no puede reasignarse
        # a otra cuenta desde el administrador.
        if obj is not None:
            campos += ("user",)

        return tuple(dict.fromkeys(campos))
