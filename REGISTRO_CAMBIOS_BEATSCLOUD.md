# REGISTRO DE CAMBIOS — BEATSCLOUD

**Proyecto:** BeatsCloud  
**Periodo cubierto:** 28-08-2026 al 31-08-2026  
**Zona horaria de referencia:** Chile continental (UTC-04:00)  
**Última actualización:** 31-08-2026

> Este archivo registra los cambios técnicos y visuales realizados durante la mejora del proyecto.
> Cuando no existe una hora exacta verificable, se registra solamente la fecha o se indica que el cambio ocurrió durante la sesión.

---

# 28-08-2026

## Cuentas, correo y configuración

| Cambio | Descripción | Estado |
|---|---|---|
| Inicio de mejoras de BeatsCloud | Se comenzó a revisar la estructura del proyecto Django, registro de usuarios, perfiles, pagos, correo y seguridad. | Iniciado |
| Confirmación de cuenta por correo | El registro fue ajustado para crear usuarios inactivos hasta confirmar el correo mediante `uidb64` y `default_token_generator`. | Implementado |
| Validación de correo duplicado | Se agregó control para impedir registrar dos cuentas con el mismo correo electrónico. | Implementado |
| Configuración `.env` | Se dejó la configuración sensible fuera del código fuente y se comprobó la lectura del archivo `.env` desde `settings.py`. | Implementado |
| Gmail SMTP | Se comprobó el envío de correos desde Django mediante Gmail SMTP. | Probado |
| Correos HTML | Se crearon plantillas HTML para confirmación de cuenta y recuperación de contraseña. | Implementado |
| Recuperación segura de contraseña | Se adoptó el flujo oficial de Django para restablecer contraseña mediante un enlace enviado por correo. | Implementado |
| Redes sociales de perfiles | Se evitó generar rutas terminadas en `/None` cuando Instagram, YouTube o Spotify no tienen URL configurada. | Implementado |
| Perfil público de artista | Se corrigieron los enlaces sociales del perfil público. | Implementado |
| Perfil propio de artista | Se corrigieron los enlaces sociales del perfil privado. | Implementado |
| Revisión de Transbank | Se comenzó a revisar el error `401 Not Authorized` y el flujo de pago del carrito. | Revisado |

---

# 29-08-2026

## Seguridad, compras y tracks

| Cambio | Descripción | Estado |
|---|---|---|
| Transbank Webpay TEST | Se corrigieron las credenciales de integración y se utilizó el ambiente de prueba de Transbank. | Implementado |
| Monto Webpay | Se normalizó el monto a entero en CLP antes de crear la transacción. | Implementado |
| Validación del retorno Webpay | `exito_carrito()` comprueba autorización, orden, sesión, monto y respuesta antes de registrar una compra. | Implementado |
| Registro posterior al pago | El historial se genera únicamente después de una respuesta autorizada y válida. | Implementado |
| Prevención de compra duplicada | Se impide volver a comprar un track ya adquirido. | Implementado |
| Carrito sin duplicados | Si un track ya está pendiente en el carrito no se crea otra venta pendiente. | Implementado |
| Descarga segura | Se creó `descargar_track()` con `FileResponse` y comprobación de compra. | Implementado |
| Detalle de track comprado | El sistema reconoce la compra previa y habilita descarga sin cobrar nuevamente. | Implementado |
| Botón Me gusta | Se convirtió en toggle: `♡ Me gusta` / `♥ Te gusta`. | Implementado |
| Comentarios | Alta y eliminación protegidas; solo el autor puede eliminar su comentario. | Implementado |
| Eliminación de tracks | Se protegió mediante login, POST, CSRF y validación de propietario. | Implementado |
| Perfiles privados | Se reforzaron vistas con `@login_required`. | Implementado |
| Edición de tracks | Se agregó control de propietario. | Implementado |
| Audio de tracks vendidos | Se puede editar metadata, pero no reemplazar el audio cuando ya existen compras. | Implementado |
| Carrito pendiente | El carrito muestra únicamente ventas con `completada=False`. | Implementado |
| Historial de compra | Se agregó acceso al detalle del track desde el historial. | Implementado |
| Callback antiguo de suscripción | Se corrigió un flujo que podía marcar compras mediante GET sin token válido. | Implementado |
| Dependencias | Se actualizaron paquetes compatibles y se verificó `python -m pip check`. | Verificado |
| README y `.env.example` | Se documentó el uso de `.env.example` sin subir el `.env` real. | Implementado |

