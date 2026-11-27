from datetime import date, timedelta
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    Genero_Musical,
    HistorialCompra,
    Track,
    Usuario,
    Venta,
    WebpayTransaction,
)


@override_settings(
    FRONTEND_URL="http://localhost:3000",
    LICENSE_SIGNING_KEY="test-only-d7-" + "d" * 48,
    LICENSE_SIGNING_KEY_FALLBACKS=(),
)
class WebpaySpaReturnTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="artista_d7",
            password="test-password",
        )

        self.profile = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.ARTISTA,
        )

        producer = User.objects.create_user(
            username="productor_d7",
            password="test-password",
        )

        producer_profile = Usuario.objects.create(
            user=producer,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genre = Genero_Musical.objects.create(
            descripcion="Genero D7",
        )

        self.track = Track.objects.create(
            nombre_track="Instrumental D7",
            precio=1000,
            genero=genre,
            usuario=producer_profile,
        )

        self.sale = Venta.objects.create(
            detalle="Carrito D7",
            fecha=date.today(),
            precio=1000,
            iva=190,
            precio_total=1190,
            usuario_id=self.profile,
            track=self.track,
        )

        self.order = WebpayTransaction.objects.create(
            user=self.user,
            buy_order="orden-d7",
            session_id="sesion-d7",
            amount="1190.00",
            status=WebpayTransaction.ESTADO_PENDIENTE,
            webpay_token="token-d7-test",
            cart_snapshot=[{
                "venta_id": self.sale.pk,
                "track_id": self.track.pk,
                "precio": 1000,
                "iva": 190,
            }],
        )

        self.url = reverse("exito_carrito") + "?spa=1"

        self.receipt_url = reverse("api_webpay_receipt")

    def provider_response(self, status, code):

        return {
            "status": status,
            "response_code": code,
            "buy_order": self.order.buy_order,
            "session_id": self.order.session_id,
            "amount": 1190,
        }

    def callback(self, status, code, data):

        with patch("app.views.WebpayOptions"):
            with patch("app.views.Transaction") as tx:

                response = self.provider_response(
                    status, code
                )

                tx.return_value.commit.return_value = response
                tx.return_value.status.return_value = response

                result = self.client.post(
                    self.url,
                    data,
                )

        self.assertEqual(result.status_code, 302)

        return parse_qs(
            urlsplit(result.url).query
        )

    def assert_cart_preserved(self):

        self.assertTrue(
            Venta.objects.filter(
                pk=self.sale.pk,
                completada=False,
            ).exists()
        )

        self.assertFalse(
            HistorialCompra.objects.filter(
                usuario=self.profile,
                track=self.track,
            ).exists()
        )

    def identifiers(self):

        return {
            "TBK_ORDEN_COMPRA": self.order.buy_order,
            "TBK_ID_SESION": self.order.session_id,
        }

    def test_approved_return_and_private_receipt(self):

        result = self.callback(
            "AUTHORIZED",
            0,
            {"token_ws": "token-d7-test"},
        )

        self.assertEqual(result["pago"], ["exito"])
        self.assertEqual(result["orden"], ["orden-d7"])
        self.assertNotIn("token_ws", result)

        self.client.force_login(self.user)

        receipt = self.client.get(
            self.receipt_url,
            {"buy_order": self.order.buy_order},
        )

        self.assertEqual(receipt.status_code, 200)
        self.assertEqual(receipt.json()["buy_order"], "orden-d7")
        self.assertEqual(receipt.json()["status"], "AUTHORIZED")
        self.assertEqual(receipt.json()["owner_id"], str(self.user.pk))
        self.assertNotIn("webpay_token", receipt.json())
        self.assertNotIn("session_id", receipt.json())

        self.assertTrue(
            HistorialCompra.objects.filter(
                usuario=self.profile,
                track=self.track,
            ).exists()
        )

        self.assertFalse(
            Venta.objects.filter(
                pk=self.sale.pk,
                completada=False,
            ).exists()
        )

    def test_rejected_preserves_cart(self):

        result = self.callback(
            "FAILED",
            -1,
            {"token_ws": "token-d7-test"},
        )

        self.assertEqual(result["estado"], ["rechazado"])
        self.assert_cart_preserved()

    def test_cancelled_preserves_cart(self):

        data = self.identifiers()
        data["TBK_TOKEN"] = "token-d7-test"

        result = self.callback(
            "INITIALIZED",
            -2,
            data,
        )

        self.assertEqual(result["estado"], ["cancelado"])
        self.assert_cart_preserved()

    def test_abandoned_preserves_cart(self):

        WebpayTransaction.objects.filter(
            pk=self.order.pk
        ).update(
            timestamp=timezone.now() - timedelta(minutes=11)
        )

        result = self.callback(
            "INITIALIZED",
            -2,
            self.identifiers(),
        )

        self.assertEqual(result["estado"], ["abandonado"])
        self.assert_cart_preserved()

    def test_recent_timeout_requires_review(self):

        result = self.callback(
            "INITIALIZED",
            -2,
            self.identifiers(),
        )

        self.assertEqual(result["pago"], ["revision"])
        self.assertNotIn("estado", result)
        self.assert_cart_preserved()

    def test_anonymous_cannot_read_receipt(self):

        response = self.client.get(
            self.receipt_url,
            {"buy_order": self.order.buy_order},
        )

        self.assertEqual(response.status_code, 401)

    def test_other_user_cannot_read_receipt(self):

        self.callback(
            "AUTHORIZED",
            0,
            {"token_ws": "token-d7-test"},
        )

        other = User.objects.create_user(
            username="otro_artista_d7",
            password="test-password",
        )

        self.client.force_login(other)

        response = self.client.get(
            self.receipt_url,
            {"buy_order": self.order.buy_order},
        )

        self.assertEqual(response.status_code, 404)

    def test_pending_order_has_no_receipt(self):

        self.client.force_login(self.user)

        response = self.client.get(
            self.receipt_url,
            {"buy_order": self.order.buy_order},
        )

        self.assertEqual(response.status_code, 404)

    def test_archived_order_has_no_receipt(self):

        self.callback(
            "AUTHORIZED",
            0,
            {"token_ws": "token-d7-test"},
        )

        WebpayTransaction.objects.filter(
            pk=self.order.pk
        ).update(archived_for_review=True)

        self.client.force_login(self.user)

        response = self.client.get(
            self.receipt_url,
            {"buy_order": self.order.buy_order},
        )

        self.assertEqual(response.status_code, 404)
