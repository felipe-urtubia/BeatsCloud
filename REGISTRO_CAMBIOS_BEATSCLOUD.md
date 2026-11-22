# REGISTRO DE CAMBIOS — BEATSCLOUD

**Proyecto:** BeatsCloud
**Periodo cubierto:** 28-08-2026 al 06-11-2026
**Última actualización:** 06-11-2026

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

## Seguimiento de cambios recientes

- Se documentaron también la corrección del borrado de usuarios desde Django
  Admin, los mensajes en español y el rechazo de reutilizar la contraseña
  actual al restablecerla, y los controles para mostrar u ocultar ambas claves.
- Se registró el rediseño visual de los botones “Acceder” y “Registrarse” en
  las barras de navegación de React.
- Verificación final del backend: `python manage.py test app` ejecutó 48
  pruebas correctamente.

## Acceso visible a registro en navegación móvil

- Se agregó una acción “Registrarse” explícita y destacada en el panel lateral
  cuando no hay una sesión activa, junto a “Acceder”.
- El botón abre el modo registro y cierra el menú móvil; conserva contraste,
  icono y estados visibles de interacción.
- Verificación: `npm run lint` y `npm run build` finalizaron correctamente.

## Ajustes recientes de administración, recuperación y acceso

- Se corrigió la representación de `HistorialCompra` para que la pantalla de
  confirmación al borrar usuarios en Django Admin pueda mostrar perfiles y
  tracks relacionados sin acceder a atributos inexistentes. Se agregó una
  prueba de regresión para ese caso.
- En la recuperación de contraseña, se tradujo al español el mensaje de
  similitud de contraseña de Django y se agregó la validación para impedir que
  la contraseña nueva sea igual a la actual.
- En la pantalla React para restablecer contraseña se añadieron controles
  accesibles para mostrar u ocultar la contraseña nueva y su confirmación.
- Se hicieron más visibles las acciones “Acceder” y “Registrarse” en las barras
  de navegación de React, con estilos destacados, iconos y estados de foco.
- Se verificaron los correos HTML de confirmación y recuperación para conservar
  el diseño BeatsCloud y los enlaces correctos.

Verificaciones realizadas:

```powershell
python manage.py test app
python manage.py check
cd frontend\client
npm run lint
npm test
npm run build
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


---

# Actualización 08-09-2026 — previews de audio de 30 segundos

Se implementó un sistema de vista previa de audio para evitar que usuarios sin compra reciban el archivo completo del track durante la reproducción pública.

Cambios realizados:

1. se agregó el campo `preview` al modelo `Track`;
2. se creó la migración `0015_track_preview`;
3. se agregó `FFMPEG_PATH` a la configuración, utilizando `.env` para la ruta local y `FFMPEG_PATH=ffmpeg` en `.env.example`;
4. se creó `app/audio_utils.py` para generar automáticamente un MP3 de hasta 30 segundos mediante FFmpeg;
5. los tracks nuevos generan su preview automáticamente al ser subidos;
6. se agregó el comando `python manage.py generar_previews` para crear previews faltantes de tracks existentes;
7. se creó una ruta pública separada para reproducir únicamente el archivo preview;
8. la ruta de audio completo quedó restringida a:
   - productor dueño del track;
   - usuario que ya compró el track;
9. usuarios no autenticados y artistas sin compra reciben únicamente el preview;
10. `detalle_track.html` selecciona automáticamente entre preview y audio completo;
11. `catalogo.html` aplica la misma regla de reproducción;
12. el reproductor permite pausar, repetir, adelantar y retroceder dentro del archivo disponible, pero el preview físico no contiene más de los primeros 30 segundos;
13. se generaron previews para los tracks existentes;
14. se reinició la numeración de tracks de prueba después de limpiar tracks antiguos asociados al usuario técnico eliminado;
15. se verificó manualmente el comportamiento del preview tanto en detalle como en catálogo.

Reglas finales de reproducción:

- visitante sin sesión: preview de hasta 30 segundos;
- artista sin compra: preview de hasta 30 segundos;
- comprador: audio completo;
- productor dueño: audio completo.

La protección implementada corresponde a control de acceso y separación física entre el preview y el archivo original; no se considera DRM.

Verificaciones realizadas:

```powershell
python manage.py test app
python manage.py check
python manage.py makemigrations --check
git diff --check
```

Resultados verificados:

- 22 pruebas automatizadas: `OK`;
- `manage.py check`: sin problemas;
- `makemigrations --check`: `No changes detected`;
- `git diff --check`: sin errores de espacios o formato, solo advertencias normales de conversión LF/CRLF en Windows;
- prueba manual del preview de 30 segundos: correcta.

Con esta actualización, BeatsCloud dispone de previews públicos separados del audio original y mantiene el acceso completo únicamente para compradores y propietarios del track.

---

# 05-11-2026 — Sincronización de registros Django con React

Se amplió la lectura de datos de Django en el frontend React para que la interfaz
en modo `hybrid` refleje los registros persistidos, sin sustituir la base de
datos ni exponer información privada de otros usuarios.

## API Django

1. Se agregó `GET /api/usuarios/` para mostrar el directorio de usuarios con
   perfil, excluyendo la cuenta técnica `UsuarioAnonimo` y sin exponer correos
   ni relaciones privadas.
2. La sesión privada ahora incluye los IDs de los tracks que le gustan al
   usuario y sus suscripciones activas, incluidas las autorizadas mediante
   Webpay.
3. La respuesta de suscripciones ahora incluye los datos públicos del
   productor asociado.
4. Se amplió el endpoint de comentarios para permitir eliminar un comentario
   mediante `DELETE`, únicamente por su autor autenticado.

## Frontend React

1. La sincronización inicial carga todas las páginas del catálogo, el directorio
   público, planes de suscripción y, para el usuario autenticado, carrito,
   historiales de compras y ventas.
2. Los perfiles React reflejan los usuarios, tracks, compras, ventas, likes y
   suscripciones existentes de Django.
3. Los comentarios persistidos se cargan al abrir el detalle del track; las
   altas y eliminaciones se guardan en Django y se vuelven a cargar desde el
   servidor.
4. Al cerrar sesión se limpian del estado React los historiales y datos
   privados del usuario anterior.
5. Se deshabilitó la contratación de suscripciones desde React en modo
   `hybrid`, porque todavía no existe un flujo React que cree esa relación de
   manera persistente. Los planes y membresías existentes sí se muestran.
6. Se actualizó la documentación del README sobre lo sincronizado y las
   integraciones aún pendientes.

## Configuración y verificaciones

- Se añadieron `http://localhost:3000` y `http://127.0.0.1:3000` a
  `DJANGO_CSRF_TRUSTED_ORIGINS` en el `.env` local, conservando el origen del
  Dev Tunnel. El `.env` es configuración personal y no debe subirse a Git.
- Se corrigió en el README el comando de clonación para utilizar la rama
  `main`, donde se encuentra integrado React.
- Se añadieron pruebas para el directorio público, likes/suscripciones de la
  sesión y eliminación autorizada de comentarios.

Verificaciones realizadas:

```powershell
python manage.py test app
python manage.py check
python manage.py makemigrations --check --dry-run
cd frontend\client
npm run lint
npm test
npm run build
npm audit
```

Resultados verificados: 33 pruebas Django y 4 pruebas frontend correctas,
compilación TypeScript y build de React correctos, configuración y migraciones
sin problemas, y `npm audit` sin vulnerabilidades reportadas.

## Limitaciones pendientes

- React todavía no persiste la edición de perfiles ni la subida de tracks.
- La contratación de suscripciones debe realizarse desde Django; React solo
  refleja los planes y membresías existentes.
- La activación de cuentas y la confirmación final de Webpay siguen ocurriendo
  en las vistas HTML de Django.
- La sincronización de lectura desde la API no reemplaza la página Django ni
  significa que todas las acciones disponibles allí estén implementadas en
  React.

## Corrección de inicio de sesión React con error 403

- Se verificó el handshake CSRF del endpoint de login con `Origin:
  http://localhost:3000` mediante una prueba Django con comprobación CSRF
  habilitada.
- El cliente React ahora renueva el token y reintenta una sola vez cuando
  Django responde con su página HTML de rechazo CSRF; no reintenta los errores
  JSON de credenciales o de cuenta inactiva.
- El cliente distingue el 403 HTML de CSRF y muestra un mensaje indicando que
  se debe reiniciar Django y autorizar el origen de React.
- En README se agregó la indicación para autorizar el origen HTTPS exacto del
  túnel de React si se usa uno en el puerto `3000`. El dominio del túnel de
  Django en el puerto `8000` no lo reemplaza.

Verificación realizada:

```powershell
python manage.py test app.test_api_shim.ApiShimSecurityTests.test_login_api_accepts_local_react_origin_with_csrf
cd frontend\client
npm run lint
npm run build
```

La prueba CSRF, el chequeo TypeScript y la compilación de React finalizaron
correctamente.

## Activación de cuentas en React

- Los enlaces de activación enviados por el registro de React ahora apuntan a
  `/activar/<uid>/<token>/` en el frontend. La URL base se configura con
  `FRONTEND_URL` en el `.env` raíz (por defecto `http://localhost:3000`).
- Se agregó una pantalla React para mostrar el estado de validación y volver al
  inicio de sesión.
- Se agregó `POST /api/auth/activar/`, que verifica el token y activa la cuenta
  sin iniciar sesión; los tokens inválidos, expirados o de usuarios
  inexistentes se rechazan. Repetir una activación válida es seguro.
- El formulario de registro HTML de Django conserva su enlace y flujo actuales.

Verificaciones realizadas:

```powershell
python manage.py test app.test_api_shim
python manage.py check
cd frontend\client
npm run lint
npm test
npm run build
```

## Recuperación de contraseña en React

- Se agregó el acceso “¿Olvidaste tu contraseña?” al inicio de sesión React y
  un formulario para solicitar el enlace por correo.
- Se informa cuando el correo no está asociado a una cuenta activa, y se
  muestra la confirmación de envío cuando sí corresponde enviar el enlace.
- Los enlaces de restablecimiento del flujo React usan `FRONTEND_URL` y abren
  `/restablecer/<uid>/<token>/`. React permite ingresar y confirmar la nueva
  contraseña; Django verifica el token de un solo uso, su vencimiento y los
  validadores configurados antes de guardarla.
- El flujo HTML de recuperación de Django permanece disponible. Ambos flujos
  comparten los validadores y el generador de tokens de Django.

Verificaciones realizadas:

```powershell
python manage.py test app.test_api_shim
python manage.py check
cd frontend\client
npm run lint
npm test
npm run build
```

### Mensaje para correo no asociado

- En la solicitud React, Django comprueba si el correo corresponde a una
  cuenta activa con contraseña utilizable. Si no encuentra una, responde con
  un mensaje explícito para que la persona pueda corregirlo.
- Si la encuentra, envía el enlace React y confirma que debe revisar su correo.
- Esta respuesta diferencia correos existentes de no existentes, lo que
  permite inferir si una dirección está registrada.

## Registro: nombre artístico separado del usuario de acceso

- Se agregó `Usuario.nombre_artistico` (máximo 100 caracteres) y la migración
  `0016_usuario_nombre_artistico`; las cuentas existentes conservan un valor
  vacío en la base y muestran como alternativa su nombre anterior o usuario.
- Los formularios de React y Django ahora piden nombre, apellido, nombre
  artístico y un usuario de acceso independiente.
- El API guarda el nombre artístico con el perfil, lo devuelve en las
  respuestas públicas y de sesión, y React lo usa para mostrar perfiles y
  productores de tracks.
- Se añadió prueba de registro con un nombre artístico con espacios, envío de
  correo y rechazo cuando falta el nombre artístico.

## Diseño de correos de registro y recuperación

- Se actualizaron los correos HTML de confirmación de cuenta y recuperación
  para reflejar la interfaz React de BeatsCloud: fondo oscuro, tarjetas
  grafito, bordes azul grisáceo y botones/acento ámbar.
- El estilo se aplica tanto a la recuperación desde React como al flujo HTML
  existente de Django; se conservaron sus enlaces, textos alternativos y
  avisos de seguridad.
- Se agregaron comprobaciones de las plantillas HTML en pruebas de envío.

La migración debe aplicarse en cada base local antes de utilizar la nueva
columna:

```powershell
python manage.py migrate
```

## Resumen final de cambios recientes

- Se documentaron la corrección del borrado de usuarios desde Django Admin,
  los mensajes de validación de contraseña en español, el rechazo a reutilizar
  la contraseña actual y los controles para mostrar u ocultar las contraseñas.
- Se registró el rediseño visual de los botones “Acceder” y “Registrarse” en
  la navegación de React.
- Verificación final del backend: `python manage.py test app` ejecutó 48
  pruebas correctamente.
- En el panel lateral móvil se agregó “Registrarse” como botón visible junto
  a “Acceder”, y al seleccionarlo se abre el formulario de registro y se cierra
  el menú.
- Se corrigió el estilo del botón “Registrarse” que se veía negro en la
  navegación: se reemplazó el fondo degradado por un fondo naranja sólido y
  estados hover/foco visibles en TopBar, Navbar y panel lateral. Lint y build
  de React finalizaron correctamente.
- En el formulario de acceso se agregó un control para mostrar u ocultar la
  contraseña antes de iniciar sesión, conservando el comportamiento de envío.
- Se conectó la subida de pistas de productores en modo `hybrid` con la API de
  Django: el formulario envía el audio y los datos persistidos, y solo muestra
  la pista como publicada cuando el backend confirma el guardado.
