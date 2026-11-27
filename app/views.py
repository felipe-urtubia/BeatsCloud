from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import FileResponse
from django.contrib.sessions.models import Session
from pyexpat.errors import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect,  HttpResponseRedirect
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse
from .forms import RegistroUsuarioForm, TrackForm
from django.contrib.auth.models import User
from .models import Genero_Musical, Usuario, Track, Comentario, Venta, HistorialCompra, Carrito, Compra, Suscripcion, HistorialVenta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UsuarioUpdateForm
import mutagen
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import render, redirect
import stripe
from django.conf import settings
from django.template.loader import render_to_string
from transbank import webpay
from transbank.common import options
from django.db import transaction
from .models import Usuario, Venta, HistorialCompra
# Create your views here.
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from transbank.error.transbank_error import TransbankError
from transbank.webpay.webpay_plus.transaction import Transaction
from .models import Venta
from transbank.error.transbank_error import TransbankError
from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Usuario, Venta, HistorialCompra, Compra
import random
from django.db import transaction
from .models import WebpayTransaction

import uuid
import mimetypes
import secrets
from .audio_utils import generar_preview_audio

ANON_USER_USERNAME = 'UsuarioAnonimo'


def _obtener_perfil_anonimo():
    """Perfil técnico para conservar contenido comprado de cuentas eliminadas."""
    user_anonimo, creado = User.objects.get_or_create(
        username=ANON_USER_USERNAME,
        defaults={
            'first_name': 'Usuario',
            'last_name': 'Anónimo',
            'email': '',
            'is_active': False,
        },
    )

    cambios = []
    if user_anonimo.is_active:
        user_anonimo.is_active = False
        cambios.append('is_active')
    if user_anonimo.email:
        user_anonimo.email = ''
        cambios.append('email')
    if user_anonimo.first_name != 'Usuario':
        user_anonimo.first_name = 'Usuario'
        cambios.append('first_name')
    if user_anonimo.last_name != 'Anónimo':
        user_anonimo.last_name = 'Anónimo'
        cambios.append('last_name')
    if creado or user_anonimo.has_usable_password():
        user_anonimo.set_unusable_password()
        cambios.append('password')
    if cambios:
        user_anonimo.save(update_fields=list(dict.fromkeys(cambios)))

    perfil_anonimo, _ = Usuario.objects.get_or_create(
        user=user_anonimo,
        defaults={
            'tipo_usu': Usuario.PRODUCTOR,
            'descripcion': 'Contenido conservado para compradores de una cuenta eliminada.',
        },
    )

    cambios_perfil = []
    if perfil_anonimo.tipo_usu != Usuario.PRODUCTOR:
        perfil_anonimo.tipo_usu = Usuario.PRODUCTOR
        cambios_perfil.append('tipo_usu')
    descripcion_anonima = 'Contenido conservado para compradores de una cuenta eliminada.'
    if perfil_anonimo.descripcion != descripcion_anonima:
        perfil_anonimo.descripcion = descripcion_anonima
        cambios_perfil.append('descripcion')
    for campo in ('spotify', 'youtube', 'instagram'):
        if getattr(perfil_anonimo, campo):
            setattr(perfil_anonimo, campo, None)
            cambios_perfil.append(campo)
    if cambios_perfil:
        perfil_anonimo.save(update_fields=cambios_perfil)

    return perfil_anonimo


def _programar_borrado_archivo(campo_archivo):
    if not campo_archivo or not campo_archivo.name:
        return

    storage = campo_archivo.storage
    nombre = campo_archivo.name

    def borrar():
        try:
            if storage.exists(nombre):
                storage.delete(nombre)
        except Exception:
            pass

    transaction.on_commit(borrar)



@login_required
def eliminar_cuenta(request):
    usuario = get_object_or_404(Usuario, user=request.user)

    if request.method == 'GET':
        return render(
            request,
            'app/eliminar_cuenta.html',
            {
                'usuario': usuario,
                'verificacion_enviada': False,
            },
        )

    password = request.POST.get('password', '')

    if not request.user.check_password(password):
        messages.error(
            request,
            'La contraseña no es correcta. Tu cuenta no fue eliminada.'
        )
        return render(
            request,
            'app/eliminar_cuenta.html',
            {
                'usuario': usuario,
                'verificacion_enviada': False,
            },
            status=400,
        )

    if not request.user.email:
        messages.error(
            request,
            'Tu cuenta no tiene un correo registrado. No fue posible iniciar '
            'la verificación de eliminación.'
        )
        return render(
            request,
            'app/eliminar_cuenta.html',
            {
                'usuario': usuario,
                'verificacion_enviada': False,
            },
            status=400,
        )

    codigo = f"{secrets.randbelow(1000000):06d}"

    request.session['eliminar_cuenta_codigo_hash'] = make_password(codigo)
    request.session['eliminar_cuenta_usuario_id'] = request.user.pk
    request.session['eliminar_cuenta_codigo_creado'] = timezone.now().timestamp()
    request.session['eliminar_cuenta_intentos'] = 0

    nombre_correo = request.user.first_name or request.user.username
    text_content = (
        f'Hola {nombre_correo},\n\n'
        'Recibimos una solicitud para eliminar definitivamente tu cuenta '
        'de BeatsCloud.\n\n'
        f'Tu código de verificación es: {codigo}\n\n'
        'Este código vence en 15 minutos. No lo compartas con nadie.\n\n'
        'Si tú no solicitaste eliminar tu cuenta, ignora este correo. '
        'Tu cuenta seguirá activa.\n\n'
        'Equipo BeatsCloud'
    )

    html_content = render_to_string(
        'emails/confirmar_eliminacion_cuenta.html',
        {
            'usuario': request.user,
            'codigo': codigo,
        },
    )

    email = EmailMultiAlternatives(
        subject='Confirma la eliminación de tu cuenta | BeatsCloud',
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[request.user.email],
    )
    email.attach_alternative(html_content, 'text/html')

    try:
        email.send(fail_silently=False)
    except Exception:
        _limpiar_verificacion_eliminacion(request)
        messages.error(
            request,
            'No pudimos enviar el código de verificación. '
            'Tu cuenta no fue eliminada.'
        )
        return render(
            request,
            'app/eliminar_cuenta.html',
            {
                'usuario': usuario,
                'verificacion_enviada': False,
            },
            status=503,
        )

    messages.success(
        request,
        'Te enviamos un código de verificación a tu correo. '
        'Tu cuenta todavía no ha sido eliminada.'
    )

    return render(
        request,
        'app/eliminar_cuenta.html',
        {
            'usuario': usuario,
            'verificacion_enviada': True,
        },
    )


def _limpiar_verificacion_eliminacion(request):
    for clave in (
        'eliminar_cuenta_codigo_hash',
        'eliminar_cuenta_usuario_id',
        'eliminar_cuenta_codigo_creado',
        'eliminar_cuenta_intentos',
    ):
        request.session.pop(clave, None)


@login_required
@require_POST
def confirmar_eliminacion_cuenta(request):
    usuario = get_object_or_404(Usuario, user=request.user)

    codigo_hash = request.session.get('eliminar_cuenta_codigo_hash')
    usuario_id = request.session.get('eliminar_cuenta_usuario_id')
    creado = request.session.get('eliminar_cuenta_codigo_creado')
    intentos = int(request.session.get('eliminar_cuenta_intentos', 0))

    if (
        not codigo_hash
        or not usuario_id
        or creado is None
        or usuario_id != request.user.pk
    ):
        _limpiar_verificacion_eliminacion(request)
        messages.error(
            request,
            'La verificación no es válida o ya terminó. '
            'Solicita un nuevo código.'
        )
        return render(
            request,
            'app/eliminar_cuenta.html',
            {
                'usuario': usuario,
                'verificacion_enviada': False,
            },
            status=400,
        )

    try:
        segundos_transcurridos = (
            timezone.now().timestamp() - float(creado)
        )
    except (TypeError, ValueError):
        segundos_transcurridos = 901

    if segundos_transcurridos > 900:
        _limpiar_verificacion_eliminacion(request)
        messages.error(
            request,
            'El código venció. Solicita uno nuevo para continuar.'
        )
        return render(
            request,
            'app/eliminar_cuenta.html',
            {
                'usuario': usuario,
                'verificacion_enviada': False,
            },
            status=400,
        )

    if intentos >= 5:
        _limpiar_verificacion_eliminacion(request)
        messages.error(
            request,
            'Superaste el máximo de intentos. Solicita un nuevo código.'
        )
        return render(
            request,
            'app/eliminar_cuenta.html',
            {
                'usuario': usuario,
                'verificacion_enviada': False,
            },
            status=400,
        )

    codigo = (request.POST.get('codigo') or '').strip()

    if not check_password(codigo, codigo_hash):
        intentos += 1
        request.session['eliminar_cuenta_intentos'] = intentos

        if intentos >= 5:
            _limpiar_verificacion_eliminacion(request)
            messages.error(
                request,
                'Código incorrecto. Superaste el máximo de intentos; '
                'solicita un nuevo código.'
            )
            return render(
                request,
                'app/eliminar_cuenta.html',
                {
                    'usuario': usuario,
                    'verificacion_enviada': False,
                },
                status=400,
            )

        messages.error(
            request,
            f'Código incorrecto. Te quedan {5 - intentos} intento(s).'
        )
        return render(
            request,
            'app/eliminar_cuenta.html',
            {
                'usuario': usuario,
                'verificacion_enviada': True,
            },
            status=400,
        )

    if _hay_webpay_sin_resolver(request.user):
        messages.error(request, 'Hay pagos por conciliar o entregar. No podemos cerrar la cuenta todavía.')
        return render(
            request, 'app/eliminar_cuenta.html',
            {'usuario': usuario, 'verificacion_enviada': True}, status=409,
        )

    _limpiar_verificacion_eliminacion(request)
    try:
        return _ejecutar_eliminacion_cuenta(request, usuario)
    except EliminacionCuentaConLicencias as exc:
        messages.error(request, str(exc))

        return render(
            request,
            'app/eliminar_cuenta.html',
            {
                'usuario': usuario,
                'verificacion_enviada': False,
            },
            status=409,
        )

    except EliminacionCuentaBloqueada:
        messages.error(request, 'Hay pagos por conciliar o entregar. Solicita un código nuevo después de resolverlos.')
        return render(
            request, 'app/eliminar_cuenta.html',
            {'usuario': usuario, 'verificacion_enviada': False}, status=409,
        )


