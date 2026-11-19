# BeatsCloud

BeatsCloud es un marketplace académico de instrumentales para productores y artistas. Los productores publican pistas; los artistas pueden explorar el catálogo, escuchar previews y comprar. El producto combina una SPA React con un backend Django y persistencia PostgreSQL mediante migraciones Django. Las sesiones Django y CSRF protegen la autenticación; Webpay Plus gestiona el flujo de pago y el acceso a archivos completos está sujeto a permisos de propietario o compra.

**Corte técnico de entrega:** 18-11-2026 · **Fuente de código:** rama `main`, commit `f017627fec99b2628e7753d3626ed33367836c5c`.

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

Al corte 18-11-2026, el registro QA documenta 372 pruebas Django, 26 pruebas frontend, TypeScript/lint, build y comprobaciones HTTP locales aprobadas. Son pruebas automatizadas y smoke checks; no equivalen a un recorrido manual E2E.

El entorno funcional aislado y su verificación reproducible están en `scripts/qa/` y `compose.qa.yml`. Sigue [la guía QA](docs/entrega-apt/qa/GUIA_QA_VICENTE.md) y usa sus guardas de base y medios.

## Validaciones pendientes

No hay evidencia del corte de una navegación manual completa en Firefox, compra y descarga E2E, transacción real Webpay TEST, conexión real R2, SMTP real ni despliegue externo. La matriz y el registro QA indican el alcance pendiente; no se deben inferir resultados de tests con dobles.

## Documentación

- [Índice técnico del corte](docs/entrega-apt/README.md)
- [Arquitectura y endpoints](docs/entrega-apt/arquitectura.md)
- [Modelo de datos y almacenamiento](docs/entrega-apt/modelo_datos_y_almacenamiento.md)
- [Validación automatizada y manual](docs/entrega-apt/validacion_qa_2026-11-18.md)
- [Guía operativa de integraciones](docs/entrega-apt/operacion/GUIA_FELIPE_GRABACION.md)
- [Guía, matriz y registro QA](docs/entrega-apt/qa/GUIA_QA_VICENTE.md)
- [Trazabilidad técnica de contribuciones](docs/entrega-apt/trazabilidad_tecnica.md)
- [Entrega académica y evidencias](https://github.com/yaeaelo/2026_2_MA_CAPSTONE_005D_GRUPO_4)
