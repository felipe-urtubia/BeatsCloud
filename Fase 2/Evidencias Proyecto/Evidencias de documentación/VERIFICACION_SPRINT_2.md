# Verificación del sprint 2

Fecha: 2026-11-05 (actualizada durante la ronda)

## DDPB-74 – Autenticación D3

Decisión final: sesión Django con cookie + CSRF. Se verificó el contrato existente de login, logout, registro y endpoints protegidos en `server/app/api_shim.py`; se agregó manejo global de `401` y del `403` de descarga que comunica sesión requerida. La SPA limpia identidad, carrito y datos privados, vuelve a la vista pública y abre login con aviso de sesión expirada.

Verificación tras este punto: comandos aprobados; la cifra final consolidada del cierre es **34 pruebas Django aprobadas** (ver sección “Pruebas Django”).

## DDPB-81 – Selector API real / mock

`VITE_API_MODE=real` selecciona el backend Django y `mock` conserva la demo. `hybrid` permanece como alias compatible. La SPA muestra el modo configurado y el usuario/sesión actual.

La prueba manual end-to-end con una cuenta local activada y pago Webpay queda pendiente. No se proporcionaron datos de una cuenta de prueba y, según instrucción, no se inspeccionó ningún `.env`; no se puede confirmar ni utilizar la configuración local de Transbank. No se inventaron credenciales ni datos.

Verificación tras este punto (05-11-2026): comandos aprobados; cifra final consolidada del cierre: **34 pruebas Django aprobadas** (ver sección “Pruebas Django”).

## Retorno Webpay y presentación

El callback del carrito redirige a `SPA_URL/?pago=approved|rejected|cancelled|abandoned`. La SPA presenta el estado y rehidrata catálogo/carrito. Solo `approved` borra las ventas pendientes y crea compra; los otros estados preservan el carrito. Se agregaron tests del callback con respuesta simulada de Transbank para estas cuatro ramas. La prueba contra el ambiente real de integración sigue pendiente.

Verificación tras este punto (05-11-2026): comandos aprobados; cifra final consolidada del cierre: **34 pruebas Django aprobadas** (ver sección “Pruebas Django”).

## Armado visual/funcional

La SPA muestra el modo `API REAL` o `DEMO · MOCK` y la identidad de sesión. Catálogo y carrito muestran carga, error/reintento y vacío; el resumen de carrito usa los importes del backend. Pago muestra progreso/errores y estado de retorno; descarga de compra muestra carga y error. En modo real, las acciones de descargas gratis/maqueta que solo eran textos locales se identifican como no disponibles o se ocultan; el mock conserva la demo.

Verificación final tras el punto 4 (05-11-2026): `python manage.py test app`: **34 aprobadas**; `npx tsc -b`: aprobado; `npx vite build`: aprobado.

## Hallazgos para debug

| Hallazgo | Ubicación | Severidad |
|---|---|---|
| La activación de registro depende de correo; el recorrido no está probado con SMTP/cuenta local. | `server/app/api_shim.py`, configuración de correo | Media; depende de servicio/cuenta de prueba. |
| La integración Transbank real y registro de extremo a extremo requieren credenciales oficiales y una cuenta activada proporcionada por el equipo; no se inspeccionó `.env`. | Integración local / SMTP / Webpay | Alta para validar el flujo real; pendiente por dependencia externa. |
| El endpoint de descarga entrega el archivo `track`, no stems separados. | `server/app/api_shim.py` (`download_api`) | Media; no bloquea la descarga del archivo disponible. |
| La SPA filtra/ordena los seis resultados recibidos de la página 1; filtros y paginación server-side siguen fuera de este sprint. | `client/src/components/CatalogPage.tsx`, `client/src/context/AppContext.tsx` | Baja para el flujo de compra; revisar en tickets de filtros. |
| La pantalla de subida aún actualiza datos locales desde `uploadTrack`; no envía el formulario aunque `DjangoApi.upload` y el endpoint estén disponibles. | `client/src/context/AppContext.tsx` (`uploadTrack`), `client/src/components/UploadTrackModal.tsx` | Baja para los flujos de Sprint 2; no modificar dentro de este alcance. |

## Pruebas Django

Comando, desde `server/`: `python manage.py test app`.

