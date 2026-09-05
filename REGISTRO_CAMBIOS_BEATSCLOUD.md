# REGISTRO DE CAMBIOS — BEATSCLOUD

**Proyecto:** BeatsCloud
**Periodo cubierto:** 28-08-2026 al 04-09-2026
**Última actualización:** 04-09-2026

> Este documento consolida los cambios funcionales, visuales, de seguridad, configuración, documentación y pruebas realizados durante la etapa final de mejora del proyecto BeatsCloud.
> Se revisó el registro anterior y se incorporaron los cambios realizados hasta la última prueba manual del 04-09-2026.

---

# 28-08-2026

## Cuentas, correo y configuración

| Cambio | Descripción | Estado |
|---|---|---|
| Inicio de revisión general | Se revisó la estructura del proyecto Django, registro, perfiles, correo, pagos y configuración. | Completado |
| Confirmación de cuenta por correo | Los usuarios nuevos quedan inactivos hasta confirmar la cuenta mediante enlace seguro con `uidb64` y token de Django. | Implementado |
| Validación de correo duplicado | Se evita registrar dos cuentas con el mismo correo electrónico. | Implementado |
| Configuración mediante `.env` | Se implementó lectura de variables sensibles desde `.env`. | Implementado |
| Gmail SMTP | Se configuró y probó el envío de correo desde Django mediante Gmail SMTP. | Probado |
| Correos HTML | Se crearon plantillas para confirmación de cuenta y recuperación de contraseña. | Implementado |
| Recuperación de contraseña | Se implementó el flujo seguro oficial de Django para restablecer contraseña mediante correo. | Implementado |
| Redes sociales sin URL | Se evitó generar rutas terminadas en `/None` cuando Instagram, YouTube o Spotify no tienen enlace configurado. | Implementado |
| Perfiles públicos y privados | Se corrigió el comportamiento de enlaces sociales y visualización de perfiles. | Implementado |

---

# 29-08-2026

## Seguridad, carrito, compras y tracks

| Cambio | Descripción | Estado |
|---|---|---|
| Webpay Plus TEST | Se configuró el flujo de pago con Transbank Webpay en ambiente TEST. | Implementado |
| Validación del monto | El monto enviado a Webpay se normaliza correctamente para CLP. | Implementado |
| Validación del retorno Webpay | Se comprueba autorización, orden, sesión y monto antes de registrar una compra. | Implementado |
| Registro posterior al pago | El historial de compras y ventas se genera solo después de una respuesta válida y autorizada. | Implementado |
| Prevención de compras duplicadas | Se evita comprar nuevamente un track ya adquirido. | Implementado |
| Carrito sin duplicados | Un track pendiente no vuelve a agregarse como venta duplicada. | Implementado |
| Eliminación segura del carrito | Eliminación mediante `POST`, CSRF, validación de propietario y estado pendiente. | Implementado |
| Descarga protegida | Los compradores descargan tracks mediante `FileResponse`. | Implementado |
| Subida de tracks | Solo los productores pueden subir tracks. | Implementado |
| Validación real de audio | Se usa `mutagen` para validar que el archivo sea realmente de audio. | Implementado |
| Validación de extensiones | Se controlan formatos permitidos de audio e imagen. | Implementado |
| Edición de tracks | Se valida propiedad del track y se permite modificar metadata. | Implementado |
| Protección de audio vendido | No se permite reemplazar el archivo de audio si el track ya tiene compras. | Implementado |
| Eliminación de tracks | Eliminación segura mediante `POST`, CSRF y validación de propietario. | Implementado |
| Reproducción controlada | El audio público se entrega mediante una ruta Django controlada. | Implementado |

> La reproducción controlada evita exponer directamente la ruta física del archivo, pero no constituye DRM.

---

# 30-08-2026

## Interfaz y experiencia de usuario

Se modernizaron las principales páginas del sistema manteniendo la identidad visual de BeatsCloud.

### Páginas modernizadas

