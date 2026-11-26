"""Pruebas de filtros server-side del catalogo."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Genero_Musical, Track, Usuario


class CatalogServerSideTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = get_user_model().objects.create_user(
            username="catalog_producer_d9"
        )

        cls.profile = Usuario.objects.create(
            user=user,
            tipo_usu=Usuario.PRODUCTOR,
        )

        cls.genre_a = Genero_Musical.objects.create(
            descripcion="D9 Alfa"
        )

        cls.genre_z = Genero_Musical.objects.create(
            descripcion="D9 Zeta"
        )

        def create(title, **kwargs):
            values = {
                "nombre_track": title,
                "usuario": cls.profile,
                "genero": cls.genre_a,
                "precio": 5000,
                "bpm": 120,
                "resource_type": "instrumental",
                "mood": "Oscuro",
                "scale_key": "Am",
                "has_stems": True,
            }

            values.update(kwargs)
            return Track.objects.create(**values)

        cls.a = create("D9 Beat Alfa")
        cls.b = create("D9 Beat Beta", bpm=150)

        cls.c = create(
            "D9 Loop",
            resource_type="loop",
            precio=0,
            mood="Bailable",
            bpm=90,
        )

        cls.d = create(
            "D9 Beat Zeta",
            genero=cls.genre_z,
            bpm=130,
            has_stems=False,
            scale_key="Cm",
            precio=15000,
        )

        cls.retired = create(
            "D9 Retirado",
            is_retired=True,
        )

        cls.pending = create(
            "D9 Pendiente",
            media_status="pending",
        )

        cls.profile.tracks_gustados.add(cls.d)

    def get_catalog(self, **params):
        response = self.client.get(
            "/api/catalogo/", params
        )

        self.assertEqual(
            response.status_code, 200, response.content
        )

        return response.json()

    def ids(self, **params):
        return [
            track["id_track"]
            for track in self.get_catalog(**params)["tracks"]
        ]

    def test_bpm_range(self):
        self.assertEqual(
            set(self.ids(bpm_min=120, bpm_max=140)),
            {self.a.pk, self.d.pk},
        )

    def test_genre(self):
        self.assertEqual(
            self.ids(genero="D9 Zeta"),
            [self.d.pk],
        )

    def test_resource_type(self):
        self.assertEqual(
            self.ids(tipo="loop"),
            [self.c.pk],
        )

    def test_mood(self):
        self.assertEqual(
            self.ids(mood="Bailable"),
            [self.c.pk],
        )

    def test_combined_filters(self):
        result = self.get_catalog(
            genero="D9 Alfa",
            tipo="instrumental",
            mood="Oscuro",
            bpm_min=110,
            bpm_max=130,
            has_stems="true",
            tonalidad="Am",
        )

        self.assertEqual(
            result["total_resultados"], 1
        )

        self.assertEqual(
            result["tracks"][0]["id_track"], self.a.pk
        )

    def test_price(self):
        self.assertEqual(
            self.ids(precio="free"),
            [self.c.pk],
        )

        self.assertEqual(
            set(self.ids(precio="paid")),
            {self.a.pk, self.b.pk, self.d.pk},
        )

        self.assertEqual(
            self.ids(precio="10001-20000"),
            [self.d.pk],
        )

    def test_search(self):
        self.assertEqual(
            self.ids(q="150"),
            [self.b.pk],
        )

        self.assertEqual(
            self.ids(q="Cm"),
            [self.d.pk],
        )

    def test_bpm_order(self):
        self.assertEqual(
            self.ids(orden="bpm_asc"),
            [self.c.pk, self.a.pk, self.d.pk, self.b.pk],
        )

        self.assertEqual(
            self.ids(orden="bpm_desc"),
            [self.b.pk, self.d.pk, self.a.pk, self.c.pk],
        )

    def test_genre_order(self):
        self.assertEqual(
            self.ids(orden="genero_asc"),
            [self.a.pk, self.b.pk, self.c.pk, self.d.pk],
        )

        self.assertEqual(
            self.ids(orden="genero_desc"),
            [self.d.pk, self.a.pk, self.b.pk, self.c.pk],
        )

    def test_price_name_and_likes_order(self):
        self.assertEqual(
            self.ids(orden="precio_mayor")[0],
            self.d.pk,
        )

        self.assertEqual(
            self.ids(orden="nombre_asc")[0],
            self.a.pk,
        )

        self.assertEqual(
            self.ids(orden="likes")[0],
            self.d.pk,
        )

    def test_hidden_tracks_remain_hidden(self):
        result = self.ids(page_size=24)

        self.assertNotIn(self.retired.pk, result)
        self.assertNotIn(self.pending.pk, result)

    def test_pagination_without_duplicate_tracks(self):
        for index in range(20):
            Track.objects.create(
                nombre_track=f"Pagination {index}",
                usuario=self.profile,
                genero=self.genre_a,
                precio=5000,
                bpm=120,
            )

        params = {
            "q": "Pagination",
            "orden": "bpm_asc",
            "page_size": 6,
        }

        first = self.get_catalog(page=1, **params)
        second = self.get_catalog(page=2, **params)
        last = self.get_catalog(page=4, **params)

        self.assertEqual(first["total_resultados"], 20)
        self.assertEqual(first["total_paginas"], 4)
        self.assertEqual(first["page_size"], 6)

        self.assertEqual(len(first["tracks"]), 6)
        self.assertEqual(len(second["tracks"]), 6)
        self.assertEqual(len(last["tracks"]), 2)

        first_ids = {
            track["id_track"] for track in first["tracks"]
        }

        second_ids = {
            track["id_track"] for track in second["tracks"]
        }

        self.assertFalse(first_ids & second_ids)

    def test_empty_results(self):
        result = self.get_catalog(q="NO_MATCH_DDPB70")

        self.assertEqual(result["tracks"], [])
        self.assertEqual(result["total_resultados"], 0)

    def test_invalid_parameters(self):
        cases = (
            {"bpm_min": "abc"},
            {"bpm_max": 999},
            {"bpm_min": 150, "bpm_max": 100},
            {"tipo": "invalid"},
            {"mood": "invalid"},
            {"has_stems": "invalid"},
            {"page_size": 9999},
        )

        for params in cases:
            with self.subTest(params=params):
                response = self.client.get(
                    "/api/catalogo/", params
                )

                self.assertEqual(response.status_code, 400)
