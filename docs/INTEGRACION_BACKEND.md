# Integración backend

## Estado del contrato

El frontend llama a Django mediante la capa tipada `client/src/api/`. `django.service.ts` define las rutas y tipos; `types.ts` contiene los DTO y `mappers.ts` transforma respuestas Django al modelo de interfaz. Vite reenvía `/api` y `/media` a `http://127.0.0.1:8000` durante desarrollo.

Rutas principales usadas: `GET /api/csrf/`, `GET /api/session/`, `POST /api/auth/login/`, `POST /api/auth/logout/`, `POST /api/auth/registro/`, `GET /api/catalogo/`, `GET /api/carrito/`, `POST /api/carrito/agregar/<id>/`, `POST /api/pago/`, `GET /api/track/<id>/descargar/`. La definición autoritativa del backend está en `server/app/api_shim.py` y `server/app/urls.py`.

## 2. Autenticación (DDPB-74)

La implementación existente es sesión de Django: login crea la sesión, el navegador conserva la cookie y las mutaciones envían `X-CSRFToken` obtenido desde `/api/csrf/`. Logout invalida la sesión en servidor. Los endpoints privados responden con `401` cuando no hay sesión; los permisos insuficientes responden con `403`. No se guarda un token bearer en `localStorage`.

La SPA captura respuestas `401` de rutas protegidas y el `403` de descarga solo cuando el mensaje indica que falta sesión; limpia estado privado y abre login con un aviso de sesión expirada. Un `403` por falta de compra conserva el error de autorización. Los `401` de credenciales incorrectas en login no activan la redirección. Logout limpia los datos privados y rehidrata el catálogo anónimo.


## 3. Modo API / mock (DDPB-81)

`VITE_API_MODE` selecciona `real` (API Django) o `mock` (demo local). `hybrid` sigue aceptado como alias temporal de `real` por compatibilidad. La selección se compila en Vite y se documenta en `client/.env.example`.

El catálogo, sesión, registro, login, carrito, creación de pago y datos de tracks tienen llamadas Django tipadas. El carrito muestra subtotal/IVA/total recibidos de Django y ajusta los totales por mutación usando los importes de la venta del servidor. El inicio del pago crea URL/token y la SPA publica el POST requerido por Webpay. El callback de Django confirma la operación antes de actualizar compras.

## 4. Diferencias y pendientes de contrato

- Las fechas y algunos montos se mapean desde los DTO del backend; conservar los mappers como frontera entre snake_case Django y el modelo de React.
- El backend usa `401` en la mayoría de rutas privadas y devuelve `403` en descargas sin sesión o sin compra. La SPA trata como expiración solo los `403` de descarga cuyo mensaje indica falta de sesión; los de compra/permisos conservan su error.
- La descarga protegida solo entrega el archivo `track`, no stems. En `real`, la SPA no presenta las descargas locales de texto como si fueran audio real; esas demos se conservan en `mock`.

## 5. Retorno post-pago

`server/app/views.py` valida `token_ws` con `commit()`. El retorno del carrito redirige a `SPA_URL/?pago=...` con `approved`, `rejected`, `cancelled` o `abandoned`. `SPA_URL` predetermina `http://localhost:3000` y se configura en `server/.env` para otro host local. La SPA muestra el estado y rehidrata catálogo/carrito. El backend solo borra ventas pendientes y crea `HistorialCompra` después de validar `AUTHORIZED`; en los otros estados conserva el carrito. Para la anulación, la búsqueda usa buy order y session ID aleatorio de esa transacción, pues el callback POST puede llegar sin cookie de sesión. La descarga se habilita desde el catálogo tras rehidratar `tracks_comprados`, y el endpoint de Django vuelve a verificar propiedad.

El test local usa un mock del cliente Transbank para verificar ramas de aprobación/rechazo/cancelación/abandono; no sustituye la prueba contra el ambiente de integración real.

## 6. Decisión final DDPB-66 / DDPB-74

**Aprobado: sesión de Django con cookie de sesión y CSRF. No se usa JWT ni se agrega Django REST Framework.** Login crea la sesión; `/api/csrf/` entrega el token para `X-CSRFToken`; logout invalida la sesión en Django. La SPA no persiste credenciales ni bearer tokens en `localStorage`.
