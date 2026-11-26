import secrets

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import HistorialCompra, Suscripcion, Track, Usuario, WebpayTransaction
from .subscription_membership import has_active_subscription
from .subscription_plans import validate_plan_duration
from secrets import token_hex as _webpay_session_token_hex


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

    # Resolver pagos antiguos antes de bloquear un nuevo checkout. La consulta
    # al proveedor se hace fuera de la transacción de base de datos.
    from .webpay_reconciliation import reconcile_stale_pending_for_user
    reconcile_stale_pending_for_user(user.pk)

    from app.r2_account_guard import lock_r2_upload_owner

    with transaction.atomic():

        if not lock_r2_upload_owner(user.pk):
            raise PaymentStartBlocked(
                "La cuenta no esta habilitada para comprar."
            )

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
            perfil = Usuario.objects.filter(user_id=user.pk).first()

            if perfil is None or perfil.tipo_usu != Usuario.ARTISTA:
                raise PaymentStartBlocked(
                    "Solo los artistas pueden contratar membresías."
                )

            suscripcion = (
                Suscripcion.objects.select_for_update()
                .filter(pk=suscripcion.pk)
                .first()
            )

            if suscripcion is None or not suscripcion.activo:
                raise PaymentStartBlocked(
                    "Este plan ya no está disponible."
                )

            if not suscripcion.user.user.is_active:
                raise PaymentStartBlocked(
                    "Este productor ya no está disponible."
                )

            if suscripcion.user.user_id == user.pk:
                raise PaymentStartBlocked(
                    "No puedes contratar tu propio plan."
                )

            if suscripcion.user.tipo_usu != Usuario.PRODUCTOR:
                raise PaymentStartBlocked(
                    "El plan no pertenece a un productor habilitado."
                )

            if suscripcion.precio <= 0 or amount != suscripcion.precio:
                raise PaymentStartBlocked(
                    "El precio del plan no es válido."
                )

            try:
                validate_plan_duration(
                    suscripcion.duracion_cantidad,
                    suscripcion.duracion_unidad,
                )
            except ValueError as error:
                raise PaymentStartBlocked(str(error))

            if has_active_subscription(user.pk, suscripcion.pk):
                raise PaymentStartBlocked(
                    "Ya tienes una membresía activa para este plan."
                )

            if sin_entrega.filter(
                suscripcion_id=suscripcion.pk
            ).exists():
                raise PaymentStartBlocked(
                    "Esta suscripcion tiene un pago pendiente de revision."
                )
        else:
            tracks = {item["track_id"] for item in snapshot}

            # Bloquear los tracks durante la creacion del pedido.
            # La retirada logica actualiza las mismas filas.
            tracks_bloqueados = list(
                Track.objects.select_for_update()
                .filter(pk__in=tracks)
                .order_by("pk")
            )

            if (
                len(tracks_bloqueados) != len(tracks)
                or any(track.is_retired for track in tracks_bloqueados)
            ):
                raise PaymentStartBlocked(
                    "El carrito contiene tracks retirados o no disponibles."
                )

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
            session_id=_webpay_session_token_hex(16),
            amount=amount,
            suscripcion=suscripcion,
            cart_snapshot=snapshot,
            suscripcion_snapshot=(
                {
                    "detalle": suscripcion.detalle,
                    "descripcion": suscripcion.descripcion,
                    "beneficios": suscripcion.beneficios,
                    "precio": suscripcion.precio,
                }
                if suscripcion else {}
            ),
            suscripcion_duracion_cantidad=(
                suscripcion.duracion_cantidad if suscripcion else 30
            ),
            suscripcion_duracion_unidad=(
                suscripcion.duracion_unidad if suscripcion else "dias"
            ),
        )
