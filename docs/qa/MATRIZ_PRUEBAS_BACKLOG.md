# Matriz de pruebas trazable al backlog DDPB

## Fuente, alcance y estado

Proyecto Jira: [DDPB](https://beatscloud.atlassian.net/jira/software/projects/DDPB). **Fuente actualizada:** consulta autenticada del proyecto completo el 24-11-2026 con JQL `project = DDPB ORDER BY Rank ASC`. Se recuperaron las 91 incidencias del proyecto; el detalle de estados, responsables y hallazgos está en la [auditoría actual del backlog](auditorias/ESTADO_BACKLOG_2026-11-24_e652600.md). La auditoría histórica anterior se conserva separada y no se usa como estado vigente.

| Estado Jira al 24-11-2026 | Incidencias |
|---|---:|
| Finalizada | 58 |
| En curso | 13 |
| Tareas por hacer | 20 |
| **Total** | **91** |

El proyecto contiene 15 épicas, 55 historias y 21 tareas. Permanecen abiertas 33 incidencias. Esto describe el estado del backlog, **no** el resultado de una ejecución QA. En esta matriz, cada caso conserva su propio estado de ejecución y empieza en **Pendiente** hasta registrar evidencia nueva. Una historia pendiente o en curso no se reporta como regresión de una prestación aceptada; se registra como alcance abierto o comportamiento observado.

Los criterios de aceptación deben consultarse en Jira antes de aprobar un caso. La presencia de una pantalla, componente, endpoint o prueba automatizada no demuestra por sí sola que todos los criterios estén aceptados. No se actualizó ningún estado de Jira en esta revisión.

## Casos de primera ronda: navegación y lectura

Solo navegador sobre `https://beats-cloud.vercel.app/`. No iniciar sesión ni ejecutar acciones que puedan persistir datos. El resultado de todos los casos es Pendiente hasta registrar evidencia nueva.

| ID estable | Comprobación | Resultado esperado | Historias | Requisitos | Estado de ejecución |
|---|---|---|---|---|---|
| WEB-01 | Abrir inicio, recorrer menú y enlaces públicos. | Navegación y páginas responden según los AC Jira aplicables; registrar enlaces o secciones sin destino. | DDPB-20 | Sin autenticación; lectura; sin persistencia ni servicio externo esperado. | Pendiente |
| WEB-02 | Abrir catálogo y revisar géneros y datos visibles de pistas. | Catálogo, géneros y datos cumplen los AC vigentes; anotar estados vacíos o errores. | DDPB-21, DDPB-24, DDPB-25 | Sin autenticación; lectura HTTP; datos dependen del backend público. | Pendiente |
| WEB-03 | Buscar pistas y productores con términos disponibles. | Coincidencias y estado sin resultados cumplen los AC vigentes. | DDPB-22, DDPB-26 | Sin autenticación; lectura HTTP; depende de datos publicados. | Pendiente |
| WEB-04 | Abrir tarjetas y detalle de pistas; leer su información. | Datos presentados cumplen los AC vigentes, sin inferir aceptación a partir de campos presentes. | DDPB-27, DDPB-42, DDPB-43 | Sin autenticación; lectura HTTP; depende de datos publicados. | Pendiente |
| WEB-05 | Probar filtros y opciones de orden visibles sin alterar datos. | Para DDPB-70, los AC vigentes exigen que el endpoint acepte filtros/orden, que la SPA envíe esos parámetros sin filtrar en cliente y que los resultados estén paginados. La historia sigue en Tareas por hacer; no asumir que el contrato está implementado. DDPB-31 figura como duplicada/finalizada, no como capacidad independiente. | DDPB-23, DDPB-28, DDPB-29, DDPB-31, DDPB-70 | Sin autenticación; lectura HTTP; paginación/datos dependen del backend. | Pendiente |
| WEB-06 | Reproducir, pausar y reanudar previews; cambiar de pista si está disponible. | Audio y controles cumplen los AC; anotar errores de carga/reproducción. | DDPB-30 | Sin autenticación; lectura de preview; servicio de medios externo no confirmado. | Pendiente |
| WEB-07 | Abrir perfiles públicos de artista y recorrer información visible. | Presentación pública y navegación cumplen los AC vigentes. | DDPB-14, DDPB-33, DDPB-34, DDPB-35 | Sin autenticación; lectura; depende de datos publicados. | Pendiente |
| WEB-08 | Abrir perfiles públicos de productor y recorrer información visible. | Presentación pública, pistas y enlaces cumplen los AC vigentes. | DDPB-17, DDPB-37, DDPB-38, DDPB-39 | Sin autenticación; lectura; depende de datos publicados. | Pendiente |
| WEB-09 | Visitar secciones de contacto y equipo; probar enlaces sin enviar formularios. | Información y enlaces cumplen los AC vigentes; no enviar información. | DDPB-57, DDPB-58 | Sin autenticación; lectura; no enviar formularios ni contactar servicios. | Pendiente |
| WEB-10 | Revisar inicio, catálogo, búsquedas, detalle, perfiles y contacto en ventana amplia y estrecha. | Controles y contenido de cada área siguen siendo accesibles conforme a los AC aplicables. | DDPB-14, DDPB-17, DDPB-20, DDPB-21, DDPB-22, DDPB-23, DDPB-24, DDPB-25, DDPB-26, DDPB-27, DDPB-28, DDPB-29, DDPB-30, DDPB-31, DDPB-33, DDPB-34, DDPB-35, DDPB-37, DDPB-38, DDPB-39, DDPB-42, DDPB-43, DDPB-57, DDPB-58, DDPB-70 | Sin autenticación; lectura. | Pendiente |

## Casos de segunda ronda: requieren entorno identificado

No ejecutar hasta confirmar entorno de QA aislado. Los resultados esperados deben completarse contra los AC actuales de Jira antes de iniciar cada caso.

| ID estable | Comprobación | Resultado esperado | Historias | Requisitos | Estado de ejecución |
|---|---|---|---|---|---|
| QA-AUTH-01 | Registro, identificador, acceso, salida y recuperación de cuenta. | Cumplir AC Jira y conservar estados de sesión esperados. | DDPB-15, DDPB-16, DDPB-18, DDPB-19 | Autenticación; persistencia; correo/servicio externo según AC; cuentas sintéticas. | Pendiente; bloqueado por ambiente |
| QA-PROFILE-01 | Consultar/editar datos propios y comprobar persistencia; revisar privacidad de datos ajenos. | Cumplir AC Jira y permisos de lectura/escritura. | DDPB-47, DDPB-48 | Autenticación; persistencia; cuenta propia y datos de prueba. | Pendiente; bloqueado por ambiente |
| QA-PUBLISH-01 | Publicar y administrar pistas; comprobar metadatos, archivos, previews y eliminación según AC. | Cumplir AC Jira; conservar historial/propiedad que corresponda. | DDPB-40, DDPB-49, DDPB-50, DDPB-51, DDPB-52, DDPB-72 | Autenticación de productor; persistencia; almacenamiento/FFmpeg externo al navegador. | Pendiente; bloqueado por ambiente |
| QA-LIKE-01 | Agregar/quitar interacción y comprobar persistencia y privacidad. | Estado del servidor y presentación cumplen AC; manejo autorizado según rol. | DDPB-32, DDPB-36 | Autenticación; persistencia; cuenta y datos sintéticos. | Pendiente; bloqueado por ambiente |
| QA-CART-01 | Agregar/quitar pistas y verificar totales del carrito. | Cantidades y totales cumplen AC vigentes. | DDPB-44, DDPB-54, DDPB-56 | Autenticación/persistencia según AC; catálogo aislado. | Pendiente; bloqueado por ambiente |
| QA-PAY-01 | Checkout, aprobación, rechazo, cancelación y retorno. | Solo las respuestas autorizadas producen el estado definido en AC; sin transacción no válida. | DDPB-45, DDPB-53, DDPB-55, DDPB-67 | Autenticación; persistencia; Webpay TEST confirmado e aislado. | Pendiente; bloqueado por ambiente |
| QA-PURCHASE-01 | Consultar compras, licencias y acceso de descarga con cuenta/datos preparados. | Propiedad, estado de compra, licencia y permiso cumplen AC Jira; acceso denegado cuando corresponde. | DDPB-46, DDPB-71, DDPB-73 | Autenticación; persistencia; archivos y compra de QA autorizada; no crear compras para producir evidencia. | Pendiente; bloqueado por ambiente |
| QA-SUB-01 | Revisar ofertas y ejecutar escenarios de suscripción descritos por Jira. | Cumplir AC y estados de pago/contrato vigentes; no tratar historias abiertas como regresión. | DDPB-41, DDPB-59, DDPB-60, DDPB-61, DDPB-62, DDPB-63 | Autenticación; persistencia; servicio de pagos externo/TEST si aplica. | Pendiente; bloqueado por ambiente |
| QA-EXT-01 | Ejecutar escenarios externos definidos en el plan de QA y verificar integraciones. | Evidencia separada por servicio y vinculada a AC e historia. | DDPB-79, DDPB-82, DDPB-83, DDPB-85 | Servicios de prueba aislados; cuentas y archivos sintéticos. | Pendiente; bloqueado por ambiente |
| QA-USABILITY-01 | Sesiones moderadas con participantes y tareas acordadas. | Hallazgos observados, sin inventar participantes ni resultados. | DDPB-84 | Protocolo, participantes autorizados y datos no sensibles. | Pendiente |
| QA-PERF-01 | Medir los escenarios y umbrales acordados para audio/archivos. | Métricas reproducibles contra umbrales definidos en AC/plan Jira. | DDPB-86 | R2/bucket QA y carga sintética; parámetros y ambiente aislados. | Pendiente; bloqueado por ambiente |
| QA-EVIDENCE-01 | Revisar completitud, trazabilidad y entrega de evidencias. | Cada corrida referencia SHA, fecha, ambiente, ID, resultado y artefactos reales. | DDPB-78, DDPB-87 | Evidencias saneadas y vínculo a historia; no publicar secretos/datos personales. | Pendiente |

## Registro de cada ejecución

Crear un registro nuevo por corrida con: SHA completo observado, fecha/hora/zona horaria, URL y ambiente, ID estable, historia Jira, criterios de aceptación consultados, navegador/versión si aplica, resultado, pasos/observación y rutas de evidencia. No reutilizar resultados de otro SHA o ambiente. Usar `Pendiente` hasta que exista evidencia; diferenciar `Bloqueado por ambiente`, `No ejecutado`, `Fallido` y `Aprobado contra AC`.

## Separación de suites y evidencia

No mezclar: pruebas automatizadas Django; pruebas automatizadas frontend; `check`/migraciones/TypeScript/lint/build; verificaciones HTTP; revisión manual en navegador; E2E con servicios externos; seguridad; usabilidad; rendimiento. El registro histórico de `evidencias/qa/execution-notes/2026-11-24_8c35a74_execution.md` pertenece al SHA y entorno allí declarados, no al sitio Vercel ni a este corte.
