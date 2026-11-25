import threading
import time
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase

from .models import Genero_Musical, Track, Usuario, Venta, WebpayTransaction
from .webpay_checkout_guard import (
    PaymentStartBlocked,
    create_pending_webpay_order,
)


class TrackRetirementConcurrencyTests(TransactionTestCase):

    def setUp(self):
        User = get_user_model()

        productor_user = User.objects.create_user(
            username="productor_race_test",
            password="test-password",
        )

        self.comprador = User.objects.create_user(
            username="comprador_race_test",
            password="test-password",
        )

        productor = Usuario.objects.create(
            user=productor_user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        comprador = Usuario.objects.create(
            user=self.comprador,
            tipo_usu=Usuario.ARTISTA,
        )

        genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        self.track = Track.objects.create(
            nombre_track="Track concurrencia",
            precio=1000,
            usuario=productor,
            genero=genero,
            media_status="ready",
            track="canciones/concurrencia_test.mp3",
            preview="previews/concurrencia_test.mp3",
        )

        venta = Venta.objects.create(
            detalle="Compra concurrencia",
            fecha=date.today(),
            precio=1000,
            iva=190,
            precio_total=1190,
            usuario_id=comprador,
            track=self.track,
        )

        self.snapshot = [{
            "venta_id": venta.pk,
            "track_id": self.track.pk,
            "precio": 1000,
            "iva": 190,
        }]

    def test_retirada_bloquea_checkout_concurrente(self):
        self.assertEqual(connection.vendor, "postgresql")

        iniciado = threading.Event()
        terminado = threading.Event()
        resultado = {}

        def intentar_checkout():
            close_old_connections()

            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    resultado["pid"] = cursor.fetchone()[0]

                iniciado.set()

                with patch(
                    "app.webpay_reconciliation.reconcile_stale_pending_for_user"
                ):
                    create_pending_webpay_order(
                        user=self.comprador,
                        amount=1190,
                        cart_snapshot=self.snapshot,
                    )

                resultado["estado"] = "orden_creada"

            except PaymentStartBlocked as error:
                resultado["estado"] = "orden_rechazada"
                resultado["mensaje"] = str(error)

            except Exception as error:
                resultado["estado"] = "error"
                resultado["error"] = repr(error)

            finally:
                connection.close()
                terminado.set()

        hilo = threading.Thread(
            target=intentar_checkout,
            daemon=True,
        )

        bloqueo_confirmado = False

        # Mantener bloqueado el track mientras se retira.
        with transaction.atomic():
            track = Track.objects.select_for_update().get(
                pk=self.track.pk
            )

            track.is_retired = True
            track.save(update_fields=["is_retired"])

            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pid_productor = cursor.fetchone()[0]

            hilo.start()

            if iniciado.wait(timeout=5):
                # Verificar que PostgreSQL realmente bloquea
                # el checkout en otra conexion.
                for _ in range(100):
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT pg_blocking_pids(%s)",
                            [resultado["pid"]],
                        )
                        bloqueadores = cursor.fetchone()[0]

                    if pid_productor in bloqueadores:
                        bloqueo_confirmado = True
                        break

                    if terminado.is_set():
                        break

                    time.sleep(0.05)

        # Tras confirmar la retirada, Webpay debe rechazar
        # el intento de crear una nueva orden.
        if hilo.ident is not None:
            hilo.join(timeout=10)

        self.assertFalse(hilo.is_alive())
        self.assertTrue(
            bloqueo_confirmado,
            "No se observo el bloqueo concurrente de PostgreSQL.",
        )
        self.assertEqual(
            resultado.get("estado"),
            "orden_rechazada",
            resultado,
        )

        self.track.refresh_from_db()
        self.assertTrue(self.track.is_retired)

        self.assertFalse(
            WebpayTransaction.objects.filter(
                user=self.comprador,
                suscripcion__isnull=True,
            ).exists()
        )


    def test_checkout_primero_y_retirada_despues(self):
        from django.test import RequestFactory
        from .api_shim import track_delete_api

        checkout_en_creacion = threading.Event()
        liberar_checkout = threading.Event()
        retiro_iniciado = threading.Event()
        resultados = {}

        productor = self.track.usuario.user
        manager = WebpayTransaction.objects
        crear_original = manager.create

        def crear_y_pausar(**kwargs):
            orden = crear_original(**kwargs)
            resultados["orden_id"] = orden.pk

            checkout_en_creacion.set()

            if not liberar_checkout.wait(timeout=15):
                raise RuntimeError("Timeout esperando liberar checkout")

            return orden

        def iniciar_checkout():
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    resultados["pid_checkout"] = cursor.fetchone()[0]

                with patch(
                    "app.webpay_reconciliation.reconcile_stale_pending_for_user"
                ):
                    with patch.object(
                        manager, "create", side_effect=crear_y_pausar
                    ):
                        orden = create_pending_webpay_order(
                            user=self.comprador,
                            amount=1190,
                            cart_snapshot=self.snapshot,
                        )

                resultados["checkout"] = "creado"
                resultados["orden_final"] = orden.pk

            except Exception as error:
                resultados["checkout"] = "error"
                resultados["error_checkout"] = repr(error)
            finally:
                connection.close()

        def retirar_track():
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    resultados["pid_retiro"] = cursor.fetchone()[0]

                retiro_iniciado.set()

                request = RequestFactory().post(
                    f"/api/tracks/{self.track.pk}/delete/"
                )
                request.user = productor

                response = track_delete_api(
                    request, self.track.pk
                )
                resultados["retiro_status"] = response.status_code

            except Exception as error:
                resultados["error_retiro"] = repr(error)
            finally:
                connection.close()

        hilo_checkout = threading.Thread(
            target=iniciar_checkout, daemon=True
        )
        hilo_retiro = threading.Thread(
            target=retirar_track, daemon=True
        )

        bloqueo_confirmado = False

        try:
            hilo_checkout.start()

            self.assertTrue(
                checkout_en_creacion.wait(timeout=10),
                resultados,
            )

            hilo_retiro.start()

            self.assertTrue(
                retiro_iniciado.wait(timeout=5),
                resultados,
            )

            # La retirada debe esperar el bloqueo de Webpay.
            for _ in range(100):
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT pg_blocking_pids(%s)",
                        [resultados["pid_retiro"]],
                    )
                    bloqueadores = cursor.fetchone()[0]

                if resultados["pid_checkout"] in bloqueadores:
                    bloqueo_confirmado = True
                    break

                if "retiro_status" in resultados or "error_retiro" in resultados:
                    break

                time.sleep(0.05)

        finally:
            liberar_checkout.set()
            if hilo_checkout.ident is not None:
                hilo_checkout.join(timeout=10)
            if hilo_retiro.ident is not None:
                hilo_retiro.join(timeout=10)

        self.assertFalse(hilo_checkout.is_alive())
        self.assertFalse(hilo_retiro.is_alive())

        self.assertTrue(
            bloqueo_confirmado,
            f"No se observo el bloqueo esperado: {resultados}",
        )

        self.assertEqual(
            resultados.get("checkout"), "creado", resultados
        )
        self.assertEqual(
            resultados.get("retiro_status"), 200, resultados
        )

        self.assertEqual(
            WebpayTransaction.objects.filter(
                pk=resultados["orden_id"],
                user=self.comprador,
            ).count(),
            1,
        )

        self.track.refresh_from_db()
        self.assertTrue(self.track.is_retired)
