import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import {
  User,
  Track,
  CartItem,
  ProducerSubscription,
  SaleRecord,
  PurchaseRecord,
  UserType,
  ResourceType,
  MusicGenre,
  MoodType,
  LicenseContract,
} from '../types';
import {
  INITIAL_USERS,
  INITIAL_TRACKS,
  INITIAL_SUBSCRIPTIONS,
  INITIAL_SALES,
  INITIAL_PURCHASES,
} from '../data/mockData';
import { audioEngine } from '../utils/audioEngine';
import DjangoApi from '../api/django.service';
import { mapTrack, mapUser, djangoId } from '../api/mappers';
import { startWebpayCheckout, submitWebpayForm } from '../api/webpayCheckout.mjs';
import type { WebpayCheckoutResult } from '../api/webpayCheckout.mjs';

/**
 * MODO DE INTEGRACIÓN — "punto medio" para el Sprint 1 (ver docs/INTEGRACION_BACKEND.md):
 *   mock   → todo localStorage (demo sin backend, plan de respaldo si falla la red)
 *   hybrid → DATOS REALES del backend Django (catálogo, sesión y carrito) sobre la UI
 *            existente. Las colecciones no confirmadas comienzan vacías; un fallo
 *            de sincronización no cambia el modo efectivo a mock.
 * Se selecciona con VITE_API_MODE (default: 'hybrid'). Si el backend no responde
 * al arrancar, la UI conserva hybrid y permite reintentar la sincronización.
 */
export type ApiMode = 'mock' | 'hybrid';
const CONFIGURED_MODE: ApiMode =
  ((import.meta.env.VITE_API_MODE as string | undefined) || 'hybrid') === 'mock' ? 'mock' : 'hybrid';

// Extensión interna del Track para URLs de audio real (la inyecta mappers.mapTrack)
type TrackWithSrc = Track & { previewSrc?: string; fullSrc?: string; downloadSrc?: string };

interface AppContextType {
  currentUser: User | null;
  users: User[];
  tracks: Track[];
  cart: CartItem[];
  subscriptions: ProducerSubscription[];
  sales: SaleRecord[];
  purchases: PurchaseRecord[];
  activeTrack: Track | null;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  globalSearchQuery: string;
  setGlobalSearchQuery: (q: string) => void;
  activeResourceFilter: ResourceType | 'all';
  setActiveResourceFilter: (filter: ResourceType | 'all') => void;
  playTrack: (track: Track) => void;
  togglePlay: () => void;
  seekAudio: (seconds: number) => void;
  setAudioVolume: (volume: number) => void;
  toggleLike: (trackId: string) => void;
  addToCart: (track: Track) => boolean;
  removeFromCart: (trackId: string) => void;
  clearCart: () => void;
  checkoutCart: () => Promise<WebpayCheckoutResult>;
  uploadTrack: (data: {
    title: string;
    resourceType: ResourceType;
    genre: MusicGenre;
    subgenre?: string;
    price: number;
    description: string;
    coverUrl?: string;
    bpm: number;
    scaleKey: string;
    mood: MoodType;
    audioBeatType: Track['audioBeatType'];
    hasStems: boolean;
    hasWav: boolean;
    hasMidi: boolean;
    isFree?: boolean;
    allowFreeDownload?: boolean;
    hasWatermark?: boolean;
    duration?: number; // Segundos detectados del archivo subido (opcional)
  }) => Track;
  updateTrack: (trackId: string, data: Partial<Track>) => void;
  deleteTrack: (trackId: string) => void;
  claimFreeTrack: (trackId: string) => boolean;
  downloadAuditionDemo: (track: Track) => void;
  getContractForPurchase: (purchase: PurchaseRecord) => LicenseContract;
  getContractForSale: (sale: SaleRecord) => LicenseContract;
  generateLicenseForTrack: (track: Track) => LicenseContract;
  addComment: (trackId: string, content: string) => void;
  deleteComment: (trackId: string, commentId: string) => void;
  switchUser: (userId: string) => void;
  login: (username: string, password?: string) => Promise<{ success: true } | { success: false; error: string }>;
  logout: () => Promise<{ success: true } | { success: false; error: string }>;
  registerUser: (username: string, email: string, artistName: string, role: UserType) => User;
  registerAccount: (form: FormData) => Promise<
    | { success: true; message: string }
    | { success: false; error: string; errors?: Record<string, string[]> }
  >;
  updateProfile: (data: Partial<User>) => void;
  subscribeToProducer: (sub: ProducerSubscription) => boolean;
  // ---- Integración backend (Sprint 1, modo hybrid) ----
  apiMode: ApiMode;            // modo efectivo; hybrid no cambia automáticamente a mock
  configuredMode: ApiMode;     // modo elegido por configuración, independiente del fallback
  backendStatus: 'idle' | 'checking' | 'online' | 'offline';
  backendError: { phase: 'session' | 'catalog' | 'cart'; type: 'network' | 'api'; status?: number; message: string } | null;
  isSyncing: boolean;          // hay una petición al backend en curso
  refreshFromBackend: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isHybrid = CONFIGURED_MODE === 'hybrid';
  // Load from localStorage or defaults
  const [users, setUsers] = useState<User[]>(() => {
    if (isHybrid) return [];
    const saved = localStorage.getItem('bc_users');
    return saved ? JSON.parse(saved) : INITIAL_USERS;
  });

