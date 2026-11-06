from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from .models import Suscripcion, Usuario, WebpayTransaction
from .views import exito, exito_carrito


class RetornosArchivadosTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.comprador = User.objects.create_user(
            username="comprador_archivado_test",
            password="solo-pruebas",
        )
        productor = User.objects.create_user(
            username="productor_archivado_test",
            password="solo-pruebas",
        )

        self.perfil = Usuario.objects.create(
            user=self.comprador,
            tipo_usu=Usuario.ARTISTA,
        )
        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.plan = Suscripcion.objects.create(
            user=perfil_productor,
            detalle="VIP de prueba archivada",
            precio=1000,
        )
        self.factory = RequestFactory()

    @patch("app.views.Transaction")
    def test_carrito_archivado_no_se_entrega(self, tx):
        orden = WebpayTransaction.objects.create(
            user=self.comprador,
            buy_order="archivo-carrito-prueba",
            session_id=self.comprador.username,
            amount=1190,
            status=WebpayTransaction.ESTADO_AUTORIZADO,
            archived_for_review=True,
            webpay_token="token-carrito-archivado-test",
            cart_snapshot=[],
        )

        tx.return_value.commit.return_value = {
            "response_code": 0,
            "status": "AUTHORIZED",
            "buy_order": orden.buy_order,
            "session_id": orden.session_id,
            "amount": 1190,
        }

        request = self.factory.get(
            "/pago/exito-carrito/"
            "?spa=1&token_ws=token-carrito-archivado-test"
        )
        request.user = self.comprador

        respuesta = exito_carrito(request)

        self.assertIn(respuesta.status_code, (302, 409))
        orden.refresh_from_db()
        self.assertTrue(orden.archived_for_review)
        self.assertEqual(
            orden.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )
        self.assertIsNone(orden.fulfilled_at)

    @patch("app.views.Transaction")
    def test_vip_archivada_no_se_activa(self, tx):
        orden = WebpayTransaction.objects.create(
            user=self.comprador,
            buy_order="archivo-vip-prueba",
            session_id=self.comprador.username,
            amount=1000,
            status=WebpayTransaction.ESTADO_PENDIENTE,
            archived_for_review=True,
            suscripcion=self.plan,
            webpay_token="token-vip-archivado-test",
        )

        tx.return_value.commit.return_value = {
            "response_code": 0,
            "status": "AUTHORIZED",
            "buy_order": orden.buy_order,
            "session_id": orden.session_id,
            "amount": 1000,
        }

        request = self.factory.get(
            "/pago/exito/"
            "?spa=1&token_ws=token-vip-archivado-test"
        )
        request.user = self.comprador

        respuesta = exito(request)

        self.assertIn(respuesta.status_code, (302, 409))
        orden.refresh_from_db()
        self.assertTrue(orden.archived_for_review)
        self.assertEqual(
            orden.status,
            WebpayTransaction.ESTADO_PENDIENTE,
        )
        self.assertIsNone(orden.fulfilled_at)
        self.assertFalse(
            self.perfil.sus.filter(pk=self.plan.pk).exists()
        )
