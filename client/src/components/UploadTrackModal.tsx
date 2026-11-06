import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { Track, MusicGenre, ResourceType, MoodType } from '../types';
import { getResourceBadgeInfo, RESOURCE_TYPES } from '../utils/resourceHelpers';
import { analyzeAudioFile, AudioAnalysisResult } from '../utils/audioAnalyzer';
import {
  X,
  Upload,
  Sparkles,
  Music,
  Sliders,
  Check,
  Disc,
  FileAudio,
  Activity,
  Layers,
  HelpCircle,
  AlertCircle,
} from 'lucide-react';

interface UploadTrackModalProps {
  isOpen: boolean;
  onClose: () => void;
  trackToEdit?: Track | null;
}

const PRESET_COVERS = [
  'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=600&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1511192336575-5a79af67a629?w=600&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1465847899084-d164df4dedc6?w=600&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1516280440614-37939bbacd81?w=600&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1519683109079-d5f539e1542f?w=600&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=600&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1498038432885-c6f3f1b912ee?w=600&auto=format&fit=crop&q=80',
];

const SCALES = [
  'A Minor', 'A Major',
  'Bb Minor', 'Bb Major',
  'B Minor', 'B Major',
  'C Minor', 'C Major',
  'C# Minor', 'C# Major',
  'D Minor', 'D Major',
  'Eb Minor', 'Eb Major',
  'E Minor', 'E Major',
  'F Minor', 'F Major',
  'F# Minor', 'F# Major',
  'G Minor', 'G Major',
  'Ab Minor', 'Ab Major'
];

const MOODS: MoodType[] = [
  'Oscuro',
  'Enérgico',
  'Chill / Relax',
  'Triste / Nostálgico',
  'Bailable',
  'Agresivo',
];