---

# 30-08-2026

## Seguridad de carrito, perfiles y pagos

| Cambio | Descripción | Estado |
|---|---|---|
| Descarga segura consolidada | Se reforzaron las vistas de descarga de tracks comprados. | Implementado |
| Detalle de track | Reconoce compras previas y ofrece descarga segura. | Probado |
| Perfiles de artista | Se corrigieron perfil público y privado. | Implementado |
| Likes | Se terminó el comportamiento toggle. | Implementado |
| Comentarios | Se completó la protección y eliminación por autor. | Implementado |
| Eliminación de track | Control de propietario y POST. | Implementado |
| Perfil del productor | Se consolidaron mejoras funcionales. | Implementado |
| Protección de perfiles | Se aplicaron controles de autenticación. | Implementado |
| Edición de track | Se bloquea el reemplazo de audio cuando existen compras. | Implementado |
| Carrito | Se mantiene únicamente con ventas pendientes. | Implementado |
| Historial | Se agregó acceso al detalle desde compras. | Implementado |
| Callback de pago | Se reforzó para evitar convertir operaciones inválidas en compras. | Implementado |
| Pago del carrito | Trabaja solo con ventas pendientes. | Implementado |
| `pago()` | Inicio de pago protegido con autenticación y POST. | Implementado |
| CSRF del carrito | Se eliminó `@csrf_exempt` del inicio de pago; se conserva solo donde Transbank necesita retornar externamente. | Probado |
| CSRF de suscripción | Inicio de pago protegido con login, POST y CSRF. | Implementado |
| Transbank de suscripción | Se corrigió el flujo usando el ambiente TEST que funcionaba en el carrito. | Probado |
| Historial de suscripciones | Se relacionó la suscripción con `WebpayTransaction`. | Implementado |
| Registro autorizado | Una suscripción solo queda autorizada después de validar la respuesta de Webpay. | Implementado |
| Historial unificado | El perfil muestra compras de tracks y suscripciones autorizadas. | Probado |

## Validación de archivos y audio

| Cambio | Descripción | Estado |
|---|---|---|
| Validación de archivos | Se añadieron extensiones permitidas para audio e imagen. | Implementado |
| Avisos de formulario | Se muestran errores claros para audio o imagen inválidos. | Implementado |
| Subida restringida | Solo productores pueden subir tracks. | Implementado |
| Formatos visibles | MP3, WAV, FLAC, M4A, AAC y OGG. | Probado |
| Validación en navegador | Se comprueba extensión antes de enviar el formulario. | Probado |
| Descarga desde historial | Se eliminó el enlace directo al archivo físico y se usa `descargar_track`. | Probado |
| Ruta de reproducción controlada | Se creó `reproducir_track(request, track_id)`. | Implementado |
| URL de reproducción | Se agregó `track/<int:track_id>/reproducir/`. | Implementado |
| Reproductores | Se reemplazaron referencias directas al archivo por la ruta controlada. | Probado |
| Bloqueo de `/media/canciones/` | El audio original no queda expuesto directamente en desarrollo. | Probado |
| Prueba de reproducción | La ruta controlada reproduce mientras el acceso directo a `/media/canciones/` devuelve 404. | Probado |

## Suscripciones y mensajes

| Cambio | Descripción | Estado |
|---|---|---|
| Compra duplicada de suscripción | Se detecta una `WebpayTransaction` `AUTHORIZED` del mismo usuario y suscripción. | Implementado |
| Mensaje por compra repetida | Se informa que la suscripción ya fue comprada anteriormente. | Probado |
| Mensajes globales | `base.html` muestra mensajes Django mediante alertas Bootstrap. | Probado |
| Productor sin suscripción | El perfil público funciona aunque no exista suscripción. | Implementado |
| Aviso sin suscripción | Se informa que el productor todavía no tiene una suscripción disponible. | Probado |
| Limpieza temporal | Se confirmó que scripts `.ps1` y respaldos `.bak` pueden eliminarse tras las pruebas. | Aprobado |
| Prueba general | Las funciones principales revisadas quedaron operativas. | Confirmado |
| Datos de prueba Transbank | Se documentó que los datos del ambiente de integración no representan clientes reales. | Documentado |

---

# 31-08-2026

## Modernización general de interfaz

Durante esta etapa se modernizó la presentación visual de BeatsCloud manteniendo la lógica funcional existente.

