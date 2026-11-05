# BeatsCloud

BeatsCloud es una aplicación web desarrollada con Django para artistas, productores y usuarios de contenido musical. El proyecto permite publicar tracks, descubrir productores y artistas, comprar contenido mediante Webpay, adquirir suscripciones y gestionar perfiles musicales.

> Estado de esta documentación: 31-08-2026.  
> La integración de Transbank descrita aquí está configurada para ambiente **TEST** durante el desarrollo.

---

## Funcionalidades implementadas

### Cuentas y autenticación

- Registro e inicio de sesión.
- Validación para evitar correos duplicados.
- Las cuentas nuevas se crean inactivas hasta confirmar el correo.
- Confirmación de cuenta mediante enlace seguro de Django (`uidb64` + token).
- Recuperación segura de contraseña mediante el flujo oficial de Django.
- Correos HTML personalizados para confirmación de cuenta y recuperación de contraseña.
- Mensajes globales mediante Bootstrap.
- Vistas privadas protegidas con autenticación.

### Perfiles y comunidad

- Perfil público y privado de artista.
- Perfil público y privado de productor.
- Edición de perfiles.
- Enlaces a YouTube, Spotify e Instagram.
- Los enlaces sociales sin URL configurada no generan rutas terminadas en `/None`.
- Catálogo de usuarios con búsqueda y filtros por tipo de usuario.
- Sistema de Me gusta para tracks.
- Comentarios con creación y eliminación segura.

### Tracks

- Subida de tracks restringida a productores.
- Validación de extensiones de audio.
- Verificación real del archivo de audio mediante `mutagen`.
- Validación de imágenes.
- Edición de metadata de tracks.
- Eliminación de tracks con validación de propietario.
- Reemplazo del archivo de audio restringido cuando el track ya posee compras.
- Reproducción mediante una vista controlada de Django.
- Descarga mediante `FileResponse` solo para compradores.
- Prevención de compras duplicadas.

> La reproducción mediante una ruta Django evita exponer directamente la ruta física del archivo, pero **no constituye un sistema DRM**.

### Catálogo y carrito

- Catálogo moderno de tracks.
- Búsqueda por track, productor y género.
- Filtros por género y rango de precio.
- Ordenamiento y paginación.
- Indicador de track ya comprado.
- Carrito con productos pendientes.
- Prevención de agregar el mismo track más de una vez.
- Eliminación segura mediante `POST` + CSRF.
- El carrito solo procesa ventas pendientes.

### Pagos Webpay / Transbank

El proyecto integra Webpay Plus mediante `transbank-sdk` y actualmente está probado en ambiente `TEST`.

El flujo implementado incluye:

- Pago de tracks desde el carrito.
- Pago de suscripciones.
- Creación local de `WebpayTransaction`.
- Estados `PENDING`, `AUTHORIZED` y `CANCELLED`.
- Validación del retorno de Transbank.
- Verificación de autorización, orden de compra, sesión, monto, usuario y tipo de operación.
- Registro de compras solo después de una respuesta autorizada.
- Las transacciones exitosas del carrito quedan en `AUTHORIZED`.
- Las suscripciones exitosas quedan en `AUTHORIZED`.
- Cancelación antes de entrar a Webpay: `PENDING -> CANCELLED`.
- Cancelación dentro de Webpay: si Transbank retorna datos de cancelación sin `token_ws`, la transacción pendiente correspondiente pasa a `CANCELLED`.
- Diferenciación entre cancelación de carrito y cancelación de suscripción.

Las credenciales de Transbank **no deben estar escritas en `views.py`**. La configuración se carga desde `.env`.

---

# 1. Requisitos

Instala antes de comenzar:

- Git
- Python 3.12 o superior
- PostgreSQL
- Visual Studio Code (recomendado)

Si el equipo ya tiene una versión concreta de Python funcionando correctamente con `requirements.txt`, es preferible mantener esa misma versión entre integrantes.

---

# 2. Clonar el repositorio

```powershell
git clone https://github.com/felipe-urtubia/BeatsCloud.git BeatCloud
cd BeatCloud
```

---

# 3. Crear el entorno virtual

```powershell
python -m venv .venv
```

Activar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

# 4. Instalar dependencias

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

Resultado esperado de `pip check`:

```text
No broken requirements found.
```

> Se recomienda usar `python -m pip` en vez de invocar directamente `pip.exe`, especialmente si el entorno virtual fue movido de carpeta.

---

# 5. Crear `.env`

