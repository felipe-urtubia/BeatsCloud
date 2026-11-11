from django.contrib.auth.models import (
    AnonymousUser,
    User,
)
from django.test import RequestFactory, TestCase

from app.api_shim import claim_free_track_api
from app.models import (
    Genero_Musical,
    HistorialCompra,
    Track,
    Usuario,
)


class R2ClaimFreeReadyTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="owner_claim_r2",
            password="test-password",
        )
        cls.owner_profile = Usuario.objects.create(
            user=cls.owner,
            tipo_usu=Usuario.PRODUCTOR,
        )

        cls.buyer = User.objects.create_user(
            username="buyer_claim_r2",
            password="test-password",
        )
        cls.buyer_profile = Usuario.objects.create(
            user=cls.buyer,
            tipo_usu=Usuario.ARTISTA,
        )

        genre = Genero_Musical.objects.create(
            descripcion="Pop",
        )

        cls.tracks = {}

        for estado in (
            "ready",
            "pending",
            "processing",
            "failed",
        ):
            cls.tracks[estado] = Track.objects.create(
                nombre_track="Free " + estado,
                precio=0,
                usuario=cls.owner_profile,
                genero=genre,
                media_status=estado,
                storage_backend="local",
            )

        cls.paid_track = Track.objects.create(
            nombre_track="Paid ready",
            precio=1000,
            usuario=cls.owner_profile,
            genero=genre,
            media_status="ready",
            storage_backend="local",
        )

    def reclamar(self, track, user=None):
        request = RequestFactory().post(
            "/api/track/" + str(track.pk) + "/claim-free/"
        )
        request.user = (
            user if user is not None
            else self.buyer
        )
        return claim_free_track_api(request, track.pk)

    def test_incompletos_no_se_reclaman(self):
        for estado in (
            "pending",
            "processing",
            "failed",
        ):
            with self.subTest(estado=estado):
                track = self.tracks[estado]
                response = self.reclamar(track)

                self.assertEqual(response.status_code, 404)

                self.assertFalse(
                    HistorialCompra.objects.filter(
                        usuario=self.buyer_profile,
                        track=track,
                    ).exists()
                )

    def test_gratuito_ready_se_registra(self):
        track = self.tracks["ready"]

        response = self.reclamar(track)

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            HistorialCompra.objects.filter(
                usuario=self.buyer_profile,
                track=track,
            ).exists()
        )

    def test_reclamo_ready_es_idempotente(self):
        track = self.tracks["ready"]

        primera = self.reclamar(track)
        segunda = self.reclamar(track)

        self.assertEqual(primera.status_code, 200)
        self.assertEqual(segunda.status_code, 200)

        self.assertEqual(
            HistorialCompra.objects.filter(
                usuario=self.buyer_profile,
                track=track,
            ).count(),
            1,
        )

    def test_cancion_de_pago_no_se_reclama_gratis(self):
        response = self.reclamar(self.paid_track)

        self.assertEqual(response.status_code, 409)

        self.assertFalse(
            HistorialCompra.objects.filter(
                usuario=self.buyer_profile,
                track=self.paid_track,
            ).exists()
        )

    def test_anonimo_no_puede_reclamar(self):
        track = self.tracks["ready"]

        response = self.reclamar(
            track,
            user=AnonymousUser(),
        )

        self.assertEqual(response.status_code, 401)

        self.assertFalse(
            HistorialCompra.objects.filter(
                usuario=self.buyer_profile,
                track=track,
            ).exists()
        )