| Pantalla / módulo | Cambio realizado | Estado |
|---|---|---|
| Inicio | Hero, secciones principales, explicación de roles, funcionamiento y llamados a la acción. | Probado |
| Catálogo de usuarios | Filtros por tipo de usuario, buscador, conteos y tarjetas modernas. | Probado |
| Catálogo de tracks | Buscador, género, precio, ordenamiento, paginación y estado de compra. | Probado |
| Detalle de track | Diseño renovado conservando reproducción, compra, descarga, likes y comentarios. | Probado |
| Perfil público de productor | Diseño moderno con portada, avatar, redes, suscripción y tracks. | Probado |
| Perfil público de artista | Diseño moderno y corrección de textos/codificación. | Probado |
| Perfil privado de artista | Historial de tracks, suscripciones, favoritos y edición de perfil. | Probado |
| Perfil privado de productor | Proyectos, ventas, suscripción, subida y edición de tracks. | Probado |
| Subir track | Diseño renovado, vista previa de portada y ayuda de formatos. | Probado |
| Editar track | Diseño renovado y aviso cuando existen compras que impiden reemplazar audio. | Probado |
| Editar perfil productor | Se corrigió la plantilla utilizada por la vista y se añadió contexto `usuario`. | Probado |
| Editar perfil artista | Se añadió contexto `usuario` y se modernizó la pantalla. | Probado |
| Carrito | Tarjetas de productos, reproductor protegido y resumen de compra. | Probado |
| Pago exitoso | Pantalla de confirmación visual de compra. | Probado |
| Pago cancelado | Pantalla moderna indicando que no se realizó el cobro. | Probado |
| Sobre nosotros | Contenido actualizado según las funciones reales del proyecto. | Probado |
| Login | Diseño renovado, recuperación de contraseña y opción mostrar/ocultar contraseña. | Probado |
| Registro | Diseño renovado, errores, imágenes y validaciones del formulario existentes. | Probado |

## Activación de cuenta

| Cambio | Descripción | Estado |
|---|---|---|
| Revisa tu correo | Se modernizó la pantalla posterior al registro. | Probado |
| Cuenta activada | Se creó una pantalla propia de BeatsCloud con acceso directo al login. | Probado |
| Enlace inválido | Se modernizó el mensaje para enlaces vencidos, usados o inválidos. | Probado |
| Corrección de codificación | Se corrigieron textos con caracteres dañados como `contraseÃ±a`, `sesiÃ³n`, etc. | Implementado |

## Recuperación de contraseña con Django

Se mantuvo el sistema oficial de Django para generar tokens y cambiar contraseñas. Se personalizaron las pantallas para evitar que apareciera la interfaz predeterminada de Django Administration.

| Paso | Cambio | Estado |
|---|---|---|
| Solicitar recuperación | Formulario propio en `app/password_reset_form.html`. | Probado |
| Correo enviado | Pantalla propia en `app/password_reset_done.html`. | Probado |
| Crear nueva contraseña | Pantalla propia en `app/password_reset_confirm.html`. | Probado |
| Contraseña actualizada | Pantalla propia en `app/password_reset_complete.html`. | Probado |
| Rutas de recuperación | Se corrigieron `template_name` en `app/urls.py` para utilizar las plantillas de BeatsCloud. | Probado |
| Privacidad | La respuesta no revela si un correo está o no registrado. | Implementado |
| Flujo completo | Correo → enlace → nueva contraseña → confirmación → login. | Probado |

## Suscripciones y pago

| Cambio | Descripción | Estado |
|---|---|---|
| Crear suscripción | Se modernizó `ingresar_suscripcion.html` conservando `detalle`, `precio`, POST y CSRF. | Probado |
| Confirmar suscripción | Se modernizó `suscripcion.html` con resumen antes de crear el pago. | Probado |
| Pantalla de Webpay | Se modernizó `pago.html`, corrigiendo codificación y conservando `token_ws` y campos necesarios para Transbank. | Probado |
| Cancelar antes de Webpay | Se agregó un botón que permite salir sin enviar el formulario a Webpay. | Probado |
| Retorno al cancelar | En suscripciones vuelve al perfil del productor; en carrito vuelve al carrito. | Probado |
| Estado `CANCELLED` | Se añadió `ESTADO_CANCELADO = 'CANCELLED'` al modelo `WebpayTransaction` y se aplicó la migración. | Implementado |

### Pendiente inmediato del flujo de cancelación

El modelo ya admite:

- `PENDING`
- `AUTHORIZED`
- `CANCELLED`

