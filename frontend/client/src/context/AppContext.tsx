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
import DjangoApi, { subscribeToSessionInvalidation } from '../api/django.service';
import {
  mapComentario,
  mapHistorialCompra,
  mapHistorialVenta,
  mapSubscription,
  mapTrack,
  mapUser,
  djangoId,
} from '../api/mappers';
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
  genres: string[];
  genreOptions: { id: number; descripcion: string }[];
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
  closeAudioPlayer: () => void;
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
    audioFile?: File;
    coverFile?: File;
  }) => Promise<Track>;
  updateTrack: (trackId: string, data: Partial<Track>, coverFile?: File) => Promise<void>;
  deleteTrack: (trackId: string) => void;
  claimFreeTrack: (trackId: string) => Promise<boolean>;
  downloadAuditionDemo: (track: Track) => Promise<void>;
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
  updateProfile: (data: ProfileUpdate) => Promise<void>;
  subscribeToProducer: (sub: ProducerSubscription) => boolean;
  createSubscription: (title: string, price: number) => Promise<void>;
  purchaseSubscription: (subscription: ProducerSubscription) => Promise<WebpayCheckoutResult>;
  // ---- Integración backend (Sprint 1, modo hybrid) ----
  apiMode: ApiMode;            // modo efectivo; hybrid no cambia automáticamente a mock
  configuredMode: ApiMode;     // modo elegido por configuración, independiente del fallback
  backendStatus: 'idle' | 'checking' | 'online' | 'offline';
  backendError: { phase: 'session' | 'catalog' | 'cart'; type: 'network' | 'api'; status?: number; message: string } | null;
  isSyncing: boolean;          // hay una petición al backend en curso
  purchasesLoading: boolean;
  purchasesError: string | null;
  paymentNotice: string | null;
  paymentReturnReady: boolean;
  authNotice: string | null;
  clearAuthNotice: () => void;
  clearPaymentNotice: () => void;
  refreshFromBackend: () => Promise<void>;
  refreshTrackComments: (trackId: string) => Promise<void>;
}

export interface ProfileUpdate {
  bio?: string;
  spotify?: string;
  youtube?: string;
  instagram?: string;
  avatarFile?: File;
  bannerFile?: File;
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

  const [genres, setGenres] = useState<string[]>([]);
  const [genreOptions, setGenreOptions] = useState<
    { id: number; descripcion: string }[]
  >([]);

  const [cart, setCart] = useState<CartItem[]>(() => {
    if (isHybrid) return [];
    const saved = localStorage.getItem('bc_cart');
    return saved ? JSON.parse(saved) : [];
  });

