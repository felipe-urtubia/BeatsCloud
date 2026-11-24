# Entrega QA para Vicente

## Base de esta integración

- Repositorio: `felipe-urtubia/BeatsCloud`.
- Rama definitiva: `main`.
- SHA de partida de esta mejora: `17ca427de31c57277b4174772fca62651c828ec4`.
- La rama de mejora Windows se entrega por PR para revisión; no se integró automáticamente.

Para usar el procedimiento integrado, clona el repositorio y cambia a `main` según el SHA indicado en el mensaje de entrega. No hay que aplicar `QA_REVIEW.patch`.

## Un paso de inicio

En Windows 11, abre la carpeta del repositorio y haz doble clic en `INICIAR_QA.bat`. En Linux, ejecuta `./INICIAR_QA.sh` en una terminal. La guía corta está en `docs/qa/GUIA_VICENTE.md` y los requisitos/casos manuales en `docs/qa/GUIA_PRUEBAS.md`.

El asistente comprueba Git/Bash, Python, Node/npm, Docker Compose y FFmpeg, crea su entorno aislado, prepara cuentas de prueba, inicia servicios, ejecuta pruebas y smoke local, detiene sus servicios e informa el resultado. En Windows necesita Git for Windows, Docker Desktop iniciado y Windows 11. No instala programas automáticamente ni solicita permisos administrativos.

## Datos y privacidad

- PostgreSQL QA usa un proyecto/volumen Docker propio, puertos locales y credenciales aleatorias; no se conecta a la base de desarrollo.
- `media/qa/` y el volumen de PostgreSQL se conservan para corridas posteriores.
- `.env.qa`, credenciales temporales, logs privados y archivos de ejecución viven en `.qa-private/` y no deben compartirse.
- Los informes HTML/Markdown que se pueden revisar se guardan en `evidencias/qa/runs/<fecha>/`.
- No se hace push automático ni se publica directamente en `main`. Publica evidencias mediante PR según `docs/qa/PUBLICAR_EVIDENCIAS.md`.

## Alcance y límites

El runner ejecuta checks/migraciones Django, suite Django, pruebas frontend, TypeScript, lint, build y smoke local Vite/proxy/catálogo/preview/denegación de descarga anónima. No presenta como validados Webpay E2E real, credenciales productivas, R2 externo y expiración real de enlaces, SMTP real, usabilidad externa ni carga productiva.

Windows 11 no estuvo disponible para ejecución real al preparar esta integración. El `.bat`, Bash y rutas se revisaron estáticamente; Vicente debe completar la lista Windows 11 de `docs/qa/GUIA_PRUEBAS.md`. Linux se valida de forma independiente.
