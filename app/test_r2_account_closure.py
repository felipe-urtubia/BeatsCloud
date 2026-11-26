"""Proteccion de cargas R2 frente al cierre de cuentas."""

from django.contrib.auth.models import User
from django.core import signing
from django.test import TestCase, RequestFactory

from app.models import (
    Usuario,
    Track,
    Genero_Musical,
    R2UploadClaim,
)

from app.r2_presign import ALLOWED, TOKEN_SALT

from app.r2_claim_service import (
    reserve_r2_upload,
    try_begin_r2_processing,
    R2ClaimConflict,
)

from app.r2_claim_lifecycle import (
    attach_r2_private_key,
    mark_r2_claim_failed,
)

from app.r2_claim_finalize import (
    finalize_r2_claim,
    R2ClaimFinalizationError,
)

from app.views import (
    _seudonimizar_identidad_cuenta,
    _ejecutar_eliminacion_cuenta,
    EliminacionCuentaBloqueada,
)


class R2AccountClosureTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="d10_r2_cierre",
            password="Solo-Pruebas-Cierre-R2-D10!",
        )

        self.perfil = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.genero, _ = Genero_Musical.objects.get_or_create(
            descripcion="Pop",
        )

        self.mime = sorted(
            ALLOWED["track"][".wav"]
        )[0]

        self.privada = (
            f"private/{self.user.pk}/track/"
            + "b" * 32
            + ".wav"
        )

    def token(self, letra="a"):

        return signing.dumps(
            {
                "owner": self.user.pk,
                "key": (
                    f"pending/{self.user.pk}/track/"
                    + letra * 32
                    + ".wav"
                ),
                "size": 16044,
                "kind": "track",
                "mime": self.mime,
            },
            salt=TOKEN_SALT,
        )

    def reservar(self, letra="a"):

        resultado = reserve_r2_upload(
            user_id=self.user.pk,
            upload_token=self.token(letra),
        )

        return R2UploadClaim.objects.get(
            pk=resultado.claim_id,
        )

    def cerrar(self):

        return _seudonimizar_identidad_cuenta(
            self.perfil,
        )

    def crear_track(self):

        return Track.objects.create(
            nombre_track="Cancion R2 protegida D10",
            precio=1000,
            genero=self.genero,
            usuario=self.perfil,
            track="",
            preview="previews/d10-prueba.mp3",
            storage_backend="r2",
            r2_object_key=self.privada,
            r2_owner_user_id=self.user.pk,
            media_status="processing",
        )

    def test_cuenta_cerrada_no_reserva(self):

        token = self.token()

        self.cerrar()

        # Simular una reactivacion accidental.
        User.objects.filter(pk=self.user.pk).update(
            is_active=True,
        )

        with self.assertRaises(R2ClaimConflict):

            reserve_r2_upload(
                user_id=self.user.pk,
                upload_token=token,
            )

        self.assertFalse(
            R2UploadClaim.objects.filter(
                owner=self.user,
            ).exists()
        )

    def test_cuenta_cerrada_no_inicia_procesamiento(self):

        reserva = self.reservar()

        self.cerrar()

        self.assertFalse(
            try_begin_r2_processing(
                claim_id=reserva.pk,
                user_id=self.user.pk,
            )
        )

        reserva.refresh_from_db()

        self.assertEqual(
            reserva.status,
            "reserved",
        )

    def test_cuenta_cerrada_no_asocia_clave_privada(self):

        reserva = self.reservar()

        self.cerrar()

        # Simular un estado residual inconsistente.
        R2UploadClaim.objects.filter(
            pk=reserva.pk,
        ).update(status="processing")

        self.assertFalse(
            attach_r2_private_key(
                claim_id=reserva.pk,
                user_id=self.user.pk,
                private_key=self.privada,
            )
        )

        reserva.refresh_from_db()

        self.assertEqual(reserva.private_key, "")

        # La recuperacion de errores debe continuar disponible.
        self.assertTrue(
            mark_r2_claim_failed(
                claim_id=reserva.pk,
                user_id=self.user.pk,
            )
        )

        reserva.refresh_from_db()

        self.assertEqual(reserva.status, "failed")

    def test_cuenta_cerrada_no_finaliza_cancion(self):

        reserva = self.reservar()

        self.cerrar()

        # Simular una reserva residual con copia privada.
        R2UploadClaim.objects.filter(
            pk=reserva.pk,
        ).update(
            status="processing",
            private_key=self.privada,
        )

        track = self.crear_track()

        with self.assertRaises(R2ClaimFinalizationError):

            finalize_r2_claim(
                claim_id=reserva.pk,
                user_id=self.user.pk,
                track_id=track.pk,
            )

        track.refresh_from_db()
        reserva.refresh_from_db()

        self.assertEqual(
            track.media_status,
            "processing",
        )

        self.assertEqual(
            reserva.status,
            "processing",
        )

        self.assertIsNone(reserva.track_id)

    def test_procesamiento_bloquea_ambos_cierres(self):

        reserva = self.reservar()

        self.assertTrue(
            try_begin_r2_processing(
                claim_id=reserva.pk,
                user_id=self.user.pk,
            )
        )

        with self.assertRaisesRegex(
            EliminacionCuentaBloqueada,
            "cargas R2",
        ):

            self.cerrar()

        solicitud = RequestFactory().post("/")
        solicitud.user = self.user

        with self.assertRaisesRegex(
            EliminacionCuentaBloqueada,
            "cargas R2",
        ):

            _ejecutar_eliminacion_cuenta(
                solicitud,
                self.perfil,
            )

        self.user.refresh_from_db()
        self.perfil.refresh_from_db()
        reserva.refresh_from_db()

        self.assertTrue(self.user.is_active)

        self.assertIsNone(
            self.perfil.cuenta_cerrada_en,
        )

        self.assertEqual(
            reserva.status,
            "processing",
        )

    def test_cierre_conserva_reservas_no_activas(self):

        lista = self.reservar("a")

        self.assertTrue(
            try_begin_r2_processing(
                claim_id=lista.pk,
                user_id=self.user.pk,
            )
        )

        self.assertTrue(
            attach_r2_private_key(
                claim_id=lista.pk,
                user_id=self.user.pk,
                private_key=self.privada,
            )
        )

        track = self.crear_track()

        self.assertTrue(
            finalize_r2_claim(
                claim_id=lista.pk,
                user_id=self.user.pk,
                track_id=track.pk,
            )
        )

        reservada = self.reservar("c")
        fallida = self.reservar("d")

        self.assertTrue(
            try_begin_r2_processing(
                claim_id=fallida.pk,
                user_id=self.user.pk,
            )
        )

        self.assertTrue(
            mark_r2_claim_failed(
                claim_id=fallida.pk,
                user_id=self.user.pk,
            )
        )

        self.cerrar()

        for reserva, estado in (
            (lista, "ready"),
            (reservada, "reserved"),
            (fallida, "failed"),
        ):

            reserva.refresh_from_db()

            self.assertEqual(
                reserva.status,
                estado,
            )

            self.assertEqual(
                reserva.owner_id,
                self.user.pk,
            )

        track.refresh_from_db()

        self.assertEqual(
            track.r2_object_key,
            self.privada,
        )

        self.assertEqual(
            lista.track_id,
            track.pk,
        )

        self.perfil.refresh_from_db()

        self.assertIsNotNone(
            self.perfil.cuenta_cerrada_en,
        )
