"""
Conciliación segura de retornos Webpay Plus.

No entrega productos ni activa membresías. Solo identifica la orden, consulta
el estado del proveedor y actualiza estados financieros locales cuando la
respuesta de Transbank coincide exactamente con la orden almacenada.
"""
import logging
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from transbank.common.options import WebpayOptions
from transbank.webpay.webpay_plus.transaction import Transaction

from .models import WebpayTransaction


logger = logging.getLogger(__name__)

# El token de creación expira para iniciar el pago después de unos minutos.
# Damos margen adicional antes de liberar automáticamente una orden INITIALIZED.
PENDING_RECHECK_AFTER = timedelta(minutes=10)
STATUS_QUERY_WINDOW = timedelta(days=7)

OUTCOME_APPROVED = "APPROVED"
OUTCOME_CANCELLED = "CANCELLED"
OUTCOME_REVIEW = "REVIEW"
OUTCOME_ALREADY_FULFILLED = "ALREADY_FULFILLED"


@dataclass(frozen=True)
class WebpayReconciliationResult:
    order: object = None
    response: object = None
    token: str = ""
    outcome: str = OUTCOME_REVIEW
    reason: str = ""


def _field(response, name, default=None):
    if isinstance(response, dict):
        return response.get(name, default)
    return getattr(response, name, default)


def _request_value(request, *names):
    """Lee parámetros de retorno tanto por POST como por GET."""
    for source in (request.POST, request.GET):
        for name in names:
            value = source.get(name)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _new_transaction(transaction_class=None, options_class=None):
    transaction_class = transaction_class or Transaction
    options_class = options_class or WebpayOptions
    return transaction_class(
        options=options_class(
            commerce_code=settings.TRANSBANK_COMMERCE_CODE,
            api_key=settings.TRANSBANK_API_KEY,
            integration_type=settings.TRANSBANK_INTEGRATION_TYPE,
        )
    )


def _response_code(response):
    try:
        return int(_field(response, "response_code"))
    except (TypeError, ValueError):
        return None


def _response_status(response):
    return str(_field(response, "status") or "").strip().upper()


def _matches_order(order, response):
    """No confiar en un estado del proveedor si no coincide toda la identidad."""
    buy_order = str(_field(response, "buy_order") or "").strip()
    session_id = str(_field(response, "session_id") or "").strip()

    try:
        amount = Decimal(str(_field(response, "amount")))
    except (InvalidOperation, TypeError, ValueError):
        return False

    return (
        buy_order == order.buy_order
        and session_id == str(order.session_id or "").strip()
        and amount == Decimal(str(order.amount))
    )


def _is_authorized(response):
    return (
        _response_status(response) == "AUTHORIZED"
        and _response_code(response) == 0
    )


def _can_mark_cancelled(order, response, mode, now=None):
    """
    Cancelar solo con evidencia de proveedor y datos coincidentes.

    - FAILED: rechazo explícito.
    - REVERSED/NULLIFIED: no queda una autorización cobrable.
    - INITIALIZED/-2: anulación explícita o timeout con más de 10 minutos.
    """
    now = now or timezone.now()
    status = _response_status(response)
    code = _response_code(response)

    if status == "FAILED":
        return code is not None and code != 0

    if status in {"REVERSED", "NULLIFIED"}:
        return True

    if status == "INITIALIZED" and code in (None, -2):
        if mode == "abort":
            return True
        if mode == "timeout":
            return now - order.timestamp >= PENDING_RECHECK_AFTER
        return False

    return False


