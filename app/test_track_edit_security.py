"""Proteccion de la edicion tradicional de canciones."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpResponse
from django.test import TestCase, RequestFactory

from app.models import Usuario, Track, Genero_Musical

from app.views import (
    editar_track,
    _seudonimizar_identidad_cuenta,
)


class TrackEditSecurityTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="d10_edicion_html",
            password="Solo-Pruebas-Edicion-D10!",
        )

        self.perfil = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.genero, _ = Genero_Musical.objects.get_or_create(
            descripcion="Pop",
        )

        self.track = Track.objects.create(
            nombre_track="Track original D10",
            precio=1000,
            usuario=self.perfil,
            genero=self.genero,
            track="canciones/d10-original.wav",
            preview="previews/d10-original.mp3",
            storage_backend="local",
            media_status="ready",
            resource_type="instrumental",
            bpm=140,
            scale_key="Am",
            mood="Oscuro",
            duration=30,
            has_stems=False,
            has_wav=True,
            has_midi=False,
            allow_free_download=False,
            has_watermark=True,
        )

        self.factory = RequestFactory()

    def datos(self):

        return {
            "nombre_track": "Track actualizado D10",
            "precio": "1000",
            "genero": str(self.genero.pk),
            "resource_type": "instrumental",
            "bpm": "140",
            "scale_key": "Am",
            "mood": "Oscuro",
            "duration": "30",
            "has_stems": "false",
            "has_wav": "true",
            "has_midi": "false",
            "allow_free_download": "false",
            "has_watermark": "true",
        }

    def solicitar(
        self,
        datos=None,
        user=None,
        metodo="POST",
    ):

        url = f"/editar_track/{self.track.pk}/"

        if metodo == "GET":

            request = self.factory.get(url)

        else:

            request = self.factory.post(
                url,
                data=self.datos() if datos is None else datos,
            )

        request.user = (
            self.user if user is None else user
        )

        with (
            patch("app.views.messages.success"),
            patch(
                "app.views.render",
                return_value=HttpResponse("Formulario"),
            ) as renderizar,
        ):

            respuesta = editar_track(
                request,
                self.track.pk,
            )

        contexto = (
            renderizar.call_args.args[2]
            if renderizar.called
            else None
        )

        return respuesta, contexto

    def convertir_r2(self):

        self.track.track = ""

        self.track.storage_backend = "r2"

        self.track.r2_owner_user_id = self.user.pk

        self.track.r2_object_key = (
            f"private/{self.user.pk}/track/"
            + "a" * 32
            + ".wav"
        )

        self.track.r2_cover_key = (
            f"private/{self.user.pk}/cover/"
            + "b" * 32
            + ".png"
        )

        self.track.save(update_fields=[
            "track",
            "storage_backend",
            "r2_owner_user_id",
            "r2_object_key",
            "r2_cover_key",
        ])

    def test_edicion_local_conserva_audio_y_preview(self):

        audio = self.track.track.name
        preview = self.track.preview.name

        respuesta, _ = self.solicitar()

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.track.refresh_from_db()

        self.assertEqual(
            self.track.nombre_track,
            "Track actualizado D10",
        )

        self.assertEqual(self.track.track.name, audio)
        self.assertEqual(self.track.preview.name, preview)
        self.assertEqual(self.track.usuario_id, self.perfil.pk)

    def test_edicion_r2_no_exige_audio_local(self):

        self.convertir_r2()

        audio = self.track.r2_object_key
        portada = self.track.r2_cover_key

        respuesta, _ = self.solicitar()

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.track.refresh_from_db()

        self.assertEqual(
            self.track.nombre_track,
            "Track actualizado D10",
        )

        self.assertFalse(self.track.track)

        self.assertEqual(
            self.track.r2_object_key,
            audio,
        )

        self.assertEqual(
            self.track.r2_cover_key,
            portada,
        )

    def test_cuenta_cerrada_no_edita(self):

        _seudonimizar_identidad_cuenta(
            self.perfil
        )

        User.objects.filter(
            pk=self.user.pk
        ).update(is_active=True)

        respuesta, _ = self.solicitar()

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        self.track.refresh_from_db()

        self.assertEqual(
            self.track.nombre_track,
            "Track original D10",
        )

    def test_track_retirado_no_edita(self):

        Track.objects.filter(
            pk=self.track.pk
        ).update(is_retired=True)

        respuesta, _ = self.solicitar()

        self.assertEqual(
            respuesta.status_code,
            409,
        )

        self.track.refresh_from_db()

        self.assertTrue(self.track.is_retired)

        self.assertEqual(
            self.track.nombre_track,
            "Track original D10",
        )

    def test_otro_productor_no_edita(self):

        otro = User.objects.create_user(
            username="d10_otro_productor_html",
            password="Solo-Pruebas-D10!",
        )

        Usuario.objects.create(
            user=otro,
            tipo_usu=Usuario.PRODUCTOR,
        )

        with self.assertRaises(Http404):

            self.solicitar(user=otro)

        self.track.refresh_from_db()

        self.assertEqual(
            self.track.nombre_track,
            "Track original D10",
        )

    def test_reemplazo_audio_rechazado(self):

        datos = self.datos()

        datos["track"] = SimpleUploadedFile(
            "reemplazo.wav",
            b"contenido-simulado",
            content_type="audio/wav",
        )

        respuesta, contexto = self.solicitar(datos)

        self.assertEqual(respuesta.status_code, 200)

        self.assertIn(
            "track",
            contexto["form"].errors,
        )

        self.track.refresh_from_db()

        self.assertEqual(
            self.track.track.name,
            "canciones/d10-original.wav",
        )

        self.assertEqual(
            self.track.nombre_track,
            "Track original D10",
        )

    def test_portada_r2_no_admite_reemplazo_local(self):

        self.convertir_r2()

        portada = self.track.r2_cover_key

        datos = self.datos()

        datos["foto"] = SimpleUploadedFile(
            "portada.png",
            b"imagen-simulada",
            content_type="image/png",
        )

        respuesta, contexto = self.solicitar(datos)

        self.assertEqual(respuesta.status_code, 200)

        self.assertIn(
            "foto",
            contexto["form"].errors,
        )

        self.track.refresh_from_db()

        self.assertEqual(
            self.track.r2_cover_key,
            portada,
        )

        self.assertEqual(
            self.track.nombre_track,
            "Track original D10",
        )

    def test_formulario_r2_deshabilita_archivos_protegidos(self):

        self.convertir_r2()

        respuesta, contexto = self.solicitar(
            metodo="GET",
        )

        self.assertEqual(respuesta.status_code, 200)

        form = contexto["form"]

        self.assertTrue(
            form.fields["track"].disabled,
        )

        self.assertFalse(
            form.fields["track"].required,
        )

        self.assertTrue(
            form.fields["foto"].disabled,
        )

        self.assertTrue(
            contexto["audio_bloqueado"],
        )

    def test_archivos_protegidos_no_consultan_almacenamiento(self):

        self.track.foto = "portadas/d10-existente.png"

        self.track.r2_cover_key = (
            f"private/{self.user.pk}/cover/"
            + "a" * 32
            + ".png"
        )

        self.track.save(update_fields=[
            "foto",
            "r2_cover_key",
        ])

        audio_original = self.track.track.name
        foto_original = self.track.foto.name
        portada_original = self.track.r2_cover_key

        with (
            patch.object(
                Track._meta.get_field("track").storage,
                "size",
                side_effect=AssertionError(
                    "No debe consultar el tamano del archivo."
                ),
            ) as consultar_size,
            patch(
                "django.db.models.fields.files.FieldFile.open",
                side_effect=AssertionError(
                    "No debe abrir el archivo existente."
                ),
            ) as abrir_archivo,
        ):

            respuesta, _ = self.solicitar()

            self.assertEqual(
                respuesta.status_code,
                302,
            )

            consultar_size.assert_not_called()
            abrir_archivo.assert_not_called()

        self.track.refresh_from_db()

        self.assertEqual(
            self.track.nombre_track,
            "Track actualizado D10",
        )

        self.assertEqual(
            self.track.track.name,
            audio_original,
        )

        self.assertEqual(
            self.track.foto.name,
            foto_original,
        )

        self.assertEqual(
            self.track.r2_cover_key,
            portada_original,
        )

    def test_no_permite_limpiar_archivos_protegidos(self):

        self.convertir_r2()

        audio_original = self.track.r2_object_key
        portada_original = self.track.r2_cover_key

        datos = self.datos()

        datos["track-clear"] = "on"
        datos["foto-clear"] = "on"

        respuesta, contexto = self.solicitar(datos)

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertIn(
            "track",
            contexto["form"].errors,
        )

        self.assertIn(
            "foto",
            contexto["form"].errors,
        )

        self.track.refresh_from_db()

        self.assertEqual(
            self.track.r2_object_key,
            audio_original,
        )

        self.assertEqual(
            self.track.r2_cover_key,
            portada_original,
        )

        self.assertEqual(
            self.track.nombre_track,
            "Track original D10",
        )

    def comprobar_inputs_protegidos(self, respuesta, nombres):

        from html.parser import HTMLParser

        class Inspector(HTMLParser):

            def __init__(self):
                super().__init__()
                self.inputs = []

            def handle_starttag(self, tag, attrs):

                if tag == "input":
                    self.inputs.append(dict(attrs))

        inspector = Inspector()

        inspector.feed(
            respuesta.content.decode(respuesta.charset)
        )

        for campo in inspector.inputs:

            if campo.get("name") in nombres:

                self.assertIn(
                    "disabled",
                    campo,
                    f"Campo protegido habilitado: {campo.get('name')}",
                )

    def test_plantilla_real_edicion_local(self):

        from django.urls import reverse

        self.client.force_login(self.user)

        respuesta = self.client.get(
            reverse(
                "editar_track",
                args=[self.track.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertTemplateUsed(
            respuesta,
            "app/editar_track.html",
        )

        form = respuesta.context["form"]

        self.assertTrue(form.fields["track"].disabled)
        self.assertFalse(form.fields["track"].required)
        self.assertFalse(form.fields["foto"].disabled)

        self.comprobar_inputs_protegidos(
            respuesta,
            {"track", "track-clear"},
        )

    def test_plantilla_real_edicion_r2(self):

        from django.urls import reverse

        self.convertir_r2()

        self.client.force_login(self.user)

        respuesta = self.client.get(
            reverse(
                "editar_track",
                args=[self.track.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertTemplateUsed(
            respuesta,
            "app/editar_track.html",
        )

        form = respuesta.context["form"]

        self.assertTrue(form.fields["track"].disabled)
        self.assertFalse(form.fields["track"].required)
        self.assertTrue(form.fields["foto"].disabled)

        self.comprobar_inputs_protegidos(
            respuesta,
            {
                "track",
                "track-clear",
                "foto",
                "foto-clear",
            },
        )


    def test_cuenta_cerrada_no_retira(self):

        from app.views import eliminar_track
        from app.api_shim import track_delete_api

        _seudonimizar_identidad_cuenta(self.perfil)

        User.objects.filter(
            pk=self.user.pk
        ).update(is_active=True)

        for endpoint in (
            eliminar_track,
            track_delete_api,
        ):

            with self.subTest(endpoint=endpoint.__name__):

                solicitud = self.factory.post(
                    "/retirada-prueba/"
                )

                solicitud.user = self.user
                solicitud._dont_enforce_csrf_checks = True

                respuesta = endpoint(
                    solicitud,
                    self.track.pk,
                )

                self.assertEqual(
                    respuesta.status_code,
                    403,
                )

                self.track.refresh_from_db()

                self.assertFalse(self.track.is_retired)
