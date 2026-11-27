import type { DSubscriptionPlanInput, DSubscriptionPlanDetails } from '../api/types';
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
import type { DAuthorizedAccount } from '../api/django.service';
import {
  mapComentario,
  mapCompraConfirmada,
  mapHistorialVenta,
  mapSubscription,
  mapTrack,
  mapUser,
  djangoId,
} from '../api/mappers';
import { startWebpayCheckout, submitWebpayForm } from '../api/webpayCheckout.mjs';
import type { WebpayCheckoutResult } from '../api/webpayCheckout.mjs';
import {
  readPaymentReturn,
  cleanPaymentReturnUrl,
  resolvePaymentReturn,
} from '../api/webpayReturn.mjs';
import type { WebpayReceipt } from '../api/webpayReturn.mjs';
import { dismissNotification, enqueueNotification } from '../utils/notificationQueue.mjs';

export type AppNotification = { id: number; kind: 'success' | 'error'; message: string };

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

import { resolveTrackPlayback } from '../utils/playbackDuration.mjs';

// Extensión interna del Track para URLs de audio real (la inyecta mappers.mapTrack)
type TrackWithSrc = Track & { previewSrc?: string; fullSrc?: string; downloadSrc?: string; playbackAuthorized?: boolean };

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
  getTrackPlaybackDuration: (track: Track) => number;
  togglePlay: () => void;
  closeAudioPlayer: () => void;
  seekAudio: (seconds: number) => void;
  setAudioVolume: (volume: number) => void;
  toggleLike: (trackId: string) => Promise<void>;
  pendingLikeTrackIds: string[];
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
    stemsFile?: File;
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
  authorizedAccounts: DAuthorizedAccount[];
  isSwitchingAccount: boolean;
  addAuthorizedAccount: (
    username: string,
    password: string,
  ) => Promise<{ success: true } | { success: false; error: string }>;
  changeAuthorizedAccount: (
    userId: number,
  ) => Promise<{ success: true } | { success: false; error: string }>;
  login: (username: string, password?: string) => Promise<{ success: true } | { success: false; error: string }>;
  logout: () => Promise<{ success: true } | { success: false; error: string }>;
  registerUser: (username: string, email: string, artistName: string, role: UserType) => User;
  registerAccount: (form: FormData) => Promise<
    | { success: true; message: string }
    | { success: false; error: string; errors?: Record<string, string[]> }
  >;
  updateProfile: (data: ProfileUpdate) => Promise<void>;
  subscribeToProducer: (sub: ProducerSubscription) => boolean;
  createSubscription: (
    title: string,
    price: number,
    details?: DSubscriptionPlanDetails,
  ) => Promise<void>;
  updateSubscription: (
    subscriptionId: string,
    data: Partial<DSubscriptionPlanInput>,
  ) => Promise<void>;
  purchaseSubscription: (subscription: ProducerSubscription) => Promise<WebpayCheckoutResult>;
  // ---- Integración backend (Sprint 1, modo hybrid) ----
  apiMode: ApiMode;            // modo efectivo; hybrid no cambia automáticamente a mock
  configuredMode: ApiMode;     // modo elegido por configuración, independiente del fallback
  backendStatus: 'idle' | 'checking' | 'online' | 'offline';
  backendError: { phase: 'session' | 'catalog' | 'cart'; type: 'network' | 'api'; status?: number; message: string } | null;
  isSyncing: boolean;          // hay una petición al backend en curso
  purchasesLoading: boolean;
  purchasesError: string | null;
  notifications: AppNotification[];
  dismissNotification: (id: number) => void;
  paymentNotice: string | null;
  paymentReturnReady: boolean;
  paymentReceipt: WebpayReceipt | null;
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
  const [pendingLikeTrackIds, setPendingLikeTrackIds] = useState<string[]>([]);
  const pendingLikeRequests = useRef(new Set<string>());
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const notificationId = useRef(0);
  const notify = (kind: AppNotification['kind'], message: string) => {
    const item: AppNotification = { id: ++notificationId.current, kind, message };
    setNotifications((queue) => enqueueNotification(queue, item));
    window.setTimeout(() => setNotifications((queue) => dismissNotification(queue, item.id)), 5000);
  };
  const dismissAppNotification = (id: number) => {
    setNotifications((queue) => dismissNotification(queue, id));
  };

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
  const [paymentReceipt, setPaymentReceipt] = useState<{
    receipt: WebpayReceipt;
    ownerId: string;
  } | null>(null);
  const [initialPaymentReturn] = useState(
    () => readPaymentReturn(window.location.href),
  );
  const paymentRun = useRef(0);

  const clearPaymentNotice = () => {
    paymentRun.current += 1;
    setPaymentNotice(null);
    setPaymentReturnReady(false);
    setPaymentReceipt(null);
  };
  const [authNotice, setAuthNotice] = useState<string | null>(null);

  const [authorizedAccounts, setAuthorizedAccounts] =
    useState<DAuthorizedAccount[]>([]);

  const [isSwitchingAccount, setIsSwitchingAccount] = useState(false);
  const switchingAccountRef = useRef(false);
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
    setAuthorizedAccounts([]);
    setCurrentUserId('');
    setUsers((prev) => prev.map((user) => ({
      ...user, email: '', likedTrackIds: [], purchasedTrackIds: [], subscriptions: [],
    })));
    setTracks((prev) => prev.map((track) => ({ ...track, isPurchased: false, isOwner: false })));
    setCart([]);
    setPurchases([]);
    setPurchasesLoading(false);
    setPurchasesError(null);
    pendingLikeRequests.current.clear();
    setPendingLikeTrackIds([]);
    setSales([]);
    setActiveTrack(null);
    audioEngine.pause();
    clearPaymentNotice();
    localStorage.removeItem('bc_session_user_id');
    localStorage.removeItem('bc_current_user_id');
    if (expired) setAuthNotice('Tu sesion termino. Inicia sesion nuevamente para continuar.');
  };
  const loadFromBackend = async () => {
    const sequence = ++refreshSequence.current;
    setPurchasesLoading(true);
    setPurchasesError(null);
    let purchaseRequestStarted = false;
    let purchasesSynced = false;
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
        ? DjangoApi.misComprasConfirmadas().then((rows) => {
            purchasesSynced = true;
            if (sequence === refreshSequence.current) {
              setPurchases(rows.map((purchase) => mapCompraConfirmada(purchase, String(session.id))));
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
        ? purchaseRows.map((purchase) => mapCompraConfirmada(purchase, String(session.id)))
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
      return {
        userId: session ? String(session.id) : null,
        purchasesSynced,
        orders: mappedPurchases.map((purchase) => purchase.buyOrder),
      };
    } catch (e) {
      if (sequence !== refreshSequence.current) return;
      if (!purchaseRequestStarted) {
        setPurchasesLoading(false);
        setPurchasesError('No se pudo cargar el historial de compras. Reintenta cuando el servicio esté disponible.');
      }
      const status = (e as Error & { status?: number }).status;
      const network = e instanceof TypeError && /fetch|network/i.test(e.message);
      setBackendError({ phase, type: network ? 'network' : 'api', ...(status ? { status } : {}), message: network ? 'No se pudo conectar con BeatsCloud.' : 'No se pudo completar la solicitud. Inténtalo nuevamente.' });
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
          if (session && String(session.id) !== expectedId) {
            // La cookie compartida ahora corresponde a otra cuenta.
            // Recargar elimina los datos privados de la identidad anterior.
            window.location.reload();
          } else {
            discardPrivateState(true);
          }
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
  // D7: bootstrap y retorno comparten una sola sincronizacion.
  // El resultado inicial se conserva durante la repeticion de efectos
  // de React StrictMode, incluso despues de limpiar la URL.
  useEffect(() => {
    if (CONFIGURED_MODE !== 'hybrid') {
      audioEngine.setPlaybackMode('synth');
      return;
    }

    const input = initialPaymentReturn;

    if (!input) {
      void withSync(loadFromBackend).catch(() => {});
      return;
    }

    const run = ++paymentRun.current;

    window.history.replaceState(
      window.history.state,
      '',
      cleanPaymentReturnUrl(window.location.href),
    );

    setPaymentReturnReady(false);
    setPaymentReceipt(null);
    setPaymentNotice(
      'Verificando el estado de tu operación Webpay...',
    );

    void resolvePaymentReturn(
      input,
      () => withSync(loadFromBackend),
      (order) => withSync(() => DjangoApi.webpayReceipt(order)),
    ).then((result) => {
      if (paymentRun.current !== run) return;

      if (
        result.ownerId &&
        authenticatedId.current !== result.ownerId
      ) {
        return;
      }

      setPaymentNotice(result.notice);
      setPaymentReturnReady(result.ready);
      setPaymentReceipt(
        result.receipt && result.ownerId
          ? { receipt: result.receipt, ownerId: result.ownerId }
          : null,
      );
    });

    return () => {
      paymentRun.current += 1;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshFromBackend = async () => {
    setBackendStatus('checking');
    setBackendError(null);
    await withSync(loadFromBackend);
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

  const resolvePlayback = (track: Track) =>
    resolveTrackPlayback(
      track as TrackWithSrc,
      modeRef.current,
      Boolean(currentUser?.purchasedTrackIds.includes(track.id))
    );

  const getTrackPlaybackDuration = (track: Track) =>
    resolvePlayback(track).duration;

  const playTrack = (track: Track) => {
    const playback = resolvePlayback(track);
    // En modo real, el <audio> apunta al archivo auténtico de Django:
    // reproducir completo solo si es gratis/dueño/comprado (la guarda vive
    // server-side en /api/track/<id>/reproducir/); si no, suena el preview 30s.
    if (modeRef.current === 'hybrid') {
      audioEngine.setAudioSource(playback.src);
    }

    if (activeTrack?.id === track.id) {
      if (isPlaying) {
        audioEngine.pause();
      } else {
        audioEngine.playTrack(track.id, track.audioBeatType, track.bpm, playback.duration);
      }
    } else {
      setActiveTrack(track);
      audioEngine.playTrack(track.id, track.audioBeatType, track.bpm, playback.duration);
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
      audioEngine.playTrack(activeTrack.id, activeTrack.audioBeatType, activeTrack.bpm, getTrackPlaybackDuration(activeTrack));
    }
  };

  const seekAudio = (seconds: number) => {
    audioEngine.seek(seconds);
  };

  const setAudioVolume = (vol: number) => {
    setVolume(vol);
    audioEngine.setVolume(vol);
  };

  const toggleLike = async (trackId: string) => {
    if (!currentUser) {
      notify('error', 'Inicia sesión como artista para guardar favoritos.');
      return;
    }
    if (modeRef.current !== 'hybrid' || !trackId.startsWith('dj-')) {
      notify('error', 'Los favoritos persistentes requieren conexión con BeatsCloud.');
      return;
    }
    if (pendingLikeRequests.current.has(trackId)) return;

    const actorId = currentUser.id;
    const isLiked = currentUser.likedTrackIds.includes(trackId);
    const desired = !isLiked;
    const applyState = (from: boolean, to: boolean) => {
      if (from === to || authenticatedId.current !== actorId) return;
      setUsers((prev) => prev.map((user) => {
        if (user.id !== actorId) return user;
        const hasLike = user.likedTrackIds.includes(trackId);
        if (hasLike === to) return user;
        return {
          ...user,
          likedTrackIds: to
            ? [...new Set([...user.likedTrackIds, trackId])]
            : user.likedTrackIds.filter((id) => id !== trackId),
        };
      }));
      setTracks((prev) => prev.map((track) => (
        track.id === trackId
          ? { ...track, likesCount: Math.max(0, track.likesCount + (to ? 1 : -1)) }
          : track
      )));
    };

    pendingLikeRequests.current.add(trackId);
    setPendingLikeTrackIds((ids) => ids.includes(trackId) ? ids : [...ids, trackId]);
    applyState(isLiked, desired);
    try {
      const response = await withSync(() => DjangoApi.setLike(djangoId(trackId), desired));
      if (response.liked !== desired) {
        applyState(desired, response.liked);
        notify('error', 'El estado del favorito cambió en otra sesión; se mostró el estado guardado.');
      } else {
        notify('success', desired ? 'Pista agregada a favoritos.' : 'Pista quitada de favoritos.');
      }
    } catch {
      applyState(desired, isLiked);
      notify('error', 'No se pudo guardar el favorito. Se recuperó el estado anterior.');
    } finally {
      pendingLikeRequests.current.delete(trackId);
      setPendingLikeTrackIds((ids) => ids.filter((id) => id !== trackId));
    }
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
          notify('success', `“${track.title}” se agregó al carrito.`);
          return venta.id;
        })
        .catch((e) => {
          // 409 duplicado/recompra, 401 sin sesión: no agregamos nada.
          console.warn('[BeatsCloud] No se pudo agregar al carrito:', e);
          notify('error', 'No se pudo agregar la pista al carrito. Revisa tu sesión e inténtalo de nuevo.');
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
        notify('success', 'La pista se quitó del carrito.');
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
        notify('error', 'No se pudo quitar la pista del carrito. Se restauró el carrito anterior.');
      });
    } else {
      notify('success', 'La pista se quitó del carrito.');
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
        message: 'El servicio de pagos no está disponible en este momento.',
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
      throw new Error('Selecciona un género musical válido.');
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
    stemsFile?: File;
  }): Promise<Track> => {
    if (modeRef.current === 'hybrid') {
      if (!data.audioFile) {
        throw new Error('Selecciona el archivo de audio que quieres guardar.');
      }

      const audio = data.audioFile;
      if (!audio) {
        throw new Error('Selecciona el archivo de audio que quieres guardar.');
      }

      const extension = audio.name.split('.').pop()?.toLowerCase() || '';
      const mimeByExtension: Record<string, string> = {
        mp3: 'audio/mpeg',
        wav: 'audio/wav',
        flac: 'audio/flac',
        m4a: 'audio/mp4',
        aac: 'audio/aac',
        ogg: 'audio/ogg',
      };
      const contentType =
        audio.type && audio.type !== 'application/octet-stream'
          ? audio.type
          : mimeByExtension[extension];

      if (!contentType) {
        throw new Error('No se pudo determinar el formato MIME del audio.');
      }

      const generoId = Number(getDjangoGenreId(data.genre));
      if (!Number.isInteger(generoId) || generoId <= 0) {
        throw new Error('No se pudo identificar el género musical seleccionado.');
      }

      // 1. Solicitar una URL firmada para subir el audio directamente a R2.
      const presigned = await withSync(() =>
        DjangoApi.r2Presign({
          kind: 'track',
          filename: audio.name,
          content_type: contentType,
          size: audio.size,
        })
      );

      // 2. Subir el archivo directamente a Cloudflare R2.
      const putResponse = await fetch(presigned.url, {
        method: presigned.method,
        headers: presigned.headers,
        body: audio,
      });

      if (!putResponse.ok) {
        const detail = await putResponse.text().catch(() => '');
        throw new Error(
          `Cloudflare R2 rechazo el archivo (${putResponse.status}). ${detail}`
        );
      }

      // 3. Confirmar en Django que R2 recibió el objeto esperado.
      const confirmation = await withSync(() =>
        DjangoApi.r2Confirm(presigned.upload_token)
      );

      if (
        !confirmation.verified ||
        confirmation.kind !== 'track' ||
        confirmation.size !== audio.size
      ) {
        throw new Error('R2 no pudo verificar la subida del audio.');
      }

      // 4. Subir la portada opcional directamente a Cloudflare R2.
      let coverUploadToken: string | undefined;

      if (data.coverFile) {
        const cover = data.coverFile;
        const coverExtension =
          cover.name.split('.').pop()?.toLowerCase() || '';

        const mimeByCoverExtension: Record<string, string> = {
          jpg: 'image/jpeg',
          jpeg: 'image/jpeg',
          png: 'image/png',
          webp: 'image/webp',
        };

        const expectedCoverContentType =
          mimeByCoverExtension[coverExtension];

        if (!expectedCoverContentType) {
          throw new Error('La portada debe ser JPG, JPEG, PNG o WEBP.');
        }

        const coverContentType =
          cover.type && cover.type !== 'application/octet-stream'
            ? cover.type
            : expectedCoverContentType;

        if (coverContentType !== expectedCoverContentType) {
          throw new Error('El formato de la portada no coincide con su extension.');
        }

        if (cover.size <= 0 || cover.size > 10 * 1024 * 1024) {
          throw new Error('La portada debe pesar como maximo 10 MB.');
        }

        const coverPresigned = await withSync(() =>
          DjangoApi.r2Presign({
            kind: 'cover',
            filename: cover.name,
            content_type: coverContentType,
            size: cover.size,
          })
        );

        const coverPutResponse = await fetch(coverPresigned.url, {
          method: coverPresigned.method,
          headers: coverPresigned.headers,
          body: cover,
        });

        if (!coverPutResponse.ok) {
          const detail = await coverPutResponse.text().catch(() => '');
          throw new Error(
            `Cloudflare R2 rechazo la portada (${coverPutResponse.status}). ${detail}`
          );
        }

        const coverConfirmation = await withSync(() =>
          DjangoApi.r2Confirm(coverPresigned.upload_token)
        );

        if (
          !coverConfirmation.verified ||
          coverConfirmation.kind !== 'cover' ||
          coverConfirmation.size !== cover.size ||
          coverConfirmation.content_type !== coverContentType
        ) {
          throw new Error('R2 no pudo verificar la subida de la portada.');
        }

        coverUploadToken = coverPresigned.upload_token;
      }

      // 5. Subir y confirmar el archivo STEMS opcional.
      let stemsUploadToken: string | undefined;
      if (data.hasStems) {
        const stems = data.stemsFile;
        if (!stems) {
          throw new Error('Selecciona el archivo STEMS o desmarca la opcion STEMS.');
        }
        const stemsExtension = stems.name.split('.').pop()?.toLowerCase() || '';
        const allowedStemsMimes: Record<string, string[]> = {
          zip: ['application/zip', 'application/x-zip-compressed'],
          wav: ['audio/wav', 'audio/x-wav', 'audio/wave'],
          flac: ['audio/flac', 'audio/x-flac'],
        };
        const allowedMimes = allowedStemsMimes[stemsExtension];
        if (!allowedMimes) throw new Error('STEMS debe ser ZIP, WAV o FLAC.');
        const stemsContentType =
          stems.type && stems.type !== 'application/octet-stream' ? stems.type : allowedMimes[0];
        if (!allowedMimes.includes(stemsContentType)) {
          throw new Error('El MIME del archivo STEMS no coincide con su extension.');
        }
        if (stems.size <= 0 || stems.size > 2 * 1024 * 1024 * 1024) {
          throw new Error('El archivo STEMS debe pesar como maximo 2 GB.');
        }
        const stemsPresigned = await withSync(() => DjangoApi.r2Presign({
          kind: 'stems', filename: stems.name,
          content_type: stemsContentType, size: stems.size,
        }));
        const stemsPutResponse = await fetch(stemsPresigned.url, {
          method: stemsPresigned.method,
          headers: stemsPresigned.headers,
          body: stems,
        });
        if (!stemsPutResponse.ok) {
          const detail = await stemsPutResponse.text().catch(() => '');
          throw new Error(`Cloudflare R2 rechazo STEMS (${stemsPutResponse.status}). ${detail}`);
        }
        const stemsConfirmation = await withSync(() =>
          DjangoApi.r2Confirm(stemsPresigned.upload_token)
        );
        if (
          !stemsConfirmation.verified || stemsConfirmation.kind !== 'stems' ||
          stemsConfirmation.size !== stems.size ||
          stemsConfirmation.content_type !== stemsContentType
        ) {
          throw new Error('R2 no pudo verificar la subida STEMS.');
        }
        stemsUploadToken = stemsPresigned.upload_token;
      }

      // 6. Registrar el Track con los tokens de portada y STEMS.
      const savedTrack = await withSync(() =>
        DjangoApi.r2Finalize({
          upload_token: presigned.upload_token,
          nombre_track: data.title,
          precio: data.isFree ? 0 : data.price,
          genero_id: generoId,
          descripcion: data.description,
          subgenre: data.subgenre ?? '',
          resource_type: data.resourceType,
          bpm: data.bpm,
          scale_key: data.scaleKey,
          mood: data.mood,
          has_stems: data.hasStems,
          has_wav: data.hasWav,
          has_midi: data.hasMidi,
          allow_free_download: data.allowFreeDownload ?? data.isFree ?? false,
          has_watermark: data.hasWatermark ?? true,
          duration: data.duration && data.duration > 0 ? data.duration : 30,
          ...(coverUploadToken
            ? { cover_upload_token: coverUploadToken }
            : {}),
          ...(stemsUploadToken
            ? { stems_upload_token: stemsUploadToken }
            : {}),
        })
      );

      const mappedTrack = mapTrack(savedTrack, { isOwner: true });
      setTracks((prev) => [
        mappedTrack,
        ...prev.filter((track) => track.id !== mappedTrack.id),
      ]);
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
    if (currentUser.purchasedTrackIds.includes(trackId)) return true;

    if (modeRef.current === 'hybrid' && trackId.startsWith('dj-')) {
      await withSync(() => DjangoApi.claimFreeTrack(djangoId(trackId)));
      await withSync(loadFromBackend);
      return true;
    }

    const track = tracks.find((t) => t.id === trackId);
    if (!track) return false;

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
      if (coverFile) {
        const coverExtension =
          coverFile.name.split('.').pop()?.toLowerCase() || '';
        const mimeByCoverExtension: Record<string, string> = {
          jpg: 'image/jpeg',
          jpeg: 'image/jpeg',
          png: 'image/png',
          webp: 'image/webp',
        };
        const expectedCoverContentType =
          mimeByCoverExtension[coverExtension];

        if (!expectedCoverContentType) {
          throw new Error('La portada debe ser JPG, JPEG, PNG o WEBP.');
        }

        const coverContentType =
          coverFile.type && coverFile.type !== 'application/octet-stream'
            ? coverFile.type
            : expectedCoverContentType;

        if (coverContentType !== expectedCoverContentType) {
          throw new Error('El formato de la portada no coincide con su extension.');
        }

        if (coverFile.size <= 0 || coverFile.size > 10 * 1024 * 1024) {
          throw new Error('La portada debe pesar como maximo 10 MB.');
        }

        const coverPresigned = await withSync(() =>
          DjangoApi.r2Presign({
            kind: 'cover',
            filename: coverFile.name,
            content_type: coverContentType,
            size: coverFile.size,
          })
        );

        const coverPutResponse = await fetch(coverPresigned.url, {
          method: coverPresigned.method,
          headers: coverPresigned.headers,
          body: coverFile,
        });

        if (!coverPutResponse.ok) {
          const detail = await coverPutResponse.text().catch(() => '');
          throw new Error(
            `Cloudflare R2 rechazo la portada (${coverPutResponse.status}). ${detail}`
          );
        }

        const coverConfirmation = await withSync(() =>
          DjangoApi.r2Confirm(coverPresigned.upload_token)
        );

        if (
          !coverConfirmation.verified ||
          coverConfirmation.kind !== 'cover' ||
          coverConfirmation.size !== coverFile.size ||
          coverConfirmation.content_type !== coverContentType
        ) {
          throw new Error('R2 no pudo verificar la subida de la portada.');
        }

        body.set('cover_upload_token', coverPresigned.upload_token);
      }

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


  // La lista de cuentas autorizadas siempre viene de Django.
  // Nunca se reconstruye desde localStorage.
  useEffect(() => {
    if (CONFIGURED_MODE !== 'hybrid') return;

    if (!currentUserId) {
      setAuthorizedAccounts([]);
      return;
    }

    let cancelled = false;
    const expectedId = authenticatedId.current;

    void DjangoApi.getAuthorizedAccounts()
      .then((result) => {
        if (
          !cancelled &&
          expectedId !== null &&
          authenticatedId.current === expectedId &&
          String(result.active_user_id) === expectedId
        ) {
          setAuthorizedAccounts(result.accounts);
        }
      })
      .catch(() => {
        if (!cancelled) setAuthorizedAccounts([]);
      });

    return () => {
      cancelled = true;
    };
  }, [currentUserId]);

  const addAuthorizedAccount: AppContextType['addAuthorizedAccount'] =
    async (username, password) => {
      if (CONFIGURED_MODE !== 'hybrid' || !authenticatedId.current) {
        return {
          success: false,
          error: 'Debes iniciar sesi?n para agregar otra cuenta.',
        };
      }

      const expectedId = authenticatedId.current;

      try {
        const result = await withSync(() =>
          DjangoApi.addAuthorizedAccount(username, password)
        );

        if (
          authenticatedId.current !== expectedId ||
          String(result.active_user_id) !== expectedId
        ) {
          setAuthorizedAccounts([]);
          return {
            success: false,
            error: 'La sesi?n cambi?. Recarga la p?gina para continuar.',
          };
        }

        setAuthorizedAccounts(result.accounts);

        return { success: true };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error
            ? error.message
            : 'No fue posible agregar esta cuenta.',
        };
      }
    };

  const changeAuthorizedAccount: AppContextType['changeAuthorizedAccount'] =
    async (userId) => {
      if (CONFIGURED_MODE !== 'hybrid' || !authenticatedId.current) {
        return {
          success: false,
          error: 'Debes iniciar sesi?n para cambiar de cuenta.',
        };
      }

      if (!Number.isSafeInteger(userId) || userId <= 0) {
        return {
          success: false,
          error: 'Selecciona una cuenta v?lida.',
        };
      }

      if (switchingAccountRef.current) {
        return {
          success: false,
          error: 'Ya hay un cambio de cuenta en proceso.',
        };
      }

      if (String(userId) === authenticatedId.current) {
        return { success: true };
      }

      switchingAccountRef.current = true;
      setIsSwitchingAccount(true);

      try {
        const result = await DjangoApi.switchAuthorizedAccount(userId);

        // Django ya cambi? la identidad. Aunque una respuesta inesperada
        // indique otra cuenta, recargar es lo m?s seguro para eliminar
        // completamente los estados privados de la sesi?n anterior.
        if (result.active_user_id !== userId) {
          window.location.reload();
          return {
            success: false,
            error: 'La sesi?n cambi? y necesita recargarse.',
          };
        }

        // Descarta toda la memoria React, peticiones pendientes, carrito,
        // compras, ventas, reproductor y cualquier dato de la cuenta anterior.
        // Django volver? a confirmar la sesi?n al iniciar la aplicaci?n.
        window.location.reload();

        return { success: true };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error
            ? error.message
            : 'No fue posible cambiar de cuenta.',
        };
      } finally {
        switchingAccountRef.current = false;
        setIsSwitchingAccount(false);
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
        clearPaymentNotice();
        const uiUser = mapUser(dUser);
        // La confirmación de Django cambia la identidad activa. Invalida cualquier
        // snapshot anterior antes de iniciar la rehidratación del nuevo usuario.
        refreshSequence.current += 1;
        cartIdentityGeneration.current += 1;
        cartVentaIds.current = {};
        cartOperationGeneration.current = {};
        pendingCartAdds.current.clear();
        setAuthorizedAccounts([]);
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
        clearPaymentNotice();
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
      setAuthorizedAccounts([]);
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

  const createSubscription = async (
    title: string,
    price: number,
    details: DSubscriptionPlanDetails = {},
  ) => {
    if (modeRef.current === 'hybrid') {
      const created = await withSync(() =>
        DjangoApi.crearSuscripcion(title, price, details)
      );
      setSubscriptions((prev) => [...prev, mapSubscription(created)]);
      return;
    }
  };

  const updateSubscription = async (
    subscriptionId: string,
    data: Partial<DSubscriptionPlanInput>,
  ) => {
    if (modeRef.current !== 'hybrid') {
      throw new Error('La edicion requiere conexion con BeatsCloud.');
    }

    const id = Number(subscriptionId.replace(/^sus-/, ''));

    if (!Number.isInteger(id) || id <= 0) {
      throw new Error('Plan no valido.');
    }

    const updated = await withSync(() =>
      DjangoApi.editarSuscripcion(id, data)
    );

    const plan = mapSubscription(updated);

    setSubscriptions((prev) =>
      prev.map((item) => item.id === plan.id ? plan : item)
    );
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
    throw new Error('Las descargas requieren conexión con BeatsCloud.');
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
        getTrackPlaybackDuration,
        togglePlay,
        closeAudioPlayer,
        seekAudio,
        setAudioVolume,
        toggleLike,
        pendingLikeTrackIds,
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
        authorizedAccounts,
        isSwitchingAccount,
        addAuthorizedAccount,
        changeAuthorizedAccount,
        login,
        logout,
        registerUser,
        registerAccount,
        updateProfile,
        subscribeToProducer,
        createSubscription,
        updateSubscription,
        purchaseSubscription,
        apiMode,
        configuredMode: CONFIGURED_MODE,
        backendStatus,
        backendError,
        isSyncing,
        purchasesLoading,
        purchasesError,
        notifications,
        dismissNotification: dismissAppNotification,
        paymentNotice,
        paymentReturnReady:
          paymentReturnReady &&
          !!paymentReceipt &&
          paymentReceipt.ownerId === currentUser?.id,
        paymentReceipt:
          paymentReceipt && paymentReceipt.ownerId === currentUser?.id
            ? paymentReceipt.receipt
            : null,
        authNotice,
        clearAuthNotice: () => setAuthNotice(null),
        clearPaymentNotice,
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
