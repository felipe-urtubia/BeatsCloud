
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import connections
from django.test import Client, TransactionTestCase, override_settings
from django.urls import reverse

from .models import (
    Genero_Musical,
    HistorialCompra,
    HistorialVenta,
    Track,
    Usuario,
    Venta,
    WebpayTransaction,
)


@override_settings(FRONTEND_URL="http://localhost:5173")
class WebpayConcurrenciaTests(TransactionTestCase):

    def setUp(self):
        self.comprador = User.objects.create_user(
            username="comprador_concurrencia",
            password="test-password",
        )
        self.perfil_comprador = Usuario.objects.create(
            user=self.comprador,
            tipo_usu=Usuario.ARTISTA,
        )

        vendedor = User.objects.create_user(
            username="vendedor_concurrencia",
            password="test-password",
        )
        perfil_vendedor = Usuario.objects.create(
            user=vendedor,
            tipo_usu=Usuario.PRODUCTOR,
        )
        genero = Genero_Musical.objects.create(
            descripcion="Genero concurrencia",
        )
        self.track = Track.objects.create(
            nombre_track="Cancion concurrencia",
            precio=1000,
            genero=genero,
            usuario=perfil_vendedor,
        )
        venta = Venta.objects.create(
            detalle="Compra concurrente",
            fecha=date.today(),
            precio=1000,
            iva=190,
            precio_total=1190,
            usuario_id=self.perfil_comprador,
            track=self.track,
        )

        self.orden = WebpayTransaction.objects.create(
            user=self.comprador,
            buy_order="orden-concurrente-123",
            session_id=self.comprador.username,
            amount=1190,
            cart_snapshot=[{
                "venta_id": venta.pk,
                "track_id": self.track.pk,
                "precio": 1000,
                "iva": 190,
            }],
        )
        self.url = reverse("exito_carrito") + "?spa=1"

    def test_dos_ordenes_mismo_carrito_no_duplican_entrega(self):
        segunda_orden = WebpayTransaction.objects.create(
            user=self.comprador,
            buy_order="orden-concurrente-456",
            session_id=self.comprador.username,
            amount=1190,
            cart_snapshot=self.orden.cart_snapshot,
        )

        def retornar_pago(orden):
            respuesta_webpay = {
                "response_code": 0,
                "status": "AUTHORIZED",
                "buy_order": orden.buy_order,
                "session_id": orden.session_id,
                "amount": 1190,
            }

            with patch("app.views.WebpayOptions"):
                with patch("app.views.Transaction") as transbank:
                    transbank.return_value.commit.return_value = (
                        respuesta_webpay
                    )
                    return Client().post(
                        self.url,
                        {"token_ws": "token-simulado"},
                    )

        # Ambas ordenes fueron creadas antes del primer retorno.
        primer_retorno = retornar_pago(self.orden)
        segundo_retorno = retornar_pago(segunda_orden)

        self.assertEqual(primer_retorno.status_code, 302)
        self.assertIn("pago=exito", primer_retorno["Location"])

        # Una segunda autorizacion sobre el mismo pedido
        # requiere conciliacion, no otra entrega.
        self.assertEqual(segundo_retorno.status_code, 302)
        self.assertIn("pago=revision", segundo_retorno["Location"])

        self.orden.refresh_from_db()
        segunda_orden.refresh_from_db()

        self.assertIsNotNone(self.orden.fulfilled_at)
        self.assertIsNone(segunda_orden.fulfilled_at)

        self.assertEqual(
            HistorialCompra.objects.filter(
                usuario=self.perfil_comprador,
                track=self.track,
            ).count(),
            1,
        )

        self.assertEqual(
            HistorialVenta.objects.filter(
                comprador=self.comprador,
                track=self.track,
            ).count(),
            1,
        )

    def test_dos_ordenes_simultaneas_misma_cancion(self):
        if connections["default"].vendor != "postgresql":
            self.skipTest("Requiere PostgreSQL.")

        segunda = WebpayTransaction.objects.create(
            user=self.comprador,
            buy_order="orden-simultanea-456",
            session_id=self.comprador.username,
            amount=1190,
            cart_snapshot=self.orden.cart_snapshot,
        )

        barrera = Barrier(2)

        respuestas = {
            "token-primero": {
                "response_code": 0,
                "status": "AUTHORIZED",
                "buy_order": self.orden.buy_order,
                "session_id": self.orden.session_id,
                "amount": 1190,
            },
            "token-segundo": {
                "response_code": 0,
                "status": "AUTHORIZED",
                "buy_order": segunda.buy_order,
                "session_id": segunda.session_id,
                "amount": 1190,
            },
        }

        def commit_simulado(token_ws):
            barrera.wait(timeout=15)
            return respuestas[token_ws].copy()

        def enviar_retorno(token):
            try:
                respuesta = Client().post(
                    self.url,
                    {"token_ws": token},
                )
                return (
                    respuesta.status_code,
                    respuesta.get("Location", ""),
                )
            finally:
                connections.close_all()

        with patch("app.views.WebpayOptions"):
            with patch("app.views.Transaction") as transbank:
                transbank.return_value.commit.side_effect = (
                    commit_simulado
                )

                with ThreadPoolExecutor(max_workers=2) as ejecutor:
                    trabajos = [
                        ejecutor.submit(
                            enviar_retorno, "token-primero"
                        ),
                        ejecutor.submit(
                            enviar_retorno, "token-segundo"
                        ),
                    ]

                    resultados = [
                        trabajo.result(timeout=30)
                        for trabajo in trabajos
                    ]

        self.assertEqual(
            [estado for estado, _ in resultados],
            [302, 302],
        )

        destinos = [url for _, url in resultados]

        self.assertEqual(
            sum("pago=exito" in url for url in destinos),
            1,
        )
        self.assertEqual(
            sum("pago=revision" in url for url in destinos),
            1,
        )

        self.orden.refresh_from_db()
        segunda.refresh_from_db()

        for orden in (self.orden, segunda):
            self.assertEqual(
                orden.status,
                WebpayTransaction.ESTADO_AUTORIZADO,
            )

        self.assertEqual(
            sum(
                orden.fulfilled_at is not None
                for orden in (self.orden, segunda)
            ),
            1,
        )

        self.assertEqual(
            HistorialCompra.objects.filter(
                usuario=self.perfil_comprador,
                track=self.track,
            ).count(),
            1,
        )

        self.assertEqual(
            HistorialVenta.objects.filter(
                comprador=self.comprador,
                track=self.track,
            ).count(),
            1,
        )

    def test_dos_retornos_simultaneos_registran_una_sola_venta(self):
        if connections["default"].vendor != "postgresql":
            self.skipTest("La prueba requiere PostgreSQL.")

        barrera = Barrier(2)

        respuesta_webpay = {
            "response_code": 0,
            "status": "AUTHORIZED",
            "buy_order": self.orden.buy_order,
            "session_id": self.orden.session_id,
            "amount": 1190,
        }

        def commit_simulado(*args, **kwargs):
            # Ambas solicitudes alcanzan la autorizacion
            # antes de intentar registrar la compra.
            barrera.wait(timeout=15)
            return respuesta_webpay.copy()

        def solicitar_retorno():
            try:
                cliente = Client()
                respuesta = cliente.post(
                    self.url,
                    {"token_ws": "token-simulado"},
                )
                return (
                    respuesta.status_code,
                    respuesta.get("Location", ""),
                )
            finally:
                connections.close_all()

        with patch("app.views.WebpayOptions"):
            with patch("app.views.Transaction") as transbank:
                transbank.return_value.commit.side_effect = (
                    commit_simulado
                )

                with ThreadPoolExecutor(max_workers=2) as ejecutor:
                    trabajos = [
                        ejecutor.submit(solicitar_retorno)
                        for _ in range(2)
                    ]
                    resultados = [
                        trabajo.result(timeout=30)
                        for trabajo in trabajos
                    ]

        self.assertEqual(len(resultados), 2)
        self.assertTrue(
            all(estado == 302 for estado, _ in resultados),
            resultados,
        )
        self.assertTrue(
            any("pago=exito" in url for _, url in resultados),
            resultados,
        )
        self.assertTrue(
            all(
                "pago=exito" in url or "pago=revision" in url
                for _, url in resultados
            ),
            resultados,
        )

        self.orden.refresh_from_db()

        self.assertEqual(
            self.orden.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )
        self.assertIsNotNone(self.orden.fulfilled_at)

        self.assertEqual(
            HistorialCompra.objects.filter(
                usuario=self.perfil_comprador,
                track=self.track,
            ).count(),
            1,
        )
        self.assertEqual(
            HistorialVenta.objects.filter(
                comprador=self.comprador,
                track=self.track,
            ).count(),
            1,
        )
