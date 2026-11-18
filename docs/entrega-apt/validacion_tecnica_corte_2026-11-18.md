# Registro de validación técnica — 18-11-2026

Registro reproducible del entorno local de demostración. Los resultados corresponden al 18-11-2026 y al código candidato integrado antes de la reescritura de historia; no son una certificación de despliegue productivo.

## Entorno

- Fedora, Python 3.14 en `.venv`, Django 6.0.6; Node.js 22/npm; FFmpeg 8.1.3.
- PostgreSQL local aislado en `127.0.0.1:55432`, base `beatscloud_demo_20261118`, con datos de demostración. No se usó una base preexistente.
- Vite en `127.0.0.1:3000`, proxy `/api` y `/media` a Django `127.0.0.1:8000`.
- `.env` existe. Los indicadores de presencia de variables R2 se revisaron sin mostrar sus valores; las credenciales/activación requeridas no estaban configuradas. Transbank declara tipo `TEST`.

## Ejecuciones automatizadas

| ID | Procedimiento | Resultado observado | Evidencia reproducible / límites |
|---|---|---|---|
| V-01 | `.venv/bin/python -m pip check` | Sin requisitos rotos. | Salida: `No broken requirements found.` |
| V-02 | `.venv/bin/python manage.py check` | Sin problemas del system check. | Comando local; depende del entorno Django configurado. |
| V-03 | `.venv/bin/python manage.py makemigrations --check --dry-run` | Sin cambios de modelo pendientes. | Salida: `No changes detected`. No modifica el esquema. |
| V-04 | `.venv/bin/python manage.py test` con `DB_NAME=beatscloud_demo_20261118`, usuario `postgres`, host socket local y puerto `55432` | 367 pruebas, `OK`, 141.969 s; system check limpio. | Suite Django completa en base temporal `test_*` del runner dentro del cluster aislado; no modificó la base demo persistente. Transbank/R2 usan mocks en sus suites. |
| V-05 | `cd frontend/client && npm test` | 26 tests aprobados en 3 archivos de prueba. | Tests Node del frontend; no ejercitan navegador real. |
| V-06 | `cd frontend/client && npm run lint` | Aprobado. | Script definido como `tsc -b`; cubre chequeo TypeScript, no reglas ESLint. |
| V-07 | `cd frontend/client && npm run build` | Aprobado; TypeScript y Vite generaron build de producción. | No prueba interacción real ni servicios externos. |

La comprobación del 18-11 se repitió después de endurecer `beatcloud/settings.py`: `DJANGO_SECRET_KEY` es obligatoria, `DEBUG` queda desactivado por defecto y `DB_PASSWORD` ya no tiene una contraseña por defecto. `manage.py check`, la verificación de migraciones y las 367 pruebas aprobaron con esa configuración.

## Comprobación HTTP local

El servidor Django y Vite estaban en ejecución. Las peticiones se hicieron contra `127.0.0.1` y no alteraron datos salvo el login de sesión de prueba.

| ID | Petición | Resultado observado | Alcance |
|---|---|---|---|
| H-01 | `GET /` en puerto 3000 | HTTP 200, HTML de Vite. | Disponibilidad HTTP de frontend. |
| H-02 | `GET /api/catalogo/` | HTTP 200; cinco tracks, precios y datos visibles; el serializador no expuso URL del original. | API real local y base demo. |
| H-03 | `GET /api/session/` sin sesión | HTTP 200; sesión no autenticada. | Endpoint de sesión. |
| H-04 | `GET /api/track/1/preview/` | HTTP 200, `audio/mpeg`, 48,684 bytes leídos. | Respuesta de preview local; no acredita percepción de audio en React/navegador. |
| H-05 | Anónimo: `/reproducir/` y `/descargar/` | HTTP 403 para ambos. | Control de autorización de archivo completo. |
| H-06 | Login con CSRF como productor demo; sesión y entrega propia | Login HTTP 200; sesión del productor; stream 200 `audio/x-wav`; descarga 200 con `Content-Disposition` de adjunto. | Flujo local autenticado de propietario; no representa compra de otro usuario. |

## Datos preparados

El comando `python manage.py prepare_demo_catalog` se ejecutó dos veces contra la base aislada. Resultado: nueve géneros, un productor demo, cinco tracks con audio original local, preview MP3 y portada. La segunda ejecución no duplicó tracks ni cambió la contraseña. Precios CLP: 7.500, 9.000, 12.000, 14.000 y 16.500. Archivos locales ignorados por Git.

## Defectos, correcciones y pendientes

- Se añadió el comando idempotente y restringido a base local `beatscloud_demo_*` para poblar datos reproducibles; no crea tracks sin archivos reproducibles.
- Se eliminó de la versión de trabajo `agregar.html` tras verificar solo metadatos del archivo que era un ZIP cuyo miembro era `.env`. No se extrajo ni mostró su contenido. El blob sensible permanece en historial Git remoto/local anterior; **la publicación requiere respuesta de seguridad y decisión de saneamiento histórico**.
- Pruebas pendientes: reproducción efectiva en Firefox/React, flujo de compra como usuario distinto, autorización post-compra, prueba real en ambiente de Transbank TEST, configuración y carga/descarga real R2, pruebas de rendimiento WAV/stems y validación manual de flujo completo.
- No hay evidencia de Jira accesible en este entorno; no se asignan estados actuales de incidencias.

## Reproducción

Con `.env` configurado para una base desechable/local y PostgreSQL activo:

```bash
.venv/bin/python -m pip check
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py test
cd frontend/client
npm test
npm run lint
npm run build
```

Para revisar HTTP, iniciar Django y Vite conforme a [inicio_proyecto.md](inicio_proyecto.md) y consultar las rutas `/`, `/api/catalogo/`, `/api/session/` y `/api/track/<id>/preview/`. La autorización se debe validar también con cuentas separadas y no inferirse de una respuesta 200 aislada.
