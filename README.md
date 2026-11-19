# BeatsCloud

BeatsCloud es un marketplace académico de instrumentales para productores y artistas. Los productores publican pistas; los artistas pueden explorar el catálogo, escuchar previews y comprar. El producto combina una SPA React con un backend Django y persistencia PostgreSQL mediante migraciones Django. Las sesiones Django y CSRF protegen la autenticación; Webpay Plus gestiona el flujo de pago y el acceso a archivos completos está sujeto a permisos de propietario o compra.

**Corte técnico:** 19-11-2026 · **Fuente de verdad del código:** rama `main` de este repositorio. El commit exacto del snapshot académico y sus hashes están en el repositorio de entrega.

## Tecnologías y alcance comprobado

- Frontend: React 19, TypeScript, Vite 6 y Tailwind CSS en `frontend/client/`.
- Backend: Python y Django 6; API JSON implementada con vistas Django propias en `app/api_shim.py`. El código vigente no usa DRF ni JWT.
- Datos: PostgreSQL y migraciones Django.
- Identidad: cookies de sesión Django y protección CSRF.
- Audio: previews de 30 segundos con FFmpeg y rutas protegidas para audio completo/descargas.
- Pagos: integración Webpay Plus/Transbank. La suite usa dobles; no acredita cobros reales.
- Archivos: almacenamiento local y flujo privado Cloudflare R2 opcional. R2 está desactivado en la configuración de ejemplo.

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

El cierre QA registra **372 pruebas Django repetidas en `4569613b29e7023161149ca5e7d5fddabf6437db`**, `manage.py check`, migraciones, `build.sh` y smoke HTTP en el QA aislado. **26 pruebas frontend, TypeScript/lint y build Vite** corresponden al corte histórico `7ad7305fecdbdeff8b4f9d8c301b1f6f1c3e7dbe`; el código fuente de la SPA no cambió después. Detalle: [validación QA de cierre](docs/entrega-apt/validacion_qa_cierre_2026-11-19.md). No equivalen a E2E manual o despliegue externo.

El entorno funcional aislado y su verificación reproducible están en `scripts/qa/` y `compose.qa.yml`. Sigue [la guía QA](docs/entrega-apt/qa/GUIA_QA_VICENTE.md) y usa sus guardas de base y medios.

## Validaciones pendientes

No hay evidencia de ejecución manual en Firefox de los cuatro casos; sus procedimientos están en [guía manual](docs/entrega-apt/qa/GUIA_EJECUCION_MANUAL_ISMAEL.md). No se acreditan compra/descarga E2E, Webpay sandbox, Gmail API, Resend, R2, SMTP ni despliegue externo. El repositorio incluye `build.sh`, configuración de estáticos para Render y `frontend/client/vercel.json` con rewrites API/media/CSRF/sesión hacia `beatscloud.onrender.com` y fallback SPA. La carpeta del frontend debe configurarse como Root Directory de Vercel para aplicar ese archivo; el panel de despliegue no se verificó. `build.sh`, `collectstatic` y migraciones se verificaron localmente en DB QA; no hay evidencia de despliegue Render/Vercel ni de sesión/CSRF a través del rewrite. La matriz y el registro QA indican el alcance pendiente; no se deben inferir resultados de tests con dobles.

## Documentación

- [Índice técnico del corte](docs/entrega-apt/README.md)
- [Arquitectura y endpoints](docs/entrega-apt/arquitectura.md)
- [Modelo de datos y almacenamiento](docs/entrega-apt/modelo_datos_y_almacenamiento.md)
- [Validación automatizada y manual](docs/entrega-apt/validacion_qa_2026-11-18.md)
- [Guía operativa de integraciones](docs/entrega-apt/operacion/GUIA_FELIPE_GRABACION.md)
- [Guía, matriz y registro QA](docs/entrega-apt/qa/GUIA_QA_VICENTE.md)
- [Procedimientos manuales de los cuatro casos](docs/entrega-apt/qa/GUIA_EJECUCION_MANUAL_ISMAEL.md)
- [Registro de ejecución manual](docs/entrega-apt/qa/REGISTRO_EJECUCION_VICENTE.md)
- [Trazabilidad técnica de contribuciones](docs/entrega-apt/trazabilidad_tecnica.md)
- [Entrega académica y evidencias](https://github.com/yaeaelo/2026_2_MA_CAPSTONE_005D_GRUPO_4)
