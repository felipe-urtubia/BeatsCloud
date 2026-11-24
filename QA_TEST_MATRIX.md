# Matriz de ejecución QA — Vicente

**Base anterior validada:** SHA `8c35a74f899b284edb521d3da5cd2d5b79357bcf`. Para una corrida nueva, registrar el SHA final mostrado por `git rev-parse HEAD` y el informe generado por `scripts/qa/run-all.sh`.

**Para esta entrega:** cada corrida nueva genera informe HTML y Markdown en `evidencias/qa/runs/<fecha>/`; los logs técnicos quedan en `.qa-private/runs/<fecha>/`. Completa el sistema operativo, el SHA completo y el tipo de evidencia en cada nota. En Windows 11 no marques casos como ejecutados hasta completar la verificación manual de `docs/qa/GUIA_PRUEBAS.md`.

Tipos: **A-mock** automatizada con dobles; **F-local** funcional local; **I-ext** integración de servicio externo; **M-usuario** manual con usuarios; **NE** no ejecutada en este plan. Los resultados anteriores de otro SHA se identifican aparte.

| ID / Área | Tipo | Escenario y criterio | Resultado esperado | Estado de partida | Evidencia a guardar |
|---|---|---|---|---|---|
| QA-01 Autenticación | F-local | Login con cuenta creada por `prepare_qa_users` | Sesión autorizada, identidad y perfil correctos | Por ejecutar en este corte | Captura sin datos sensibles + nota HTTP/log |
| QA-02 Registro | A-mock / I-ext | Alta con token válido e inválido; en local registrar límites del Turnstile | Token aceptado/rechazado según configuración | Suite automatizada existente; proveedor local deshabilitado | Reporte test; captura/log sanitizado |
| QA-03 Catálogo | F-local | Cargar, paginar y abrir una pista semilla | Pistas visibles y página navegable | Evidencia Selenium histórica ee981a7 para catálogo; repetir para nuevo corte | Captura/vídeo y JSON HTTP |
| QA-04 Búsqueda/filtros | F-local | Texto, género, precio; comparar UI y API | Resultados coherentes con filtros soportados | Backend soporta q/género/precio; BPM/tipo/mood server-side faltan | Captura y URL/JSON de API |
| QA-05 Preview | F-local | Reproducir, pausar y retomar preview | Controles reflejan audio; sin errores de fuente | Evidencia posterior 22-11 reportada; repetir local si archivo generado | Vídeo y log de red sin cookies |
| QA-06 Carrito agregar/quitar | F-local | Agregar pista y retirar; revisar totales | Estado y subtotal/IVA/total se actualizan y se persisten conforme contrato | Selenium histórico ee981a7 cubrió carrito; repetir | Capturas antes/después |
| QA-07 Seguridad descarga anónima | A-mock y F-local | GET descarga sin sesión | Denegación HTTP (403 esperado para archivo completo) | Automatizada histórica; ejecución local nueva pendiente | Salida HTTP sin URL firmada/token |
| QA-08 Seguridad usuario sin compra | A-mock / I-ext | Usuario autenticado sin compra intenta original | Denegación | Registro 22-11 informa HTTP 403 en entorno de integración; no repetir aquí | Log HTTP sanitizado y nota de cuenta de test |
| QA-09 Like | F-local | Activar/desactivar like y recargar | Estado persiste y errores se comunican | Hay endpoint/estado optimista; error sin aviso observado en código | Vídeo + solicitud/respuesta |
| QA-10 Subida | F-local | Productor carga audio válido y revisa resultado | Progreso/estado terminal comprensible, pista disponible | Depende de formatos/herramientas locales; storage QA es local | Vídeo, log Django, metadatos; no subir audio privado |
| QA-11 Perfil productor | F-local | Actualizar datos/listado según permisos | Confirmación o error visible; datos persistidos | Por ejecutar en este corte | Capturas antes/después |
| QA-12 Webpay aprobado | I-ext | Compra de integración aprobada, retorno y registro | Compra aparece solo tras autorización; permiso de descarga concedido | Ejecución TEST histórica reportada el 22-11 (no cobro real); repetir requiere credenciales/ambiente autorizado | Vídeo de redacción controlada + captura estado + comprobante TEST sin PAN/token |
| QA-13 Webpay rechazado | I-ext | Rechazo/cancelación | No crea compra y no habilita archivo | Ejecución TEST histórica 22-11; repetir autorizado | Vídeo/capturas y consulta de estado saneada |
| QA-14 Descarga postcompra | I-ext | Descargar tras transacción autorizada | Archivo válido; anónimo/sin compra continúa denegado | 22-11 se reporta HTTP 200 con compra y 403 sin compra; repetición pendiente | Vídeo y hash/tamaño de archivo, nunca URL firmada |
| QA-15 R2 enlace firmado/expiración | I-ext | Subir, confirmar, descargar y esperar expiración | Persistencia privada; enlace válido hasta vencimiento y rechazo posterior | Producción R2/previews reportada 22-11; expiración de descarga/stems no verificada en este paquete | Logs sanitizados, objetos de prueba identificados y tiempo de expiración |
| QA-16 Usabilidad | M-usuario | 3–5 usuarios externos completan tareas y reportan fricciones | Resultados individualizados y consentimiento/anonimización apropiados | No hay ronda documentada localizada | Pautas, notas anonimizadas y síntesis; no inventar participantes |
| QA-17 Carga de archivos | I-ext | WAV/stems grandes y concurrencia sobre R2 | Tiempos/errores medidos con tamaño, concurrentes y entorno descritos | No ejecutado según seguimiento disponible | Archivo de resultados y configuración de carga |

## Evidencia automatizada anterior sobre el corte base

- Backend: `manage.py test` **499/499 aprobadas**; `manage.py check` correcto; migraciones sin cambios pendientes.
- Frontend tras añadir notificaciones: **40/40 aprobadas**; TypeScript/lint y build aprobados (1.930 módulos; advertencia de chunk 504.49 kB).
- Smoke local: Vite y proxy a Django HTTP 200, catálogo 6/125, preview HTTP 200, descarga anónima HTTP 403.
- El smoke no prueba reproducción visual. QA-01 (login manual), QA-03 (navegación visual), QA-05 (play/pausa), QA-06 (mutar carrito en UI), QA-09/10/11 requieren ejecución funcional de Vicente.
- Estos resultados son del SHA base anterior. La nueva versión que integra el asistente debe validarse y producir su propio informe antes de entregar.

## Conteo y separación de evidencia

- Ejecución local histórica `ee981a7`: 372 Django y 26 frontend según validación académica del 19-11; no sumarla con otros cortes.
- `4569613`: 372 Django históricos de un corte previo, junto a otras comprobaciones registradas por separado.
- `ee981a7`: una prueba focalizada adicional de registro/activación/login y Selenium Firefox de catálogo/carrito constan en paquete académico, no se suman a la suite como si fueran una misma corrida.
- 22-11: existen referencias históricas a pruebas de otros cortes y pruebas de integración; no se consideran evidencia de esta validación ni aprobación de servicios externos.
- 24-11: existen referencias históricas a pruebas de otros cortes; no se agregan ni presentan como un único resultado del SHA base.
- Esta matriz es diseño de ejecución, no evidencia de casos aprobados. Añadir resultados solo después de correrlos.

## Integraciones externas no demostradas

La ejecución local no valida Webpay E2E real completo ni credenciales productivas; tampoco R2 externo con enlaces firmados y expiración real, SMTP real, usabilidad con usuarios externos o pruebas de carga/concurrencia en infraestructura productiva. Las pruebas con mocks no prueban esos servicios.
