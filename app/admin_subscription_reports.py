"""Administracion privada de reportes de suscripciones."""

import json

from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import connection, transaction
from django.utils import timezone
from django.utils.html import format_html

from .models import SubscriptionReport


Status = SubscriptionReport.Status


TERMINAL_STATUSES = {
    Status.RESOLVED,
    Status.DISMISSED,
}


ALLOWED_TRANSITIONS = {
    Status.OPEN: {Status.IN_REVIEW},
    Status.IN_REVIEW: {
        Status.RESOLVED,
        Status.DISMISSED,
    },
    Status.RESOLVED: set(),
    Status.DISMISSED: set(),
}


def can_moderate(request, obj=None):

    user = request.user

    if not (
        user.is_authenticated
        and user.is_active
        and user.is_staff
        and user.is_superuser
    ):
        return False

    if obj is not None:

        if user.pk in {
            obj.artist.user_id,
            obj.producer.user_id,
        }:
            return False

    return True


def validate_transition(previous, target, resolution):

    if previous in TERMINAL_STATUSES:
        raise forms.ValidationError(
            "El reporte ya esta finalizado."
        )

    if (
        target != previous
        and target not in ALLOWED_TRANSITIONS.get(
            previous, set()
        )
    ):
        raise forms.ValidationError(
            "Transicion de estado no permitida."
        )

    if target in TERMINAL_STATUSES:

        if not 20 <= len(resolution) <= 2000:
            raise forms.ValidationError(
                "La resolucion debe contener entre "
                "20 y 2000 caracteres."
            )

    elif resolution:
        raise forms.ValidationError(
            "La resolucion se registra al finalizar el reporte."
        )


class SubscriptionReportAdminForm(forms.ModelForm):

    class Meta:
        model = SubscriptionReport
        fields = (
            "status",
            "resolution",
        )

    def clean(self):

        cleaned = super().clean()

        target = cleaned.get("status")

        if target is None or "resolution" not in cleaned:
            return cleaned

        resolution = (
            cleaned.get("resolution") or ""
        ).strip()

        validate_transition(
            self.instance.status,
            target,
            resolution,
        )

        cleaned["resolution"] = resolution

        return cleaned


class SubscriptionReportAdmin(admin.ModelAdmin):

    form = SubscriptionReportAdminForm

    list_display = (
        "id",
        "artist",
        "producer",
        "subscription",
        "reason",
        "status",
        "created_at",
        "reviewed_at",
    )

    list_filter = (
        "status",
        "reason",
        "created_at",
    )

    search_fields = (
        "=id",
        "artist__nombre_artistico",
        "producer__nombre_artistico",
        "subscription__detalle",
    )

    list_select_related = (
        "artist__user",
        "producer__user",
        "subscription",
    )

    ordering = (
        "-created_at",
        "-pk",
    )

    list_per_page = 25

    date_hierarchy = "created_at"

    actions = None

    readonly_fields = (
        "id",
        "artist",
        "producer",
        "subscription",
        "reason",
        "description",
        "contract_details",
        "payment_details",
        "reviewed_by",
        "reviewed_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Identificacion del reporte",
            {
                "fields": (
                    "id",
                    "artist",
                    "producer",
                    "subscription",
                    "created_at",
                ),
            },
        ),
        (
            "Incumplimiento informado",
            {
                "fields": (
                    "reason",
                    "description",
                ),
            },
        ),
        (
            "Antecedentes de contratacion",
            {
                "fields": (
                    "contract_details",
                    "payment_details",
                ),
            },
        ),
        (
            "Gestion administrativa",
            {
                "fields": (
                    "status",
                    "resolution",
                    "reviewed_by",
                    "reviewed_at",
                    "updated_at",
                ),
                "description": (
                    "La resolucion sera visible para "
                    "el artista. No incluyas claves, "
                    "tokens ni datos personales innecesarios."
                ),
            },
        ),
    )

    def has_module_permission(self, request):

        return can_moderate(request)

    def has_view_permission(self, request, obj=None):

        return can_moderate(request, obj)

    def has_change_permission(self, request, obj=None):

        if not can_moderate(request, obj):
            return False

        if obj is not None:

            if obj.status in TERMINAL_STATUSES:
                return False

        return True

    def has_add_permission(self, request):

        return False

    def has_delete_permission(self, request, obj=None):

        return False

    def delete_model(self, request, obj):

        raise PermissionDenied(
            "No se permite eliminar reportes."
        )

    def delete_queryset(self, request, queryset):

        raise PermissionDenied(
            "No se permite eliminar reportes."
        )

    def get_queryset(self, request):

        qs = super().get_queryset(request)

        if not can_moderate(request):
            return qs.none()

        return (
            qs.exclude(
                artist__user_id=request.user.pk
            )
            .exclude(
                producer__user_id=request.user.pk
            )
        )

    def get_object(self, request, object_id, from_field=None):

        obj = super().get_object(
            request,
            object_id,
            from_field,
        )

        if obj is None:
            return None

        if (
            request.method == "POST"
            and connection.in_atomic_block
        ):

            return (
                self.get_queryset(request)
                .select_for_update(of=("self",))
                .filter(pk=obj.pk)
                .first()
            )

        return obj

    @admin.display(description="Contrato original")

    def contract_details(self, obj):

        snapshot = obj.payment.suscripcion_snapshot

        if not isinstance(snapshot, dict) or not snapshot:

            return (
                "No existe un contrato historico disponible."
            )

        allowed = (
            "detalle",
            "descripcion",
            "beneficios",
            "precio",
            "duracion_cantidad",
            "duracion_unidad",
        )

        details = {
            key: snapshot[key]
            for key in allowed
            if key in snapshot
        }

        if not details:
            return "Detalles historicos no disponibles."

        return format_html(
            '<pre style="white-space:pre-wrap">{}</pre>',
            json.dumps(
                details,
                ensure_ascii=False,
                indent=2,
            ),
        )

    @admin.display(description="Pago asociado")

    def payment_details(self, obj):

        payment = obj.payment

        return format_html(
            "{} CLP | Estado: {} | Entrega: {} | ID interno: {}",
            payment.amount,
            payment.get_status_display(),
            payment.fulfilled_at or "No disponible",
            payment.pk,
        )

    @transaction.atomic

    def save_model(self, request, obj, form, change):

        if not change or not obj.pk:
            raise PermissionDenied(
                "No se permite crear reportes administrativos."
            )

        current = (
            SubscriptionReport.objects
            .select_for_update(of=("self",))
            .get(pk=obj.pk)
        )

        if not self.has_change_permission(
            request,
            current,
        ):
            raise PermissionDenied(
                "No puedes modificar este reporte."
            )

        resolution = (
            obj.resolution or ""
        ).strip()

        try:

            validate_transition(
                current.status,
                obj.status,
                resolution,
            )

        except forms.ValidationError as exc:

            raise PermissionDenied(
                "Cambio de estado no autorizado."
            ) from exc

        if (
            current.status == obj.status
            and current.resolution == resolution
        ):
            return

        current.status = obj.status
        current.resolution = resolution

        current.reviewed_by = request.user
        current.reviewed_at = timezone.now()

        current.save(
            update_fields=[
                "status",
                "resolution",
                "reviewed_by",
                "reviewed_at",
                "updated_at",
            ]
        )

        obj.refresh_from_db()