El archivo `.env` contiene configuración privada y **no se sube a GitHub**.

```powershell
Copy-Item .env.example .env
```

Después completa el `.env` de tu propio equipo.

Ejemplo de estructura:

```env
# Django
DJANGO_SECRET_KEY=TU_CLAVE_SECRETA
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Stripe (opcional mientras no se use)
STRIPE_PUBLIC_KEY=
STRIPE_SECRET_KEY=

# Transbank / Webpay
TRANSBANK_COMMERCE_CODE=TU_COMMERCE_CODE_DE_PRUEBA
TRANSBANK_API_KEY=TU_API_KEY_DE_PRUEBA
TRANSBANK_INTEGRATION_TYPE=TEST

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=beatsbd
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD_POSTGRES
DB_HOST=localhost
DB_PORT=5432

# Gmail / correo
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=TU_CORREO@gmail.com
EMAIL_HOST_PASSWORD=TU_CONTRASENA_DE_APLICACION
DEFAULT_FROM_EMAIL=BeatsCloud <TU_CORREO@gmail.com>
EMAIL_TIMEOUT=15
```

Nunca subas valores reales a `.env.example`.

## Generar `DJANGO_SECRET_KEY`

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia el resultado únicamente a tu `.env`.

---

# 6. Variables Django para desarrollo

Para trabajar solo en localhost:

```env
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

`settings.py` construye `DEBUG`, `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` desde variables de entorno.

Durante desarrollo `SESSION_COOKIE_SECURE` queda en `False` porque depende de `DEBUG`.

No actives redirección HTTPS forzada mientras necesites trabajar también mediante `http://127.0.0.1:8000`.

---

# 7. Configurar Gmail

BeatsCloud utiliza SMTP para confirmar cuentas y recuperar contraseñas.

Con Gmail:

1. Activa la verificación en dos pasos.
2. Crea una **Contraseña de aplicación**.
3. Coloca el correo en `EMAIL_HOST_USER`.
4. Coloca la contraseña de aplicación en `EMAIL_HOST_PASSWORD`.

No uses tu contraseña normal de Gmail.

Comprobación segura:

```powershell
python manage.py shell -c "from django.conf import settings; print({'HOST': settings.EMAIL_HOST, 'USUARIO_CONFIGURADO': bool(settings.EMAIL_HOST_USER), 'PASSWORD_CONFIGURADA': bool(settings.EMAIL_HOST_PASSWORD)})"
```

Nunca imprimas ni compartas `EMAIL_HOST_PASSWORD`.

---

# 8. PostgreSQL

Cada integrante puede tener su propia base local.

```sql
CREATE DATABASE beatsbd;
```

Configuración típica:

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=beatsbd
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD
DB_HOST=localhost
DB_PORT=5432
```

Comprobar conexión:

```powershell
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Conexion PostgreSQL OK')"
```

---

# 9. Migraciones

```powershell
python manage.py migrate
```

Si se modificaron modelos:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Las migraciones sincronizan la estructura de la base, pero **no copian automáticamente los datos** de la base local de otro integrante.

---

# 10. Crear administrador

Opcional:

```powershell
python manage.py createsuperuser
```

Panel:

```text
http://127.0.0.1:8000/admin/
```

---

# 11. Verificar y ejecutar BeatsCloud

```powershell
python manage.py check
```

Resultado esperado:

```text
System check identified no issues (0 silenced).
```

Ejecutar localmente:

```powershell
python manage.py runserver
```

Abrir:

```text
http://127.0.0.1:8000/
```

Para permitir además reenvío de puerto de VS Code:

```powershell
python manage.py runserver 0.0.0.0:8000
```

---

# 12. Compartir temporalmente mediante VS Code Dev Tunnels

En la pestaña **Ports**:

1. Agrega el puerto `8000`.
2. Configura `Visibility` como `Public` si necesitas compartirlo.
3. Mantén el protocolo interno como **HTTP** porque Django `runserver` sirve HTTP.
4. VS Code entregará una dirección pública similar a `https://xxxxx-8000.brs.devtunnels.ms/`.

La URL externa puede ser HTTPS aunque el protocolo interno hacia Django sea HTTP.

Cada integrante recibe su propio dominio. Debe agregarlo **solo en su `.env` personal**:

```env
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,SU-DOMINIO-8000.brs.devtunnels.ms
DJANGO_CSRF_TRUSTED_ORIGINS=https://SU-DOMINIO-8000.brs.devtunnels.ms
```

