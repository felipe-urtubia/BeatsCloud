/**
 * DTOs espejo 1:1 del backend Django de Felipe (github.com/felipe-urtubia/BeatsCloud).
 * Nomenclatura snake_case idéntica a los serializers que expondrá la Fase B (DRF),
 * para que el día del swap el único cambio sea la URL base.
 * Fuente: app/models.py @ commit analizado 01-10-2026.
 */

export type DjangoUserId = number;

/** app.models.Usuario.tipo_usu */
export const TIPO_USU = { ARTISTA: 1, PRODUCTOR: 2 } as const;
export type TipoUsu = 1 | 2;

/** django.contrib.auth.User + perfil Usuario (payload combinado) */
export interface DUser {
  id: DjangoUserId;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  // Perfil Usuario (OneToOne)
  tipo_usu: TipoUsu | null;
  nombre_artistico: string;
  descripcion: string | null;
  foto_perfil: string | null;   // MEDIA_URL relativa o absoluta
  foto_fondo: string | null;
  spotify: string | null;
  youtube: string | null;
  instagram: string | null;
  /** Solo en login/sesión del propio usuario (nunca en payloads públicos, donde email viene vacío). */
  liked_track_ids?: number[];
  /** Solo en sesión propia; no se exponen las relaciones privadas en el directorio público. */
  subscription_ids?: number[];
}

/** app.models.Genero_Musical — 9 choices declarados */
export interface DGenero {
  id: number;
  descripcion: string; // 'Pop' | 'Rock' | 'Hip-Hop' | 'Electronica' | 'Reggaeton' | 'R&B' | 'Jazz' | 'Metal' | 'Soul'
}

/** app.models.Track */
export interface DTrack {
  id_track: number;
  nombre_track: string;
  precio: number; // CLP entero
  track: string | null;      // path media original -> servir por /track/<id>/reproducir/
  preview: string | null;    // mp3 30s FFmpeg -> /track/<id>/preview/ (abierto a anónimos)
  descripcion: string | null;
  foto: string | null;
  genero: DGenero;
  usuario: DUser;            // productor dueño
  likes_count?: number;      // tracks_gustados.count()
  is_purchased?: boolean;    // el usuario autenticado ya lo compró
  is_owner?: boolean;        // el usuario autenticado es el productor
  // Metadatos propuestos (migración 0016_track_metadata, ver docs/INTEGRACION_BACKEND.md §3-C)
  resource_type?: 'instrumental' | 'acapella' | 'loop' | 'drumkit';
  subgenre?: string;
  bpm?: number;
  scale_key?: string;
  mood?: string;
  has_stems?: boolean;
  has_wav?: boolean;
  has_midi?: boolean;
  allow_free_download?: boolean;
  has_watermark?: boolean;
  duration?: number;
}

/** Respuesta de GET /api/catalogo/ (espejo del contexto de catalogo()) */
export interface DCatalogoPage {
  tracks: DTrack[];
  total_resultados: number;
  pagina_actual: number;
  total_paginas: number;
  tracks_comprados: number[]; // ids que el usuario autenticado ya adquirió
  generos: DGenero[];
}

/** app.models.Venta (fila del carrito persistente, completada=False) */
export interface DVenta {
  id: number;
  detalle: string;
  fecha: string;
  precio: number;
  iva: number;               // round(precio * 0.19) — regla confirmada en views.py
  precio_total: number;
  track: number;             // id_track
}

/** app.models.Comentario */
export interface DComentario {
  id: number;
  usuario: { id: number; username: string; first_name: string; last_name: string };
  contenido: string;
  fecha_creacion: string;    // ISO
}

/** app.models.HistorialCompra */
export interface DHistorialCompra {
  id: number;
  track: DTrack;
  fecha_compra: string;
}

/** app.models.HistorialVenta */
export interface DHistorialVenta {
  id: number;
  comprador: { id: number; username: string } | null;
  precio: number;
  track: DTrack;
  fecha_venta: string;
}

/** app.models.WebpayTransaction */
export type WebpayStatus = 'PENDING' | 'AUTHORIZED' | 'CANCELLED';
export interface DWebpayTransaction {
  id: number;
  buy_order: string;
  session_id: string;
  amount: number;
  status: WebpayStatus;
  timestamp: string;
  suscripcion: number | null;
}

/** POST /api/pago/ -> resultado de tx.create() del SDK Transbank */
export interface DPagoInit {
  url_webpay: string;   // redirigir el navegador aquí
  token_ws: string;
  buy_order: string;
  amount: number;
  transaction_id: number;
}

/** app.models.Suscripcion */
export interface DSuscripcion {
  id_sus: number;
  detalle: string;
  precio: number;
  user: DUser;
}

export interface DLicense {
  license_code: string;
  verification_hash: string;
  issue_date: string;
  purchase_reference: string;
  amount_clp: number;
  track: DTrack;
  buyer: {
    id: number;
    username: string;
    nombre_artistico: string;
  };
}
