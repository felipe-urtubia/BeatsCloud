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
