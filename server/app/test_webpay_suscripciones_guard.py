from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Suscripcion, Usuario, WebpayTransaction


@override_settings(FRONTEND_URL="http://localhost:5173")
class WebpaySuscripcionesGuardTests(TestCase):
    def setUp(self):
        self.comprador = User.objects.create_user(
            username="comprador_suscripcion_segura",
            password="test-password",
        )
        Usuario.objects.create(
            user=self.comprador,
            tipo_usu=Usuario.ARTISTA,
        )

        vendedor = User.objects.create_user(
            username="vendedor_suscripcion_segura",
            password="test-password",
        )
        perfil_vendedor = Usuario.objects.create(
            user=vendedor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.plan = Suscripcion.objects.create(
            user=perfil_vendedor,
            detalle="Suscripcion de prueba",
            precio=1190,
        )
        self.orden = WebpayTransaction.objects.create(
            user=self.comprador,
            buy_order="orden-suscripcion-segura",
            session_id=self.comprador.username,
            amount=1190,
            suscripcion=self.plan,
        )
        self.client.force_login(self.comprador)
        self.url = reverse("exito") + "?spa=1"

    def autorizacion(self):
        return {
            "response_code": 0,
            "status": "AUTHORIZED",
            "buy_order": self.orden.buy_order,
            "session_id": self.orden.session_id,
            "amount": 1190,
        }

    def retorno(self, respuesta=None, error=None):
        with patch("app.views.WebpayOptions"):
            with patch("app.views.Transaction") as tx:
                if error is None:
                    tx.return_value.commit.return_value = respuesta
                else:
                    tx.return_value.commit.side_effect = error

                return self.client.post(
                    self.url, {"token_ws": "token-simulado"}
                )

    def test_autorizacion_correcta(self):
        respuesta = self.retorno(self.autorizacion())
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("pago=exito", respuesta.url)

        self.orden.refresh_from_db()
        self.assertEqual(
            self.orden.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )
        self.assertIsNotNone(self.orden.fulfilled_at)

    def test_error_commit_requiere_revision(self):
        respuesta = self.retorno(
            error=RuntimeError("Fallo simulado")
        )
        self.assertIn("pago=revision", respuesta.url)

        self.orden.refresh_from_db()
        self.assertEqual(
            self.orden.status,
            WebpayTransaction.ESTADO_PENDIENTE,
        )

    def test_monto_incorrecto_requiere_revision(self):
        datos = self.autorizacion()
        datos["amount"] = 9999

        respuesta = self.retorno(datos)
        self.assertIn("pago=revision", respuesta.url)

        self.orden.refresh_from_db()
        self.assertIsNone(self.orden.fulfilled_at)

    def test_retorno_sin_token_requiere_revision(self):
        respuesta = self.client.post(self.url)
        self.assertIn("pago=revision", respuesta.url)

        self.orden.refresh_from_db()
        self.assertEqual(
            self.orden.status,
            WebpayTransaction.ESTADO_PENDIENTE,
        )

    def test_bloquea_inicio_con_orden_pendiente(self):
        url = reverse(
            "realizar_pago",
            kwargs={"suscripcion_id": self.plan.pk},
        )
        with patch("app.views.Transaction") as tx:
            respuesta = self.client.post(url)
            tx.assert_not_called()

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            WebpayTransaction.objects.filter(
                user=self.comprador,
                suscripcion=self.plan,
            ).count(),
            1,
        )

    def test_retorno_sin_sesion_django(self):
        self.client.logout()
        respuesta = self.retorno(self.autorizacion())
        self.assertIn("pago=exito", respuesta.url)

        self.orden.refresh_from_db()
        self.assertIsNotNone(self.orden.fulfilled_at)
