"""Pruebas concurrentes de reportes en PostgreSQL."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from django.contrib.auth.models import User
from django.db import connection, connections
from django.test import (
    Client,
    TransactionTestCase,
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
)
class SubscriptionReportConcurrencyTests(TransactionTestCase):

    def setUp(self):

        self.assertEqual(
            connection.vendor,
            "postgresql",
        )

        self.artists = []

        for index in range(2):

            user = User.objects.create_user(
                username=f"concurrent_artist_{index}",
                password="test-password",
            )

            artist = Usuario.objects.create(
                user=user,
                tipo_usu=Usuario.ARTISTA,
            )

            self.artists.append(artist)

        producer_user = User.objects.create_user(
            username="concurrent_producer",
            password="test-password",
        )

        self.producer = Usuario.objects.create(
            user=producer_user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.plan = Suscripcion.objects.create(
            detalle="Plan concurrente",
            precio=15000,
            user=self.producer,
        )

        for index, artist in enumerate(self.artists):

            WebpayTransaction.objects.create(
                user_id=artist.user_id,
                suscripcion=self.plan,
                buy_order=f"concurrent-order-{index}",
                session_id=f"concurrent-session-{index}",
                amount=15000,
                status=WebpayTransaction.ESTADO_AUTORIZADO,
                fulfilled_at=(
                    timezone.now() - timedelta(days=1)
                ),
            )

        self.url = reverse(
            "api_subscription_reports"
        )

        self.payload = {
            "subscription_id": self.plan.pk,
            "reason": "MISSING_BENEFITS",
            "description": (
                "No se entregaron los beneficios "
                "contratados en esta membresia."
            ),
        }

    def submit(self, user_id, barrier):

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    "SET lock_timeout = '10s'"
                )

                cursor.execute(
                    "SET statement_timeout = '20s'"
                )

            user = User.objects.get(pk=user_id)

            client = Client()

            client.force_login(user)

            barrier.wait(timeout=15)

            response = client.post(
                self.url,
                self.payload,
                content_type="application/json",
            )

            return response.status_code

        finally:

            connections.close_all()

    def simultaneous_requests(self, user_ids):

        barrier = Barrier(len(user_ids))

        with ThreadPoolExecutor(
            max_workers=len(user_ids)
        ) as executor:

            futures = [
                executor.submit(
                    self.submit,
                    user_id,
                    barrier,
                )
                for user_id in user_ids
            ]

            results = [
                future.result(timeout=45)
                for future in futures
            ]

        return sorted(results)

    def test_same_artist_concurrent_reports(self):

        artist = self.artists[0]

        results = self.simultaneous_requests([
            artist.user_id,
            artist.user_id,
        ])

        self.assertEqual(
            results,
            [201, 409],
        )

        self.assertEqual(
            SubscriptionReport.objects.count(),
            1,
        )

        report = SubscriptionReport.objects.get()

        self.assertEqual(
            report.artist_id,
            artist.pk,
        )

        self.assertEqual(
            report.status,
            SubscriptionReport.Status.OPEN,
        )

        print(
            "OK: Solicitudes simultaneas:",
            results,
        )

    def test_different_artists_concurrent_reports(self):

        results = self.simultaneous_requests([
            self.artists[0].user_id,
            self.artists[1].user_id,
        ])

        self.assertEqual(
            results,
            [201, 201],
        )

        self.assertEqual(
            SubscriptionReport.objects.count(),
            2,
        )

        self.assertSetEqual(
            set(
                SubscriptionReport.objects.values_list(
                    "artist_id",
                    flat=True,
                )
            ),
            {
                self.artists[0].pk,
                self.artists[1].pk,
            },
        )

        self.assertEqual(
            SubscriptionReport.objects.filter(
                producer=self.producer,
                subscription=self.plan,
            ).count(),
            2,
        )

        print(
            "OK: Artistas independientes:",
            results,
        )
