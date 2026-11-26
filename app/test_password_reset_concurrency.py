"""Pruebas de concurrencia entre recuperacion y cierre D10."""

import time

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from queue import Queue

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator

from django.db import (
    connection,
    connections,
    transaction,
)

from django.test import (
    Client,
    TransactionTestCase,
    override_settings,
)

from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from app.models import (
    Usuario,
    Track,
    Genero_Musical,
    HistorialCompra,
    WebpayTransaction,
    Licencia,
)

from app.license_service import (
    issue_license_for_purchase,
    verify_license,
)

from app.views import _seudonimizar_identidad_cuenta


@override_settings(
    LICENSE_SIGNING_KEY="test-reset-concurrency-d10-" + "a" * 48,
    LICENSE_SIGNING_KEY_FALLBACKS=(),
)
class PasswordResetConcurrencyTests(TransactionTestCase):

    nueva_password = "Nueva-Clave-Concurrencia-D10!2026"

    def setUp(self):

        if connection.vendor != "postgresql":
            self.skipTest("Requiere PostgreSQL.")

        self.comprador = User.objects.create_user(
            username="d10_reset_concurrente",
            email="reset-d10@example.invalid",
            password="Solo-Pruebas-Concurrencia-D10!",
        )

        self.perfil = Usuario.objects.create(
            user=self.comprador,
            tipo_usu=Usuario.ARTISTA,
        )

        productor = User.objects.create_user(
            username="d10_reset_productor",
            password="Solo-Pruebas-Productor-D10!",
        )

        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero = Genero_Musical.objects.create(
            descripcion="Pop",
        )

        track = Track.objects.create(
            nombre_track="Instrumental concurrencia D10",
            precio=1000,
            track="canciones/reset-d10-test.wav",
            genero=genero,
            usuario=perfil_productor,
            media_status="ready",
        )

        self.compra = HistorialCompra.objects.create(
            usuario=self.perfil,
            track=track,
            origen_adquisicion=HistorialCompra.ORIGEN_WEBPAY,
        )

        self.orden = WebpayTransaction.objects.create(
            user=self.comprador,
            buy_order="orden-reset-concurrente-d10",
            session_id="sesion-reset-d10",
            amount=Decimal("1190.00"),
            status=WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at=timezone.now(),
            cart_snapshot=[{
                "venta_id": 1001,
                "track_id": track.pk,
                "precio": 1000,
                "iva": 190,
            }],
        )

        self.licencia, creada = issue_license_for_purchase(
            self.compra,
            self.orden,
        )

        self.assertTrue(creada)
        self.assertTrue(verify_license(self.licencia))

        self.codigo_original = self.licencia.license_code
        self.firma_original = self.licencia.verification_hash

        self.uidb64 = urlsafe_base64_encode(
            force_bytes(self.comprador.pk)
        )

        self.token = default_token_generator.make_token(
            self.comprador
        )

    def _preparar_recuperacion(self, modalidad):

        cliente = Client()

        datos = {
            "new_password1": self.nueva_password,
            "new_password2": self.nueva_password,
        }

        if modalidad == "api":

            url = reverse("api_password_reset_confirm")

            datos.update({
                "uidb64": self.uidb64,
                "token": self.token,
            })

            def recuperar():
                respuesta = cliente.post(
                    url,
                    data=datos,
                    content_type="application/json",
                )

                return respuesta.status_code, None

            return recuperar

        url = reverse(
            modalidad,
            kwargs={
                "uidb64": self.uidb64,
                "token": self.token,
            },
        )

        respuesta = cliente.get(url)

        self.assertEqual(
            respuesta.status_code, 302
        )

        confirmacion = respuesta["Location"]

        respuesta = cliente.get(confirmacion)

        self.assertEqual(
            respuesta.status_code, 200
        )

        self.assertTrue(
            respuesta.context["validlink"]
        )

        def recuperar():

            respuesta = cliente.post(
                confirmacion,
                datos,
            )

            valido = None

            if respuesta.status_code == 200:
                valido = respuesta.context["validlink"]

            return respuesta.status_code, valido

        return recuperar

    def _cerrar(self):

        perfil = Usuario.objects.get(
            pk=self.perfil.pk
        )

        _seudonimizar_identidad_cuenta(perfil)

    def _trabajador(self, operacion, cola):

        conexion = connections["default"]

        try:

            conexion.ensure_connection()

            with conexion.cursor() as cursor:

                cursor.execute(
                    "SET lock_timeout = '20s'"
                )

                cursor.execute(
                    "SET statement_timeout = '30s'"
                )

                cursor.execute(
                    "SELECT pg_backend_pid()"
                )

                pid = cursor.fetchone()[0]

            cola.put(pid)

            return operacion()

        finally:

            conexion.close()

    def _esperar_bloqueo(
        self,
        pid_secundario,
        pid_principal,
        futuro,
    ):

        limite = time.monotonic() + 10

        while time.monotonic() < limite:

            if futuro.done():
                futuro.result()

                self.fail(
                    "La operacion termino sin esperar el bloqueo."
                )

            with connection.cursor() as cursor:

                cursor.execute(
                    "SELECT pg_blocking_pids(%s)",
                    [pid_secundario],
                )

                bloqueadores = cursor.fetchone()[0]

            if pid_principal in bloqueadores:
                return

            time.sleep(0.05)

        self.fail(
            "No se comprobo el bloqueo real en PostgreSQL."
        )

    def _comprobar_resultado_final(self):

        cuenta = User.objects.get(
            pk=self.comprador.pk
        )

        perfil = Usuario.objects.get(
            pk=self.perfil.pk
        )

        self.assertFalse(cuenta.is_active)

        self.assertFalse(
            cuenta.has_usable_password()
        )

        self.assertIsNotNone(
            perfil.cuenta_cerrada_en
        )

        self.assertFalse(
            cuenta.check_password(
                self.nueva_password
            )
        )

        self.assertFalse(
            default_token_generator.check_token(
                cuenta,
                self.token,
            )
        )

        self.compra.refresh_from_db()
        self.orden.refresh_from_db()
        self.licencia.refresh_from_db()

        self.assertEqual(
            self.compra.usuario_id,
            perfil.pk,
        )

        self.assertEqual(
            self.orden.user_id,
            cuenta.pk,
        )

        self.assertEqual(
            self.licencia.compra_id,
            self.compra.pk,
        )

        self.assertEqual(
            self.licencia.transaccion_id,
            self.orden.pk,
        )

        self.assertEqual(
            self.licencia.license_code,
            self.codigo_original,
        )

        self.assertEqual(
            self.licencia.verification_hash,
            self.firma_original,
        )

        self.assertEqual(
            Licencia.objects.filter(
                compra_id=self.compra.pk
            ).count(),
            1,
        )

        self.assertTrue(
            verify_license(self.licencia)
        )

    def _comprobar_concurrencia(
        self,
        modalidad,
        cierre_primero,
    ):

        recuperar = self._preparar_recuperacion(
            modalidad
        )

        cola = Queue()

        with ThreadPoolExecutor(
            max_workers=1
        ) as executor:

            with transaction.atomic():

                User.objects.select_for_update().get(
                    pk=self.comprador.pk
                )

                with connection.cursor() as cursor:

                    cursor.execute(
                        "SELECT pg_backend_pid()"
                    )

                    pid_principal = cursor.fetchone()[0]

                operacion_secundaria = (
                    recuperar
                    if cierre_primero
                    else self._cerrar
                )

                futuro = executor.submit(
                    self._trabajador,
                    operacion_secundaria,
                    cola,
                )

                pid_secundario = cola.get(timeout=10)

                self.assertNotEqual(
                    pid_principal,
                    pid_secundario,
                )

                self._esperar_bloqueo(
                    pid_secundario,
                    pid_principal,
                    futuro,
                )

                if cierre_primero:

                    self._cerrar()

                    cuenta = User.objects.get(
                        pk=self.comprador.pk
                    )

                    self.assertFalse(cuenta.is_active)

                    self.assertFalse(
                        cuenta.has_usable_password()
                    )

                else:

                    resultado = recuperar()

                    esperado = (
                        (200, None)
                        if modalidad == "api"
                        else (302, None)
                    )

                    self.assertEqual(
                        resultado,
                        esperado,
                    )

                    cuenta = User.objects.get(
                        pk=self.comprador.pk
                    )

                    self.assertTrue(
                        cuenta.check_password(
                            self.nueva_password
                        )
                    )

            # El bloqueo principal ya fue liberado.
            resultado_secundario = futuro.result(
                timeout=35
            )

            if cierre_primero:

                esperado = (
                    (400, None)
                    if modalidad == "api"
                    else (200, False)
                )

                self.assertEqual(
                    resultado_secundario,
                    esperado,
                )

        self._comprobar_resultado_final()

    def test_api_cierre_antes_recuperacion(self):

        self._comprobar_concurrencia(
            "api", True
        )

    def test_api_recuperacion_antes_cierre(self):

        self._comprobar_concurrencia(
            "api", False
        )

    def test_django_cierre_antes_recuperacion(self):

        self._comprobar_concurrencia(
            "beatcloud_password_reset_confirm",
            True,
        )

    def test_django_recuperacion_antes_cierre(self):

        self._comprobar_concurrencia(
            "beatcloud_password_reset_confirm",
            False,
        )

    def test_accounts_cierre_antes_recuperacion(self):

        self._comprobar_concurrencia(
            "password_reset_confirm",
            True,
        )

    def test_accounts_recuperacion_antes_cierre(self):

        self._comprobar_concurrencia(
            "password_reset_confirm",
            False,
        )
