/**
 * django.service.ts — Cliente tipado de la API JSON del backend Django (api_shim.py).
 *
 * Contrato verificado contra `backend-integration/api_shim.py` (Fase B):
 *   GET    /api/csrf/                      -> {detail: token}
 *   GET    /api/session/                   -> DUser | null
 *   POST   /api/auth/login/                -> DUser (401 credenciales, 403 sin activar)
 *   POST   /api/auth/logout/               -> {ok}
 *   POST   /api/auth/registro/             -> multipart (activación por correo)
 *   GET    /api/catalogo/?q=&genero=&precio=&orden=&page=  -> DCatalogoPage
 *   GET    /api/track/<id>/                -> DTrack (+is_purchased)   PATCH mismo endpoint
 *   POST   /api/track/<id>/delete/         -> {ok} (409 si tiene ventas)
 *   GET    /api/track/<id>/comentarios/    -> DComentario[]            POST {contenido}
 *   GET    /api/carrito/                   -> {items, subtotal, iva, total} (totales server-side)
 *   POST   /api/carrito/agregar/<id>/      -> DVenta (409 duplicado/recompra)
 *   DELETE /api/carrito/<venta_id>/        -> {ok}
 *   POST   /api/pago/                      -> DPagoInit (redirigir navegador a url_webpay)
 *   POST   /api/pago/cancelar/<tx_id>/     -> {ok}
 *   POST   /api/upload/                    -> multipart DTrack (201)
 *   GET    /api/mis-ventas/ · /api/mis-compras/
 *   POST   /api/like/<id>/                 -> {liked: bool}
 *   GET    /api/perfil/<username>/         -> DUser + tracks
 *   GET    /api/suscripciones/?user=       -> DSuscripcion[]
 *
 * Auth: sesión por cookie de Django + handshake CSRF (header X-CSRFToken), no JWT.
 */
import type {
  DUser,
  DTrack,
  DCatalogoPage,
  DVenta,
  DComentario,
  DHistorialCompra,
  DHistorialVenta,
  DPagoInit,
  DSuscripcion,
} from './types';

const BASE = ((import.meta.env.VITE_DJANGO_URL as string | undefined) ?? '').replace(/\/$/, '');

let csrfToken: string | null = null;

async function parse(res: Response): Promise<any> {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.detail || data.message || `Error ${res.status}: ${res.statusText}`) as Error & {
      status?: number;
      errors?: Record<string, string[]>;
    };
    err.status = res.status;
    err.errors = data.errors;
    throw err;
  }
  return data;
}

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers = new Headers(opts.headers);
  if (!(opts.body instanceof FormData) && opts.body != null) headers.set('Content-Type', 'application/json');
  if (csrfToken && opts.method && opts.method !== 'GET') headers.set('X-CSRFToken', csrfToken);
  const res = await fetch(`${BASE}${path}`, { ...opts, headers, credentials: 'same-origin' });
  return parse(res) as Promise<T>;
}

/** Handshake CSRF que hace SPA + Django. Idempotente y barato. */
export async function ensureCsrf(): Promise<string> {
  if (!csrfToken) {
    const d = await request<{ detail: string }>('/api/csrf/');
    csrfToken = d.detail;
  }
  return csrfToken;
}

const qsp = (params: Record<string, string | number | undefined>) => {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== '') qs.set(k, String(v));
  });
  const s = qs.toString();
  return s ? `?${s}` : '';
};

export interface CatalogoParams {
  q?: string;
  genero?: string;
  precio?: string; // '0-5000' | '5001-10000' | '10001-20000' | '20001-mas'
  orden?: 'recientes' | 'antiguos' | 'precio_menor' | 'precio_mayor' | 'nombre';
  page?: number;
}

export const DjangoApi = {
  // Sesión / auth
  getSession: () => ensureCsrf().then(() => request<DUser | null>('/api/session/')),
  login: (username: string, password: string) =>
    ensureCsrf().then(() =>
      request<DUser>('/api/auth/login/', { method: 'POST', body: JSON.stringify({ username, password }) }),
    ),
  logout: () => request<{ ok: boolean }>('/api/auth/logout/', { method: 'POST' }),
  registro: (form: FormData) =>
    ensureCsrf().then(() => request<{ detail: string }>('/api/auth/registro/', { method: 'POST', body: form })),

  // Catálogo / tracks
  catalogo: (p: CatalogoParams = {}) => request<DCatalogoPage>(`/api/catalogo/${qsp(p as Record<string, string | number>)}`),
  track: (id: number) => request<DTrack>(`/api/track/${id}/`),
  updateTrack: (id: number, data: Partial<Pick<DTrack, 'nombre_track' | 'precio' | 'descripcion'>>) =>
    request<DTrack>(`/api/track/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteTrack: (id: number) => request<{ ok: boolean }>(`/api/track/${id}/delete/`, { method: 'POST' }),
  upload: (form: FormData) => ensureCsrf().then(() => request<DTrack>('/api/upload/', { method: 'POST', body: form })),

  // Comentarios / likes
  comentarios: (id: number) => request<DComentario[]>(`/api/track/${id}/comentarios/`),
  addComment: (id: number, contenido: string) =>
    ensureCsrf().then(() =>
      request<DComentario>(`/api/track/${id}/comentarios/`, { method: 'POST', body: JSON.stringify({ contenido }) }),
    ),
  toggleLike: (id: number) => ensureCsrf().then(() => request<{ liked: boolean }>(`/api/like/${id}/`, { method: 'POST' })),

  // Carrito (precios/IVA SIEMPRE del servidor)
  // El contexto solo consulta carrito tras confirmar una sesión autenticada.
  // Un 401 aquí debe conservarse como error de sincronización, no disfrazarse de carrito vacío.
  carrito: () => request<{ items: DVenta[]; subtotal: number; iva: number; total: number }>(`/api/carrito/`),
  addToCart: (trackId: number) =>
    ensureCsrf().then(() => request<DVenta>(`/api/carrito/agregar/${trackId}/`, { method: 'POST' })),
  removeFromCart: (ventaId: number) => request<{ ok: boolean }>(`/api/carrito/${ventaId}/`, { method: 'DELETE' }),

  // Pago Webpay — el SPA solo INICIA; la validación vive en el retorno HTML de Django
  initPago: () => ensureCsrf().then(() => request<DPagoInit>('/api/pago/', { method: 'POST' })),
  cancelPago: (transactionId: number) =>
    ensureCsrf().then(() => request<{ ok: boolean }>(`/api/pago/cancelar/${transactionId}/`, { method: 'POST' })),

  // Productor / artista
  misVentas: () => request<DHistorialVenta[]>('/api/mis-ventas/'),
  misCompras: () => request<DHistorialCompra[]>('/api/mis-compras/'),
  perfil: (username: string) =>
    request<DUser & { tracks: DTrack[] }>(`/api/perfil/${encodeURIComponent(username)}/`),
  suscripciones: (userId?: string | number) =>
    request<DSuscripcion[]>(`/api/suscripciones/${userId ? qsp({ user: userId }) : ''}`),
};

export default DjangoApi;
