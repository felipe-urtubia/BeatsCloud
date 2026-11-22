from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.http import Http404, HttpResponseRedirect
from django.test import RequestFactory, SimpleTestCase

from app.views import reproducir_preview_track


class R2PreviewViewsTests(SimpleTestCase):

    def setUp(self):
        self.request = RequestFactory().get(
            "/preview/1/"
        )

    def test_cancion_r2_utiliza_entrega_remota(self):
        preview = Mock()
        preview.name = (
            "previews/r2-" + "a" * 32 + ".mp3"
        )

        track = SimpleNamespace(
            preview=preview,
            storage_backend="r2",
        )

        with patch(
            "app.views.get_object_or_404",
            return_value=track,
        ), patch(
            "app.r2_preview_delivery.r2_preview_response",
            return_value=HttpResponseRedirect(
                "https://example.com/preview.mp3"
            ),
        ) as entregar:
            response = reproducir_preview_track(
                self.request, 1
            )

        self.assertEqual(response.status_code, 302)
        entregar.assert_called_once_with(track)
        preview.open.assert_not_called()

    def test_cancion_local_conserva_reproduccion(self):
        preview = Mock()
        preview.name = "previews/local.mp3"
        preview.open.return_value = BytesIO(b"ID3")

        track = SimpleNamespace(
            preview=preview,
            storage_backend="local",
        )

        with patch(
            "app.views.get_object_or_404",
            return_value=track,
        ):
            response = reproducir_preview_track(
                self.request, 2
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"], "audio/mpeg"
        )
        preview.open.assert_called_once_with("rb")
        response.close()

    def test_sin_preview_devuelve_404(self):
        track = SimpleNamespace(
            preview=None,
            storage_backend="r2",
        )

        with patch(
            "app.views.get_object_or_404",
            return_value=track,
        ):
            with self.assertRaises(Http404):
                reproducir_preview_track(
                    self.request, 3
                )
