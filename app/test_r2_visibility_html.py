from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser, User
from django.http import Http404, HttpResponse
from django.test import RequestFactory, TestCase

from app import views
from app.models import Genero_Musical, Track, Usuario


class R2VisibilityHTMLTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="productor_html_r2",
            password="test-password",
        )

        cls.profile = Usuario.objects.create(
            user=cls.user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero = Genero_Musical.objects.create(
            descripcion="Pop",
        )

        cls.tracks = {}

        for estado in (
            "ready", "pending", "processing", "failed"
        ):
            cls.tracks[estado] = Track.objects.create(
                nombre_track="HTML R2 " + estado,
                precio=1000,
                usuario=cls.profile,
                genero=genero,
                track="canciones/test_" + estado + ".mp3",
                media_status=estado,
                storage_backend="local",
            )

    def request_anonima(self, ruta):
        request = RequestFactory().get(ruta)
        request.user = AnonymousUser()
        return request

    def test_catalogo_muestra_solo_ready(self):
        request = self.request_anonima("/catalogo/")

        with patch(
            "app.views.render",
            return_value=HttpResponse("OK"),
        ) as render_mock:
            views.catalogo(request)

        contexto = render_mock.call_args.args[2]

        resultados = None
        for nombre in ("page_obj", "tracks", "canciones"):
            if nombre in contexto:
                resultados = contexto[nombre]
                break

        self.assertIsNotNone(resultados)

        ids = {track.pk for track in resultados}

        self.assertIn(self.tracks["ready"].pk, ids)

        for estado in ("pending", "processing", "failed"):
            self.assertNotIn(self.tracks[estado].pk, ids)

    def test_perfil_publico_muestra_solo_ready(self):
        request = self.request_anonima(
            "/perfil/productor/" + self.user.username + "/"
        )

        with patch(
            "app.views.render",
            return_value=HttpResponse("OK"),
        ) as render_mock:
            views.perfil_productor1(
                request,
                self.user.username,
            )

        contexto = render_mock.call_args.args[2]
        ids = {
            track.pk
            for track in contexto["canciones"]
        }

        self.assertIn(self.tracks["ready"].pk, ids)

        for estado in ("pending", "processing", "failed"):
            self.assertNotIn(self.tracks[estado].pk, ids)

    def test_detalle_oculta_canciones_incompletas(self):
        for estado in ("pending", "processing", "failed"):
            with self.subTest(estado=estado):
                request = self.request_anonima("/detalle/")

                with self.assertRaises(Http404):
                    views.detalle_track(
                        request,
                        self.tracks[estado].pk,
                    )

    def test_detalle_permite_cancion_ready(self):
        request = self.request_anonima("/detalle/")

        with patch(
            "app.views.render",
            return_value=HttpResponse("OK"),
        ) as render_mock:
            response = views.detalle_track(
                request,
                self.tracks["ready"].pk,
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(render_mock.called)