- Se agregó una prueba de regresión que confirma que una pista subida queda
  guardada y aparece en el catálogo y en el perfil público del productor.

# 05-11-2026

## Integración de funciones Django pendientes en React

- Se conectó la edición del perfil propio a Django para guardar biografía,
  enlaces sociales y archivos de avatar/banner. Se corrigió el parseo de
  formularios `multipart/form-data` enviados mediante `PATCH`, tanto para
  perfiles como para editar la portada de una pista.
- La carga y edición de pistas en modo `hybrid` ahora persisten los metadatos
  disponibles en el modelo Django: tipo de recurso, BPM, tonalidad, mood,
  duración, opciones de archivos, género y portada subida. Las cargas antiguas
  que omiten estos nuevos campos conservan valores predeterminados.
- Se conectaron la creación y contratación de planes de suscripción con las API
  y el flujo de Webpay existente. Los retornos de pago hacia React muestran el
  resultado procesado por Django; no se efectuó una transacción real en este
  cambio.
- Se conectó el reclamo de pistas gratuitas, la descarga protegida del archivo
  disponible, la descarga de la maqueta de preview y la consulta de datos de
  compra con huella HMAC. Se eliminaron descargas `.txt` que simulaban archivos
  de audio o términos legales. El comprobante informa que no es un contrato ni
  establece por sí solo condiciones de licencia.
- Se conectó la eliminación de cuenta desde React mediante verificación de
  contraseña y código enviado por correo, reutilizando la rutina Django para
  anonimizar o retirar datos de manera segura.
- La biblioteca de compras y membresías del perfil de artista solo muestra los
  datos privados de la sesión propia.
- Se agregaron pruebas de API para creación de planes, carga y edición de
  metadatos, edición de perfil, reclamo gratuito/licencia y eliminación de
  cuenta con código. Se actualizó la prueba de métodos HTTP de suscripciones.
- El README describe las funciones conectadas y los límites reales del modelo:
  una pista almacena un archivo de audio (no WAV más stems), los planes no
  persisten beneficios/periodo y el comprobante HMAC no equivale a una licencia
  legal.

Verificaciones ejecutadas:

```powershell
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py check
cd frontend\client
npm run lint
npm test
npm run build
```

Resultado: 54 pruebas Django aprobadas; 4 pruebas frontend aprobadas; lint,
build, comprobación de migraciones y `manage.py check` finalizados correctamente.

## Aclaración de comprobantes y descargas

- Se reemplazó el verificador local simulado por un aviso que explica que
  Django no ofrece una consulta pública de códigos. Los comprobantes se
  consultan desde la biblioteca de compras de la cuenta autenticada.
- Se retiraron de la interfaz afirmaciones de derechos, reparto de regalías,
  archivos WAV/stems, condiciones de uso gratuito y protección ante reclamos
  que no están respaldadas por los datos del sistema.
- El perfil de productor conserva el historial de ventas, sin ofrecer un
  certificado legal generado localmente.

## Persistencia del subgénero

- Se agregó el campo opcional `Track.subgenre` y la migración `0018_track_subgenre`.
- El formulario de pista, la API Django y los DTO/mapeadores React ahora guardan
  y recuperan el subgénero en modo `hybrid`.

## Validación de portadas al editar pistas

- La API valida las imágenes de portada de las solicitudes `PATCH` con el
  mismo `ImageField` de Django antes de persistirlas.
- La prueba de edición multipart usa una imagen válida y confirma que se guarda.

---

## Cierre de Webpay TEST - 5 y 6 de noviembre de 2026

### Compras y membresias

- Se verifico el checkout de canciones desde React y Django.
- Se completo una compra de prueba por $11.900 CLP,
  con autorizacion de Transbank, entrega y descarga.
- Se habilito la contratacion VIP desde el perfil del productor.
- Se probo el plan VIP de $1.000 CLP de felia7x.
- Se identifico un problema causado por una sesion de navegador
  diferente durante el retorno de Webpay.
- Se corrigio el retorno para validar la orden y su token,
  sin depender del usuario autenticado en el navegador.
- Se incorporo activacion de membresias dentro de una
  transaccion atomica de PostgreSQL.
- Se recupero la orden VIP 49 consultando el estado AUTHORIZED
  directamente a Transbank TEST, sin iniciar otro cobro.
- Se confirmo la membresia activa en PostgreSQL y React.

### Conciliacion y archivo de ordenes antiguas

- Se auditaron las ordenes 19745345 y 31674163.
- Ambas carecian de token guardado, detalle de productos
  y evidencia suficiente para una conciliacion automatica.
- Se creo un respaldo privado fuera del repositorio.
- Se incorporaron archived_for_review, archived_at y
  archive_reason al modelo WebpayTransaction.
- Se creo y aplico la migracion 0022_archivo_legacy_webpay.
- Las dos ordenes se archivaron conservando sus estados
  AUTHORIZED y PENDING, respectivamente.
- Se modifico el control de inicio para excluir exclusivamente
  las ordenes archivadas, sin desproteger las demas.
- Se verifico el desbloqueo de felipeurtubia y felia7x.
- Las ordenes temporales de comprobacion se revirtieron.
- Se agregaron barreras para impedir entregas locales
  desde retornos de ordenes archivadas.
- Las dos ordenes siguen pendientes de conciliacion financiera;
  el archivo no implica cancelacion en Transbank.

### Pruebas y seguridad

- Se incorporaron pruebas de retorno con sesion diferente,
  activacion de membresias, archivo y bloqueo de entregas.
- La suite Django finalizo con 87 pruebas aprobadas.
- python manage.py check no reporto errores.
- No quedaron migraciones pendientes.
- Se verificaron las cuatro ordenes existentes y la membresia VIP.
- Se auditaron archivos preparados para Git, incluyendo tokens,
  credenciales y archivos privados.
- Se sustituyeron ejemplos de credenciales del README por
  marcadores explicitos.
- La auditoria automatica no sustituye la revision manual.

### Control de versiones

- Se prepararon 67 archivos de Django, React, pruebas y documentacion.
- Se creo el commit local 3ffa625:
  feat: integrar mejoras de BeatCloud y pagos Webpay.
- Se comprobo la rama main y la existencia de origin/main.
- La publicacion mediante git push quedo pendiente.

### Mejoras pendientes

- Evaluar evitar llamadas commit a Transbank cuando una orden
  ya esta archivada, siempre que pueda identificarse con seguridad.
- Resolver manualmente la conciliacion financiera de las dos
  ordenes antiguas si se obtiene evidencia suficiente.
- No considerar probados los cobros recurrentes ni los pagos
  de produccion: las verificaciones fueron en ambiente TEST.

---

## Mejoras del carrito y reproductor - 05-11-2026

### Carrito de compras

- Se elimino el mensaje sobre la validacion de Django.
- Se conservo la validacion real de Webpay.
- Se comprobo visualmente el carrito.

### Reproductor de audio

- Se agrego un boton X para cerrar el reproductor.
- Al cerrar, el audio se detiene y se limpia el estado.
- Se incorporaron controles de reproducir y pausar.
- Se agregaron botones para retroceder y avanzar 5 segundos.
- Se mejoro el control de progreso y duracion.
- Se corrigio la sincronizacion del estado de reproduccion.
- Se conserva la limitacion del archivo de vista previa.

### Validaciones

- Compilacion React/Vite aprobada.
- Cuatro pruebas automatizadas frontend aprobadas.
- Funcionamiento visual confirmado en navegador.
- No se modificaron Django, PostgreSQL ni los pagos.
- Cambios preparados para un nuevo commit.

---

## Confirmacion previa de compra - 06-11-2026

### Mejoras implementadas

- Se incorporo una ventana de confirmacion antes de Webpay.
- El carrito incluye el boton Revisar compra.
- La ventana muestra canciones, subtotal, IVA y total estimado.
- Se agrego la opcion Volver al carrito.
- Se permite cerrar la confirmacion con Escape.
- El usuario conserva sus productos al regresar al carrito.
- Solo el boton de confirmacion inicia el checkout existente.
- La validacion definitiva del pago permanece en Django.

### Verificaciones

- Compilacion React/Vite aprobada.
- Cuatro pruebas automatizadas frontend aprobadas.
- Apertura de la ventana confirmada en navegador.
- Cierre mediante boton y tecla Escape confirmado.
- No se inicio un nuevo pago durante las pruebas visuales.
- No se modificaron Django, PostgreSQL ni Webpay.
- La confirmacion final contra Webpay queda pendiente de prueba.

---

## Mejoras del catalogo React - 06-11-2026

### Filtros de precios

- Se incorporaron cuatro rangos de precios en pesos chilenos.
- Se conservaron los filtros Todos, De pago y Gratis.
- Se actualizaron las opciones de restablecimiento.

### Ordenamiento

- Se agrego el ordenamiento por antiguedad.
- Se agrego el ordenamiento por precio mayor.
- Se agrego el ordenamiento alfabetico A-Z y Z-A.
- Se conservaron las opciones anteriores.

### Paginacion

- Se agrego paginacion de 6, 12 y 24 canciones.
- Se incorporaron botones Primera, Anterior, Siguiente y Ultima.
- Se actualizaron las vistas de tabla y cuadricula.
- Los cambios de filtros reinician la navegacion de paginas.
- La paginacion se realiza en React, sobre las pistas cargadas.

### Validaciones

- Compilacion React/Vite aprobada.
- Cuatro pruebas automatizadas existentes de Webpay aprobadas.
- Filtros y ordenamiento verificados visualmente.
- Paginacion verificada visualmente.
- No se modificaron Django, PostgreSQL ni los pagos.

---

## Generos dinamicos Django y React - 06-11-2026

### Catalogo

- Se reemplazo el selector fijo de generos por opciones dinamicas.
- Se reutilizan los generos recibidos desde la API de Django.
- Se conserva el genero original de cada cancion.
- Se eliminaron las conversiones Jazz a Boom-Bap y Metal a Drill.
- Se mantienen los filtros, ordenamiento y paginacion.

### Publicacion y edicion

- El formulario React utiliza los generos registrados en Django.
- Se conservan los identificadores reales de cada genero.
- La publicacion envia el ID del genero seleccionado.
- La edicion envia el ID correspondiente cuando cambia el genero.
- Se conserva el modo de demostracion.
- Se valida la seleccion del genero antes de guardar.

### Validaciones

- Compilacion React/Vite aprobada.
- Cuatro pruebas automatizadas existentes de Webpay aprobadas.
- Catalogo y selector de generos verificados visualmente.
- Selector de publicacion verificado visualmente.
- Formulario de edicion y genero original verificados visualmente.
- No se realizaron publicaciones ni ediciones reales en la prueba.
- Persistencia real de generos pendiente de prueba controlada.
- Django y PostgreSQL no fueron modificados.

---

## Pruebas automatizadas de generos - 06-11-2026

### Pruebas incorporadas

- Se agrego app/test_generos_api.py con cuatro pruebas Django.
- Se verifico la publicacion con el ID real del genero Jazz.
- Se verifico la edicion de una cancion de Jazz a Metal.
- Se verifico el rechazo de un ID inexistente al editar.
- Se verifico el rechazo de un ID inexistente al publicar.

### Resultados

- Cuatro pruebas ejecutadas: 4 aprobadas y 0 fallidas.
- Django System Check: sin problemas.
- Las pruebas utilizaron una base PostgreSQL temporal.
- La base temporal fue eliminada al finalizar.
- No se realizaron modificaciones a la base beatsbd.
- No se modificaron canciones ni pagos existentes.
- No se cambio la logica de produccion de Django.
- El archivo de pruebas queda disponible para futuras regresiones.

### Estado

- Persistencia de generos verificada mediante pruebas aisladas.
- Publicacion y edicion visual verificadas previamente.
- No se ejecuto en este paso la suite completa de Django.

---

## Enlaces directos a canciones React - 06-11-2026

### Navegacion

- Se incorporaron enlaces directos utilizando el parametro track.
- La URL se actualiza cuando se abre el detalle de una cancion.
- El detalle puede abrirse directamente desde una URL compartida.
- Se sincronizo la navegacion con los botones Atras y Adelante.
- Se actualizo el cierre del detalle para mantener la URL coherente.
- Se conservaron los parametros existentes de la direccion.
- Se mantuvo el sistema de navegacion actual de React.

### Verificaciones

- Compilacion React/Vite aprobada.
- Cuatro pruebas automatizadas existentes de Webpay aprobadas.
- Apertura desde el catalogo verificada visualmente.
- Apertura del enlace en otra pestana verificada.
- Recarga conservando la cancion verificada.
- Navegacion Atras y Adelante verificada.
- Cierre del detalle mediante X verificado.
- Cierre despues de recargar verificado.

### Alcance

- Cambio realizado exclusivamente en App.tsx.
- No se modificaron rutas existentes de Django.
- No se modificaron canciones, usuarios ni pagos.
- No se realizaron cambios en PostgreSQL.
- Enlaces a perfiles publicos pendientes de desarrollo.
- Compartir enlaces fuera del entorno local requiere despliegue.

---

## Enlaces directos a perfiles publicos React - 06-11-2026

### Funcionalidades incorporadas

- Se incorporaron enlaces directos a perfiles mediante el parametro profile.
- Las direcciones utilizan el nombre de usuario publico.
- React resuelve el identificador interno y el rol del usuario.
- Se habilitaron enlaces compartibles para artistas y productores.
- Los perfiles pueden abrirse en nuevas pestanas y recargarse.
- Se sincronizo la navegacion con los botones Atras y Adelante.
- Se mantuvo el acceso a productores desde el detalle de canciones.
- Los perfiles no encontrados muestran Perfil no disponible.
- Se evito mostrar otra cuenta como alternativa ante perfiles inexistentes.

