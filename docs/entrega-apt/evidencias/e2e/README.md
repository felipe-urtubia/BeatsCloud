# Evidencia de pruebas E2E — BeatsCloud

**Estado al 12-11-2026:** no se encontró `Evidencia_Pruebas_E2E_BeatsCloud.docx` ni capturas E2E en los archivos visibles del repositorio. Este README deja el protocolo; no afirma que las pruebas se hayan ejecutado.

Antes de crear un archivo nuevo, preguntar a Vicente/equipo por la ubicación del DOCX. Si aparece, abrir y revisar su contenido, conservar copia de respaldo y añadir evidencias al documento existente. No duplicar el informe.

## Capturas solicitadas

1. **Catálogo/dashboard:** sesión iniciada con usuario de prueba; ocultar correo, nombre real, cookies y datos de cuenta.
2. **Carrito:** seleccionar una pista de prueba; mostrar título y subtotal. Capturar también IVA/total si caben. No dejar otros datos personales.
3. **Webpay TEST:** capturar la página/ambiente de pruebas sin PAN, CVV, vencimiento, token, credenciales ni datos bancarios visibles. Si la pasarela no permite enmascarar, usar encuadre/recorte que no capture esos campos.
4. **Pago exitoso:** retorno a BeatsCloud con resultado aprobado. Ocultar identificadores que sirvan para conciliar o datos personales; conservar el estado visible.
5. **Compras:** sección de biblioteca con la pista comprada y datos mínimos.
6. **Descarga:** registrar inicio/resultado de descarga y verificar localmente que el archivo esperado existe, tiene tamaño no nulo y se reproduce. Para demostrarlo puede adjuntarse captura de la descarga terminada y propiedades básicas, sin incluir el audio si tiene derechos.

## Procedimiento reproducible

1. Confirmar con responsable que frontend y Django usan `hybrid`, cuenta autorizada de prueba y credenciales oficiales de integración Webpay TEST. No leer ni copiar secretos en documentos.
2. Anotar commit, ambiente, navegador/versión y fecha/hora. Registrar la cuenta solo como alias ficticio.
3. Iniciar sesión, capturar catálogo, agregar la pista de prueba al carrito y capturar subtotal/IVA/total.
4. Iniciar pago y capturar pasarela TEST con los campos sensibles ocultos. Completar únicamente con datos de prueba publicados por el proveedor, en el ambiente verificado.
5. Capturar retorno aprobado. Confirmar en la sección de compras que el ítem aparece.
6. Descargar el audio mediante el botón de la biblioteca; confirmar tamaño no nulo y reproducción local. Registrar el nombre usando un alias si revela datos del catálogo.
7. Ejecutar por separado rechazo/cancelación para verificar que no se acredita compra y el carrito conserva su estado. No reutilizar una captura de aprobación como evidencia de ese caso.
8. Revisar todas las imágenes antes de agregarlas: sin datos personales, credenciales, tarjetas, correo, cookies/DevTools, tokens, URLs con parámetros secretos ni información no autorizada.

## Registro por recorrido

| Caso | Estado | Fecha | Responsable | Commit/ambiente/navegador | Archivo de evidencia | Observación/defecto |
|---|---|---|---|---|---|---|
| Catálogo autenticado | Pendiente | — | Por asignar | — | — | — |
| Carrito con subtotal | Pendiente | — | Por asignar | — | — | — |
| Webpay TEST | Pendiente | — | Por asignar | — | — | — |
| Retorno aprobado | Pendiente | — | Por asignar | — | — | — |
| Biblioteca | Pendiente | — | Por asignar | — | — | — |
| Descarga reproducible | Pendiente | — | Por asignar | — | — | — |
| Rechazo/cancelación | Pendiente | — | Por asignar | — | — | — |

No marcar un caso como aprobado hasta adjuntar evidencia auténtica y completar los metadatos. No publicar tarjetas, tokens ni credenciales aunque sean de prueba.
