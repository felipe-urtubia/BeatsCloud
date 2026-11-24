# Traspaso de entorno QA a Vicente

## Versión que se valida

- Repositorio: `felipe-urtubia/BeatsCloud`, rama `main`.
- Corte base anterior: `8c35a74f899b284edb521d3da5cd2d5b79357bcf`.
- La infraestructura QA, notificaciones y pruebas de este paquete quedan integradas en el árbol final de `main`; no se requiere aplicar un parche manual.
- El checkout local de trabajo puede estar atrasado. Comprueba siempre el SHA indicado por el mensaje de entrega y por `git rev-parse HEAD`.

## Inicio recomendado

Sigue `docs/qa/GUIA_VICENTE.md`. En Linux abre una terminal en el clon y ejecuta `./INICIAR_QA.sh`; en Windows abre `INICIAR_QA.bat`. Los lanzadores llaman a `scripts/qa/run-all.sh` dentro de una sola sesión persistente.

## Requisitos y aislamiento

Se requieren Git/Bash, Python 3.12+, Node.js 20+/npm, Docker Compose v2 (o Podman Compose rootless) y FFmpeg. La base corre en PostgreSQL local y aislado. El script crea `.env.qa` con credenciales aleatorias, restringe permisos, deshabilita R2 y SMTP externo, y conserva base y medios para la siguiente sesión. No usa archivos `.env` productivos.

## Evidencia anterior sobre el corte base

En la validación anterior ejecutada directamente sobre `8c35a74f899b284edb521d3da5cd2d5b79357bcf`, se registraron 499 pruebas Django y 40 de frontend aprobadas, checks y migraciones, TypeScript, lint, build y smoke local. Esos resultados no se atribuyen a otro SHA. La integración de los scripts, lanzadores y documentos requiere una validación final sobre su propio SHA.

La validación anterior comprobó Vite y proxy HTTP 200, catálogo y preview HTTP 200, y descarga anónima HTTP 403. No constituye evidencia de Webpay E2E real, credenciales productivas, R2 real con expiración de enlaces, SMTP real, usabilidad externa ni carga de producción.

## Seguridad y soporte

Los logs privados están en `.qa-private/runs/<fecha>/`. Envía `INFORME_VALIDACION.md` y, solo si falla, `qa-run.log`. Nunca envíes `.env.qa`, contraseñas, tokens o URLs firmadas. `scripts/qa/reset.sh` es una operación separada, pide confirmación explícita y no forma parte del asistente.

Consulta `docs/qa/DETALLE_TECNICO.md` y `QA_TEST_MATRIX.md` para detalles y casos manuales.
