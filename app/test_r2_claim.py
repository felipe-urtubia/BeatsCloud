from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.migrations.recorder import MigrationRecorder
from django.test import TestCase

from app.r2_claim import R2UploadClaim


class R2ClaimTests(TestCase):

    def setUp(self):
        usuario_modelo = get_user_model()

        self.usuario = usuario_modelo.objects.create_user(
            username="r2_prueba_productor"
        )

        self.clave = (
            "pending/"
            + str(self.usuario.pk)
            + "/track/"
            + ("a" * 32)
            + ".wav"
        )

    def crear(self, clave=None, usuario=None):
        return R2UploadClaim.objects.create(
            owner=usuario or self.usuario,
            pending_key=clave or self.clave,
            expected_size=16044,
            expected_mime="audio/wav",
        )

    def test_migracion_0024_aplicada_en_pruebas(self):
        self.assertTrue(
            MigrationRecorder.Migration.objects.filter(
                app="app",
                name="0024_r2uploadclaim",
            ).exists()
        )

    def test_crea_reserva_con_estado_inicial(self):
        reserva = self.crear()

        self.assertEqual(
            reserva.status,
            "reserved",
        )

        self.assertEqual(
            reserva.owner_id,
            self.usuario.pk,
        )

        self.assertIsNone(reserva.track_id)

    def test_rechaza_clave_duplicada(self):
        self.crear()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.crear()

        self.assertEqual(
            R2UploadClaim.objects.count(),
            1,
        )

    def test_rechaza_clave_duplicada_de_otro_usuario(self):
        self.crear()

        otro = get_user_model().objects.create_user(
            username="r2_segundo_productor"
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.crear(
                    usuario=otro
                )

        self.assertEqual(
            R2UploadClaim.objects.count(),
            1,
        )

    def test_permite_claves_diferentes(self):
        self.crear()

        otra_clave = (
            "pending/"
            + str(self.usuario.pk)
            + "/track/"
            + ("b" * 32)
            + ".wav"
        )

        self.crear(clave=otra_clave)

        self.assertEqual(
            R2UploadClaim.objects.count(),
            2,
        )
