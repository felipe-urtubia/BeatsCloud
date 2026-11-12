# Plan de pruebas — entrega APT

**Versión:** borrador 12-11-2026
**Propósito:** definir ejecución y evidencia para el corte APT del 19-11-2026.

## Alcance y ambientes

Validar integración SPA + Django, sesión y permisos, catálogo/detalle, carga, carrito, inicio/retorno Webpay TEST, biblioteca y descarga autorizada. Separar pruebas automatizadas, integración con dobles/simuladores y recorrido manual en navegador. Modo `mock` solo sirve para presentación visual de datos de demo y nunca como prueba de persistencia/pago.

Usar entorno de integración configurado por el equipo, cuenta de prueba activada, datos ficticios y archivo de audio no sensible. Antes de iniciar Webpay, confirmar que la URL/credenciales correspondan a TEST y no registrar PAN, CVV, credenciales, cookies ni token de transacción en capturas/logs.

## Matriz

| ID | Escenario | Tipo | Resultado esperado | Evidencia requerida | Estado al 12-11 |
|---|---|---|---|---|---|
| T-01 | Catálogo con sesión iniciada | E2E navegador/API real | Catálogo cargado e identidad visible | Captura saneada del dashboard | Pendiente de adjuntar |
| T-02 | Carrito con pista elegida | E2E | Ítem correcto y subtotal/IVA/total coinciden con valores servidos por Django | Captura de carrito con subtotal visible | Pendiente |
| T-03 | Inicio de Webpay TEST | E2E | Redirección a ambiente de pruebas; no exponer datos personales | Captura saneada de pantalla de pasarela sin campos/credenciales | Pendiente |
| T-04 | Pago autorizado y retorno | E2E | Retorno indica aprobado y existe registro de compra en backend | Captura del retorno; referencia de transacción parcialmente ocultada si se requiere | Pendiente; no asumir ejecución |
| T-05 | Rechazo/cancelación | E2E | No se registra compra; carrito permanece según resultado | Estado observado y captura/log saneado | Pendiente |
| T-06 | Biblioteca y descarga | E2E | Compra visible; respuesta descarga el audio esperado y archivo reproducible/no vacío | Captura de compras + archivo descargado de prueba (no publicar si tiene derechos) | Pendiente |
| T-07 | Acceso sin autorización | API/backend | Carrito/descarga privados rechazan usuario anónimo o sin compra | Resultado HTTP/log sin cookie ni datos personales | Pendiente de consolidar |
| T-08 | Retorno Webpay por ramas | Automatizada | Cobertura de aprobación/rechazo/cancelación/abandono simulados | Reporte de `app/test_webpay_*` | Hay tests en repositorio; ejecutar en el corte y adjuntar salida actual |
| T-09 | Estados de carga del upload | Automatizada/UI | Progreso, final y error reflejan respuesta real | Reporte de tests/build y captura si es interacción visual | No ejecutar aún |
| T-10 | Audio en navegador | Manual en navegador | Audio audible, controles/visualizador consistentes al cambiar pista y volumen | Navegador/versión, pasos, resultado y captura o grabación | Pendiente explícito; incluye cambio local `audioEngine.ts` |

## Ejecución y registro

Por cada fila completar: fecha/hora, responsable real, commit, URL/ambiente, navegador/versión, cuenta ficticia identificada solo por alias, pasos, resultado observado (Aprobado/Fallido/Bloqueado), defecto Jira y ruta de evidencia. Si se bloquea por falta de cuenta/configuración, conservar **Pendiente** con la dependencia; no convertirlo en aprobación.

El repositorio registra evidencia previa de backend e integración, pero no se ejecutaron pruebas durante esta auditoría. La evidencia de ejecuciones anteriores no reemplaza el registro del corte final ni demuestra el recorrido real E2E solicitado.
