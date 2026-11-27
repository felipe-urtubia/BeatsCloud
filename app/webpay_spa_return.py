"""Presentacion segura del resultado Webpay en la SPA."""

from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .models import WebpayTransaction
from .webpay_reconciliation import OUTCOME_CANCELLED


def cancellation_result(result):
    """Clasificar solo cancelaciones conciliadas por el proveedor."""

    if result.outcome != OUTCOME_CANCELLED:
        return "revision"

    response = result.response

    if isinstance(response, dict):
        status = response.get("status")
    else:
        status = getattr(response, "status", None)

    status = str(status or "").strip().upper()

    if status == "FAILED":
        return "rechazado"

    if status in {"REVERSED", "NULLIFIED"}:
        return "cancelado"

    if status == "INITIALIZED":
        if result.mode == "abort":
            return "cancelado"

        if result.mode == "timeout":
            return "abandonado"

    return "revision"


def cart_spa_return(request, result, order=None):
    """Redireccion SPA; el resultado no concede permisos."""

    if request.GET.get("spa") != "1":
        return None

    params = {}

    if result == "exito" and order is not None:
        params["pago"] = "exito"
        params["orden"] = order.buy_order

    elif result in {"rechazado", "cancelado", "abandonado"}:
        params["pago"] = "fracaso"
        params["estado"] = result

    else:
        params["pago"] = "revision"

    target = urlsplit(settings.FRONTEND_URL.rstrip("/"))

    query = [
        (key, value)
        for key, value in parse_qsl(
            target.query,
            keep_blank_values=True,
        )
        if key not in {"pago", "estado", "orden"}
    ]

    query.extend(params.items())

    response = HttpResponseRedirect(
        urlunsplit((
            target.scheme,
            target.netloc,
            target.path or "/",
            urlencode(query),
            target.fragment,
        ))
    )

    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"

    return response


@never_cache
@require_GET
def webpay_receipt_api(request):
    """Comprobante privado de una compra entregada y autorizada."""

    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Autenticacion requerida."},
            status=401,
        )

    buy_order = request.GET.get("buy_order", "").strip()

    if not buy_order or len(buy_order) > 50:
        return JsonResponse(
            {"error": "Orden invalida."},
            status=400,
        )

    order = WebpayTransaction.objects.filter(
        user=request.user,
        buy_order=buy_order,
        status=WebpayTransaction.ESTADO_AUTORIZADO,
        fulfilled_at__isnull=False,
        archived_for_review=False,
        suscripcion__isnull=True,
    ).first()

    if order is None:
        return JsonResponse(
            {"error": "Comprobante no disponible."},
            status=404,
        )

    return JsonResponse({
        "status": "AUTHORIZED",
        "owner_id": str(order.user_id),
        "buy_order": order.buy_order,
        "amount": str(order.amount),
        "currency": "CLP",
        "fulfilled_at": order.fulfilled_at.isoformat(),
    })
