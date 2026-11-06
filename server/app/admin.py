from django.contrib import admin
from .models import Usuario, Suscripcion, Venta, Genero_Musical, Track, Metodo_Pago
# Register your models here.

admin.site.register(Usuario)
admin.site.register(Suscripcion)
admin.site.register(Venta)
admin.site.register(Genero_Musical)
admin.site.register(Track)
admin.site.register(Metodo_Pago)