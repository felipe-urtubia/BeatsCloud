import type { DSubscriptionPlanInput, DSubscriptionPlanDetails } from './types';
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
 *   DELETE /api/track/<id>/comentarios/?id=<comment_id> (solo autor)
 *   GET    /api/carrito/                   -> {items, subtotal, iva, total} (totales server-side)
 *   POST   /api/carrito/agregar/<id>/      -> DVenta (409 duplicado/recompra)
 *   DELETE /api/carrito/<venta_id>/        -> {ok}
 *   POST   /api/pago/                      -> DPagoInit (redirigir navegador a url_webpay)
 *   POST   /api/pago/cancelar/<tx_id>/     -> {ok}
 *   POST   /api/upload/                    -> multipart DTrack (201)
 *   GET    /api/mis-ventas/ · /api/mis-compras/
 *   POST   /api/like/<id>/                 -> {liked: bool}
 *   GET    /api/perfil/<username>/         -> DUser + tracks
 *   GET    /api/usuarios/                  -> DUser[] (datos públicos)
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
  DCompraConfirmada,
  DHistorialVenta,
  DPagoInit,
  DSuscripcion,
  DLicense,
} from './types';

const BASE = ((import.meta.env.VITE_DJANGO_URL as string | undefined) ?? '').replace(/\/$/, '');

type R2PresignRequest = {
  kind: 'track' | 'stems' | 'cover';
  filename: string;
  content_type: string;
  size: number;
};

type R2PresignResponse = {
  method: 'PUT';
  url: string;
  headers: Record<string, string>;
  upload_token: string;
  expires_in: number;
};

type R2ConfirmResponse = {
  verified: boolean;
  kind: 'track' | 'stems' | 'cover';
  size: number;
  content_type: string;
  detail: string;
};

type R2FinalizeRequest = {
  upload_token: string;
  nombre_track: string;
  precio: number;
  genero_id: number;
  descripcion: string;
  subgenre: string;
  resource_type: string;
  bpm: number;
  scale_key: string;
  mood: string;
  has_stems: boolean;
  has_wav: boolean;
  has_midi: boolean;
  allow_free_download: boolean;
  has_watermark: boolean;
  duration: number;
  cover_upload_token?: string;
  stems_upload_token?: string;
};

type R2FinalizeResponse = DTrack;

let csrfToken: string | null = null;
const sessionInvalidationListeners = new Set<() => void>();
export function subscribeToSessionInvalidation(listener: () => void): () => void {
  sessionInvalidationListeners.add(listener);
  return () => { sessionInvalidationListeners.delete(listener); };
}
function invalidateApiSession() {
  csrfToken = null;
  for (const listener of sessionInvalidationListeners) {
    try { listener(); } catch (error) { console.error('[BeatCloud] Error al invalidar la sesion:', error); }
  }
}

async function parse(res: Response): Promise<any> {
  const isHtml = res.headers.get('content-type')?.includes('text/html') ?? false;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = res.status === 403 && isHtml
      ? 'No pudimos validar la seguridad de tu sesión. Recarga la página e inténtalo nuevamente.'
      : data.detail || data.message || `Error ${res.status}: ${res.statusText}`;
    const err = new Error(message) as Error & {
      status?: number;
      errors?: Record<string, string[]>;
      csrfFailure?: boolean;
    };
    err.status = res.status;
    err.errors = data.errors;
    err.csrfFailure = res.status === 403 && isHtml;
    throw err;
  }
  return data;
}

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers = new Headers(opts.headers);
  if (!(opts.body instanceof FormData) && opts.body != null) headers.set('Content-Type', 'application/json');
  if (csrfToken && opts.method && opts.method !== 'GET') headers.set('X-CSRFToken', csrfToken);
  const res = await fetch(`${BASE}${path}`, { ...opts, headers, credentials: 'same-origin' });
  if (res.status === 401 && path !== '/api/auth/login/') invalidateApiSession();
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
  tipo?: string;
  mood?: string;
  tonalidad?: string;
  bpm_min?: number;
  bpm_max?: number;
  has_stems?: string;
  precio?: string;
  orden?:
    | 'recientes'
    | 'antiguos'
    | 'precio_menor'
    | 'precio_mayor'
    | 'nombre'
    | 'nombre_asc'
    | 'nombre_desc'
    | 'genero_asc'
    | 'genero_desc'
    | 'bpm_asc'
    | 'bpm_desc'
    | 'likes';
  page?: number;
  page_size?: number;
}

