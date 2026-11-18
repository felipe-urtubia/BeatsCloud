# Guía operativa para Felipe: configuración y grabación

**Propósito:** preparar una ejecución local verificable de BeatsCloud y, si las credenciales de integración están disponibles, probar Webpay TEST y Cloudflare R2 con recursos aislados. No es evidencia de que esos servicios estén configurados o validados hoy.

## 0. Obtener el código seguro

El `origin/main` de GitHub todavía contiene historial anterior con archivos de configuración privada. No hagas `git clone`, `fetch` ni push hacia ese remoto hasta que el equipo coordine el saneamiento. Git no permite un bundle shallow autónomo que omita objetos padre: para iniciar este entorno, usa el archivo fuente `beatscloud-main-source.tar.gz` que Ismael entregue por canal privado:

```bash
mkdir BeatsCloud
tar -xzf /ruta/privada/beatscloud-main-source.tar.gz -C BeatsCloud
cd BeatsCloud
git switch main
git status --short --branch
```

El archivo contiene solo el árbol de código de `main`, no historial Git, `.env`, DB ni media. Se entrega solo para iniciar trabajo operativo; no sirve como archivo de trazabilidad histórica. Después de que la publicación segura se complete, se podrá sustituir esta descarga por un clon de GitHub.

## A. Preparación inicial

### Requisitos comprobados en el corte local

- Linux/Fedora; Python 3.14.10, Django 6.0.6.
- Node 22.23.1 y npm 10.9.8.
- PostgreSQL disponible localmente; FFmpeg 8.1.3.
- Cuenta local con permisos sobre PostgreSQL y credenciales propias de integración para servicios externos si se probarán.

Windows/macOS no han sido verificados. No se requiere Docker para ejecución manual si PostgreSQL está instalado y accesible; Docker Compose QA se explica en la guía de Vicente.

### Plantillas de configuración

`.env.example` es una plantilla versionada de variables. Django **no la carga directamente**: `beatcloud/settings.py` carga el archivo local de raíz `.env` y luego las variables del entorno. No contiene credenciales de Felipe.

`frontend/client/.env.example` describe las variables que lee Vite; el archivo local `frontend/client/.env` lo carga Vite en desarrollo. Ninguna variable `VITE_*` debe contener secretos porque se incorpora al cliente.

Crear los dos archivos locales:

```bash
cp .env.example .env
cp frontend/client/.env.example frontend/client/.env
chmod 600 .env frontend/client/.env
```

En `.env`:

- `DJANGO_SECRET_KEY`: obligatoria, aleatoria y exclusiva del equipo/ambiente.
- `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: conexión a PostgreSQL local. DB recomendada `beatscloud_demo_local`, nunca producción.
- `DJANGO_DEBUG=True`, `DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost`, CSRF origins `http://localhost:3000,http://127.0.0.1:3000` y `FRONTEND_URL=http://localhost:3000` para desarrollo HTTP local.
- `FFMPEG_PATH=ffmpeg` si el ejecutable está en PATH.
- `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` durante pruebas locales; SMTP es opcional y se configura solo para probar correo real.
- `TRANSBANK_INTEGRATION_TYPE=TEST`; credenciales se detallan más abajo.
- `R2_UPLOADS_ENABLED=false` por defecto. R2 es opcional y no necesario para storage local.

Si el nombre de la base demo comienza `beatscloud_demo_` y el host es local, los comandos de seed locales admiten la operación. No corras seed/reset en DB compartida ni productiva.

### PostgreSQL, Python y frontend

Crear `beatscloud_demo_local` desde tu instalación PostgreSQL. Ejemplo si `createdb` está en PATH:

```bash
createdb -h 127.0.0.1 -p 5432 -U postgres beatscloud_demo_local
```

