# Evidencias QA

Guarda artefactos reales en estas carpetas. No incorpores capturas ficticias, datos personales, contraseñas, cookies, encabezados `Authorization`, tokens Webpay, URLs firmadas completas, secretos ni archivos de usuarios.

## Nomenclatura

`YYYY-MM-DD_<SHA-corto>_<ID-caso>_<resultado>_<secuencia>.<ext>`

Ejemplos de nombres (no son archivos de evidencia):

- `2026-11-24_8c35a74_QA-03_aprobada_01.png`
- `2026-11-24_8c35a74_QA-12_no-ejecutada_nota.md`

Carpetas: `screenshots/`, `videos/`, `logs/`, `reports/`, `execution-notes/`. Adjunta una nota por corrida con SHA completo, fecha y zona horaria, SO, navegador/versiones, tipo de ejecución (mock/local/externa/manual), precondiciones, resultado esperado/observado y artefactos. Redacta identificadores de cuenta y datos de pago.

No afirmes aprobación basándote en preparación del entorno o en una prueba mock. El flujo integrado `scripts/qa/run-all.sh` guarda cada corrida en `.qa-private/runs/<fecha>/`, con fecha y SHA propios. Pauta: `../../QA_TEST_MATRIX.md` y `../../QA_HANDOFF.md`. No es necesario aplicar un parche para usar la infraestructura integrada.
