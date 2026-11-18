# Plan de pruebas — entrega APT BeatsCloud

**Versión de trabajo:** 12-11-2026 · **Presentación prevista:** 19-11-2026
**Aprobación:** pendiente del equipo. El presente plan separa ejecuciones históricas documentadas de pruebas aún no realizadas para el corte APT.

## 1. Objetivos

- Comprobar el recorrido de un usuario desde sesión y catálogo hasta carrito, pago y acceso a la compra.
- Verificar que Django conserva autoridad sobre identidad, importes, transacciones y descarga.
- Comprobar publicación de audio y el funcionamiento del reproductor en navegador.
- Conservar resultados reproducibles con evidencias saneadas y vínculo a defectos Jira.
- Evitar que modo `mock` o respuestas simuladas se reporten como operación real.

## 2. Alcance y exclusiones

**Incluido:** cuenta/sesión, catálogo, selección de pista, carrito y totales, inicio/retorno Webpay TEST, rechazo/cancelación, biblioteca, descarga, carga y audio en navegador. Incluye pruebas automatizadas Django y frontend existentes.

**No se valida por este plan:** producción, pagos reales/cobros, tarjeta real, DRM, distribución separada de stems, carga masiva, desempeño/seguridad de infraestructura o funciones no ligadas a historias Jira verificadas. Modo `mock` sirve solo para comprobar presentación de demo.

## 3. Estrategia y tipos

1. **Automatizadas unitarias/integración:** validar helpers frontend, contratos API, reglas Django, permisos, guards y ramas de callback con datos aislados/dobles.
2. **Integración local:** conectar SPA con Django por proxy Vite (`hybrid`); verificar sesión, catálogo y contratos sin depender de simulación local.
3. **E2E manual en navegador:** cuenta de prueba, catálogo, carrito, pasarela TEST, retorno y descarga. Ejecutar por separado aprobación y rechazo/cancelación.
4. **Audio manual:** validar play/pausa, fuente, seek, volumen, duración y visualizador en navegador objetivo.
5. **Modo mock:** smoke visual separado e identificado explícitamente como `SIMULADO`; nunca sustituye puntos 2–4.

No se añaden o ejecutan pruebas como parte de esta documentación. Los comandos siguientes son instrucciones para el equipo.

## 4. Ambiente y precondiciones

- Commit y rama anotados; frontend y backend de la misma revisión.
- Entorno aislado/TEST definido por el equipo; `VITE_API_MODE=hybrid`; no usar `mock` para probar persistencia, pagos o descargas.
- Django accesible por origen/proxy; base temporal o de pruebas con datos sintéticos; migraciones compatibles.
- Cuenta ficticia habilitada con rol requerido, activada sin exponer correo/datos reales; si se prueba activación, backend de correo controlado.
- Productor y pista de prueba autorizados, archivo de audio no sensible y de uso permitido.
- Para Webpay, responsable confirma ambiente TEST antes del inicio. Usar exclusivamente datos publicados por el proveedor; no guardar PAN, CVV, vencimiento, clave, token ni credenciales en evidencia.
- Navegador y versión anotados; herramientas de captura recortan datos personales y URLs sensibles.
- No abrir/extractar `agregar.html`; no usar el archivo ni su miembro `.env` como fixture.

## 5. Casos de prueba de entrega

Todos los estados de esta tabla están al corte **12-11-2026**. “Pendiente” significa que no hay evidencia E2E reciente adjunta en este paquete; no afirma que jamás se haya probado una parte del flujo.

