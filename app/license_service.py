"""D10: emision y verificacion persistente de licencias."""

import hashlib
import hmac
import json
import secrets
from datetime import timezone as dt_timezone
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone

from app.models import (
    HistorialCompra,
    Licencia,
    WebpayTransaction,
)


class LicenseError(ValueError):
    pass


def _validate_purchase(compra, orden):
    """Exige una compra efectivamente autorizada y entregada."""

    if compra.origen_adquisicion != HistorialCompra.ORIGEN_WEBPAY:
        raise LicenseError(
            "La adquisicion no tiene un origen comercial valido."
        )

    if (
        orden.status != WebpayTransaction.ESTADO_AUTORIZADO
        or orden.fulfilled_at is None
        or orden.archived_for_review
        or orden.suscripcion_id is not None
    ):
        raise LicenseError("El pago no habilita una licencia.")

    if compra.usuario.user_id != orden.user_id:
        raise LicenseError("El comprador no corresponde a la orden.")

    snapshot = orden.cart_snapshot

    if not isinstance(snapshot, list) or not snapshot:
        raise LicenseError("El pedido original no es valido.")

    tracks = set()
    ventas = set()
    total = 0
    encontrado = False

    for item in snapshot:
        if not isinstance(item, dict):
            raise LicenseError("Pedido malformado.")

        campos = (
            item.get("venta_id"),
            item.get("track_id"),
            item.get("precio"),
            item.get("iva"),
        )

        if any(type(valor) is not int for valor in campos):
            raise LicenseError("Valores de pedido invalidos.")

        venta_id, track_id, precio, iva = campos

        if (
            venta_id <= 0 or track_id <= 0
            or precio < 0 or iva < 0
            or track_id in tracks or venta_id in ventas
        ):
            raise LicenseError("Pedido inconsistente.")

        tracks.add(track_id)
        ventas.add(venta_id)
        total += precio + iva

        if track_id == compra.track_id:
            encontrado = True

    if Decimal(total) != orden.amount:
        raise LicenseError("El monto de la orden no coincide.")

    if not encontrado:
        raise LicenseError("La cancion no pertenece a esta orden.")


def _signing_keys():
    """Devuelve la clave activa y las claves anteriores."""

    activa = getattr(settings, "LICENSE_SIGNING_KEY", "")

    anteriores = getattr(
        settings,
        "LICENSE_SIGNING_KEY_FALLBACKS",
        (),
    )

    if not isinstance(anteriores, (list, tuple)):
        raise ImproperlyConfigured(
            "Configuracion de claves anteriores invalida."
        )

    claves = (activa, *anteriores)

    for clave in claves:
        if not isinstance(clave, str) or len(clave) < 32:
            raise ImproperlyConfigured(
                "Clave de licencias ausente o insuficiente."
            )

        if hmac.compare_digest(
            clave.encode("utf-8"),
            settings.SECRET_KEY.encode("utf-8"),
        ):
            raise ImproperlyConfigured(
                "Las claves de Django y licencias deben ser independientes."
            )

    return tuple(dict.fromkeys(claves))


def _signature(compra, orden, codigo, fecha, *, key):
    """Firma datos persistentes sin exponer la clave del servidor."""

    fecha_utc = fecha.astimezone(dt_timezone.utc).isoformat(
        timespec="microseconds"
    )

    datos = {
        "version": "D10-v2",
        "license_code": codigo,
        "purchase_id": compra.pk,
        "transaction_id": orden.pk,
        "buy_order": orden.buy_order,
        "buyer_id": compra.usuario.user_id,
        "track_id": compra.track_id,
        "issued_at": fecha_utc,
        "amount_clp": format(orden.amount, ".2f"),
        "cart_snapshot": sorted(
            [
                {
                    "venta_id": item["venta_id"],
                    "track_id": item["track_id"],
                    "precio": item["precio"],
                    "iva": item["iva"],
                }
                for item in orden.cart_snapshot
            ],
            key=lambda item: item["track_id"],
        ),
    }

    mensaje = json.dumps(
        datos,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hmac.new(
        key.encode("utf-8"),
        mensaje,
        hashlib.sha256,
    ).hexdigest()


def verify_license(licencia):
    """Comprueba compra, orden y firma almacenada."""

    try:
        compra = licencia.compra
        orden = licencia.transaccion

        _validate_purchase(compra, orden)

        if licencia.buy_order != orden.buy_order:
            return False

        for clave in _signing_keys():
            esperado = _signature(
                compra,
                orden,
                licencia.license_code,
                licencia.issued_at,
                key=clave,
            )

            if hmac.compare_digest(
                esperado,
                licencia.verification_hash,
            ):
                return True

        return False

    except (LicenseError, ValueError, TypeError, AttributeError):
        return False


def issue_license_for_purchase(compra, orden):
    """Crea una licencia unica; devuelve (licencia, creada)."""

    with transaction.atomic():
        # Mantener el mismo orden de bloqueo que Webpay.
        orden = (
            WebpayTransaction.objects
            .select_for_update()
            .get(pk=orden.pk)
        )

        # Bloquear solo la compra, no el perfil relacionado.
        compra = (
            HistorialCompra.objects
            .select_related("usuario")
            .select_for_update(of=("self",))
            .get(pk=compra.pk)
        )

        _validate_purchase(compra, orden)

        existente = Licencia.objects.filter(compra=compra).first()

        if existente is not None:
            if (
                existente.transaccion_id != orden.pk
                or not verify_license(existente)
            ):
                raise LicenseError(
                    "La compra tiene una licencia inconsistente."
                )

            return existente, False

        codigo = "BC-" + secrets.token_hex(12).upper()
        fecha = timezone.now()

        firma = _signature(
            compra,
            orden,
            codigo,
            fecha,
            key=_signing_keys()[0],
        )

        licencia = Licencia.objects.create(
            compra=compra,
            transaccion=orden,
            buy_order=orden.buy_order,
            license_code=codigo,
            verification_hash=firma,
            issued_at=fecha,
        )

        return licencia, True
