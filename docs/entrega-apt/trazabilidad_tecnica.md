# Trazabilidad de contribuciones técnicas

**Fuente:** objetos y referencias Git locales inspeccionados el 18-11-2026. Jira no estaba conectado; las incidencias no se usan como fuente de estado. Los alias de autor son los metadatos registrados por Git y no prueban por sí solos identidad o autoría exclusiva del contenido.

| Integrante indicado | Actividad técnica verificable | Archivos/componentes o referencias | Evidencia Git/Jira | Observaciones |
|---|---|---|---|---|
| Felipe Urtubia | Autor de GitHub PR #3 y del merge de descargas R2 privadas; PR #3 incorpora descarga firmada temporal y tests | `6087f21` (feature; nombre Git `Elmetaleroxd`, cuenta GitHub asociada `felipe-urtubia`); `71abdfc` (merge) | PR #3, autor `felipe-urtubia`, MERGED; GitHub asocia el commit del PR a esa cuenta. | No atribuir automáticamente todos los commits R2 previos a este PR ni trabajo no respaldado por autoría/PR. |
| Vicente Monroy | No verificable con las fuentes disponibles | No se encontró autor Git coincidente en las referencias locales ni autoría/review suyo en los PR inspeccionados. | PR GitHub #1–#3 sin review/comentario de Vicente; Jira no disponible. | Esto no demuestra ausencia de QA o documentación; falta evidencia enlazada a su identidad para atribuirla con certeza. |
| Ismael Araya | Autor de PR #1 de integración React-Django y PR #2 de subida/documentación; commits asociados usan el alias Git `Yaelo` | PR #1: `d3d6e0d`, `84ded7c`, `7b0424a`, merge `e2f144f`; PR #2: `6df926e`, `2d66714`, `7ad680a` | GitHub muestra `yaeaelo` / Ismael Araya como autor de PR #1 y PR #2; `e2f144f` tiene autor Git Ismael Araya. PR #1 MERGED; PR #2 OPEN. | PR acredita autoría/integración registrada, no colaboración exclusiva en todo el código. PR #2 requiere decisión coordinada antes de eliminar su rama. |

Otros metadatos relevantes: GitHub vincula la cuenta `yaeaelo` (Ismael Araya) con PR #1 y PR #2; Git registra commits de esas contribuciones bajo `Yaelo`. GitHub vincula la cuenta `felipe-urtubia` con PR #3, cuyo commit aparece localmente como `Elmetaleroxd`. `Elmetaleroxd` firma además otros commits de producto, Webpay, metadatos y pruebas; no se asignan todos a Felipe sin evidencia individual de PR/autor. No se infieren porcentajes ni dedicación.

## Commits incorporados en este corte

`origin/main` aportaba 10 commits exclusivos respecto de `frontend-trabajo` antes de esta consolidación local: integración R2/Webpay (`01b3089`, `ea111ab`), migraciones y módulos R2, descargas temporales (`6087f21`, `71abdfc`), registros técnicos (`00a792a`, `d0a0b6d`, `f721a33`) y `ec00e2e`, que reintrodujo el ZIP retirado del árbol de trabajo. La rama `integration/reorganization-checkpoint` contiene además cuatro commits exclusivos (`a1294b9`, `91262ba`, `c72ed1e`, `c060b67`); se evaluarán sus cambios de estructura frente al árbol actual antes de consolidar.

La rama fuente `frontend-trabajo` se conserva como referencia de retorno. No se hizo push. El historial todavía contiene el objeto del ZIP y requiere tratamiento de seguridad antes de publicar.
