"""Pruebas D10 con conexiones concurrentes a PostgreSQL."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from queue import Queue
from time import monotonic, sleep

from django.contrib.auth.models import User
from django.db import connection, connections, transaction
from django.test import (
    RequestFactory,
    TransactionTestCase,
    override_settings,
)
from django.utils import timezone

from app.api_shim import claim_free_track_api

from app.license_service import (
    issue_license_for_purchase,
    verify_license,
)

from app.models import (
    Genero_Musical,
    HistorialCompra,
    Licencia,
    Track,
    Usuario,
    WebpayTransaction,
)


@override_settings(
    LICENSE_SIGNING_KEY="test-only-concurrency-d10-" + "e" * 48,
    LICENSE_SIGNING_KEY_FALLBACKS=(),
)
class LicenseConcurrencyTests(TransactionTestCase):

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("Esta prueba requiere PostgreSQL.")

        self.comprador = User.objects.create_user(
            username="d10_concurrent_buyer",
            password="test-only-password",
        )

        self.perfil = Usuario.objects.create(
            user=self.comprador,
            tipo_usu=Usuario.ARTISTA,
        )

        productor = User.objects.create_user(
            username="d10_concurrent_producer",
            password="test-only-password",
        )

        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero = Genero_Musical.objects.create(
            descripcion="Genero concurrencia D10",
        )

        self.track = Track.objects.create(
            nombre_track="Track concurrencia D10",
            precio=1000,
            genero=genero,
            usuario=perfil_productor,
            media_status="ready",
        )

    def _crear_compra_comercial(self):
        compra = HistorialCompra.objects.create(
            usuario=self.perfil,
            track=self.track,
            origen_adquisicion=HistorialCompra.ORIGEN_WEBPAY,
        )

        orden = WebpayTransaction.objects.create(
            user=self.comprador,
            buy_order="orden-d10-concurrente",
            session_id=self.comprador.username,
            amount=Decimal("1190.00"),
            status=WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at=timezone.now(),
            cart_snapshot=[
                {
                    "venta_id": 1001,
                    "track_id": self.track.pk,
                    "precio": 1000,
                    "iva": 190,
                }
            ],
        )

        return compra.pk, orden.pk

    @staticmethod
    def _trabajador(operacion, pids):
        # Cada hilo utiliza su propia conexion Django.
        conexiones = connections["default"]

        try:
            with conexiones.cursor() as cursor:
                cursor.execute("SET lock_timeout = '20s'")
                cursor.execute("SET statement_timeout = '30s'")
                cursor.execute("SELECT pg_backend_pid()")
                pid = cursor.fetchone()[0]

            pids.put(pid)

            return operacion()

        finally:
            conexiones.close()

    def _esperar_bloqueos(self, pids, pid_principal):
        limite = monotonic() + 8

        while monotonic() < limite:
            bloqueos = []

            with connection.cursor() as cursor:
                for pid in pids:
                    cursor.execute(
                        "SELECT pg_blocking_pids(%s)",
                        [pid],
                    )

                    bloqueos.append(
                        cursor.fetchone()[0]
                    )

            # Los trabajadores deben estar esperando.
            # Al menos uno depende del bloqueo principal.
            if all(bloqueos) and any(
                pid_principal in grupo
                for grupo in bloqueos
            ):
                return

            sleep(0.05)

        self.fail(
            "No se confirmaron bloqueos reales en PostgreSQL."
        )

    def _ejecutar_con_bloqueo(
        self,
        modelo,
        pk,
        operacion,
        cantidad=2,
    ):
        pids = Queue()

        with ThreadPoolExecutor(
            max_workers=cantidad
        ) as executor:

            # Liberar el bloqueo antes de esperar los resultados.
            with transaction.atomic():
                modelo.objects.select_for_update().get(
                    pk=pk
                )

                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    pid_principal = cursor.fetchone()[0]

                futuros = [
                    executor.submit(
                        self._trabajador,
                        operacion,
                        pids,
                    )
                    for _ in range(cantidad)
                ]

                trabajadores = [
                    pids.get(timeout=10)
                    for _ in range(cantidad)
                ]

                self.assertEqual(
                    len(set(trabajadores)),
                    cantidad,
                )

                self.assertNotIn(
                    pid_principal,
                    trabajadores,
                )

                self._esperar_bloqueos(
                    trabajadores,
                    pid_principal,
                )

                self.assertTrue(
                    all(
                        not futuro.done()
                        for futuro in futuros
                    )
                )

            # El bloqueo principal ya fue liberado.
            return [
                futuro.result(timeout=35)
                for futuro in futuros
            ]

    def test_adquisiciones_gratuitas_concurrentes(self):
        Track.objects.filter(
            pk=self.track.pk
        ).update(precio=0)

        usuario_id = self.comprador.pk
        track_id = self.track.pk

        def reclamar():
            request = RequestFactory().post(
                f"/api/track/{track_id}/claim-free/"
            )

            request.user = User.objects.get(
                pk=usuario_id
            )

            respuesta = claim_free_track_api(
                request,
                track_id,
            )

            return respuesta.status_code

        resultados = self._ejecutar_con_bloqueo(
            Usuario,
            self.perfil.pk,
            reclamar,
        )

        self.assertEqual(resultados, [200, 200])

        compras = HistorialCompra.objects.filter(
            usuario=self.perfil,
            track=self.track,
        )

        self.assertEqual(compras.count(), 1)

        self.assertEqual(
            compras.get().origen_adquisicion,
            HistorialCompra.ORIGEN_GRATUITO,
        )

        self.assertEqual(Licencia.objects.count(), 0)

    def _comprobar_emisiones_concurrentes(
        self,
        modelo_bloqueado,
    ):
        compra_id, orden_id = (
            self._crear_compra_comercial()
        )

        def emitir():
            compra = HistorialCompra.objects.get(
                pk=compra_id
            )

            orden = WebpayTransaction.objects.get(
                pk=orden_id
            )

            licencia, creada = (
                issue_license_for_purchase(
                    compra,
                    orden,
                )
            )

            return (
                licencia.pk,
                licencia.license_code,
                licencia.verification_hash,
                creada,
            )

        bloqueo_id = (
            orden_id
            if modelo_bloqueado is WebpayTransaction
            else compra_id
        )

        resultados = self._ejecutar_con_bloqueo(
            modelo_bloqueado,
            bloqueo_id,
            emitir,
        )

        primero, segundo = resultados

        # Mismo identificador, codigo y firma.
        self.assertEqual(
            primero[:3],
            segundo[:3],
        )

        # Exactamente una emision nueva.
        self.assertEqual(
            sorted([primero[3], segundo[3]]),
            [False, True],
        )

        self.assertEqual(Licencia.objects.count(), 1)

        licencia = Licencia.objects.get(
            compra_id=compra_id
        )

        self.assertTrue(
            verify_license(licencia)
        )

    def test_emisiones_concurrentes_bloqueo_orden(self):
        self._comprobar_emisiones_concurrentes(
            WebpayTransaction
        )

    def test_emisiones_concurrentes_bloqueo_compra(self):
        self._comprobar_emisiones_concurrentes(
            HistorialCompra
        )

    def _crear_pedido_cruzado(self):
        from datetime import date
        from app.models import Venta

        venta = Venta.objects.create(
            detalle="Pedido concurrencia cruzada D10",
            fecha=date.today(),
            precio=1000,
            iva=190,
            precio_total=1190,
            usuario_id=self.perfil,
            track=self.track,
        )

        orden = WebpayTransaction.objects.create(
            user=self.comprador,
            buy_order="orden-d10-cruzada",
            session_id=self.comprador.username,
            amount=Decimal("1190.00"),
            status=WebpayTransaction.ESTADO_PENDIENTE,
            webpay_token="token-d10-cruzado",
            cart_snapshot=[
                {
                    "venta_id": venta.pk,
                    "track_id": self.track.pk,
                    "precio": 1000,
                    "iva": 190,
                }
            ],
        )

        # El precio cambia despues de iniciar el pedido.
        Track.objects.filter(
            pk=self.track.pk
        ).update(precio=0)

        return orden, venta

    def _reclamar_gratis_cruzado(self):
        request = RequestFactory().post(
            f"/api/track/{self.track.pk}/claim-free/"
        )

        request.user = User.objects.get(
            pk=self.comprador.pk
        )

        respuesta = claim_free_track_api(
            request,
            self.track.pk,
        )

        return respuesta.status_code

    @staticmethod
    def _confirmar_webpay_cruzado():
        from django.test import Client
        from django.urls import reverse

        url = reverse("exito_carrito") + "?spa=1"

        respuesta = Client().post(
            url,
            {"token_ws": "token-d10-cruzado"},
        )

        return (
            respuesta.status_code,
            respuesta.get("Location", ""),
        )

    def _ejecutar_cruce_controlado(
        self,
        primera,
        segunda,
        orden,
    ):
        from unittest.mock import patch

        pids = Queue()

        datos_webpay = {
            "response_code": 0,
            "status": "AUTHORIZED",
            "buy_order": orden.buy_order,
            "session_id": orden.session_id,
            "amount": 1190,
        }

        with self.settings(
            FRONTEND_URL="http://localhost:5173"
        ):
            with patch("app.views.WebpayOptions"):
                with patch(
                    "app.views.Transaction"
                ) as proveedor:

                    proveedor.return_value.commit.return_value = (
                        datos_webpay
                    )

                    with ThreadPoolExecutor(
                        max_workers=1
                    ) as executor:

                        with transaction.atomic():

                            Usuario.objects.select_for_update().get(
                                pk=self.perfil.pk
                            )

                            with connection.cursor() as cursor:
                                cursor.execute(
                                    "SELECT pg_backend_pid()"
                                )

                                pid_principal = (
                                    cursor.fetchone()[0]
                                )

                            futuro = executor.submit(
                                self._trabajador,
                                segunda,
                                pids,
                            )

                            pid_secundario = pids.get(
                                timeout=10
                            )

                            self.assertNotEqual(
                                pid_principal,
                                pid_secundario,
                            )

                            self._esperar_bloqueos(
                                [pid_secundario],
                                pid_principal,
                            )

                            self.assertFalse(
                                futuro.done()
                            )

                            # Ejecutar la primera operacion
                            # mientras conservamos el bloqueo.
                            resultado_primero = primera()

                            self.assertFalse(
                                futuro.done()
                            )

                        # La primera transaccion ya confirmo
                        # sus cambios y libero el bloqueo.
                        resultado_segundo = futuro.result(
                            timeout=35
                        )

                    proveedor.return_value.commit.assert_called_once()

        return (
            resultado_primero,
            resultado_segundo,
        )

    def test_concurrencia_gratuita_antes_de_webpay(self):
        from app.models import HistorialVenta, Venta

        orden, venta = self._crear_pedido_cruzado()

        gratuita, webpay = (
            self._ejecutar_cruce_controlado(
                self._reclamar_gratis_cruzado,
                self._confirmar_webpay_cruzado,
                orden,
            )
        )

        self.assertEqual(gratuita, 200)
        self.assertEqual(webpay[0], 302)
        self.assertIn("pago=revision", webpay[1])

        orden.refresh_from_db()

        self.assertEqual(
            orden.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )

        self.assertIsNone(orden.fulfilled_at)

        self.assertEqual(
            HistorialCompra.objects.count(),
            1,
        )

        compra = HistorialCompra.objects.get(
            usuario=self.perfil,
            track=self.track,
        )

        self.assertEqual(
            compra.origen_adquisicion,
            HistorialCompra.ORIGEN_GRATUITO,
        )

        self.assertEqual(
            HistorialVenta.objects.count(),
            0,
        )

        self.assertEqual(
            Licencia.objects.count(),
            0,
        )

        self.assertTrue(
            Venta.objects.filter(
                pk=venta.pk,
                completada=False,
            ).exists()
        )

    def test_concurrencia_webpay_antes_de_gratuita(self):
        from app.models import HistorialVenta, Venta

        orden, venta = self._crear_pedido_cruzado()

        webpay, gratuita = (
            self._ejecutar_cruce_controlado(
                self._confirmar_webpay_cruzado,
                self._reclamar_gratis_cruzado,
                orden,
            )
        )

        self.assertEqual(webpay[0], 302)
        self.assertIn("pago=exito", webpay[1])
        self.assertEqual(gratuita, 200)

        orden.refresh_from_db()

        self.assertEqual(
            orden.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )

        self.assertIsNotNone(orden.fulfilled_at)

        self.assertEqual(
            HistorialCompra.objects.count(),
            1,
        )

        compra = HistorialCompra.objects.get(
            usuario=self.perfil,
            track=self.track,
        )

        self.assertEqual(
            compra.origen_adquisicion,
            HistorialCompra.ORIGEN_WEBPAY,
        )

        self.assertEqual(
            HistorialVenta.objects.filter(
                comprador=self.comprador,
                track=self.track,
            ).count(),
            1,
        )

        self.assertEqual(
            HistorialVenta.objects.count(),
            1,
        )

        self.assertEqual(
            Licencia.objects.count(),
            1,
        )

        licencia = Licencia.objects.get(
            compra=compra
        )

        self.assertEqual(
            licencia.transaccion_id,
            orden.pk,
        )

        self.assertTrue(
            verify_license(licencia)
        )

        self.assertFalse(
            Venta.objects.filter(
                pk=venta.pk
            ).exists()
        )

    def _comprobar_concurrencia_activacion_cierre(
        self,
        cierre_primero,
    ):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from app.account_activation import activate_account_from_token
        from app.views import _seudonimizar_identidad_cuenta

        compra_id, orden_id = self._crear_compra_comercial()

        compra = HistorialCompra.objects.get(pk=compra_id)
        orden = WebpayTransaction.objects.get(pk=orden_id)

        licencia, creada = issue_license_for_purchase(
            compra,
            orden,
        )

        self.assertTrue(creada)

        licencia_id = licencia.pk
        codigo_original = licencia.license_code
        firma_original = licencia.verification_hash

        usuario_id = self.comprador.pk
        perfil_id = self.perfil.pk

        # Simular una cuenta pendiente de activacion.
        User.objects.filter(
            pk=usuario_id
        ).update(is_active=False)

        cuenta = User.objects.get(pk=usuario_id)

        self.assertTrue(
            cuenta.has_usable_password()
        )

        uidb64 = urlsafe_base64_encode(
            force_bytes(usuario_id)
        )

        token = default_token_generator.make_token(
            cuenta
        )

        self.assertTrue(
            default_token_generator.check_token(
                cuenta,
                token,
            )
        )

        def activar():
            return activate_account_from_token(
                uidb64,
                token,
            )

        def cerrar():
            perfil = Usuario.objects.get(
                pk=perfil_id
            )

            cuenta_cerrada, perfil_cerrado = (
                _seudonimizar_identidad_cuenta(
                    perfil
                )
            )

            return (
                cuenta_cerrada.pk,
                perfil_cerrado.pk,
            )

        if cierre_primero:
            primera = cerrar
            segunda = activar
        else:
            primera = activar
            segunda = cerrar

        pids = Queue()

        with ThreadPoolExecutor(max_workers=1) as executor:

            with transaction.atomic():

                with connection.cursor() as cursor:

                    cursor.execute(
                        "SET LOCAL lock_timeout = '10s'"
                    )

                    cursor.execute(
                        "SET LOCAL statement_timeout = '20s'"
                    )

                User.objects.select_for_update().get(
                    pk=usuario_id
                )

                with connection.cursor() as cursor:

                    cursor.execute(
                        "SELECT pg_backend_pid()"
                    )

                    pid_principal = cursor.fetchone()[0]

                futuro = executor.submit(
                    self._trabajador,
                    segunda,
                    pids,
                )

                pid_secundario = pids.get(timeout=10)

                self.assertNotEqual(
                    pid_principal,
                    pid_secundario,
                )

                # Comprobar un bloqueo real en PostgreSQL.
                self._esperar_bloqueos(
                    [pid_secundario],
                    pid_principal,
                )

                self.assertFalse(futuro.done())

                resultado_primero = primera()

                estado_intermedio = User.objects.get(
                    pk=usuario_id
                )

                self.assertEqual(
                    estado_intermedio.is_active,
                    not cierre_primero,
                )

                self.assertFalse(futuro.done())

            # La primera operacion libera el bloqueo.
            resultado_segundo = futuro.result(
                timeout=35
            )

        if cierre_primero:

            self.assertEqual(
                resultado_primero,
                (usuario_id, perfil_id),
            )

            self.assertIs(
                resultado_segundo,
                False,
            )

        else:

            self.assertIs(
                resultado_primero,
                True,
            )

            self.assertEqual(
                resultado_segundo,
                (usuario_id, perfil_id),
            )

        # Validar el estado definitivo de la identidad.
        cuenta = User.objects.get(pk=usuario_id)

        self.assertFalse(cuenta.is_active)

        self.assertFalse(
            cuenta.has_usable_password()
        )

        self.assertEqual(cuenta.email, "")

        self.assertTrue(
            cuenta.username.startswith("closed_")
        )

        self.assertFalse(
            activate_account_from_token(
                uidb64,
                token,
            )
        )

        # Incluso un token nuevo debe ser rechazado.
        token_nuevo = (
            default_token_generator.make_token(
                cuenta
            )
        )

        self.assertTrue(
            default_token_generator.check_token(
                cuenta,
                token_nuevo,
            )
        )

        self.assertFalse(
            activate_account_from_token(
                uidb64,
                token_nuevo,
            )
        )

        cuenta.refresh_from_db()

        self.assertFalse(cuenta.is_active)

        # Comprobar la conservacion comercial.
        compra.refresh_from_db()
        orden.refresh_from_db()

        licencia = Licencia.objects.get(
            pk=licencia_id
        )

        self.assertEqual(
            compra.usuario.user_id,
            usuario_id,
        )

        self.assertEqual(
            orden.user_id,
            usuario_id,
        )

        self.assertEqual(
            licencia.license_code,
            codigo_original,
        )

        self.assertEqual(
            licencia.verification_hash,
            firma_original,
        )

        self.assertEqual(
            Licencia.objects.count(),
            1,
        )

        self.assertTrue(
            verify_license(licencia)
        )

    def test_concurrencia_cierre_antes_activacion(self):
        self._comprobar_concurrencia_activacion_cierre(
            cierre_primero=True,
        )

    def test_concurrencia_activacion_antes_cierre(self):
        self._comprobar_concurrencia_activacion_cierre(
            cierre_primero=False,
        )
