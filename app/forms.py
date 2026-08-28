from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Usuario, Genero_Musical, Track

class RegistroUsuarioForm(UserCreationForm):
    TIPO_USUARIO_CHOICES = (
        (Usuario.ARTISTA, 'Artista'),
        (Usuario.PRODUCTOR, 'Productor'),
    )
    tipo_usu = forms.ChoiceField(choices=TIPO_USUARIO_CHOICES)
    foto_perfil = forms.ImageField(required=False)
    foto_fondo = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'tipo_usu','foto_perfil', 'foto_fondo']

    def validate_password_for_user(self, user, **kwargs):
        return

class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['descripcion', 'foto_perfil', 'foto_fondo', 'spotify', 'youtube', 'instagram']


class UsuarioEditForm(forms.ModelForm):
       class Meta:
        model = Usuario
        fields = ['descripcion', 'foto_perfil', 'foto_fondo', 'spotify', 'youtube', 'instagram']



class TrackForm(forms.ModelForm):
    class Meta:
        model = Track
        fields = ['nombre_track', 'precio', 'track', 'foto', 'genero', 'descripcion']
    genero = forms.ModelChoiceField(queryset=Genero_Musical.objects.all().order_by('descripcion'), widget=forms.Select)