| ID | Caso y precondiciones | Procedimiento | Resultado esperado | Evidencia requerida | Estado |
|---|---|---|---|---|---|
| APT-01 | Login y catálogo; cuenta ficticia activa, `hybrid`, Django disponible. | Abrir SPA; iniciar sesión; comprobar identidad; abrir catálogo y detalle de un beat. | Django confirma sesión; catálogo y detalle muestran datos del backend; no aparece modo mock. | Captura de sesión/catalogo saneada; commit, navegador y fecha; sin correo/cookie. | **PENDIENTE** de captura actual. Verificaciones históricas en integración backend. |
| APT-02 | Selección de beat; beat de prueba visible, no comprado. | Abrir detalle, comprobar nombre/metadata/precio y añadir una sola vez al carrito. | La pista correcta queda seleccionada; backend rechaza duplicado si se intenta repetir. | Captura del detalle/selección y resultado de carrito; alias de pista permitido. | **PENDIENTE** para evidencia de corte. |
| APT-03 | Carrito autenticado con un beat. | Abrir resumen y comparar subtotal/IVA/total de interfaz con respuesta de Django; quitar/reagregar solo si se permite usar fixture. | Importes corresponden a valores del servidor; selección correcta, sin datos ajenos. | Captura del carrito con subtotal visible (y total/IVA recomendable), sin datos personales. | **PENDIENTE** para evidencia de corte; contrato server-side documentado históricamente. |
| APT-04 | Carrito de prueba; configuración TEST confirmada por responsable. | Iniciar checkout; seguir la redirección a Webpay; confirmar que es ambiente de pruebas sin introducir secretos en captura. | Django crea intento pendiente y el navegador llega a la pasarela TEST; el pedido/monto corresponde al carrito. | Captura saneada de la pasarela; no mostrar campos con datos de tarjeta, tokens, credenciales ni URL sensible. | **PENDIENTE**; los tests de inicio con doble no reemplazan esta prueba. |
| APT-05 | Transacción TEST iniciada; datos oficiales de prueba autorizados. | Completar la ruta de aprobación según el simulador; volver a BeatsCloud; abrir biblioteca. | UI informa aprobación solo tras respuesta confirmada; Django registra compra una vez y la biblioteca la muestra. | Captura del retorno aprobado + biblioteca; referencia transaccional minimizada y nunca token. | **PENDIENTE**; no se acredita cobro/retorno real en las fuentes. |
| APT-06 | Otra transacción y datos de prueba para rechazo o cancelación. | Ejecutar rechazo y cancelación como recorridos separados; observar retorno y estado del carrito. | No se registra compra; se informa rechazo/cancelación y el carrito conserva el estado que define el backend. | Una evidencia por rama y resultado consultado en backend, saneados. | **PENDIENTE** E2E; hay ramas cubiertas con respuestas simuladas históricas. |
| APT-07 | Compra autorizada de APT-05; usuario comprador autenticado. | Abrir Mi perfil/Compras, localizar beat y pulsar descargar; comprobar archivo local con tamaño mayor que cero y apertura/reproducción. | La compra aparece; respuesta descarga el archivo del track y el archivo es legible; sin autorización el backend rechaza descarga. | Captura de biblioteca y descarga finalizada; tamaño/lectura observados; no adjuntar audio con derechos no autorizados. | **PENDIENTE** de evidencia actual. |
| APT-08 | Sesión anónima y otra cuenta sin compra (fixtures). | Llamar/abrir carrito y descarga protegidos sin permiso. | API rechaza solicitud privada; no entrega audio completo ni datos de otro usuario. | Código HTTP y salida saneados; sin cookies, cabeceras sensibles ni contenido de archivo. | **VALIDADO históricamente** por tests documentados; reejecución/captura del corte **PENDIENTE**. |
| APT-09 | Productor ficticio activo, track/audio de prueba permitido, modo `hybrid`. | Subir desde SPA; esperar respuesta; volver a catálogo/perfil y consultar la pista persistida; repetir con archivo no permitido. | Confirmación solo al persistir; track visible tras recarga; archivo inválido muestra error y no crea registro. | Capturas del estado final/error; referencia de respuesta/backend sin datos personales. | **PENDIENTE** de ejecución actual tras cambios de upload del PR #2. |
| APT-10 | Audio con acceso permitido; navegador/versión anotados. | Reproducir, pausar, reanudar, cambiar pista, seek, cambiar volumen, esperar `ended`; repetir con preview autorizado. | Audio audible y controles/tiempo/visualizador siguen la fuente y estado; sin excepción o silencio inesperado. | Registro navegador/OS, pasos y resultado; captura/video sin identidad; anotar consola saneada si hay fallo. | **PENDIENTE** explícito; cambio de `audioEngine.ts` sin validación real acreditada. |

## 6. Registro de ejecuciones históricas disponibles

