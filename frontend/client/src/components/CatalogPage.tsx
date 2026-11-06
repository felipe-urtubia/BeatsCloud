import React, { useState, useMemo, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { MusicGenre, ResourceType, MoodType, Track } from '../types';
import { getResourceBadgeInfo, RESOURCE_TYPES } from '../utils/resourceHelpers';
import DjangoApi from '../api/django.service';
import {
  Search,
  SlidersHorizontal,
  Play,
  Pause,
  ShoppingCart,
  Heart,
  MessageSquare,
  Layers,
  LayoutGrid,
  List,
  Filter,
  Check,
  Disc3,
  Flame,
  ArrowUpDown,
  Music,
  Download,
  Mic2,
  ShieldCheck,
  Lock,
} from 'lucide-react';

interface CatalogPageProps {
  onOpenTrackDetail: (trackId: string) => void;
  onOpenProducerProfile: (producerId: string) => void;
}


const SCALES = [
  'Todas',
  'A Minor',
  'C Minor',
  'D Minor',
  'E Minor',
  'F Minor',
  'G Minor',
  'F# Minor',
  'G Major',
  'C Major',
  'F Major',
];

export const CatalogPage: React.FC<CatalogPageProps> = ({
  onOpenTrackDetail,
  onOpenProducerProfile,
}) => {
  const {
    tracks,
    genres,
    playTrack,
    activeTrack,
    isPlaying,
    addToCart,
    toggleLike,
    claimFreeTrack,
    downloadAuditionDemo,
    currentUser,
    configuredMode,
    globalSearchQuery,
    setGlobalSearchQuery,
    activeResourceFilter,
    setActiveResourceFilter,
  } = useApp();

  const [selectedGenre, setSelectedGenre] = useState<'Todos' | MusicGenre>('Todos');
  const [selectedKey, setSelectedKey] = useState<string>('Todas');
  const [selectedMood, setSelectedMood] = useState<string>('Todos');
  const [minBpm, setMinBpm] = useState<number>(60);
  const [maxBpm, setMaxBpm] = useState<number>(180);
  const [onlyWithStems, setOnlyWithStems] = useState<boolean>(false);
  const [priceFilter, setPriceFilter] = useState<
    'all' | 'paid' | 'free' |
    '0_5000' | '5001_10000' |
    '10001_20000' | '20001_plus'
  >('all');
  const [sortBy, setSortBy] = useState<
    'recientes' | 'antiguos' |
    'bpm_asc' | 'bpm_desc' |
    'likes' | 'precio_menor' | 'precio_mayor' |
    'nombre_asc' | 'nombre_desc'
  >('recientes');
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(12);

  const availableGenres = useMemo(() => {
    const names = [...genres, ...tracks.map((track) => track.genre)]
      .map((genre) => genre.trim())
      .filter((genre) => genre.length > 0 && genre !== 'Todos');

    return [
      'Todos',
      ...Array.from(new Set(names)).sort((a, b) =>
        a.localeCompare(b, 'es', { sensitivity: 'base' })
      ),
    ];
  }, [genres, tracks]);

  const handleDownloadFree = async (e: React.MouseEvent, track: Track) => {
    e.stopPropagation();
    if (configuredMode !== 'hybrid' || !track.id.startsWith('dj-')) {
      window.alert('Las descargas de audio requieren el backend Django conectado.');
      return;
    }
    try {
      const claimed = await claimFreeTrack(track.id);
      if (!claimed) throw new Error('Inicia sesión para reclamar esta pista gratuita.');
      await DjangoApi.downloadTrack(Number(track.id.slice(3)), track.title);
    } catch (error) {
      window.alert((error as Error).message);
    }
  };

  // "Punto Medio": descarga de maqueta de composición (MP3 acuñado) en beats de pago
  // habilitados por el productor con allowFreeDownload.
  const handleDownloadAudition = (e: React.MouseEvent, track: Track) => {
    e.stopPropagation();
    void downloadAuditionDemo(track).catch((error) => window.alert((error as Error).message));
  };

  const filteredTracks = useMemo(() => {
    return tracks
      .filter((track) => {
        // Resource Type
        if (activeResourceFilter !== 'all' && track.resourceType !== activeResourceFilter) {
          return false;
        }

        // Search
        const q = globalSearchQuery.toLowerCase().trim();
        if (q) {
          const matchTitle = track.title.toLowerCase().includes(q);
          const matchProd = track.producerName.toLowerCase().includes(q);
          const matchGenre = track.genre.toLowerCase().includes(q);
          const matchKey = track.scaleKey.toLowerCase().includes(q);
          const matchBpm = track.bpm.toString().includes(q);
          const matchTags = track.tags.some((t) => t.toLowerCase().includes(q));
          if (!matchTitle && !matchProd && !matchGenre && !matchKey && !matchBpm && !matchTags) {
            return false;
          }
        }

        // Genre
        if (selectedGenre !== 'Todos' && track.genre !== selectedGenre) {
          return false;
        }

        // Key
        if (selectedKey !== 'Todas' && track.scaleKey !== selectedKey) {
          return false;
        }

        // Mood
        if (selectedMood !== 'Todos' && track.mood !== selectedMood) {
          return false;
        }

        // BPM range
        if (track.bpm < minBpm || track.bpm > maxBpm) {
          return false;
        }

        // Stems filter
        if (onlyWithStems && !track.hasStems) {
          return false;
        }

        // Price mode filter (Gratis vs Pago)
        if (priceFilter === 'free' && !track.isFree && track.price > 0) {
          return false;
        }
        if (priceFilter === 'paid' && (track.isFree || track.price === 0)) {
          return false;
        }

        // Rangos de precio en pesos chilenos.
        const price = track.isFree ? 0 : track.price;

        if (priceFilter === '0_5000' && (!Number.isFinite(price) || price < 0 || price > 5000)) return false;
        if (priceFilter === '5001_10000' && (!Number.isFinite(price) || price <= 5000 || price > 10000)) return false;
        if (priceFilter === '10001_20000' && (!Number.isFinite(price) || price <= 10000 || price > 20000)) return false;
        if (priceFilter === '20001_plus' && (!Number.isFinite(price) || price <= 20000)) return false;

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'bpm_asc') return a.bpm - b.bpm;
        if (sortBy === 'bpm_desc') return b.bpm - a.bpm;
        if (sortBy === 'likes') return b.likesCount - a.likesCount;
        if (sortBy === 'precio_menor') return a.price - b.price;
        if (sortBy === 'precio_mayor') return b.price - a.price;

        if (sortBy === 'nombre_asc') {
          return a.title.localeCompare(b.title, 'es', {
            sensitivity: 'base',
            numeric: true,
          });
        }

        if (sortBy === 'nombre_desc') {
          return b.title.localeCompare(a.title, 'es', {
            sensitivity: 'base',
            numeric: true,
          });
        }

        if (sortBy === 'antiguos') {
          return new Date(a.createdAt).getTime() -
            new Date(b.createdAt).getTime();
        }

        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      });
  }, [
    tracks,
    activeResourceFilter,
    globalSearchQuery,
    selectedGenre,
    selectedKey,
    selectedMood,
    minBpm,
    maxBpm,
    onlyWithStems,
    priceFilter,
    sortBy,
  ]);

  useEffect(() => {
    setCurrentPage(1);
  }, [
    activeResourceFilter,
    globalSearchQuery,
    selectedGenre,
    selectedKey,
    selectedMood,
    minBpm,
    maxBpm,
    onlyWithStems,
    priceFilter,
    sortBy,
    pageSize,
  ]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredTracks.length / pageSize)
  );

  const safePage = Math.min(currentPage, totalPages);
  const startIndex = (safePage - 1) * pageSize;

  const pagedTracks = filteredTracks.slice(
    startIndex,
    startIndex + pageSize
  );

  return (
    <div className="py-5 pb-36 max-w-7xl mx-auto space-y-5">
      {/* Top Filter Bar: Content Type Pill Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#0d0f17] border border-[#1b2030] p-3 rounded-2xl shadow-sm">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          <button
            onClick={() => setActiveResourceFilter('all')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeResourceFilter === 'all'
                ? 'bg-amber-400 text-zinc-950 font-black shadow-sm'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
            }`}
          >
            <span>Todos los Recursos</span>
            <span className="text-[10px] opacity-80 font-mono">({tracks.length})</span>
          </button>

          {RESOURCE_TYPES.map((t) => {
            const isSelected = activeResourceFilter === t.id;
            const info = getResourceBadgeInfo(t.id);
            const count = tracks.filter((tr) => tr.resourceType === t.id).length;

            return (
              <button
                key={t.id}
                onClick={() => setActiveResourceFilter(t.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 whitespace-nowrap ${
                  isSelected
                    ? `${info.badgeClass} ring-1 ring-amber-400 font-bold`
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${info.dotColor}`} />
                <span>{t.label}</span>
                <span className="text-[10px] opacity-75 font-mono">({count})</span>
              </button>
            );
          })}
        </div>

        {/* View mode toggle (Table vs Grid) */}
        <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-800 p-1 rounded-xl">
          <button
            onClick={() => setViewMode('table')}
            className={`p-1.5 rounded-lg text-xs transition-colors ${
              viewMode === 'table' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-400 hover:text-white'
            }`}
            title="Vista de lista / DAW"
          >
            <List className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`p-1.5 rounded-lg text-xs transition-colors ${
              viewMode === 'grid' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-400 hover:text-white'
            }`}
            title="Vista en cuadrícula"
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Advanced Filter Strip */}
      <div className="bg-[#10131d] border border-[#1b2030] p-4 rounded-2xl space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Genre selector */}
          <div className="flex items-center gap-2">
            <span className="text-zinc-400 font-semibold font-mono text-[11px]">Género:</span>
            <select
              value={selectedGenre}
              onChange={(e) => setSelectedGenre(e.target.value)}
              className="bg-[#171b29] border border-zinc-700/80 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-amber-400"
            >
              {availableGenres.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          </div>

          {/* Key selector */}
          <div className="flex items-center gap-2">
            <span className="text-zinc-400 font-semibold font-mono text-[11px]">Tonalidad:</span>
            <select
              value={selectedKey}
              onChange={(e) => setSelectedKey(e.target.value)}
              className="bg-[#171b29] border border-zinc-700/80 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-amber-400 font-mono"
            >
              {SCALES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Mood filter */}
          <div className="flex items-center gap-2">
            <span className="text-zinc-400 font-semibold font-mono text-[11px]">Mood:</span>
            <select
              value={selectedMood}
              onChange={(e) => setSelectedMood(e.target.value)}
              className="bg-[#171b29] border border-zinc-700/80 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-amber-400"
            >
              <option value="Todos">Todos</option>
              <option value="Oscuro">Oscuro</option>
              <option value="Bailable">Bailable</option>
              <option value="Chill / Relax">Chill / Relax</option>
              <option value="Triste / Nostálgico">Triste / Nostálgico</option>
              <option value="Enérgico">Enérgico</option>
              <option value="Agresivo">Agresivo</option>
            </select>
          </div>

          {/* Price Filter (Todos / De Pago / Gratis) */}
          <div className="flex items-center gap-1.5 bg-[#171b29] p-1 rounded-xl border border-zinc-700/80 font-mono text-[11px]">
            <button
              onClick={() => setPriceFilter('all')}
              className={`px-2.5 py-1 rounded-lg font-bold transition-colors ${
                priceFilter === 'all'
                  ? 'bg-amber-400 text-zinc-950 shadow-sm'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              Todos
            </button>
            <button
              onClick={() => setPriceFilter('paid')}
              className={`px-2.5 py-1 rounded-lg font-bold transition-colors ${
                priceFilter === 'paid'
                  ? 'bg-amber-400 text-zinc-950 shadow-sm'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              De Pago ($)
            </button>
            <button
              onClick={() => setPriceFilter('free')}
              className={`px-2.5 py-1 rounded-lg font-bold transition-colors ${
                priceFilter === 'free'
                  ? 'bg-emerald-400 text-zinc-950 font-black shadow-sm'
                  : 'text-emerald-400 hover:bg-emerald-950/40'
              }`}
            >
              Solo Gratis (Free)
            </button>
          </div>

          {/* Rango de precio */}
          <div className="flex items-center gap-2">
            <label
              htmlFor="catalog-price-range"
              className="text-zinc-400 font-semibold font-mono text-[11px]"
            >
              Precio:
            </label>
            <select
              id="catalog-price-range"
              value={['all', 'paid', 'free'].includes(priceFilter) ? 'any' : priceFilter}
              onChange={(event) => {
                const next = event.target.value;
                setPriceFilter(next === 'any' ? 'all' : (next as typeof priceFilter));
              }}
              className="bg-[#171b29] border border-zinc-700/80 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-amber-400"
            >
              <option value="any">Todos los precios</option>
              <option value="0_5000">$0 - $5.000</option>
              <option value="5001_10000">$5.001 - $10.000</option>
              <option value="10001_20000">$10.001 - $20.000</option>
              <option value="20001_plus">Mas de $20.000</option>
            </select>
          </div>
          {/* Stems only toggle */}
          <label className="flex items-center gap-2 cursor-pointer text-zinc-300 font-semibold text-xs">
            <input
              type="checkbox"
              checked={onlyWithStems}
              onChange={(e) => setOnlyWithStems(e.target.checked)}
              className="rounded text-amber-400 focus:ring-amber-400 bg-zinc-900 border-zinc-700"
            />
            <span className="flex items-center gap-1 font-mono text-[11px]">
              <Layers className="w-3.5 h-3.5 text-amber-400" />
              <span>Solo con Stems</span>
            </span>
          </label>

          {/* Sort By */}
          <div className="flex items-center gap-2">
            <span className="text-zinc-400 font-semibold font-mono text-[11px]">Ordenar:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-[#171b29] border border-zinc-700/80 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-amber-400 font-semibold"
            >
              <option value="recientes">Más recientes</option>
               <option value="antiguos">Más antiguos</option>
              <option value="likes">Más populares</option>
              <option value="bpm_asc">BPM (Menor a Mayor)</option>
              <option value="bpm_desc">BPM (Mayor a Menor)</option>
              <option value="precio_menor">Precio menor</option>
               <option value="precio_mayor">Precio mayor</option>
               <option value="nombre_asc">Nombre A-Z</option>
               <option value="nombre_desc">Nombre Z-A</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-bold text-zinc-400">
            RESULTADOS: <strong className="text-white">{filteredTracks.length}</strong> PISTAS ENCONTRADAS
          </span>
          {globalSearchQuery && (
            <span className="text-xs text-amber-400 bg-amber-400/10 border border-amber-400/30 px-2 py-0.5 rounded-md font-mono">
              Filtro: "{globalSearchQuery}"
            </span>
          )}
        </div>
      </div>

      {/* Content Rendering: TABLE / DAW VIEW vs GRID VIEW */}
      {filteredTracks.length === 0 ? (
        <div className="p-12 text-center bg-[#0d0f17] border border-[#1b2030] rounded-3xl">
          <Disc3 className="w-10 h-10 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white mb-1">No se encontraron resultados</h3>
          <p className="text-xs text-zinc-500 mb-4">
            Prueba ajustando los filtros de BPM, tonalidad o género musical.
          </p>
          <button
            onClick={() => {
              setSelectedGenre('Todos');
              setSelectedKey('Todas');
              setSelectedMood('Todos');
              setOnlyWithStems(false);
              setPriceFilter('all');
              setGlobalSearchQuery('');
              setActiveResourceFilter('all');
            }}
            className="px-4 py-2 bg-amber-400 text-zinc-950 font-bold rounded-xl text-xs hover:bg-amber-300"
          >
            Restablecer todos los filtros
          </button>
        </div>
      ) : viewMode === 'table' ? (
        /* DAW Compact Table Layout */
        <div className="bg-[#0e111a] border border-[#1b2030] rounded-2xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#141724] border-b border-[#1b2030] text-zinc-400 font-mono uppercase text-[10px]">
                  <th className="py-3 px-4 w-12 text-center">#</th>
                  <th className="py-3 px-4">Pista / Productor</th>
                  <th className="py-3 px-4">Tipo</th>
                  <th className="py-3 px-4">Género</th>
                  <th className="py-3 px-4">BPM</th>
                  <th className="py-3 px-4">Tonalidad</th>
                  <th className="py-3 px-4">Mood</th>
                  <th className="py-3 px-4">Formatos</th>
                  <th className="py-3 px-4 text-right">Precio</th>
                  <th className="py-3 px-4 text-center w-28">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#181d2c] font-medium text-zinc-300">
                {pagedTracks.map((track, idx) => {
                  const isThisPlaying = isPlaying && activeTrack?.id === track.id;
                  const isLiked = currentUser?.likedTrackIds.includes(track.id);
                  const isPurchased = currentUser?.purchasedTrackIds.includes(track.id);
                  const badge = getResourceBadgeInfo(track.resourceType);

                  return (
                    <tr
                      key={track.id}
                      className="hover:bg-[#151926] transition-colors group"
                    >
                      {/* Play Action / Index */}
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => playTrack(track)}
                          className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                            isThisPlaying
                              ? 'bg-amber-400 text-zinc-950 shadow-md shadow-amber-400/30'
                              : 'bg-zinc-800 text-zinc-300 group-hover:bg-amber-400 group-hover:text-zinc-950'
                          }`}
                          title={isThisPlaying ? 'Pausar' : 'Reproducir previa'}
                        >
                          {isThisPlaying ? (
                            <Pause className="w-3.5 h-3.5 fill-current" />
                          ) : (
                            <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
                          )}
                        </button>
                      </td>

                      {/* Title & Cover */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <img
                            src={track.coverUrl}
                            alt={track.title}
                            className="w-10 h-10 rounded-lg object-cover flex-shrink-0 cursor-pointer"
                            onClick={() => onOpenTrackDetail(track.id)}
                          />
                          <div className="min-w-0">
                            <span
                              onClick={() => onOpenTrackDetail(track.id)}
                              className="font-bold text-white hover:text-amber-400 cursor-pointer truncate block text-sm transition-colors"
                            >
                              {track.title}
                            </span>
                            <button
                              onClick={() => onOpenProducerProfile(track.producerId)}
                              className="text-xs text-zinc-400 hover:text-zinc-200 truncate block transition-colors"
                            >
                              {track.producerName}
                            </button>
                          </div>
                        </div>
                      </td>

                      {/* Resource Type Tag with Color */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase border ${badge.badgeClass}`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${badge.dotColor}`} />
                          <span>{badge.label}</span>
                        </span>
                      </td>

                      {/* Genre */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="text-zinc-300 text-xs font-semibold">{track.genre}</span>
                        {track.subgenre && (
                          <span className="text-[10px] text-zinc-400 block">{track.subgenre}</span>
                        )}
                      </td>

                      {/* BPM */}
                      <td className="py-3 px-4 font-mono font-bold text-zinc-200">
                        {track.bpm}
                      </td>

                      {/* Scale Key */}
                      <td className="py-3 px-4 font-mono text-xs text-amber-300">
                        {track.scaleKey}
                      </td>

                      {/* Mood */}
                      <td className="py-3 px-4 text-xs text-zinc-400 whitespace-nowrap">
                        {track.mood || 'Oscuro'}
                      </td>

                      {/* Formats / Stems */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <div className="flex items-center gap-1 text-[10px] font-mono">
                          {track.hasWav && (
                            <span className="px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300">WAV</span>
                          )}
                          {track.hasStems && (
                            <span className="px-1.5 py-0.5 rounded bg-amber-400/20 text-amber-300 font-bold">
                              STEMS
                            </span>
                          )}
                          {track.hasMidi && (
                            <span className="px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">MIDI</span>
                          )}
                        </div>
                      </td>

                      {/* Price */}
                      <td className="py-3 px-4 text-right font-mono font-black whitespace-nowrap">
                        {track.isFree || track.price === 0 ? (
                          <span className="text-[11px] font-black text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/40">
                            GRATIS
                          </span>
                        ) : (
                          <span className="text-amber-400">
                            ${track.price.toLocaleString('es-CL')} CLP
                          </span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          <button
                            onClick={() => toggleLike(track.id)}
                            className={`p-1.5 rounded-lg border transition-colors ${
                              isLiked
                                ? 'border-rose-500/40 text-rose-400 bg-rose-500/10'
                                : 'border-zinc-800 text-zinc-400 hover:text-white'
                            }`}
                            title="Favorito"
                          >
                            <Heart className={`w-3.5 h-3.5 ${isLiked ? 'fill-current' : ''}`} />
                          </button>

                          {!isPurchased ? (
                            track.isFree || track.price === 0 ? (
                              <button
                                onClick={(e) => handleDownloadFree(e, track)}
                                className="px-2.5 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-black rounded-lg text-xs flex items-center gap-1 shadow-sm transition-transform active:scale-95"
                                title="Descargar demo libre (Non-Profit)"
                              >
                                <Download className="w-3 h-3 stroke-[2.5]" />
                                <span>Descargar</span>
                              </button>
                            ) : (
                              <div className="flex items-center gap-1.5">
                                <button
                                  onClick={() => addToCart(track)}
                                  className="px-2.5 py-1.5 bg-amber-400 hover:bg-amber-300 text-zinc-950 font-bold rounded-lg text-xs flex items-center gap-1 shadow-sm transition-transform active:scale-95"
                                  title="Comprar / Agregar al carrito"
                                >
                                  <ShoppingCart className="w-3 h-3" />
                                  <span>Comprar</span>
                                </button>
                                {track.allowFreeDownload && (
                                  <button
                                    onClick={(e) => handleDownloadAudition(e, track)}
                                    className="px-2 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-bold rounded-lg text-xs border border-zinc-700 flex items-center gap-1 transition-colors"
                                    title="Descargar Maqueta de Composición (MP3 con marca de agua)"
                                  >
                                    <Mic2 className="w-3 h-3 text-amber-400" />
                                  </button>
                                )}
                              </div>
                            )
                          ) : (
                            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/60 px-2 py-1 rounded border border-emerald-500/30">
                              ✓ Adquirido
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Grid Layout */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {pagedTracks.map((track) => {
            const isThisPlaying = isPlaying && activeTrack?.id === track.id;
            const isLiked = currentUser?.likedTrackIds.includes(track.id);
            const isPurchased = currentUser?.purchasedTrackIds.includes(track.id);
            const badge = getResourceBadgeInfo(track.resourceType);

            return (
              <div
                key={track.id}
                className="bg-[#0e111a] border border-[#1b2030] hover:border-amber-400/40 rounded-2xl p-4 transition-all hover:-translate-y-0.5 shadow-md flex flex-col justify-between group"
              >
                <div>
                  <div className="relative aspect-video rounded-xl overflow-hidden mb-3 bg-zinc-900">
                    <img
                      src={track.coverUrl}
                      alt={track.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/30 to-transparent" />

                    <button
                      onClick={() => playTrack(track)}
                      className="absolute inset-0 m-auto w-12 h-12 rounded-full bg-amber-400 text-zinc-950 flex items-center justify-center shadow-lg transition-transform hover:scale-110"
                    >
                      {isThisPlaying ? (
                        <Pause className="w-5 h-5 fill-current" />
                      ) : (
                        <Play className="w-5 h-5 fill-current ml-0.5" />
                      )}
                    </button>

                    {/* Badge */}
                    <span
                      className={`absolute top-2 left-2 text-[10px] font-black uppercase px-2 py-0.5 rounded-md border ${badge.badgeClass}`}
                    >
                      {badge.label}
                    </span>

                    <span className="absolute bottom-2 left-2 text-[10px] font-mono text-zinc-300 bg-black/75 px-2 py-0.5 rounded">
                      {track.bpm} BPM • {track.scaleKey}
                    </span>
                  </div>

                  <h3
                    onClick={() => onOpenTrackDetail(track.id)}
                    className="font-bold text-white text-base hover:text-amber-400 cursor-pointer truncate transition-colors"
                  >
                    {track.title}
                  </h3>

                  <button
                    onClick={() => onOpenProducerProfile(track.producerId)}
                    className="text-xs text-zinc-400 hover:text-zinc-200 mt-0.5 block truncate"
                  >
                    Por <span className="font-semibold text-zinc-300">{track.producerName}</span>
                  </button>

                  <div className="flex items-center gap-2 mt-2 text-[10px] text-zinc-400 font-mono">
                    <span className="bg-zinc-900 px-1.5 py-0.5 rounded">{track.genre}</span>
                    <span className="bg-zinc-900 px-1.5 py-0.5 rounded">{track.mood}</span>
                    {track.hasStems && (
                      <span className="text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded font-bold">
                        Stems
                      </span>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-[#1b2030] flex items-center justify-between">
                  <span className="text-base font-black font-mono">
                    {track.isFree || track.price === 0 ? (
                      <span className="text-[11px] font-black text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/40">
                        GRATIS
                      </span>
                    ) : (
                      <span className="text-amber-400">
                        ${track.price.toLocaleString('es-CL')}
                      </span>
                    )}
                  </span>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => toggleLike(track.id)}
                      className={`p-2 rounded-lg border transition-colors ${
                        isLiked
                          ? 'border-rose-500/40 text-rose-400 bg-rose-500/10'
                          : 'border-zinc-800 text-zinc-400 hover:text-white'
                      }`}
                    >
                      <Heart className={`w-3.5 h-3.5 ${isLiked ? 'fill-current' : ''}`} />
                    </button>

                    {!isPurchased ? (
                      track.isFree || track.price === 0 ? (
                        <button
                          onClick={(e) => handleDownloadFree(e, track)}
                          className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-black rounded-lg text-xs flex items-center gap-1 shadow-sm transition-transform active:scale-95"
                          title="Descargar demo libre (Non-Profit)"
                        >
                          <Download className="w-3.5 h-3.5 stroke-[2.5]" />
                          <span>Descargar</span>
                        </button>
                      ) : (
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => addToCart(track)}
                            className="px-3 py-1.5 bg-amber-400 hover:bg-amber-300 text-zinc-950 font-bold rounded-lg text-xs flex items-center gap-1"
                          >
                            <ShoppingCart className="w-3.5 h-3.5" />
                            <span>Comprar</span>
                          </button>
                          {track.allowFreeDownload && (
                            <button
                              onClick={(e) => handleDownloadAudition(e, track)}
                              className="p-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-lg border border-zinc-700 flex items-center transition-colors"
                              title="Descargar Maqueta de Composición (MP3 con marca de agua)"
                            >
                              <Mic2 className="w-3.5 h-3.5 text-amber-400" />
                            </button>
                          )}
                        </div>
                      )
                    ) : (
                      <span className="text-xs text-emerald-400 font-bold bg-emerald-950/60 px-2 py-1 rounded border border-emerald-500/30">
                        ✓ Adquirido
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
      {filteredTracks.length > 0 && (
        <nav
          aria-label="Paginacion del catalogo"
          className="flex flex-wrap items-center justify-between gap-4 bg-[#10131d] border border-[#1b2030] p-4 rounded-2xl"
        >
          <div className="flex flex-wrap items-center gap-3">
            <label
              htmlFor="catalog-page-size"
              className="text-xs font-semibold text-zinc-300"
            >
              Pistas por pagina
            </label>

            <select
              id="catalog-page-size"
              value={pageSize}
              onChange={(event) => {
                setPageSize(Number(event.target.value));
                setCurrentPage(1);
              }}
              className="bg-[#171b29] border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white"
            >
              <option value={6}>6</option>
              <option value={12}>12</option>
              <option value={24}>24</option>
            </select>

            <span className="text-xs text-zinc-400" role="status">
              Mostrando {startIndex + 1}-
              {Math.min(startIndex + pageSize, filteredTracks.length)}
              {' '}de {filteredTracks.length} pistas
            </span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              disabled={safePage === 1}
              onClick={() => setCurrentPage(1)}
              className="px-3 py-2 text-xs rounded-lg bg-zinc-800 text-white disabled:opacity-40"
            >
              Primera
            </button>

            <button
              type="button"
              disabled={safePage === 1}
              onClick={() => setCurrentPage(safePage - 1)}
              className="px-3 py-2 text-xs rounded-lg bg-zinc-800 text-white disabled:opacity-40"
            >
              Anterior
            </button>

            <span
              className="px-2 text-xs font-bold text-amber-400 whitespace-nowrap"
              aria-live="polite"
            >
              Pagina {safePage} de {totalPages}
            </span>

            <button
              type="button"
              disabled={safePage === totalPages}
              onClick={() => setCurrentPage(safePage + 1)}
              className="px-3 py-2 text-xs rounded-lg bg-amber-400 text-zinc-950 font-bold disabled:opacity-40"
            >
              Siguiente
            </button>

            <button
              type="button"
              disabled={safePage === totalPages}
              onClick={() => setCurrentPage(totalPages)}
              className="px-3 py-2 text-xs rounded-lg bg-zinc-800 text-white disabled:opacity-40"
            >
              Ultima
            </button>
          </div>
        </nav>
      )}

    </div>
  );
};
