from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import WebpayTransaction
from .webpay_checkout_guard import (
    PaymentStartBlocked,
    create_pending_webpay_order,
)


class ArchivoLegacyWebpayTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="archivo_legacy_test",
            password="solo-pruebas",
        )

    def orden(self, estado, archivada):
        return WebpayTransaction.objects.create(
            user=self.usuario,
            buy_order=(
                "antigua-"
                + estado
                + ("-archivo" if archivada else "-normal")
            ),
            session_id=self.usuario.username,
            amount=1190,
            status=estado,
            archived_for_review=archivada,
        )

    def nueva_compra(self):
        return create_pending_webpay_order(
            user=self.usuario,
            amount=1190,
            cart_snapshot=[
                {
                    "venta_id": 901,
                    "track_id": 902,
                    "precio": 1000,
                    "iva": 190,
                }
            ],
        )

    def test_pendiente_archivada_no_bloquea(self):
        anterior = self.orden(
            WebpayTransaction.ESTADO_PENDIENTE,
            True,
        )
        nueva = self.nueva_compra()
        self.assertNotEqual(anterior.pk, nueva.pk)
        anterior.refresh_from_db()
        self.assertEqual(
            anterior.status,
            WebpayTransaction.ESTADO_PENDIENTE,
        )

    def test_autorizada_archivada_no_bloquea(self):
        anterior = self.orden(
            WebpayTransaction.ESTADO_AUTORIZADO,
            True,
        )
        nueva = self.nueva_compra()
        self.assertNotEqual(anterior.pk, nueva.pk)
        anterior.refresh_from_db()
        self.assertEqual(
            anterior.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )
        self.assertIsNone(anterior.fulfilled_at)

    def test_pendiente_normal_sigue_bloqueando(self):
        self.orden(
            WebpayTransaction.ESTADO_PENDIENTE,
            False,
        )
        with self.assertRaises(PaymentStartBlocked):
            self.nueva_compra()

    def test_autorizada_normal_sigue_bloqueando(self):
        self.orden(
            WebpayTransaction.ESTADO_AUTORIZADO,
            False,
        )
        with self.assertRaises(PaymentStartBlocked):
            self.nueva_compra()