Sin embargo, todavía falta conectar el botón **Cancelar pago** con una vista segura que cambie la transacción creada de `PENDING` a `CANCELLED`.

Actualmente el botón evita entrar a Webpay, pero la transacción creada antes de mostrar `pago.html` todavía puede quedar en estado `PENDING`.

Este es el siguiente cambio técnico a realizar.

## Limpieza de archivos temporales

Se eliminaron los scripts `.ps1` utilizados para aplicar cambios puntuales y los respaldos `.bak` después de comprobar que las modificaciones funcionaban.

Los scripts eran herramientas temporales y no forman parte de la aplicación en producción.

---

# RESUMEN ACTUAL DE FUNCIONALIDADES

## Seguridad

- Activación de cuentas por correo.
- Recuperación de contraseña mediante tokens de Django.
- Contraseñas gestionadas mediante el sistema seguro de Django.
- Vistas privadas protegidas con autenticación.
- Acciones sensibles mediante POST y CSRF.
- Validación de propiedad al editar o eliminar contenido.
- Descarga de tracks solo para compradores.
- Prevención de compras duplicadas.
- Validación del retorno de Webpay.
- Datos sensibles almacenados en `.env`.
- El `.env` real no debe subirse al repositorio.

## Pagos

- Carrito con Transbank Webpay en ambiente TEST.
- Suscripciones con Transbank Webpay en ambiente TEST.
- Validación de orden, sesión, monto y autorización.
- Registro de suscripciones mediante `WebpayTransaction`.
- Estados disponibles: `PENDING`, `AUTHORIZED` y `CANCELLED`.
- Botón para abandonar el pago antes de entrar a Webpay.
- Pendiente: marcar automáticamente `CANCELLED` al usar ese botón.

## Tracks

- Subida solo para productores.
- Validación real de archivos de audio.
- Validación de extensiones de audio e imagen.
- Edición de metadata.
- Protección del audio de tracks con compras.
- Reproducción mediante una ruta Django controlada.
- Descarga protegida para compradores.

> La reproducción controlada evita exponer directamente la ruta física del archivo,
> pero no constituye un sistema DRM.

## Perfiles e interfaz

- Perfiles públicos y privados modernizados.
- Redes sociales seguras cuando no existe URL.
- Edición de perfiles modernizada.
- Catálogo de usuarios con filtros y búsqueda.
- Catálogo de tracks con filtros, búsqueda y paginación.
- Carrito y detalle de track modernizados.
- Login, registro, activación y recuperación con diseño propio de BeatsCloud.
- Pantallas de éxito y cancelación de pago modernizadas.
- Suscripciones y confirmación de pago modernizadas.
- Mensajes globales mediante Bootstrap.

## Archivos y repositorio

- `.env` para datos sensibles.
- `.env.example` para configuración de otros integrantes.
- README de instalación y ejecución.
- Dependencias verificadas.
- Scripts temporales `.ps1` eliminables después de aplicarlos.
- Respaldos `.bak` eliminables después de validar los cambios.

---

# ESTADO ACTUAL

Al 31-08-2026:

- Las funciones principales probadas continúan funcionando.
- La modernización visual cubre las principales páginas del sistema.
- El flujo completo de recuperación de contraseña fue probado correctamente.
- La activación de cuenta cuenta con pantallas propias de BeatsCloud.
- El flujo de creación y confirmación de suscripciones fue modernizado.
- Webpay continúa en ambiente de integración TEST.
- `WebpayTransaction` ya incluye el estado `CANCELLED`.
- Falta implementar la acción del servidor que convierta una transacción `PENDING` en `CANCELLED` al abandonar el pago.
- Antes de subir los cambios finales a GitHub se debe volver a ejecutar `python manage.py check` y revisar `git status`.

---

# SIGUIENTE PASO TÉCNICO

Implementar una vista segura para **cancelar una transacción pendiente**:

1. Recibir la cancelación mediante POST.
2. Verificar que la transacción pertenezca al usuario autenticado.
3. Verificar que su estado actual sea `PENDING`.
4. Cambiar el estado a `CANCELLED`.
5. No registrar ninguna compra ni suscripción como autorizada.
6. Redirigir al perfil del productor o al carrito según el origen.
7. Mantener CSRF y autenticación.

Después de completar ese cambio:

```powershell
python manage.py check
git status
```

Antes del commit final, comprobar que no se incluyan:

- `.env`
- contraseñas o claves privadas
- archivos temporales `.ps1`
- respaldos `.bak`
- archivos generados que no deban formar parte del repositorio
