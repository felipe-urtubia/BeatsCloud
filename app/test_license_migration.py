"""Proteccion de adquisiciones anteriores a D10."""

from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class LicenseMigrationTests(TransactionTestCase):

    def test_migracion_0035_conserva_historial(self):

        anterior = ("app", "0034_licencia")
        siguiente = (
            "app",
            "0035_historialcompra_origen_adquisicion",
        )

        executor = MigrationExecutor(connection)

        finales = executor.loader.graph.leaf_nodes()

        if siguiente not in executor.loader.graph.nodes:
            self.fail("No existe la migracion historica esperada.")

        try:
            # Simular el esquema anterior al campo de origen.
            executor.migrate([anterior])

            executor = MigrationExecutor(connection)

            apps = executor.loader.project_state(
                [anterior]
            ).apps

            User = apps.get_model("auth", "User")
            Usuario = apps.get_model("app", "Usuario")
            Track = apps.get_model("app", "Track")
            Genero = apps.get_model("app", "Genero_Musical")

            Compra = apps.get_model(
                "app", "HistorialCompra"
            )

            Venta = apps.get_model(
                "app", "HistorialVenta"
            )

            Orden = apps.get_model(
                "app", "WebpayTransaction"
            )

            comprador = User.objects.create(
                username="d10_migracion_comprador",
                password="!",
            )

            productor = User.objects.create(
                username="d10_migracion_productor",
                password="!",
            )

            # Utilizar los valores definidos por el modelo actual.
            from app.models import Usuario as UsuarioActual

            perfil_comprador = Usuario.objects.create(
                user_id=comprador.pk,
                tipo_usu=UsuarioActual.ARTISTA,
            )

            perfil_productor = Usuario.objects.create(
                user_id=productor.pk,
                tipo_usu=UsuarioActual.PRODUCTOR,
            )

            genero = Genero.objects.create(
                descripcion="Genero migracion D10",
            )

            tracks = []

            for nombre, precio in (
                ("Compra Webpay historica", 1000),
                ("Venta sin orden verificable", 2000),
                ("Adquisicion de origen desconocido", 0),
            ):
                track = Track.objects.create(
                    nombre_track=nombre,
                    precio=precio,
                    genero_id=genero.pk,
                    usuario_id=perfil_productor.pk,
                    media_status="ready",
                )

                tracks.append(track)

                Compra.objects.create(
                    usuario_id=perfil_comprador.pk,
                    track_id=track.pk,
                )

                if precio > 0:
                    Venta.objects.create(
                        comprador_id=comprador.pk,
                        track_id=track.pk,
                        precio=Decimal(precio),
                    )

            orden = Orden.objects.create(
                user_id=comprador.pk,
                buy_order="orden-migracion-d10",
                session_id=comprador.username,
                amount=Decimal("1190.00"),
                status="AUTHORIZED",
                fulfilled_at=timezone.now(),
                webpay_token="token-prueba-migracion",
                cart_snapshot=[
                    {
                        "venta_id": 1001,
                        "track_id": tracks[0].pk,
                        "precio": 1000,
                        "iva": 190,
                    }
                ],
            )

            campos_compra = (
                "pk",
                "usuario_id",
                "track_id",
                "fecha_compra",
            )

            campos_venta = (
                "pk",
                "comprador_id",
                "track_id",
                "precio",
                "fecha_venta",
            )

            campos_orden = (
                "pk",
                "user_id",
                "amount",
                "status",
                "fulfilled_at",
                "cart_snapshot",
            )

            compras_antes = list(
                Compra.objects.filter(
                    usuario_id=perfil_comprador.pk
                ).order_by("pk").values(*campos_compra)
            )

            ventas_antes = list(
                Venta.objects.filter(
                    comprador_id=comprador.pk
                ).order_by("pk").values(*campos_venta)
            )

            orden_antes = Orden.objects.filter(
                pk=orden.pk
            ).values(*campos_orden).get()

            self.assertEqual(len(compras_antes), 3)
            self.assertEqual(len(ventas_antes), 2)

            # Aplicar la migracion sobre los datos historicos.
            executor = MigrationExecutor(connection)

            executor.migrate([siguiente])

            executor = MigrationExecutor(connection)

            apps = executor.loader.project_state(
                [siguiente]
            ).apps

            Compra = apps.get_model(
                "app", "HistorialCompra"
            )

            Venta = apps.get_model(
                "app", "HistorialVenta"
            )

            Orden = apps.get_model(
                "app", "WebpayTransaction"
            )

            Licencia = apps.get_model(
                "app", "Licencia"
            )

            compras = Compra.objects.filter(
                usuario_id=perfil_comprador.pk
            )

            compras_despues = list(
                compras.order_by("pk").values(
                    *campos_compra
                )
            )

            ventas_despues = list(
                Venta.objects.filter(
                    comprador_id=comprador.pk
                ).order_by("pk").values(*campos_venta)
            )

            orden_despues = Orden.objects.filter(
                pk=orden.pk
            ).values(*campos_orden).get()

            # Conservar todos los registros originales.
            self.assertEqual(
                compras_antes,
                compras_despues,
            )

            self.assertEqual(
                ventas_antes,
                ventas_despues,
            )

            self.assertEqual(
                orden_antes,
                orden_despues,
            )

            # Ningun origen se deduce automaticamente.
            self.assertEqual(compras.count(), 3)

            self.assertEqual(
                compras.filter(
                    origen_adquisicion="unknown"
                ).count(),
                3,
            )

            # La migracion no debe inventar licencias.
            self.assertFalse(
                Licencia.objects.filter(
                    compra_id__in=compras.values("pk")
                ).exists()
            )

        finally:
            # Restaurar todas las migraciones finales de pruebas.
            executor = MigrationExecutor(connection)
            executor.migrate(finales)
