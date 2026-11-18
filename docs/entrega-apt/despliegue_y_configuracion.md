# Configuración y preparación de despliegue

Estado: **propuesta técnica, no despliegue ejecutado**. Código de referencia en `main` local. Render/Vercel, DNS, proveedores, dominios, credenciales, backups y salud operativa no están configurados/verificados.

## Topología propuesta

- Render Web Service para Django/API, Render PostgreSQL administrado y Vercel como frontend estático Vite.
- El navegador debe conservar cookie de sesión y CSRF. Como el cliente usa `credentials: same-origin`, una SPA en dominio Vercel y backend en dominio Render **no es compatible directamente** con el modo actual sin cambios y validación. Opción a evaluar: Vercel rewrite de `/api/:path*` y `/media/:path*` al servicio Django, con misma URL visible del frontend, o configurar explícitamente cliente cross-origin, CORS, cookies `SameSite=None; Secure`, `CSRF_TRUSTED_ORIGINS`, proxy TLS y pruebas en navegador. La opción rewrite conserva URL pública same-origin, pero los headers/cookies deben comprobarse en el entorno real.
- PostgreSQL debe ser exclusivo por entorno; migraciones se aplican mediante procedimiento de release/pre-deploy controlado.
- Archivos: Cloudflare R2 privado para producción tras prueba con bucket aislado; filesystem Render es efímero por defecto. R2 requiere credenciales privadas en plataforma. No guardar audios privados solo en disco efímero.
- Webpay se mantiene `TEST` hasta completar validación explícita; `LIVE` requiere autorización de Felipe y revisión operativa. SMTP necesita proveedor y dominio verificado.

## Bloqueos técnicos antes del despliegue

1. El repositorio no configura `STATIC_ROOT`, WhiteNoise ni un comando de build/deploy Django con Gunicorn; `gunicorn` no está confirmado en `requirements.txt`. `runserver` es solo desarrollo. Definir servidor WSGI/ASGI, static files y health check antes de crear servicio.
2. `settings.py` consume variables separadas `DB_*`, no `DATABASE_URL`; definir mapeo compatible o configurar `DB_*` con el panel. No asumir que la receta de plataforma funciona sin adaptación.
3. No existe endpoint health-check dedicado verificado; `/api/session/` es una ruta funcional, no chequeo de salud completa. Añadir/seleccionar health check solo tras decisión técnica y prueba.
4. Configurar `ALLOWED_HOSTS`, `DJANGO_DEBUG=False`, clave Django aleatoria, HTTPS, cookies, CSRF y proxy. Validar headers forward-proto y dominios efectivos.
5. Confirmar migraciones revisadas, backup/restore PostgreSQL, retención, límites de upload y R2, monitoreo/logs.
6. No correr `createsuperuser`, seeders demo ni comandos destructivos contra servicio productivo desde build/deploy.

## Variables requeridas por código

`.env.example` es una plantilla versionada; Django no la carga automáticamente. Copiarla a `.env` local, y `beatcloud/settings.py` carga ese archivo desde la raíz. No completar credenciales reales en la plantilla. `frontend/client/.env.example` también es referencia versionada; copiar a `frontend/client/.env` para que Vite lea su configuración. `.env.qa` lo genera el script QA, es local y no se publica.

