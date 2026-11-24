# Documentación técnica de BeatsCloud

La guía de instalación y ejecución está en el [README principal](../../README.md). Esta sección conserva la arquitectura real, configuración, pruebas y límites técnicos del producto.

## Documentos

- [Arquitectura y endpoints](arquitectura.md)
- [Modelo de datos y almacenamiento](modelo_datos_y_almacenamiento.md)
- [Configuración local e integraciones](despliegue_y_configuracion.md)
- [Plan de pruebas](plan_pruebas.md)
- [Ejecución QA de cierre](validacion_qa_cierre_2026-11-19.md)
- [Validación HTTP local del 18-11](validacion_tecnica_corte_2026-11-18.md)
- [Riesgos técnicos](plan_riesgos.md)
- [Visión y alcance observable](vision_producto.md)
- [Plan de primera revisión web](../qa/PLAN_REVISION_WEB.md)
- [Matriz de pruebas trazable al backlog DDPB](../qa/MATRIZ_PRUEBAS_BACKLOG.md)
- [Verificación del despliegue público, 24-11-2026](../qa/VERIFICACION_DESPLIEGUE_2026-11-24.md)

## Estado técnico

La SPA React/TypeScript/Vite se conecta a una API JSON propia en Django, con PostgreSQL, sesiones y CSRF. En el SHA `ee981a750904b4263b20be2f91e3568c0e1699ea` aprobaron 372 pruebas Django, 26 frontend, checks, migraciones, TypeScript, lint y build Vite. Webpay Plus tiene implementación y pruebas automatizadas con dobles; no se completó una compra E2E. El flujo R2 de presign, subida directa, confirmación y descarga firmada está en código, pero no se validó contra un bucket real. Felipe confirmó pruebas funcionales del equipo para registro/correo de activación, recuperación/cambio de contraseña y eliminación de cuenta; las suites locales usan correo en memoria/consola y no repiten esa integración externa.

`.env.example` y `frontend/client/.env.example` son plantillas versionadas sin credenciales reales. Los archivos `.env` y `.env.qa` contienen configuración local y no deben incluirse en Git.
