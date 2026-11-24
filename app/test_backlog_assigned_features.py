"""Regresión API de compras confirmadas y favoritos persistentes del artista."""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import (
    Genero_Musical,
    HistorialCompra,
    Track,
    Usuario,
    WebpayTransaction,
)


class CompletedPurchaseHistoryApiTests(TestCase):
    def setUp(self):
        self.artist_user = User.objects.create_user(
            username="backlog_buyer",
            password="Local-test-only-8812!",
        )
        self.artist = Usuario.objects.create(
            user=self.artist_user,
            tipo_usu=Usuario.ARTISTA,
            nombre_artistico="Artista Comprador",
        )
        producer_user = User.objects.create_user(
            username="backlog_producer",
            password="Local-test-only-9913!",
        )
        self.producer = Usuario.objects.create(
            user=producer_user,
            tipo_usu=Usuario.PRODUCTOR,
            nombre_artistico="Productor Real",
        )
        self.genre = Genero_Musical.objects.create(descripcion="Pop")
        self.track = Track.objects.create(
            nombre_track="Compra confirmada",
            precio=1000,
            track="canciones/compra-confirmada.wav",
            genero=self.genre,
            usuario=self.producer,
            media_status="ready",
        )
        self.order = self.order_for(
            self.artist_user,
            "orden-real-1",
            WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at=timezone.now(),
            snapshot=[{
                "venta_id": 501,
                "track_id": self.track.pk,
                "precio": 1000,
                "iva": 190,
            }],
        )
        HistorialCompra.objects.create(usuario=self.artist, track=self.track)

    def order_for(self, user, buy_order, status, *, fulfilled_at=None, snapshot=None, subscription=None):
        return WebpayTransaction.objects.create(
            user=user,
            buy_order=buy_order,
            session_id=f"session-{buy_order}",
            amount=Decimal("1190.00"),
            status=status,
            fulfilled_at=fulfilled_at,
            cart_snapshot=snapshot or [],
            suscripcion=subscription,
            webpay_token=f"private-{buy_order}",
        )

    def test_only_own_authorized_fulfilled_cart_orders_are_returned(self):
        self.order_for(
            self.artist_user,
            "orden-pendiente",
            WebpayTransaction.ESTADO_PENDIENTE,
            fulfilled_at=timezone.now(),
            snapshot=self.order.cart_snapshot,
        )
        self.order_for(
            self.artist_user,
            "orden-no-entregada",
            WebpayTransaction.ESTADO_AUTORIZADO,
            snapshot=self.order.cart_snapshot,
        )
        other = User.objects.create_user(username="other_buyer", password="Local-test-only-9914!")
        self.order_for(
            other,
            "orden-ajena",
            WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at=timezone.now(),
            snapshot=self.order.cart_snapshot,
        )

        self.client.force_login(self.artist_user)
        response = self.client.get("/api/mis-compras/confirmadas/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        row = response.json()[0]
        self.assertEqual(row["buy_order"], "orden-real-1")
        self.assertEqual(row["order_amount"], 1190)
        self.assertEqual(row["line_amount"], 1190)
        self.assertEqual(row["status"], WebpayTransaction.ESTADO_AUTORIZADO)
        self.assertEqual(row["track"]["nombre_track"], self.track.nombre_track)
        self.assertEqual(row["track"]["usuario"]["nombre_artistico"], "Productor Real")
        self.assertTrue(row["download_available"])
        self.assertNotIn("webpay_token", row)

    def test_order_without_history_is_not_claimed_as_a_completed_purchase(self):
        HistorialCompra.objects.filter(usuario=self.artist, track=self.track).delete()
        self.client.force_login(self.artist_user)
        self.assertEqual(self.client.get("/api/mis-compras/confirmadas/").json(), [])

    def test_endpoint_requires_authentication_and_get(self):
        self.assertEqual(self.client.get("/api/mis-compras/confirmadas/").status_code, 401)
        self.client.force_login(self.artist_user)
        self.assertEqual(self.client.post("/api/mis-compras/confirmadas/").status_code, 405)

    def test_subscription_orders_are_not_track_purchases(self):
        from .models import Suscripcion

        plan = Suscripcion.objects.create(
            detalle="Plan productor",
            precio=1190,
            user=self.producer,
        )
        self.order_for(
            self.artist_user,
            "orden-suscripcion",
            WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at=timezone.now(),
            snapshot=self.order.cart_snapshot,
            subscription=plan,
        )
        self.client.force_login(self.artist_user)
        orders = self.client.get("/api/mis-compras/confirmadas/").json()
        self.assertEqual([row["buy_order"] for row in orders], ["orden-real-1"])


class PersistentLikeApiTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="like_artist", password="Local-test-only-7711!")
        self.artist = Usuario.objects.create(user=user, tipo_usu=Usuario.ARTISTA)
        self.user = user
        producer = User.objects.create_user(username="like_producer", password="Local-test-only-7712!")
        self.producer = Usuario.objects.create(user=producer, tipo_usu=Usuario.PRODUCTOR)
        genre = Genero_Musical.objects.create(descripcion="Rock")
        self.track = Track.objects.create(
            nombre_track="Favorita persistente",
            precio=1000,
            track="canciones/favorita.wav",
            genero=genre,
            usuario=self.producer,
        )
        self.url = f"/api/like/{self.track.pk}/"

    def set_like(self, liked):
        return self.client.post(
            self.url,
            data={"liked": liked},
            content_type="application/json",
        )

    def test_artist_can_idempotently_add_and_remove_persisted_like(self):
        self.client.force_login(self.user)
        self.assertEqual(self.set_like(True).json(), {"liked": True})
        self.assertEqual(self.set_like(True).json(), {"liked": True})
        self.assertEqual(self.artist.tracks_gustados.filter(pk=self.track.pk).count(), 1)
        self.assertEqual(self.set_like(False).json(), {"liked": False})
        self.assertEqual(self.set_like(False).json(), {"liked": False})
        self.assertFalse(self.artist.tracks_gustados.filter(pk=self.track.pk).exists())

    def test_invalid_desired_state_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            data='{"liked":"yes"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_producer_cannot_use_artist_favorites(self):
        self.client.force_login(self.producer.user)
        self.assertEqual(self.set_like(True).status_code, 403)

    def test_legacy_toggle_remains_compatible(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(self.url).json(), {"liked": True})
        self.assertEqual(self.client.post(self.url).json(), {"liked": False})
