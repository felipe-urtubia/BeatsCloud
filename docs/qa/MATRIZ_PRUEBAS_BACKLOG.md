# Matriz de pruebas trazable al backlog DDPB

## Fuente, alcance y estado

Proyecto Jira: [DDPB](https://beatscloud.atlassian.net/jira/software/projects/DDPB). No hay una conexión autenticada a Jira disponible en esta sesión; la API anónima no permitió leer las historias. Se conserva como referencia el snapshot incluido en `BACKLOG_ISMAEL_CIERRE.md` (consulta del 24-11-2026, `main` en `0c4d316e0e2ac7fdc9fd9ef1fc9c4907f86f0c4b`) y los estados registrados en la matriz anterior del mismo corte. No se afirma que esos estados sigan vigentes. Antes de aceptar una historia, contrastar título, descripción, criterios de aceptación y estado con Jira actual.

Los resúmenes de comprobación de esta matriz indican el objeto de prueba a observar; no sustituyen los criterios de aceptación. Para historias cuyo AC no está transcrito en el snapshot disponible, el resultado esperado es **cumplir el AC vigente en Jira**, que debe consultarse antes de marcar aprobación. La presencia de una pantalla, componente o endpoint no demuestra aceptación. Cada resultado de ejecución empieza en **Pendiente**.

Estados históricos que sí aparecen en el snapshot: **Finalizada** (DDPB-31, 73, 78, 79), **En curso** (DDPB-53, 55, 67, 72, 83, 85, 87) y **Tareas por hacer** (DDPB-23, 28, 29, 32, 36, 46, 52, 59–63, 70, 71, 82, 84, 86). Para las demás claves el estado es **No verificable en el snapshot**. La matriz no actualiza Jira. Una historia pendiente o en curso no se reporta como regresión de una prestación aceptada; se registra como alcance pendiente o comportamiento observado.

## Casos de primera ronda: navegación y lectura

Solo navegador sobre `https://beats-cloud.vercel.app/`. No iniciar sesión ni ejecutar acciones que puedan persistir datos. El resultado de todos los casos es Pendiente hasta registrar evidencia nueva.

| ID estable | Comprobación | Resultado esperado | Historias | Requisitos | Estado de ejecución |
|---|---|---|---|---|---|
| WEB-01 | Abrir inicio, recorrer menú y enlaces públicos. | Navegación y páginas responden según los AC Jira aplicables; registrar enlaces o secciones sin destino. | DDPB-20 | Sin autenticación; lectura; sin persistencia ni servicio externo esperado. | Pendiente |
| WEB-02 | Abrir catálogo y revisar géneros y datos visibles de pistas. | Catálogo, géneros y datos cumplen los AC vigentes; anotar estados vacíos o errores. | DDPB-21, DDPB-24, DDPB-25 | Sin autenticación; lectura HTTP; datos dependen del backend público. | Pendiente |
| WEB-03 | Buscar pistas y productores con términos disponibles. | Coincidencias y estado sin resultados cumplen los AC vigentes. | DDPB-22, DDPB-26 | Sin autenticación; lectura HTTP; depende de datos publicados. | Pendiente |
| WEB-04 | Abrir tarjetas y detalle de pistas; leer su información. | Datos presentados cumplen los AC vigentes, sin inferir aceptación a partir de campos presentes. | DDPB-27, DDPB-42, DDPB-43 | Sin autenticación; lectura HTTP; depende de datos publicados. | Pendiente |
| WEB-05 | Probar filtros y opciones de orden visibles sin alterar datos. | Para DDPB-70, el snapshot histórico describe: API acepta filtros/orden; SPA envía esos parámetros sin filtrar en cliente; resultados paginados. Validar el contrato vigente en Jira antes de aprobar. DDPB-31 figura como duplicada/finalizada, no como capacidad independiente. | DDPB-23, DDPB-28, DDPB-29, DDPB-31, DDPB-70 | Sin autenticación; lectura HTTP; paginación/datos dependen del backend. | Pendiente |
| WEB-06 | Reproducir, pausar y reanudar previews; cambiar de pista si está disponible. | Audio y controles cumplen los AC; anotar errores de carga/reproducción. | DDPB-30 | Sin autenticación; lectura de preview; servicio de medios externo no confirmado. | Pendiente |
| WEB-07 | Abrir perfiles públicos de artista y recorrer información visible. | Presentación pública y navegación cumplen los AC vigentes. | DDPB-14, DDPB-33, DDPB-34, DDPB-35 | Sin autenticación; lectura; depende de datos publicados. | Pendiente |
| WEB-08 | Abrir perfiles públicos de productor y recorrer información visible. | Presentación pública, pistas y enlaces cumplen los AC vigentes. | DDPB-17, DDPB-37, DDPB-38, DDPB-39 | Sin autenticación; lectura; depende de datos publicados. | Pendiente |
| WEB-09 | Visitar secciones de contacto y equipo; probar enlaces sin enviar formularios. | Información y enlaces cumplen los AC vigentes; no enviar información. | DDPB-57, DDPB-58 | Sin autenticación; lectura; no enviar formularios ni contactar servicios. | Pendiente |
| WEB-10 | Revisar los mismos recorridos en ventana amplia y estrecha. | Controles y contenido siguen siendo accesibles conforme a los AC aplicables. | Transversal; relacionar los defectos con las historias pertinentes | Sin autenticación; lectura. | Pendiente |

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
