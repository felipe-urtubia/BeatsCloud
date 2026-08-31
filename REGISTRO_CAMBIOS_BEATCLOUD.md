# REGISTRO DE CAMBIOS — BEATCLOUD

**Periodo cubierto:** desde el inicio de este chat técnico hasta el 30-08-2026  
**Zona horaria usada:** Chile continental (UTC-04:00)  
**Generado:** 30-08-2026 23:13 aprox.

> Nota sobre las horas: no todos los mensajes del chat exponen una hora individual exacta.  
> Cuando existe una marca de tiempo asociada a archivos creados/subidos durante el trabajo, se usa esa hora convertida a Chile.  
> En los cambios anteriores a esas marcas, la hora se indica como **aprox.** para no inventar una precisión que no está disponible.

---

## 28-08-2026

| Hora | Cambio | Descripción | Estado |
|---|---|---|---|
| 17:19 aprox. | Inicio de mejoras de BeatCloud | Se comenzó a revisar el proyecto Django BeatCloud, su estructura, registro de usuarios, perfiles, pagos, correo y seguridad. | Iniciado |
| 17:30 aprox. | Confirmación de cuenta por correo | El registro fue ajustado para crear usuarios inactivos hasta confirmar el correo mediante `uidb64` + `default_token_generator`. | Implementado |
| 17:40 aprox. | Validación de correo duplicado | Se agregó control para impedir registrar dos cuentas con el mismo correo electrónico. | Implementado |
| 17:50 aprox. | Configuración `.env` | Se dejó la configuración sensible fuera del código fuente y se comprobó la lectura del archivo `.env` desde `settings.py`. | Implementado |
| 18:00 aprox. | Gmail SMTP | Se comprobó el envío de correos desde Django mediante Gmail SMTP. | Probado |
| 18:10 aprox. | Correos HTML profesionales | Se crearon plantillas HTML para confirmación de cuenta y recuperación de contraseña. | Implementado |
| 18:20 aprox. | Recuperación segura de contraseña | Se cambió al flujo oficial y seguro de Django para restablecer contraseña mediante enlace enviado por correo. | Implementado |
| 18:30 aprox. | Redes sociales de perfiles | Se evitó que Instagram, YouTube o Spotify generaran rutas terminadas en `/None` cuando el usuario no tenía un enlace configurado. | Implementado |
| 18:40 aprox. | Perfil público de artista | Se corrigieron los enlaces sociales en el perfil público del artista. | Implementado |
| 18:50 aprox. | Perfil propio de artista | Se corrigieron los enlaces sociales dentro de `/perfil/artista/`. | Implementado |
| 19:00 aprox. | Revisión de pagos | Se comenzó a revisar el problema `401 Not Authorized` de Transbank y el flujo de carrito. | Revisado |

---

## 29-08-2026

