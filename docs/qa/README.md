# QA y evidencias

- [Snapshot histórico del backlog DDPB — 24-11-2026](auditorias/ESTADO_BACKLOG_2026-11-24_e652600.md): consulta autenticada de 91 incidencias en ese corte. **No representa el estado actual de Jira al 25-11-2026.**
- [Plan de primera revisión web](PLAN_REVISION_WEB.md): alcance de solo lectura en el sitio publicado y límites de seguridad.
- [Matriz de pruebas trazable al backlog DDPB](MATRIZ_PRUEBAS_BACKLOG.md): casos estables, historias vinculadas, requisitos y estados de ejecución QA separados del estado Jira.
- [Verificación del despliegue del 24-11-2026](VERIFICACION_DESPLIEGUE_2026-11-24.md): respuestas GET observadas y datos de entorno que siguen sin confirmar.
- [Detalle técnico de automatización QA existente](DETALLE_TECNICO.md): suites y límites de la ejecución local automatizada.
- [Auditorías históricas](auditorias/): snapshots fechados y asociados a su SHA; no deben interpretarse como estado vigente sin cotejar fecha y rama.

Las ejecuciones nuevas deben registrar SHA, fecha, ambiente, caso, resultado y evidencia. Las notas históricas de `evidencias/qa/` siguen asociadas al SHA y entorno que declaran.

La carpeta raíz ya no contiene el prototipo de registro HTML anterior a la SPA; el flujo vigente de registro está en Django/React.
