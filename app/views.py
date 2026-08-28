from django.contrib.auth.tokens import default_token_generator
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
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password1'])
                user.save()

                # crear y guardar el objeto Usuario asociado al usuario
                usuario = Usuario(
                    user=user,
                    tipo_usu=form.cleaned_data['tipo_usu'],
                    foto_perfil=request.FILES.get('foto_perfil'),
                    foto_fondo=request.FILES.get('foto_fondo'),
                )
                usuario.save()
                return redirect('inicio')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'registration/registro.html', {'form': form})


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
    if request.method == 'GET':
        # Obtener el usuario comprador y las ventas del carrito
        usuario_comprador = Usuario.objects.get(user=request.user)
        ventas = Venta.objects.filter(usuario_id=usuario_comprador.id)
        # Realizar las operaciones necesarias con las ventas
        with transaction.atomic():
            for venta in ventas:
                # Verificar si el producto ya existe en el historial de compras del comprador
                historial_compra, created = HistorialCompra.objects.get_or_create(usuario=usuario_comprador, track=venta.track)
                if created:
                    historial_compra.save()

                # Registrar la venta en el historial de ventas con el comprador
                historial_venta = HistorialVenta.objects.create(
                    comprador=usuario_comprador.user,
                    precio=venta.track.precio,
                    track=venta.track
                )

                # Eliminar la venta del carrito
                venta.delete()

        return render(request, 'app/exito.html')


@csrf_exempt
def cancelado(request):
    return render(request, 'app/cancelado.html')

@csrf_exempt
def pago(request):
    usuario = Usuario.objects.get(user=request.user)
    ventas = Venta.objects.filter(usuario_id=usuario.id)
    precio_total = sum(venta.precio for venta in ventas)
    iva_total = sum(venta.iva for venta in ventas)
    precio_total_con_iva = precio_total + iva_total

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
            # Ocurrió un error en la transacción de Transbank, puedes mostrar un mensaje de error o redirigir a una página de error
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

@require_POST
def eliminar_del_carrito(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
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
    return render(request, 'recuperar_contrasena_success.html')

def recuperar_contrasena(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            return render(request, 'recuperar_contrasena_success.html')
        except User.DoesNotExist:
            return render(request, 'recuperar_contrasena.html', {'error': 'El correo electrónico no está registrado.'})
    else:
        return render(request, 'registration/recuperar_contrasena.html')


def eliminar_del_carrito(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    venta.delete()
    return redirect('carrito')

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