  const [tracks, setTracks] = useState<Track[]>(() => {
    if (isHybrid) return [];
    const saved = localStorage.getItem('bc_tracks');
    if (!saved) return INITIAL_TRACKS;
    try {
      const parsed = JSON.parse(saved);
      // Ensure all tracks have resourceType and mood if from old cache
      return parsed.map((t: any) => ({
        ...t,
        resourceType: t.resourceType || 'instrumental',
        mood: t.mood || 'Oscuro',
        hasStems: t.hasStems !== undefined ? t.hasStems : true,
        hasWav: t.hasWav !== undefined ? t.hasWav : true,
        hasMidi: t.hasMidi !== undefined ? t.hasMidi : false,
      }));
    } catch {
      return INITIAL_TRACKS;
    }
  });

  const [cart, setCart] = useState<CartItem[]>(() => {
    if (isHybrid) return [];
    const saved = localStorage.getItem('bc_cart');
    return saved ? JSON.parse(saved) : [];
  });

  const [subscriptions] = useState<ProducerSubscription[]>(isHybrid ? [] : INITIAL_SUBSCRIPTIONS);

  const [sales, setSales] = useState<SaleRecord[]>(() => {
    if (isHybrid) return [];
    const saved = localStorage.getItem('bc_sales');
    return saved ? JSON.parse(saved) : INITIAL_SALES;
  });

  const [purchases, setPurchases] = useState<PurchaseRecord[]>(() => {
    if (isHybrid) return [];
    const saved = localStorage.getItem('bc_purchases');
    return saved ? JSON.parse(saved) : INITIAL_PURCHASES;
  });

  const [currentUserId, setCurrentUserId] = useState<string>(() => {
    if (CONFIGURED_MODE === 'hybrid') return '';
    const saved = localStorage.getItem('bc_current_user_id');
    return saved || 'user_art_1'; // Default as artist MC Flow
  });

  // Global search & Resource filter
  const [globalSearchQuery, setGlobalSearchQuery] = useState('');
  const [activeResourceFilter, setActiveResourceFilter] = useState<ResourceType | 'all'>('all');

  // Audio Player State
  const [activeTrack, setActiveTrack] = useState<Track | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(180);
  const [volume, setVolume] = useState<number>(0.8);

  const currentUser = users.find((u) => u.id === currentUserId) || null;

  // ==== Estado de integración con el backend Django (modo hybrid) ====
  const [apiMode, setApiMode] = useState<ApiMode>(CONFIGURED_MODE);
  const [backendStatus, setBackendStatus] = useState<'idle' | 'checking' | 'online' | 'offline'>(isHybrid ? 'checking' : 'idle');
  const [backendError, setBackendError] = useState<AppContextType['backendError']>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const syncCount = useRef(0);
  const refreshSequence = useRef(0);
  const cartIdentityGeneration = useRef(0);
  const cartOperationGeneration = useRef<Record<string, number>>({});
  const pendingCartAdds = useRef<Map<string, Promise<number | null>>>(new Map());
  const modeRef = React.useRef<ApiMode>(CONFIGURED_MODE);
  modeRef.current = apiMode;
  // Carrito real: mapa trackId UI -> ventaId de Django (DELETE /api/carrito/<venta_id>/)
  const cartVentaIds = React.useRef<Record<string, number>>({});

  /** Marca "syncing" alrededor de una llamada al backend. */
  const withSync = async <T,>(fn: () => Promise<T>): Promise<T> => {
    syncCount.current += 1;
    setIsSyncing(true);
    try {
      return await fn();
    } finally {
      syncCount.current -= 1;
      setIsSyncing(syncCount.current > 0);
    }
  };

  // Pendiente de confiabilidad: errores de likes (rollback sin aviso), agregar/quitar
  // del carrito, checkout, edición de pistas y comentarios aún no comparten una
  // señalización de mutación uniforme. Se conservan sus manejadores actuales en esta tarea.

  /** Carga en orden y publica las colecciones solo cuando sesión, catálogo y carrito son coherentes. */
  const loadFromBackend = async () => {
    const sequence = ++refreshSequence.current;
    let phase: 'session' | 'catalog' | 'cart' = 'session';
    try {
      const session = await DjangoApi.getSession();
      phase = 'catalog';
      const page = await DjangoApi.catalogo({ page: 1 });
      const comprados = new Set(page.tracks_comprados.map((n) => `dj-${n}`));
      const mapped = page.tracks.map((dt) =>
        mapTrack(dt, { isPurchased: comprados.has(`dj-${dt.id_track}`), isOwner: !!session && dt.usuario.username === session.username }),
      ) as TrackWithSrc[];

      const uiUser = session ? mapUser(session) : null;
      if (uiUser) {
        uiUser.purchasedTrackIds = Array.from(comprados);
      }

      // Anónimo = carrito vacío válido. Autenticado = carrito consultado obligatoriamente.
      phase = 'cart';
      const identityGeneration = cartIdentityGeneration.current;
      const cartRes = session ? await DjangoApi.carrito() : { items: [] };
      const byId = new Map(mapped.map((t) => [t.id, t]));
      const nextCartVentaIds: Record<string, number> = {};
      const items = cartRes.items
        .map((v) => {
          const t = byId.get(`dj-${v.track}`);
          if (t) nextCartVentaIds[t.id] = v.id;
          return t ? { track: t, addedAt: v.fecha } : null;
        })
        .filter((x): x is CartItem => x !== null);
      if (sequence !== refreshSequence.current || identityGeneration !== cartIdentityGeneration.current) return;
      cartVentaIds.current = nextCartVentaIds;
      setTracks(mapped);
      setUsers(uiUser ? [uiUser] : []);
      setCurrentUserId(uiUser?.id ?? '');
      if (uiUser) localStorage.setItem('bc_session_user_id', uiUser.id);
      else localStorage.removeItem('bc_session_user_id');
      setCart(items);
      setBackendError(null);
      setBackendStatus('online');
      audioEngine.setPlaybackMode('file');
    } catch (e) {
      if (sequence !== refreshSequence.current) return;
      const status = (e as Error & { status?: number }).status;
      const network = e instanceof TypeError && /fetch|network/i.test(e.message);
      setBackendError({ phase, type: network ? 'network' : 'api', ...(status ? { status } : {}), message: network ? 'No se pudo conectar con Django.' : 'Django rechazó o no pudo completar la solicitud.' });
      setBackendStatus('offline');
      throw e;
    }
  };