Resultado más reciente (2026-11-05): `python manage.py test app` ejecutado desde `server/`: **34 pruebas aprobadas**, 0 fallidas. Django reportó `System check identified no issues`.

## Compilación TypeScript y Vite

Comandos, desde `client/`: `npx tsc -b` y `npx vite build`.

Resultado más reciente (2026-11-05): `npx tsc -b` y `npx vite build`, ejecutados desde `client/`, finalizaron con código 0. Vite generó el bundle de producción.

## Prueba de integración local (DDPB-81)

Registro, login, catálogo, carrito, pago Webpay y descarga requieren una ejecución manual integrada. Pendiente. El pago autorizado requiere credenciales de integración proporcionadas por el equipo; no se registran aquí.

## Hallazgo de seguridad

Durante la revisión se detectó que el archivo rastreado `agregar.html` era un ZIP con un `.env` embebido. Se retiró del árbol de trabajo y no se copiaron sus valores a documentación. El blob permanece en el historial Git actual hasta que se autorice su saneamiento; rota las credenciales que contenga antes de volver a utilizarlas o publicar el repositorio.

## Guía de prueba manual (DDPB-81 / 82)

### Variables locales necesarias

Configura los nombres de variable siguientes en los archivos locales ignorados por Git. Usa los valores de desarrollo que correspondan al equipo; esta guía no incluye valores ni secretos.

| Archivo | Nombres de variables |
|---|---|
| `server/.env` | `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `SPA_URL`, `EMAIL_BACKEND`, `DB_ENGINE`, `TRANSBANK_COMMERCE_CODE`, `TRANSBANK_API_KEY`, `TRANSBANK_SHARED_SECRET`, `TRANSBANK_INTEGRATION_TYPE` |
| `client/.env` | `VITE_API_MODE`, `VITE_DJANGO_URL`, `VITE_API_URL` (opcional si se usa el proxy local de Vite) |

Para local, configura el backend de correo para imprimir el mensaje de activación en la consola de Django y `VITE_API_MODE` para API real. El ejemplo `client/.env.example` documenta el modo; `SPA_URL` debe apuntar al origen Vite local. No sobrescribas un `.env` existente.

### Levantar la aplicación

1. En una terminal:

   ```bash
   cd server
   python -m pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver 127.0.0.1:8000
   ```

2. En otra terminal:

   ```bash
   cd client
   npm ci
   npm run dev
   ```

3. Abre `http://localhost:3000`. Vite escucha en el puerto 3000 y proxifica `/api` y `/media` a Django en el puerto 8000.

### Recorrido y cuenta

1. Registra una cuenta desde la SPA con datos de prueba propios.
2. Copia el enlace de activación que Django imprime en su terminal y ábrelo en el navegador. Luego inicia sesión desde la SPA.
3. Abre el catálogo, elige un track de pago, agrégalo al carrito y confirma que subtotal, IVA y total coinciden con el backend.
4. Inicia Webpay Plus. Para aprobación usa la VISA `4051885600446623`, CVV `123` y cualquier fecha de vencimiento futura. En la autenticación bancaria usa RUT `11.111.111-1` y clave `123`.
5. Para rechazo usa la MASTERCARD `5186059559590568`, CVV `123` y cualquier fecha de vencimiento futura.
6. Para anulación, en el simulador bancario elige volver/cancelar antes de autorizar. Para abandono, deja el flujo sin completar y comprueba el retorno sin token si el simulador lo emite; si no emite callback, anota esa limitación y prueba la rama local abriendo `http://127.0.0.1:8000/pago/exito-carrito/` sin parámetros.
7. Tras aprobar, confirma que la SPA muestra el estado aprobado y el carrito queda vacío. Vuelve al catálogo, abre la pista adquirida y descarga el archivo; una compra rechazada, anulada o abandonada debe conservar el carrito y no habilitar la descarga.

Las tarjetas VISA y Mastercard, CVV, vencimiento y datos de autenticación son los publicados por [Transbank Developers para el ambiente de integración](https://transbankdevelopers.com/documentacion/como_empezar).

### Resultados manuales

| Recorrido | Resultado | Fecha | Evidencia |
|---|---|---|---|
| Pago aprobado (VISA) |  |  |  |
| Pago rechazado (Mastercard) |  |  |  |
| Pago anulado |  |  |  |
| Pago abandonado |  |  |  |
| Descarga tras aprobación |  |  |  |