### Verificaciones realizadas

- Compilacion React y TypeScript aprobada.
- Cuatro pruebas automatizadas existentes de Webpay aprobadas.
- Prueba visual de enlace a productor aprobada.
- Prueba visual de enlace a artista aprobada.
- Prueba visual de perfil inexistente aprobada.
- Prueba visual de Atras y Adelante aprobada.
- Prueba visual de navegacion desde cancion a productor aprobada.
- Se comprobaron visualmente los controles privados de perfiles ajenos.

### Alcance y pendientes

- Archivos React modificados: App.tsx y TrackDetailModal.tsx.
- No se modifico Django ni PostgreSQL.
- No se alteraron canciones, cuentas, compras ni pagos.
- La validacion visual no sustituye una auditoria completa de seguridad.
- Pendiente publicar el commit en GitHub.

---

## Pruebas automatizadas de navegacion - 06-11-2026

### Implementacion

- Se creo frontend/client/src/navigation/urlState.ts.
- Se incorporaron funciones reutilizables para leer y construir URLs.
- Se centralizo la resolucion de perfiles publicos por username.
- Se incorporo la validacion de usuarios por ID y rol.
- App.tsx utiliza las funciones del modulo de navegacion.
- Se creo frontend/client/src/navigation/urlState.test.mjs.
- Se actualizo npm test para ejecutar ambas suites.
- No se instalaron dependencias nuevas.

### Pruebas automatizadas

- Once pruebas nuevas de navegacion.
- Cuatro pruebas existentes de Webpay.
- Total ejecutado: 15 pruebas.
- Pruebas aprobadas: 15.
- Pruebas fallidas: 0.
- Compilacion TypeScript y Vite aprobada.

### Verificaciones visuales

- Apertura de enlaces a canciones aprobada.
- Apertura de perfiles publicos aprobada.
- Navegacion combinada aprobada.
- Validacion de perfil inexistente aprobada.
- Navegacion habitual y reproductor aprobados.
- Total: cinco comprobaciones visuales aprobadas.

### Alcance

- No se modifico el backend Django.
- No se realizaron operaciones en PostgreSQL.
- No se alteraron canciones, usuarios, compras ni pagos.
- Las pruebas automatizadas cubren funciones de navegacion.
- Las comprobaciones visuales complementan las pruebas unitarias.
- No se incorporaron pruebas automatizadas de navegador completo.

---

## Totales oficiales del carrito - 06-11-2026

### Correccion implementada

- CartPage.tsx consulta los totales mediante DjangoApi.carrito().
- Django mantiene la responsabilidad del subtotal, IVA y total.
- React valida la coincidencia entre los productos locales y los del servidor.
- Los totales se verifican antes de permitir continuar hacia el pago.
- Si falla la consulta, se informa al usuario y se ofrece reintentar.
- El modo de demostracion conserva su calculo local.

### Verificaciones realizadas

- Compilacion TypeScript y Vite aprobada.
- Quince pruebas automatizadas existentes aprobadas.
- Verificacion visual del carrito con productos existentes aprobada.
- Subtotal, IVA y total coinciden con la respuesta de Django.
- No se realizaron pagos durante la comprobacion.

### Alcance

- Modificacion limitada a CartPage.tsx.
- No se modificaron Django ni las tablas de PostgreSQL.
- No se altero el procedimiento de confirmacion de Webpay.
- Las pruebas automatizadas existentes no cubren directamente
  la nueva integracion de totales del carrito.

---

## Enlaces individuales y menu principal - 06-11-2026

### Mejoras implementadas

- Se incorporaron enlaces directos a las secciones principales.
- El catalogo conserva enlaces a sus categorias de audio.
- Se actualizaron los manejadores del historial del navegador.
- Los enlaces soportan recarga, Atras y Adelante.
- Se conservaron los enlaces de canciones y perfiles publicos.
- Se mantuvieron las restricciones de las vistas privadas.
- Se retiro el buscador de la barra superior.
- La busqueda de canciones permanece disponible en el catalogo.
- Se corrigieron dos manejadores de clic en DiscoverPage.tsx.

### Verificacion tecnica

- Compilacion TypeScript y Vite aprobada.
- Pruebas automatizadas: 23 aprobadas, 0 fallidas.
- Ocho pruebas nuevas sobre enlaces y navegacion.

### Verificaciones visuales

- Enlaces de secciones principales aprobados.
- Enlaces de categorias de audio aprobados.
- Apartados de usuario comprobados.
- Buscador del catalogo comprobado.
- Historial Atras y Adelante comprobado.
- Enlaces a canciones y perfiles comprobados.
- Total: 6 verificaciones visuales aprobadas.

### Alcance y seguridad

- Sin cambios en Django ni PostgreSQL.
- Sin modificar canciones, compras ni pagos.
- Sin dependencias nuevas para las pruebas.
- No se realizaron operaciones en Webpay.

---

## Correccion de acentos del buscador - 06-11-2026

- Se corrigieron los textos accesibles y visibles del buscador del catalogo.
- Se restauraron correctamente los acentos de catalogo, cancion y genero.
- Se verifico visualmente que el buscador funciona correctamente.
- Compilacion aprobada y 23 pruebas automatizadas aprobadas.
- Sin cambios en Django, PostgreSQL, canciones o pagos.

---

## Acceso a biblioteca tras Webpay - 06-11-2026

### Mejora implementada

- Se incorpora un boton para acceder a compras y descargas
  desde el aviso de retorno exitoso de Webpay.
- El acceso se muestra a cuentas de artista tras intentar
  sincronizar sus datos con Django.
- La navegacion abre Mi perfil, donde se encuentra la
  biblioteca y las descargas.
- No se ofrece el boton en retornos fallidos o en revision.
- Django conserva el control de autorizacion de descargas.

### Comprobaciones

- Compilacion React y TypeScript aprobada.
- 23 pruebas automatizadas existentes aprobadas.
- Biblioteca de artista abierta correctamente.
- Compras existentes visibles sin realizar pagos.

### Limitaciones pendientes

- No se ha realizado una prueba integral del retorno real
  de Webpay y posterior descarga.
- La sincronizacion de datos no demuestra por si sola
  la aprobacion de una transaccion concreta.
- Las pruebas existentes no cubren directamente el nuevo
  comportamiento del aviso de retorno.

### Seguridad

- Sin modificaciones en Django ni PostgreSQL.
- Sin compras ni operaciones Webpay durante las pruebas.
- Cambios de interfaz limitados a App.tsx y AppContext.tsx.

---

## Implementacion D3 - Sesiones Django - 06-11-2026

### Implementacion
- Autenticacion mediante sesiones Django y proteccion CSRF.
- Django conserva la autoridad sobre identidad y permisos.
- React controla logout, expiracion y rutas privadas.
- Se incorpora recuperacion mediante nuevo inicio de sesion.
- Documentacion en docs/INTEGRACION_BACKEND.md.

### Validacion
- Compilacion TypeScript y React aprobada.
- 23 pruebas automatizadas React aprobadas.
- 5 pruebas Django aprobadas con base temporal.
- Login y logout comprobados.
- Rutas privadas comprobadas.
- Expiracion simulada y recuperacion comprobadas.

### Pendientes
- Verificar caducidad real por tiempo.
- Registrar el cierre formal de D3 en DDPB-66.

### Seguridad
- Sin cambios en datos reales de PostgreSQL.
- Sin pagos ni modificaciones a canciones o compras.

---

## Integracion SPA con API real y respaldo mock - 06-11-2026

- API real (`hybrid`) y modo `mock` seleccionables con `VITE_API_MODE`.
- Corregido tipo `DPagoInit` para coincidir con la respuesta Django.
- Actualizado comentario de configuracion antiguo en `app/api_shim.py`.
- Agregadas 7 pruebas de integracion aislada en `app/test_integration_real.py`.
- Pruebas: React 23/23, autenticacion Django 5/5, integracion Django 7/7.
- Validacion visual con API real y respaldo mock aprobadas (pasos 199 y 200).
- Documentacion ampliada en `docs/INTEGRACION_BACKEND.md`.
- Pagos Webpay reales y registro en base principal no ejecutados.
- Pendiente: validacion integral del pago en ambiente de integracion.
- Sin cambios en canciones, compras ni datos reales de PostgreSQL.

<!-- BEATCLOUD_CONSOLIDADO_2026_11_06_PASOS_196_210 -->

## 2026-11-06 - Consolidado de trabajo: API real/mock y unificacion de repositorios (pasos 196-210)

**Alcance:** avances realizados y resultados comunicados en esta conversacion hasta el intento de publicacion del paso 210. Esta seccion complementa el historial anterior sin sustituirlo. Las verificaciones descritas se basan en las salidas de PowerShell y en las comprobaciones visuales confirmadas; no debe confundirse una prueba simulada con un cobro real.

### Antecedentes utilizados

- Se partio de un BeatCloud con Django/PostgreSQL y SPA React/TypeScript/Vite; ya se habian integrado sesiones Django, proteccion CSRF, navegacion, carrito e inicio del flujo Webpay. La rama `main` del repositorio de origen estaba en `01e2bd1` antes de la etapa API real/mock.
- Se mantuvieron como antecedentes de desarrollo los commits `8d7f7f1` (totales/IVA del carrito desde Django), `daa41c6` (navegacion y busqueda), `fcb4c32` (ajuste visual), `e1ad46f` (retorno Webpay y acceso a compras/descargas) y `01e2bd1` (autenticacion Django/CSRF). Estas referencias no reemplazan sus registros historicos previos.

### Integracion de la SPA con Django real y modo mock (196-202)

- **196 - Diagnostico de conectividad:** el primer sondeo HTTP devolvio 0 porque los servidores no estaban iniciados. Se levantaron Django en `127.0.0.1:8000` y Vite en `localhost:3000` y se repitieron consultas de solo lectura. Se comprobaron `/api/catalogo/` (4 canciones en esa ejecucion), `/api/session/`, `/api/csrf/`, respuestas 401/405 de rutas protegidas y proxy de `/api/` por Vite. Se confirmo `VITE_API_MODE=hybrid` como modo normal y `mock` como respaldo; no era correcto usar `rest` como indicaba un comentario antiguo.
- **197 - Ajuste de contrato y documentacion:** `frontend/client/src/api/types.ts` dejo de exigir `session_id` en `DPagoInit`, porque la respuesta de inicio de pago Django no lo proporciona; `DWebpayTransaction` mantuvo su identificador interno. Se corrigio un comentario de `app/api_shim.py` y se amplio `docs/INTEGRACION_BACKEND.md`. Compilacion `tsc -b && vite build` aprobada; **23/23 pruebas React** y **5/5 pruebas de autenticacion Django** aprobadas. Sin commit en este paso.
- **198 - Integracion aislada de Django:** se creo `app/test_integration_real.py` con **7/7 pruebas aprobadas**: registro/activacion/login, catalogo y filtros, carrito/totales/eliminacion, rechazo de pago con carrito vacio, inicio de pago con Webpay simulado, descarga protegida y compra ficticia, y track gratuito con descarga. Se empleo una base de datos temporal de pruebas y respuestas simuladas de Webpay; no hubo cobros ni cambios en datos reales.
- **199 - QA visual API real:** se confirmaron desde la SPA el catalogo real, login, carrito existente sin modificaciones, biblioteca y descarga ya autorizada, logout y bloqueo de rutas privadas. No se realizaron compras ni registros reales durante esta verificacion visual.
- **200 - QA de modo mock:** el frontend se ejecuto en el puerto `3001` con `VITE_API_MODE=mock` y siguio funcionando con Django detenido. Se verificaron catalogo de demostracion, navegacion y ausencia de pagos reales.
- **201 - Documentacion y commit de origen:** se actualizaron `docs/INTEGRACION_BACKEND.md` y `REGISTRO_CAMBIOS_BEATSCLOUD.md`, y se guardaron los ajustes de codigo y el nuevo test. Commit local **`d8b4376`**, `test: validar API real y conservar modo mock en BeatCloud` (5 archivos). El primer intento fallo por ejecutarse desde `frontend/client/`; se corrigio ejecutandolo desde la raiz del proyecto.
- **202 - Publicacion del origen:** el commit **`d8b4376`** se publico y verifico en `felipe-urtubia/BeatsCloud`, rama `main`, avanzando desde `01e2bd1`. El recorrido completo de aprobacion y retorno real de Transbank quedo pendiente de validacion en ambiente de integracion.

### Unificacion para repositorio de entrega (203-210)

