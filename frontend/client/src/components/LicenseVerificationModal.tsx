import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { LicenseContract } from '../types';
import {
  ShieldCheck,
  Search,
  CheckCircle2,
  AlertTriangle,
  X,
  FileText,
  ExternalLink,
  Award,
} from 'lucide-react';

interface LicenseVerificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onViewContract: (contract: LicenseContract) => void;
}

export const LicenseVerificationModal: React.FC<LicenseVerificationModalProps> = ({
  isOpen,
  onClose,
  onViewContract,
}) => {
  const { sales, purchases, tracks, users } = useApp();
  const [queryCode, setQueryCode] = useState('');
  const [searchResult, setSearchResult] = useState<{
    found: boolean;
    contract?: LicenseContract;
    message?: string;
  } | null>(null);

  if (!isOpen) return null;

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanCode = queryCode.trim().toUpperCase();

    if (!cleanCode) {
      setSearchResult(null);
      return;
    }

    // Look in sales and purchases
    const purchase = purchases.find(
      (p) =>
        (p.licenseCode && p.licenseCode.toUpperCase() === cleanCode) ||
        (p.buyOrder && p.buyOrder.toUpperCase() === cleanCode)
    );

    const sale = sales.find(
      (s) =>
        (s.licenseCode && s.licenseCode.toUpperCase() === cleanCode) ||
        (s.buyOrder && s.buyOrder.toUpperCase() === cleanCode)
    );

    if (purchase || sale) {
      const trackId = purchase?.trackId || sale?.trackId || '';
      const track = tracks.find((t) => t.id === trackId);
      const buyerUser = users.find((u) => u.id === (purchase?.userId || sale?.buyerId));
      const producerUser = users.find((u) => u.id === track?.producerId);

      const contract: LicenseContract = {
        licenseCode: purchase?.licenseCode || sale?.licenseCode || `LIC-${cleanCode}`,
        verificationHash:
          purchase?.verificationHash ||
          sale?.verificationHash ||
          'SHA256:7e9b2a1c0d4e8f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a',
        issueDate: purchase?.date || sale?.date || '2026-03-12',
        trackId: track?.id || trackId,
        trackTitle: track?.title || purchase?.trackTitle || sale?.trackTitle || 'Beat Registrado',
        trackGenre: track?.genre || 'Urbano',
        trackBpm: track?.bpm || 130,
        trackKey: track?.scaleKey || 'C Menor',
        producerId: producerUser?.id || track?.producerId || 'user_prod_1',
        producerName: producerUser?.artistName || track?.producerName || 'Productor BeatsCloud',
        producerUsername: producerUser?.username || track?.producerUsername || 'productor',
        producerRut: '18.421.902-3 (Verificado)',
        buyerId: buyerUser?.id || 'user_buyer',
        buyerName: buyerUser?.artistName || buyerUser?.username || purchase?.producerName || 'Artista Licenciatario',
        buyerUsername: buyerUser?.username || 'artista',
        buyerRut: '19.824.110-K (Verificado)',
        amountClp: purchase?.amount || sale?.amount || 18000,
        buyOrder: purchase?.buyOrder || sale?.buyOrder || cleanCode,
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

      setSearchResult({
        found: true,
        contract,
      });
    } else {
      setSearchResult({
        found: false,
        message: `El código "${cleanCode}" no figura en el registro oficial de transacciones autorizadas de BeatsCloud Chile. Verifique que no contenga espacios u omisiones.`,
      });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-150">
      <div className="relative w-full max-w-xl bg-[#0e111a] border border-[#232a40] rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-full bg-zinc-800/80 hover:bg-zinc-700 text-zinc-400 hover:text-white flex items-center justify-center transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-amber-400/10 text-amber-400 border border-amber-400/20 flex items-center justify-center flex-shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-black text-white font-mono uppercase tracking-tight">
              Verificador Público de Licencias
            </h3>
            <p className="text-xs text-zinc-400">
              Comprueba la validez de un contrato de beat para SCD, Spotify o YouTube.
            </p>
          </div>
        </div>

        {/* Search Form */}
        <form onSubmit={handleVerify} className="space-y-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-zinc-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={queryCode}
                onChange={(e) => setQueryCode(e.target.value)}
                placeholder="Ej: LIC-BC-541209 o BC-541209"
                className="w-full bg-[#121520] border border-[#232a40] rounded-xl pl-9 pr-3 py-2.5 text-xs text-white placeholder-zinc-500 font-mono uppercase focus:outline-none focus:border-amber-400"
              />
            </div>
            <button
              type="submit"
              className="bg-amber-400 hover:bg-amber-300 text-zinc-950 font-black px-4 py-2.5 rounded-xl text-xs font-mono uppercase transition-colors shadow-sm"
            >
              Verificar
            </button>
          </div>

          <div className="text-[11px] text-zinc-500 font-mono">
            Código de prueba en base de datos: <button type="button" onClick={() => setQueryCode('LIC-BC-541209')} className="text-amber-400 underline font-bold">LIC-BC-541209</button>
          </div>
        </form>

        {/* Search Results */}
        {searchResult && (
          <div className="animate-in fade-in duration-200">
            {searchResult.found && searchResult.contract ? (
              <div className="bg-[#121624] border border-emerald-500/40 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-bold font-mono text-emerald-400 uppercase">
                      Licencia Auténtica y Vigente
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-zinc-400">
                    Transbank Webpay Aprobada
                  </span>
                </div>

                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between font-mono">
                    <span className="text-zinc-500">Pista:</span>
                    <span className="text-white font-bold">{searchResult.contract.trackTitle}</span>
                  </div>
                  <div className="flex justify-between font-mono">
                    <span className="text-zinc-500">Productor Licenciante:</span>
                    <span className="text-zinc-200 font-bold">{searchResult.contract.producerName}</span>
                  </div>
                  <div className="flex justify-between font-mono">
                    <span className="text-zinc-500">Artista Licenciatario:</span>
                    <span className="text-amber-400 font-bold">{searchResult.contract.buyerName}</span>
                  </div>
                  <div className="flex justify-between font-mono">
                    <span className="text-zinc-500">Reparto SCD:</span>
                    <span className="text-zinc-300">50% Productor / 50% Artista</span>
                  </div>
                  <div className="flex justify-between font-mono">
                    <span className="text-zinc-500">Archivos Master:</span>
                    <span className="text-emerald-400 font-bold">WAV 24-bit + Stems</span>
                  </div>
                </div>

                <button
                  onClick={() => {
                    onClose();
                    onViewContract(searchResult.contract!);
                  }}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-black py-2.5 rounded-xl text-xs font-mono uppercase transition-colors flex items-center justify-center gap-2"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Abrir Certificado Oficial Completo</span>
                </button>
              </div>
            ) : (
              <div className="bg-rose-950/20 border border-rose-500/30 rounded-2xl p-4 text-xs text-rose-300 flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                <p>{searchResult.message}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
