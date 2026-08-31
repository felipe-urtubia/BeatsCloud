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
import mimetypes

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
    track = get_object_or_404(
        Track,
        id_track=track_id,
        usuario=request.user.usuario,
    )

    # Si el track ya fue comprado, permitimos editar sus datos,
    # pero no reemplazar el archivo de audio para no cambiar
    # lo que ya adquirieron otros usuarios.
    tiene_compras = (
        HistorialVenta.objects.filter(track=track).exists()
        or HistorialCompra.objects.filter(track=track).exists()
    )

    if request.method == 'POST':
        form = TrackForm(
            request.POST,
            request.FILES,
            instance=track,
        )

        if tiene_compras and request.FILES.get('track'):
            form.add_error(
                'track',
                'Este track ya tiene compras y el archivo de audio no puede reemplazarse.'
            )

        if form.is_valid():
            track_actualizado = form.save(commit=False)

            # Conservamos siempre al dueño original.
            track_actualizado.usuario = request.user.usuario
            track_actualizado.save()

            messages.success(
                request,
                f'El track "{track_actualizado.nombre_track}" fue actualizado correctamente.'
            )
            return redirect('perfil_productor')
    else:
        form = TrackForm(instance=track)

    context = {
        'form': form,
        'track': track,
        'tiene_compras': tiene_compras,
    }

    return render(request, 'app/editar_track.html', context)


@login_required
@require_POST
def eliminar_track(request, track_id):
    track = get_object_or_404(
        Track,
        id_track=track_id,
        usuario=request.user.usuario,
    )

    nombre_track = track.nombre_track
    track.delete()

    messages.success(
        request,
        f'El track "{nombre_track}" fue eliminado correctamente.'
    )
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
    # Solo los productores pueden acceder a la subida de tracks.
    if request.user.usuario.tipo_usu != Usuario.PRODUCTOR:
        messages.error(request, 'Solo los productores pueden subir pistas.')
        return redirect('perfil')

    if request.method == 'POST':
        form = TrackForm(request.POST, request.FILES)

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
            usuario = request.user.usuario

            track = form.save(commit=False)
            track.usuario = usuario
            track.save()

            messages.success(request, 'Track subido correctamente.')
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
    }

    return render(request, 'app/detalle_track.html', context)


@require_GET
def reproducir_track(request, track_id):
    """
    Reproduce el audio mediante una vista de Django en lugar de exponer
    directamente la ruta física /media/canciones/...
    """
    track = get_object_or_404(Track, id_track=track_id)

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
    track = get_object_or_404(Track, id_track=track_id)
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
@login_required
@csrf_exempt
def exito(request):
    """
    Retorno de Webpay Plus para el pago de suscripción.

    Esta vista ya NO registra compras del carrito.
    Solo muestra éxito si Transbank confirma que la transacción fue autorizada.
    """
    token_ws = request.POST.get('token_ws') or request.GET.get('token_ws')

    if not token_ws:
        print(
            "PAGO SUSCRIPCION CANCELADO O SIN TOKEN:",
            dict(request.POST) if request.method == 'POST' else dict(request.GET)
        )
        return redirect('cancelado')

    try:
        test_commerce_code = "***REMOVED***"
        test_api_key = "***REMOVED***"

        tx = Transaction(
            options=WebpayOptions(
                commerce_code=test_commerce_code,
                api_key=test_api_key,
                integration_type="TEST",
            )
        )

        response = tx.commit(token_ws)

        def tbk_value(name, default=None):
            if isinstance(response, dict):
                return response.get(name, default)
            return getattr(response, name, default)

        response_code = tbk_value('response_code')
        status = tbk_value('status')
        buy_order = str(tbk_value('buy_order', ''))
        session_id = str(tbk_value('session_id', ''))
        amount = tbk_value('amount')

        try:
            response_code_ok = int(response_code) == 0
        except (TypeError, ValueError):
            response_code_ok = False

        if not response_code_ok or str(status).upper() != 'AUTHORIZED':
            print("PAGO SUSCRIPCION RECHAZADO POR TRANSBANK")
            return redirect('cancelado')

        webpay_transaction = WebpayTransaction.objects.filter(
            buy_order=buy_order
        ).first()

        if webpay_transaction is None:
            print("PAGO SUSCRIPCION: buy_order no encontrado:", buy_order)
            return redirect('cancelado')

        try:
            expected_amount = int(round(float(webpay_transaction.amount)))
            paid_amount = int(round(float(amount)))
        except (TypeError, ValueError):
            print("PAGO SUSCRIPCION: monto inválido")
            return redirect('cancelado')

        if expected_amount != paid_amount:
            print(
                "PAGO SUSCRIPCION: monto no coincide.",
                "Esperado:", expected_amount,
                "Pagado:", paid_amount,
            )
            return redirect('cancelado')

        if session_id and str(webpay_transaction.session_id) != session_id:
            print("PAGO SUSCRIPCION: session_id no coincide")
            return redirect('cancelado')

        if webpay_transaction.user_id != request.user.id:
            print("PAGO SUSCRIPCION: la transacción pertenece a otro usuario")
            return redirect('cancelado')

        if webpay_transaction.suscripcion_id is None:
            print("PAGO SUSCRIPCION: la transacción no tiene una suscripción asociada")
            return redirect('cancelado')

        # Solo después de que Transbank confirmó AUTHORIZED marcamos
        # la suscripción como comprada.
        if webpay_transaction.status != WebpayTransaction.ESTADO_AUTORIZADO:
            webpay_transaction.status = WebpayTransaction.ESTADO_AUTORIZADO
            webpay_transaction.save(update_fields=['status'])

        # El carrito mantiene su retorno seguro independiente: exito_carrito().
        return render(request, 'app/exito.html')

    except Exception as e:
        print("ERROR CONFIRMANDO PAGO SUSCRIPCION:", repr(e))
        return redirect('cancelado')


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
            usuario_id=usuario_comprador,
            completada=False,
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

