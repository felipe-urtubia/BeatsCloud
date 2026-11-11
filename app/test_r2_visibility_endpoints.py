from django.contrib.auth.models import User
from django.test import TestCase

from app.models import (
    Genero_Musical,
    Track,
    Usuario,
)


class R2VisibilityEndpointsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="productor_visibilidad_r2",
            password="test-password",
        )

        cls.profile = Usuario.objects.create(
            user=cls.user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        cls.genre = Genero_Musical.objects.create(
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
                nombre_track="Prueba R2 " + estado,
                precio=1000,
                usuario=cls.profile,
                genero=cls.genre,
                media_status=estado,
                storage_backend="local",
            )

    def test_catalogo_solo_publica_ready(self):
        response = self.client.get("/api/catalogo/")

        self.assertEqual(response.status_code, 200)

        ids = {
            item["id_track"]
            for item in response.json()["tracks"]
        }

        self.assertIn(self.tracks["ready"].pk, ids)

        for estado in (
            "pending",
            "processing",
            "failed",
        ):
            with self.subTest(estado=estado):
                self.assertNotIn(
                    self.tracks[estado].pk,
                    ids,
                )

    def test_detalle_oculta_tracks_incompletos(self):
        for estado in (
            "pending",
            "processing",
            "failed",
        ):
            with self.subTest(estado=estado):
                track = self.tracks[estado]

                response = self.client.get(
                    f"/api/track/{track.pk}/"
                )

                self.assertEqual(
                    response.status_code,
                    404,
                )

        ready = self.tracks["ready"]

        response = self.client.get(
            f"/api/track/{ready.pk}/"
        )

        self.assertEqual(response.status_code, 200)

    def test_perfil_publico_solo_muestra_ready(self):
        response = self.client.get(
            f"/api/perfil/{self.user.username}/"
        )

        self.assertEqual(response.status_code, 200)

        ids = {
            item["id_track"]
            for item in response.json()["tracks"]
        }

        self.assertIn(self.tracks["ready"].pk, ids)

        for estado in (
            "pending",
            "processing",
            "failed",
        ):
            with self.subTest(estado=estado):
                self.assertNotIn(
                    self.tracks[estado].pk,
                    ids,
                )
