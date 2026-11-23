import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { User, Track, ProducerSubscription } from '../types';
import { PaymentMethodsNotice } from './PaymentMethodsNotice';
import { ProfileEditForm } from './ProfileEditForm';
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
    configuredMode,
    createSubscription,
    updateSubscription,
    purchaseSubscription,
  } = useApp();

  const [activeTab, setActiveTab] = useState<'beats' | 'suscripciones' | 'ventas'>(initialTab);
  const [isEditingBio, setIsEditingBio] = useState(false);
  const [subSuccess, setSubSuccess] = useState<string | null>(null);
  const [newPlanTitle, setNewPlanTitle] = useState('');
  const [newPlanPrice, setNewPlanPrice] = useState('');
  const [newPlanDescription, setNewPlanDescription] = useState('');
  const [newPlanBenefits, setNewPlanBenefits] = useState('');
  const [newPlanDuration, setNewPlanDuration] = useState('1');
  const [newPlanUnit, setNewPlanUnit] = useState<'meses' | 'anios'>('meses');
  const [editingPlanId, setEditingPlanId] = useState<string | null>(null);
  const [planNotice, setPlanNotice] = useState<string | null>(null);
  const [subscriptionError, setSubscriptionError] = useState<string | null>(null);
  const [isSavingPlan, setIsSavingPlan] = useState(false);
  const [isProcessingSubscription, setIsProcessingSubscription] = useState(false);

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

  const handleSaveProfile = async (data: Parameters<typeof updateProfile>[0]) => {
    await updateProfile(data);
    setIsEditingBio(false);
  };

  const handleSubscribe = async (sub: ProducerSubscription) => {
    if (!currentUser || currentUser.role !== 'artista') {
      setSubscriptionError('Inicia sesión como artista para contratar un plan.');
      return;
    }

    if (sub.active === false) {
      setSubscriptionError('Este plan ya no está disponible.');
      return;
    }

    setSubscriptionError(null);
    if (configuredMode === 'hybrid') {
      if (isProcessingSubscription) return;

      setIsProcessingSubscription(true);

      try {
        const result = await purchaseSubscription(sub);

        if (result.status === 'error') {
          setSubscriptionError(result.message);
        }
      } catch (error) {
        setSubscriptionError(
          error instanceof Error
            ? error.message
            : 'No fue posible iniciar el pago con Webpay.'
        );
      } finally {
        setIsProcessingSubscription(false);
      }

      return;
    }
    const ok = subscribeToProducer(sub);
    if (ok) {
      setSubSuccess(sub.id);
      setTimeout(() => setSubSuccess(null), 3000);
    }
  };

  const resetPlanForm = () => {
    setEditingPlanId(null);
    setNewPlanTitle('');
    setNewPlanPrice('');
    setNewPlanDescription('');
    setNewPlanBenefits('');
    setNewPlanDuration('1');
    setNewPlanUnit('meses');
  };

  const handleEditPlan = (sub: ProducerSubscription) => {
    setEditingPlanId(sub.id);
    setNewPlanTitle(sub.title);
    setNewPlanPrice(String(sub.price));
    setNewPlanDescription(sub.description ?? '');
    setNewPlanBenefits(sub.benefits.join('\n'));
    setNewPlanDuration(String(sub.durationCount ?? 1));
    setNewPlanUnit(sub.durationUnit ?? 'meses');
    setSubscriptionError(null);
    setPlanNotice(null);

    document.getElementById('subscription-plan-form')
      ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const handleCreatePlan = async (event: React.FormEvent) => {
    event.preventDefault();

    if (isSavingPlan || !isOwner || currentUser?.role !== 'productor') return;

    const price = Number(newPlanPrice);
    const duration = Number(newPlanDuration);
    const benefits = newPlanBenefits
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean);

    if (!newPlanTitle.trim() || !Number.isInteger(price) || price < 1 || price > 99999999) {
      setSubscriptionError('Ingresa un nombre y un precio válido en CLP.');
      return;
    }

    const maxDuration = newPlanUnit === 'meses' ? 12 : 5;

    if (!Number.isInteger(duration) || duration < 1 || duration > maxDuration) {
      setSubscriptionError('Selecciona una duración válida.');
      return;
    }

    if (benefits.length > 10 || benefits.some((item) => item.length > 200)) {
      setSubscriptionError('Agrega hasta 10 beneficios de máximo 200 caracteres cada uno.');
      return;
    }

    setIsSavingPlan(true);
    setSubscriptionError(null);
    setPlanNotice(null);

    const details = {
      descripcion: newPlanDescription.trim(),
      beneficios: benefits,
      duracion_cantidad: duration,
      duracion_unidad: newPlanUnit,
    };

    try {
      if (editingPlanId) {
        await updateSubscription(editingPlanId, {
          detalle: newPlanTitle.trim(),
          precio: price,
          ...details,
        });

        setPlanNotice('Plan actualizado correctamente.');
      } else {
        await createSubscription(newPlanTitle.trim(), price, details);
        setPlanNotice('Plan publicado correctamente.');
      }

      resetPlanForm();
    } catch (error) {
      setSubscriptionError(
        error instanceof Error ? error.message : 'No se pudo guardar el plan.'
      );
    } finally {
      setIsSavingPlan(false);
    }
  };

  const handleTogglePlan = async (sub: ProducerSubscription) => {
    if (isSavingPlan || !isOwner || currentUser?.role !== 'productor') return;

    const nextActive = sub.active === false;

    setIsSavingPlan(true);
    setSubscriptionError(null);
    setPlanNotice(null);

    try {
      await updateSubscription(sub.id, { activo: nextActive });

      setPlanNotice(nextActive
        ? 'Plan reactivado correctamente.'
        : 'Plan desactivado. Las membresías vigentes conservarán su duración.');
    } catch (error) {
      setSubscriptionError(
        error instanceof Error ? error.message : 'No se pudo actualizar el plan.'
      );
    } finally {
      setIsSavingPlan(false);
    }
  };

  const durationLabel = (count: number, unit: string) => {
    const label = unit === 'anios'
      ? (count === 1 ? 'año' : 'años')
      : unit === 'dias'
        ? (count === 1 ? 'día' : 'días')
        : (count === 1 ? 'mes' : 'meses');

    return `${count} ${label}`;
  };

  const planFieldClass = 'w-full rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white';

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
                <ProfileEditForm
                  user={targetUser}
                  onSave={handleSaveProfile}
                  onCancel={() => setIsEditingBio(false)}
                />
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
                    setIsEditingBio(!isEditingBio);
                  }}
                  className="bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-bold px-4 py-2.5 rounded-xl text-xs border border-zinc-700 transition-colors flex items-center gap-2"
                >
                  <Edit3 className="w-4 h-4" />
                  <span>Editar Perfil</span>
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
            <span className="text-xs text-zinc-400 block font-semibold">Ventas registradas</span>
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
                        <p className="mt-1 max-w-2xl text-xs leading-relaxed text-zinc-400 whitespace-pre-wrap break-words">
                          {track.description?.trim() || 'Este track no tiene descripción.'}
                        </p>
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
            {isOwner && configuredMode === 'hybrid' && currentUser?.role === 'productor' && (
              <form
                id="subscription-plan-form"
                onSubmit={handleCreatePlan}
                className="col-span-full rounded-2xl border border-zinc-800 bg-[#14151f] p-6 space-y-4"
              >
                <h3 className="text-lg font-bold text-white">
                  {editingPlanId ? 'Editar plan de suscripción' : 'Crear plan de suscripción'}
                </h3>

                <p className="text-xs text-zinc-400">
                  Define tus servicios, beneficios y duración. El precio corresponde al período completo.
                </p>

                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="space-y-2 text-xs text-zinc-300">
                    <span>Nombre del plan</span>
                    <input
                      required
                      value={newPlanTitle}
                      onChange={(e) => setNewPlanTitle(e.target.value)}
                      maxLength={200}
                      placeholder="Producción musical VIP"
                      className={planFieldClass}
                    />
                  </label>

                  <label className="space-y-2 text-xs text-zinc-300">
                    <span>Precio total (CLP)</span>
                    <input
                      required
                      type="number"
                      min="1"
                      max="99999999"
                      step="1"
                      value={newPlanPrice}
                      onChange={(e) => setNewPlanPrice(e.target.value)}
                      placeholder="45000"
                      className={planFieldClass}
                    />
                  </label>

                  <label className="space-y-2 text-xs text-zinc-300">
                    <span>Unidad de duración</span>
                    <select
                      value={newPlanUnit}
                      onChange={(e) => {
                        setNewPlanUnit(e.target.value as 'meses' | 'anios');
                        setNewPlanDuration('1');
                      }}
                      className={planFieldClass}
                    >
                      <option value="meses">Meses</option>
                      <option value="anios">Años</option>
                    </select>
                  </label>

                  <label className="space-y-2 text-xs text-zinc-300">
                    <span>Cantidad</span>
                    <select
                      value={newPlanDuration}
                      onChange={(e) => setNewPlanDuration(e.target.value)}
                      className={planFieldClass}
                    >
                      {Array.from(
                        { length: newPlanUnit === 'meses' ? 12 : 5 },
                        (_, i) => i + 1
                      ).map((count) => (
                        <option key={count} value={count}>
                          {durationLabel(count, newPlanUnit)}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <label className="block space-y-2 text-xs text-zinc-300">
                  <span>Descripción del servicio</span>
                  <textarea
                    value={newPlanDescription}
                    onChange={(e) => setNewPlanDescription(e.target.value)}
                    maxLength={1000}
                    rows={3}
                    placeholder="Describe el servicio que ofrecerás al artista..."
                    className={planFieldClass}
                  />
                </label>

                <label className="block space-y-2 text-xs text-zinc-300">
                  <span>Beneficios incluidos (uno por línea, máximo 10)</span>
                  <textarea
                    value={newPlanBenefits}
                    onChange={(e) => setNewPlanBenefits(e.target.value)}
                    rows={4}
                    placeholder={'Mezcla profesional\nMasterización\nAsesoría musical'}
                    className={planFieldClass}
                  />
                </label>

                <div className="flex flex-wrap gap-3">
                  <button
                    type="submit"
                    disabled={isSavingPlan}
                    className="rounded-xl bg-amber-400 px-5 py-3 text-xs font-black text-zinc-950 disabled:opacity-50"
                  >
                    {isSavingPlan ? 'Guardando...' : editingPlanId ? 'Guardar cambios' : 'Publicar plan'}
                  </button>

                  {editingPlanId && (
                    <button
                      type="button"
                      onClick={resetPlanForm}
                      disabled={isSavingPlan}
                      className="rounded-xl bg-zinc-800 px-5 py-3 text-xs text-white"
                    >
                      Cancelar edición
                    </button>
                  )}
                </div>
              </form>
            )}

            {subscriptionError && (
              <p role="alert" className="col-span-full rounded-xl bg-rose-500/10 p-3 text-sm text-rose-400">
                {subscriptionError}
              </p>
            )}

            {planNotice && (
              <p role="status" className="col-span-full rounded-xl bg-emerald-500/10 p-3 text-sm text-emerald-400">
                {planNotice}
              </p>
            )}

            {producerSubscriptions.length === 0 ? (
              <div className="col-span-full bg-[#14151f] border border-zinc-800 rounded-2xl p-10 text-center text-sm text-zinc-400">
                Este productor no tiene planes de suscripción disponibles.
              </div>
            ) : (
              producerSubscriptions.map((sub) => {
                const membership = currentUser?.subscriptionPeriods?.[sub.id];
                const isSubscribed = membership
                  ? membership.active && Date.parse(membership.expires_at) > Date.now()
                  : Boolean(currentUser?.subscriptions?.includes(sub.id));

                const planActive = sub.active !== false;
                const count = sub.durationCount ?? 1;
                const unit = sub.durationUnit ?? (sub.period === 'anual' ? 'anios' : 'meses');
                const canPurchase = currentUser?.role === 'artista' && planActive;

                return (
                  <div
                    key={sub.id}
                    className="bg-[#14151f] border border-amber-400/20 rounded-3xl p-6 sm:p-8 flex flex-col justify-between gap-4"
                  >
                    <div>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="text-xs font-bold uppercase text-amber-400">
                          Plan de Creador
                        </span>
                        {!planActive && (
                          <span className="rounded-full bg-zinc-800 px-3 py-1 text-xs text-zinc-400">
                            Desactivado
                          </span>
                        )}
                      </div>

                      <h3 className="text-2xl font-black text-white mt-2 mb-2">
                        {sub.title}
                      </h3>

                      <div className="text-3xl font-black text-amber-400">
                        ${sub.price.toLocaleString('es-CL')} CLP
                      </div>

                      <p className="text-sm text-zinc-400 mt-1 mb-4">
                        Pago único por {durationLabel(count, unit)}
                      </p>

                      {sub.description && (
                        <p className="text-sm text-zinc-300 whitespace-pre-wrap mb-5 break-words">
                          {sub.description}
                        </p>
                      )}

                      <ul className="space-y-3 text-sm text-zinc-300">
                        {sub.benefits.map((benefit, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <CheckCircle className="w-4 h-4 mt-0.5 text-amber-400 flex-shrink-0" />
                            <span className="break-words min-w-0">{benefit}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {membership && (
                      <div className="rounded-xl bg-zinc-900 p-4 text-xs text-zinc-300 space-y-2">
                        <p className={isSubscribed ? 'font-bold text-emerald-400' : 'font-bold text-amber-400'}>
                          {isSubscribed ? 'Tu membresía está activa' : 'Tu membresía ha vencido'}
                        </p>
                        <p>Duración contratada: {durationLabel(membership.duration_count, membership.duration_unit)}</p>
                        <p>Inicio: {new Date(membership.starts_at).toLocaleDateString('es-CL')}</p>
                        <p>Vencimiento: {new Date(membership.expires_at).toLocaleDateString('es-CL')}</p>
                      </div>
                    )}

                    {isOwner && configuredMode === 'hybrid' && (
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          type="button"
                          onClick={() => handleEditPlan(sub)}
                          disabled={isSavingPlan}
                          className="rounded-xl bg-zinc-800 py-3 text-xs font-bold text-white"
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleTogglePlan(sub)}
                          disabled={isSavingPlan}
                          className="rounded-xl border border-zinc-700 py-3 text-xs font-bold text-amber-400"
                        >
                          {planActive ? 'Desactivar' : 'Reactivar'}
                        </button>
                      </div>
                    )}

                    {!isOwner && planActive && !isSubscribed && (
                      <PaymentMethodsNotice compact />
                    )}

                    {!isOwner && (
                      <button
                        type="button"
                        onClick={() => void handleSubscribe(sub)}
                        disabled={!canPurchase || isSubscribed || isProcessingSubscription}
                        className={`w-full py-3 rounded-xl text-xs font-black transition-all disabled:cursor-not-allowed disabled:opacity-60 ${
                          isSubscribed
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : 'bg-amber-400 hover:bg-amber-300 text-zinc-950'
                        }`}
                      >
                        {isSubscribed
                          ? 'Membresía activa'
                          : !planActive
                            ? 'Plan no disponible'
                            : currentUser?.role !== 'artista'
                              ? 'Disponible para artistas'
                              : isProcessingSubscription
                                ? 'Conectando con Webpay...'
                                : subSuccess === sub.id
                                  ? 'Suscripción completada'
                                  : membership
                                    ? 'Renovar membresía'
                                    : 'Contratar servicio'}
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
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

      </div>
    </div>
  );
};
