import React, { useState } from 'react';
import { LicenseContract } from '../types';
import {
  FileText,
  ShieldCheck,
  CheckCircle2,
  Copy,
  Printer,
  Download,
  X,
  ExternalLink,
  Scale,
  Award,
  Disc3,
  Calendar,
  Lock,
} from 'lucide-react';

interface LicenseCertificateModalProps {
  isOpen: boolean;
  onClose: () => void;
  contract: LicenseContract | null;
}

export const LicenseCertificateModal: React.FC<LicenseCertificateModalProps> = ({
  isOpen,
  onClose,
  contract,
}) => {
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);

  if (!isOpen || !contract) return null;

  const handleCopyCode = () => {
    navigator.clipboard.writeText(contract.licenseCode);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2500);
  };

  const handleCopyHash = () => {
    navigator.clipboard.writeText(contract.verificationHash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2500);
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadTextContract = () => {
    const textContent = `
================================================================================
             CERTIFICADO OFICIAL DE LICENCIA MUSICAL BEATSCLOUD
                 REGISTRO PÚBLICO DE PROPIEDAD INTELECTUAL
================================================================================

CÓDIGO ÚNICO DE LICENCIA: ${contract.licenseCode}
FIRMA CRIPTOGRÁFICA (SHA-256): ${contract.verificationHash}
ORDEN DE COMPRA / TRANSBANK WEBPAY: ${contract.buyOrder}
FECHA DE EMISIÓN: ${contract.issueDate}
MODALIDAD DE LICENCIA: ${contract.licenseType.toUpperCase().replace(/_/g, ' ')}
MONTO DE TRANSACCIÓN: $${contract.amountClp.toLocaleString('es-CL')} CLP (+ 19% IVA)

--------------------------------------------------------------------------------
1. IDENTIFICACIÓN DE LAS PARTES CONTRATANTES
--------------------------------------------------------------------------------
PARTE LICENCIANTE (PRODUCTOR / BEATMAKER):
  Nombre Artístico: ${contract.producerName}
  Usuario BeatsCloud: @${contract.producerUsername}
  RUT / Cédula de Identidad: ${contract.producerRut || 'Registro Verificado'}

PARTE LICENCIATARIA (ARTISTA / CANTANTE):
  Nombre Artístico: ${contract.buyerName}
  Usuario BeatsCloud: @${contract.buyerUsername}
  RUT / Cédula de Identidad: ${contract.buyerRut || 'Registro Verificado'}

--------------------------------------------------------------------------------
2. IDENTIFICACIÓN DE LA OBRA FONOGRÁFICA (BEAT / INSTRUMENTAL)
--------------------------------------------------------------------------------
  Título de la Pista: "${contract.trackTitle}"
  Género / Estilo: ${contract.trackGenre}
  Tempo Oficial: ${contract.trackBpm} BPM
  Escala Armónica: ${contract.trackKey}
  Archivos Entregados: Master WAV 24-bit (Sin Marcas de Agua) + Stems Multitrack

--------------------------------------------------------------------------------
3. CONDICIONES Y TÉRMINOS LEGALES DE EXPLOTACIÓN COMERCIAL
--------------------------------------------------------------------------------
A) DERECHOS DE AUTOR Y REPARTO DE REGALÍAS (SPLIT SHEET SCD / DNDA CHILE):
   - Derechos Morales y Patrimoniales sobre la Composición Instrumental:
     ${contract.musicRightsSplit.producerPercent}% a favor de ${contract.producerName} (Productor).
   - Derechos Morales y Patrimoniales sobre la Letra e Interpretación Vocal:
     ${contract.musicRightsSplit.artistPercent}% a favor de ${contract.buyerName} (Artista).
   - Se autoriza expresamente la inscripción de la obra resultante ante la
     Sociedad Chilena de Autores e Intérpretes Musicales (SCD) o entidad análoga en LATAM.

B) DERECHOS DE SINCRONIZACIÓN Y DISTRIBUCIÓN DIGITAL:
   - Reproducciones en Streaming (Spotify, Apple Music, Tidal, Amazon): ${contract.distributionTerms.streamsLimit}.
   - Monetización en YouTube y Redes Sociales: Autorizada sin reclamos de copyright.
   - Presentaciones en Vivo con Fines de Lucro: Autorizadas.
   - Difusión Radial y Televisiva: Autorizada.

C) GARANTÍA DE INMUNIDAD ANTE COPYRIGHT STRIKES:
   Este certificado otorga al Artista Licenciatario el derecho irrestricto de uso comercial.
   En caso de detección automática por algoritmos de Content ID o reclamos de distribuidoras
   (DistroKid, TuneCore, Altafonte, CD Baby), el Artista presentará este código de licencia
   (${contract.licenseCode}) y su Hash criptográfico como prueba irrefutable de adquisición legítima.

================================================================================
Emitido digitalmente por BeatsCloud Platform SpA - Santiago de Chile.
Validación en línea: https://beatscloud.lat/verify/${contract.licenseCode}
================================================================================
`;

    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Contrato_Licencia_${contract.licenseCode}_${contract.trackTitle.replace(/[\s/]/g, '_')}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl max-h-[92vh] bg-[#0c0e15] border border-[#232a3d] rounded-3xl shadow-2xl overflow-y-auto flex flex-col">
        {/* Modal Top Actions Header */}
        <div className="sticky top-0 z-20 bg-[#0e111a]/95 backdrop-blur-md border-b border-[#1b2030] px-5 sm:px-7 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <h3 className="text-xs font-mono font-black text-zinc-200 uppercase tracking-wider">
              Contrato de Licencia Oficial · BeatsCloud Chile
            </h3>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="p-1.5 sm:px-3 sm:py-1.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-bold transition-colors flex items-center gap-1.5"
              title="Imprimir o Guardar en PDF"
            >
              <Printer className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Imprimir PDF</span>
            </button>
            <button
              onClick={handleDownloadTextContract}
              className="p-1.5 sm:px-3 sm:py-1.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-zinc-950 text-xs font-black transition-colors flex items-center gap-1.5 shadow-sm"
              title="Descargar Documento Legal"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Descargar Contrato</span>
            </button>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-zinc-800/80 hover:bg-zinc-700 text-zinc-400 hover:text-white flex items-center justify-center transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Printable Certificate Sheet */}
        <div className="p-6 sm:p-10 space-y-6 text-zinc-200">
          {/* Certificate Header Banner */}
          <div className="relative rounded-2xl bg-gradient-to-br from-[#121624] via-[#101420] to-[#0c0e16] border border-[#262e45] p-6 sm:p-8 overflow-hidden text-center sm:text-left">
            <div className="absolute top-0 right-0 w-64 h-64 bg-amber-400/5 rounded-full blur-3xl pointer-events-none" />

            <div className="flex flex-col sm:flex-row items-center justify-between gap-5 relative z-10">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-amber-500 to-amber-300 p-0.5 shadow-xl flex-shrink-0">
                  <div className="w-full h-full bg-[#0c0e15] rounded-[14px] flex items-center justify-center">
                    <Award className="w-8 h-8 text-amber-400" />
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-2 justify-center sm:justify-start">
                    <span className="text-[10px] font-mono font-bold tracking-widest uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-md">
                      Licencia Autorizada & Registrada
                    </span>
                    <span className="text-[10px] font-mono text-zinc-400">
                      SCD / DNDA Compliant
                    </span>
                  </div>
                  <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight mt-1">
                    CÉDULA DE LICENCIA COMERCIAL
                  </h1>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Certificado de cesión de derechos fonográficos y sincronización comercial.
                  </p>
                </div>
              </div>

              {/* Unique License Box */}
              <div className="bg-[#08090e] border border-amber-400/40 rounded-2xl p-4 text-center sm:text-right font-mono flex-shrink-0 shadow-lg">
                <span className="text-[10px] text-zinc-400 uppercase tracking-widest block font-bold">
                  Código de Registro Único
                </span>
                <div className="flex items-center justify-center sm:justify-end gap-2 mt-1">
                  <span className="text-base font-black text-amber-400">
                    {contract.licenseCode}
                  </span>
                  <button
                    onClick={handleCopyCode}
                    className="text-zinc-400 hover:text-white transition-colors p-1"
                    title="Copiar código"
                  >
                    {copiedCode ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
                <span className="text-[10px] text-zinc-500 block mt-1">
                  Webpay Order: {contract.buyOrder}
                </span>
              </div>
            </div>
          </div>

          {/* Cryptographic Hash Verification Pill */}
          <div className="bg-[#10131e] border border-[#1e2436] rounded-2xl p-4 font-mono text-xs flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 min-w-0">
              <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <div className="min-w-0">
                <span className="text-[10px] text-zinc-400 uppercase font-bold block">
                  Firma Criptográfica SHA-256 (Prueba de Inmutabilidad)
                </span>
                <span className="text-xs text-zinc-300 font-bold break-all block truncate">
                  {contract.verificationHash}
                </span>
              </div>
            </div>

            <button
              onClick={handleCopyHash}
              className="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-bold flex items-center gap-1.5 flex-shrink-0 transition-colors"
            >
              {copiedHash ? (
                <>
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  <span>Copiado</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copiar Hash</span>
                </>
              )}
            </button>
          </div>

          {/* Parties & Track Summary Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Licensor (Producer) */}
            <div className="bg-[#10131e] border border-[#1e2436] rounded-2xl p-5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-amber-400 uppercase">
                  Parte Licenciante (Productor)
                </span>
                <span className="text-[10px] font-mono text-zinc-500">50% Autoría Musical</span>
              </div>
              <h4 className="text-sm font-bold text-white">{contract.producerName}</h4>
              <p className="text-xs text-zinc-400 font-mono">@{contract.producerUsername}</p>
              <div className="pt-2 border-t border-[#1e2436] text-[11px] text-zinc-400 flex justify-between">
                <span>RUT / Identificación:</span>
                <span className="font-mono text-zinc-300 font-bold">{contract.producerRut}</span>
              </div>
            </div>

            {/* Licensee (Artist) */}
            <div className="bg-[#10131e] border border-[#1e2436] rounded-2xl p-5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase">
                  Parte Licenciataria (Artista)
                </span>
                <span className="text-[10px] font-mono text-zinc-500">50% Letra y Voz</span>
              </div>
              <h4 className="text-sm font-bold text-white">{contract.buyerName}</h4>
              <p className="text-xs text-zinc-400 font-mono">@{contract.buyerUsername}</p>
              <div className="pt-2 border-t border-[#1e2436] text-[11px] text-zinc-400 flex justify-between">
                <span>RUT / Identificación:</span>
                <span className="font-mono text-zinc-300 font-bold">{contract.buyerRut}</span>
              </div>
            </div>
          </div>

          {/* Track Technical Card */}
          <div className="bg-[#10131e] border border-[#1e2436] rounded-2xl p-5 space-y-3">
            <span className="text-[10px] font-mono font-bold text-zinc-400 uppercase block">
              Obra Musical Licenciada
            </span>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-black text-white">"{contract.trackTitle}"</h3>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Estilo: {contract.trackGenre} · {contract.trackBpm} BPM · Tonalidad: {contract.trackKey}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold bg-amber-400/20 text-amber-400 px-3 py-1.5 rounded-xl border border-amber-400/30">
                  WAV 24-bit + Stems Sin Marcas
                </span>
              </div>
            </div>
          </div>

          {/* Legal Clauses Explainer */}
          <div className="space-y-4">
            <h4 className="text-xs font-mono font-bold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
              <Scale className="w-4 h-4 text-amber-400" />
              <span>Cláusulas de Explotación y Protección Legal (Chile y LATAM)</span>
            </h4>

            <div className="space-y-2.5 text-xs text-zinc-300 leading-relaxed font-sans">
              <div className="p-3.5 rounded-xl bg-[#10131e] border border-[#1e2436]">
                <strong className="text-white block mb-0.5">
                  1. Registro de Split Sheet (SCD / DNDA):
                </strong>
                El Productor y el Artista acuerdan un reparto paritario ({contract.musicRightsSplit.producerPercent}% Productor / {contract.musicRightsSplit.artistPercent}% Artista) sobre los derechos patrimoniales y regalías de ejecución pública recaudados por sociedades de gestión colectiva (SCD en Chile, SADAIC en Argentina, SACM en México, etc.).
              </div>

              <div className="p-3.5 rounded-xl bg-[#10131e] border border-[#1e2436]">
                <strong className="text-white block mb-0.5">
                  2. Distribución en Plataformas Digitales:
                </strong>
                El Artista está plenamente facultado para distribuir comercialmente la canción en Spotify, Apple Music, Deezer, TikTok y demás plataformas mediante distribuidores certificados (DistroKid, Altafonte, TuneCore, etc.) con alcance de streaming {contract.distributionTerms.streamsLimit.toLowerCase()}.
              </div>

              <div className="p-3.5 rounded-xl bg-[#10131e] border border-[#1e2436]">
                <strong className="text-white block mb-0.5">
                  3. Inmunidad ante Reclamos de Content ID / YouTube:
                </strong>
                El presente certificado y su código único ({contract.licenseCode}) constituyen prueba fehaciente de cesión de derechos para disputar y levantar de forma inmediata cualquier reclamo o advertencia por derechos de autor automatizados.
              </div>
            </div>
          </div>

          {/* Bottom Security Note */}
          <div className="pt-4 border-t border-[#1b2030] flex flex-col sm:flex-row items-center justify-between text-[11px] text-zinc-500 font-mono gap-3">
            <span>Fecha de emisión: {contract.issueDate}</span>
            <span>BeatsCloud Chile SpA · Trazabilidad de Contratos Musicales</span>
          </div>
        </div>
      </div>
    </div>
  );
};
