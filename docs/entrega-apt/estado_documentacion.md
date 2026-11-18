# Estado de la documentación — auditoría de entrega APT

**Corte histórico de esta ficha:** 12-11-2026 · **Destino:** presentación/entrega APT prevista para 19-11-2026. Para resultados posteriores consultar [validación técnica 18-11-2026](validacion_tecnica_corte_2026-11-18.md).
**Estado general:** paquete estructurado y redactado hasta el límite de las fuentes verificables; hay datos de gestión y evidencias que el equipo debe completar. No se presenta ningún borrador como aprobado.

## Criterio de estados

- **Completo para revisión:** contiene propósito, base documental y vacíos identificados; aún puede requerir aprobación.
- **Borrador de validación:** redacción basada en código o calendario sin aprobación de negocio/equipo.
- **Preliminar/no oficial:** inventario técnico, no artefacto institucional como Jira.
- **Plantilla pendiente:** estructura lista, pero no existe fuente suficiente para rellenar hechos/reunión/resultados.
- **Protocolo pendiente de ejecución:** pasos/capturas definidos, evidencia de ejecución no adjunta.
- **No localizado:** no se encontró el artefacto en este checkout ni las carpetas inspeccionadas.

## Matriz documental

| Documento | Propósito | Estado al corte | Fuentes utilizadas | Validación pendiente |
|---|---|---|---|---|
| [README de entrega](README.md) | Índice, alcance de estados y orden de cierre | Completo para revisión | Todos los documentos enlazados | Aprobación del equipo y confirmación de rúbrica/entregables APT. |
| [Inicio del proyecto](inicio_proyecto.md) | Contexto, problema, objetivos, alcance, actores, metodología, tecnología y restricciones | Borrador de validación | README, registro de cambios, modelos/rutas/settings, API y SPA | Problema de negocio, patrocinador/cliente, objetivos oficiales, equipo/roles, método, exclusiones y plataforma de demo. |
| [Visión del producto](vision_producto.md) | Necesidad, usuarios, valor, alcance, limitaciones y éxito | Borrador de validación | Modelos, API, componentes/contexto y documentación de integración | Cliente/Product Owner debe aprobar segmento, propuesta de valor, diferenciadores, metas y roadmap. |
| [Product Backlog](product_backlog.md) | Mapeo entre capacidades técnicas visibles y Jira | Preliminar, explícitamente no oficial | Código, registros del proyecto y verificación Sprint 2 en otra rama | Acceso/export de Jira DDPB: épicas, keys, prioridad, estado, sprint, criterios, estimaciones y asignaciones. |
| [Arquitectura](arquitectura.md) | Vista lógica y flujos reales del sistema | Completo para revisión; topología de despliegue desconocida | Django settings/models/views/API, Vite config, cliente SPA y documentación | Motor/instancia DB y almacenamiento del ambiente, proxy/origen/TLS, servicios de entrega y despliegue real. |
| [Plan de pruebas](plan_pruebas.md) | Estrategia, precondiciones, casos y registro | Plan preparado; E2E pendientes al corte de esta ficha | Tests del repositorio, log 14-10, integración 06-11, regresiones 06/08-11 y verificación Sprint 2 de otra rama | Los resultados del 18-11 están en el registro técnico enlazado en el encabezado; completar las pruebas manuales E2E pendientes. |
| [Plan de riesgos](plan_riesgos.md) | Gestionar condiciones que pueden impedir una entrega segura/aceptable | Inicial y abierto; sin propietarios asignados | Configuración/código, registro de cambios, hallazgo ZIP, plan E2E | Asignar dueños, confirmar escala, rotación/saneamiento, entorno y plan de contingencia. |
| [Índice retrospectivas](retrospectivas/README.md) | Convención y estado de fuentes | Completo para revisión | Registro de cambios; verificación Sprint 2 externa a rama | Confirmación del equipo. |
| [Retrospectiva Sprint 1](retrospectivas/sprint-1.md) | Hallazgos y acción de mejora | Fuente indirecta únicamente; no acta | Registro alude a acción 5 vinculada con unificación | Recuperar acta y validar acción, contexto, dueño y resultado. |
| [Retrospectiva Sprint 2](retrospectivas/sprint-2.md) | Hallazgos y acciones | No localizada; ficha de trazabilidad | Verificación técnica de otra rama | Recuperar acta original; no inferir hallazgos a partir del reporte técnico. |
| [Retrospectiva Sprint 3](retrospectivas/sprint-3.md) | Hallazgos y acciones | Plantilla; sprint en curso al corte | Calendario informado 12–15 nov. | Completar tras reunión real, con participantes y hechos. |
| [Retrospectiva Sprint 4](retrospectivas/sprint-4.md) | Hallazgos y acciones | Plantilla; sprint futuro al corte | Calendario informado 16–19 nov. | Completar tras reunión real. |
| [Índice Sprint Reviews](sprint-reviews/README.md) | Convención, calendario y estado de fuentes | Completo para revisión | Registro de cambios; verificación Sprint 2 externa a rama | Confirmación de equipo. |
| [Sprint Review 1](sprint-reviews/sprint-1.md) | Objetivo, demostración, aceptación y feedback | Acta no localizada | Registro de cambios no contiene resultados de Review | Recuperar acta/demo/feedback y Jira. |
| [Sprint Review 2](sprint-reviews/sprint-2.md) | Objetivo, demo y resultado | No localizada; resumen técnico separado | `VERIFICACION_SPRINT_2.md` en otra rama local | Confirmar relación con sprint, demo, participantes y aceptación. |
| [Sprint Review 3](sprint-reviews/sprint-3.md) | Demostración del incremento | Plantilla; sprint en curso al corte | Calendario informado 12–15 nov. | Completar después de la Review real. |
| [Sprint Review 4](sprint-reviews/sprint-4.md) | Demostración del incremento | Plantilla; sprint futuro al corte | Calendario informado 16–19 nov. | Completar después de la Review real. |
| [Protocolo E2E](evidencias/e2e/README.md) | Organizar ejecución y capturas requeridas | Protocolo listo; ejecución pendiente | Requisitos de entrega, `docs/INTEGRACION_BACKEND.md`, plan de pruebas | Ubicar/revisar DOCX de Vicente; ejecutar casos con ambiente real TEST y capturas saneadas. |
| `Evidencia_Pruebas_E2E_BeatsCloud.docx` | Informe de evidencia mencionado por el equipo | No localizado | Inventario del repositorio/carpeta documental y búsqueda de documentos | Vicente/equipo debe indicar ruta y versión; revisar antes de editar. No se reemplazó ni duplicó como DOCX. |
| Capturas E2E | Respaldar cada escenario de extremo a extremo | No localizadas | Inventario de archivos de imagen; evidencia existente de logos/fondos no corresponde a E2E | Ejecutar login, carrito, Webpay, retorno y descarga; no fabricar imágenes. |

