import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Track } from '../types';
import { getResourceBadgeInfo } from '../utils/resourceHelpers';
import {
  X,
  Play,
  Pause,
  ShoppingCart,
  Download,
  Heart,
  MessageSquare,
  Trash2,
  Send,
  ExternalLink,
  ShieldCheck,
  Disc3,
  Clock,
  Layers,
  Sparkles,
  Lock,
  Mic2,
  FileText,
  CheckCircle2,
  Scale,
} from 'lucide-react';
import { LicenseCertificateModal } from './LicenseCertificateModal';

interface TrackDetailModalProps {
  trackId: string | null;
  onClose: () => void;
  onOpenProducerProfile: (producerId: string) => void;
}

export const TrackDetailModal: React.FC<TrackDetailModalProps> = ({
  trackId,
  onClose,
  onOpenProducerProfile,
}) => {
  const {
    tracks,
    users,
    playTrack,
    activeTrack,
    isPlaying,
    currentTime,
    duration,
    seekAudio,
    toggleLike,
    addToCart,
    claimFreeTrack,
    downloadAuditionDemo,
    generateLicenseForTrack,
    addComment,
    deleteComment,
    currentUser,
  } = useApp();

  const [commentText, setCommentText] = useState('');
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const [auditionSuccess, setAuditionSuccess] = useState(false);
  const [certificateModalOpen, setCertificateModalOpen] = useState(false);

  if (!trackId) return null;

  const track = tracks.find((t) => t.id === trackId);
  if (!track) return null;

  const producer = users.find((u) => u.id === track.producerId);
  const isThisPlaying = isPlaying && activeTrack?.id === track.id;
  const isLiked = currentUser?.likedTrackIds.includes(track.id);
  const isPurchased = currentUser?.purchasedTrackIds.includes(track.id);
  // Regla de negocio "Punto Medio": un beat de pago puede ofrecer la maqueta
  // de composición si el productor activó allowFreeDownload al subirlo.
  const canDownloadAuditionDemo = !isPurchased && (track.isFree || track.price === 0 ? false : track.allowFreeDownload === true);
  const badge = getResourceBadgeInfo(track.resourceType);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const handleSendComment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    addComment(track.id, commentText);
    setCommentText('');
  };

  const handleDownloadFree = () => {
    setDownloadSuccess(true);
    claimFreeTrack(track.id);
    const blob = new Blob(
      [
        `BeatsCloud Licencia Gratuita (Non-Profit / Demo)\n` +
        `Track: ${track.title}\n` +
        `Productor: ${track.producerName}\n` +
        `BPM: ${track.bpm} | Key: ${track.scaleKey}\n` +
        `Descargado por: ${currentUser?.artistName || 'Artista'}\n\n` +
        `Condiciones de la Licencia Gratuita:\n` +
        `1. Permite uso libre para ensayos, maquetas y streaming no lucrativo (SoundCloud / YouTube sin monetizar).\n` +
        `2. Requiere acreditar obligatoriamente al productor: (Prod. ${track.producerName}).\n` +
        `3. Para distribución comercial en Spotify, Apple Music o directos pagados, se debe adquirir la Licencia Comercial en BeatsCloud.`
      ],
      { type: 'text/plain' }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${track.title.replace(/[\s/]/g, '_')}_Demo_Gratis_BeatsCloud.txt`;
    a.click();
    setTimeout(() => setDownloadSuccess(false), 3000);
  };

  const handleDownload = () => {
    setDownloadSuccess(true);
    const blob = new Blob(
      [
        `BeatsCloud License & Stems Certificate\nTrack: ${track.title}\nProducer: ${track.producerName}\nResource Type: ${track.resourceType}\nBPM: ${track.bpm}\nKey: ${track.scaleKey}\nPurchased by: ${currentUser?.artistName || 'Artist'}\nLicense: Full Commercial Rights (Unlimited Distribution)`,
      ],
      { type: 'text/plain' }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${track.title.replace(/[\s/]/g, '_')}_Licencia_BeatsCloud.txt`;
    a.click();
    setTimeout(() => setDownloadSuccess(false), 3000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/85 backdrop-blur-md animate-in fade-in duration-150">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-[#0e111a] border border-[#1f2538] rounded-3xl shadow-2xl overflow-y-auto">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 w-9 h-9 rounded-full bg-zinc-900/80 hover:bg-zinc-800 text-zinc-300 hover:text-white flex items-center justify-center border border-zinc-700 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Modal Header */}
        <div className="relative p-6 sm:p-8 bg-gradient-to-br from-[#131623] via-[#10131e] to-[#0c0e15] border-b border-[#1b2030]">
          <div className="flex flex-col sm:flex-row gap-6 items-start sm:items-center">
            {/* Big Cover */}
            <div className="relative w-36 h-36 sm:w-44 sm:h-44 rounded-2xl overflow-hidden shadow-2xl flex-shrink-0 group bg-zinc-800 border border-zinc-700">
              <img
                src={track.coverUrl}
                alt={track.title}
                className="w-full h-full object-cover"
              />
              <button
                onClick={() => playTrack(track)}
                className="absolute inset-0 m-auto w-14 h-14 rounded-full bg-amber-400 text-zinc-950 flex items-center justify-center shadow-2xl transition-transform hover:scale-110"
              >
                {isThisPlaying ? (
                  <Pause className="w-6 h-6 fill-current" />
                ) : (
                  <Play className="w-6 h-6 fill-current ml-0.5" />
                )}
              </button>

              {isPurchased && (
                <span className="absolute top-2 left-2 text-[10px] font-black uppercase tracking-wider bg-emerald-600 text-white px-2 py-0.5 rounded shadow">
                  Comprado
                </span>
              )}
            </div>

            {/* Track Info */}
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span
                  className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase border ${badge.badgeClass}`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${badge.dotColor}`} />
                  <span>{badge.label}</span>
                </span>
                <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-zinc-800 text-zinc-300">
                  {track.genre}
                </span>
                <span className="text-xs font-mono text-zinc-400">
                  {track.bpm} BPM · {track.scaleKey}
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight mb-1">
                {track.title}
              </h1>

              {/* Producer quick link */}
              <div
                onClick={() => {
                  onClose();
                  onOpenProducerProfile(track.producerId);
                }}
                className="flex items-center gap-2 text-zinc-300 hover:text-amber-400 cursor-pointer w-fit mb-4 transition-colors"
              >
                <img
                  src={track.producerAvatar}
                  alt={track.producerName}
                  className="w-5 h-5 rounded-full object-cover ring-1 ring-amber-400/30"
                />
                <span className="text-xs font-bold">{track.producerName}</span>
                <ExternalLink className="w-3 h-3 text-zinc-500" />
              </div>

              {/* Price & Action Row */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="bg-[#151926] border border-[#23283b] px-4 py-2 rounded-xl">
                  <span className="text-[10px] text-zinc-400 block uppercase font-mono font-bold">
                    Precio Licencia
                  </span>
                  {track.isFree || track.price === 0 ? (
                    <span className="text-lg font-black text-emerald-400 font-mono">
                      GRATIS ($0 CLP)
                    </span>
                  ) : (
                    <span className="text-lg font-black text-amber-400 font-mono">
                      ${track.price.toLocaleString('es-CL')} CLP
                    </span>
                  )}
                </div>

                {!isPurchased ? (
                  track.isFree || track.price === 0 ? (
                    <button
                      onClick={handleDownloadFree}
                      className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-black px-5 py-3 rounded-xl text-xs transition-all shadow-md shadow-emerald-500/20 hover:scale-102"
                    >
                      <Download className="w-4 h-4 stroke-[2.5]" />
                      <span>{downloadSuccess ? '¡Descargado!' : 'Descargar Beat Gratis'}</span>
                    </button>
                  ) : (
                    <div className="flex flex-wrap items-center gap-2.5">
                      <button
                        onClick={() => addToCart(track)}
                        className="flex items-center gap-2 bg-amber-400 hover:bg-amber-300 text-zinc-950 font-black px-5 py-3 rounded-xl text-xs transition-all shadow-md shadow-amber-400/20 hover:scale-102"
                      >
                        <ShoppingCart className="w-4 h-4" />
                        <span>Comprar Licencia Comercial (WAV + Stems)</span>
                      </button>

                      {/* Sweet spot action: Writing / Audition demo (solo si el productor la habilitó) */}
                      {canDownloadAuditionDemo && (
                        <button
                          onClick={() => {
                            setAuditionSuccess(true);
                            downloadAuditionDemo(track);
                            setTimeout(() => setAuditionSuccess(false), 3000);
                          }}
                          className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 hover:text-white font-bold px-4 py-3 rounded-xl text-xs border border-zinc-700 transition-colors"
                          title="Descarga una copia MP3 con marca de agua para probar tu voz y componer antes de comprar"
                        >
                          <Mic2 className="w-4 h-4 text-amber-400" />
                          <span>{auditionSuccess ? '¡Maqueta Descargada!' : 'Descargar Maqueta para Composición'}</span>
                        </button>
                      )}
                    </div>
                  )
                ) : (
                  <div className="flex flex-wrap items-center gap-2.5">
                    <button
                      onClick={handleDownload}
                      className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-black px-5 py-3 rounded-xl text-xs transition-all shadow-md shadow-emerald-500/20"
                    >
                      <Download className="w-4 h-4" />
                      <span>{downloadSuccess ? '¡Descargado!' : 'Descargar Master WAV + Stems'}</span>
                    </button>

                    <button
                      onClick={() => setCertificateModalOpen(true)}
                      className="flex items-center gap-2 bg-[#161a29] hover:bg-[#1e2338] text-amber-300 border border-amber-400/30 font-bold px-4 py-3 rounded-xl text-xs transition-colors"
                    >
                      <FileText className="w-4 h-4 text-amber-400" />
                      <span>Ver Certificado de Licencia Oficial</span>
                    </button>
                  </div>
                )}

                <button
                  onClick={() => toggleLike(track.id)}
                  className={`flex items-center gap-2 px-4 py-3 rounded-xl border text-xs font-bold transition-colors ${
                    isLiked
                      ? 'border-rose-500/50 bg-rose-500/10 text-rose-400'
                      : 'border-zinc-800 bg-[#151926] text-zinc-300 hover:text-white'
                  }`}
                >
                  <Heart className={`w-3.5 h-3.5 ${isLiked ? 'fill-current' : ''}`} />
                  <span>{track.likesCount} Likes</span>
                </button>
              </div>

              {/* Security & Sweet Spot (Punto Medio) Explainer Banner */}
              {!isPurchased && !track.isFree && track.price > 0 && (
                <div className="mt-3.5 p-3.5 rounded-2xl bg-gradient-to-r from-amber-500/10 via-[#141724] to-[#121522] border border-amber-500/25 text-xs text-zinc-300 space-y-2">
                  <div className="flex items-center gap-2 text-amber-300 font-bold font-mono">
                    <Scale className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    <span>El Punto Medio BeatsCloud (Practicalidad vs Seguridad):</span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-zinc-300">
                    <strong>1. Para cantar y probar:</strong> Descarga la <em>Maqueta de Composición</em> para grabar tus voces en tu DAW o teléfono y comprobar si tu estilo calza con el beat.<br />
                    <strong>2. Para distribución comercial:</strong> Adquiere la <em>Licencia Comercial</em> para desbloquear el master en WAV 24-bit sin marcas, los Stems separados y el <strong>Certificado Oficial con Hash para SCD y Spotify</strong>.
                  </p>
                </div>
              )}

              {isPurchased && (
                <div className="mt-3.5 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <span>
                      <strong>Licencia Master Adquirida:</strong> Tienes acceso perpetuo a descargar WAV 24-bit, Stems multitrack y tu Cédula Oficial de Licencia comercial.
                    </span>
                  </div>
                  <button
                    onClick={() => setCertificateModalOpen(true)}
                    className="text-xs font-mono font-bold text-amber-400 hover:text-amber-300 underline flex-shrink-0"
                  >
                    Ver Contrato
                  </button>
                </div>
              )}

              {(track.isFree || track.price === 0) && !isPurchased && (
                <div className="mt-3.5 p-3 rounded-xl bg-sky-500/10 border border-sky-500/20 text-xs text-sky-200 flex items-center gap-2.5">
                  <Sparkles className="w-4 h-4 text-sky-400 flex-shrink-0" />
                  <span>
                    <strong>Pista Gratuita:</strong> Puedes utilizar esta instrumental libremente para ensayos, demos y proyectos sin fines de lucro acreditando a <strong>{track.producerName}</strong>.
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Interactive Live Waveform scrubber bar inside modal */}
          <div className="mt-6 pt-5 border-t border-[#1b2030]">
            <div className="flex items-center justify-between text-xs text-zinc-400 font-mono mb-2">
              <span className="font-bold text-amber-400">
                {isThisPlaying ? 'Reproduciendo vista previa en vivo' : 'Haz clic para escuchar'}
              </span>
              <span>
                {formatTime(isThisPlaying ? currentTime : 0)} / {formatTime(track.duration)}
              </span>
            </div>

            <div className="flex items-center gap-1 h-12 bg-black/50 rounded-xl px-4 border border-[#1f2538]">
              {Array.from({ length: 48 }).map((_, i) => {
                const isActive = isThisPlaying && (currentTime / (track.duration || 180)) * 48 > i;
                const dynamicHeight = isThisPlaying
                  ? Math.sin(currentTime * 3 + i * 0.4) * 35 + 45
                  : Math.sin(i * 0.5) * 20 + 35;

                return (
                  <button
                    key={i}
                    onClick={() => {
                      if (!isThisPlaying) playTrack(track);
                      seekAudio((i / 48) * (track.duration || 180));
                    }}
                    className="flex-1 h-full flex items-center justify-center focus:outline-none group py-1"
                    title={`Ir al ${Math.round((i / 48) * 100)}%`}
                  >
                    <div
                      className={`w-full rounded-full transition-all duration-150 ${
                        isActive
                          ? 'bg-amber-400 group-hover:bg-amber-300'
                          : 'bg-zinc-700 group-hover:bg-zinc-500'
                      }`}
                      style={{ height: `${Math.max(15, dynamicHeight)}%` }}
                    />
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 sm:p-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left Column: Description & Specs */}
          <div className="md:col-span-2 space-y-5">
            <div>
              <h3 className="text-sm font-bold text-white mb-2 font-mono uppercase">
                Descripción & Características
              </h3>
              <p className="text-xs text-zinc-300 leading-relaxed bg-[#121520] p-4 rounded-xl border border-[#1b2030]">
                {track.description}
              </p>
            </div>

            {/* Technical Specs */}
            <div>
              <h3 className="text-sm font-bold text-white mb-3 font-mono uppercase">
                Ficha Técnica
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="bg-[#121520] p-3 rounded-xl border border-[#1b2030]">
                  <span className="text-[10px] text-zinc-400 block font-mono font-semibold">TEMPO</span>
                  <span className="text-xs font-bold text-white font-mono">{track.bpm} BPM</span>
                </div>
                <div className="bg-[#121520] p-3 rounded-xl border border-[#1b2030]">
                  <span className="text-[10px] text-zinc-400 block font-mono font-semibold">TONALIDAD</span>
                  <span className="text-xs font-bold text-white font-mono">{track.scaleKey}</span>
                </div>
                <div className="bg-[#121520] p-3 rounded-xl border border-[#1b2030]">
                  <span className="text-[10px] text-zinc-400 block font-mono font-semibold">MOOD</span>
                  <span className="text-xs font-bold text-white">{track.mood || 'Oscuro'}</span>
                </div>
                <div className="bg-[#121520] p-3 rounded-xl border border-[#1b2030]">
                  <span className="text-[10px] text-zinc-400 block font-mono font-semibold">STEMS</span>
                  <span className="text-xs font-bold text-amber-400">
                    {track.hasStems ? 'Incluidos' : 'No'}
                  </span>
                </div>
              </div>
            </div>

            {/* Comments Thread */}
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-3 font-mono uppercase">
                <MessageSquare className="w-3.5 h-3.5 text-amber-400" />
                <span>Comentarios ({track.comments.length})</span>
              </h3>

              <form onSubmit={handleSendComment} className="flex gap-2 mb-3">
                <input
                  type="text"
                  placeholder={
                    currentUser
                      ? 'Escribe tu comentario sobre este beat...'
                      : 'Inicia sesión para comentar'
                  }
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  disabled={!currentUser}
                  className="flex-1 bg-[#121520] border border-[#23283b] rounded-xl px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-400 disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={!currentUser || !commentText.trim()}
                  className="bg-amber-400 hover:bg-amber-300 disabled:opacity-50 text-zinc-950 font-bold px-3 py-2 rounded-xl text-xs transition-colors flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Publicar</span>
                </button>
              </form>

              <div className="space-y-2">
                {track.comments.length === 0 ? (
                  <p className="text-xs text-zinc-500 italic py-2">
                    Aún no hay comentarios. ¡Sé el primero en opinar!
                  </p>
                ) : (
                  track.comments.map((comm) => (
                    <div
                      key={comm.id}
                      className="bg-[#121520] p-3 rounded-xl border border-[#1b2030] flex items-start justify-between gap-3"
                    >
                      <div className="flex items-start gap-2.5">
                        <img
                          src={comm.userAvatar}
                          alt={comm.username}
                          className="w-7 h-7 rounded-full object-cover ring-1 ring-zinc-700"
                        />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-white">@{comm.username}</span>
                            <span className="text-[10px] text-zinc-500">{comm.createdAt}</span>
                          </div>
                          <p className="text-xs text-zinc-300 mt-0.5">{comm.content}</p>
                        </div>
                      </div>

                      {currentUser?.id === comm.userId && (
                        <button
                          onClick={() => deleteComment(track.id, comm.id)}
                          className="text-zinc-500 hover:text-rose-400 transition-colors p-1"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Producer Mini Card */}
          <div>
            <div className="bg-[#121520] p-5 rounded-2xl border border-[#1b2030] sticky top-4">
              <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest block mb-3 font-mono">
                Productor Verificado
              </span>

              <div className="flex items-center gap-3 mb-3">
                <img
                  src={producer?.avatarUrl || track.producerAvatar}
                  alt={track.producerName}
                  className="w-12 h-12 rounded-xl object-cover ring-2 ring-amber-400/40"
                />
                <div>
                  <h4 className="font-bold text-white text-sm leading-tight">
                    {track.producerName}
                  </h4>
                  <p className="text-xs text-zinc-400">@{track.producerUsername}</p>
                </div>
              </div>

              <p className="text-xs text-zinc-300 leading-relaxed mb-4">
                {producer?.bio || 'Productor independiente en BeatsCloud.'}
              </p>

              <button
                onClick={() => {
                  onClose();
                  onOpenProducerProfile(track.producerId);
                }}
                className="w-full bg-zinc-800 hover:bg-zinc-700 text-white font-bold py-2 px-3 rounded-xl text-xs transition-colors border border-zinc-700 text-center block"
              >
                Ver Catálogo del Productor
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Official License Certificate Modal */}
      <LicenseCertificateModal
        isOpen={certificateModalOpen}
        onClose={() => setCertificateModalOpen(false)}
        contract={generateLicenseForTrack(track)}
      />
    </div>
  );
};
