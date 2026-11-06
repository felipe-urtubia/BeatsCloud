/**
 * mappers.ts — Traducción entre los DTOs snake_case del backend Django de Felipe
 * y los tipos camelCase que consume la UI React (src/types.ts).
 *
 * REGLA DE ORO: la UI nunca debe ver snake_case ni ids numéricos crudos;
 * todo pasa por estos mapeadores. Si mañana DRF cambia un campo, solo se toca aquí.
 */
import type {
  ProducerSubscription,
  Track,
  User,
  UserType,
  MusicGenre,
  SaleRecord,
  PurchaseRecord,
} from '../types';
import type {
  DTrack,
  DUser,
  DVenta,
  DHistorialVenta,
  DHistorialCompra,
  DComentario,
  DSuscripcion,
  DLicense,
} from './types';

const DJANGO_BASE: string = (((import.meta as any).env?.VITE_DJANGO_URL as string | undefined) ?? '').replace(/\/$/, ''); // '' = mismo origen (proxy de Vite)

/** Rutas protegidas confirmadas en app/urls.py — el <audio> apunta aquí, no a /media/. */
export const audioFullUrl = (idTrack: number) => `${DJANGO_BASE}/track/${idTrack}/reproducir/`;
export const audioPreviewUrl = (idTrack: number) => `${DJANGO_BASE}/track/${idTrack}/preview/`;
// Espejo de las rutas que expone api_shim.py para el SPA (prefijo /api/)
export const apiAudioFullUrl = (idTrack: number) => `${DJANGO_BASE}/api/track/${idTrack}/reproducir/`;
export const apiAudioPreviewUrl = (idTrack: number) => `${DJANGO_BASE}/api/track/${idTrack}/preview/`;
export const apiDownloadUrl = (idTrack: number) => `${DJANGO_BASE}/api/track/${idTrack}/descargar/`;
export const mediaUrl = (path: string | null): string | null =>
  path ? (path.startsWith('http') ? path : `${DJANGO_BASE}${path.startsWith('/') ? '' : '/'}${path}`) : null;

/** Genero_Musical.descripcion -> MusicGenre de la UI (con alias para variantes de spelling) */
// MusicGenre de la UI no incluye Jazz/Metal -> mapeo a la variante más cercana.
const GENERO_MAP: Record<string, MusicGenre> = {
  'Pop': 'Pop', 'Rock': 'Rock', 'Hip-Hop': 'Hip-Hop', 'Electronica': 'Electronica',
  'Reggaeton': 'Reggaeton', 'R&B': 'R&B', 'Jazz': 'Boom-Bap', 'Metal': 'Drill', 'Soul': 'Soul',
};

const slug = (n: number) => `dj-${n}`; // ids UI como string estable ("dj-42")

export function mapUser(d: DUser): User {
  const role: UserType = d.tipo_usu === 2 ? 'productor' : 'artista';
  return {
    id: String(d.id),
    username: d.username,
    artistName: d.nombre_artistico || (
      d.first_name && d.last_name ? `${d.first_name} ${d.last_name}` : d.first_name || d.username
    ),
    email: d.email,
    role,
    hasProfile: d.tipo_usu !== null,
    bio: d.descripcion ?? '',
    avatarUrl: mediaUrl(d.foto_perfil) ?? `https://api.dicebear.com/7.x/shapes/svg?seed=${d.username}`,
    bannerUrl: mediaUrl(d.foto_fondo) ?? '',
    spotify: d.spotify ?? undefined,
    youtube: d.youtube ?? undefined,
    instagram: d.instagram ?? undefined,
    subscriptions: (d.subscription_ids ?? []).map((id) => `sus-${id}`),
    purchasedTrackIds: [],   // se hidratan con tracks_comprados del catálogo
    likedTrackIds: (d.liked_track_ids ?? []).map(slug),
  };
}

export function mapTrack(d: DTrack, opts?: { isPurchased?: boolean; isOwner?: boolean }): Track {
  const free = d.precio === 0;
  return {
    id: slug(d.id_track),
    title: d.nombre_track,
    producerId: String(d.usuario.id),
    producerName: d.usuario.nombre_artistico || d.usuario.username,
    producerUsername: d.usuario.username,
    producerAvatar: mediaUrl(d.usuario.foto_perfil) ?? `https://api.dicebear.com/7.x/shapes/svg?seed=${d.usuario.username}`,
    resourceType: d.resource_type ?? 'instrumental',
    genre: GENERO_MAP[d.genero?.descripcion] ?? 'Hip-Hop',
    subgenre: d.subgenre ?? '',
    price: d.precio,
    coverUrl: mediaUrl(d.foto) ?? `https://picsum.photos/seed/${d.id_track}/600/600`,
    description: d.descripcion ?? '',
    bpm: d.bpm ?? 140,
    scaleKey: d.scale_key ?? 'Am',
    mood: (d.mood as Track['mood']) ?? 'Oscuro',
    duration: d.duration ?? 30, // preview dura 30s (FFmpeg -t 30 en audio_utils.py)
    likesCount: d.likes_count ?? 0,
    tags: [d.genero?.descripcion].filter(Boolean) as string[],
    audioBeatType: beatTypeFromGenre(d.genero?.descripcion ?? ''),
    hasStems: d.has_stems ?? false,
    hasWav: d.has_wav ?? true,
    hasMidi: d.has_midi ?? false,
    isFree: free,
    allowFreeDownload: d.allow_free_download ?? free,
    // Marca de agua = NO comprado y NO gratis. El audio real lo decide Django
    // (preview abierto vs reproducir restringido); esto solo pilota el badge/baja de gain.
    hasWatermark: !(opts?.isPurchased || opts?.isOwner || free),
    comments: [],
    createdAt: new Date().toISOString(),
    // Extensión opcional propia del frontend para el motor de reproducción.
    // Apuntan a las rutas /api/track/<id>/... que expone api_shim.py (Fase B):
    // el preview es abierto a anónimos; reproducir/descargar tienen guarda server-side.
    ...(d.preview ? { previewSrc: apiAudioPreviewUrl(d.id_track) } : {}),
    ...(d.track ? { fullSrc: apiAudioFullUrl(d.id_track), downloadSrc: apiDownloadUrl(d.id_track) } : {}),
  } as Track & { previewSrc?: string; fullSrc?: string; downloadSrc?: string };
}

