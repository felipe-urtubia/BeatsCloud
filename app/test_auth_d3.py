"""D3: verificaciones aisladas de login/logout/CSRF/expiracion de sesion."""
import json
from django.contrib.auth.models import User
from django.test import Client, TestCase


class DjangoSessionAuthD3Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='d3_tester', password='d3-strong-test-password', is_active=True
        )
        self.client = Client(enforce_csrf_checks=True)

    def _csrf(self):
        response = self.client.get('/api/csrf/')
        self.assertEqual(response.status_code, 200)
        return response.json()['detail']

    def _login(self):
        csrf = self._csrf()
        return self.client.post(
            '/api/auth/login/',
            data=json.dumps({'username': 'd3_tester', 'password': 'd3-strong-test-password'}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )

    def test_anonymous_session_and_protected_purchase_route(self):
        response = self.client.get('/api/session/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json())
        self.assertEqual(self.client.get('/api/mis-compras/').status_code, 401)

    def test_login_requires_csrf(self):
        response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({'username': 'd3_tester', 'password': 'd3-strong-test-password'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
        self.assertIsNone(self.client.get('/api/session/').json())

    def test_bad_password_never_creates_session(self):
        csrf = self._csrf()
        response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({'username': 'd3_tester', 'password': 'wrong'}),
            content_type='application/json', HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, 401)
        self.assertIsNone(self.client.get('/api/session/').json())

    def test_login_and_logout(self):
        response = self._login()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/api/session/').json()['username'], 'd3_tester')
        csrf_after_login = self._csrf()
        response = self.client.post('/api/auth/logout/', HTTP_X_CSRFTOKEN=csrf_after_login)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.client.get('/api/session/').json())

    def test_expired_session_revokes_protected_access(self):
        self.assertEqual(self._login().status_code, 200)
        self.assertEqual(self.client.get('/api/session/').status_code, 200)
        self.client.session.flush()
        self.assertIsNone(self.client.get('/api/session/').json())
        self.assertEqual(self.client.get('/api/mis-compras/').status_code, 401)
