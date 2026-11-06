# Integracion backend - D3 autenticacion

## Decision D3 y alcance

Mecanismo aplicado: **sesiones de Django mediante cookie + proteccion CSRF**; no JWT.
Esta fue la propuesta tecnica registrada en el plan del equipo (DDPB-66). La
ratificacion formal de DDPB-66 en Jira debe comprobarse con el equipo; este
archivo documenta el mecanismo efectivamente implementado en codigo.
D6 es una decision diferente: obtencion de tracks de precio cero.

## Arquitectura

- Django es la autoridad de identidad y permisos. La SPA no guarda claves,
  JWT ni identificadores de sesion para autenticar al usuario.
- La cookie `sessionid` se gestiona por Django; `HttpOnly=True`, `SameSite=Lax`,
  `Secure=True` fuera de DEBUG. Se usa el backend de sesiones en base de datos.
- La cookie CSRF usa `SameSite=Lax` y `Secure=True` fuera de DEBUG.
  El cliente obtiene el token mediante `GET /api/csrf/` y envia `X-CSRFToken`
  en solicitudes que cambian estado.
- Frontend y API deben servirse en el mismo origen o detras de un proxy
  de mismo origen. El cliente usa `credentials: same-origin`; una URL de API
  ajena al origen NO transportara las cookies con esta configuracion.
- No se debe usar el modo `mock` para validar autenticacion o pagos reales.

## Endpoints existentes

| Metodo | Ruta | Resultado |
|---|---|---|
| GET | `/api/csrf/` | Token CSRF |
| GET | `/api/session/` | Usuario validado o `null` anonimo |
| POST | `/api/auth/login/` | Login Django; 401 credenciales incorrectas |
| POST | `/api/auth/logout/` | Destruye la sesion de Django |
| GET | `/api/mis-compras/` | 401 sin sesion |
| GET | `/api/carrito/` | 401 sin sesion |

El backend ya limita funciones por autenticacion y rol (productor/artista)
y conserva la autorizacion definitiva de descargas, pagos y edicion.
`session`, `login` y `logout` envian cabeceras que evitan el cache de respuestas.

## SPA: login, logout y expiracion

1. Login: solicitar CSRF, enviar credenciales, aceptar identidad solo si Django
   confirma. Recargar compras y carrito de esa sesion.
2. Logout: esperar respuesta de Django, vaciar los datos privados locales y
   retirar cualquier identificador de sesion heredado de `localStorage`.
3. Expiracion: si un endpoint privado devuelve 401, o `GET /api/session/`
   devuelve `null` despues de una sesion verificada, ocultar la identidad,
   carrito, historial y ventas y mostrar un enlace a iniciar sesion.
4. Revalidacion: comprobar `GET /api/session/` al enfocar la ventana, al
   volver a mostrarla y cada 60 segundos mientras exista identidad validada.
5. Un error de red o fallo CSRF no se interpreta automaticamente como cierre
   de sesion; mostrar el error de conectividad y permitir recuperacion.
6. Las rutas privadas de perfil, carrito, ventas y favoritos requieren la
   cuenta o el rol apropiado; Django vuelve a verificarlos en cada API.

## Comprobacion y despliegue

- `python manage.py test app.test_auth_d3`: usa la base de datos aislada de
  pruebas de Django; no utiliza cuentas ni compras de produccion.
- `cd frontend/client && npm run build && npm test`.
- Comprobacion visual aprobada (paso 193): login, logout, rutas privadas,
  expiracion simulada retirando la cookie sessionid y nuevo inicio de sesion.
- React: compilacion correcta y 23 pruebas automatizadas aprobadas.
- Django: 5 pruebas D3 aprobadas en base de datos temporal.
- Pendiente: comprobar caducidad real por tiempo en una prueba controlada.
- Nunca publicar contrasenas, cookies, tokens CSRF, claves ni archivos `.env`.
- En produccion: HTTPS, `DEBUG=False`, secreto privado, proxy de mismo origen,
  `ALLOWED_HOSTS` y origenes CSRF configurados correctamente.

## Integracion SPA con Django real: verificacion paso 196 (06-11-2026)

- Selector `VITE_API_MODE`: `hybrid` para la API Django real (valor predeterminado), `mock` para demo sin servidor. No cambiar automaticamente a `mock` ante un fallo de red.
- En desarrollo local: SPA en `http://localhost:3000`, proxy Vite de `/api/` a Django en `http://127.0.0.1:8000`. Dejar `VITE_DJANGO_URL` sin definir para conservar las cookies de sesion de mismo origen.
- Smoke test de solo lectura: `/api/catalogo/` devolvio 4 tracks con campos esperados; `/api/session/` y `/api/csrf/` respondieron por Django y proxy Vite. Sin cookie, `/api/carrito/` respondio 401. Las rutas POST-only rechazaron GET con 405.
- Contrato corregido: `DPagoInit` refleja la respuesta real de `POST /api/pago/`: `url_webpay`, `token_ws`, `buy_order`, `amount` y `transaction_id`. `session_id` pertenece al registro interno `DWebpayTransaction`, no al JSON de inicio de pago.
- Comentario heredado de `app/api_shim.py` actualizado de `VITE_API_MODE=rest` a `hybrid`/`mock`.
- La prueba del paso 196 no ejecuto registro, login, escrituras de carrito, pagos ni descargas. Estos flujos requieren validacion controlada adicional; no afirmar que quedaron probados solo con el smoke test.
- No se modificaron reglas de negocio de Webpay, compras, archivos ni permisos de descarga.

---

## Validacion integral de API real y modo mock - 06-11-2026

### Seleccion de entorno
- `VITE_API_MODE=hybrid`: SPA conectada a Django real mediante el proxy de Vite.
- `VITE_API_MODE=mock`: datos de demostracion sin depender de Django.
- En la configuracion verificada, `hybrid` es el modo predeterminado.
- Django conserva las sesiones con cookies y CSRF (decision D3).

### Contratos verificados
- Catalogo: GET `/api/catalogo/` responde correctamente por Django y Vite.
- Sesion y CSRF: endpoints accesibles; carrito sin sesion responde 401.
- Login, registro y pago: los endpoints rechazan solicitudes GET con 405.
- Se corrigio `DPagoInit`: la respuesta inicial de pago no exige `session_id`.
- `DWebpayTransaction` conserva su identificador interno de sesion.
- Se actualizo el comentario historico de `rest` a `hybrid` en el backend.

### Evidencia de pruebas
- Paso 196: diagnostico de Django directo y proxy Vite aprobado, sin escrituras.
- Paso 197: compilacion TypeScript/Vite y 23/23 pruebas frontend aprobadas.
- Paso 197: 5/5 pruebas aisladas de autenticacion Django aprobadas.
- Paso 198: 7/7 pruebas integradas Django en base temporal aprobadas.
- Paso 198: registro/activacion/login, catalogo, carrito e IVA, inicio Webpay
  sustituido, descarga protegida y obtencion gratis comprobados.
- Paso 199: catalogo, login, carrito existente, biblioteca, descarga autorizada,
  logout y rutas privadas aprobados visualmente contra Django real.
- Paso 200: modo mock comprobado sin Django en el puerto 3001.

### Alcance y limitaciones
- El inicio de Webpay se verifico con doble de prueba; no se realizo un cobro.
- Registro y carrito mutables se verificaron en una base temporal Django;
  en la SPA real se validaron datos existentes sin alterar compras.
- La validacion completa de un pago real y su retorno sigue pendiente de una
  prueba controlada en el ambiente de integracion de Webpay.
- No se modificaron datos reales de PostgreSQL durante las pruebas aisladas.
