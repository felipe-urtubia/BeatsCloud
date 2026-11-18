from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from app.api_shim import cart_add_api
from app.models import (
    Genero_Musical,
    Track,
    Usuario,
    Venta,
)


class R2VisibilityAccessTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="owner_r2_access",
            password="test-password",
        )
        cls.owner_profile = Usuario.objects.create(
            user=cls.owner,
            tipo_usu=Usuario.PRODUCTOR,
        )

        cls.buyer = User.objects.create_user(
            username="buyer_r2_access",
            password="test-password",
        )
        Usuario.objects.create(
            user=cls.buyer,
            tipo_usu=Usuario.ARTISTA,
        )

        genre = Genero_Musical.objects.create(
            descripcion="Pop",
        )

        cls.tracks = {}

        for estado in ("pending", "processing", "failed"):
            cls.tracks[estado] = Track.objects.create(
                nombre_track="Audio " + estado,
                precio=1000,
                usuario=cls.owner_profile,
                genero=genre,
                track="canciones/prueba_" + estado + ".mp3",
                preview="previews/prueba_" + estado + ".mp3",
                media_status=estado,
                storage_backend="local",
            )

    def test_preview_incompleto_no_se_entrega(self):
        for estado, track in self.tracks.items():
            with self.subTest(estado=estado):
                response = self.client.get(
                    f"/api/track/{track.pk}/preview/"
                )
                self.assertEqual(response.status_code, 404)

    def test_original_incompleto_no_se_reproduce(self):
        self.client.force_login(self.owner)

        for estado, track in self.tracks.items():
            with self.subTest(estado=estado):
                response = self.client.get(
                    f"/api/track/{track.pk}/reproducir/"
                )
                self.assertEqual(response.status_code, 404)

    def test_original_incompleto_no_se_descarga(self):
        self.client.force_login(self.owner)

        for estado, track in self.tracks.items():
            with self.subTest(estado=estado):
                response = self.client.get(
                    f"/api/track/{track.pk}/descargar/"
                )
                self.assertEqual(response.status_code, 404)

    def test_no_se_compra_un_track_incompleto(self):
        factory = RequestFactory()

        for estado, track in self.tracks.items():
            with self.subTest(estado=estado):
                request = factory.post(
                    f"/api/carrito/agregar/{track.pk}/"
                )
                request.user = self.buyer

                response = cart_add_api(request, track.pk)

                self.assertEqual(response.status_code, 404)
                self.assertFalse(
                    Venta.objects.filter(track=track).exists()
                )