def _persist_provider_result(
    order,
    token,
    response,
    *,
    mode,
    persist_authorized,
):
    """
    Actualiza el estado con bloqueo de fila después de validar la respuesta.
    La entrega de canciones/membresías permanece en las vistas existentes.
    """
    now = timezone.now()

    if not _matches_order(order, response):
        return OUTCOME_REVIEW, "Los datos del proveedor no coinciden."

    authorized = _is_authorized(response)
    cancelable = _can_mark_cancelled(order, response, mode, now=now)

    with transaction.atomic():
        current = WebpayTransaction.objects.select_for_update().get(
            pk=order.pk
        )

        if (
            current.webpay_token != token
            or current.buy_order != order.buy_order
            or current.session_id != order.session_id
            or current.amount != order.amount
            or current.archived_for_review
        ):
            return OUTCOME_REVIEW, "La orden cambió o está archivada."

        if current.fulfilled_at is not None:
            return OUTCOME_ALREADY_FULFILLED, ""

        if authorized:
            # Una autorización que llega después de una cancelación local
            # no debe provocar entrega automática: se archiva para revisión.
            if current.status == WebpayTransaction.ESTADO_CANCELADO:
                current.status = WebpayTransaction.ESTADO_AUTORIZADO
                current.archived_for_review = True
                current.archived_at = now
                current.archive_reason = (
                    "Autorización recibida después de cancelación local"
                )
                current.save(update_fields=[
                    "status",
                    "archived_for_review",
                    "archived_at",
                    "archive_reason",
                ])
                return OUTCOME_REVIEW, "Autorización posterior a cancelación."

            if current.status not in (
                WebpayTransaction.ESTADO_PENDIENTE,
                WebpayTransaction.ESTADO_AUTORIZADO,
            ):
                return OUTCOME_REVIEW, "Estado local no conciliable."

            # En el retorno, la vista conserva PENDING hasta que termine la
            # entrega atómica. En la conciliación previa al checkout sí se
            # registra AUTHORIZED para impedir un segundo cobro.
            if (
                persist_authorized
                and current.status == WebpayTransaction.ESTADO_PENDIENTE
            ):
                current.status = WebpayTransaction.ESTADO_AUTORIZADO
                current.save(update_fields=["status"])

            return OUTCOME_APPROVED, ""

        if cancelable:
            if current.status == WebpayTransaction.ESTADO_CANCELADO:
                return OUTCOME_CANCELLED, ""

            if current.status == WebpayTransaction.ESTADO_PENDIENTE:
                current.status = WebpayTransaction.ESTADO_CANCELADO
                current.save(update_fields=["status"])
                return OUTCOME_CANCELLED, ""

            if (
                current.status == WebpayTransaction.ESTADO_AUTORIZADO
                and _response_status(response) in {"REVERSED", "NULLIFIED"}
            ):
                current.status = WebpayTransaction.ESTADO_CANCELADO
                current.save(update_fields=["status"])
                return OUTCOME_CANCELLED, ""

        return OUTCOME_REVIEW, (
            "Transbank no confirmó una autorización ni una cancelación segura."
        )


def _result(order, token, response=None, outcome=OUTCOME_REVIEW, reason=""):
    if order is not None:
        order.refresh_from_db()
    return WebpayReconciliationResult(
        order=order,
        response=response,
        token=token or "",
        outcome=outcome,
        reason=reason,
    )


def reconcile_webpay_return(
    request,
    *,
    expected_subscription,
    transaction_class=None,
    options_class=None,
):
    """
    Resuelve los retornos Webpay:
      1. token_ws: commit normal.
      2. TBK_TOKEN + orden/sesión: status de anulación.
      3. orden + sesión sin token: status usando el token persistido (timeout).
      4. ambos tokens: status de recuperación; deben ser idénticos.
    """
    token_ws = _request_value(request, "token_ws")
    tbk_token = _request_value(request, "TBK_TOKEN")
    buy_order = _request_value(request, "TBK_ORDEN_COMPRA")
    session_id = _request_value(
        request,
        "TBK_ID_SESION",
        "TBK_ID_SESSION",
    )

    if token_ws and tbk_token and token_ws != tbk_token:
        return _result(
            None, "", outcome=OUTCOME_REVIEW,
            reason="Los tokens de retorno no coinciden.",
        )

    if token_ws and tbk_token:
        token = tbk_token
        mode = "recovery"
        order = WebpayTransaction.objects.filter(
            webpay_token=token
        ).first()
        use_commit = False
    elif tbk_token:
        token = tbk_token
        mode = "abort"
        order = WebpayTransaction.objects.filter(
            webpay_token=token
        ).first()
        use_commit = False
    elif token_ws:
        token = token_ws
        mode = "commit"
        order = WebpayTransaction.objects.filter(
            webpay_token=token
        ).first()
        use_commit = True
    elif buy_order and session_id:
        mode = "timeout"
        order = WebpayTransaction.objects.filter(
            buy_order=buy_order,
            session_id=session_id,
        ).first()
        token = order.webpay_token if order else ""
        use_commit = False
    else:
        return _result(
            None, "", outcome=OUTCOME_REVIEW,
            reason="Retorno sin token ni identificadores suficientes.",
        )

    if order is None:
        return _result(
            None, token, outcome=OUTCOME_REVIEW,
            reason="No existe una orden local asociada al retorno.",
        )

    if bool(order.suscripcion_id) != bool(expected_subscription):
        return _result(
            order, token, outcome=OUTCOME_REVIEW,
            reason="El tipo de orden no coincide con la ruta de retorno.",
        )

    if buy_order and buy_order != order.buy_order:
        return _result(
            order, token, outcome=OUTCOME_REVIEW,
            reason="La orden del retorno no coincide.",
        )

    if session_id and session_id != order.session_id:
        return _result(
            order, token, outcome=OUTCOME_REVIEW,
            reason="La sesión del retorno no coincide.",
        )

    if not token or not order.webpay_token or token != order.webpay_token:
        return _result(
            order, token, outcome=OUTCOME_REVIEW,
            reason="El token no coincide con el token almacenado.",
        )

    if order.archived_for_review:
        return _result(
            order, token, outcome=OUTCOME_REVIEW,
            reason="La orden está archivada para revisión.",
        )

    if order.fulfilled_at is not None:
        return _result(
            order, token, outcome=OUTCOME_ALREADY_FULFILLED,
            reason="La entrega ya fue completada.",
        )

    # Una orden ya cancelada nunca se vuelve a entregar automáticamente.
    # Se consulta status para detectar una eventual autorización tardía.
    if order.status == WebpayTransaction.ESTADO_CANCELADO:
        use_commit = False
        mode = "cancelled_recheck"

    if order.timestamp and timezone.now() - order.timestamp > STATUS_QUERY_WINDOW:
        return _result(
            order, token, outcome=OUTCOME_REVIEW,
            reason="La transacción superó la ventana de consulta de siete días.",
        )

    try:
        tx = _new_transaction(transaction_class, options_class)

        if use_commit:
            try:
                response = tx.commit(token)
            except Exception:
                # Un fallo de commit no demuestra rechazo: consultar status.
                response = tx.status(token)
                mode = "commit_error"
        else:
            response = tx.status(token)

    except Exception as error:
        logger.warning(
            "No se pudo conciliar Webpay para la orden local %s: %s",
            order.pk,
            type(error).__name__,
        )
        return _result(
            order, token, outcome=OUTCOME_REVIEW,
            reason="No se pudo consultar Transbank.",
        )

    outcome, reason = _persist_provider_result(
        order,
        token,
        response,
        mode=mode,
        persist_authorized=False,
    )
    return _result(order, token, response, outcome, reason)