| Hora | Cambio | Descripción | Estado |
|---|---|---|---|
| 00:00 aprox. | Transbank Webpay TEST | Se corrigieron las credenciales de integración y se utilizó el ambiente de prueba de Transbank. | Implementado |
| 00:15 aprox. | Monto Webpay | Se normalizó el monto a entero en CLP antes de crear la transacción. | Implementado |
| 00:30 aprox. | Validación de retorno Webpay | Se reforzó `exito_carrito()` para comprobar autorización, orden de compra, sesión, monto y respuesta antes de registrar una compra. | Implementado |
| 00:45 aprox. | Registro de compra posterior al pago | El historial se crea solamente después de una respuesta autorizada y válida de Transbank. | Implementado |
| 01:00 aprox. | Prevención de compra duplicada de tracks | Se agregó control para impedir que un usuario vuelva a comprar un track ya adquirido. | Implementado |
| 01:15 aprox. | Carrito sin duplicados | Si un track ya está pendiente en el carrito, no se vuelve a crear otra venta pendiente. | Implementado |
| 01:30 aprox. | Descarga segura de tracks | Se creó `descargar_track()` con `FileResponse` y comprobación de compra antes de permitir la descarga. | Implementado |
| 01:45 aprox. | Detalle de track comprado | El detalle del track reconoce si ya fue comprado y permite descargarlo sin volver a comprar. | Implementado |
| 02:00 aprox. | Botón Me gusta | Se convirtió en un toggle: “♡ Me gusta” / “♥ Te gusta”. | Implementado |
| 02:15 aprox. | Comentarios | Se protegió el alta y eliminación de comentarios; solo el autor puede borrar el suyo. | Implementado |
| 02:30 aprox. | Eliminación de tracks | Se protegió la eliminación con login, POST, CSRF, confirmación y validación de propietario. | Implementado |
| 02:45 aprox. | Perfiles privados | Se añadieron protecciones `@login_required` a vistas de perfil que requerían autenticación. | Implementado |
| 03:00 aprox. | Edición de tracks | Se agregó edición de track con control de propietario. | Implementado |
| 03:15 aprox. | Audio de tracks vendidos | Si un track ya tiene compras, se puede editar su información, pero no reemplazar el archivo de audio original. | Implementado |
| 03:30 aprox. | Carrito pendiente | El carrito se ajustó para mostrar solamente ventas con `completada=False`. | Implementado |
| 03:45 aprox. | Historial de compra | Se agregó botón para ver el detalle del track desde el historial de compras. | Implementado |
| 04:00 aprox. | Callback antiguo de suscripción | Se corrigió un flujo antiguo que podía marcar compras por una llamada GET sin token válido. | Implementado |
| 04:15 aprox. | Dependencias | Se actualizaron paquetes compatibles y se verificó `python -m pip check` sin dependencias rotas. | Verificado |
| 04:30 aprox. | README / `.env.example` | Se documentó el uso de `.env.example` sin subir el `.env` real al repositorio. | Implementado |

---

## 30-08-2026

### Seguridad de carrito, perfiles y pagos

| Hora | Cambio | Descripción | Estado |
|---|---|---|---|
| 19:53 aprox. | Lógica general corregida | Se consolidaron correcciones de vistas relacionadas con compras, descargas y permisos. | Implementado |
| 19:57 | Descarga segura | Se generó una versión de vistas con descarga protegida de tracks comprados. | Implementado |
| 20:05 | Detalle de track | Se actualizó el detalle del track para reconocer compras previas y ofrecer descarga segura. | Probado |
| 20:11 | Perfil público de artista | Se corrigió el perfil público del artista y sus enlaces sociales. | Implementado |
| 20:15 | Perfil propio de artista | Se corrigió el perfil propio del artista. | Implementado |
| 20:26 | Likes | Se terminó el comportamiento toggle del botón de Me gusta. | Implementado |
| 20:33 | Comentarios | Se terminó la protección de comentarios y eliminación por autor. | Implementado |
| 20:38 | Eliminación de track | Se terminó la eliminación segura con control de propietario y POST. | Implementado |
| 20:39 | Perfil del productor | Se consolidaron mejoras del perfil del productor. | Implementado |
| 20:43 | Protección de perfiles | Se aplicaron protecciones de autenticación a perfiles. | Implementado |
| 20:47 | Edición de track | Se agregó edición segura y bloqueo del reemplazo de audio cuando existen compras. | Implementado |
| 20:52 | Carrito | Se dejó el carrito mostrando únicamente ventas pendientes. | Implementado |
| 20:57 | Historial | Se agregó acceso al detalle desde el historial de compras. | Implementado |
| 21:04 | Callback de pago | Se reforzó el callback para evitar convertir operaciones inválidas en compras. | Implementado |
| 21:11 | Pago del carrito | El pago se ajustó para trabajar solo con ventas pendientes. | Implementado |
| 21:14 | `pago()` con login y POST | La vista de inicio de pago quedó protegida con autenticación y POST. | Implementado |
| 21:31 | CSRF del carrito | Se eliminó `@csrf_exempt` de `pago()` y se dejó CSRF solo donde Transbank necesita retornar externamente. | Probado |
| 21:41 | CSRF de suscripción | El inicio del pago de suscripción quedó protegido con login, POST y CSRF. | Implementado |
| 21:45 | Transbank de suscripción | Se corrigió el flujo de suscripción usando las mismas credenciales TEST de Transbank que funcionaban en el carrito. | Probado |
| 21:55 | Historial de suscripciones | Se agregó relación de suscripción a `WebpayTransaction` y estado `PENDING/AUTHORIZED`. | Implementado |
| 21:55 | Registro de suscripción autorizada | La suscripción solo queda registrada como autorizada después de validar la respuesta de Webpay. | Implementado |
| 21:55 | Historial unificado | El perfil del artista muestra compras de tracks y suscripciones autorizadas. | Probado |

