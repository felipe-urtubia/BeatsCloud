from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import signing
from django.test import TestCase
from django.utils import timezone

from app.r2_claim import R2UploadClaim
from app.r2_claim_service import (
    reserve_r2_upload,
    try_begin_r2_processing,
)
from app.r2_claim_lifecycle import (
    R2ClaimStateError,
    attach_r2_private_key,
    mark_r2_claim_failed,
)
from app.r2_presign import ALLOWED, TOKEN_SALT


class R2ClaimLifecycleTests(TestCase):

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="productor_ciclo_r2"
        )

        self.mime = sorted(ALLOWED["track"][".wav"])[0]

        self.pendiente = (
            f"pending/{self.usuario.pk}/track/"
            + ("a" * 32)
            + ".wav"
        )

        self.privada = (
            f"private/{self.usuario.pk}/track/"
            + ("b" * 32)
            + ".wav"
        )

        token = signing.dumps(
            {
                "owner": self.usuario.pk,
                "key": self.pendiente,
                "size": 16044,
                "kind": "track",
                "mime": self.mime,
            },
            salt=TOKEN_SALT,
        )

        self.reserva = reserve_r2_upload(
            user_id=self.usuario.pk,
            upload_token=token,
        )

    def comenzar(self):
        self.assertTrue(
            try_begin_r2_processing(
                claim_id=self.reserva.claim_id,
                user_id=self.usuario.pk,
            )
        )

    def asociar(self, **cambios):
        datos = {
            "claim_id": self.reserva.claim_id,
            "user_id": self.usuario.pk,
            "private_key": self.privada,
        }

        datos.update(cambios)

        return attach_r2_private_key(**datos)

    def fallar(self, **cambios):
        datos = {
            "claim_id": self.reserva.claim_id,
            "user_id": self.usuario.pk,
        }

        datos.update(cambios)

        return mark_r2_claim_failed(**datos)

    def obtener(self):
        return R2UploadClaim.objects.get(
            pk=self.reserva.claim_id
        )

    def test_asocia_clave_privada(self):
        self.comenzar()

        self.assertTrue(self.asociar())
        self.assertEqual(
            self.obtener().private_key,
            self.privada,
        )

    def test_no_asocia_reserva_sin_iniciar(self):
        self.assertFalse(self.asociar())
        self.assertEqual(
            self.obtener().private_key,
            "",
        )

    def test_no_reemplaza_clave_asociada(self):
        self.comenzar()
        self.assertTrue(self.asociar())

        nueva = (
            f"private/{self.usuario.pk}/track/"
            + ("c" * 32)
            + ".wav"
        )

        self.assertFalse(
            self.asociar(private_key=nueva)
        )

        self.assertEqual(
            self.obtener().private_key,
            self.privada,
        )

    def test_no_asocia_a_otro_usuario(self):
        self.comenzar()

        otro_id = 99999

        clave_ajena = (
            f"private/{otro_id}/track/"
            + ("b" * 32)
            + ".wav"
        )

        self.assertFalse(
            self.asociar(
                user_id=otro_id,
                private_key=clave_ajena,
            )
        )

        self.assertEqual(
            self.obtener().private_key,
            "",
        )

    def test_rechaza_clave_de_otro_productor(self):
        self.comenzar()

        with self.assertRaises(R2ClaimStateError):
            self.asociar(
                private_key="private/999/track/"
                + ("b" * 32)
                + ".wav"
            )

    def test_rechaza_clave_pending(self):
        self.comenzar()

        with self.assertRaises(R2ClaimStateError):
            self.asociar(
                private_key=self.pendiente
            )

    def test_no_asocia_extension_diferente(self):
        self.comenzar()

        otra = self.privada[:-4] + ".mp3"

        self.assertFalse(
            self.asociar(private_key=otra)
        )

    def test_fallo_conserva_clave_privada(self):
        self.comenzar()
        self.assertTrue(self.asociar())
        self.assertTrue(self.fallar())

        reserva = self.obtener()

        self.assertEqual(
            reserva.status,
            "failed",
        )

        self.assertEqual(
            reserva.private_key,
            self.privada,
        )

    def test_no_modifica_reserva_ready(self):
        self.comenzar()

        R2UploadClaim.objects.filter(
            pk=self.reserva.claim_id
        ).update(status="ready")

        self.assertFalse(self.fallar())

        self.assertEqual(
            self.obtener().status,
            "ready",
        )

    def test_no_falla_reserva_ajena(self):
        self.comenzar()

        self.assertFalse(
            self.fallar(user_id=99999)
        )

        self.assertEqual(
            self.obtener().status,
            "processing",
        )

    def test_reserva_failed_no_se_reprocesa(self):
        self.comenzar()
        self.assertTrue(self.fallar())

        self.assertFalse(
            try_begin_r2_processing(
                claim_id=self.reserva.claim_id,
                user_id=self.usuario.pk,
            )
        )

    def test_actualiza_fecha_al_comenzar(self):
        fecha_pasada = (
            timezone.now() - timedelta(days=1)
        )

        R2UploadClaim.objects.filter(
            pk=self.reserva.claim_id
        ).update(updated_at=fecha_pasada)

        self.comenzar()

        self.assertGreater(
            self.obtener().updated_at,
            fecha_pasada,
        )