- Inicio.
- Catálogo de usuarios.
- Catálogo de tracks.
- Detalle de track.
- Perfil público de artista.
- Perfil público de productor.
- Perfil privado de artista.
- Perfil privado de productor.
- Edición de perfil.
- Subida de track.
- Edición de track.
- Carrito.
- Pago.
- Pago exitoso.
- Pago cancelado.
- Login.
- Registro.
- Activación de cuenta.
- Recuperación de contraseña.
- Creación de suscripción.
- Confirmación y pago de suscripciones.
- Página “Sobre nosotros”.

### Catálogo de tracks

Se agregaron:

- búsqueda;
- filtros;
- rango de precio;
- filtros por género;
- ordenamiento;
- paginación;
- indicador de track comprado.

### Interacción

- Sistema de Me gusta.
- Comentarios.
- Eliminación segura de comentarios.
- Mensajes globales mediante Bootstrap.

---

# 31-08-2026

## WebpayTransaction y estados de pago

Se amplió el modelo de transacciones para trabajar con tres estados:

```text
PENDING
AUTHORIZED
CANCELLED
```

Se creó y aplicó la migración correspondiente.

### Cancelación segura antes de Webpay

Se implementó una vista autenticada que:

- recibe la transacción por ID;
- valida que pertenezca al usuario;
- solo modifica transacciones `PENDING`;
- actualiza el estado a `CANCELLED`;
- diferencia entre carrito y suscripción;
- utiliza formulario `POST` con CSRF.

### Cancelación dentro de Webpay

También se corrigió el caso donde el usuario entra a Webpay y cancela allí.

Cuando Transbank retorna sin `token_ws`, BeatsCloud utiliza los datos `TBK_*` disponibles para localizar de forma segura la transacción correspondiente y marcarla:

```text
PENDING -> CANCELLED
```

Se probó correctamente tanto para:

- carrito;
- suscripciones.

### Pago autorizado del carrito

Se corrigió el flujo de éxito para que la transacción local quede explícitamente:

```text
AUTHORIZED
```

después de que Transbank confirma correctamente el pago.

Se comprobó que después del pago:

- `WebpayTransaction` queda `AUTHORIZED`;
- no quedan ventas pendientes correspondientes en el carrito;
- no se duplica el historial de compras.

---

# Seguridad de credenciales Transbank

## Credenciales fuera del código

Las credenciales de Transbank fueron retiradas de `app/views.py`.

Ahora se utilizan variables de entorno:

```env
TRANSBANK_COMMERCE_CODE=
TRANSBANK_API_KEY=
TRANSBANK_INTEGRATION_TYPE=TEST
```

Y las vistas acceden a:

```python
settings.TRANSBANK_COMMERCE_CODE
settings.TRANSBANK_API_KEY
settings.TRANSBANK_INTEGRATION_TYPE
```

Se comprobaron los cuatro puntos principales del flujo Webpay:

- creación de pago del carrito;
- confirmación de pago del carrito;
- creación de pago de suscripción;
- confirmación de pago de suscripción.

Todos continuaron funcionando después de mover la configuración a `.env`.

---

# Limpieza del historial de Git

Se detectó que credenciales de Transbank habían aparecido en commits históricos.

Se realizó una limpieza mediante:

```text
git-filter-repo
```

Antes de reescribir el historial:

- se creó un bundle local de respaldo;
- se verificó el bundle;
- se preparó un reemplazo temporal de secretos.

Después:

- se reescribió el historial;
- se verificó que los valores sensibles ya no aparecieran;
- se restauró el remoto;
- se realizó un `force-with-lease`;
- se eliminó el archivo temporal utilizado para el reemplazo.

### Importante

El bundle de respaldo del historial antiguo puede contener referencias a secretos anteriores y debe mantenerse privado o eliminarse cuando ya no sea necesario.

Si un compañero tiene un clon anterior a la reescritura del historial, se recomienda volver a clonar el repositorio para evitar reintroducir commits antiguos.

---

# Configuración segura de Django por entorno

Se reemplazó la configuración fija de:

```python
DEBUG = True
ALLOWED_HOSTS = []
```

por configuración basada en variables de entorno:

```env
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=
```

`settings.py` construye por entorno:

- `DEBUG`;
- `ALLOWED_HOSTS`;
- `CSRF_TRUSTED_ORIGINS`.