| Grupo | Variables | Requisito |
|---|---|---|
| Django | `DJANGO_SECRET_KEY` | Obligatoria; aleatoria, privada y distinta por ambiente. |
| PostgreSQL | `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Necesarias para una DB real local/servidor; configurar acceso y DB antes de migrar. |
| Entorno web | `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `FRONTEND_URL` | Necesarias para configuración adecuada del ambiente; en producción usar dominio HTTPS y DEBUG false. |
| Audio local | `FFMPEG_PATH`, `MEDIA_ROOT` | FFmpeg requerido al generar preview; `MEDIA_ROOT` puede usar default local. |
| Correo | `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, `EMAIL_TIMEOUT` | El backend console basta en local; credenciales SMTP solo si se prueba servicio real. |
| R2 | `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_UPLOADS_ENABLED` | Opcionales; todas las credenciales/bucket deben existir y `R2_UPLOADS_ENABLED=true` para habilitar el flujo. |
| Webpay | `TRANSBANK_COMMERCE_CODE`, `TRANSBANK_API_KEY`, `TRANSBANK_INTEGRATION_TYPE` | TEST y credenciales de integración para probar checkout real; LIVE no se configura en esta preparación. |
| Frontend | `VITE_API_MODE`, `VITE_API_URL`, `VITE_DJANGO_URL`, `VITE_DJANGO_PROXY_TARGET` | Variables públicas/desarrollo. API normalmente `/api`, URL Django vacía y proxy al backend local. Nunca guardar secretos `VITE_*`. |

`TRANSBANK_SHARED_SECRET` no se usa por el SDK/configuración de los flujos actuales y no está en la plantilla. `STRIPE_*` también fue retirado: Stripe no tiene integración activa en el código.

R2 usa variables de cuenta, bucket, acceso y secreto (`R2_ACCOUNT_ID`, `R2_BUCKET_NAME`, claves access/secret) y bandera `R2_UPLOADS_ENABLED`; completar solo con credenciales de Felipe y bucket privado dedicado. Webpay recibe `TRANSBANK_COMMERCE_CODE`, `TRANSBANK_API_KEY` y `TRANSBANK_INTEGRATION_TYPE=TEST|LIVE`. `TRANSBANK_SHARED_SECRET` era una variable heredada sin lectores en los flujos actuales; si su valor histórico estuvo en el archivo accidental, también debe rotarse como secreto potencialmente expuesto. Stripe no tiene flujo de pago implementado ni variables necesarias en la plantilla. Frontend conoce `VITE_API_MODE`, `VITE_DJANGO_URL` y `VITE_API_URL`; el Vite proxy de desarrollo usa `VITE_DJANGO_PROXY_TARGET`. `VITE_*` se incorpora al bundle público: no colocar secretos.

`.env.example` enumera configuración local sin credenciales. Cada plataforma debe mantener secretos en su panel, nunca commitearlos. No importar el `.env` local a Render/Vercel.

## Render + Vercel: procedimiento a validar

1. Crear PostgreSQL y Web Service Django en Render; configurar variables del servicio, región, acceso interno de DB y servicio de correo/R2/Webpay TEST. Render recomienda build command y servidor Django productivo; la documentación oficial de Render incluye PostgreSQL, static files y configuración de entorno ([guía Django](https://render.com/docs/deploy-django), [variables y secretos](https://render.com/docs/configure-environment-variables)).
2. Antes del primer deploy, agregar en el repositorio configuración de static collection/servidor productivo y confirmar dependencias. No usar `manage.py runserver` como comando productivo.
3. Definir un pre-deploy de migraciones con respaldo y revisión; no ejecutar migraciones destructivas de forma implícita.
4. Desplegar frontend Vite desde `frontend/client` con build `npm ci && npm run build`, output `dist`. Confirmar `base`/rutas y rewrite. Vercel soporta rewrites a orígenes externos para actuar como proxy ([documentación rewrites](https://vercel.com/docs/routing/rewrites)); esta arquitectura no está probada para las cookies/CSRF actuales.
5. Configurar dominios, rewrite o cliente cross-origin, cookies y CSRF. Ejecutar en navegador: login persistente, logout, CSRF, sesión, upload, media, callback y descarga; registrar Network redacted.
6. Habilitar R2/Webpay TEST/SMTP por etapas, realizar prueba acotada y revisar logs. No habilitar LIVE sin aprobación del propietario.
7. Activar backups PostgreSQL y probar recuperación en una base separada. R2 necesita política/versionado/retención definida.

Render documenta que el filesystem de servicio es efímero salvo disco persistente; R2 o disco persistente configurado son necesarios para archivos. Revisar [discos persistentes](https://render.com/docs/disks) y política de despliegue/migraciones. La propuesta no implica que haya servicios creados.

## CORS, cookies y CSRF

Primero preferir un origen visible único/proxy para `/api` y medios. Si se adopta origen cruzado: permitir exactamente el origen frontend en `CSRF_TRUSTED_ORIGINS` y CORS con credenciales; `Access-Control-Allow-Origin` no puede ser comodín; cliente debe usar `credentials: include`; configurar `SESSION_COOKIE_SAMESITE=None`, `CSRF_COOKIE_SAMESITE=None`, ambos Secure bajo HTTPS; validar `Origin`, `Referer`, dominio de cookies, `CSRF_COOKIE_DOMAIN` solo si corresponde y `X-Forwarded-Proto`. No bajar protecciones para hacer pasar QA.

## Archivos, pago y actualización

- `collectstatic` aún no está demostrado en este proyecto; servir estáticos solo tras configurar backend de static files.
- Subida R2: presign, upload, confirm/finalize, metadata y validación deben verificarse contra bucket de desarrollo. Descargas de objetos privados deben exigir ownership/purchase server-side y probar expiración.
- Webpay: usar credenciales de integración TEST, callbacks HTTPS públicos y montos/órdenes QA; probar autorización, rechazo, cancelación y callback repetido antes de cualquier entorno LIVE.
- Procedimiento de release: backup DB -> desplegar código identificado por commit -> ejecutar migraciones aprobadas -> smoke de sesión/catálogo -> prueba de permisos -> monitorear -> rollback según backup/commit. No se ha ensayado restauración ni rollback en un deployment real.

## Verificación y referencias

No hay health endpoint dedicado confirmado. Para QA local se usan `GET /api/session/`, `GET /api/catalogo/` y frontend HTTP, sin inferir salud de DB/servicios externos por un status 200. Fuentes de configuración: `beatcloud/settings.py`, `beatcloud/urls.py`, `app/r2_presign.py`, `app/r2_upload_http.py`, `app/webpay_reconciliation.py`, `frontend/client/src/api/django.service.ts`, `frontend/client/vite.config.ts`.
