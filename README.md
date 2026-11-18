# BeatsCloud

Marketplace académico de instrumentales para artistas y productores. La aplicación combina una SPA React/TypeScript con API y backend Django. La única rama compartida de trabajo es `main`.

## Stack

- Python 3.14.10 / Django 6.0.6; dependencias Python en `requirements.txt`.
- PostgreSQL; el entorno aislado QA usa PostgreSQL 16 mediante Docker Compose.
- React 19, TypeScript, Vite 6 y Tailwind CSS 4 en `frontend/client/`.
- FFmpeg para generar previews; almacenamiento local o Cloudflare R2 privado opcional.
- Webpay Plus mediante `transbank-sdk`; pruebas automatizadas usan dobles. No se afirma una transacción externa validada.

## Obtener la versión correcta

Clona la rama oficial:

```bash
git clone --branch main https://github.com/felipe-urtubia/BeatsCloud.git BeatsCloud
cd BeatsCloud
```

## Configuración local de desarrollo

`.env.example` y `frontend/client/.env.example` son **plantillas versionadas**, no archivos cargados automáticamente ni credenciales de Felipe. Cada persona debe crear sus propios archivos locales:

```bash
cp .env.example .env
cp frontend/client/.env.example frontend/client/.env
```

Completa `.env` con clave Django y conexión a tu PostgreSQL local. Para desarrollo, el ejemplo fija `DJANGO_DEBUG=True`, DB `beatscloud_demo_local` y Webpay `TEST`; R2 queda desactivado y email usa consola. El `VITE_DJANGO_PROXY_TARGET` del ejemplo apunta a Django local en `127.0.0.1:8000`. No pongas secretos en variables `VITE_*`.

Con PostgreSQL disponible y la base local creada:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python manage.py check
python manage.py migrate
python manage.py prepare_demo_catalog
```

En otra terminal:

```bash
cd frontend/client
npm ci
npm run dev
```

Frontend: <http://localhost:3000/>. Backend: <http://127.0.0.1:8000/>. La configuración detallada de proveedores y requisitos pendientes está en [configuración de despliegue](docs/entrega-apt/despliegue_y_configuracion.md).

## Preparación de QA

En Fedora/Linux, con Docker Compose v2 o Podman Compose, Python, Node y FFmpeg:

```bash
scripts/qa/setup.sh
scripts/qa/start.sh
scripts/qa/verify.sh
```

Frontend QA: <http://127.0.0.1:3010/>. La guía incluye cuentas, catálogo sintético, pasos de Firefox, ejecución y reinicio seguro: [Guía de Vicente](docs/entrega-apt/qa/GUIA_QA_VICENTE.md). Detener con `scripts/qa/stop.sh`; el reset de QA pide confirmación y solo afecta DB/media identificadas de QA.

## Documentación

- [Índice técnico APT](docs/entrega-apt/README.md)
- [Guía de Felipe: grabación y configuración externa](docs/entrega-apt/operacion/GUIA_FELIPE_GRABACION.md)
- [Guía de Vicente: QA funcional](docs/entrega-apt/qa/GUIA_QA_VICENTE.md)
- [Matriz de casos QA](docs/entrega-apt/qa/matriz_qa_funcional.md)
- [Registro y reporte de defectos](docs/entrega-apt/qa/REGISTRO_EJECUCION_VICENTE.md)
- [Arquitectura](docs/entrega-apt/arquitectura.md)
- [Modelo de datos y almacenamiento](docs/entrega-apt/modelo_datos_y_almacenamiento.md)
- [Validación QA del 18-11-2026](docs/entrega-apt/validacion_qa_2026-11-18.md)
- [Trazabilidad técnica](docs/entrega-apt/trazabilidad_tecnica.md)

La verificación local automatizada aprobó 372 pruebas Django, 26 pruebas frontend, TypeScript, build y smoke HTTP. Navegación Firefox, R2 real, SMTP real, Webpay real y despliegue siguen pendientes de evidencia.
