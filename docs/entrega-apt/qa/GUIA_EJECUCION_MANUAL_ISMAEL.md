# Ejecución manual de cuatro casos QA — BeatsCloud

**Diseño:** Vicente Monroy, según el antecedente disponible. **Ejecución manual prevista:** Ismael Araya; aún pendiente. **Automatización:** runner de `scripts/qa/verify.sh`, registrada aparte. Ningún caso tiene resultado manual aprobado.

El chat del equipo del 11-11 reporta un documento de casos E2E preparado por Vicente, pero el adjunto original no se recuperó. Esta guía hace ejecutables las cuatro categorías descritas; no reemplaza el original ni afirma sus resultados.

Esta guía es para la instancia QA local aislada, no producción. No uses cuentas, datos, pagos, correos o archivos de producción. No automatices una compra. No registres contraseñas, cookies, tokens CSRF/Webpay/OAuth ni URLs firmadas.

## Preparación común

1. Registra `git rev-parse HEAD`, fecha/hora local, Firefox y sistema operativo.
2. Comprueba `.env.qa` en modo `600`, `DB_HOST=127.0.0.1`, puerto 55433–55499, base `beatscloud_qa_local`, `MEDIA_ROOT` dentro de `media/qa`, Webpay `TEST`, R2 `false` y correo `console`. `scripts/qa/common.sh` rechaza credenciales SMTP, Resend y Gmail.
3. Si el entorno no existe, ejecuta `scripts/qa/setup.sh`; no lo resetees si ya está preparado. Inicia `scripts/qa/start.sh` y abre <http://127.0.0.1:3010/>.
4. Usa `qa-comprador-carrito` y pistas sintéticas `qa-*`. Si no conoces la contraseña QA, confirma el proyecto Compose/local y rota las cuentas QA con: `set -a; source .env.qa; set +a; .venv/bin/python manage.py prepare_qa_users --rotate-passwords`. Guarda la salida privada en el gestor autorizado. No captures credenciales.
5. No edites la base a mano. Capturas y logs deben omitir datos de cuenta, cookies, cabeceras sensibles, tokens y rutas firmadas.
6. Los casos Webpay requieren credenciales oficiales de integración **TEST** facilitadas por Felipe y autorización. Si no están, registra **Bloqueado** y no inicies el pago. Nunca configures LIVE.

## QA-VIC-01 — Catálogo y carrito

**Precondición:** servicios QA activos; iniciar sesión como `qa-comprador-carrito`.

1. Abre `http://127.0.0.1:3010/?tab=catalogo`; espera a que cargue la primera página. Busca `qa-cat-prod-01` o una pista cuyo título empiece por `qa-`.
2. Abre la pista y verifica título, productor, género, precio y portada. Anota el ID si está visible; puede cambiar al regenerar QA.
3. Pulsa **Comprar / Agregar al carrito**. Abre Carrito desde la barra superior o `/?tab=carrito`. Confirma que el producto aparece una vez y que subtotal, IVA 19 % y total coinciden con los importes del servidor.
4. Recarga: sesión y carrito deben persistir. Quita el producto agregado; verifica que desaparezca y que los totales se actualicen.
5. Adjunta capturas saneadas de catálogo y carrito; registra valores esperado/observado.

**Esperado:** catálogo/detalle visibles, alta persistida para el comprador, totales del servidor coherentes y eliminación reflejada después de actualizar. **No pulses Revisar compra en este caso.**

## QA-VIC-02 — Pasarela Webpay (inicio y retorno)

**Precondición:** QA-VIC-01 aprobado, artículo pagado en carrito y Transbank integración TEST autorizado por Felipe. Sin credenciales/autorización: **Bloqueado; sin intento**.

1. En Carrito revisa artículo, subtotal, IVA y total. Pulsa **Revisar compra** y vuelve a comprobar el monto en el diálogo.
2. Pulsa una sola vez **Confirmar e ir a Webpay**. Comprueba que el navegador navega al dominio oficial de Transbank TEST. Si no navega, registra mensaje visible y estado de la solicitud local, sin copiar el token.
3. Comprueba que se creó una sola orden QA y que su monto corresponde al total. No repitas si no sabes si se creó una orden.
4. Solo si la pasarela da un recorrido de prueba, sigue su flujo oficial TEST y vuelve al callback local. Verifica el mensaje de retorno; la redirección por sí sola no es aprobación de pago.
5. Registra host TEST, estado HTTP y mensaje, con evidencia redactada. No registres token ni datos de pago.

**Esperado:** inicialización server-side devuelve destino de integración TEST con orden/monto coherentes y el resultado se valida en backend. No afirmar compra aprobada en este caso.

## QA-VIC-03 — Pago exitoso en entorno de prueba

**Precondición:** QA-VIC-02 inició correctamente, Felipe autorizó completar el sandbox y entregó por canal privado los datos oficiales de prueba. Sin ellos: **Bloqueado**. No usar LIVE ni automatizar compras.

1. En Transbank **TEST**, sigue la documentación oficial del sandbox con los datos de prueba facilitados por Felipe; no uses tarjetas ni credenciales reales.
2. Completa la simulación de aprobación y regresa por el retorno oficial a BeatsCloud local. Espera la conciliación backend; no refresques ni reenvíes repetidamente el retorno.
3. Comprueba estado aprobado, orden, monto, comprador y productos. Recarga y verifica que la compra no se duplique.
4. Abre **Mis compras** y confirma que aparece una sola compra sintética. Registra ID de orden si no revela información personal.
5. Si solo aprueba la pantalla del proveedor pero Django no confirma, registra fallo/impedimento. No marcar aprobado.

**Esperado:** únicamente la confirmación backend crea una compra coherente e idempotente. No registrar datos de tarjeta ni tokens.

## QA-VIC-04 — Descarga del archivo comprado

**Precondición:** QA-VIC-03 aprobado para una pista descargable local; no crear compras directamente en la DB.

1. En **Mis compras**, abre la pista aprobada y pulsa **Descargar** desde BeatsCloud.
2. Confirma que el audio corresponde a la pista y que el archivo local puede abrirse. No compartas el fixture fuera de QA.
3. Cierra sesión; en ventana privada sin autenticar, solicita la ruta de descarga desde la ficha, sin copiar URLs firmadas. Verifica rechazo según el flujo.
4. Inicia sesión con otro comprador QA sin derecho a esa pista y vuelve a comprobar que no descarga.
5. Registra el resultado de la descarga autorizada y ambos controles negativos; conserva solo capturas saneadas o metadata local del archivo.

**Esperado:** comprador con compra validada descarga el archivo correcto; anónimo y comprador sin derecho reciben rechazo sin exponer contenido.

## Registro

Completa la fila correspondiente en `REGISTRO_EJECUCION_VICENTE.md` con `Aprobado`, `Fallido` o `Bloqueado`, SHA, hora, navegador, pasos observados, expected/actual y evidencia saneada. Diseño se atribuye a Vicente; ejecución manual, a Ismael solo después de realizarla. Automatización se registra separadamente como runner. Jira solo se cita si la clave existe y fue verificada.
