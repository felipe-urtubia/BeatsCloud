"""Rutas Django con recuperacion de cuentas protegida."""

from django.contrib.auth import views as auth_views
from django.contrib.auth.urls import urlpatterns as django_auth_patterns
from django.urls import URLPattern

from .account_password_reset import (
    BeatsCloudPasswordResetForm,
    BeatsCloudPasswordResetConfirmView,
)


reemplazos = {
    "password_reset": auth_views.PasswordResetView.as_view(
        form_class=BeatsCloudPasswordResetForm,
        template_name="app/password_reset_form.html",
        email_template_name="registration/password_reset_email.txt",
        html_email_template_name="emails/restablecer_contrasena.html",
        subject_template_name="registration/password_reset_subject.txt",
    ),
    "password_reset_confirm": (
        BeatsCloudPasswordResetConfirmView.as_view(
            template_name="app/password_reset_confirm.html",
        )
    ),
}


# Conservar todos los patrones originales, sustituyendo
# exclusivamente las dos vistas de recuperacion.
urlpatterns = [
    URLPattern(
        patron.pattern,
        reemplazos[patron.name],
        default_args=patron.default_args,
        name=patron.name,
    )
    if patron.name in reemplazos
    else patron
    for patron in django_auth_patterns
]