Si el usuario requiere contraseña, ingrésala de forma interactiva o configúrala con el administrador local; no la pongas en el historial de shell. Completa `DB_*` de `.env` para que coincida.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python manage.py check
python manage.py migrate
python manage.py prepare_demo_catalog
python manage.py prepare_qa_users
python manage.py generate_qa_catalog --count 120 --seed 20261118
```

`prepare_demo_catalog` crea cinco instrumentales sintéticas con audio, preview y portada; `generate_qa_catalog` suma el conjunto sintético variado. Ambos requieren base Postgres local con nombre `beatscloud_demo_*` o `beatscloud_qa_*`. `prepare_qa_users` genera cuentas comprador/productor/admin y muestra contraseñas aleatorias solo al crearlas o rotarlas: guardarlas en un gestor privado. Nunca copiarlas a documentación, capturas ni Git. Para nuevas contraseñas: `python manage.py prepare_qa_users --rotate-passwords`.

Instalar e iniciar frontend en otra terminal:

```bash
cd frontend/client
npm ci
npm test
npm run lint
npm run build
npm run dev
```

Iniciar backend desde la raíz (terminal con `.venv` activado):

```bash
python manage.py runserver 127.0.0.1:8000
```

Vite usa el proxy configurado en `VITE_DJANGO_PROXY_TARGET`; API y media se enrutan a Django. URLs: React <http://localhost:3000/>, Django <http://127.0.0.1:8000/>.

Comprobar por separado:

```bash
curl -i http://127.0.0.1:8000/api/session/
curl -i http://127.0.0.1:8000/api/catalogo/
curl -i http://localhost:3000/
```

La respuesta de sesión anónima `null` con HTTP 200 es normal. Catálogo debe incluir tracks. Esto verifica conectividad, no reproducción audible, autorización de compra ni proveedores externos.

### Media y estáticos

Django crea subdirectorios de medios al guardar audios/previews/portadas. FFmpeg se utiliza al procesar/generar previews. El repo no configura `STATIC_ROOT`, WhiteNoise ni `collectstatic` productivo; `runserver`/Vite sirven el desarrollo. No ejecutar `collectstatic` como prueba de despliegue sin completar esa configuración.

## B. Webpay Plus / Transbank

### Integración existente

La app utiliza `transbank-sdk` y crea `Transaction(WebpayOptions(commerce_code, api_key, integration_type))` en `app/api_shim.py`/`app/webpay_reconciliation.py`. `POST /api/pago/` crea orden local `WebpayTransaction`, captura snapshot y monto del carrito en servidor, invoca `tx.create`, y devuelve URL/token para redirección del navegador. El retorno va a `exito_carrito` o `exito`; Django reconcilia `commit` o `status`, compara orden/sesión/monto/usuario, y registra la compra solo ante autorización verificada. La cancelación y retornos incompletos pueden dejar la orden pendiente/archivada para revisión; no asumas que un error HTTP equivale a rechazo confirmado.

### Credenciales TEST

En [Transbank Developers](https://www.transbankdevelopers.cl/producto/webpay), obtener datos de integración/sandbox que correspondan al proyecto o solicitarlos a quien administra la cuenta. El SDK usa estas variables actuales:

- `TRANSBANK_COMMERCE_CODE`
- `TRANSBANK_API_KEY`
- `TRANSBANK_INTEGRATION_TYPE=TEST`

El histórico `TRANSBANK_SHARED_SECRET` no tiene lectores en los flujos activos y no va en la plantilla. Si ese valor fue incluido en el archivo accidental, también debe rotarse como credencial potencialmente expuesta. No usar credenciales LIVE en este recorrido. No pegarlas en el chat, issues, logs, screenshots o `.env.example`; escribirlas solo en el `.env` privado local (modo `0600`).

### Prueba controlada

1. Confirmar DB local demo, Webpay TEST, variables de integración presentes y disponibilidad del ambiente.
2. Iniciar sesión como comprador, agregar tracks de demo al carrito y abrir checkout.
3. Verificar que `POST /api/pago/` responde con URL de pasarela y que el navegador va al dominio de integración. No registrar ni compartir `token_ws`.
4. Usar los datos de tarjeta/casos de prueba que publica el portal oficial. Registrar hora, `buy_order` y `transaction_id` sin copiar tokens ni datos de tarjeta.
5. Completar el caso aprobado y volver a la ruta de retorno. Verificar en el perfil comprador la compra y en Django admin/DB local `WebpayTransaction.status=AUTHORIZED`, `fulfilled_at` y las filas de historial/venta asociadas.
6. Repetir casos rechazo/cancelación con datos oficiales del sandbox. Resultado aceptable: no se entrega archivo ni se registra una compra autorizada; revisar estado transaccional, cancelación o `archived_for_review` en DB.
7. Repetir el retorno/callback si se prueba idempotencia: no debe duplicar historial/venta ni entregar dos veces.
8. Guardar evidencia redactada: commit, entorno TEST, hora, orden local, estado antes/después y capturas. Nunca guardar PAN/CVV/token.

El suite automatizado usa doubles y cubre ramas de conciliación/concurrencia. No constituye una transacción real. Registrar aparte cualquier ejecución con el portal sandbox. Ver [flujo Webpay Plus](https://proyecto-ejemplo-python.transbankdevelopers.cl/webpay-plus/) y [estado del ambiente](https://status.transbankdevelopers.cl/).

**Disponibilidad fechada:** el status de Transbank consultado el 18-11-2026 mostraba mantenimiento programado del ambiente de integración el jueves 19-11-2026, 13:00–15:00 (GMT-03). Revisar el status el mismo día antes de grabar, pues esa ventana puede impedir pagos de prueba.

## C. Cloudflare R2

### Comportamiento implementado

Con `R2_UPLOADS_ENABLED=true`, el flujo frontend/backend ejecuta:

1. `POST /api/r2/presign/`: Django requiere sesión y rol productor, valida extensión/MIME/tamaño y firma una URL PUT por una hora.
2. El navegador carga audio, portada o stems por `PUT` a la URL firmada, directo a R2.
3. `POST /api/r2/confirm/`: Django verifica objeto y metadatos vía HEAD; esto no publica aún un track.
4. `POST /api/r2/finalize/`: valida claims/propiedad, verifica/stagea el objeto, registra track y genera preview mediante FFmpeg local.
5. Los servicios de entrega privada emiten entrega temporal tras revisar propietario/compra; `/api/track/<id>/preview/` es la ruta de preview. Full stream, descarga y stems aplican permisos específicos.

Almacenamiento local usa `MEDIA_ROOT` y no requiere R2. R2 mantiene objetos privados; no configurar bucket público para el flujo de compras.

### Bucket y credenciales de desarrollo

En Cloudflare Dashboard, crear un bucket separado de desarrollo y un token S3/API con mínimo acceso de lectura/escritura al bucket necesario. Felipe obtiene `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` y nombre de bucket desde sus credenciales privadas del panel. El account ID requerido por el cliente debe ser ID de 32 caracteres hexadecimales. Mantener claves en `.env` local con `chmod 600`, nunca en `VITE_*` ni Git.

Completar localmente `.env` con las variables indicadas en `.env.example` y `R2_UPLOADS_ENABLED=true`. No activar R2 en `.env.qa`; sus scripts lo bloquean deliberadamente. Usa base local demo y bucket aislado, nunca bucket productivo.

El navegador llama directamente a R2, por lo que bucket necesita CORS para el origen frontend exacto (local `http://localhost:3000`; en despliegue el dominio Vercel definitivo), operaciones requeridas `PUT` para subir y `GET`/`HEAD` solo si se solicitan desde navegador, y headers mínimos como `Content-Type` según el request firmado. No uses origen `*`. Ajustar según pestaña Network y probar la política guardada. [Cloudflare documenta CORS y URLs firmadas](https://developers.cloudflare.com/r2/buckets/cors/) y explica que requests firmados desde navegador requieren CORS.

