# Modelo de datos y almacenamiento

**Corte técnico inicial:** 18-11-2026. Actualización de almacenamiento R2: 22-11-2026.

## Entidades principales

| Entidad | Clave y relaciones relevantes | Uso técnico |
|---|---|---|
| `auth.User` | PK Django; uno a uno con `Usuario` | Credenciales, sesión y estado de autenticación. |
| `Usuario` | PK propia; `user` OneToOne; tipo artista/productor | Perfil, rol funcional, enlaces y relaciones de catálogo. |
| `Genero_Musical` | PK `id`; catálogo referenciado por `Track.genero` (FK `PROTECT`) | Género del instrumental. |
| `Track` | PK `id_track`; FKs a género y perfil productor | Metadatos, precio, audio/preview/portada y estado de media. |
| `WebpayTransaction` | PK Django; `buy_order` único; usuario FK; token de Webpay único y nullable | Intento de pago, importe, estado, snapshot de carrito y conciliación. |
| `HistorialCompra`, `Venta`, `HistorialVenta`, `Compra`, `Carrito` | FKs hacia usuario, perfil o track conforme a cada modelo | Registros de compras/ventas y compatibilidad con flujos anteriores. No son todos intercambiables. |
| `R2UploadClaim` | propietario FK, `pending_key` único, track OneToOne nullable (`SET_NULL`) | Reserva de carga y vínculo de objetos privados pendientes/finalizados. |

`Track` conserva `storage_backend` (`local`/`r2`, predeterminado `local`), claves de objetos R2, `r2_owner_user_id` (entero sin FK para conservar la identidad original tras borrar la cuenta), `media_status` (`pending`, `processing`, `ready`, `failed`), metadatos D9 y campos `FileField`. Los campos y relaciones exactos están en [app/models.py](../../app/models.py). Las restricciones e índices explícitos de transacciones, claims y relaciones se definen en esos modelos y sus migraciones.

## Migraciones

La secuencia integrada de app incluye la migración 0028_seed_generos_musicales.py. Las migraciones 0023 a 0027 incorporan campos y controles de almacenamiento R2. La migración 0028 incorpora los géneros musicales iniciales. Los cambios de persistencia de previews reutilizan los campos existentes y no requieren una migración nueva.

## Almacenamiento local

Los modelos usan `FileField`/`ImageField` y el backend de archivos configurado por Django; con la configuración revisada los archivos locales residen bajo `MEDIA_ROOT`. El modo local es el usado por los cinco datos de demostración. El endpoint de preview sirve el MP3 generado; el audio completo y la descarga tienen controles de sesión, propiedad/compra según endpoint. En HTTP se verificaron preview anónimo, rechazo anónimo del archivo completo/descarga y acceso del propietario de demostración.

## Cloudflare R2

`app/r2_presign.py` lee las variables de configuración permitidas y construye un cliente S3 compatible con el endpoint de la cuenta. La carga requiere configuración válida y `R2_UPLOADS_ENABLED=true`; las variables están enumeradas sin valores en [`.env.example`](../../.env.example). El flujo expone presign y confirmación en `/api/r2/presign/` y `/api/r2/confirm/`, y finalización/registro en `/api/r2/finalize/`. `app/r2_upload_workflow.py` verifica perfil productor, metadatos y claim, serializa el paso de procesamiento y registra el track; las etapas de preparación validan el objeto antes de asociarlo. El frontend usa `django.service.ts` para negociar y enviar la carga directa.

Los tracks R2 solo son visibles cuando `media_status=ready`. La entrega privada comprueba sesión y autorización (propietario o comprador según la operación), valida formato de clave privada y existencia del objeto antes de emitir una URL temporal. Las URLs firmadas expiran según el código: 3.600 segundos para subida (`app/r2_presign.py`) y 300 segundos para descarga (`app/r2_private_delivery.py`). Las respuestas privadas no se almacenan en caché. Los puentes de audio limitan la entrega y contemplan solicitudes de rango conforme al código de `app/r2_audio_bridge.py` y `app/r2_private_delivery.py`.

### Persistencia de previews R2

- Los originales permanecen privados en sus claves R2.
- FFmpeg genera una preview MP3 de hasta 30 segundos.
- La preview se almacena bajo previews/r2-<identificador>.mp3.
- PostgreSQL conserva la referencia al archivo.
- Django valida la existencia del objeto antes de emitir una URL GET firmada con vigencia de 600 segundos.
- El bucket permanece privado.
- El almacenamiento local conserva su comportamiento.

El 22-11-2026 se verificaron tres originales de producción y se recuperaron sus previews. La auditoría final confirmó tres correctas, cero pendientes y cero con problemas. La reproducción mediante el nuevo código desplegado permanece pendiente.

## Audio

`app/audio_utils.py` delega procesamiento a FFmpeg y genera previews MP3 de hasta 30 segundos. El archivo original permanece separado del preview. La API diferencia `/api/track/<id>/preview/`, `/reproducir/` y `/descargar/`; el cliente React usa dichas rutas y valida el host R2 de una URL firmada antes de navegar. La síntesis de los archivos locales de demo está etiquetada como material de demostración, no corresponde a samples comerciales.

## Pagos y persistencia

PostgreSQL se selecciona con `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT`; el código actual usa opciones específicas de PostgreSQL. `DJANGO_SECRET_KEY` debe configurarse y `DB_PASSWORD` no incorpora contraseña por defecto; [`.env.example`](../../.env.example) enumera variables con secreto vacío. `WebpayTransaction` guarda importe y snapshot del carrito; `app/webpay_reconciliation.py` concilia respuesta con orden, sesión e importe, utiliza bloqueo transaccional e idempotencia de fulfillment. El entorno configurado en este corte declara `TRANSBANK_INTEGRATION_TYPE=TEST`; las pruebas automatizadas sustituyen el proveedor por dobles. No hubo transacción contra Transbank.

## Referencias de implementación

- [Migraciones de R2](../../app/migrations/0023_track_r2_fields.py)
- [Presign R2](../../app/r2_presign.py)
- [Entrega privada](../../app/r2_private_delivery.py)
- [Conciliación Webpay](../../app/webpay_reconciliation.py)
- [API y rutas](../../app/api_shim.py)
- [Configuración Django](../../beatcloud/settings.py)
