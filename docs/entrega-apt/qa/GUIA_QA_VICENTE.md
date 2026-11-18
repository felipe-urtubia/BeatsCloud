# Guía de QA local para Vicente

Esta guía prepara un ambiente aislado para pruebas funcionales. Está escrita y parcialmente verificada en Fedora/Linux con Docker Compose, Python 3.14, Django 6.0.6, Node 22 y npm 10. No se afirma compatibilidad con Windows/macOS. No usar cuentas, bases, servicios ni credenciales de producción.

`.env.example` es solo plantilla de la instalación manual; el entorno de esta guía usa el archivo local `.env.qa`, que `scripts/qa/setup.sh` crea y que `.gitignore` excluye. No copiar `.env` de otra persona ni guardar `.env.qa` en el repositorio.

## 1. Obtener la versión saneada

Solicitar al equipo la copia shallow de código `beatscloud-main-source-shallow.bundle` y verificar con Felipe/Ismael que corresponde al corte acordado. No contiene historial completo y no reemplaza la trazabilidad Git. El bundle no se publica por GitHub mientras el remoto conserve historial sensible.

```bash
git bundle verify /ruta/recibida/beatscloud-main-source-shallow.bundle
git clone /ruta/recibida/beatscloud-main-source-shallow.bundle BeatsCloud-QA
cd BeatsCloud-QA
git switch main
git status --short --branch
```

La versión debe indicar únicamente `main`. Si la verificación del bundle falla o no incluye `refs/heads/main`, detenerse y pedir una nueva copia. No hacer fetch del remoto antiguo.

## 2. Requisitos

- Linux con Bash, Git, `curl`, `realpath` y `ps`.
- Python 3.12 o posterior compatible con dependencias; corte probado en 3.14.10.
- Node.js 22/npm 10; FFmpeg en `PATH`.
- Docker Engine con Compose v2, o Podman rootless con Compose. No usar `sudo`.
- Puertos locales libres: PostgreSQL 55433, Django 8010 y Vite 3010.
- Espacio para PostgreSQL de QA y hasta 300 clips WAV, previews MP3 y portadas. El valor predeterminado es 120 clips.
- Firefox actualizado para los casos manuales de navegador; no hay Playwright/E2E automatizado integrado.

## 3. Preparar entorno, DB y datos

Desde la raíz del repositorio:

```bash
scripts/qa/setup.sh
```

El script crea `.env.qa` con modo `0600`, genera una clave local aleatoria, arranca solo el servicio `db` con un proyecto Compose único, aplica migraciones y ejecuta los seeders. La base exacta es `beatscloud_qa_local`, publicada en `127.0.0.1:55433`; el volumen Compose persiste. R2 queda desactivado, Webpay queda en `TEST` sin claves y el correo se imprime en la consola de Django.

Los datos no usan identidad real: 5 pistas demo, 120 pistas sintéticas reproducibles, 12 perfiles ficticios y cuentas `qa-*`. Los WAV/MP3/PNG quedan bajo `media/qa/`, excluido de Git. Los 120 tracks sintéticos tienen WAV, preview y portada generados localmente; no son beats comerciales. El usuario `qa-comprador-carrito` tiene dos artículos pendientes de checkout.

El comando es repetible:

```bash
set -a; source .env.qa; set +a
.venv/bin/python manage.py generate_qa_catalog --count 120 --seed 20261118
```

Cuenta se limita de 1 a 300; la misma semilla genera títulos/metadatos/audio deterministas y los marcadores impiden duplicados. Para regenerar únicamente catálogo sintético, usar `--reset` solo después de parar Django/Vite y revisar que no existan ventas/historial; si hay historia de compra, el comando se bloquea. Para reconstruir todo el entorno QA, `scripts/qa/reset.sh` pide escribir exactamente `RESET-QA`, limita DB/media mediante nombre, configuración y sentinel, retiene volumen y rota contraseñas QA. No usarlo si hay resultados que conservar.

Verificar datos sin exponer credenciales:

```bash
set -a; source .env.qa; set +a
.venv/bin/python manage.py shell -c "from app.models import Track; q=Track.objects.filter(original_filename__startswith='qa-catalog:v1:'); print('sintéticas',q.count(),'listas',q.filter(media_status='ready').exclude(track='').exclude(preview='').count())"
```

