from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from app.r2_visibility import (
    only_ready_tracks,
    is_media_ready,
)


class R2VisibilityTests(SimpleTestCase):

    def test_ready_es_visible(self):
        track = SimpleNamespace(media_status="ready")
        self.assertTrue(is_media_ready(track))

    def test_estados_incompletos_no_son_visibles(self):
        for estado in ("pending", "processing", "failed"):
            with self.subTest(estado=estado):
                track = SimpleNamespace(media_status=estado)
                self.assertFalse(is_media_ready(track))

    def test_estado_desconocido_no_es_visible(self):
        track = SimpleNamespace()
        self.assertFalse(is_media_ready(track))

    def test_queryset_filtra_solo_ready(self):
        queryset = Mock()
        resultado = only_ready_tracks(queryset)

        queryset.filter.assert_called_once_with(
            media_status="ready"
        )
        self.assertIs(
            resultado,
            queryset.filter.return_value
        )
