"""Integracion publica del cierre de cuentas D10."""

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.utils import timezone

from app.models import (
    Usuario,
    Track,
    Genero_Musical,
    HistorialCompra,
    R2UploadClaim,
)


class AccountClosureIntegrationTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="d10_cierre_productor",
            password="Solo-Pruebas-D10!",
        )

        self.perfil = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero, _ = Genero_Musical.objects.get_or_create(
            descripcion="Pop"
        )

        self.track = Track.objects.create(
            nombre_track="Track protegido D10",
            precio=1000,
            usuario=self.perfil,
            genero=genero,
            storage_backend="r2",
            r2_owner_user_id=self.user.pk,
            r2_object_key=(
                f"private/{self.user.pk}/track/"
                + "a" * 32
                + ".wav"
            ),
            preview="previews/d10-cierre.mp3",
            media_status="ready",
        )

        self.client.force_login(self.user)

    def confirmar(self):

        session = self.client.session

        session["eliminar_cuenta_codigo_hash"] = (
            make_password("123456")
        )

        session["eliminar_cuenta_usuario_id"] = self.user.pk

        session["eliminar_cuenta_codigo_creado"] = (
            timezone.now().timestamp()
        )

        session["eliminar_cuenta_intentos"] = 0

        session.save()

        return self.client.post(
            "/api/auth/account-deletion/confirm/",
            {"codigo": "123456"},
            content_type="application/json",
        )

    def crear_reserva(self, estado):

        return R2UploadClaim.objects.create(
            owner=self.user,
            pending_key=(
                f"pending/{self.user.pk}/track/"
                + "b" * 32
                + ".wav"
            ),
            expected_size=16044,
            expected_mime="audio/wav",
            status=estado,
        )

    def test_cierre_conserva_track_comprado_y_reserva(self):

        comprador = User.objects.create_user(
            username="d10_comprador_cierre",
            password="Solo-Pruebas-D10!",
        )

        perfil_comprador = Usuario.objects.create(
            user=comprador,
            tipo_usu=Usuario.ARTISTA,
        )

        compra = HistorialCompra.objects.create(
            usuario=perfil_comprador,
            track=self.track,
        )

        reserva = self.crear_reserva("reserved")

        audio = self.track.r2_object_key

        respuesta = self.confirmar()

        self.assertEqual(
            respuesta.status_code,
            200,
            respuesta.content,
        )

        self.user.refresh_from_db()
        self.perfil.refresh_from_db()
        self.track.refresh_from_db()
        compra.refresh_from_db()
        reserva.refresh_from_db()

        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.has_usable_password())

        self.assertIsNotNone(
            self.perfil.cuenta_cerrada_en
        )

        self.assertTrue(self.track.is_retired)
        self.assertEqual(self.track.r2_object_key, audio)
        self.assertEqual(self.track.usuario_id, self.perfil.pk)
        self.assertEqual(compra.track_id, self.track.pk)
        self.assertEqual(reserva.owner_id, self.user.pk)
        self.assertEqual(reserva.status, "reserved")

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_cierre_bloqueado_por_procesamiento_r2(self):

        reserva = self.crear_reserva("processing")

        respuesta = self.confirmar()

        self.assertEqual(
            respuesta.status_code,
            409,
        )

        self.user.refresh_from_db()
        self.perfil.refresh_from_db()
        self.track.refresh_from_db()
        reserva.refresh_from_db()

        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.perfil.cuenta_cerrada_en)
        self.assertFalse(self.track.is_retired)
        self.assertEqual(reserva.status, "processing")
