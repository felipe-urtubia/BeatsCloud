from calendar import monthrange
from datetime import timedelta

from django.utils import timezone

from .models import WebpayTransaction
from .subscription_plans import validate_plan_duration


MEMBERSHIP_DURATION = timedelta(days=30)


def calculate_subscription_expiry(starts_at, cantidad, unidad):
    if unidad == "dias" and cantidad == 30:
        return starts_at + MEMBERSHIP_DURATION

    validate_plan_duration(cantidad, unidad)

    meses = cantidad if unidad == "meses" else cantidad * 12

    total = starts_at.year * 12 + starts_at.month - 1 + meses
    year, month_index = divmod(total, 12)
    month = month_index + 1

    day = min(starts_at.day, monthrange(year, month)[1])

    return starts_at.replace(year=year, month=month, day=day)


def payment_expiry(payment):
    return calculate_subscription_expiry(
        payment.fulfilled_at,
        payment.suscripcion_duracion_cantidad,
        payment.suscripcion_duracion_unidad,
    )


def valid_subscription_payments(user_id, now=None):
    now = now or timezone.now()

    return WebpayTransaction.objects.filter(
        user_id=user_id,
        suscripcion__isnull=False,
        status=WebpayTransaction.ESTADO_AUTORIZADO,
        fulfilled_at__isnull=False,
        fulfilled_at__lte=now,
        archived_for_review=False,
    )


def subscription_periods(user_id, now=None):
    now = now or timezone.now()
    periods = {}

    payments = valid_subscription_payments(
        user_id, now
    ).order_by(
        "suscripcion_id",
        "-fulfilled_at",
        "-pk",
    )

    for payment in payments:
        plan_id = payment.suscripcion_id

        if plan_id in periods:
            continue

        expires_at = payment_expiry(payment)

        periods[plan_id] = {
            "starts_at": payment.fulfilled_at,
            "expires_at": expires_at,
            "active": now < expires_at,
            "duration_count": payment.suscripcion_duracion_cantidad,
            "duration_unit": payment.suscripcion_duracion_unidad,
            "contract": payment.suscripcion_snapshot or None,
            "amount_clp": str(payment.amount),
        }

    return periods


def active_subscription_ids(user_id, now=None):
    return sorted(
        plan_id
        for plan_id, period in subscription_periods(
            user_id, now
        ).items()
        if period["active"]
    )


def has_active_subscription(user_id, plan_id, now=None):
    now = now or timezone.now()

    payment = (
        valid_subscription_payments(user_id, now)
        .filter(suscripcion_id=plan_id)
        .order_by("-fulfilled_at", "-pk")
        .first()
    )

    return payment is not None and now < payment_expiry(payment)
