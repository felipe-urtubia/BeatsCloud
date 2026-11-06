from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from transbank.common.options import WebpayOptions
from transbank.webpay.webpay_plus.transaction import Transaction

from app.models import WebpayTransaction


class Command(BaseCommand):
    help = "Consulta el estado de Webpay sin modificar registros."

    def add_arguments(self, parser):
        parser.add_argument("--orden", required=True)

    def handle(self, *args, **options):
        orden = WebpayTransaction.objects.filter(
            buy_order=options["orden"]
        ).first()

        if orden is None:
            raise CommandError("Orden no encontrada.")

        if not orden.webpay_token:
            raise CommandError(
                "Esta orden no tiene token almacenado. "
                "Requiere conciliacion manual."
            )

        if timezone.now() - orden.timestamp > timedelta(days=7):
            raise CommandError(
                "La orden supera la ventana documentada "
                "de consulta de siete dias."
            )

        tx = Transaction(
            options=WebpayOptions(
                commerce_code=settings.TRANSBANK_COMMERCE_CODE,
                api_key=settings.TRANSBANK_API_KEY,
                integration_type=settings.TRANSBANK_INTEGRATION_TYPE,
            )
        )

        try:
            respuesta = tx.status(orden.webpay_token)
        except Exception as error:
            raise CommandError(
                "No se pudo consultar el estado en Transbank. "
                "No se modifico la orden."
            ) from error

        def campo(nombre):
            if isinstance(respuesta, dict):
                return respuesta.get(nombre)
            return getattr(respuesta, nombre, None)

        try:
            montos_iguales = (
                Decimal(str(campo("amount"))) == orden.amount
            )
        except (InvalidOperation, TypeError, ValueError):
            montos_iguales = False

        coincide = (
            str(campo("buy_order")) == orden.buy_order
            and str(campo("session_id")) == orden.session_id
            and montos_iguales
        )

        try:
            codigo_ok = int(campo("response_code")) == 0
        except (TypeError, ValueError):
            codigo_ok = False

        autorizado = (
            coincide
            and str(campo("status")).upper() == "AUTHORIZED"
            and codigo_ok
        )

        self.stdout.write("===== CONSULTA WEBPAY =====")
        self.stdout.write(f"Orden: {orden.buy_order}")
        self.stdout.write(f"Estado proveedor: {campo('status')}")
        self.stdout.write(
            f"Codigo de respuesta: {campo('response_code')}"
        )
        self.stdout.write(
            f"Datos coinciden: {'SI' if coincide else 'NO'}"
        )
        self.stdout.write(
            f"Autorizacion valida: {'SI' if autorizado else 'NO'}"
        )
        self.stdout.write(
            f"Estado local: {orden.status}"
        )
        self.stdout.write(
            "Entrega local: "
            + ("SI" if orden.fulfilled_at else "NO")
        )
        self.stdout.write(
            "Resultado: consulta informativa. "
            "No se modificaron pagos, entregas ni suscripciones."
        )