No coloques el dominio personal de un compañero en `.env.example`.

Si el túnel muestra `404` pero localhost funciona:

- confirma que `python manage.py runserver 0.0.0.0:8000` siga ejecutándose;
- elimina el puerto de la pestaña **Ports**;
- vuelve a agregar `8000`;
- usa la nueva dirección reenviada;
- mantén el protocolo interno en HTTP.

---

# 13. Comprobar configuración sin revelar secretos

Django:

```powershell
python manage.py shell -c "from django.conf import settings; print({'DEBUG': settings.DEBUG, 'ALLOWED_HOSTS': settings.ALLOWED_HOSTS, 'CSRF_TRUSTED_ORIGINS': settings.CSRF_TRUSTED_ORIGINS, 'SESSION_COOKIE_SECURE': settings.SESSION_COOKIE_SECURE})"
```

Transbank:

```powershell
python manage.py shell -c "from django.conf import settings; print({'COMMERCE_CODE': bool(settings.TRANSBANK_COMMERCE_CODE), 'API_KEY': bool(settings.TRANSBANK_API_KEY), 'TYPE': settings.TRANSBANK_INTEGRATION_TYPE})"
```

Ejemplo esperado en desarrollo:

```text
{'COMMERCE_CODE': True, 'API_KEY': True, 'TYPE': 'TEST'}
```

No imprimas los valores reales.

---

# 14. Webpay / Transbank

Variables necesarias:

```env
TRANSBANK_COMMERCE_CODE=
TRANSBANK_API_KEY=
TRANSBANK_INTEGRATION_TYPE=TEST
```

Las vistas de pago usan:

```python
settings.TRANSBANK_COMMERCE_CODE
settings.TRANSBANK_API_KEY
settings.TRANSBANK_INTEGRATION_TYPE
```

No deben existir commerce codes o API keys escritos directamente en `app/views.py`.

## Flujo del carrito

1. El usuario agrega un track.
2. BeatsCloud crea una `WebpayTransaction` en `PENDING`.
3. Se crea la transacción en Webpay.
4. Webpay retorna a `exito_carrito`.
5. BeatsCloud valida la respuesta.
6. Si es correcta, la transacción pasa a `AUTHORIZED`, se registra el historial y se eliminan las ventas pendientes correspondientes.

## Flujo de suscripción

1. El usuario elige una suscripción.
2. Se crea una `WebpayTransaction` asociada a la suscripción.
3. Webpay procesa el pago.
4. BeatsCloud valida autorización, monto, orden, sesión y usuario.
5. La transacción queda en `AUTHORIZED`.

## Cancelaciones

Antes de Webpay:

```text
PENDING -> CANCELLED
```

Si el usuario cancela dentro de Webpay, Transbank puede retornar parámetros `TBK_*` sin `token_ws`; BeatsCloud localiza la transacción pendiente correspondiente y la marca `CANCELLED`.

Nunca utilices tarjetas reales mientras estés en ambiente TEST.

---

# 15. Estado de Stripe

El proyecto conserva:

```env
STRIPE_PUBLIC_KEY=
STRIPE_SECRET_KEY=
```

Si el flujo Stripe no se está utilizando en la versión actual, pueden permanecer vacías. No es necesario configurar Stripe para probar Webpay.

---

# 16. Seguridad aplicada

- `.env` ignorado por Git.
- Secrets fuera de `views.py`.
- Configuración sensible leída desde variables de entorno.
- Historial de Git reescrito para retirar credenciales de Transbank que habían aparecido en commits antiguos.
- Acciones sensibles mediante `POST`.
- Protección CSRF.
- Comprobación de usuario/propietario al editar o eliminar recursos.
- Confirmación segura de Webpay antes de registrar compras.
- Prevención de recompras.
- Descarga solo para compradores.
- Recuperación de contraseña con tokens oficiales de Django.
- Activación de cuentas por correo.
- `ALLOWED_HOSTS` configurable desde `.env`.
- `CSRF_TRUSTED_ORIGINS` configurable desde `.env`.

Si una credencial real de producción llega a publicarse, eliminarla del historial **no sustituye la rotación de la credencial**.

---

# 17. Historial de Git y limpieza de credenciales

Durante la revisión de seguridad se detectaron credenciales de Transbank escritas en commits antiguos. La rama `main` fue reescrita con `git-filter-repo` y actualizada en GitHub mediante un force push controlado.

Un compañero que tenga un clon realizado **antes de esa reescritura** debería evitar mezclar el historial antiguo con el nuevo. La opción más segura es:

1. Guardar aparte cualquier cambio local importante.
2. Eliminar o renombrar el clon antiguo.
3. Clonar de nuevo:

```powershell
git clone https://github.com/felipe-urtubia/BeatsCloud.git BeatCloud
```

4. Crear nuevamente `.venv`.
5. Crear su `.env` personal desde `.env.example`.
6. Instalar `requirements.txt`.
7. Ejecutar migraciones.

Esto evita reintroducir commits del historial antiguo.

---

# 18. Archivos que no deben subirse

`.gitignore` debe excluir como mínimo:

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

Nunca subir:

- `.env`;
- passwords de Gmail;
- `DJANGO_SECRET_KEY` real;
- password de PostgreSQL;
- claves privadas de Stripe;
- credenciales reales de Transbank;
- respaldos que contengan un historial antiguo con secretos.

Sí se pueden versionar `.env.example`, `requirements.txt`, `README.md` y `REGISTRO_CAMBIOS_BEATSCLOUD.md` siempre que no contengan secretos reales.

---

# 19. Trabajo en equipo

Antes de comenzar:

```powershell
git pull
```

Revisar estado:

```powershell
git status --short
```

Agregar archivos concretos:

```powershell
git add archivo1 archivo2
```

Crear commit:

```powershell
git commit -m "Descripcion breve del cambio"
```

Subir:

```powershell
git push origin main
```

Para cambios grandes:

```powershell
git switch -c nombre-de-la-rama
```

Si cambió `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
python -m pip check
```

Si hay nuevas migraciones:

```powershell
python manage.py migrate
```

Antes de subir cambios:

```powershell
python manage.py check
git status --short
```

---

# 20. Actualizar dependencias

```powershell
python -m pip check
python manage.py check
python -m pip freeze > requirements.txt
```

Revisa `requirements.txt` antes de hacer commit y no subas `.venv`.

---

# 21. Problemas frecuentes

## `ModuleNotFoundError`

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Error de launcher de `pip`

```powershell
python -m pip --version
python -m pip install -r requirements.txt
```

## Error de PostgreSQL

Comprueba servicio, base `beatsbd`, usuario, password, `DB_HOST`, puerto `5432` y dependencias.

```powershell
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Conexion PostgreSQL OK')"
```

## El correo intenta conectar a localhost

```powershell
python manage.py shell -c "from django.conf import settings; print(settings.EMAIL_HOST)"
```

Debe devolver `smtp.gmail.com`.

## Gmail no envía

```powershell
python manage.py shell -c "from django.conf import settings; print(bool(settings.EMAIL_HOST_USER), bool(settings.EMAIL_HOST_PASSWORD))"
```

## `DisallowedHost`

Agrega el hostname usado a `DJANGO_ALLOWED_HOSTS`.

## `403 CSRF verification failed` desde un túnel HTTPS

Agrega el origen completo:

```env
DJANGO_CSRF_TRUSTED_ORIGINS=https://SU-DOMINIO-8000.brs.devtunnels.ms
```

Reinicia `runserver` después de modificar `.env`.

## Dev Tunnel muestra 404

Si localhost funciona:

1. Mantén Django en `0.0.0.0:8000`.
2. Elimina el puerto reenviado.
3. Vuelve a agregar `8000`.
4. Protocolo interno: HTTP.
5. Visibilidad: Public cuando necesites compartir.
6. Abre la nueva URL HTTPS entregada por VS Code.

## Webpay falla después de mover credenciales a `.env`

```powershell
python manage.py shell -c "from django.conf import settings; print({'COMMERCE_CODE': bool(settings.TRANSBANK_COMMERCE_CODE), 'API_KEY': bool(settings.TRANSBANK_API_KEY), 'TYPE': settings.TRANSBANK_INTEGRATION_TYPE})"
```

No muestres las credenciales.

---

# 22. Estructura principal

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
├── REGISTRO_CAMBIOS_BEATSCLOUD.md
└── README.md
```

---

# 23. Resumen para un compañero nuevo

```powershell
git clone https://github.com/felipe-urtubia/BeatsCloud.git BeatCloud
cd BeatCloud

python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Copy-Item .env.example .env
```

Después:

1. Completar `.env`.
2. Crear la base PostgreSQL `beatsbd`.
3. Ejecutar:

```powershell
python manage.py migrate
python manage.py check
python manage.py runserver
```

4. Abrir `http://127.0.0.1:8000/`.

---

# Importante para el equipo

