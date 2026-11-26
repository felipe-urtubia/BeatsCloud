# Plan de revisión web de BeatsCloud

**Aplicación objetivo:** https://beats-cloud.vercel.app/\
**Tipo:** revisión manual de navegación y lectura desde navegador\
**Corte de código local:** `070cf3c491972b46f2ce4088d95a20667d426831` (24-11-2026)\
**Estado de ejecución:** no iniciada; todos los casos están pendientes de evidencia.

## Alcance de la primera ronda

La primera ronda observa las páginas y controles públicos: inicio y menú, catálogo y géneros, búsqueda de pistas y productores, detalle e información de pistas, filtros y orden visibles, previews, perfiles públicos, contacto/equipo y presentación adaptable. Los casos WEB-01 a WEB-10 de [la matriz trazable al backlog](MATRIZ_PRUEBAS_BACKLOG.md) vinculan cada observación con sus historias Jira.

La ronda es de solo lectura. No iniciar sesión, enviar formularios, editar datos, dar/quitar likes, cambiar el carrito, publicar/eliminar pistas, descargar originales, iniciar pagos ni subir archivos. No hace falta clonar el proyecto, instalar programas ni ejecutar scripts para esta revisión.

La configuración versionada de Vercel reescribe `/api/`, `/media/`, `/csrf/` y `/session/` a `https://beatscloud.onrender.com`. Las comprobaciones GET del 24-11-2026 confirmaron que Vercel sirve una página HTTP 200 y que ese host de Render responde en rutas de sesión y catálogo. No fue posible verificar el SHA de frontend desplegado, el servicio/configuración de Render, la versión exacta del backend, el ambiente, ni el aislamiento de base de datos, almacenamiento o integraciones. Por ello, el sitio no se considera un entorno QA identificado y no se autorizan operaciones que escriben datos. El detalle verificable está en [la revisión de despliegue](VERIFICACION_DESPLIEGUE_2026-11-24.md).

## Cómo registrar observaciones

Para cada ID de caso, registrar fecha/hora con zona horaria, URL, navegador y versión, resultado (`Pendiente`, `Observado sin anomalía`, `Problema` o `No comprobable`), pasos observados y nombre de evidencia saneada. La primera ronda no cambia Jira ni certifica criterios de aceptación. Si una función no está disponible o su historia no está terminada, registrar el comportamiento sin reportarlo como regresión de una función aceptada.

No incluir nombres personales en títulos ni capturas; ocultar datos personales, cookies, tokens, claves, encabezados de autorización y enlaces firmados. No guardar contenido de coordinación privada.

## Rondas posteriores

La segunda ronda cubre historias que crean o modifican datos, requieren autenticación/persistencia, servicios externos o escenarios E2E. Solo se agenda cuando el backend, la base de datos y los servicios involucrados estén identificados y aislados para QA. Los pagos requieren confirmación explícita de Webpay TEST y de su aislamiento. El detalle de dependencias está en la matriz; no ejecutar casos bloqueados por ambiente.

## Separación de evidencia

Registrar cada ejecución con SHA, fecha, ambiente, ID, resultado y evidencia. Mantener separadas estas clases:

- Pruebas automatizadas Django.
- Pruebas automatizadas frontend.
- Checks Django, migraciones, TypeScript/lint y build.
- Verificaciones HTTP de solo lectura.
- Revisión manual de navegador.
- Pruebas E2E con servicios externos.
- Pruebas de seguridad, usabilidad y rendimiento.

Los registros automatizados existentes son evidencia de sus propios SHA y entornos. No se trasladan a la ejecución web actual ni prueban el despliegue publicado.
