# BeatsCloud

Repositorio unificado del sprint 2. El frontend React/Vite está en `client/` y el backend Django en `server/`. Este repositorio parte del historial de `felipe-urtubia/BeatsCloud`; los repositorios de origen se conservan como historial y no son la ubicación de desarrollo activa.

## Estado actual

- Django sirve la API JSON que consume `client/src/api/`, además de las vistas HTML históricas.
- La autenticación implementada usa sesión Django, cookie y protección CSRF (decisión DDPB-66: sin JWT ni DRF).
- `VITE_API_MODE=real` conecta con Django; `VITE_API_MODE=mock` mantiene la demo local. `hybrid` se acepta como alias temporal de `real`. La validación del flujo de compra y descarga con backend real sigue pendiente.
- Webpay requiere credenciales de integración propias para probar un pago. No se incluyen credenciales en el repositorio.

## Requisitos

Python 3.12+, Node.js y npm. SQLite se usa por defecto; PostgreSQL se configura con las variables `DB_*`. FFmpeg solo se necesita para generar previews de audio.

## Ejecutar localmente

### Backend

```bash
cd server
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env                   # Windows: Copy-Item .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Coloca la clave generada en `DJANGO_SECRET_KEY` de `server/.env`. El ejemplo queda con SQLite y correo de consola para desarrollo; el enlace de activación se imprime en la terminal de Django. Define `DB_*` para PostgreSQL y SMTP cuando necesites correo real. Webpay requiere credenciales públicas oficiales de integración en el `.env` local. Después:

```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

### Frontend

En otra terminal:

```bash
cd client
npm ci
cp .env.example .env
npm run dev
```

Abre <http://localhost:3000>. `client/vite.config.ts` envía `/api` y `/media` a `127.0.0.1:8000`. Usa `VITE_API_MODE=mock` para una demo sin backend; el modo integrado predeterminado es `real`. `VITE_DJANGO_URL` se deja vacío para usar el proxy local.

## Verificaciones

Desde `server/`: `python manage.py test app`.

Desde `client/`: `npx tsc -b` y `npx vite build` (o `npm run build`, que ejecuta ambos). El resultado y la fecha se registran en [Evidencia de verificación](Fase%202/Evidencias%20Proyecto/Evidencias%20de%20documentación/VERIFICACION_SPRINT_2.md).

El registro histórico de cambios está en [Registro de cambios](Fase%202/Evidencias%20Proyecto/Evidencias%20de%20documentación/REGISTRO_CAMBIOS_BEATSCLOUD.md); para los pasos vigentes de instalación, usa las instrucciones de este README.

## Variables y secretos

Los archivos `server/.env` y `client/.env` son locales e ignorados por Git. Los ejemplos `server/.env.example` y `client/.env.example` contienen solo nombres y valores vacíos/de desarrollo. Nunca coloques secretos de Django, base de datos, correo, Stripe o Transbank en el repositorio ni en variables `VITE_*`. La revisión encontró un `.env` embebido en el historial Git; se retiró el archivo del árbol de trabajo, pero el saneamiento de commits anteriores sigue pendiente. Rota esas credenciales antes de usarlas de nuevo.

## Integración frontend/backend

Contrato de endpoints, autenticación y diferencias conocidas: [docs/INTEGRACION_BACKEND.md](docs/INTEGRACION_BACKEND.md).
