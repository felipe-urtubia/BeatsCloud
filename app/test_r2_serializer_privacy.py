from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from app.api_shim import ser_track


class TrackSerializerPrivacyTests(SimpleTestCase):

    def test_no_expone_url_del_audio_original(self):
        track = Mock()

        track.id_track = 1
        track.nombre_track = "Audio de prueba"
        track.precio = 5000
        track.descripcion = "Prueba de privacidad"

        track.track.name = "canciones/privado.mp3"
        track.track.url = "/media/canciones/privado.mp3"

        track.preview.name = "previews/prueba.mp3"
        track.preview.url = "/media/previews/prueba.mp3"

        track.foto = None
        track.usuarios_que_dieron_like.count.return_value = 0

        with (
            patch(
                "app.api_shim.ser_genero",
                return_value={}
            ),
            patch(
                "app.api_shim.ser_user_public",
                return_value={}
            ),
        ):
            resultado = ser_track(track)

        self.assertIn("track", resultado)
        self.assertIsNone(resultado["track"])
        self.assertEqual(
            resultado["preview"],
            "/media/previews/prueba.mp3"
        )
