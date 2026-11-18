# Protocolo de evidencia E2E — BeatsCloud

**Corte:** 12-11-2026 · **Entrega prevista:** 19-11-2026
**Estado:** guía preparada; no registra una ejecución nueva ni incorpora capturas.

## Disponibilidad del informe y evidencias

No se localizó `Evidencia_Pruebas_E2E_BeatsCloud.docx` en este checkout ni en las carpetas documentales inspeccionadas; tampoco se encontraron capturas que documenten estos recorridos. Vicente informó que el documento existe. **Antes de crear un DOCX nuevo**, confirmar con él/equipo su ruta y versión y revisar su contenido. Mantener el documento original y completar esa versión si corresponde; no duplicarlo ni sobrescribirlo. Si no aparece, el equipo puede convertir esta estructura en el informe de entrega indicando claramente que es un informe nuevo.

La evidencia de integración/backend ya versionada es histórica y no contiene las capturas pedidas. No se generaron imágenes ni se realizaron pruebas E2E durante esta sesión.

## Estados de evidencia

- **PENDIENTE:** sin evidencia auténtica de ejecución del caso en el corte.
- **VALIDADO histórico:** existe un resultado anterior descrito por fuente/fecha; requiere decidir si repetirlo para APT.
- **BLOQUEADO:** la ejecución se intentó y quedó detenida por dependencia registrada. No usar “bloqueado” si no hubo intento.
- **APROBADO / FALLIDO:** solo tras ejecución observada, registro completo y revisión de evidencia.

## Matriz de escenarios

Los resultados esperados son criterios de prueba, no resultados ejecutados. Precondiciones incluyen cuenta ficticia autorizada; no usar datos reales de clientes.

| ID | Funcionalidad | Precondiciones | Procedimiento | Resultado esperado | Evidencia que se debe capturar | Estado al 12-11-2026 |
|---|---|---|---|---|---|---|
| E2E-01 | Inicio de sesión y catálogo | Ambiente `hybrid`; Django disponible; cuenta ficticia activa; navegador anotado. | Abrir SPA; iniciar sesión; confirmar identidad con alias; entrar al catálogo y abrir detalle de beat. | Django establece sesión; identidad y catálogo se muestran; detalle coincide con la pista seleccionada. | Captura de dashboard/catálogo; alias; commit, fecha, ambiente y navegador; sin correo, ID personal, cookies ni DevTools. | **PENDIENTE** de evidencia del corte. Integración visual histórica descrita 06-11. |
| E2E-02 | Selección de un beat | Sesión activa; beat de prueba visible y permitido. | Abrir detalle; verificar título/metadata; seleccionar “Agregar al carrito”. | Beat correcto se añade una sola vez y se refleja en carrito. | Captura de detalle y resultado de selección; ocultar identidad personal. | **PENDIENTE** de evidencia del corte. |
| E2E-03 | Carrito y subtotal | E2E-02 completado; carrito de prueba con beat elegido. | Abrir carrito; comparar subtotal, IVA y total con valores devueltos por Django. | El resumen corresponde a selección y a cálculo server-side. | Captura de carrito con beat y subtotal visible; mostrar IVA/total si caben. Alias ficticio y sin otros datos privados. | **PENDIENTE** de captura actual. Contrato de totales documentado históricamente. |
| E2E-04 | Inicio Webpay TEST | Carrito de prueba; responsable confirma URL y ambiente TEST; datos oficiales de prueba disponibles. | Pulsar pagar; observar solicitud/redirect; confirmar entorno de pruebas antes de seguir. No incluir datos de tarjeta en encuadre. | Se inicia una transacción para el monto/orden esperados y se abre la pasarela TEST. | Captura de pasarela que permita reconocer ambiente TEST sin mostrar campos ni valores privados, token o URL con parámetros. | **PENDIENTE**; inicio con doble de prueba no equivale a recorrido real. |
| E2E-05 | Retorno de pago aprobado | E2E-04; procedimiento de aprobación en simulador TEST autorizado. | Completar aprobación con datos publicados por el proveedor dentro de TEST; regresar a BeatsCloud; consultar biblioteca/registro backend. | El backend confirma autorización; UI informa éxito; compra registrada una vez y visible al comprador. | Captura del retorno exitoso + captura de biblioteca; registro del estado backend sin PAN, token ni identificadores reutilizables. | **PENDIENTE**; no hay prueba de compra/retorno real acreditada. |
| E2E-06 | Pago rechazado o anulado | Sesión/beat de prueba; nueva transacción separada de la aprobación. | Ejecutar rechazo y, si el simulador permite, cancelación como casos independientes; observar retorno y carrito. | No se registra compra ni se habilita descarga; estado visible corresponde al resultado y carrito se conserva según regla backend. | Captura independiente de cada retorno/estado y comprobación saneada de que no existe compra. | **PENDIENTE** E2E; existen tests de ramas con respuestas simuladas según informe histórico. |
| E2E-07 | Descarga desde compras | Solo después de E2E-05 real; usuario comprador aún autenticado; archivo de prueba autorizado. | Entrar a sección Compras; confirmar beat; descargar; verificar que el archivo existe, tiene tamaño > 0 y se abre/reproduce. | Compra aparece y backend entrega el archivo esperado a esa cuenta; sin compra, descarga debe rechazarse. | Captura de sección Compras, descarga terminada y resultado de verificación del archivo (tamaño/lectura); no adjuntar audio con derechos no autorizados. | **PENDIENTE** de evidencia del corte. |

