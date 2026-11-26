from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import encode_multipart

from app.api_shim import ser_track
from app.models import Genero_Musical, Track, Usuario
from app.r2_registration_guard import R2RegistrationGuardError


class R2CoverUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cover-producer",
            password="secret",
        )
        self.profile = Usuario.objects.create(
            user=self.user,
            tipo_usu=Usuario.PRODUCTOR,
        )
        self.genre = Genero_Musical.objects.create(
            descripcion="Pop",
        )
        self.track = Track.objects.create(
            nombre_track="Track de prueba",
            precio=1000,
            genero=self.genre,
            usuario=self.profile,
        )
        self.client.force_login(self.user)

    def patch_cover(self, data):
        # El boundary del cuerpo y el anunciado en Content-Type deben coincidir.
        boundary = "R2CoverBoundary"
        encoded = encode_multipart(boundary, data)
        return self.client.patch(
            f"/api/track/{self.track.pk}/",
            data=encoded,
            content_type=f"multipart/form-data; boundary={boundary}",
        )

    def test_serializador_devuelve_endpoint_para_portada_r2(self):
        self.track.r2_cover_key = (
            f"private/{self.user.pk}/cover/"
            + ("a" * 32)
            + ".png"
        )
        self.track.save(update_fields=["r2_cover_key"])

        payload = ser_track(self.track)

        self.assertEqual(
            payload["foto"],
            f"/api/track/{self.track.pk}/cover/",
        )
        self.assertNotIn("r2_cover_key", payload)

    def test_actualizacion_promueve_portada_y_limpia_la_anterior(self):
        old_key = (
            f"private/{self.user.pk}/cover/"
            + ("a" * 32)
            + ".png"
        )
        new_key = (
            f"private/{self.user.pk}/cover/"
            + ("b" * 32)
            + ".webp"
        )
        self.track.r2_cover_key = old_key
        self.track.save(update_fields=["r2_cover_key"])

        r2_client = Mock()
        draft = SimpleNamespace(private_key=new_key)

        with (
            patch("app.r2_presign.r2_uploads_enabled", return_value=True),
            patch(
                "app.r2_presign.r2_configuration",
                return_value={"R2_BUCKET_NAME": "beatcloud-test"},
            ),
            patch("app.r2_presign.r2_client", return_value=r2_client),
            patch("app.r2_upload_http._bucket", return_value="beatcloud-test"),
            patch("app.r2_registration_guard.validate_r2_cover_token"),
            patch(
                "app.r2_registration_prepare.prepare_r2_cover_upload",
                return_value=draft,
            ) as preparar,
            self.captureOnCommitCallbacks(execute=True),
        ):
            response = self.patch_cover(
                {
                    "nombre_track": "Track actualizado",
                    "cover_upload_token": "token-firmado",
                }
            )

        self.assertEqual(response.status_code, 200, response.content)
        self.track.refresh_from_db()
        self.assertEqual(self.track.nombre_track, "Track actualizado")
        self.assertEqual(self.track.r2_cover_key, new_key)
        self.assertEqual(
            response.json()["foto"],
            f"/api/track/{self.track.pk}/cover/",
        )
        preparar.assert_called_once()
        r2_client.delete_object.assert_called_once_with(
            Bucket="beatcloud-test",
            Key=old_key,
        )

    def test_token_invalido_no_actualiza_la_portada(self):
        original = self.track.r2_cover_key

        with (
            patch("app.r2_presign.r2_uploads_enabled", return_value=True),
            patch(
                "app.r2_registration_guard.validate_r2_cover_token",
                side_effect=R2RegistrationGuardError("token invalido"),
            ),
            patch(
                "app.r2_registration_prepare.prepare_r2_cover_upload"
            ) as preparar,
        ):
            response = self.patch_cover(
                {
                    "nombre_track": "No debe guardarse",
                    "cover_upload_token": "token-invalido",
                }
            )

        self.assertEqual(response.status_code, 400)
        self.track.refresh_from_db()
        self.assertEqual(self.track.nombre_track, "Track de prueba")
        self.assertEqual(self.track.r2_cover_key, original)
        preparar.assert_not_called()

    def preparar_cambio_portada(self):

        from contextlib import ExitStack

        old_key = (
            f"private/{self.user.pk}/cover/"
            + "a" * 32
            + ".png"
        )

        new_key = (
            f"private/{self.user.pk}/cover/"
            + "b" * 32
            + ".webp"
        )

        self.track.r2_cover_key = old_key
        self.track.save(update_fields=["r2_cover_key"])

        cloud = Mock()
        stack = ExitStack()
        self.addCleanup(stack.close)

        stack.enter_context(
            patch(
                "app.r2_presign.r2_uploads_enabled",
                return_value=True,
            )
        )

        stack.enter_context(
            patch(
                "app.r2_presign.r2_configuration",
                return_value={
                    "R2_BUCKET_NAME": "beatcloud-test",
                },
            )
        )

        stack.enter_context(
            patch(
                "app.r2_presign.r2_client",
                return_value=cloud,
            )
        )

        stack.enter_context(
            patch(
                "app.r2_upload_http._bucket",
                return_value="beatcloud-test",
            )
        )

        stack.enter_context(
            patch(
                "app.r2_registration_guard.validate_r2_cover_token"
            )
        )

        preparar_portada = stack.enter_context(
            patch(
                "app.r2_registration_prepare.prepare_r2_cover_upload",
                return_value=SimpleNamespace(
                    private_key=new_key,
                ),
            )
        )

        return (
            old_key,
            new_key,
            cloud,
            preparar_portada,
        )

    def test_portada_anterior_compartida_se_conserva(self):

        old_key, new_key, cloud, preparar = (
            self.preparar_cambio_portada()
        )

        otra = Track.objects.create(
            nombre_track="Otra cancion protegida",
            precio=1000,
            genero=self.genre,
            usuario=self.profile,
            r2_cover_key=old_key,
        )

        with self.captureOnCommitCallbacks(execute=True):

            respuesta = self.patch_cover({
                "cover_upload_token": "token-pruebas",
            })

            cloud.delete_object.assert_not_called()

        self.assertEqual(
            respuesta.status_code,
            200,
            respuesta.content,
        )

        self.track.refresh_from_db()
        otra.refresh_from_db()

        self.assertEqual(
            self.track.r2_cover_key,
            new_key,
        )

        self.assertEqual(
            otra.r2_cover_key,
            old_key,
        )

        preparar.assert_called_once()
        cloud.delete_object.assert_not_called()

    def test_rollback_conserva_portada_original(self):

        from django.db import transaction

        old_key, new_key, cloud, preparar = (
            self.preparar_cambio_portada()
        )

        with self.captureOnCommitCallbacks(
            execute=True
        ) as callbacks:

            with transaction.atomic():

                respuesta = self.patch_cover({
                    "nombre_track": "No debe persistir",
                    "cover_upload_token": "token-pruebas",
                })

                self.assertEqual(
                    respuesta.status_code,
                    200,
                    respuesta.content,
                )

                self.track.refresh_from_db()

                self.assertEqual(
                    self.track.r2_cover_key,
                    new_key,
                )

                cloud.delete_object.assert_not_called()

                transaction.set_rollback(True)

        self.assertEqual(callbacks, [])

        self.track.refresh_from_db()

        self.assertEqual(
            self.track.r2_cover_key,
            old_key,
        )

        self.assertEqual(
            self.track.nombre_track,
            "Track de prueba",
        )

        preparar.assert_called_once()
        cloud.delete_object.assert_not_called()

    def test_fallo_guardado_conserva_objetos(self):

        from django.db import DatabaseError

        old_key, _, cloud, preparar = (
            self.preparar_cambio_portada()
        )

        with self.captureOnCommitCallbacks(
            execute=True
        ) as callbacks:

            with patch(
                "app.api_shim.Track.save",
                side_effect=DatabaseError(
                    "Fallo simulado de PostgreSQL"
                ),
            ):

                with self.assertRaises(DatabaseError):

                    self.patch_cover({
                        "nombre_track": "No debe persistir",
                        "cover_upload_token": "token-pruebas",
                    })

        self.assertEqual(callbacks, [])

        self.track.refresh_from_db()

        self.assertEqual(
            self.track.r2_cover_key,
            old_key,
        )

        self.assertEqual(
            self.track.nombre_track,
            "Track de prueba",
        )

        preparar.assert_called_once()
        cloud.delete_object.assert_not_called()

    def test_track_retirado_no_permite_edicion(self):

        old_key, _, cloud, preparar = (
            self.preparar_cambio_portada()
        )

        Track.objects.filter(
            pk=self.track.pk
        ).update(is_retired=True)

        respuesta = self.patch_cover({
            "nombre_track": "No debe reactivarse",
            "cover_upload_token": "token-pruebas",
        })

        self.assertEqual(
            respuesta.status_code,
            409,
        )

        self.track.refresh_from_db()

        self.assertTrue(self.track.is_retired)

        self.assertEqual(
            self.track.nombre_track,
            "Track de prueba",
        )

        self.assertEqual(
            self.track.r2_cover_key,
            old_key,
        )

        preparar.assert_not_called()
        cloud.delete_object.assert_not_called()

    def test_cuenta_cerrada_no_edita_con_solicitud_antigua(self):

        import json

        from django.test import RequestFactory

        from app.api_shim import track_update_api

        from app.views import (
            _seudonimizar_identidad_cuenta,
        )

        old_key, _, cloud, preparar = (
            self.preparar_cambio_portada()
        )

        solicitud = RequestFactory().patch(
            f"/api/track/{self.track.pk}/",
            data=json.dumps({
                "nombre_track": "Edicion no autorizada",
                "cover_upload_token": "token-pruebas",
            }),
            content_type="application/json",
        )

        solicitud.user = self.user

        _seudonimizar_identidad_cuenta(
            self.profile
        )

        # Simular una reactivacion accidental.
        User.objects.filter(
            pk=self.user.pk
        ).update(is_active=True)

        respuesta = track_update_api(
            solicitud,
            self.track.pk,
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        self.track.refresh_from_db()

        self.assertEqual(
            self.track.nombre_track,
            "Track de prueba",
        )

        self.assertEqual(
            self.track.r2_cover_key,
            old_key,
        )

        preparar.assert_not_called()
        cloud.delete_object.assert_not_called()

    def test_actualiza_solo_campos_solicitados(self):

        guardar_original = Track.save

        with patch.object(
            Track,
            "save",
            autospec=True,
            side_effect=guardar_original,
        ) as guardar:

            respuesta = self.patch_cover({
                "nombre_track": "Nombre actualizado D10",
            })

        self.assertEqual(
            respuesta.status_code,
            200,
            respuesta.content,
        )

        guardar.assert_called_once()

        self.assertEqual(
            set(guardar.call_args.kwargs["update_fields"]),
            {"nombre_track"},
        )

        self.track.refresh_from_db()

        self.assertEqual(
            self.track.nombre_track,
            "Nombre actualizado D10",
        )

        self.assertEqual(
            self.track.precio,
            1000,
        )

        self.assertFalse(self.track.is_retired)
