import json
import os
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.test import (
    Client,
    TestCase,
    override_settings,
)

from app.models import Usuario
from app.r2_presign import ALLOWED, TOKEN_SALT
from app.r2_upload_workflow import (
    R2UploadWorkflowConflict,
)


@override_settings(
    ROOT_URLCONF="app.r2_upload_http"
)
class R2UploadHTTPTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="productor_http_r2",
            password="clave-de-prueba",
        )

        self.perfil = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.client = Client(
            enforce_csrf_checks=True
        )

        self.client.force_login(self.user)

        self.csrf = "a" * 32

        self.client.cookies[
            settings.CSRF_COOKIE_NAME
        ] = self.csrf

        self.url = "/api/r2/finalize/"

        self.mime = sorted(
            ALLOWED["track"][".wav"]
        )[0]

        self.token = signing.dumps(
            {
                "owner": self.user.pk,
                "key": (
                    f"pending/{self.user.pk}/track/"
                    + ("a" * 32)
                    + ".wav"
                ),
                "size": 16044,
                "kind": "track",
                "mime": self.mime,
            },
            salt=TOKEN_SALT,
        )

        self.datos = {
            "upload_token": self.token,
            "nombre_track": "Beat de prueba",
            "precio": 1000,
            "genero_id": 1,
        }

    def publicar(
        self,
        *,
        csrf=True,
        datos=None,
        cliente=None,
    ):
        cliente = cliente or self.client

        argumentos = {}

        if csrf:
            argumentos["HTTP_X_CSRFTOKEN"] = self.csrf

        return cliente.post(
            self.url,
            data=json.dumps(
                self.datos if datos is None else datos
            ),
            content_type="application/json",
            **argumentos,
        )

    def test_desactivado_no_ejecuta_workflow(self):
        with (
            patch.dict(
                os.environ,
                {"R2_UPLOADS_ENABLED": "false"},
            ),
            patch(
                "app.r2_upload_http.complete_r2_track_upload"
            ) as ejecutar,
        ):
            respuesta = self.publicar()

        self.assertEqual(
            respuesta.status_code,
            503,
        )
        ejecutar.assert_not_called()

    def test_metodo_get_rechazado(self):
        respuesta = self.client.get(self.url)

        self.assertEqual(
            respuesta.status_code,
            405,
        )

    def test_csrf_obligatorio(self):
        with patch.dict(
            os.environ,
            {"R2_UPLOADS_ENABLED": "true"},
        ):
            respuesta = self.publicar(
                csrf=False
            )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    def test_anonimo_no_puede_registrar(self):
        anonimo = Client(
            enforce_csrf_checks=True
        )

        anonimo.cookies[
            settings.CSRF_COOKIE_NAME
        ] = self.csrf

        with patch.dict(
            os.environ,
            {"R2_UPLOADS_ENABLED": "true"},
        ):
            respuesta = self.publicar(
                cliente=anonimo
            )

        self.assertEqual(
            respuesta.status_code,
            401,
        )

    def test_usuario_no_productor_rechazado(self):
        self.perfil.tipo_usu = 0
        self.perfil.save(
            update_fields=["tipo_usu"]
        )

        with patch.dict(
            os.environ,
            {"R2_UPLOADS_ENABLED": "true"},
        ):
            respuesta = self.publicar()

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    def test_json_invalido(self):
        with patch.dict(
            os.environ,
            {"R2_UPLOADS_ENABLED": "true"},
        ):
            respuesta = self.client.post(
                self.url,
                data="{json-invalido",
                content_type="application/json",
                HTTP_X_CSRFTOKEN=self.csrf,
            )

        self.assertEqual(
            respuesta.status_code,
            400,
        )

    def test_token_invalido_no_conecta_r2(self):
        datos = dict(self.datos)
        datos["upload_token"] = "token-invalido"

        with (
            patch.dict(
                os.environ,
                {"R2_UPLOADS_ENABLED": "true"},
            ),
            patch(
                "app.r2_upload_http.r2_client"
            ) as crear_cliente,
        ):
            respuesta = self.publicar(
                datos=datos
            )

        self.assertEqual(
            respuesta.status_code,
            400,
        )
        crear_cliente.assert_not_called()

    def test_bucket_ausente_rechazado(self):
        with (
            patch.dict(
                os.environ,
                {
                    "R2_UPLOADS_ENABLED": "true",
                    "R2_BUCKET_NAME": "",
                    "R2_BUCKET": "",
                },
            ),
            patch(
                "app.r2_upload_http.r2_configuration",
                return_value={},
            ),
            patch(
                "app.r2_upload_http.r2_client"
            ) as crear_cliente,
        ):
            respuesta = self.publicar()

        self.assertEqual(
            respuesta.status_code,
            503,
        )
        crear_cliente.assert_not_called()

    def test_solicitud_valida_regresa_201(self):
        cancion = Mock()
        cancion.pk = 77

        with (
            patch.dict(
                os.environ,
                {"R2_UPLOADS_ENABLED": "true"},
            ),
            patch(
                "app.r2_upload_http.r2_configuration",
                return_value={
                    "R2_BUCKET_NAME": "beatcloud-media",
                },
            ),
            patch(
                "app.r2_upload_http.r2_client",
                return_value=object(),
            ),
            patch(
                "app.r2_upload_http.complete_r2_track_upload",
                return_value=cancion,
            ) as ejecutar,
        ):
            respuesta = self.publicar()

        self.assertEqual(
            respuesta.status_code,
            201,
        )

        self.assertEqual(
            respuesta.json()["id_track"],
            77,
        )

        ejecutar.assert_called_once()

    def test_registro_duplicado_regresa_409(self):
        with (
            patch.dict(
                os.environ,
                {"R2_UPLOADS_ENABLED": "true"},
            ),
            patch(
                "app.r2_upload_http.r2_configuration",
                return_value={
                    "R2_BUCKET_NAME": "beatcloud-media",
                },
            ),
            patch(
                "app.r2_upload_http.r2_client",
                return_value=object(),
            ),
            patch(
                "app.r2_upload_http.complete_r2_track_upload",
                side_effect=R2UploadWorkflowConflict(
                    "Duplicado simulado"
                ),
            ),
        ):
            respuesta = self.publicar()

        self.assertEqual(
            respuesta.status_code,
            409,
        )