### Prueba de subida, preview y privacidad

1. Confirmar `python manage.py check`, FFmpeg disponible y productor activo. Abrir upload en React y subir audio original de prueba, pequeño y autorizado; usar portada opcional.
2. En Network comprobar orden `presign -> PUT R2 -> confirm -> finalize`. No copiar URL firmada ni `upload_token` a evidencia.
3. Verificar respuesta UI, track persistido como `storage_backend=r2`, `media_status=ready`, clave privada, preview asociado y objeto existente en el bucket privado.
4. Abrir catálogo y reproducir preview. Confirmar request de audio y audibilidad en navegador (no solo HTTP 200).
5. Solicitar full/download como anónimo y cuenta sin compra; backend debe negar. Probar como propietario y usuario con compra real TEST; validar entrega correcta. El link temporal es bearer token: no compartirlo.
6. Si se prueba expirar URL, confirmar `expires_in` de la respuesta, volver a usarla tras ese plazo y verificar rechazo. No probar sobre archivos/bucket productivos.
7. Revisar track en estado ready y preview audible. Retirar objetos de prueba solo mediante procedimiento del bucket/DB demo, nunca con comandos genéricos ni en producción.

La integración R2 tiene pruebas automatizadas con mocks/stubs. No se probó Cloudflare real en este corte; CORS, permisos y workflow de preview requieren evidencia de Felipe.

## D. Recorrido para grabar

Grabar solo con DB/bucket y cuentas de prueba. No mostrar contraseñas, tokens, datos de tarjeta ni medios privados.

