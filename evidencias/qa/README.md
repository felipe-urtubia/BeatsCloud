# Resultados y evidencias QA

## Resultado automático

Cada corrida crea `runs/<fecha>/INFORME_VALIDACION.html` y `INFORME_VALIDACION.md`. Son copias legibles para revisar y, tras comprobar que no haya información privada, publicar por Pull Request. Se guarda una copia técnica con logs en `.qa-private/runs/<fecha>/`; esa carpeta está ignorada por Git y no se publica.

## Evidencia manual

- Capturas: `screenshots/`.
- Videos: `videos/`.
- Observaciones: `execution-notes/`.
- Matriz/casos: `../../QA_TEST_MATRIX.md`.
- Plantilla de observación: `plantillas/PLANTILLA_EVIDENCIA.md`.

Usa nombres como `AAAA-MM-DD_SHA-corto_QA-03_aprobada_01.png`. Adjunta la plantilla o una nota por corrida indicando fecha, SHA probado, Windows/Linux, navegador si aplica, tipo (automática, local, externa o manual), escenario, esperado/observado y resultado.

## Antes de compartir

Revisa cada archivo. No agregues `.env`, `.env.qa`, `.qa-private/`, `.venv/`, `node_modules/`, bases de datos, medios privados, claves, contraseñas, cookies, cabeceras de autorización, tokens de pago, URLs firmadas, ni datos personales. No publiques logs técnicos privados.

Publica solo mediante una rama y Pull Request hacia `main`, nunca con push directo. Sigue `../../docs/qa/PUBLICAR_EVIDENCIAS.md`. En el PR resume resultado y SHA y enlaza el informe.

No declares aprobada Webpay E2E real, R2 externo y su expiración, SMTP real, usabilidad externa o carga productiva a partir de pruebas locales/mock.
