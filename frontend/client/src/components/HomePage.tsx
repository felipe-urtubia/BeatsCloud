import React from 'react';
import { useApp } from '../context/AppContext';
import { Play, Pause, ShoppingCart, Sparkles, Music, ShieldCheck, Flame, Mic2, Sliders, ArrowRight } from 'lucide-react';
import { Track } from '../types';

interface HomePageProps {
  onNavigateCatalog: () => void;
  onOpenTrackDetail: (trackId: string) => void;
  onOpenAuth: (mode: 'login' | 'register') => void;
  onOpenProducerProfile?: (producerId: string) => void;
}

export const HomePage: React.FC<HomePageProps> = ({
  onNavigateCatalog,
  onOpenTrackDetail,
  onOpenAuth,
  onOpenProducerProfile,
}) => {
  const { tracks, playTrack, activeTrack, isPlaying, addToCart, currentUser } = useApp();

  const featuredTracks = tracks.slice(0, 4);

  return (
    <div className="pb-28">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#121318] via-[#1a1b24] to-[#121318] border border-zinc-800 shadow-2xl p-8 sm:p-14 my-6">
        <div className="absolute top-0 right-0 w-96 h-96 bg-amber-400/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-400/10 border border-amber-400/30 text-amber-300 text-xs font-bold mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Plataforma líder para creadores de música urbana e independiente</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight leading-[1.08] mb-6">
            El sonido que define tu próximo <span className="text-amber-400">éxito musical</span>.
          </h1>

          <p className="text-base sm:text-lg text-zinc-300 leading-relaxed mb-8 max-w-2xl">
            Conectamos a los productores más innovadores con artistas independientes. Descubre instrumentales exclusivas de Trap, Hip-Hop, Reggaetón, R&B y más, listas para grabar y monetizar.
          </p>

          <div className="flex flex-wrap items-center gap-4">
            <button
              onClick={onNavigateCatalog}
              className="bg-amber-400 hover:bg-amber-300 text-zinc-950 font-black px-7 py-3.5 rounded-xl text-sm transition-all hover:scale-105 shadow-lg shadow-amber-400/20 flex items-center gap-2"
            >
              <span>Explorar Catálogo</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onOpenAuth('register')}
              className="bg-zinc-800/80 hover:bg-zinc-700 text-white font-bold px-6 py-3.5 rounded-xl text-sm border border-zinc-700 transition-colors"
            >
              Únete como Productor o Artista
            </button>
          </div>
        </div>
      </section>

      {/* Featured Tracks Preview */}
      <section className="my-14">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-2">
              <Flame className="w-6 h-6 text-amber-400 fill-amber-400" />
              <span>Beats Destacados</span>
            </h2>
            <p className="text-sm text-zinc-400 mt-1">
              Las instrumentales más escuchadas y valoradas por la comunidad
            </p>
          </div>
          <button
            onClick={onNavigateCatalog}
            className="text-xs sm:text-sm font-bold text-amber-400 hover:text-amber-300 transition-colors flex items-center gap-1"
          >
            Ver todos los beats ({tracks.length}) →
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {featuredTracks.map((track) => {
            const isThisPlaying = isPlaying && activeTrack?.id === track.id;
            const isPurchased = currentUser?.purchasedTrackIds.includes(track.id);

            return (
              <div
                key={track.id}
                className="group bg-[#161720] rounded-2xl border border-zinc-800 hover:border-amber-400/40 p-4 transition-all hover:-translate-y-1 shadow-lg hover:shadow-amber-400/5 flex flex-col"
              >
                {/* Cover Art */}
                <div className="relative aspect-square rounded-xl overflow-hidden mb-4 bg-zinc-800">
                  <img
                    src={track.coverUrl}
                    alt={track.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

                  {/* Play Button Overlay */}
                  <button
                    onClick={() => playTrack(track)}
                    className="absolute inset-0 m-auto w-14 h-14 rounded-full bg-amber-400 text-zinc-950 flex items-center justify-center shadow-xl transition-all duration-200 hover:scale-110 opacity-90 group-hover:opacity-100"
                    title={isThisPlaying ? 'Pausar' : 'Reproducir previa'}
                  >
                    {isThisPlaying ? (
                      <Pause className="w-6 h-6 fill-current" />
                    ) : (
                      <Play className="w-6 h-6 fill-current ml-0.5" />
                    )}
                  </button>

                  <span className="absolute top-2.5 left-2.5 text-[10px] font-black uppercase tracking-wider px-2 py-1 rounded bg-black/60 backdrop-blur-md text-amber-400 border border-amber-400/30">
                    {track.genre}
                  </span>

                  <span className="absolute bottom-2.5 left-2.5 text-[11px] font-mono font-bold text-zinc-300 bg-black/60 px-2 py-0.5 rounded">
                    {track.bpm} BPM
                  </span>
                </div>

                {/* Details */}
                <div className="flex-1 flex flex-col justify-between">
                  <div>
                    <h3
                      onClick={() => onOpenTrackDetail(track.id)}
                      className="font-bold text-white text-base hover:text-amber-400 cursor-pointer truncate transition-colors"
                    >
                      {track.title}
                    </h3>
                    <p className="text-xs text-zinc-400 mt-1 truncate">
                      Por <span className="text-zinc-300 font-semibold">{track.producerName}</span>
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-zinc-800 flex items-center justify-between">
                    <div>
                      <span className="text-xs text-zinc-400 block font-semibold">Precio</span>
                      <span className="text-sm font-black text-amber-400">
                        ${track.price.toLocaleString('es-CL')} CLP
                      </span>
                    </div>

                    {!isPurchased ? (
                      <button
                        onClick={() => addToCart(track)}
                        className="p-2.5 rounded-xl bg-zinc-800 hover:bg-amber-400 hover:text-zinc-950 text-zinc-200 transition-colors border border-zinc-700 hover:border-amber-400"
                        title="Agregar al carrito"
                      >
                        <ShoppingCart className="w-4 h-4" />
                      </button>
                    ) : (
                      <span className="text-xs text-emerald-400 font-bold bg-emerald-950/60 px-2 py-1 rounded">
                        Comprado
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Role Benefits (Artistas vs Productores) */}
      <section className="my-16 grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* For Artists */}
        <div className="bg-[#151720] border border-zinc-800 rounded-3xl p-8 sm:p-10 relative overflow-hidden group hover:border-amber-400/30 transition-colors">
          <div className="w-14 h-14 rounded-2xl bg-amber-400/10 border border-amber-400/20 text-amber-400 flex items-center justify-center mb-6">
            <Mic2 className="w-7 h-7" />
          </div>
          <span className="text-xs font-bold text-amber-400 uppercase tracking-widest block mb-2">
            Para Artistas y Cantantes
          </span>
          <h3 className="text-2xl font-black text-white mb-4">
            Encuentra la instrumental perfecta sin complicaciones
          </h3>
          <ul className="space-y-3 text-sm text-zinc-300 mb-8">
            <li className="flex items-start gap-2.5">
              <span className="text-amber-400 font-bold">✓</span>
              <span>Preescucha con reproductor y visualizador de onda en tiempo real</span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="text-amber-400 font-bold">✓</span>
              <span>Compra directa y segura en pesos chilenos ($ CLP) con Webpay</span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="text-amber-400 font-bold">✓</span>
              <span>Descarga inmediata de archivos en alta fidelidad y licencias comerciales</span>
            </li>
          </ul>
          <button
            onClick={onNavigateCatalog}
            className="text-sm font-bold text-amber-400 hover:text-amber-300 flex items-center gap-2 group-hover:translate-x-1 transition-transform"
          >
            <span>Buscar instrumentales</span>
            <span>→</span>
          </button>
        </div>

        {/* For Producers */}
        <div className="bg-[#151720] border border-zinc-800 rounded-3xl p-8 sm:p-10 relative overflow-hidden group hover:border-amber-400/30 transition-colors">
          <div className="w-14 h-14 rounded-2xl bg-amber-400 text-zinc-950 flex items-center justify-center mb-6 font-black shadow-lg shadow-amber-400/20">
            <Sliders className="w-7 h-7" />
          </div>
          <span className="text-xs font-bold text-amber-400 uppercase tracking-widest block mb-2">
            Para Productores Musicales
          </span>
          <h3 className="text-2xl font-black text-white mb-4">
            Monetiza tu creatividad y expande tu comunidad
          </h3>
          <ul className="space-y-3 text-sm text-zinc-300 mb-8">
            <li className="flex items-start gap-2.5">
              <span className="text-amber-400 font-bold">✓</span>
              <span>Sube tus producciones con tus propios precios y licencias</span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="text-amber-400 font-bold">✓</span>
              <span>Crea membresías y suscripciones VIP recurrentes para tus seguidores</span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="text-amber-400 font-bold">✓</span>
              <span>Panel con historial completo de transacciones y ventas</span>
            </li>
          </ul>
          <button
            onClick={() => onOpenAuth('register')}
            className="text-sm font-bold text-amber-400 hover:text-amber-300 flex items-center gap-2 group-hover:translate-x-1 transition-transform"
          >
            <span>Crear perfil de productor</span>
            <span>→</span>
          </button>
        </div>
      </section>

      {/* How it works steps */}
      <section className="my-16 bg-[#12131a] rounded-3xl border border-zinc-800/80 p-8 sm:p-12 text-center">
        <h2 className="text-2xl sm:text-3xl font-black text-white mb-2">
          ¿Cómo funciona BeatsCloud?
        </h2>
        <p className="text-sm text-zinc-400 max-w-xl mx-auto mb-10">
          Un ecosistema fluido diseñado especialmente para el flujo de trabajo de la música independiente
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 text-left">
          <div className="bg-[#171822] p-6 rounded-2xl border border-zinc-800">
            <div className="w-10 h-10 rounded-xl bg-zinc-800 text-amber-400 font-black flex items-center justify-center text-lg mb-4">
              1
            </div>
            <h4 className="font-bold text-white mb-2">Explora géneros</h4>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Filtra por Trap, Reggaetón, R&B, BPM o tonalidad musical según lo que tu proyecto requiera.
            </p>
          </div>

          <div className="bg-[#171822] p-6 rounded-2xl border border-zinc-800">
            <div className="w-10 h-10 rounded-xl bg-zinc-800 text-amber-400 font-black flex items-center justify-center text-lg mb-4">
              2
            </div>
            <h4 className="font-bold text-white mb-2">Escucha la previa</h4>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Reproduce las instrumentales con el reproductor interactivo y siente la vibra antes de comprar.
            </p>
          </div>

          <div className="bg-[#171822] p-6 rounded-2xl border border-zinc-800">
            <div className="w-10 h-10 rounded-xl bg-zinc-800 text-amber-400 font-black flex items-center justify-center text-lg mb-4">
              3
            </div>
            <h4 className="font-bold text-white mb-2">Paga seguro</h4>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Usa el carrito de compras con cálculo de IVA y pasarela de pago Transbank Webpay integrada.
            </p>
          </div>

          <div className="bg-[#171822] p-6 rounded-2xl border border-zinc-800">
            <div className="w-10 h-10 rounded-xl bg-zinc-800 text-amber-400 font-black flex items-center justify-center text-lg mb-4">
              4
            </div>
            <h4 className="font-bold text-white mb-2">Crea tu hit</h4>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Descarga los archivos a tu biblioteca, graba tus voces y distribuye tu canción al mundo.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