Todos pueden trabajar con el mismo código, pero cada integrante mantiene:

- su propio `.env`;
- su propia `.venv`;
- su propia configuración PostgreSQL;
- su propio dominio Dev Tunnel, si lo utiliza;
- sus propias credenciales locales autorizadas.

Los datos de las bases locales no se sincronizan mediante Git.

**Nunca copies el `.env` de otra persona a GitHub ni envíes secretos en commits, capturas o mensajes.**

---

# 24. Frontend React

El frontend está ubicado en `frontend/client/` y se comunica con Django
mediante la API JSON implementada en `app/api_shim.py`.

Esta sección permite preparar una instalación local desde cero. La aplicación
Django original sigue disponible en `http://127.0.0.1:8000/`; React se sirve
por separado en `http://localhost:3000/`.

## Requisitos

- Git.
- Python 3.12 o superior, PostgreSQL y Node.js con npm.
- Un archivo `.env` de Django configurado desde `.env.example`.
- En Windows, ejecuta los comandos Python en PowerShell; en Linux/macOS, usa
  los comandos indicados para esos sistemas.

## Configuración local desde cero

Clona la rama de integración:

```bash
git clone --branch integration/react-frontend https://github.com/felipe-urtubia/BeatsCloud.git
cd BeatsCloud
```

Crea y activa un entorno virtual, e instala las dependencias del backend:

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copia `.env.example` a `.env` en la raíz. En Linux/macOS usa `cp .env.example .env`;
en Windows PowerShell usa `Copy-Item .env.example .env`. Genera tu propia clave
Django y rellena la configuración local de PostgreSQL; no copies secretos de
otra persona:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Pon el resultado en `DJANGO_SECRET_KEY` de `.env`. La configuración de base
de datos usada por el proyecto es PostgreSQL; los nombres por defecto del
ejemplo son `DB_NAME=beatsbd`, `DB_USER=postgres`, `DB_HOST=localhost` y
`DB_PORT=5432`. Asigna `DB_PASSWORD` según tu PostgreSQL local. Crea la base
si aún no existe (por ejemplo, desde `psql` como usuario con permisos):

```sql
CREATE DATABASE beatsbd;
```

En `.env`, asegúrate de que existan estas variables para React y el correo
local:

```env
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

El backend de consola imprime en la terminal de Django los correos de registro
y sus enlaces de activación. Para usar SMTP en lugar de la consola, las
variables `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`,
`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` y
`EMAIL_TIMEOUT` están documentadas en `.env.example`. Gmail requiere una
contraseña de aplicación. No se necesitan credenciales de SMTP para la
demostración con backend de consola.

Para probar Webpay además se requieren credenciales de integración TEST de
Transbank en las variables `TRANSBANK_*` del `.env`; sin ellas se puede recorrer
el carrito, pero no completar el inicio de pago.

Aplica las migraciones y, si necesitas entrar al administrador Django, crea
un superusuario:

```bash
python manage.py migrate
python manage.py createsuperuser
```

La base y los archivos `media/` de cada desarrollador son locales y no vienen
incluidos en Git. Por eso, una instalación limpia puede mostrar un catálogo
vacío hasta que se carguen datos por las herramientas existentes de Django.
No se crean tracks ficticios automáticamente.

## Configuración de Django para React

En el `.env` de la raíz, permite los dos orígenes locales que usa Vite para
las solicitudes protegidas por CSRF:

```env
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

El proyecto utiliza SMTP para los correos de registro y activación. Configura
en el `.env` de la raíz las variables `EMAIL_BACKEND`, `EMAIL_HOST`,
`EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`,
`DEFAULT_FROM_EMAIL` y `EMAIL_TIMEOUT`, cuyos nombres y valores de ejemplo
están en `.env.example`. Para Gmail se necesita una contraseña de aplicación;
no uses la contraseña normal de la cuenta.

Para pruebas locales sin SMTP, configura en el `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Con esta alternativa, Django muestra en su terminal los correos y enlaces de
activación. La activación de cuentas todavía usa la vista HTML existente de
Django; la interfaz de confirmación integrada en React queda pendiente.

## Configuración del frontend

Desde la raíz del proyecto, crea el archivo local del frontend e instala las
dependencias bloqueadas con `npm ci`:

Linux/macOS:

```bash
cd frontend/client
cp .env.example .env
npm ci
```

Windows PowerShell:

```powershell
cd frontend/client
Copy-Item .env.example .env
npm ci
```

El modo recomendado es:

```env
VITE_API_MODE=hybrid
VITE_DJANGO_URL=
```

No colocar claves de Django, PostgreSQL ni Transbank en variables
`VITE_*`, porque quedan expuestas en el código del navegador.

`VITE_DJANGO_URL` vacío usa el proxy de desarrollo de Vite. No es necesario
agregar credenciales privadas al `.env` del frontend.

## Inicio de los servicios

Primero, desde la raíz del proyecto, iniciar Django después de configurar
PostgreSQL, completar el archivo `.env` y ejecutar las migraciones:

```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

