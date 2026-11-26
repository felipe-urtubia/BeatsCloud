"""Pruebas de proteccion administrativa de identidades D10."""

from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from django.test import (
    TestCase,
    RequestFactory,
    override_settings,
)

from django.urls import reverse
from django.utils import timezone

from app.models import (
    Usuario,
    Track,
    Genero_Musical,
    HistorialCompra,
    WebpayTransaction,
    Licencia,
)

from app.license_service import (
    issue_license_for_purchase,
    verify_license,
)

from app.views import _seudonimizar_identidad_cuenta


@override_settings(
    LICENSE_SIGNING_KEY="test-admin-identity-d10-" + "a" * 48,
    LICENSE_SIGNING_KEY_FALLBACKS=(),
)
class AdminIdentityTests(TestCase):

    def setUp(self):

        self.administrador = User.objects.create_superuser(
            username="admin_d10_pruebas",
            email="admin-d10@example.invalid",
            password="Solo-Pruebas-Admin-D10!",
        )

        comprador = User.objects.create_user(
            username="admin_d10_comprador",
            password="Solo-Pruebas-Comprador-D10!",
        )

        perfil = Usuario.objects.create(
            user=comprador,
            tipo_usu=Usuario.ARTISTA,
        )

        self.productor = User.objects.create_user(
            username="admin_d10_productor",
            password="Solo-Pruebas-Productor-D10!",
        )

        self.perfil_productor = Usuario.objects.create(
            user=self.productor,
            tipo_usu=Usuario.PRODUCTOR,
        )

        genero = Genero_Musical.objects.create(
            descripcion="Pop"
        )

        track = Track.objects.create(
            nombre_track="Instrumental administrativo D10",
            precio=1000,
            track="canciones/admin-d10-test.wav",
            genero=genero,
            usuario=self.perfil_productor,
            media_status="ready",
        )

        self.compra = HistorialCompra.objects.create(
            usuario=perfil,
            track=track,
            origen_adquisicion=HistorialCompra.ORIGEN_WEBPAY,
        )

        self.orden = WebpayTransaction.objects.create(
            user=comprador,
            buy_order="orden-admin-d10",
            session_id="sesion-admin-d10",
            amount=Decimal("1190.00"),
            status=WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at=timezone.now(),
            cart_snapshot=[{
                "venta_id": 1001,
                "track_id": track.pk,
                "precio": 1000,
                "iva": 190,
            }],
        )

        self.licencia, creada = issue_license_for_purchase(
            self.compra,
            self.orden,
        )

        self.assertTrue(creada)

        self.codigo = self.licencia.license_code
        self.firma = self.licencia.verification_hash

        self.cuenta, self.perfil = (
            _seudonimizar_identidad_cuenta(perfil)
        )

        self.fecha_cierre = (
            self.perfil.cuenta_cerrada_en
        )

        self.client.force_login(
            self.administrador
        )

    def _comprobar_integridad(self):

        self.cuenta.refresh_from_db()
        self.perfil.refresh_from_db()
        self.compra.refresh_from_db()
        self.orden.refresh_from_db()
        self.licencia.refresh_from_db()

        self.assertFalse(self.cuenta.is_active)
        self.assertFalse(self.cuenta.is_staff)
        self.assertFalse(self.cuenta.is_superuser)

        self.assertFalse(
            self.cuenta.has_usable_password()
        )

        self.assertEqual(
            self.perfil.cuenta_cerrada_en,
            self.fecha_cierre,
        )

        self.assertEqual(
            self.perfil.user_id,
            self.cuenta.pk,
        )

        self.assertEqual(
            self.compra.usuario_id,
            self.perfil.pk,
        )

        self.assertEqual(
            self.orden.user_id,
            self.cuenta.pk,
        )

        self.assertEqual(
            self.licencia.license_code,
            self.codigo,
        )

        self.assertEqual(
            self.licencia.verification_hash,
            self.firma,
        )

        self.assertEqual(
            Licencia.objects.filter(
                compra_id=self.compra.pk
            ).count(),
            1,
        )

        self.assertTrue(
            verify_license(self.licencia)
        )

    def test_admin_no_reactiva_cuenta_cerrada(self):

        url = reverse(
            "admin:auth_user_change",
            args=[self.cuenta.pk],
        )

        # La cuenta sigue disponible para consulta.
        self.assertEqual(
            self.client.get(url).status_code,
            200,
        )

        respuesta = self.client.post(
            url,
            {
                "username": self.cuenta.username,
                "is_active": "on",
                "is_staff": "on",
                "is_superuser": "on",
                "_save": "Guardar",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        self._comprobar_integridad()

    def test_admin_no_cambia_password_de_cerrada(self):

        url = reverse(
            "admin:auth_user_password_change",
            args=[self.cuenta.pk],
        )

        self.assertEqual(
            self.client.get(url).status_code,
            403,
        )

        respuesta = self.client.post(
            url,
            {
                "password1": "Nueva-Clave-Admin-D10!",
                "password2": "Nueva-Clave-Admin-D10!",
                "usable_password": "true",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        self._comprobar_integridad()

    def test_admin_no_modifica_perfil_cerrado(self):

        url = reverse(
            "admin:app_usuario_change",
            args=[self.perfil.pk],
        )

        self.assertEqual(
            self.client.get(url).status_code,
            200,
        )

        respuesta = self.client.post(
            url,
            {
                "user": self.productor.pk,
                "nombre_artistico": "Identidad restaurada",
                "tipo_usu": Usuario.ARTISTA,
                "_save": "Guardar",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        self._comprobar_integridad()

    def test_admin_no_elimina_identidades_cerradas(self):

        for nombre, pk in (
            ("admin:auth_user_delete", self.cuenta.pk),
            ("admin:app_usuario_delete", self.perfil.pk),
        ):

            with self.subTest(ruta=nombre):

                url = reverse(
                    nombre,
                    args=[pk],
                )

                self.assertEqual(
                    self.client.get(url).status_code,
                    403,
                )

                self.assertEqual(
                    self.client.post(
                        url,
                        {"post": "yes"},
                    ).status_code,
                    403,
                )

        self._comprobar_integridad()

    def test_admin_bloquea_eliminacion_masiva_identidades(self):

        solicitud = RequestFactory().post("/")
        solicitud.user = self.administrador

        for modelo, ids in (
            (
                User,
                [self.cuenta.pk, self.productor.pk],
            ),
            (
                Usuario,
                [self.perfil.pk, self.perfil_productor.pk],
            ),
        ):

            with self.subTest(modelo=modelo.__name__):

                administrador = admin.site._registry[modelo]

                self.assertNotIn(
                    "delete_selected",
                    administrador.get_actions(solicitud),
                )

                consulta = modelo.objects.filter(
                    pk__in=ids
                )

                with self.assertRaises(PermissionDenied):

                    administrador.delete_queryset(
                        solicitud,
                        consulta,
                    )

                self.assertEqual(
                    consulta.count(),
                    2,
                )

        self._comprobar_integridad()

    def test_admin_conserva_acceso_a_identidades_abiertas(self):

        solicitud = RequestFactory().get("/")
        solicitud.user = self.administrador

        admin_user = admin.site._registry[User]
        admin_perfil = admin.site._registry[Usuario]

        self.assertTrue(
            admin_user.has_change_permission(
                solicitud,
                self.productor,
            )
        )

        self.assertTrue(
            admin_perfil.has_change_permission(
                solicitud,
                self.perfil_productor,
            )
        )

        self.assertIn(
            "user",
            admin_perfil.get_readonly_fields(
                solicitud,
                self.perfil_productor,
            ),
        )

        self.assertIn(
            "cuenta_cerrada_en",
            admin_perfil.get_readonly_fields(
                solicitud,
                self.perfil_productor,
            ),
        )

        for nombre, pk in (
            (
                "admin:auth_user_change",
                self.productor.pk,
            ),
            (
                "admin:app_usuario_change",
                self.perfil_productor.pk,
            ),
            (
                "admin:auth_user_password_change",
                self.productor.pk,
            ),
        ):

            with self.subTest(ruta=nombre):

                self.assertEqual(
                    self.client.get(
                        reverse(nombre, args=[pk])
                    ).status_code,
                    200,
                )

        # Una cuenta abierta sin dependencias comerciales
        # conserva la eliminacion individual normal.
        temporal = User.objects.create_user(
            username="admin_d10_temporal",
            password="Solo-Pruebas-Temporal-D10!",
        )

        respuesta = self.client.post(
            reverse(
                "admin:auth_user_delete",
                args=[temporal.pk],
            ),
            {"post": "yes"},
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.assertFalse(
            User.objects.filter(
                pk=temporal.pk
            ).exists()
        )

        self._comprobar_integridad()

    def test_admin_catalogo_bloquea_eliminacion_individual(self):
        from app.models import Suscripcion
        from app.admin_catalog import BeatsCloudCatalogAdmin

        track = self.compra.track
        genero = track.genero

        solicitud = RequestFactory().post("/")
        solicitud.user = self.administrador

        for modelo, objeto in (
            (Track, track),
            (Genero_Musical, genero),
            (
                Suscripcion,
                Suscripcion(user=self.perfil_productor),
            ),
        ):

            with self.subTest(modelo=modelo.__name__):

                administrador = admin.site._registry[modelo]

                self.assertIsInstance(
                    administrador,
                    BeatsCloudCatalogAdmin,
                )

                self.assertFalse(
                    administrador.has_delete_permission(
                        solicitud,
                        objeto,
                    )
                )

                with self.assertRaises(PermissionDenied):

                    administrador.delete_model(
                        solicitud,
                        objeto,
                    )

        # Comprobar rutas reales de eliminacion.
        for modelo, objeto in (
            (Track, track),
            (Genero_Musical, genero),
        ):

            nombre = (
                f"admin:{modelo._meta.app_label}_"
                f"{modelo._meta.model_name}_delete"
            )

            url = reverse(
                nombre,
                args=[objeto.pk],
            )

            self.assertEqual(
                self.client.get(url).status_code,
                403,
            )

            self.assertEqual(
                self.client.post(
                    url,
                    {"post": "yes"},
                ).status_code,
                403,
            )

            self.assertTrue(
                modelo.objects.filter(
                    pk=objeto.pk
                ).exists()
            )

        self._comprobar_integridad()

    def test_admin_catalogo_bloquea_eliminacion_masiva(self):
        from app.models import Suscripcion

        solicitud = RequestFactory().post("/")
        solicitud.user = self.administrador

        for modelo in (
            Track,
            Suscripcion,
            Genero_Musical,
        ):

            with self.subTest(modelo=modelo.__name__):

                administrador = admin.site._registry[modelo]

                self.assertNotIn(
                    "delete_selected",
                    administrador.get_actions(solicitud),
                )

                consulta = modelo.objects.all()

                cantidad_original = consulta.count()

                with self.assertRaises(PermissionDenied):

                    administrador.delete_queryset(
                        solicitud,
                        consulta,
                    )

                self.assertEqual(
                    consulta.count(),
                    cantidad_original,
                )

        self._comprobar_integridad()

    def test_admin_catalogo_conserva_permisos_legitimos(self):
        from app.models import Suscripcion

        solicitud = RequestFactory().get("/")
        solicitud.user = self.administrador

        track = self.compra.track

        for modelo, objeto in (
            (Track, track),
            (Genero_Musical, track.genero),
            (Suscripcion, None),
        ):

            with self.subTest(modelo=modelo.__name__):

                administrador = admin.site._registry[modelo]

                self.assertTrue(
                    administrador.has_view_permission(
                        solicitud,
                        objeto,
                    )
                )

                self.assertTrue(
                    administrador.has_change_permission(
                        solicitud,
                        objeto,
                    )
                )

                self.assertEqual(
                    administrador.has_add_permission(
                        solicitud
                    ),
                    modelo is Genero_Musical,
                )

                self.assertFalse(
                    administrador.has_delete_permission(
                        solicitud,
                        objeto,
                    )
                )

        self._comprobar_integridad()

    def test_admin_no_elimina_identidades_abiertas_con_perfil(self):

        track = self.compra.track

        temporal = User.objects.create_user(
            username="admin_d10_perfil_sin_compras",
            password="Solo-Pruebas-Perfil-D10!",
        )

        perfil_temporal = Usuario.objects.create(
            user=temporal,
            tipo_usu=Usuario.ARTISTA,
        )

        objetivos = (
            (
                User,
                self.productor.pk,
                "admin:auth_user_delete",
            ),
            (
                Usuario,
                self.perfil_productor.pk,
                "admin:app_usuario_delete",
            ),
            (
                User,
                temporal.pk,
                "admin:auth_user_delete",
            ),
            (
                Usuario,
                perfil_temporal.pk,
                "admin:app_usuario_delete",
            ),
        )

        for modelo, pk, nombre in objetivos:

            with self.subTest(modelo=modelo.__name__, pk=pk):

                url = reverse(nombre, args=[pk])

                respuesta = self.client.get(url)

                self.assertEqual(
                    respuesta.status_code,
                    200,
                )

                self.assertTrue(
                    respuesta.context["protected"]
                )

                respuesta = self.client.post(
                    url,
                    {"post": "yes"},
                )

                self.assertEqual(
                    respuesta.status_code,
                    200,
                )

                self.assertTrue(
                    respuesta.context["protected"]
                )

                self.assertTrue(
                    modelo.objects.filter(pk=pk).exists()
                )

        track.refresh_from_db()

        self.assertEqual(
            track.usuario_id,
            self.perfil_productor.pk,
        )

        self._comprobar_integridad()

    def test_admin_no_elimina_cuenta_con_webpay_sin_perfil(self):

        cuenta = User.objects.create_user(
            username="admin_d10_webpay_sin_perfil",
            password="Solo-Pruebas-Webpay-D10!",
        )

        self.assertFalse(
            Usuario.objects.filter(
                user=cuenta
            ).exists()
        )

        orden = WebpayTransaction.objects.create(
            user=cuenta,
            buy_order="orden-admin-sin-perfil-d10",
            session_id="sesion-admin-sin-perfil",
            amount=Decimal("1190.00"),
            status=WebpayTransaction.ESTADO_PENDIENTE,
        )

        url = reverse(
            "admin:auth_user_delete",
            args=[cuenta.pk],
        )

        respuesta = self.client.get(url)

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertTrue(
            respuesta.context["protected"]
        )

        respuesta = self.client.post(
            url,
            {"post": "yes"},
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertTrue(
            respuesta.context["protected"]
        )

        self.assertTrue(
            User.objects.filter(pk=cuenta.pk).exists()
        )

        orden.refresh_from_db()

        self.assertEqual(
            orden.user_id,
            cuenta.pk,
        )

        self.assertEqual(
            orden.status,
            WebpayTransaction.ESTADO_PENDIENTE,
        )

        self._comprobar_integridad()

    def test_admin_metodo_directo_no_elimina_identidad_protegida(self):

        solicitud = RequestFactory().post("/")
        solicitud.user = self.administrador

        for modelo, objeto in (
            (User, self.productor),
            (Usuario, self.perfil_productor),
        ):

            with self.subTest(modelo=modelo.__name__):

                administrador = admin.site._registry[modelo]

                self.assertTrue(
                    administrador._requiere_cierre_controlado(
                        objeto
                    )
                )

                with self.assertRaises(PermissionDenied):

                    administrador.delete_model(
                        solicitud,
                        objeto,
                    )

                self.assertTrue(
                    modelo.objects.filter(
                        pk=objeto.pk
                    ).exists()
                )

        self.assertTrue(
            Track.objects.filter(
                pk=self.compra.track_id,
                usuario=self.perfil_productor,
            ).exists()
        )

        self._comprobar_integridad()

    def test_admin_track_protege_campos_y_permite_precio(self):

        track = self.compra.track

        propietario = track.usuario_id
        archivo = track.track.name
        almacenamiento = track.storage_backend
        objeto_r2 = track.r2_object_key
        portada_r2 = track.r2_cover_key
        retirado = track.is_retired

        url = reverse(
            "admin:app_track_change",
            args=[track.pk],
        )

        respuesta = self.client.post(
            url,
            {
                "nombre_track": "Titulo actualizado D10",
                "descripcion": "Descripcion administrativa valida",
                "precio": 1500,
                "usuario": self.perfil.pk,
                "track": "archivo-sustituido.wav",
                "storage_backend": "r2",
                "r2_object_key": "objeto-alterado.wav",
                "r2_cover_key": "portada-alterada.jpg",
                "is_retired": "on",
                "_save": "Guardar",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        track.refresh_from_db()

        self.assertEqual(
            track.nombre_track,
            "Titulo actualizado D10",
        )

        self.assertEqual(track.precio, 1500)

        self.assertEqual(
            track.descripcion,
            "Descripcion administrativa valida",
        )

        self.assertEqual(track.usuario_id, propietario)
        self.assertEqual(track.track.name, archivo)
        self.assertEqual(track.storage_backend, almacenamiento)
        self.assertEqual(track.r2_object_key, objeto_r2)
        self.assertEqual(track.r2_cover_key, portada_r2)
        self.assertEqual(track.is_retired, retirado)

        self.assertEqual(
            self.orden.amount,
            Decimal("1190.00"),
        )

        self._comprobar_integridad()

    def test_admin_track_rechaza_precio_negativo(self):

        track = self.compra.track

        precio_original = track.precio

        respuesta = self.client.post(
            reverse(
                "admin:app_track_change",
                args=[track.pk],
            ),
            {
                "nombre_track": track.nombre_track,
                "descripcion": track.descripcion or "",
                "precio": -100,
                "_save": "Guardar",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        formulario = respuesta.context[
            "adminform"
        ].form

        self.assertIn(
            "precio",
            formulario.errors,
        )

        track.refresh_from_db()

        self.assertEqual(
            track.precio,
            precio_original,
        )

        self._comprobar_integridad()

    def test_admin_track_no_sobrescribe_estado_protegido(self):

        from types import SimpleNamespace

        track = self.compra.track

        # Simular una instancia obtenida antes de una retirada.
        instancia_antigua = Track.objects.get(
            pk=track.pk
        )

        Track.objects.filter(
            pk=track.pk
        ).update(
            is_retired=True
        )

        instancia_antigua.descripcion = (
            "Edicion de instancia anterior"
        )

        self.assertFalse(
            instancia_antigua.is_retired
        )

        solicitud = RequestFactory().post("/")
        solicitud.user = self.administrador

        administrador = admin.site._registry[Track]

        formulario = SimpleNamespace(
            changed_data=["descripcion"]
        )

        administrador.save_model(
            solicitud,
            instancia_antigua,
            formulario,
            True,
        )

        track.refresh_from_db()

        self.assertTrue(track.is_retired)

        self.assertEqual(
            track.descripcion,
            "Edicion de instancia anterior",
        )

        self._comprobar_integridad()

    def test_admin_suscripcion_protege_condiciones_comerciales(self):

        from app.models import Suscripcion

        opciones = Suscripcion._meta.get_field(
            "duracion_unidad"
        ).flatchoices

        unidad = next(
            valor
            for valor, etiqueta in opciones
            if valor
        )

        plan = Suscripcion.objects.create(
            detalle="Plan original D10",
            precio=1000,
            user=self.perfil_productor,
            descripcion="Descripcion original",
            beneficios=["Beneficio original"],
            activo=True,
            duracion_cantidad=1,
            duracion_unidad=unidad,
        )

        respuesta = self.client.post(
            reverse(
                "admin:app_suscripcion_change",
                args=[plan.pk],
            ),
            {
                "detalle": "Plan actualizado D10",
                "descripcion": "Descripcion actualizada",
                "user": self.perfil.pk,
                "precio": 999999,
                "beneficios": '["Beneficio alterado"]',
                "duracion_cantidad": 99,
                "duracion_unidad": "alterada",
                "_save": "Guardar",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        plan.refresh_from_db()

        self.assertEqual(
            plan.detalle,
            "Plan actualizado D10",
        )

        self.assertEqual(
            plan.descripcion,
            "Descripcion actualizada",
        )

        self.assertEqual(
            plan.user_id,
            self.perfil_productor.pk,
        )

        self.assertEqual(plan.precio, 1000)
        self.assertEqual(plan.duracion_cantidad, 1)
        self.assertEqual(plan.duracion_unidad, unidad)
        self.assertEqual(plan.beneficios, ["Beneficio original"])
        self.assertTrue(plan.activo)

        # Verificar tambien una suscripcion persistida.
        url = reverse(
            "admin:app_suscripcion_delete",
            args=[plan.pk],
        )

        self.assertEqual(
            self.client.post(
                url,
                {"post": "yes"},
            ).status_code,
            403,
        )

        self.assertTrue(
            Suscripcion.objects.filter(
                pk=plan.pk
            ).exists()
        )

        self._comprobar_integridad()

    def test_admin_registros_comerciales_solo_lectura(self):

        from app.models import (
            Venta,
            Metodo_Pago,
            Suscripcion,
        )

        venta = Venta.objects.create(
            detalle="Venta administrativa D10",
            fecha=timezone.localdate(),
            precio=1000,
            iva=190,
            precio_total=1190,
            usuario_id=self.perfil,
            track=self.compra.track,
            completada=False,
        )

        metodo = Metodo_Pago.objects.create(
            descripcion="Webpay de prueba",
            venta_id=venta,
        )

        for modelo, objeto in (
            (Venta, venta),
            (Metodo_Pago, metodo),
        ):

            with self.subTest(modelo=modelo.__name__):

                prefijo = (
                    f"admin:app_{modelo._meta.model_name}"
                )

                url = reverse(
                    prefijo + "_change",
                    args=[objeto.pk],
                )

                self.assertEqual(
                    self.client.get(url).status_code,
                    200,
                )

                self.assertEqual(
                    self.client.post(
                        url,
                        {
                            "descripcion": "Alterado",
                            "precio": 1,
                            "completada": "on",
                            "_save": "Guardar",
                        },
                    ).status_code,
                    403,
                )

                self.assertEqual(
                    self.client.post(
                        reverse(
                            prefijo + "_delete",
                            args=[objeto.pk],
                        ),
                        {"post": "yes"},
                    ).status_code,
                    403,
                )

        for modelo in (
            Track,
            Suscripcion,
            Venta,
            Metodo_Pago,
        ):

            nombre = (
                f"admin:app_{modelo._meta.model_name}_add"
            )

            self.assertEqual(
                self.client.get(
                    reverse(nombre)
                ).status_code,
                403,
            )

        venta.refresh_from_db()
        metodo.refresh_from_db()

        self.assertEqual(venta.precio, 1000)
        self.assertEqual(venta.iva, 190)
        self.assertEqual(venta.precio_total, 1190)
        self.assertFalse(venta.completada)

        self.assertEqual(
            metodo.descripcion,
            "Webpay de prueba",
        )

        self._comprobar_integridad()