- **Objetivo:** cumplir la accion 5 de la Retrospectiva del Sprint 1 y unificar el codigo actual en `Fase 2/Evidencias Proyecto/Evidencias de sistema/client/` y `server/` de `yaeaelo/2026_2_MA_CAPSTONE_005D_GRUPO_4`, conservando los repositorios de origen como historial.
- **203 - Prevuelo:** se verifico como unica fuente actualizada `felipe-urtubia/BeatsCloud` en `d8b4376` y se clono por separado el repositorio del profesor, cuyo commit base era **`f96708d`**. El inventario inicial identifico `client/` antiguo (42 archivos), `server/` antiguo (101), `alpha/` duplicado (90), un `.env` versionado en el `client/` antiguo, y documentos en `Evidencias de documentacion`. No se modifico ningun remoto.
- **204 - Auditoria de duplicados y documentos:** `alpha/` contenia **90 archivos, ninguno exclusivo respecto de `server/`**; 15 archivos comunes diferian. Se identificaron **5 documentos de gestion** (acta de Sprint 1, indicadores de calidad, planilla de defectos, pruebas backend y respuesta API de tracks). Se constato que el `.env` antiguo estuvo en un commit, sin detectar variables con nombres sensibles y valores no vacios en esa revision limitada; esto **no demuestra** que el historial este libre de secretos.
- **205 - Migracion local:** en el clon de entrega se sustituyeron las versiones antiguas con **52 archivos del frontend** y **127 archivos del backend**, tomados del commit `d8b4376`; se retiro `alpha/` del arbol activo y el `.env` antiguo; se preservaron `.env.example` de ambos servicios. Se quito una contrasena fija de PostgreSQL de la copia de entrega, se actualizo el README y se conservaron los 5 documentos de gestion sin alterar. Ni el origen ni el remoto del profesor fueron modificados.
- **206/206B/206C - Auditoria y QA:** hubo dos falsos bloqueos iniciales del verificador por comparacion de finales de linea y por la ruta Unicode `documentacion`. Corregidos, se comprobaron los **179 archivos** contra los blobs Git, los **5 documentos** intactos, `npm ci`, compilacion TypeScript/Vite y **23/23 pruebas React**. `python manage.py check` no informo problemas. La primera ejecucion completa de Django registro **101/103 pruebas aprobadas y 2 fallas CSRF HTTP 403**, no un fallo general de login.
- **206D - Diagnostico CSRF:** el proyecto de origen tenia un `.env` local y 3 origenes de confianza, incluidos `http://localhost:3000` y `http://127.0.0.1:3000`; la copia limpia de `server/` no tenia `.env` y mostraba 0 origenes. Ambas pruebas fallidas enviaban `Origin: http://localhost:3000` con token CSRF. No se desactivo el middleware ni se copiaron secretos.
- **206E - Revalidacion Django:** se establecieron temporalmente los dos origenes locales mediante `DJANGO_CSRF_TRUSTED_ORIGINS` en la ejecucion de prueba, manteniendo token y cookie CSRF. Se aprobaron las **2/2 pruebas afectadas** y la suite completa **103/103 pruebas** (`python manage.py test app`, desde `server/`). La base `test_beatsbd` se creo y destruyo en las pruebas; no se modifico la base principal ni se invoco un pago real. **Fecha del QA: 2026-11-06**.
- **207 - Evidencia y documentacion:** se actualizo el README de entrega y se crearon `QA_UNIFICACION_2026-11-06.md` y `REGISTRO_EVIDENCIA.md` en `Fase 2/Evidencias Proyecto/Evidencias de documentacion/`; los cinco archivos originales de gestion se conservaron intactos. Se registro explicitamente la condicion de orígenes CSRF para las pruebas.
- **208/208A/208B/208C - Commit de unificacion:** el primer intento de staging detecto 54 archivos `client/` en vez de 52. Se confirmo que los dos adicionales eran `tsconfig.app.tsbuildinfo` y `tsconfig.node.tsbuildinfo`, caches generadas por TypeScript. Otro intento reconocio un `.gitignore` nuevo creado en la migracion. Tras corregir reglas `*.tsbuildinfo` y exclusion de `.env`, el commit local de unificacion quedo en **`064e3f7`** (`chore: unificar BeatCloud en client y server para entrega`). Incluye la retirada de **90 archivos de `alpha/`** del arbol activo, sin borrar su historial Git.
- **209 - Evidencia enlazada:** `REGISTRO_EVIDENCIA.md` recibio el enlace al primer commit de unificacion: `https://github.com/yaeaelo/2026_2_MA_CAPSTONE_005D_GRUPO_4/commit/064e3f7c6388e1a4a0c50a62432c268b12144804`. Se creo un segundo commit local **`8b77074`**, solo de registro de evidencia. El enlace requiere publicar los commits para que sea accesible en GitHub.
- **210 - Intento de publicacion:** se verificaron la rama `main`, ambos commits locales y que el remoto del profesor seguia en `f96708d`. `git push` fue rechazado con **HTTP 403**: `Permission to yaeaelo/2026_2_MA_CAPSTONE_005D_GRUPO_4.git denied to felipe-urtubia`. **Los commits `064e3f7` y `8b77074` NO quedaron publicados en el repositorio del profesor**. No se utilizo `force push` y el trabajo quedo disponible localmente en `BeatCloud_Entrega_Grupo4`.

### Resultados consolidados y asuntos pendientes

- **Origen actualizado:** `https://github.com/felipe-urtubia/BeatsCloud`, commit **`d8b4376` publicado** y verificado.
- **Destino de entrega:** `https://github.com/yaeaelo/2026_2_MA_CAPSTONE_005D_GRUPO_4`, base remota observada **`f96708d`**, unificacion **`064e3f7` local** y evidencia **`8b77074` local**. No confundir commits locales con publicados.
- **Pruebas finales verificadas (2026-11-06):** Django **103/103**, React **23/23**, `tsc -b && vite build` exitosa, `python manage.py check` sin incidencias. La suite Django solo aprobo por completo con los origenes CSRF locales declarados explicitamente durante las pruebas.
- **Seguridad:** `.env` eliminado del arbol activo de entrega y `.env.example` disponible en `client/` y `server/`; no se publico una contrasena fija en la copia nueva. El `.env` antiguo permanece en historial Git previo. La revision de secretos fue limitada; si existieron credenciales reales expuestas, deben rotarse, y eliminar el archivo actual no sanea el historial.
- **Pendientes:** obtener acceso de escritura al repositorio de `yaeaelo` (invitacion a `felipe-urtubia` o autenticacion autorizada de una cuenta con permiso), verificar nuevamente el remoto antes de publicar sin `force push`, comprobar en GitHub la presencia de `client/`, `server/` y documentos, mantener documentada la configuracion CSRF para pruebas locales, y realizar en otro momento la validacion real del retorno Webpay/Transbank en entorno de integracion.
- **Esta anotacion historica:** se incorpora al registro sin crear automaticamente commits ni publicar los cambios. Cualquier actualizacion adicional de este registro debe incorporarse deliberadamente a los repositorios correspondientes.

<!-- BEATCLOUD_D9_VALIDACIONES_CERRADAS -->
## D9 - Metadatos musicales: validaciones de subida y edicion (2026-11-08)

- **Estado tecnico:** implementado y probado en el repositorio principal. Publicacion GitHub pendiente de este commit.
- **Migraciones:** 0016_usuario_nombre_artistico, 0017_track_metadata y 0018_track_subgenre existentes y aplicadas. D9 utiliza 0017 para los metadatos; no se crea otra 0016.
- **Modelo y API:** Track incluye bpm, mood, resource_type y has_stems. GET /api/catalogo/ devolvio los cuatro campos para un catalogo local de 4 canciones.
- **Validaciones:** se agrego app/metadata_validation.py y se reforzaron TrackForm (app/forms.py) y track_update_api (app/api_shim.py). BPM entre 1 y 300; resource_type en instrumental/acapella/loop/drumkit; mood en los seis estados definidos por React; has_stems acepta solo valores booleanos reconocidos.
- **Compatibilidad:** upload_api y las vistas Django tradicionales ya usan TrackForm; la edicion PATCH/PUT ahora tambien valida metadatos antes de guardar. No se cambiaron valores existentes de PostgreSQL.
- **Pruebas nuevas:** app/test_d9_metadata.py, 8 de 8 aprobadas, incluida la verificacion de rechazos sin persistir valores invalidos.
- **Regresion:** python manage.py check sin problemas; python manage.py makemigrations --check --dry-run: No changes detected; python manage.py test app -v 1: 111 pruebas, resultado OK, 70.230 segundos, en base temporal de pruebas.
- **Alcance de esta entrega:** codigo y documentacion de validacion D9. No incluye filtros reales del lado del servidor ni despliegue externo, que son trabajo separado.

## Paso D8 — Cierre técnico de integración Cloudflare R2 (11-11-2026)

### Objetivo
Registrar los avances de la implementación del almacenamiento privado de archivos de audio mediante Cloudflare R2 en BeatCloud.

### Implementación backend
- Se incorporó la estructura backend para gestionar el almacenamiento privado de archivos en Cloudflare R2.
- Se desarrollaron las operaciones de presign, confirmación y finalización de cargas.
- Se incorporó el mecanismo de claims para controlar las operaciones de carga.
- Se agregaron validaciones de metadatos y del proceso de recepción de archivos.
- Se incorporó el proceso de promoción de archivos, preparación de staging y generación de previews.
- Se contempló la entrega privada de archivos de audio, incluyendo soporte para solicitudes HTTP Range.
- Se incorporó el control de visibilidad de tracks según su estado de disponibilidad.
- Se mantuvo la compatibilidad con el mecanismo anterior de cargas locales.

### Configuración y protección
- El bucket configurado es `beatcloud-media`, de carácter privado.
- La URL pública de desarrollo permanece deshabilitada.
- `R2_UPLOADS_ENABLED` permanece en `false`; no se habilitó la recepción de nuevas cargas mediante R2.
- Las migraciones `0023_track_r2_fields.py` y `0024_r2uploadclaim.py` están preparadas, pero no se han aplicado a la base de datos PostgreSQL principal.
- No se realizaron cambios de esquema en la base de datos principal durante este cierre.

### Validaciones registradas
- `python manage.py check`: ejecución correcta.
- Pruebas específicas de integración R2: 31 de 31 aprobadas.
- Suite de pruebas de la aplicación: 299 de 299 aprobadas.

### Pendientes para completar la integración
- Integrar el flujo de carga directa R2 en el frontend React: presign, PUT, confirmación y finalización.
- Mantener la transferencia de metadatos y portadas durante el registro de tracks.
- Revisar y validar la configuración CORS del bucket.
- Ejecutar una prueba integral de carga, reproducción y descarga privada.
- Comprobar la compatibilidad del flujo anterior de cargas locales.
- Preparar un procedimiento de respaldo y autorización antes de aplicar las migraciones a PostgreSQL.
- Mantener deshabilitada la activación de nuevas cargas R2 hasta completar las pruebas integrales.

### Versionamiento
- Se publicó el commit `97bd7ec` en la rama `main`.
- Descripción del commit: `feat(r2): integra almacenamiento privado de audio en Cloudflare R2`.
- Este registro documenta los avances backend y deja constancia de que la integración frontend y las pruebas de extremo a extremo siguen pendientes.

<!-- AMPLIACION_BEATSCLOUD_2026_11_12_15 -->

---

# Ampliación del registro — 12 al 15 de noviembre de 2026

> Esta sección se agrega al final del registro existente. No reemplaza ni modifica las anotaciones anteriores. Se documentan los cambios y verificaciones que quedaron respaldados en las conversaciones y salidas de comandos revisadas.

## 12-11-2026 — R2: conservación del nombre original del audio

- Se reforzó la validación de `original_filename` en `app/r2_presign.py`, rechazando caracteres de control y nombres no válidos.
- Se incorporó el uso del nombre original validado en `app/r2_private_delivery.py` para la reproducción y descarga de archivos almacenados en R2.
- La respuesta de entrega utiliza `Content-Disposition` seguro mediante `content_disposition_header`.
- Para tracks antiguos que no tienen `original_filename` válido, se conserva la compatibilidad utilizando el nombre derivado de la clave del objeto R2.
- Se ampliaron las pruebas de `app/test_r2_private_delivery.py` para comprobar el nombre original tanto en reproducción (`inline`) como en descarga (`attachment`), además de la compatibilidad con registros anteriores.
- Se incorporó el campo `Track.original_filename` mediante la migración `0025_track_original_filename`.

### Verificaciones registradas

```powershell
python manage.py test app.test_r2_private_delivery
python manage.py test app.test_r2_presign app.test_r2_registration_guard app.test_r2_registration_prepare app.test_r2_track_registration
python manage.py check
```

Resultados:
- `app.test_r2_private_delivery`: 13/13 pruebas aprobadas.
- Pruebas de presign, guard, preparación y registro R2: 44/44 aprobadas.
- `python manage.py check`: sin problemas.

## 12-11-2026 — R2: validación del flujo de carga y limpieza de rutas

- Se continuó la validación del flujo backend de R2, incluyendo recepción por bloques, comprobación del tamaño, validación real del audio mediante Mutagen y limpieza de archivos temporales.
- En el frontend, `UploadTrackModal.tsx` delega el proceso de publicación en la función `uploadTrack` de `AppContext.tsx`.
- En esta etapa, `has_stems` seguía funcionando como indicador de metadatos; todavía no existía un selector ni una carga independiente de archivos stems.
- Se creó un respaldo externo de los archivos de configuración y rutas antes de aplicar los ajustes:
  `BeatCloud_backup_20261112_194830`.

### Corrección de rutas Django y cierre de sesión

- Se consolidó el registro de las rutas R2: `r2_presign_upload`, `r2_confirm_upload` y `r2_finalize_upload`.
- Se retiraron las rutas R2 duplicadas de `app/urls.py`, manteniendo allí la ruta de finalización; las rutas de presign y confirmación quedan centralizadas en `api_shim`.
- Se estandarizaron los nombres de las rutas de presign y confirmación en `app/api_shim.py`.
- Se eliminó la ruta antigua `/logout/` y una ruta duplicada de cierre de sesión que apuntaba a `app_logout`.
- En `app/templates/base.html`, el cierre de sesión pasó de un enlace GET a un formulario POST con token CSRF.
- Se verificaron las rutas de logout de Django y React, las tres rutas R2, la ausencia de rutas duplicadas y la eliminación de `/logout/`.