  const [subscriptions, setSubscriptions] = useState<ProducerSubscription[]>(isHybrid ? [] : INITIAL_SUBSCRIPTIONS);

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
  const [purchasesLoading, setPurchasesLoading] = useState(isHybrid);
  const [purchasesError, setPurchasesError] = useState<string | null>(null);

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
  const [paymentNotice, setPaymentNotice] = useState<string | null>(null);
  const [paymentReturnReady, setPaymentReturnReady] = useState(false);
  const [authNotice, setAuthNotice] = useState<string | null>(null);
  const authenticatedId = useRef<string | null>(null);
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
  // D3: descartar datos privados al perder la sesion; nunca borrar compras del servidor.
  const discardPrivateState = (expired: boolean, invalidateLoads = true) => {
    if (invalidateLoads) refreshSequence.current += 1;
    cartIdentityGeneration.current += 1;
    cartVentaIds.current = {};
    cartOperationGeneration.current = {};
    pendingCartAdds.current.clear();
    authenticatedId.current = null;
    setCurrentUserId('');
    setUsers((prev) => prev.map((user) => ({
      ...user, email: '', likedTrackIds: [], purchasedTrackIds: [], subscriptions: [],
    })));
    setTracks((prev) => prev.map((track) => ({ ...track, isPurchased: false, isOwner: false })));
    setCart([]);
    setPurchases([]);
    setPurchasesLoading(false);
    setPurchasesError(null);
    setSales([]);
    setActiveTrack(null);
    audioEngine.pause();
    setPaymentReturnReady(false);
    setPaymentNotice(null);
    localStorage.removeItem('bc_session_user_id');
    localStorage.removeItem('bc_current_user_id');
    if (expired) setAuthNotice('Tu sesion termino. Inicia sesion nuevamente para continuar.');
  };
  const loadFromBackend = async () => {
    const sequence = ++refreshSequence.current;
    setPurchasesLoading(true);
    setPurchasesError(null);
    let purchaseRequestStarted = false;
    let phase: 'session' | 'catalog' | 'cart' = 'session';
    try {
      const session = await DjangoApi.getSession();
      if (!session && authenticatedId.current) {
        // Django ya no reconoce la cookie: limpiar sin interrumpir el catalogo publico.
        discardPrivateState(true, false);
      }
      phase = 'catalog';
      const firstPage = await DjangoApi.catalogo({ page: 1 });
      const remainingPages = await Promise.all(
        Array.from({ length: Math.max(0, firstPage.total_paginas - 1) }, (_, index) =>
          DjangoApi.catalogo({ page: index + 2 }),
        ),
      );
      const catalogPages = [firstPage, ...remainingPages];
      const comprados = new Set(firstPage.tracks_comprados.map((n) => `dj-${n}`));
      const mapped = catalogPages.flatMap((page) =>
        page.tracks.map((dt) =>
          mapTrack(dt, {
            isPurchased: comprados.has(`dj-${dt.id_track}`),
            isOwner: !!session && dt.usuario.username === session.username,
          }),
        ),
      ) as TrackWithSrc[];

      const uiUser = session ? mapUser(session) : null;
      if (uiUser) {
        uiUser.purchasedTrackIds = Array.from(comprados);
      }

      phase = 'cart';
      const identityGeneration = cartIdentityGeneration.current;
      purchaseRequestStarted = !!session;
      const purchaseRowsPromise = session
        ? DjangoApi.misCompras().then((rows) => {
            if (sequence === refreshSequence.current) {
              setPurchases(rows.map((purchase) => mapHistorialCompra(purchase, String(session.id))));
              setPurchasesLoading(false);
            }
            return rows;
          }).catch((error: unknown) => {
            if (sequence === refreshSequence.current) {
              setPurchasesError(error instanceof Error ? error.message : 'No se pudo cargar el historial de compras.');
              setPurchasesLoading(false);
            }
            return [];
          })
        : Promise.resolve([]);
      const [publicUsers, subscriptionRows, cartRes, purchaseRows, saleRows] = await Promise.all([
        DjangoApi.usuarios(),
        DjangoApi.suscripciones(),
        session ? DjangoApi.carrito() : Promise.resolve({ items: [] }),
        purchaseRowsPromise,
        session ? DjangoApi.misVentas() : Promise.resolve([]),
      ]);
      const mappedPurchases = session
        ? purchaseRows.map((purchase) => mapHistorialCompra(purchase, String(session.id)))
        : [];
      const mappedSales = session ? saleRows.map(mapHistorialVenta) : [];
      const usersById = new Map(publicUsers.map((user) => {
        const mappedUser = mapUser(user);
        return [mappedUser.id, mappedUser] as const;
      }));
      if (uiUser) {
        uiUser.purchasedTrackIds = Array.from(new Set([
          ...uiUser.purchasedTrackIds,
          ...mappedPurchases.map((purchase) => purchase.trackId),
        ]));
        usersById.set(uiUser.id, uiUser);
      }
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
      const serverGenres = (firstPage.generos ?? [])
        .map((genre) => genre.descripcion?.trim())
        .filter((genre): genre is string => Boolean(genre));

      setGenres(Array.from(new Set(serverGenres)));
      setGenreOptions(
        (firstPage.generos ?? [])
          .filter((g) =>
            Number.isSafeInteger(g.id) &&
            g.id > 0 &&
            typeof g.descripcion === 'string' &&
            g.descripcion.trim().length > 0
          )
          .map((g) => ({
            id: g.id,
            descripcion: g.descripcion.trim(),
          }))
      );
      setTracks(mapped);
      setUsers(Array.from(usersById.values()));
      setCurrentUserId(uiUser?.id ?? '');
      authenticatedId.current = session ? String(session.id) : null;
      if (session) setAuthNotice(null);
      localStorage.removeItem('bc_session_user_id');
      setCart(items);
      setPurchases(mappedPurchases);
      setPurchasesLoading(false);
      setSales(mappedSales);
      setSubscriptions(subscriptionRows.map(mapSubscription));
      setBackendError(null);
      setBackendStatus('online');
      audioEngine.setPlaybackMode('file');
    } catch (e) {
      if (sequence !== refreshSequence.current) return;
      if (!purchaseRequestStarted) {
        setPurchasesLoading(false);
        setPurchasesError('No se pudo cargar el historial de compras. Reintenta cuando el servicio esté disponible.');
      }
      const status = (e as Error & { status?: number }).status;
      const network = e instanceof TypeError && /fetch|network/i.test(e.message);
      setBackendError({ phase, type: network ? 'network' : 'api', ...(status ? { status } : {}), message: network ? 'No se pudo conectar con Django.' : 'Django rechazó o no pudo completar la solicitud.' });
      setBackendStatus('offline');
      throw e;
    }
  };