Estas entradas son citas de informes versionados; no son ejecuciones de esta sesión ni deben confundirse con el corte final.

| Fecha informada | Fuente | Resultado descrito por la fuente | Alcance/precaución |
|---|---|---|---|
| 14-10-2026 | `docs/evidencias/pruebas_backend.txt` | Log UTF-16 registra 22 tests Django y salida de sistema sin incidencias. | Informe histórico; no representa revisión actual ni E2E Webpay. |
| 06-11-2026 | `docs/INTEGRACION_BACKEND.md` | Reporta 23 pruebas frontend, 5 pruebas D3 y 7 pruebas Django integradas, además de smoke/validaciones visuales por pasos 196–200. | Registro descriptivo; distingue que el inicio Webpay tuvo doble y que el pago/retorno real siguió pendiente. No adjunta capturas E2E solicitadas. |
| 06-11-2026 | `REGISTRO_CAMBIOS_BEATSCLOUD.md` | Registra 103/103 pruebas Django, 23/23 frontend, `tsc -b && vite build` y `manage.py check` aprobados. | Resultado histórico documentado; la fuente detalla que fueron necesarias variables CSRF de orígenes locales. No reejecutado aquí. |
| 08-11-2026 | `REGISTRO_CAMBIOS_BEATSCLOUD.md` (D9) | Registra `manage.py check`, `makemigrations --check --dry-run` sin cambios y 111 pruebas Django aprobadas en DB temporal. | Último resultado de regresión fechado que se encontró en esta rama; no reejecutado para el corte ni equivalente a E2E. |
| 05-11-2026 | `VERIFICACION_SPRINT_2.md`, conservado en el historial desde `c060b67` | Reporta 34 tests Django, `tsc` y `vite build` aprobados. | Fuente de otro corte; no acta de Review/retro ni resultado del código actual. No se suma ni se extrapola. |

Este plan conserva el estado histórico documentado al 12-11-2026. El corte posterior ejecutado el 18-11-2026 se registra por separado en [validacion_tecnica_corte_2026-11-18.md](validacion_tecnica_corte_2026-11-18.md); sus resultados no se extrapolan a pruebas manuales, navegador, R2 real ni Webpay externo.

## 7. Criterios de aceptación de pruebas

- Casos E2E de compra solo se aceptan cuando el resultado se consulta en backend y la captura/registro concuerdan.
- Aprobación es distinta de inicio de checkout; una respuesta simulada es distinta de Webpay TEST.
- Descarga requiere confirmar archivo no vacío/legible y autorización correcta, no solo que el botón sea visible.
- Cada caso se marca `APROBADO`, `FALLIDO` o `BLOQUEADO` con fecha, ambiente, versión, ejecutor y evidencia. Sin ejecución se conserva `PENDIENTE`.
- Cualquier defecto lleva clave Jira si el equipo la confirma; no inventar clave, severidad ni persona responsable.
- No cerrar APT-10 sin prueba en navegador real.

## 8. Formato de resultado por ejecución

| ID | Resultado observado | Fecha/hora | Rama/commit | Ambiente | Navegador | Ejecutó | Evidencia | Jira/observación |
|---|---|---|---|---|---|---|---|---|
| APT-__ | Pendiente | — | — | — | — | Por asignar | — | — |

## Pendiente de validación del equipo

El equipo debe definir URL y DB de integración, cuenta activada, pista/archivo de prueba autorizado, responsable de validar Webpay TEST y navegador objetivo. El administrador del proyecto debe facilitar criterios Jira; el evaluador/profesor debe confirmar rúbrica si aplica. Cada persona que ejecute completa su fila y adjunta evidencia al [protocolo E2E](evidencias/e2e/README.md).

## Fuentes

[Protocolo E2E](evidencias/e2e/README.md); [integración backend](../INTEGRACION_BACKEND.md); [evidencia de pruebas backend](../evidencias/pruebas_backend.txt); `app/test_webpay_*.py`; `app/test_auth_d3.py`; `app/test_api_shim.py`; `app/test_integration_real.py`; `frontend/client/src/utils/uploadStatus.test.mjs` (incluido en PR #2, no ejecutado aquí).