### Verificaciones registradas

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 1
cd frontend\client
npm run test
npm run build
```

Resultados:
- Django: 299/299 pruebas aprobadas.
- Frontend: 23/23 pruebas aprobadas.
- `makemigrations --check --dry-run`: `No changes detected`.
- `python manage.py check`: sin problemas.
- Compilación TypeScript y build Vite: correctos; 1926 módulos transformados.

## 13-11-2026 — Conciliación segura de órdenes Webpay

- Se incorporó `app/webpay_reconciliation.py` para consultar el estado de órdenes pendientes mediante el servicio de estado de Transbank.
- El servicio de conciliación identifica la orden y contrasta la respuesta del proveedor con los datos locales antes de actualizar el estado financiero.
- La conciliación no entrega canciones ni activa membresías por sí misma. Una autorización que no tenga entrega confirmada debe permanecer pendiente de revisión, sin generar una segunda entrega.
- Se integró la conciliación de órdenes pendientes antiguas con las protecciones de inicio de pago de `app/webpay_checkout_guard.py`.
- Se reforzaron los controles del retorno Webpay en Django para comprobar la orden, el estado de autorización, el monto y el `session_id`.
- El procesamiento del carrito utiliza el pedido original guardado en `cart_snapshot`, no el contenido que el usuario tenga actualmente en el carrito.
- Se utilizaron bloqueos transaccionales (`transaction.atomic()` y `select_for_update()`) para evitar entregas concurrentes o duplicadas.
- Las órdenes archivadas para revisión manual permanecen fuera del flujo automático de entrega.

### Estado de las órdenes revisadas

- Orden local ID `54`: estado `PENDING`, con token Webpay, sin entrega registrada y sin archivo de revisión. Quedó pendiente de consulta/conciliación con Transbank; no se debe asumir que está cancelada ni entregada.
- Orden local ID `46`: estado `PENDING`, sin token guardado y archivada para revisión. Se conserva archivada y no debe procesarse automáticamente.
- La inspección de estas órdenes no constituye un cobro nuevo ni una confirmación de entrega.

> No se registra aquí un resultado de suite completa para esta modificación porque la salida revisada no aporta un conteo final verificable de pruebas.

## 14-11-2026 — Backend R2: almacenamiento de portadas

- Se agregó el campo `Track.r2_cover_key` para asociar una portada privada almacenada en Cloudflare R2.
- Se creó la migración `0026_track_r2_cover_key`, dependiente de `0025_track_original_filename`.
- Se desarrollaron las validaciones del token firmado de carga de portada, la preparación/promoción del objeto desde la ruta pendiente hacia la clave privada y los controles de propiedad de la clave.
- Se incorporó la entrega de portadas privadas mediante Django, sin exponer al frontend la clave interna ni la URL del bucket.
- Se preparó el flujo de actualización de portada para validar el token, promover la nueva portada y limpiar la anterior después de guardar correctamente el cambio.
- Se agregaron pruebas específicas para la validación del token, preparación, entrega y actualización de portadas R2.
- En el PASO 46 se verificó la compilación y se aprobaron 41/41 pruebas, incluyendo promoción y validación de portadas.
- El PASO 47 integró el flujo backend en cuatro archivos y obtuvo 56/56 pruebas aprobadas.
- El PASO 47.1 generó `PASO47_R2_WORKFLOW_SOURCE.txt` como extracción de fuentes de solo lectura; ese paso no modificó archivos.
- Al cierre de esta etapa, la integración del flujo de portadas en el frontend React todavía estaba pendiente.

## 15-11-2026 — Integración de portadas R2 en React

### Publicación de tracks

- Se conectó el flujo de portada opcional de `UploadTrackModal.tsx` con la API R2 de Django.
- El frontend solicita una URL firmada para `kind: 'cover'`, sube el archivo directamente a Cloudflare R2 y luego confirma la recepción mediante Django.
- Se validan las extensiones JPG, JPEG, PNG y WEBP, la correspondencia entre extensión y MIME, y un tamaño máximo de 10 MB.
- La publicación solo continúa si Django confirma que el objeto recibido corresponde al tipo, tamaño y MIME esperados.
- El token de carga de portada (`cover_upload_token`) se entrega al proceso de finalización del track junto con los metadatos.
- Se mantuvo el flujo de carga de audio separado del de portada: ambos utilizan presign, transferencia directa a R2 y confirmación en Django.

### Edición de tracks

- Se integró en `AppContext.tsx` la carga directa de una nueva portada R2 durante la edición de un track.
- La edición solicita presign, sube el archivo directamente a R2, confirma la carga y envía `cover_upload_token` a `DjangoApi.updateTrack`.
- En `app/api_shim.py` se incorporó la entrega de la portada mediante `GET /api/track/<track_id>/cover/`.
- El serializador `ser_track()` devuelve esa ruta en el campo `foto` cuando el track tiene `r2_cover_key`; no expone la clave privada de R2.
- La actualización valida el token y la propiedad de la clave. La portada anterior se limpia después de guardar la nueva; si falla el guardado, se intenta limpiar el objeto nuevo para evitar dejarlo abandonado.
- Se incorporaron los módulos `app/r2_cover_delivery.py` y `app/r2_cover_bridge.py`, además de pruebas para entrega, guard, preparación y actualización de portadas.
- El parche PASO 59.10 modificó `app/api_shim.py` y `frontend/client/src/context/AppContext.tsx`, y creó los módulos y pruebas nuevos correspondientes.
- La aplicación del parche no ejecutó migraciones ni modificó canciones u objetos R2 existentes.

### Vista previa de portada en el formulario

- Se agregó la vista previa de la imagen seleccionada en el formulario de publicación.
- Se corrigió la disposición del texto/etiqueta y la vista previa mediante el ajuste PASO 59.37, para que ambos elementos no se superpongan ni queden asociados visualmente de forma incorrecta.
- La selección de portada, la vista previa, el flujo de carga R2, la respuesta de Django y la visualización en el catálogo React se comprobaron manualmente en el navegador.
- Se verificó que el catálogo respondiera HTTP 200 con 10 resultados y que el campo `foto` apuntara al endpoint Django de portada R2.

### Ajuste visual del detalle de track y texto de compra

- En `frontend/client/src/components/TrackDetailModal.tsx` se eliminó únicamente la frase:
  `Django confirmará el pago antes de registrar la compra.`
- La modificación fue exclusivamente de texto visible. No se alteró la lógica de carrito, checkout, Webpay, confirmación ni registro de pagos.
- Antes del cambio se creó el respaldo:
  `TrackDetailModal.tsx.bak_remove_django_payment_20261115_195405`.
- Se utilizó el script temporal `PASO_ELIMINAR_TEXTO_DJANGO.py` para realizar una sustitución única y comprobar que la frase ya no apareciera. El script se eliminó después de ejecutarse.
- Se comprobó que el respaldo del componente permaneciera disponible y que la lógica de pagos no fuera modificada por este ajuste.

### Verificación de compilación

```powershell
cd frontend\client
npm run build
```

Resultado:
- `tsc -b` finalizó correctamente.
- Vite 6.4.5 transformó 1926 módulos.
- Build de producción completado correctamente en 2.68 segundos.
- No se documenta en este paso una ejecución adicional de la suite completa de pruebas frontend o backend.

## 15-11-2026 — Inventario de archivos temporales y respaldos

- Se realizó una inspección de solo lectura de los archivos locales candidatos a limpieza, distinguiendo respaldos, scripts/informes PASO y archivos temporales.
- Se consultó `git status --short --untracked-files=all` para identificar archivos modificados y no rastreados.
- El inventario detectó múltiples respaldos `.bak`, carpetas `backups`, archivos de diagnóstico y fuentes `PASO34` a `PASO59`, además de archivos de contexto R2 y `r2-cors.json`.
- Entre los archivos identificados se encuentran respaldos de `app/api_shim.py`, `app/models.py`, módulos R2, pruebas R2, `UploadTrackModal.tsx`, `TrackDetailModal.tsx` y `AppContext.tsx`.
- También se identificaron archivos de pruebas que forman parte de la cobertura automatizada y que no deben confundirse con scripts temporales.
- Durante la ejecución del bloque de inspección apareció un error de sintaxis al ejecutar un `else` separado del bloque PowerShell correspondiente. El error no ejecutó operaciones de borrado.
- Resultado explícito de la inspección: **no se eliminó ningún archivo**.

### Pendiente de limpieza

- Clasificar los respaldos y scripts PASO uno por uno antes de decidir su eliminación.
- Mantener los archivos de pruebas automatizadas (`test_*.py`) y los módulos fuente que forman parte de la implementación.
- No eliminar respaldos de archivos modificados hasta comprobar que el código actual está validado y que existe otro respaldo recuperable cuando corresponda.
- Revisar los archivos no rastreados y el estado de Git antes de preparar el siguiente commit.
- La limpieza del inventario queda pendiente; esta anotación no autoriza ni registra la eliminación de archivos.

---

**Fin de la ampliación del registro al 15-11-2026.**

<!-- AMPLIACION_COMPLEMENTARIA_R2_PASOS_2026_11_15 -->

---

# Ampliación complementaria — hitos R2 de los chats anteriores y anteanterior

> Esta ampliación complementa la sección anterior. Se incorpora al final del mismo registro y conserva íntegro todo el contenido previo. Los resultados de pruebas se anotan como ejecuciones separadas cuando corresponden a comandos o conjuntos distintos. Los datos reconstruidos desde mensajes de conversación se identifican como tales cuando no se conservó el log completo.

## 11–12-11-2026 — Primera integración de carga directa a Cloudflare R2

- Se aplicó la integración inicial mediante el script `BeatCloud_R2_Integracion_Desde_Descargas.ps1`.
- Se creó el respaldo previo:
  `backups/r2_integracion_20261112_010123`.
- Los archivos que quedaron registrados como modificados en esta primera integración fueron:
  - `app/models.py`
  - `app/metadata_validation.py`
  - `app/r2_upload_http.py`
  - `app/r2_upload_workflow.py`
  - `app/r2_track_registration.py`
  - `app/urls.py`
  - `frontend/client/src/context/AppContext.tsx`
  - `frontend/client/src/api/django.service.ts`
- La integración conectó la preparación de la carga, la emisión de URL firmada, la transferencia directa a R2, la confirmación del objeto y la finalización/registro del track.
- Se incorporaron validaciones de metadatos, autorización del productor, reserva de la carga y preparación del audio antes de su publicación.
- Se mantuvo la separación entre el objeto temporal pendiente y el objeto privado definitivo.
- En esta etapa se reportaron 26/26 pruebas R2 aprobadas y compilación del frontend correcta.
- Los puntos que seguían pendientes al terminar esa primera etapa eran la revisión de CORS y la prueba real de extremo a extremo. Esos puntos se verificaron posteriormente y se documentan más abajo.

## 12–13-11-2026 — Resultados intermedios de pruebas R2

Los siguientes resultados corresponden a ejecuciones independientes y no deben sumarse como si fueran una única suite:

| Fecha / etapa | Resultado | Alcance documentado |
|---|---:|---|
| Integración inicial | 26/26 | Pruebas R2 reportadas tras aplicar el primer script de integración |
| Regresión R2 posterior | 39/39 | Resultado comunicado durante la conversación; el comando completo no quedó disponible en los archivos recuperados |
| Entrega privada y nombre original | 13/13 | `app.test_r2_private_delivery` |
| Presign, guard, preparación y registro | 44/44 | `app.test_r2_presign`, `app.test_r2_registration_guard`, `app.test_r2_registration_prepare` y `app.test_r2_track_registration` |
| Verificación agrupada | 57/57 | 13/13 más 44/44, registrados como dos grupos de pruebas |
| Regresión de claims y rutas | 58/58 | Ejecución registrada en `Texto pegado(20261113-213241).txt` |
| Regresión R2 ampliada | 74/74 | Ejecución registrada en `Texto pegado(20261113-233736).txt` |

### Detalle de la regresión 58/58

- La salida conservada confirma que se ejecutaron pruebas de ciclo de vida y servicio de claims, además de las pruebas de rutas R2.
- Se verificaron, entre otros aspectos, que una reserva no se procese dos veces, que no se reinicie un procesamiento ya iniciado, que una clave de otro productor no pueda reutilizarse y que las rutas mantengan la protección CSRF.
- Resultado de la ejecución: `Ran 58 tests ... OK`.

### Detalle de la regresión 74/74

El comando conservado fue:

```powershell
python manage.py test `
    app.test_r2_presign `
    app.test_r2_upload_http `
    app.test_r2_upload_workflow `
    app.test_r2_track_registration `
    app.test_r2_registration_guard `
    app.test_r2_registration_prepare `
    app.test_r2_registration_cleanup `
    app.test_r2_route_wiring `
    --verbosity 2
```

- Resultado: 74 pruebas ejecutadas y aprobadas.
- La salida confirmó que se aplicaron las migraciones en la base de datos temporal de pruebas, incluyendo `0023_track_r2_fields`, `0024_r2uploadclaim`, `0025_track_original_filename` y `0026_track_r2_cover_key`.
- El sistema de comprobación de Django no identificó problemas.
- Esta ejecución de 74/74 es distinta del resultado 72/72 comunicado posteriormente en otra conversación; ambos se conservan como resultados independientes y no se sustituyen entre sí.

## 13-11-2026 — Prueba real de transferencia directa a R2

- Se verificó la configuración CORS del bucket para el origen de desarrollo `http://localhost:3000`.
- La configuración comprobada permitía el método `PUT`, el encabezado `Content-Type`, exponía `ETag` y tenía `MaxAgeSeconds` de 3600.
- Se ejecutó una prueba real de carga del archivo:
  `Mi_Nuevo_Beat_Rock_2026.wav`.
