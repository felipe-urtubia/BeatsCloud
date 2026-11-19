# Documentación técnica de BeatsCloud

**Corte:** 18-11-2026 · **Código fuente:** `main` · `f017627fec99b2628e7753d3626ed33367836c5c`.

`felipe-urtubia/BeatsCloud` es la fuente de verdad del código vigente. La entrega académica y sus artefactos están en [el repositorio Capstone](https://github.com/yaeaelo/2026_2_MA_CAPSTONE_005D_GRUPO_4). Este índice resume la documentación técnica del producto; las evidencias académicas originales se mantienen en el repositorio de entrega y no se duplican aquí.

## Documentación vigente

| Documento | Alcance |
|---|---|
| [README de ejecución](../../README.md) | Requisitos, plantillas de entorno, instalación, servicios locales y comandos de prueba. |
| [Arquitectura](arquitectura.md) | Componentes actuales, flujo de sesión/CSRF, API JSON, rutas relevantes e integraciones. |
| [Modelo de datos y almacenamiento](modelo_datos_y_almacenamiento.md) | Modelos, migraciones, PostgreSQL, almacenamiento local/R2 y permisos de archivos. |
| [Validación QA 18-11-2026](validacion_qa_2026-11-18.md) | Ejecuciones automatizadas y HTTP locales; separa navegador y proveedores externos pendientes. |
| [Guía de operación de integraciones](operacion/GUIA_FELIPE_GRABACION.md) | Preparación de Webpay TEST y R2 de desarrollo, con secretos gestionados localmente. |
| [Guía QA](qa/GUIA_QA_VICENTE.md) | Entorno QA aislado, guardas, catálogo sintético y recolección segura de resultados. |
| [Matriz QA](qa/matriz_qa_funcional.md) | Casos funcionales pendientes de ejecución manual cuando no existe resultado registrado. |
| [Registro QA](qa/REGISTRO_EJECUCION_VICENTE.md) | Plantilla que debe completarse solo después de ejecutar cada caso. |
| [Plan de pruebas](plan_pruebas.md) | Casos, precondiciones, criterios y resultados históricos fechados. |
| [Trazabilidad de contribuciones](trazabilidad_tecnica.md) | Commits, PR y evidencias académicas individuales, con límites de atribución. |
| [Matriz interrepositorios](contribuciones_interrepositorios.md) | Relación entre evidencia del producto y de la entrega académica. |
| [Configuración y despliegue](despliegue_y_configuracion.md) | Configuración local y propuesta de despliegue; no acredita una publicación externa. |
| [Riesgos](plan_riesgos.md) | Riesgos conocidos y acciones pendientes, incluidas validaciones externas y saneamiento. |

## Estado de validación al corte

La ejecución documentada registró **372 pruebas Django**, **26 pruebas frontend**, `manage.py check`, comprobación de migraciones, TypeScript/lint, build y smoke HTTP local aprobados. Los detalles, comandos y límites están en [validación QA](validacion_qa_2026-11-18.md).

No se declaran aprobados por ese resultado: recorrido manual Firefox, compra y descarga de extremo a extremo, Webpay real, R2 real, SMTP real ni despliegue externo. El registro de Vicente permanece listo para los resultados que entregue; no completar casos anticipadamente.

## Configuración y seguridad

`.env.example` y `frontend/client/.env.example` son plantillas. Cada entorno crea sus archivos privados; `.env`, `.env.qa`, bases locales, credenciales, medios privados y builds no se publican. El ejemplo usa Webpay TEST y R2 desactivado. La rotación de credenciales que pudieron aparecer en historia anterior no se declara completada sin confirmación del custodio.

Los documentos de Scrum y evidencias individuales pertenecen al [repositorio académico](https://github.com/yaeaelo/2026_2_MA_CAPSTONE_005D_GRUPO_4); este repositorio conserva solo referencias técnicas necesarias para operar y justificar el código.