class EliminacionCuentaBloqueada(Exception):
    """Evita pérdida de órdenes Webpay que todavía se están procesando."""


def _hay_webpay_sin_resolver(user):
    # Excluye únicamente CANCELLED o AUTHORIZED con entrega completada.
    # PENDING, AUTHORIZED sin entrega, y estados desconocidos bloquean.
    return (
        WebpayTransaction.objects.filter(user=user)
        .exclude(status=WebpayTransaction.ESTADO_CANCELADO)
        .exclude(
            status=WebpayTransaction.ESTADO_AUTORIZADO,
            fulfilled_at__isnull=False,
        )
        .exists()
    )


class EliminacionCuentaConLicencias(Exception):
    """Impide destruir registros comerciales protegidos."""


def _seudonimizar_identidad_cuenta(usuario):
    """Retira datos personales conservando los identificadores internos."""

    with transaction.atomic():

        cuenta = User.objects.select_for_update().get(
            pk=usuario.user_id
        )

        from app.r2_account_guard import r2_upload_in_progress

        if r2_upload_in_progress(cuenta.pk):

            raise EliminacionCuentaBloqueada(
                "Hay cargas R2 pendientes de procesamiento."
            )

        perfil = Usuario.objects.select_for_update().get(
            pk=usuario.pk,
            user_id=cuenta.pk,
        )

        # Programar la retirada de fotografias tras confirmar cambios.
        _programar_borrado_archivo(perfil.foto_perfil)
        _programar_borrado_archivo(perfil.foto_fondo)

        # Conservar la PK utilizada por las firmas comerciales.
        cuenta.username = "closed_" + secrets.token_hex(20)
        cuenta.first_name = ""
        cuenta.last_name = ""
        cuenta.email = ""
        cuenta.last_login = None

        cuenta.is_active = False
        cuenta.is_staff = False
        cuenta.is_superuser = False

        cuenta.set_unusable_password()

        cuenta.save(update_fields=[
            "username",
            "first_name",
            "last_name",
            "email",
            "last_login",
            "is_active",
            "is_staff",
            "is_superuser",
            "password",
        ])

        cuenta.groups.clear()
        cuenta.user_permissions.clear()

        # Retirar informacion identificativa del perfil.
        if perfil.cuenta_cerrada_en is None:
            perfil.cuenta_cerrada_en = timezone.now()

        perfil.nombre_artistico = "Usuario eliminado"
        perfil.descripcion = None
        perfil.foto_perfil = None
        perfil.foto_fondo = None
        perfil.spotify = None
        perfil.youtube = None
        perfil.instagram = None

        perfil.save(update_fields=[
            "cuenta_cerrada_en",
            "nombre_artistico",
            "descripcion",
            "foto_perfil",
            "foto_fondo",
            "spotify",
            "youtube",
            "instagram",
        ])

        perfil.tracks_gustados.clear()
        perfil.carrito1.clear()
        perfil.sus.clear()

        # D10: eliminar actividad personal no comercial.
        from .models import Comentario, Interes

        Comentario.objects.filter(
            usuario_id=cuenta.pk
        ).delete()

        Interes.objects.filter(
            usuario_id=cuenta.pk
        ).delete()

        # Las compras, ventas y ordenes comerciales se conservan.
        return cuenta, perfil


def _ejecutar_eliminacion_cuenta(request, usuario):

    from django.db import transaction
    from app.models import Licencia, R2UploadClaim
    from app.r2_account_guard import r2_upload_in_progress

    with transaction.atomic():

        cuenta = (
            User.objects.select_for_update(no_key=True)
            .filter(pk=request.user.pk)
            .first()
        )

        if cuenta is None or not cuenta.is_active:
            raise EliminacionCuentaBloqueada(
                "Cuenta no disponible."
            )

        perfil = (
            Usuario.objects.select_for_update()
            .filter(
                pk=usuario.pk,
                user_id=cuenta.pk,
                cuenta_cerrada_en__isnull=True,
            )
            .first()
        )

        if perfil is None:
            raise EliminacionCuentaBloqueada(
                "Cuenta no disponible."
            )

        if _hay_webpay_sin_resolver(cuenta):
            raise EliminacionCuentaBloqueada(
                "Hay pagos pendientes de conciliacion o entrega."
            )

        if r2_upload_in_progress(cuenta.pk):
            raise EliminacionCuentaBloqueada(
                "Hay cargas R2 pendientes de procesamiento."
            )

        email_destino = cuenta.email
        nombre_destino = cuenta.first_name or cuenta.username

        tracks = list(
            Track.objects.select_for_update()
            .filter(usuario_id=perfil.pk)
            .order_by("pk")
        )

        planes = list(
            Suscripcion.objects.select_for_update()
            .filter(user_id=perfil.pk)
            .order_by("pk")
        )

        conservar = (
            bool(tracks)
            or bool(planes)
            or HistorialCompra.objects.filter(
                usuario_id=perfil.pk
            ).exists()
            or Compra.objects.filter(
                usuario_id=perfil.pk
            ).exists()
            or Venta.objects.filter(
                usuario_id=perfil,
                completada=True,
            ).exists()
            or WebpayTransaction.objects.filter(
                user_id=cuenta.pk
            ).exists()
            or R2UploadClaim.objects.filter(
                owner_id=cuenta.pk
            ).exists()
            or Licencia.objects.filter(
                compra__usuario_id=perfil.pk
            ).exists()
            or Licencia.objects.filter(
                transaccion__user_id=cuenta.pk
            ).exists()
        )

        # Eliminar exclusivamente el carrito pendiente propio.
        # No destruir items de pedidos de otros compradores.
        Venta.objects.filter(
            usuario_id=perfil,
            completada=False,
        ).delete()

        Carrito.objects.filter(
            usuario=perfil
        ).delete()

        if conservar:

            # Mantener archivos, IDs, ventas, compras y licencias.
            for track in tracks:

                campos = []

                if not track.is_retired:
                    track.is_retired = True
                    campos.append("is_retired")

                if (
                    track.storage_backend == "r2"
                    and not track.r2_owner_user_id
                ):
                    track.r2_owner_user_id = cuenta.pk
                    campos.append("r2_owner_user_id")

                if campos:
                    track.save(update_fields=campos)

            # Impedir nuevas contrataciones.
            # No destruir planes ni contratos historicos.
            for plan in planes:

                if plan.activo:
                    plan.activo = False
                    plan.save(update_fields=["activo"])

            _seudonimizar_identidad_cuenta(perfil)

        else:

            # Compatibilidad con cuentas sin registros protegidos.
            _programar_borrado_archivo(perfil.foto_perfil)
            _programar_borrado_archivo(perfil.foto_fondo)

            cuenta.delete()

        def enviar_confirmacion():

            if not email_destino:
                return

            email = EmailMultiAlternatives(
                subject="Cierre de cuenta | BeatsCloud",
                body=(
                    f"Hola {nombre_destino},\\n\\n"
                    "Tu cuenta de BeatsCloud ha sido cerrada. "
                    "El acceso ha sido deshabilitado. "
                    "Cuando corresponde, conservamos registros "
                    "comerciales y tecnicos necesarios para "
                    "proteger las transacciones y los derechos "
                    "de los compradores.\\n\\n"
                    "Equipo BeatsCloud"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_destino],
            )

            email.send(fail_silently=True)

        transaction.on_commit(
            enviar_confirmacion,
            robust=True,
        )

    auth_logout(request)

    return render(
        request,
        "app/cuenta_eliminada.html",
    )


def inicio(request):
    return render(request, 'app/inicio.html')

def sobre_nosotros(request):
    return render(request, 'app/sobre_nosotros.html')


def logout(request):
    auth_logout(request)
    return redirect('inicio')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            # If user is None, then the credentials are invalid
            return render(request, 'login.html', {'error_message': 'Invalid login credentials'})
    else:
        return render(request, 'login.html')


