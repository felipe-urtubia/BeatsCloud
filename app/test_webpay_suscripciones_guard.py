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
            webpay_token="token-simulado",
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

    def iniciar_api(self):
        from django.test import RequestFactory
        from .api_shim import pago_init_api

        request = RequestFactory().post(
            "/api/pago/init/",
            {"subscription_id": self.plan.pk},
            content_type="application/json",
        )
        request.user = self.comprador

        return pago_init_api(request)

    def confirmar_orden(self, antiguedad=0):
        from datetime import timedelta
        from django.utils import timezone

        self.orden.status = WebpayTransaction.ESTADO_AUTORIZADO
        self.orden.fulfilled_at = (
            timezone.now() - timedelta(days=antiguedad)
        )

        self.orden.save(
            update_fields=["status", "fulfilled_at"]
        )

    def test_membresia_activa_bloquea_nuevo_pago(self):
        self.confirmar_orden()

        with patch("app.api_shim._webpay_tx") as tx:
            respuesta = self.iniciar_api()
            tx.assert_not_called()

        self.assertEqual(respuesta.status_code, 409)

    def test_membresia_vencida_permite_renovar(self):
        self.confirmar_orden(antiguedad=31)

        with patch("app.api_shim._webpay_tx") as tx:
            tx.return_value.create.return_value = {
                "url": "https://example.test/webpay",
                "token": "token-renovacion-test",
            }

            respuesta = self.iniciar_api()

            self.assertEqual(respuesta.status_code, 200)
            tx.return_value.create.assert_called_once()

        self.assertEqual(
            WebpayTransaction.objects.filter(
                user=self.comprador,
                suscripcion=self.plan,
            ).count(),
            2,
        )

        with patch("app.api_shim._webpay_tx") as tx:
            respuesta = self.iniciar_api()
            tx.assert_not_called()

        self.assertEqual(respuesta.status_code, 409)

    def test_autorizada_sin_entrega_bloquea_renovacion(self):
        self.orden.status = WebpayTransaction.ESTADO_AUTORIZADO
        self.orden.save(update_fields=["status"])

        with patch("app.api_shim._webpay_tx") as tx:
            respuesta = self.iniciar_api()
            tx.assert_not_called()

        self.assertEqual(respuesta.status_code, 409)

    def test_retorno_repetido_no_extiende_vigencia(self):
        self.retorno(self.autorizacion())

        self.orden.refresh_from_db()
        fecha_original = self.orden.fulfilled_at

        self.assertIsNotNone(fecha_original)

        self.retorno(self.autorizacion())
        self.orden.refresh_from_db()

        self.assertEqual(
            self.orden.fulfilled_at,
            fecha_original,
        )