/** Aproximación hasta que audioAnalyzer corra sobre el archivo real subido. */
function beatTypeFromGenre(g: string): Track['audioBeatType'] {
  if (/reggaeton/i.test(g)) return 'reggaeton';
  if (/hip|drill|trap/i.test(g)) return 'trap';
  if (/electr/i.test(g)) return 'synthwave';
  if (/r&b|soul/i.test(g)) return 'rnb';
  if (/jazz/i.test(g)) return 'lofi';
  return 'boom_bap';
}

export function mapVentaToCartItem(d: DVenta, track: Track) {
  return { track, addedAt: d.fecha };
}

export function mapHistorialVenta(d: DHistorialVenta): SaleRecord {
  return {
    id: `sv-${d.id}`,
    trackId: slug(d.track.id_track),
    trackTitle: d.track.nombre_track,
    buyerId: d.comprador ? String(d.comprador.id) : 'anon',
    buyerName: d.comprador?.username ?? 'Usuario eliminado',
    amount: d.precio,
    date: d.fecha_venta,
    soldAt: d.fecha_venta, // alias decorativo para componentes que lo muestran
    status: 'AUTHORIZED' as const,
    buyOrder: `WEBPAY-${d.id}`,
    receiptCode: `WEBPAY-${d.id}`,
    licenseType: 'comercial_wav_stems',
  } as unknown as SaleRecord;
}

export function mapHistorialCompra(d: DHistorialCompra, buyerUserId: string): PurchaseRecord {
  return {
    id: `sc-${d.id}`,
    userId: buyerUserId,
    trackId: slug(d.track.id_track),
    trackTitle: d.track.nombre_track,
    producerName: d.track.usuario.nombre_artistico || d.track.usuario.username,
    amount: d.track.precio,
    date: d.fecha_compra,
    purchasedAt: d.fecha_compra, // alias decorativo
    buyOrder: `WEBPAY-${d.id}`,
    receiptCode: `WEBPAY-${d.id}`,
    downloadUrl: apiDownloadUrl(d.track.id_track),
    licenseType: 'comercial_wav_stems',
  } as unknown as PurchaseRecord;
}

export function mapSubscription(d: DSuscripcion): ProducerSubscription {
  return {
    id: `sus-${d.id_sus}`,
    producerId: String(d.user.id),
    title: d.detalle,
    price: d.precio,
    benefits: [],
  };
}

export function mapLicense(d: DLicense): import('../types').LicenseContract {
  const producer = d.track.usuario;
  return {
    licenseCode: d.license_code,
    verificationHash: `HMAC-SHA256:${d.verification_hash}`,
    issueDate: d.issue_date,
    trackId: slug(d.track.id_track),
    trackTitle: d.track.nombre_track,
    trackGenre: d.track.genero.descripcion,
    trackBpm: d.track.bpm ?? 0,
    trackKey: d.track.scale_key ?? 'No informado',
    producerId: String(producer.id),
    producerName: producer.nombre_artistico || producer.username,
    producerUsername: producer.username,
    producerRut: 'No registrado',
    buyerId: String(d.buyer.id),
    buyerName: d.buyer.nombre_artistico || d.buyer.username,
    buyerUsername: d.buyer.username,
    buyerRut: 'No registrado',
    amountClp: d.amount_clp,
    buyOrder: d.purchase_reference,
    licenseType: d.amount_clp === 0 ? 'maqueta_ensayo' : 'comercial_wav_stems',
    musicRightsSplit: { producerPercent: 0, artistPercent: 0, scdRegistered: false },
    distributionTerms: {
      streamsLimit: 'No especificado por Django',
      musicVideoMonetized: false,
      radioBroadcasting: false,
      livePerformancesForProfit: false,
      contentIdProtected: false,
    },
  };
}

export function mapComentario(d: DComentario): Track['comments'][number] {
  return {
    id: `cm-${d.id}`,
    userId: String(d.usuario.id),
    username: d.usuario.username,
    userAvatar: `https://api.dicebear.com/7.x/shapes/svg?seed=${d.usuario.username}`,
    content: d.contenido,
    createdAt: d.fecha_creacion,
  };
}

/** 'dj-42' -> 42 (para devolver ids numéricos a Django) */
export const djangoId = (uiId: string): number => Number(uiId.replace(/^dj-/, ''));
