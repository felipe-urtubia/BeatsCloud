# REGISTRO DE CAMBIOS — BEATSCLOUD

**Proyecto:** BeatsCloud  
**Periodo cubierto:** 28-08-2026 al 31-08-2026  
**Última actualización:** 31-08-2026

> Este documento resume los cambios funcionales, visuales, de seguridad, configuración y documentación realizados durante la etapa final de mejora del proyecto BeatsCloud.

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

`settings.py` ahora construye:

- `DEBUG`;
- `ALLOWED_HOSTS`;
- `CSRF_TRUSTED_ORIGINS`.

Se mantuvo:

```python
SESSION_COOKIE_SECURE = not DEBUG
```

para permitir HTTP local durante desarrollo y usar cookies seguras cuando `DEBUG=False`.

### Verificación realizada

Se comprobó desde Django que:

- `DEBUG=True`;
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

---

# Commit de documentación y configuración

Se creó el commit:

```text
1a3e302 Actualiza configuracion y documentacion del proyecto
```

Incluye:

- `.env.example`;
- `README.md`;
- `beatcloud/settings.py`.

El commit fue subido correctamente a:

```text
origin/main
```

y posteriormente:

```powershell
git status --short
```

no mostró archivos pendientes.

---

# Estado actual de BeatsCloud

Al 31-08-2026:

## Cuentas

- Registro funcional.
- Activación por correo funcional.
- Recuperación de contraseña funcional.
- Validación de correo duplicado.
- Perfiles protegidos donde corresponde.

## Perfiles

- Artistas y productores.
- Perfiles públicos y privados.
- Redes sociales seguras.
- Edición de perfiles.

## Tracks

- Subida solo para productores.
- Validación real de audio.
- Edición y eliminación seguras.
- Reproducción controlada.
- Descarga protegida.
- Prevención de reemplazo de audio cuando existen compras.

## Comunidad

- Me gusta.
- Comentarios.
- Eliminación segura de comentarios.

## Catálogo

- Búsqueda.
- Filtros.
- Paginación.
- Ordenamiento.
- Indicador de compra previa.

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

## Seguridad

- `.env` ignorado.
- Secrets fuera del código.
- Historial de Git limpiado.
- POST + CSRF en acciones sensibles.
- Validación de propietario.
- Retorno Webpay validado.
- Descargas protegidas.
- `ALLOWED_HOSTS` configurable.
- `CSRF_TRUSTED_ORIGINS` configurable.

## Configuración y equipo

- README actualizado.
- `.env.example` actualizado.
- Dev Tunnels documentado.
- Instrucciones para nuevos integrantes.
- Repositorio sincronizado con GitHub.

---

# Próximos puntos de revisión

Los siguientes puntos pueden revisarse posteriormente sin afectar el funcionamiento actual:

- comprobar de forma segura que `DJANGO_SECRET_KEY` real está definido en `.env` y no se usa el fallback de desarrollo;
- ejecutar `python manage.py check --deploy` para revisar recomendaciones de producción;
- decidir configuración de `CSRF_COOKIE_SECURE`;
- configurar `SECURE_SSL_REDIRECT` solo cuando exista un despliegue HTTPS real;
- definir HSTS únicamente cuando el sitio esté correctamente desplegado en HTTPS;
- limpiar transacciones `PENDING` antiguas que hayan quedado abandonadas;
- eliminar imports duplicados o código de baja prioridad;
- eliminar el bundle local del historial antiguo cuando ya no sea necesario conservarlo.

---

# Verificaciones recomendadas antes de cada push

```powershell
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