def registro(request):
    from os import environ
    from .turnstile_verification import registration_turnstile_required

    turnstile_site_key = (
        environ.get("TURNSTILE_SITE_KEY", "").strip()
        if registration_turnstile_required()
        else ""
    )

    if request.method == 'POST':
        from .turnstile_verification import (
            registration_turnstile_required,
            verify_registration_turnstile,
        )

        if registration_turnstile_required():
            token = request.POST.get("cf-turnstile-response", "")

            if not verify_registration_turnstile(token):
                form = RegistroUsuarioForm(
                    request.POST, request.FILES
                )
                form.add_error(
                    None,
                    "No pudimos verificar que eres una persona. "
                    "Intenta nuevamente.",
                )
                return render(
                    request,
                    'registration/registro.html',
                    {'form': form, 'turnstile_site_key': turnstile_site_key},
                    status=403,
                )

        form = RegistroUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    # UserCreationForm ya deja la contraseña correctamente hasheada.
                    # La cuenta permanece inactiva hasta confirmar el correo.
                    user.email = form.cleaned_data['email'].strip().lower()
                    user.is_active = False
                    user.save()

                    Usuario.objects.create(
                        user=user,
                        tipo_usu=form.cleaned_data['tipo_usu'],
                        nombre_artistico=form.cleaned_data['nombre_artistico'].strip(),
                        foto_perfil=request.FILES.get('foto_perfil'),
                        foto_fondo=request.FILES.get('foto_fondo'),
                    )

                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = default_token_generator.make_token(user)
                    activation_url = request.build_absolute_uri(
                        reverse('activar_cuenta', kwargs={'uidb64': uid, 'token': token})
                    )

                    # Correo profesional HTML + versión de texto para compatibilidad.
                    email_context = {
                        'usuario': user,
                        'activation_url': activation_url,
                    }

                    html_content = render_to_string(
                        'emails/confirmar_cuenta.html',
                        email_context,
                    )

                    text_content = (
                        f'Hola {user.first_name or user.username},\n\n'
                        '¡Bienvenido a BeatsCloud!\n\n'
                        'Gracias por crear tu cuenta. Para confirmar tu correo y activar '
                        'tu cuenta, abre el siguiente enlace:\n\n'
                        f'{activation_url}\n\n'
                        'Si tú no creaste esta cuenta, puedes ignorar este mensaje.\n\n'
                        'Equipo BeatsCloud'
                    )

                    email = EmailMultiAlternatives(
                        subject='Confirma tu cuenta | BeatsCloud',
                        body=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[user.email],
                    )
                    email.attach_alternative(html_content, 'text/html')
                    email.send(fail_silently=False)

                return render(request, 'registration/revisar_correo.html', {'email': user.email})
            except Exception:
                form.add_error(
                    'email',
                    'No pudimos enviar el correo de confirmación. Inténtalo nuevamente más tarde.'
                )
    else:
        form = RegistroUsuarioForm()
    return render(request, 'registration/registro.html', {'form': form, 'turnstile_site_key': turnstile_site_key})


def activar_cuenta(request, uidb64, token):
    from .account_activation import activate_account_from_token

    if activate_account_from_token(uidb64, token):
        return render(
            request,
            'registration/cuenta_activada.html',
        )

    return render(
        request,
        'registration/enlace_invalido.html',
        status=400,
    )


@login_required
def perfil(request):
    # Obtener el usuario actual
    user = request.user
    # Verificar el tipo de usuario
    if user.usuario.tipo_usu == Usuario.ARTISTA:
        # Redirigir a la página del perfil de artista
        return redirect('perfil_artista')
    elif user.usuario.tipo_usu == Usuario.PRODUCTOR:
        # Redirigir a la página del perfil de productor
        return redirect('perfil_productor')
    
@login_required
def perfil_artista(request):
    usuario = request.user.usuario
    tracks_gustados = usuario.tracks_gustados.all()
    historial_compras = HistorialCompra.objects.filter(
        usuario=usuario
    ).order_by('-fecha_compra')

    historial_suscripciones = WebpayTransaction.objects.filter(
        user=request.user,
        suscripcion__isnull=False,
        status=WebpayTransaction.ESTADO_AUTORIZADO,
    ).select_related(
        'suscripcion',
        'suscripcion__user',
        'suscripcion__user__user',
    ).order_by('-timestamp')

    context = {
        'usuario': usuario,
        'tracks_gustados': tracks_gustados,
        'historial_compras': historial_compras,
        'historial_suscripciones': historial_suscripciones,
    }

    return render(request, 'registration/perfil_artista.html', context)


@login_required
def perfil_productor(request):
    user = request.user
    usuario = user.usuario
    tracks = usuario.track_set.all()  # Reemplaza "usuario.tracks.all()" por "usuario.track_set.all()" si estás utilizando una relación ForeignKey
    suscripciones = Suscripcion.objects.filter(user=usuario).order_by('-id_sus')
    ventas = HistorialVenta.objects.filter(track__in=tracks)
    if suscripciones:
        suscripcion = suscripciones[0]
    else:
        suscripcion = None
     # Obtener el historial de ventas del productor
    return render(request, 'registration/perfil_productor.html', {'usuario': usuario, 'tracks': tracks, 'suscripcion': suscripcion, 'ventas': ventas})


@login_required
def editar_track(request, track_id):

    from django.db import transaction
    from django.http import (
        HttpResponse,
        HttpResponseForbidden,
        HttpResponseNotAllowed,
    )

    from app.r2_account_guard import lock_r2_upload_owner
    from app.forms import ArchivoExistenteProtegido

    if request.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])

    with transaction.atomic():

        if not lock_r2_upload_owner(request.user.pk):

            return HttpResponseForbidden(
                "La cuenta no esta habilitada para editar."
            )

        track = get_object_or_404(
            Track.objects.select_for_update(of=("self",)),
            pk=track_id,
            usuario__user_id=request.user.pk,
        )

        if track.is_retired:

            return HttpResponse(
                "No se puede editar un track retirado.",
                status=409,
            )

        tiene_compras = (
            HistorialVenta.objects.filter(track=track).exists()
            or HistorialCompra.objects.filter(track=track).exists()
        )

        portada_r2 = bool(track.r2_cover_key)

        if request.method == "POST":

            form = TrackForm(
                request.POST,
                request.FILES,
                instance=track,
            )

        else:

            form = TrackForm(instance=track)

        # Proteccion conservadora del audio original.
        # No exigir un archivo local a las canciones R2.
        form.fields["track"] = (
            ArchivoExistenteProtegido.desde_campo(
                form.fields["track"]
            )
        )

        # Una portada R2 solo puede reemplazarse
        # mediante el flujo R2 autorizado.
        if portada_r2:

            form.fields["foto"] = (
                ArchivoExistenteProtegido.desde_campo(
                    form.fields["foto"]
                )
            )

        if request.method == "POST":

            valido = form.is_valid()

            if (
                request.FILES.get("track") is not None
                or "track-clear" in request.POST
            ):

                form.add_error(
                    "track",
                    "El reemplazo de audio esta temporalmente restringido.",
                )

                valido = False

            if portada_r2 and (
                request.FILES.get("foto") is not None
                or "foto-clear" in request.POST
            ):

                form.add_error(
                    "foto",
                    "La portada debe actualizarse mediante R2.",
                )

                valido = False

            if valido and not form.errors:

                permitidos = {
                    "nombre_track",
                    "precio",
                    "foto",
                    "genero",
                    "descripcion",
                    "subgenre",
                    "resource_type",
                    "bpm",
                    "scale_key",
                    "mood",
                    "has_stems",
                    "has_wav",
                    "has_midi",
                    "allow_free_download",
                    "has_watermark",
                    "duration",
                }

                if portada_r2:
                    permitidos.discard("foto")

                campos = sorted(
                    permitidos.intersection(
                        form.changed_data
                    )
                )

                actualizado = form.save(commit=False)

                if campos:

                    actualizado.save(
                        update_fields=campos
                    )

                messages.success(
                    request,
                    "El track fue actualizado correctamente.",
                )

                return redirect("perfil_productor")

        context = {
            "form": form,
            "track": track,
            "tiene_compras": tiene_compras,
            "audio_bloqueado": True,
            "portada_r2": portada_r2,
        }

        return render(
            request,
            "app/editar_track.html",
            context,
        )


@login_required
@require_POST
def eliminar_track(request, track_id):

    from django.db import transaction
    from django.http import (
        HttpResponseForbidden,
        HttpResponseNotAllowed,
    )
    from app.r2_account_guard import lock_r2_upload_owner

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    with transaction.atomic():

        if not lock_r2_upload_owner(request.user.pk):
            return HttpResponseForbidden("Cuenta no habilitada.")

        track = get_object_or_404(
            Track.objects.select_for_update(of=("self",)),
            pk=track_id,
            usuario__user_id=request.user.pk,
        )

        if not track.is_retired:
            track.is_retired = True
            track.save(update_fields=["is_retired"])

        messages.success(
            request,
            "El track fue retirado del catalogo correctamente.",
        )

        return redirect("perfil_productor")

