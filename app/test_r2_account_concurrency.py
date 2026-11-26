"""Concurrencia real PostgreSQL entre cargas R2 y cierre."""

import time

from concurrent.futures import ThreadPoolExecutor
from queue import Queue

from django.contrib.auth.models import User
from django.core import signing
from django.db import (
    connection,
    connections,
    transaction,
    close_old_connections,
)
from django.test import TransactionTestCase

from app.models import Usuario, R2UploadClaim

from app.r2_presign import ALLOWED, TOKEN_SALT

from app.r2_claim_service import (
    reserve_r2_upload,
    try_begin_r2_processing,
    R2ClaimConflict,
)

from app.r2_claim_lifecycle import (
    mark_r2_claim_failed,
)

from app.views import (
    _seudonimizar_identidad_cuenta,
    EliminacionCuentaBloqueada,
)


class R2AccountConcurrencyTests(TransactionTestCase):

    def setUp(self):

        if connection.vendor != "postgresql":
            self.skipTest("Requiere PostgreSQL.")

        self.user = User.objects.create_user(
            username="d10_r2_concurrencia",
            password="Solo-Pruebas-Concurrencia-R2!",
        )

        self.perfil = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.user_id = self.user.pk
        self.perfil_id = self.perfil.pk

        self.token = signing.dumps(
            {
                "owner": self.user_id,
                "key": (
                    f"pending/{self.user_id}/track/"
                    + "a" * 32
                    + ".wav"
                ),
                "size": 16044,
                "kind": "track",
                "mime": sorted(
                    ALLOWED["track"][".wav"]
                )[0],
            },
            salt=TOKEN_SALT,
        )

    def reservar(self):

        return reserve_r2_upload(
            user_id=self.user_id,
            upload_token=self.token,
        )

    def iniciar(self, claim_id):

        return try_begin_r2_processing(
            claim_id=claim_id,
            user_id=self.user_id,
        )

    def cerrar(self):

        perfil = Usuario.objects.get(
            pk=self.perfil_id
        )

        try:
            _seudonimizar_identidad_cuenta(
                perfil
            )

        except EliminacionCuentaBloqueada as exc:

            return ("bloqueado", str(exc))

        return ("cerrado", "")

    def reservar_controlado(self):

        try:
            resultado = self.reservar()

        except R2ClaimConflict:

            return ("rechazado", None)

        return ("reservado", resultado.claim_id)

    def trabajador(self, operacion, cola):

        close_old_connections()

        conexion = connections["default"]

        try:
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

    def comprobar_bloqueo(
        self,
        pid_principal,
        pid_secundario,
    ):

        self.assertNotEqual(
            pid_principal,
            pid_secundario,
        )

        limite = time.monotonic() + 8

        while time.monotonic() < limite:

            with connection.cursor() as cursor:

                cursor.execute(
                    "SELECT pg_blocking_pids(%s)",
                    [pid_secundario],
                )

                bloqueadores = cursor.fetchone()[0]

            if pid_principal in bloqueadores:

                print(
                    "\nOK: Bloqueo PostgreSQL comprobado "
                    f"({pid_principal} -> {pid_secundario})"
                )

                return

            time.sleep(0.05)

        self.fail(
            "No se comprobo el bloqueo concurrente."
        )

    def ejecutar_cruce(
        self,
        operacion_primera,
        operacion_segunda,
    ):

        cola = Queue()

        with ThreadPoolExecutor(
            max_workers=1
        ) as executor:

            with transaction.atomic():

                User.objects.select_for_update().get(
                    pk=self.user_id
                )

                with connection.cursor() as cursor:

                    cursor.execute(
                        "SELECT pg_backend_pid()"
                    )

                    pid_principal = cursor.fetchone()[0]

                futuro = executor.submit(
                    self.trabajador,
                    operacion_segunda,
                    cola,
                )

                pid_secundario = cola.get(
                    timeout=10
                )

                self.comprobar_bloqueo(
                    pid_principal,
                    pid_secundario,
                )

                self.assertFalse(
                    futuro.done()
                )

                primero = operacion_primera()

                self.assertFalse(
                    futuro.done()
                )

            # La transaccion principal ya hizo COMMIT.
            segundo = futuro.result(
                timeout=35
            )

        return primero, segundo

    def comprobar_cuenta_cerrada(self):

        self.user.refresh_from_db()
        self.perfil.refresh_from_db()

        self.assertFalse(
            self.user.is_active
        )

        self.assertFalse(
            self.user.has_usable_password()
        )

        self.assertIsNotNone(
            self.perfil.cuenta_cerrada_en
        )

    def test_concurrencia_cierre_antes_procesamiento(self):

        reserva = self.reservar()

        primero, segundo = self.ejecutar_cruce(
            self.cerrar,
            lambda: self.iniciar(
                reserva.claim_id
            ),
        )

        self.assertEqual(
            primero[0],
            "cerrado",
        )

        self.assertFalse(segundo)

        self.comprobar_cuenta_cerrada()

        registro = R2UploadClaim.objects.get(
            pk=reserva.claim_id
        )

        self.assertEqual(
            registro.status,
            "reserved",
        )

        self.assertEqual(
            registro.private_key,
            "",
        )

        self.assertIsNone(
            registro.track_id
        )

    def test_concurrencia_procesamiento_antes_cierre(self):

        reserva = self.reservar()

        primero, segundo = self.ejecutar_cruce(
            lambda: self.iniciar(
                reserva.claim_id
            ),
            self.cerrar,
        )

        self.assertTrue(primero)

        self.assertEqual(
            segundo[0],
            "bloqueado",
        )

        self.assertIn(
            "cargas R2",
            segundo[1],
        )

        self.user.refresh_from_db()
        self.perfil.refresh_from_db()

        self.assertTrue(
            self.user.is_active
        )

        self.assertIsNone(
            self.perfil.cuenta_cerrada_en
        )

        registro = R2UploadClaim.objects.get(
            pk=reserva.claim_id
        )

        self.assertEqual(
            registro.status,
            "processing",
        )

        # Una vez conciliado el procesamiento,
        # el cierre debe poder continuar.
        self.assertTrue(
            mark_r2_claim_failed(
                claim_id=reserva.claim_id,
                user_id=self.user_id,
            )
        )

        self.assertEqual(
            self.cerrar()[0],
            "cerrado",
        )

        self.comprobar_cuenta_cerrada()

        registro.refresh_from_db()

        self.assertEqual(
            registro.status,
            "failed",
        )

    def test_concurrencia_cierre_antes_reserva(self):

        primero, segundo = self.ejecutar_cruce(
            self.cerrar,
            self.reservar_controlado,
        )

        self.assertEqual(
            primero[0],
            "cerrado",
        )

        self.assertEqual(
            segundo,
            ("rechazado", None),
        )

        self.comprobar_cuenta_cerrada()

        self.assertFalse(
            R2UploadClaim.objects.filter(
                owner_id=self.user_id
            ).exists()
        )

    def test_concurrencia_reserva_antes_cierre(self):

        primero, segundo = self.ejecutar_cruce(
            self.reservar_controlado,
            self.cerrar,
        )

        self.assertEqual(
            primero[0],
            "reservado",
        )

        self.assertEqual(
            segundo[0],
            "cerrado",
        )

        self.comprobar_cuenta_cerrada()

        registro = R2UploadClaim.objects.get(
            pk=primero[1]
        )

        self.assertEqual(
            registro.status,
            "reserved",
        )

        self.assertEqual(
            registro.owner_id,
            self.user_id,
        )

        self.assertFalse(
            self.iniciar(registro.pk)
        )

        registro.refresh_from_db()

        self.assertEqual(
            registro.status,
            "reserved",
        )

        self.assertEqual(
            R2UploadClaim.objects.filter(
                owner_id=self.user_id
            ).count(),
            1,
        )

    def preparar_finalizacion(self):

        from app.models import Track, Genero_Musical

        from app.r2_claim_lifecycle import (
            attach_r2_private_key,
        )

        reserva = self.reservar()

        self.assertTrue(
            self.iniciar(reserva.claim_id)
        )

        privada = (
            f"private/{self.user_id}/track/"
            + "b" * 32
            + ".wav"
        )

        self.assertTrue(
            attach_r2_private_key(
                claim_id=reserva.claim_id,
                user_id=self.user_id,
                private_key=privada,
            )
        )

        genero, _ = Genero_Musical.objects.get_or_create(
            descripcion="Pop"
        )

        track = Track.objects.create(
            nombre_track="Finalizacion concurrente D10",
            precio=1000,
            genero=genero,
            usuario_id=self.perfil_id,
            track="",
            preview="previews/d10-finalizacion.mp3",
            storage_backend="r2",
            r2_object_key=privada,
            r2_owner_user_id=self.user_id,
            media_status="processing",
        )

        return (
            reserva.claim_id,
            track.pk,
            privada,
        )

    def finalizar(self, claim_id, track_id):

        from app.r2_claim_finalize import (
            finalize_r2_claim,
        )

        return finalize_r2_claim(
            claim_id=claim_id,
            user_id=self.user_id,
            track_id=track_id,
        )

    def comprobar_finalizacion(
        self,
        claim_id,
        track_id,
        privada,
    ):

        from app.models import Track

        reserva = R2UploadClaim.objects.get(
            pk=claim_id
        )

        track = Track.objects.get(
            pk=track_id
        )

        self.assertEqual(
            reserva.status,
            "ready",
        )

        self.assertEqual(
            track.media_status,
            "ready",
        )

        self.assertEqual(
            reserva.track_id,
            track.pk,
        )

        self.assertEqual(
            reserva.owner_id,
            self.user_id,
        )

        self.assertEqual(
            reserva.private_key,
            privada,
        )

        self.assertEqual(
            track.r2_object_key,
            privada,
        )

        self.assertEqual(
            track.r2_owner_user_id,
            self.user_id,
        )

        self.assertEqual(
            track.usuario_id,
            self.perfil_id,
        )

        self.assertEqual(
            track.preview.name,
            "previews/d10-finalizacion.mp3",
        )

        self.assertEqual(
            track.precio,
            1000,
        )

        self.assertEqual(
            R2UploadClaim.objects.filter(
                track_id=track_id,
            ).count(),
            1,
        )

        self.assertEqual(
            Track.objects.filter(
                r2_object_key=privada,
            ).count(),
            1,
        )

    def test_concurrencia_finalizacion_antes_cierre(self):

        claim_id, track_id, privada = (
            self.preparar_finalizacion()
        )

        primero, segundo = self.ejecutar_cruce(
            lambda: self.finalizar(
                claim_id,
                track_id,
            ),
            self.cerrar,
        )

        # La finalizacion debe confirmarse antes del cierre.
        self.assertTrue(primero)

        self.assertEqual(
            segundo[0],
            "cerrado",
        )

        self.comprobar_cuenta_cerrada()

        self.comprobar_finalizacion(
            claim_id,
            track_id,
            privada,
        )

    def test_concurrencia_cierre_antes_finalizacion(self):

        claim_id, track_id, privada = (
            self.preparar_finalizacion()
        )

        primero, segundo = self.ejecutar_cruce(
            self.cerrar,
            lambda: self.finalizar(
                claim_id,
                track_id,
            ),
        )

        # El procesamiento pendiente debe bloquear el cierre.
        self.assertEqual(
            primero[0],
            "bloqueado",
        )

        self.assertIn(
            "cargas R2",
            primero[1],
        )

        # Despues de liberar el bloqueo,
        # la finalizacion debe continuar.
        self.assertTrue(segundo)

        self.user.refresh_from_db()
        self.perfil.refresh_from_db()

        self.assertTrue(
            self.user.is_active
        )

        self.assertIsNone(
            self.perfil.cuenta_cerrada_en
        )

        self.comprobar_finalizacion(
            claim_id,
            track_id,
            privada,
        )

        # Una nueva solicitud de cierre debe ser posible
        # una vez terminado el procesamiento.
        self.assertEqual(
            self.cerrar()[0],
            "cerrado",
        )

        self.comprobar_cuenta_cerrada()

        self.comprobar_finalizacion(
            claim_id,
            track_id,
            privada,
        )

    def solicitar_autorizacion_r2(self, operacion):

        import json

        from django.test import RequestFactory

        from app.r2_presign import (
            r2_presign_upload_api,
            r2_confirm_upload_api,
        )

        if operacion == "presign":

            endpoint = r2_presign_upload_api

            payload = {
                "kind": "track",
                "filename": "prueba.wav",
                "size": 16044,
                "content_type": sorted(
                    ALLOWED["track"][".wav"]
                )[0],
            }

        elif operacion == "confirm":

            endpoint = r2_confirm_upload_api

            payload = {
                "upload_token": self.token,
            }

        else:

            raise ValueError(
                "Operacion de prueba desconocida."
            )

        solicitud = RequestFactory().post(
            "/api/r2/prueba/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Simular una solicitud autenticada antes del cierre.
        solicitud.user = self.user
        solicitud._dont_enforce_csrf_checks = True

        respuesta = endpoint(solicitud)

        return (
            respuesta.status_code,
            json.loads(respuesta.content),
            respuesta.get("Cache-Control"),
        )

    def ejecutar_cruce_autorizacion(
        self,
        operacion,
        cierre_primero,
    ):

        from unittest.mock import Mock, patch

        cloud = Mock()

        cloud.generate_presigned_url.return_value = (
            "https://example.invalid/r2-prueba"
        )

        cloud.head_object.return_value = {
            "ContentLength": 16044,
            "ContentType": sorted(
                ALLOWED["track"][".wav"]
            )[0],
        }

        configuracion = {
            "R2_BUCKET_NAME": "bucket-exclusivo-pruebas",
        }

        def autorizar():

            return self.solicitar_autorizacion_r2(
                operacion
            )

        with (
            patch(
                "app.r2_presign.r2_uploads_enabled",
                return_value=True,
            ),
            patch(
                "app.r2_presign.r2_configuration",
                return_value=configuracion,
            ) as mock_configuracion,
            patch(
                "app.r2_presign.r2_client",
                return_value=cloud,
            ) as mock_cliente,
        ):

            if cierre_primero:

                cierre, respuesta = (
                    self.ejecutar_cruce(
                        self.cerrar,
                        autorizar,
                    )
                )

                self.assertEqual(
                    respuesta[0],
                    403,
                )

                self.assertNotIn(
                    "url",
                    respuesta[1],
                )

                self.assertNotIn(
                    "upload_token",
                    respuesta[1],
                )

                self.assertNotIn(
                    "verified",
                    respuesta[1],
                )

                mock_configuracion.assert_not_called()
                mock_cliente.assert_not_called()

                cloud.generate_presigned_url.assert_not_called()
                cloud.head_object.assert_not_called()

            else:

                respuesta, cierre = (
                    self.ejecutar_cruce(
                        autorizar,
                        self.cerrar,
                    )
                )

                self.assertEqual(
                    respuesta[0],
                    200,
                    respuesta[1],
                )

                self.assertEqual(
                    respuesta[2],
                    "no-store",
                )

                if operacion == "presign":

                    self.assertEqual(
                        respuesta[1]["expires_in"],
                        3600,
                    )

                    self.assertIn(
                        "upload_token",
                        respuesta[1],
                    )

                    cloud.generate_presigned_url.assert_called_once()
                    cloud.head_object.assert_not_called()

                else:

                    self.assertTrue(
                        respuesta[1]["verified"]
                    )

                    cloud.head_object.assert_called_once()
                    cloud.generate_presigned_url.assert_not_called()

                mock_configuracion.assert_called_once()
                mock_cliente.assert_called_once()

                # Una vez cerrada la cuenta,
                # ninguna nueva solicitud debe utilizar R2.
                mock_configuracion.reset_mock()
                mock_cliente.reset_mock()
                cloud.reset_mock()

                posterior = autorizar()

                self.assertEqual(
                    posterior[0],
                    403,
                )

                mock_configuracion.assert_not_called()
                mock_cliente.assert_not_called()

                cloud.generate_presigned_url.assert_not_called()
                cloud.head_object.assert_not_called()

        self.assertEqual(
            cierre[0],
            "cerrado",
        )

        self.comprobar_cuenta_cerrada()

        # Autorizar o confirmar archivos no debe crear reservas.
        self.assertFalse(
            R2UploadClaim.objects.filter(
                owner_id=self.user_id,
            ).exists()
        )

    def test_concurrencia_cierre_antes_presign(self):

        self.ejecutar_cruce_autorizacion(
            operacion="presign",
            cierre_primero=True,
        )

    def test_concurrencia_presign_antes_cierre(self):

        self.ejecutar_cruce_autorizacion(
            operacion="presign",
            cierre_primero=False,
        )

    def test_concurrencia_cierre_antes_confirm(self):

        self.ejecutar_cruce_autorizacion(
            operacion="confirm",
            cierre_primero=True,
        )

    def test_concurrencia_confirm_antes_cierre(self):

        self.ejecutar_cruce_autorizacion(
            operacion="confirm",
            cierre_primero=False,
        )

    def preparar_track_edicion(self):

        from app.models import Track, Genero_Musical

        genero, _ = Genero_Musical.objects.get_or_create(
            descripcion="Pop"
        )

        return Track.objects.create(
            nombre_track="Track concurrente D10",
            precio=1000,
            genero=genero,
            usuario_id=self.perfil_id,
            track="",
            preview="previews/d10-edicion.mp3",
            storage_backend="r2",
            r2_object_key=(
                f"private/{self.user_id}/track/"
                + "a" * 32
                + ".wav"
            ),
            r2_owner_user_id=self.user_id,
            media_status="ready",
            r2_cover_key=(
                f"private/{self.user_id}/cover/"
                + "b" * 32
                + ".png"
            ),
        )

    def editar_concurrente(self, track_id, datos):

        import json

        from django.test import RequestFactory
        from app.api_shim import track_update_api

        solicitud = RequestFactory().patch(
            f"/api/track/{track_id}/",
            data=json.dumps(datos),
            content_type="application/json",
        )

        # Simular una solicitud autenticada antes del cierre.
        solicitud.user = self.user

        respuesta = track_update_api(
            solicitud,
            track_id,
        )

        return (
            respuesta.status_code,
            json.loads(respuesta.content),
        )

    def preparar_cloud_edicion(self):

        from types import SimpleNamespace
        from contextlib import ExitStack
        from unittest.mock import Mock, patch

        cloud = Mock()

        nueva = (
            f"private/{self.user_id}/cover/"
            + "c" * 32
            + ".webp"
        )

        stack = ExitStack()
        self.addCleanup(stack.close)

        configuraciones = (
            (
                "app.r2_presign.r2_uploads_enabled",
                True,
            ),
            (
                "app.r2_presign.r2_configuration",
                {"R2_BUCKET_NAME": "bucket-pruebas"},
            ),
            (
                "app.r2_presign.r2_client",
                cloud,
            ),
            (
                "app.r2_upload_http._bucket",
                "bucket-pruebas",
            ),
            (
                "app.r2_registration_guard.validate_r2_cover_token",
                None,
            ),
        )

        for objetivo, valor in configuraciones:

            stack.enter_context(
                patch(
                    objetivo,
                    return_value=valor,
                )
            )

        preparar = stack.enter_context(
            patch(
                "app.r2_registration_prepare.prepare_r2_cover_upload",
                return_value=SimpleNamespace(
                    private_key=nueva,
                ),
            )
        )

        return cloud, nueva, preparar

    def retirar_track_simulado(self, track_id):

        from app.models import Track

        # Simular un escritor concurrente de PostgreSQL.
        # No sustituye las pruebas del endpoint de retirada.
        return Track.objects.filter(
            pk=track_id,
        ).update(is_retired=True)

    def ejecutar_cruce_track(
        self,
        track_id,
        primera,
        segunda,
        bloquear_usuario=False,
    ):

        from app.models import Track

        cola = Queue()

        with ThreadPoolExecutor(max_workers=1) as executor:

            with transaction.atomic():

                if bloquear_usuario:

                    User.objects.select_for_update().get(
                        pk=self.user_id
                    )

                Track.objects.select_for_update().get(
                    pk=track_id
                )

                with connection.cursor() as cursor:

                    cursor.execute(
                        "SELECT pg_backend_pid()"
                    )

                    pid_principal = cursor.fetchone()[0]

                futuro = executor.submit(
                    self.trabajador,
                    segunda,
                    cola,
                )

                pid_secundario = cola.get(timeout=10)

                self.comprobar_bloqueo(
                    pid_principal,
                    pid_secundario,
                )

                self.assertFalse(futuro.done())

                resultado_primero = primera()

                self.assertFalse(futuro.done())

            resultado_segundo = futuro.result(
                timeout=35
            )

        return resultado_primero, resultado_segundo

    def test_concurrencia_cierre_antes_edicion_portada(self):

        track = self.preparar_track_edicion()

        anterior = track.r2_cover_key

        cloud, nueva, preparar = (
            self.preparar_cloud_edicion()
        )

        cierre, respuesta = self.ejecutar_cruce(
            self.cerrar,
            lambda: self.editar_concurrente(
                track.pk,
                {
                    "nombre_track": "Edicion rechazada",
                    "cover_upload_token": "token-pruebas",
                },
            ),
        )

        self.assertEqual(cierre[0], "cerrado")
        self.assertEqual(respuesta[0], 403)

        self.comprobar_cuenta_cerrada()

        track.refresh_from_db()

        self.assertEqual(
            track.nombre_track,
            "Track concurrente D10",
        )

        self.assertEqual(
            track.r2_cover_key,
            anterior,
        )

        preparar.assert_not_called()
        cloud.delete_object.assert_not_called()

    def test_concurrencia_edicion_portada_antes_cierre(self):

        track = self.preparar_track_edicion()

        anterior = track.r2_cover_key

        cloud, nueva, preparar = (
            self.preparar_cloud_edicion()
        )

        respuesta, cierre = self.ejecutar_cruce(
            lambda: self.editar_concurrente(
                track.pk,
                {
                    "nombre_track": "Edicion confirmada",
                    "cover_upload_token": "token-pruebas",
                },
            ),
            self.cerrar,
        )

        self.assertEqual(
            respuesta[0],
            200,
            respuesta[1],
        )

        self.assertEqual(cierre[0], "cerrado")

        self.comprobar_cuenta_cerrada()

        track.refresh_from_db()

        self.assertEqual(
            track.nombre_track,
            "Edicion confirmada",
        )

        self.assertEqual(
            track.r2_cover_key,
            nueva,
        )

        preparar.assert_called_once()

        cloud.delete_object.assert_called_once_with(
            Bucket="bucket-pruebas",
            Key=anterior,
        )

        posterior = self.editar_concurrente(
            track.pk,
            {"nombre_track": "No permitido"},
        )

        self.assertEqual(posterior[0], 403)

    def test_concurrencia_retirada_antes_edicion(self):

        track = self.preparar_track_edicion()

        anterior = track.r2_cover_key

        cloud, nueva, preparar = (
            self.preparar_cloud_edicion()
        )

        retirada, respuesta = (
            self.ejecutar_cruce_track(
                track.pk,
                lambda: self.retirar_track_simulado(
                    track.pk
                ),
                lambda: self.editar_concurrente(
                    track.pk,
                    {
                        "nombre_track": "No permitido",
                        "cover_upload_token": "token-pruebas",
                    },
                ),
            )
        )

        self.assertEqual(retirada, 1)
        self.assertEqual(respuesta[0], 409)

        track.refresh_from_db()

        self.assertTrue(track.is_retired)

        self.assertEqual(
            track.nombre_track,
            "Track concurrente D10",
        )

        self.assertEqual(
            track.r2_cover_key,
            anterior,
        )

        preparar.assert_not_called()
        cloud.delete_object.assert_not_called()

    def test_concurrencia_edicion_antes_retirada(self):

        track = self.preparar_track_edicion()

        anterior = track.r2_cover_key

        respuesta, retirada = (
            self.ejecutar_cruce_track(
                track.pk,
                lambda: self.editar_concurrente(
                    track.pk,
                    {"nombre_track": "Edicion anterior"},
                ),
                lambda: self.retirar_track_simulado(
                    track.pk
                ),
                bloquear_usuario=True,
            )
        )

        self.assertEqual(
            respuesta[0],
            200,
            respuesta[1],
        )

        self.assertEqual(retirada, 1)

        track.refresh_from_db()

        self.assertTrue(track.is_retired)

        self.assertEqual(
            track.nombre_track,
            "Edicion anterior",
        )

        self.assertEqual(
            track.r2_cover_key,
            anterior,
        )

        posterior = self.editar_concurrente(
            track.pk,
            {"precio": 2000},
        )

        self.assertEqual(posterior[0], 409)

        track.refresh_from_db()

        self.assertEqual(track.precio, 1000)

    def test_concurrencia_ediciones_no_pierden_campos(self):

        track = self.preparar_track_edicion()

        anterior = track.r2_cover_key

        primero, segundo = self.ejecutar_cruce(
            lambda: self.editar_concurrente(
                track.pk,
                {"nombre_track": "Nuevo nombre D10"},
            ),
            lambda: self.editar_concurrente(
                track.pk,
                {"precio": 2500},
            ),
        )

        self.assertEqual(primero[0], 200)
        self.assertEqual(segundo[0], 200)

        track.refresh_from_db()

        self.assertEqual(
            track.nombre_track,
            "Nuevo nombre D10",
        )

        self.assertEqual(track.precio, 2500)

        self.assertEqual(
            track.r2_cover_key,
            anterior,
        )

        self.assertFalse(track.is_retired)

        self.assertEqual(
            track.media_status,
            "ready",
        )

        self.assertEqual(
            track.usuario_id,
            self.perfil_id,
        )

    def editar_html_concurrente(self, track_id):

        from django.test import RequestFactory
        from django.http import HttpResponse
        from unittest.mock import patch
        from app.models import Track
        from app.views import editar_track

        genero_id = Track.objects.values_list(
            "genero_id",
            flat=True,
        ).get(pk=track_id)

        datos = {
            "nombre_track": "Edicion HTML concurrente",
            "precio": "1000",
            "genero": str(genero_id),
            "resource_type": "instrumental",
            "bpm": "140",
            "scale_key": "Am",
            "mood": "Oscuro",
            "duration": "30",
            "has_stems": "false",
            "has_wav": "true",
            "has_midi": "false",
            "allow_free_download": "false",
            "has_watermark": "true",
        }

        solicitud = RequestFactory().post(
            f"/editar_track/{track_id}/",
            data=datos,
        )

        # Simular solicitud autenticada antes del cierre.
        solicitud.user = self.user

        with (
            patch("app.views.messages.success"),
            patch(
                "app.views.render",
                return_value=HttpResponse("Formulario"),
            ),
        ):

            respuesta = editar_track(
                solicitud,
                track_id,
            )

        return respuesta.status_code

    def test_concurrencia_cierre_antes_edicion_html(self):

        track = self.preparar_track_edicion()

        original = track.nombre_track
        audio = track.r2_object_key
        portada = track.r2_cover_key
        preview = track.preview.name

        cierre, respuesta = self.ejecutar_cruce(
            self.cerrar,
            lambda: self.editar_html_concurrente(
                track.pk
            ),
        )

        self.assertEqual(cierre[0], "cerrado")
        self.assertEqual(respuesta, 403)

        self.comprobar_cuenta_cerrada()

        track.refresh_from_db()

        self.assertEqual(track.nombre_track, original)
        self.assertEqual(track.r2_object_key, audio)
        self.assertEqual(track.r2_cover_key, portada)
        self.assertEqual(track.preview.name, preview)

    def test_concurrencia_edicion_html_antes_cierre(self):

        track = self.preparar_track_edicion()

        audio = track.r2_object_key
        portada = track.r2_cover_key
        preview = track.preview.name

        respuesta, cierre = self.ejecutar_cruce(
            lambda: self.editar_html_concurrente(
                track.pk
            ),
            self.cerrar,
        )

        self.assertEqual(respuesta, 302)
        self.assertEqual(cierre[0], "cerrado")

        self.comprobar_cuenta_cerrada()

        track.refresh_from_db()

        self.assertEqual(
            track.nombre_track,
            "Edicion HTML concurrente",
        )

        self.assertEqual(track.r2_object_key, audio)
        self.assertEqual(track.r2_cover_key, portada)
        self.assertEqual(track.preview.name, preview)
        self.assertEqual(track.usuario_id, self.perfil_id)

        posterior = self.editar_html_concurrente(
            track.pk
        )

        self.assertEqual(posterior, 403)
