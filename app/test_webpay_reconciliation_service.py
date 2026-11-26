from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from .models import WebpayTransaction
from .webpay_checkout_guard import create_pending_webpay_order
from .webpay_reconciliation import (
    OUTCOME_APPROVED,
    OUTCOME_CANCELLED,
    OUTCOME_REVIEW,
    reconcile_pending_order,
    reconcile_stale_pending_for_user,
    reconcile_webpay_return,
)


class WebpayReconciliationServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="comprador_reconciliacion_service",
            password="test-password",
        )
        self.order = WebpayTransaction.objects.create(
            user=self.user,
            buy_order="orden-reconciliacion-service",
            session_id=self.user.username,
            amount="1190.00",
            webpay_token="token-reconciliacion-service",
            cart_snapshot=[{
                "venta_id": 1,
                "track_id": 2,
                "precio": 1000,
                "iva": 190,
            }],
        )
        self.factory = RequestFactory()

    def provider_response(
        self,
        *,
        status="INITIALIZED",
        response_code=None,
        amount=1190,
        buy_order=None,
        session_id=None,
    ):
        return {
            "buy_order": buy_order or self.order.buy_order,
            "session_id": session_id or self.order.session_id,
            "amount": amount,
            "status": status,
            "response_code": response_code,
        }

    def request(self, data):
        return self.factory.post("/pago/exito-carrito/", data)

    @patch("app.webpay_reconciliation.WebpayOptions")
    @patch("app.webpay_reconciliation.Transaction")
    def test_anulacion_explicita_consulta_status_y_cancela(self, tx, options):
        tx.return_value.status.return_value = self.provider_response()

        result = reconcile_webpay_return(
            self.request({
                "TBK_TOKEN": "token-reconciliacion-service",
                "TBK_ORDEN_COMPRA": self.order.buy_order,
                "TBK_ID_SESION": self.order.session_id,
            }),
            expected_subscription=False,
        )

        self.assertEqual(result.outcome, OUTCOME_CANCELLED)
        tx.return_value.status.assert_called_once_with(
            "token-reconciliacion-service"
        )
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.status,
            WebpayTransaction.ESTADO_CANCELADO,
        )
        self.assertIsNone(self.order.fulfilled_at)

    @patch("app.webpay_reconciliation.WebpayOptions")
    @patch("app.webpay_reconciliation.Transaction")
    def test_timeout_antiguo_consulta_token_local_y_cancela(self, tx, options):
        self.order.timestamp = timezone.now() - timedelta(minutes=12)
        self.order.save(update_fields=["timestamp"])
        tx.return_value.status.return_value = self.provider_response()

        result = reconcile_webpay_return(
            self.request({
                "TBK_ORDEN_COMPRA": self.order.buy_order,
                "TBK_ID_SESSION": self.order.session_id,
            }),
            expected_subscription=False,
        )

        self.assertEqual(result.outcome, OUTCOME_CANCELLED)
        tx.return_value.status.assert_called_once_with(
            "token-reconciliacion-service"
        )
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.status,
            WebpayTransaction.ESTADO_CANCELADO,
        )

    @patch("app.webpay_reconciliation.WebpayOptions")
    @patch("app.webpay_reconciliation.Transaction")
    def test_timeout_reciente_no_libera_orden(self, tx, options):
        tx.return_value.status.return_value = self.provider_response()

        result = reconcile_webpay_return(
            self.request({
                "TBK_ORDEN_COMPRA": self.order.buy_order,
                "TBK_ID_SESION": self.order.session_id,
            }),
            expected_subscription=False,
        )

        self.assertEqual(result.outcome, OUTCOME_REVIEW)
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.status,
            WebpayTransaction.ESTADO_PENDIENTE,
        )

    @patch("app.webpay_reconciliation.WebpayOptions")
    @patch("app.webpay_reconciliation.Transaction")
    def test_status_autorizado_devuelve_aprobado_sin_marcar_entrega(
        self, tx, options
    ):
        tx.return_value.status.return_value = self.provider_response(
            status="AUTHORIZED",
            response_code=0,
        )

        result = reconcile_webpay_return(
            self.request({
                "TBK_TOKEN": "token-reconciliacion-service",
                "TBK_ORDEN_COMPRA": self.order.buy_order,
                "TBK_ID_SESION": self.order.session_id,
            }),
            expected_subscription=False,
        )

        self.assertEqual(result.outcome, OUTCOME_APPROVED)
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.status,
            WebpayTransaction.ESTADO_PENDIENTE,
        )
        self.assertIsNone(self.order.fulfilled_at)

    @patch("app.webpay_reconciliation.WebpayOptions")
    @patch("app.webpay_reconciliation.Transaction")
    def test_respuesta_con_monto_distinto_no_cancela(self, tx, options):
        self.order.timestamp = timezone.now() - timedelta(minutes=12)
        self.order.save(update_fields=["timestamp"])
        tx.return_value.status.return_value = self.provider_response(
            amount=9999,
        )

        result = reconcile_webpay_return(
            self.request({
                "TBK_ORDEN_COMPRA": self.order.buy_order,
                "TBK_ID_SESION": self.order.session_id,
            }),
            expected_subscription=False,
        )

        self.assertEqual(result.outcome, OUTCOME_REVIEW)
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.status,
            WebpayTransaction.ESTADO_PENDIENTE,
        )

    @patch("app.webpay_reconciliation.WebpayOptions")
    @patch("app.webpay_reconciliation.Transaction")
    def test_commit_rechazado_con_datos_validos_cancela(self, tx, options):
        tx.return_value.commit.return_value = self.provider_response(
            status="FAILED",
            response_code=-1,
        )

        result = reconcile_webpay_return(
            self.request({"token_ws": "token-reconciliacion-service"}),
            expected_subscription=False,
        )

        self.assertEqual(result.outcome, OUTCOME_CANCELLED)
        tx.return_value.commit.assert_called_once_with(
            "token-reconciliacion-service"
        )
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.status,
            WebpayTransaction.ESTADO_CANCELADO,
        )

    @patch("app.webpay_reconciliation.WebpayOptions")
    @patch("app.webpay_reconciliation.Transaction")
    def test_autorizacion_tardia_de_orden_cancelada_se_archiva(self, tx, options):
        self.order.status = WebpayTransaction.ESTADO_CANCELADO
        self.order.save(update_fields=["status"])
        tx.return_value.status.return_value = self.provider_response(
            status="AUTHORIZED",
            response_code=0,
        )

        result = reconcile_webpay_return(
            self.request({"token_ws": "token-reconciliacion-service"}),
            expected_subscription=False,
        )

        self.assertEqual(result.outcome, OUTCOME_REVIEW)
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )
        self.assertTrue(self.order.archived_for_review)
        self.assertIsNone(self.order.fulfilled_at)

    @patch("app.webpay_reconciliation.WebpayOptions")
    @patch("app.webpay_reconciliation.Transaction")
    def test_reconciliacion_previa_al_checkout_libera_timeout(self, tx, options):
        self.order.timestamp = timezone.now() - timedelta(minutes=12)
        self.order.save(update_fields=["timestamp"])
        tx.return_value.status.return_value = self.provider_response()

        reconcile_stale_pending_for_user(self.user.pk)

        tx.return_value.status.assert_called_once_with(
            "token-reconciliacion-service"
        )
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.status,
            WebpayTransaction.ESTADO_CANCELADO,
        )

    @patch("app.webpay_reconciliation.WebpayOptions")
    @patch("app.webpay_reconciliation.Transaction")
    def test_cancelar_endpoint_reconcilia_y_conserva_autorizacion(
        self, tx, options
    ):
        tx.return_value.status.return_value = self.provider_response(
            status="AUTHORIZED",
            response_code=0,
        )

        result = reconcile_pending_order(
            self.order.pk,
            user_id=self.user.pk,
        )

        self.assertEqual(result.outcome, OUTCOME_APPROVED)
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )
        self.assertIsNone(self.order.fulfilled_at)

    @patch("app.webpay_reconciliation.WebpayOptions")
    @patch("app.webpay_reconciliation.Transaction")
    def test_nuevo_checkout_libera_pendiente_vencido(self, tx, options):
        self.order.timestamp = timezone.now() - timedelta(minutes=12)
        self.order.save(update_fields=["timestamp"])
        tx.return_value.status.return_value = self.provider_response()

        from datetime import date
        from django.contrib.auth import get_user_model
        from app.models import Usuario, Track, Genero_Musical, Venta

        comprador = self.user

        perfil, _ = Usuario.objects.get_or_create(
            user=comprador,
            defaults={"tipo_usu": Usuario.ARTISTA},
        )

        vendedor = get_user_model().objects.create_user(
            username="productor_fixture_checkout",
            password="solo-pruebas",
        )

        productor = Usuario.objects.create(
            user=vendedor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero, _ = Genero_Musical.objects.get_or_create(
            descripcion="Pop",
        )

        track = Track.objects.create(
            nombre_track="Track valido checkout",
            precio=1000,
            genero=genero,
            usuario=productor,
            track="canciones/fixture-checkout.mp3",
            media_status="ready",
            is_retired=False,
        )

        venta = Venta.objects.create(
            detalle="Pedido de prueba",
            fecha=date.today(),
            precio=1000,
            iva=190,
            precio_total=1190,
            usuario_id=perfil,
            track=track,
            completada=False,
        )

        nueva = create_pending_webpay_order(
            user=self.user,
            amount=1190,
            cart_snapshot=[{
                "venta_id": venta.pk,
                "track_id": track.pk,
                "precio": 1000,
                "iva": 190,
            }],
        )

        self.order.refresh_from_db()
        self.assertEqual(
            self.order.status,
            WebpayTransaction.ESTADO_CANCELADO,
        )
        self.assertNotEqual(nueva.pk, self.order.pk)
        self.assertEqual(nueva.status, WebpayTransaction.ESTADO_PENDIENTE)

    @patch("app.webpay_reconciliation.WebpayOptions")
    @patch("app.webpay_reconciliation.Transaction")
    def test_retorno_recuperacion_con_ambos_tokens_usa_status(self, tx, options):
        tx.return_value.status.return_value = self.provider_response(
            status="AUTHORIZED",
            response_code=0,
        )

        result = reconcile_webpay_return(
            self.request({
                "token_ws": "token-reconciliacion-service",
                "TBK_TOKEN": "token-reconciliacion-service",
                "TBK_ORDEN_COMPRA": self.order.buy_order,
                "TBK_ID_SESION": self.order.session_id,
            }),
            expected_subscription=False,
        )

        self.assertEqual(result.outcome, OUTCOME_APPROVED)
        tx.return_value.status.assert_called_once_with(
            "token-reconciliacion-service"
        )
        tx.return_value.commit.assert_not_called()

    @patch("app.webpay_reconciliation.WebpayOptions")
    @patch("app.webpay_reconciliation.Transaction")
    def test_retorno_con_tokens_distintos_no_consulta_ni_cambia_orden(
        self, tx, options
    ):
        result = reconcile_webpay_return(
            self.request({
                "token_ws": "token-reconciliacion-service",
                "TBK_TOKEN": "otro-token",
                "TBK_ORDEN_COMPRA": self.order.buy_order,
                "TBK_ID_SESION": self.order.session_id,
            }),
            expected_subscription=False,
        )

        self.assertEqual(result.outcome, OUTCOME_REVIEW)
        tx.assert_not_called()
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.status,
            WebpayTransaction.ESTADO_PENDIENTE,
        )
