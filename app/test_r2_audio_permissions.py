from io import BytesIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from app.models import (
    Genero_Musical,
    HistorialCompra,
    Track,
    Usuario,
)


class R2AudioPermissionsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="owner_audio_r2",
            password="test-password",
        )
        cls.owner_profile = Usuario.objects.create(
            user=cls.owner,
            tipo_usu=Usuario.PRODUCTOR,
        )

        cls.buyer = User.objects.create_user(
            username="buyer_audio_r2",
            password="test-password",
        )
        cls.buyer_profile = Usuario.objects.create(
            user=cls.buyer,
            tipo_usu=Usuario.ARTISTA,
        )

        cls.stranger = User.objects.create_user(
            username="stranger_audio_r2",
            password="test-password",
        )
        Usuario.objects.create(
            user=cls.stranger,
            tipo_usu=Usuario.ARTISTA,
        )

        genre = Genero_Musical.objects.create(
            descripcion="Pop",
        )

        cls.paid = Track.objects.create(
            nombre_track="Audio pagado ready",
            precio=1000,
            usuario=cls.owner_profile,
            genero=genre,
            track="canciones/paid_test.mp3",
            preview="previews/paid_test.mp3",
            storage_backend="local",
            media_status="ready",
        )

        cls.free = Track.objects.create(
            nombre_track="Audio gratuito ready",
            precio=0,
            usuario=cls.owner_profile,
            genero=genre,
            track="canciones/free_test.mp3",
            preview="previews/free_test.mp3",
            storage_backend="local",
            media_status="ready",
        )

        cls.pending = Track.objects.create(
            nombre_track="Audio pendiente",
            precio=0,
            usuario=cls.owner_profile,
            genero=genre,
            track="canciones/pending_test.mp3",
            preview="previews/pending_test.mp3",
            storage_backend="local",
            media_status="pending",
        )

    def url(self, track, accion):
        return (
            f"/api/track/{track.pk}/{accion}/"
        )

    def solicitar_audio(self, url):
        with patch(
            "django.db.models.fields.files.FieldFile.open",
            side_effect=lambda *args, **kwargs: BytesIO(
                b"audio-de-prueba"
            ),
        ):
            return self.client.get(url)

    def test_visitante_puede_escuchar_preview(self):
        response = self.solicitar_audio(
            self.url(self.paid, "preview")
        )

        self.assertEqual(response.status_code, 200)

    def test_visitante_no_escucha_original_pagado(self):
        response = self.client.get(
            self.url(self.paid, "reproducir")
        )

        self.assertEqual(response.status_code, 403)

    def test_usuario_sin_compra_no_descarga(self):
        self.client.force_login(self.stranger)

        response = self.client.get(
            self.url(self.paid, "descargar")
        )

        self.assertEqual(response.status_code, 403)

    def test_propietario_reproduce_original_ready(self):
        self.client.force_login(self.owner)

        response = self.solicitar_audio(
            self.url(self.paid, "reproducir")
        )

        self.assertEqual(response.status_code, 200)

    def test_comprador_reproduce_y_descarga(self):
        HistorialCompra.objects.get_or_create(
            usuario=self.buyer_profile,
            track=self.paid,
        )

        self.client.force_login(self.buyer)

        reproduccion = self.solicitar_audio(
            self.url(self.paid, "reproducir")
        )

        self.assertEqual(
            reproduccion.status_code,
            200,
        )

        descarga = self.solicitar_audio(
            self.url(self.paid, "descargar")
        )

        self.assertEqual(
            descarga.status_code,
            200,
        )

        self.assertIn(
            "attachment",
            descarga["Content-Disposition"],
        )

    def test_gratuito_sin_reclamo_no_da_original(self):
        visitante = self.client.get(
            self.url(self.free, "reproducir")
        )

        self.assertEqual(
            visitante.status_code,
            403,
        )

        self.client.force_login(self.buyer)

        usuario = self.client.get(
            self.url(self.free, "reproducir")
        )

        self.assertEqual(
            usuario.status_code,
            403,
        )

    def test_gratuito_reclamado_permite_audio(self):
        self.client.force_login(self.buyer)

        reclamo = self.client.post(
            self.url(self.free, "claim-free")
        )

        self.assertEqual(
            reclamo.status_code,
            200,
        )

        self.assertTrue(
            HistorialCompra.objects.filter(
                usuario=self.buyer_profile,
                track=self.free,
            ).exists()
        )

        reproduccion = self.solicitar_audio(
            self.url(self.free, "reproducir")
        )

        self.assertEqual(
            reproduccion.status_code,
            200,
        )

        descarga = self.solicitar_audio(
            self.url(self.free, "descargar")
        )

        self.assertEqual(
            descarga.status_code,
            200,
        )

    def test_pendiente_no_entrega_audio(self):
        self.client.force_login(self.owner)

        for accion in (
            "preview",
            "reproducir",
            "descargar",
        ):
            with self.subTest(accion=accion):
                response = self.client.get(
                    self.url(self.pending, accion)
                )

                self.assertEqual(
                    response.status_code,
                    404,
                )
