# BeatsCloud

BeatsCloud es un marketplace académico de instrumentales para productores y artistas. Los productores publican pistas; los artistas pueden explorar el catálogo, escuchar previews y comprar. El producto combina una SPA React con un backend Django y persistencia PostgreSQL mediante migraciones Django. Las sesiones Django y CSRF protegen la autenticación; Webpay Plus gestiona el flujo de pago y el acceso a archivos completos está sujeto a permisos de propietario o compra.

**Corte técnico:** 19-11-2026 · **Fuente de verdad del código:** rama `main` de este repositorio. El commit exacto del snapshot académico y sus hashes están en el repositorio de entrega.

## Tecnologías y alcance comprobado

- Frontend: React 19, TypeScript, Vite 6 y Tailwind CSS en `frontend/client/`.
- Backend: Python y Django 6; API JSON implementada con vistas Django propias en `app/api_shim.py`. El código vigente no usa DRF ni JWT.
- Datos: PostgreSQL y migraciones Django.
- Identidad: cookies de sesión Django y protección CSRF.
- Audio: previews MP3 de hasta 30 segundos con FFmpeg, almacenamiento persistente en R2 y rutas protegidas para audio completo y descargas.
- Pagos: integración Webpay Plus/Transbank. La suite usa dobles; no acredita cobros reales.
- Archivos: almacenamiento local y flujo privado Cloudflare R2 opcional. R2 está desactivado en la configuración de ejemplo.
- Cuentas: registro y activación, recuperación de contraseña y eliminación de cuenta. El equipo confirmó pruebas funcionales de estos flujos con el proveedor de correo configurado en su entorno; esta confirmación de equipo se distingue de la ejecución automatizada local, que usa backend de correo en memoria/consola.

## Requisitos

- Python 3.12 o superior (corte probado con Python 3.14.10).
- PostgreSQL 14 o superior.
- Node.js 20 o superior y npm.
- FFmpeg disponible en `PATH` o configurado con `FFMPEG_PATH`.
- Git.

## Instalación local

```bash
git clone --branch main https://github.com/felipe-urtubia/BeatsCloud.git
cd BeatsCloud
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
cp frontend/client/.env.example frontend/client/.env
```

`.env.example` y `frontend/client/.env.example` son plantillas versionadas. Cada integrante crea su propio `.env` privado y configura su PostgreSQL local. No se deben subir `.env`, `.env.qa`, credenciales ni valores privados a Git. No pongas secretos en variables `VITE_*`: se incluyen en el bundle del navegador.

En PostgreSQL, crea una base local con `createdb -U postgres beatscloud_demo_local` (o con el usuario configurado) y asegúrate de que ese usuario tenga acceso. Completa `DJANGO_SECRET_KEY`, `DB_USER` y `DB_PASSWORD` en `.env`; ajusta `DB_NAME`, host y puerto si usas otros valores. Después:

```bash
python manage.py check
python manage.py migrate
python manage.py prepare_demo_catalog
python manage.py runserver 127.0.0.1:8000
```

En otra terminal:

```bash
cd frontend/client
npm ci
npm run dev
```

Vite sirve la SPA en `http://localhost:3000/` y reenvía `/api` y `/media` al backend local. Para detener servicios, usa `Ctrl+C` en cada terminal.

## Pruebas

Pruebas automatizadas del backend:

```bash
python manage.py test
```

Pruebas y comprobaciones automatizadas del frontend:

```bash
cd frontend/client
npm test
npm run lint
npm run build
```

En una ejecución local aislada sobre `ee981a750904b4263b20be2f91e3568c0e1699ea` se aprobaron **372 pruebas Django y 26 pruebas frontend**, `manage.py check`, revisión de migraciones, TypeScript/lint y build Vite. El registro conserva por separado las verificaciones `build.sh` y smoke HTTP de `4569613b29e7023161149ca5e7d5fddabf6437db`. Estas comprobaciones automatizadas no equivalen a una transacción Webpay, validación de bucket R2, recorrido manual E2E ni despliegue externo. Detalle: [validación QA de cierre](docs/entrega-apt/validacion_qa_cierre_2026-11-19.md).

El entorno funcional aislado y sus guardas reproducibles están en `scripts/qa/` y `compose.qa.yml`. La ejecución y sus límites constan en el [registro QA de cierre](docs/entrega-apt/validacion_qa_cierre_2026-11-19.md).

La validación local de los cambios de previews registró **405 pruebas Django aprobadas**, manage.py check correcto, ausencia de cambios pendientes de migración y build Vite exitoso.

## Validaciones pendientes

El despliegue de BeatsCloud se encuentra disponible en Render y Vercel. Se comprobó la conexión a PostgreSQL de producción y la existencia de tres audios originales en Cloudflare R2. Las tres previews fueron recuperadas y verificadas en el bucket privado.

Los cambios de entrega de previews mediante URL firmada fueron publicados en el commit 7cec7e1 y desplegados en Render. Se verificó la reproducción con y sin sesión, la subida de una nueva pista y una auditoría final de cuatro previews válidas en R2.

El 22-11-2026 se verificó el flujo E2E de compra y descarga mediante Webpay TEST, incluyendo pagos aprobados y rechazados, persistencia en PostgreSQL y permisos de acceso al audio original. La suite frontend alcanzó 33 pruebas aprobadas. No se han acreditado cobros reales ni pruebas de carga o usabilidad con usuarios externos.

## Documentación

- [Índice técnico](docs/entrega-apt/README.md)
- [Arquitectura y endpoints](docs/entrega-apt/arquitectura.md)
- [Modelo de datos y almacenamiento](docs/entrega-apt/modelo_datos_y_almacenamiento.md)
- [Configuración e integraciones](docs/entrega-apt/despliegue_y_configuracion.md)
- [Plan de pruebas y QA de cierre](docs/entrega-apt/plan_pruebas.md) · [resultados](docs/entrega-apt/validacion_qa_cierre_2026-11-19.md)
- [Riesgos técnicos](docs/entrega-apt/plan_riesgos.md) · [visión y alcance](docs/entrega-apt/vision_producto.md)
- [Índice de QA web y evidencias](docs/qa/README.md)