def reconcile_pending_order(order_id, *, user_id=None):
    """
    Consulta una orden pendiente desde el botón cancelar/API.
    No cancela una orden sin token, sin respuesta verificable o con estado
    ambiguo. Una autorización se conserva como AUTHORIZED sin entregar.
    """
    query = WebpayTransaction.objects.filter(
        pk=order_id,
        status=WebpayTransaction.ESTADO_PENDIENTE,
        archived_for_review=False,
        fulfilled_at__isnull=True,
    )
    if user_id is not None:
        query = query.filter(user_id=user_id)

    order = query.first()
    if order is None:
        existing = WebpayTransaction.objects.filter(
            pk=order_id,
            **({"user_id": user_id} if user_id is not None else {}),
        ).first()
        if existing is None:
            return _result(None, "", outcome=OUTCOME_REVIEW)
        if existing.status == WebpayTransaction.ESTADO_CANCELADO:
            return _result(existing, existing.webpay_token, outcome=OUTCOME_CANCELLED)
        if existing.status == WebpayTransaction.ESTADO_AUTORIZADO:
            return _result(existing, existing.webpay_token, outcome=OUTCOME_APPROVED)
        return _result(existing, existing.webpay_token, outcome=OUTCOME_REVIEW)

    token = order.webpay_token
    if not token:
        return _result(
            order, "", outcome=OUTCOME_REVIEW,
            reason="La orden no tiene token almacenado.",
        )

    if timezone.now() - order.timestamp > STATUS_QUERY_WINDOW:
        return _result(
            order, token, outcome=OUTCOME_REVIEW,
            reason="La transacción superó la ventana de consulta.",
        )

    try:
        response = _new_transaction().status(token)
    except Exception as error:
        logger.warning(
            "No se pudo consultar Webpay para la orden local %s: %s",
            order.pk,
            type(error).__name__,
        )
        return _result(
            order, token, outcome=OUTCOME_REVIEW,
            reason="No se pudo consultar Transbank.",
        )

    outcome, reason = _persist_provider_result(
        order,
        token,
        response,
        mode="timeout",
        persist_authorized=True,
    )
    return _result(order, token, response, outcome, reason)


def reconcile_stale_pending_for_user(user_id):
    """
    Antes de iniciar un nuevo pago, intenta resolver órdenes PENDING antiguas.
    Si status() confirma INITIALIZED/-2 después del margen de espera, o un
    rechazo definitivo, libera la orden. Si aparece AUTHORIZED, la conserva
    como AUTHORIZED sin entregar y el guard existente decidirá si bloquea.
    """
    now = timezone.now()
    stale = WebpayTransaction.objects.filter(
        user_id=user_id,
        status=WebpayTransaction.ESTADO_PENDIENTE,
        archived_for_review=False,
        fulfilled_at__isnull=True,
        timestamp__lte=now - PENDING_RECHECK_AFTER,
    ).exclude(
        webpay_token__isnull=True,
    ).exclude(
        webpay_token="",
    ).filter(
        timestamp__gte=now - STATUS_QUERY_WINDOW,
    ).order_by("timestamp")

    for order in stale:
        reconcile_pending_order(order.pk, user_id=user_id)