- Tamaño del archivo: 23.040.044 bytes.
- La transferencia directa desde el navegador a Cloudflare R2 respondió HTTP 200.
- R2 devolvió un `ETag`.
- Posteriormente, la confirmación enviada a Django respondió HTTP 200 con:
  - `verified: true`
  - `kind: track`
  - `content_type: audio/wav`
- Esta prueba confirmó que la transferencia directa y la verificación del objeto pendiente funcionaban desde el origen de desarrollo.
- La prueba automatizada del endpoint de finalización también contiene el caso `test_solicitud_valida_regresa_201`, que comprueba la respuesta HTTP 201 al registrar una solicitud válida. Este 201 corresponde a la prueba automatizada del endpoint; no se debe confundir con los HTTP 200 de la transferencia y confirmación reales.

### Prueba aislada posterior de preparación

- Se preparó una comprobación aislada para validar autorización, propietario, nombre original, tamaño, MIME, existencia del objeto pendiente, preparación de copia privada y generación de preview.
- El archivo de prueba fue `_prueba_aislada_r2.py`, eliminado al terminar el intento.
- La ejecución recuperada no terminó correctamente: el token leído desde el portapapeles llegó contaminado con texto adicional y Django lanzó `BadSignature`.
- Por tanto, esa ejecución no debe registrarse como una prueba aislada aprobada ni como una publicación completada.
- La prueba real anterior de PUT y confirmación sí quedó confirmada por separado.

## 13–14-11-2026 — Regresión y ampliación del pipeline de portadas

### PASO 46 y PASO 47

- El PASO 46 verificó la compilación y aprobó 41/41 pruebas relacionadas con promoción y validación de portadas.
- El PASO 47 aplicó cambios en:
  - `app/r2_upload_workflow.py`
  - `app/r2_upload_http.py`
  - `app/test_r2_upload_workflow.py`
  - `app/test_r2_upload_http.py`
- Se generaron respaldos `.paso47.bak` de esos cuatro archivos.
- Se ejecutó `py_compile` sobre los cuatro módulos y la compilación Python fue correcta.
- La batería seleccionada para el PASO 47 ejecutó 56/56 pruebas aprobadas. Incluyó registro de tracks, flujo de subida, endpoint HTTP, preparación/validación de portadas y promoción.
- En esa etapa se dejó constancia de que no se modificaron modelos, migraciones, URLs ni el flujo de audio.
- El archivo `PASO47_R2_WORKFLOW_SOURCE.txt` se generó posteriormente como extracción de fuentes para inspección; no fue un parche de código.

### PASO 49 — Extracción de fuentes de rutas y portadas

- Se generó el archivo `PASO49_R2_ROUTE_COVER_SOURCE.txt`.
- El archivo contiene una extracción de lectura de:
  - `frontend/client/src/api/mappers.ts`
  - `frontend/client/src/api/types.ts`
  - `app/urls.py`
  - `beatcloud/urls.py`
  - respaldos de rutas anteriores a la limpieza y de la primera integración R2
  - referencias al campo y flujo backend de portadas R2
- La extracción permitió comparar el mapeo de datos React, las rutas Django actuales, las rutas respaldadas y el cableado de portadas.
- El PASO 49 fue una inspección/documentación de fuentes, no una modificación funcional del proyecto. No se registra como cambio de código ni como migración.

### PASO 53 y PASO 54 — Diagnóstico de brechas y fuentes

- Se generaron `PASO53_R2_COVER_PIPELINE_GAPS.txt` y `PASO54_R2_COVER_MISSING_SOURCE.txt` como archivos de inspección de brechas y extracción de fuentes.
- Los documentos reunieron referencias a la entrega privada de audio, las rutas protegidas, el guard de autorización, el pipeline de preparación y las pruebas de portadas.
- Estos archivos son artefactos de diagnóstico; no se deben contabilizar como módulos funcionales añadidos al proyecto.

## 14-11-2026 — Integración frontend inicial de portadas R2 (PASO 55)

- Se modificaron dos archivos:
  - `frontend/client/src/api/django.service.ts`
  - `frontend/client/src/context/AppContext.tsx`
- Se creó el respaldo:
  `backups/PASO55_R2_COVER_20261114_211501`.
- Se incorporó el tipo `cover` al flujo de presign y confirmación.
- El frontend solicita una URL firmada para la portada, realiza el `PUT` directamente a R2 y confirma el objeto con Django.
- La confirmación verifica que el objeto sea de tipo `cover`, que el tamaño coincida y que el MIME sea el esperado.
- El token de portada se incorpora al registro mediante `cover_upload_token`.
- El PASO 55 no modificó el backend ni ejecutó migraciones.

## 14–15-11-2026 — PASO 59: diagnóstico y verificación del flujo de portadas

### PASO 59 — Diagnóstico de portadas R2

- Se generó `PASO59_DIAGNOSTICO_PORTADAS_R2.txt` como extracción de contexto y fuentes del backend y frontend.
- El diagnóstico incluyó, entre otros, los módulos de entrega privada de audio, endpoints de reproducción/descarga, serialización, contexto React y formulario de publicación.
- La generación del diagnóstico fue de solo lectura: no modificó código, migraciones, pruebas ni objetos de Cloudflare R2.
- Se generó también `PASO59_1_CONTEXTO_COMPLETO_R2.txt` como recopilación de contexto para continuar el trabajo. Ese paso tampoco modificó el proyecto ni ejecutó migraciones o pruebas.

### PASO 59.10 — Conexión de actualización de portadas

- Se aplicó el parche `PASO59_10_APLICAR_PATCH_PORTADAS.py`.
- Se modificaron `app/api_shim.py` y `frontend/client/src/context/AppContext.tsx`.
- Se incorporaron `app/r2_cover_delivery.py` y `app/r2_cover_bridge.py`, junto con sus pruebas correspondientes.
- La actualización valida el token firmado, el tipo de archivo, el tamaño, el MIME y la propiedad de la clave R2.
- La portada nueva se guarda antes de limpiar la anterior; si falla el guardado, se intenta limpiar el objeto nuevo para no dejar una carga huérfana.
- El parche no ejecutó migraciones ni modificó canciones u objetos R2 existentes.

### PASO 59.35 — Comprobación de vista previa

- Se creó y ejecutó el script temporal `PASO59_35_PATCH_PREVIEW_PORTADA.py`.
- El script detectó que `coverPreviewUrl` ya existía y terminó indicando: `La vista previa ya existe. No se realizaron cambios.`
- Por ello, el PASO 59.35 no debe anotarse como una modificación efectiva de `UploadTrackModal.tsx`.
- A continuación se ejecutó `npm run build`, que finalizó correctamente: TypeScript y Vite completaron la compilación de producción.

### PASO 59.37 — Corrección de la estructura del selector de portada

- Se corrigió el cierre y la separación del `label` del selector de archivo respecto del bloque de vista previa en `frontend/client/src/components/UploadTrackModal.tsx`.
- Se creó un respaldo con sufijo `.bak_paso59_37_20261115_194245`.
- Se mantuvo intacta la lógica de carga R2 y publicación.
- Se volvió a ejecutar `npm run build`; TypeScript y Vite finalizaron correctamente y se transformaron 1926 módulos.

## 15-11-2026 — Resultados adicionales de pruebas y verificación manual de portadas

### Resultados comunicados en la conversación

- Se reportó una regresión R2 de 72/72 pruebas aprobadas, junto con una comprobación seleccionada de 3/3.
- El comando completo y el listado de casos de esa ejecución no quedaron preservados en el log recuperado; por ello se registra como resultado comunicado en conversación.
- En otra ejecución se reportaron 218/218 pruebas de la batería R2 aprobadas en 42,637 segundos.
- También se reportó la suite completa de Django con 350/350 pruebas aprobadas en 97,769 segundos.
- `python manage.py makemigrations --check --dry-run` devolvió `No changes detected`.
- Estos resultados son ejecuciones distintas de las regresiones 58/58 y 74/74 documentadas anteriormente.

### Publicación y comprobación de portadas reales

- Se utilizó el productor temporal `r2_test_productor` para validar la publicación de tracks con almacenamiento R2.
- El productor tenía `user_id=25`, perfil de productor con ID 20 y cuenta activa.
- Se publicaron y verificaron dos tracks de prueba:
  - Track ID 12: `PRUEBA PORTADA R2`.
  - Track ID 13: `campo`.
- Ambos tracks quedaron con `media_status=ready`, audio en R2 y clave de portada privada asociada al propietario.
- Se comprobó que los objetos de portada existían en el bucket privado `beatcloud-media` y que sus metadatos indicaban `image/jpeg`.
- Se verificó el endpoint `GET /api/track/12/cover/`:
  - HTTP 200.
  - `Content-Type: image/jpeg`.
  - `Cache-Control: private, no-store`.
  - `Content-Disposition: inline`.
  - `X-Content-Type-Options: nosniff`.
  - 8.571 bytes recibidos y firma JPEG válida.
- La misma ruta fue probada a través del proxy Vite:
  `http://127.0.0.1:3000/api/track/12/cover/`.
  Respondió HTTP 200, `image/jpeg`, 8.571 bytes.
- Se verificó que `GET /api/catalogo/` incluyera el track 12 y devolviera `foto: /api/track/12/cover/`.
- Para el track 13, el endpoint de portada respondió HTTP 200, `image/jpeg` y 53.545 bytes.
- La portada del track 13 se abrió directamente en el navegador y se visualizó correctamente.
- Esta verificación confirmó la cadena de entrega: objeto privado en R2, endpoint Django, proxy de Vite, serializador del catálogo y visualización en navegador.

## Aclaraciones para mantener la trazabilidad de las pruebas

- Los resultados 26/26, 39/39, 57/57, 58/58, 72/72, 74/74, 218/218 y 350/350 corresponden a ejecuciones o grupos de pruebas diferentes; no se suman entre sí.
- El resultado 57/57 corresponde a los grupos 13/13 y 44/44 documentados en el apartado de entrega privada y validación de registro.
- El resultado 74/74 cuenta con un comando y una salida completos conservados.
- El resultado 72/72 se conserva como dato comunicado en conversación porque no se recuperó su log íntegro; no reemplaza el resultado 74/74.
- La prueba real de PUT y confirmación R2 respondió HTTP 200. El HTTP 201 mencionado en el test automatizado corresponde a la respuesta esperada del endpoint de finalización, no a la transferencia PUT.
- Los diagnósticos y extracciones de fuentes PASO 47.1, PASO 49, PASO 53, PASO 54, PASO 59 y PASO 59.1 son documentación/inspección; no deben contabilizarse como cambios funcionales por sí solos.

---

**Fin de la ampliación complementaria de hitos R2 al 15-11-2026.**

------------------------------------------------------------------------

# 15-11-2026 --- Decisión y procedimiento de limpieza de archivos auxiliares

## Objetivo

Se decidió mantener `REGISTRO_CAMBIOS_BEATSCLOUD.md` como el registro
histórico único de los cambios de BeatsCloud. Los pasos ya ejecutados
deben permanecer documentados en este archivo, pero no es necesario
conservar indefinidamente todos los scripts, diagnósticos, extracciones
de fuentes y archivos temporales que se utilizaron para aplicarlos o
verificarlos.

La limpieza física de esos auxiliares se realizará después de
identificar cada archivo y comprobar que no forma parte de la
aplicación, de las pruebas automatizadas ni de una configuración
necesaria.

## Criterios para clasificar los archivos

### Candidatos a eliminación, previa comprobación

-   Scripts puntuales `PASO*.py` que ya se ejecutaron y cuya función
    quedó completada.
-   Scripts PowerShell `PASO*.ps1` de aplicación única, siempre que no
    sean herramientas reutilizables del proyecto.
-   Extracciones de fuentes y diagnósticos `PASO*.txt` que solo
    sirvieron para inspección y cuyo contenido relevante ya quedó
    documentado.
-   Archivos temporales de prueba y salidas intermedias que no sean
    entradas de otras pruebas o procesos.
-   Copias de trabajo duplicadas que puedan recuperarse desde Git o
    desde un respaldo verificado.

### Archivos que deben conservarse

-   Código funcional de Django y React, incluidos los módulos
    `app/r2_*.py` que participan en la integración R2.
-   Pruebas automatizadas, incluidos `app/test_*.py` y los módulos de
    pruebas R2.
-   Migraciones de Django.
-   Configuración y dependencias necesarias para ejecutar el proyecto.
-   `README.md`, `.env.example` y este registro histórico.
-   Configuraciones de R2, como `r2-cors.json`, hasta comprobar que su
    contenido está aplicado, respaldado o ya no es necesario.
-   Archivos que estén siendo utilizados por otros scripts, pruebas o
    procesos del proyecto.

### Respaldos `.bak` y carpetas `backups`

No se eliminarán de forma masiva. Cada respaldo se revisará junto con el
archivo actual y el estado de Git. Se conservará al menos una vía de
recuperación verificable para los cambios recientes hasta confirmar que
el código está estable y respaldado.

## Procedimiento acordado

1.  Obtener un inventario actualizado con rutas completas y estado de
    Git (`git status --short --untracked-files=all`).
2.  Clasificar los archivos como código funcional, pruebas, migraciones,
    configuración, respaldo o auxiliar temporal.
3.  Comprobar si cada candidato está rastreado por Git, si contiene
    cambios únicos y si otro archivo depende de él.
4.  Preparar una lista explícita de archivos que pueden eliminarse; no
    utilizar patrones generales de borrado sobre todos los archivos
    `PASO*` o `.bak`.
