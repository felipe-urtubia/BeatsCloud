"""Pruebas de aislamiento de datos al cambiar entre cuentas Django."""

import json
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase

from app.models import (
    Genero_Musical,
    HistorialCompra,
    HistorialVenta,
    Track,
    Usuario,
    Venta,
)


class AccountSwitchIsolationTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

        self.artist_user = User.objects.create_user(
            username="aislamiento_artista",
            password="ClaveArtista123!",
        )

        self.producer_user = User.objects.create_user(
            username="aislamiento_productor",
            password="ClaveProductor123!",
        )

        self.artist = Usuario.objects.create(
            user=self.artist_user,
            tipo_usu=Usuario.ARTISTA,
            nombre_artistico="Artista Aislamiento",
        )

        self.producer = Usuario.objects.create(
            user=self.producer_user,
            tipo_usu=Usuario.PRODUCTOR,
            nombre_artistico="Productor Aislamiento",
        )

        genre = Genero_Musical.objects.create(
            descripcion="Genero Aislamiento",
        )

        # Dos tracks distintos para evitar mezclar carrito y compra.
        self.cart_track = Track.objects.create(
            nombre_track="Beat Exclusivo Carrito",
            precio=1000,
            track="canciones/aislamiento_carrito.mp3",
            genero=genre,
            usuario=self.producer,
        )

        self.bought_track = Track.objects.create(
            nombre_track="Beat Exclusivo Comprado",
            precio=2000,
            track="canciones/aislamiento_comprado.mp3",
            genero=genre,
            usuario=self.producer,
        )

        # Solamente el artista tiene este carrito pendiente.
        self.artist_cart = Venta.objects.create(
            usuario_id=self.artist,
            track=self.cart_track,
            detalle="Carrito privado del artista",
            fecha=date.today(),
            precio=1000,
            iva=190,
            precio_total=1190,
            completada=False,
        )

        # Solamente el artista tiene esta compra.
        HistorialCompra.objects.create(
            usuario=self.artist,
            track=self.bought_track,
        )

        # Solamente el productor tiene esta venta.
        HistorialVenta.objects.create(
            comprador=self.artist_user,
            track=self.bought_track,
            precio=Decimal("2000.00"),
        )

    def csrf(self):
        response = self.client.get("/api/csrf/")
        self.assertEqual(response.status_code, 200)
        return response.json()["detail"]

    def post_json(self, path, data):
        return self.client.post(
            path,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf(),
        )

    def login_artist_and_add_producer(self):
        login = self.post_json(
            "/api/auth/login/",
            {
                "username": "aislamiento_artista",
                "password": "ClaveArtista123!",
            },
        )

        self.assertEqual(login.status_code, 200)

        added = self.post_json(
            "/api/auth/accounts/add/",
            {
                "username": "aislamiento_productor",
                "password": "ClaveProductor123!",
            },
        )

        self.assertEqual(added.status_code, 200)

    def switch_to(self, user_id):
        response = self.post_json(
            "/api/auth/accounts/switch/",
            {"user_id": user_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["active_user_id"], user_id)

    def private_data(self):
        cart_response = self.client.get("/api/carrito/")
        purchases_response = self.client.get("/api/mis-compras/")
        sales_response = self.client.get("/api/mis-ventas/")

        for response in (
            cart_response,
            purchases_response,
            sales_response,
        ):
            self.assertEqual(
                response.status_code,
                200,
                response.content[:500],
            )

        cart = cart_response.json()
        purchases = purchases_response.json()
        sales = sales_response.json()

        self.assertIsInstance(cart, dict)
        self.assertIn("items", cart)
        self.assertIsInstance(purchases, list)
        self.assertIsInstance(sales, list)

        return cart["items"], purchases, sales

    def test_private_data_remains_isolated_after_switching(self):
        self.login_artist_and_add_producer()

        # ARTISTA: carrito y compra, pero ninguna venta.
        artist_cart, artist_purchases, artist_sales = (
            self.private_data()
        )

        self.assertEqual(len(artist_cart), 1)
        self.assertEqual(
            artist_cart[0]["track"],
            self.cart_track.pk,
        )
        self.assertEqual(len(artist_purchases), 1)
        self.assertEqual(len(artist_sales), 0)

        # PRODUCTOR: sin carrito ni compras; tiene una venta.
        self.switch_to(self.producer_user.pk)

        producer_cart, producer_purchases, producer_sales = (
            self.private_data()
        )

        self.assertEqual(len(producer_cart), 0)
        self.assertEqual(len(producer_purchases), 0)
        self.assertEqual(len(producer_sales), 1)

        # REGRESO AL ARTISTA: los datos originales siguen intactos.
        self.switch_to(self.artist_user.pk)

        cart_again, purchases_again, sales_again = (
            self.private_data()
        )

        self.assertEqual(len(cart_again), 1)
        self.assertEqual(len(purchases_again), 1)
        self.assertEqual(len(sales_again), 0)

    def test_producer_cannot_delete_artist_cart(self):
        self.login_artist_and_add_producer()

        self.switch_to(self.producer_user.pk)

        # Intentar eliminar directamente una venta/carrito ajeno.
        response = self.client.delete(
            f"/api/carrito/{self.artist_cart.pk}/",
            HTTP_X_CSRFTOKEN=self.csrf(),
        )

        self.assertIn(response.status_code, (403, 404))

        # No debe haber eliminado el registro del artista.
        self.assertTrue(
            Venta.objects.filter(
                pk=self.artist_cart.pk,
                usuario_id=self.artist,
            ).exists()
        )

        self.switch_to(self.artist_user.pk)

        items, _, _ = self.private_data()
        self.assertEqual(len(items), 1)

    def test_logout_removes_private_access(self):
        self.login_artist_and_add_producer()

        response = self.post_json("/api/auth/logout/", {})
        self.assertEqual(response.status_code, 200)

        for path in (
            "/api/carrito/",
            "/api/mis-compras/",
            "/api/mis-ventas/",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 401)
