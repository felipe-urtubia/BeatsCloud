# Trazabilidad de contribuciones técnicas

**Fuente:** objetos y referencias Git locales inspeccionados el 18-11-2026. Jira no estaba conectado; las incidencias no se usan como fuente de estado. Los alias de autor son los metadatos registrados por Git y no prueban por sí solos identidad o autoría exclusiva del contenido.

| Integrante indicado | Actividad técnica verificable | Archivos/componentes o referencias | Evidencia Git/Jira | Observaciones |
|---|---|---|---|---|
| Felipe Urtubia | Autor de GitHub PR #3 y del merge de descargas R2 privadas; PR #3 incorpora descarga firmada temporal y tests | `8ab8c5e` (feature; nombre Git `Elmetaleroxd`, cuenta GitHub asociada `felipe-urtubia`); `416218f` (merge) | PR #3, autor `felipe-urtubia`, MERGED; GitHub asocia el commit del PR a esa cuenta. | No atribuir automáticamente todos los commits R2 previos a este PR ni trabajo no respaldado por autoría/PR. |
| Vicente Monroy | No verificable con las fuentes disponibles | No se encontró autor Git coincidente en las referencias locales ni autoría/review suyo en los PR inspeccionados. | PR GitHub #1–#3 sin review/comentario de Vicente; Jira no disponible. | Esto no demuestra ausencia de QA o documentación; falta evidencia enlazada a su identidad para atribuirla con certeza. |
| Ismael Araya | Autor de PR #1 de integración React-Django y PR #2 de subida/documentación; commits asociados usan el alias Git `Yaelo` | PR #1: `5023888`, `63865d2`, `9b04db0`, merge `3083b55`; PR #2: `9813ba7`, `7d6c9fc`, `383ecf1` | GitHub muestra `yaeaelo` / Ismael Araya como autor de PR #1 y PR #2; `3083b55` tiene autor Git Ismael Araya. PR #1 MERGED; PR #2 OPEN en la última consulta remota. | PR acredita autoría/integración registrada, no colaboración exclusiva en todo el código. PR #2 debe coordinarse antes de eliminar su rama remota. Los OID locales cambiaron al retirar rutas sensibles. |

Otros metadatos relevantes: GitHub vincula la cuenta `yaeaelo` (Ismael Araya) con PR #1 y PR #2; Git registra commits de esas contribuciones bajo `Yaelo`. GitHub vincula la cuenta `felipe-urtubia` con PR #3, cuyo commit aparece localmente como `Elmetaleroxd`. `Elmetaleroxd` firma además otros commits de producto, Webpay, metadatos y pruebas; no se asignan todos a Felipe sin evidencia individual de PR/autor. No se infieren porcentajes ni dedicación.

## Commits incorporados en este corte

Antes de consolidar, `origin/main` aportaba 10 commits exclusivos respecto de `frontend-trabajo`, entre ellos integración R2/Webpay (`41eaf57`, `d87cc5c`), descargas temporales (`8ab8c5e`, `416218f`) y registros técnicos (`5264328`, `2d915dd`, `dc7f408`). La rama `integration/reorganization-checkpoint` aportaba cuatro commits exclusivos (`9f4f85b`, `de4a79a`, `a907e41`, `53db43f`); se preservan como ascendencia de `main` mediante merge `ours`, sin aplicar su árbol antiguo. Estos son OID posteriores al saneamiento local.

Los commits de las ramas iniciales quedaron alcanzables desde `main` antes de retirar las referencias locales. Tras filtrar, desaparecieron localmente las referencias remotas de seguimiento; `origin` aún apunta a GitHub, que conserva las tres ramas verificadas en la auditoría. No se hizo push. El PR #2 seguía abierto en la última consulta; la coordinación de su cierre y sincronización remota queda pendiente. Los hashes originales afectados son referencias históricas previas a la limpieza.

## Preparación QA del corte 18-11-2026

Cambios locales de esta preparación: guard de DB QA (`app/management/commands/_qa_safety.py`), generación reproducible de catálogo sintético, cuentas QA temporales, pruebas de comandos, Compose y scripts bajo `scripts/qa/`, aislamiento de media/puerto y Vite proxy configurable. Registrados en `035298d` (`feat(qa): add isolated reproducible catalog and local environment`, 18-11-2026). Las guías/matrices se registran en un commit documental posterior. El autor de commit no demuestra colaboración exclusiva. La matriz QA y la plantilla no afirman ejecución de Vicente.
