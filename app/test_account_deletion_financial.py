import json
import re
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import Genero_Musical, HistorialVenta, Track, Usuario, WebpayTransaction


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class CierreCuentaWebpayTests(TestCase):
    CLAVE = 'ClaveSoloDePrueba123!'

    def usuario(self, nombre, tipo=Usuario.ARTISTA):
        user = User.objects.create_user(
            username=nombre, password=self.CLAVE, email=f'{nombre}@example.com'
        )
        Usuario.objects.create(user=user, tipo_usu=tipo)
        return user

    def orden(self, user, referencia, estado, entregada=False):
        return WebpayTransaction.objects.create(
            user=user, buy_order=f'cierre-{referencia}',
            session_id=f'sesion-{referencia}', amount='1190.00',
            status=estado,
            fulfilled_at=timezone.now() if entregada else None,
        )

    def codigo(self, user):
        self.client.force_login(user)
        respuesta = self.client.post(reverse('eliminar_cuenta'), {
            'password': self.CLAVE
        })
        self.assertEqual(respuesta.status_code, 200)
        hallado = re.search(r'\b(\d{6})\b', mail.outbox[-1].body)
        self.assertIsNotNone(hallado)
        return hallado.group(1)

    def test_ordenes_terminales_se_conservan(self):
        user = self.usuario('usuario_terminal')
        autorizado = self.orden(user, 'autorizado', 'AUTHORIZED', entregada=True)
        cancelado = self.orden(user, 'cancelado', 'CANCELLED')
        otro = self.usuario('productor_ajeno', Usuario.PRODUCTOR)
        orden_ajena = self.orden(otro, 'ajena', 'AUTHORIZED', entregada=True)
        codigo = self.codigo(user)
        respuesta = self.client.post(reverse('confirmar_eliminacion_cuenta'), {
            'codigo': codigo
        })
        self.assertEqual(respuesta.status_code, 200)
        cuenta = User.objects.get(pk=user.pk)

        self.assertFalse(cuenta.is_active)
        self.assertFalse(cuenta.has_usable_password())
        self.assertEqual(cuenta.email, "")

        self.assertTrue(
            Usuario.objects.filter(
                user_id=user.pk,
                cuenta_cerrada_en__isnull=False,
            ).exists()
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

        for anterior_pago in (autorizado, cancelado):

            pago = WebpayTransaction.objects.get(
                pk=anterior_pago.pk
            )

            self.assertEqual(pago.user_id, user.pk)
            self.assertEqual(str(pago.amount), "1190.00")
            self.assertEqual(pago.status, anterior_pago.status)
            self.assertEqual(pago.buy_order, anterior_pago.buy_order)
            self.assertEqual(pago.session_id, anterior_pago.session_id)
            self.assertEqual(pago.fulfilled_at, anterior_pago.fulfilled_at)
            self.assertEqual(pago.cart_snapshot, anterior_pago.cart_snapshot)
        self.assertTrue(User.objects.filter(pk=otro.pk).exists())
        orden_ajena.refresh_from_db()
        self.assertEqual(orden_ajena.user_id, otro.pk)

    def test_orden_pendiente_bloquea_cierre_web(self):
        user = self.usuario('usuario_pendiente')
        pago = self.orden(user, 'pendiente', 'PENDING')
        codigo = self.codigo(user)
        respuesta = self.client.post(reverse('confirmar_eliminacion_cuenta'), {
            'codigo': codigo
        })
        self.assertEqual(respuesta.status_code, 409)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        pago.refresh_from_db()
        self.assertEqual(pago.user_id, user.pk)

    def test_autorizada_sin_entrega_bloquea_cierre(self):
        user = self.usuario('usuario_sin_entrega')
        pago = self.orden(user, 'sin-entrega', 'AUTHORIZED', entregada=False)
        codigo = self.codigo(user)
        respuesta = self.client.post(reverse('confirmar_eliminacion_cuenta'), {
            'codigo': codigo
        })
        self.assertEqual(respuesta.status_code, 409)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertTrue(WebpayTransaction.objects.filter(pk=pago.pk).exists())

    def test_orden_pendiente_bloquea_cierre_api(self):
        user = self.usuario('usuario_api')
        pago = self.orden(user, 'api', 'PENDING')
        self.client.force_login(user)
        sesion = self.client.session
        sesion['eliminar_cuenta_codigo_hash'] = make_password('123456')
        sesion['eliminar_cuenta_usuario_id'] = user.pk
        sesion['eliminar_cuenta_codigo_creado'] = timezone.now().timestamp()
        sesion['eliminar_cuenta_intentos'] = 0
        sesion.save()
        respuesta = self.client.post(
            reverse('api_account_deletion_confirm'),
            data=json.dumps({'codigo': '123456'}),
            content_type='application/json',
        )
        self.assertEqual(respuesta.status_code, 409)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        pago.refresh_from_db()
        self.assertEqual(pago.user_id, user.pk)

    def test_str_venta_sin_comprador(self):
        producer = self.usuario('test_creador', Usuario.PRODUCTOR)
        genero = Genero_Musical.objects.create(descripcion=Genero_Musical.POP)
        track = Track.objects.create(
            nombre_track='Prueba', precio=1000,
            track='canciones/prueba.mp3', genero=genero,
            usuario=Usuario.objects.get(user=producer),
        )
        venta = HistorialVenta.objects.create(
            comprador=None, precio=1000, track=track,
        )
        self.assertIn('Usuario eliminado', str(venta))
