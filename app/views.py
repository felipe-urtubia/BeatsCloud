from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.sessions.models import Session
from pyexpat.errors import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate, login
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
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
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
TRANSBANK_API_KEY = settings.TRANSBANK_API_KEY
TRANSBANK_SHARED_SECRET = settings.TRANSBANK_SHARED_SECRET
TRANSBANK_INTEGRATION_TYPE = settings.TRANSBANK_INTEGRATION_TYPE


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Usuario, Venta, HistorialCompra, Compra
import random
from django.db import transaction
from .models import WebpayTransaction

import uuid

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
    if request.method == 'POST':
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
                        '¡Bienvenido a BeatCloud!\n\n'
                        'Gracias por crear tu cuenta. Para confirmar tu correo y activar '
                        'tu cuenta, abre el siguiente enlace:\n\n'
                        f'{activation_url}\n\n'
                        'Si tú no creaste esta cuenta, puedes ignorar este mensaje.\n\n'
                        'Equipo BeatCloud'
                    )

                    email = EmailMultiAlternatives(
                        subject='Confirma tu cuenta | BeatCloud',
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
                    'No pudimos enviar el correo de confirmación. Revisa la configuración SMTP e inténtalo nuevamente.'
                )
    else:
        form = RegistroUsuarioForm()
    return render(request, 'registration/registro.html', {'form': form})


def activar_cuenta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])
        return render(request, 'registration/cuenta_activada.html')

    return render(request, 'registration/enlace_invalido.html', status=400)


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
    historial_compras = HistorialCompra.objects.filter(usuario=usuario)
    return render(request, 'registration/perfil_artista.html', {'usuario': usuario, 'tracks_gustados': tracks_gustados, 'historial_compras': historial_compras})


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


def eliminar_track(request, track_id):
    # Obtener la instancia del track a eliminar
    track = get_object_or_404(Track, id_track=track_id, usuario=request.user.usuario)

    # Eliminar el track
    track.delete()

    # Redireccionar a la página de perfil del productor
    return redirect('perfil_productor')

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
        'form': form
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
        'form': form
    }

    return render(request, 'app/editar_perfil.html', context)




@login_required
def upload_file(request):
    if request.method == 'POST':
        form = TrackForm(request.POST, request.FILES)
        if form.is_valid():
            # Aquí obtenemos la instancia de Usuario del usuario logueado
            usuario = request.user.usuario

            # Creamos la instancia Track y establecemos el campo usuario con la instancia obtenida
            track = form.save(commit=False)
            track.usuario = usuario
            track.save()

            return redirect('perfil')
    else:
        form = TrackForm()

    return render(request, 'app/subir_archivo.html', {'form': form})

def catalogo(request):
        # Obtener todos los tracks de la base de datos
    tracks = Track.objects.all()

    # Obtener todos los géneros de la base de datos
    generos = Genero_Musical.objects.all()

    # Obtener todos los usuarios de tipo ARTISTA de la base de datos
    usuarios = Usuario.objects.filter(tipo_usu=Usuario.ARTISTA)

    # Obtener el valor del parámetro de búsqueda (si existe)
    query = request.GET.get('q')
    
    # Obtener el valor del parámetro de precio (si existe)
    precio_selected = request.GET.get('precio')
    genero_selected = request.GET.get('genero')

    if genero_selected:
    # Si se ha proporcionado un parámetro de género, filtrar los tracks por género
        tracks = tracks.filter(genero__descripcion=genero_selected)
    if precio_selected:
        # Si se ha proporcionado un parámetro de precio, convertir el valor en un rango de precios
        min_price, max_price = [int(p) for p in precio_selected.split('-')]
        tracks = tracks.filter(precio__gte=min_price, precio__lte=max_price)

    if query:
        # Si se ha proporcionado un parámetro de búsqueda, filtrar los tracks y usuarios por nombre o descripción
        tracks = tracks.filter(
            Q(nombre_track__icontains=query) |
            Q(genero__descripcion__icontains=query)
        )
        usuarios = usuarios.filter(user__username__icontains=query)


    context = {
        'tracks': tracks,
        'generos': generos,
        'usuarios': usuarios,
        'query': query,
        'precio_selected': precio_selected
    }
    return render(request, 'app/catalogo.html', context)

