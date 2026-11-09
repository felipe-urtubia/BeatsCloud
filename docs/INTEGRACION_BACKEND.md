# Integración React-Django

## Arquitectura y ejecución

React usa la capa tipada `client/src/api/`: `django.service.ts` define las rutas
y DTO, y `mappers.ts` adapta las respuestas al modelo de interfaz. En desarrollo,
Vite reenvía `/api` y `/media` a Django en `http://127.0.0.1:8000`. Configure
`client/.env` a partir de `client/.env.example`; `VITE_API_MODE=real` (también
acepta `hybrid` como alias) conecta al backend y `mock` ejecuta la demo local.
La configuración se fija al compilar. Para validar autenticación, permisos o
pagos se debe usar el modo real.

El backend autoritativo está en `server/app/api_shim.py`, `server/app/views.py`
y `server/app/urls.py`; la configuración activa es `server/beatcloud/settings.py`.
Consulte el README para instalar dependencias y levantar ambos procesos. Las
cookies usan `same-origin`, por lo que frontend y API deben compartir origen o
quedar detrás de un proxy de mismo origen.

## Autenticación D3: sesión y CSRF

Django es la autoridad de identidad y permisos. El login crea una sesión Django
en la base de datos y el navegador mantiene la cookie `sessionid` (HttpOnly,
SameSite=Lax y Secure fuera de DEBUG). No se usa JWT ni se guarda un bearer
token en `localStorage`. El logout invalida la sesión en Django.

Antes de mutaciones, React obtiene CSRF mediante `GET /api/csrf/` y envía el
valor en `X-CSRFToken`. Las rutas principales son:

| Método | Ruta | Uso |
|---|---|---|
| GET | `/api/csrf/` | Handshake CSRF |
| GET | `/api/session/` | Identidad validada o `null` |
| POST | `/api/auth/login/` | Login Django |
| POST | `/api/auth/logout/` | Cierre de sesión Django |
| POST | `/api/auth/registro/` | Registro sujeto a activación por correo |
| GET | `/api/mis-compras/`, `/api/carrito/` | Datos privados; requieren sesión |

React invalida sus datos privados ante un 401 de una ruta protegida o cuando
`/api/session/` confirma que la sesión ya no existe. Un 403 de descarga solo se
trata como sesión expirada si su respuesta indica que falta sesión; errores de
compra o rol permanecen como errores de autorización. Errores de red y CSRF no
cierran automáticamente la sesión. La SPA vuelve a validar la sesión al
recuperar foco, al hacerse visible y periódicamente mientras haya identidad.
Django vuelve a comprobar autenticación y permisos en cada operación.

## Operaciones conectadas y contratos

`django.service.ts` contiene llamadas para catálogo, tracks, comentarios,
carrito, pago, subida, ventas/compras, likes, perfiles, usuarios y suscripciones.
Los mappers son la frontera entre nombres snake_case de Django y los tipos de
React. La carga del catálogo combina las páginas del backend para conservar el
catálogo completo y sus géneros; filtros y paginación se envían como parámetros.
Los totales de carrito proceden de Django y se actualizan con importes devueltos
por el servidor.

El backend devuelve estados de retorno de pago `exito`, `fracaso`, `cancelado`
o `revision`. React los adapta explícitamente a `approved`, `rejected`,
`cancelled` o `review`. El estado local `abandoned` solo describe un flujo
abandonado en el cliente; no confirma un resultado del servidor.

## Webpay

`server/app/views.py` valida el retorno de Transbank y Django es la fuente de
verdad del pago. La SPA solo presenta el resultado confirmado que Django
devuelve y luego vuelve a cargar compras y catálogo. El backend conserva el
carrito si el pago no queda autorizado y crea el historial de compra después
de validar el resultado. La anulación se reconcilia con los identificadores de
la transacción, porque el callback puede llegar sin cookie de sesión. La
descarga protegida vuelve a verificar propiedad y compra en Django.

Las pruebas locales pueden simular respuestas de Transbank, pero no verifican
credenciales, callbacks ni operación en producción. La validación del ambiente
real de Webpay requiere coordinación y configuración externa.

## Comprobaciones

- Backend: desde `server/`, `python manage.py check` y
  `python manage.py test app.test_auth_d3`.
- Frontend: desde `client/`, `npm run test`, `npm run lint` y `npm run build`.
- `app.test_auth_d3` verifica acceso anónimo, CSRF de login, rechazo de
  credenciales incorrectas, login/logout y expiración de sesión. Estas pruebas
  usan la base de datos temporal de Django; no sustituyen un recorrido manual.
- Recorrido manual sugerido: ejecutar Django y Vite en modo real; probar sesión
  anónima, login con cuenta activada, carrito y sus totales, logout, rutas
  privadas, expiración confirmada y revalidación; finalmente verificar el
  retorno de Webpay en el ambiente de integración.

En producción: HTTPS, `DEBUG=False`, secreto privado, `ALLOWED_HOSTS` y orígenes
CSRF configurados. Nunca versionar contraseñas, cookies, tokens ni archivos
`.env`.