Se mantiene:

```python
SESSION_COOKIE_SECURE = not DEBUG
```

para permitir HTTP local durante desarrollo y usar cookies seguras cuando `DEBUG=False`.

### Verificación realizada

Se comprobó desde Django que:

- `DEBUG=True` en el entorno local;
- `ALLOWED_HOSTS` carga localhost, 127.0.0.1 y el dominio configurado;
- `CSRF_TRUSTED_ORIGINS` carga correctamente el origen HTTPS;
- `SESSION_COOKIE_SECURE=False` en desarrollo.

`python manage.py check` continuó mostrando:

```text
System check identified no issues (0 silenced).
```

---

# VS Code Dev Tunnels

Se configuró correctamente el proyecto para compartirlo temporalmente mediante el puerto 8000.

Configuración utilizada:

- Django ejecutado en `0.0.0.0:8000`;
- puerto reenviado desde VS Code;
- visibilidad pública cuando se necesita compartir;
- protocolo interno HTTP;
- URL pública HTTPS generada por VS Code.

Se resolvió un error `404` del túnel eliminando y recreando el puerto reenviado.

Cada integrante debe utilizar su propio dominio de Dev Tunnel en su `.env`:

```env
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,SU-DOMINIO.brs.devtunnels.ms
DJANGO_CSRF_TRUSTED_ORIGINS=https://SU-DOMINIO.brs.devtunnels.ms
```

El dominio personal del túnel no debe quedar escrito en `.env.example`.

---

# Documentación para el equipo

Se actualizó `README.md` con una guía completa para levantar BeatsCloud desde cero.

Incluye:

- clonado del repositorio;
- creación y activación de `.venv`;
- uso de `python -m pip`;
- instalación de `requirements.txt`;
- creación de `.env`;
- variables Django;
- PostgreSQL;
- Gmail SMTP;
- migraciones;
- administrador;
- ejecución local;
- Dev Tunnels;
- configuración Transbank;
- explicación de estados `PENDING`, `AUTHORIZED` y `CANCELLED`;
- seguridad de secretos;
- limpieza de historial Git;
- trabajo colaborativo;
- solución de errores frecuentes;
- pasos para compañeros con clones anteriores a la reescritura del historial.

También se actualizó `.env.example` con:

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=

