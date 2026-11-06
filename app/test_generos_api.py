import json
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .models import Genero_Musical, Track, Usuario


class GenerosPorIdAPITests(TestCase):
    def setUp(self):
        self.productor = User.objects.create_user(
            username="productor_generos_test",
            password="test-password",
        )
        self.perfil = Usuario.objects.create(
            user=self.productor,
            tipo_usu=Usuario.PRODUCTOR,
        )
        self.jazz = Genero_Musical.objects.create(
            descripcion="Jazz"
        )
        self.metal = Genero_Musical.objects.create(
            descripcion="Metal"
        )
        self.client.force_login(self.productor)

    def crear_track(self):
        return Track.objects.create(
            nombre_track="Pista para probar generos",
            precio=12000,
            genero=self.jazz,
            usuario=self.perfil,
        )

    def datos_publicacion(self, genero):
        return {
            "nombre_track": "Pista prueba genero ID",
            "precio": "12000",
            "descripcion": "Prueba automatizada",
            "genero": str(genero),
            "resource_type": "instrumental",
            "bpm": "120",
            "scale_key": "Am",
            "mood": "Oscuro",
            "duration": "30",
            "track": SimpleUploadedFile(
                "genero_prueba.wav",
                b"audio de prueba aislada",
                content_type="audio/wav",
            ),
        }

    def publicar(self, genero):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                with (
                    patch("mutagen.File", return_value=object()),
                    patch("app.api_shim.generar_preview_audio"),
                ):
                    return self.client.post(
                        "/api/upload/",
                        self.datos_publicacion(genero),
                    )

    def test_publicar_con_id_jazz(self):
        respuesta = self.publicar(self.jazz.pk)

        self.assertEqual(
            respuesta.status_code, 201, respuesta.content
        )

        pista = Track.objects.get(
            nombre_track="Pista prueba genero ID"
        )
        self.assertEqual(pista.genero_id, self.jazz.pk)
        self.assertEqual(pista.genero.descripcion, "Jazz")

    def test_editar_de_jazz_a_metal(self):
        pista = self.crear_track()

        respuesta = self.client.patch(
            f"/api/track/{pista.pk}/",
            data=json.dumps({
                "genero": str(self.metal.pk),
            }),
            content_type="application/json",
        )

        self.assertEqual(
            respuesta.status_code, 200, respuesta.content
        )

        pista.refresh_from_db()
        self.assertEqual(pista.genero_id, self.metal.pk)
        self.assertEqual(pista.genero.descripcion, "Metal")

    def test_edicion_rechaza_id_inexistente(self):
        pista = self.crear_track()
        id_invalido = self.metal.pk + 100000

        respuesta = self.client.patch(
            f"/api/track/{pista.pk}/",
            data=json.dumps({
                "genero": str(id_invalido),
            }),
            content_type="application/json",
        )

        self.assertEqual(respuesta.status_code, 400)

        pista.refresh_from_db()
        self.assertEqual(pista.genero_id, self.jazz.pk)

    def test_publicacion_rechaza_id_inexistente(self):
        cantidad_inicial = Track.objects.count()
        id_invalido = self.metal.pk + 100000

        respuesta = self.publicar(id_invalido)

        self.assertEqual(
            respuesta.status_code, 400, respuesta.content
        )
        self.assertEqual(
            Track.objects.count(), cantidad_inicial
        )
