# BeatCloud

BeatCloud es una aplicación web desarrollada con Django orientada a artistas, productores y usuarios de contenido musical.

Entre sus funciones actuales se encuentran:

- Registro e inicio de sesión.
- Confirmación de cuenta por correo electrónico.
- Recuperación segura de contraseña por correo.
- Perfiles de artistas y productores.
- Enlaces a YouTube, Spotify e Instagram.
- Publicación y reproducción de proyectos musicales.
- Catálogo y carrito de compras.
- Pagos de prueba mediante Webpay Plus / Transbank.
- Suscripciones.
- Historial de compras y ventas.
- Integración preparada con Stripe.
- Base de datos PostgreSQL.

---

## 1. Requisitos

Antes de comenzar instala:

- Git
- Python 3.12 o superior
- PostgreSQL
- Visual Studio Code (recomendado)

> El SDK actual de Transbank requiere Python moderno. Si el proyecto ya funciona en tu equipo con otra versión específica de Python, usa preferentemente esa misma versión.

---

## 2. Clonar el proyecto

Abre PowerShell o la terminal de VS Code:

```powershell
git clone https://github.com/felipe-urtubia/BeatsCloud.git BeatCloud
cd BeatCloud
```

El último argumento (`BeatCloud`) hace que la carpeta local conserve el mismo nombre usado en el resto de esta guía.

---

## 3. Crear el entorno virtual

En Windows:

```powershell
python -m venv .venv
```

Actívalo:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecución del script, habilítalo solo para la sesión actual y vuelve a activarlo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Si quedó activado verás algo parecido a:

```text
(.venv) PS C:\...\BeatCloud>
```

---

## 4. Instalar las dependencias

Con el entorno virtual activado:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` es la fuente de verdad para las versiones del proyecto. No es necesario subir la carpeta `.venv` a GitHub: cada integrante la recrea localmente con los comandos anteriores.

Comprueba que no haya dependencias rotas:

```powershell
python -m pip check
```

El resultado esperado es:

```text
No broken requirements found.
```

---

## 5. Crear el archivo `.env`

El archivo `.env` **no está en GitHub** porque contiene claves privadas.

Cada integrante debe crear su propio archivo:

```text
BeatCloud
├── .env
├── .env.example
├── manage.py
├── app
└── beatcloud
```

Puedes copiar `.env.example`:

```powershell
Copy-Item .env.example .env
```

Luego abre `.env` y completa tus propios datos.

Ejemplo:

```env
# Django
DJANGO_SECRET_KEY=TU_CLAVE_SECRETA_DJANGO

# Gmail / correo
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=TU_CORREO@gmail.com
EMAIL_HOST_PASSWORD=TU_CONTRASENA_DE_APLICACION_GOOGLE
DEFAULT_FROM_EMAIL=BeatCloud <TU_CORREO@gmail.com>
EMAIL_TIMEOUT=15

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=beatsbd
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD_POSTGRES
DB_HOST=localhost
DB_PORT=5432

# Stripe
STRIPE_PUBLIC_KEY=
STRIPE_SECRET_KEY=
```

Para Transbank, usa únicamente la configuración de integración que esté definida en la versión actual del proyecto. Antes de pasar a producción, las credenciales reales deben quedar centralizadas en variables de entorno o en un gestor de secretos y nunca en GitHub.

### Generar la clave secreta de Django

Ejecuta:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia el resultado en:

```env
DJANGO_SECRET_KEY=...
```

No publiques esta clave.

---

## 6. Configurar Gmail

BeatCloud usa correo SMTP para:

- confirmar nuevas cuentas;
- recuperar contraseñas.

Para usar Gmail:

1. Activa la verificación en dos pasos de tu cuenta Google.
2. Crea una **Contraseña de aplicación**.
3. Coloca tu correo en `EMAIL_HOST_USER`.
4. Coloca la contraseña de aplicación en `EMAIL_HOST_PASSWORD`.

No uses la contraseña normal de Gmail.

El archivo `.env` nunca debe subirse a GitHub.

---

## 7. Crear la base de datos PostgreSQL

Cada integrante tendrá su propia base de datos local.

En PostgreSQL crea:

```sql
CREATE DATABASE beatsbd;
```

También puedes crearla desde pgAdmin.

Luego revisa que `.env` tenga:

```env
DB_NAME=beatsbd
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD_POSTGRES
DB_HOST=localhost
DB_PORT=5432
```

---

## 8. Aplicar las migraciones

Con PostgreSQL funcionando:

```powershell
python manage.py migrate
```

Esto crea las tablas necesarias del proyecto.

> Las migraciones crean la estructura de la base de datos, pero no copian automáticamente los usuarios, canciones, compras u otros datos existentes en la base de datos de otro compañero.

---

## 9. Crear un administrador (opcional)

```powershell
python manage.py createsuperuser
```

Después puedes entrar a:

```text
http://127.0.0.1:8000/admin/
```

---

## 10. Ejecutar BeatCloud

Antes de iniciar el servidor, verifica la configuración de Django:

```powershell
python manage.py check
```

El resultado esperado es similar a:

```text
System check identified no issues (0 silenced).
```

Después inicia BeatCloud:

```powershell
python manage.py runserver
```

Luego abre:

```text
http://127.0.0.1:8000/
```

Para detener el servidor:

```text
Ctrl + C
```

---

## 11. Comprobar el correo

Si quieres verificar que Django está leyendo la configuración:

```powershell
python manage.py shell
```

Dentro del shell:

```python
from django.conf import settings