## Secuencia para obtener y conservar evidencia

1. **Responsable de integración/QA por asignar** confirma entorno, rama/commit, modo `hybrid`, base de pruebas, origen, cuenta y autorización del archivo. No compartir secretos con quien captura.
2. Anotar fecha/hora, nombre de ambiente (sin URL con credenciales), navegador/versión, commit, responsable y alias ficticio de cuenta.
3. Ejecutar E2E-01 a E2E-03 y comprobar con Django los importes antes de abrir Webpay.
4. Confirmar TEST en pasarela y completar E2E-04/E2E-05. El equipo debe usar los datos de prueba oficiales vigentes; este documento no transcribe números, claves ni secretos.
5. Ejecutar E2E-06 con otra transacción. No reutilizar captura de aprobación.
6. Ejecutar E2E-07 solo tras aprobación verificada. Confirmar archivo descargado no vacío y reproducible. Usar una pista propia o autorizada.
7. Antes de adjuntar, revisar imagen y metadatos: retirar nombres/correos, identificadores de cuenta, PAN/CVV/vencimiento, tokens, cookies, cabeceras, claves, parámetros sensibles de URL, datos de terceros y metadata privada del archivo.
8. Guardar capturas bajo una carpeta de evidencia acordada y relacionar cada archivo con su ID E2E. Mantener original privado si el formato exige datos de auditoría que no deben publicarse.

## Registro de resultados

Completar una línea por intento. Un caso se marca APROBADO o FALLIDO únicamente con resultado observado. Si falta servicio/cuenta y se intentó, usar BLOQUEADO con la dependencia; si no se intentó, mantener PENDIENTE.

| ID | Estado | Fecha/hora | Rama/commit | Ambiente/navegador | Ejecutó | Archivo(s) | Resultado/defecto Jira |
|---|---|---|---|---|---|---|---|
| E2E-01 | PENDIENTE | — | — | — | Por asignar | — | — |
| E2E-02 | PENDIENTE | — | — | — | Por asignar | — | — |
| E2E-03 | PENDIENTE | — | — | — | Por asignar | — | — |
| E2E-04 | PENDIENTE | — | — | — | Por asignar | — | — |
| E2E-05 | PENDIENTE | — | — | — | Por asignar | — | — |
| E2E-06 | PENDIENTE | — | — | — | Por asignar | — | — |
| E2E-07 | PENDIENTE | — | — | — | Por asignar | — | — |

## Pendiente de validación del equipo

Vicente/equipo debe proporcionar ruta y versión del DOCX. QA debe confirmar ambiente TEST, cuenta, beat/archivo de prueba, responsable y ventana de ejecución. Integración/backend debe habilitar consulta de estado de compra sin exponer datos personales. Si el documento original no aparece, el equipo debe confirmar si esta matriz será el formato final de evidencia.

## Fuentes

[Plan de pruebas](../../plan_pruebas.md); [integración backend](../../../INTEGRACION_BACKEND.md); [evidencia backend histórica](../../../evidencias/pruebas_backend.txt); `app/test_webpay_*.py`; `app/test_integration_real.py`; cliente `frontend/client/src/api/django.service.ts`.
