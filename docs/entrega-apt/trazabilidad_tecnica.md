# Trazabilidad de contribuciones técnicas

**Fuente:** objetos y referencias Git locales inspeccionados el 18-11-2026. Jira no estaba conectado; las incidencias no se usan como fuente de estado. Los alias de autor son los metadatos registrados por Git y no prueban por sí solos identidad o autoría exclusiva del contenido.

| Integrante indicado | Actividad técnica verificable | Archivos/componentes o referencias | Evidencia Git/Jira | Observaciones |
|---|---|---|---|---|
| Felipe Urtubia | Integración del PR #3 de almacenamiento privado/descargas R2 | Commit `71abdfc` (merge); rango integrado contiene cambios R2, previews, claims, permisos y tests | Mensaje de merge identifica `felipe-urtubia/feature/d8-r2-expiring-downloads`; PR #3 en mensaje Git. | Los commits de funcionalidad aparecen firmados como `Elmetaleroxd`; no se atribuye ese alias a Felipe sin evidencia adicional. |
| Vicente Monroy | No verificable con las fuentes disponibles | No se encontró autor Git coincidente en las referencias locales inspeccionadas. | Jira no disponible; sin issue/comentario verificable en este corte. | Esto no demuestra ausencia de trabajo; falta fuente verificable que conecte actividad y persona. |
| Ismael Araya | Integración del frontend React documentada en el historial local | Merge `e2f144f` (“Merge pull request #1 … integration/react-frontend”); cambios posteriores de frontend aparecen mayormente bajo otro autor Git. | Commit `e2f144f`, autor `Ismael Araya`. | El autor del merge prueba integración registrada, no autoría individual de todo el contenido fusionado. |

Otros metadatos relevantes: `Yaelo` figura en commits de organización de frontend y documentación, incluidos `a1294b9`, `c060b67`, `7ad680a`. `Elmetaleroxd` figura como autor de commits de producto, R2, Webpay, metadatos y pruebas. No se infieren nombres reales, porcentajes, dedicación ni equivalencias entre aliases.

## Commits incorporados en este corte

`origin/main` aporta 10 commits exclusivos respecto del punto de partida `frontend-trabajo` según comparación de ancestros local: integración de R2/Webpay (`01b3089`, `ea111ab`), migraciones y módulos R2, expiración de descargas (`6087f21`, `71abdfc`), registros técnicos (`00a792a`, `d0a0b6d`, `f721a33`) y el commit `ec00e2e` que añadió el archivo ZIP posteriormente retirado del árbol de trabajo.

La rama fuente `frontend-trabajo` se conserva como referencia de retorno. No se hizo push. El historial todavía contiene el objeto del ZIP y requiere tratamiento de seguridad antes de publicar.
