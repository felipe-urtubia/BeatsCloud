# BeatsCloud

BeatsCloud es un marketplace académico de instrumentales. Productores pueden publicar pistas; artistas pueden descubrirlas, escuchar previews y gestionar compras. La rama `main` de este repositorio es la fuente de verdad del producto.

## Tecnologías y arquitectura

- **Frontend:** React 19, TypeScript, Vite 6 y Tailwind CSS (`frontend/client/`).
- **Backend:** Python 3.12+ y Django 6 (`app/`, `beatcloud/`). La API JSON usa vistas Django propias.
- **Persistencia:** PostgreSQL y migraciones Django.
- **Sesión:** cookies de Django y protección CSRF.
- **Pagos:** Webpay Plus/Transbank. Las pruebas locales usan dobles o el ambiente TEST; no se deben realizar cobros reales durante QA.
- **Audio y archivos:** previews preparados con FFmpeg; almacenamiento local y Cloudflare R2 privado opcional.

El navegador carga la SPA de Vite o el build publicado en Vercel. Django entrega la API, procesa sesiones y verifica permisos de compra o propiedad antes de servir audio completo. PostgreSQL conserva cuentas, pistas, compras y transacciones. R2 se habilita solo en entornos configurados para almacenamiento externo.

## Estructura

- `frontend/client/src/`: aplicación React, servicios HTTP, navegación y pruebas frontend.
- `app/`: modelos, endpoints, integraciones, comandos de gestión y pruebas Django.
- `beatcloud/`: configuración Django, URLs y puntos de entrada ASGI/WSGI.
- `scripts/qa/`, `compose.qa.yml`: preparación y ejecución del entorno QA local aislado.
- `docs/entrega-apt/`: arquitectura y documentación técnica.

## Requisitos

- Python 3.12 o posterior.
- PostgreSQL (QA Compose usa PostgreSQL 16).
- Node.js 20 o posterior y npm.
- FFmpeg en `PATH` o definido en `FFMPEG_PATH`.
- Docker Compose v2 para el entorno QA reproducible.

## Instalación y ejecución local

```bash
git clone --branch main https://github.com/felipe-urtubia/BeatsCloud.git
cd BeatsCloud
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
cp frontend/client/.env.example frontend/client/.env
```

Configura una base PostgreSQL local y completa `.env`. Las variables principales están descritas en la plantilla: `DJANGO_SECRET_KEY`, `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `FRONTEND_URL`, `FFMPEG_PATH`, variables de `TRANSBANK_*`, `R2_*` y `EMAIL_*`. Las credenciales de proveedores son opcionales en desarrollo; mantén Webpay en `TEST` y R2 desactivado mientras no configures un ambiente aislado. No guardes secretos en variables `VITE_*`.

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

Vite sirve la SPA en `http://localhost:3000` y reenvía `/api` y `/media` a Django local.

## Pruebas

Backend:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Frontend:

```bash
cd frontend/client
npm test
npm run lint
npm run build
```

Para instalar y operar el ambiente QA PostgreSQL aislado, usa `scripts/qa/setup.sh`, `scripts/qa/start.sh`, `scripts/qa/verify.sh` y `scripts/qa/stop.sh`, o `scripts/qa/run-all.sh`. El entorno mantiene R2 apagado, correo local y Webpay TEST sin credenciales. Consulta el paquete QA del [repositorio académico](https://github.com/yaeaelo/2026_2_MA_CAPSTONE_005D_GRUPO_4/tree/main/Fase%202/Evidencias%20Proyecto/Evidencias%20de%20documentaci%C3%B3n/QA_Cierre_2026-11-25) para resultados asociados a un SHA concreto.

## Repositorio académico

Los informes, entregables y evidencias académicas están en [2026_2_MA_CAPSTONE_005D_GRUPO_4](https://github.com/yaeaelo/2026_2_MA_CAPSTONE_005D_GRUPO_4).