def perfil2(request, username):
    usuario = get_object_or_404(User, username=username)
    tipo_usuario = usuario.usuario.tipo_usu
    
    if tipo_usuario == Usuario.ARTISTA:
        return redirect('perfil_artista1', username=username)
    elif tipo_usuario == Usuario.PRODUCTOR:
        return redirect('perfil_productor1', username=username)


def perfil_artista1(request, username):
    usuario = get_object_or_404(User, username=username)
    perfil = get_object_or_404(Usuario, user=usuario)
    return render(request, 'app/perfil_artista1.html', {'perfil': perfil})

def perfil_productor1(request, username):
    usuario = get_object_or_404(User, username=username)
    perfil = get_object_or_404(Usuario, user=usuario)
    canciones = Track.objects.filter(usuario=perfil)
    suscripcion = Suscripcion.objects.filter(user=perfil).first()
    context = {
        'perfil': perfil,
        'canciones': canciones,
        'suscripcion': suscripcion
    }

    return render(request, 'app/perfil_productor2.html', context)


def detalle_track(request, track_id):
    track = get_object_or_404(Track, id_track=track_id)
    comentarios = track.comentarios.all()

    # Agrega la variable de tipo de perfil al contexto
    context = {
        'track': track,
        'comentarios': comentarios,
        'tipo_usuario': track.usuario.tipo_usu
    }

    return render(request, 'app/detalle_track.html', context)

@login_required
def agregar_comentario(request, track_id):
    if request.method == 'POST':
        contenido = request.POST['contenido']
        track = get_object_or_404(Track, id_track=track_id)

        comentario = Comentario(usuario=request.user, track=track, contenido=contenido)
        comentario.save()

    return HttpResponseRedirect(reverse('detalle', args=[track_id]))

@login_required
def carrito(request):
    usuario = Usuario.objects.get(user=request.user)
    ventas = Venta.objects.filter(usuario_id=usuario.id)
    precio_total = sum(venta.precio for venta in ventas)
    iva_total = sum(venta.iva for venta in ventas)
    precio_total_con_iva = precio_total + iva_total

    context = {
        "ventas": ventas,
        "precio_total": precio_total,
        "precio_total_con_iva": precio_total_con_iva,
    }

    return render(request, 'app/carrito.html', context)
@login_required
def exito(request):
    """
    Flujo existente conservado para compatibilidad con el pago de suscripción.
    El pago del carrito usa exito_carrito(), que valida la respuesta de Transbank.
    """
    if request.method == 'GET':
        usuario_comprador = Usuario.objects.get(user=request.user)
        ventas = Venta.objects.filter(usuario_id=usuario_comprador.id)

        with transaction.atomic():
            for venta in ventas:
                historial_compra, created = HistorialCompra.objects.get_or_create(
                    usuario=usuario_comprador,
                    track=venta.track
                )
                if created:
                    historial_compra.save()

                HistorialVenta.objects.create(
                    comprador=usuario_comprador.user,
                    precio=venta.track.precio,
                    track=venta.track
                )

                venta.delete()

        return render(request, 'app/exito.html')

    return redirect('perfil')