@login_required
def editar_perfil(request):
    usuario = request.user.usuario

    if request.method == 'POST':
        form = UsuarioUpdateForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado.')
            return redirect('perfil')
    else:
        form = UsuarioUpdateForm(instance=usuario)

    context = {
        'form': form,
        'usuario': usuario,
    }

    return render(request, 'app/editar_perfil.html', context)

@login_required
def editar_perfil_p(request):
    usuario = request.user.usuario

    if request.method == 'POST':
        form = UsuarioUpdateForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado.')
            return redirect('perfil')
    else:
        form = UsuarioUpdateForm(instance=usuario)

    context = {
        'form': form,
        'usuario': usuario,
    }

    return render(request, 'app/editar_perfil_p.html', context)





def reproducir_preview_track(request, track_id):
    # Entrega únicamente el archivo de vista previa del track.
    import mimetypes
    from django.http import FileResponse, Http404

    track = get_object_or_404(Track, id_track=track_id, media_status="ready")

    from .track_retirement_access import can_access_retired_track

    if track.is_retired and not can_access_retired_track(request.user, track):
        raise Http404("Track no encontrado.")

    if not track.preview:
        raise Http404("Este track todavía no tiene una vista previa disponible.")

    if getattr(track, "storage_backend", "local") == "r2":
        from app.r2_preview_delivery import r2_preview_response
        return r2_preview_response(track)

    archivo = track.preview.open("rb")
    content_type, _ = mimetypes.guess_type(track.preview.name)

    response = FileResponse(
        archivo,
        content_type=content_type or "audio/mpeg",
    )
    nombre = track.preview.name.replace("\\", "/").rsplit("/", 1)[-1]
    response["Content-Disposition"] = f'inline; filename="{nombre}"'
    return response

@login_required
def upload_file(request):
    # Solo los productores pueden acceder a la subida de tracks.
    from django.db import transaction
    from app.r2_account_guard import lock_r2_upload_owner
    from django.http import HttpResponseForbidden, HttpResponseNotAllowed

    if request.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])

    with transaction.atomic():
        if not lock_r2_upload_owner(request.user.pk):
            return HttpResponseForbidden(
                "La cuenta no esta habilitada para publicar."
            )

        perfil = Usuario.objects.filter(
            user_id=request.user.pk,
            tipo_usu=Usuario.PRODUCTOR,
            cuenta_cerrada_en__isnull=True,
        ).first()

        if perfil is None:
            messages.error(request, 'Solo los productores pueden subir pistas.')
            return redirect('perfil')

        if request.method == 'POST':
            post_data = request.POST.copy()
            post_data.setdefault('resource_type', 'instrumental')
            post_data.setdefault('bpm', '140')
            post_data.setdefault('scale_key', 'Am')
            post_data.setdefault('mood', 'Oscuro')
            post_data.setdefault('has_stems', 'false')
            post_data.setdefault('has_wav', 'true')
            post_data.setdefault('has_midi', 'false')
            post_data.setdefault('allow_free_download', 'false')
            post_data.setdefault('has_watermark', 'true')
            post_data.setdefault('duration', '30')
            form = TrackForm(post_data, request.FILES)

            # Primero dejamos que Django ejecute todas las validaciones del formulario.
            formulario_valido = form.is_valid()
            archivos_validos = True

            archivo_audio = request.FILES.get('track')
            archivo_imagen = request.FILES.get('foto')

            formatos_audio = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'}
            formatos_imagen = {'.jpg', '.jpeg', '.png', '.webp'}

            # Validación adicional del archivo de audio directamente en la vista.
            # Esto evita que un archivo inválido se guarde aunque el navegador
            # permita seleccionarlo manualmente.
            if archivo_audio:
                nombre_audio = archivo_audio.name.lower()
                extension_audio = (
                    '.' + nombre_audio.rsplit('.', 1)[-1]
                    if '.' in nombre_audio
                    else ''
                )

                if extension_audio not in formatos_audio:
                    form.add_error(
                        'track',
                        'Archivo de audio inválido. Solo se permiten '
                        'MP3, WAV, FLAC, M4A, AAC u OGG.'
                    )
                    archivos_validos = False
                else:
                    try:
                        archivo_audio.seek(0)
                        audio_detectado = mutagen.File(archivo_audio)
                        archivo_audio.seek(0)

                        if audio_detectado is None:
                            form.add_error(
                                'track',
                                'El archivo seleccionado no contiene un audio válido.'
                            )
                            archivos_validos = False

                    except Exception:
                        try:
                            archivo_audio.seek(0)
                        except Exception:
                            pass

                        form.add_error(
                            'track',
                            'No fue posible validar el audio. '
                            'Comprueba que el archivo no esté dañado.'
                        )
                        archivos_validos = False
            else:
                form.add_error(
                    'track',
                    'Debes seleccionar un archivo de audio.'
                )
                archivos_validos = False

            # La imagen es opcional, pero si se envía debe tener un formato permitido.
            if archivo_imagen:
                nombre_imagen = archivo_imagen.name.lower()
                extension_imagen = (
                    '.' + nombre_imagen.rsplit('.', 1)[-1]
                    if '.' in nombre_imagen
                    else ''
                )

                if extension_imagen not in formatos_imagen:
                    form.add_error(
                        'foto',
                        'Imagen inválida. Solo se permiten JPG, JPEG, PNG o WEBP.'
                    )
                    archivos_validos = False

            if formulario_valido and archivos_validos:
                usuario = perfil

                track = form.save(commit=False)
                track.usuario = usuario
                track.save()
                try:
                    generar_preview_audio(track)
                except Exception:
                    from django.http import HttpResponse

                    transaction.set_rollback(True)

                    return HttpResponse(
                        "No fue posible generar el preview.",
                        status=500,
                    )

                messages.success(request, 'Track subido correctamente.')
                return redirect('perfil')

        else:
            form = TrackForm()

        return render(request, 'app/subir_archivo.html', {'form': form})

def catalogo(request):
    from .r2_visibility import only_ready_tracks
    # Cargamos los datos relacionados en la misma consulta para evitar
    # consultas repetidas al mostrar productor y género.
    tracks = Track.objects.select_related(
        'usuario__user',
        'genero',
    ).exclude(
        usuario__user__username=ANON_USER_USERNAME,
    )

    tracks = only_ready_tracks(tracks).filter(is_retired=False)

    generos = Genero_Musical.objects.all().order_by('descripcion')

    query = (request.GET.get('q') or '').strip()
    genero_selected = (request.GET.get('genero') or '').strip()
    precio_selected = (request.GET.get('precio') or '').strip()
    orden_selected = (request.GET.get('orden') or 'recientes').strip()

    # Buscar por nombre del track, productor o género.
    if query:
        tracks = tracks.filter(
            Q(nombre_track__icontains=query) |
            Q(usuario__user__username__icontains=query) |
            Q(genero__descripcion__icontains=query)
        )

    if genero_selected:
        tracks = tracks.filter(genero__descripcion=genero_selected)

    # Rangos de precio definidos por la interfaz.
    rangos_precio = {
        '0-5000': (0, 5000),
        '5001-10000': (5001, 10000),
        '10001-20000': (10001, 20000),
    }

    if precio_selected in rangos_precio:
        minimo, maximo = rangos_precio[precio_selected]
        tracks = tracks.filter(precio__gte=minimo, precio__lte=maximo)
    elif precio_selected == '20001-mas':
        tracks = tracks.filter(precio__gte=20001)

    # Ordenamiento.
    ordenes = {
        'recientes': '-id_track',
        'antiguos': 'id_track',
        'precio_menor': 'precio',
        'precio_mayor': '-precio',
        'nombre': 'nombre_track',
    }

    tracks = tracks.order_by(
        ordenes.get(orden_selected, '-id_track')
    )

    # Identificamos los tracks que el usuario autenticado ya compró.
    tracks_comprados = []

    if request.user.is_authenticated:
        perfil_usuario = Usuario.objects.filter(user=request.user).first()

        ids_historial_compra = set()
        if perfil_usuario:
            ids_historial_compra = set(
                HistorialCompra.objects.filter(
                    usuario=perfil_usuario
                ).values_list('track_id', flat=True)
            )

        ids_historial_venta = set(
            HistorialVenta.objects.filter(
                comprador=request.user
            ).values_list('track_id', flat=True)
        )

        tracks_comprados = list(
            ids_historial_compra | ids_historial_venta
        )

    # Guardamos el total antes de paginar.
    total_resultados = tracks.count()

    # Mostramos 6 tracks por página.
    paginator = Paginator(tracks, 6)
    numero_pagina = request.GET.get('page')
    pagina_tracks = paginator.get_page(numero_pagina)

    context = {
        'tracks': pagina_tracks,
        'generos': generos,
        'query': query,
        'genero_selected': genero_selected,
        'precio_selected': precio_selected,
        'orden_selected': orden_selected,
        'total_resultados': total_resultados,
        'tracks_comprados': tracks_comprados,
    }

    return render(request, 'app/catalogo.html', context)

