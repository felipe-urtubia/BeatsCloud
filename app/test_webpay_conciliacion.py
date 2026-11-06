from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, TestCase

from .api_shim import pago_cancel_api
from .models import WebpayTransaction


class WebpayConciliacionTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="comprador_conciliacion",
            password="test-password",
        )
        self.orden = WebpayTransaction.objects.create(
            user=self.usuario,
            buy_order="orden-conciliacion-test",
            session_id=self.usuario.username,
            amount=1190,
        )

    def test_cancelacion_api_no_cambia_estado(self):
        request = RequestFactory().post("/api/pago/cancelar/")
        request.user = self.usuario

        respuesta = pago_cancel_api(request, self.orden.pk)

        self.assertEqual(respuesta.status_code, 409)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.status, "PENDING")

    def test_consulta_sin_token_no_accede_a_transbank(self):
        with patch(
            "app.management.commands.consultar_webpay.Transaction"
        ) as tx:
            with self.assertRaises(CommandError):
                call_command(
                    "consultar_webpay",
                    orden=self.orden.buy_order,
                )
            tx.assert_not_called()

    def consultar(self, respuesta):
        self.orden.webpay_token = "token-prueba-conciliacion"
        self.orden.save(update_fields=["webpay_token"])

        salida = StringIO()

        with patch(
            "app.management.commands.consultar_webpay.Transaction"
        ) as tx:
            tx.return_value.status.return_value = respuesta

            call_command(
                "consultar_webpay",
                orden=self.orden.buy_order,
                stdout=salida,
            )
            tx.return_value.status.assert_called_once_with(
                "token-prueba-conciliacion"
            )

        self.orden.refresh_from_db()
        self.assertEqual(self.orden.status, "PENDING")
        self.assertIsNone(self.orden.fulfilled_at)
        return salida.getvalue()

    def respuesta_autorizada(self):
        return {
            "buy_order": self.orden.buy_order,
            "session_id": self.orden.session_id,
            "amount": 1190,
            "status": "AUTHORIZED",
            "response_code": 0,
        }

    def test_consulta_valida_no_modifica_base(self):
        salida = self.consultar(self.respuesta_autorizada())
        self.assertIn("Datos coinciden: SI", salida)
        self.assertIn("Autorizacion valida: SI", salida)

    def test_consulta_inconsistente_no_valida_pago(self):
        respuesta = self.respuesta_autorizada()
        respuesta["amount"] = 9999

        salida = self.consultar(respuesta)
        self.assertIn("Datos coinciden: NO", salida)
        self.assertIn("Autorizacion valida: NO", salida)
