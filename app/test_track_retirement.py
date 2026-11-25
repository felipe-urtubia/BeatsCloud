import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import RequestFactory, TestCase

from .api_shim import (
    cart_add_api,
    catalogo_api,
    claim_free_track_api,
    preview_stream_api,
    track_delete_api,
    track_detail_api,
)
from .models import (
    Genero_Musical,
    HistorialCompra,
    HistorialVenta,
    Track,
    Usuario,
    WebpayTransaction,
)
from .webpay_checkout_guard import (
    PaymentStartBlocked,
    create_pending_webpay_order,
)


class TrackRetirementTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.productor = User.objects.create_user(
            username="ret_productor",
            password="TestPassword123!",
        )
        cls.comprador = User.objects.create_user(
            username="ret_comprador",
            password="TestPassword123!",
        )
        cls.otro = User.objects.create_user(
            username="ret_otro",
            password="TestPassword123!",
        )

        cls.perfil_productor = Usuario.objects.create(
            user=cls.productor,
            tipo_usu=Usuario.PRODUCTOR,
        )
        cls.perfil_comprador = Usuario.objects.create(
            user=cls.comprador,
            tipo_usu=Usuario.ARTISTA,
        )
        Usuario.objects.create(
            user=cls.otro,
            tipo_usu=Usuario.PRODUCTOR,
        )

        cls.genero = Genero_Musical.objects.create(
            descripcion=Genero_Musical.POP,
        )

        cls.track = Track.objects.create(
            nombre_track="Track de prueba retirada",
            precio=1000,
            usuario=cls.perfil_productor,
            genero=cls.genero,
            track="canciones/track_retirada.mp3",
            preview="previews/track_retirada.mp3",
            media_status="ready",
        )

        HistorialCompra.objects.create(
            usuario=cls.perfil_comprador,
            track=cls.track,
        )

        HistorialVenta.objects.create(
            comprador=cls.comprador,
            track=cls.track,
            precio=1000,
        )

    def setUp(self):
        self.factory = RequestFactory()

    def request(self, method, path, user=None):
        req = getattr(self.factory, method)(path)
        req.user = user if user is not None else AnonymousUser()
        return req

    def retirar(self):
        req = self.request(
            "post",
            f"/api/track/{self.track.pk}/delete/",
            self.productor,
        )
        return track_delete_api(req, self.track.pk)

    def test_productor_retira_sin_borrar_compras(self):
        archivo_original = self.track.track.name

        respuesta = self.retirar()

        self.assertEqual(respuesta.status_code, 200)

        self.track.refresh_from_db()
        self.assertTrue(self.track.is_retired)
        self.assertEqual(self.track.track.name, archivo_original)

        self.assertTrue(
            HistorialCompra.objects.filter(
                usuario=self.perfil_comprador,
                track=self.track,
            ).exists()
        )

        self.assertTrue(
            HistorialVenta.objects.filter(
                comprador=self.comprador,
                track=self.track,
            ).exists()
        )

    def test_otro_productor_no_puede_retirar(self):
        req = self.request(
            "post",
            f"/api/track/{self.track.pk}/delete/",
            self.otro,
        )

        respuesta = track_delete_api(req, self.track.pk)

        self.assertEqual(respuesta.status_code, 403)

        self.track.refresh_from_db()
        self.assertFalse(self.track.is_retired)

    def test_catalogo_oculta_track_retirado(self):
        self.retirar()

        req = self.request("get", "/api/catalogo/")
        respuesta = catalogo_api(req)

        self.assertEqual(respuesta.status_code, 200)
        ids = [
            item["id_track"]
            for item in json.loads(respuesta.content.decode("utf-8"))["tracks"]
        ]

        self.assertNotIn(self.track.pk, ids)

    def test_detalle_retirado_solo_para_autorizados(self):
        self.retirar()

        ruta = f"/api/track/{self.track.pk}/"

        anonimo = track_detail_api(
            self.request("get", ruta),
            self.track.pk,
        )
        self.assertEqual(anonimo.status_code, 404)

        sin_compra = track_detail_api(
            self.request("get", ruta, self.otro),
            self.track.pk,
        )
        self.assertEqual(sin_compra.status_code, 404)

        comprador = track_detail_api(
            self.request("get", ruta, self.comprador),
            self.track.pk,
        )
        self.assertEqual(comprador.status_code, 200)

        productor = track_detail_api(
            self.request("get", ruta, self.productor),
            self.track.pk,
        )
        self.assertEqual(productor.status_code, 200)

    def test_preview_retirado_bloquea_anonimos(self):
        self.retirar()

        req = self.request(
            "get",
            f"/api/track/{self.track.pk}/preview/",
        )

        with self.assertRaises(Http404):
            preview_stream_api(req, self.track.pk)

    def test_no_permite_nuevas_adquisiciones(self):
        self.retirar()

        ruta = f"/api/track/{self.track.pk}/"

        respuesta_carrito = cart_add_api(
            self.request("post", ruta + "cart/", self.otro),
            self.track.pk,
        )
        self.assertEqual(respuesta_carrito.status_code, 409)

        respuesta_gratis = claim_free_track_api(
            self.request("post", ruta + "claim/", self.otro),
            self.track.pk,
        )
        self.assertEqual(respuesta_gratis.status_code, 409)

    def test_webpay_rechaza_nueva_orden(self):
        self.retirar()

        snapshot = [{
            "venta_id": 123,
            "track_id": self.track.pk,
            "precio": 1000,
            "iva": 190,
        }]

        with patch(
            "app.webpay_reconciliation.reconcile_stale_pending_for_user"
        ):
            with self.assertRaises(PaymentStartBlocked):
                create_pending_webpay_order(
                    user=self.otro,
                    amount=1190,
                    cart_snapshot=snapshot,
                )

        self.assertFalse(
            WebpayTransaction.objects.filter(
                user=self.otro,
                suscripcion__isnull=True,
            ).exists()
        )

    def test_detalle_django_retirado_bloquea_visitantes(self):
        from .views import detalle_track

        self.retirar()

        req = self.request(
            "get",
            f"/track/{self.track.pk}/",
        )

        with self.assertRaises(Http404):
            detalle_track(req, self.track.pk)

    def test_preview_django_retirado_bloquea_visitantes(self):
        from .views import reproducir_preview_track

        self.retirar()

        req = self.request(
            "get",
            f"/track/{self.track.pk}/preview/",
        )

        with self.assertRaises(Http404):
            reproducir_preview_track(req, self.track.pk)

    def test_comprador_conserva_permisos(self):
        from .track_retirement_access import can_access_retired_track
        from .api_shim import _puede_escuchar_completo

        self.retirar()
        self.track.refresh_from_db()

        self.assertTrue(self.track.is_retired)

        self.assertTrue(
            can_access_retired_track(self.comprador, self.track)
        )
        self.assertTrue(
            can_access_retired_track(self.productor, self.track)
        )
        self.assertFalse(
            can_access_retired_track(self.otro, self.track)
        )

        req_comprador = self.request(
            "get", "/audio/", self.comprador
        )
        req_otro = self.request(
            "get", "/audio/", self.otro
        )

        self.assertTrue(
            _puede_escuchar_completo(req_comprador, self.track)
        )
        self.assertFalse(
            _puede_escuchar_completo(req_otro, self.track)
        )

    def test_orden_webpay_anterior_no_se_elimina(self):
        snapshot = [{
            "venta_id": 123,
            "track_id": self.track.pk,
            "precio": 1000,
            "iva": 190,
        }]

        with patch(
            "app.webpay_reconciliation.reconcile_stale_pending_for_user"
        ):
            orden = create_pending_webpay_order(
                user=self.otro,
                amount=1190,
                cart_snapshot=snapshot,
            )

        orden_id = orden.pk

        respuesta = self.retirar()
        self.assertEqual(respuesta.status_code, 200)

        self.track.refresh_from_db()
        self.assertTrue(self.track.is_retired)

        orden.refresh_from_db()

        self.assertEqual(orden.pk, orden_id)
        self.assertEqual(orden.cart_snapshot, snapshot)
        self.assertTrue(
            WebpayTransaction.objects.filter(pk=orden_id).exists()
        )


    def test_perfil_publico_legacy_oculta_track_retirado(self):
        from .views import perfil_productor1

        self.retirar()

        request = self.request(
            "get",
            f"/perfil/{self.productor.username}/",
            self.otro,
        )

        with patch("app.views.render") as mocked_render:
            perfil_productor1(
                request,
                self.productor.username,
            )

        self.assertTrue(mocked_render.called)

        context = mocked_render.call_args.args[2]
        self.assertIn("canciones", context)

        visible_ids = list(
            context["canciones"].values_list("pk", flat=True)
        )

        self.assertNotIn(self.track.pk, visible_ids)

        self.track.refresh_from_db()
        self.assertTrue(self.track.is_retired)