| Paso | Acción | Resultado esperado | Evidencia útil | Requisitos previos | Estado al 18-11 |
|---|---|---|---|---|---|
| 1 | Abrir SPA y catálogo | Catálogo con precio, género, portada y metadatos | URL y captura sin datos sensibles | Servicios local, seed demo | HTTP local comprobado; navegación Firefox pendiente |
| 2 | Buscar, filtrar y abrir detalle/perfil | Resultados y metadatos coherentes | Captura de filtro y detalle | Catálogo sintético/demo | Manual pendiente |
| 3 | Registro/login comprador | Sesión persiste; registro requiere activación | Vista Network redactada y sesión | Email consola o cuenta demo activa | Tests HTTP; navegador pendiente |
| 4 | Login productor y perfil | Upload disponible para rol productor | Captura de rol/productor | Contraseña QA privada | Manual pendiente |
| 5 | Subir audio | Upload completa, Track queda ready | UI, Network redactada, ID de pista | Local: storage local; cloud: bucket/CORS/keys R2 | Mocks; R2 real pendiente |
| 6 | Comprobar preview | Preview disponible y audible | Reproducción del navegador, consola | FFmpeg; preview listo | Endpoint MP3 comprobado; Firefox pendiente |
| 7 | Agregar pista y pagar | Webpay TEST inicia con monto backend | Orden local, respuesta y retorno sin token | Credenciales sandbox y portal disponible | Tests dobles; transacción real pendiente |
| 8 | Confirmar compra | Historial refleja autorización conciliada | Estado de transacción/historial DB local | Pago autorizado sandbox | E2E pendiente |
| 9 | Descargar compra | Archivo solo para comprador autorizado | Descarga no vacía, evidencia redactada | Compra autorizada; storage local/R2 | Denegación anónima comprobada; descarga permitida pendiente |
| 10 | Repetir como anónimo/usuario ajeno | Full/download denegado | Status/error sin cookies | Track privado de prueba | 403 anónimo comprobado |

Si Webpay/R2 no están configurados, no narrarlos como operativos: indicar “integración implementada; validación externa bloqueada”. Como alternativa de video, grabar catálogo/preview local y omitir compra, sin fingir confirmación.

## E. Solución de problemas

| Síntoma | Comprobación |
|---|---|
| Django exige `DJANGO_SECRET_KEY` | Confirmar `.env` de raíz con clave local; la plantilla sola no basta. No imprimirla en logs. |
| PostgreSQL `connection refused` | Revisar servicio/puerto, `DB_HOST`, `DB_PORT`, DB y credenciales. `pg_isready -h 127.0.0.1 -p 5432`. No cambiar a DB productiva. |
| Migraciones pendientes | `python manage.py showmigrations`, `python manage.py migrate`; confirmar DB local antes. No migrar producción durante grabación. |
| Login/CSRF 403 | Revisar origen exacto/puerto en `DJANGO_CSRF_TRUSTED_ORIGINS`, cookies y proxy. Mantener `X-CSRFToken`; no desactivar CSRF. |
| Vite recibe 404/502 | Iniciar desde `frontend/client`, revisar `VITE_DJANGO_PROXY_TARGET`, puertos 3000/8000 y `/api/session/`. `VITE_DJANGO_URL` vacío usa proxy same-origin. |
| Upload local rechazado | Revisar rol, MIME/extensión/tamaño, metadata D9, espacio y FFmpeg. Inspeccionar respuesta/status. |
| R2 firma inválida/403 | Confirmar account ID, bucket, token y permisos, hora, `Content-Type` firmado, expiración, CORS y endpoint R2. No compartir URL firmada. |
| Preview falta/no suena | Revisar `media_status`, archivo preview, FFmpeg, logs y Network; probar gesto de usuario y consola Firefox/AudioContext. HTTP 200 no prueba audibilidad. |
| Webpay no crea transacción | Confirmar `TEST`, commerce/API keys sandbox, conectividad, carrito y status del proveedor. Un 502 deja orden para revisión; no reintentar en bucle ni asumir cancelación. |
| Retorno no confirma | Revisar orden/sesión/monto/status y logs sin tokens; el servidor concilia la respuesta, el frontend no confirma pago. |

## Fuentes de implementación

`beatcloud/settings.py`; `app/api_shim.py`; `app/webpay_reconciliation.py`; `app/webpay_checkout_guard.py`; `app/r2_presign.py`; `app/r2_upload_http.py`; `app/r2_upload_workflow.py`; `app/r2_registration_prepare.py`; `app/r2_private_delivery.py`; `app/r2_audio_bridge.py`; `frontend/client/src/context/AppContext.tsx`; `frontend/client/src/api/django.service.ts`.
