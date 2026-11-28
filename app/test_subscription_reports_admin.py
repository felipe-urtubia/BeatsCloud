"""Pruebas HTTP de administracion de reportes."""

from datetime import timedelta

from django.contrib.auth.models import User, Permission
from django.contrib.admin.models import LogEntry
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    SubscriptionReport,
    Suscripcion,
    Usuario,
    WebpayTransaction,
)


@override_settings(
    SECURE_SSL_REDIRECT=False,
)
class SubscriptionReportAdminTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.admin_user = User.objects.create_superuser(
            username="report_admin",
            email="admin@example.com",
            password="test-password",
        )

        cls.staff_user = User.objects.create_user(
            username="report_staff",
            password="test-password",
            is_staff=True,
        )

        permissions = Permission.objects.filter(
            content_type__app_label="app",
            content_type__model="subscriptionreport",
        )

        cls.staff_user.user_permissions.add(
            *permissions
        )

        cls.artist_user = User.objects.create_user(
            username="admin_report_artist",
            password="test-password",
        )

        cls.artist = Usuario.objects.create(
            user=cls.artist_user,
            tipo_usu=Usuario.ARTISTA,
            nombre_artistico="Artista de prueba",
        )

        cls.producer_user = User.objects.create_user(
            username="admin_report_producer",
            password="test-password",
        )

        cls.producer = Usuario.objects.create(
            user=cls.producer_user,
            tipo_usu=Usuario.PRODUCTOR,
            nombre_artistico="Productor de prueba",
        )

        cls.plan = Suscripcion.objects.create(
            detalle="Plan actual",
            precio=15000,
            user=cls.producer,
            beneficios=["Beneficio musical"],
        )

        cls.payment = WebpayTransaction.objects.create(
            user=cls.artist_user,
            suscripcion=cls.plan,
            buy_order="admin-report-order",
            session_id="admin-report-private-session",
            webpay_token="admin-report-private-token",
            amount=15000,
            status=WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at=(
                timezone.now() - timedelta(days=1)
            ),
            suscripcion_snapshot={
                "detalle": "Contrato original contratado",
                "beneficios": ["Beneficio original"],
                "descripcion": "<script>report_test()</script>",
            },
        )

        cls.report = SubscriptionReport.objects.create(
            artist=cls.artist,
            producer=cls.producer,
            subscription=cls.plan,
            payment=cls.payment,
            reason=SubscriptionReport.Reason.MISSING_BENEFITS,
            description=(
                "El productor no entrego los beneficios "
                "establecidos en el contrato original."
            ),
        )

    def setUp(self):

        self.client.force_login(self.admin_user)

        self.list_url = reverse(
            "admin:app_subscriptionreport_changelist"
        )

        self.change_url = reverse(
            "admin:app_subscriptionreport_change",
            args=[self.report.pk],
        )

        self.delete_url = reverse(
            "admin:app_subscriptionreport_delete",
            args=[self.report.pk],
        )

        self.add_url = reverse(
            "admin:app_subscriptionreport_add"
        )

        self.resolution = (
            "Se revisaron las condiciones originales "
            "y se gestiono el incumplimiento informado."
        )

    def submit(self, status, resolution="", **extra):

        data = {
            "status": status,
            "resolution": resolution,
            "_save": "Save",
        }

        data.update(extra)

        return self.client.post(
            self.change_url,
            data,
        )

    def start_review(self):

        response = self.submit("IN_REVIEW")

        self.assertEqual(
            response.status_code,
            302,
        )

        self.report.refresh_from_db()

        self.assertEqual(
            self.report.status,
            "IN_REVIEW",
        )

    def assert_open(self):

        self.report.refresh_from_db()

        self.assertEqual(
            self.report.status,
            "OPEN",
        )

        self.assertEqual(
            self.report.resolution,
            "",
        )

    def test_01_superuser_can_list_and_read(self):

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            self.report.pk,
            [
                row.pk
                for row in response.context["cl"].result_list
            ],
        )

        response = self.client.get(self.change_url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Contrato original contratado",
        )

        self.assertContains(
            response,
            "Beneficio original",
        )

    def test_02_anonymous_admin_access_denied(self):

        self.client.logout()

        for url in (
            self.list_url,
            self.change_url,
        ):

            response = self.client.get(url)

            self.assertEqual(
                response.status_code,
                302,
            )

        self.assert_open()

    def test_03_ordinary_users_cannot_access_admin(self):

        for user in (
            self.artist_user,
            self.producer_user,
        ):

            with self.subTest(user=user.pk):

                self.client.force_login(user)

                response = self.client.get(
                    self.list_url
                )

                self.assertEqual(
                    response.status_code,
                    302,
                )

                response = self.submit("IN_REVIEW")

                self.assertEqual(
                    response.status_code,
                    302,
                )

        self.assert_open()

    def test_04_staff_permissions_not_sufficient(self):

        self.client.force_login(
            self.staff_user
        )

        self.assertEqual(
            self.client.get(self.list_url).status_code,
            403,
        )

        self.assertEqual(
            self.client.get(self.change_url).status_code,
            403,
        )

        self.assertEqual(
            self.submit("IN_REVIEW").status_code,
            403,
        )

        self.assert_open()

    def test_05_superuser_conflict_of_interest(self):

        for user in (
            self.artist_user,
            self.producer_user,
        ):

            with self.subTest(user=user.pk):

                user.is_staff = True
                user.is_superuser = True

                user.save(
                    update_fields=[
                        "is_staff",
                        "is_superuser",
                    ]
                )

                self.client.force_login(user)

                response = self.client.get(
                    self.list_url
                )

                self.assertEqual(
                    response.status_code,
                    200,
                )

                self.assertNotIn(
                    self.report.pk,
                    [
                        row.pk
                        for row in response.context["cl"].result_list
                    ],
                )

                response = self.client.get(
                    self.change_url
                )

                self.assertIn(
                    response.status_code,
                    (302, 403, 404),
                )

                response = self.submit("IN_REVIEW")

                self.assertIn(
                    response.status_code,
                    (302, 403, 404),
                )

                self.assert_open()

    def test_06_start_review_records_moderator(self):

        self.start_review()

        self.assertEqual(
            self.report.reviewed_by_id,
            self.admin_user.pk,
        )

        self.assertIsNotNone(
            self.report.reviewed_at
        )

        self.assertTrue(
            LogEntry.objects.filter(
                user=self.admin_user,
                object_id=str(self.report.pk),
                content_type__model="subscriptionreport",
                action_flag=2,
            ).exists()
        )

    def test_07_cannot_skip_review(self):

        for status in (
            "RESOLVED",
            "DISMISSED",
        ):

            response = self.submit(
                status,
                self.resolution,
            )

            self.assertEqual(
                response.status_code,
                200,
            )

            self.assertContains(
                response,
                "Transicion de estado no permitida.",
            )

            self.assert_open()

    def test_08_resolution_required(self):

        self.start_review()

        for resolution in (
            "",
            "Muy corta",
            "x" * 2001,
        ):

            with self.subTest(length=len(resolution)):

                response = self.submit(
                    "RESOLVED",
                    resolution,
                )

                self.assertEqual(
                    response.status_code,
                    200,
                )

                self.report.refresh_from_db()

                self.assertEqual(
                    self.report.status,
                    "IN_REVIEW",
                )

                self.assertEqual(
                    self.report.resolution,
                    "",
                )

    def test_09_resolution_not_allowed_before_closure(self):

        response = self.submit(
            "IN_REVIEW",
            self.resolution,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "La resolucion se registra al finalizar el reporte.",
        )

        self.assert_open()

    def test_10_resolve_and_show_to_artist(self):

        self.start_review()

        response = self.submit(
            "RESOLVED",
            self.resolution,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.report.refresh_from_db()

        self.assertEqual(
            self.report.status,
            "RESOLVED",
        )

        self.assertEqual(
            self.report.resolution,
            self.resolution,
        )

        self.assertEqual(
            self.report.reviewed_by_id,
            self.admin_user.pk,
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

        data = response.json()["reports"][0]

        self.assertEqual(
            data["status"],
            "RESOLVED",
        )

        self.assertEqual(
            data["resolution"],
            self.resolution,
        )

    def test_11_dismiss_report(self):

        self.start_review()

        response = self.submit(
            "DISMISSED",
            self.resolution,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.report.refresh_from_db()

        self.assertEqual(
            self.report.status,
            "DISMISSED",
        )

        self.assertEqual(
            self.report.resolution,
            self.resolution,
        )

    def test_12_terminal_report_is_readonly(self):

        self.start_review()

        self.assertEqual(
            self.submit(
                "RESOLVED",
                self.resolution,
            ).status_code,
            302,
        )

        self.assertEqual(
            self.client.get(
                self.change_url
            ).status_code,
            200,
        )

        self.assertEqual(
            self.submit("OPEN").status_code,
            403,
        )

        self.assertEqual(
            self.submit(
                "RESOLVED",
                "Intento de modificar una resolucion anterior.",
            ).status_code,
            403,
        )

        self.report.refresh_from_db()

        self.assertEqual(
            self.report.status,
            "RESOLVED",
        )

        self.assertEqual(
            self.report.resolution,
            self.resolution,
        )

    def test_13_original_report_cannot_be_modified(self):

        original_description = self.report.description

        response = self.submit(
            "IN_REVIEW",
            artist=self.producer.pk,
            producer=self.artist.pk,
            subscription=999999,
            payment=999999,
            reason="OTHER",
            description="Denuncia manipulada",
            reviewed_by=self.artist_user.pk,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.report.refresh_from_db()

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
            self.report.reason,
            "MISSING_BENEFITS",
        )

        self.assertEqual(
            self.report.description,
            original_description,
        )

        self.assertEqual(
            self.report.reviewed_by_id,
            self.admin_user.pk,
        )

    def test_14_admin_cannot_create_or_delete_reports(self):

        self.assertEqual(
            self.client.get(self.add_url).status_code,
            403,
        )

        self.assertEqual(
            self.client.post(
                self.add_url,
                {"status": "OPEN"},
            ).status_code,
            403,
        )

        self.assertEqual(
            self.client.get(self.delete_url).status_code,
            403,
        )

        self.assertEqual(
            self.client.post(
                self.delete_url,
                {"post": "yes"},
            ).status_code,
            403,
        )

        self.assertEqual(
            SubscriptionReport.objects.count(),
            1,
        )

    def test_15_contract_html_escaped_and_secrets_hidden(self):

        response = self.client.get(
            self.change_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotContains(
            response,
            "<script>report_test()</script>",
        )

        self.assertContains(
            response,
            "&lt;script&gt;report_test()&lt;/script&gt;",
        )

        self.assertNotContains(
            response,
            "admin-report-private-token",
        )

        self.assertNotContains(
            response,
            "admin-report-private-session",
        )

    def test_16_resolution_does_not_change_payment(self):

        self.start_review()

        self.assertEqual(
            self.submit(
                "RESOLVED",
                self.resolution,
            ).status_code,
            302,
        )

        self.payment.refresh_from_db()
        self.plan.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )

        self.assertEqual(
            self.payment.amount,
            15000,
        )

        self.assertIsNotNone(
            self.payment.fulfilled_at
        )

        self.assertEqual(
            self.payment.suscripcion_snapshot["detalle"],
            "Contrato original contratado",
        )

        self.assertTrue(
            self.plan.activo
        )
