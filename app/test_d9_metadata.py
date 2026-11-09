"""Pruebas D9: validacion de metadatos en formulario y API."""

import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, SimpleTestCase, TestCase

from app.forms import TrackForm
from app.metadata_validation import validate_d9_field
from app.models import Genero_Musical, Track, Usuario
from app.api_shim import track_update_api


class D9MetadataValidationTests(SimpleTestCase):
    def test_bpm_limites(self):
        for value in (1, '120', 300):
            with self.subTest(value=value):
                self.assertEqual(validate_d9_field('bpm', value), int(value))
        for value in (0, -10, 'abc', 301, 9999, True):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_d9_field('bpm', value)

    def test_tipos_validos_e_invalidos(self):
        for value in ('instrumental', 'acapella', 'loop', 'drumkit'):
            self.assertEqual(validate_d9_field('resource_type', value), value)
        with self.assertRaises(ValidationError):
            validate_d9_field('resource_type', 'tipo_inventado')

    def test_moods_validos_e_invalidos(self):
        for value in ('Oscuro', 'Enérgico', 'Chill / Relax',
                      'Triste / Nostálgico', 'Bailable', 'Agresivo'):
            self.assertEqual(validate_d9_field('mood', value), value)
        with self.assertRaises(ValidationError):
            validate_d9_field('mood', 'Estado inventado')

    def test_stems_booleanos(self):
        for value in (True, 1, 'true', '1', 'on'):
            self.assertIs(validate_d9_field('has_stems', value), True)
        for value in (False, 0, 'false', '0', 'off', None, ''):
            self.assertIs(validate_d9_field('has_stems', value), False)
        for value in ('valor_invalido', 2, [], {}):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_d9_field('has_stems', value)

    def test_formulario_rechaza_stems_incorrectos(self):
        form = TrackForm(data={'has_stems': 'valor_invalido'})
        with self.assertRaises(ValidationError):
            form.clean_has_stems()

    def test_formulario_valida_bpm_mood_y_tipo(self):
        form = TrackForm()
        form.cleaned_data = {'bpm': 9999, 'mood': 'Estado inventado',
                             'resource_type': 'tipo_inventado'}
        for method in (form.clean_bpm, form.clean_mood, form.clean_resource_type):
            with self.assertRaises(ValidationError):
                method()


class D9TrackUpdateAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.producer = get_user_model().objects.create_user(
            username='producer_d9', password='only-for-test'
        )
        cls.profile = Usuario.objects.create(
            user=cls.producer, tipo_usu=Usuario.PRODUCTOR
        )
        cls.genre = Genero_Musical.objects.create(descripcion='Pop')
        cls.track = Track.objects.create(
            nombre_track='D9 prueba API', precio=1000,
            genero=cls.genre, usuario=cls.profile,
        )

    def _patch(self, data):
        request = RequestFactory().patch(
            '/api/track/d9/',
            data=json.dumps(data),
            content_type='application/json',
        )
        request.user = self.producer
        return track_update_api(request, self.track.pk)

    def test_api_rechaza_valores_invalidos_sin_guardar(self):
        cases = (
            ('bpm', 9999),
            ('bpm', 'abc'),
            ('resource_type', 'tipo_inventado'),
            ('mood', 'Estado inventado'),
            ('has_stems', 'valor_invalido'),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value):
                self.track.refresh_from_db()
                old = getattr(self.track, field)
                response = self._patch({field: value})
                self.assertEqual(response.status_code, 400, response.content)
                self.track.refresh_from_db()
                self.assertEqual(getattr(self.track, field), old)

    def test_api_acepta_y_persiste_datos_validos(self):
        response = self._patch({
            'bpm': 120,
            'resource_type': 'loop',
            'mood': 'Chill / Relax',
            'has_stems': False,
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.track.refresh_from_db()
        self.assertEqual(self.track.bpm, 120)
        self.assertEqual(self.track.resource_type, 'loop')
        self.assertEqual(self.track.mood, 'Chill / Relax')
        self.assertIs(self.track.has_stems, False)
