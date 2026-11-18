import os
from unittest.mock import patch

from django.test import Client, SimpleTestCase
from django.urls import resolve, reverse

from app import api_shim
from app.r2_upload_http import r2_finalize_upload_api


class R2RouteWiringTests(SimpleTestCase):

    def setUp(self):
        self.url = "/api/r2/finalize/"

    def test_ruta_r2_resuelve_endpoint_correcto(self):
        self.assertEqual(
            reverse("r2_finalize_upload"),
            self.url,
        )

        self.assertIs(
            resolve(self.url).func,
            r2_finalize_upload_api,
        )

    def test_ruta_tradicional_sigue_disponible(self):
        rutas = [
            ruta
            for ruta in api_shim.urlpatterns
            if getattr(ruta, "callback", None)
            is api_shim.upload_api
        ]

        self.assertTrue(
            rutas,
            "No se encontro la ruta de subida tradicional.",
        )

        for ruta in rutas:
            direccion = "/" + str(ruta.pattern)

            self.assertIs(
                resolve(direccion).func,
                api_shim.upload_api,
            )

            self.assertNotEqual(
                direccion,
                self.url,
            )

    def test_subidas_desactivadas_responden_503(self):
        cliente = Client()

        with (
            patch.dict(
                os.environ,
                {"R2_UPLOADS_ENABLED": "false"},
            ),
            patch(
                "app.r2_upload_http.complete_r2_track_upload"
            ) as ejecutar,
        ):
            respuesta = cliente.post(
                self.url,
                data="{}",
                content_type="application/json",
            )

        self.assertEqual(respuesta.status_code, 503)
        ejecutar.assert_not_called()

    def test_valor_yes_no_activa_subidas(self):
        cliente = Client()

        with (
            patch.dict(
                os.environ,
                {"R2_UPLOADS_ENABLED": "yes"},
            ),
            patch(
                "app.r2_upload_http.complete_r2_track_upload"
            ) as ejecutar,
        ):
            respuesta = cliente.post(
                self.url,
                data="{}",
                content_type="application/json",
            )

        self.assertEqual(respuesta.status_code, 503)
        ejecutar.assert_not_called()

    def test_get_no_permitido(self):
        respuesta = Client().get(self.url)

        self.assertEqual(respuesta.status_code, 405)

    def test_csrf_sigue_protegiendo_la_ruta(self):
        cliente = Client(
            enforce_csrf_checks=True
        )

        with (
            patch.dict(
                os.environ,
                {"R2_UPLOADS_ENABLED": "true"},
            ),
            patch(
                "app.r2_upload_http.complete_r2_track_upload"
            ) as ejecutar,
        ):
            respuesta = cliente.post(
                self.url,
                data="{}",
                content_type="application/json",
            )

        self.assertEqual(respuesta.status_code, 403)
        ejecutar.assert_not_called()
