from django.contrib import admin
from .models import Usuario, Suscripcion, Venta, Genero_Musical, Track, Metodo_Pago
# Register your models here.

from django.contrib.auth.models import User

from .admin_identity import (
    BeatsCloudUserAdmin,
    BeatsCloudUsuarioAdmin,
)

admin.site.unregister(User)
admin.site.register(User, BeatsCloudUserAdmin)
admin.site.register(Usuario, BeatsCloudUsuarioAdmin)
from .admin_catalog import (
    BeatsCloudCatalogAdmin,
    BeatsCloudTrackAdmin,
    BeatsCloudSubscriptionAdmin,
    BeatsCloudCommercialReadOnlyAdmin,
)

admin.site.register(Suscripcion, BeatsCloudSubscriptionAdmin)
admin.site.register(Venta, BeatsCloudCommercialReadOnlyAdmin)
admin.site.register(Genero_Musical, BeatsCloudCatalogAdmin)
admin.site.register(Track, BeatsCloudTrackAdmin)
admin.site.register(Metodo_Pago, BeatsCloudCommercialReadOnlyAdmin)
