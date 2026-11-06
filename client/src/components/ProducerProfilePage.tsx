import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { LicenseContract, User, Track } from '../types';
import { LicenseCertificateModal } from './LicenseCertificateModal';
import {
  Play,
  Pause,
  Upload,
  Trash2,
  Edit3,
  ExternalLink,
  ShieldCheck,
  Disc,
  DollarSign,
  Heart,
  Calendar,
  CheckCircle,
  FileText,
  Plus,
} from 'lucide-react';

interface ProducerProfilePageProps {
  producerId?: string;
  initialTab?: 'beats' | 'suscripciones' | 'ventas';
  onOpenTrackDetail: (trackId: string) => void;
  onOpenUploadModal: () => void;
  onEditTrack: (track: Track) => void;
}

export const ProducerProfilePage: React.FC<ProducerProfilePageProps> = ({
  producerId,
  initialTab = 'beats',
  onOpenTrackDetail,
  onOpenUploadModal,
  onEditTrack,
}) => {
  const {
    currentUser,
    users,
    tracks,
    subscriptions,
    sales,
    playTrack,
    activeTrack,
    isPlaying,
    deleteTrack,
    subscribeToProducer,
    updateProfile,
    getContractForSale,
  } = useApp();

  const [activeTab, setActiveTab] = useState<'beats' | 'suscripciones' | 'ventas'>(initialTab);
  const [isEditingBio, setIsEditingBio] = useState(false);
  const [editedBio, setEditedBio] = useState('');
  const [subSuccess, setSubSuccess] = useState<string | null>(null);
  const [viewingContract, setViewingContract] = useState<LicenseContract | null>(null);

  // Target producer
  const targetUser: User = producerId
    ? users.find((u) => u.id === producerId) || (currentUser as User)
    : (currentUser as User);

  const isOwner = currentUser?.id === targetUser.id;

  const producerTracks = tracks.filter((t) => t.producerId === targetUser.id);
  const producerSubscriptions = subscriptions.filter((s) => s.producerId === targetUser.id);
  const producerSales = sales.filter((s) => {
    const track = tracks.find((t) => t.id === s.trackId);
    return track?.producerId === targetUser.id;
  });

  const totalSalesRevenue = producerSales.reduce((sum, s) => sum + s.amount, 0);
  const totalLikes = producerTracks.reduce((sum, t) => sum + t.likesCount, 0);

  const handleSaveBio = () => {
    updateProfile({ bio: editedBio });
    setIsEditingBio(false);
  };

  const handleSubscribe = (sub: any) => {
    const ok = subscribeToProducer(sub);
    if (ok) {
      setSubSuccess(sub.id);
      setTimeout(() => setSubSuccess(null), 3000);
    }
  };

  return (
    <div className="pb-32">
      {/* Cover Banner */}
      <div className="relative h-64 sm:h-80 rounded-3xl overflow-hidden shadow-2xl border border-zinc-800">
        <img
          src={targetUser.bannerUrl}
          alt={targetUser.artistName}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#0e0f15] via-[#0e0f15]/50 to-transparent" />
      </div>

      {/* Profile Header Card */}
      <div className="relative -mt-20 px-4 sm:px-8 max-w-6xl mx-auto">
        <div className="bg-[#14151f] border border-zinc-800 rounded-3xl p-6 sm:p-8 shadow-2xl flex flex-col md:flex-row items-center md:items-end justify-between gap-6">
          <div className="flex flex-col sm:flex-row items-center sm:items-end gap-6 text-center sm:text-left">
            <img
              src={targetUser.avatarUrl}
              alt={targetUser.artistName}
              className="w-28 h-28 sm:w-36 sm:h-36 rounded-3xl object-cover ring-4 ring-amber-400 shadow-2xl"
            />
            <div>
              <div className="flex items-center justify-center sm:justify-start gap-2 mb-1">
                <span className="text-[11px] font-black uppercase tracking-wider bg-amber-400/20 text-amber-400 border border-amber-400/30 px-2.5 py-0.5 rounded-full">
                  Productor Musical
                </span>
                <span className="text-xs text-zinc-400">@{targetUser.username}</span>
              </div>

              <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-2">
                {targetUser.artistName || targetUser.username}
              </h1>

              {/* Bio */}
              {!isEditingBio ? (
                <p className="text-xs sm:text-sm text-zinc-300 max-w-xl leading-relaxed">
                  {targetUser.bio || 'Sin biografía disponible aún.'}
                </p>
              ) : (
                <div className="mt-2 space-y-2">
                  <textarea
                    value={editedBio}
                    onChange={(e) => setEditedBio(e.target.value)}
                    rows={3}
                    className="w-full bg-zinc-900 border border-zinc-700 rounded-xl p-3 text-xs text-white"
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

              {/* Social Media Links */}
              <div className="flex items-center justify-center sm:justify-start gap-3 mt-4 text-xs font-semibold text-zinc-400">
                {targetUser.spotify && (
                  <a
                    href={targetUser.spotify}
                    target="_blank"
                    rel="noreferrer"
                    className="text-emerald-400 hover:underline flex items-center gap-1"
                  >
                    <span>Spotify</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
                {targetUser.instagram && (
                  <a
                    href={targetUser.instagram}
                    target="_blank"
                    rel="noreferrer"
                    className="text-pink-400 hover:underline flex items-center gap-1"
                  >
                    <span>Instagram</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
                {targetUser.youtube && (
                  <a
                    href={targetUser.youtube}
                    target="_blank"
                    rel="noreferrer"
                    className="text-red-400 hover:underline flex items-center gap-1"
                  >
                    <span>YouTube</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-3">
            {isOwner && (
              <>
                <button
                  onClick={() => {
                    setEditedBio(targetUser.bio);
                    setIsEditingBio(!isEditingBio);
                  }}
                  className="bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-bold px-4 py-2.5 rounded-xl text-xs border border-zinc-700 transition-colors flex items-center gap-2"
                >
                  <Edit3 className="w-4 h-4" />
                  <span>Editar Bio</span>
                </button>
                <button
                  onClick={onOpenUploadModal}
                  className="bg-amber-400 hover:bg-amber-300 text-zinc-950 font-black px-5 py-2.5 rounded-xl text-xs transition-transform hover:scale-105 shadow-md shadow-amber-400/20 flex items-center gap-2"
                >
                  <Upload className="w-4 h-4" />
                  <span>Subir Beat</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
          <div className="bg-[#14151f] p-4 rounded-2xl border border-zinc-800">
            <span className="text-xs text-zinc-400 block font-semibold">Instrumentales</span>
            <span className="text-2xl font-black text-white">{producerTracks.length}</span>
          </div>
          <div className="bg-[#14151f] p-4 rounded-2xl border border-zinc-800">
            <span className="text-xs text-zinc-400 block font-semibold">Likes de Comunidad</span>
            <span className="text-2xl font-black text-rose-400 flex items-center gap-1.5">
              <Heart className="w-5 h-5 fill-current" />
              <span>{totalLikes}</span>
            </span>
          </div>
          <div className="bg-[#14151f] p-4 rounded-2xl border border-zinc-800">
            <span className="text-xs text-zinc-400 block font-semibold">Licencias Vendidas</span>
            <span className="text-2xl font-black text-amber-400">{producerSales.length}</span>
          </div>
          <div className="bg-[#14151f] p-4 rounded-2xl border border-zinc-800">
            <span className="text-xs text-zinc-400 block font-semibold">Ventas Totales</span>
            <span className="text-2xl font-black text-emerald-400">
              ${totalSalesRevenue.toLocaleString('es-CL')}
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-zinc-800 mt-10 gap-6">
          <button
            onClick={() => setActiveTab('beats')}
            className={`pb-3 text-sm font-bold transition-all relative ${
              activeTab === 'beats' ? 'text-amber-400' : 'text-zinc-400 hover:text-white'
            }`}
          >
            <span>Mis Beats ({producerTracks.length})</span>
            {activeTab === 'beats' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400 rounded-full" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('suscripciones')}
            className={`pb-3 text-sm font-bold transition-all relative ${
              activeTab === 'suscripciones' ? 'text-amber-400' : 'text-zinc-400 hover:text-white'
            }`}
          >
            <span>Membresías VIP ({producerSubscriptions.length})</span>
            {activeTab === 'suscripciones' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400 rounded-full" />
            )}
          </button>
          {isOwner && (
            <button
              onClick={() => setActiveTab('ventas')}
              className={`pb-3 text-sm font-bold transition-all relative ${
                activeTab === 'ventas' ? 'text-amber-400' : 'text-zinc-400 hover:text-white'
              }`}
            >
              <span>Historial de Ventas ({producerSales.length})</span>
              {activeTab === 'ventas' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400 rounded-full" />
              )}
            </button>
          )}
        </div>

        {/* Tab 1: Producer's Tracks */}
        {activeTab === 'beats' && (
          <div className="mt-8 space-y-4">
            {producerTracks.length === 0 ? (
              <div className="bg-[#14151f] border border-zinc-800 rounded-2xl p-10 text-center">
                <Disc className="w-10 h-10 text-zinc-500 mx-auto mb-3" />
                <p className="text-sm font-bold text-zinc-300">No hay instrumentales publicadas</p>
                {isOwner && (
                  <button
                    onClick={onOpenUploadModal}
                    className="mt-4 px-4 py-2 bg-amber-400 text-zinc-950 font-bold rounded-xl text-xs"
                  >
                    Publicar primer beat
                  </button>
                )}
              </div>
            ) : (
              producerTracks.map((track) => {
                const isThisPlaying = isPlaying && activeTrack?.id === track.id;

                return (
                  <div
                    key={track.id}
                    className="bg-[#14151f] border border-zinc-800 hover:border-amber-400/30 rounded-2xl p-4 flex items-center justify-between gap-4 transition-all"
                  >
                    <div className="flex items-center gap-4 min-w-0">
                      <div className="relative w-14 h-14 rounded-xl overflow-hidden flex-shrink-0 group">
                        <img
                          src={track.coverUrl}
                          alt={track.title}
                          className="w-full h-full object-cover"
                        />
                        <button
                          onClick={() => playTrack(track)}
                          className="absolute inset-0 m-auto w-8 h-8 rounded-full bg-amber-400 text-zinc-950 flex items-center justify-center opacity-90 group-hover:opacity-100"
                        >
                          {isThisPlaying ? (
                            <Pause className="w-4 h-4 fill-current" />
                          ) : (
                            <Play className="w-4 h-4 fill-current ml-0.5" />
                          )}
                        </button>
                      </div>

                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold uppercase text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded">
                            {track.genre}
                          </span>
                          <span className="text-xs font-mono text-zinc-500">
                            {track.bpm} BPM • {track.scaleKey}
                          </span>
                        </div>
                        <h4
                          onClick={() => onOpenTrackDetail(track.id)}
                          className="font-bold text-white text-base hover:text-amber-400 cursor-pointer truncate mt-0.5"
                        >
                          {track.title}
                        </h4>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <span className="text-base font-black text-amber-400">
                        ${track.price.toLocaleString('es-CL')} CLP
                      </span>

                      {isOwner && (
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => onEditTrack(track)}
                            className="p-2 text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-800"
                            title="Editar beat"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => deleteTrack(track.id)}
                            className="p-2 text-zinc-400 hover:text-rose-400 rounded-lg hover:bg-zinc-800"
                            title="Eliminar beat"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Tab 2: Subscriptions */}
        {activeTab === 'suscripciones' && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
            {producerSubscriptions.length === 0 ? (
              <div className="col-span-full bg-[#14151f] border border-zinc-800 rounded-2xl p-10 text-center text-sm text-zinc-400">
                Este productor no tiene planes de suscripción activos actualmente.
              </div>
            ) : (
              producerSubscriptions.map((sub) => {
                const isSubscribed = currentUser?.subscriptions?.includes(sub.id);

                return (
                  <div
                    key={sub.id}
                    className="bg-[#14151f] border border-amber-400/20 rounded-3xl p-6 sm:p-8 flex flex-col justify-between"
                  >
                    <div>
                      <span className="text-[10px] font-black uppercase text-amber-400 tracking-wider">
                        Plan de Creador
                      </span>
                      <h3 className="text-2xl font-black text-white mt-1 mb-2">{sub.title}</h3>
                      <div className="text-3xl font-black text-amber-400 mb-6">
                        ${sub.price.toLocaleString('es-CL')}{' '}
                        <span className="text-xs font-normal text-zinc-400">/ {sub.period}</span>
                      </div>

                      <ul className="space-y-3 text-xs sm:text-sm text-zinc-300 mb-6">
                        {sub.benefits.map((b, idx) => (
                          <li key={idx} className="flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                            <span>{b}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {!isOwner && (
                      <button
                        onClick={() => handleSubscribe(sub)}
                        disabled={isSubscribed}
                        className={`w-full py-3 rounded-xl text-xs font-black transition-all ${
                          isSubscribed
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : 'bg-amber-400 hover:bg-amber-300 text-zinc-950 shadow-md shadow-amber-400/20'
                        }`}
                      >
                        {isSubscribed
                          ? '✓ Membresía Activa'
                          : subSuccess === sub.id
                          ? '¡Suscrito con Éxito!'
                          : 'Suscribirse al Productor'}
                      </button>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Tab 3: Sales History */}
        {activeTab === 'ventas' && isOwner && (
          <div className="mt-8 bg-[#14151f] border border-zinc-800 rounded-2xl overflow-hidden">
            {producerSales.length === 0 ? (
              <p className="p-8 text-center text-sm text-zinc-400">
                Aún no registras ventas. Promociona tus beats en redes sociales para conseguir tus primeras compras.
              </p>
            ) : (
              <table className="w-full text-left text-xs">
                <thead className="bg-zinc-900 border-b border-zinc-800 text-zinc-400 uppercase font-mono">
                  <tr>
                    <th className="p-4">Fecha</th>
                    <th className="p-4">Track</th>
                    <th className="p-4">Comprador</th>
                    <th className="p-4">Monto</th>
                    <th className="p-4">Estado</th>
                    <th className="p-4 text-right">Licencia</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800 text-zinc-300 font-mono">
                  {producerSales.map((sale) => (
                    <tr key={sale.id} className="hover:bg-zinc-900/50">
                      <td className="p-4">{sale.date}</td>
                      <td className="p-4 font-bold text-white">{sale.trackTitle}</td>
                      <td className="p-4 text-amber-400">@{sale.buyerName}</td>
                      <td className="p-4 font-bold text-white">
                        ${sale.amount.toLocaleString('es-CL')} CLP
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold">
                          {sale.status}
                        </span>
                      </td>
                      <td className="p-4 text-right">
                        <button
                          onClick={() => setViewingContract(getContractForSale(sale))}
                          className="inline-flex items-center gap-1.5 bg-[#181d2c] hover:bg-[#22283d] text-amber-300 border border-amber-400/30 font-bold px-3 py-1.5 rounded-xl text-[10px] transition-colors"
                          title={`Ver certificado oficial de licencia ${sale.licenseCode || ''}`}
                        >
                          <FileText className="w-3 h-3 text-amber-400" />
                          <span>Certificado</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

      {/* Certificado de Licencia emitido al comprador (vista productor) */}
      <LicenseCertificateModal
        isOpen={viewingContract !== null}
        onClose={() => setViewingContract(null)}
        contract={viewingContract}
      />
      </div>
    </div>
  );
};
