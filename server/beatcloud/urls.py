"""
URL configuration for beatcloud project.

The `urlpatterns` list routes URLs to views.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import Http404
from app.views import logout as app_logout


def bloquear_acceso_directo_canciones(request, path):
    """
    Impide abrir directamente archivos de audio mediante
    /media/canciones/<archivo>.

    Los audios de BeatCloud deben reproducirse mediante la vista
    reproducir_track() y descargarse mediante descargar_track().
    """
    raise Http404("Archivo de audio no disponible mediante acceso directo.")


urlpatterns = [
    # IMPORTANTE: esta ruta debe ir antes del static(MEDIA_URL, ...)
    # para que /media/canciones/ no quede expuesto directamente.
    path(
        'media/canciones/<path:path>',
        bloquear_acceso_directo_canciones,
        name='bloquear_acceso_directo_canciones'
    ),

    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    path('accounts/logout/', app_logout, name='accounts_logout'),
    path('accounts/', include('django.contrib.auth.urls')),
]


if settings.DEBUG:
    # Sigue sirviendo las demás imágenes/archivos de MEDIA durante desarrollo.
    # /media/canciones/... queda interceptado por la ruta anterior.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
