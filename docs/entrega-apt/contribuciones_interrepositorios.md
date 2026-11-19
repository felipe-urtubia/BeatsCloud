# Matriz interrepositorios de contribuciones

**Corte:** 18-11-2026. La fuente de verdad del código es `felipe-urtubia/BeatsCloud` (`main`, `f017627`). La entrega académica aporta documentos y evidencia individual complementaria; no se infiere autoría por carpetas ni por cantidad de commits.

| Integrante | Rol | Contribuciones verificables | Evidencia y commits asociados | Estado / límite |
|---|---|---|---|---|
| Ismael Araya | Scrum Master; UI/UX, frontend e integración | SPA React/TypeScript, catálogo y reproductor, integración con API Django, carga/audio y organización técnica. | BeatsCloud PR #1 (`6ff738c`, `4c64877`, `041f6f3`, merge `3bf2090`) y PR #2 (`f0c54f9`, `6883459`, `750e49e`, equivalencias por `patch-id`). Académico: `c2f2881`, `17b5672`. | Trabajo integrado y documentado. Los alias Git de commits de saneamiento no se atribuyen automáticamente a Ismael. |
| Felipe Urtubia | Product Owner; backend, pagos y almacenamiento | Django/API, modelos y PostgreSQL, autenticación, Webpay/Transbank, R2 y descargas protegidas. | BeatsCloud PR #3 (`41f85b8`, merge `1553203`) y commits técnicos de R2/Webpay/metadatos descritos en [trazabilidad](trazabilidad_tecnica.md). Académico: `8c7def7`, `d45d0f6`. | Implementación verificable; las pruebas externas reales no están acreditadas por el corte automatizado. |
| Vicente Monroy | QA / Development Team; pruebas, evidencias y apoyo al desarrollo | Registro de defectos, métricas, respuesta API y acta de Sprint Review/Retrospective. | Académico: `4a48d6e`, `4281f79`, `6f1bf7b`; autor Vicente, committer `yaeaelo`. | Contribución documental/QA histórica verificable. La validez externa de métricas requiere evidencia primaria. QA funcional del corte actual: en ejecución según el equipo, sin resultados incorporados todavía. |

## Evidencia histórica de Vicente

Los tres commits del repositorio académico se conservan con Vicente como autor. La planilla de defectos distingue la detección/registro de las correcciones: asigna DEF-01 y DEF-02 a Felipe e Ismael/Felipe y DEF-03 a Ismael. Por eso esta matriz reconoce el trabajo QA de Vicente sin atribuirle esos cambios de código. El informe de métricas recoge mediciones declaradas; no se encontraron capturas o logs originales para revalidar cada valor.

## Validación actual y límites

El corte de BeatsCloud registra 372 pruebas Django, 26 pruebas frontend, TypeScript/lint, build y HTTP local. Son resultados automatizados/de integración local, no ejecución manual de Vicente. Su registro permanece vacío hasta que cada caso se ejecute. No se afirma Firefox manual, E2E de compra/descarga, Webpay real, R2 real, SMTP real ni despliegue externo.

## Coherencia documental

El repositorio de producto conserva código, pruebas y documentación técnica de operación. El repositorio académico mantiene los informes de asignatura, artefactos grupales/individuales y el snapshot de sistema vinculado a un SHA concreto del producto. Para evitar versiones contradictorias, la copia académica identifica su commit de origen y no se usa como fuente alternativa de código.