En una segunda terminal, desde la raíz:

```bash
cd frontend/client
npm run dev
```

Abre http://localhost:3000. Vite escucha en el puerto 3000 y reenvía las
solicitudes de `/api` y `/media` a Django en `127.0.0.1:8000`.
La aplicación Django original y el administrador siguen accesibles,
respectivamente, en http://127.0.0.1:8000/ y http://127.0.0.1:8000/admin/.

Para recorrer autenticación: registra una cuenta desde React, copia el enlace
que Django imprime en su terminal y ábrelo. La activación sigue usando la
vista HTML existente de Django; la pantalla de confirmación integrada en
React está pendiente.

## Modos de funcionamiento

- `hybrid`: utiliza la API de Django para sesión, catálogo y operaciones del usuario.
  Si el backend falla, informa el error y permite reintentar la sincronización.
- `mock`: utiliza datos locales de demostración y no valida la integración real.

Para la demostración integrada, conserva `VITE_API_MODE=hybrid`. Usa `mock`
solo para recorrer la interfaz sin conexión real con Django.

## Funcionalidades integradas y limitaciones conocidas

**Conectadas y verificadas manualmente:** inicio y cierre de sesión con Django,
persistencia de sesión al recargar React, registro (activación mediante enlace
de Django), consulta del catálogo, agregar productos al carrito y cargar o
eliminar productos del carrito. Estas comprobaciones manuales no son pruebas
automatizadas de navegador.

**Parcialmente integradas:** detalle de track, perfiles y paneles muestran
pantallas de React, pero algunos datos y acciones no están sincronizados con
Django. El reproductor puede usar el endpoint de medios cuando hay un archivo
disponible. El inicio del pago envía al usuario a Webpay; la validación y el
resultado final ocurren en la vista HTML de Django, no en React.

**Demostrativas o simuladas:** el modo `mock` usa datos locales. Algunas
acciones de panel, suscripción, certificados/licencias y descargas usan estado
local o contenido generado para la interfaz; no equivalen a operaciones
persistidas o validadas por el backend.

**Pendientes de integración o validación:** confirmación de activación dentro
de React, confirmación final de Webpay dentro de React, pagos probados de punta
a punta, y sincronización completa de subida/edición de tracks, perfiles,
comentarios, likes, suscripciones, compras, descargas y certificados. No se
deben interpretar sus pantallas como evidencia de que esas operaciones están
conectadas.

La aplicación Django original conserva sus vistas HTML y administración. En
una instalación limpia, el administrador y los flujos de React que requieren
contenido dependen de que cada integrante cree usuarios y cargue sus propios
tracks/medios; esos datos no se incluyen en el repositorio.

## Comprobaciones

Desde `frontend/client`:

```bash
npm run lint
npm run test
npm run build
npm audit
```

Desde la raíz del proyecto:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

El chequeo y las pruebas de Django requieren dependencias instaladas y
PostgreSQL configurado y disponible. `npm run test` ejecuta las pruebas
automatizadas del flujo de inicialización de Webpay; no simula una aprobación.

## Problemas habituales

- **No conecta a PostgreSQL:** revisa que el servicio esté activo, que la base
  `beatsbd` exista y que `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y
  `DB_PORT` en `.env` correspondan a tu instalación.
- **Error 403 CSRF al usar React:** confirma que el `.env` de la raíz contenga
  `DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` y
  reinicia Django.
- **El registro no envía correo:** con el backend de consola, revisa la
  terminal de Django y abre allí el enlace impreso. Para SMTP, configura las
  variables de correo descritas arriba; Gmail exige contraseña de aplicación.
- **El catálogo está vacío o faltan imágenes/audio:** la base y `media/` no
  están incluidos en el clon. Añade contenido local desde Django; no se
  descargan datos de prueba automáticamente.
- **El puerto ya está ocupado:** detén el proceso que usa `8000` o `3000` y
  vuelve a iniciar el servicio correspondiente.
