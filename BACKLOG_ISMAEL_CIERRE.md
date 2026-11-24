# Auditoría de cierre del backlog de Ismael

**Fecha de auditoría:** 24 de noviembre de 2026  
**Repositorio:** `felipe-urtubia/BeatsCloud`  
**Proyecto Jira:** [DDPB — Desarrollo de plataforma BeatsCloud](https://beatscloud.atlassian.net/jira/software/projects/DDPB)  
**Rama revisada:** `main`  
**HEAD de main revisado:** `0c4d316e0e2ac7fdc9fd9ef1fc9c4907f86f0c4b`  
**PR de implementación:** [#6 — Complete artist backlog features](https://github.com/felipe-urtubia/BeatsCloud/pull/6)  
**Commit de código validado antes de integrar:** `153337726337f62725ddc53d8f97d7ccf3935073`

> Esta auditoría contrasta el estado de Jira con el código disponible en `main`. No equivale a una certificación manual del despliegue ni autoriza cerrar historias cuya validación funcional siga pendiente.

## 1. Resultado ejecutivo

La consulta de Jira para todos los elementos asignados a Ismael en el proyecto DDPB encontró como elementos no finalizados:

- Épicas: **DDPB-4 (Catálogo)** y **DDPB-5 (Perfil de artista)**, ambas «En curso».
- Historias/tareas: **DDPB-23, DDPB-28, DDPB-29, DDPB-32, DDPB-36 y DDPB-46**, todas en «Tareas por hacer».

No se encontraron otras historias o tareas abiertas asignadas a Ismael fuera de esos seis tickets. Los demás elementos devueltos por la consulta están en «Finalizada».

El código de los seis tickets fue integrado a `main` mediante PR #6. Sin embargo, eso no significa que las seis historias puedan pasar directamente a «Finalizada»:

- **DDPB-23/28/29:** cubiertas parcialmente en frontend; el alcance server-side depende de DDPB-70, asignado a Felipe.
- **DDPB-32/36:** implementación persistente integrada; falta validación manual en navegador. Las etiquetas `postergado` reflejan que originalmente quedaron fuera del alcance comprometido para la APT del 19-11, aunque su implementación se incorporó después.
- **DDPB-46:** historial de compras confirmadas implementado; falta validar el recorrido funcional postpago/descarga con una compra de QA autorizada y entorno aislado.

## 2. Estado por ticket

| Ticket | Estado en Jira | Evidencia encontrada en `main` | Diagnóstico y siguiente paso |
|---|---|---|---|
| **DDPB-23 — Filtros del catálogo** | Tareas por hacer | `CatalogPage.tsx` aplica filtros por género, tonalidad, mood, BPM, stems y precio sobre pistas cargadas. `catalogo_api` ofrece búsqueda, género, precio, orden limitado y paginación. | Parcial frente al requisito server-side. Acordar DDPB-70 antes de cerrar. |
| **DDPB-28 — Orden ascendente/descendente** | Tareas por hacer | `catalogSort.mjs` ordena en frontend por BPM, precio y nombre, además de fechas. | Implementado en frontend; ordenamiento remoto/paginación server-side queda ligado a DDPB-70 si ese alcance sigue vigente. Validar en navegador. |
| **DDPB-29 — Orden por género** | Tareas por hacer | `CatalogPage.tsx` incorpora Género A-Z y Género Z-A. `catalogSort.test.mjs` prueba orden, desempate estable por título y no mutación del arreglo original. | Implementado en frontend; validar en navegador. La variante server-side depende de DDPB-70. |
| **DDPB-32 — Like de una pista** | Tareas por hacer; etiqueta `postergado` | `like_toggle_api` acepta `liked: true/false`, restringe la operación a artistas autenticados y permite agregar/quitar de forma idempotente. React actualiza optimistamente, evita solicitudes duplicadas y muestra feedback/reversión. | Implementación integrada y pruebas de API presentes. Falta validar agregar/quitar, persistencia tras recarga y rechazo a cuentas no autorizadas en navegador. |
| **DDPB-36 — Lista de pistas interesadas** | Tareas por hacer; etiqueta `postergado` | `ArtistProfilePage.tsx` muestra favoritos solo al propietario, permite quitarlos y reutiliza la API de DDPB-32. | Implementación integrada. Falta validar persistencia tras recarga y privacidad entre perfiles. |
| **DDPB-46 — Historial de compras** | Tareas por hacer | `GET /api/mis-compras/confirmadas/` devuelve solo líneas de órdenes propias autorizadas y entregadas, con snapshot/montos coherentes e historial asociado. La respuesta incluye referencia, fecha, productor y montos, sin exponer el token Webpay. | Implementación integrada para compras verificables. Falta E2E manual postpago/descarga; el historial antiguo sin transacción verificable no se presenta como compra confirmada. |

### Detalles de DDPB-70 y el catálogo

La descripción oficial de DDPB-70 establece estos criterios:

1. El endpoint de catálogo acepta parámetros de filtro y orden.
2. La SPA usa esos parámetros, sin filtrar en el cliente.
3. Los resultados están paginados.

El código actual **no completa ese contrato**. El endpoint `catalogo_api` soporta `q`, `genero`, `precio`, órdenes limitados y `page`, pero no el conjunto server-side de BPM, tipo y mood que pide DDPB-70. La SPA continúa filtrando/ordenando la colección cargada en el cliente.

DDPB-70 está asignado a **Felipe**, permanece en «Tareas por hacer», tiene 3 puntos y pertenece al Sprint 4. Su prioridad en Jira es **Must**. Existe, además, un comentario del 19-11 que dice que puede quedar para una siguiente iteración y que no bloquea el cierre académico. Esta diferencia entre prioridad Must y postergación debe resolverse explícitamente con Felipe; no debe inferirse ni cambiarse unilateralmente.

DDPB-31 está marcado como duplicado de DDPB-23 y aparece finalizado en Jira.

## 3. Estado de las épicas

| Épica | Estado | Historias relacionadas | Diagnóstico |
|---|---|---|---|
| **DDPB-4 — Catálogo** | En curso | DDPB-21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32 y DDPB-70 | No cerrar hasta acordar el alcance server-side de DDPB-70 y el estado final de DDPB-23/28/29. |
| **DDPB-5 — Perfil de artista** | En curso | DDPB-14, 33, 34, 35 y 36 | Las historias antiguas están finalizadas; DDPB-36 tiene implementación integrada, pero requiere validación manual y actualización de Jira antes de cerrar la épica. |
| **DDPB-10 — Carrito de compra** | En curso | Incluye DDPB-46 y otras historias/tareas asignadas a Felipe | DDPB-46 es responsabilidad de Ismael; el cierre de la épica depende también del trabajo de Felipe y no corresponde cerrarla unilateralmente. |

## 4. Evidencia técnica disponible

El código de PR #6 fue validado en el commit `153337726337f62725ddc53d8f97d7ccf3935073`, que quedó integrado en `main` mediante el merge `0c4d316e0e2ac7fdc9fd9ef1fc9c4907f86f0c4b`.

Resultados registrados para el commit de código:

- Django: **507/507 pruebas aprobadas**.
- Frontend: **44/44 pruebas aprobadas**.
- Pruebas focalizadas nuevas de compras/likes: **8/8 aprobadas**.
- `manage.py check`: correcto.
- `makemigrations --check --dry-run`: sin cambios de migración.
- TypeScript/lint (`npm run lint`): correcto.
- Build (`npm run build`): correcto; permanece un aviso del bundle principal de aproximadamente 507,5 kB.
- Smoke local: Vite, proxy/API, catálogo y preview respondieron HTTP 200; descarga anónima respondió HTTP 403.
- `git diff --check`: correcto.

**Límite de esta evidencia:** las suites no contienen pruebas automatizadas de interacción React en navegador para estas pantallas. Las pruebas de API cubren compras/likes y las pruebas frontend incluyen utilidades como ordenamiento, pero no sustituyen la validación visual/funcional manual. No se ejecutó una compra Webpay E2E real.

## 5. Validación manual pendiente

Antes de pedirle a Vicente que pruebe la aplicación, debe identificarse la versión exacta desplegada y confirmar que el backend y la base de datos sean seguros para QA.

### Precondiciones

- Confirmar el SHA desplegado en Vercel y compararlo con el commit que se desea validar.
- Confirmar qué backend Render utiliza ese frontend.
- Verificar que la base de datos sea de QA o que exista autorización explícita para las operaciones previstas.
- No realizar compras reales ni ingresar datos bancarios/personales.
- No crear, publicar, eliminar ni modificar datos persistentes hasta confirmar el aislamiento del entorno.

### Casos por validar

| Área | Caso | Resultado esperado |
|---|---|---|
| DDPB-28/29 | Cambiar orden por BPM, precio, nombre y género | Orden correcto, sin duplicados ni saltos inesperados. |
| DDPB-32 | Agregar y quitar like como artista; recargar | Estado persiste y el feedback coincide con el servidor. |
| DDPB-32 | Probar como productor o sin autenticación | La acción no queda permitida. |
| DDPB-36 | Revisar favoritos del propio perfil, quitar uno y recargar | La lista se actualiza y conserva el cambio. |
| DDPB-36 | Visitar el perfil público de otro artista | No se muestran sus favoritos privados. |
| DDPB-46 | Con orden de QA previamente autorizada y entregada | Aparecen referencia, pista, productor, fecha y montos correctos. |
| DDPB-46 | Revisar descarga de una compra válida | Descarga permitida solo si el archivo sigue disponible y la compra pertenece a la cuenta. |

Los casos de DDPB-46 requieren datos de QA preparados de manera segura; no se debe crear una transacción real para producir evidencia académica.

## 6. Decisiones que requieren coordinación con Felipe

1. **DDPB-70:** ¿se implementa el filtrado server-side completo o se formaliza su postergación? Resolver el conflicto entre prioridad Must y el comentario de aplazamiento.
2. **DDPB-23/28/29:** según esa decisión, definir qué parte queda aceptada, qué parte permanece pendiente y si las historias se mantienen separadas o se agrupan con DDPB-70.
3. **DDPB-46:** confirmar que el flujo postpago y la descarga están integrados en el entorno de QA para permitir una validación E2E segura.
4. **Cierre de épicas:** DDPB-4 depende de DDPB-70; DDPB-5 depende de validar y cerrar DDPB-36; DDPB-10 incluye trabajo adicional que no pertenece a Ismael.

## 7. Acciones que Ismael puede completar sin Felipe

- Mantener este informe actualizado contra el SHA de `main`.
- Preparar la lista y los resultados esperados de pruebas manuales, sin ejecutarlas contra un despliegue no identificado.
- Coordinar con Vicente una revisión de navegador después de confirmar versión y entorno de QA.
- Tras obtener evidencia de pruebas, actualizar comentarios/estados de DDPB-32, DDPB-36 y DDPB-46.
- No modificar DDPB-70 ni cerrar DDPB-23/28/29 o la épica DDPB-4 hasta la decisión de Felipe.

## 8. Registro de cambios y límites

Esta auditoría **no cambia estados de Jira**, no modifica datos de producción, no crea compras y no declara como realizada ninguna prueba manual. Jira conserva los estados actuales hasta que exista evidencia funcional y, en los tickets dependientes, una decisión de equipo.

El despliegue actual de Vercel/Render no quedó vinculado en esta auditoría a un SHA concreto. Por tanto, no se afirma que `https://beats-cloud.vercel.app/` corresponda a `0c4d316` ni que sea la versión definitiva de entrega.
