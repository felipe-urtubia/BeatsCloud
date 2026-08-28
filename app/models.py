from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_migrate
from django.utils import timezone
# Create your models here.

class Usuario(models.Model):
    ARTISTA = 1
    PRODUCTOR = 2
    TIPO_USUARIO_CHOICES = (
    (ARTISTA, 'Artista'),
    (PRODUCTOR, 'Productor'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    descripcion = models.TextField(max_length=500, null=True, blank=True)
    tipo_usu = models.IntegerField(choices=TIPO_USUARIO_CHOICES)
    foto_perfil = models.ImageField(upload_to="media/perfil",null=True, blank=True)
    foto_fondo = models.ImageField(upload_to="media/fondo",null=True,blank=True)
    spotify = models.URLField(null=True, blank=True) 
    youtube = models.URLField(null=True, blank=True) 
    instagram = models.URLField(null=True, blank=True) 
    tracks_gustados = models.ManyToManyField('Track', related_name='usuarios_que_dieron_like')
    carrito1 = models.ManyToManyField('Track', related_name='usuarios_en_carrito')
    sus = models.ManyToManyField('Suscripcion')

    def __str__(self):
        return self.user.username

class Suscripcion(models.Model):
    id_sus = models.AutoField(primary_key=True)
    detalle = models.CharField(max_length=200)
    precio = models.IntegerField()
    user = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    def __str__(self):
        return self.detalle
    



genero_musical = [0, "Pop"],[1, "Rock"],[2, "Hip-hop/rap"], [3,"Electrónica"], [4, "Reggaetón"],[5,"R&B/soul"],[6,"Jazz"],[7,"Metal"]
class Genero_Musical(models.Model):
    POP = 1
    ROCK = 2
    HIPHOP = 3 
    ELECTRONICA =4 
    REGGAETON = 5
    RnB = 6
    JAZZ = 7 
    METAL = 8
    SOUL = 9 
    GENERO_CHOICES = (
    (POP, 'Pop'),
    (ROCK, 'Rock'),
    (HIPHOP, 'Hip-Hop'),
    (ELECTRONICA, 'Electronica'),
    (REGGAETON, 'Reggaeton'),
    (RnB, 'R&B'),
    (JAZZ, 'Jazz'),
    (METAL, 'Metal'),
    (SOUL, 'Soul'),
    )
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(choices=GENERO_CHOICES, max_length=50)
    
    def __str__(self):
        return self.descripcion
    

class Track(models.Model):
    id_track = models.AutoField(primary_key=True)
    nombre_track = models.CharField(max_length=200)
    precio = models.IntegerField()
    track = models.FileField(upload_to="canciones")
    descripcion = models.TextField(max_length=500, null=True, blank=True)
    foto = models.ImageField(upload_to="tracks",null = True )
    genero = models.ForeignKey(Genero_Musical, on_delete=models.PROTECT)
    usuario= models.ForeignKey(Usuario, on_delete=models.CASCADE )

    def __str__(self):
        return self.nombre_track

class Interes(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    genero = models.ForeignKey(Genero_Musical, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.usuario.username} - {self.genero}"
    
class Comentario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='comentarios')
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class Venta(models.Model):
    id = models.AutoField(primary_key=True)
    detalle = models.CharField(max_length=200)
    fecha = models.DateField()
    precio = models.IntegerField()
    iva = models.IntegerField()
    precio_total = models.IntegerField()
    usuario_id = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    track = models.ForeignKey(Track, on_delete=models.PROTECT)
    
    completada = models.BooleanField(default=False)
    def __str__(self):
        return self.id
    
class Metodo_Pago(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=200)
    venta_id = models.ForeignKey(Venta, on_delete=models.CASCADE)

    def __str__(self):
        return self.id
    
class HistorialCompra(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    fecha_compra = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.usuario.username} - {self.track.nombre}'

    class Meta:
        verbose_name_plural = 'Historial de compras'

class Carrito(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    detalle = models.CharField(max_length=200)
    fecha = models.DateField()  # Utiliza el valor actual por defecto
    precio = models.IntegerField()
    iva = models.IntegerField()
    precio_total = models.IntegerField()

    def __str__(self):
        return f'{self.usuario.user.username} - {self.track.nombre_track}'


class Compra(models.Model):
    id = models.AutoField(primary_key=True)
    fecha = models.DateField()
    precio = models.IntegerField()
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    track = models.ForeignKey(Track, on_delete=models.PROTECT)
    def __str__(self):
        return str(self.id)

class WebpayTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    buy_order = models.CharField(max_length=50)
    session_id = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    # Otros campos que desees almacenar, como el estado de la transacción, por ejemplo

    def __str__(self):
        return f"{self.buy_order} - {self.amount}"
    
class HistorialVenta(models.Model):
    comprador = models.ForeignKey(User, on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    fecha_venta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Venta de '{self.track.nombre_track}' a {self.comprador.username}"