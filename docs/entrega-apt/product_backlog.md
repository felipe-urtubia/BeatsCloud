# Product Backlog — BeatsCloud

**Este documento NO es el Product Backlog oficial.** Jira no estuvo disponible en las herramientas de esta sesión, por lo que no se pudieron consultar ni validar épicas, historias, prioridades, estados, asignaciones, criterios acordados o sprints. El contenido siguiente es un inventario técnico preliminar del producto observado en el código, para conciliar con la exportación oficial; no debe copiarse a Jira como si fueran historias aprobadas.

**Corte técnico:** 19-11-2026 · **Entrega prevista:** 19-11-2026. Las fechas y sprints del plan original se conservan como antecedente, no como estado actual confirmado.

## Convención de estado

- **IMPLEMENTADO:** existe código para la capacidad; no implica que se haya validado en el ambiente actual.
- **VALIDADO:** una fuente registra una prueba/observación con fecha; se conserva su alcance y antigüedad.
- **PARCIAL:** existe solo parte del flujo o depende de pasos/servicios no comprobados.
- **SIMULADO:** se ejercita con datos/dobles de prueba o modo mock, no con la integración real completa.
- **PENDIENTE:** falta implementación, validación o fuente para afirmar el resultado.

## Inventario técnico por área de producto

Los códigos `TEC-*` son referencias editoriales locales de este documento, no claves Jira. Prioridad, estado Jira, épica, sprint y responsable se dejan sin atribuir hasta consultar el tablero.

| Épica Jira | Referencia local | Historia/capacidad técnica observada | Prioridad Jira | Estado Jira | Estado de implementación / verificación al corte | Criterio de aceptación a contrastar con Jira |
|---|---|---|---|---|---|---|
| No consultable | TEC-01 | Cuenta, activación, sesión Django y CSRF | No disponible | No disponible | **IMPLEMENTADO; pruebas automatizadas incluidas en la suite 372/372 del 19-11 pasaron**. Activación SMTP E2E real y recorrido manual siguen **PENDIENTES**. | Cuenta de prueba activada inicia sesión; endpoint privado rechaza anónimo; CSRF protege escrituras; cierre invalida identidad y datos privados. |
| No consultable | TEC-02 | Catálogo, búsqueda, perfiles y detalle de track | No disponible | No disponible | **IMPLEMENTADO; API de catálogo responde en smoke local (6/125, 21 páginas) y la suite pasó**. Filtros cliente y render visual manual no se validaron en navegador; algunas opciones se filtran en cliente. | Abrir catálogo y detalle en modo `hybrid`; datos y permisos coinciden con backend; verificar paginación/filtros que defina el ticket. |
| No consultable | TEC-03 | Publicación y edición de pista/audio | No disponible | No disponible | Backend y API **IMPLEMENTADOS; pruebas automatizadas de suite pasaron**. No se completó una subida manual real desde navegador durante este cierre. | Productor autorizado sube archivo de prueba válido, observa confirmación del backend y puede consultar la pista; archivo inválido presenta rechazo claro. |
| No consultable | TEC-04 | Carrito, totales y prevención de duplicados | No disponible | No disponible | **IMPLEMENTADO; suite Django aprobada en QA local**. No se ejecutó checkout manual completo ni se afirma compra E2E. | Agregar/eliminar pista con sesión; subtotal/IVA/total provienen de Django; no permitir duplicado/recompra según regla vigente. |
| No consultable | TEC-05 | Inicio y retorno de pago Webpay | No disponible | No disponible | SDK, vistas y estados **IMPLEMENTADOS**; suite Django aprobada con respuestas simuladas/dobles. Transacción y retorno Webpay TEST reales **PENDIENTES**. | Aprobación genera retorno y registro coherentes; rechazo/cancelación no crean compra y conservan carrito según regla acordada. |
| No consultable | TEC-06 | Historial, licencia y descarga protegida | No disponible | No disponible | API/UI y autorización **IMPLEMENTADAS**; suite aprobada y smoke anónimo de sesión/catálogo, pero no se probó una descarga autorizada postcompra E2E. Evidencia de entrega **PENDIENTE**. | Compra autorizada aparece en biblioteca y devuelve archivo esperado no vacío; usuario sin derecho recibe rechazo. |
| No consultable | TEC-07 | Reproductor y visualizador | No disponible | No disponible | Motor y UI **IMPLEMENTADOS**; las pruebas Node pasan, pero reproducción/pausa/cambio de pista y visualizador requieren validación manual real en navegador. | Probar reproducción/pausa, cambio de pista, volumen, posición, finalización y visualizador en navegador/versiones objetivo. |
| No consultable | TEC-08 | Modo de demostración `mock` | No disponible | No disponible | **SIMULADO** por diseño; no acredita API, persistencia, autenticación, pago ni descarga real. | La interfaz indica modo demo; ninguna evidencia mock se presenta como transacción real. |
| No consultable | TEC-09 | Documentación y evidencia de entrega APT | No disponible | No disponible | Documentación y matrices preparadas; backlog Jira vigente no consultado; el DOCX E2E reportado por Vicente no está recuperado y las capturas manuales siguen pendientes. | Entrega contiene documentos aceptados por equipo, referencias Jira y evidencia auténtica por recorrido. |


## Ejecución de cierre 19-11-2026

Se ejecutaron 372 pruebas Django, 26 pruebas frontend, TypeScript/lint, build Vite y smoke HTTP en una base QA aislada; `bash build.sh` también completó collectstatic y migraciones locales. La evidencia y las limitaciones están en [validacion_qa_cierre_2026-11-19.md](validacion_qa_cierre_2026-11-19.md). Estos resultados no convierten en validados manualmente los flujos UI, pago, descarga, SMTP o R2 externos.

## Antecedentes identificados (no equivalen a consulta de Jira)

El archivo `VERIFICACION_SPRINT_2.md`, conservado en el historial desde el commit `ceb3a9c`, cita los identificadores **DDPB-74** (autenticación D3) y **DDPB-81** (selector API real/mock) y reporta 34 tests backend, build TS/Vite y pruebas pendientes de Webpay manual, fechados 05-11-2026. Esto es una fuente histórica, no una consulta del estado actual de Jira ni evidencia automática de que su código sea idéntico al incremento actual. `docs/INTEGRACION_BACKEND.md` alude además a DDPB-66 para la decisión de sesiones/CSRF y pide validar su ratificación formal.

## Pendiente de validación del equipo

Un integrante con acceso al proyecto DDPB debe exportar el backlog vigente y conciliar cada fila técnica con: clave/título exactos, épica, prioridad, estado Jira, sprint, criterio de aceptación, estimación y responsable cuando estén registrados. Confirmar también si DDPB-66, DDPB-74 y DDPB-81 siguen vigentes y qué issues cubren las pruebas E2E y la entrega documental. Hasta entonces, no se atribuye prioridad/estado/sprint a ningún TEC-*.

## Fuentes internas

- [Registro de cambios](../../REGISTRO_CAMBIOS_BEATSCLOUD.md)
- [Integración backend](../INTEGRACION_BACKEND.md)
- Verificación técnica Sprint 2 (`VERIFICACION_SPRINT_2.md`, commit histórico `ceb3a9c`) — referencia histórica; no es acta de ceremonia.
- `app/models.py`, `app/api_shim.py`, `app/views.py`, `app/test_webpay_*.py`, `app/test_auth_d3.py`
- `frontend/client/src/` y `frontend/client/package.json`
