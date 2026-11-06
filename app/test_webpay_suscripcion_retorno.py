from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from .models import Suscripcion, Usuario, WebpayTransaction
from .views import exito


class RetornoVIPSessionTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.comprador = User.objects.create_user(
            username="vip_comprador_test",
            password="test-password",
        )
        self.otro = User.objects.create_user(
            username="vip_otro_test",
            password="test-password",
        )
        self.productor = User.objects.create_user(
            username="vip_productor_test",
            password="test-password",
        )

        self.perfil = Usuario.objects.create(
            user=self.comprador,
            tipo_usu=Usuario.ARTISTA,
        )
        productor_perfil = Usuario.objects.create(
            user=self.productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.plan = Suscripcion.objects.create(
            user=productor_perfil,
            detalle="Plan VIP de prueba",
            precio=1000,
        )
        self.orden = WebpayTransaction.objects.create(
            user=self.comprador,
            buy_order="vip-orden-test-sesion",
            session_id=self.comprador.username,
            amount=1000,
            status=WebpayTransaction.ESTADO_PENDIENTE,
            suscripcion=self.plan,
            webpay_token="token-vip-test",
        )
        self.factory = RequestFactory()

    def respuesta_proveedor(self):
        return {
            "response_code": 0,
            "status": "AUTHORIZED",
            "buy_order": self.orden.buy_order,
            "session_id": self.orden.session_id,
            "amount": 1000,
        }

    def retornar(self, usuario):
        request = self.factory.get(
            "/pago/exito/?spa=1&token_ws=token-vip-test"
        )
        request.user = usuario
        return exito(request)

    @patch("app.views.Transaction")
    def test_sesion_de_otro_usuario_activa_al_comprador(self, tx):
        tx.return_value.commit.return_value = self.respuesta_proveedor()

        respuesta = self.retornar(self.otro)

        self.assertEqual(respuesta.status_code, 302)
        self.orden.refresh_from_db()
        self.assertEqual(
            self.orden.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )
        self.assertIsNotNone(self.orden.fulfilled_at)
        self.assertTrue(self.perfil.sus.filter(pk=self.plan.pk).exists())

    @patch("app.views.Transaction")
    def test_sesion_anonima_activa_al_comprador(self, tx):
        tx.return_value.commit.return_value = self.respuesta_proveedor()

        respuesta = self.retornar(AnonymousUser())

        self.assertEqual(respuesta.status_code, 302)
        self.orden.refresh_from_db()
        self.assertEqual(
            self.orden.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )
        self.assertTrue(self.perfil.sus.filter(pk=self.plan.pk).exists())

    @patch("app.views.Transaction")
    def test_token_incorrecto_no_activa_membresia(self, tx):
        tx.return_value.commit.return_value = self.respuesta_proveedor()

        self.orden.webpay_token = "otro-token"
        self.orden.save(update_fields=["webpay_token"])

        self.retornar(self.otro)

        self.orden.refresh_from_db()
        self.assertEqual(
            self.orden.status,
            WebpayTransaction.ESTADO_PENDIENTE,
        )
        self.assertFalse(self.perfil.sus.filter(pk=self.plan.pk).exists())
