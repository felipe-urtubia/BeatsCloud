# Registro de validación técnica y QA — corte 18-11-2026

Fecha de ejecución: 18-11-2026 (America/Santiago). Código base histórico `2f1c6f3`; preparación QA local registrada en `035298d`. La documentación actual se registra después como commit separado. La suite Django completa de 371 pasó antes del refuerzo final del reset; los cuatro tests del generador y los chequeos de build/HTTP se ejecutaron también sobre el código reforzado. No hubo cambios de código después de esos chequeos salvo documentación.

## Entorno

- Fedora, Python 3.14.10, Django 6.0.6, Node 22.23.1, npm 10.9.8, FFmpeg 8.1.3, Pillow 12.3.0.
- DB dedicada Docker Compose `beatscloud_qa_local` en localhost:55433; volumen de proyecto QA aislado. `MEDIA_ROOT` es `media/qa`, R2 desactivado, Webpay TEST con claves vacías, email console.
- Django `127.0.0.1:8010`; Vite `127.0.0.1:3010`; procesos verificados por sesiones de ejecución. Procesos ajenos detectados previamente en 8000/3000 no fueron terminados.
- Datos: 5 tracks demo + 120 marcados sintéticos; nueve géneros. Los 120 tienen WAV distinto, MP3 preview y PNG original generado localmente. No se generaron pagos externos ni se subió contenido a R2.
- Verificación local tras reseed: 120 SHA-256 WAV distintos; media QA ocupa aproximadamente 72 MB (no versionada).

## Resultados automatizados

| Control | Resultado observado | Alcance y limitación |
|---|---|---|
| `scripts/qa/setup.sh` | Finalizó; migraciones aplicadas, 5 demo, cuentas QA, 120 sintéticas listas | Primera ejecución en DB QA aislada. El comando se repitió desde start para verificar idempotencia de seed; no usa datos producción. |
| `bash -n scripts/qa/*.sh` | Sin errores de sintaxis | No prueba todas las condiciones de plataforma. |
| `manage.py check` | Sin issues | Configuración cargada bajo QA local. |
| `makemigrations --check --dry-run` | No changes detected | No aplica migraciones. |
| Suite Django completa inicial | 371 tests; 369 OK, 2 fallaron por CSRF `localhost:3000` ausente de los orígenes permitidos en `.env.qa` | No se ocultó ni se deshabilitó seguridad. Se ajustó solo la configuración QA local y el generador de entorno para incluir el origen de desarrollo ya usado por pruebas. |
| Repetición aislada de ambos tests afectados | 2 tests OK | `test_login_api_accepts_local_react_origin_with_csrf`, `test_account_activation_requires_csrf_for_react_origin`; tras añadir puerto legacy a la lista local CSRF. |
| Suite Django completa | 371 tests, OK; 151.373 s en verificación integrada final | Ejecutada sobre `035298d`; incluye el generador ya ajustado para reset seguro y no declarar stems/MIDI inexistentes. |
| Frontend tests | 26 tests, 26 pass, 0 fail; tres suites Node | Los tests prueban lógica aislada, no navegador. |
| Frontend lint | Inicialmente falló por `process` sin tipos Node en `vite.config.ts`; corregido con `loadEnv`; `npm run lint` posterior pasó | `lint` equivale a `tsc -b`. Sin dependencia agregada. |
| Frontend build | `npm run build` pasó; Vite transformó 1,926 módulos y generó `dist` | Confirma empaquetado; no interacción visual. `dist/` está ignorado. |
| Verificación compuesta | `scripts/qa/verify.sh` segunda ejecución terminó con exit code 0: PostgreSQL ready, check, migraciones, 371 Django, 26 frontend, lint, build y smoke HTTP | La primera ejecución había detectado el defecto TypeScript; se corrigió antes de esta ejecución. |
| Tests del generador tras refuerzo | 4 tests, OK en 10.152 s, incluyendo reset limitado/idempotencia/guard de DB/usuarios | Suite focalizada sobre `035298d`; adicional a la suite completa. |
| Reseed QA definitivo | `generate_qa_catalog --count 120 --seed 20261118 --reset`; 120 tracks, 120 ready con WAV/preview, 0 marcados con stems/MIDI | Reset tocó exclusivamente filas con marcador QA y media bajo namespace QA. IDs DB cambian al regenerar. |
| `pip check` | No broken requirements found | Dependencias instaladas; no modificación de paquetes durante la ejecución. |
| Shell/whitespace | `bash -n scripts/qa/*.sh`, `git diff --check` sin errores | Verificación estática de shell/diff. |
| HTTP smoke backend | `/api/session/` HTTP 200 (anónimo retorna null); `/api/catalogo/` HTTP 200, total 125, 21 páginas, 9 géneros | Ruta y JSON de lectura, no flujo completo. |
| HTTP smoke Vite | `/` HTTP 200 | Sirvió `index.html`; no se recorrieron controles React con navegador real. |
| Proxy Vite → Django/media | `/api/session/` vía 3010 HTTP 200; portada `/media/...png` vía proxy HTTP 200 | Confirma el enrutamiento local del proxy y acceso de lectura al archivo. |
| Preview anónimo | `/api/track/245/preview/` HTTP 200, `audio/mpeg`, 80,589 bytes; archivo reconocido MP3 ID3/MPEG | Track ID es incidental y cambia tras reset. Confirma respuesta y archivo, no audibilidad/AudioContext en Firefox. |
| Audio completo anónimo | `/api/track/245/reproducir/` HTTP 403 | Control de acceso observado para pista sintética no comprada. No prueba usuario comprador/propietario. |
| Descarga anónima | `/api/track/245/descargar/` HTTP 403 | Confirma denegación; falta compra válida y descarga autorizada. |
| Portada | `/media/tracks/qa-catalog/qa-catalog_v1_20261118_0119.png` HTTP 200, `image/png` tras el reseed final | No valida visualización/crop real en navegador. |