@csrf_exempt
def exito_carrito(request):
    """
    Retorno exclusivo de Webpay Plus para compras del carrito.

    Transbank devuelve token_ws al return_url. Aquí se confirma la transacción
    mediante commit() y SOLO si está autorizada se registra la compra.
    """
    token_ws = request.POST.get('token_ws') or request.GET.get('token_ws')

    # Cuando el usuario cancela/abandona Webpay, Transbank puede retornar
    # parámetros TBK_* en vez de token_ws.
    if not token_ws:
        print(
            "PAGO CARRITO CANCELADO O SIN TOKEN:",
            dict(request.POST) if request.method == 'POST' else dict(request.GET)
        )
        return redirect('cancelado')

    test_commerce_code = "***REMOVED***"
    test_api_key = "***REMOVED***"

    try:
        tx = Transaction(
            options=WebpayOptions(
                commerce_code=test_commerce_code,
                api_key=test_api_key,
                integration_type="TEST",
            )
        )

        response = tx.commit(token_ws)

        # El SDK puede entregar un dict u objeto dependiendo de la versión.
        def tbk_value(name, default=None):
            if isinstance(response, dict):
                return response.get(name, default)
            return getattr(response, name, default)

        response_code = tbk_value('response_code')
        status = tbk_value('status')
        buy_order = str(tbk_value('buy_order', ''))
        session_id = str(tbk_value('session_id', ''))
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
            return redirect('cancelado')

        # Verificar que la respuesta corresponde a una transacción creada
        # previamente por BeatCloud.
        webpay_transaction = WebpayTransaction.objects.filter(
            buy_order=buy_order
        ).first()

        if webpay_transaction is None:
            print("PAGO CARRITO: buy_order no encontrado:", buy_order)
            return redirect('cancelado')

        try:
            expected_amount = int(round(float(webpay_transaction.amount)))
            paid_amount = int(round(float(amount)))
        except (TypeError, ValueError):
            print("PAGO CARRITO: monto inválido en la respuesta")
            return redirect('cancelado')

        if expected_amount != paid_amount:
            print(
                "PAGO CARRITO: monto no coincide.",
                "Esperado:", expected_amount,
                "Pagado:", paid_amount
            )
            return redirect('cancelado')

        if session_id and str(webpay_transaction.session_id) != session_id:
            print("PAGO CARRITO: session_id no coincide")
            return redirect('cancelado')

        usuario_comprador = Usuario.objects.get(
            user=webpay_transaction.user
        )
        ventas = Venta.objects.filter(
            usuario_id=usuario_comprador.id
        )

        if not ventas.exists():
            print("PAGO CARRITO: no hay productos pendientes en el carrito")
            return redirect('cancelado')

        # Validación adicional: el carrito actual debe coincidir con el monto
        # que efectivamente fue pagado.
        total_actual = int(round(sum(
            float(venta.precio) + float(venta.iva)
            for venta in ventas
        )))

        if total_actual != paid_amount:
            print(
                "PAGO CARRITO: el total actual del carrito cambió.",
                "Carrito:", total_actual,
                "Pagado:", paid_amount
            )
            return redirect('cancelado')

        # Registrar la compra únicamente después del commit exitoso.
        with transaction.atomic():
            for venta in ventas:
                HistorialCompra.objects.get_or_create(
                    usuario=usuario_comprador,
                    track=venta.track
                )

                HistorialVenta.objects.create(
                    comprador=usuario_comprador.user,
                    precio=venta.track.precio,
                    track=venta.track
                )

                venta.delete()

        return render(
            request,
            'app/exito.html',
            {
                'transbank_response': response,
                'monto_pagado': paid_amount,
                'buy_order': buy_order,
            }
        )

    except Exception as e:
        print("ERROR COMMIT TRANSBANK CARRITO:", repr(e))
        return redirect('cancelado')


@csrf_exempt
def cancelado(request):
    return render(request, 'app/cancelado.html')

@csrf_exempt
def pago(request):
    usuario = Usuario.objects.get(user=request.user)
    ventas = Venta.objects.filter(usuario_id=usuario.id)
    precio_total = sum(venta.precio for venta in ventas)
    iva_total = sum(venta.iva for venta in ventas)
    precio_total_con_iva = int(round(float(precio_total + iva_total)))

    if request.method == 'POST':
        try:
            # Crear una instancia de WebpayTransaction y guardarla en la base de datos
            transaction = WebpayTransaction.objects.create(
                user=request.user,
                buy_order=str(random.randrange(1000000, 99999999)),
                session_id=request.user.username,
                amount=precio_total_con_iva,
            )

            # Obtener los datos necesarios de la transacción
            buy_order = transaction.buy_order
            session_id = transaction.session_id
            return_url = request.build_absolute_uri(reverse('exito_carrito'))
            final_url = request.build_absolute_uri(reverse('cancelado'))
            amount = transaction.amount
            commercecode = TRANSBANK_API_KEY
            apikey = TRANSBANK_SHARED_SECRET

            # Credenciales oficiales del ambiente de integración de Webpay Plus.
            # Son credenciales públicas de PRUEBA de Transbank; no corresponden a producción.
            test_commerce_code = "***REMOVED***"
            test_api_key = "***REMOVED***"

            tx = Transaction(
                options=WebpayOptions(
                    commerce_code=test_commerce_code,
                    api_key=test_api_key,
                    integration_type="TEST",
                )
            )
            response = tx.create(buy_order, session_id, amount, return_url)
            token_ws = response['token']
            url_webpay = response['url']

            # Realizar el proceso de pago con Transbank
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
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
            }

            return render(request, 'app/pago.html', context)
        except Exception as e:
            # Muestra el error real del pago del carrito en la terminal.
            print("ERROR PAGO TRANSBANK:", repr(e))
            return redirect('cancelado')

    return redirect('carrito')
 