export const UploadTrackModal: React.FC<UploadTrackModalProps> = ({
  isOpen,
  onClose,
  trackToEdit,
}) => {
  const { uploadTrack, updateTrack } = useApp();

  const [title, setTitle] = useState('');
  const [resourceType, setResourceType] = useState<ResourceType>('instrumental');
  const [genre, setGenre] = useState<MusicGenre>('Trap');
  const [subgenre, setSubgenre] = useState('Dark Latin Trap');
  const [price, setPrice] = useState<number>(18000);
  const [description, setDescription] = useState('');
  const [bpm, setBpm] = useState<number>(140);
  const [scaleKey, setScaleKey] = useState('A Minor');
  const [mood, setMood] = useState<MoodType>('Oscuro');
  const [audioBeatType, setAudioBeatType] = useState<Track['audioBeatType']>('trap');
  const [coverUrl, setCoverUrl] = useState(PRESET_COVERS[0]);

  // Stems checkboxes
  const [hasWav, setHasWav] = useState(true);
  const [hasStems, setHasStems] = useState(true);
  const [hasMidi, setHasMidi] = useState(false);
  const [isFree, setIsFree] = useState(false);
  const [hasWatermark, setHasWatermark] = useState(true);
  // "Punto medio": permitir descarga de maqueta de composición en beats de pago
  const [allowFreeDownload, setAllowFreeDownload] = useState(false);

  // Duración real detectada del archivo subido (segundos). Si no hay archivo,
  // uploadTrack usará su valor por defecto (180s) como antes.
  const [detectedDuration, setDetectedDuration] = useState<number | null>(null);

  // Fallback Audio Analyzer State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AudioAnalysisResult | null>(null);
  const [fileNameInput, setFileNameInput] = useState('');

  // Autodetección por nombre de archivo: si el productor sube un archivo real,
  // se usa su nombre como insumo del analizador de fallback.
  const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileNameInput(file.name);
    if (!title.trim()) {
      setTitle(file.name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ').trim());
    }

    // Extracción de metadatos reales del audio (duración y BPM aproximado).
    // En producción esto lo hará el backend Django con Mutagen al recibir el
    // archivo en Cloudflare R2; aquí se replica la lógica en el cliente.
    const url = URL.createObjectURL(file);
    const probe = new Audio();
    probe.preload = 'metadata';
    probe.onloadedmetadata = () => {
      URL.revokeObjectURL(url);
      if (Number.isFinite(probe.duration) && probe.duration > 0) {
        setDetectedDuration(Math.round(probe.duration));
      }
    };
    probe.onerror = () => URL.revokeObjectURL(url);
    probe.src = url;
  };

  useEffect(() => {
    if (trackToEdit) {
      setTitle(trackToEdit.title);
      setResourceType(trackToEdit.resourceType || 'instrumental');
      setGenre(trackToEdit.genre);
      setSubgenre(trackToEdit.subgenre || '');
      setPrice(trackToEdit.price);
      setDescription(trackToEdit.description);
      setBpm(trackToEdit.bpm);
      setScaleKey(trackToEdit.scaleKey);
      setMood(trackToEdit.mood || 'Oscuro');
      setAudioBeatType(trackToEdit.audioBeatType);
      setCoverUrl(trackToEdit.coverUrl);
      setHasWav(trackToEdit.hasWav);
      setHasStems(trackToEdit.hasStems);
      setHasMidi(trackToEdit.hasMidi);
      setIsFree(trackToEdit.isFree ?? trackToEdit.price === 0);
      setHasWatermark(trackToEdit.hasWatermark ?? true);
      setAllowFreeDownload(trackToEdit.allowFreeDownload ?? false);
    } else {
      setTitle('');
      setResourceType('instrumental');
      setGenre('Trap');
      setSubgenre('Dark Latin Trap');
      setPrice(18000);
      setDescription('');
      setBpm(140);
      setScaleKey('A Minor');
      setMood('Oscuro');
      setAudioBeatType('trap');
      setCoverUrl(PRESET_COVERS[0]);
      setHasWav(true);
      setHasStems(true);
      setHasMidi(false);
      setIsFree(false);
      setHasWatermark(true);
      setAllowFreeDownload(false);
      setAnalysisResult(null);
      setFileNameInput('');
      setDetectedDuration(null);
    }
  }, [trackToEdit, isOpen]);

  if (!isOpen) return null;

  // Run the fallback audio analyzer
  const handleRunAnalyzer = async () => {
    setIsAnalyzing(true);
    try {
      const name = fileNameInput.trim() || title.trim() || `${genre}_track_${bpm}bpm_${scaleKey}.wav`;
      const result = await analyzeAudioFile(name);
      setAnalysisResult(result);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleApplyAnalysis = () => {
    if (!analysisResult) return;
    setBpm(analysisResult.detectedBpm);
    setScaleKey(analysisResult.detectedKey);
    setResourceType(analysisResult.detectedType);
    setMood(analysisResult.detectedMood);
    setGenre(analysisResult.suggestedGenre);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const finalPrice = isFree ? 0 : price;

    if (trackToEdit) {
      updateTrack(trackToEdit.id, {
        title,
        resourceType,
        genre,
        subgenre,
        price: finalPrice,
        description,
        bpm,
        scaleKey,
        mood,
        audioBeatType,
        coverUrl,
        hasWav,
        hasStems,
        hasMidi,
        isFree,
        allowFreeDownload: isFree ? true : allowFreeDownload,
        hasWatermark,
        ...(detectedDuration ? { duration: detectedDuration } : {}),
      });
    } else {
      uploadTrack({
        title,
        resourceType,
        genre,
        subgenre,
        price: finalPrice,
        description,
        bpm,
        scaleKey,
        mood,
        audioBeatType,
        coverUrl,
        hasWav,
        hasStems,
        hasMidi,
        isFree,
        allowFreeDownload: isFree ? true : allowFreeDownload,
        hasWatermark,
        duration: detectedDuration ?? undefined,
      });
    }

    onClose();
  };

  const badgeInfo = getResourceBadgeInfo(resourceType);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-150">
      <div className="relative w-full max-w-3xl bg-[#0e111a] border border-[#1f2538] rounded-3xl p-6 sm:p-8 shadow-2xl overflow-y-auto max-h-[92vh]">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-zinc-400 hover:text-white p-2 rounded-full hover:bg-zinc-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3.5 mb-6">
          <div className="w-11 h-11 rounded-2xl bg-amber-400 text-zinc-950 font-black flex items-center justify-center shadow-lg shadow-amber-400/20">
            <Upload className="w-6 h-6 stroke-[2.5]" />
          </div>
          <div>
            <h2 className="text-xl font-black text-white">
              {trackToEdit ? 'Editar Pista de Audio' : 'Subir Archivo de Audio'}
            </h2>
            <p className="text-xs text-zinc-400">
              Especifica los detalles técnicos del audio para facilitar la búsqueda precisa de los artistas.
            </p>
          </div>
        </div>

        {/* Fallback Audio Detection System Card */}
        <div className="mb-6 p-4 rounded-2xl bg-[#141824] border border-[#232a40] space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5" />
                <span>Sistema de Reconocimiento Acústico (Fallback)</span>
              </span>
              <p className="text-xs text-zinc-300 mt-0.5">
                ¿No estás seguro del tempo o la tonalidad? El analizador extrae transientes y frecuencias armónicas automáticamente.
              </p>
            </div>

            <button
              type="button"
              onClick={handleRunAnalyzer}
              disabled={isAnalyzing}
              className="bg-zinc-800 hover:bg-zinc-700 text-amber-400 font-bold px-3.5 py-2 rounded-xl text-xs border border-amber-400/30 flex items-center justify-center gap-2 transition-all flex-shrink-0 disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>{isAnalyzing ? 'Analizando Audio...' : '⚡ Auto-Detectar'}</span>
            </button>
          </div>

          {/* Archivo de audio (insumo del analizador; en producción se sube a Cloudflare R2) */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <label className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[#0b0d13] border border-dashed border-zinc-600 hover:border-amber-400/60 cursor-pointer text-xs text-zinc-300 transition-colors">
              <FileAudio className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span className="font-mono truncate max-w-[220px]">
                {fileNameInput || 'Selecciona tu archivo WAV / MP3...'}
              </span>
              <input
                type="file"
                accept=".wav,.mp3,.aiff,.flac,audio/*"
                className="hidden"
                onChange={handleFileSelected}
              />
            </label>
            <input
              type="text"
              value={fileNameInput}
              onChange={(e) => setFileNameInput(e.target.value)}
              placeholder="o escribe el nombre del archivo (ej: trap_beat_140bpm_Aminor.wav)"
              className="flex-1 bg-[#0b0d13] border border-[#232a40] focus:border-amber-400 rounded-xl px-3 py-2 text-xs text-white font-mono placeholder-zinc-500 focus:outline-none"
            />
          </div>

          {/* Analysis Result Banner */}
          {analysisResult && (
            <div className="mt-3 p-3 rounded-xl bg-amber-400/10 border border-amber-400/30 text-xs animate-in fade-in duration-200">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2 font-mono">
                <span className="text-amber-300 font-bold">
                  ✓ Análisis completado ({analysisResult.confidence}% de coincidencia)
                </span>
                <span className="text-zinc-400 text-[11px]">
                  {analysisResult.harmonicSpectrum}
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-zinc-200 text-[11px] font-mono mb-2.5">
                <div className="bg-black/40 p-1.5 rounded">BPM: <strong className="text-white">{analysisResult.detectedBpm}</strong></div>
                <div className="bg-black/40 p-1.5 rounded">Tono: <strong className="text-white">{analysisResult.detectedKey}</strong></div>
                <div className="bg-black/40 p-1.5 rounded">Tipo: <strong className="text-white uppercase">{analysisResult.detectedType}</strong></div>
                <div className="bg-black/40 p-1.5 rounded">Mood: <strong className="text-white">{analysisResult.detectedMood}</strong></div>
              </div>
              <button
                type="button"
                onClick={handleApplyAnalysis}
                className="w-full py-1.5 bg-amber-400 text-zinc-950 font-bold rounded-lg text-xs hover:bg-amber-300 transition-colors"
              >
                Aplicar valores detectados al formulario
              </button>
            </div>
          )}
        </div>

        {/* Main Upload Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* 1. Resource Type Selection (Instrumental, Acapella, Loop, Drumkit) */}
          <div>
            <label className="text-xs font-bold text-zinc-300 block mb-2">
              Tipo de Contenido * <span className="text-zinc-400 font-normal">(Identificador y color en catálogo)</span>
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {RESOURCE_TYPES.map((t) => {
                const isSelected = resourceType === t.id;
                const info = getResourceBadgeInfo(t.id);
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setResourceType(t.id)}
                    className={`p-3 rounded-2xl border text-left transition-all flex flex-col justify-between ${
                      isSelected
                        ? `${info.badgeClass} ring-1 ring-amber-400`
                        : 'bg-[#121520] border-[#1e2334] text-zinc-400 hover:text-zinc-200 hover:border-zinc-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-mono font-black uppercase tracking-wider px-1.5 py-0.5 rounded bg-black/40 border border-white/10">
                        {info.badge}
                      </span>
                      {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
                    </div>
                    <div>
                      <span className="text-xs font-bold text-white block">{t.label}</span>
                      <span className="text-[10px] text-zinc-400 block line-clamp-1">
                        {t.description}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 2. Track Title */}
          <div>
            <label className="text-xs font-bold text-zinc-300 block mb-1.5">
              Título del Beat o Recurso *
            </label>
            <input
              type="text"
              required
              placeholder="Ej: Fuego Nocturno, Andes Drill Stems, Voces de Luna..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-[#121520] border border-[#232a40] focus:border-amber-400 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-400 focus:outline-none"
            />
          </div>

          {/* 3. Genre, Subgenre & Price */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-bold text-zinc-300 block mb-1.5">
                Género Principal *
              </label>
              <select
                value={genre}
                onChange={(e) => setGenre(e.target.value as MusicGenre)}
                className="w-full bg-[#121520] border border-[#232a40] focus:border-amber-400 rounded-xl px-3 py-2 text-xs text-white focus:outline-none font-medium"
              >
                <option value="Trap">Trap</option>
                <option value="Hip-Hop">Hip-Hop</option>
                <option value="Reggaeton">Reggaetón</option>
                <option value="Drill">Drill</option>
                <option value="Boom-Bap">Boom-Bap</option>
                <option value="R&B">R&B</option>
                <option value="Electronica">Electrónica</option>
                <option value="Pop">Pop</option>
                <option value="Rock">Rock</option>
                <option value="Soul">Soul</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-zinc-300 block mb-1.5">
                Subgénero / Estilo
              </label>
              <input
                type="text"
                placeholder="Dark Trap, Dembow Club, etc."
                value={subgenre}
                onChange={(e) => setSubgenre(e.target.value)}
                className="w-full bg-[#121520] border border-[#232a40] focus:border-amber-400 rounded-xl px-3 py-2 text-xs text-white placeholder-zinc-400 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-zinc-300 block mb-1.5">
                Modalidad de Precio *
              </label>
              <div className="flex gap-1.5 p-1 bg-[#121520] rounded-xl border border-[#232a40]">
                <button
                  type="button"
                  onClick={() => setIsFree(false)}
                  className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                    !isFree
                      ? 'bg-amber-400 text-zinc-950 shadow-sm'
                      : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  De Pago
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsFree(true);
                    setPrice(0);
                  }}
                  className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                    isFree
                      ? 'bg-emerald-500 text-zinc-950 font-black shadow-sm'
                      : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  Gratis ($0)
                </button>
              </div>
            </div>
          </div>

          {/* Price Value Input if paid */}
          {!isFree ? (
            <div className="p-3 rounded-2xl bg-[#121520] border border-[#232a40]">
              <label className="text-xs font-bold text-zinc-300 block mb-1">
                Precio de Licencia Comercial ($ CLP) *
              </label>
              <input
                type="number"
                min={1000}
                step={500}
                required={!isFree}
                value={price}
                onChange={(e) => setPrice(Number(e.target.value))}
                className="w-full bg-[#0b0d13] border border-[#232a40] focus:border-amber-400 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none"
                placeholder="18000"
              />
              <span className="text-[10px] text-zinc-500 mt-1 block">
                Los compradores pagarán este valor + 19% IVA a través de Webpay Plus.
              </span>
            </div>
          ) : (
            <div className="p-3 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-emerald-400 block">
                  Beat Gratuito para Artistas (Non-Profit / Demo)
                </span>
                <span className="text-[11px] text-zinc-400 block">
                  Cualquier cantante o productor podrá descargarlo sin costo para maquetar su música.
                </span>
              </div>
              <span className="text-xs font-mono font-black text-emerald-400 bg-emerald-950 px-2.5 py-1 rounded-lg border border-emerald-500/40">
                $0 CLP
              </span>
            </div>
          )}

          {/* Security & Watermark Option */}
          <div className="p-3 rounded-2xl bg-[#121520] border border-[#232a40] space-y-3">
            <label className="flex items-start gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={hasWatermark}
                onChange={(e) => setHasWatermark(e.target.checked)}
                className="rounded text-amber-400 focus:ring-amber-400 bg-zinc-900 border-zinc-700 mt-0.5"
              />
              <div>
                <span className="text-xs font-bold text-zinc-200 block">
                  Proteger preescucha con Marca de Agua Sonora (Audio Watermark)
                </span>
                <span className="text-[11px] text-zinc-400 block mt-0.5">
                  Inserta un tag de seguridad audible durante la reproducción en el catálogo para evitar que ripeen tu instrumental sin pagar la licencia.
                </span>
              </div>
            </label>

            {!isFree && (
              <div className="pt-3 border-t border-[#232a40]">
                <label className="flex items-start gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={allowFreeDownload}
                    onChange={(e) => setAllowFreeDownload(e.target.checked)}
                    className="rounded text-amber-400 focus:ring-amber-400 bg-zinc-900 border-zinc-700 mt-0.5"
                  />
                  <div>
                    <span className="text-xs font-bold text-zinc-200 block">
                      Permitir descarga de Maqueta de Composición (MP3 con marca de agua)
                    </span>
                    <span className="text-[11px] text-zinc-400 block mt-0.5">
                      El "Punto Medio BeatsCloud": los artistas podrán descargar una copia acuñada no comercial para escribir y grabar sus voces antes de comprar la Licencia Comercial.
                    </span>
                  </div>
                </label>
              </div>
            )}
          </div>

          {/* 4. Strict Music Details: BPM, Key, Mood */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-bold text-zinc-300 block mb-1.5">
                Tempo Exacto (BPM) *
              </label>
              <input
                type="number"
                min={50}
                max={220}
                required
                value={bpm}
                onChange={(e) => setBpm(Number(e.target.value))}
                className="w-full bg-[#121520] border border-[#232a40] focus:border-amber-400 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-zinc-300 block mb-1.5">
                Tonalidad / Escala *
              </label>
              <select
                value={scaleKey}
                onChange={(e) => setScaleKey(e.target.value)}
                className="w-full bg-[#121520] border border-[#232a40] focus:border-amber-400 rounded-xl px-3 py-2 text-xs text-white focus:outline-none font-mono"
              >
                {SCALES.map((scale) => (
                  <option key={scale} value={scale}>
                    {scale}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-zinc-300 block mb-1.5">
                Mood / Estado de Ánimo *
              </label>
              <select
                value={mood}
                onChange={(e) => setMood(e.target.value as MoodType)}
                className="w-full bg-[#121520] border border-[#232a40] focus:border-amber-400 rounded-xl px-3 py-2 text-xs text-white focus:outline-none"
              >
                {MOODS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* 5. Audio Stems & Included Formats */}
          <div>
            <label className="text-xs font-bold text-zinc-300 block mb-2">
              Archivos Incluidos en la Descarga
            </label>
            <div className="grid grid-cols-3 gap-3">
              <label className="flex items-center gap-2 p-2.5 rounded-xl bg-[#121520] border border-[#232a40] cursor-pointer hover:border-zinc-600 transition-colors">
                <input
                  type="checkbox"
                  checked={hasWav}
                  onChange={(e) => setHasWav(e.target.checked)}
                  className="rounded text-amber-400 focus:ring-amber-400 bg-zinc-900 border-zinc-700"
                />
                <span className="text-xs font-mono text-zinc-200">WAV 24-bit</span>
              </label>

              <label className="flex items-center gap-2 p-2.5 rounded-xl bg-[#121520] border border-[#232a40] cursor-pointer hover:border-zinc-600 transition-colors">
                <input
                  type="checkbox"
                  checked={hasStems}
                  onChange={(e) => setHasStems(e.target.checked)}
                  className="rounded text-amber-400 focus:ring-amber-400 bg-zinc-900 border-zinc-700"
                />
                <span className="text-xs font-mono text-zinc-200">Stems / Trackouts</span>
              </label>

              <label className="flex items-center gap-2 p-2.5 rounded-xl bg-[#121520] border border-[#232a40] cursor-pointer hover:border-zinc-600 transition-colors">
                <input
                  type="checkbox"
                  checked={hasMidi}
                  onChange={(e) => setHasMidi(e.target.checked)}
                  className="rounded text-amber-400 focus:ring-amber-400 bg-zinc-900 border-zinc-700"
                />
                <span className="text-xs font-mono text-zinc-200">Archivos MIDI</span>
              </label>
            </div>
          </div>

          {/* 6. Cover Artwork */}
          <div>
            <label className="text-xs font-bold text-zinc-300 block mb-1.5">
              Carátula / Arte del Track
            </label>
            <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
              {PRESET_COVERS.map((url, i) => (
                <img
                  key={i}
                  src={url}
                  alt="Preset"
                  onClick={() => setCoverUrl(url)}
                  className={`w-14 h-14 rounded-xl object-cover cursor-pointer transition-all flex-shrink-0 ${
                    coverUrl === url
                      ? 'ring-2 ring-amber-400 scale-105'
                      : 'opacity-50 hover:opacity-100'
                  }`}
                />
              ))}
            </div>
          </div>

          {/* 7. Description */}
          <div>
            <label className="text-xs font-bold text-zinc-300 block mb-1.5">
              Descripción y Notas para el Artista
            </label>
            <textarea
              rows={2}
              placeholder="Indica recomendaciones de voces, instrumentos destacados o condiciones comerciales..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-[#121520] border border-[#232a40] focus:border-amber-400 rounded-xl p-3 text-xs text-white placeholder-zinc-400 focus:outline-none"
            />
          </div>

          {/* Actions */}
          <div className="pt-2 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-bold py-3 rounded-xl text-xs transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 bg-amber-400 hover:bg-amber-300 text-zinc-950 font-black py-3 rounded-xl text-xs transition-all shadow-md shadow-amber-400/20"
            >
              {trackToEdit ? 'Guardar Cambios' : 'Publicar en Catálogo'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
