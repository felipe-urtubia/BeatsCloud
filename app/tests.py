import re

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

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
