import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { User, Track } from '../types';
import { getResourceBadgeInfo } from '../utils/resourceHelpers';
import {
  Play,
  Pause,
  Download,
  Heart,
  Music,
  FileMusic,
  ExternalLink,
  Edit3,
  CheckCircle,
  FileAudio,
  FileText,
} from 'lucide-react';
import { LicenseCertificateModal } from './LicenseCertificateModal';
import { LicenseContract } from '../types';

interface ArtistProfilePageProps {
  artistId?: string;
  initialTab?: 'compras' | 'favoritos' | 'membresias';
  onOpenTrackDetail: (trackId: string) => void;
  onNavigateCatalog: () => void;
}

export const ArtistProfilePage: React.FC<ArtistProfilePageProps> = ({
  artistId,
  initialTab = 'compras',
  onOpenTrackDetail,
  onNavigateCatalog,
}) => {
  const {
    currentUser,
    users,
    tracks,
    subscriptions,
    purchases,
    playTrack,
    activeTrack,
    isPlaying,
    updateProfile,
    getContractForPurchase,
    generateLicenseForTrack,
  } = useApp();

  const [activeTab, setActiveTab] = useState<'compras' | 'favoritos' | 'membresias'>(initialTab);
  const [isEditingBio, setIsEditingBio] = useState(false);
  const [editedBio, setEditedBio] = useState('');
  const [viewingContract, setViewingContract] = useState<LicenseContract | null>(null);

  const targetUser: User = artistId
    ? users.find((u) => u.id === artistId) || (currentUser as User)
    : (currentUser as User);

  const isOwner = currentUser?.id === targetUser.id;

  const purchasedTracks = tracks.filter((t) => targetUser.purchasedTrackIds.includes(t.id));
  const likedTracks = tracks.filter((t) => targetUser.likedTrackIds.includes(t.id));
  const activeSubs = subscriptions.filter((s) => targetUser.subscriptions?.includes(s.id));

  const handleSaveBio = () => {
    updateProfile({ bio: editedBio });
    setIsEditingBio(false);
  };

  const handleDownload = (track: Track) => {
    const blob = new Blob(
      [
        `BeatsCloud License & Stems Certificate\nTrack: ${track.title}\nProducer: ${track.producerName}\nBPM: ${track.bpm}\nKey: ${track.scaleKey}\nPurchased by: ${targetUser.artistName}\nLicense: Full Commercial Rights (Unlimited Distribution)`,
      ],
      { type: 'text/plain' }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${track.title.replace(/[\s/]/g, '_')}_Licencia_BeatsCloud.txt`;
    a.click();
  };

  return (
    <div className="pb-36 max-w-7xl mx-auto space-y-6">
      {/* Banner */}
      <div className="relative h-56 sm:h-72 rounded-3xl overflow-hidden shadow-xl border border-[#1b2030]">
        <img
          src={targetUser.bannerUrl}
          alt={targetUser.artistName}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#0a0c10] via-[#0a0c10]/60 to-transparent" />
      </div>

      {/* Profile Card */}
      <div className="relative -mt-16 px-4 sm:px-6">
        <div className="bg-[#0e111a] border border-[#1f2538] rounded-3xl p-6 sm:p-7 shadow-2xl flex flex-col md:flex-row items-center md:items-end justify-between gap-6">
          <div className="flex flex-col sm:flex-row items-center sm:items-end gap-5 text-center sm:text-left">
            <img
              src={targetUser.avatarUrl}
              alt={targetUser.artistName}
              className="w-24 h-24 sm:w-32 sm:h-32 rounded-2xl object-cover ring-4 ring-emerald-400 shadow-2xl"
            />
            <div>
              <div className="flex items-center justify-center sm:justify-start gap-2 mb-1">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider bg-emerald-400/20 text-emerald-400 border border-emerald-400/30 px-2 py-0.5 rounded-md">
                  Artista / Cantante
                </span>
                <span className="text-xs text-zinc-400 font-mono">@{targetUser.username}</span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight mb-1">
                {targetUser.artistName || targetUser.username}
              </h1>

              {!isEditingBio ? (
                <p className="text-xs text-zinc-300 max-w-xl leading-relaxed">
                  {targetUser.bio || 'Sin biografía disponible aún.'}
                </p>
              ) : (
                <div className="mt-2 space-y-2">
                  <textarea
                    value={editedBio}
                    onChange={(e) => setEditedBio(e.target.value)}
                    rows={3}
                    className="w-full bg-[#141724] border border-zinc-700 rounded-xl p-3 text-xs text-white"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={handleSaveBio}
                      className="px-3 py-1 bg-amber-400 text-zinc-950 font-bold rounded-lg text-xs"
                    >
                      Guardar
                    </button>
                    <button
                      onClick={() => setIsEditingBio(false)}
                      className="px-3 py-1 bg-zinc-800 text-zinc-300 rounded-lg text-xs"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {isOwner && (
            <button
              onClick={() => {
                setEditedBio(targetUser.bio);
                setIsEditingBio(!isEditingBio);
              }}
              className="bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-bold px-3.5 py-2 rounded-xl text-xs border border-zinc-700 transition-colors flex items-center gap-1.5"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>Editar Bio</span>
            </button>
          )}
        </div>

        {/* Stats Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-4">
          <div className="bg-[#0e111a] p-3.5 rounded-2xl border border-[#1b2030]">
            <span className="text-[10px] text-zinc-400 block font-mono font-semibold">PISTAS COMPRADAS</span>
            <span className="text-xl font-black text-amber-400 font-mono">{purchasedTracks.length}</span>
          </div>
          <div className="bg-[#0e111a] p-3.5 rounded-2xl border border-[#1b2030]">
            <span className="text-[10px] text-zinc-400 block font-mono font-semibold">FAVORITOS GUARDADOS</span>
            <span className="text-xl font-black text-rose-400 font-mono">{likedTracks.length}</span>
          </div>
          <div className="bg-[#0e111a] p-3.5 rounded-2xl border border-[#1b2030]">
            <span className="text-[10px] text-zinc-400 block font-mono font-semibold">MEMBRESÍAS ACTIVAS</span>
            <span className="text-xl font-black text-emerald-400 font-mono">{activeSubs.length}</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[#1b2030] mt-8 gap-6 text-xs font-mono font-bold">
          <button
            onClick={() => setActiveTab('compras')}
            className={`pb-3 transition-all relative ${
              activeTab === 'compras' ? 'text-amber-400' : 'text-zinc-400 hover:text-white'
            }`}
          >
            <span>BIBLIOTECA & DESCARGAS ({purchasedTracks.length})</span>
            {activeTab === 'compras' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400 rounded-full" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('favoritos')}
            className={`pb-3 transition-all relative ${
              activeTab === 'favoritos' ? 'text-amber-400' : 'text-zinc-400 hover:text-white'
            }`}
          >
            <span>BEATS GUARDADOS ({likedTracks.length})</span>
            {activeTab === 'favoritos' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400 rounded-full" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('membresias')}
            className={`pb-3 transition-all relative ${
              activeTab === 'membresias' ? 'text-amber-400' : 'text-zinc-400 hover:text-white'
            }`}
          >
            <span>MEMBRESÍAS VIP ({activeSubs.length})</span>
            {activeTab === 'membresias' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400 rounded-full" />
            )}
          </button>
        </div>

        {/* Tab 1: Purchased Tracks */}
        {activeTab === 'compras' && (
          <div className="mt-6 space-y-3">
            {purchasedTracks.length === 0 ? (
              <div className="bg-[#0e111a] border border-[#1b2030] rounded-2xl p-10 text-center">
                <FileMusic className="w-8 h-8 text-zinc-500 mx-auto mb-2" />
                <p className="text-sm font-bold text-zinc-300">Aún no has adquirido pistas</p>
                <p className="text-xs text-zinc-500 mt-1 mb-4">
                  Las compras quedan registradas en tu biblioteca con acceso perpetuo a stems.
                </p>
                <button
                  onClick={onNavigateCatalog}
                  className="px-4 py-2 bg-amber-400 text-zinc-950 font-bold rounded-xl text-xs hover:bg-amber-300"
                >
                  Explorar Catálogo
                </button>
              </div>
            ) : (
              purchasedTracks.map((track) => {
                const isThisPlaying = isPlaying && activeTrack?.id === track.id;
                const badge = getResourceBadgeInfo(track.resourceType);

                return (
                  <div
                    key={track.id}
                    className="bg-[#0e111a] border border-[#1b2030] hover:border-amber-400/30 rounded-2xl p-3.5 flex items-center justify-between gap-4 transition-all"
                  >
                    <div className="flex items-center gap-3.5 min-w-0">
                      <div className="relative w-12 h-12 rounded-xl overflow-hidden flex-shrink-0 group">
                        <img
                          src={track.coverUrl}
                          alt={track.title}
                          className="w-full h-full object-cover"
                        />
                        <button
                          onClick={() => playTrack(track)}
                          className="absolute inset-0 m-auto w-7 h-7 rounded-full bg-amber-400 text-zinc-950 flex items-center justify-center opacity-90 group-hover:opacity-100"
                        >
                          {isThisPlaying ? (
                            <Pause className="w-3.5 h-3.5 fill-current" />
                          ) : (
                            <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
                          )}
                        </button>
                      </div>

                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-[9px] font-mono font-bold uppercase px-1.5 py-0.2 rounded border ${badge.badgeClass}`}
                          >
                            {badge.label}
                          </span>
                          <span className="text-[11px] font-mono text-zinc-400">
                            {track.bpm} BPM · {track.scaleKey}
                          </span>
                        </div>
                        <h4
                          onClick={() => onOpenTrackDetail(track.id)}
                          className="font-bold text-white text-sm hover:text-amber-400 cursor-pointer truncate mt-0.5"
                        >
                          {track.title}
                        </h4>
                        <p className="text-[11px] text-zinc-400">
                          Productor: <span className="text-zinc-200">{track.producerName}</span>
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        onClick={() => {
                          const purchase = purchases.find((p) => p.trackId === track.id && p.userId === targetUser.id);
                          if (purchase) {
                            setViewingContract(getContractForPurchase(purchase));
                          } else {
                            setViewingContract(generateLicenseForTrack(track));
                          }
                        }}
                        className="flex items-center gap-1.5 bg-[#181d2c] hover:bg-[#22283d] text-amber-300 border border-amber-400/30 font-bold px-3 py-2 rounded-xl text-xs transition-colors shadow-sm"
                        title="Ver Cédula Oficial de Licencia comercial emitida para esta obra"
                      >
                        <FileText className="w-3.5 h-3.5 text-amber-400" />
                        <span>Ver Contrato</span>
                      </button>

                      <button
                        onClick={() => handleDownload(track)}
                        className="flex items-center gap-1.5 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-black px-3.5 py-2 rounded-xl text-xs transition-colors shadow-sm"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Descargar WAV + Stems</span>
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Tab 2: Liked Tracks */}
        {activeTab === 'favoritos' && (
          <div className="mt-6 space-y-3">
            {likedTracks.length === 0 ? (
              <div className="bg-[#0e111a] border border-[#1b2030] rounded-2xl p-8 text-center text-xs text-zinc-400">
                No tienes beats guardados en favoritos todavía.
              </div>
            ) : (
              likedTracks.map((track) => (
                <div
                  key={track.id}
                  className="bg-[#0e111a] border border-[#1b2030] rounded-2xl p-3.5 flex items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <img
                      src={track.coverUrl}
                      alt={track.title}
                      className="w-10 h-10 rounded-lg object-cover"
                    />
                    <div className="min-w-0">
                      <h4
                        onClick={() => onOpenTrackDetail(track.id)}
                        className="font-bold text-white text-xs hover:text-amber-400 cursor-pointer truncate"
                      >
                        {track.title}
                      </h4>
                      <p className="text-[11px] text-zinc-400 truncate">{track.producerName}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono font-bold text-amber-400">
                      ${track.price.toLocaleString('es-CL')}
                    </span>
                    <button
                      onClick={() => onOpenTrackDetail(track.id)}
                      className="px-2.5 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-xs font-semibold"
                    >
                      Ver Detalle
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Tab 3: Subscriptions */}
        {activeTab === 'membresias' && (
          <div className="mt-6 space-y-3">
            {activeSubs.length === 0 ? (
              <div className="bg-[#0e111a] border border-[#1b2030] rounded-2xl p-8 text-center text-xs text-zinc-400">
                No tienes suscripciones activas a productores.
              </div>
            ) : (
              activeSubs.map((sub) => (
                <div
                  key={sub.id}
                  className="bg-[#0e111a] border border-emerald-500/30 rounded-2xl p-4 flex items-center justify-between gap-4"
                >
                  <div>
                    <span className="text-[9px] font-mono font-black uppercase text-emerald-400">
                      Membresía Activa
                    </span>
                    <h4 className="text-base font-black text-white">{sub.title}</h4>
                    <p className="text-xs text-zinc-400 font-mono">
                      ${sub.price.toLocaleString('es-CL')} CLP / {sub.period}
                    </p>
                  </div>
                  <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 rounded-lg text-xs font-bold">
                    ✓ Activa
                  </span>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
