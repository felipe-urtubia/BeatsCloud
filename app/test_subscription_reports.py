"""Pruebas de seguridad y funcionalidad de reportes."""

from datetime import timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.middleware.csrf import get_token
from django.test import (
    Client,
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


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CSRF_USE_SESSIONS=False,
)
class SubscriptionReportTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.artist_user = User.objects.create_user(
            username="report_artist",
            password="test-password",
        )

        cls.artist = Usuario.objects.create(
            user=cls.artist_user,
            tipo_usu=Usuario.ARTISTA,
        )

        cls.other_user = User.objects.create_user(
            username="report_other_artist",
            password="test-password",
        )

        cls.other_artist = Usuario.objects.create(
            user=cls.other_user,
            tipo_usu=Usuario.ARTISTA,
        )

        cls.producer_user = User.objects.create_user(
            username="report_producer",
            password="test-password",
        )

        cls.producer = Usuario.objects.create(
            user=cls.producer_user,
            tipo_usu=Usuario.PRODUCTOR,
            nombre_artistico="Productor de prueba",
        )

        cls.plan = Suscripcion.objects.create(
            detalle="Plan Premium",
            precio=15000,
            user=cls.producer,
            descripcion="Servicios musicales",
            beneficios=["Instrumentales exclusivas"],
        )

        cls.other_plan = Suscripcion.objects.create(
            detalle="Otro plan",
            precio=20000,
            user=cls.producer,
        )

        cls.payment = WebpayTransaction.objects.create(
            user=cls.artist_user,
            suscripcion=cls.plan,
            buy_order="report-order-001",
            session_id="report-session-001",
            amount=15000,
            status=WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at=timezone.now() - timedelta(days=1),
            suscripcion_snapshot={
                "detalle": "Plan Premium Original",
                "beneficios": ["Instrumentales exclusivas"],
            },
        )

    def setUp(self):

        self.url = reverse("api_subscription_reports")

        self.client.force_login(self.artist_user)

    def payload(self, **changes):

        data = {
            "subscription_id": self.plan.pk,
            "reason": "MISSING_BENEFITS",
            "description": (
                "No se entregaron las instrumentales "
                "incluidas en la suscripcion contratada."
            ),
        }

        data.update(changes)

        return data

    def create_report(self, **changes):

        return self.client.post(
            self.url,
            self.payload(**changes),
            content_type="application/json",
        )

    def test_01_create_valid_report(self):

        response = self.create_report()

        self.assertEqual(response.status_code, 201)

        report = SubscriptionReport.objects.get()

        self.assertEqual(report.artist_id, self.artist.pk)
        self.assertEqual(report.producer_id, self.producer.pk)
        self.assertEqual(report.subscription_id, self.plan.pk)
        self.assertEqual(report.payment_id, self.payment.pk)
        self.assertEqual(report.status, "OPEN")

        data = response.json()

        self.assertEqual(
            data["owner_id"],
            str(self.artist_user.pk),
        )

        self.assertEqual(
            data["report"]["subscription_title"],
            "Plan Premium Original",
        )

    def test_02_anonymous_access(self):

        self.client.logout()

        self.assertEqual(
            self.client.get(self.url).status_code,
            401,
        )

        self.assertEqual(
            self.create_report().status_code,
            401,
        )

        self.assertFalse(
            SubscriptionReport.objects.exists()
        )

    def test_03_producer_cannot_report(self):

        self.client.force_login(self.producer_user)

        self.assertEqual(
            self.create_report().status_code,
            403,
        )

        self.assertEqual(
            self.client.get(self.url).status_code,
            403,
        )

    def test_04_other_artist_cannot_report_payment(self):

        self.client.force_login(self.other_user)

        self.assertEqual(
            self.create_report().status_code,
            404,
        )

        self.assertFalse(
            SubscriptionReport.objects.exists()
        )

    def test_05_unpurchased_plan(self):

        response = self.create_report(
            subscription_id=self.other_plan.pk,
        )

        self.assertEqual(response.status_code, 404)

    def test_06_pending_payment(self):

        WebpayTransaction.objects.filter(
            pk=self.payment.pk
        ).update(
            status=WebpayTransaction.ESTADO_PENDIENTE
        )

        self.assertEqual(
            self.create_report().status_code,
            404,
        )

    def test_07_cancelled_payment(self):

        WebpayTransaction.objects.filter(
            pk=self.payment.pk
        ).update(
            status=WebpayTransaction.ESTADO_CANCELADO
        )

        self.assertEqual(
            self.create_report().status_code,
            404,
        )

    def test_08_unfulfilled_payment(self):

        WebpayTransaction.objects.filter(
            pk=self.payment.pk
        ).update(fulfilled_at=None)

        self.assertEqual(
            self.create_report().status_code,
            404,
        )

    def test_09_archived_payment(self):

        WebpayTransaction.objects.filter(
            pk=self.payment.pk
        ).update(archived_for_review=True)

        self.assertEqual(
            self.create_report().status_code,
            404,
        )

    def test_10_expired_subscription_can_be_reported(self):

        WebpayTransaction.objects.filter(
            pk=self.payment.pk
        ).update(
            fulfilled_at=timezone.now() - timedelta(days=90)
        )

        self.assertEqual(
            self.create_report().status_code,
            201,
        )

    def test_11_duplicate_open_report(self):

        self.assertEqual(
            self.create_report().status_code,
            201,
        )

        self.assertEqual(
            self.create_report().status_code,
            409,
        )

        self.assertEqual(
            SubscriptionReport.objects.count(),
            1,
        )

    def test_12_duplicate_in_review_report(self):

        self.create_report()

        SubscriptionReport.objects.update(
            status=SubscriptionReport.Status.IN_REVIEW
        )

        self.assertEqual(
            self.create_report().status_code,
            409,
        )

    def test_13_new_report_after_resolution(self):

        self.create_report()

        SubscriptionReport.objects.update(
            status=SubscriptionReport.Status.RESOLVED
        )

        self.assertEqual(
            self.create_report().status_code,
            201,
        )

        self.assertEqual(
            SubscriptionReport.objects.count(),
            2,
        )

    def test_14_list_is_private(self):

        self.create_report()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["reports"]), 1)

        self.client.force_login(self.other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reports"], [])

    def test_15_reject_manipulated_fields(self):

        fields = {
            "artist_id": self.other_artist.pk,
            "producer_id": self.other_artist.pk,
            "payment_id": self.payment.pk,
            "status": "RESOLVED",
            "resolution": "Manipulated",
            "reviewed_by": self.artist_user.pk,
        }

        for key, value in fields.items():

            with self.subTest(field=key):

                response = self.create_report(
                    **{key: value}
                )

                self.assertEqual(
                    response.status_code,
                    400,
                )

        self.assertFalse(
            SubscriptionReport.objects.exists()
        )

    def test_16_invalid_reason(self):

        self.assertEqual(
            self.create_report(reason="INVALID").status_code,
            400,
        )

    def test_17_invalid_description(self):

        for value in (
            "",
            "   ",
            "Muy corto",
            "x" * 2001,
            None,
            123,
            [],
            "Descripcion con caracter nulo" + chr(0),
        ):

            with self.subTest(value_type=type(value).__name__):

                response = self.create_report(
                    description=value
                )

                self.assertEqual(
                    response.status_code,
                    400,
                )

    def test_18_invalid_subscription_identifier(self):

        for value in (
            True,
            False,
            -1,
            0,
            "1",
            None,
            2147483648,
        ):

            with self.subTest(value=value):

                response = self.create_report(
                    subscription_id=value
                )

                self.assertEqual(
                    response.status_code,
                    400,
                )

    def test_19_invalid_json(self):

        response = self.client.post(
            self.url,
            "{invalid",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_20_csrf_required(self):

        client = Client(enforce_csrf_checks=True)

        client.force_login(self.artist_user)

        response = client.post(
            self.url,
            self.payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

        self.assertFalse(
            SubscriptionReport.objects.exists()
        )

    def test_21_valid_csrf(self):

        from django.conf import settings

        client = Client(enforce_csrf_checks=True)

        client.force_login(self.artist_user)

        request = RequestFactory().get("/")

        token = get_token(request)

        client.cookies[settings.CSRF_COOKIE_NAME] = (
            request.META["CSRF_COOKIE"]
        )

        response = client.post(
            self.url,
            self.payload(),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 201)

    def test_22_database_duplicate_constraint(self):

        self.create_report()

        existing = SubscriptionReport.objects.get()

        with self.assertRaises(IntegrityError):

            with transaction.atomic():

                SubscriptionReport.objects.create(
                    artist=existing.artist,
                    producer=existing.producer,
                    subscription=existing.subscription,
                    payment=existing.payment,
                    reason=existing.reason,
                    description=existing.description,
                )

        self.assertEqual(
            SubscriptionReport.objects.count(),
            1,
        )

    def test_23_protected_commercial_records(self):

        self.create_report()

        for obj in (
            self.artist,
            self.producer,
            self.plan,
            self.payment,
        ):

            with self.subTest(model=obj.__class__.__name__):

                with self.assertRaises(ProtectedError):

                    with transaction.atomic():

                        obj.delete()

        self.assertEqual(
            SubscriptionReport.objects.count(),
            1,
        )

    def test_24_report_does_not_modify_payment(self):

        self.payment.refresh_from_db()

        original_status = self.payment.status
        original_amount = self.payment.amount
        original_fulfilled_at = self.payment.fulfilled_at

        self.create_report()

        self.payment.refresh_from_db()
        self.plan.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            original_status,
        )

        self.assertEqual(
            self.payment.amount,
            original_amount,
        )

        self.assertEqual(
            self.payment.fulfilled_at,
            original_fulfilled_at,
        )

        self.assertTrue(self.plan.activo)

    def test_25_private_response_excludes_secrets(self):

        response = self.create_report()

        self.assertEqual(response.status_code, 201)

        data = response.json()["report"]

        for field in (
            "webpay_token",
            "session_id",
            "buy_order",
            "reviewed_by",
            "email",
            "password",
        ):

            self.assertNotIn(field, data)

        self.assertIn(
            "no-store",
            response.headers.get("Cache-Control", ""),
        )

    def test_26_latest_authorized_contract(self):

        renewal = WebpayTransaction.objects.create(
            user=self.artist_user,
            suscripcion=self.plan,
            buy_order="report-order-renewal",
            session_id="report-session-renewal",
            amount=17000,
            status=WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at=timezone.now() - timedelta(minutes=1),
            suscripcion_snapshot={
                "detalle": "Plan Premium Renovado",
            },
        )

        response = self.create_report()

        self.assertEqual(response.status_code, 201)

        report = SubscriptionReport.objects.get()

        self.assertEqual(report.payment_id, renewal.pk)

        self.assertEqual(
            response.json()["report"]["subscription_title"],
            "Plan Premium Renovado",
        )


    def test_27_expected_owner_can_create_report(self):

        response = self.client.post(
            self.url,
            self.payload(),
            content_type="application/json",
            HTTP_X_REPORT_OWNER=str(
                self.artist_user.pk
            ),
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            SubscriptionReport.objects.count(),
            1,
        )

    def test_28_changed_identity_cannot_create_report(self):

        response = self.client.post(
            self.url,
            self.payload(),
            content_type="application/json",
            HTTP_X_REPORT_OWNER=str(
                self.other_user.pk
            ),
        )

        self.assertEqual(response.status_code, 409)

        self.assertFalse(
            SubscriptionReport.objects.exists()
        )

    def test_29_changed_identity_cannot_read_reports(self):

        self.assertEqual(
            self.create_report().status_code,
            201,
        )

        response = self.client.get(
            self.url,
            HTTP_X_REPORT_OWNER=str(
                self.other_user.pk
            ),
        )

        self.assertEqual(response.status_code, 409)

        self.assertNotIn(
            "reports",
            response.json(),
        )

        response = self.client.get(
            self.url,
            HTTP_X_REPORT_OWNER=str(
                self.artist_user.pk
            ),
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            len(response.json()["reports"]),
            1,
        )
