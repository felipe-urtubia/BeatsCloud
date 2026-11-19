# Plan de riesgos técnicos — BeatsCloud

**Corte:** 19-11-2026. Este registro resume riesgos técnicos del producto y evidencia disponible; no atribuye responsables o planes de despliegue no respaldados.

| Riesgo | Evidencia/condición | Impacto | Control o tratamiento documentado | Estado al corte |
|---|---|---|---|---|
| Pago incompleto en integración real | Webpay Plus y conciliación existen en código; las suites usan dobles. No se acreditó transacción TEST, retorno SPA y descarga postpago en un flujo único. | Una aprobación, rechazo o retorno podrían no coincidir con el estado mostrado si se despliega sin prueba externa. | Django valida estado, monto, orden y relación de transacción; ejecutar QA de proveedor antes de habilitar un ambiente externo. | Implementación y pruebas simuladas; flujo E2E real no validado. |
| Persistencia de archivos cloud | R2 incluye presign, upload, confirmación y descarga firmada; no se probó contra bucket real. | El archivo puede no persistir, tener permisos incorrectos o no estar disponible tras el pago. | Bucket privado, políticas de acceso y expiración; validar subida, confirmación, persistencia y descarga en entorno de pruebas. | Flujo de código implementado; infraestructura real no validada. |
| Disponibilidad y recuperación de archivos | QA local sirve audio/medios; no hay evidencia de despliegue, backup ni restauración cloud. | Interrupción o pérdida de archivos/base en operación externa. | Definir almacenamiento persistente, respaldos y prueba de recuperación para cualquier despliegue. | No evaluado en infraestructura externa. |
| Seguridad de sesión y origen web | El código usa sesiones Django, cookies y CSRF; la configuración Vercel/Render no se probó desplegada. | Fallas de sesión o CSRF podrían bloquear o exponer acciones autenticadas. | Mantener HTTPS, orígenes permitidos y atributos de cookie/CSRF estrictos; comprobar sesión en el dominio final antes de publicar. | Código local probado; despliegue externo no acreditado. |
| Correo de cuenta | El equipo confirmó pruebas funcionales de activación y recuperación con proveedor externo; runner local utiliza backend de prueba. | Cambios de configuración/proveedor pueden impedir notificaciones en otro ambiente. | Mantener backend/proveedor configurado en entorno seguro y comprobar el envío en el ambiente objetivo. | Equipo confirma funcionamiento; auditoría local no repitió el envío. |
| Capacidad y experiencia de usuario | No se localizaron pruebas de usabilidad externa ni carga/concurrencia cloud. | Rendimiento y comprensión de flujos en escala real no conocidos. | Medir bajo entorno controlado antes de operación pública. | No evaluado en esta entrega. |

## Referencias

- [README e instalación](../../README.md)
- [Arquitectura](arquitectura.md) y [modelo de datos/almacenamiento](modelo_datos_y_almacenamiento.md)
- [Configuración](despliegue_y_configuracion.md)
- [Plan de pruebas](plan_pruebas.md) y [QA de cierre](validacion_qa_cierre_2026-11-19.md)
