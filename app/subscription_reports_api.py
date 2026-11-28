"""API privada de reportes de incumplimiento de suscripciones."""

import json

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from .models import SubscriptionReport, Usuario
from .subscription_membership import valid_subscription_payments


OPEN_STATUSES = (
    SubscriptionReport.Status.OPEN,
    SubscriptionReport.Status.IN_REVIEW,
)


def _error(message, status=400):
    return JsonResponse(
        {"detail": message},
        status=status,
    )


def _artist(user_id):
    return Usuario.objects.filter(
        user_id=user_id,
        user__is_active=True,
        tipo_usu=Usuario.ARTISTA,
        cuenta_cerrada_en__isnull=True,
    )


def _serialize(report):
    contract = report.payment.suscripcion_snapshot

    if not isinstance(contract, dict):
        contract = {}

    title = contract.get("detalle")

    if not isinstance(title, str) or not title.strip():
        title = report.subscription.detalle

    return {
        "id": report.pk,
        "subscription_id": report.subscription_id,
        "subscription_title": title,
        "producer_name": (
            report.producer.nombre_artistico
            or "Productor"
        ),
        "reason": report.reason,
        "reason_label": report.get_reason_display(),
        "description": report.description,
        "status": report.status,
        "status_label": report.get_status_display(),
        "resolution": report.resolution,
        "created_at": report.created_at.isoformat(),
        "updated_at": report.updated_at.isoformat(),
        "contract_started_at": (
            report.payment.fulfilled_at.isoformat()
            if report.payment.fulfilled_at else None
        ),
        "reviewed_at": (
            report.reviewed_at.isoformat()
            if report.reviewed_at else None
        ),
    }


def _open_reports(artist_id, subscription_id):
    return SubscriptionReport.objects.filter(
        artist_id=artist_id,
        subscription_id=subscription_id,
        status__in=OPEN_STATUSES,
    )


@never_cache
@require_http_methods(["GET", "POST"])
@csrf_protect
def subscription_reports_api(request):

    if not request.user.is_authenticated:
        return _error("Autenticacion requerida.", 401)

    expected_owner = request.headers.get(
        "X-Report-Owner"
    )

    if (
        expected_owner is not None
        and expected_owner != str(request.user.pk)
    ):
        return _error(
            "La identidad de la sesion ha cambiado.",
            409,
        )

    artist = _artist(request.user.pk).first()

    if artist is None:
        return _error(
            "Solo los artistas pueden acceder a sus reportes.",
            403,
        )

    if request.method == "GET":

        reports = (
            SubscriptionReport.objects
            .filter(artist_id=artist.pk)
            .select_related(
                "producer",
                "subscription",
                "payment",
            )
        )

        return JsonResponse({
            "owner_id": str(request.user.pk),
            "reports": [
                _serialize(report)
                for report in reports
            ],
        })

    if request.content_type != "application/json":
        return _error(
            "Se requiere contenido JSON.",
            415,
        )

    raw_body = request.body

    if len(raw_body) > 32768:
        return _error(
            "Contenido demasiado extenso.",
            413,
        )

    try:
        data = json.loads(raw_body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return _error("JSON invalido.")

    if not isinstance(data, dict):
        return _error("Contenido invalido.")

    allowed = {
        "subscription_id",
        "reason",
        "description",
    }

    if set(data) != allowed:
        return _error(
            "Campos del reporte invalidos."
        )

    subscription_id = data.get("subscription_id")
    reason = data.get("reason")
    description = data.get("description")

    if (
        type(subscription_id) is not int
        or not 1 <= subscription_id <= 2147483647
    ):
        return _error("Suscripcion invalida.")

    if (
        not isinstance(reason, str)
        or reason not in SubscriptionReport.Reason.values
    ):
        return _error("Motivo invalido.")

    if not isinstance(description, str):
        return _error("Descripcion invalida.")

    description = description.strip()

    if not 20 <= len(description) <= 2000:
        return _error(
            "La descripcion debe contener entre 20 y 2000 caracteres."
        )

    if chr(0) in description:
        return _error("Descripcion invalida.")

    try:
        description.encode("utf-8")
    except UnicodeEncodeError:
        return _error("Descripcion invalida.")

    try:
        with transaction.atomic():

            account = (
                User.objects.select_for_update(no_key=True)
                .filter(
                    pk=request.user.pk,
                    is_active=True,
                )
                .first()
            )

            if account is None:
                return _error(
                    "Cuenta no disponible.",
                    403,
                )

            artist = (
                _artist(account.pk)
                .select_for_update(of=("self",))
                .first()
            )

            if artist is None:
                return _error(
                    "Cuenta de artista no disponible.",
                    403,
                )

            payment = (
                valid_subscription_payments(
                    account.pk,
                    timezone.now(),
                )
                .filter(
                    suscripcion_id=subscription_id,
                    suscripcion__user__tipo_usu=Usuario.PRODUCTOR,
                )
                .select_related(
                    "suscripcion__user",
                )
                .select_for_update(of=("self",))
                .order_by(
                    "-fulfilled_at",
                    "-pk",
                )
                .first()
            )

            if payment is None:
                return _error(
                    "No existe una contratacion autorizada.",
                    404,
                )

            subscription = payment.suscripcion
            producer = subscription.user

            if producer.pk == artist.pk:
                return _error(
                    "No puedes reportar tu propia suscripcion.",
                    403,
                )

            if _open_reports(
                artist.pk,
                subscription.pk,
            ).exists():
                return _error(
                    "Ya existe un reporte pendiente o en revision.",
                    409,
                )

            report = SubscriptionReport.objects.create(
                artist=artist,
                producer=producer,
                subscription=subscription,
                payment=payment,
                reason=reason,
                description=description,
            )

            payload = {
                "detail": "Reporte registrado correctamente.",
                "owner_id": str(account.pk),
                "report": _serialize(report),
            }

    except IntegrityError:

        if _open_reports(
            artist.pk,
            subscription_id,
        ).exists():
            return _error(
                "Ya existe un reporte pendiente o en revision.",
                409,
            )

        raise

    return JsonResponse(
        payload,
        status=201,
    )
