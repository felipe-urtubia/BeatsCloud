# Trazabilidad técnica de contribuciones

**Corte documental:** 19-11-2026 · **Código fuente:** `5021ee84ada9fbd8121362c676572b3a3e68d6d4`. Los SHA son del historial publicado saneado. No se reescribieron autores ni committers durante esta preparación. La evidencia académica complementaria está en el [repositorio de entrega](https://github.com/yaeaelo/2026_2_MA_CAPSTONE_005D_GRUPO_4) y se relaciona en la [matriz interrepositorios](contribuciones_interrepositorios.md).

| Integrante | Responsabilidad principal | Evidencia en BeatsCloud | Evidencia académica | Alcance de atribución |
|---|---|---|---|---|
| Ismael Araya | Scrum Master; UI/UX, frontend e integración | PR #1 React/Django: commits actuales `6ff738c`, `4c64877`, `041f6f3` y merge `3bf2090`. PR #2: `f0c54f9`, `6883459`, `750e49e`, cotejados por `patch-id`. | `c2f2881` (catálogo React/API) y `17b5672` (sincronización de evidencias). | La cuenta autora de los PR vincula el trabajo a Ismael; no implica autoría exclusiva de cada archivo compartido. |
| Felipe Urtubia | Product Owner; backend, pagos y almacenamiento | PR #3: `41f85b8` (descargas R2 expirables) y merge `1553203`; trabajo de R2/Webpay/metadatos en `8be7000`, `4323df2`, `df8a28b`, `b56c3e1`, `064101c`, `e87280a`; commit `5021ee8` añade configuración Render. Esta preparación no prueba un despliegue y conserva autoría de Felipe. | `8c7def7` (API/serializers/PostgreSQL) y `d45d0f6` (reporte de pruebas backend). | PR y contenido de código sustentan integración/backend; el reporte académico de tests no prueba su repetición en el corte actual. |
| Vicente Monroy | QA / Development Team; pruebas, evidencias y apoyo | El registro QA manual actual sigue vacío. Las pruebas automatizadas del corte constan en `validacion_qa_2026-11-18.md`; no se atribuyen a Vicente. | `4a48d6e` (registro de defectos), `4281f79` (métricas/respuesta API), `6f1bf7b` (Review/Retrospective Sprint 1). Autor registrado: Vicente; committer registrado: `yaeaelo`. | Acredita autoría de documentos y seguimiento. La planilla asigna las correcciones de código a Felipe/Ismael. Las métricas requieren sus capturas/logs originales para validación independiente. |

## Correspondencias de PR

| PR | SHA/actividad original documentada | SHA equivalente publicado | Estado |
|---|---|---|---|
| #1 | `5023888`, `63865d2`, `9b04db0`; merge `e2f144f` | `6ff738c`, `4c64877`, `041f6f3`; merge `3bf2090` | Integrado; frontend React/API y checkout híbrido. |
| #2 | `6df926e`, `2d66714`, `7ad680a` | `f0c54f9`, `6883459`, `750e49e` | Cerrado tras comprobar equivalencias; no se fusionó el tip atrasado. |
| #3 | `6087f21`; merge `71abdfc` | `41f85b8`; merge `1553203` | Integrado; descarga privada R2 temporal. |

Los nombres `Yaelo` y `Elmetaleroxd` aparecen en commits históricos y no se normalizan automáticamente. Algunos commits documentales del saneamiento tienen atribución individual ambigua. Se conserva el historial y se evita usar conteos de commits como medida de esfuerzo.

## Evidencia de QA del corte previo

La [validación automatizada](validacion_qa_2026-11-18.md) registra resultados de `f017627`: 372 tests Django, 26 frontend, TypeScript/lint, build y smoke HTTP. No se repitieron sobre `5021ee8`, que agrega configuración Render; no es QA manual ni E2E real. El QA funcional que Vicente está ejecutando permanece separado y se incorpora al [registro de ejecución](qa/REGISTRO_EJECUCION_VICENTE.md) únicamente cuando entregue resultados reproducibles.


## Evidencia de trabajo externo del semestre

La exportación de WhatsApp del equipo respalda de forma complementaria la coordinación Scrum de Ismael, la integración React/Django reportada el 15-10 (ese día aún sin pruebas), el trabajo de producto/backend reportado por Felipe y la preparación de casos/capturas E2E de Vicente el 11-11. El archivo original E2E no se localizó y no se declaran resultados. La [matriz externa de contribuciones](https://github.com/yaeaelo/2026_2_MA_CAPSTONE_005D_GRUPO_4/blob/main/Fase%202/Evidencias%20Proyecto/Evidencias%20de%20documentaci%C3%B3n/matriz_contribuciones_externas.md) registra fechas, mensajes y límites probatorios. Esta evidencia no convierte un reporte conversacional en autoría de un commit salvo los vínculos específicos indicados por SHA en la matriz de autores.