### Interfaz y validación de archivos

| Hora | Cambio | Descripción | Estado |
|---|---|---|---|
| 21:27 | Navbar | Se ordenó el menú como: Inicio – Catálogo – Usuarios – Sobre nosotros – Carrito. | Probado |
| 22:08 | Validación de archivos | Se añadieron extensiones permitidas para audio e imagen en `TrackForm`. | Implementado |
| 22:11 | Avisos de formulario | Se agregaron mensajes visibles para archivos de audio o imagen inválidos. | Implementado |
| 22:16 | Subida restringida a productores | Se reforzó la vista para que solo productores puedan subir tracks. | Implementado |
| 22:19 | Extensiones visibles | El formulario muestra claramente: MP3, WAV, FLAC, M4A, AAC y OGG. | Probado |
| 22:19 | Validación inmediata en navegador | Se agregó comprobación del nombre/extensión antes de enviar el formulario. | Probado |
| 22:22 | Descarga desde historial | El historial dejó de enlazar directamente al archivo físico y usa `descargar_track`. | Probado |

### Protección del audio original

| Hora | Cambio | Descripción | Estado |
|---|---|---|---|
| 22:39 | Ruta de reproducción controlada | Se creó `reproducir_track(request, track_id)` para entregar audio mediante Django en vez de exponer directamente `/media/canciones/...`. | Implementado |
| 22:39 | URL de reproducción | Se agregó `track/<int:track_id>/reproducir/`. | Implementado |
| 22:44 aprox. | Prueba de track por ID | Se consultaron los IDs reales de la tabla Track; la pista llamada `pista` resultó tener `id_track = 9`. | Verificado |
| 22:45 aprox. | Prueba `/track/9/reproducir/` | Se comprobó que el audio se reproduce correctamente mediante la nueva ruta controlada. | Probado |
| 22:48 aprox. | Reproductores protegidos | Se reemplazaron las 6 referencias directas `track.track.url` / `cancion.track.url` por la nueva ruta `reproducir_track`. | Probado |
| 22:55 aprox. | Bloqueo de `/media/canciones/` | Se agregó una ruta previa al `static()` de desarrollo para devolver 404 al intentar acceder directamente al audio original. | Probado |
| 22:58 aprox. | Comprobación final de audio | Se verificó que `/track/9/reproducir/` continúa funcionando mientras `/media/canciones/...` devuelve 404. | Probado |

### Suscripciones y mensajes

