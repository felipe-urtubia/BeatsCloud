import React from 'react';
import { useApp } from '../context/AppContext';
import { ResourceType, Track } from '../types';
import { getResourceBadgeInfo } from '../utils/resourceHelpers';
import {
  Compass,
  Flame,
  Play,
  Pause,
  ShoppingCart,
  Heart,
  Sparkles,
  ArrowRight,
  Disc3,
  Sliders,
  Layers,
  Radio,
} from 'lucide-react';

interface DiscoverPageProps {
  onNavigateCatalog: () => void;
  onOpenTrackDetail: (trackId: string) => void;
  onOpenProducerProfile: (producerId: string) => void;
}

export const DiscoverPage: React.FC<DiscoverPageProps> = ({
  onNavigateCatalog,
  onOpenTrackDetail,
  onOpenProducerProfile,
}) => {
  const { tracks, users, playTrack, activeTrack, isPlaying, addToCart, toggleLike, currentUser, setActiveResourceFilter } = useApp();

  const trendingTracks = tracks.slice(0, 5);
  const producers = users.filter((u) => u.role === 'productor');
  const recentLoops = tracks.filter((t) => t.resourceType === 'loop' || t.resourceType === 'acapella').slice(0, 4);

  return (
    <div className="py-5 pb-36 max-w-7xl mx-auto space-y-8">
      {/* Studio Banner / Spotlight */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-[#111420] via-[#171b2a] to-[#0f121d] border border-[#1f2538] p-6 sm:p-8 shadow-xl">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-400/10 border border-amber-400/30 text-amber-300 text-xs font-mono font-bold mb-3">
            <Radio className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
            <span>EN VIVO · BEATSCLOUD STUDIO</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-black text-white tracking-tight leading-tight mb-2">
            Workspace de Producción & Beats Independientes
          </h1>

          <p className="text-xs sm:text-sm text-zinc-300 mb-5 leading-relaxed">
            Explora instrumentales con stems separados, loops de melodía sin royalties, acapellas de estudio y drum kits listos para tu DAW.
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={onNavigateCatalog}
              className="bg-amber-400 hover:bg-amber-300 text-zinc-950 font-black px-5 py-2.5 rounded-xl text-xs transition-all hover:scale-102 flex items-center gap-2 shadow-sm"
            >
              <span>Explorar Todo el Catálogo</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Quick Category Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div
          onClick={() => {
            setActiveResourceFilter('instrumental');
            onNavigateCatalog();
          }}
          className="bg-[#0e111a] border border-sky-500/20 hover:border-sky-500/50 p-4 rounded-2xl cursor-pointer transition-all hover:-translate-y-0.5 group"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="w-3 h-3 rounded-full bg-sky-400" />
            <span className="text-[10px] font-mono text-zinc-400 uppercase">BEATS</span>
          </div>
          <h3 className="font-bold text-white text-sm group-hover:text-sky-400 transition-colors">
            Instrumentales
          </h3>
          <p className="text-[11px] text-zinc-400 mt-1">Trap, Dembow, Drill</p>
        </div>

        <div
          onClick={() => {
            setActiveResourceFilter('loop');
            onNavigateCatalog();
          }}
          className="bg-[#0e111a] border border-amber-500/20 hover:border-amber-500/50 p-4 rounded-2xl cursor-pointer transition-all hover:-translate-y-0.5 group"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="w-3 h-3 rounded-full bg-amber-400" />
            <span className="text-[10px] font-mono text-zinc-400 uppercase">LOOPS</span>
          </div>
          <h3 className="font-bold text-white text-sm group-hover:text-amber-400 transition-colors">
            Loops & Melodías
          </h3>
          <p className="text-[11px] text-zinc-400 mt-1">Guitarras, Rhodes, Synths</p>
        </div>

        <div
          onClick={() => {
            setActiveResourceFilter('acapella');
            onNavigateCatalog();
          }}
          className="bg-[#0e111a] border border-purple-500/20 hover:border-purple-500/50 p-4 rounded-2xl cursor-pointer transition-all hover:-translate-y-0.5 group"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="w-3 h-3 rounded-full bg-purple-400" />
            <span className="text-[10px] font-mono text-zinc-400 uppercase">VOX</span>
          </div>
          <h3 className="font-bold text-white text-sm group-hover:text-purple-400 transition-colors">
            Acapellas & Hooks
          </h3>
          <p className="text-[11px] text-zinc-400 mt-1">Vocales secos y procesados</p>
        </div>

        <div
          onClick={() => {
            setActiveResourceFilter('drumkit');
            onNavigateCatalog();
          }}
          className="bg-[#0e111a] border border-emerald-500/20 hover:border-emerald-500/50 p-4 rounded-2xl cursor-pointer transition-all hover:-translate-y-0.5 group"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="w-3 h-3 rounded-full bg-emerald-400" />
            <span className="text-[10px] font-mono text-zinc-400 uppercase">KITS</span>
          </div>
          <h3 className="font-bold text-white text-sm group-hover:text-emerald-400 transition-colors">
            Drum Kits & 808s
          </h3>
          <p className="text-[11px] text-zinc-400 mt-1">One-shots y percusión</p>
        </div>
      </div>

      {/* Trending Tracks Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Flame className="w-5 h-5 text-amber-400 fill-amber-400" />
            <h2 className="text-base font-black text-white tracking-tight uppercase font-mono">
              Top Tendencias en el Estudio
            </h2>
          </div>
          <button
            onClick={onNavigateCatalog}
            className="text-xs font-bold text-amber-400 hover:text-amber-300"
          >
            Ver catálogo completo →
          </button>
        </div>

        <div className="bg-[#0e111a] border border-[#1b2030] rounded-2xl divide-y divide-[#181d2c] overflow-hidden">
          {trendingTracks.map((track, i) => {
            const isThisPlaying = isPlaying && activeTrack?.id === track.id;
            const isLiked = currentUser?.likedTrackIds.includes(track.id);
            const isPurchased = currentUser?.purchasedTrackIds.includes(track.id);
            const badge = getResourceBadgeInfo(track.resourceType);

            return (
              <div
                key={track.id}
                className="p-3 sm:px-4 flex items-center justify-between gap-3 hover:bg-[#141824] transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-xs font-mono font-bold text-zinc-400 w-5 text-center">
                    0{i + 1}
                  </span>

                  <button
                    onClick={() => playTrack(track)}
                    className={`w-9 h-9 rounded-full flex items-center justify-center transition-all flex-shrink-0 ${
                      isThisPlaying
                        ? 'bg-amber-400 text-zinc-950'
                        : 'bg-zinc-800 text-zinc-300 hover:bg-amber-400 hover:text-zinc-950'
                    }`}
                  >
                    {isThisPlaying ? (
                      <Pause className="w-4 h-4 fill-current" />
                    ) : (
                      <Play className="w-4 h-4 fill-current ml-0.5" />
                    )}
                  </button>

                  <img
                    src={track.coverUrl}
                    alt={track.title}
                    className="w-10 h-10 rounded-lg object-cover flex-shrink-0 cursor-pointer"
                    onClick={() => onOpenTrackDetail(track.id)}
                  />

                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded border uppercase ${badge.badgeClass}`}
                      >
                        {badge.badge}
                      </span>
                      <span
                        onClick={() => onOpenTrackDetail(track.id)}
                        className="font-bold text-white hover:text-amber-400 cursor-pointer text-xs sm:text-sm truncate"
                      >
                        {track.title}
                      </span>
                    </div>
                    <span className="text-[11px] text-zinc-400 block truncate">
                      {track.producerName} · {track.bpm} BPM · {track.scaleKey}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-xs sm:text-sm font-mono font-bold text-amber-400 whitespace-nowrap">
                    ${track.price.toLocaleString('es-CL')}
                  </span>

                  <button
                    onClick={() => toggleLike(track.id)}
                    className={`p-1.5 rounded-lg border transition-colors hidden sm:block ${
                      isLiked
                        ? 'border-rose-500/40 text-rose-400 bg-rose-500/10'
                        : 'border-zinc-800 text-zinc-400 hover:text-white'
                    }`}
                  >
                    <Heart className={`w-3.5 h-3.5 ${isLiked ? 'fill-current' : ''}`} />
                  </button>

                  {!isPurchased ? (
                    <button
                      onClick={() => addToCart(track)}
                      className="px-2.5 py-1.5 bg-amber-400 hover:bg-amber-300 text-zinc-950 font-bold rounded-lg text-xs flex items-center gap-1 shadow-sm"
                    >
                      <ShoppingCart className="w-3 h-3" />
                      <span className="hidden sm:inline">Comprar</span>
                    </button>
                  ) : (
                    <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/60 px-2 py-1 rounded border border-emerald-500/30">
                      Adquirido
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Featured Producers Row */}
      <div>
        <h2 className="text-base font-black text-white tracking-tight uppercase font-mono mb-4">
          Productores Verificados
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {producers.map((prod) => {
            const count = tracks.filter((t) => t.producerId === prod.id).length;

            return (
              <div
                key={prod.id}
                onClick={() => onOpenProducerProfile(prod.id)}
                className="bg-[#0e111a] border border-[#1b2030] hover:border-amber-400/40 p-4 rounded-2xl cursor-pointer transition-all hover:-translate-y-0.5 group"
              >
                <div className="flex items-center gap-3">
                  <img
                    src={prod.avatarUrl}
                    alt={prod.artistName}
                    className="w-12 h-12 rounded-xl object-cover ring-1 ring-amber-400/30"
                  />
                  <div className="min-w-0 flex-1">
                    <h4 className="font-bold text-white text-sm group-hover:text-amber-400 truncate">
                      {prod.artistName}
                    </h4>
                    <p className="text-[11px] text-zinc-400 truncate">@{prod.username}</p>
                    <span className="text-[10px] font-mono text-amber-400 font-bold">
                      {count} producciones activas
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