def perfil2(request, username):
    usuario = get_object_or_404(
        User.objects.filter(
            usuario__isnull=False,
            usuario__cuenta_cerrada_en__isnull=True,
        ).exclude(
            username=ANON_USER_USERNAME,
        ),
        username=username,
    )
    tipo_usuario = usuario.usuario.tipo_usu
    
    if tipo_usuario == Usuario.ARTISTA:
        return redirect('perfil_artista1', username=username)
    elif tipo_usuario == Usuario.PRODUCTOR:
        return redirect('perfil_productor1', username=username)


def perfil_artista1(request, username):
    usuario = get_object_or_404(
        User.objects.filter(
            usuario__isnull=False,
            usuario__cuenta_cerrada_en__isnull=True,
        ).exclude(
            username=ANON_USER_USERNAME,
        ),
        username=username,
    )
    perfil = get_object_or_404(Usuario, user=usuario)
    return render(request, 'app/perfil_artista1.html', {'perfil': perfil})

def perfil_productor1(request, username):
    from .r2_visibility import only_ready_tracks
    usuario = get_object_or_404(
        User.objects.filter(
            usuario__isnull=False,
            usuario__cuenta_cerrada_en__isnull=True,
        ).exclude(
            username=ANON_USER_USERNAME,
        ),
        username=username,
    )
    perfil = get_object_or_404(Usuario, user=usuario)
    canciones = only_ready_tracks(Track.objects.filter(usuario=perfil, is_retired=False))
    suscripcion = Suscripcion.objects.filter(
        user=perfil,
        activo=True,
    ).first()
    context = {
        'perfil': perfil,
        'canciones': canciones,
        'suscripcion': suscripcion
    }

    return render(request, 'app/perfil_productor2.html', context)


def detalle_track(request, track_id):
    track = get_object_or_404(Track, id_track=track_id, media_status="ready")

    from django.http import Http404
    from .track_retirement_access import can_access_retired_track

    if track.is_retired and not can_access_retired_track(request.user, track):
        raise Http404("Track no encontrado.")
    comentarios = track.comentarios.all()

    ya_comprado = False
    le_gusta = False

    if request.user.is_authenticated:
        usuario = Usuario.objects.filter(user=request.user).first()

        if usuario is not None:
            ya_comprado = (
                HistorialCompra.objects.filter(
                    usuario=usuario,
                    track=track,
                ).exists()
                or HistorialVenta.objects.filter(
                    comprador=request.user,
                    track=track,
                ).exists()
            )

            le_gusta = usuario.tracks_gustados.filter(
                id_track=track.id_track
            ).exists()

    context = {
        'track': track,
        'comentarios': comentarios,
        'tipo_usuario': track.usuario.tipo_usu,
        'ya_comprado': ya_comprado,
        'le_gusta': le_gusta,
        'audio_completo': (
            ya_comprado
            or (
                request.user.is_authenticated
                and track.usuario.user_id == request.user.id
            )
        ),
    }

    return render(request, 'app/detalle_track.html', context)


@require_GET
def reproducir_track(request, track_id):
    """
    Reproduce el audio mediante una vista de Django en lugar de exponer
    directamente la ruta física /media/canciones/...
    """
    track = get_object_or_404(Track, id_track=track_id, media_status="ready")

    puede_escuchar_completo = False

    if request.user.is_authenticated:
        if track.usuario.user_id == request.user.id:
            puede_escuchar_completo = True
        else:
            usuario = Usuario.objects.filter(user=request.user).first()

            if usuario is not None:
                puede_escuchar_completo = (
                    HistorialCompra.objects.filter(
                        usuario=usuario,
                        track=track,
                    ).exists()
                    or HistorialVenta.objects.filter(
                        comprador=request.user,
                        track=track,
                    ).exists()
                )

    if not puede_escuchar_completo:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden(
            'Debes comprar este track para escuchar el audio completo.'
        )

    if not track.track:
        from django.http import Http404
        raise Http404('El archivo de audio no está disponible.')

    archivo = track.track.open('rb')
    nombre_archivo = track.track.name.rsplit('/', 1)[-1]

    content_type = (
        mimetypes.guess_type(nombre_archivo)[0]
        or 'application/octet-stream'
    )

    response = FileResponse(
        archivo,
        content_type=content_type,
    )

    # El navegador puede reproducirlo, pero no se presenta como descarga.
    response['Content-Disposition'] = (
        f'inline; filename="{nombre_archivo}"'
    )
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'

    return response


@login_required
def descargar_track(request, track_id):
    track = get_object_or_404(Track, id_track=track_id, media_status="ready")
    usuario = get_object_or_404(Usuario, user=request.user)

    ya_comprado = (
        HistorialCompra.objects.filter(
            usuario=usuario,
            track=track,
        ).exists()
        or HistorialVenta.objects.filter(
            comprador=request.user,
            track=track,
        ).exists()
    )

    if not ya_comprado:
        messages.error(
            request,
            'Debes comprar este track antes de poder descargarlo.'
        )
        return redirect('detalle', track_id=track_id)

    if not track.track:
        messages.error(
            request,
            'El archivo de este track no está disponible.'
        )
        return redirect('detalle', track_id=track_id)

    archivo = track.track.open('rb')
    nombre_archivo = track.track.name.rsplit('/', 1)[-1]

    return FileResponse(
        archivo,
        as_attachment=True,
        filename=nombre_archivo,
    )


@login_required
@require_POST
def agregar_comentario(request, track_id):
    contenido = request.POST.get('contenido', '').strip()
    track = get_object_or_404(Track, id_track=track_id)

    if not contenido:
        messages.warning(request, 'El comentario no puede estar vacío.')
        return redirect('detalle', track_id=track_id)

    Comentario.objects.create(
        usuario=request.user,
        track=track,
        contenido=contenido,
    )

    messages.success(request, 'Comentario publicado correctamente.')
    return redirect('detalle', track_id=track_id)


@login_required
@require_POST
def eliminar_comentario(request, comentario_id):
    comentario = get_object_or_404(
        Comentario,
        pk=comentario_id,
        usuario=request.user,
    )

    track_id = comentario.track.id_track
    comentario.delete()

    messages.success(request, 'Comentario eliminado correctamente.')
    return redirect('detalle', track_id=track_id)

@login_required
def carrito(request):
    usuario = get_object_or_404(Usuario, user=request.user)

    # El carrito solo debe mostrar compras pendientes.
    # Las ventas ya completadas quedan en el historial,
    # pero no vuelven a aparecer como productos por pagar.
    ventas = Venta.objects.filter(
        usuario_id=usuario,
        completada=False,
    )

    precio_total = sum(venta.precio for venta in ventas)
    iva_total = sum(venta.iva for venta in ventas)
    precio_total_con_iva = precio_total + iva_total

    context = {
        "ventas": ventas,
        "precio_total": precio_total,
        "precio_total_con_iva": precio_total_con_iva,
    }

    return render(request, 'app/carrito.html', context)

def _respuesta_retorno_webpay(request, resultado):
    if request.GET.get('spa') != '1':
        return None
    frontend_url = settings.FRONTEND_URL.rstrip('/')
    separador = '&' if '?' in frontend_url else '?'
    return HttpResponseRedirect(f'{frontend_url}{separador}pago={resultado}')


