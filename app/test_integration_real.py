"""API real DDPB-81: prueba aislada sin transacciones externas.

Se ejecuta exclusivamente con `python manage.py test`, que crea una base
separada. El envio de correo se sustituye por locmem y Webpay por un mock.
"""
import json
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.files.base import ContentFile
from django.test import Client, TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Genero_Musical, HistorialCompra, Track, Usuario, Venta, WebpayTransaction


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ApiRealFlowTests(TestCase):
    def setUp(self):
        self.archivos = tempfile.TemporaryDirectory(prefix='beatcloud_api_test_')
        self.addCleanup(self.archivos.cleanup)
        entorno = override_settings(MEDIA_ROOT=self.archivos.name)
        entorno.enable()
        self.addCleanup(entorno.disable)

        self.client = Client(enforce_csrf_checks=True)
        self.productor = User.objects.create_user(
            username='api_prod_test', password='TestSegura_2026!X', is_active=True
        )
        self.perfil_productor = Usuario.objects.create(
            user=self.productor, tipo_usu=Usuario.PRODUCTOR,
            nombre_artistico='Productor Prueba'
        )
        self.comprador = User.objects.create_user(
            username='api_artist_test', password='TestSegura_2026!X', is_active=True
        )
        self.perfil_comprador = Usuario.objects.create(
            user=self.comprador, tipo_usu=Usuario.ARTISTA,
            nombre_artistico='Artista Prueba'
        )
        self.genero = Genero_Musical.objects.create(descripcion='Rock')
        self.pagada = Track.objects.create(
            nombre_track='Beat Test Local', precio=1000,
            genero=self.genero, usuario=self.perfil_productor
        )
        self.pagada.track.save('beat_prueba.wav', ContentFile(b'RIFF TEST DATA'), save=True)
        self.gratis = Track.objects.create(
            nombre_track='Beat Gratis Local', precio=0,
            genero=self.genero, usuario=self.perfil_productor,
            allow_free_download=True
        )
        self.gratis.track.save('beat_gratis.wav', ContentFile(b'RIFF FREE DATA'), save=True)

    def csrf(self):
        response = self.client.get('/api/csrf/')
        self.assertEqual(response.status_code, 200)
        return response.json()['detail']

    def post_json(self, ruta, datos):
        return self.client.post(
            ruta, data=json.dumps(datos), content_type='application/json',
            HTTP_X_CSRFTOKEN=self.csrf()
        )

    def login_comprador(self):
        respuesta = self.post_json('/api/auth/login/', {
            'username': 'api_artist_test', 'password': 'TestSegura_2026!X'
        })
        self.assertEqual(respuesta.status_code, 200, respuesta.content[:350])
        self.assertEqual(self.client.get('/api/session/').json()['username'], 'api_artist_test')

    def test_01_registro_activacion_y_login(self):
        data = {
            'username': 'registro_api_prueba',
            'first_name': 'Prueba', 'last_name': 'Local',
            'email': 'registro-api@example.invalid',
            'password1': 'PruebaSegura_2026!X',
            'password2': 'PruebaSegura_2026!X',
            'nombre_artistico': 'Artista Registro',
            'tipo_usu': str(Usuario.ARTISTA),
        }
        respuesta = self.client.post(
            '/api/auth/registro/', data=data, HTTP_X_CSRFTOKEN=self.csrf()
        )
        self.assertEqual(respuesta.status_code, 201, respuesta.content[:350])
        cuenta = User.objects.get(username='registro_api_prueba')
        self.assertFalse(cuenta.is_active)
        self.assertEqual(cuenta.usuario.tipo_usu, Usuario.ARTISTA)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            self.post_json('/api/auth/login/', {
                'username': cuenta.username, 'password': data['password1']
            }).status_code,
            403,
        )
        uid = urlsafe_base64_encode(force_bytes(cuenta.pk))
        token = default_token_generator.make_token(cuenta)
        respuesta = self.post_json('/api/auth/activar/', {
            'uidb64': uid, 'token': token
        })
        self.assertEqual(respuesta.status_code, 200, respuesta.content[:350])
        respuesta = self.post_json('/api/auth/login/', {
            'username': cuenta.username, 'password': data['password1']
        })
        self.assertEqual(respuesta.status_code, 200, respuesta.content[:350])
        self.assertEqual(self.client.get('/api/session/').json()['username'], cuenta.username)
        respuesta = self.client.post('/api/auth/logout/', HTTP_X_CSRFTOKEN=self.csrf())
        self.assertEqual(respuesta.status_code, 200)
        self.assertIsNone(self.client.get('/api/session/').json())

    def test_02_catalogo_y_filtros_reales(self):
        respuesta = self.client.get('/api/catalogo/?q=Beat&orden=precio_menor')
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertIn('tracks', datos)
        self.assertIn('total_resultados', datos)
        ids = {item['id_track'] for item in datos['tracks']}
        self.assertIn(self.pagada.pk, ids)
        self.assertIn(self.gratis.pk, ids)
        for item in datos['tracks']:
            self.assertIn('precio', item)
            self.assertIn('usuario', item)
            self.assertIn('genero', item)
            self.assertIn('is_purchased', item)

    def test_03_carrito_totales_y_eliminacion(self):
        self.assertEqual(self.client.get('/api/carrito/').status_code, 401)
        self.login_comprador()
        respuesta = self.client.get('/api/carrito/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['total'], 0)
        ruta = f'/api/carrito/agregar/{self.pagada.pk}/'
        respuesta = self.client.post(ruta, HTTP_X_CSRFTOKEN=self.csrf())
        self.assertEqual(respuesta.status_code, 201, respuesta.content[:350])
        venta_id = respuesta.json()['id']
        self.assertEqual(
            self.client.post(ruta, HTTP_X_CSRFTOKEN=self.csrf()).status_code, 409
        )
        datos = self.client.get('/api/carrito/').json()
        self.assertEqual((datos['subtotal'], datos['iva'], datos['total']), (1000, 190, 1190))
        respuesta = self.client.delete(
            f'/api/carrito/{venta_id}/', HTTP_X_CSRFTOKEN=self.csrf()
        )
        self.assertEqual(respuesta.status_code, 200, respuesta.content[:350])
        self.assertEqual(self.client.get('/api/carrito/').json()['items'], [])

    def test_04_pago_no_inicia_si_carrito_vacio(self):
        self.assertEqual(self.post_json('/api/pago/', {}).status_code, 401)
        self.login_comprador()
        self.assertEqual(self.post_json('/api/pago/', {}).status_code, 400)
        self.assertEqual(WebpayTransaction.objects.count(), 0)

    def test_05_inicio_pago_con_webpay_sustituido(self):
        self.login_comprador()
        self.assertEqual(
            self.client.post(
                f'/api/carrito/agregar/{self.pagada.pk}/',
                HTTP_X_CSRFTOKEN=self.csrf()
            ).status_code, 201
        )
        # Impide la solicitud externa a Transbank. Solo simula su respuesta.
        with patch('app.api_shim._webpay_tx') as cliente_webpay:
            cliente_webpay.return_value.create.return_value = {
                'url': 'https://example.invalid/webpay-simulacion',
                'token': 'token_prueba_sin_valor_real',
            }
            respuesta = self.post_json('/api/pago/', {})
            self.assertEqual(respuesta.status_code, 200, respuesta.content[:350])
            cliente_webpay.return_value.create.assert_called_once()
        datos = respuesta.json()
        self.assertEqual(datos['amount'], 1190)
        self.assertEqual(datos['token_ws'], 'token_prueba_sin_valor_real')
        self.assertNotIn('session_id', datos)
        orden = WebpayTransaction.objects.get(pk=datos['transaction_id'])
        self.assertEqual(int(orden.amount), 1190)
        self.assertEqual(orden.user, self.comprador)
        self.assertEqual(len(orden.cart_snapshot), 1)
        self.assertEqual(Venta.objects.filter(usuario_id=self.perfil_comprador).count(), 1)
        self.assertFalse(HistorialCompra.objects.filter(usuario=self.perfil_comprador).exists())

    def test_06_descarga_protegida_y_compra_ficticia(self):
        ruta = f'/api/track/{self.pagada.pk}/descargar/'
        self.assertEqual(self.client.get(ruta).status_code, 403)
        self.login_comprador()
        self.assertEqual(self.client.get(ruta).status_code, 403)
        # La compra solo existe en la base de TEST, no en PostgreSQL real.
        HistorialCompra.objects.create(usuario=self.perfil_comprador, track=self.pagada)
        respuesta = self.client.get(ruta)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('attachment', respuesta.get('Content-Disposition', ''))
        self.assertEqual(b''.join(respuesta.streaming_content), b'RIFF TEST DATA')

    def test_07_track_gratis_y_descarga(self):
        self.login_comprador()
        ruta = f'/api/track/{self.gratis.pk}/claim-free/'
        respuesta = self.client.post(ruta, HTTP_X_CSRFTOKEN=self.csrf())
        self.assertEqual(respuesta.status_code, 200, respuesta.content[:350])
        self.assertTrue(HistorialCompra.objects.filter(
            usuario=self.perfil_comprador, track=self.gratis
        ).exists())
        respuesta = self.client.get(f'/api/track/{self.gratis.pk}/descargar/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(b''.join(respuesta.streaming_content), b'RIFF FREE DATA')
