"""Proteccion de autorizaciones R2 frente al cierre de cuentas."""

import json

from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core import signing
from django.test import TestCase, RequestFactory

from app.models import Usuario, R2UploadClaim

from app.r2_presign import (
    ALLOWED,
    TOKEN_SALT,
    r2_presign_upload_api,
    r2_confirm_upload_api,
)

from app.views import (
    _seudonimizar_identidad_cuenta,
)


class R2PresignClosureTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="d10_r2_presign_closure",
            password="Solo-Pruebas-Presign-D10!",
        )

        self.perfil = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.factory = RequestFactory()

        self.cloud = Mock()

        self.cloud.generate_presigned_url.return_value = (
            "https://example.invalid/upload-test"
        )

        self.config = {
            "R2_BUCKET_NAME": "bucket-exclusivo-pruebas",
        }

    def datos(self, kind):

        extension = {
            "track": ".wav",
            "cover": ".jpg",
            "stems": ".zip",
        }[kind]

        mime = sorted(
            ALLOWED[kind][extension]
        )[0]

        payload = {
            "kind": kind,
            "filename": "archivo" + extension,
            "size": 16044,
            "content_type": mime,
        }

        token = signing.dumps(
            {
                "owner": self.user.pk,
                "key": (
                    f"pending/{self.user.pk}/{kind}/"
                    + "a" * 32
                    + extension
                ),
                "size": 16044,
                "kind": kind,
                "mime": mime,
            },
            salt=TOKEN_SALT,
        )

        return payload, token

    def solicitud(self, endpoint, body):

        request = self.factory.post(
            "/api/r2/prueba/",
            data=json.dumps(body),
            content_type="application/json",
        )

        # Solo en pruebas: simular una solicitud autenticada
        # antes del cierre, con una instancia antigua de User.
        request.user = self.user
        request._dont_enforce_csrf_checks = True

        with (
            patch(
                "app.r2_presign.r2_uploads_enabled",
                return_value=True,
            ),
            patch(
                "app.r2_presign.r2_configuration",
                return_value=self.config,
            ) as configuracion,
            patch(
                "app.r2_presign.r2_client",
                return_value=self.cloud,
            ) as cliente,
        ):

            respuesta = endpoint(request)

            if respuesta.status_code == 403:

                configuracion.assert_not_called()
                cliente.assert_not_called()

        return respuesta

    def cerrar(self):

        _seudonimizar_identidad_cuenta(
            self.perfil
        )

    def test_cuenta_cerrada_no_emite_autorizaciones(self):

        datos = [
            self.datos(kind)
            for kind in ("track", "cover", "stems")
        ]

        self.cerrar()

        # Incluso si se restaura is_active accidentalmente,
        # el estado persistente debe prevalecer.
        User.objects.filter(
            pk=self.user.pk
        ).update(is_active=True)

        for payload, _ in datos:

            with self.subTest(kind=payload["kind"]):

                respuesta = self.solicitud(
                    r2_presign_upload_api,
                    payload,
                )

                self.assertEqual(
                    respuesta.status_code,
                    403,
                )

                self.assertNotIn(
                    "url",
                    json.loads(respuesta.content),
                )

        self.cloud.generate_presigned_url.assert_not_called()
        self.cloud.head_object.assert_not_called()

        self.assertFalse(
            R2UploadClaim.objects.filter(
                owner_id=self.user.pk
            ).exists()
        )

    def test_cuenta_cerrada_no_confirma_tokens_anteriores(self):

        datos = [
            self.datos(kind)
            for kind in ("track", "cover", "stems")
        ]

        self.cerrar()

        User.objects.filter(
            pk=self.user.pk
        ).update(is_active=True)

        for payload, token in datos:

            with self.subTest(kind=payload["kind"]):

                respuesta = self.solicitud(
                    r2_confirm_upload_api,
                    {"upload_token": token},
                )

                self.assertEqual(
                    respuesta.status_code,
                    403,
                )

        self.cloud.head_object.assert_not_called()
        self.cloud.generate_presigned_url.assert_not_called()

    def test_instancia_antigua_no_autoriza_cuenta_inactiva(self):

        payload, token = self.datos("track")

        User.objects.filter(
            pk=self.user.pk
        ).update(is_active=False)

        # La instancia de la solicitud mantiene su estado antiguo.
        self.assertTrue(self.user.is_active)

        for endpoint, body in (
            (r2_presign_upload_api, payload),
            (r2_confirm_upload_api, {"upload_token": token}),
        ):

            with self.subTest(endpoint=endpoint.__name__):

                respuesta = self.solicitud(
                    endpoint,
                    body,
                )

                self.assertEqual(
                    respuesta.status_code,
                    403,
                )

        self.cloud.generate_presigned_url.assert_not_called()
        self.cloud.head_object.assert_not_called()

    def test_productor_activo_conserva_autorizaciones(self):

        for kind in ("track", "cover", "stems"):

            with self.subTest(kind=kind):

                payload, token = self.datos(kind)

                respuesta = self.solicitud(
                    r2_presign_upload_api,
                    payload,
                )

                self.assertEqual(
                    respuesta.status_code,
                    200,
                    respuesta.content,
                )

                contenido = json.loads(
                    respuesta.content
                )

                self.assertEqual(
                    contenido["expires_in"],
                    3600,
                )

                self.assertEqual(
                    respuesta["Cache-Control"],
                    "no-store",
                )

                self.cloud.head_object.return_value = {
                    "ContentLength": payload["size"],
                    "ContentType": payload["content_type"],
                }

                respuesta = self.solicitud(
                    r2_confirm_upload_api,
                    {"upload_token": token},
                )

                self.assertEqual(
                    respuesta.status_code,
                    200,
                    respuesta.content,
                )

                self.assertTrue(
                    json.loads(respuesta.content)["verified"]
                )

                self.assertEqual(
                    respuesta["Cache-Control"],
                    "no-store",
                )

        self.assertEqual(
            self.cloud.generate_presigned_url.call_count,
            3,
        )

        self.assertEqual(
            self.cloud.head_object.call_count,
            3,
        )

        self.assertFalse(
            R2UploadClaim.objects.filter(
                owner_id=self.user.pk
            ).exists()
        )
