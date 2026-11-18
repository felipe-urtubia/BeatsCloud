# Paquete documental APT — BeatsCloud

**Fecha de corte documental:** 18-11-2026
**Presentación APT prevista:** 19-11-2026
**Clasificación:** documentos de trabajo; no aprobados mientras la validación indicada siga pendiente.

Este índice guía la revisión técnica del repositorio. La documentación de trabajo preexistente se conserva; los documentos técnicos de corte describen el código consolidado localmente en `main`, sin tratar simulaciones, registros históricos o borradores como aprobaciones.

La actualización controlada de ramas, saneamiento y validaciones finales se registra en [cierre de saneamiento y publicación](cierre_saneamiento_2026-11-18.md).

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
| [Validación de QA 18-11-2026](validacion_qa_2026-11-18.md) | Ejecución actual de setup, suite y smoke checks | Distingue prueba automatizada, HTTP local, navegador y servicios externos. |
| [Guía de QA para Vicente](qa/GUIA_QA_VICENTE.md) | Procedimiento reproducible del entorno local aislado | Requisitos, DB, seed, cuentas temporales, inicio, evidencias y límites. |
| [Guía de operación de Felipe](operacion/GUIA_FELIPE_GRABACION.md) | Procedimiento de grabación y configuración de integraciones | Ejecución local, Webpay TEST, R2, recorrido y solución de problemas; proveedores reales pendientes. |
| [Matriz QA funcional](qa/matriz_qa_funcional.md) | Casos derivados del código real; pendientes hasta ejecutarlos | Catálogo, auth, perfiles, upload, audio, compras, Webpay y roles. |
| [Registro de ejecución QA](qa/REGISTRO_EJECUCION_VICENTE.md) | Plantilla vacía | Registrar resultados/evidencia y defectos sin atribuir ejecución previa. |
| [Despliegue y configuración](despliegue_y_configuracion.md) | Propuesta futura, no desplegada | Render/Vercel, cookies/CSRF, PostgreSQL, R2, Webpay y bloqueos técnicos. |
| Plantillas de configuración | `.env.example`, `frontend/client/.env.example` | Referencia versionada; copiar a `.env` locales. `.env.qa` es generado/excluido. |
| [Trazabilidad técnica](trazabilidad_tecnica.md) | Metadatos Git observables; Jira no accesible | Commits, merges y límites de atribución individual. |
| [Matriz de evidencias técnicas](matriz_evidencias_tecnicas.md) | Matriz de cumplimiento técnico del corte | Evidencias localizadas, estado y pendientes. |
| [Plan de pruebas](plan_pruebas.md) | **PLAN DE TRABAJO**; contiene registro separado de resultados históricos y pruebas pendientes | Casos, precondiciones, pasos, resultados esperados y evidencia requerida. Las ejecuciones automatizadas/HTTP del 18-11 se registran por separado; E2E de navegador sigue pendiente. |
| [Plan de riesgos](plan_riesgos.md) | Evaluación inicial **ABIERTA**, responsables no asignados | Riesgos de archivo/secretos, Webpay, E2E, audio, almacenamiento, integración y fecha APT. |
| [Retrospectivas](retrospectivas/README.md) | Actas históricas no localizadas; plantillas y límites de evidencia | Documentar Sprint 1–4 solo con participantes, fechas y hechos confirmados. |
| [Sprint Reviews](sprint-reviews/README.md) | Actas históricas no localizadas; plantillas y registro técnico histórico separado | No confundir el commit histórico `ceb3a9c` (verificación Sprint 2) con una Review. |
| [Evidencia E2E](evidencias/e2e/README.md) | Protocolo preparado; ejecuciones/capturas **PENDIENTES** | Matriz de login, catálogo, carrito, Webpay, retorno, rechazo y descarga. DOCX referido no localizado. |

## Convención de estados y límites de evidencia

- **IMPLEMENTADO** indica código presente, no una prueba aprobada.
- **VALIDADO** se acompaña siempre de fecha/fuente y alcance exactos.
- **PARCIAL** indica que falta parte del flujo o integración.
- **SIMULADO** identifica mock o doble de prueba; no acredita servicio real.
- **PENDIENTE** indica falta implementación, acceso, ejecución o evidencia.
- Webpay está integrado; tests con dobles no equivalen a compra E2E TEST.
- El cambio de `audioEngine.ts` del PR #2 requiere validación real en navegador.
- `agregar.html` era un ZIP con un miembro `.env`; se inspeccionaron solo metadatos y no se extrajo ni imprimió contenido. La historia publicada de las ramas de trabajo se saneó. La rotación/revocación de credenciales y la purga de refs internas/cachés por GitHub Support se registran como seguimiento de seguridad, no como operaciones ya realizadas.
- El corte técnico 18-11-2026 registra pruebas automatizadas y HTTP locales en [validación técnica](validacion_tecnica_corte_2026-11-18.md). No acredita R2 real, pago externo ni reproducción verificada en navegador.

## Fuentes principales

- [README del proyecto](../../README.md)
- [Integración backend](../INTEGRACION_BACKEND.md)
- [Evidencia de pruebas backend (log histórico, 14-10-2026)](../evidencias/pruebas_backend.txt)
- [Registro de cambios del proyecto](../../REGISTRO_CAMBIOS_BEATSCLOUD.md)
- Código: `app/models.py`, `app/api_shim.py`, `app/views.py`, `app/urls.py`, `beatcloud/settings.py`, `frontend/client/src/context/AppContext.tsx`, `frontend/client/src/api/django.service.ts`, `frontend/client/src/components/UploadTrackModal.tsx`.
- Antecedente adicional: `VERIFICACION_SPRINT_2.md` se conserva en el historial a partir del commit `ceb3a9c`, fechado 05-11-2026. Es verificación técnica, no Review/Retrospectiva, y no se trata como resultado oficial.

## Forma de completar el paquete

1. Obtener export de Jira DDPB y actas originales; conciliar alcance/prioridad/sprints/criterios.
2. Asignar responsables confirmados y validar inicio/visión/arquitectura/riesgos.
3. Ejecutar casos del plan en ambiente identificado y adjuntar evidencias saneadas al documento E2E existente si aparece.
4. Incorporar reviews y retrospectivas solo después de verificar actas o celebrar la reunión real.
5. Marcar cada documento como aprobado únicamente tras registrar quién lo validó y cuándo.
# Documentación técnica

Para levantar el entorno aislado y ejecutar QA, comenzar por la [Guía de QA de Vicente](qa/GUIA_QA_VICENTE.md), la [matriz funcional](qa/matriz_qa_funcional.md) y el [registro de ejecución](qa/REGISTRO_EJECUCION_VICENTE.md). Los resultados locales del corte se conservan en [validación técnica del 18-11-2026](validacion_tecnica_corte_2026-11-18.md); las pruebas de navegador y servicios externos siguen separadas como pendientes.

La [configuración de despliegue](despliegue_y_configuracion.md) es una propuesta técnica, no evidencia de despliegue.