| Hora | Cambio | Descripción | Estado |
|---|---|---|---|
| 23:00 aprox. | Compra duplicada de suscripción | Se añadió control para detectar una `WebpayTransaction` `AUTHORIZED` del mismo usuario y la misma suscripción. | Implementado |
| 23:03 aprox. | Mensaje por suscripción repetida | Si el usuario intenta comprar otra vez la misma suscripción, se muestra: “Ya compraste esta suscripción anteriormente.” | Probado |
| 23:05 aprox. | Mensajes globales de Django | Se actualizó `base.html` para mostrar `messages.info`, `messages.success` y `messages.error` como alertas Bootstrap. | Probado |
| 23:08 aprox. | Productor sin suscripción | Se corrigió `perfil_productor2.html` para no intentar usar `suscripcion.id_sus` cuando no existe suscripción. | Implementado |
| 23:09 aprox. | Aviso en perfil de productor | Cuando un productor no tiene suscripción, ahora aparece: “Este productor todavía no tiene una suscripción disponible.” | Probado |
| 23:10 aprox. | Limpieza de scripts temporales | Se confirmó que los `.ps1` y copias `.bak_*` usados durante las modificaciones pueden eliminarse una vez probado el proyecto. | Aprobado |
| 23:11 aprox. | Prueba general | El usuario confirmó que el proyecto funciona correctamente tras las mejoras. | Confirmado |
| 23:12 aprox. | RUT de prueba Transbank | Se aclaró que `11.111.111-1` corresponde al ambiente de integración/pruebas de Transbank y no a un RUT real del comprador. | Documentado |
| 23:13 | Registro de cambios | Se creó este archivo antes de preparar la subida final a GitHub. | Completado |

---

# RESUMEN DE CAMBIOS PRINCIPALES

## Seguridad
- Activación de cuentas por correo.
- Recuperación segura de contraseña.
- Protección de vistas con `@login_required`.
- Acciones sensibles mediante POST y CSRF.
- Validación de propiedad al editar/eliminar contenido.
- Descarga de tracks únicamente para compradores.
- Bloqueo de acceso directo a `/media/canciones/`.
- Reproducción mediante una vista controlada de Django.
- Validación estricta del retorno de Webpay.
- Prevención de compras duplicadas de tracks.
- Prevención de compras duplicadas de suscripciones.

## Pagos
- Corrección del flujo de carrito con Transbank TEST.
- Corrección del flujo de suscripciones con Transbank TEST.
- Validación de orden, sesión, monto y estado autorizado.
- Historial de pagos de suscripción mediante `WebpayTransaction`.
- Estados de transacción `PENDING` y `AUTHORIZED`.
- Explicación del RUT ficticio `11.111.111-1` usado en integración.

## Tracks
- Subida permitida solo a productores.
- Validación de formatos de audio.
- Validación de formatos de imagen.
- Avisos visibles de archivos inválidos.
- Lista visible de formatos permitidos.
- Edición de metadata.
- Bloqueo de reemplazo de audio cuando ya existen ventas.
- Descarga protegida.
- Reproducción protegida por ruta Django.

## Perfiles e interfaz
- Corrección de enlaces de Instagram, YouTube y Spotify.
- Perfil público y privado de artista corregidos.
- Perfil del productor corregido.
- Manejo correcto de productores sin suscripción.
- Mensajes globales con Bootstrap.
- Navbar reorganizado.
- Historial de compras mejorado.
- Historial de suscripciones agregado.
- Botón Me gusta convertido en toggle.
- Comentarios protegidos.

## Archivos y repositorio
- Uso de `.env` para datos sensibles.
- `.env.example` para compañeros.
- README actualizado.
- Dependencias verificadas.
- Scripts `.ps1` utilizados únicamente como herramientas temporales y eliminables después de las pruebas.

---

# ESTADO ACTUAL

Al cierre de este registro:

- `python manage.py check` no presenta errores conocidos.
- El usuario confirmó que las funciones principales probadas están funcionando.
- El audio se reproduce mediante la ruta controlada.
- El acceso directo a `/media/canciones/` queda bloqueado.
- Las descargas requieren una compra previa.
- No se permiten compras duplicadas del mismo track.
- No se permiten compras duplicadas de la misma suscripción autorizada.
- Los pagos siguen utilizando **Transbank TEST / integración**, por lo que los datos de prueba no representan clientes reales.
- El proyecto está en condiciones de pasar a la revisión de `git status`, limpieza final y posterior commit/push a GitHub.

---

# SIGUIENTE PASO SUGERIDO

Antes del `git push`:

```powershell
python manage.py check
git status
```

Luego revisar que no estén incluidos:
- `.env`
- contraseñas
- claves API reales
- archivos temporales `.ps1`
- copias `.bak_*`

Después se puede preparar un commit descriptivo con todos estos cambios.
