# Cierre técnico del backlog de Ismael

**Auditoría:** 24 de noviembre de 2026, 15:53 (-03)

**Repositorio:** `felipe-urtubia/BeatsCloud`

**Base revisada:** `origin/main` = `17ca427de31c57277b4174772fca62651c828ec4`

**Rama de trabajo:** `feature/ismael-backlog-close-2026-11-24`
**Commit de código validado:** `153337726337f62725ddc53d8f97d7ccf3935073`

## Acceso a Jira

Se proporcionó `https://beatscloud.atlassian.net/jira/software/projects/DDPB`. La página no es accesible desde esta sesión; no hay una integración Jira disponible y la búsqueda web no devuelve los tickets privados. Por eso no pude cotejar las descripciones ni los criterios oficiales literales. Este cierre usa los criterios que Ismael incluyó en la solicitud. Jira no fue modificado y no se cerró ningún ticket.

## Estado inicial y conservación

- `origin/main` y el SHA base confirmado por el usuario eran `17ca427de31c57277b4174772fca62651c828ec4`.
- El checkout principal `main` estaba atrasado y tenía cambios locales/no rastreados. No se cambió ni se limpió.
- La implementación se hizo en un worktree nuevo, limpio, basado en el SHA anterior. El commit validado conserva ese ancestro.
- No se tocaron el repositorio académico ni otros worktrees.

## Historias

| Ticket | Estado inicial y criterios de la solicitud | Implementación y archivos | Estado técnico |
|---|---|---|---|
| **DDPB-23 — Filtros de catálogo** | El catálogo ya consultaba pistas reales en modo híbrido. React descargaba sus páginas y filtraba en cliente por género, tipo, tonalidad/mood, BPM, stems y precio; combinaba filtros y reiniciaba la página al cambiar criterios. El endpoint actual expone búsqueda, género y precio, con paginación. | Se conserva el filtrado frontend que opera sobre datos backend reales y la paginación local sobre la colección completa ya cargada. No se añadió un segundo contrato backend. | Los criterios de UI descritos están cubiertos. Los filtros BPM/tipo/mood no son server-side; si el criterio oficial exige filtrado remoto, depende del contrato DDPB-70. |
| **DDPB-28 — Orden ascendente/descendente** | Ya existían órdenes ascendentes/descendentes por BPM, precio y nombre, además de fechas recientes/antiguas. | Se extrajo la ordenación reutilizable a `frontend/client/src/utils/catalogSort.mjs`; se mantiene el comportamiento existente. | Cubierto en frontend con datos backend. El ordenamiento remoto sigue siendo parte de la dependencia DDPB-70. |
| **DDPB-29 — Orden por género** | No había opción para ordenar por género. | Se añadieron `Género A-Z` y `Género Z-A`, con título como criterio secundario estable, en `CatalogPage.tsx` y `catalogSort.mjs`. | Implementado en frontend; orden remoto pendiente de DDPB-70 si lo requiere el criterio oficial. |
| **DDPB-46 — Historial de compras** | La UI derivaba una orden `WEBPAY-<id de historial>` y mostraba el precio actual de la pista; esos datos no probaban el monto ni el estado real de la transacción. | Se añadió `GET /api/mis-compras/confirmadas/` en `app/api_shim.py`. Devuelve solo compras propias con transacción Webpay autorizada y entregada, snapshot válido cuyo monto coincide y registro `HistorialCompra` asociado. Incluye orden real, fecha, estado, productor, monto de línea y total; no serializa token Webpay. React consume esos datos y desactiva la descarga cuando no está configurada/disponible. Rutas frontend: `django.service.ts`, `types.ts`, `mappers.ts`, `AppContext.tsx`, `ArtistProfilePage.tsx`. | Implementado para compras de pistas confirmadas. Historial antiguo sin transacción/snapshot verificable no se simula ni se presenta como confirmado. |
| **DDPB-32 — Likes de pistas** | La interacción anterior era optimista y llamaba un endpoint toggle, lo que no era idempotente frente a reintentos y no daba feedback consistente. | El endpoint acepta `liked: boolean` para agregar/quitar idempotentemente, exige artista autenticado y conserva compatibilidad con toggle legado. React envía el estado deseado, actualiza de inmediato, bloquea clics repetidos, muestra estado pendiente y notificación, y revierte si falla. | Persistencia backend y permisos implementados. |
| **DDPB-36 — Lista de pistas interesadas** | Existía una pestaña de favoritos, pero no había acción para quitar y el listado podía mostrar favoritos del perfil consultado. | `ArtistProfilePage.tsx` limita la lista al dueño, muestra vacío y añade quitar favorito usando la API persistente de DDPB-32; mantiene título, productor, precio y acceso al detalle. En modo mock aclara que no hay persistencia real. | Implementado e integrado con DDPB-32; no se crea un segundo modelo/end-point. |

