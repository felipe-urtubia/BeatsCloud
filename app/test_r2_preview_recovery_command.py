from io import StringIO
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from django.test import TestCase

from app.models import Genero_Musical, Track, Usuario


CONFIRMACION = "RECUPERAR_SOLO_PREVIEWS_R2"


class R2PreviewRecoveryCommandTests(TestCase):

    def setUp(self):
        user = User.objects.create_user(
            username="comando_recuperacion",
            password="password-de-prueba",
        )

        self.perfil = Usuario.objects.create(
            user=user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.genero = Genero_Musical.objects.create(
            descripcion="Pop",
        )

        self.private_key = (
            f"private/{user.pk}/track/"
            + "a" * 32 + ".wav"
        )

        self.preview_key = (
            "previews/r2-" + "b" * 32 + ".mp3"
        )

        self.track = Track.objects.create(
            nombre_track="Prueba de recuperacion",
            precio=1000,
            usuario=self.perfil,
            genero=self.genero,
            storage_backend="r2",
            media_status="ready",
            r2_owner_user_id=user.pk,
            r2_object_key=self.private_key,
            preview="previews/antigua.mp3",
        )

        self.r2 = Mock()
        self.r2.head_object.side_effect = self._head

        self.configuracion = self._patch(
            "app.management.commands.recuperar_previews_r2.r2_configuration",
            return_value={"R2_BUCKET_NAME": "bucket-prueba"},
        )

        self.cliente = self._patch(
            "app.management.commands.recuperar_previews_r2.r2_client",
            return_value=self.r2,
        )

        self.motor = self._patch(
            "app.r2_preview_recovery.recover_track_preview",
            return_value={
                "status": "recuperada",
                "key": self.preview_key,
            },
        )

    def _patch(self, nombre, **kwargs):
        parche = patch(nombre, **kwargs)
        simulado = parche.start()
        self.addCleanup(parche.stop)
        return simulado

    def _head(self, **kwargs):
        self.assertEqual(
            kwargs["Bucket"], "bucket-prueba"
        )

        if kwargs["Key"] == self.private_key:
            return {
                "ContentLength": 100000,
                "ContentType": "audio/wav",
            }

        if kwargs["Key"] == self.preview_key:
            return {
                "ContentLength": 5000,
                "ContentType": "audio/mpeg",
            }

        raise AssertionError(
            "Consulta inesperada a R2."
        )

    def _ejecutar(self, *argumentos):
        salida = StringIO()

        call_command(
            "recuperar_previews_r2",
            *argumentos,
            stdout=salida,
        )

        return salida.getvalue()

    def _sin_escrituras_r2(self):
        self.r2.put_object.assert_not_called()
        self.r2.delete_object.assert_not_called()
        self.r2.get_object.assert_not_called()

    def test_por_defecto_solo_audita(self):
        salida = self._ejecutar(
            "--track-id", str(self.track.pk),
        )

        self.assertIn("MODO AUDITORIA", salida)
        self.assertIn("1 pendientes", salida)
        self.assertIn("No se aplicaron cambios", salida)

        self.motor.assert_not_called()
        self._sin_escrituras_r2()

        self.track.refresh_from_db()
        self.assertEqual(
            self.track.preview.name,
            "previews/antigua.mp3",
        )

    def test_apply_sin_confirmacion_se_rechaza(self):
        with self.assertRaisesRegex(
            CommandError, "confirmacion explicita"
        ):
            self._ejecutar(
                "--track-id", str(self.track.pk),
                "--apply",
            )

        self.configuracion.assert_not_called()
        self.motor.assert_not_called()
        self.r2.head_object.assert_not_called()
        self._sin_escrituras_r2()

    def test_confirm_sin_apply_se_rechaza(self):
        with self.assertRaises(CommandError):
            self._ejecutar(
                "--track-id", str(self.track.pk),
                "--confirm", CONFIRMACION,
            )

        self.configuracion.assert_not_called()
        self.motor.assert_not_called()
        self._sin_escrituras_r2()

    def test_apply_confirmado_llama_al_motor(self):
        salida = self._ejecutar(
            "--track-id", str(self.track.pk),
            "--apply",
            "--confirm", CONFIRMACION,
        )

        self.assertIn("MODO RECUPERACION", salida)
        self.assertIn("Recuperacion finalizada", salida)

        self.motor.assert_called_once_with(
            track_id=self.track.pk,
            client=self.r2,
            bucket="bucket-prueba",
        )

        self._sin_escrituras_r2()

    def test_preview_existente_no_se_recupera(self):
        self.track.preview = self.preview_key
        self.track.save(update_fields=["preview"])

        salida = self._ejecutar(
            "--track-id", str(self.track.pk),
            "--apply",
            "--confirm", CONFIRMACION,
        )

        self.assertIn("1 correctas", salida)
        self.assertIn("No hay previews pendientes", salida)

        self.motor.assert_not_called()
        self._sin_escrituras_r2()

    def test_auditoria_fallida_bloquea_todo_apply(self):
        otro = Track.objects.create(
            nombre_track="Cancion local",
            precio=1000,
            usuario=self.perfil,
            genero=self.genero,
            storage_backend="local",
            media_status="ready",
            preview="previews/local.mp3",
        )

        with self.assertRaisesRegex(
            CommandError,
            "auditoria detecto",
        ):
            self._ejecutar(
                "--track-id", str(self.track.pk),
                "--track-id", str(otro.pk),
                "--apply",
                "--confirm", CONFIRMACION,
            )

        self.motor.assert_not_called()
        self._sin_escrituras_r2()

    def test_error_del_motor_detiene_la_recuperacion(self):
        segundo = Track.objects.create(
            nombre_track="Segunda cancion R2",
            precio=1000,
            usuario=self.perfil,
            genero=self.genero,
            storage_backend="r2",
            media_status="ready",
            r2_owner_user_id=self.perfil.user_id,
            r2_object_key=self.private_key,
            preview="previews/otra_antigua.mp3",
        )

        self.motor.side_effect = RuntimeError(
            "Error simulado del motor"
        )

        with self.assertRaisesRegex(
            CommandError,
            "recuperacion fallida",
        ):
            self._ejecutar(
                "--track-id", str(self.track.pk),
                "--track-id", str(segundo.pk),
                "--apply",
                "--confirm", CONFIRMACION,
            )

        self.motor.assert_called_once_with(
            track_id=self.track.pk,
            client=self.r2,
            bucket="bucket-prueba",
        )

        self._sin_escrituras_r2()
