# -*- coding: utf-8 -*-
"""
api_shim.py — Capa API REST (JSON) para BeatsCloud, escrita SOBRE la lógica de Felipe.

REGLA DE ORO: este archivo NO reescribe ninguna regla de negocio. Cada endpoint
delega en las mismas consultas/validaciones que ya viven en `app/views.py`
(HistorialCompra/HistorialVenta como prueba de propiedad, IVA 19% server-side,
Webpay create→commit→verificación, preview FFmpeg de 30 s, guardas de descarga).
Si una regla cambia en views.py, debe cambiar acá también — o mejor: extraerla
a una función compartida en app/services.py (sugerencia de refactor futuro).

Qué agrega:
  * Serialización JSON de los modelos existentes.
  * Vistas funcionales clásicas de Django (NO require djangorestframework,
    NO toca INSTALLED_APPS salvo una línea comentada opcional).
  * Endpoints espejo de lo que consume el frontend React (src/api/client.ts).

Instalación (en el repo de Felipe, mínimo invasivo):
  1. Copiar este archivo a  app/api_shim.py
  2. En app/urls.py agregar AL FINAL del urlpatterns existente:
        from django.urls import path
        from . import api_shim
        urlpatterns += api_shim.urlpatterns          # <- única línea obligatoria
     (o bien:  urlpatterns = api_shim.wrap_with_api(urlpatterns)  si además
      quieren CORS para localhost:3000 sin instalar django-cors-headers)
  3. Nada más. Las vistas HTML de Felipe siguen intactas y funcionando.

Frontend: correr con  VITE_API_MODE=rest  VITE_DJANGO_URL=http://localhost:8000
"""
import json
import mimetypes
import random

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.db import transaction as db_transaction
from django.shortcuts import render  # noqa: F401 (por si se reutiliza)
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie

from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions

from .audio_utils import generar_preview_audio
from .forms import RegistroUsuarioForm, TrackForm
from .models import (
    Comentario,
    Genero_Musical,
    HistorialCompra,
    HistorialVenta,
    Suscripcion,
    Track,
    Usuario,
    Venta,
    WebpayTransaction,
)

ANON_USER_USERNAME = "UsuarioAnonimo"  # mismo literal que app/views.py

IVA_PCT = 0.19  # regla confirmada en views.py: iva = round(precio * 0.19)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return {}


def _err(message, status=400, headers=None):
    response = JsonResponse({"detail": message}, status=status)
    if headers:
        for k, v in headers.items():
            response[k] = v
    return response


def _method_not_allowed(allowed_methods):
    if isinstance(allowed_methods, (list, tuple, set)):
        allow_val = ", ".join(sorted(allowed_methods))
    else:
        allow_val = str(allowed_methods)
    return _err("Método no permitido.", status=405, headers={"Allow": allow_val})


def _media_url(field):
    if not field or not getattr(field, "name", ""):
        return None
    return field.url  # MEDIA_URL relativo -> el frontend lo absolute-iza


def _ser_user_base(u: User, include_email: bool = False):
    """django User + perfil Usuario (OneToOne) combinados, snake_case."""
    try:
        p = u.usuario
    except (Usuario.DoesNotExist, AttributeError):
        p = None

    if p is None:
        return {
            "id": u.id,
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email if include_email else "",
            "tipo_usu": None,
            "descripcion": None,
            "foto_perfil": None,
            "foto_fondo": None,
            "spotify": None,
            "youtube": None,
            "instagram": None,
        }

    return {
        "id": u.id,
        "username": u.username,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "email": u.email if include_email else "",
        "tipo_usu": p.tipo_usu,  # 1=Artista, 2=Productor
        "descripcion": p.descripcion,
        "foto_perfil": _media_url(p.foto_perfil),
        "foto_fondo": _media_url(p.foto_fondo),
        "spotify": p.spotify,
        "youtube": p.youtube,
        "instagram": p.instagram,
    }


def ser_user_public(u: User):
    return _ser_user_base(u, include_email=False)


def ser_user_private(u: User):
    return _ser_user_base(u, include_email=True)