@csrf_exempt
def exito(request):
    """
    Retorno de Webpay Plus para el pago de suscripción.
    La conciliación valida el retorno; esta vista conserva la entrega VIP.
    """

    def retorno_revision():
        from django.http import HttpResponse
        return _respuesta_retorno_webpay(
            request, 'revision'
        ) or HttpResponse(
            'El estado del pago requiere verificacion. '
            'Contacta a soporte antes de intentar otro cobro.',
            status=409,
        )

    from .webpay_reconciliation import (
        OUTCOME_ALREADY_FULFILLED,
        OUTCOME_APPROVED,
        OUTCOME_CANCELLED,
        reconcile_webpay_return,
    )

    conciliacion = reconcile_webpay_return(
        request,
        expected_subscription=True,
        transaction_class=Transaction,
        options_class=WebpayOptions,
    )

    if conciliacion.outcome == OUTCOME_ALREADY_FULFILLED:
        return _respuesta_retorno_webpay(
            request, 'exito'
        ) or render(request, 'app/exito.html')

    if conciliacion.outcome == OUTCOME_CANCELLED:
        return _respuesta_retorno_webpay(
            request, 'fracaso'
        ) or redirect('cancelado')

    if conciliacion.outcome != OUTCOME_APPROVED:
        print(
            "PAGO SUSCRIPCION REQUIERE REVISION:",
            conciliacion.reason,
        )
        return retorno_revision()

    webpay_transaction = conciliacion.order
    response = conciliacion.response
    token_ws = conciliacion.token

    if response is None:
        return retorno_revision()

    try:
        # El SDK puede entregar un dict u objeto dependiendo de la versión.
        def tbk_value(name, default=None):
            if isinstance(response, dict):
                return response.get(name, default)
            return getattr(response, name, default)

        response_code = tbk_value('response_code')
        status = tbk_value('status')
        buy_order = str(tbk_value('buy_order', ''))
        session_id = str(tbk_value('session_id') or '').strip()
        amount = tbk_value('amount')

        try:
            response_code_ok = int(response_code) == 0
        except (TypeError, ValueError):
            response_code_ok = False

        if not response_code_ok or str(status).upper() != 'AUTHORIZED':
            return _respuesta_retorno_webpay(
                request, 'fracaso'
            ) or redirect('cancelado')

        # La orden ya fue identificada y validada por el servicio central.
        # Se vuelve a leer para evitar trabajar con una instancia obsoleta.
        webpay_transaction = WebpayTransaction.objects.filter(
            buy_order=buy_order
        ).first()

        if webpay_transaction is None:
            print("PAGO SUSCRIPCION: buy_order no encontrado:", buy_order)
            return retorno_revision()

        if webpay_transaction.archived_for_review:
            print("WEBPAY: orden VIP archivada")
            return retorno_revision()

        try:
            expected_amount = int(round(float(webpay_transaction.amount)))
            paid_amount = int(round(float(amount)))
        except (TypeError, ValueError):
            print("PAGO SUSCRIPCION: monto inválido")
            return retorno_revision()

        if expected_amount != paid_amount:
            print(
                "PAGO SUSCRIPCION: monto no coincide.",
                "Esperado:", expected_amount,
                "Pagado:", paid_amount,
            )
            return retorno_revision()

        stored_session_id = str(webpay_transaction.session_id or '').strip()

        if not session_id or not stored_session_id or stored_session_id != session_id:
            print("PAGO SUSCRIPCION: session_id no coincide")
            return retorno_revision()

        # En producción siempre debe existir y coincidir el token persistido.
        if not token_ws or not webpay_transaction.webpay_token:
            print("PAGO SUSCRIPCION: falta token local")
            return retorno_revision()

        if webpay_transaction.webpay_token != token_ws:
            print("PAGO SUSCRIPCION: token no coincide")
            return retorno_revision()

        if webpay_transaction.suscripcion_id is None:
            print("PAGO SUSCRIPCION: la transacción no tiene suscripción asociada")
            return retorno_revision()

        from django.db import transaction as db_transaction
        from django.utils import timezone

        with db_transaction.atomic():
            orden = WebpayTransaction.objects.select_for_update().get(
                pk=webpay_transaction.pk
            )

            if orden.archived_for_review:
                print("WEBPAY: orden VIP archivada bajo bloqueo")
                return retorno_revision()

            if orden.status not in (
                WebpayTransaction.ESTADO_PENDIENTE,
                WebpayTransaction.ESTADO_AUTORIZADO,
            ):
                return retorno_revision()

            if (
                orden.user_id != webpay_transaction.user_id
                or orden.suscripcion_id != webpay_transaction.suscripcion_id
                or orden.amount != webpay_transaction.amount
                or orden.webpay_token != token_ws
            ):
                return retorno_revision()

            perfil = Usuario.objects.select_for_update().get(
                user_id=orden.user_id
            )

            # ManyToMany: agregar otra vez no duplica la membresía.
            perfil.sus.add(orden.suscripcion_id)

            orden.status = WebpayTransaction.ESTADO_AUTORIZADO
            if orden.fulfilled_at is None:
                orden.fulfilled_at = timezone.now()

            orden.save(update_fields=["status", "fulfilled_at"])

        return _respuesta_retorno_webpay(
            request, 'exito'
        ) or render(request, 'app/exito.html')

    except Exception as e:
        print("ERROR CONFIRMANDO PAGO SUSCRIPCION:", repr(e))
        return retorno_revision()


@csrf_exempt
def exito_carrito(request):
    """
    Retorno exclusivo de Webpay Plus para compras del carrito.
    La conciliación valida la respuesta; esta vista conserva la entrega
    atómica del snapshot original.
    """

    from .webpay_spa_return import (
        cancellation_result,
        cart_spa_return,
    )

    def retorno_revision_inconsistente():
        from django.http import HttpResponse

        return _respuesta_retorno_webpay(
            request, 'revision'
        ) or HttpResponse(
            'La respuesta de Webpay requiere verificacion. '
            'No vuelvas a pagar antes de contactar a soporte.',
            status=409,
        )

    from .webpay_reconciliation import (
        OUTCOME_ALREADY_FULFILLED,
        OUTCOME_APPROVED,
        OUTCOME_CANCELLED,
        reconcile_webpay_return,
    )

    conciliacion = reconcile_webpay_return(
        request,
        expected_subscription=False,
        transaction_class=Transaction,
        options_class=WebpayOptions,
    )

    if conciliacion.outcome == OUTCOME_ALREADY_FULFILLED:
        return cart_spa_return(
            request, 'exito', conciliacion.order
        ) or render(request, 'app/exito.html')

    if conciliacion.outcome == OUTCOME_CANCELLED:
        return cart_spa_return(
            request, cancellation_result(conciliacion)
        ) or redirect('cancelado')

    if conciliacion.outcome != OUTCOME_APPROVED:
        print(
            "PAGO CARRITO REQUIERE REVISION:",
            conciliacion.reason,
        )
        return retorno_revision_inconsistente()

    response = conciliacion.response
    token_ws = conciliacion.token
    if response is None:
        return retorno_revision_inconsistente()

    orden_autorizada_id = None

    try:
        # El SDK puede entregar un dict u objeto dependiendo de la versión.
        def tbk_value(name, default=None):
            if isinstance(response, dict):
                return response.get(name, default)
            return getattr(response, name, default)

        response_code = tbk_value('response_code')
        status = tbk_value('status')
        buy_order = str(tbk_value('buy_order', ''))
        session_id = str(tbk_value('session_id') or '').strip()
        amount = tbk_value('amount')

        print(
            "RESPUESTA TRANSBANK CARRITO:",
            {
                "response_code": response_code,
                "status": status,
                "buy_order": buy_order,
                "session_id": session_id,
                "amount": amount,
            }
        )

        # Webpay Plus considera aprobada una operación con response_code 0
        # y estado AUTHORIZED.
        try:
            response_code_ok = int(response_code) == 0
        except (TypeError, ValueError):
            response_code_ok = False

        if not response_code_ok or str(status).upper() != 'AUTHORIZED':
            print("PAGO CARRITO RECHAZADO POR TRANSBANK")
            return retorno_revision_inconsistente()

        # Verificar que la respuesta corresponde a una transacción creada
        # previamente por BeatCloud.
        webpay_transaction = WebpayTransaction.objects.filter(
            buy_order=buy_order
        ).first()

        if webpay_transaction is None:
            print("PAGO CARRITO: buy_order no encontrado:", buy_order)
            return retorno_revision_inconsistente()

        if (
            not token_ws
            or not webpay_transaction.webpay_token
            or webpay_transaction.webpay_token != token_ws
        ):
            print("PAGO CARRITO: token no coincide con la orden local")
            return retorno_revision_inconsistente()

        if webpay_transaction.archived_for_review:
            print("WEBPAY: orden de carrito archivada")
            from django.http import HttpResponse
            return _respuesta_retorno_webpay(request, 'revision') or HttpResponse(
                "Orden archivada: requiere revision manual.",
                status=409,
            )

        try:
            expected_amount = int(round(float(webpay_transaction.amount)))
            paid_amount = int(round(float(amount)))
        except (TypeError, ValueError):
            print("PAGO CARRITO: monto inválido en la respuesta")
            return retorno_revision_inconsistente()

        if expected_amount != paid_amount:
            print(
                "PAGO CARRITO: monto no coincide.",
                "Esperado:", expected_amount,
                "Pagado:", paid_amount
            )
            return retorno_revision_inconsistente()

        stored_session_id = str(webpay_transaction.session_id or '').strip()

        if not session_id or not stored_session_id or stored_session_id != session_id:
            print("PAGO CARRITO: session_id no coincide")
            return retorno_revision_inconsistente()

        # Orden asociada a una respuesta autorizada y validada.
        orden_autorizada_id = webpay_transaction.pk

        # Procesar exclusivamente el pedido original, nunca el carrito actual.
        def respuesta_revision():
            from django.http import HttpResponse
            return _respuesta_retorno_webpay(request, 'revision') or HttpResponse(
                'Pago autorizado pendiente de revision. No vuelvas a pagar; contacta a soporte.',
                status=409,
            )

        with transaction.atomic():
            orden = WebpayTransaction.objects.select_for_update().get(
                pk=webpay_transaction.pk
            )

            if orden.archived_for_review:
                print("WEBPAY: carrito archivado bajo bloqueo")
                from django.http import HttpResponse
                return _respuesta_retorno_webpay(request, 'revision') or HttpResponse(
                    "Orden archivada: requiere revision manual.",
                    status=409,
                )

            # Una orden cancelada o con estado desconocido nunca se entrega.
            if orden.status not in (
                WebpayTransaction.ESTADO_PENDIENTE,
                WebpayTransaction.ESTADO_AUTORIZADO,
            ):
                return respuesta_revision()

            # Una entrega completada no puede registrarse nuevamente.
            if orden.fulfilled_at is not None:
                return cart_spa_return(request, 'exito', orden) or render(
                    request, 'app/exito.html'
                )

            # Una autorizacion antigua sin entrega requiere conciliacion.
            if orden.status == WebpayTransaction.ESTADO_AUTORIZADO:
                return respuesta_revision()

            snapshot = orden.cart_snapshot

            try:
                if (
                    orden.suscripcion_id is not None
                    or not isinstance(snapshot, list)
                    or not snapshot
                ):
                    raise ValueError("Pedido original no disponible")

                items = []

                for registro in snapshot:
                    if not isinstance(registro, dict):
                        raise ValueError("Elemento invalido")

                    valores = (
                        registro.get("venta_id"),
                        registro.get("track_id"),
                        registro.get("precio"),
                        registro.get("iva"),
                    )

                    if any(type(valor) is not int for valor in valores):
                        raise ValueError("Datos invalidos")

                    venta_id, track_id, precio, iva = valores

                    if venta_id <= 0 or track_id <= 0 or precio < 0 or iva < 0:
                        raise ValueError("Valores invalidos")

                    items.append(valores)

                if (
                    len({item[0] for item in items}) != len(items)
                    or len({item[1] for item in items}) != len(items)
                ):
                    raise ValueError("Productos duplicados")

                if sum(item[2] + item[3] for item in items) != paid_amount:
                    raise ValueError("Monto del pedido no coincide")

            except (TypeError, ValueError) as error:
                print("PEDIDO WEBPAY REQUIERE REVISION:", str(error))
                orden.status = WebpayTransaction.ESTADO_AUTORIZADO
                orden.save(update_fields=["status"])
                return respuesta_revision()

            # Serializar entregas de distintas ordenes del comprador.
            usuario_comprador = Usuario.objects.select_for_update().filter(
                user_id=orden.user_id
            ).first()

            tracks = Track.objects.in_bulk(
                [item[1] for item in items]
            )

            if (
                usuario_comprador is None
                or len(tracks) != len(items)
            ):
                orden.status = WebpayTransaction.ESTADO_AUTORIZADO
                orden.save(update_fields=["status"])
                return respuesta_revision()

            # Verificar el pedido original antes de registrar historial.
            # El bloqueo tambien protege frente a cambios concurrentes.
            ventas_originales = {
                venta.pk: venta
                for venta in Venta.objects.select_for_update().filter(
                    pk__in=[item[0] for item in items],
                    usuario_id=usuario_comprador,
                    completada=False,
                ).order_by("pk")
            }

            pedido_disponible = (
                len(ventas_originales) == len(items)
                and all(
                    ventas_originales[venta_id].track_id == track_id
                    and int(ventas_originales[venta_id].precio) == precio
                    and int(ventas_originales[venta_id].iva) == iva
                    for venta_id, track_id, precio, iva in items
                )
            )

            # Tampoco registrar nuevamente una cancion ya comprada.
            canciones_ya_compradas = (
                HistorialCompra.objects.filter(
                    usuario=usuario_comprador,
                    track_id__in=[item[1] for item in items],
                ).exists()
                or HistorialVenta.objects.filter(
                    comprador=usuario_comprador.user,
                    track_id__in=[item[1] for item in items],
                ).exists()
            )

            if not pedido_disponible or canciones_ya_compradas:
                print(
                    "PAGO CARRITO: pedido ya entregado o modificado.",
                    "Orden:", orden.buy_order,
                )
                orden.status = WebpayTransaction.ESTADO_AUTORIZADO
                orden.save(update_fields=["status"])
                return respuesta_revision()

            # Registrar la entrega una sola vez.
            for venta_id, track_id, precio, iva in items:
                track = tracks[track_id]

                HistorialCompra.objects.create(
                    usuario=usuario_comprador,
                    track=track,
                    origen_adquisicion=HistorialCompra.ORIGEN_WEBPAY,
                )

                HistorialVenta.objects.create(
                    comprador=usuario_comprador.user,
                    precio=precio,
                    track=track,
                )

                # Eliminar solo la venta asociada al pedido original.
                Venta.objects.filter(
                    pk=venta_id,
                    usuario_id=usuario_comprador,
                    track_id=track_id,
                    completada=False,
                ).delete()

            from django.utils import timezone

            orden.status = WebpayTransaction.ESTADO_AUTORIZADO
            orden.fulfilled_at = timezone.now()
            orden.save(update_fields=["status", "fulfilled_at"])

            # D10: emitir las licencias dentro de la misma
            # transaccion atomica que registra la compra.
            from .license_service import issue_license_for_purchase

            for _, track_id, _, _ in items:
                compra = HistorialCompra.objects.get(
                    usuario=usuario_comprador,
                    track_id=track_id,
                )
                issue_license_for_purchase(compra, orden)

        return cart_spa_return(request, 'exito', orden) or render(
            request,
            'app/exito.html',
            {
                'transbank_response': response,
                'monto_pagado': paid_amount,
                'buy_order': buy_order,
            }
        )

    except Exception as e:
        print(
            "ERROR PROCESANDO PAGO CARRITO - REQUIERE REVISION:",
            repr(e),
        )

        # Si la respuesta autorizada ya fue validada, conservar
        # su estado fuera de cualquier transaccion que haya fallado.
        if orden_autorizada_id is not None:
            try:
                WebpayTransaction.objects.filter(
                    pk=orden_autorizada_id,
                    archived_for_review=False
                ).update(
                    status=WebpayTransaction.ESTADO_AUTORIZADO,
                )
            except Exception as error_guardado:
                print(
                    "ERROR GUARDANDO AUTORIZACION WEBPAY:",
                    repr(error_guardado),
                )

        # Si commit() fallo, el resultado tambien puede ser incierto.
        # No afirmar que el pago fue rechazado.
        from django.http import HttpResponse

        return _respuesta_retorno_webpay(request, 'revision') or HttpResponse(
            'No fue posible verificar o completar el pago. '
            'Revisa tu historial y contacta a soporte antes de pagar nuevamente.',
            status=409,
        )