El catálogo API debe reportar 125 pistas (120 sintéticas + 5 demo), nueve géneros y 21 páginas con seis filas por página. Las opciones disponibles para probar en el cliente se leen del catálogo generado: género, búsqueda por título/productor, recurso, clave, mood, BPM, stems, gratis/pago y precio. La API backend solo implementa su subconjunto; BPM/clave/mood/subgénero se filtran en cliente. No hay filtro de duración confirmado.

Las cuentas se usan exclusivamente en la DB QA aislada. Al ejecutar setup por primera vez, las contraseñas temporales se imprimen una vez; guárdalas antes de cerrar la terminal. No copiar las contraseñas mostradas en este equipo a capturas ni al registro. Si setup encuentra cuentas previas, no revela ni cambia sus claves; rótalas explícitamente como se explica abajo.

## 4. Cuentas y roles

El comando `prepare_qa_users` crea, una sola vez, cuentas locales para comprador (`qa-comprador`), comprador con carrito (`qa-comprador-carrito`), productor (`qa-productor`) y administrador (`qa-admin`). Contraseñas temporales aleatorias se muestran únicamente cuando se crean o con `--rotate-passwords`; deben conservarse en un gestor privado y no registrarse en capturas ni Git. Si se pierden, ejecutar tras verificar el entorno QA:

```bash
set -a; source .env.qa; set +a
.venv/bin/python manage.py prepare_qa_users --rotate-passwords
```

La cuenta anónima no requiere login. No utilizar el productor de demo para pruebas que modifiquen registros; preferir `qa-productor`. La regeneración de cuentas no revela ni cambia contraseñas existentes si no se solicita rotación.

## 5. Iniciar y comprobar

```bash
scripts/qa/start.sh
```

Este comando valida la configuración, vuelve a comprobar DB y seed idempotente, y se niega a tomar puertos ocupados. Deja los procesos vinculados a esta copia del repositorio y escribe logs/PID bajo `/tmp/<proyecto-qa>-runtime/`.

- Frontend: <http://127.0.0.1:3010/>
- Backend/API: <http://127.0.0.1:8010/>
- Catálogo: <http://127.0.0.1:8010/api/catalogo/>
- Sesión anónima: <http://127.0.0.1:8010/api/session/>

No publicar esos servicios en una red externa. Navegar el frontend usando la URL de Vite; el proxy manda `/api` y `/media` al backend.

## 6. Ejecutar validación automatizada

Con la DB levantada, ejecutar desde raíz:

```bash
scripts/qa/verify.sh
```

El script comprueba PostgreSQL, `manage.py check`, migraciones sin aplicarlas, suite Django, `npm test`, TypeScript (`npm run lint`), build y HTTP frontend/API/catálogo. Salida exit code 0 es una verificación automatizada de ese commit/entorno; no aprueba los casos manuales ni proveedores externos. También puede ejecutarse una suite por separado:

```bash
set -a; source .env.qa; set +a
.venv/bin/python manage.py test
(cd frontend/client && npm test && npm run lint && npm run build)
```

En la matriz, registrar el resultado observado, commit, hora y salida relevante. Si falla, conservar el fallo; no desactivar CSRF, pruebas o validaciones para obtener un exit code 0.

## 7. Recorrido manual desde Firefox

1. Iniciar con `scripts/qa/start.sh` y abrir <http://127.0.0.1:3010/> en Firefox.
2. En Network confirmar `/api/session/` y `/api/catalogo/` pasan por el proxy y responden. No exportar cookies ni headers de autorización.
3. Abrir catálogo, recorrer páginas, buscar un título y un usuario ficticio `qa-cat-prod-*`, cambiar género, precio, BPM y orden. Probar búsqueda vacía.
4. Abrir track, perfil productor y portada; verificar los metadatos del registro. Anotar el ID del track, no tratarlo como estable después de reset.
5. Reproducir preview desde el control React: activar por click, escuchar, pausar, reanudar, buscar posición y variar volumen. Revisar consola por `AudioContext`, CORS o `NotAllowedError`. Un endpoint 200 sin escucha no es aprobado.
6. Probar login/logout con comprador/productor de QA y verificar sesión luego de recargar. Revisar `X-CSRFToken` en mutaciones, ocultando su valor en evidencia.
7. Como anónimo, solicitar audio completo/descarga de una pista no comprada: rechazo esperado. Las rutas de preview pública no deben confundirse con full/download.
8. Probar productor, carrito y permisos según matriz. Compra autorizada y acceso posterior requieren transacción de sandbox autorizada por Felipe; no simular compra manualmente en DB.
9. Anotar resultado por ID de caso, hora y commit en el registro. Capturas deben excluir contraseñas, emails reales, cookies, tokens y URLs firmadas.