print(settings.EMAIL_HOST)
print(settings.EMAIL_HOST_USER)
print(bool(settings.EMAIL_HOST_PASSWORD))
```

Debería mostrar:

```text
smtp.gmail.com
tu_correo@gmail.com
True
```

Nunca imprimas ni compartas el contenido real de `EMAIL_HOST_PASSWORD`.

Sal con:

```python
exit()
```

---

## 12. Webpay / Transbank

El proyecto tiene integración de Webpay Plus en ambiente de prueba mediante `transbank-sdk` (`from transbank import webpay`). No instales el paquete independiente llamado `webpay`, porque no corresponde a esta integración.

Durante desarrollo:

- No utilices tarjetas bancarias reales.
- Utiliza únicamente los datos de prueba oficiales de Transbank.
- Una compra del carrito se considera exitosa solamente después de que BeatCloud recibe el retorno de Webpay y confirma la transacción mediante `commit`.
- Las credenciales reales de producción nunca deben almacenarse directamente en GitHub.

Para producción deben configurarse las credenciales oficiales entregadas al comercio y revisar toda la configuración de seguridad antes de publicar.

---

## 13. Archivos que NO deben subirse a GitHub

Verifica que `.gitignore` incluya al menos:

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

Nunca subir:

- `.env`
- contraseñas de Gmail
- claves secretas de Django
- credenciales privadas de PostgreSQL
- claves privadas de Stripe
- credenciales privadas de producción de Transbank

Sí se puede subir:

```text
.env.example
requirements.txt
README.md
```

porque no contienen claves privadas reales.

---

## 14. Flujo recomendado para trabajar en equipo

Antes de comenzar a trabajar:

```powershell
git pull
```

Revisar cambios:

```powershell
git status
```

Agregar solo los archivos que deseas incluir en el commit:

```powershell
git add nombre-del-archivo
```

Si revisaste `git status` y realmente quieres incluir todos los cambios pendientes, puedes usar:

```powershell
git add .
```

Crear un commit:

```powershell
git commit -m "Descripcion breve del cambio"
```

Subir:

```powershell
git push
```

Es recomendable que cada integrante cree ramas para cambios grandes:

```powershell
git switch -c nombre-de-la-rama
```

### Cuando agregues o actualices una dependencia

Hazlo dentro de `.venv`, comprueba que el proyecto siga funcionando y luego actualiza el archivo de dependencias:

```powershell
python -m pip check
python manage.py check
python -m pip freeze > requirements.txt
```

Antes de subirlo, revisa `requirements.txt` para evitar paquetes instalados por error o dependencias que el proyecto ya no utiliza.

---

## 15. Cuando un compañero descargue cambios nuevos

Normalmente bastará con:

```powershell
git pull
```

Si cambió `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
python -m pip check
```

Si se agregaron migraciones:

```powershell
python manage.py migrate
```

Después:

```powershell
python manage.py runserver
```

---

## 16. Problemas frecuentes

### `ModuleNotFoundError`

Activa `.venv` e instala las dependencias:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### `pip` muestra un error de launcher o una ruta antigua

Usa `pip` a través del intérprete activo:

```powershell
python -m pip --version
python -m pip install -r requirements.txt
```

Esto evita depender directamente del ejecutable `pip.exe` cuando el entorno virtual fue movido de carpeta.

### Error al conectar PostgreSQL

Revisa:

- que PostgreSQL esté iniciado;
- que exista la base `beatsbd`;
- usuario y contraseña del `.env`;
- puerto `5432`;
- que instalaste las dependencias desde `requirements.txt`.

El proyecto usa el controlador PostgreSQL incluido en `requirements.txt` (actualmente la familia `psycopg` 3). No instales `psycopg2` manualmente salvo que el proyecto vuelva a requerirlo explícitamente.

Para comprobar una conexión real desde Django:

```powershell
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Conexion PostgreSQL OK')"
```

### El correo intenta conectar a localhost

Django no está leyendo correctamente el `.env`.

Comprueba:

```python
from django.conf import settings
print(settings.EMAIL_HOST)
```

Debe ser:

```text
smtp.gmail.com
```

### El registro no envía correos

Revisa:

```env
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

`EMAIL_HOST_PASSWORD` debe contener una contraseña de aplicación de Google.

### Cambios de base de datos

Si un compañero agregó o modificó modelos:

```powershell
python manage.py makemigrations
python manage.py migrate
```

---

---

## 17. Estructura principal

```text
BeatCloud/
├── app/
│   ├── migrations/
│   ├── static/
│   ├── templates/
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── beatcloud/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── media/
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

---

## Importante para el equipo

Cada integrante puede usar el mismo código de GitHub, pero:

- cada uno mantiene su propio `.env`;
- cada uno crea su propia `.venv` local a partir de `requirements.txt`;
- cada uno puede tener su propia base PostgreSQL local;
- los datos locales no se sincronizan mediante Git;
- las claves privadas nunca se comparten mediante commits.

Si se necesita que todos trabajen con los mismos datos de prueba, se puede crear posteriormente un fixture de Django (`datos_iniciales.json`) o utilizar una base de datos compartida de desarrollo.