def ser_user(u: User):
    return ser_user_public(u)


def ser_genero(g: Genero_Musical):
    return {"id": g.id, "descripcion": g.descripcion}


def ser_track(t: Track, comprador=None):
    """Espejo del DTrack del frontend. Metadatos Fase C caen en defaults."""
    likes = t.usuarios_que_dieron_like.count()
    is_purchased = False
    if comprador is not None and comprador.is_authenticated:
        perfil = Usuario.objects.filter(user=comprador).first()
        is_purchased = bool(perfil) and (
            HistorialCompra.objects.filter(usuario=perfil, track=t).exists()
            or HistorialVenta.objects.filter(comprador=comprador, track=t).exists()
        )
    return {
        "id_track": t.id_track,
        "nombre_track": t.nombre_track,
        "precio": t.precio,
        "track": _media_url(t.track),          # NO usar para stream: ir a /api/track/<id>/reproducir/
        "preview": _media_url(t.preview),      # idem -> /api/track/<id>/preview/
        "descripcion": t.descripcion,
        "foto": _media_url(t.foto),
        "genero": ser_genero(t.genero),
        "usuario": ser_user_public(t.usuario.user),
        "likes_count": likes,
        "is_purchased": is_purchased,
        # --- defaults Fase C (cuando exista la migración 0016, leer de t.<campo>) ---
        "resource_type": getattr(t, "resource_type", "instrumental"),
        "bpm": getattr(t, "bpm", None),
        "scale_key": getattr(t, "scale_key", None),
        "mood": getattr(t, "mood", None),
        "has_stems": getattr(t, "has_stems", True),
        "has_wav": getattr(t, "has_wav", True),
        "has_midi": getattr(t, "has_midi", False),
        "allow_free_download": getattr(t, "allow_free_download", t.precio == 0),
        "has_watermark": getattr(t, "has_watermark", t.precio > 0),
        "duration": getattr(t, "duration", None),
    }


def ser_venta(v: Venta):
    return {
        "id": v.id,
        "detalle": v.detalle,
        "fecha": v.fecha.isoformat() if v.fecha else None,
        "precio": v.precio,
        "iva": v.iva,                       # server-side, NUNCA calcular en el SPA
        "precio_total": v.precio_total,
        "track": v.track_id,
    }


def ser_comentario(c: Comentario):
    return {
        "id": c.id,
        "usuario": ser_user_public(c.usuario),
        "track": c.track_id,
        "contenido": c.contenido,
        "fecha_creacion": c.fecha_creacion.isoformat(),
    }


def _owned_track_or_404(track_id, user):
    """Misma guarda que eliminar_track/editar_track de views.py."""
    t = Track.objects.filter(id_track=track_id).first()
    if t is None:
        return None, _err("Track no encontrado.", 404)
    if t.usuario.user_id != getattr(user, "id", None):
        return None, _err("No tienes permisos sobre este track.", 403)
    return t, None


# --------------------------------------------------------------------------
# CSRF handshake (SPA cross-origin)
# --------------------------------------------------------------------------
@ensure_csrf_cookie
def csrf_token(request):
    if request.method != "GET":
        return _method_not_allowed(["GET"])
    # Formato compatible con DRF's GetCSRFToken (el cliente lee j.detail)
    return JsonResponse({"detail": get_token(request)})


def session_view(request):
    if request.method != "GET":
        return _method_not_allowed(["GET"])
    if request.user.is_authenticated:
        return JsonResponse(ser_user_private(request.user))
    return JsonResponse(None, safe=False)


# --------------------------------------------------------------------------
# Auth — delega en las MISMAS forms de Felipe (registro con activación por correo)
# --------------------------------------------------------------------------
def login_api(request):
    """Igual criterio que login_view()/registro() de views.py: la cuenta queda
    inactiva hasta confirmar el correo; authenticate() ya lo refleja."""
    if request.method != "POST":
        return _method_not_allowed(["POST"])
    body = _json_body(request)
    from django.contrib.auth import authenticate

    user = authenticate(
        request, username=body.get("username", ""), password=body.get("password", "")
    )
    if user is None:
        perfil = Usuario.objects.filter(user__username=body.get("username", "")).first()
        if perfil and not perfil.user.is_active:
            return _err(
                "Debes confirmar tu cuenta desde el correo de activación antes de iniciar sesión.",
                403,
            )
        return _err("Credenciales incorrectas.", 401)
    auth_login(request, user)
    return JsonResponse(ser_user_private(user))