5.  Eliminar únicamente los auxiliares aprobados y ya documentados.
6.  Ejecutar las verificaciones correspondientes: pruebas Django,
    `python manage.py check`, comprobación de migraciones y compilación
    del frontend.
7.  Revisar nuevamente `git status` y `git diff` para confirmar que no
    se hayan eliminado código, pruebas, migraciones ni configuraciones
    necesarias.

## Estado de la limpieza al 15-11-2026

-   La decisión de consolidar la documentación en un solo registro quedó
    establecida.
-   La inspección previa identificó scripts PASO, diagnósticos,
    respaldos y archivos temporales como candidatos para revisión.
-   No se ha realizado una eliminación general de esos archivos.
-   El script `PASO_ELIMINAR_TEXTO_DJANGO.py` sí fue eliminado
    expresamente después de ejecutarse.
-   `PASO59_35_PATCH_PREVIEW_PORTADA.py` se ejecutó, detectó que la
    vista previa ya existía y no modificó el componente. Su eliminación
    física no quedó confirmada en la salida conservada.
-   `PASO59_37_CORREGIR_LABEL_PORTADA.py` se ejecutó y corrigió la
    estructura del selector. Su eliminación física tampoco quedó
    confirmada en la salida conservada.
-   La existencia actual de esos dos scripts y la de los demás
    auxiliares deberá comprobarse mediante un inventario nuevo antes de
    preparar el comando de limpieza.
-   No se registra en esta etapa la eliminación de módulos funcionales,
    pruebas automatizadas, migraciones, canciones de prueba, registros
    de PostgreSQL ni objetos de Cloudflare R2.

**Regla de trazabilidad:** los pasos completados se conservan en este
registro como historial; borrar un script auxiliar no significa borrar
su documentación ni revertir el cambio funcional que aplicó.

## 15-11-2026 — Limpieza de archivos auxiliares PASO

- Se realizó una simulación previa con PowerShell mediante -WhatIf.
- Se identificaron 33 archivos auxiliares correspondientes a extracciones de código, diagnósticos y scripts de aplicación puntual.
- Se registra su eliminación porque los avances funcionales y las verificaciones correspondientes están documentados en este registro.
- No se eliminaron módulos fuente, migraciones, pruebas automatizadas ni configuraciones funcionales.

### Archivos retirados

- `PASO34_R2_CONTEXT.txt`
- `PASO35_R2_MISSING.txt`
- `PASO36_R2_PIPELINE.txt`
- `PASO37_R2_COVER_CONTEXT.txt`
- `PASO38_R2_COVER_IMPLEMENTATION_CONTEXT.txt`
- `PASO39_R2_COVER_NEXT.txt`
- `PASO40_R2_COVER_ROUTES_CLAIMS.txt`
- `PASO41_R2_COVER_FLOW_SOURCE.txt`
- `PASO42_R2_COVER_MODEL_CONFIG.txt`
- `PASO47_R2_WORKFLOW_SOURCE.txt`
- `PASO48_FRONTEND_SOURCE.txt`
- `PASO49_R2_ROUTE_COVER_SOURCE.txt`
- `PASO50_R2_COVER_FLOW_SOURCE.txt`
- `PASO51_R2_COVER_DELIVERY_SOURCE.txt`
- `PASO52_R2_COVER_FULL_SOURCE.txt`
- `PASO53_R2_COVER_PIPELINE_GAPS.txt`
- `PASO54_R2_COVER_MISSING_SOURCE.txt`
- `PASO55_COVER_CURRENT_SOURCE.txt`
- `PASO56_COVER_DELIVERY_AUDIT.txt`
- `PASO57_CODIGO_PORTADAS_R2.txt`
- `PASO58_PORTADAS_COMPLETO.txt`
- `PASO59_1_CONTEXTO_COMPLETO_R2.txt`
- `PASO59_2_ARCHIVOS_R2.txt`
- `PASO59_3_BACKEND_PORTADAS.txt`
- `PASO59_4_FRONTEND_COMPLETO.txt`
- `PASO59_6_FUENTES_PORTADAS.txt`
- `PASO59_7_FUENTES_COMPLEMENTARIAS.txt`
- `PASO59_8_DEPENDENCIAS_PORTADAS.txt`
- `PASO59_9_ULTIMAS_FUENTES_PORTADAS.txt`
- `PASO59_DIAGNOSTICO_PORTADAS_R2.txt`
- `PASO59_10_APLICAR_PATCH_PORTADAS.py`
- `PASO59_35_PATCH_PREVIEW_PORTADA.py`
- `PASO59_37_CORREGIR_LABEL_PORTADA.py`

- Resultado de limpieza: eliminacion efectiva de los 33 archivos confirmada.
- Verificacion posterior: ninguno de los archivos de esta lista permanece en la raiz del proyecto.
- Los cambios funcionales permanecen en sus archivos fuente.
- No se modificaron objetos de Cloudflare R2 ni registros de canciones.

## 16-11-2026 — AUDITORIA DE LIMPIEZA PASO 47 Y PASO 59.10.1

- PASO 47: integracion de portadas R2 en workflow, endpoint HTTP y pruebas.
- Se incorporo preparacion y registro de portada, validacion y limpieza compensatoria ante fallos.
- Se mantuvo compatibilidad con el campo tradicional foto.
- PASO 59.10.1: correccion del boundary multipart en app/test_r2_cover_update.py.
- Ambos scripts cumplieron su funcion y ya no son necesarios para ejecutar la aplicacion.
- Se conservaron los respaldos originales generados por ambos procedimientos.
- No se modificaron modelos, migraciones, pagos, canciones ni objetos de R2 durante esta limpieza.
- Se mantienen pendientes de revision los respaldos historicos y r2_integracion_contexto.txt.

## 16-11-2026 — ARCHIVO HISTORICO DE CONTEXTO R2

- Se verifico que r2_integracion_contexto.txt no estaba rastreado por Git.
- Se traslado el archivo a backups/historico_contexto.
- Se verifico la integridad de la copia mediante SHA256.
- El archivo se conserva como referencia historica, fuera de la raiz.
- REGISTRO_CAMBIOS_BEATSCLOUD.md permanece como registro de hitos y modificaciones.
- No se modificaron modulos funcionales, pruebas, migraciones ni objetos R2.


## 16-11-2026 — Retiro de 12 respaldos duplicados de Git HEAD

- Se verifico individualmente cada respaldo contra su archivo original rastreado en Git.
- Los 12 respaldos coinciden byte por byte con la version HEAD.
- Se autoriza retirar las copias fisicas redundantes.
- Los archivos fuente y pruebas actuales permanecen intactos.
- Las versiones anteriores siguen siendo recuperables mediante Git.
- No se modificaron migraciones, modelos, compras, ventas ni objetos R2.

### Archivos retirados
- `app/models.py.bak_original_filename_20261112_214307`
- `app/r2_private_delivery.py.bak_original_filename_delivery_20261112_225419`
- `app/r2_promotion.py.paso43.bak`
- `app/r2_registration_guard.py.bak_original_filename_20261112_221507`
- `app/r2_registration_prepare.py.bak_original_filename_20261112_221507`
- `app/test_r2_private_delivery.py.bak_original_filename_delivery_20261112_225419`
- `app/test_r2_promotion.py.paso43.bak`
- `app/test_r2_registration_guard.py.bak_original_filename_20261112_221507`
- `app/test_r2_registration_prepare.py.bak_original_filename_20261112_221507`
- `app/test_r2_upload_http.py.paso47.bak`
- `app/test_webpay_regresion.py.bak_20261112_192728`
- `app/views.py.bak_20261112_192728`


- Resultado: eliminacion efectiva de los 12 respaldos confirmada.
- Verificacion posterior: ninguno permanece en su ubicacion original.
- Los 12 archivos fuente y sus versiones actuales permanecen intactos.

## 16-11-2026 — Archivo historico de 23 respaldos

- Se trasladaron 23 respaldos historicos de pruebas.
- Se conservaron las rutas relativas originales.
- Se verifico SHA-256 antes y despues del traslado.
- Se genero manifest_sha256.csv.
- No se modificaron archivos funcionales.
- No se eliminaron pruebas actuales.
- Los respaldos permanecen disponibles para recuperacion.

Ubicacion: backups\historico_pruebas\20261116
Manifiesto: backups\historico_pruebas\20261116\manifest_sha256.csv

## 16-11-2026 - Eliminacion de respaldos y temporales

- Se verificaron los 23 respaldos mediante SHA256.
- Se elimino el archivo historico y su manifiesto.
- Se eliminaron los temporales identificados.
- Se conservaron las pruebas activas y los archivos funcionales.
- No se modificaron modelos, migraciones ni registros comerciales.


---

# 16-11-2026 — Protección financiera, propiedad de R2 e integración de STEMS

## Protección del historial financiero durante la eliminación de cuentas

Se aplicó el parche `beatcloud_parche_cierre_webpay.py` para reforzar el
proceso de eliminación de cuentas y evitar que la eliminación de un usuario
comprometa operaciones financieras que deben permanecer como respaldo
histórico.

### Cambios incorporados

- Se reforzó la conservación de registros y transacciones financieras ya
  finalizadas.
- Se agregaron controles para impedir que la eliminación continúe cuando
  existan operaciones pendientes o pagos que todavía no hayan completado su
  entrega o cierre seguro.
- Se reforzó la validación tanto en las vistas como en la capa API para evitar
  que se pueda omitir la protección utilizando una ruta alternativa.
- Se añadieron pruebas específicas para la protección de los datos
  financieros durante la eliminación de cuentas.

### Archivos relacionados

```text
beatcloud_parche_cierre_webpay.py
app/views.py
app/api_shim.py
app/models.py
app/test_account_deletion_financial.py
```

El parche indicó expresamente que no modificaba la base de datos, las
migraciones ni la integración R2.

### Verificaciones realizadas

```powershell
python manage.py check
python manage.py test app.test_account_deletion_financial app.tests.EliminarCuentaTests
python manage.py test app
```

Resultados registrados:

```text
System check identified no issues (0 silenced).
15 tests: OK
355 tests: OK
```

### Observaciones de formato pendientes en esa revisión

Se ejecutó `git diff --check`. La comprobación detectó tres detalles de
formato que quedaron pendientes de corrección:

- Línea en blanco adicional al final de `app/test_r2_presign.py`.
- Línea en blanco adicional al final de `app/test_r2_track_registration.py`.
- Espacio en blanco al final de una línea de
  `frontend/client/src/components/TrackDetailModal.tsx`.

También aparecieron advertencias de conversión de finales de línea LF/CRLF
en varios archivos de trabajo. Estos avisos no impidieron las pruebas, pero
la revisión de formato no quedó completamente limpia.

---

## Migración de propiedad de archivos privados R2

Se incorporó el campo `r2_owner_user_id` al modelo `Track` para conservar la
identidad del usuario propietario de los objetos privados almacenados en
Cloudflare R2.

La migración aplicada fue:

```text
app/migrations/0027_track_r2_owner_user_id.py
```

La migración incluye la incorporación del campo y el proceso de backfill de
propietarios a partir de las claves R2 existentes, según la estructura de
almacenamiento.

### Aplicación y verificación

Se ejecutó:

```powershell
python manage.py migrate
python manage.py showmigrations app
```

Resultado:

```text
Applying app.0027_track_r2_owner_user_id... OK
```

Las migraciones de `app`, desde `0001_initial` hasta
`0027_track_r2_owner_user_id`, quedaron marcadas como aplicadas `[X]`.

---

## Integración de archivos STEMS con almacenamiento privado R2

Se completó la integración para asociar archivos STEMS a los tracks y
almacenarlos de forma privada en Cloudflare R2.

### Funcionalidad incorporada

- Se agregó el campo `r2_stems_key` al modelo `Track` para asociar el archivo
  STEMS almacenado en R2.
- Se incorporó el flujo de subida mediante URLs prefirmadas, confirmación y
  finalización del registro.
- Se admiten archivos ZIP, WAV y FLAC, con un límite configurado de hasta
  2 GB.
- Se validan la propiedad del track, el token de subida, el tipo MIME y el
  tamaño del archivo antes de aceptar el registro.
- Los STEMS se entregan mediante una ruta autenticada y protegida de Django,
  sin exponer directamente la ubicación privada del objeto R2.
- La interfaz permite incorporar STEMS durante la subida del track y
  consultar/descargar el archivo desde el detalle del track cuando el usuario
  tiene autorización.

### Ruta de descarga

```text
GET /api/track/<id>/stems/
```

### Archivos backend relacionados

```text
app/r2_stems.py
app/r2_registration_guard.py
app/r2_track_registration.py
app/r2_upload_http.py
app/r2_upload_workflow.py
app/test_r2_stems.py
app/urls.py
app/models.py
app/migrations/0027_track_r2_owner_user_id.py
```

### Archivos frontend relacionados

```text
frontend/client/src/api/django.service.ts
frontend/client/src/components/TrackDetailModal.tsx
frontend/client/src/components/UploadTrackModal.tsx
frontend/client/src/context/AppContext.tsx
```

---

## Pruebas de permisos y descarga de STEMS

Se verificaron los permisos desde distintos estados de sesión y acceso:

| Escenario | Respuesta | Resultado |
|---|---:|---|
| Propietario del track | HTTP 200 | Acceso permitido |
| Usuario sin sesión | HTTP 401 | Acceso rechazado |
| Usuario autenticado sin derecho de acceso | HTTP 403 | Acceso rechazado |
| Usuario que reclamó correctamente el track gratuito | HTTP 200 | Acceso permitido |

Los códigos HTTP 401 y 403 correspondieron a los controles de autorización
esperados; no representaron una falla del almacenamiento R2.