@login_required
@require_POST
def pago(request):
    usuario = get_object_or_404(Usuario, user=request.user)

    # Solo se incluyen productos que todavía están pendientes de pago.
    ventas = Venta.objects.filter(
        usuario_id=usuario,
        completada=False,
    )

    if not ventas.exists():
        messages.info(request, 'Tu carrito no tiene productos pendientes de pago.')
        return redirect('carrito')

    precio_total = sum(venta.precio for venta in ventas)
    iva_total = sum(venta.iva for venta in ventas)
    precio_total_con_iva = int(round(float(precio_total + iva_total)))

    try:
        # Guardar exactamente el monto que se enviará a Webpay.
        transaction = WebpayTransaction.objects.create(
            user=request.user,
            buy_order=str(random.randrange(1000000, 99999999)),
            session_id=request.user.username,
            amount=precio_total_con_iva,
        )

        buy_order = transaction.buy_order
        session_id = transaction.session_id
        return_url = request.build_absolute_uri(reverse('exito_carrito'))
        amount = transaction.amount

        # Credenciales oficiales del ambiente de integración de Webpay Plus.
        test_commerce_code = "***REMOVED***"
        test_api_key = "***REMOVED***"

        tx = Transaction(
            options=WebpayOptions(
                commerce_code=test_commerce_code,
                api_key=test_api_key,
                integration_type="TEST",
            )
        )

        response = tx.create(
            buy_order,
            session_id,
            amount,
            return_url,
        )

        token_ws = response['token']
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
    usuario = get_object_or_404(Usuario, user=request.user)

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

@login_required
def realizar_pago(request, suscripcion_id):
    suscripcion = get_object_or_404(Suscripcion, id_sus=suscripcion_id)

    # Si esta cuenta ya compró esta misma suscripción y el pago fue
    # autorizado por Webpay, no permitimos volver a cobrarla.
    ya_suscrito = WebpayTransaction.objects.filter(
        user=request.user,
        suscripcion=suscripcion,
        status=WebpayTransaction.ESTADO_AUTORIZADO,
    ).exists()

    if ya_suscrito:
        messages.info(
            request,
            'Ya compraste esta suscripción anteriormente.'
        )
        return redirect(
            'perfil_productor1',
            username=suscripcion.user.user.username,
        )

    if request.method == 'POST':
        try:
            # Crear una instancia de WebpayTransaction y guardarla en la base de datos
            transaction = WebpayTransaction.objects.create(
                user=request.user,
                buy_order=str(random.randrange(1000000, 99999999)),
                session_id=request.user.username,
                amount=suscripcion.precio,
                suscripcion=suscripcion,
                status=WebpayTransaction.ESTADO_PENDIENTE,
            )
            # Obtener los datos necesarios de la transacción
            buy_order = transaction.buy_order
            session_id = transaction.session_id
            return_url = request.build_absolute_uri(reverse('exito'))
            amount = int(round(float(transaction.amount)))

            test_commerce_code = "***REMOVED***"
            test_api_key = "***REMOVED***"

            tx = Transaction(
                options=WebpayOptions(
                    commerce_code=test_commerce_code,
                    api_key=test_api_key,
                    integration_type="TEST",
                )
            )

            response = tx.create(
                buy_order,
                session_id,
                amount,
                return_url,
            )
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
            print("ERROR PAGO SUSCRIPCION TRANSBANK:", repr(e))
            return redirect('cancelado')

    context = {
        "suscripcion": suscripcion,
    }
    return render(request, 'app/suscripcion.html', context)