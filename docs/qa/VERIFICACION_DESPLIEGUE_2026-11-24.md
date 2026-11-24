# Verificación de despliegue — 24-11-2026

**Fecha:** 2026-11-24 (UTC; consultas entre aproximadamente 22:32 y 22:41 UTC)\
**SHA de `main` antes del cambio documental:** `070cf3c491972b46f2ce4088d95a20667d426831`\
**SHA de `main` después del push documental:** `720cf6a5714385445ef480ae7ec6f01b7fb627fb`\
**Método:** solicitudes HTTP GET de solo lectura. No se enviaron formularios ni se hicieron operaciones POST, PUT, PATCH o DELETE.

| Caso | Ambiente/URL | Resultado observado | Límite |
|---|---|---|---|
| DEPLOY-01 | `https://beats-cloud.vercel.app/` | GET de solo lectura después del push documental: HTTP 200; página BeatsCloud y cabeceras de Vercel. | La respuesta no expone SHA ni metadato que permita asociarla inequívocamente con `main`. SHA desplegado: no verificado. |
| DEPLOY-02 | `https://beatscloud.onrender.com/api/session/` | HTTP 200; respuesta de 4 bytes (contenido no registrado); servicio responde con Gunicorn detrás de Cloudflare. | La respuesta no identifica el nombre/configuración del servicio Render, versión de backend, ambiente ni SHA. |
| DEPLOY-03 | `https://beatscloud.onrender.com/api/catalogo/` | HTTP 200; respuesta JSON de catálogo con 5 resultados reportados. | Solo comprueba lectura del endpoint. No identifica DB, almacenamiento, datos reales/de QA ni servicios externos. |
| DEPLOY-04 | Consulta de `main` en GitHub | El API público informó `070cf3c491972b46f2ce4088d95a20667d426831` antes del cambio documental y `720cf6a5714385445ef480ae7ec6f01b7fb627fb` después del push. | Confirma SHA fuente de GitHub, no el SHA del deployment de Vercel ni Render. |
| DEPLOY-05 | Consulta Jira anónima para DDPB-21 | Jira devolvió HTTP 404 a la API anónima. | No se pudo leer título, criterios o estado actual; se requiere acceso autenticado existente para sincronizar la matriz. |
| DEPLOY-06 | API pública de deployments de GitHub | HTTP 200, sin registros de deployment para el repositorio. | No permite asociar Vercel o Render con un SHA; no se modificaron configuraciones. |

La configuración versionada en `frontend/client/vercel.json` dirige `/api/`, `/media/`, `/csrf/` y `/session/` al host `beatscloud.onrender.com`. El hecho de que el endpoint responda no prueba que sea un entorno de QA. No se pudo comprobar si PostgreSQL está aislado de datos reales, si el almacenamiento es de prueba ni si pagos/correo/otros servicios externos están en modo de prueba.

**Decisión de seguridad para QA:** solo navegación y lectura. No iniciar sesión ni modificar perfiles, likes, favoritos, carrito, publicaciones o archivos; no iniciar Webpay ni compras. No realizar acciones de escritura hasta que el responsable del entorno confirme por un canal autorizado el SHA de cada deployment, su ambiente y aislamiento de base de datos, almacenamiento e integraciones.

**Evidencia de la consulta GitHub:** [referencia pública de `main`](https://api.github.com/repos/felipe-urtubia/BeatsCloud/commits/main). Las respuestas HTTP no se guardaron con cookies ni cabeceras de autenticación; no se imprimieron valores de sesión, claves o URLs firmadas.