## Datos reproducibles

Comando ejecutado: `generate_qa_catalog --count 120 --seed 20261118`; salida reportó 120 tags, 120 con audio original y preview, 9 géneros. El endpoint retornó 125 total al incluir 5 demo. Comprobaciones del comando/test cubren audios distintos, WAV válido, metadata, preview HTTP, idempotencia, reset limitado, guard DB y roles de QA. Resultados definitivos de suite completa deben reemplazar el estado “en ejecución” arriba.

## Validación manual y externa

- **Navegador Firefox/React:** no ejecutado. Requiere Vicente; foco prioritario: `audioEngine.ts` y posible interacción `HTMLAudioElement`/`AudioContext`, búsqueda/filtros y login/CSRF.
- **Webpay TEST real:** no ejecutado; pruebas con doubles/mocks y credenciales QA vacías.
- **Cloudflare R2 real:** no ejecutado; pruebas de integración con stubs/mocks, sin credenciales ni upload a R2.
- **SMTP real:** no ejecutado; backend local console.
- **Compra completa, callback, historial y descarga posterior:** no ejecutados de extremo a extremo; suites automatizadas cubren estados/ramas aislados.
- **Despliegue Render/Vercel:** no ejecutado.

## Defecto / ajuste detectado

La configuración `.env.qa` aislada no incluía `http://localhost:3000`, aunque pruebas CSRF del backend lo declaran origen React y el Vite convencional usa 3000. Las dos pruebas devolvieron 403. Se incorporó el origen local de desarrollo a `DJANGO_CSRF_TRUSTED_ORIGINS` de configuración QA, manteniendo tokens CSRF y comprobación de origen. La repetición enfocada y la suite completa de 371 pasaron después. No se amplió el allowlist productivo ni se desactivó middleware.

La compilación TypeScript detectó referencias directas a `process` sin tipos Node, introducidas al hacer configurable el proxy Vite. Se reemplazó por `loadEnv` de Vite. Lint y build posteriores aprobaron. Al reforzar la limpieza del generador, su prueba de `--reset` detectó un nombre local ausente (`media_root`); se corrigió y se repite la suite focalizada del generador.

## Evidencia a conservar

- Resultado ejecutable: `scripts/qa/verify.sh` (actualizar tabla y adjuntar stdout/exit code redactado).
- Catálogo API, sesión y endpoints preview/full/download observados el 18-11-2026 en localhost.
- Logs locales de Django/Vite en `/tmp/beatscloud-qa-1a0b31f5-runtime/`; revisar y redactar antes de compartir.
- Configuración privada `.env.qa`, base de datos y media no se versionan ni adjuntan.

Este registro separa pruebas automatizadas, HTTP de integración local, navegador pendiente y servicios externos pendientes. No representa “QA aprobado” hasta que Vicente complete la matriz y el registro de ejecución.
