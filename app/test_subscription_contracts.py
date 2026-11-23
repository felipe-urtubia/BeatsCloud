from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Suscripcion, Usuario, WebpayTransaction
from .subscription_membership import (
    calculate_subscription_expiry,
    has_active_subscription,
    subscription_periods,
)
from .webpay_checkout_guard import (
    PaymentStartBlocked,
    create_pending_webpay_order,
)


class SubscriptionContractTests(TestCase):

    def setUp(self):
        self.producer = User.objects.create_user(
            username="contract_producer"
        )
        self.artist = User.objects.create_user(
            username="contract_artist"
        )
        self.other = User.objects.create_user(
            username="contract_other"
        )

        self.profile = Usuario.objects.create(
            user=self.producer,
            tipo_usu=Usuario.PRODUCTOR,
        )

        Usuario.objects.create(
            user=self.artist,
            tipo_usu=Usuario.ARTISTA,
        )

        Usuario.objects.create(
            user=self.other,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.plan = Suscripcion.objects.create(
            user=self.profile,
            detalle="Plan anual",
            precio=45000,
            duracion_cantidad=1,
            duracion_unidad="anios",
        )

        self.url = "/api/suscripciones/"
        self.detail_url = f"{self.url}{self.plan.pk}/"

    def test_three_month_contract(self):
        inicio = datetime(2026, 11, 23, tzinfo=dt_timezone.utc)

        self.assertEqual(
            calculate_subscription_expiry(inicio, 3, "meses"),
            datetime(2027, 2, 23, tzinfo=dt_timezone.utc),
        )

    def test_last_day_of_month(self):
        inicio = datetime(2027, 1, 31, tzinfo=dt_timezone.utc)

        self.assertEqual(
            calculate_subscription_expiry(inicio, 1, "meses"),
            datetime(2027, 2, 28, tzinfo=dt_timezone.utc),
        )

    def test_leap_year_contract(self):
        inicio = datetime(2028, 2, 29, tzinfo=dt_timezone.utc)

        self.assertEqual(
            calculate_subscription_expiry(inicio, 1, "anios"),
            datetime(2029, 2, 28, tzinfo=dt_timezone.utc),
        )

    def test_two_year_contract(self):
        inicio = datetime(2026, 11, 23, tzinfo=dt_timezone.utc)

        self.assertEqual(
            calculate_subscription_expiry(inicio, 2, "anios"),
            datetime(2028, 11, 23, tzinfo=dt_timezone.utc),
        )

    def test_producer_can_create_annual_plan(self):
        self.client.force_login(self.producer)

        response = self.client.post(
            self.url,
            {
                "detalle": "Servicio profesional",
                "precio": 75000,
                "descripcion": "Produccion musical personalizada",
                "beneficios": ["Mezcla", "Masterizacion"],
                "duracion_cantidad": 2,
                "duracion_unidad": "anios",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["duracion_cantidad"], 2)
        self.assertEqual(response.json()["duracion_unidad"], "anios")

    def test_artist_cannot_create_plan(self):
        self.client.force_login(self.artist)

        response = self.client.post(
            self.url,
            {"detalle": "Plan", "precio": 5000},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_invalid_duration_is_rejected(self):
        self.client.force_login(self.producer)

        for cantidad, unidad in [
            (0, "meses"),
            (13, "meses"),
            (6, "anios"),
            (True, "meses"),
            (1, "semanas"),
        ]:
            with self.subTest(cantidad=cantidad, unidad=unidad):
                response = self.client.post(
                    self.url,
                    {
                        "detalle": "Plan invalido",
                        "precio": 5000,
                        "duracion_cantidad": cantidad,
                        "duracion_unidad": unidad,
                    },
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 400)

    def test_other_producer_cannot_edit_plan(self):
        self.client.force_login(self.other)

        response = self.client.patch(
            self.detail_url,
            {"precio": 1000},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

        self.plan.refresh_from_db()
        self.assertEqual(self.plan.precio, 45000)

    def test_owner_can_deactivate_plan(self):
        self.client.force_login(self.producer)

        response = self.client.patch(
            self.detail_url,
            {"activo": False},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["activo"])

        self.client.logout()

        response = self.client.get(self.url)

        ids = [item["id_sus"] for item in response.json()]
        self.assertNotIn(self.plan.pk, ids)

    @patch("app.webpay_reconciliation.reconcile_stale_pending_for_user")
    def test_inactive_plan_cannot_be_purchased(self, reconcile):
        self.plan.activo = False
        self.plan.save(update_fields=["activo"])

        with self.assertRaises(PaymentStartBlocked):
            create_pending_webpay_order(
                user=self.artist,
                amount=self.plan.precio,
                suscripcion=self.plan,
            )

        self.assertFalse(
            WebpayTransaction.objects.filter(
                user=self.artist,
                suscripcion=self.plan,
            ).exists()
        )

    @patch("app.webpay_reconciliation.reconcile_stale_pending_for_user")
    def test_contract_preserves_original_duration(self, reconcile):
        orden = create_pending_webpay_order(
            user=self.artist,
            amount=self.plan.precio,
            suscripcion=self.plan,
        )

        self.assertEqual(
            orden.suscripcion_duracion_cantidad, 1
        )
        self.assertEqual(
            orden.suscripcion_duracion_unidad, "anios"
        )

        self.plan.duracion_unidad = "meses"
        self.plan.duracion_cantidad = 1
        self.plan.save(
            update_fields=[
                "duracion_unidad",
                "duracion_cantidad",
            ]
        )

        inicio = timezone.now()

        orden.status = WebpayTransaction.ESTADO_AUTORIZADO
        orden.fulfilled_at = inicio
        orden.save(update_fields=["status", "fulfilled_at"])

        periodo = subscription_periods(
            self.artist.pk, inicio
        )[self.plan.pk]

        self.assertEqual(
            periodo["expires_at"],
            calculate_subscription_expiry(inicio, 1, "anios"),
        )

        self.assertTrue(
            has_active_subscription(
                self.artist.pk, self.plan.pk, inicio
            )
        )

        self.assertFalse(
            has_active_subscription(
                self.artist.pk,
                self.plan.pk,
                periodo["expires_at"],
            )
        )

    @patch("app.webpay_reconciliation.reconcile_stale_pending_for_user")
    def test_manual_renewal_after_calendar_expiry(self, reconcile):
        from datetime import timedelta

        inicio = datetime(
            2026, 11, 23, 12, 0,
            tzinfo=dt_timezone.utc,
        )

        self.plan.duracion_cantidad = 1
        self.plan.duracion_unidad = "meses"
        self.plan.save(
            update_fields=[
                "duracion_cantidad",
                "duracion_unidad",
            ]
        )

        # Primera contratacion.
        with patch("django.utils.timezone.now", return_value=inicio):
            primera = create_pending_webpay_order(
                user=self.artist,
                amount=self.plan.precio,
                suscripcion=self.plan,
            )

            # Una orden pendiente no activa la membresia.
            self.assertFalse(
                has_active_subscription(
                    self.artist.pk, self.plan.pk
                )
            )

            # Simular confirmacion autorizada del proveedor.
            primera.status = WebpayTransaction.ESTADO_AUTORIZADO
            primera.fulfilled_at = inicio
            primera.save(
                update_fields=["status", "fulfilled_at"]
            )

            self.assertTrue(
                has_active_subscription(
                    self.artist.pk, self.plan.pk
                )
            )

        vencimiento = calculate_subscription_expiry(
            inicio, 1, "meses"
        )

        self.assertEqual(
            vencimiento,
            datetime(
                2026, 12, 23, 12, 0,
                tzinfo=dt_timezone.utc,
            ),
        )

        # La membresia sigue activa justo antes del vencimiento.
        with patch(
            "django.utils.timezone.now",
            return_value=vencimiento - timedelta(microseconds=1),
        ):
            self.assertTrue(
                has_active_subscription(
                    self.artist.pk, self.plan.pk
                )
            )

        # Llegada la fecha de vencimiento.
        with patch(
            "django.utils.timezone.now",
            return_value=vencimiento,
        ):
            self.assertFalse(
                has_active_subscription(
                    self.artist.pk, self.plan.pk
                )
            )

            periodo = subscription_periods(self.artist.pk)[
                self.plan.pk
            ]

            self.assertFalse(periodo["active"])

            # No hubo cobro ni renovacion automatica.
            self.assertEqual(
                WebpayTransaction.objects.filter(
                    user=self.artist,
                    suscripcion=self.plan,
                ).count(),
                1,
            )

            # El artista inicia manualmente otra contratacion.
            segunda = create_pending_webpay_order(
                user=self.artist,
                amount=self.plan.precio,
                suscripcion=self.plan,
            )

            self.assertNotEqual(
                primera.pk,
                segunda.pk,
            )

            self.assertIsNone(segunda.fulfilled_at)

            # La orden pendiente todavia no reactiva el acceso.
            self.assertFalse(
                has_active_subscription(
                    self.artist.pk, self.plan.pk
                )
            )

            # Simular la autorizacion del segundo pago.
            segunda.status = WebpayTransaction.ESTADO_AUTORIZADO
            segunda.fulfilled_at = vencimiento
            segunda.save(
                update_fields=["status", "fulfilled_at"]
            )

            self.assertTrue(
                has_active_subscription(
                    self.artist.pk, self.plan.pk
                )
            )

            renovada = subscription_periods(self.artist.pk)[
                self.plan.pk
            ]

            self.assertEqual(
                renovada["expires_at"],
                datetime(
                    2027, 1, 23, 12, 0,
                    tzinfo=dt_timezone.utc,
                ),
            )

            # Desactivar el plan no anula contratos pagados.
            self.plan.activo = False
            self.plan.save(update_fields=["activo"])

            self.assertTrue(
                has_active_subscription(
                    self.artist.pk, self.plan.pk
                )
            )