def agregar_al_carrito(request, track_id):
    track = get_object_or_404(Track, id_track=track_id)
    
    precio = track.precio
    iva = 0.19 * precio  # Calcula el IVA como el 19% del precio
    precio_total = precio + iva

    usuario = Usuario.objects.get(user=request.user)
    
        # Guardar la información del track en el carrito


    venta = Venta(detalle=track.nombre_track, fecha=timezone.now(), precio=precio, iva=iva, precio_total=precio_total, usuario_id=usuario, track = track)
    venta.save()

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
def dar_like(request, track_id):
    # Obtener el track
    track = get_object_or_404(Track, id_track=track_id)

    # Obtener el perfil del usuario actual
    perfil_usuario = request.user.usuario

    # Guardar el track en el perfil del usuario
    perfil_usuario.tracks_gustados.add(track)

    # Redirigir a la página de detalle del track
    return redirect('detalle', track_id=track_id)

def recuperar_contrasena_success(request):
    # Compatibilidad con la ruta antigua: ahora solo muestra que el correo fue enviado.
    return render(request, 'registration/password_reset_done.html')

def recuperar_contrasena(request):
    # Flujo seguro oficial de Django: nunca cambia la contraseña solo conociendo el correo.
    view = PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.txt',
        html_email_template_name='emails/restablecer_contrasena.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url=reverse('beatcloud_password_reset_done'),
    )
    return view(request)


def catalogo_usuarios(request):
    usuarios = Usuario.objects.all()
    return render(request, 'app/catalogo_usuarios.html', {'usuarios': usuarios})

def ingresar_suscripcion_view(request):
    if request.method == 'POST':
        detalle = request.POST.get('detalle')
        precio = request.POST.get('precio')
        user = request.user.usuario

        # Crear una nueva instancia de Suscripcion
        suscripcion = Suscripcion(detalle=detalle, precio=precio, user=user)
        suscripcion.save()

        return redirect('perfil_productor')

    return render(request, 'app/ingresar_suscripcion.html')

@csrf_exempt
def realizar_pago(request, suscripcion_id):
    suscripcion = Suscripcion.objects.get(id_sus=suscripcion_id)
    
    if request.method == 'POST':
        try:
            # Crear una instancia de WebpayTransaction y guardarla en la base de datos
            transaction = WebpayTransaction.objects.create(
                user=request.user,
                buy_order=str(random.randrange(1000000, 99999999)),
                session_id=request.user.username,
                amount=suscripcion.precio,
            )
            suscripcion.usuario = request.user
            suscripcion.save()
            # Obtener los datos necesarios de la transacción
            buy_order = transaction.buy_order
            session_id = transaction.session_id
            return_url = request.build_absolute_uri(reverse('exito'))
            final_url = request.build_absolute_uri(reverse('cancelado'))
            amount = transaction.amount
            commercecode = TRANSBANK_API_KEY
            apikey = TRANSBANK_SHARED_SECRET

            tx = Transaction(options=WebpayOptions(commerce_code=commercecode, api_key=apikey, integration_type="TEST"))
            response = tx.create(buy_order, session_id, amount, return_url)
            token_ws = response['token']
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
            }

            return render(request, 'app/pago.html', context)
        except Exception as e:
            # Ocurrió un error en la transacción de Transbank, puedes mostrar un mensaje de error o redirigir a una página de error
            return redirect('cancelado')

    context = {
        "suscripcion": suscripcion,
    }
    return render(request, 'app/suscripcion.html', context)