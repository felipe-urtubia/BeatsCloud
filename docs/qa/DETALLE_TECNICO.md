# Detalle técnico de la ejecución QA

## Flujo

`INICIAR_QA.bat` (Windows) y `INICIAR_QA.sh` (Linux) llaman a `scripts/qa/run-all.sh`. Este orquestador ejecuta, en orden, requisitos, preparación, inicio, checks/pruebas, smoke, detención e informe. Las pruebas y el smoke comparten procesos en una sola sesión persistente. Una salida no exitosa detiene el flujo y el manejador de salida intenta detener el entorno QA.

## Requisitos detectados por el asistente

- Git y Bash.
- Python 3.12 o superior.
- Node.js 20 o superior y npm.
- Docker Compose v2 con Docker iniciado, o Podman Compose rootless.
- FFmpeg.
- Acceso a puertos locales 8010, 3010 y un puerto libre de 55433–55499.

No se instalan herramientas con privilegios administrativos. El entorno Windows requiere Git Bash y Docker Desktop; se revisó estáticamente, pero no se ejecutó en Windows.

## Archivos, datos y seguridad

- `.env.qa` se genera localmente con permisos restringidos y valores aleatorios; no se versiona.
- `.qa-private/` contiene logs y reportes con permisos locales privados. Las salidas comunes de credenciales generadas se ocultan en los logs.
- `media/qa/` y el volumen de PostgreSQL son persistentes. `run-all.sh` no ejecuta `reset.sh` ni borra datos.
- El servicio de correo usa backend de consola. R2 está desactivado y Webpay usa configuración TEST sin credenciales externas.
- El proceso de detención verifica que cada PID corresponda a BeatsCloud QA antes de enviar TERM. No usa kill forzado.

## Alcance de validación

La ejecución cubre checks Django, migraciones, pruebas Django, pruebas frontend, TypeScript, lint, build y smoke local de Vite/proxy/API, catálogo, preview y rechazo de descarga anónima.

No valida Webpay E2E real, credenciales productivas, R2 externo con firma/expiración, SMTP real, usabilidad con participantes externos ni carga/concurrencia de infraestructura productiva. Los tests con mocks no demuestran integraciones externas.

## Diagnóstico

El asistente imprime pasos y errores breves. Los detalles técnicos se guardan en `.qa-private/runs/<fecha>/qa-run.log`; el resumen queda en el mismo directorio como `INFORME_VALIDACION.md`. Ante un fallo, comparte ambos archivos. No compartas `.env.qa`, credenciales ni URLs firmadas.
