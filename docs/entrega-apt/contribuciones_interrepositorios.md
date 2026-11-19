# Matriz interrepositorios de contribuciones

**Corte documental:** 19-11-2026. La fuente de verdad del código es `felipe-urtubia/BeatsCloud`; el SHA exacto del snapshot académico aparece en `SOURCE_COMMIT.txt`. La suite Django actual y los checks están registrados en `validacion_qa_cierre_2026-11-19.md`; frontend 26/TypeScript/lint/build tienen un corte histórico separado. No se infiere autoría por carpeta ni por cantidad de commits.

| Integrante | Rol | Contribuciones verificables | Evidencia y commits asociados | Estado / límite |
|---|---|---|---|---|
| Ismael Araya | Scrum Master; UI/UX, frontend e integración | SPA React/TypeScript, catálogo y reproductor, integración con API Django, carga/audio y organización técnica. | BeatsCloud PR #1 (`6ff738c`, `4c64877`, `041f6f3`, merge `3bf2090`) y PR #2 (`f0c54f9`, `6883459`, `750e49e`, equivalencias por `patch-id`). Académico: `c2f2881`, `17b5672`. | Trabajo integrado y documentado. Los alias Git de commits de saneamiento no se atribuyen automáticamente a Ismael. |
| Felipe Urtubia | Product Owner; backend, pagos y almacenamiento | Django/API, modelos y PostgreSQL, autenticación, Webpay/Transbank, R2 y descargas protegidas. | BeatsCloud PR #3 (`41f85b8`, merge `1553203`) y commits técnicos de R2/Webpay/metadatos descritos en [trazabilidad](trazabilidad_tecnica.md). Académico: `8c7def7`, `d45d0f6`. | Implementación verificable; las pruebas externas reales no están acreditadas por el corte automatizado. |
| Vicente Monroy | QA / Development Team; pruebas, evidencias y apoyo al desarrollo | Registro de defectos, métricas, respuesta API y acta de Sprint Review/Retrospective. | Académico: `4a48d6e`, `4281f79`, `6f1bf7b`; autor Vicente, committer `yaeaelo`. | Contribución documental/QA histórica verificable. La validez externa de métricas requiere evidencia primaria. El runner ejecutó las suites locales de cierre; no hay resultados manuales incorporados por Vicente. Su registro de ejecución se mantiene abierto. |

## Evidencia histórica de Vicente

Los tres commits del repositorio académico se conservan con Vicente como autor. La planilla de defectos distingue la detección/registro de las correcciones: asigna DEF-01 y DEF-02 a Felipe e Ismael/Felipe y DEF-03 a Ismael. Por eso esta matriz reconoce el trabajo QA de Vicente sin atribuirle esos cambios de código. El informe de métricas recoge mediciones declaradas; no se encontraron capturas o logs originales para revalidar cada valor.

## Validación actual y límites

La evidencia del 19-11-2026 está en `validacion_qa_cierre_2026-11-19.md`: 372 pruebas Django, checks, `build.sh` y smoke HTTP en `4569613b29e7023161149ca5e7d5fddabf6437db`; frontend 26/TypeScript/lint/build en `7ad7305fecdbdeff8b4f9d8c301b1f6f1c3e7dbe`. La suite actual la ejecutó el runner, no Vicente o Ismael manualmente. Los cuatro procedimientos manuales están separados en `qa/GUIA_EJECUCION_MANUAL_ISMAEL.md`; siguen pendientes.

## Identidad y alcance de autoría

La rama de cierre se rebasa localmente sobre el `origin/main` observado; los autores originales de los commits publicados se conservan. Los commits de consolidación no publicados se atribuyen a Ismael según la identidad verificada de su perfil. No se reasigna trabajo de Felipe o Vicente. La matriz CSV histórica conserva su corte base; los SHA de cierre se consultan en el historial Git local del repositorio, no se sustituyen dentro de esa matriz.

## Coherencia documental

El repositorio de producto conserva código, pruebas y documentación técnica de operación. El repositorio académico mantiene los informes de asignatura, artefactos grupales/individuales y el snapshot de sistema vinculado a un SHA concreto del producto. Para evitar versiones contradictorias, la copia académica identifica su commit de origen y no se usa como fuente alternativa de código.


La comunicación del equipo desde agosto a noviembre complementa los registros: Ismael creó/organizó el repositorio académico, planificó y coordinó la integración y preparación de entrega; Felipe informó avances de backend/pagos/almacenamiento y preparación de demo; Vicente produjo documentación de defectos, indicadores y ceremonias y reportó casos E2E en preparación, sin resultados/capturas disponibles. Para fechas y límites ver la matriz externa del repositorio académico. La asignación inicial de roles del 03-09 fue tentativa y multidisciplinaria; las responsabilidades técnicas evolucionaron durante los sprints.