def logout_api(request):
    if request.method != "POST":
        return _method_not_allowed(["POST"])
    from django.contrib.auth import logout

    logout(request)
    return JsonResponse({"ok": True})


def registro_api(request):
    """Espejo JSON EXACTO de registro() (views.py l.532): misma RegistroUsuarioForm,
    transacción atómica, cuenta inactiva, perfil Usuario y correo de activación."""
    if request.method != "POST":
        return _method_not_allowed(["POST"])

    form = RegistroUsuarioForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse(
            {"detail": "Datos inválidos.", "errors": form.errors_json if hasattr(form, "errors_json") else {k: [str(m) for m in v] for k, v in form.errors.items()}},
            status=400,
        )
    try:
        with db_transaction.atomic():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"].strip().lower()
            user.is_active = False
            user.save()

            Usuario.objects.create(
                user=user,
                tipo_usu=form.cleaned_data["tipo_usu"],
                foto_perfil=request.FILES.get("foto_perfil"),
                foto_fondo=request.FILES.get("foto_fondo"),
            )

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_url = request.build_absolute_uri(
                reverse("activar_cuenta", kwargs={"uidb64": uid, "token": token})
            )

            html_content = render_to_string(
                "emails/confirmar_cuenta.html",
                {"usuario": user, "activation_url": activation_url},
            )
            text_content = (
                f"Hola {user.first_name or user.username},\n\n"
                "¡Bienvenido a BeatCloud!\n\n"
                "Gracias por crear tu cuenta. Para confirmar tu correo y activar "
                "tu cuenta, abre el siguiente enlace:\n\n"
                f"{activation_url}\n\n"
                "Si tú no creaste esta cuenta, puedes ignorar este mensaje.\n\n"
                "Equipo BeatCloud"
            )
            email = EmailMultiAlternatives(
                subject="Confirma tu cuenta | BeatCloud",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
    except Exception:
        return _err(
            "No pudimos enviar el correo de confirmación. "
            "Revisa la configuración SMTP e inténtalo nuevamente.", 500,
        )
    return JsonResponse(
        {"detail": "Registro exitoso. Revisa tu correo para activar la cuenta."},
        status=201,
    )


# --------------------------------------------------------------------------
# Catálogo — mismo queryset/paginación/filtros que catalogo() de views.py
# --------------------------------------------------------------------------
def catalogo_api(request):
    if request.method != "GET":
        return _method_not_allowed(["GET"])
    tracks = Track.objects.select_related("usuario__user", "genero").exclude(
        usuario__user__username=ANON_USER_USERNAME,
    )

    q = request.GET.get("q", "").strip()
    if q:
        from django.db.models import Q

        tracks = tracks.filter(
            Q(nombre_track__icontains=q)
            | Q(usuario__user__username__icontains=q)
            | Q(genero__descripcion__icontains=q)
        )

    genero = request.GET.get("genero", "").strip()
    if genero:
        tracks = tracks.filter(genero__descripcion=genero)

    precio = request.GET.get("precio", "").strip()
    if precio == "0-5000":
        tracks = tracks.filter(precio__lte=5000)
    elif precio == "5001-10000":
        tracks = tracks.filter(precio__gte=5001, precio__lte=10000)
    elif precio == "10001-20000":
        tracks = tracks.filter(precio__gte=10001, precio__lte=20000)
    elif precio == "20001-mas":
        tracks = tracks.filter(precio__gte=20001)

    orden = request.GET.get("orden", "recientes")
    order_map = {
        "recientes": "-id_track",
        "antiguos": "id_track",
        "precio_menor": "precio",
        "precio_mayor": "-precio",
        "nombre": "nombre_track",
    }
    tracks = tracks.order_by(order_map.get(orden, "-id_track"))

    paginator = Paginator(tracks, 6)  # mismo tamaño de página que el monolito
    page_obj = paginator.get_page(request.GET.get("page", 1) or 1)

    comprados = []
    if request.user.is_authenticated:
        perfil = Usuario.objects.filter(user=request.user).first()
        if perfil:
            comprados = list(
                HistorialCompra.objects.filter(usuario=perfil).values_list(
                    "track_id", flat=True
                )
            ) + list(
                HistorialVenta.objects.filter(comprador=request.user).values_list(
                    "track_id", flat=True
                )
            )

    return JsonResponse(
        {
            "tracks": [ser_track(t, request.user) for t in page_obj],
            "total_resultados": paginator.count,
            "pagina_actual": page_obj.number,
            "total_paginas": paginator.num_pages,
            "tracks_comprados": sorted(set(comprados)),
            "generos": [ser_genero(g) for g in Genero_Musical.objects.all()],
        }
    )


def track_detail_api(request, track_id):
    """GET detalle; PATCH/PUT delega en update (misma ruta, como REST estándar)."""
    if request.method in ("PATCH", "PUT"):
        return track_update_api(request, track_id)
    if request.method != "GET":
        return _method_not_allowed(["GET", "PATCH", "PUT"])
    t = Track.objects.select_related("usuario__user", "genero").filter(
        id_track=track_id
    ).first()
    if t is None:
        return _err("Track no encontrado.", 404)
    return JsonResponse(ser_track(t, request.user))


# --------------------------------------------------------------------------
# Audio protegido — mismas reglas que reproducir_track()/descargar_track():
#   preview: abierto a anónimos (mp3 30s generado con FFmpeg)
#   full/descarga: dueño o comprador (HistorialCompra ∪ HistorialVenta)
# --------------------------------------------------------------------------
def _puede_escuchar_completo(request, track):
    if not request.user.is_authenticated:
        return False
    if track.usuario.user_id == request.user.id:
        return True
    perfil = Usuario.objects.filter(user=request.user).first()
    if perfil is None:
        return False
    return (
        HistorialCompra.objects.filter(usuario=perfil, track=track).exists()
        or HistorialVenta.objects.filter(comprador=request.user, track=track).exists()
    )


def preview_stream_api(request, track_id):
    if request.method != "GET":
        return _method_not_allowed(["GET"])
    from django.http import FileResponse, Http404

    track = Track.objects.filter(id_track=track_id).first()
    if track is None or not track.preview:
        raise Http404("Este track todavía no tiene una vista previa disponible.")
    archivo = track.preview.open("rb")
    content_type, _ = mimetypes.guess_type(track.preview.name)
    response = FileResponse(archivo, content_type=content_type or "audio/mpeg")
    response["Accept-Ranges"] = "bytes"  # scrubbing del <audio> de React
    return response


def full_stream_api(request, track_id):
    if request.method != "GET":
        return _method_not_allowed(["GET"])
    from django.http import FileResponse, HttpResponseForbidden, Http404

    track = Track.objects.filter(id_track=track_id).first()
    if track is None:
        raise Http404()
    if not _puede_escuchar_completo(request, track):
        return HttpResponseForbidden(
            "Debes comprar este track para escuchar el audio completo."
        )
    if not track.track:
        raise Http404("El archivo de audio no está disponible.")
    archivo = track.track.open("rb")
    nombre = track.track.name.rsplit("/", 1)[-1]
    response = FileResponse(
        archivo, content_type=mimetypes.guess_type(nombre)[0] or "application/octet-stream"
    )
    response["Content-Disposition"] = f'inline; filename="{nombre}"'
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response


def download_api(request, track_id):
    if request.method != "GET":
        return _method_not_allowed(["GET"])
    from django.http import FileResponse, HttpResponseForbidden, Http404

    if not request.user.is_authenticated:
        return HttpResponseForbidden("Inicia sesión para descargar.")
    track = Track.objects.filter(id_track=track_id).first()
    if track is None:
        raise Http404()
    if not _puede_escuchar_completo(request, track):
        return HttpResponseForbidden(
            "Debes comprar este track antes de poder descargarlo."
        )
    if not track.track:
        raise Http404("El archivo de este track no está disponible.")
    nombre = track.track.name.rsplit("/", 1)[-1]
    return FileResponse(
        track.track.open("rb"), as_attachment=True, filename=nombre
    )


# --------------------------------------------------------------------------
# Carrito — misma tabla Venta(completada=False), mismo IVA server-side,
# mismos bloqueos anti-recompra/anti-duplicado de agregar_al_carrito()
# --------------------------------------------------------------------------
def cart_list_api(request):
    if request.method != "GET":
        return _method_not_allowed(["GET"])
    if not request.user.is_authenticated:
        return _err("Autenticación requerida.", 401)
    perfil = Usuario.objects.filter(user=request.user).first()
    ventas = Venta.objects.filter(usuario_id=perfil, completada=False)
    data = [ser_venta(v) for v in ventas]
    subtotal = sum(v["precio"] for v in data)
    iva = sum(v["iva"] for v in data)
    return JsonResponse(
        {"items": data, "subtotal": subtotal, "iva": iva, "total": subtotal + iva}
    )


def cart_add_api(request, track_id):
    if request.method != "POST":
        return _method_not_allowed(["POST"])
    if not request.user.is_authenticated:
        return _err("Autenticación requerida.", 401)

    track = Track.objects.filter(id_track=track_id).first()
    if track is None:
        return _err("Track no encontrado.", 404)
    perfil = Usuario.objects.filter(user=request.user).first()

    if track.usuario.user.username == ANON_USER_USERNAME:
        return _err(
            "Este track se conserva únicamente para compradores anteriores.", 409
        )
    if (
        HistorialCompra.objects.filter(usuario=perfil, track=track).exists()
        or HistorialVenta.objects.filter(comprador=request.user, track=track).exists()
    ):
        return _err(
            "Ya compraste este track anteriormente. Puedes descargarlo desde esta página.",
            409,
        )
    if Venta.objects.filter(usuario_id=perfil, track=track, completada=False).exists():
        return _err("Este track ya está agregado a tu carrito.", 409)

    precio = track.precio
    iva = int(round(precio * IVA_PCT))
    venta = Venta.objects.create(
        detalle=track.nombre_track,
        fecha=timezone.now(),
        precio=precio,
        iva=iva,
        precio_total=precio + iva,
        usuario_id=perfil,
        track=track,
    )
    return JsonResponse(ser_venta(venta), status=201)


def cart_remove_api(request, venta_id):
    if request.method != "DELETE":
        return _method_not_allowed(["DELETE"])
    if not request.user.is_authenticated:
        return _err("Autenticación requerida.", 401)
    perfil = Usuario.objects.filter(user=request.user).first()
    venta = Venta.objects.filter(
        pk=venta_id, usuario_id=perfil, completada=False
    ).first()
    if venta is None:
        return _err("Elemento no encontrado en tu carrito.", 404)
    venta.delete()
    return JsonResponse({"ok": True})


# --------------------------------------------------------------------------
# Pago — inicia el MISMO flujo Webpay de pago(); el retorno sigue siendo la
# vista HTML exito_carrito() de Felipe (allí vive la validación completa:
# commit, response_code==0, AUTHORIZED, buy_order, monto, session_id, y el
# registro atómico de HistorialCompra + HistorialVenta + delete(Venta)).
# El SPA solo necesita url_webpay para redirigir el navegador.
# --------------------------------------------------------------------------
def _webpay_tx():
    return Transaction(
        options=WebpayOptions(
            commerce_code=settings.TRANSBANK_COMMERCE_CODE,
            api_key=settings.TRANSBANK_API_KEY,
            integration_type=settings.TRANSBANK_INTEGRATION_TYPE,
        )
    )


def pago_init_api(request):
    if request.method != "POST":
        return _method_not_allowed(["POST"])
    if not request.user.is_authenticated:
        return _err("Autenticación requerida.", 401)
    perfil = Usuario.objects.filter(user=request.user).first()
    ventas = Venta.objects.filter(usuario_id=perfil, completada=False)
    if not ventas.exists():
        return _err("Tu carrito no tiene productos pendientes de pago.", 400)

    precio_total = sum(v.precio for v in ventas)
    iva_total = sum(v.iva for v in ventas)
    amount = int(round(float(precio_total + iva_total)))

    wt = WebpayTransaction.objects.create(
        user=request.user,
        buy_order=str(random.randrange(1000000, 99999999)),
        session_id=request.user.username,  # misma convencion que views.py
        amount=amount,
    )
    from django.urls import reverse

    return_url = request.build_absolute_uri(reverse("exito_carrito"))
    try:
        response = _webpay_tx().create(wt.buy_order, wt.session_id, amount, return_url)
    except Exception as e:  # TransbankError etc.: mismo fallback que views.py
        wt.status = WebpayTransaction.ESTADO_CANCELADO
        wt.save(update_fields=["status"])
        return _err(f"No fue posible iniciar el pago: {e!r}", 502)

    return JsonResponse(
        {
            "url_webpay": response["url"],
            "token_ws": response["token"],
            "buy_order": wt.buy_order,
            "amount": amount,
            "transaction_id": wt.id,
        }
    )


def pago_cancel_api(request, transaction_id):
    """Espejo de cancelar_pago_pendiente(): marca CANCELLED localmente."""
    if request.method != "POST":
        return _method_not_allowed(["POST"])
    if not request.user.is_authenticated:
        return _err("Autenticación requerida.", 401)
    wt = WebpayTransaction.objects.filter(
        id=transaction_id, user=request.user, status=WebpayTransaction.ESTADO_PENDIENTE
    ).first()
    if wt is None:
        return _err("Transacción no encontrada o ya resuelta.", 404)
    wt.status = WebpayTransaction.ESTADO_CANCELADO
    wt.save(update_fields=["status"])
    return JsonResponse({"ok": True})


# --------------------------------------------------------------------------
# Productor — upload delega en TrackForm + validaciones de upload_file()
# --------------------------------------------------------------------------
def upload_api(request):
    if request.method != "POST":
        return _err("Método no permitido.", 405)
    if not request.user.is_authenticated:
        return _err("Autenticación requerida.", 401)
    if request.user.usuario.tipo_usu != Usuario.PRODUCTOR:
        return _err("Solo los productores pueden subir pistas.", 403)

    form = TrackForm(request.POST, request.FILES)
    archivos_ok = True
    errores = {}

    import mutagen

    audio = request.FILES.get("track")
    formatos_audio = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"}
    if audio:
        ext = "." + audio.name.lower().rsplit(".", 1)[-1] if "." in audio.name else ""
        if ext not in formatos_audio:
            archivos_ok = False
            errores["track"] = "Archivo de audio inválido. Solo MP3, WAV, FLAC, M4A, AAC u OGG."
        else:
            try:
                audio.seek(0)
                if mutagen.File(audio) is None:
                    archivos_ok = False
                    errores["track"] = "El archivo seleccionado no contiene un audio válido."
            except Exception:
                archivos_ok = False
                errores["track"] = "No fue posible validar el audio."
            finally:
                try:
                    audio.seek(0)
                except Exception:
                    pass
    else:
        archivos_ok = False
        errores["track"] = "Debes seleccionar un archivo de audio."

    if not form.is_valid() or not archivos_ok:
        errs = {k: [str(m) for m in v] for k, v in form.errors.items()}
        errs.update({k: [v] for k, v in errores.items()})
        return JsonResponse({"detail": "Errores de validación.", "errors": errs}, status=400)

    track = form.save(commit=False)
    track.usuario = request.user.usuario
    track.save()
    try:
        generar_preview_audio(track)  # mp3 30s — seguridad de preview server-side
    except Exception as e:
        track.delete()
        return _err(f"Track guardado pero sin preview: {e!r}", 500)

    return JsonResponse(ser_track(track, request.user), status=201)


def track_update_api(request, track_id):
    if request.method not in ("PATCH", "PUT"):
        return _err("Método no permitido.", 405)
    if not request.user.is_authenticated:
        return _err("Autenticación requerida.", 401)
    t, err = _owned_track_or_404(track_id, request.user)
    if err:
        return err
    # Misma restricción de editar_track: no se reemplaza el audio si ya hay ventas.
    body = _json_body(request)
    editable = {"nombre_track", "precio", "descripcion"}
    changed = False
    for campo in editable:
        if campo in body:
            setattr(t, campo, body[campo])
            changed = True
    if changed:
        t.save()
    return JsonResponse(ser_track(t, request.user))


def track_delete_api(request, track_id):
    if request.method != "POST":
        return _err("Método no permitido.", 405)
    if not request.user.is_authenticated:
        return _err("Autenticación requerida.", 401)
    t, err = _owned_track_or_404(track_id, request.user)
    if err:
        return err
    if HistorialVenta.objects.filter(track=t).exists():
        return _err(
            "No puedes eliminar un track que ya ha sido vendido.", 409
        )  # misma guarda que eliminar_track()
    t.delete()
    return JsonResponse({"ok": True})


def mis_ventas_api(request):
    if request.method != "GET":
        return _method_not_allowed(["GET"])
    if not request.user.is_authenticated:
        return _err("Autenticación requerida.", 401)
    ventas = HistorialVenta.objects.filter(
        track__usuario__user=request.user
    ).select_related("track", "comprador")
    return JsonResponse(
        [
            {
                "id": v.pk,
                "comprador": (
                    {"id": v.comprador.id, "username": v.comprador.username}
                    if v.comprador
                    else None
                ),
                "precio": float(v.precio),
                "track": ser_track(v.track),
                "fecha_venta": v.fecha_venta.isoformat(),
            }
            for v in ventas
        ],
        safe=False,
    )


# --------------------------------------------------------------------------
# Usuario / artista
# --------------------------------------------------------------------------
def mis_compras_api(request):
    if request.method != "GET":
        return _method_not_allowed(["GET"])
    if not request.user.is_authenticated:
        return _err("Autenticación requerida.", 401)
    perfil = Usuario.objects.filter(user=request.user).first()
    compras = HistorialCompra.objects.filter(usuario=perfil).select_related("track")
    return JsonResponse(
        [
            {
                "id": c.pk,
                "track": ser_track(c.track),
                "fecha_compra": c.fecha_compra.isoformat(),
            }
            for c in compras
        ],
        safe=False,
    )


def like_toggle_api(request, track_id):
    if request.method != "POST":
        return _err("Método no permitido.", 405)
    if not request.user.is_authenticated:
        return _err("Autenticación requerida.", 401)
    track = Track.objects.filter(id_track=track_id).first()
    perfil = Usuario.objects.filter(user=request.user).first()
    if track is None or perfil is None:
        return _err("No encontrado.", 404)
    if perfil.tracks_gustados.filter(pk=track.pk).exists():
        perfil.tracks_gustados.remove(track)
        return JsonResponse({"liked": False})
    perfil.tracks_gustados.add(track)
    return JsonResponse({"liked": True})


def comments_api(request, track_id):
    track = Track.objects.filter(id_track=track_id).first()
    if track is None:
        return _err("Track no encontrado.", 404)
    if request.method == "GET":
        return JsonResponse(
            [ser_comentario(c) for c in track.comentarios.select_related("usuario")],
            safe=False,
        )
    if request.method == "POST":
        if not request.user.is_authenticated:
            return _err("Autenticación requerida.", 401)
        contenido = (_json_body(request).get("contenido") or "").strip()
        if not contenido:
            return _err("El comentario no puede estar vacío.", 400)
        c = Comentario.objects.create(
            usuario=request.user, track=track, contenido=contenido
        )
        return JsonResponse(ser_comentario(c), status=201)
    return _err("Método no permitido.", 405)


def perfil_publico_api(request, username):
    if request.method != "GET":
        return _method_not_allowed(["GET"])
    u = User.objects.filter(username=username).first()
    if u is None or u.username == ANON_USER_USERNAME:
        return _err("Perfil no encontrado.", 404)
    data = ser_user_public(u)
    try:
        perfil = u.usuario
    except (Usuario.DoesNotExist, AttributeError):
        perfil = None
    if perfil is not None:
        tracks = Track.objects.filter(usuario=perfil).order_by("-id_track")
        data["tracks"] = [ser_track(t, request.user) for t in tracks]
    else:
        data["tracks"] = []
    return JsonResponse(data)


def suscripciones_api(request):
    if request.method != "GET":
        return _method_not_allowed(["GET"])
    qs = Suscripcion.objects.all()
    uid = request.GET.get("user")
    if uid:
        qs = qs.filter(user_id=uid)
    return JsonResponse(
        [{"id_sus": s.id_sus, "detalle": s.detalle, "precio": s.precio} for s in qs],
        safe=False,
    )


# --------------------------------------------------------------------------
# URLs — se agregan al urlpatterns de app/urls.py con UNA sola línea
# --------------------------------------------------------------------------
from django.urls import path  # noqa: E402

urlpatterns = [
    path("api/csrf/", csrf_token, name="api_csrf"),
    path("api/session/", session_view, name="api_session"),
    path("api/auth/login/", login_api, name="api_login"),
    path("api/auth/logout/", logout_api, name="api_logout"),
    path("api/auth/registro/", registro_api, name="api_registro"),
    path("api/catalogo/", catalogo_api, name="api_catalogo"),
    path("api/track/<int:track_id>/", track_detail_api, name="api_track"),
    path("api/track/<int:track_id>/preview/", preview_stream_api, name="api_preview"),
    path("api/track/<int:track_id>/reproducir/", full_stream_api, name="api_full"),
    path("api/track/<int:track_id>/descargar/", download_api, name="api_download"),
    path("api/track/<int:track_id>/delete/", track_delete_api, name="api_delete"),
    path("api/track/<int:track_id>/comentarios/", comments_api, name="api_comments"),
    path("api/carrito/", cart_list_api, name="api_cart"),
    path("api/carrito/agregar/<int:track_id>/", cart_add_api, name="api_cart_add"),
    path("api/carrito/<int:venta_id>/", cart_remove_api, name="api_cart_remove"),
    path("api/pago/", pago_init_api, name="api_pago"),
    path("api/pago/cancelar/<int:transaction_id>/", pago_cancel_api, name="api_pago_cancel"),
    path("api/upload/", upload_api, name="api_upload"),
    path("api/mis-ventas/", mis_ventas_api, name="api_sales"),
    path("api/mis-compras/", mis_compras_api, name="api_purchases"),
    path("api/like/<int:track_id>/", like_toggle_api, name="api_like"),
    path("api/perfil/<str:username>/", perfil_publico_api, name="api_profile"),
    path("api/suscripciones/", suscripciones_api, name="api_suscripciones"),
]


# --------------------------------------------------------------------------
# CORS mínimo sin dependencias nuevas (solo para desarrollo local del SPA).
# Uso opcional en beatcloud/urls.py:
#     from app.api_shim import wrap_with_api
#     urlpatterns = wrap_with_api(urlpatterns)
# --------------------------------------------------------------------------
ALLOWED_ORIGIN = "http://localhost:3000"


def _corsify(response):
    origin = ALLOWED_ORIGIN
    response["Access-Control-Allow-Origin"] = origin
    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Methods"] = "GET, POST, PATCH, PUT, DELETE, OPTIONS"
    response["Access-Control-Allow-Headers"] = "X-CSRFToken, Content-Type, Accept"
    response["Vary"] = "Origin"
    return response


def wrap_with_api(base_patterns):
    def middleware(get_response):
        def handler(request):
            if request.path.startswith("/api/"):
                from django.urls import get_resolver

                resolver = get_resolver(list(urlpatterns))
                match = resolver.resolve(request.path_info)
                view = match.func
                request.resolver_match = match
                if request.method == "OPTIONS":
                    resp = JsonResponse({}, status=200)
                else:
                    resp = view(request, *match.args, **match.kwargs)
                return _corsify(resp)
            return get_response(request)

        return handler

    # Devuelve (patterns_nuevos, factory_de_middleware) — el README explica cómo montarlo
    return list(base_patterns) + list(urlpatterns), middleware
