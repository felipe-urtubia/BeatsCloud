"""Pruebas aisladas del servicio D10."""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from app.license_service import (
    LicenseError,
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
    LICENSE_SIGNING_KEY="test-only-d10-key-" + "a" * 48,
    LICENSE_SIGNING_KEY_FALLBACKS=(),
)
class LicenseServiceTests(TestCase):

    def setUp(self):
        comprador = User.objects.create_user(
            username="d10_comprador",
            password="Solo-Pruebas-D10-2026",
        )

        perfil_comprador = Usuario.objects.create(
            user=comprador,
            tipo_usu=Usuario.ARTISTA,
        )

        productor = User.objects.create_user(
            username="d10_productor",
            password="Solo-Pruebas-D10-2026",
        )

        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero = Genero_Musical.objects.create(
            descripcion="Pop"
        )

        track = Track.objects.create(
            nombre_track="Instrumental de prueba D10",
            precio=1000,
            track="canciones/d10-test.wav",
            genero=genero,
            usuario=perfil_productor,
            media_status="ready",
        )

        self.compra = HistorialCompra.objects.create(
            origen_adquisicion=HistorialCompra.ORIGEN_WEBPAY,
            usuario=perfil_comprador,
            track=track,
        )

        self.orden = WebpayTransaction.objects.create(
            user=comprador,
            buy_order="orden-d10-test-001",
            session_id=comprador.username,
            amount=Decimal("1190.00"),
            status=WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at=timezone.now(),
            cart_snapshot=[
                {
                    "venta_id": 1001,
                    "track_id": track.pk,
                    "precio": 1000,
                    "iva": 190,
                }
            ],
        )

    def emitir(self):
        return issue_license_for_purchase(
            self.compra,
            self.orden,
        )

    def test_compra_valida_emite_licencia(self):
        licencia, creada = self.emitir()

        self.assertTrue(creada)
        self.assertEqual(Licencia.objects.count(), 1)
        self.assertEqual(
            licencia.buy_order,
            self.orden.buy_order,
        )
        self.assertEqual(
            licencia.compra_id,
            self.compra.pk,
        )
        self.assertEqual(len(licencia.verification_hash), 64)
        self.assertTrue(
            verify_license(
                Licencia.objects.get(pk=licencia.pk)
            )
        )

    def test_emision_repetida_no_duplica(self):
        primera, creada_1 = self.emitir()
        segunda, creada_2 = self.emitir()

        self.assertTrue(creada_1)
        self.assertFalse(creada_2)
        self.assertEqual(primera.pk, segunda.pk)
        self.assertEqual(Licencia.objects.count(), 1)

    def test_pago_cancelado_no_emite(self):
        self.orden.status = (
            WebpayTransaction.ESTADO_CANCELADO
        )
        self.orden.fulfilled_at = None
        self.orden.save()

        with self.assertRaises(LicenseError):
            self.emitir()

        self.assertEqual(Licencia.objects.count(), 0)

    def test_pago_sin_entrega_no_emite(self):
        self.orden.fulfilled_at = None
        self.orden.save(update_fields=["fulfilled_at"])

        with self.assertRaises(LicenseError):
            self.emitir()

        self.assertEqual(Licencia.objects.count(), 0)

    def test_pago_archivado_no_emite(self):
        self.orden.archived_for_review = True
        self.orden.save(
            update_fields=["archived_for_review"]
        )

        with self.assertRaises(LicenseError):
            self.emitir()

        self.assertEqual(Licencia.objects.count(), 0)

    def test_monto_incorrecto_no_emite(self):
        self.orden.amount = Decimal("1500.00")
        self.orden.save(update_fields=["amount"])

        with self.assertRaises(LicenseError):
            self.emitir()

        self.assertEqual(Licencia.objects.count(), 0)

    def test_track_ajeno_a_orden_no_emite(self):
        self.orden.cart_snapshot = [
            {
                "venta_id": 1001,
                "track_id": 99999,
                "precio": 1000,
                "iva": 190,
            }
        ]
        self.orden.save(
            update_fields=["cart_snapshot"]
        )

        with self.assertRaises(LicenseError):
            self.emitir()

        self.assertEqual(Licencia.objects.count(), 0)

    def test_hash_modificado_no_verifica(self):
        licencia, _ = self.emitir()

        licencia.verification_hash = "0" * 64

        self.assertFalse(verify_license(licencia))

    def test_buy_order_modificado_no_verifica(self):
        licencia, _ = self.emitir()

        licencia.buy_order = "orden-falsificada"

        self.assertFalse(verify_license(licencia))

    def test_comprador_incorrecto_no_emite(self):
        otro = User.objects.create_user(
            username="d10_otro_usuario",
            password="Solo-Pruebas-D10-2026",
        )

        self.orden.user = otro
        self.orden.save(update_fields=["user"])

        with self.assertRaises(LicenseError):
            self.emitir()

        self.assertEqual(Licencia.objects.count(), 0)

    def test_api_devuelve_licencia_persistente(self):
        licencia, _ = self.emitir()
        self.client.force_login(self.compra.usuario.user)

        respuesta = self.client.get(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual(
            datos["license_code"],
            licencia.license_code,
        )
        self.assertEqual(
            datos["verification_hash"],
            licencia.verification_hash,
        )
        self.assertEqual(
            datos["purchase_reference"],
            self.orden.buy_order,
        )
        self.assertTrue(datos["verified"])

    def test_api_no_inventa_licencia_pagada(self):
        self.client.force_login(self.compra.usuario.user)

        respuesta = self.client.get(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(Licencia.objects.count(), 0)

    def test_api_rechaza_hash_alterado(self):
        licencia, _ = self.emitir()
        Licencia.objects.filter(pk=licencia.pk).update(
            verification_hash="0" * 64
        )
        self.client.force_login(self.compra.usuario.user)

        respuesta = self.client.get(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(respuesta.status_code, 409)

    def test_api_requiere_autenticacion(self):
        self.emitir()

        respuesta = self.client.get(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(respuesta.status_code, 401)

    def test_api_no_expone_licencia_a_otro_comprador(self):
        self.emitir()

        otro = User.objects.create_user(
            username="d10_comprador_ajeno",
            password="Solo-Pruebas-D10-2026",
        )

        Usuario.objects.create(
            user=otro,
            tipo_usu=Usuario.ARTISTA,
        )

        self.client.force_login(otro)

        respuesta = self.client.get(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(Licencia.objects.count(), 1)

    def test_api_no_expone_licencia_al_productor(self):
        self.emitir()

        productor = self.compra.track.usuario.user

        self.client.force_login(productor)

        respuesta = self.client.get(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(Licencia.objects.count(), 1)

    def test_api_rechaza_metodo_post(self):
        self.emitir()

        self.client.force_login(self.compra.usuario.user)

        respuesta = self.client.post(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(respuesta.status_code, 405)
        self.assertEqual(Licencia.objects.count(), 1)

    def test_api_get_repetido_no_modifica_licencia(self):
        licencia, _ = self.emitir()

        self.client.force_login(self.compra.usuario.user)

        url = f"/api/track/{self.compra.track_id}/license/"

        primera = self.client.get(url)
        segunda = self.client.get(url)

        self.assertEqual(primera.status_code, 200)
        self.assertEqual(segunda.status_code, 200)

        self.assertEqual(
            primera.json()["license_code"],
            segunda.json()["license_code"],
        )

        self.assertEqual(
            primera.json()["verification_hash"],
            segunda.json()["verification_hash"],
        )

        licencia.refresh_from_db()

        self.assertEqual(
            licencia.verification_hash,
            primera.json()["verification_hash"],
        )

        self.assertEqual(Licencia.objects.count(), 1)

    def test_precio_e_iva_alterados_invalidan_firma(self):
        licencia, _ = self.emitir()

        self.orden.cart_snapshot[0]["precio"] = 1100
        self.orden.cart_snapshot[0]["iva"] = 90

        self.orden.save(update_fields=["cart_snapshot"])

        licencia.refresh_from_db()

        self.assertFalse(verify_license(licencia))

    def test_monto_y_snapshot_alterados_invalidan_firma(self):
        licencia, _ = self.emitir()

        self.orden.cart_snapshot[0]["precio"] = 2000
        self.orden.cart_snapshot[0]["iva"] = 380
        self.orden.amount = Decimal("2380.00")

        self.orden.save(
            update_fields=["cart_snapshot", "amount"]
        )

        licencia.refresh_from_db()

        self.assertFalse(verify_license(licencia))

    def test_cambio_precio_actual_no_invalida_licencia(self):
        licencia, _ = self.emitir()

        Track.objects.filter(
            pk=self.compra.track_id
        ).update(precio=2500)

        licencia.refresh_from_db()

        self.assertTrue(verify_license(licencia))

        self.client.force_login(self.compra.usuario.user)

        respuesta = self.client.get(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["amount_clp"], 1190)

    def test_api_rechaza_snapshot_economico_alterado(self):
        self.emitir()

        self.orden.cart_snapshot[0]["precio"] = 1100
        self.orden.cart_snapshot[0]["iva"] = 90

        self.orden.save(update_fields=["cart_snapshot"])

        self.client.force_login(self.compra.usuario.user)

        respuesta = self.client.get(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(Licencia.objects.count(), 1)

    def test_cambio_secret_key_no_invalida_licencia(self):
        licencia, _ = self.emitir()

        with self.settings(
            SECRET_KEY="test-only-django-rotation-" + "b" * 48,
        ):
            self.assertTrue(verify_license(licencia))

    def test_rotacion_con_clave_anterior_conserva_licencia(self):
        licencia, _ = self.emitir()

        anterior = "test-only-d10-key-" + "a" * 48
        nueva = "test-only-d10-key-" + "c" * 48

        with self.settings(
            LICENSE_SIGNING_KEY=nueva,
            LICENSE_SIGNING_KEY_FALLBACKS=(anterior,),
        ):
            self.assertTrue(verify_license(licencia))

            repetida, creada = self.emitir()

            self.assertFalse(creada)
            self.assertEqual(repetida.pk, licencia.pk)
            self.assertEqual(
                repetida.verification_hash,
                licencia.verification_hash,
            )

    def test_rotacion_sin_clave_anterior_no_verifica(self):
        licencia, _ = self.emitir()

        with self.settings(
            LICENSE_SIGNING_KEY="test-only-d10-key-" + "c" * 48,
            LICENSE_SIGNING_KEY_FALLBACKS=(),
        ):
            self.assertFalse(verify_license(licencia))

    def test_nuevas_licencias_solo_usan_clave_activa(self):
        anterior = "test-only-d10-key-" + "a" * 48
        nueva = "test-only-d10-key-" + "c" * 48

        with self.settings(
            LICENSE_SIGNING_KEY=nueva,
            LICENSE_SIGNING_KEY_FALLBACKS=(anterior,),
        ):
            licencia, creada = self.emitir()
            self.assertTrue(creada)

        with self.settings(
            LICENSE_SIGNING_KEY=anterior,
            LICENSE_SIGNING_KEY_FALLBACKS=(),
        ):
            self.assertFalse(verify_license(licencia))

        with self.settings(
            LICENSE_SIGNING_KEY=nueva,
            LICENSE_SIGNING_KEY_FALLBACKS=(),
        ):
            self.assertTrue(verify_license(licencia))

    def test_clave_ausente_impide_emision(self):
        with self.settings(LICENSE_SIGNING_KEY=""):
            with self.assertRaises(ImproperlyConfigured):
                self.emitir()

        self.assertEqual(Licencia.objects.count(), 0)

    def test_clave_django_no_puede_firmar_licencias(self):
        from django.conf import settings

        with self.settings(
            LICENSE_SIGNING_KEY=settings.SECRET_KEY,
        ):
            with self.assertRaises(ImproperlyConfigured):
                self.emitir()

        self.assertEqual(Licencia.objects.count(), 0)

    def test_adquisicion_gratuita_conserva_origen_y_comprobante(self):
        perfil = self.compra.usuario
        track_id = self.compra.track_id

        self.compra.delete()

        Track.objects.filter(pk=track_id).update(precio=0)

        self.client.force_login(perfil.user)

        url = f"/api/track/{track_id}/claim-free/"
        licencia_url = f"/api/track/{track_id}/license/"

        respuesta = self.client.post(url)

        self.assertEqual(respuesta.status_code, 200)

        compra = HistorialCompra.objects.get(
            usuario=perfil,
            track_id=track_id,
        )

        self.assertEqual(
            compra.origen_adquisicion,
            HistorialCompra.ORIGEN_GRATUITO,
        )

        primera = self.client.get(licencia_url)
        self.assertEqual(primera.status_code, 200)

        Track.objects.filter(pk=track_id).update(precio=5000)

        segunda = self.client.get(licencia_url)
        self.assertEqual(segunda.status_code, 200)

        datos = segunda.json()

        self.assertEqual(datos["amount_clp"], 0)
        self.assertFalse(datos["verified"])
        self.assertEqual(
            datos["record_type"],
            "legacy_free_receipt",
        )

        self.assertEqual(
            primera.json()["verification_hash"],
            datos["verification_hash"],
        )

        self.assertEqual(Licencia.objects.count(), 0)

    def test_adquisicion_gratuita_repetida_no_duplica(self):
        perfil = self.compra.usuario
        track_id = self.compra.track_id

        self.compra.delete()

        Track.objects.filter(pk=track_id).update(precio=0)

        self.client.force_login(perfil.user)

        url = f"/api/track/{track_id}/claim-free/"

        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(self.client.post(url).status_code, 200)

        compras = HistorialCompra.objects.filter(
            usuario=perfil,
            track_id=track_id,
        )

        self.assertEqual(compras.count(), 1)

        self.assertEqual(
            compras.get().origen_adquisicion,
            HistorialCompra.ORIGEN_GRATUITO,
        )

    def test_historial_desconocido_no_se_convierte_en_gratuito(self):

        self.compra.origen_adquisicion = (
            HistorialCompra.ORIGEN_DESCONOCIDO
        )

        self.compra.save(
            update_fields=["origen_adquisicion"]
        )

        Track.objects.filter(
            pk=self.compra.track_id
        ).update(precio=0)

        self.client.force_login(self.compra.usuario.user)

        respuesta = self.client.post(
            f"/api/track/{self.compra.track_id}/claim-free/"
        )

        self.assertEqual(respuesta.status_code, 200)

        self.compra.refresh_from_db()

        self.assertEqual(
            self.compra.origen_adquisicion,
            HistorialCompra.ORIGEN_DESCONOCIDO,
        )

        comprobante = self.client.get(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(comprobante.status_code, 404)
        self.assertEqual(HistorialCompra.objects.count(), 1)
        self.assertEqual(Licencia.objects.count(), 0)

    def test_licencia_pagada_prevalece_sobre_precio_gratuito(self):
        licencia, _ = self.emitir()

        Track.objects.filter(
            pk=self.compra.track_id
        ).update(precio=0)

        self.client.force_login(self.compra.usuario.user)

        respuesta = self.client.get(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.json()

        self.assertTrue(datos["verified"])
        self.assertEqual(datos["record_type"], "paid_license")
        self.assertEqual(datos["amount_clp"], 1190)

        self.assertEqual(
            datos["license_code"],
            licencia.license_code,
        )

    def test_venta_historica_no_genera_adquisicion_gratuita(self):
        from app.models import HistorialVenta

        perfil = self.compra.usuario
        track_id = self.compra.track_id

        self.compra.delete()

        HistorialVenta.objects.create(
            comprador=perfil.user,
            track_id=track_id,
            precio=Decimal("1000.00"),
        )

        Track.objects.filter(pk=track_id).update(precio=0)

        self.client.force_login(perfil.user)

        respuesta = self.client.post(
            f"/api/track/{track_id}/claim-free/"
        )

        self.assertEqual(respuesta.status_code, 409)

        self.assertFalse(
            HistorialCompra.objects.filter(
                usuario=perfil,
                track_id=track_id,
            ).exists()
        )

        self.assertEqual(Licencia.objects.count(), 0)

    def test_origen_gratuito_no_emite_licencia_comercial(self):
        self.compra.origen_adquisicion = (
            HistorialCompra.ORIGEN_GRATUITO
        )

        self.compra.save(
            update_fields=["origen_adquisicion"]
        )

        from app.license_service import LicenseError

        with self.assertRaises(LicenseError):
            self.emitir()

        self.assertEqual(Licencia.objects.count(), 0)

    def test_origen_desconocido_no_emite_licencia_comercial(self):
        self.compra.origen_adquisicion = (
            HistorialCompra.ORIGEN_DESCONOCIDO
        )

        self.compra.save(
            update_fields=["origen_adquisicion"]
        )

        from app.license_service import LicenseError

        with self.assertRaises(LicenseError):
            self.emitir()

        self.assertEqual(Licencia.objects.count(), 0)

    def test_origen_alterado_invalida_licencia(self):
        licencia, _ = self.emitir()

        for origen in (
            HistorialCompra.ORIGEN_GRATUITO,
            HistorialCompra.ORIGEN_DESCONOCIDO,
        ):
            with self.subTest(origen=origen):
                HistorialCompra.objects.filter(
                    pk=self.compra.pk
                ).update(origen_adquisicion=origen)

                licencia.refresh_from_db()

                self.assertFalse(
                    verify_license(licencia)
                )

        self.assertEqual(Licencia.objects.count(), 1)

    def test_api_rechaza_licencia_con_origen_alterado(self):
        self.emitir()

        self.compra.origen_adquisicion = (
            HistorialCompra.ORIGEN_GRATUITO
        )

        self.compra.save(
            update_fields=["origen_adquisicion"]
        )

        self.client.force_login(self.compra.usuario.user)

        respuesta = self.client.get(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(Licencia.objects.count(), 1)

    def _preparar_cierre_con_licencia_d10(self):
        from django.contrib.auth.hashers import make_password

        licencia, creada = self.emitir()

        self.assertTrue(creada)

        comprador = self.compra.usuario.user

        self.client.force_login(comprador)

        session = self.client.session

        session["eliminar_cuenta_codigo_hash"] = (
            make_password("123456")
        )

        session["eliminar_cuenta_usuario_id"] = (
            comprador.pk
        )

        session["eliminar_cuenta_codigo_creado"] = (
            timezone.now().timestamp()
        )

        session["eliminar_cuenta_intentos"] = 0

        session.save()

        return comprador.pk, licencia.pk

    def _comprobar_cierre_integrado_d10(
        self,
        comprador_id,
        licencia_id,
        respuesta,
    ):
        from django.contrib.auth.models import User

        self.assertEqual(
            respuesta.status_code,
            200,
        )


        self.assertTrue(
            User.objects.filter(
                pk=comprador_id
            ).exists()
        )

        self.compra.refresh_from_db()
        self.orden.refresh_from_db()

        self.assertEqual(
            self.compra.usuario.user_id,
            comprador_id,
        )

        self.assertEqual(
            self.orden.user_id,
            comprador_id,
        )

        self.assertEqual(
            self.orden.status,
            WebpayTransaction.ESTADO_AUTORIZADO,
        )

        self.assertIsNotNone(
            self.orden.fulfilled_at
        )

        self.assertEqual(
            Licencia.objects.count(),
            1,
        )

        licencia = Licencia.objects.get(
            pk=licencia_id
        )

        self.assertTrue(
            verify_license(licencia)
        )


        from app.models import Usuario

        cuenta = User.objects.get(pk=comprador_id)

        self.assertFalse(cuenta.is_active)
        self.assertFalse(cuenta.has_usable_password())
        self.assertEqual(cuenta.email, "")

        self.assertTrue(
            Usuario.objects.filter(
                user_id=comprador_id,
                cuenta_cerrada_en__isnull=False,
            ).exists()
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_cierre_api_no_destruye_licencia_d10(self):
        comprador_id, licencia_id = (
            self._preparar_cierre_con_licencia_d10()
        )

        respuesta = self.client.post(
            "/api/auth/account-deletion/confirm/",
            data={"codigo": "123456"},
            content_type="application/json",
        )

        self._comprobar_cierre_integrado_d10(
            comprador_id,
            licencia_id,
            respuesta,
        )

    def test_cierre_django_no_destruye_licencia_d10(self):
        from django.urls import reverse

        comprador_id, licencia_id = (
            self._preparar_cierre_con_licencia_d10()
        )

        respuesta = self.client.post(
            reverse("confirmar_eliminacion_cuenta"),
            {"codigo": "123456"},
        )

        self._comprobar_cierre_integrado_d10(
            comprador_id,
            licencia_id,
            respuesta,
        )

    def test_seudonimizacion_conserva_licencia_d10(self):
        from django.contrib.auth.models import Group, Permission
        from app.views import _seudonimizar_identidad_cuenta

        licencia, creada = self.emitir()

        self.assertTrue(creada)

        perfil = self.compra.usuario
        cuenta = perfil.user

        comprador_id = cuenta.pk
        perfil_id = perfil.pk
        compra_id = self.compra.pk
        orden_id = self.orden.pk

        codigo_original = licencia.license_code
        firma_original = licencia.verification_hash

        username_original = cuenta.username

        cuenta.first_name = "Nombre prueba"
        cuenta.last_name = "Apellido prueba"
        cuenta.email = "d10-cierre@example.com"
        cuenta.is_staff = True
        cuenta.is_superuser = True

        cuenta.save()

        grupo = Group.objects.create(
            name="grupo-cierre-d10"
        )

        permiso = Permission.objects.get(
            content_type__app_label="auth",
            codename="change_user",
        )

        cuenta.groups.add(grupo)
        cuenta.user_permissions.add(permiso)

        perfil.nombre_artistico = "Artista de prueba"
        perfil.descripcion = "Descripcion personal"
        perfil.spotify = "https://example.com/spotify"
        perfil.youtube = "https://example.com/youtube"
        perfil.instagram = "https://example.com/instagram"
        perfil.foto_perfil = "media/perfil/prueba-d10.png"
        perfil.foto_fondo = "media/fondo/prueba-d10.png"

        perfil.save()

        cuenta, perfil = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        self.assertEqual(cuenta.pk, comprador_id)
        self.assertEqual(perfil.pk, perfil_id)

        self.assertNotEqual(
            cuenta.username,
            username_original,
        )

        self.assertTrue(
            cuenta.username.startswith("closed_")
        )

        self.assertEqual(cuenta.email, "")
        self.assertEqual(cuenta.first_name, "")
        self.assertEqual(cuenta.last_name, "")

        self.assertFalse(cuenta.is_active)
        self.assertFalse(cuenta.is_staff)
        self.assertFalse(cuenta.is_superuser)

        self.assertFalse(
            cuenta.has_usable_password()
        )

        self.assertIsNone(cuenta.last_login)

        self.assertEqual(cuenta.groups.count(), 0)
        self.assertEqual(
            cuenta.user_permissions.count(),
            0,
        )

        self.assertEqual(
            perfil.nombre_artistico,
            "Usuario eliminado",
        )

        self.assertIsNone(perfil.descripcion)
        self.assertIsNone(perfil.spotify)
        self.assertIsNone(perfil.youtube)
        self.assertIsNone(perfil.instagram)

        self.assertFalse(bool(perfil.foto_perfil))
        self.assertFalse(bool(perfil.foto_fondo))

        self.compra.refresh_from_db()
        self.orden.refresh_from_db()
        licencia.refresh_from_db()

        self.assertEqual(self.compra.pk, compra_id)
        self.assertEqual(self.orden.pk, orden_id)

        self.assertEqual(
            self.compra.usuario.user_id,
            comprador_id,
        )

        self.assertEqual(
            self.orden.user_id,
            comprador_id,
        )

        self.assertEqual(
            licencia.license_code,
            codigo_original,
        )

        self.assertEqual(
            licencia.verification_hash,
            firma_original,
        )

        self.assertTrue(
            verify_license(licencia)
        )

        self.assertEqual(
            Licencia.objects.count(),
            1,
        )

    def test_seudonimizacion_revoca_acceso_d10(self):
        from django.contrib.auth import authenticate
        from app.views import _seudonimizar_identidad_cuenta

        self.emitir()

        perfil = self.compra.usuario
        cuenta = perfil.user

        username_original = cuenta.username
        password_prueba = "Solo-Pruebas-Cierre-D10-2026"

        cuenta.set_password(password_prueba)
        cuenta.save(update_fields=["password"])

        self.assertIsNotNone(
            authenticate(
                username=username_original,
                password=password_prueba,
            )
        )

        self.client.force_login(cuenta)

        url = (
            f"/api/track/{self.compra.track_id}/license/"
        )

        anterior = self.client.get(url)

        self.assertEqual(anterior.status_code, 200)

        cuenta_cerrada, _ = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        # La sesion anterior ya no permite consultar licencias.
        posterior = self.client.get(url)

        self.assertEqual(
            posterior.status_code,
            401,
        )

        # Tampoco se puede autenticar con el nombre anterior.
        self.assertIsNone(
            authenticate(
                username=username_original,
                password=password_prueba,
            )
        )

        # El nuevo identificador tampoco permite iniciar sesion.
        self.assertIsNone(
            authenticate(
                username=cuenta_cerrada.username,
                password=password_prueba,
            )
        )

        licencia = Licencia.objects.get(
            compra=self.compra
        )

        self.assertTrue(
            verify_license(licencia)
        )

    def _comprobar_activacion_cuenta_cerrada_d10(
        self,
        usar_api,
    ):
        from django.contrib.auth.tokens import default_token_generator
        from django.urls import reverse
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from app.views import _seudonimizar_identidad_cuenta

        licencia, creada = self.emitir()

        self.assertTrue(creada)

        perfil = self.compra.usuario
        cuenta = perfil.user

        uidb64 = urlsafe_base64_encode(
            force_bytes(cuenta.pk)
        )

        token_anterior = (
            default_token_generator.make_token(cuenta)
        )

        self.assertTrue(
            default_token_generator.check_token(
                cuenta,
                token_anterior,
            )
        )

        cuenta, _ = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        self.assertFalse(cuenta.is_active)

        self.assertFalse(
            cuenta.has_usable_password()
        )

        self.assertFalse(
            default_token_generator.check_token(
                cuenta,
                token_anterior,
            )
        )

        # Generar un token criptograficamente valido
        # exclusivamente para esta prueba.
        token_nuevo = (
            default_token_generator.make_token(cuenta)
        )

        self.assertTrue(
            default_token_generator.check_token(
                cuenta,
                token_nuevo,
            )
        )

        casos = (
            ("token_anterior", token_anterior),
            ("token_nuevo", token_nuevo),
        )

        for nombre, token in casos:

            with self.subTest(caso=nombre):

                if usar_api:

                    respuesta = self.client.post(
                        "/api/auth/activar/",
                        data={
                            "uidb64": uidb64,
                            "token": token,
                        },
                        content_type="application/json",
                    )

                else:

                    respuesta = self.client.get(
                        reverse(
                            "activar_cuenta",
                            args=[uidb64, token],
                        )
                    )

                self.assertEqual(
                    respuesta.status_code,
                    400,
                )

                cuenta.refresh_from_db()

                self.assertFalse(
                    cuenta.is_active
                )

                self.assertFalse(
                    cuenta.has_usable_password()
                )

        licencia.refresh_from_db()

        self.assertTrue(
            verify_license(licencia)
        )

    def test_activacion_api_rechaza_cuenta_cerrada_d10(self):
        self._comprobar_activacion_cuenta_cerrada_d10(
            usar_api=True,
        )

    def test_activacion_django_rechaza_cuenta_cerrada_d10(self):
        self._comprobar_activacion_cuenta_cerrada_d10(
            usar_api=False,
        )

    def test_activacion_django_legitima_es_idempotente_d10(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.urls import reverse
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        cuenta = self.compra.usuario.user

        cuenta.is_active = False

        cuenta.save(
            update_fields=["is_active"]
        )

        self.assertTrue(
            cuenta.has_usable_password()
        )

        uidb64 = urlsafe_base64_encode(
            force_bytes(cuenta.pk)
        )

        token = default_token_generator.make_token(
            cuenta
        )

        url = reverse(
            "activar_cuenta",
            args=[uidb64, token],
        )

        primera = self.client.get(url)

        self.assertEqual(
            primera.status_code,
            200,
        )

        self.assertTemplateUsed(
            primera,
            "registration/cuenta_activada.html",
        )

        cuenta.refresh_from_db()

        self.assertTrue(cuenta.is_active)

        segunda = self.client.get(url)

        self.assertEqual(
            segunda.status_code,
            200,
        )

        cuenta.refresh_from_db()

        self.assertTrue(cuenta.is_active)

    def test_estado_persistente_de_cuenta_cerrada_d10(self):
        from app.views import _seudonimizar_identidad_cuenta

        licencia, creada = self.emitir()

        self.assertTrue(creada)

        perfil = self.compra.usuario

        self.assertIsNone(
            perfil.cuenta_cerrada_en
        )

        inicio = timezone.now()

        cuenta, perfil = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        perfil.refresh_from_db()

        self.assertIsNotNone(
            perfil.cuenta_cerrada_en
        )

        self.assertGreaterEqual(
            perfil.cuenta_cerrada_en,
            inicio,
        )

        self.assertLessEqual(
            perfil.cuenta_cerrada_en,
            timezone.now(),
        )

        fecha_original = perfil.cuenta_cerrada_en

        self.assertFalse(cuenta.is_active)

        self.assertFalse(
            cuenta.has_usable_password()
        )

        # El estado de cierre debe conservar su fecha original.
        cuenta, perfil = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        perfil.refresh_from_db()

        self.assertEqual(
            perfil.cuenta_cerrada_en,
            fecha_original,
        )

        licencia.refresh_from_db()

        self.assertTrue(
            verify_license(licencia)
        )

    def test_estado_cerrado_impide_activacion_con_password_d10(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from app.account_activation import activate_account_from_token
        from app.views import _seudonimizar_identidad_cuenta

        licencia, creada = self.emitir()

        self.assertTrue(creada)

        cuenta, perfil = (
            _seudonimizar_identidad_cuenta(
                self.compra.usuario
            )
        )

        self.assertIsNotNone(
            perfil.cuenta_cerrada_en
        )

        # Simular una modificacion accidental de credenciales.
        # La cuenta permanece cerrada e inactiva.
        cuenta.set_password(
            "Solo-Pruebas-Estado-Cerrado-D10"
        )

        cuenta.save(update_fields=["password"])

        self.assertTrue(
            cuenta.has_usable_password()
        )

        self.assertFalse(cuenta.is_active)

        uidb64 = urlsafe_base64_encode(
            force_bytes(cuenta.pk)
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

        # El estado persistente debe impedir la activacion.
        self.assertFalse(
            activate_account_from_token(
                uidb64,
                token,
            )
        )

        cuenta.refresh_from_db()
        perfil.refresh_from_db()

        self.assertFalse(cuenta.is_active)

        self.assertIsNotNone(
            perfil.cuenta_cerrada_en
        )

        licencia.refresh_from_db()

        self.assertTrue(
            verify_license(licencia)
        )

    def test_perfiles_cerrados_ocultos_en_api_d10(self):
        from app.views import (
            _seudonimizar_identidad_cuenta,
            _obtener_perfil_anonimo,
        )

        perfil = self.compra.usuario

        cuenta = perfil.user

        username_original = cuenta.username

        productor = self.compra.track.usuario.user

        # Una cuenta pendiente de activacion no esta cerrada.
        productor.is_active = False
        productor.username = "closed_prefijo_legitimo_d10"

        productor.save(
            update_fields=["is_active", "username"]
        )

        cuenta, perfil = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        anonimo = _obtener_perfil_anonimo()

        respuesta = self.client.get("/api/usuarios/")

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        ids = {
            item["id"]
            for item in respuesta.json()
        }

        self.assertNotIn(cuenta.pk, ids)
        self.assertNotIn(anonimo.user_id, ids)
        self.assertIn(productor.pk, ids)

        for username in (
            username_original,
            cuenta.username,
            anonimo.user.username,
        ):
            with self.subTest(username=username):

                respuesta = self.client.get(
                    f"/api/perfil/{username}/"
                )

                self.assertEqual(
                    respuesta.status_code,
                    404,
                )

        respuesta = self.client.get(
            f"/api/perfil/{productor.username}/"
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

    def test_catalogo_django_excluye_cerrados_y_contadores_d10(self):
        from django.urls import reverse
        from app.views import _seudonimizar_identidad_cuenta

        url = reverse("catalogo_usuarios")

        anterior = self.client.get(url)

        self.assertEqual(anterior.status_code, 200)

        artistas_antes = anterior.context[
            "total_artistas"
        ]

        productores_antes = anterior.context[
            "total_productores"
        ]

        perfil = self.compra.usuario

        cuenta, perfil = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        respuesta = self.client.get(url)

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        ids = {
            usuario.pk
            for usuario in respuesta.context["usuarios"]
        }

        self.assertNotIn(
            perfil.pk,
            ids,
        )

        self.assertIn(
            self.compra.track.usuario_id,
            ids,
        )

        self.assertEqual(
            respuesta.context["total_artistas"],
            artistas_antes - 1,
        )

        self.assertEqual(
            respuesta.context["total_productores"],
            productores_antes,
        )

        # Buscar el identificador nuevo tampoco debe exponerlo.
        busqueda = self.client.get(
            url,
            {"q": cuenta.username},
        )

        self.assertEqual(
            busqueda.status_code,
            200,
        )

        self.assertFalse(
            busqueda.context["usuarios"].exists()
        )

        self.assertEqual(
            busqueda.context["total_artistas"],
            artistas_antes - 1,
        )

    def test_rutas_django_rechazan_perfiles_cerrados_d10(self):
        from django.urls import reverse
        from app.views import (
            _seudonimizar_identidad_cuenta,
            _obtener_perfil_anonimo,
        )

        perfil_comprador = self.compra.usuario
        perfil_productor = self.compra.track.usuario

        cuentas = []

        for perfil in (
            perfil_comprador,
            perfil_productor,
        ):
            username_original = perfil.user.username

            cuenta, _ = (
                _seudonimizar_identidad_cuenta(perfil)
            )

            cuentas.extend([
                username_original,
                cuenta.username,
            ])

        anonimo = _obtener_perfil_anonimo()

        cuentas.append(anonimo.user.username)

        for ruta in (
            "perfil2",
            "perfil_artista1",
            "perfil_productor1",
        ):
            for username in cuentas:

                with self.subTest(
                    ruta=ruta,
                    username=username,
                ):
                    respuesta = self.client.get(
                        reverse(
                            ruta,
                            kwargs={"username": username},
                        )
                    )

                    self.assertEqual(
                        respuesta.status_code,
                        404,
                    )

    def test_productor_seudonimizado_conserva_licencia_d10(self):
        from app.views import _seudonimizar_identidad_cuenta

        licencia, creada = self.emitir()

        self.assertTrue(creada)

        codigo_original = licencia.license_code
        firma_original = licencia.verification_hash

        productor = self.compra.track.usuario

        cuenta, productor = (
            _seudonimizar_identidad_cuenta(productor)
        )

        self.assertFalse(cuenta.is_active)

        self.assertIsNotNone(
            productor.cuenta_cerrada_en
        )

        self.client.force_login(
            self.compra.usuario.user
        )

        respuesta = self.client.get(
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        datos = respuesta.json()

        self.assertTrue(datos["verified"])

        self.assertEqual(
            datos["license_code"],
            codigo_original,
        )

        self.assertEqual(
            datos["verification_hash"],
            firma_original,
        )

        licencia.refresh_from_db()

        self.assertTrue(
            verify_license(licencia)
        )

    def test_limpieza_selectiva_actividad_personal_d10(self):
        from app.models import (
            Comentario,
            Interes,
            HistorialVenta,
        )

        from app.views import (
            _seudonimizar_identidad_cuenta,
        )

        licencia, creada = self.emitir()

        self.assertTrue(creada)

        perfil = self.compra.usuario
        comprador = perfil.user

        track = self.compra.track

        productor = track.usuario.user

        comentario_comprador = Comentario.objects.create(
            usuario=comprador,
            track=track,
            contenido="Comentario personal de prueba",
        )

        comentario_productor = Comentario.objects.create(
            usuario=productor,
            track=track,
            contenido="Comentario de otro usuario",
        )

        interes_comprador = Interes.objects.create(
            usuario=comprador,
            genero=track.genero,
        )

        interes_productor = Interes.objects.create(
            usuario=productor,
            genero=track.genero,
        )

        venta = HistorialVenta.objects.create(
            comprador=comprador,
            track=track,
            precio=track.precio,
        )

        codigo_original = licencia.license_code
        firma_original = licencia.verification_hash

        comprador_id = comprador.pk
        perfil_id = perfil.pk

        cuenta, perfil = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        self.assertEqual(cuenta.pk, comprador_id)
        self.assertEqual(perfil.pk, perfil_id)

        # Solo se elimina actividad del usuario cerrado.
        self.assertFalse(
            Comentario.objects.filter(
                pk=comentario_comprador.pk
            ).exists()
        )

        self.assertFalse(
            Interes.objects.filter(
                pk=interes_comprador.pk
            ).exists()
        )

        self.assertTrue(
            Comentario.objects.filter(
                pk=comentario_productor.pk
            ).exists()
        )

        self.assertTrue(
            Interes.objects.filter(
                pk=interes_productor.pk
            ).exists()
        )

        self.assertFalse(
            Comentario.objects.filter(
                usuario_id=comprador_id
            ).exists()
        )

        self.assertFalse(
            Interes.objects.filter(
                usuario_id=comprador_id
            ).exists()
        )

        # Los registros comerciales permanecen intactos.
        venta.refresh_from_db()
        self.compra.refresh_from_db()
        self.orden.refresh_from_db()
        licencia.refresh_from_db()

        self.assertEqual(
            venta.comprador_id,
            comprador_id,
        )

        self.assertEqual(
            self.compra.usuario_id,
            perfil_id,
        )

        self.assertEqual(
            self.orden.user_id,
            comprador_id,
        )

        self.assertEqual(
            licencia.license_code,
            codigo_original,
        )

        self.assertEqual(
            licencia.verification_hash,
            firma_original,
        )

        self.assertTrue(
            verify_license(licencia)
        )

    def test_limpieza_actividad_revierte_con_transaccion_d10(self):
        from django.db import transaction

        from app.models import (
            Comentario,
            Interes,
        )

        from app.views import (
            _seudonimizar_identidad_cuenta,
        )

        licencia, creada = self.emitir()

        self.assertTrue(creada)

        perfil = self.compra.usuario
        cuenta = perfil.user
        track = self.compra.track

        username_original = cuenta.username
        password_original = cuenta.password

        comentario = Comentario.objects.create(
            usuario=cuenta,
            track=track,
            contenido="Comentario para rollback",
        )

        interes = Interes.objects.create(
            usuario=cuenta,
            genero=track.genero,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Fallo simulado de cierre",
        ):

            with transaction.atomic():

                _seudonimizar_identidad_cuenta(
                    perfil
                )

                self.assertFalse(
                    Comentario.objects.filter(
                        pk=comentario.pk
                    ).exists()
                )

                self.assertFalse(
                    Interes.objects.filter(
                        pk=interes.pk
                    ).exists()
                )

                raise RuntimeError(
                    "Fallo simulado de cierre"
                )

        cuenta.refresh_from_db()
        perfil.refresh_from_db()
        licencia.refresh_from_db()

        # Debe restaurarse la identidad original.
        self.assertEqual(
            cuenta.username,
            username_original,
        )

        self.assertEqual(
            cuenta.password,
            password_original,
        )

        self.assertTrue(cuenta.is_active)

        self.assertTrue(
            cuenta.has_usable_password()
        )

        self.assertIsNone(
            perfil.cuenta_cerrada_en
        )

        # Tambien debe restaurarse la actividad personal.
        self.assertTrue(
            Comentario.objects.filter(
                pk=comentario.pk
            ).exists()
        )

        self.assertTrue(
            Interes.objects.filter(
                pk=interes.pk
            ).exists()
        )

        self.assertTrue(
            verify_license(licencia)
        )

    def test_webpay_session_id_aleatorio_conserva_historico_d10(self):
        from datetime import date
        from unittest.mock import patch

        from app.models import Venta
        from app.webpay_checkout_guard import (
            create_pending_webpay_order,
        )

        licencia, creada = self.emitir()

        self.assertTrue(creada)

        session_historica = self.orden.session_id
        firma_original = licencia.verification_hash

        track = self.compra.track

        sesiones = set()

        campo = WebpayTransaction._meta.get_field(
            "session_id"
        )

        for numero in range(2):

            comprador = User.objects.create_user(
                username=f"d10_session_buyer_{numero}",
                password="Solo-Pruebas-Sesion-D10",
            )

            perfil = Usuario.objects.create(
                user=comprador,
                tipo_usu=Usuario.ARTISTA,
            )

            venta = Venta.objects.create(
                detalle="Pedido de prueba D10",
                fecha=date.today(),
                precio=1000,
                iva=190,
                precio_total=1190,
                usuario_id=perfil,
                track=track,
                completada=False,
            )

            snapshot = [{
                "venta_id": venta.pk,
                "track_id": track.pk,
                "precio": 1000,
                "iva": 190,
            }]

            with patch(
                "app.webpay_reconciliation.reconcile_stale_pending_for_user"
            ):
                orden = create_pending_webpay_order(
                    user=comprador,
                    amount=1190,
                    cart_snapshot=snapshot,
                )

            orden.refresh_from_db()

            self.assertEqual(
                orden.user_id,
                comprador.pk,
            )

            self.assertEqual(
                orden.status,
                WebpayTransaction.ESTADO_PENDIENTE,
            )

            self.assertRegex(
                orden.session_id,
                r"^[0-9a-f]{32}$",
            )

            self.assertLessEqual(
                len(orden.session_id),
                campo.max_length,
            )

            self.assertNotEqual(
                orden.session_id,
                comprador.username,
            )

            self.assertNotIn(
                comprador.username,
                orden.session_id,
            )

            self.assertNotIn(
                orden.session_id,
                sesiones,
            )

            sesiones.add(orden.session_id)

        self.assertEqual(len(sesiones), 2)

        # No modificar identificadores comerciales anteriores.
        self.orden.refresh_from_db()
        licencia.refresh_from_db()

        self.assertEqual(
            self.orden.session_id,
            session_historica,
        )

        self.assertEqual(
            licencia.verification_hash,
            firma_original,
        )

        self.assertTrue(
            verify_license(licencia)
        )

    def test_backend_rechaza_cuenta_cerrada_reactivada_d10(self):
        from django.contrib.auth import authenticate
        from app.views import _seudonimizar_identidad_cuenta

        licencia, creada = self.emitir()
        self.assertTrue(creada)

        perfil = self.compra.usuario
        cuenta = perfil.user

        password = "Solo-Pruebas-Backend-D10!"

        cuenta.set_password(password)
        cuenta.save(update_fields=["password"])

        self.assertIsNotNone(
            authenticate(
                username=cuenta.username,
                password=password,
            )
        )

        cuenta, perfil = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        # Simular una reactivacion administrativa accidental.
        cuenta.set_password(password)
        cuenta.is_active = True

        cuenta.save(
            update_fields=["password", "is_active"]
        )

        self.assertTrue(cuenta.has_usable_password())

        self.assertIsNone(
            authenticate(
                username=cuenta.username,
                password=password,
            )
        )

        respuesta = self.client.post(
            "/api/auth/login/",
            data={
                "username": cuenta.username,
                "password": password,
            },
            content_type="application/json",
        )

        self.assertEqual(
            respuesta.status_code,
            401,
        )

        # Administradores sin perfil Usuario deben seguir
        # utilizando el mecanismo normal de autenticacion.
        admin = User.objects.create_superuser(
            username="admin_backend_d10",
            email="admin-d10@example.invalid",
            password=password,
        )

        self.assertIsNotNone(
            authenticate(
                username=admin.username,
                password=password,
            )
        )

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_backend_revoca_sesion_con_hash_restaurado_d10(self):
        from app.views import _seudonimizar_identidad_cuenta

        licencia, creada = self.emitir()
        self.assertTrue(creada)

        perfil = self.compra.usuario
        cuenta = perfil.user

        password_original = cuenta.password

        self.client.force_login(cuenta)

        url = (
            f"/api/track/{self.compra.track_id}/license/"
        )

        self.assertEqual(
            self.client.get(url).status_code,
            200,
        )

        cuenta, perfil = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        # Simular restauracion accidental del estado y hash.
        User.objects.filter(pk=cuenta.pk).update(
            is_active=True,
            password=password_original,
        )

        cuenta.refresh_from_db()

        self.assertEqual(
            cuenta.password,
            password_original,
        )

        self.assertTrue(cuenta.is_active)

        # El estado persistente debe bloquear la sesion.
        respuesta = self.client.get(url)

        self.assertEqual(
            respuesta.status_code,
            401,
        )

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_cambio_de_cuenta_excluye_cerrada_d10(self):
        from django.contrib.auth import BACKEND_SESSION_KEY
        from django.test import RequestFactory

        from app import account_switch_api
        from app.views import _seudonimizar_identidad_cuenta

        perfil = self.compra.usuario

        cuenta, perfil = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        cuenta.is_active = True

        cuenta.set_password(
            "Solo-Pruebas-Cambio-Cerrado-D10!"
        )

        cuenta.save(
            update_fields=["is_active", "password"]
        )

        productor = self.compra.track.usuario.user

        backend = (
            "app.auth_backends.BeatsCloudModelBackend"
        )

        entrada = {
            "id": cuenta.pk,
            "auth_hash": cuenta.get_session_auth_hash(),
            "backend": backend,
        }

        solicitud = RequestFactory().post(
            "/",
            data={"user_id": cuenta.pk},
            content_type="application/json",
        )

        solicitud.user = productor

        solicitud.session = {
            BACKEND_SESSION_KEY: backend,
            account_switch_api.SESSION_KEY: [entrada],
        }

        entradas = account_switch_api.valid_accounts(
            solicitud
        )

        ids = {
            item["id"]
            for item in entradas
        }

        self.assertNotIn(cuenta.pk, ids)
        self.assertIn(productor.pk, ids)

        publicas = account_switch_api.public_accounts(
            solicitud,
            [entrada],
        )

        self.assertEqual(publicas, [])

        respuesta = account_switch_api.account_switch_api(
            solicitud
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        self.assertEqual(
            solicitud.user.pk,
            productor.pk,
        )

    def test_backend_anterior_no_autoriza_sesion_d10(self):
        from django.conf import settings

        self.assertNotIn(
            "django.contrib.auth.backends.ModelBackend",
            settings.AUTHENTICATION_BACKENDS,
        )

        licencia, creada = self.emitir()
        self.assertTrue(creada)

        cuenta = self.compra.usuario.user

        self.client.force_login(
            cuenta,
            backend="django.contrib.auth.backends.ModelBackend",
        )

        url = (
            f"/api/track/{self.compra.track_id}/license/"
        )

        # Una sesion anterior requiere autenticarse nuevamente.
        self.assertEqual(
            self.client.get(url).status_code,
            401,
        )

        self.client.force_login(
            cuenta,
            backend="app.auth_backends.BeatsCloudModelBackend",
        )

        self.assertEqual(
            self.client.get(url).status_code,
            200,
        )

    def _cuenta_cerrada_con_credenciales_restauradas_d10(self):
        from app.views import _seudonimizar_identidad_cuenta

        licencia, creada = self.emitir()

        self.assertTrue(creada)

        cuenta, perfil = (
            _seudonimizar_identidad_cuenta(
                self.compra.usuario
            )
        )

        # Simular una modificacion administrativa accidental.
        cuenta.email = "cerrado-d10@example.invalid"
        cuenta.is_active = True

        cuenta.set_password(
            "Solo-Pruebas-Recuperacion-D10!"
        )

        cuenta.save(
            update_fields=[
                "email",
                "is_active",
                "password",
            ]
        )

        self.assertIsNotNone(
            perfil.cuenta_cerrada_en
        )

        self.assertTrue(cuenta.is_active)

        self.assertTrue(
            cuenta.has_usable_password()
        )

        return cuenta, licencia

    def test_formulario_recuperacion_excluye_cerrados_d10(self):
        from django.contrib.auth.forms import PasswordResetForm

        from app.account_password_reset import (
            BeatsCloudPasswordResetForm,
        )

        cuenta, licencia = (
            self._cuenta_cerrada_con_credenciales_restauradas_d10()
        )

        productor = self.compra.track.usuario.user

        productor.email = cuenta.email

        productor.save(update_fields=["email"])

        # El formulario normal incluiria ambas cuentas.
        originales = {
            user.pk
            for user in PasswordResetForm().get_users(
                cuenta.email
            )
        }

        self.assertIn(cuenta.pk, originales)
        self.assertIn(productor.pk, originales)

        # El formulario protegido excluye solo la cerrada.
        elegibles = {
            user.pk
            for user in BeatsCloudPasswordResetForm().get_users(
                cuenta.email
            )
        }

        self.assertNotIn(cuenta.pk, elegibles)
        self.assertIn(productor.pk, elegibles)

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_recuperacion_api_no_envia_correo_a_cerrada_d10(self):
        import json

        from unittest.mock import patch
        from django.test import RequestFactory

        from app.api_shim import (
            solicitar_restauracion_contrasena_api,
        )

        cuenta, licencia = (
            self._cuenta_cerrada_con_credenciales_restauradas_d10()
        )

        solicitud = RequestFactory().post(
            "/",
            data={"email": cuenta.email},
            content_type="application/json",
        )

        with patch(
            "app.account_password_reset."
            "BeatsCloudPasswordResetForm.send_mail"
        ) as correo:

            respuesta = (
                solicitar_restauracion_contrasena_api(
                    solicitud
                )
            )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        correo.assert_not_called()

        datos = json.loads(respuesta.content)

        self.assertIn(
            "No encontramos",
            datos["detail"],
        )

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_recuperacion_api_rechaza_token_de_cerrada_d10(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.test import RequestFactory
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        from app.api_shim import (
            confirmar_restauracion_contrasena_api,
        )

        cuenta, licencia = (
            self._cuenta_cerrada_con_credenciales_restauradas_d10()
        )

        password_original = cuenta.password

        uidb64 = urlsafe_base64_encode(
            force_bytes(cuenta.pk)
        )

        token = default_token_generator.make_token(
            cuenta
        )

        # Incluso un token criptograficamente valido debe
        # rechazarse si la cuenta fue cerrada definitivamente.
        self.assertTrue(
            default_token_generator.check_token(
                cuenta,
                token,
            )
        )

        solicitud = RequestFactory().post(
            "/",
            data={
                "uidb64": uidb64,
                "token": token,
                "new_password1": "Nueva-Clave-Prueba-D10!2026",
                "new_password2": "Nueva-Clave-Prueba-D10!2026",
            },
            content_type="application/json",
        )

        respuesta = (
            confirmar_restauracion_contrasena_api(
                solicitud
            )
        )

        self.assertEqual(
            respuesta.status_code,
            400,
        )

        cuenta.refresh_from_db()

        self.assertEqual(
            cuenta.password,
            password_original,
        )

        licencia.refresh_from_db()

        self.assertTrue(
            verify_license(licencia)
        )

    def test_recuperacion_django_no_envia_correo_a_cerrada_d10(self):
        from django.urls import reverse
        from django.core import mail

        cuenta, licencia = (
            self._cuenta_cerrada_con_credenciales_restauradas_d10()
        )

        with self.settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        ):
            for nombre in (
                "recuperar_contrasena",
                "password_reset",
            ):
                with self.subTest(ruta=nombre):

                    anteriores = len(
                        getattr(mail, "outbox", [])
                    )

                    respuesta = self.client.post(
                        reverse(nombre),
                        {"email": cuenta.email},
                    )

                    self.assertEqual(
                        respuesta.status_code,
                        302,
                    )

                    self.assertEqual(
                        len(getattr(mail, "outbox", [])),
                        anteriores,
                    )

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_recuperacion_django_rechaza_token_de_cerrada_d10(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.urls import reverse
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        cuenta, licencia = (
            self._cuenta_cerrada_con_credenciales_restauradas_d10()
        )

        password_original = cuenta.password

        uidb64 = urlsafe_base64_encode(
            force_bytes(cuenta.pk)
        )

        token = default_token_generator.make_token(cuenta)

        self.assertTrue(
            default_token_generator.check_token(
                cuenta, token
            )
        )

        for nombre in (
            "beatcloud_password_reset_confirm",
            "password_reset_confirm",
        ):
            with self.subTest(ruta=nombre):

                url = reverse(
                    nombre,
                    kwargs={
                        "uidb64": uidb64,
                        "token": token,
                    },
                )

                respuesta = self.client.get(url)

                self.assertEqual(
                    respuesta.status_code, 200
                )

                self.assertFalse(
                    respuesta.context["validlink"]
                )

                respuesta = self.client.post(
                    url,
                    {
                        "new_password1": "Nueva-Clave-D10!2026",
                        "new_password2": "Nueva-Clave-D10!2026",
                    },
                )

                self.assertEqual(
                    respuesta.status_code, 200
                )

                self.assertFalse(
                    respuesta.context["validlink"]
                )

                cuenta.refresh_from_db()

                self.assertEqual(
                    cuenta.password,
                    password_original,
                )

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_recuperacion_django_legitima_conserva_licencia_d10(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.urls import reverse
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        licencia, creada = self.emitir()
        self.assertTrue(creada)

        cuenta = self.compra.usuario.user

        uidb64 = urlsafe_base64_encode(
            force_bytes(cuenta.pk)
        )

        for numero, nombre in enumerate((
            "beatcloud_password_reset_confirm",
            "password_reset_confirm",
        )):
            with self.subTest(ruta=nombre):

                cuenta.refresh_from_db()

                token = default_token_generator.make_token(
                    cuenta
                )

                url = reverse(
                    nombre,
                    kwargs={
                        "uidb64": uidb64,
                        "token": token,
                    },
                )

                respuesta = self.client.get(url)

                self.assertEqual(
                    respuesta.status_code, 302
                )

                confirmacion = respuesta["Location"]

                respuesta = self.client.get(confirmacion)

                self.assertEqual(
                    respuesta.status_code, 200
                )

                self.assertTrue(
                    respuesta.context["validlink"]
                )

                nueva = (
                    f"Nueva-Clave-Valida-D10!2026-{numero}"
                )

                respuesta = self.client.post(
                    confirmacion,
                    {
                        "new_password1": nueva,
                        "new_password2": nueva,
                    },
                )

                self.assertEqual(
                    respuesta.status_code, 302
                )

                cuenta.refresh_from_db()

                self.assertTrue(
                    cuenta.check_password(nueva)
                )

                self.assertFalse(
                    default_token_generator.check_token(
                        cuenta, token
                    )
                )

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_cierre_invalida_recuperacion_iniciada_d10(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.urls import reverse
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.test import Client
        from app.views import _seudonimizar_identidad_cuenta

        licencia, creada = self.emitir()
        self.assertTrue(creada)

        perfil = self.compra.usuario
        cuenta = perfil.user

        password_original = cuenta.password
        email_original = cuenta.email
        ultimo_login = cuenta.last_login

        uidb64 = urlsafe_base64_encode(
            force_bytes(cuenta.pk)
        )

        token = default_token_generator.make_token(cuenta)

        confirmaciones = []

        # Abrir ambos enlaces antes del cierre.
        for nombre in (
            "beatcloud_password_reset_confirm",
            "password_reset_confirm",
        ):
            cliente = Client()

            url = reverse(
                nombre,
                kwargs={
                    "uidb64": uidb64,
                    "token": token,
                },
            )

            respuesta = cliente.get(url)

            self.assertEqual(
                respuesta.status_code, 302
            )

            confirmacion = respuesta["Location"]

            respuesta = cliente.get(confirmacion)

            self.assertTrue(
                respuesta.context["validlink"]
            )

            confirmaciones.append(
                (cliente, confirmacion)
            )

        cuenta, perfil = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        # Restaurar accidentalmente los datos que intervienen
        # en el token, pero mantener el estado de cierre.
        User.objects.filter(pk=cuenta.pk).update(
            is_active=True,
            password=password_original,
            email=email_original,
            last_login=ultimo_login,
        )

        cuenta.refresh_from_db()
        perfil.refresh_from_db()

        self.assertIsNotNone(
            perfil.cuenta_cerrada_en
        )

        self.assertTrue(
            default_token_generator.check_token(
                cuenta, token
            )
        )

        for cliente, confirmacion in confirmaciones:

            respuesta = cliente.post(
                confirmacion,
                {
                    "new_password1": "Clave-Rechazada-D10!2026",
                    "new_password2": "Clave-Rechazada-D10!2026",
                },
            )

            self.assertEqual(
                respuesta.status_code, 200
            )

            self.assertFalse(
                respuesta.context["validlink"]
            )

            cuenta.refresh_from_db()

            self.assertEqual(
                cuenta.password,
                password_original,
            )

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_auth_async_rechaza_cuenta_cerrada_d10(self):

        from asgiref.sync import async_to_sync
        from django.contrib.auth import aauthenticate

        cuenta, licencia = (
            self._cuenta_cerrada_con_credenciales_restauradas_d10()
        )

        password = "Solo-Pruebas-Recuperacion-D10!"

        self.assertTrue(cuenta.is_active)
        self.assertTrue(cuenta.check_password(password))

        autenticado = async_to_sync(aauthenticate)(
            username=cuenta.username,
            password=password,
        )

        self.assertIsNone(autenticado)

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_auth_async_no_recupera_usuario_cerrado_d10(self):

        from asgiref.sync import async_to_sync
        from app.auth_backends import BeatsCloudModelBackend

        cuenta, licencia = (
            self._cuenta_cerrada_con_credenciales_restauradas_d10()
        )

        self.assertTrue(cuenta.is_active)

        backend = BeatsCloudModelBackend()

        recuperado = async_to_sync(
            backend.aget_user
        )(cuenta.pk)

        self.assertIsNone(recuperado)

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_auth_async_permite_usuarios_legitimos_d10(self):

        from asgiref.sync import async_to_sync
        from django.contrib.auth import aauthenticate
        from app.auth_backends import BeatsCloudModelBackend

        password = "Solo-Pruebas-Async-D10!2026"

        usuario = User.objects.create_user(
            username="d10_async_legitimo",
            password=password,
        )

        Usuario.objects.create(
            user=usuario,
            tipo_usu=Usuario.ARTISTA,
        )

        administrador = User.objects.create_superuser(
            username="d10_async_admin",
            email="async-admin@example.invalid",
            password=password,
        )

        self.assertFalse(
            Usuario.objects.filter(
                user=administrador
            ).exists()
        )

        backend = BeatsCloudModelBackend()

        for cuenta in (usuario, administrador):

            with self.subTest(usuario=cuenta.username):

                autenticado = async_to_sync(
                    aauthenticate
                )(
                    username=cuenta.username,
                    password=password,
                )

                self.assertIsNotNone(autenticado)

                self.assertEqual(
                    autenticado.pk,
                    cuenta.pk,
                )

                recuperado = async_to_sync(
                    backend.aget_user
                )(cuenta.pk)

                self.assertIsNotNone(recuperado)

                self.assertEqual(
                    recuperado.pk,
                    cuenta.pk,
                )

    def test_auth_async_rechaza_credenciales_invalidas_d10(self):

        from asgiref.sync import async_to_sync
        from django.contrib.auth import aauthenticate
        from app.auth_backends import BeatsCloudModelBackend

        password = "Solo-Pruebas-Async-D10!2026"

        cuenta = User.objects.create_user(
            username="d10_async_credenciales",
            password=password,
        )

        Usuario.objects.create(
            user=cuenta,
            tipo_usu=Usuario.ARTISTA,
        )

        backend = BeatsCloudModelBackend()

        # Una clave incorrecta no permite autenticacion.
        resultado = async_to_sync(aauthenticate)(
            username=cuenta.username,
            password="Clave-Incorrecta-D10!",
        )

        self.assertIsNone(resultado)

        # Un usuario inexistente tampoco puede autenticarse.
        resultado = async_to_sync(aauthenticate)(
            username="d10_async_inexistente",
            password=password,
        )

        self.assertIsNone(resultado)

        # Una cuenta inactiva conserva las restricciones normales.
        cuenta.is_active = False
        cuenta.save(update_fields=["is_active"])

        resultado = async_to_sync(aauthenticate)(
            username=cuenta.username,
            password=password,
        )

        self.assertIsNone(resultado)

        recuperado = async_to_sync(
            backend.aget_user
        )(cuenta.pk)

        self.assertIsNone(recuperado)

    def test_autorizacion_cerrada_sin_permisos_d10(self):

        from asgiref.sync import async_to_sync
        from django.contrib.auth.models import Permission, Group
        from app.auth_backends import BeatsCloudModelBackend

        cuenta, licencia = (
            self._cuenta_cerrada_con_credenciales_restauradas_d10()
        )

        permiso = Permission.objects.get(
            content_type__app_label="app",
            codename="view_track",
        )

        permiso_grupo = Permission.objects.get(
            content_type__app_label="app",
            codename="change_track",
        )

        grupo = Group.objects.create(
            name="Grupo cerrado D10"
        )

        grupo.permissions.add(permiso_grupo)

        # Simular restauracion accidental de privilegios.
        cuenta.user_permissions.add(permiso)
        cuenta.groups.add(grupo)

        cuenta.refresh_from_db()

        self.assertTrue(cuenta.is_active)
        self.assertTrue(
            cuenta.user_permissions.filter(
                pk=permiso.pk
            ).exists()
        )

        backend = BeatsCloudModelBackend()

        for metodo in (
            backend.get_user_permissions,
            backend.get_group_permissions,
            backend.get_all_permissions,
        ):

            self.assertEqual(
                metodo(cuenta),
                set(),
            )

        for metodo in (
            backend.aget_user_permissions,
            backend.aget_group_permissions,
            backend.aget_all_permissions,
        ):

            self.assertEqual(
                async_to_sync(metodo)(cuenta),
                set(),
            )

        for nombre in (
            "app.view_track",
            "app.change_track",
        ):

            self.assertFalse(
                backend.has_perm(cuenta, nombre)
            )

            self.assertFalse(
                async_to_sync(backend.ahas_perm)(
                    cuenta,
                    nombre,
                )
            )

            self.assertFalse(cuenta.has_perm(nombre))

            self.assertFalse(
                async_to_sync(cuenta.ahas_perm)(nombre)
            )

        self.assertFalse(
            backend.has_module_perms(cuenta, "app")
        )

        self.assertFalse(
            async_to_sync(backend.ahas_module_perms)(
                cuenta,
                "app",
            )
        )

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_autorizacion_cerrada_ignora_cache_d10(self):

        from asgiref.sync import async_to_sync
        from django.contrib.auth.models import Permission
        from app.auth_backends import BeatsCloudModelBackend
        from app.views import _seudonimizar_identidad_cuenta

        licencia, creada = self.emitir()
        self.assertTrue(creada)

        perfil = self.compra.usuario

        cuenta_antigua = User.objects.get(
            pk=perfil.user_id
        )

        permiso = Permission.objects.get(
            content_type__app_label="app",
            codename="view_track",
        )

        cuenta_antigua.user_permissions.add(permiso)

        backend = BeatsCloudModelBackend()

        # Llenar la cache antes del cierre.
        self.assertIn(
            "app.view_track",
            backend.get_all_permissions(cuenta_antigua),
        )

        self.assertTrue(
            hasattr(cuenta_antigua, "_perm_cache")
        )

        _seudonimizar_identidad_cuenta(perfil)

        # La instancia antigua conserva el estado anterior.
        self.assertTrue(cuenta_antigua.is_active)

        self.assertIn(
            "app.view_track",
            cuenta_antigua._perm_cache,
        )

        # La consulta persistente debe prevalecer sobre la cache.
        self.assertEqual(
            backend.get_all_permissions(cuenta_antigua),
            set(),
        )

        self.assertEqual(
            backend.get_user_permissions(cuenta_antigua),
            set(),
        )

        self.assertFalse(
            backend.has_perm(
                cuenta_antigua,
                "app.view_track",
            )
        )

        self.assertEqual(
            async_to_sync(backend.aget_all_permissions)(
                cuenta_antigua
            ),
            set(),
        )

        self.assertFalse(
            async_to_sync(backend.ahas_perm)(
                cuenta_antigua,
                "app.view_track",
            )
        )

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_autorizacion_superusuario_cerrado_backend_d10(self):

        from asgiref.sync import async_to_sync
        from app.auth_backends import BeatsCloudModelBackend

        cuenta, licencia = (
            self._cuenta_cerrada_con_credenciales_restauradas_d10()
        )

        cuenta.is_staff = True
        cuenta.is_superuser = True

        cuenta.save(
            update_fields=[
                "is_staff",
                "is_superuser",
            ]
        )

        backend = BeatsCloudModelBackend()

        self.assertTrue(cuenta.is_active)
        self.assertTrue(cuenta.is_superuser)

        self.assertEqual(
            backend.get_all_permissions(cuenta),
            set(),
        )

        self.assertEqual(
            async_to_sync(backend.aget_all_permissions)(
                cuenta
            ),
            set(),
        )

        self.assertFalse(
            backend.has_perm(
                cuenta,
                "app.change_track",
            )
        )

        self.assertFalse(
            async_to_sync(backend.ahas_perm)(
                cuenta,
                "app.change_track",
            )
        )

        # El listado de usuarios autorizados tampoco
        # debe incluir cuentas cerradas.
        for activo in (True, False, None):

            self.assertFalse(
                backend.with_perm(
                    "app.change_track",
                    is_active=activo,
                ).filter(pk=cuenta.pk).exists()
            )

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))

    def test_autorizacion_conserva_permisos_legitimos_d10(self):

        from asgiref.sync import async_to_sync
        from django.contrib.auth.models import Permission, Group
        from app.auth_backends import BeatsCloudModelBackend

        cuenta = User.objects.create_user(
            username="d10_autorizacion_legitima",
            password="Solo-Pruebas-Permisos-D10!",
        )

        Usuario.objects.create(
            user=cuenta,
            tipo_usu=Usuario.ARTISTA,
        )

        permiso = Permission.objects.get(
            content_type__app_label="app",
            codename="view_track",
        )

        permiso_grupo = Permission.objects.get(
            content_type__app_label="app",
            codename="change_track",
        )

        grupo = Group.objects.create(
            name="Grupo legitimo D10"
        )

        cuenta.user_permissions.add(permiso)
        grupo.permissions.add(permiso_grupo)
        cuenta.groups.add(grupo)

        backend = BeatsCloudModelBackend()

        esperados = {
            "app.view_track",
            "app.change_track",
        }

        self.assertEqual(
            backend.get_all_permissions(cuenta),
            esperados,
        )

        self.assertEqual(
            async_to_sync(backend.aget_all_permissions)(
                cuenta
            ),
            esperados,
        )

        self.assertTrue(
            backend.has_module_perms(cuenta, "app")
        )

        self.assertTrue(
            async_to_sync(backend.ahas_module_perms)(
                cuenta,
                "app",
            )
        )

        for nombre in esperados:

            self.assertTrue(
                backend.has_perm(cuenta, nombre)
            )

            self.assertTrue(
                async_to_sync(backend.ahas_perm)(
                    cuenta,
                    nombre,
                )
            )

            self.assertTrue(
                backend.with_perm(nombre).filter(
                    pk=cuenta.pk
                ).exists()
            )

        # Conservar administradores legitimos sin perfil.
        administrador = User.objects.create_superuser(
            username="d10_autorizacion_admin",
            email="permisos-d10@example.invalid",
            password="Solo-Pruebas-Admin-D10!",
        )

        self.assertTrue(
            backend.has_perm(
                administrador,
                "app.change_track",
            )
        )

        self.assertTrue(
            async_to_sync(backend.ahas_perm)(
                administrador,
                "app.change_track",
            )
        )

    def test_autorizacion_cerrada_no_accede_admin_d10(self):

        from django.urls import reverse

        cuenta, licencia = (
            self._cuenta_cerrada_con_credenciales_restauradas_d10()
        )

        cuenta.is_staff = True
        cuenta.is_superuser = True

        cuenta.save(
            update_fields=[
                "is_staff",
                "is_superuser",
            ]
        )

        # Simular una sesion que contiene una cuenta cerrada.
        self.client.force_login(cuenta)

        for nombre in (
            "admin:index",
            "admin:password_change",
            "password_change",
        ):

            with self.subTest(ruta=nombre):

                respuesta = self.client.get(
                    reverse(nombre)
                )

                self.assertEqual(
                    respuesta.status_code,
                    302,
                )

                self.assertIn(
                    "login",
                    respuesta["Location"],
                )

        licencia.refresh_from_db()
        self.assertTrue(verify_license(licencia))
