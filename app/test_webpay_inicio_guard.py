from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import WebpayTransaction
from .webpay_checkout_guard import (
    PaymentStartBlocked, create_pending_webpay_order,
)


class WebpayInicioGuardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="comprador_inicio_guard",
            password="test-password",
        )
        self.snapshot = [{
            "venta_id": 10,
            "track_id": 20,
            "precio": 1000,
            "iva": 190,
        }]

    def iniciar(self, snapshot=None):
        return create_pending_webpay_order(
            user=self.user,
            amount=1190,
            cart_snapshot=(
                self.snapshot if snapshot is None else snapshot
            ),
        )

    def test_bloquea_segunda_orden_pendiente(self):
        self.iniciar()
        with self.assertRaises(PaymentStartBlocked):
            self.iniciar()
        self.assertEqual(WebpayTransaction.objects.count(), 1)

    def test_bloquea_autorizada_sin_entrega(self):
        orden = self.iniciar()
        orden.status = WebpayTransaction.ESTADO_AUTORIZADO
        orden.save(update_fields=["status"])

        with self.assertRaises(PaymentStartBlocked):
            self.iniciar()

    def test_permite_otra_compra_tras_entrega(self):
        orden = self.iniciar()
        orden.status = WebpayTransaction.ESTADO_AUTORIZADO
        orden.fulfilled_at = timezone.now()
        orden.save(update_fields=["status", "fulfilled_at"])

        nueva = self.iniciar([{
            "venta_id": 11,
            "track_id": 21,
            "precio": 1000,
            "iva": 190,
        }])
        self.assertNotEqual(orden.pk, nueva.pk)