### Prueba real de subida y publicación

Se ejecutaron las solicitudes de subida para audio y STEMS:

```text
POST /api/r2/presign/   -> HTTP 200
POST /api/r2/confirm/   -> HTTP 200
POST /api/r2/finalize/  -> HTTP 201
```

La pista quedó publicada y asociada a sus recursos privados.

### Prueba de descarga de la pista ID 14

Se utilizó la acción de reclamación gratuita:

```text
POST /api/track/14/claim-free/ -> HTTP 200
```

Después de la reclamación se comprobaron las descargas:

```text
GET /api/track/14/descargar/ -> HTTP 200
GET /api/track/14/stems/     -> HTTP 200
```

El registro del servidor indicó:

```text
Descarga de audio: 2.116.844 bytes
Descarga de STEMS:   100.365 bytes
```

Se descargó el ZIP de STEMS y se verificó que contenía los archivos:

```text
Kick.wav
Bass.wav
Synth.wav
Percussion.wav
```

La prueba confirmó que el propietario puede subir y descargar los STEMS y
que un usuario con derecho de compra o reclamación gratuita puede acceder a
ellos. Los usuarios anónimos y las cuentas autenticadas sin autorización
siguen bloqueados por el backend.

### Comprobación de sesión y catálogo durante la prueba manual

En los registros del servidor del 16-11-2026 se observaron también las
siguientes respuestas:

```text
POST /api/track/14/claim-free/ -> HTTP 200
GET /api/session/              -> HTTP 200
GET /api/catalogo/?page=1      -> HTTP 200
```

Estas respuestas confirmaron que, después de la reclamación gratuita, la
sesión y la carga de la primera página del catálogo respondieron correctamente.

---

## Verificación general del proyecto al cierre de las pruebas STEMS

Se registraron las siguientes comprobaciones:

- `python manage.py check`: sin problemas del sistema Django.
- `python manage.py test app`: 360 pruebas ejecutadas, todas aprobadas.
- `npm run build`: compilación del frontend React/Vite completada
  correctamente.
- `python manage.py migrate`: migración `0027` aplicada correctamente.
- `python manage.py showmigrations app`: migraciones `0001` a `0027`
  aplicadas.
- Servidor Django iniciado con Django 6.0.6 sin errores de comprobación.
- Endpoints de sesión, catálogo, usuarios y suscripciones respondieron
  correctamente durante la prueba manual.

**Estado al 16-11-2026:** la integración de STEMS con R2, la descarga
protegida y la validación de permisos quedaron implementadas y probadas.
Las tareas de limpieza de auxiliares y respaldos se documentan en las
entradas anteriores de este registro. Durante las pruebas descritas en esta
sección no se eliminaron cuentas, canciones de prueba ni objetos de R2.

---

**Fin de la actualización del 16-11-2026: protección financiera, propiedad
de archivos R2 e integración y pruebas de STEMS.**


---

## Cierre de estabilización R2 y Webpay - 17-11-2026

### 1. Validación de portadas R2

Se ejecutaron las pruebas específicas de almacenamiento y entrega de portadas:

- 117 pruebas ejecutadas.
- 117 pruebas aprobadas.
- Sin errores.
- Migraciones verificadas sin cambios pendientes.

### 2. Validación funcional manual

Se comprobó el funcionamiento desde el servidor local:

- Acceso correcto al servidor Django.
- Visualización correcta de la portada de una canción.
- Persistencia de la imagen después de recargar la página.
- Actualización correcta de la portada al reemplazarla.

### 3. Validación integral del proyecto

Se ejecutó:

`python manage.py test`

Resultado:
- 360 pruebas ejecutadas.
- 360 pruebas aprobadas.
- Sin errores.
- Tiempo aproximado: 206 segundos.

También se verificó:

- `python manage.py check`: correcto.
- `makemigrations --check --dry-run`: sin cambios.
- Migraciones 0001 a 0027 aplicadas.
- `migrate --plan`: sin operaciones pendientes.
- `git diff --check`: correcto.

### 4. Estabilización y control de versiones

Se creó el siguiente commit:

`ea111ab`

Mensaje:

`feat: finalize R2 storage and Webpay reconciliation`

Rama:

`feature/d8-r2-direct-upload`

Resumen:
- 48 archivos modificados o incorporados.
- 5.341 inserciones.
- 397 eliminaciones.

El respaldo histórico de pruebas R2 se mantuvo fuera del control de versiones mediante `.git/info/exclude`, sin eliminar los archivos locales.

### 5. Estado de cierre

- Integración R2: implementada y probada.
- Portadas R2: funcionamiento manual comprobado.
- STEMS: integración y permisos comprobados.
- Webpay: integración y pruebas de conciliación incorporadas.
- Suite completa: 360/360 pruebas aprobadas.
- Migraciones: actualizadas hasta 0027.
- Commit de estabilización: creado.

**Pendiente de esta etapa:** integración del commit en main, publicación en el repositorio remoto y eliminación segura de la rama de trabajo anterior.

---


---

## Cierre D9 - Metadatos musicales - 17-11-2026

### Implementacion

Se verifico la integracion de los metadatos musicales:

- BPM (`bpm`).
- Estado de animo (`mood`).
- Tipo de recurso (`resource_type`).
- Indicador de STEMS (`has_stems`).

Los campos estan incorporados al modelo Track, cuentan con
validaciones y se integran con el flujo de subida directa a Cloudflare R2.

### Migraciones

- 0016_usuario_nombre_artistico: aplicada.
- 0017_track_metadata: aplicada.
- Migraciones 0001 a 0027: aplicadas.
- makemigrations --check --dry-run: sin cambios pendientes.
- migrate --plan: sin operaciones pendientes.

Nota: la migracion de metadatos musicales es 0017,
ya que 0016 estaba ocupada por nombre artistico.

### API y funcionamiento

Se verifico manualmente:

- Subida correcta de canciones.
- Persistencia de los metadatos musicales.
- Exposicion de BPM, mood, tipo y STEMS en el catalogo.
- Visualizacion correcta de los valores asociados a cada cancion.

### Pruebas

Se ejecutaron 38 pruebas automatizadas correspondientes a:

- test_d9_metadata.
- test_r2_track_registration.
- test_r2_upload_workflow.
- test_r2_stems.

Resultado: 38/38 pruebas aprobadas.
Tiempo: 2.193 segundos.

### Estado final

D9: IMPLEMENTADO, INTEGRADO Y VERIFICADO.

No se requirieron modificaciones adicionales al codigo,
nuevas migraciones ni cambios en la infraestructura R2.

---

---

## Cierre D8 - Subida directa a Cloudflare R2 - 17-11-2026

### 1. Objetivo

Implementar y verificar la subida directa de archivos musicales desde
la SPA hacia Cloudflare R2 mediante URLs presignadas PUT, evitando
transferir los archivos pesados a través del servidor Django.

### 2. Configuración del almacenamiento

Se verificó mediante Django:

- Subidas R2 habilitadas.
- Configuración disponible.
- Bucket configurado correctamente.

La prueba de conectividad directa con R2 también fue satisfactoria:

- Generación de URL presignada.
- PUT HTTP 200.
- Verificación del objeto mediante HEAD.
- Eliminación del objeto temporal de diagnóstico.

### 3. Prueba real desde la aplicación

Se realizaron dos subidas desde la interfaz de BeatCloud:

**Archivo de audio WAV**

- Solicitud de URL presignada: HTTP 200.
- Preflight CORS OPTIONS: HTTP 204.
- Subida directa PUT a Cloudflare R2: HTTP 200.
- Confirmación al backend: HTTP 200.

**Archivo ZIP de STEMS**

- Solicitud de URL presignada: HTTP 200.
- Preflight CORS OPTIONS: HTTP 204.
- Subida directa PUT a Cloudflare R2: HTTP 200.
- Confirmación al backend: HTTP 200.

### 4. Finalización y publicación

Se verificó la finalización del registro:

- POST /api/r2/finalize/: HTTP 201.
- Canción incorporada al catálogo.
- Preview generado automáticamente y visible.
- STEMS asociados correctamente a la canción.
- Reproducción de la canción comprobada desde la aplicación.

Las solicitudes PUT se realizaron directamente contra el almacenamiento
Cloudflare R2, no mediante una transferencia del archivo al servidor Django.

### 5. Evidencia de funcionamiento

Se revisó la pestaña Network de Chrome DevTools.

Se identificaron:

- Solicitudes presignadas.
- Preflight CORS satisfactorio.
- PUT de audio con respuesta 200.
- PUT de STEMS con respuesta 200.
- Confirmaciones del backend.
- Finalización con respuesta 201.

También se verificaron los registros de ejecución de Django.

### 6. Estado de aceptación

- URL presignada PUT: VERIFICADA.
- Validación de archivos: IMPLEMENTADA.
- Subida directa desde SPA: VERIFICADA.
- Confirmación al backend: VERIFICADA.
- Preview automático: VERIFICADO.
- Archivos WAV: VERIFICADOS.
- STEMS: VERIFICADOS.
- Publicación en catálogo: VERIFICADA.

**D8: IMPLEMENTADO Y FUNCIONALMENTE VERIFICADO.**

### 7. Validación automatizada y cierre técnico

**Pruebas específicas R2:**
- 61 pruebas ejecutadas.
- 61 pruebas aprobadas.
- Sin errores.

**Suite completa Django:**
- 360 pruebas ejecutadas.
- 360 pruebas aprobadas.
- Resultado: OK.
- Tiempo: 110.732 segundos.

**Frontend:**
- npm run build: correcto.
- TypeScript: compilación correcta.
- Vite: 1.926 módulos transformados.
- Tiempo: 2.94 segundos.

**Resultado:** pruebas automatizadas y compilación aprobadas.

### 8. Estado de publicación

- Implementación D8: verificada.
- Pruebas automatizadas: aprobadas.
- Compilación frontend: aprobada.
- Commit documental: pendiente.
- Publicación en main: pendiente.

---
## 22-11-2026 - Persistencia y recuperación de previews en producción

**Estado:** IMPLEMENTADO Y FUNCIONALMENTE VERIFICADO.

### 1. Diagnóstico

- Los audios originales estaban almacenados en Cloudflare R2.
- Las previews se almacenaban localmente en Render.
- El almacenamiento efímero no garantizaba su persistencia.
- Las solicitudes de reproducción presentaban errores HTTP 404 y 500.

### 2. Solución implementada

- Generación de previews MP3 mediante FFmpeg.
- Almacenamiento persistente de previews en Cloudflare R2.
- Registro de las referencias en PostgreSQL.
- Entrega mediante URLs GET firmadas con vigencia de 600 segundos.
- Conservación del acceso privado a los audios originales.
- Compatibilidad con el almacenamiento local.
- Validación de existencia y tamaño de los objetos R2.

### 3. Nuevos módulos

- app/r2_preview_storage.py
- app/r2_preview_delivery.py
- app/r2_preview_recovery.py
- app/management/commands/recuperar_previews_r2.py

### 4. Recuperación de previews existentes

Se estableció una conexión TLS con PostgreSQL de Render.

Se auditaron las canciones existentes:

- ID 1: Mi Nuevo Beat Rock 2026.
- ID 2: preview prueba.
- ID 3: BeatCloud D8 prueba WAV 24bit 48kHz 45s.

Los tres originales fueron verificados y sus previews recuperadas.

La recuperación no modificó los audios originales.

### 5. Validación automatizada

- Pruebas Django ejecutadas: 405.
- Pruebas aprobadas: 405.
- Errores: 0.
- Django system check: correcto.
- Migraciones pendientes de generación: ninguna.
- Compilación TypeScript y Vite: correcta.

### 6. Publicación y despliegue

- Rama: main.
- Commit: 7cec7e1.
- Archivos modificados y agregados: 21.
- Inserciones: 1775.
- Eliminaciones: 28.
- Publicación GitHub: correcta.
- Despliegue automático Render: correcto.
- Duración del despliegue: 57,5 segundos.
- Estado del servicio: Live.

### 7. Pruebas HTTP en producción

| Track | Render | Vercel | Tamaño MP3 |
|---|---|---|---|
| 1 | HTTP 200 | HTTP 200 | 235557 bytes |
| 2 | HTTP 200 | HTTP 200 | 3063 bytes |
| 3 | HTTP 200 | HTTP 200 | 322101 bytes |

Todas las respuestas entregaron contenido audio/mpeg.

### 8. Validación funcional en navegador

- Reproducción sin iniciar sesión: VERIFICADA.
- Reproducción con sesión iniciada: VERIFICADA.
- Subida de una nueva canción: VERIFICADA.
- Confirmación de publicación por Django: VERIFICADA.
- Reproducción de la nueva canción: VERIFICADA.

### 9. Auditoría final de producción

- Canciones R2 disponibles: 4.
- Previews correctas: 4.
- Previews pendientes: 0.
- Previews con problemas: 0.

**Resultado: corrección de persistencia y reproducción R2 completada.**

### 10. Documentación actualizada

- README.md.
- Modelo de datos y almacenamiento.
- Despliegue y configuración.
- Registro de validación QA.
- Registro histórico de cambios BeatsCloud.

### 11. Tareas pendientes

- [ ] Modificar la posición de la notificación de subida exitosa.
  - Mensaje: Subida completada y confirmada por Django.
  - Ubicación actual: parte superior de la pantalla.
  - Ubicación requerida: parte inferior de la pantalla.
  - Tipo: mejora visual del frontend.
  - Prioridad: baja.
  - No modificar el flujo funcional de subida.

- [ ] Validar el flujo completo de compra y descarga mediante Webpay TEST.

---
