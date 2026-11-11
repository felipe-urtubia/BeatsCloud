from django.contrib.auth.models import (
    AnonymousUser,
    User,
)
from django.http import Http404
from django.test import RequestFactory, TestCase

from app import views
from app.models import Genero_Musical, Track, Usuario


class R2TraditionalMediaTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="owner_traditional_r2",
            password="test-password",
        )

        cls.profile = Usuario.objects.create(
            user=cls.owner,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genre = Genero_Musical.objects.create(
            descripcion="Pop",
        )

        cls.tracks = {}

        for estado in (
            "ready", "pending", "processing", "failed"
        ):
            cls.tracks[estado] = Track.objects.create(
                nombre_track="Traditional " + estado,
                precio=1000,
                usuario=cls.profile,
                genero=genre,
                track="canciones/test_" + estado + ".mp3",
                preview="previews/test_" + estado + ".mp3",
                media_status=estado,
                storage_backend="local",
            )

    def crear_request(self, user=None):
        request = RequestFactory().get("/prueba/")
        request.user = (
            user if user is not None
            else AnonymousUser()
        )
        return request

    def test_preview_incompleto_devuelve_404(self):
        for estado in ("pending", "processing", "failed"):
            with self.subTest(estado=estado):
                with self.assertRaises(Http404):
                    views.reproducir_preview_track(
                        self.crear_request(),
                        self.tracks[estado].pk,
                    )

    def test_reproduccion_incompleta_devuelve_404(self):
        for estado in ("pending", "processing", "failed"):
            with self.subTest(estado=estado):
                with self.assertRaises(Http404):
                    views.reproducir_track(
                        self.crear_request(self.owner),
                        self.tracks[estado].pk,
                    )

    def test_descarga_incompleta_devuelve_404(self):
        for estado in ("pending", "processing", "failed"):
            with self.subTest(estado=estado):
                with self.assertRaises(Http404):
                    views.descargar_track(
                        self.crear_request(self.owner),
                        self.tracks[estado].pk,
                    )

    def test_ready_no_permite_reproduccion_anonima(self):
        response = views.reproducir_track(
            self.crear_request(),
            self.tracks["ready"].pk,
        )

        self.assertEqual(response.status_code, 403)

    def test_descarga_ready_requiere_autenticacion(self):
        response = views.descargar_track(
            self.crear_request(),
            self.tracks["ready"].pk,
        )

        self.assertEqual(response.status_code, 302)
