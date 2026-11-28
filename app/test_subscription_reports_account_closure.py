"""Compatibilidad entre reportes y cierre de cuentas D10."""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import (
    RequestFactory,
    TestCase,
    override_settings,
)
from django.urls import reverse
from django.utils import timezone

from .models import (
    SubscriptionReport,
    Suscripcion,
    Usuario,
    WebpayTransaction,
)

from .views import (
    _ejecutar_eliminacion_cuenta,
    EliminacionCuentaBloqueada,
)


@override_settings(
    SECURE_SSL_REDIRECT=False,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class SubscriptionReportAccountClosureTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.artist_user = User.objects.create_user(
            username="closure_report_artist",
            email="artist@example.com",
            password="test-password",
            first_name="Artista",
        )

        cls.artist = Usuario.objects.create(
            user=cls.artist_user,
            tipo_usu=Usuario.ARTISTA,
            nombre_artistico="Artista de prueba",
            descripcion="Descripcion personal",
        )

        cls.producer_user = User.objects.create_user(
            username="closure_report_producer",
            email="producer@example.com",
            password="test-password",
            first_name="Productor",
        )

        cls.producer = Usuario.objects.create(
            user=cls.producer_user,
            tipo_usu=Usuario.PRODUCTOR,
            nombre_artistico="Productor de prueba",
            descripcion="Descripcion personal",
        )

        cls.plan = Suscripcion.objects.create(
            detalle="Plan contratado",
            precio=15000,
            user=cls.producer,
            beneficios=["Beneficio musical"],
        )

        cls.payment = WebpayTransaction.objects.create(
            user=cls.artist_user,
            suscripcion=cls.plan,
            buy_order="closure-report-order",
            session_id="closure-report-session",
            amount=15000,
            status=WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at=(
                timezone.now() - timedelta(days=1)
            ),
            suscripcion_snapshot={
                "detalle": "Plan contratado original",
                "beneficios": ["Beneficio musical"],
            },
        )

        cls.report = SubscriptionReport.objects.create(
            artist=cls.artist,
            producer=cls.producer,
            subscription=cls.plan,
            payment=cls.payment,
            reason=SubscriptionReport.Reason.MISSING_BENEFITS,
            description=(
                "No se entregaron los beneficios "
                "establecidos en el plan contratado."
            ),
        )

    def close_account(self, user, profile):

        request = RequestFactory().post(
            "/eliminar-cuenta/"
        )

        middleware = SessionMiddleware(
            lambda req: HttpResponse()
        )

        middleware.process_request(request)

        request.user = User.objects.get(pk=user.pk)

        with patch(
            "app.views.render",
            return_value=HttpResponse(status=200),
        ):

            response = _ejecutar_eliminacion_cuenta(
                request,
                profile,
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            request.user.is_authenticated
        )

    def assert_closed_identity(self, user, profile):

        user.refresh_from_db()
        profile.refresh_from_db()

        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_usable_password())

        self.assertEqual(user.email, "")
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")

        self.assertTrue(
            user.username.startswith("closed_")
        )

        self.assertIsNotNone(
            profile.cuenta_cerrada_en
        )

        self.assertEqual(
            profile.nombre_artistico,
            "Usuario eliminado",
        )

        self.assertIsNone(profile.descripcion)

    def assert_report_preserved(self):

        self.report.refresh_from_db()
        self.payment.refresh_from_db()

        self.assertEqual(
            self.report.artist_id,
            self.artist.pk,
        )

        self.assertEqual(
            self.report.producer_id,
            self.producer.pk,
        )

        self.assertEqual(
            self.report.subscription_id,
            self.plan.pk,
        )

        self.assertEqual(
            self.report.payment_id,
            self.payment.pk,
        )

        self.assertEqual(
            self.report.status,
            SubscriptionReport.Status.OPEN,
        )

        self.assertEqual(
            self.payment.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )

        self.assertEqual(
            self.payment.amount,
            15000,
        )

        self.assertEqual(
            self.payment.suscripcion_snapshot["detalle"],
            "Plan contratado original",
        )

    def test_artist_closure_preserves_report(self):

        self.close_account(
            self.artist_user,
            self.artist,
        )

        self.assert_closed_identity(
            self.artist_user,
            self.artist,
        )

        self.assert_report_preserved()

    def test_producer_closure_preserves_report(self):

        self.close_account(
            self.producer_user,
            self.producer,
        )

        self.assert_closed_identity(
            self.producer_user,
            self.producer,
        )

        self.assert_report_preserved()

        self.plan.refresh_from_db()

        self.assertFalse(
            self.plan.activo
        )

    def test_artist_can_read_report_after_producer_closure(self):

        self.close_account(
            self.producer_user,
            self.producer,
        )

        self.client.force_login(
            self.artist_user
        )

        response = self.client.get(
            reverse("api_subscription_reports")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        reports = response.json()["reports"]

        self.assertEqual(len(reports), 1)

        self.assertEqual(
            reports[0]["producer_name"],
            "Usuario eliminado",
        )

        self.assertEqual(
            reports[0]["subscription_title"],
            "Plan contratado original",
        )

        self.assertNotIn(
            "producer@example.com",
            response.content.decode("utf-8"),
        )

    def test_closed_artist_cannot_access_reports(self):

        self.close_account(
            self.artist_user,
            self.artist,
        )

        self.client.force_login(
            self.artist_user
        )

        url = reverse(
            "api_subscription_reports"
        )

        response = self.client.get(url)

        self.assertIn(
            response.status_code,
            (401, 403),
        )

        response = self.client.post(
            url,
            {
                "subscription_id": self.plan.pk,
                "reason": "OTHER",
                "description": (
                    "Intento de acceso desde una cuenta cerrada."
                ),
            },
            content_type="application/json",
        )

        self.assertIn(
            response.status_code,
            (401, 403),
        )

        self.assert_report_preserved()

    def test_both_accounts_can_close(self):

        self.close_account(
            self.artist_user,
            self.artist,
        )

        self.close_account(
            self.producer_user,
            self.producer,
        )

        self.assert_closed_identity(
            self.artist_user,
            self.artist,
        )

        self.assert_closed_identity(
            self.producer_user,
            self.producer,
        )

        self.assert_report_preserved()

        self.assertEqual(
            SubscriptionReport.objects.count(),
            1,
        )

    def test_pending_payment_still_blocks_account_closure(self):

        WebpayTransaction.objects.create(
            user=self.artist_user,
            suscripcion=self.plan,
            buy_order="closure-pending-order",
            session_id="closure-pending-session",
            amount=15000,
            status=WebpayTransaction.ESTADO_PENDIENTE,
        )

        with self.assertRaises(
            EliminacionCuentaBloqueada
        ):

            self.close_account(
                self.artist_user,
                self.artist,
            )

        self.artist_user.refresh_from_db()
        self.artist.refresh_from_db()

        self.assertTrue(
            self.artist_user.is_active
        )

        self.assertIsNone(
            self.artist.cuenta_cerrada_en
        )

        self.assert_report_preserved()