## Hallazgos de fuente y límites

1. Jira no está disponible entre las integraciones/herramientas de esta sesión. No se consultaron issues DDPB ni se completó una exportación. Un registro en rama local cita DDPB-66/74/81; no confirma el estado vigente de Jira.
2. El árbol actual contiene `README.md`, `docs/INTEGRACION_BACKEND.md`, `docs/evidencias/pruebas_backend.txt` y `REGISTRO_CAMBIOS_BEATSCLOUD.md`. El log UTF-16 registra 22 tests el 14-10-2026. Integración backend registra resultados al 06-11; el registro de cambios informa 103 pruebas Django el 06-11 y 111 el 08-11. Son resultados históricos según sus documentos, no pruebas repetidas hoy.
3. El commit histórico `53db43f` conserva `VERIFICACION_SPRINT_2.md` (05-11-2026), que registra DDPB-74/81, 34 pruebas Django y build frontend; la prueba manual Webpay real consta pendiente. Esta verificación no es acta de Review/retrospectiva y sus resultados corresponden a otro corte de código.
4. El registro de cambios menciona una acción de retrospectiva de Sprint 1, pero no describe la reunión, sus hallazgos ni la acción con suficiente detalle para reconstruir un acta.
5. Riesgo crítico: `agregar.html` era un ZIP con un miembro `.env`; no se extrajo. `git-filter-repo` retiró esas rutas de las referencias locales. Las ramas remotas conservan el historial anterior y la rotación/revocación aún no está confirmada. Ver [plan de riesgos](plan_riesgos.md) y la validación del 18-11 enlazada en el encabezado.

## Pendiente de validación del equipo

- **Administrador/Product Owner Jira:** exportar DDPB y conciliar backlog, prioridades, estados, sprints y criterios.
- **Quienes participaron en Sprint 1 y Sprint 2:** facilitar actas originales de Reviews y retrospectivas; confirmar decisiones, comentarios, acciones y fechas.
- **Equipo para Sprint 3 y Sprint 4:** entregar objetivos/compromisos y documentar ceremonias después de ocurridas.
- **Vicente/equipo:** confirmar ubicación y revisión del DOCX E2E existente.
- **Integración/QA:** identificar ambiente, cuenta ficticia, responsables, ejecutar pruebas E2E y adjuntar capturas auténticas.
- **Custodio Git/responsables de secretos:** resolver exposición potencial de credenciales y datos embebidos en el ZIP preexistente sin registrar valores en estos documentos.
- **Cliente/evaluador:** validar visión, alcance aprobado, criterios académicos y rúbrica APT.