@csrf_exempt
def cancelado(request):
    return render(request, 'app/cancelado.html')


@login_required
@require_POST
def cancelar_pago_pendiente(request, transaction_id):
    webpay_transaction = get_object_or_404(
        WebpayTransaction,
        id=transaction_id,
        user=request.user,
    )

    from .webpay_reconciliation import (
        OUTCOME_APPROVED,
        OUTCOME_CANCELLED,
        reconcile_pending_order,
    )

    resultado = reconcile_pending_order(
        webpay_transaction.pk,
        user_id=request.user.pk,
    )

    if resultado.outcome == OUTCOME_CANCELLED:
        messages.success(
            request,
            'Transbank confirmó que el pago no quedó autorizado. '
            'Ya puedes intentar una nueva compra.'
        )
    elif resultado.outcome == OUTCOME_APPROVED:
        messages.warning(
            request,
            'Transbank confirmó la autorización. La entrega requiere revisión '
            'antes de iniciar otro pago.'
        )
    else:
        messages.warning(
            request,
            'No fue posible confirmar la cancelación con Transbank. '
            'La orden permanece protegida y no debes iniciar otro pago.'
        )

    if webpay_transaction.suscripcion_id:
        return redirect(
            'perfil_productor1',
            username=webpay_transaction.suscripcion.user.user.username,
        )

    return redirect('carrito')


@login_required
@require_POST
def pago(request):
    usuario = get_object_or_404(Usuario, user=request.user)

    # Solo se incluyen productos que todavía están pendientes de pago.
    ventas = list(Venta.objects.filter(
        usuario_id=usuario,
        completada=False,
    ).order_by("pk"))

    if not ventas:
        messages.info(request, 'Tu carrito no tiene productos pendientes de pago.')
        return redirect('carrito')

    cart_snapshot = [
        {
            "venta_id": venta.pk,
            "track_id": venta.track_id,
            "precio": int(venta.precio),
            "iva": int(venta.iva),
        }
        for venta in ventas
    ]

    precio_total = sum(venta.precio for venta in ventas)
    iva_total = sum(venta.iva for venta in ventas)
    precio_total_con_iva = int(round(float(precio_total + iva_total)))

    try:
        # Guardar exactamente el monto que se enviará a Webpay.
        from .webpay_checkout_guard import (
            PaymentStartBlocked, create_pending_webpay_order,
        )
        try:
            transaction = create_pending_webpay_order(
                user=request.user,
                amount=precio_total_con_iva,
                cart_snapshot=cart_snapshot,
            )
        except PaymentStartBlocked as error:
            messages.warning(request, str(error))
            return redirect('carrito')

        buy_order = transaction.buy_order
        session_id = transaction.session_id
        return_url = request.build_absolute_uri(reverse('exito_carrito'))
        amount = transaction.amount

        # Credenciales oficiales del ambiente de integración de Webpay Plus.
        tx = Transaction(
            options=WebpayOptions(
                commerce_code=settings.TRANSBANK_COMMERCE_CODE,
                api_key=settings.TRANSBANK_API_KEY,
                integration_type=settings.TRANSBANK_INTEGRATION_TYPE,
            )
        )

        response = tx.create(
            buy_order,
            session_id,
            amount,
            return_url,
        )

        token_ws = response['token']
        if not isinstance(token_ws, str) or not 1 <= len(token_ws) <= 255:
            raise ValueError("Token Webpay invalido.")
        transaction.webpay_token = token_ws
        transaction.save(update_fields=["webpay_token"])
        url_webpay = response['url']

        context = {
            "ventas": ventas,
            "precio_total": precio_total,
            "precio_total_con_iva": precio_total_con_iva,
            "buy_order": buy_order,
            "session_id": session_id,
            "amount": amount,
            "return_url": return_url,
            "token_ws": token_ws,
            "url_webpay": url_webpay,
            "transaction_id": transaction.id,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
        }

        return render(request, 'app/pago.html', context)

    except Exception as e:
        print("ERROR PAGO TRANSBANK:", repr(e))
        return redirect('cancelado')

 