Parar:

```bash
scripts/qa/stop.sh
```

El script valida PID, comando, cwd antes de detener Django/Vite y detiene únicamente el contenedor DB del proyecto identificado; conserva volumen y medios. Si su PID no corresponde con el proceso esperado, no fuerza terminación: inspeccionar y resolver manualmente. `docker compose ps` o `podman ps` son lectura. Para volver a iniciar, repetir `scripts/qa/start.sh`; para reset completo usar el procedimiento con confirmación anterior.

## 8. Orden de pruebas sugerido

1. BUILD-01: versión, setup, puertos, frontend, API, conteo.
2. CAT-01–07: catálogo, navegación, búsqueda, filtros, orden y paginación.
3. AUTH-01–04 y PROF-01–02: cuentas, CSRF, roles, perfiles, recuperación.
4. AUDIO-01–05 y PROD-01–03: preview/UI, carga, edición, permisos y descarga.
5. CART-01–02, BUY-01, LIC-01 y PAY-01–02: carrito e integración de pago solo en entorno TEST autorizado.
6. SOCIAL-01, SUB-01 y regresión según la matriz completa.

La matriz completa, roles, precondiciones, resultados esperados y límites está en [matriz_qa_funcional.md](matriz_qa_funcional.md). Registra solo lo ejecutado en [REGISTRO_EJECUCION_VICENTE.md](REGISTRO_EJECUCION_VICENTE.md). Cada defecto debe tener versión/commit, entorno, pasos, frecuencia, resultado esperado/actual y evidencia; plantilla en el registro.

## 9. Evidencias y diagnóstico

- Capturar vista/UI, URL y hora; para API guardar método, path, status y cuerpo redactado. No guardar cookies `sessionid`/CSRF, passwords, tokens Webpay, datos personales ni `.env.qa`.
- Adjuntar consola del navegador y Network solo con cabeceras sensibles ocultas.
- Ver logs en `/tmp/<proyecto-qa>-runtime/django.log` y `vite.log`; revisar que no se copien secretos.
- Para errores de API: verificar primero `curl` a `/api/session/` y `/api/catalogo/`, después proxy Vite, luego logs Django.
- 401/403 en audio completo para anónimo puede ser resultado esperado. Un preview HTTP 200 no demuestra que el navegador lo reproduzca.
- Un fallo de CSRF puede ser origen/puerto fuera de `DJANGO_CSRF_TRUSTED_ORIGINS`. Un fallo de Webpay/R2 externo no prueba defecto funcional cuando las credenciales están vacías.
- Evidencia técnica saneada puede organizarse por commit/caso bajo `docs/entrega-apt/qa/evidencias/`; antes de versionar, revisar metadatos y eliminar secretos, datos personales, tokens, URLs firmadas y credenciales visibles.
- Para defectos, completar en el registro el reporte con título, prioridad/severidad, entorno, versión, precondiciones, pasos exactos, esperado/actual, frecuencia, evidencia y estado. No asignar responsable/Jira sin confirmación del equipo.

## 10. Casos que requieren a Felipe

R2 real (bucket de desarrollo aislado, credenciales y autorización de upload) y Webpay Plus TEST (commerce/API credentials de pruebas y flujo de aprobación/rechazo) requieren aportes de Felipe. No colocar secretos en archivos, incidencias o capturas; configurarlos solo en el gestor privado de la plataforma local autorizada. La QA local preparada no usa esas credenciales y no afirma pruebas externas. SMTP real también requiere cuenta de pruebas; localmente enlaces de activación/reset quedan en consola.

## Límites actuales

No se ha demostrado un recorrido de navegador completo por Vicente, un pago Webpay real, operación Cloudflare R2 real ni despliegue. Playwright/E2E no está incorporado. Las pruebas Django usan DB temporal y el catálogo manual usa la DB aislada local.
