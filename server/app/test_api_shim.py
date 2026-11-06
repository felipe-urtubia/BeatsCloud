import json
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Genero_Musical, HistorialCompra, Track, Usuario, Venta, WebpayTransaction


class ApiShimSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="artist", password="secret")
        self.profile = Usuario.objects.create(user=self.user, tipo_usu=Usuario.ARTISTA)
        self.genre = Genero_Musical.objects.create(descripcion="Pop")
        self.track = Track.objects.create(
            nombre_track="Track de prueba",
            precio=1000,
            genero=self.genre,
            usuario=self.profile,
        )

    def assert_method_not_allowed(self, response, allow):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], allow)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_existing_nine_method_restrictions_and_allow_headers(self):
        cases = (
            ("/api/csrf/", "post", "GET"),
            ("/api/session/", "post", "GET"),
            ("/api/auth/login/", "get", "POST"),
            ("/api/auth/logout/", "get", "POST"),
            ("/api/auth/registro/", "get", "POST"),
            ("/api/catalogo/", "post", "GET"),
            (f"/api/track/{self.track.pk}/preview/", "post", "GET"),
            (f"/api/track/{self.track.pk}/reproducir/", "post", "GET"),
            (f"/api/track/{self.track.pk}/descargar/", "post", "GET"),
        )
        for path, method, allow in cases:
            with self.subTest(path=path, method=method):
                response = getattr(self.client, method)(path)
                self.assert_method_not_allowed(response, allow)

    def test_four_get_endpoints_allow_get_and_reject_other_methods(self):
        self.client.force_login(self.user)
        paths = (
            "/api/mis-ventas/",
            "/api/mis-compras/",
            f"/api/perfil/{self.user.username}/",
            "/api/suscripciones/",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
                self.assert_method_not_allowed(self.client.post(path), "GET")
                self.assert_method_not_allowed(self.client.put(path), "GET")

    def test_track_detail_allows_get_patch_put_and_rejects_delete(self):
        self.client.force_login(self.user)
        path = f"/api/track/{self.track.pk}/"
        self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(
            self.client.patch(
                path,
                data=json.dumps({"nombre_track": "Editado"}),
                content_type="application/json",
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.put(
                path,
                data=json.dumps({"descripcion": "Descripción"}),
                content_type="application/json",
            ).status_code,
            200,
        )
        self.assert_method_not_allowed(self.client.delete(path), "GET, PATCH, PUT")

    def create_pending_transaction(self, user):
        return WebpayTransaction.objects.create(
            user=user,
            buy_order=f"order-{user.pk}",
            session_id=user.username,
            amount="1000.00",
            status=WebpayTransaction.ESTADO_PENDIENTE,
        )

    def test_payment_cancel_requires_authentication(self):
        payment = self.create_pending_transaction(self.user)
        response = self.client.post(f"/api/pago/cancelar/{payment.pk}/")
        self.assertEqual(response.status_code, 401)
        payment.refresh_from_db()
        self.assertEqual(payment.status, WebpayTransaction.ESTADO_PENDIENTE)

    def test_payment_cancel_succeeds_for_owner(self):
        payment = self.create_pending_transaction(self.user)
        self.client.force_login(self.user)
        response = self.client.post(f"/api/pago/cancelar/{payment.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        payment.refresh_from_db()
        self.assertEqual(payment.status, WebpayTransaction.ESTADO_CANCELADO)

    def test_payment_cancel_hides_other_users_transaction(self):
        payment = self.create_pending_transaction(self.user)
        other_user = User.objects.create_user(username="other", password="secret")
        self.client.force_login(other_user)
        response = self.client.post(f"/api/pago/cancelar/{payment.pk}/")
        self.assertEqual(response.status_code, 404)
        payment.refresh_from_db()
        self.assertEqual(payment.status, WebpayTransaction.ESTADO_PENDIENTE)

    def test_logout_post_succeeds_and_ends_session(self):
        self.client.force_login(self.user)
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.assertIsNone(self.client.get("/api/session/").json())

    def create_pending_cart_payment(self):
        venta = Venta.objects.create(
            detalle=self.track.nombre_track,
            fecha=timezone.localdate(),
            precio=1000,
            iva=190,
            precio_total=1190,
            usuario_id=self.profile,
            track=self.track,
        )
        payment = WebpayTransaction.objects.create(
            user=self.user,
            buy_order="cart-order",
            session_id=self.user.username,
            amount="1190.00",
            status=WebpayTransaction.ESTADO_PENDIENTE,
        )
        return venta, payment

    def test_cart_return_without_token_is_abandoned_and_preserves_cart(self):
        venta, _ = self.create_pending_cart_payment()

        response = self.client.post(reverse("exito_carrito"))

        self.assertRedirects(
            response,
            f"{settings.SPA_URL}/?pago=abandoned",
            fetch_redirect_response=False,
        )
        self.assertTrue(Venta.objects.filter(pk=venta.pk).exists())

    def test_cart_return_cancellation_is_cancelled_and_preserves_cart(self):
        venta, payment = self.create_pending_cart_payment()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("exito_carrito"),
            {"TBK_ORDEN_COMPRA": payment.buy_order, "TBK_ID_SESION": payment.session_id},
        )

        self.assertRedirects(
            response,
            f"{settings.SPA_URL}/?pago=cancelled",
            fetch_redirect_response=False,
        )
        payment.refresh_from_db()
        self.assertEqual(payment.status, WebpayTransaction.ESTADO_CANCELADO)
        self.assertTrue(Venta.objects.filter(pk=venta.pk).exists())

    def test_cart_cancellation_callback_works_without_session_cookie(self):
        _, payment = self.create_pending_cart_payment()

        response = self.client.post(
            reverse("exito_carrito"),
            {"TBK_ORDEN_COMPRA": payment.buy_order, "TBK_ID_SESION": payment.session_id},
        )

        self.assertRedirects(
            response,
            f"{settings.SPA_URL}/?pago=cancelled",
            fetch_redirect_response=False,
        )
        payment.refresh_from_db()
        self.assertEqual(payment.status, WebpayTransaction.ESTADO_CANCELADO)

    def test_cart_return_rejection_preserves_cart_and_does_not_create_purchase(self):
        venta, payment = self.create_pending_cart_payment()
        commit = {"response_code": 1, "status": "FAILED"}
        with patch("app.views.Transaction") as transaction_class:
            transaction_class.return_value.commit.return_value = commit

            response = self.client.post(reverse("exito_carrito"), {"token_ws": "test-token"})

        self.assertRedirects(
            response,
            f"{settings.SPA_URL}/?pago=rejected",
            fetch_redirect_response=False,
        )
        payment.refresh_from_db()
        self.assertEqual(payment.status, WebpayTransaction.ESTADO_PENDIENTE)
        self.assertTrue(Venta.objects.filter(pk=venta.pk).exists())
        self.assertFalse(HistorialCompra.objects.filter(usuario=self.profile, track=self.track).exists())

    def test_cart_return_approval_clears_cart_and_grants_purchase(self):
        venta, payment = self.create_pending_cart_payment()
        commit = {
            "response_code": 0,
            "status": "AUTHORIZED",
            "buy_order": payment.buy_order,
            "session_id": payment.session_id,
            "amount": 1190,
        }
        with patch("app.views.Transaction") as transaction_class:
            transaction_class.return_value.commit.return_value = commit

            response = self.client.post(reverse("exito_carrito"), {"token_ws": "test-token"})

        self.assertRedirects(
            response,
            f"{settings.SPA_URL}/?pago=approved",
            fetch_redirect_response=False,
        )
        payment.refresh_from_db()
        self.assertEqual(payment.status, WebpayTransaction.ESTADO_AUTORIZADO)
        self.assertFalse(Venta.objects.filter(pk=venta.pk).exists())
        self.assertTrue(HistorialCompra.objects.filter(usuario=self.profile, track=self.track).exists())
