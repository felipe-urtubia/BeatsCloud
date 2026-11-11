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