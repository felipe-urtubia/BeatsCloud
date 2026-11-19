# Matriz interrepositorios de contribuciones

**Corte documental:** 19-11-2026. La fuente de verdad del código es `felipe-urtubia/BeatsCloud` (`main`); el SHA exacto del snapshot académico aparece en `SOURCE_COMMIT.txt`. El cierre local reejecutó las suites y verificó `build.sh` contra una base QA aislada. No se infiere autoría por carpeta ni por cantidad de commits. La entrega académica aporta documentos y evidencia individual complementaria; no se infiere autoría por carpetas ni por cantidad de commits.

| Integrante | Rol | Contribuciones verificables | Evidencia y commits asociados | Estado / límite |
|---|---|---|---|---|
| Ismael Araya | Scrum Master; UI/UX, frontend e integración | SPA React/TypeScript, catálogo y reproductor, integración con API Django, carga/audio y organización técnica. | BeatsCloud PR #1 (`6ff738c`, `4c64877`, `041f6f3`, merge `3bf2090`) y PR #2 (`f0c54f9`, `6883459`, `750e49e`, equivalencias por `patch-id`). Académico: `c2f2881`, `17b5672`. | Trabajo integrado y documentado. Los alias Git de commits de saneamiento no se atribuyen automáticamente a Ismael. |
| Felipe Urtubia | Product Owner; backend, pagos y almacenamiento | Django/API, modelos y PostgreSQL, autenticación, Webpay/Transbank, R2 y descargas protegidas. | BeatsCloud PR #3 (`41f85b8`, merge `1553203`) y commits técnicos de R2/Webpay/metadatos descritos en [trazabilidad](trazabilidad_tecnica.md). Académico: `8c7def7`, `d45d0f6`. | Implementación verificable; las pruebas externas reales no están acreditadas por el corte automatizado. |
| Vicente Monroy | QA / Development Team; pruebas, evidencias y apoyo al desarrollo | Registro de defectos, métricas, respuesta API y acta de Sprint Review/Retrospective. | Académico: `4a48d6e`, `4281f79`, `6f1bf7b`; autor Vicente, committer `yaeaelo`. | Contribución documental/QA histórica verificable. La validez externa de métricas requiere evidencia primaria. El runner ejecutó las suites locales de cierre; no hay resultados manuales incorporados por Vicente. Su registro de ejecución se mantiene abierto. |

## Evidencia histórica de Vicente

Los tres commits del repositorio académico se conservan con Vicente como autor. La planilla de defectos distingue la detección/registro de las correcciones: asigna DEF-01 y DEF-02 a Felipe e Ismael/Felipe y DEF-03 a Ismael. Por eso esta matriz reconoce el trabajo QA de Vicente sin atribuirle esos cambios de código. El informe de métricas recoge mediciones declaradas; no se encontraron capturas o logs originales para revalidar cada valor.

## Validación actual y límites

La evidencia del 19-11-2026 está en `validacion_qa_cierre_2026-11-19.md`: 372 pruebas Django, 26 frontend, TypeScript/lint, build, smoke HTTP y `build.sh` local con base QA aislada. Es ejecución automatizada por runner, no prueba manual de Vicente. La autoría de casos de Vicente se conserva separada del ejecutor. Firefox manual, compra/descarga E2E, Webpay real, R2 real, SMTP real y despliegue externo siguen sin evidencia aprobada.

## Commits de cierre documentados aparte de la matriz histórica

La matriz CSV académica conserva el universo histórico de los cortes base (112 commits) y no se reescribe para incluir trabajo posterior. En la rama local `closure/2026-11-19` se agregaron estos commits bajo la identidad verificada de Ismael para consolidar tooling y documentación; la ejecución automatizada se atribuye al runner, no a una prueba manual del autor:

| SHA | Autor / committer registrado | Contenido |
|---|---|---|
| `6c19529` | Ismael Araya | Selección aislada de puerto PostgreSQL QA y actualización de guía; no cambia funcionalidades del producto. |
| `b4dc23b` | Ismael Araya | Registro de resultados de cierre QA local; incluye límites explícitos. |
| `cb4f16c` | Ismael Araya | README e índice técnico alineados con los resultados de cierre. |

El snapshot académico identifica el árbol completo y sus hashes. Los commits de integración documental no se usan para alterar la autoría histórica de Felipe o Vicente.

## Coherencia documental

El repositorio de producto conserva código, pruebas y documentación técnica de operación. El repositorio académico mantiene los informes de asignatura, artefactos grupales/individuales y el snapshot de sistema vinculado a un SHA concreto del producto. Para evitar versiones contradictorias, la copia académica identifica su commit de origen y no se usa como fuente alternativa de código.


La comunicación del equipo desde agosto a noviembre complementa los registros: Ismael creó/organizó el repositorio académico, planificó y coordinó la integración y preparación de entrega; Felipe informó avances de backend/pagos/almacenamiento y preparación de demo; Vicente produjo documentación de defectos, indicadores y ceremonias y reportó casos E2E en preparación, sin resultados/capturas disponibles. Para fechas y límites ver la matriz externa del repositorio académico. La asignación inicial de roles del 03-09 fue tentativa y multidisciplinaria; las responsabilidades técnicas evolucionaron durante los sprints.