TRANSBANK_COMMERCE_CODE=
TRANSBANK_API_KEY=
TRANSBANK_INTEGRATION_TYPE=TEST
```

además de las variables de PostgreSQL, Gmail y Stripe.

### Commits de documentación registrados

```text
1a3e302 Actualiza configuracion y documentacion del proyecto
7283e34 Actualiza registro de cambios de BeatsCloud
```

---

# 04-09-2026

## Revisión adicional de seguridad de Django

Se realizó una revisión de configuración orientada a separar correctamente desarrollo local y producción.

### `DJANGO_SECRET_KEY`

Se verificó que el entorno local está cargando una clave desde `.env` y no el valor fallback de desarrollo:

```text
USA_FALLBACK_DEV_SECRET_KEY: False
```

### `check --deploy`

Se ejecutó:

```powershell
python manage.py check --deploy
```

La revisión detectó recomendaciones de producción relacionadas con:

- HSTS;
- redirección obligatoria a HTTPS;
- `SESSION_COOKIE_SECURE`;
- `CSRF_COOKIE_SECURE`;
- `DEBUG=True`.

En el entorno local estas recomendaciones no se habilitaron de forma indiscriminada, porque el servidor de desarrollo utiliza HTTP.

### `CSRF_COOKIE_SECURE`

Se agregó:

```python
CSRF_COOKIE_SECURE = not DEBUG
```

Comportamiento esperado:

- desarrollo con `DEBUG=True`: `False`;
- producción con `DEBUG=False`: `True`.

Este cambio fue probado sin romper la ejecución local.

### Configuraciones no forzadas en desarrollo

No se considera completada todavía la activación permanente de:

```text
SECURE_SSL_REDIRECT
SECURE_HSTS_SECONDS
```

Estas opciones deben habilitarse solamente cuando exista un despliegue HTTPS real y permanente.

---

# 04-09-2026 — Eliminación segura de cuentas

Se implementó un flujo completo para que artistas y productores puedan eliminar su cuenta de BeatsCloud sin comprometer compras históricas ni dejar datos personales visibles.

## Acceso desde el perfil

Se agregó la opción:

```text
Eliminar mi cuenta
```

en la edición de perfil de:

- artistas;
- productores.

La eliminación no se ejecuta con un solo clic.

---

## Primera verificación: contraseña actual

El usuario debe ingresar su contraseña actual.

Si la contraseña es incorrecta:

- la cuenta no se elimina;
- no se envía código;
- el usuario permanece autenticado;
- se muestra un mensaje de error.

---

## Segunda verificación: correo electrónico

Después de validar correctamente la contraseña:

1. se genera un código aleatorio de 6 dígitos;
2. el código se envía al correo registrado;
3. la cuenta permanece activa mientras no se confirme el código;
4. el código se guarda hasheado en la sesión, no en texto plano;
5. la sesión vincula la solicitud con el ID del usuario;
6. se registra la hora de creación del código;
7. se controla el número de intentos.

### Seguridad del código

El código:

- vence después de 15 minutos;
- tiene un máximo de 5 intentos;
- se compara mediante `check_password`;
- se invalida cuando la verificación termina o supera los límites.

Si la cuenta no tiene un correo registrado, la eliminación no continúa.

---

## Correo HTML para confirmar la eliminación

El correo que contiene el código se modernizó para utilizar diseño HTML coherente con los correos de activación y recuperación de contraseña.

Incluye:

- encabezado visual de BeatCloud;
- nombre del usuario;
- explicación de la solicitud;
- código de 6 dígitos destacado;
- aviso de expiración de 15 minutos;
- advertencia de no compartir el código;
- indicación de ignorar el mensaje si el usuario no inició la solicitud;
- versión de texto como alternativa de compatibilidad.

El envío real mediante Gmail SMTP fue probado manualmente.

---

## Confirmación definitiva

La cuenta solamente se elimina cuando:

```text
contraseña correcta
        +
código de correo válido
```

El flujo definitivo es:

```text
Eliminar mi cuenta
        ↓
Contraseña actual
        ↓
Código de 6 dígitos al correo
        ↓
Validación del código
        ↓
