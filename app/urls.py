from django import views
from django.contrib import admin

from django.contrib.auth import views as auth_views

from django.urls import path
from .views import inicio, logout, registro, perfil_artista, perfil_productor, perfil, editar_perfil, upload_file, \
editar_perfil_p, catalogo, perfil_artista1, perfil_productor1, detalle_track, agregar_comentario, perfil2,  \
carrito, agregar_al_carrito, eliminar_del_carrito, dar_like, recuperar_contrasena, recuperar_contrasena_success, \
exito, eliminar_del_carrito, pago, cancelado, catalogo_usuarios, ingresar_suscripcion_view, eliminar_track, \
realizar_pago, sobre_nosotros
    
urlpatterns = [
    path('', inicio, name = 'inicio'),
    path('logout/', logout, name='logout'),
    path('registro/', registro, name="registro"),
    path('perfil/', perfil, name="perfil"),
    path('perfil/artista/', perfil_artista, name='perfil_artista'),
    path('perfil/productor/', perfil_productor, name='perfil_productor'),
    path('perfil/artista/editar/', editar_perfil, name = 'editar'),
    path('perfil/productor/editar_p/', editar_perfil_p, name = 'editar_p'),
    path('perfil/productor/upload/', upload_file, name='upload_file'),
    path('catalogo/', catalogo, name = 'catalogo'),
    path('perfiles/<str:username>/', perfil2, name='perfil2'),
    path('perfil_artista/<str:username>/', perfil_artista1, name='perfil_artista1'),
    path('perfil_productor/<str:username>/', perfil_productor1, name='perfil_productor1'),
    path('detalle/<int:track_id>/', detalle_track, name = 'detalle'),
    path('agregar_comentario/<int:track_id>/', agregar_comentario, name='agregar_comentario'),
    path('carrito/', carrito, name='carrito'),
    path('carrito/agregar/<int:track_id>/', agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/eliminar/<int:venta_id>/', eliminar_del_carrito, name='eliminar_del_carrito'),
    path('dar_like/<int:track_id>/', dar_like, name='dar_like'),
    path('recuperar/', recuperar_contrasena, name='recuperar_contrasena'),
    path('recuperar/success/', recuperar_contrasena_success, name='recuperar_contrasena_success'),
    path('eliminar-del-carrito/<int:venta_id>/', eliminar_del_carrito, name='eliminar_del_carrito'),
    path('pago/', pago, name='pago'),
    path('pago/cancelado/', cancelado, name='cancelado'),
    path('pago/exito/', exito, name='exito'),
    path('usuarios/', catalogo_usuarios, name='catalogo_usuarios'),
    path('ingresar-suscripcion/', ingresar_suscripcion_view, name='ingresar_suscripcion'),
    path('eliminar_track/<int:track_id>/', eliminar_track, name='eliminar_track'),
    path('suscripcion/<int:suscripcion_id>/', realizar_pago, name = 'realizar_pago'),
    path('sobre_nosotros/', sobre_nosotros, name = 'sobre_nosotros'),


]
    

