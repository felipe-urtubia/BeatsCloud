from django.contrib.auth import get_user_model
from django.core import signing
from django.test import TestCase

from app.r2_claim import R2UploadClaim
from app.r2_claim_service import (
    R2ClaimConflict,
    reserve_r2_upload,
    try_begin_r2_processing,
)
from app.r2_presign import ALLOWED, TOKEN_SALT
from app.r2_registration_guard import R2RegistrationGuardError


class R2ClaimServiceTests(TestCase):

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="productor_claim_servicio",
        )

        self.clave = (
            f"pending/{self.usuario.pk}/track/"
            + ("e" * 32)
            + ".wav"
        )

        self.mime = sorted(ALLOWED["track"][".wav"])[0]

    def token(self, **cambios):
        datos = {
            "owner": self.usuario.pk,
            "key": self.clave,
            "size": 16044,
            "kind": "track",
            "mime": self.mime,
        }

        datos.update(cambios)

        return signing.dumps(
            datos,
            salt=TOKEN_SALT,
        )

    def reservar(self, **cambios):
        opciones = {
            "user_id": self.usuario.pk,
            "upload_token": self.token(),
        }

        opciones.update(cambios)
        return reserve_r2_upload(**opciones)

    def test_reserva_inicial(self):
        resultado = self.reservar()

        self.assertTrue(resultado.created)
        self.assertEqual(resultado.status, "reserved")
        self.assertEqual(R2UploadClaim.objects.count(), 1)

    def test_repeticion_no_crea_otra_reserva(self):
        primera = self.reservar()
        segunda = self.reservar()

        self.assertFalse(segunda.created)
        self.assertEqual(primera.claim_id, segunda.claim_id)
        self.assertEqual(R2UploadClaim.objects.count(), 1)

    def test_procesamiento_solo_una_vez(self):
        reserva = self.reservar()

        self.assertTrue(
            try_begin_r2_processing(
                claim_id=reserva.claim_id,
                user_id=self.usuario.pk,
            )
        )

        self.assertFalse(
            try_begin_r2_processing(
                claim_id=reserva.claim_id,
                user_id=self.usuario.pk,
            )
        )

        self.assertEqual(
            R2UploadClaim.objects.get(
                pk=reserva.claim_id
            ).status,
            "processing",
        )

    def test_repeticion_no_reinicia_procesamiento(self):
        reserva = self.reservar()

        try_begin_r2_processing(
            claim_id=reserva.claim_id,
            user_id=self.usuario.pk,
        )

        repetida = self.reservar()

        self.assertFalse(repetida.created)
        self.assertEqual(repetida.status, "processing")

    def test_no_reprocesa_reserva_finalizada(self):
        reserva = self.reservar()

        R2UploadClaim.objects.filter(
            pk=reserva.claim_id
        ).update(status="ready")

        self.assertFalse(
            try_begin_r2_processing(
                claim_id=reserva.claim_id,
                user_id=self.usuario.pk,
            )
        )

    def test_no_procesa_reserva_de_otro_usuario(self):
        reserva = self.reservar()

        otro = get_user_model().objects.create_user(
            username="productor_claim_ajeno",
        )

        self.assertFalse(
            try_begin_r2_processing(
                claim_id=reserva.claim_id,
                user_id=otro.pk,
            )
        )

        self.assertEqual(
            R2UploadClaim.objects.get(
                pk=reserva.claim_id
            ).status,
            "reserved",
        )

    def test_token_invalido_no_reserva(self):
        with self.assertRaises(R2RegistrationGuardError):
            self.reservar(
                upload_token="token-invalido"
            )

        self.assertEqual(R2UploadClaim.objects.count(), 0)

    def test_otro_productor_no_reserva(self):
        otro = get_user_model().objects.create_user(
            username="productor_token_ajeno",
        )

        with self.assertRaises(R2RegistrationGuardError):
            self.reservar(user_id=otro.pk)

        self.assertEqual(R2UploadClaim.objects.count(), 0)

    def test_metadatos_diferentes_generan_conflicto(self):
        self.reservar()

        with self.assertRaises(R2ClaimConflict):
            self.reservar(
                upload_token=self.token(size=16045)
            )

        self.assertEqual(R2UploadClaim.objects.count(), 1)

    def test_clave_de_otro_owner_generara_conflicto(self):
        reserva = self.reservar()

        otro = get_user_model().objects.create_user(
            username="productor_owner_incompatible",
        )

        R2UploadClaim.objects.filter(
            pk=reserva.claim_id
        ).update(owner=otro)

        with self.assertRaises(R2ClaimConflict):
            self.reservar()

        self.assertEqual(R2UploadClaim.objects.count(), 1)

    def test_claves_distintas_generan_reservas_distintas(self):
        primera = self.reservar()

        otra_clave = (
            f"pending/{self.usuario.pk}/track/"
            + ("f" * 32)
            + ".wav"
        )

        segunda = self.reservar(
            upload_token=self.token(key=otra_clave)
        )

        self.assertTrue(segunda.created)
        self.assertNotEqual(
            primera.claim_id,
            segunda.claim_id,
        )
        self.assertEqual(R2UploadClaim.objects.count(), 2)
