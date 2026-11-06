export type UserType = 'artista' | 'productor';

export interface User {
  id: string;
  username: string;
  artistName: string;
  email: string;
  role: UserType;
  bio: string;
  avatarUrl: string;
  bannerUrl: string;
  spotify?: string;
  youtube?: string;
  instagram?: string;
  subscriptions?: string[]; // IDs de productores a los que se está suscrito
  purchasedTrackIds: string[];
  likedTrackIds: string[];
  hasProfile?: boolean;
}

export type MusicGenre =
  | 'Hip-Hop'
  | 'Trap'
  | 'Reggaeton'
  | 'Electronica'
  | 'R&B'
  | 'Pop'
  | 'Rock'
  | 'Drill'
  | 'Boom-Bap'
  | 'Soul'
  | 'Jazz'
  | 'Metal'
  | (string & {});

export type ResourceType = 'instrumental' | 'acapella' | 'loop' | 'drumkit';

export type MoodType =
  | 'Oscuro'
  | 'Enérgico'
  | 'Chill / Relax'
  | 'Triste / Nostálgico'
  | 'Bailable'
  | 'Agresivo';

export interface TrackComment {
  id: string;
  userId: string;
  username: string;
  userAvatar: string;
  content: string;
  createdAt: string;
}

export interface Track {
  id: string;
  title: string;
  producerId: string;
  producerName: string;
  producerUsername: string;
  producerAvatar: string;
  resourceType: ResourceType; // instrumental, acapella, loop, drumkit
  genre: MusicGenre;
  subgenre?: string;
  price: number; // En CLP (ej: 18000)
  coverUrl: string;
  description: string;
  bpm: number;
  scaleKey: string;
  mood: MoodType;
  duration: number; // en segundos
  likesCount: number;
  tags: string[];
  audioBeatType: 'trap' | 'boom_bap' | 'reggaeton' | 'synthwave' | 'rnb' | 'lofi';
  hasStems: boolean;
  hasWav: boolean;
  hasMidi: boolean;
  isFree?: boolean; // Beat gratuito ($0 CLP)
  allowFreeDownload?: boolean; // Permite descarga directa de demo / no comercial
  hasWatermark?: boolean; // Preescucha con marca de agua de seguridad
  comments: TrackComment[];
  createdAt: string;
}

export interface ProducerSubscription {
  id: string;
  producerId: string;
  title: string;
  price: number;
  period?: 'mensual' | 'anual';
  benefits: string[];
}

export interface CartItem {
  track: Track;
  addedAt: string;
}

// Modelos alineados con la BD Django original (HistorialVenta, HistorialCompra, WebpayTransaction)
export interface LicenseContract {
  licenseCode: string; // Ej: LIC-BC-541209
  verificationHash: string; // Hash SHA-256 de verificación digital
  issueDate: string;
  trackId: string;
  trackTitle: string;
  trackGenre: string;
  trackBpm: number;
  trackKey: string;
  producerId: string;
  producerName: string;
  producerUsername: string;
  producerRut: string;
  buyerId: string;
  buyerName: string;
  buyerUsername: string;
  buyerRut: string;
  amountClp: number;
  buyOrder: string;
  licenseType: 'comercial_wav_stems' | 'exclusiva' | 'maqueta_ensayo';
  musicRightsSplit: {
    producerPercent: number; // Ej: 50% derechos de autoría y composición musical
    artistPercent: number; // Ej: 50% letra e interpretación
    scdRegistered: boolean;
  };
  distributionTerms: {
    streamsLimit: string; // "Ilimitado" o "Hasta 500.000 streams"
    musicVideoMonetized: boolean;
    radioBroadcasting: boolean;
    livePerformancesForProfit: boolean;
    contentIdProtected: boolean;
  };
}

export interface SaleRecord {
  id: string;
  buyerId: string;
  buyerName: string;
  trackId: string;
  trackTitle: string;
  amount: number;
  date: string;
  status: 'AUTHORIZED' | 'PENDING' | 'CANCELLED';
  buyOrder: string;
  licenseCode?: string;
  verificationHash?: string;
  licenseType?: 'comercial_wav_stems' | 'exclusiva' | 'maqueta_ensayo';
}

export interface PurchaseRecord {
  id: string;
  userId: string;
  trackId: string;
  trackTitle: string;
  producerName: string;
  amount: number;
  buyOrder: string;
  date: string;
  downloadUrl?: string;
  licenseCode?: string;
  verificationHash?: string;
  licenseType?: 'comercial_wav_stems' | 'exclusiva' | 'maqueta_ensayo';
  webpayAmount?: number; // Total autorizado por Transbank (precio + IVA), espejo de WebpayTransaction.amount
}

export interface WebpayTransactionRecord {
  token: string;
  buyOrder: string;
  sessionId: string;
  amount: number;
  status: 'INITIALIZED' | 'AUTHORIZED' | 'FAILED' | 'REJECTED';
  createdAt: string;
}