### Relación con DDPB-70

La API de catálogo actual entrega datos reales y admite búsqueda, género, precio y páginas. No admite server-side BPM, tipo, mood ni todo el conjunto de ordenamientos solicitado por DDPB-70. React carga todas las páginas y filtra/ordena esa colección en cliente, así que no se agregó otra implementación backend ni se afirma que DDPB-70 esté terminado. Si DDPB-23/28/29 exigen sincronización remota/server-side, quedan condicionados al contrato y trabajo de DDPB-70.

## Archivos modificados

- Backend: `app/api_shim.py`; pruebas nuevas `app/test_backlog_assigned_features.py`.
- Tipos/API/contexto: `frontend/client/src/api/django.service.ts`, `mappers.ts`, `types.ts`, `context/AppContext.tsx` y `frontend/client/src/types.ts`.
- UI: `ArtistProfilePage.tsx`, `CatalogPage.tsx`, `DiscoverPage.tsx`, `GlobalAudioPlayer.tsx`, `TrackDetailModal.tsx`.
- Ordenación y pruebas frontend: `frontend/client/src/utils/catalogSort.mjs`, `catalogSort.d.mts`, `catalogSort.test.mjs`; actualización del comando `test` en `frontend/client/package.json`.

No se añadieron migraciones.

## Validación en el commit de código

En `153337726337f62725ddc53d8f97d7ccf3935073`:

- Pruebas Django completas: **507/507 aprobadas**.
- Pruebas frontend: **44/44 aprobadas**.
- Pruebas focalizadas nuevas de compras/likes: **8/8 aprobadas**.
- `manage.py check`: correcto.
- `makemigrations --check --dry-run`: sin cambios de migración.
- TypeScript/lint (`npm run lint`): correcto.
- Build (`npm run build`): correcto; queda el aviso existente del bundle principal de ~507.5 kB.
- Smoke local: Vite y proxy/API HTTP 200; catálogo y preview HTTP 200; descarga anónima HTTP 403.
- Servicios QA detenidos; la base QA y sus medios persistentes se conservaron.
- `git diff --check`: correcto.

El `run-all.sh` heredado de `origin/main` se detuvo en requisitos al considerar ocupado el puerto 8010 tras una corrida previa, aunque no había un listener. Para validar el commit no se ocultó ese resultado: se ejecutó `verify.sh --no-smoke` completo y luego `start.sh`, smoke y `stop.sh` secuencialmente. La rama PR #5 actualiza la detección de puertos para comprobar listeners y ya tiene su propia corrida completa aprobada; se debe mantener ese cambio al integrar ambas ramas.

La suite no incluye pruebas automatizadas de interacción React en navegador para estas pantallas; los cambios frontend se cubrieron con pruebas de utilidades, API/contexto existente, TypeScript, lint, build y smoke local. Se recomienda revisión manual de likes, favoritos e historial antes de cerrar Jira.

## Pendientes, riesgos y estado de integración

1. Consultar los criterios oficiales de Jira cuando el proyecto sea accesible. No cerrar historias basándose solo en esta descripción resumida.
2. Coordinar DDPB-70 para decidir el contrato server-side de filtros, ordenamiento y paginación. No marcar esa parte como entregada por estos cambios frontend.
3. Revisar manualmente los flujos de UI con una compra autorizada de QA y una cuenta artista; la ejecución local no hace una compra real.
4. El historial no muestra filas antiguas sin prueba verificable de transacción autorizada y entrega.
5. El aviso de bundle frontend de ~507.5 kB permanece.
6. La rama está preparada para PR hacia `main`; este commit todavía no está integrado. No se actualizó `main`, no se hizo merge, no se modificó Jira y no se desplegó producción.

## SHA

El commit que contiene el código y fue validado es `153337726337f62725ddc53d8f97d7ccf3935073`. El PR y cualquier commit de documentación posterior deben conservar esa referencia como SHA del código probado.
