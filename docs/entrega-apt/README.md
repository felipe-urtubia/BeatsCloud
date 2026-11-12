# Entrega APT — BeatsCloud

**Fecha de entrega:** 19-11-2026
**Corte de esta auditoría:** 12-11-2026
**Sprints del calendario informado por el equipo:** Sprint 3 (12–15 nov.) y Sprint 4 (16–19 nov.)

Este índice reúne documentación de entrega y distingue hechos observables en el repositorio de datos que el equipo debe validar. No sustituye Jira ni actas de reunión.

## Documentos

| Documento | Estado al corte | Fuente / acción pendiente |
|---|---|---|
| [Inicio del proyecto](inicio_proyecto.md) | Borrador verificable | Confirmar alcance, equipo, patrocinador/cliente y criterios APT. |
| [Visión del producto](vision_producto.md) | Borrador basado en implementación | Validar con usuario/cliente y Jira. |
| [Product Backlog](product_backlog.md) | Inventario técnico inicial, no export Jira | Conciliar cada épica/ítem con Jira, prioridad, responsable y aceptación. |
| [Arquitectura](arquitectura.md) | Diagrama basado en código actual | Confirmar despliegue objetivo y ambiente de demo. |
| [Plan de pruebas](plan_pruebas.md) | Plan y matriz pendientes | Ejecutar y adjuntar resultados por ambiente; no asumir pruebas pasadas. |
| [Plan de riesgos](plan_riesgos.md) | Inicial | Asignar responsables y revisar probabilidad/impacto con el equipo. |
| [Retrospectivas](retrospectivas/README.md) | No hay actas verificables aquí | Recuperar actas de Sprint 1–2; levantar Sprint 3–4 al cierre real. |
| [Sprint Reviews](sprint-reviews/README.md) | No hay actas verificables aquí | Recuperar demos/resultados de Sprint 1–2; completar Sprint 3–4 tras demo. |
| [Evidencia E2E](evidencias/e2e/README.md) | DOCX y capturas no encontrados | Ejecutar recorrido autenticado y adjuntar evidencias auténticas. |

## Fuentes consultadas

- Código Django: `app/models.py`, `app/views.py`, `app/api_shim.py`, `app/urls.py`, `beatcloud/urls.py`.
- SPA: `frontend/client/src/`, `frontend/client/package.json` y `.env.example`.
- Documentación existente: `README.md`, `docs/INTEGRACION_BACKEND.md`, `docs/evidencias/pruebas_backend.txt`, `REGISTRO_CAMBIOS_BEATSCLOUD.md`.
- Un documento `VERIFICACION_SPRINT_2.md` está en otra rama local de reorganización y no en el árbol actual. Sirve como pista de verificación técnica fechada 05-11-2026, no como evidencia oficial de Review/Retrospectiva ni como estado actual.

## Convención de evidencia

Cada resultado de prueba o decisión debe incluir fecha/hora, ambiente, versión/commit, ejecutor, pasos, resultado observado y enlace a evidencia sin datos personales ni secretos. Si no se ejecutó, indicar **Pendiente** y la dependencia concreta. Los términos “aprobado”, “real” y “completo” se reservan para resultados observados y reproducibles.
