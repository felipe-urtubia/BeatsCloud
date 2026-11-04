import json

from django.contrib.auth.models import User
from django.test import TestCase
from .models import Genero_Musical, Track, Usuario, WebpayTransaction


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
