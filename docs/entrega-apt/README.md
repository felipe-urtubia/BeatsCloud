# Paquete documental APT — BeatsCloud

**Fecha de corte documental:** 18-11-2026
**Presentación APT prevista:** 19-11-2026
**Clasificación:** documentos de trabajo; no aprobados mientras la validación indicada siga pendiente.

Este índice guía la revisión técnica del repositorio. La documentación de trabajo preexistente se conserva; los documentos técnicos de corte identifican explícitamente lo observado en `codex/integracion-demo-20261118`, sin tratar simulaciones, registros históricos o borradores como aprobaciones.

## Documentos de entrega

| Documento | Estado | Uso |
|---|---|---|
| [Estado de la documentación](estado_documentacion.md) | Auditoría documental al corte; requiere validación del equipo | Resume fuente, nivel de evidencia y vacío por documento. |
| [Inicio del proyecto](inicio_proyecto.md) | **BORRADOR** basado en producto/repositorio | Contexto, objetivos técnicos, alcance, actores, método, herramientas, fechas, dependencias. Validar negocio, roles y alcance oficial. |
| [Visión del producto](vision_producto.md) | **BORRADOR** basado en funciones visibles | Visión funcional, usuarios, valor, capacidades, limitaciones y criterios sugeridos. Cliente/Product Owner debe aprobar. |
| [Product Backlog](product_backlog.md) | **INVENTARIO TÉCNICO PRELIMINAR; NO es respaldo oficial Jira** | Conciliar con export del proyecto DDPB. Jira no fue accesible en esta sesión. |
| [Arquitectura](arquitectura.md) | **DESCRIPCIÓN LÓGICA** derivada del código; topología productiva no acreditada | Componentes, datos, sesión, pagos, archivos, flujos Mermaid e integraciones. |
| [Modelo de datos y almacenamiento](modelo_datos_y_almacenamiento.md) | Estado técnico derivado del código integrado; R2 externo no probado | Entidades, migraciones, archivos locales/R2, audio y persistencia de pagos. |
| [Validación técnica 18-11-2026](validacion_tecnica_corte_2026-11-18.md) | Registro de comandos, resultados y límites del corte | Django, frontend, HTTP local, datos demo y pruebas pendientes. |
| [Trazabilidad técnica](trazabilidad_tecnica.md) | Metadatos Git observables; Jira no accesible | Commits, merges y límites de atribución individual. |
| [Matriz de evidencias técnicas](matriz_evidencias_tecnicas.md) | Matriz de cumplimiento técnico del corte | Evidencias localizadas, estado y pendientes. |
| [Plan de pruebas](plan_pruebas.md) | **PLAN DE TRABAJO**; contiene registro separado de resultados históricos documentados y pruebas pendientes | Casos, precondiciones, pasos, resultados esperados y evidencia requerida. No se ejecutaron pruebas en esta sesión. |
| [Plan de riesgos](plan_riesgos.md) | Evaluación inicial **ABIERTA**, responsables no asignados | Riesgos de archivo/secretos, Webpay, E2E, audio, almacenamiento, integración y fecha APT. |
| [Retrospectivas](retrospectivas/README.md) | Actas históricas no localizadas; plantillas y límites de evidencia | Documentar Sprint 1–4 solo con participantes, fechas y hechos confirmados. |
| [Sprint Reviews](sprint-reviews/README.md) | Actas históricas no localizadas; plantillas y registro técnico histórico separado | No confundir la verificación técnica Sprint 2 de otra rama con Review. |
| [Evidencia E2E](evidencias/e2e/README.md) | Protocolo preparado; ejecuciones/capturas **PENDIENTES** | Matriz de login, catálogo, carrito, Webpay, retorno, rechazo y descarga. DOCX referido no localizado. |

## Estado del producto que debe conservarse en la presentación

- **IMPLEMENTADO** indica código presente, no una prueba aprobada.
- **VALIDADO** se acompaña siempre de fecha/fuente y alcance exactos.
- **PARCIAL** indica que falta parte del flujo o integración.
- **SIMULADO** identifica mock o doble de prueba; no acredita servicio real.
- **PENDIENTE** indica falta implementación, acceso, ejecución o evidencia.
- Webpay está integrado; tests con dobles no equivalen a compra E2E TEST.
- El cambio de `audioEngine.ts` del PR #2 requiere validación real en navegador.
- `agregar.html` fue retirado del árbol de integración después de verificar sus metadatos: es un ZIP con un miembro `.env`. No se extrajo ni se imprimió su contenido. El objeto permanece en historial Git; se requiere respuesta de seguridad antes de publicar.
- El corte técnico 18-11-2026 registra pruebas automatizadas y HTTP locales en [validación técnica](validacion_tecnica_corte_2026-11-18.md). No acredita R2 real, pago externo ni reproducción verificada en navegador.

## Fuentes principales

- [README del proyecto](../../README.md)
- [Integración backend](../INTEGRACION_BACKEND.md)
- [Evidencia de pruebas backend (log histórico, 14-10-2026)](../evidencias/pruebas_backend.txt)
- [Registro de cambios del proyecto](../../REGISTRO_CAMBIOS_BEATSCLOUD.md)
- Código: `app/models.py`, `app/api_shim.py`, `app/views.py`, `app/urls.py`, `beatcloud/settings.py`, `frontend/client/src/context/AppContext.tsx`, `frontend/client/src/api/django.service.ts`, `frontend/client/src/components/UploadTrackModal.tsx`.
- Antecedente adicional: `VERIFICACION_SPRINT_2.md` está en la rama local `integration/reorganization-checkpoint`, fechado 05-11-2026. Es verificación técnica, no Review/Retrospectiva, y no se ha trasladado como resultado oficial.

## Forma de completar el paquete

1. Obtener export de Jira DDPB y actas originales; conciliar alcance/prioridad/sprints/criterios.
2. Asignar responsables confirmados y validar inicio/visión/arquitectura/riesgos.
3. Ejecutar casos del plan en ambiente identificado y adjuntar evidencias saneadas al documento E2E existente si aparece.
4. Incorporar reviews y retrospectivas solo después de verificar actas o celebrar la reunión real.
5. Marcar cada documento como aprobado únicamente tras registrar quién lo validó y cuándo.