export interface DAuthorizedAccount {
  id: number;
  username: string;
  is_current: boolean;
}

export interface DAuthorizedAccountsResponse {
  accounts: DAuthorizedAccount[];
  active_user_id: number;
}

export const DjangoApi = {
  // Sesión / auth
  getSession: () => ensureCsrf().then(() => request<DUser | null>('/api/session/')),

  // Cuentas adicionales autorizadas por la sesion Django.
  getAuthorizedAccounts: () =>
    request<DAuthorizedAccountsResponse>('/api/auth/accounts/'),

  addAuthorizedAccount: async (username: string, password: string) => {
    await ensureCsrf();

    return request<DAuthorizedAccountsResponse>(
      '/api/auth/accounts/add/',
      {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      },
    );
  },

  switchAuthorizedAccount: async (userId: number) => {
    await ensureCsrf();

    const response = await request<DAuthorizedAccountsResponse>(
      '/api/auth/accounts/switch/',
      {
        method: 'POST',
        body: JSON.stringify({ user_id: userId }),
      },
    );

    // Django rota CSRF cuando cambia la identidad autenticada.
    // El siguiente POST debe solicitar un token nuevo.
    csrfToken = null;

    return response;
  },
  usuarios: () => request<DUser[]>('/api/usuarios/'),
  login: async (username: string, password: string) => {
    const submit = () =>
      request<DUser>('/api/auth/login/', { method: 'POST', body: JSON.stringify({ username, password }) });
    await ensureCsrf();
    try {
      const user = await submit();
      csrfToken = null;
      return user;
    } catch (error) {
      if (!(error instanceof Error) || !(error as Error & { csrfFailure?: boolean }).csrfFailure) throw error;
      csrfToken = null;
      await ensureCsrf();
      const user = await submit();
      csrfToken = null;
      return user;
    }
  },
  activarCuenta: (uidb64: string, token: string) =>
    ensureCsrf().then(() =>
      request<{ detail: string }>('/api/auth/activar/', {
        method: 'POST',
        body: JSON.stringify({ uidb64, token }),
      }),
    ),
  solicitarRestauracionContrasena: (email: string) =>
    ensureCsrf().then(() =>
      request<{ detail: string }>('/api/auth/password-reset/', {
        method: 'POST',
        body: JSON.stringify({ email }),
      }),
    ),
  confirmarRestauracionContrasena: (
    uidb64: string,
    token: string,
    newPassword: string,
    confirmPassword: string,
  ) =>
    ensureCsrf().then(() =>
      request<{ detail: string }>('/api/auth/password-reset/confirm/', {
        method: 'POST',
        body: JSON.stringify({
          uidb64,
          token,
          new_password1: newPassword,
          new_password2: confirmPassword,
        }),
      }),
    ),
  logout: () => request<{ ok: boolean }>('/api/auth/logout/', { method: 'POST' }),
  registro: (form: FormData) =>
    ensureCsrf().then(() => request<{ detail: string }>('/api/auth/registro/', { method: 'POST', body: form })),

  // Catálogo / tracks
  catalogo: (p: CatalogoParams = {}, signal?: AbortSignal) =>
    request<DCatalogoPage>(
      `/api/catalogo/${qsp(p as Record<string, string | number>)}`,
      { signal },
    ),
  track: (id: number) => request<DTrack>(`/api/track/${id}/`),
  updateTrack: (id: number, data: FormData | Partial<DTrack>) =>
    request<DTrack>(`/api/track/${id}/`, {
      method: 'PATCH',
      body: data instanceof FormData ? data : JSON.stringify(data),
    }),
  deleteTrack: (id: number) => request<{ ok: boolean }>(`/api/track/${id}/delete/`, { method: 'POST' }),
  claimFreeTrack: (id: number) =>
    ensureCsrf().then(() => request<{ ok: boolean }>(`/api/track/${id}/claim-free/`, { method: 'POST' })),
  license: (id: number) => request<DLicense>(`/api/track/${id}/license/`),
  downloadTrack: async (id: number, fallbackName: string) => {
    const response = await fetch(`${BASE}/api/track/${id}/descargar/`, { credentials: 'same-origin' });
    if (!response.ok) {
      if (response.status === 401) invalidateApiSession();
      const detail = await response.text();
      throw new Error(detail || `No se pudo descargar la pista (${response.status}).`);
    }

    const contentType = response.headers.get('content-type') ?? '';

    // R2: el navegador descarga directamente desde Cloudflare con URL temporal.
    if (contentType.includes('application/json')) {
      const payload = await response.json() as {
        method?: unknown;
        url?: unknown;
        filename?: unknown;
        expires_in?: unknown;
      };

      if (typeof payload.url !== 'string' || typeof payload.filename !== 'string') {
        throw new Error('El servidor devolvio un enlace de descarga invalido.');
      }

      let signedUrl: URL;
      try {
        signedUrl = new URL(payload.url);
      } catch {
        throw new Error('El servidor devolvio una URL de descarga invalida.');
      }

      if (
        signedUrl.protocol !== 'https:' ||
        !signedUrl.hostname.endsWith('.r2.cloudflarestorage.com') ||
        signedUrl.username ||
        signedUrl.password
      ) {
        throw new Error('El servidor devolvio un destino de descarga no permitido.');
      }

      const link = document.createElement('a');
      link.href = signedUrl.toString();
      link.download = payload.filename;
      link.rel = 'noopener noreferrer';
      document.body.appendChild(link);
      link.click();
      link.remove();
      return;
    }

    // Almacenamiento local: conserva la descarga binaria existente.
    const disposition = response.headers.get('content-disposition') ?? '';
    const encodedFilename = disposition.match(/filename\*\s*=\s*UTF-8''([^;]+)/i)?.[1];
    const plainFilename =
      disposition.match(/filename\s*=\s*"([^"]+)"/i)?.[1] ??
      disposition.match(/filename\s*=\s*([^;]+)/i)?.[1]?.trim();

    let filename = plainFilename ?? `${fallbackName}.wav`;

    if (encodedFilename) {
      try {
        filename = decodeURIComponent(encodedFilename);
      } catch {
        // Conserva el nombre alternativo si la codificacion es invalida.
      }
    }
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  },
  downloadPreview: async (id: number, fallbackName: string) => {
    const response = await fetch(`${BASE}/api/track/${id}/preview/`, { credentials: 'same-origin' });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `No se pudo descargar la maqueta (${response.status}).`);
    }
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = url;
    link.download = `${fallbackName}_preview.mp3`;
    link.click();
    URL.revokeObjectURL(url);
  },
  upload: (form: FormData) => ensureCsrf().then(() => request<DTrack>('/api/upload/', { method: 'POST', body: form })),
  downloadStems: async (id: number, fallbackName: string) => {
    const response = await fetch(`${BASE}/api/track/${id}/stems/`, {
      credentials: 'same-origin',
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `No se pudieron descargar los STEMS (${response.status}).`);
    }
    const blob = await response.blob();
    const disposition = response.headers.get('content-disposition') || '';
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = match?.[1] || `${fallbackName}_STEMS.zip`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },

  r2Presign: (data: R2PresignRequest) =>
    ensureCsrf().then(() =>
      request<R2PresignResponse>('/api/r2/presign/', {
        method: 'POST',
        body: JSON.stringify(data),
      })
    ),

  r2Confirm: (uploadToken: string) =>
    ensureCsrf().then(() =>
      request<R2ConfirmResponse>('/api/r2/confirm/', {
        method: 'POST',
        body: JSON.stringify({
          upload_token: uploadToken,
        }),
      })
    ),

  r2Finalize: (data: R2FinalizeRequest, coverFile?: File) =>
    ensureCsrf().then(() => {
      const form = new FormData();
      Object.entries(data).forEach(([key, value]) => {
        form.set(key, String(value));
      });
      if (coverFile) form.set('foto', coverFile, coverFile.name);
      return request<R2FinalizeResponse>('/api/r2/finalize/', {
        method: 'POST',
        body: form,
      });
    }),
  updateProfile: (form: FormData) =>
    ensureCsrf().then(() => request<DUser>('/api/perfil/', { method: 'PATCH', body: form })),
  iniciarEliminacionCuenta: (password: string) =>
    ensureCsrf().then(() =>
      request<{ detail: string }>('/api/auth/account-deletion/start/', {
        method: 'POST',
        body: JSON.stringify({ password }),
      }),
    ),
  confirmarEliminacionCuenta: (codigo: string) =>
    ensureCsrf().then(() =>
      request<{ ok: boolean }>('/api/auth/account-deletion/confirm/', {
        method: 'POST',
        body: JSON.stringify({ codigo }),
      }),
    ),

  // Comentarios / likes
  comentarios: (id: number) => request<DComentario[]>(`/api/track/${id}/comentarios/`),
  addComment: (id: number, contenido: string) =>
    ensureCsrf().then(() =>
      request<DComentario>(`/api/track/${id}/comentarios/`, { method: 'POST', body: JSON.stringify({ contenido }) }),
    ),
  deleteComment: (trackId: number, commentId: number) =>
    ensureCsrf().then(() =>
      request<{ ok: boolean }>(`/api/track/${trackId}/comentarios/?id=${commentId}`, { method: 'DELETE' }),
    ),
  toggleLike: (id: number) => ensureCsrf().then(() => request<{ liked: boolean }>(`/api/like/${id}/`, { method: 'POST' })),
  setLike: (id: number, liked: boolean) => ensureCsrf().then(() => request<{ liked: boolean }>(`/api/like/${id}/`, {
    method: 'POST',
    body: JSON.stringify({ liked }),
  })),

  // Carrito (precios/IVA SIEMPRE del servidor)
  // El contexto solo consulta carrito tras confirmar una sesión autenticada.
  // Un 401 aquí debe conservarse como error de sincronización, no disfrazarse de carrito vacío.
  carrito: () => request<{ items: DVenta[]; subtotal: number; iva: number; total: number }>(`/api/carrito/`),
  addToCart: (trackId: number) =>
    ensureCsrf().then(() => request<DVenta>(`/api/carrito/agregar/${trackId}/`, { method: 'POST' })),
  removeFromCart: (ventaId: number) => request<{ ok: boolean }>(`/api/carrito/${ventaId}/`, { method: 'DELETE' }),

  // Pago Webpay — el SPA solo INICIA; la validación vive en el retorno HTML de Django
  initPago: (subscriptionId?: number) =>
    ensureCsrf().then(() =>
      request<DPagoInit>('/api/pago/', {
        method: 'POST',
        ...(subscriptionId === undefined ? {} : { body: JSON.stringify({ subscription_id: subscriptionId }) }),
      }),
    ),
  crearSuscripcion: (
    detalle: string,
    precio: number,
    details: DSubscriptionPlanDetails = {},
  ) =>
    ensureCsrf().then(() =>
      request<DSuscripcion>('/api/suscripciones/', {
        method: 'POST',
        body: JSON.stringify({ detalle, precio, ...details }),
      }),
    ),

  editarSuscripcion: (
    id: number,
    data: Partial<DSubscriptionPlanInput>,
  ) =>
    ensureCsrf().then(() =>
      request<DSuscripcion>(`/api/suscripciones/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    ),
  cancelPago: (transactionId: number) =>
    ensureCsrf().then(() => request<{ ok: boolean }>(`/api/pago/cancelar/${transactionId}/`, { method: 'POST' })),

  // Productor / artista
  misVentas: () => request<DHistorialVenta[]>('/api/mis-ventas/'),
  misCompras: () => request<DHistorialCompra[]>('/api/mis-compras/'),
  misComprasConfirmadas: () => request<DCompraConfirmada[]>('/api/mis-compras/confirmadas/'),
  perfil: (username: string) =>
    request<DUser & { tracks: DTrack[] }>(`/api/perfil/${encodeURIComponent(username)}/`),
  suscripciones: (userId?: string | number) =>
    request<DSuscripcion[]>(`/api/suscripciones/${userId ? qsp({ user: userId }) : ''}`),
};

export default DjangoApi;
