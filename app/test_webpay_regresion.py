from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    HistorialCompra,
    HistorialVenta,
    Usuario,
    WebpayTransaction,
)


@override_settings(FRONTEND_URL="http://localhost:5173")
class WebpayRegresionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="comprador_test",
            password="test-password",
        )
        self.profile = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.ARTISTA,
        )
        self.payment = WebpayTransaction.objects.create(
            user=self.user,
            buy_order="orden-test-123",
            session_id=self.user.username,
            amount="1190.00",
            status=WebpayTransaction.ESTADO_PENDIENTE,
        )
        self.url = reverse("exito_carrito") + "?spa=1"

    def simular_retorno(self, response_data):
        with patch("app.views.WebpayOptions"):
            with patch("app.views.Transaction") as transaction:
                transaction.return_value.commit.return_value = response_data
                return self.client.post(
                    self.url,
                    {"token_ws": "token-simulado"},
                )

    def respuesta_webpay(self, code, status):
        return {
            "response_code": code,
            "status": status,
            "buy_order": self.payment.buy_order,
            "session_id": self.payment.session_id,
            "amount": 1190,
        }

    def test_autorizacion_con_datos_inconsistentes_requiere_revision(self):
        escenarios = (
            ("amount", 9999),
            ("session_id", "otra_sesion"),
            ("buy_order", "orden_desconocida"),
        )

        for campo, valor in escenarios:
            with self.subTest(campo=campo):
                respuesta_webpay = self.respuesta_webpay(
                    0, "AUTHORIZED"
                )
                respuesta_webpay[campo] = valor

                respuesta = self.simular_retorno(
                    respuesta_webpay
                )

                self.assertEqual(respuesta.status_code, 302)
                self.assertIn("pago=revision", respuesta.url)

                self.payment.refresh_from_db()
                self.assertEqual(
                    self.payment.status,
                    WebpayTransaction.ESTADO_PENDIENTE,
                )
                self.assertIsNone(self.payment.fulfilled_at)

                self.assertEqual(
                    HistorialCompra.objects.count(), 0
                )
                self.assertEqual(
                    HistorialVenta.objects.count(), 0
                )

    def test_pago_rechazado_no_registra_compra(self):
        response = self.simular_retorno(
            self.respuesta_webpay(-1, "FAILED")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("pago=fracaso", response.url)
        self.assertEqual(HistorialCompra.objects.count(), 0)
        self.assertEqual(HistorialVenta.objects.count(), 0)

    def test_retorno_sin_token_no_cancela_orden(self):
        from django.urls import reverse

        respuesta = self.client.post(
            reverse("exito_carrito") + "?spa=1",
            {
                "TBK_ORDEN_COMPRA": self.payment.buy_order,
                "TBK_ID_SESION": self.payment.session_id,
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("pago=revision", respuesta["Location"])

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "PENDING")
        self.assertIsNone(self.payment.fulfilled_at)


    def test_pago_autorizado_sin_snapshot_requiere_revision(self):
        ventas = MagicMock()
        ventas.exists.return_value = True
        ventas.__iter__.return_value = iter([
            SimpleNamespace(precio=800, iva=152)
        ])

        with patch("app.views.Venta.objects.filter", return_value=ventas):
            response = self.simular_retorno(
                self.respuesta_webpay(0, "AUTHORIZED")
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("pago=revision", response.url)

        self.payment.refresh_from_db()
        self.assertEqual(
            self.payment.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )
        self.assertEqual(HistorialCompra.objects.count(), 0)
        self.assertEqual(HistorialVenta.objects.count(), 0)

    def test_carrito_modificado_durante_webpay_entrega_solo_snapshot(self):
        from datetime import date
        from .models import Genero_Musical, Track, Venta

        vendedor = User.objects.create_user(
            username="vendedor_snapshot_test",
            password="test-password",
        )
        perfil_vendedor = Usuario.objects.create(
            user=vendedor,
            tipo_usu=Usuario.PRODUCTOR,
        )
        genero = Genero_Musical.objects.create(
            descripcion="Genero snapshot Webpay",
        )

        cancion_a = Track.objects.create(
            nombre_track="Cancion A pagada",
            precio=1000,
            genero=genero,
            usuario=perfil_vendedor,
        )
        cancion_b = Track.objects.create(
            nombre_track="Cancion B agregada despues",
            precio=3000,
            genero=genero,
            usuario=perfil_vendedor,
        )

        venta_a = Venta.objects.create(
            detalle="Pedido original",
            fecha=date.today(),
            precio=1000,
            iva=190,
            precio_total=1190,
            usuario_id=self.profile,
            track=cancion_a,
        )

        # Guardar el pedido antes de modificar el carrito.
        self.payment.cart_snapshot = [{
            "venta_id": venta_a.pk,
            "track_id": cancion_a.pk,
            "precio": 1000,
            "iva": 190,
        }]
        self.payment.save(update_fields=["cart_snapshot"])

        # Agregar otra cancion antes de que Webpay confirme.
        venta_b = Venta.objects.create(
            detalle="Agregada durante Webpay",
            fecha=date.today(),
            precio=3000,
            iva=570,
            precio_total=3570,
            usuario_id=self.profile,
            track=cancion_b,
        )

        respuesta = self.simular_retorno(
            self.respuesta_webpay(0, "AUTHORIZED")
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("pago=exito", respuesta.url)

        self.payment.refresh_from_db()
        self.assertEqual(
            self.payment.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )
        self.assertIsNotNone(self.payment.fulfilled_at)

        # Solo la cancion original debe estar comprada.
        self.assertTrue(
            HistorialCompra.objects.filter(
                usuario=self.profile,
                track=cancion_a,
            ).exists()
        )
        self.assertFalse(
            HistorialCompra.objects.filter(
                usuario=self.profile,
                track=cancion_b,
            ).exists()
        )

        self.assertEqual(
            HistorialVenta.objects.filter(
                comprador=self.user,
                track=cancion_a,
            ).count(),
            1,
        )
        self.assertEqual(
            HistorialVenta.objects.filter(
                comprador=self.user,
                track=cancion_b,
            ).count(),
            0,
        )

        # El pedido pagado desaparece del carrito.
        self.assertFalse(
            Venta.objects.filter(pk=venta_a.pk).exists()
        )

        # La cancion nueva permanece pendiente.
        self.assertTrue(
            Venta.objects.filter(
                pk=venta_b.pk,
                completada=False,
            ).exists()
        )

    def test_error_registro_tras_autorizacion_no_entrega_parcial(self):
        from datetime import date
        from .models import Genero_Musical, Track, Venta

        vendedor = User.objects.create_user(
            username="vendedor_fallo_webpay",
            password="test-password",
        )
        perfil_vendedor = Usuario.objects.create(
            user=vendedor,
            tipo_usu=Usuario.PRODUCTOR,
        )
        genero = Genero_Musical.objects.create(
            descripcion="Genero prueba error Webpay",
        )
        track = Track.objects.create(
            nombre_track="Cancion prueba error",
            precio=1000,
            genero=genero,
            usuario=perfil_vendedor,
        )
        venta = Venta.objects.create(
            detalle="Compra con error simulado",
            fecha=date.today(),
            precio=1000,
            iva=190,
            precio_total=1190,
            usuario_id=self.profile,
            track=track,
        )

        self.payment.cart_snapshot = [{
            "venta_id": venta.pk,
            "track_id": track.pk,
            "precio": 1000,
            "iva": 190,
        }]
        self.payment.save(update_fields=["cart_snapshot"])

        # Simular una falla de PostgreSQL al registrar la venta.
        with patch(
            "app.views.HistorialVenta.objects.create",
            side_effect=RuntimeError("Fallo simulado de registro"),
        ):
            respuesta = self.simular_retorno(
                self.respuesta_webpay(0, "AUTHORIZED")
            )

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("pago=revision", respuesta.url)

        self.payment.refresh_from_db()

        # La autorizacion no debe perderse.
        self.assertEqual(
            self.payment.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )

        # La entrega no se completo.
        self.assertIsNone(self.payment.fulfilled_at)

        # No deben quedar registros de compra parciales.
        self.assertEqual(
            HistorialCompra.objects.filter(
                usuario=self.profile,
                track=track,
            ).count(),
            0,
        )
        self.assertEqual(
            HistorialVenta.objects.filter(
                comprador=self.user,
                track=track,
            ).count(),
            0,
        )

        # La venta pendiente no debe desaparecer.
        self.assertTrue(
            Venta.objects.filter(
                pk=venta.pk,
                completada=False,
            ).exists()
        )

    def test_pago_aprobado_registra_compra(self):
        from datetime import date
        from .models import Genero_Musical, Track, Venta

        vendedor = User.objects.create_user(
            username="vendedor_webpay_test",
            password="test-password",
        )
        perfil_vendedor = Usuario.objects.create(
            user=vendedor,
            tipo_usu=Usuario.PRODUCTOR,
        )
        genero = Genero_Musical.objects.create(
            descripcion="Genero Webpay Test",
        )
        track = Track.objects.create(
            nombre_track="Instrumental Webpay Test",
            precio=1000,
            genero=genero,
            usuario=perfil_vendedor,
        )
        Venta.objects.create(
            detalle="Compra de prueba",
            fecha=date.today(),
            precio=1000,
            iva=190,
            precio_total=1190,
            usuario_id=self.profile,
            track=track,
        )

        venta_original = Venta.objects.get(
            usuario_id=self.profile,
            track=track,
        )
        self.payment.cart_snapshot = [{
            "venta_id": venta_original.pk,
            "track_id": track.pk,
            "precio": 1000,
            "iva": 190,
        }]
        self.payment.save(update_fields=["cart_snapshot"])

        response = self.simular_retorno(
            self.respuesta_webpay(0, "AUTHORIZED")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("pago=exito", response.url)

        self.payment.refresh_from_db()
        self.assertEqual(
            self.payment.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )

        self.assertTrue(
            HistorialCompra.objects.filter(
                usuario=self.profile,
                track=track,
            ).exists()
        )
        self.assertEqual(
            HistorialVenta.objects.filter(
                comprador=self.user,
                track=track,
            ).count(),
            1,
        )
        self.assertFalse(
            Venta.objects.filter(
                usuario_id=self.profile,
                track=track,
                completada=False,
            ).exists()
        )

    def test_pago_repetido_no_entrega_otro_track(self):
        from datetime import date
        from .models import Genero_Musical, Track, Venta

        vendedor = User.objects.create_user(
            username="vendedor_duplicados",
            password="test-password",
        )
        perfil = Usuario.objects.create(
            user=vendedor,
            tipo_usu=Usuario.PRODUCTOR,
        )
        genero = Genero_Musical.objects.create(
            descripcion="Genero prueba duplicados",
        )

        def crear_track(nombre):
            return Track.objects.create(
                nombre_track=nombre,
                precio=1000,
                genero=genero,
                usuario=perfil,
            )

        def agregar_carrito(track):
            return Venta.objects.create(
                detalle="Compra de prueba",
                fecha=date.today(),
                precio=1000,
                iva=190,
                precio_total=1190,
                usuario_id=self.profile,
                track=track,
            )

        track_original = crear_track("Primera cancion")
        track_nuevo = crear_track("Segunda cancion")

        agregar_carrito(track_original)

        venta_original = Venta.objects.get(
            usuario_id=self.profile,
            track=track_original,
        )
        self.payment.cart_snapshot = [{
            "venta_id": venta_original.pk,
            "track_id": track_original.pk,
            "precio": 1000,
            "iva": 190,
        }]
        self.payment.save(update_fields=["cart_snapshot"])

        respuesta = self.respuesta_webpay(0, "AUTHORIZED")

        primer_retorno = self.simular_retorno(respuesta)

        self.assertIn("pago=exito", primer_retorno.url)
        self.assertTrue(
            HistorialCompra.objects.filter(
                usuario=self.profile,
                track=track_original,
            ).exists()
        )

        # El comprador agrega otra cancion posteriormente.
        agregar_carrito(track_nuevo)

        # Simular nuevamente el retorno de la orden antigua.
        self.simular_retorno(respuesta)

        # La orden anterior no debe entregar la nueva cancion.
        self.assertFalse(
            HistorialCompra.objects.filter(
                usuario=self.profile,
                track=track_nuevo,
            ).exists()
        )

        self.assertEqual(
            HistorialVenta.objects.filter(
                comprador=self.user,
            ).count(),
            1,
        )

        self.assertTrue(
            Venta.objects.filter(
                usuario_id=self.profile,
                track=track_nuevo,
                completada=False,
            ).exists()
        )