  // Bootstrap: intentamos conectar una vez al montar (solo si el modo configurado es hybrid)
  useEffect(() => {
    if (CONFIGURED_MODE === 'hybrid') {
      withSync(loadFromBackend).catch(() => {});
    } else {
      audioEngine.setPlaybackMode('synth');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Al pagar en Webpay, Django redirige de vuelta con ?pago=exito|fracaso|cancelado:
  // re-hidratamos para que HistorialCompra/Venta ya reflejen la compra autorizada.
  useEffect(() => {
    if (modeRef.current !== 'hybrid') return;
    const params = new URLSearchParams(window.location.search);
    const pago = params.get('pago');
    if (pago) {
      window.history.replaceState({}, '', `${window.location.pathname}${window.location.hash}`);
      withSync(loadFromBackend).catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshFromBackend = () => {
    setBackendStatus('checking');
    setBackendError(null);
    return withSync(loadFromBackend);
  };

  // Regla de seguridad central: una pista está protegida (preview amortiguada,
  // sin descarga de master) si tiene marca de agua y el usuario no la adquirió.
  const isTrackProtected = (track: Track | null): boolean => {
    if (!track) return false;
    const owned = currentUser?.purchasedTrackIds.includes(track.id) ?? false;
    if (owned) return false;
    if (track.isFree || track.price === 0) return false; // Beats gratis: demo libre sin protección
    return track.hasWatermark ?? true;
  };

  // Persist to localStorage
  useEffect(() => {
    if (isHybrid) return;
    localStorage.setItem('bc_users', JSON.stringify(users));
  }, [users]);

  useEffect(() => {
    if (isHybrid) return;
    localStorage.setItem('bc_tracks', JSON.stringify(tracks));
  }, [tracks]);

  useEffect(() => {
    if (isHybrid) return;
    localStorage.setItem('bc_cart', JSON.stringify(cart));
  }, [cart]);

  useEffect(() => {
    if (isHybrid) return;
    localStorage.setItem('bc_sales', JSON.stringify(sales));
  }, [sales]);

  useEffect(() => {
    if (isHybrid) return;
    localStorage.setItem('bc_purchases', JSON.stringify(purchases));
  }, [purchases]);

  useEffect(() => {
    if (isHybrid) {
      localStorage.removeItem('bc_current_user_id');
    } else {
      localStorage.setItem('bc_current_user_id', currentUserId);
    }
  }, [currentUserId]);

  // Audio Engine Hookup
  useEffect(() => {
    audioEngine.setCallbacks(
      (time, dur) => {
        setCurrentTime(time);
        setDuration(dur);
      },
      (playing) => {
        setIsPlaying(playing);
      }
    );
  }, []);

  const playTrack = (track: Track) => {
    // Seguridad de preescucha: amortiguar la preview si la pista no fue adquirida.
    audioEngine.setPreviewSecurityMode(isTrackProtected(track));

    // En modo real, el <audio> apunta al archivo auténtico de Django:
    // reproducir completo solo si es gratis/dueño/comprado (la guarda vive
    // server-side en /api/track/<id>/reproducir/); si no, suena el preview 30s.
    if (modeRef.current === 'hybrid') {
      const t = track as TrackWithSrc;
      const src = !isTrackProtected(track) && t.fullSrc ? t.fullSrc : t.previewSrc ?? t.fullSrc ?? null;
      audioEngine.setAudioSource(src);
    }

    if (activeTrack?.id === track.id) {
      if (isPlaying) {
        audioEngine.pause();
      } else {
        audioEngine.playTrack(track.id, track.audioBeatType, track.bpm, track.duration);
      }
    } else {
      setActiveTrack(track);
      audioEngine.playTrack(track.id, track.audioBeatType, track.bpm, track.duration);
    }
  };

  const togglePlay = () => {
    if (!activeTrack) {
      if (tracks.length > 0) {
        playTrack(tracks[0]);
      }
      return;
    }
    audioEngine.setPreviewSecurityMode(isTrackProtected(activeTrack));
    if (isPlaying) {
      audioEngine.pause();
    } else {
      audioEngine.playTrack(activeTrack.id, activeTrack.audioBeatType, activeTrack.bpm, activeTrack.duration);
    }
  };

  const seekAudio = (seconds: number) => {
    audioEngine.seek(seconds);
    setCurrentTime(seconds);
  };

  const setAudioVolume = (vol: number) => {
    setVolume(vol);
    audioEngine.setVolume(vol);
  };

  const toggleLike = (trackId: string) => {
    if (!currentUser) return;
    const isLiked = currentUser.likedTrackIds.includes(trackId);

    const updatedUserLiked = isLiked
      ? currentUser.likedTrackIds.filter((id) => id !== trackId)
      : [...currentUser.likedTrackIds, trackId];

    setUsers((prev) =>
      prev.map((u) => (u.id === currentUser.id ? { ...u, likedTrackIds: updatedUserLiked } : u))
    );

    setTracks((prev) =>
      prev.map((t) =>
        t.id === trackId
          ? { ...t, likesCount: isLiked ? Math.max(0, t.likesCount - 1) : t.likesCount + 1 }
          : t
      )
    );

    // Modo real: espejar en /api/like/<id>/ (optimista arriba, revert si falla)
    if (modeRef.current === 'hybrid' && trackId.startsWith('dj-')) {
      withSync(() => DjangoApi.toggleLike(djangoId(trackId)))
        .then((res) => {
          if (res.liked !== !isLiked) {
            // El servidor dice lo contrario: revertir UI
            toggleLikeServerRollback(trackId, isLiked);
          }
        })
        .catch(() => toggleLikeServerRollback(trackId, isLiked));
    }
  };

  const toggleLikeServerRollback = (trackId: string, wasLiked: boolean) => {
    setUsers((prev) =>
      prev.map((u) =>
        u.id === currentUser?.id
          ? {
              ...u,
              likedTrackIds: wasLiked
                ? [...new Set([...u.likedTrackIds, trackId])]
                : u.likedTrackIds.filter((id) => id !== trackId),
            }
          : u
      )
    );
    setTracks((prev) =>
      prev.map((t) => (t.id === trackId ? { ...t, likesCount: wasLiked ? t.likesCount + 1 : Math.max(0, t.likesCount - 1) } : t))
    );
  };

  const addToCart = (track: Track): boolean => {
    if (currentUser?.purchasedTrackIds.includes(track.id)) {
      return false; // Already owned
    }
    const alreadyInCart = cart.some((item) => item.track.id === track.id) || pendingCartAdds.current.has(track.id);
    if (alreadyInCart) {
      return false;
    }

    if (modeRef.current === 'hybrid' && track.id.startsWith('dj-')) {
      // Fuente de verdad: Venta server-side con IVA calculado por Django.
      const identityGeneration = cartIdentityGeneration.current;
      const operationGeneration = (cartOperationGeneration.current[track.id] || 0) + 1;
      cartOperationGeneration.current[track.id] = operationGeneration;
      const addPromise = withSync(() => DjangoApi.addToCart(djangoId(track.id)))
        .then((venta) => {
          if (identityGeneration !== cartIdentityGeneration.current || cartOperationGeneration.current[track.id] !== operationGeneration) return venta.id;
          cartVentaIds.current[track.id] = venta.id;
          setCart((prev) =>
            prev.some((i) => i.track.id === track.id) ? prev : [...prev, { track, addedAt: venta.fecha }]
          );
          return venta.id;
        })
        .catch((e) => {
          // 409 duplicado/recompra, 401 sin sesión: no agregamos nada.
          console.warn('[BeatsCloud] No se pudo agregar al carrito:', e);
          return null;
        }).finally(() => {
          if (pendingCartAdds.current.get(track.id) === addPromise) pendingCartAdds.current.delete(track.id);
        });
      pendingCartAdds.current.set(track.id, addPromise);
      return true;
    }

    setCart((prev) => [...prev, { track, addedAt: new Date().toISOString() }]);
    return true;
  };

  const removeFromCart = (trackId: string) => {
    const pendingAdd = pendingCartAdds.current.get(trackId);
    const ventaId = cartVentaIds.current[trackId];
    const item = cart.find((entry) => entry.track.id === trackId);
    const identityGeneration = cartIdentityGeneration.current;
    const operationGeneration = (cartOperationGeneration.current[trackId] || 0) + 1;
    cartOperationGeneration.current[trackId] = operationGeneration;
    setCart((prev) => prev.filter((item) => item.track.id !== trackId));
    delete cartVentaIds.current[trackId];
    if (modeRef.current === 'hybrid' && (ventaId != null || pendingAdd)) {
      const remove = async () => {
        const confirmedVentaId = ventaId ?? await pendingAdd;
        if (confirmedVentaId == null || identityGeneration !== cartIdentityGeneration.current || cartOperationGeneration.current[trackId] !== operationGeneration) return;
        await withSync(() => DjangoApi.removeFromCart(confirmedVentaId));
      };
      remove().catch((e) => {
        if (identityGeneration === cartIdentityGeneration.current && cartOperationGeneration.current[trackId] === operationGeneration) {
          if (item) setCart((prev) => prev.some((entry) => entry.track.id === trackId) ? prev : [...prev, item]);
          if (ventaId != null) cartVentaIds.current[trackId] = ventaId;
          else pendingAdd?.then((id) => {
            if (id != null && identityGeneration === cartIdentityGeneration.current && cartOperationGeneration.current[trackId] === operationGeneration) cartVentaIds.current[trackId] = id;
          });
        }
        console.warn('[BeatsCloud] No se pudo quitar del carrito (server):', e);
      });
    }
  };

  const clearCart = () => {
    if (CONFIGURED_MODE === 'hybrid') {
      // Cada fila requiere confirmación individual; Django no ofrece vaciado masivo.
      cart.forEach((item) => removeFromCart(item.track.id));
      return;
    }
    setCart([]);
    cartVentaIds.current = {};
  };

  const checkoutCart = async (): Promise<WebpayCheckoutResult> => {
    if (!currentUser || cart.length === 0) {
      return { status: 'error', message: 'Inicia sesión y agrega productos antes de continuar.' };
    }

    if (modeRef.current !== 'hybrid') {
      return {
        status: 'error',
        message: 'El pago Webpay requiere el modo hybrid conectado a Django.',
      };
    }

    return startWebpayCheckout(
      () => withSync(() => DjangoApi.initPago()),
      submitWebpayForm,
    );
  };

  const uploadTrack = (data: {
    title: string;
    resourceType: ResourceType;
    genre: MusicGenre;
    subgenre?: string;
    price: number;
    description: string;
    coverUrl?: string;
    bpm: number;
    scaleKey: string;
    mood: MoodType;
    audioBeatType: Track['audioBeatType'];
    hasStems: boolean;
    hasWav: boolean;
    hasMidi: boolean;
    isFree?: boolean;
    allowFreeDownload?: boolean;
    hasWatermark?: boolean;
    duration?: number; // Segundos. Si no se informa, se usa la maqueta por defecto (180s)
  }): Track => {
    const id = 'track_' + Date.now();
    const isFree = data.isFree ?? (data.price === 0);
    const newTrack: Track = {
      id,
      title: data.title,
      producerId: currentUser?.id || 'user_prod_1',
      producerName: currentUser?.artistName || currentUser?.username || 'Productor',
      producerUsername: currentUser?.username || 'productor',
      producerAvatar: currentUser?.avatarUrl || 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400&auto=format&fit=crop&q=80',
      resourceType: data.resourceType,
      genre: data.genre,
      subgenre: data.subgenre || '',
      price: isFree ? 0 : data.price,
      coverUrl: data.coverUrl || 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop&q=80',
      description: data.description,
      bpm: data.bpm || 130,
      scaleKey: data.scaleKey || 'C Minor',
      mood: data.mood || 'Oscuro',
      duration: data.duration && data.duration > 0 ? data.duration : 180,
      likesCount: 0,
      tags: [data.genre, data.resourceType, `${data.bpm} BPM`, data.mood, ...(isFree ? ['Free', 'Gratis'] : [])],
      audioBeatType: data.audioBeatType || 'trap',
      hasStems: data.hasStems,
      hasWav: data.hasWav,
      hasMidi: data.hasMidi,
      isFree,
      allowFreeDownload: data.allowFreeDownload ?? isFree,
      hasWatermark: data.hasWatermark ?? !isFree,
      comments: [],
      createdAt: new Date().toISOString().split('T')[0],
    };

    setTracks((prev) => [newTrack, ...prev]);
    return newTrack;
  };

  const claimFreeTrack = (trackId: string): boolean => {
    if (!currentUser) return false;
    const track = tracks.find((t) => t.id === trackId);
    if (!track) return false;
    if (currentUser.purchasedTrackIds.includes(trackId)) return true;

    const buyOrder = 'FREE-' + Math.floor(100000 + Math.random() * 900000);
    const today = new Date().toISOString().split('T')[0];

    const freeCode = 'LIC-FREE-' + Math.floor(100000 + Math.random() * 900000);
    const freeHash = 'SHA256:' + Math.random().toString(36).substring(2) + Math.random().toString(36).substring(2);

    const freePurchase: PurchaseRecord = {
      id: 'pur_free_' + Math.random().toString(36).substr(2, 9),
      userId: currentUser.id,
      trackId: track.id,
      trackTitle: track.title,
      producerName: track.producerName,
      amount: 0,
      buyOrder,
      date: today,
      licenseCode: freeCode,
      verificationHash: freeHash,
      licenseType: 'maqueta_ensayo',
    };

    setPurchases((prev) => [freePurchase, ...prev]);
    setUsers((prev) =>
      prev.map((u) =>
        u.id === currentUser.id
          ? { ...u, purchasedTrackIds: Array.from(new Set([...u.purchasedTrackIds, trackId])) }
          : u
      )
    );
    return true;
  };

  const updateTrack = (trackId: string, data: Partial<Track>) => {
    setTracks((prev) => prev.map((t) => (t.id === trackId ? { ...t, ...data } : t)));
    if (activeTrack?.id === trackId) {
      setActiveTrack((prev) => (prev ? { ...prev, ...data } : null));
    }
    // Modo real: PATCH /api/track/<id>/ — Django solo acepta nombre/precio/descripción.
    if (modeRef.current === 'hybrid' && trackId.startsWith('dj-')) {
      const body: Record<string, unknown> = {};
      if (data.title !== undefined) body.nombre_track = data.title;
      if (data.price !== undefined) body.precio = data.price;
      if (data.description !== undefined) body.descripcion = data.description;
      if (Object.keys(body).length > 0) {
        withSync(() => DjangoApi.updateTrack(djangoId(trackId), body as never)).catch((e) =>
          console.warn('[BeatsCloud] No se pudo actualizar el track en el servidor:', e),
        );
      }
    }
  };

  const deleteTrack = (trackId: string) => {
    // Modo real: POST /api/track/<id>/delete/ — el servidor responde 409 si ya tiene ventas.
    if (modeRef.current === 'hybrid' && trackId.startsWith('dj-')) {
      withSync(() => DjangoApi.deleteTrack(djangoId(trackId)))
        .then(() => {
          setTracks((prev) => prev.filter((t) => t.id !== trackId));
          if (activeTrack?.id === trackId) {
            audioEngine.pause();
            setActiveTrack(null);
          }
          setCart((prev) => prev.filter((item) => item.track.id !== trackId));
        })
        .catch((e) => alert((e as Error).message || 'No se pudo eliminar el track.'));
      return;
    }

    setTracks((prev) => prev.filter((t) => t.id !== trackId));
    if (activeTrack?.id === trackId) {
      audioEngine.pause();
      setActiveTrack(null);
    }
    setCart((prev) => prev.filter((item) => item.track.id !== trackId));
  };

  const addComment = (trackId: string, content: string) => {
    if (!currentUser || !content.trim()) return;
    const newComment = {
      id: 'comm_' + Date.now(),
      userId: currentUser.id,
      username: currentUser.username,
      userAvatar: currentUser.avatarUrl,
      content: content.trim(),
      createdAt: new Date().toISOString().split('T')[0],
    };

    setTracks((prev) =>
      prev.map((t) => (t.id === trackId ? { ...t, comments: [...t.comments, newComment] } : t))
    );

    if (activeTrack?.id === trackId) {
      setActiveTrack((prev) => (prev ? { ...prev, comments: [...prev.comments, newComment] } : null));
    }

    // Modo real: persistir en Comentario de Django y re-sincronizar los comentarios
    // del track para reflejar los que ya existían en el servidor.
    if (modeRef.current === 'hybrid' && trackId.startsWith('dj-')) {
      withSync(async () => {
        await DjangoApi.addComment(djangoId(trackId), content.trim());
        const list = await DjangoApi.comentarios(djangoId(trackId));
        const mapped = list.map((c) => ({
          id: `cm-${c.id}`,
          userId: String(c.usuario.id),
          username: c.usuario.username,
          userAvatar: `https://api.dicebear.com/7.x/shapes/svg?seed=${c.usuario.username}`,
          content: c.contenido,
          createdAt: c.fecha_creacion,
        }));
        setTracks((prev) => prev.map((t) => (t.id === trackId ? { ...t, comments: mapped } : t)));
        setActiveTrack((prev) => (prev && prev.id === trackId ? { ...prev, comments: mapped } : prev));
      }).catch((e) => console.warn('[BeatsCloud] No se pudo guardar el comentario:', e));
    }
  };

  const deleteComment = (trackId: string, commentId: string) => {
    setTracks((prev) =>
      prev.map((t) =>
        t.id === trackId ? { ...t, comments: t.comments.filter((c) => c.id !== commentId) } : t
      )
    );
    if (activeTrack?.id === trackId) {
      setActiveTrack((prev) =>
        prev ? { ...prev, comments: prev.comments.filter((c) => c.id !== commentId) } : null
      );
    }
  };

  const switchUser = (userId: string) => {
    // En modo real la sesión la manda Django: no se puede "saltar" de usuario.
    if (CONFIGURED_MODE === 'hybrid') return;
    setCurrentUserId(userId);
  };

  /**
   * Login: en modo hybrid usa la sesión de Django (POST /api/auth/login/ con CSRF).
   * Devuelve el mensaje de error del servidor ('' si ok, null = credenciales locales inválidas).
   */
  const login: AppContextType['login'] = async (username, password) => {
    if (CONFIGURED_MODE === 'hybrid') {
      if (!password) return { success: false, error: 'Ingresa tu contraseña.' };
      try {
        const dUser = await withSync(() => DjangoApi.login(username, password));
        const uiUser = mapUser(dUser);
        // La confirmación de Django cambia la identidad activa. Invalida cualquier
        // snapshot anterior antes de iniciar la rehidratación del nuevo usuario.
        refreshSequence.current += 1;
        cartIdentityGeneration.current += 1;
        cartVentaIds.current = {};
        cartOperationGeneration.current = {};
        pendingCartAdds.current.clear();
        setUsers([uiUser]);
        setTracks([]);
        setCart([]);
        setActiveTrack(null);
        setCurrentUserId(uiUser.id);
        localStorage.setItem('bc_session_user_id', uiUser.id);
        // La autenticación ya fue confirmada por Django. Un error al recargar
        // catálogo/carrito no debe presentarse como credenciales rechazadas.
        await withSync(loadFromBackend).catch(() => {});
        return { success: true };
      } catch (e) {
        return { success: false, error: (e as Error).message || 'No fue posible iniciar sesión.' };
      }
    }
    const user = users.find(
      (u) => u.username.toLowerCase() === username.toLowerCase() || u.email.toLowerCase() === username.toLowerCase()
    );
    if (user) {
      setCurrentUserId(user.id);
      return { success: true };
    }
    return { success: false, error: 'Usuario o correo no encontrado.' };
  };

  const logout: AppContextType['logout'] = async () => {
    if (CONFIGURED_MODE === 'hybrid') {
      try {
        await withSync(() => DjangoApi.logout());
      } catch (e) {
        return { success: false, error: (e as Error).message || 'No fue posible cerrar sesión.' };
      }
      // Django confirmó el logout: descarta snapshots de la identidad anterior y
      // evita que una carga pendiente vuelva a publicarlos.
      refreshSequence.current += 1;
      cartIdentityGeneration.current += 1;
      cartVentaIds.current = {};
      cartOperationGeneration.current = {};
      pendingCartAdds.current.clear();
      setCart([]);
      localStorage.removeItem('bc_cart');
    }
    if (CONFIGURED_MODE === 'hybrid') localStorage.removeItem('bc_current_user_id');
    localStorage.removeItem('bc_session_user_id');
    if (CONFIGURED_MODE === 'hybrid') setCurrentUserId('');
    else setCurrentUserId('');
    return { success: true };
  };

  const registerAccount: AppContextType['registerAccount'] = async (form) => {
    if (CONFIGURED_MODE !== 'hybrid') {
      return { success: false, error: 'El registro del backend no está disponible en modo mock.' };
    }

    try {
      const response = await withSync(() => DjangoApi.registro(form));
      return { success: true, message: response.detail };
    } catch (e) {
      const error = e as Error & { errors?: Record<string, string[]> };
      return {
        success: false,
        error: error.message || 'No fue posible completar el registro.',
        ...(error.errors ? { errors: error.errors } : {}),
      };
    }
  };

  const registerUser = (
    username: string,
    email: string,
    artistName: string,
    role: UserType
  ): User => {
    const newUser: User = {
      id: 'user_' + Date.now(),
      username: username.toLowerCase().replace(/\s+/g, '_'),
      artistName: artistName || username,
      email,
      role,
      bio: role === 'productor' ? 'Nuevo productor musical en BeatsCloud.' : 'Nuevo artista independiente en BeatsCloud.',
      avatarUrl:
        role === 'productor'
          ? 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400&auto=format&fit=crop&q=80'
          : 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&auto=format&fit=crop&q=80',
      bannerUrl: 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=1200&auto=format&fit=crop&q=80',
      purchasedTrackIds: [],
      likedTrackIds: [],
      subscriptions: [],
    };

    setUsers((prev) => [...prev, newUser]);
    if (CONFIGURED_MODE === 'mock') setCurrentUserId(newUser.id);
    return newUser;
  };

  const updateProfile = (data: Partial<User>) => {
    if (!currentUser) return;
    setUsers((prev) => prev.map((u) => (u.id === currentUser.id ? { ...u, ...data } : u)));
  };

  const subscribeToProducer = (sub: ProducerSubscription): boolean => {
    if (!currentUser) return false;
    const currentSubs = currentUser.subscriptions || [];
    if (currentSubs.includes(sub.id)) return false;

    setUsers((prev) =>
      prev.map((u) =>
        u.id === currentUser.id ? { ...u, subscriptions: [...(u.subscriptions || []), sub.id] } : u
      )
    );
    return true;
  };

  const downloadAuditionDemo = (track: Track) => {
    const textContent = `================================================================================
       BEATSCLOUD CHILE · LICENCIA DE COMPOSICIÓN Y ENSAYO (DEMO GRATIS)
================================================================================

Pista: "${track.title}"
Productor: ${track.producerName} (@${track.producerUsername})
Tempo: ${track.bpm} BPM | Escala: ${track.scaleKey}
Descargado por: ${currentUser?.artistName || currentUser?.username || 'Artista'}
Fecha de Descarga: ${new Date().toISOString().split('T')[0]}

CONDICIONES DEL PUNTO MEDIO (ENSAYO & COMPOSICIÓN VOCAL):
1. Esta maqueta MP3 está destinada exclusivamente para que puedas grabar tu voz,
   escribir tu letra y comprobar en tu DAW/estudio si tu flow y melodía encajan.
2. No está permitido subir esta grabación con propósitos comerciales a Spotify,
   Apple Music ni monetizar en YouTube sin la Licencia Comercial.
3. Una vez que tu tema esté compuesto y listo para ser masterizado, adquiere la
   Licencia Comercial en BeatsCloud para recibir:
   - El máster original en WAV 24-bit sin pérdida ni marcas.
   - Los Stems multitrack por pistas separadas (batería, bajo, sintetizadores).
   - El Certificado de Licencia Oficial con Código Único para inscripción en SCD
     y autorización ante distribuidoras (DistroKid, Altafonte).

BeatsCloud Chile SpA · Regularizando la música en Chile y Latinoamérica.
================================================================================`;

    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Maqueta_Ensayo_${track.title.replace(/[\s/]/g, '_')}_BeatsCloud.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getContractForPurchase = (purchase: PurchaseRecord): LicenseContract => {
    const track = tracks.find((t) => t.id === purchase.trackId);
    const buyerUser = users.find((u) => u.id === purchase.userId) || currentUser;
    const producerUser = users.find((u) => u.id === track?.producerId);

    const isFree = purchase.amount === 0;

    return {
      licenseCode: purchase.licenseCode || `LIC-${purchase.buyOrder}`,
      verificationHash:
        purchase.verificationHash ||
        'SHA256:7e9b2a1c0d4e8f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a',
      issueDate: purchase.date || '2026-03-12',
      trackId: purchase.trackId,
      trackTitle: purchase.trackTitle,
      trackGenre: track?.genre || 'Trap',
      trackBpm: track?.bpm || 135,
      trackKey: track?.scaleKey || 'A Menor',
      producerId: producerUser?.id || track?.producerId || 'user_prod_1',
      producerName: purchase.producerName || track?.producerName || 'Metro Santiago',
      producerUsername: producerUser?.username || track?.producerUsername || 'metrosantiago',
      producerRut: '18.421.902-3 (Verificado)',
      buyerId: buyerUser?.id || purchase.userId,
      buyerName: buyerUser?.artistName || buyerUser?.username || 'MC Flow Valparaíso',
      buyerUsername: buyerUser?.username || 'mcflow',
      buyerRut: '19.824.110-K (Verificado)',
      amountClp: purchase.amount,
      buyOrder: purchase.buyOrder,
      licenseType: isFree ? 'maqueta_ensayo' : 'comercial_wav_stems',
      musicRightsSplit: {
        producerPercent: 50,
        artistPercent: 50,
        scdRegistered: true,
      },
      distributionTerms: {
        streamsLimit: isFree ? 'Solo Maqueta No Comercial' : 'Ilimitado (Streaming comercial)',
        musicVideoMonetized: !isFree,
        radioBroadcasting: !isFree,
        livePerformancesForProfit: !isFree,
        contentIdProtected: true,
      },
    };
  };

  const getContractForSale = (sale: SaleRecord): LicenseContract => {
    const track = tracks.find((t) => t.id === sale.trackId);
    const buyerUser = users.find((u) => u.id === sale.buyerId);
    const producerUser = users.find((u) => u.id === track?.producerId) || currentUser;

    return {
      licenseCode: sale.licenseCode || `LIC-${sale.buyOrder}`,
      verificationHash:
        sale.verificationHash ||
        'SHA256:7e9b2a1c0d4e8f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a',
      issueDate: sale.date || '2026-03-12',
      trackId: sale.trackId,
      trackTitle: sale.trackTitle,
      trackGenre: track?.genre || 'Trap',
      trackBpm: track?.bpm || 135,
      trackKey: track?.scaleKey || 'A Menor',
      producerId: producerUser?.id || 'user_prod_1',
      producerName: producerUser?.artistName || producerUser?.username || 'Metro Santiago',
      producerUsername: producerUser?.username || 'metrosantiago',
      producerRut: '18.421.902-3 (Verificado)',
      buyerId: sale.buyerId,
      buyerName: sale.buyerName,
      buyerUsername: buyerUser?.username || 'mcflow',
      buyerRut: '19.824.110-K (Verificado)',
      amountClp: sale.amount,
      buyOrder: sale.buyOrder,
      licenseType: 'comercial_wav_stems',
      musicRightsSplit: {
        producerPercent: 50,
        artistPercent: 50,
        scdRegistered: true,
      },
      distributionTerms: {
        streamsLimit: 'Ilimitado (Streaming comercial)',
        musicVideoMonetized: true,
        radioBroadcasting: true,
        livePerformancesForProfit: true,
        contentIdProtected: true,
      },
    };
  };

  const generateLicenseForTrack = (track: Track): LicenseContract => {
    const buyer = currentUser || users[1];
    const buyOrder = 'BC-' + Math.floor(100000 + Math.random() * 900000);
    return {
      licenseCode: 'LIC-' + buyOrder,
      verificationHash: 'SHA256:' + Math.random().toString(36).substring(2) + Math.random().toString(36).substring(2),
      issueDate: new Date().toISOString().split('T')[0],
      trackId: track.id,
      trackTitle: track.title,
      trackGenre: track.genre,
      trackBpm: track.bpm,
      trackKey: track.scaleKey,
      producerId: track.producerId,
      producerName: track.producerName,
      producerUsername: track.producerUsername,
      producerRut: '18.421.902-3 (Verificado)',
      buyerId: buyer.id,
      buyerName: buyer.artistName || buyer.username,
      buyerUsername: buyer.username,
      buyerRut: '19.824.110-K (Verificado)',
      amountClp: track.price,
      buyOrder,
      licenseType: track.price === 0 ? 'maqueta_ensayo' : 'comercial_wav_stems',
      musicRightsSplit: {
        producerPercent: 50,
        artistPercent: 50,
        scdRegistered: true,
      },
      distributionTerms: {
        streamsLimit: track.price === 0 ? 'Solo Maqueta No Comercial' : 'Ilimitado (Streaming comercial)',
        musicVideoMonetized: track.price > 0,
        radioBroadcasting: track.price > 0,
        livePerformancesForProfit: track.price > 0,
        contentIdProtected: true,
      },
    };
  };

  return (
    <AppContext.Provider
      value={{
        currentUser,
        users,
        tracks,
        cart,
        subscriptions,
        sales,
        purchases,
        activeTrack,
        isPlaying,
        currentTime,
        duration,
        volume,
        globalSearchQuery,
        setGlobalSearchQuery,
        activeResourceFilter,
        setActiveResourceFilter,
        playTrack,
        togglePlay,
        seekAudio,
        setAudioVolume,
        toggleLike,
        addToCart,
        removeFromCart,
        clearCart,
        checkoutCart,
        uploadTrack,
        updateTrack,
        deleteTrack,
        claimFreeTrack,
        downloadAuditionDemo,
        getContractForPurchase,
        getContractForSale,
        generateLicenseForTrack,
        addComment,
        deleteComment,
        switchUser,
        login,
        logout,
        registerUser,
        registerAccount,
        updateProfile,
        subscribeToProducer,
        apiMode,
        configuredMode: CONFIGURED_MODE,
        backendStatus,
        backendError,
        isSyncing,
        refreshFromBackend,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