Eliminación definitiva
```

---

## Eliminación transaccional de datos

La operación de base de datos se ejecuta dentro de:

```python
transaction.atomic()
```

Durante el proceso se eliminan o limpian, según corresponda:

- cuenta `User` de Django;
- perfil `Usuario`;
- información personal del perfil;
- descripción personal;
- redes sociales;
- foto de perfil;
- foto de fondo;
- Me gusta;
- carrito;
- compras e historiales propios que corresponden al usuario eliminado;
- suscripciones sin referencias históricas;
- transacciones personales eliminables mediante las relaciones configuradas;
- comentarios e intereses vinculados a la cuenta mediante las relaciones de Django.

Los archivos personales programados para borrado se eliminan después de confirmar la transacción de base de datos.

---

# Eliminación de cuenta de productor

La eliminación de un productor necesitó un tratamiento especial porque otros usuarios pueden haber comprado sus tracks.

## Tracks nunca comprados

Los tracks del productor que no poseen compras:

- se eliminan de la base de datos;
- dejan de estar disponibles;
- sus archivos de audio e imagen se programan para eliminación.

## Tracks ya comprados

Los tracks que poseen compras anteriores no se eliminan.

Se transfieren a un perfil técnico:

```text
UsuarioAnonimo
```

Este perfil:

- no representa al productor original;
- está inactivo;
- no tiene contraseña utilizable;
- no conserva correo del productor;
- no conserva redes sociales del productor;
- no conserva datos personales del productor;
- se reutiliza para contenido histórico anonimizado.

El track conservado reemplaza su descripción por un texto genérico que indica que el creador original eliminó su cuenta.

### Protección comercial

Un track transferido a `UsuarioAnonimo`:

- se conserva para quienes ya lo compraron;
- no puede agregarse nuevamente al carrito;
- no puede venderse a usuarios nuevos;
- no aparece como un productor normal.

### Catálogos

El perfil técnico `UsuarioAnonimo` fue excluido del:

- catálogo de usuarios;
- conteo de artistas/productores.

Los tracks históricos asociados al usuario técnico fueron retirados del catálogo general de nuevas compras.

---

# Suscripciones de un productor eliminado

También se revisaron las suscripciones creadas por productores.

Si una suscripción nunca tuvo transacciones:

- puede eliminarse.

Si una suscripción tiene transacciones históricas asociadas:

- se conserva;
- se reasigna a `UsuarioAnonimo`;
- su detalle se anonimiza.

Esto evita romper registros históricos pertenecientes a otros usuarios.

---

# Eliminación de cuenta de artista/comprador

Se detectó que originalmente:

```python
HistorialVenta.comprador
```

utilizaba eliminación en cascada.

Eso provocaba que, al borrar al artista comprador, también desapareciera la venta del historial del productor.

## Corrección del modelo

Se cambió la relación del comprador para utilizar:

```python
on_delete=models.SET_NULL
null=True
blank=True
```

De esta forma:

- el artista real desaparece;
- su nombre y correo dejan de existir;
- el perfil del artista deja de existir;
- la venta permanece como registro histórico;
- el productor mantiene la información de que existió una venta.

Se creó y aplicó la migración:

```text
app.0014_alter_historialventa_comprador
```

Resultado de la migración:

```text
Applying app.0014_alter_historialventa_comprador... OK
```

---

## Historial del productor: “Usuario eliminado”

Cuando el comprador ya eliminó su cuenta, el productor no ve un usuario inexistente ni un enlace roto.

El historial muestra:

```text
Usuario eliminado
```

Este texto:

- no corresponde a una cuenta real;
- no permite abrir un perfil;
- no conserva username;
- no conserva correo;
- permite mantener únicamente el registro histórico de la venta.

Se diferencia deliberadamente de:

```text
UsuarioAnonimo
```

que es el perfil técnico utilizado exclusivamente para conservar contenido adquirido de productores eliminados.

---

# Correo posterior a la eliminación

Después de completar correctamente la eliminación de la cuenta, BeatsCloud envía un segundo correo al correo que pertenecía al usuario antes del borrado.

Asunto:

```text
Tu cuenta fue eliminada | BeatCloud
```

El correo:

- confirma que la eliminación terminó;
- utiliza diseño HTML coherente con los demás correos de seguridad;
- informa que el perfil y acceso ya no están activos;
- explica que ciertos registros históricos pueden mantenerse de forma anonimizada;
- incluye versión texto para compatibilidad.

El envío se programa después de confirmar la operación de eliminación, evitando enviar una confirmación si la transacción de borrado no terminó correctamente.

La prueba manual confirmó la recepción de:

1. correo de código de verificación;
2. correo final de cuenta eliminada.

---

# Interfaz de eliminación

Se agregaron nuevas pantallas para el proceso:

```text
app/templates/app/eliminar_cuenta.html
app/templates/app/cuenta_eliminada.html
```

La pantalla de eliminación informa claramente:

- que la acción es permanente;
- que primero se requiere contraseña;
- que después se requiere verificación por correo;
- qué ocurre con los datos personales;
- qué ocurre con tracks de productores;
- qué ocurre con registros históricos.

---

# Rutas del flujo de eliminación

Se incorporaron rutas para:

```text
/cuenta/eliminar/
/cuenta/eliminar/confirmar/
```

La confirmación definitiva utiliza `POST` y CSRF.

---

# Pruebas automatizadas de eliminación de cuenta

`app/tests.py` se amplió para cubrir el nuevo flujo.

Las pruebas incluyen, entre otros casos:

- usuario no autenticado no puede acceder directamente;
- usuario autenticado puede ver la pantalla;
- contraseña incorrecta no elimina;
- contraseña correcta envía correo y no elimina inmediatamente;
- código incorrecto no elimina;
- código correcto elimina;
- productor conserva track comprado bajo `UsuarioAnonimo`;
- track no comprado se elimina;
- historial de venta permanece cuando el artista comprador se elimina;
- comprador del historial queda en `NULL`;
- el productor visualiza `Usuario eliminado`;
- `UsuarioAnonimo` no aparece en el catálogo de usuarios.

### Resultado final

Se ejecutó:

```powershell
python manage.py test app
```

Resultado:

```text
Found 9 test(s).
.........
Ran 9 tests

