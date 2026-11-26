"""Proteccion administrativa del catalogo comercial D10."""

from django import forms
from django.contrib import admin

from .models import Track
from django.core.exceptions import PermissionDenied


class BeatsCloudCatalogAdmin(admin.ModelAdmin):

    """Evita eliminaciones fisicas accidentales del catalogo."""

    def has_delete_permission(self, request, obj=None):

        return False

    def get_actions(self, request):

        acciones = super().get_actions(request)

        acciones.pop("delete_selected", None)

        return acciones

    def delete_model(self, request, obj):

        raise PermissionDenied(
            "La eliminacion fisica del catalogo esta deshabilitada."
        )

    def delete_queryset(self, request, queryset):

        raise PermissionDenied(
            "La eliminacion masiva del catalogo esta deshabilitada."
        )


class BeatsCloudCommercialEditAdmin(BeatsCloudCatalogAdmin):

    """Permite modificar exclusivamente campos autorizados."""

    editable_fields = ()

    def has_add_permission(self, request):

        return False

    def get_readonly_fields(self, request, obj=None):

        permitidos = set(self.editable_fields)

        campos = (
            list(self.model._meta.fields)
            + list(self.model._meta.many_to_many)
        )

        protegidos = tuple(
            campo.name
            for campo in campos
            if campo.name not in permitidos
        )

        return tuple(dict.fromkeys(
            tuple(super().get_readonly_fields(request, obj))
            + protegidos
        ))

    def save_model(self, request, obj, form, change):

        if not change or obj.pk is None:

            raise PermissionDenied(
                "La creacion debe realizarse desde BeatsCloud."
            )

        campos = tuple(
            nombre
            for nombre in self.editable_fields
            if nombre in form.changed_data
        )

        # Evitar que una instancia antigua sobrescriba
        # el estado comercial o las referencias protegidas.
        if campos:

            obj.save(update_fields=campos)


class BeatsCloudTrackAdminForm(forms.ModelForm):

    precio = forms.IntegerField(
        min_value=0,
        max_value=2147483647,
    )

    class Meta:

        model = Track

        fields = (
            "nombre_track",
            "descripcion",
            "precio",
        )


class BeatsCloudTrackAdmin(BeatsCloudCommercialEditAdmin):

    form = BeatsCloudTrackAdminForm

    editable_fields = (
        "nombre_track",
        "descripcion",
        "precio",
    )


class BeatsCloudSubscriptionAdmin(BeatsCloudCommercialEditAdmin):

    editable_fields = (
        "detalle",
        "descripcion",
    )


class BeatsCloudCommercialReadOnlyAdmin(BeatsCloudCatalogAdmin):

    """Consulta administrativa sin modificar registros comerciales."""

    def has_add_permission(self, request):

        return False

    def has_change_permission(self, request, obj=None):

        return False

    def save_model(self, request, obj, form, change):

        raise PermissionDenied(
            "El registro comercial es de solo lectura."
        )
