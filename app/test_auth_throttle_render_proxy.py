"""Verificacion de IP tras proxies de Render."""

import os
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from .auth_throttle import _bucket_key


class RenderProxyThrottleTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

        environment = patch.dict(
            os.environ,
            {
                "AUTH_TRUST_RENDER_CF_IP": "0",
                "RENDER_SERVICE_ID": "",
            },
        )
        environment.start()
        self.addCleanup(environment.stop)

    def request(self, remote="8.8.8.8", cf=None, xff=None):
        meta = {"REMOTE_ADDR": remote}

        if cf is not None:
            meta["HTTP_CF_CONNECTING_IP"] = cf

        if xff is not None:
            meta["HTTP_X_FORWARDED_FOR"] = xff

        return self.factory.post(
            "/api/auth/login/",
            **meta,
        )

    def key(self, request):
        return _bucket_key(request, "cuenta_objetivo")

    def test_local_uses_remote_addr(self):
        a = self.request(remote="8.8.8.8")
        b = self.request(remote="1.1.1.1")

        self.assertNotEqual(self.key(a), self.key(b))

    def test_local_ignores_spoofed_xff(self):
        a = self.request(xff="1.1.1.1")
        b = self.request(xff="9.9.9.9")

        self.assertEqual(self.key(a), self.key(b))

    def test_local_ignores_cf_header(self):
        a = self.request(cf="1.1.1.1")
        b = self.request(cf="9.9.9.9")

        self.assertEqual(self.key(a), self.key(b))

    def test_requires_render_service_id(self):
        with patch.dict(
            os.environ,
            {"AUTH_TRUST_RENDER_CF_IP": "1"},
        ):
            a = self.request(cf="1.1.1.1")
            b = self.request(cf="9.9.9.9")

            self.assertEqual(self.key(a), self.key(b))

    def test_requires_explicit_opt_in(self):
        with patch.dict(
            os.environ,
            {"RENDER_SERVICE_ID": "srv-test"},
        ):
            a = self.request(cf="1.1.1.1")
            b = self.request(cf="9.9.9.9")

            self.assertEqual(self.key(a), self.key(b))

    def test_render_separates_visitors(self):
        with patch.dict(
            os.environ,
            {
                "AUTH_TRUST_RENDER_CF_IP": "1",
                "RENDER_SERVICE_ID": "srv-test",
            },
        ):
            a = self.request(
                remote="10.0.0.5",
                cf="1.1.1.1",
            )
            b = self.request(
                remote="10.0.0.5",
                cf="8.8.8.8",
            )

            self.assertNotEqual(self.key(a), self.key(b))

    def test_render_ignores_xff(self):
        with patch.dict(
            os.environ,
            {
                "AUTH_TRUST_RENDER_CF_IP": "1",
                "RENDER_SERVICE_ID": "srv-test",
            },
        ):
            a = self.request(
                cf="1.1.1.1",
                xff="9.9.9.9",
            )
            b = self.request(
                cf="1.1.1.1",
                xff="8.8.8.8",
            )

            self.assertEqual(self.key(a), self.key(b))

    def test_invalid_cf_falls_back(self):
        with patch.dict(
            os.environ,
            {
                "AUTH_TRUST_RENDER_CF_IP": "1",
                "RENDER_SERVICE_ID": "srv-test",
            },
        ):
            original = self.request(
                remote="8.8.8.8",
            )
            invalid = self.request(
                remote="8.8.8.8",
                cf="direccion-invalida",
            )
            private = self.request(
                remote="8.8.8.8",
                cf="192.168.1.10",
            )

            self.assertEqual(
                self.key(original),
                self.key(invalid),
            )
            self.assertEqual(
                self.key(original),
                self.key(private),
            )

    def test_actor_scope_ignores_ip_changes(self):
        with patch.dict(
            os.environ,
            {
                "AUTH_TRUST_RENDER_CF_IP": "1",
                "RENDER_SERVICE_ID": "srv-test",
            },
        ):
            a = self.request(cf="1.1.1.1")
            b = self.request(cf="8.8.8.8")

            actor = SimpleNamespace(
                is_authenticated=True,
                pk=123,
            )
            a.user = actor
            b.user = actor

            self.assertEqual(
                _bucket_key(
                    a,
                    "cuenta_objetivo",
                    actor_scoped=True,
                ),
                _bucket_key(
                    b,
                    "cuenta_objetivo",
                    actor_scoped=True,
                ),
            )
