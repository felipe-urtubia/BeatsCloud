# Product Backlog — BeatsCloud

**Este documento NO es el Product Backlog oficial.** Jira no estuvo disponible en las herramientas de esta sesión, por lo que no se pudieron consultar ni validar épicas, historias, prioridades, estados, asignaciones, criterios acordados o sprints. El contenido siguiente es un inventario técnico preliminar del producto observado en el código, para conciliar con la exportación oficial; no debe copiarse a Jira como si fueran historias aprobadas.

**Corte:** 12-11-2026 · **Entrega prevista:** 19-11-2026 · **Calendario informado:** Sprint 3 (12–15 nov.) y Sprint 4 (16–19 nov.).

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
| No consultable | TEC-01 | Cuenta, activación, sesión Django y CSRF | No disponible | No disponible | **IMPLEMENTADO**; pruebas de autenticación y recorrido SPA aparecen documentados históricamente (ver fuentes), no repetidos para este corte. Activación SMTP E2E actual **PENDIENTE**. | Cuenta de prueba activada inicia sesión; endpoint privado rechaza anónimo; CSRF protege escrituras; cierre invalida identidad y datos privados. |
| No consultable | TEC-02 | Catálogo, búsqueda, perfiles y detalle de track | No disponible | No disponible | **IMPLEMENTADO**; verificaciones de lectura/render documentadas en noviembre. Confirmar alcance de filtros/paginación del servidor: registro Sprint 2 de otra rama menciona limitaciones de filtrado SPA. | Abrir catálogo y detalle en modo `hybrid`; datos y permisos coinciden con backend; verificar paginación/filtros que defina el ticket. |
| No consultable | TEC-03 | Publicación y edición de pista/audio | No disponible | No disponible | Backend y API **IMPLEMENTADOS**; cambios de flujo de carga del PR #2 están integrados en `main` local; validación de subida persistida actual **PENDIENTE**. | Productor autorizado sube archivo de prueba válido, observa confirmación del backend y puede consultar la pista; archivo inválido presenta rechazo claro. |
| No consultable | TEC-04 | Carrito, totales y prevención de duplicados | No disponible | No disponible | **IMPLEMENTADO**; contratos/totales server-side documentados en prueba de integración histórica. Validar en entorno actual **PENDIENTE**. | Agregar/eliminar pista con sesión; subtotal/IVA/total provienen de Django; no permitir duplicado/recompra según regla vigente. |
| No consultable | TEC-05 | Inicio y retorno de pago Webpay | No disponible | No disponible | SDK, vistas, estados y comprobaciones **IMPLEMENTADOS**; ramas de retorno **SIMULADAS** en pruebas. Pago/retorno TEST integrado **PENDIENTE** de evidencia E2E. | Aprobación genera retorno y registro coherentes; rechazo/cancelación no crean compra y conservan carrito según regla acordada. |
| No consultable | TEC-06 | Historial, licencia y descarga protegida | No disponible | No disponible | API/UI y autorización **IMPLEMENTADAS**; verificaciones históricas constan en integración; evidencia de entrega solicitada **PENDIENTE**. | Compra autorizada aparece en biblioteca y devuelve archivo esperado no vacío; usuario sin derecho recibe rechazo. |
| No consultable | TEC-07 | Reproductor y visualizador | No disponible | No disponible | Motor y UI **IMPLEMENTADOS**; cambio de `audioEngine.ts` en PR #2 **PENDIENTE** de validación manual en navegador. | Probar reproducción/pausa, cambio de pista, volumen, posición, finalización y visualizador en navegador/versiones objetivo. |
| No consultable | TEC-08 | Modo de demostración `mock` | No disponible | No disponible | **SIMULADO** por diseño; no acredita API, persistencia, autenticación, pago ni descarga real. | La interfaz indica modo demo; ninguna evidencia mock se presenta como transacción real. |
| No consultable | TEC-09 | Documentación y evidencia de entrega APT | No disponible | No disponible | Documentos base preparados en este paquete; Backlog oficial, ceremonias y evidencias E2E **PENDIENTES** de fuentes/equipo. | Entrega contiene documentos aceptados por equipo, referencias Jira y evidencia auténtica por recorrido. |

## Antecedentes identificados (no equivalen a consulta de Jira)

El archivo `VERIFICACION_SPRINT_2.md`, conservado en el historial desde el commit `53db43f`, cita los identificadores **DDPB-74** (autenticación D3) y **DDPB-81** (selector API real/mock) y reporta 34 tests backend, build TS/Vite y pruebas pendientes de Webpay manual, fechados 05-11-2026. Esto es una fuente histórica, no una consulta del estado actual de Jira ni evidencia automática de que su código sea idéntico al incremento actual. `docs/INTEGRACION_BACKEND.md` alude además a DDPB-66 para la decisión de sesiones/CSRF y pide validar su ratificación formal.

## Pendiente de validación del equipo

Un integrante con acceso al proyecto DDPB debe exportar el backlog vigente y conciliar cada fila técnica con: clave/título exactos, épica, prioridad, estado Jira, sprint, criterio de aceptación, estimación y responsable cuando estén registrados. Confirmar también si DDPB-66, DDPB-74 y DDPB-81 siguen vigentes y qué issues cubren las pruebas E2E y la entrega documental. Hasta entonces, no se atribuye prioridad/estado/sprint a ningún TEC-*.

## Fuentes internas

- [Registro de cambios](../../REGISTRO_CAMBIOS_BEATSCLOUD.md)
- [Integración backend](../INTEGRACION_BACKEND.md)
- Verificación técnica Sprint 2 (`VERIFICACION_SPRINT_2.md`, commit histórico `53db43f`) — referencia histórica; no es acta de ceremonia.
- `app/models.py`, `app/api_shim.py`, `app/views.py`, `app/test_webpay_*.py`, `app/test_auth_d3.py`
- `frontend/client/src/` y `frontend/client/package.json`