OK
```

---

# Verificaciones técnicas finales del 04-09-2026

## Compilación de la vista

Se ejecutó:

```powershell
python -m py_compile app\views.py
```

Resultado:

```text
Sin errores de sintaxis.
```

## Migración

Se ejecutó:

```powershell
python manage.py migrate
```

Resultado relevante:

```text
Applying app.0014_alter_historialventa_comprador... OK
```

## Tests

Se ejecutó:

```powershell
python manage.py test app
```

Resultado:

```text
9 tests
OK
```

## Django system check

Se ejecutó:

```powershell
python manage.py check
```

Resultado:

```text
System check identified no issues (0 silenced).
```

## Prueba manual completa

Se comprobó manualmente:

- acceso a “Eliminar mi cuenta”;
- validación de contraseña;
- recepción del correo HTML con código;
- ingreso del código;
- eliminación real de la cuenta;
- recepción del correo final de eliminación;
- funcionamiento general del flujo.

Estado:

```text
PROBADO MANUALMENTE
```

---

# Archivos relacionados con la funcionalidad de eliminación

Durante esta etapa se modificaron o agregaron principalmente:

```text
app/models.py
app/views.py
app/urls.py
app/tests.py
app/templates/app/editar_perfil.html
app/templates/app/editar_perfil_p.html
app/templates/app/eliminar_cuenta.html
app/templates/app/cuenta_eliminada.html
app/templates/registration/perfil_productor.html
app/migrations/0014_alter_historialventa_comprador.py
```

También se utilizaron scripts temporales de apoyo durante las pruebas y aplicación de cambios.

> Los scripts temporales de instalación, reparación o prueba no forman parte de la funcionalidad final y no deberían subirse al repositorio salvo que el equipo decida conservarlos expresamente.

---

# Estado actual de BeatsCloud al 04-09-2026

## Cuentas

- Registro funcional.
- Activación por correo.
- Validación de correo duplicado.
- Recuperación segura de contraseña.
- Eliminación de cuenta para artista y productor.
- Confirmación por contraseña.
- Confirmación adicional por correo.
- Código con vencimiento e intentos limitados.
- Correo de confirmación de eliminación.
- Eliminación de datos personales.

## Perfiles

- Artistas y productores.
- Perfiles públicos y privados.
- Redes sociales seguras.
- Edición de perfiles.
- Eliminación desde edición de perfil.
- Perfiles eliminados dejan de estar disponibles.
- `UsuarioAnonimo` oculto de los catálogos normales.

## Tracks

- Subida solo para productores.
- Validación real de audio.
- Edición y eliminación seguras.
- Reproducción controlada.
- Descarga protegida.
- Prevención de reemplazo de audio vendido.
- Tracks no comprados se eliminan con el productor.
- Tracks ya comprados se conservan anonimizados.
- Tracks anonimizados no se vuelven a vender.

## Comunidad

- Me gusta.
- Comentarios.
- Eliminación segura de comentarios.
- Datos vinculados a usuarios eliminados se limpian de acuerdo con las relaciones configuradas.

## Catálogo

- Búsqueda.
- Filtros.
- Paginación.
- Ordenamiento.
- Indicador de compra previa.
- Exclusión del perfil técnico `UsuarioAnonimo`.

## Carrito

- Ventas pendientes.
- Prevención de duplicados.
- Eliminación segura.
- Pago mediante Webpay TEST.

## Webpay

- Carrito probado.
- Suscripciones probadas.
- Transacciones autorizadas correctamente.
- Cancelaciones registradas.
- Credenciales leídas desde `.env`.
- Estados `PENDING`, `AUTHORIZED`, `CANCELLED`.

## Historiales

- Historial de compra.
- Historial de venta.
- Ventas de compradores eliminados se conservan.
- Comprador eliminado aparece como `Usuario eliminado`.
- No se conserva vínculo a la cuenta eliminada.

## Seguridad

- `.env` ignorado.
- Secrets fuera del código.
- Historial Git limpiado.
- POST + CSRF en acciones sensibles.
- Validación de propietario.
- Retorno Webpay validado.
- Descargas protegidas.
- `ALLOWED_HOSTS` configurable.
- `CSRF_TRUSTED_ORIGINS` configurable.
- `SESSION_COOKIE_SECURE` depende de `DEBUG`.
- `CSRF_COOKIE_SECURE` depende de `DEBUG`.
- `DJANGO_SECRET_KEY` real comprobada en `.env`.
- Eliminación de cuenta con doble verificación.
- Códigos de eliminación almacenados hasheados en sesión.
- Expiración e intentos limitados para código de eliminación.

## Correos

- Activación de cuenta en HTML.
- Recuperación de contraseña en HTML.
- Código de eliminación en HTML.
- Confirmación final de eliminación en HTML.
- Gmail SMTP probado.

## Configuración y equipo

- README actualizado.
- `.env.example` actualizado.
- Dev Tunnels documentado.
- Instrucciones para nuevos integrantes.
- Repositorio preparado para configuración local por integrante.

---

# Puntos que siguen pendientes o deben decidirse al desplegar

Los siguientes puntos no deben marcarse como implementados todavía:

- definir `DEBUG=False` en el entorno real de producción;
- activar `SECURE_SSL_REDIRECT=True` solamente cuando el despliegue HTTPS sea permanente;
- configurar HSTS únicamente cuando el dominio funcione completamente bajo HTTPS;
- volver a ejecutar `python manage.py check --deploy` en el servidor real;
- decidir la política de limpieza automática para transacciones `PENDING` antiguas;
- eliminar imports duplicados o código de baja prioridad en `views.py`;
- eliminar el bundle privado del historial Git antiguo cuando ya no sea necesario;
- documentar en README el nuevo flujo de eliminación de cuenta si el equipo desea incluirlo en las instrucciones generales;
- revisar y eliminar scripts temporales locales antes del próximo commit.

---

# Verificaciones recomendadas antes de cada push

```powershell
python -m py_compile app\views.py
python manage.py test app
python manage.py check
git status --short
git diff --stat
```

Si se modifica `requirements.txt`:

```powershell
python -m pip check
```

Si se modifican modelos:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Antes de subir:

```powershell
git diff
```

para comprobar que no se incluyan:

- credenciales;
- `.env`;
- archivos temporales;
- scripts de reparación que no deban quedar en el repositorio;
- datos de prueba.

---

# Nota final para el equipo

Todos pueden trabajar con el mismo código de GitHub, pero cada integrante debe mantener:

- su propio `.env`;
- su propia `.venv`;
- su configuración local de PostgreSQL;
- su propio dominio Dev Tunnel;
- sus propias credenciales autorizadas.

Los datos locales y los secretos no se sincronizan mediante Git.

**Nunca se deben subir credenciales reales a GitHub.**

---

# Resumen de la revisión del registro

El registro anterior llegaba hasta el 31-08-2026. En esta actualización se incorporaron los cambios posteriores verificados durante la continuación del proyecto, principalmente:

1. revisión adicional de seguridad de Django;
2. `CSRF_COOKIE_SECURE` por entorno;
3. comprobación de `DJANGO_SECRET_KEY`;
4. auditoría con `check --deploy`;
5. eliminación segura de cuentas de artistas y productores;
6. doble verificación por contraseña y correo;
7. código de 6 dígitos con expiración e intentos limitados;
8. correos HTML de eliminación;
9. anonimización de tracks comprados;
10. perfil técnico `UsuarioAnonimo`;
11. conservación de ventas con comprador eliminado;
12. etiqueta `Usuario eliminado` en historial del productor;
13. migración `0014_alter_historialventa_comprador`;
14. pruebas automatizadas ampliadas a 9;
15. pruebas de compilación, migración y `manage.py check`;
16. prueba manual completa del flujo de eliminación.

Con esto el documento queda actualizado al estado probado del proyecto al **04-09-2026**.