@login_required
@require_POST
def agregar_al_carrito(request, track_id):
    track = get_object_or_404(Track, id_track=track_id)

    if track.is_retired:
        messages.error(
            request,
            "Este track fue retirado del catalogo y no puede comprarse."
        )
        return redirect("carrito")

    usuario = get_object_or_404(Usuario, user=request.user)

    if track.usuario.user.username == ANON_USER_USERNAME:
        messages.info(
            request,
            'Este track se conserva únicamente para compradores anteriores.'
        )
        return redirect('detalle', track_id=track_id)

    # Impedir recomprar un track que ya fue adquirido.
    # Se revisan ambos historiales para cubrir compras antiguas y actuales.
    ya_comprado = (
        HistorialCompra.objects.filter(
            usuario=usuario,
            track=track,
        ).exists()
        or HistorialVenta.objects.filter(
            comprador=request.user,
            track=track,
        ).exists()
    )

    if ya_comprado:
        messages.info(
            request,
            'Ya compraste este track anteriormente. Puedes descargarlo desde esta página.'
        )
        return redirect('detalle', track_id=track_id)

    # Impedir agregar el mismo track más de una vez al carrito.
    if Venta.objects.filter(
        usuario_id=usuario,
        track=track,
        completada=False,
    ).exists():
        messages.info(
            request,
            'Este track ya está agregado a tu carrito.'
        )
        return redirect('carrito')

    precio = track.precio
    iva = int(round(precio * 0.19))
    precio_total = precio + iva

    Venta.objects.create(
        detalle=track.nombre_track,
        fecha=timezone.now(),
        precio=precio,
        iva=iva,
        precio_total=precio_total,
        usuario_id=usuario,
        track=track,
    )

    messages.success(request, 'Track agregado al carrito.')
    return redirect('carrito')


@login_required
@require_POST
def eliminar_del_carrito(request, venta_id):
    usuario = get_object_or_404(Usuario, user=request.user)

    venta = get_object_or_404(
        Venta,
        pk=venta_id,
        usuario_id=usuario,
        completada=False,
    )

    venta.delete()
    return redirect('carrito')

@login_required
@require_POST
def dar_like(request, track_id):
    track = get_object_or_404(Track, id_track=track_id)
    perfil_usuario = get_object_or_404(Usuario, user=request.user)

    if perfil_usuario.tracks_gustados.filter(id_track=track.id_track).exists():
        perfil_usuario.tracks_gustados.remove(track)
        messages.info(request, 'Quitaste este track de tus Me gusta.')
    else:
        perfil_usuario.tracks_gustados.add(track)
        messages.success(request, 'Este track ahora está en tus Me gusta.')

    return redirect('detalle', track_id=track_id)

def recuperar_contrasena_success(request):
    # Compatibilidad con la ruta antigua: ahora solo muestra que el correo fue enviado.
    return render(request, 'app/password_reset_done.html')

def recuperar_contrasena(request):
    # Flujo seguro oficial de Django: nunca cambia la contraseña solo conociendo el correo.
    from .account_password_reset import BeatsCloudPasswordResetForm

    view = PasswordResetView.as_view(
        form_class=BeatsCloudPasswordResetForm,
        template_name='app/password_reset_form.html',
        email_template_name='registration/password_reset_email.txt',
        html_email_template_name='emails/restablecer_contrasena.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url=reverse('beatcloud_password_reset_done'),
    )
    return view(request)


def catalogo_usuarios(request):
    # Todos los perfiles reales; la cuenta técnica anónima no se lista.
    visibles = (
        Usuario.objects
        .select_related('user')
        .filter(cuenta_cerrada_en__isnull=True)
        .exclude(user__username=ANON_USER_USERNAME)
        .order_by('user__username')
    )

    usuarios = visibles

    tipo = (request.GET.get('tipo') or 'todos').strip().lower()
    query = (request.GET.get('q') or '').strip()

    if tipo == 'artistas':
        usuarios = usuarios.filter(tipo_usu=Usuario.ARTISTA)
    elif tipo == 'productores':
        usuarios = usuarios.filter(tipo_usu=Usuario.PRODUCTOR)
    else:
        tipo = 'todos'

    if query:
        usuarios = usuarios.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

    context = {
        'usuarios': usuarios,
        'tipo': tipo,
        'query': query,
        'total_artistas': visibles.filter(tipo_usu=Usuario.ARTISTA).count(),
        'total_productores': visibles.filter(tipo_usu=Usuario.PRODUCTOR).count(),
    }

    return render(request, 'app/catalogo_usuarios.html', context)

@login_required
def ingresar_suscripcion_view(request):
    from django.http import HttpResponseForbidden, HttpResponseBadRequest
    from django.http import HttpResponseNotAllowed
    from .subscription_plans import validate_subscription_plan

    perfil = Usuario.objects.filter(user=request.user).first()

    if perfil is None or perfil.tipo_usu != Usuario.PRODUCTOR:
        return HttpResponseForbidden(
            "Solo los productores pueden crear planes."
        )

    if request.method == "POST":
        try:
            valores = validate_subscription_plan({
                "detalle": request.POST.get("detalle"),
                "precio": request.POST.get("precio"),
            })
        except ValueError as error:
            return HttpResponseBadRequest(str(error))

        Suscripcion.objects.create(user=perfil, **valores)

        return redirect("perfil_productor")

    if request.method != "GET":
        return HttpResponseNotAllowed(["GET", "POST"])

    return render(request, "app/ingresar_suscripcion.html")


@login_required
def realizar_pago(request, suscripcion_id):
    from django.http import HttpResponseForbidden, HttpResponseNotAllowed

    if request.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])

    perfil = Usuario.objects.filter(user=request.user).first()

    if perfil is None or perfil.tipo_usu != Usuario.ARTISTA:
        return HttpResponseForbidden(
            "Solo los artistas pueden contratar membresías."
        )

    suscripcion = get_object_or_404(
        Suscripcion,
        id_sus=suscripcion_id,
        activo=True,
        user__tipo_usu=Usuario.PRODUCTOR,
        user__user__is_active=True,
    )

    if suscripcion.user.user_id == request.user.id:
        return HttpResponseForbidden(
            "No puedes contratar tu propio plan."
        )

    from .subscription_membership import has_active_subscription

    ya_suscrito = has_active_subscription(
        request.user.pk, suscripcion.pk
    )

    if ya_suscrito:
        messages.info(
            request,
            'Ya tienes una membresía activa para este plan.'
        )
        return redirect(
            'perfil_productor1',
            username=suscripcion.user.user.username,
        )

    if request.method == 'POST':
        try:
            # Crear una instancia de WebpayTransaction y guardarla en la base de datos
            from .webpay_checkout_guard import (
                PaymentStartBlocked, create_pending_webpay_order,
            )
            try:
                transaction = create_pending_webpay_order(
                    user=request.user,
                    amount=int(round(float(suscripcion.precio))),
                    suscripcion=suscripcion,
                )
            except PaymentStartBlocked as error:
                messages.warning(request, str(error))
                return redirect(
                    'perfil_productor1',
                    username=suscripcion.user.user.username,
                )
            # Obtener los datos necesarios de la transacción
            buy_order = transaction.buy_order
            session_id = transaction.session_id
            return_url = request.build_absolute_uri(reverse('exito'))
            amount = int(round(float(transaction.amount)))

            tx = Transaction(
                options=WebpayOptions(
                    commerce_code=settings.TRANSBANK_COMMERCE_CODE,
                    api_key=settings.TRANSBANK_API_KEY,
                    integration_type=settings.TRANSBANK_INTEGRATION_TYPE,
                )
            )

            response = tx.create(
                buy_order,
                session_id,
                amount,
                return_url,
            )
            token_ws = response['token']
            if not isinstance(token_ws, str) or not 1 <= len(token_ws) <= 255:
                raise ValueError("Token Webpay invalido.")
            transaction.webpay_token = token_ws
            transaction.save(update_fields=["webpay_token"])
            url_webpay = response['url']

            # Realizar el proceso de pago con Transbank
            context = {
                "suscripcion": suscripcion,
                "buy_order": buy_order,
                "session_id": session_id,
                "amount": amount,
                "return_url": return_url,
                "token_ws": token_ws,
                "url_webpay": url_webpay,
                "transaction_id": transaction.id,
            }

            return render(request, 'app/pago.html', context)
        except Exception as e:
            print("ERROR PAGO SUSCRIPCION TRANSBANK:", repr(e))
            return redirect('cancelado')

    context = {
        "suscripcion": suscripcion,
    }
    return render(request, 'app/suscripcion.html', context)
