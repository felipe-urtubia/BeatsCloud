import secrets

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import HistorialCompra, Usuario, WebpayTransaction


class PaymentStartBlocked(Exception):
    pass


def create_pending_webpay_order(
    *, user, amount, suscripcion=None, cart_snapshot=None
):
    snapshot = list(cart_snapshot or [])

    if suscripcion is None:
        if not snapshot:
            raise PaymentStartBlocked("El carrito esta vacio.")

        try:
            if (
                any(
                    type(item.get("venta_id")) is not int
                    or type(item.get("track_id")) is not int
                    or type(item.get("precio")) is not int
                    or type(item.get("iva")) is not int
                    or item["venta_id"] <= 0
                    or item["track_id"] <= 0
                    or item["precio"] < 0
                    or item["iva"] < 0
                    for item in snapshot
                )
                or sum(
                    item["precio"] + item["iva"]
                    for item in snapshot
                ) != int(amount)
            ):
                raise ValueError()
        except (AttributeError, KeyError, TypeError, ValueError):
            raise PaymentStartBlocked(
                "Los datos del pedido no son validos."
            )

    with transaction.atomic():
        # Serializa solicitudes de inicio del mismo usuario.
        get_user_model().objects.select_for_update().get(pk=user.pk)

        pendientes = WebpayTransaction.objects.filter(
            user_id=user.pk,
            status=WebpayTransaction.ESTADO_PENDIENTE,
            archived_for_review=False,
        )
        if pendientes.exists():
            raise PaymentStartBlocked(
                "Ya existe un pago pendiente. Verifica su estado "
                "antes de iniciar otro."
            )

        sin_entrega = WebpayTransaction.objects.filter(
            user_id=user.pk,
            status=WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at__isnull=True,
            archived_for_review=False,
        )

        if suscripcion is not None:
            if sin_entrega.filter(
                suscripcion_id=suscripcion.pk
            ).exists():
                raise PaymentStartBlocked(
                    "Esta suscripcion tiene un pago pendiente de revision."
                )
        else:
            tracks = {item["track_id"] for item in snapshot}

            perfil = Usuario.objects.filter(user_id=user.pk).first()
            if perfil is not None and HistorialCompra.objects.filter(
                usuario=perfil,
                track_id__in=tracks,
            ).exists():
                raise PaymentStartBlocked(
                    "El carrito contiene canciones ya compradas."
                )

            for anterior in sin_entrega.filter(
                suscripcion__isnull=True
            ):
                original = anterior.cart_snapshot

                if not original or any(
                    isinstance(item, dict)
                    and item.get("track_id") in tracks
                    for item in original
                ):
                    raise PaymentStartBlocked(
                        "Hay un pago autorizado sin entregar "
                        "que requiere revision."
                    )

        return WebpayTransaction.objects.create(
            user=user,
            buy_order=secrets.token_hex(12),
            session_id=user.username,
            amount=amount,
            suscripcion=suscripcion,
            cart_snapshot=snapshot,
        )
