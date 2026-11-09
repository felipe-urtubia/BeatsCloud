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
    first_name = forms.CharField(max_length=150, required=True)
    nombre_artistico = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    foto_perfil = forms.ImageField(required=False)
    foto_fondo = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password1',
            'password2',
            'first_name',
            'last_name',
            'nombre_artistico',
            'tipo_usu',
            'foto_perfil',
            'foto_fondo',
        ]

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta registrada con este correo electrónico.')
        return email

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



from .metadata_validation import validate_d9_field


class TrackForm(forms.ModelForm):
    class Meta:
        model = Track
        fields = [
            'nombre_track', 'precio', 'track', 'foto', 'genero', 'descripcion',
            'subgenre', 'resource_type', 'bpm', 'scale_key', 'mood', 'has_stems', 'has_wav',
            'has_midi', 'allow_free_download', 'has_watermark', 'duration',
        ]
    genero = forms.ModelChoiceField(queryset=Genero_Musical.objects.all().order_by('descripcion'), widget=forms.Select)
    def clean_bpm(self):
        return validate_d9_field('bpm', self.cleaned_data['bpm'])

    def clean_mood(self):
        return validate_d9_field('mood', self.cleaned_data['mood'])

    def clean_resource_type(self):
        return validate_d9_field('resource_type', self.cleaned_data['resource_type'])

    def clean_has_stems(self):
        # El widget CheckboxInput trata textos arbitrarios como True.
        # Validar el dato ORIGINAL antes de convertirlo.
        return validate_d9_field('has_stems', self.data.get('has_stems', None))