  // 401 de endpoints privados y revalidacion ligera cuando vuelve el usuario.
  useEffect(() => {
    if (CONFIGURED_MODE !== 'hybrid') return;
    const unsubscribe = subscribeToSessionInvalidation(() => {
      if (authenticatedId.current) discardPrivateState(true);
    });
    let checking = false;
    const verifySession = async () => {
      const expectedId = authenticatedId.current;
      if (!expectedId || checking) return;
      checking = true;
      try {
        const session = await DjangoApi.getSession();
        if (authenticatedId.current === expectedId &&
            (!session || String(session.id) !== expectedId)) {
          discardPrivateState(true);
        }
      } catch {
        // Fallo de red no equivale a expiracion: no cerrar sesion sin confirmacion.
      } finally {
        checking = false;
      }
    };
    const onFocus = () => { void verifySession(); };
    const onVisible = () => {
      if (document.visibilityState === 'visible') void verifySession();
    };
    window.addEventListener('focus', onFocus);
    document.addEventListener('visibilitychange', onVisible);
    const intervalId = window.setInterval(() => { void verifySession(); }, 60000);
    return () => {
      unsubscribe();
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onVisible);
      window.clearInterval(intervalId);
    };
    // Las referencias y setState de React se mantienen estables.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  // Bootstrap: intentamos conectar una vez al montar (solo si el modo configurado es hybrid)
  useEffect(() => {
    if (CONFIGURED_MODE === 'hybrid') {
      withSync(loadFromBackend).catch(() => {});
    } else {
      audioEngine.setPlaybackMode('synth');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // El backend procesa el retorno de Webpay antes de redirigir al SPA.
  // React solo presenta el acceso a compras cuando termina su sincronizacion.
  useEffect(() => {
    if (modeRef.current !== 'hybrid') return;
    const url = new URL(window.location.href);
    const pago = url.searchParams.get('pago');
    if (!pago) return;

    // Quitar solo el dato transitorio de pago; preservar enlaces del SPA.
    url.searchParams.delete('pago');
    window.history.replaceState(
      window.history.state,
      '',
      `${url.pathname}${url.search}${url.hash}`
    );
    setPaymentReturnReady(false);

    if (pago === 'exito') {
      setPaymentNotice('Webpay regresó con resultado exitoso. Actualizando tu cuenta con Django...');
      void withSync(loadFromBackend)
        .then(() => {
          setPaymentNotice(
            'Webpay informó una operación exitosa. Django actualizó tu cuenta; revisa tus compras registradas.'
          );
          setPaymentReturnReady(true);
        })
        .catch(() => {
          setPaymentNotice(
            'No pudimos actualizar las compras desde Django. Verifica el estado de tu compra antes de intentar pagar otra vez.'
          );
          setPaymentReturnReady(false);
        });
      return;
    }

    setPaymentNotice(
      pago === 'cancelado'
        ? 'El pago fue cancelado; no se registró ningún cobro.'
        : pago === 'revision'
        ? 'Pago en revisión: no vuelvas a pagar; contacta a soporte.'
        : 'El pago no fue aprobado. Revisa el estado de tu cuenta antes de volver a intentarlo.'
    );
    void withSync(loadFromBackend).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const refreshFromBackend = () => {
    setBackendStatus('checking');
    setBackendError(null);
    return withSync(loadFromBackend);
  };

  const refreshTrackComments = async (trackId: string) => {
    if (modeRef.current !== 'hybrid' || !trackId.startsWith('dj-')) return;
    const comments = await withSync(() => DjangoApi.comentarios(djangoId(trackId)));
    const mappedComments = comments.map(mapComentario);
    setTracks((prev) => prev.map((track) =>
      track.id === trackId ? { ...track, comments: mappedComments } : track,
    ));
    setActiveTrack((prev) =>
      prev?.id === trackId ? { ...prev, comments: mappedComments } : prev,
    );
  };

  // Determina qué URL de audio solicitar; la autorización del archivo completo
  // sigue validándose en el backend.
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

  const closeAudioPlayer = () => {
    audioEngine.stop();
    setActiveTrack(null);
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
  };

  const togglePlay = () => {
    if (!activeTrack) {
      if (tracks.length > 0) {
        playTrack(tracks[0]);
      }
      return;
    }
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

  const getDjangoGenreId = (name: string): string => {
    const selected = genreOptions.find(
      (item) => item.descripcion === name
    );

    if (!selected || !Number.isSafeInteger(selected.id) || selected.id <= 0) {
      throw new Error('Selecciona un genero valido de Django.');
    }

    return String(selected.id);
  };

  const uploadTrack = async (data: {
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
    audioFile?: File;
    coverFile?: File;
  }): Promise<Track> => {
    if (modeRef.current === 'hybrid') {
      if (!data.audioFile) {
        throw new Error('Selecciona el archivo de audio que quieres guardar.');
      }

      const form = new FormData();
      form.set('nombre_track', data.title);
      form.set('precio', String(data.isFree ? 0 : data.price));
      form.set('descripcion', data.description);
      form.set('genero', getDjangoGenreId(data.genre));
      form.set('subgenre', data.subgenre ?? '');
      form.set('track', data.audioFile);
      form.set('resource_type', data.resourceType);
      form.set('bpm', String(data.bpm));
      form.set('scale_key', data.scaleKey);
      form.set('mood', data.mood);
      form.set('has_stems', String(data.hasStems));
      form.set('has_wav', String(data.hasWav));
      form.set('has_midi', String(data.hasMidi));
      form.set('allow_free_download', String(data.allowFreeDownload ?? data.isFree ?? false));
      form.set('has_watermark', String(data.hasWatermark ?? true));
      if (data.duration) form.set('duration', String(data.duration));
      if (data.coverFile) form.set('foto', data.coverFile);

      const savedTrack = await withSync(() => DjangoApi.upload(form));
      const mappedTrack = mapTrack(savedTrack, { isOwner: true });
      setTracks((prev) => [mappedTrack, ...prev.filter((track) => track.id !== mappedTrack.id)]);
      return mappedTrack;
    }

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

  const claimFreeTrack = async (trackId: string): Promise<boolean> => {
    if (!currentUser) return false;
    const track = tracks.find((t) => t.id === trackId);
    if (!track) return false;
    if (currentUser.purchasedTrackIds.includes(trackId)) return true;

    if (modeRef.current === 'hybrid' && trackId.startsWith('dj-')) {
      await withSync(() => DjangoApi.claimFreeTrack(djangoId(trackId)));
      await withSync(loadFromBackend);
      return true;
    }

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

  const updateTrack = async (trackId: string, data: Partial<Track>, coverFile?: File) => {
    if (modeRef.current === 'hybrid' && trackId.startsWith('dj-')) {
      const body = new FormData();
      const fields: Array<[keyof Track, string]> = [
        ['title', 'nombre_track'], ['price', 'precio'], ['description', 'descripcion'],
        ['subgenre', 'subgenre'],
        ['resourceType', 'resource_type'], ['bpm', 'bpm'], ['scaleKey', 'scale_key'],
        ['mood', 'mood'], ['hasStems', 'has_stems'], ['hasWav', 'has_wav'],
        ['hasMidi', 'has_midi'], ['allowFreeDownload', 'allow_free_download'],
        ['hasWatermark', 'has_watermark'], ['duration', 'duration'],
      ];
      fields.forEach(([key, field]) => {
        const value = data[key];
        if (value !== undefined) body.set(field, String(value));
      });
      if (data.genre !== undefined) {
        body.set('genero', getDjangoGenreId(data.genre));
      }
      if (coverFile) body.set('foto', coverFile);
      const saved = await withSync(() => DjangoApi.updateTrack(djangoId(trackId), body));
      const updated = mapTrack(saved, { isOwner: true });
      setTracks((prev) => prev.map((track) => track.id === trackId ? updated : track));
      if (activeTrack?.id === trackId) setActiveTrack(updated);
      return;
    }

    setTracks((prev) => prev.map((t) => (t.id === trackId ? { ...t, ...data } : t)));
    if (activeTrack?.id === trackId) setActiveTrack((prev) => (prev ? { ...prev, ...data } : null));
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

    if (modeRef.current === 'hybrid' && trackId.startsWith('dj-')) {
      withSync(async () => {
        await DjangoApi.addComment(djangoId(trackId), content.trim());
        await refreshTrackComments(trackId);
      }).catch((e) => console.warn('[BeatsCloud] No se pudo guardar el comentario:', e));
      return;
    }

    setTracks((prev) =>
      prev.map((t) => (t.id === trackId ? { ...t, comments: [...t.comments, newComment] } : t))
    );

    if (activeTrack?.id === trackId) {
      setActiveTrack((prev) => (prev ? { ...prev, comments: [...prev.comments, newComment] } : null));
    }

  };

  const deleteComment = (trackId: string, commentId: string) => {
    if (modeRef.current === 'hybrid' && trackId.startsWith('dj-')) {
      const commentPk = Number(commentId.replace(/^cm-/, ''));
      if (!Number.isInteger(commentPk) || commentPk <= 0) {
        console.warn('[BeatsCloud] No se pudo eliminar el comentario: identificador inválido.');
        return;
      }
      withSync(async () => {
        await DjangoApi.deleteComment(djangoId(trackId), commentPk);
        await refreshTrackComments(trackId);
      }).catch((e) => console.warn('[BeatsCloud] No se pudo eliminar el comentario:', e));
      return;
    }

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
        authenticatedId.current = String(dUser.id);
        setAuthNotice(null);
        localStorage.removeItem('bc_session_user_id');
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
        authenticatedId.current = null;
        setAuthNotice(null);
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
      setPurchases([]);
      setPurchasesLoading(false);
      setPurchasesError(null);
      setSales([]);
      setUsers((prev) => prev.map((user) =>
        user.id === currentUserId
          ? { ...user, email: '', likedTrackIds: [], purchasedTrackIds: [], subscriptions: [] }
          : user,
      ));
      await withSync(loadFromBackend).catch(() => {});
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

  const updateProfile = async (data: ProfileUpdate) => {
    if (!currentUser) return;
    if (modeRef.current === 'hybrid') {
      const form = new FormData();
      if (data.bio !== undefined) form.set('descripcion', data.bio);
      if (data.spotify !== undefined) form.set('spotify', data.spotify);
      if (data.youtube !== undefined) form.set('youtube', data.youtube);
      if (data.instagram !== undefined) form.set('instagram', data.instagram);
      if (data.avatarFile) form.set('foto_perfil', data.avatarFile);
      if (data.bannerFile) form.set('foto_fondo', data.bannerFile);
      const savedUser = await withSync(() => DjangoApi.updateProfile(form));
      const updatedUser = mapUser(savedUser);
      setUsers((prev) => prev.map((user) =>
        user.id === updatedUser.id
          ? { ...user, ...updatedUser, purchasedTrackIds: user.purchasedTrackIds }
          : user,
      ));
      return;
    }
    setUsers((prev) => prev.map((user) => user.id === currentUser.id
      ? {
          ...user,
          bio: data.bio ?? user.bio,
          spotify: data.spotify ?? user.spotify,
          youtube: data.youtube ?? user.youtube,
          instagram: data.instagram ?? user.instagram,
          ...(data.avatarFile ? { avatarUrl: URL.createObjectURL(data.avatarFile) } : {}),
          ...(data.bannerFile ? { bannerUrl: URL.createObjectURL(data.bannerFile) } : {}),
        }
      : user,
    ));
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

  const createSubscription = async (title: string, price: number) => {
    if (modeRef.current === 'hybrid') {
      const created = await withSync(() => DjangoApi.crearSuscripcion(title, price));
      setSubscriptions((prev) => [...prev, mapSubscription(created)]);
      return;
    }
  };

  const purchaseSubscription = (subscription: ProducerSubscription) =>
    startWebpayCheckout(
      () => withSync(() => DjangoApi.initPago(Number(subscription.id.replace(/^sus-/, '')))),
      submitWebpayForm,
    );

  const downloadAuditionDemo = async (track: Track) => {
    if (modeRef.current === 'hybrid' && track.id.startsWith('dj-')) {
      await DjangoApi.downloadPreview(djangoId(track.id), track.title.replace(/[\s/]/g, '_'));
      return;
    }
    throw new Error('Las descargas de audio requieren el backend Django conectado.');
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
        genres,
        genreOptions,
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
        closeAudioPlayer,
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
        createSubscription,
        purchaseSubscription,
        apiMode,
        configuredMode: CONFIGURED_MODE,
        backendStatus,
        backendError,
        isSyncing,
        purchasesLoading,
        purchasesError,
        paymentNotice,
        paymentReturnReady,
        authNotice,
        clearAuthNotice: () => setAuthNotice(null),
        clearPaymentNotice: () => setPaymentNotice(null),
        refreshFromBackend,
        refreshTrackComments,
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
