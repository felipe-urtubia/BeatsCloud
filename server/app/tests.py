import re

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from django.core.files.uploadedfile import SimpleUploadedFile

from .models import (
    Genero_Musical,
    HistorialCompra,
    HistorialVenta,
    Track,
    Usuario,
)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
)
class EliminarCuentaTests(TestCase):
    PASSWORD = 'ClaveSegura123!'

    def crear_usuario(self, username, tipo, email=None):
        user = User.objects.create_user(
            username=username,
            email=email or f'{username}@example.com',
            password=self.PASSWORD,
        )
        perfil = Usuario.objects.create(
            user=user,
            tipo_usu=tipo,
        )
        return user, perfil

    def crear_genero(self):
        return Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

    def solicitar_codigo(self, user):
        self.client.force_login(user)
        response = self.client.post(
            reverse('eliminar_cuenta'),
            {'password': self.PASSWORD},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        match = re.search(r'\b(\d{6})\b', mail.outbox[-1].body)
        self.assertIsNotNone(match)
        return match.group(1)

    def confirmar_codigo(self, codigo):
        return self.client.post(
            reverse('confirmar_eliminacion_cuenta'),
            {'codigo': codigo},
        )

    def test_pide_login_para_eliminar_cuenta(self):
        response = self.client.get(reverse('eliminar_cuenta'))
        self.assertEqual(response.status_code, 302)

    def test_muestra_confirmacion_a_usuario_autenticado(self):
        user, _ = self.crear_usuario('artista1', Usuario.ARTISTA)
        self.client.force_login(user)

        response = self.client.get(reverse('eliminar_cuenta'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/eliminar_cuenta.html')

    def test_password_incorrecta_no_elimina_ni_envia_correo(self):
        user, _ = self.crear_usuario('artista2', Usuario.ARTISTA)
        user_id = user.pk
        self.client.force_login(user)

        response = self.client.post(
            reverse('eliminar_cuenta'),
            {'password': 'incorrecta'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(User.objects.filter(pk=user_id).exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_password_correcta_envia_correo_y_no_elimina_de_inmediato(self):
        user, _ = self.crear_usuario('artista_correo', Usuario.ARTISTA)
        user_id = user.pk
        self.client.force_login(user)

        response = self.client.post(
            reverse('eliminar_cuenta'),
            {'password': self.PASSWORD},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(pk=user_id).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('eliminación', mail.outbox[0].subject.lower())

    def test_codigo_incorrecto_no_elimina_cuenta(self):
        user, _ = self.crear_usuario('artista_codigo_mal', Usuario.ARTISTA)
        user_id = user.pk
        self.solicitar_codigo(user)

        response = self.confirmar_codigo('000000')

        self.assertEqual(response.status_code, 400)
        self.assertTrue(User.objects.filter(pk=user_id).exists())

    def test_codigo_correcto_elimina_artista(self):
        user, perfil = self.crear_usuario('artista3', Usuario.ARTISTA)
        user_id = user.pk
        perfil_id = perfil.pk

        codigo = self.solicitar_codigo(user)
        response = self.confirmar_codigo(codigo)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=user_id).exists())
        self.assertFalse(Usuario.objects.filter(pk=perfil_id).exists())
        self.assertTemplateUsed(response, 'app/cuenta_eliminada.html')

    def test_productor_conserva_track_comprado_como_anonimo(self):
        productor, perfil_productor = self.crear_usuario(
            'productor1',
            Usuario.PRODUCTOR,
        )
        comprador, perfil_comprador = self.crear_usuario(
            'comprador1',
            Usuario.ARTISTA,
        )
        genero = self.crear_genero()

        comprado = Track.objects.create(
            nombre_track='Track comprado',
            precio=5000,
            track='canciones/comprado.mp3',
            genero=genero,
            usuario=perfil_productor,
        )
        sin_compras = Track.objects.create(
            nombre_track='Track sin compras',
            precio=4000,
            track='canciones/sin_compras.mp3',
            genero=genero,
            usuario=perfil_productor,
        )

        HistorialCompra.objects.create(
            usuario=perfil_comprador,
            track=comprado,
        )

        productor_id = productor.pk
        comprado_id = comprado.pk
        sin_compras_id = sin_compras.pk

        codigo = self.solicitar_codigo(productor)
        response = self.confirmar_codigo(codigo)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=productor_id).exists())
        self.assertTrue(Track.objects.filter(pk=comprado_id).exists())
        self.assertFalse(Track.objects.filter(pk=sin_compras_id).exists())

        comprado.refresh_from_db()
        self.assertEqual(
            comprado.usuario.user.username,
            'UsuarioAnonimo',
        )
        self.assertFalse(comprado.usuario.user.is_active)
        self.assertFalse(comprado.usuario.user.has_usable_password())

        self.assertTrue(
            HistorialCompra.objects.filter(
                usuario=perfil_comprador,
                track=comprado,
            ).exists()
        )

    def test_al_borrar_artista_venta_permanece_como_usuario_eliminado(self):
        productor, perfil_productor = self.crear_usuario(
            'productor_historial',
            Usuario.PRODUCTOR,
        )
        artista, _ = self.crear_usuario(
            'artista_a_eliminar',
            Usuario.ARTISTA,
        )
        genero = self.crear_genero()

        track = Track.objects.create(
            nombre_track='Track historial',
            precio=5000,
            track='canciones/historial.mp3',
            genero=genero,
            usuario=perfil_productor,
        )

        venta = HistorialVenta.objects.create(
            comprador=artista,
            precio=track.precio,
            track=track,
        )
        venta_id = venta.pk
        artista_id = artista.pk

        codigo = self.solicitar_codigo(artista)
        response = self.confirmar_codigo(codigo)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=artista_id).exists())
        self.assertTrue(
            HistorialVenta.objects.filter(pk=venta_id).exists()
        )

        venta.refresh_from_db()
        self.assertIsNone(venta.comprador)

        self.client.force_login(productor)
        perfil_response = self.client.get(reverse('perfil_productor'))
        self.assertContains(perfil_response, 'Usuario eliminado')

    def test_usuario_anonimo_no_aparece_en_catalogo_usuarios(self):
        anonimo, _ = self.crear_usuario(
            'UsuarioAnonimo',
            Usuario.PRODUCTOR,
        )
        anonimo.is_active = False
        anonimo.set_unusable_password()
        anonimo.save()

        response = self.client.get(reverse('catalogo_usuarios'))

        self.assertEqual(response.status_code, 200)
        usuarios = list(response.context['usuarios'])
        self.assertFalse(
            any(
                usuario.user.username == 'UsuarioAnonimo'
                for usuario in usuarios
            )
        )



class PreviewAudioTests(TestCase):
    def test_artista_sin_compra_no_tiene_audio_completo_en_detalle(self):
        productor = User.objects.create_user(
            username='productor_preview',
            email='productor_preview@example.com',
            password='ClaveSegura123!',
        )
        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        artista = User.objects.create_user(
            username='artista_preview',
            email='artista_preview@example.com',
            password='ClaveSegura123!',
        )
        Usuario.objects.create(
            user=artista,
            tipo_usu=Usuario.ARTISTA,
        )

        genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        track = Track.objects.create(
            nombre_track='Track preview',
            precio=5000,
            track='canciones/track_preview.mp3',
            genero=genero,
            usuario=perfil_productor,
        )

        self.client.force_login(artista)

        response = self.client.get(
            reverse('detalle', kwargs={'track_id': track.id_track})
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn('audio_completo', response.context)
        self.assertFalse(response.context['audio_completo'])


    def test_artista_sin_compra_no_puede_obtener_audio_completo(self):
        productor = User.objects.create_user(
            username='productor_audio_protegido',
            email='productor_audio_protegido@example.com',
            password='ClaveSegura123!',
        )
        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        artista = User.objects.create_user(
            username='artista_sin_compra',
            email='artista_sin_compra@example.com',
            password='ClaveSegura123!',
        )
        Usuario.objects.create(
            user=artista,
            tipo_usu=Usuario.ARTISTA,
        )

        genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        track = Track.objects.create(
            nombre_track='Audio protegido',
            precio=5000,
            track=SimpleUploadedFile(
                'audio_completo.mp3',
                b'ESTE-ES-EL-AUDIO-COMPLETO',
                content_type='audio/mpeg',
            ),
            genero=genero,
            usuario=perfil_productor,
        )

        self.client.force_login(artista)

        response = self.client.get(
            reverse('reproducir_track', kwargs={'track_id': track.id_track})
        )

        self.assertEqual(response.status_code, 403)


    def test_track_tiene_archivo_preview_separado(self):
        nombres_campos = {
            campo.name
            for campo in Track._meta.get_fields()
        }

        self.assertIn('preview', nombres_campos)

        campo_preview = Track._meta.get_field('preview')
        self.assertEqual(campo_preview.upload_to, 'previews/')


    def test_configuracion_expone_ffmpeg_path(self):
        self.assertTrue(hasattr(settings, 'FFMPEG_PATH'))
        self.assertTrue(settings.FFMPEG_PATH)


    def test_generar_preview_audio_crea_muestra_de_maximo_30_segundos(self):
        from importlib import import_module
        import io
        import tempfile
        import wave

        import mutagen

        try:
            audio_utils = import_module('app.audio_utils')
        except ModuleNotFoundError:
            self.fail(
                'Falta app.audio_utils con la función generar_preview_audio.'
            )

        self.assertTrue(
            hasattr(audio_utils, 'generar_preview_audio'),
            'Falta la función generar_preview_audio.'
        )

        productor = User.objects.create_user(
            username='productor_preview_ffmpeg',
            email='productor_preview_ffmpeg@example.com',
            password='ClaveSegura123!',
        )
        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(8000)
            audio.writeframes(b'\x00\x00' * 8000 * 31)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                track = Track.objects.create(
                    nombre_track='Track largo para preview',
                    precio=5000,
                    track=SimpleUploadedFile(
                        'track_largo.wav',
                        wav_buffer.getvalue(),
                        content_type='audio/wav',
                    ),
                    genero=genero,
                    usuario=perfil_productor,
                )

                audio_utils.generar_preview_audio(track)
                track.refresh_from_db()

                self.assertTrue(track.preview.name)
                self.assertTrue(track.preview.name.startswith('previews/'))

                audio_preview = mutagen.File(track.preview.path)
                self.assertIsNotNone(audio_preview)
                self.assertIsNotNone(audio_preview.info)
                self.assertLessEqual(audio_preview.info.length, 30.5)
                self.assertGreater(audio_preview.info.length, 29.0)


    def test_subir_track_genera_preview_automaticamente(self):
        import io
        import tempfile
        import wave

        productor = User.objects.create_user(
            username='productor_upload_preview',
            email='productor_upload_preview@example.com',
            password='ClaveSegura123!',
        )
        Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(8000)
            audio.writeframes(b'\x00\x00' * 8000 * 2)

        self.client.force_login(productor)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse('upload_file'),
                    {
                        'nombre_track': 'Track con preview automático',
                        'precio': 5000,
                        'genero': genero.pk,
                        'descripcion': 'Prueba de generación automática.',
                        'track': SimpleUploadedFile(
                            'track_upload.wav',
                            wav_buffer.getvalue(),
                            content_type='audio/wav',
                        ),
                    },
                )

                self.assertEqual(response.status_code, 302)

                track = Track.objects.get(
                    nombre_track='Track con preview automático'
                )

                self.assertTrue(
                    track.preview.name,
                    'La subida debe generar automáticamente el archivo preview.'
                )
                self.assertTrue(track.preview.name.startswith('previews/'))


    def test_visitante_puede_obtener_solo_archivo_preview(self):
        productor = User.objects.create_user(
            username='productor_ruta_preview',
            email='productor_ruta_preview@example.com',
            password='ClaveSegura123!',
        )
        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        track = Track.objects.create(
            nombre_track='Track con ruta preview',
            precio=5000,
            track=SimpleUploadedFile(
                'original.mp3',
                b'ESTE_ES_EL_AUDIO_COMPLETO',
                content_type='audio/mpeg',
            ),
            preview=SimpleUploadedFile(
                'preview.mp3',
                b'ESTE_ES_SOLO_EL_PREVIEW',
                content_type='audio/mpeg',
            ),
            genero=genero,
            usuario=perfil_productor,
        )

        response = self.client.get(
            reverse(
                'reproducir_preview_track',
                kwargs={'track_id': track.id_track},
            )
        )

        self.assertEqual(response.status_code, 200)

        contenido = b''.join(response.streaming_content)

        self.assertEqual(contenido, b'ESTE_ES_SOLO_EL_PREVIEW')
        self.assertNotIn(b'AUDIO_COMPLETO', contenido)


    def test_detalle_sin_compra_usa_ruta_preview(self):
        productor = User.objects.create_user(
            username='productor_detalle_preview',
            email='productor_detalle_preview@example.com',
            password='ClaveSegura123!',
        )
        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        track = Track.objects.create(
            nombre_track='Track detalle preview',
            precio=5000,
            track=SimpleUploadedFile(
                'original.mp3',
                b'AUDIO_COMPLETO',
                content_type='audio/mpeg',
            ),
            preview=SimpleUploadedFile(
                'preview.mp3',
                b'AUDIO_PREVIEW',
                content_type='audio/mpeg',
            ),
            genero=genero,
            usuario=perfil_productor,
        )

        response = self.client.get(
            reverse(
                'detalle',
                kwargs={'track_id': track.id_track},
            )
        )

        self.assertEqual(response.status_code, 200)

        url_preview = reverse(
            'reproducir_preview_track',
            kwargs={'track_id': track.id_track},
        )
        url_completo = reverse(
            'reproducir_track',
            kwargs={'track_id': track.id_track},
        )

        contenido = response.content.decode('utf-8')

        self.assertIn(f'src="{url_preview}"', contenido)
        self.assertNotIn(f'src="{url_completo}"', contenido)


    def test_dueno_del_track_usa_audio_completo_en_detalle(self):
        productor = User.objects.create_user(
            username='productor_dueno_audio',
            email='productor_dueno_audio@example.com',
            password='ClaveSegura123!',
        )
        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        track = Track.objects.create(
            nombre_track='Track del dueño',
            precio=5000,
            track=SimpleUploadedFile(
                'original.mp3',
                b'AUDIO_COMPLETO_DUENO',
                content_type='audio/mpeg',
            ),
            preview=SimpleUploadedFile(
                'preview.mp3',
                b'AUDIO_PREVIEW_DUENO',
                content_type='audio/mpeg',
            ),
            genero=genero,
            usuario=perfil_productor,
        )

        self.client.force_login(productor)

        response = self.client.get(
            reverse(
                'detalle',
                kwargs={'track_id': track.id_track},
            )
        )

        self.assertEqual(response.status_code, 200)

        url_completo = reverse(
            'reproducir_track',
            kwargs={'track_id': track.id_track},
        )
        url_preview = reverse(
            'reproducir_preview_track',
            kwargs={'track_id': track.id_track},
        )

        contenido = response.content.decode('utf-8')

        self.assertIn(f'src="{url_completo}"', contenido)
        self.assertNotIn(f'src="{url_preview}"', contenido)


    def test_comprador_del_track_usa_audio_completo_en_detalle(self):
        productor = User.objects.create_user(
            username='productor_para_comprador',
            email='productor_para_comprador@example.com',
            password='ClaveSegura123!',
        )
        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        comprador = User.objects.create_user(
            username='comprador_audio_completo',
            email='comprador_audio_completo@example.com',
            password='ClaveSegura123!',
        )
        Usuario.objects.create(
            user=comprador,
            tipo_usu=Usuario.ARTISTA,
        )

        genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        track = Track.objects.create(
            nombre_track='Track comprado',
            precio=5000,
            track=SimpleUploadedFile(
                'original.mp3',
                b'AUDIO_COMPLETO_COMPRADO',
                content_type='audio/mpeg',
            ),
            preview=SimpleUploadedFile(
                'preview.mp3',
                b'AUDIO_PREVIEW_COMPRADO',
                content_type='audio/mpeg',
            ),
            genero=genero,
            usuario=perfil_productor,
        )

        HistorialVenta.objects.create(
            comprador=comprador,
            precio=track.precio,
            track=track,
        )

        self.client.force_login(comprador)

        response = self.client.get(
            reverse(
                'detalle',
                kwargs={'track_id': track.id_track},
            )
        )

        self.assertEqual(response.status_code, 200)

        url_completo = reverse(
            'reproducir_track',
            kwargs={'track_id': track.id_track},
        )
        url_preview = reverse(
            'reproducir_preview_track',
            kwargs={'track_id': track.id_track},
        )

        contenido = response.content.decode('utf-8')

        self.assertIn(f'src="{url_completo}"', contenido)
        self.assertNotIn(f'src="{url_preview}"', contenido)


    def test_comando_genera_previews_faltantes(self):
        import io
        import tempfile
        import wave

        from django.core.management import call_command

        productor = User.objects.create_user(
            username='productor_comando_preview',
            email='productor_comando_preview@example.com',
            password='ClaveSegura123!',
        )
        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(8000)
            audio.writeframes(b'\x00\x00' * 8000 * 2)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                track = Track.objects.create(
                    nombre_track='Track antiguo sin preview',
                    precio=5000,
                    track=SimpleUploadedFile(
                        'track_antiguo.wav',
                        wav_buffer.getvalue(),
                        content_type='audio/wav',
                    ),
                    genero=genero,
                    usuario=perfil_productor,
                )

                self.assertFalse(track.preview.name)

                call_command('generar_previews')

                track.refresh_from_db()

                self.assertTrue(track.preview.name)
                self.assertTrue(track.preview.name.startswith('previews/'))


    def test_catalogo_artista_sin_compra_usa_preview(self):
        productor = User.objects.create_user(
            username='productor_catalogo_preview',
            email='productor_catalogo_preview@example.com',
            password='ClaveSegura123!',
        )
        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        artista = User.objects.create_user(
            username='artista_catalogo_preview',
            email='artista_catalogo_preview@example.com',
            password='ClaveSegura123!',
        )
        Usuario.objects.create(
            user=artista,
            tipo_usu=Usuario.ARTISTA,
        )

        genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        track = Track.objects.create(
            nombre_track='Track catálogo preview',
            precio=5000,
            track=SimpleUploadedFile(
                'original.mp3',
                b'AUDIO_COMPLETO_CATALOGO',
                content_type='audio/mpeg',
            ),
            preview=SimpleUploadedFile(
                'preview.mp3',
                b'AUDIO_PREVIEW_CATALOGO',
                content_type='audio/mpeg',
            ),
            genero=genero,
            usuario=perfil_productor,
        )

        self.client.force_login(artista)
        response = self.client.get(reverse('catalogo'))

        self.assertEqual(response.status_code, 200)

        url_preview = reverse(
            'reproducir_preview_track',
            kwargs={'track_id': track.id_track},
        )
        url_completo = reverse(
            'reproducir_track',
            kwargs={'track_id': track.id_track},
        )

        contenido = response.content.decode('utf-8')

        self.assertIn(f'src="{url_preview}"', contenido)
        self.assertNotIn(f'src="{url_completo}"', contenido)


    def test_catalogo_comprador_usa_audio_completo(self):
        productor = User.objects.create_user(
            username='productor_catalogo_comprado',
            email='productor_catalogo_comprado@example.com',
            password='ClaveSegura123!',
        )
        perfil_productor = Usuario.objects.create(
            user=productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        comprador = User.objects.create_user(
            username='comprador_catalogo_audio',
            email='comprador_catalogo_audio@example.com',
            password='ClaveSegura123!',
        )
        Usuario.objects.create(
            user=comprador,
            tipo_usu=Usuario.ARTISTA,
        )

        genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        track = Track.objects.create(
            nombre_track='Track comprado en catálogo',
            precio=5000,
            track=SimpleUploadedFile(
                'original.mp3',
                b'AUDIO_COMPLETO_CATALOGO_COMPRADO',
                content_type='audio/mpeg',
            ),
            preview=SimpleUploadedFile(
                'preview.mp3',
                b'AUDIO_PREVIEW_CATALOGO_COMPRADO',
                content_type='audio/mpeg',
            ),
            genero=genero,
            usuario=perfil_productor,
        )

        HistorialVenta.objects.create(
            comprador=comprador,
            precio=track.precio,
            track=track,
        )

        self.client.force_login(comprador)
        response = self.client.get(reverse('catalogo'))

        self.assertEqual(response.status_code, 200)

        url_completo = reverse(
            'reproducir_track',
            kwargs={'track_id': track.id_track},
        )
        url_preview = reverse(
            'reproducir_preview_track',
            kwargs={'track_id': track.id_track},
        )

        contenido = response.content.decode('utf-8')

        self.assertIn(f'src="{url_completo}"', contenido)
        self.assertNotIn(f'src="{url_preview}"', contenido)
