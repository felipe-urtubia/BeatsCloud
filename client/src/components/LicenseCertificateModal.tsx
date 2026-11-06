import React, { useState } from 'react';
import { LicenseContract } from '../types';
import {
  ShieldCheck,
  CheckCircle2,
  Copy,
  Printer,
  Download,
  X,
  Award,
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
Comprobante de compra de BeatsCloud

Código de registro: ${contract.licenseCode}
Referencia interna: ${contract.buyOrder}
Fecha registrada: ${contract.issueDate}
Monto registrado: $${contract.amountClp.toLocaleString('es-CL')} CLP
Pista: ${contract.trackTitle}
Género: ${contract.trackGenre}
Productor: ${contract.producerName} (@${contract.producerUsername})
Comprador: ${contract.buyerName} (@${contract.buyerUsername})
Huella de verificación HMAC-SHA256: ${contract.verificationHash}

Este comprobante refleja los datos de compra disponibles en BeatsCloud. No define
por sí solo condiciones de licencia ni sustituye un contrato legal.
`;

    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Comprobante_BeatsCloud_${contract.licenseCode}.txt`;
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
              Comprobante de compra · BeatsCloud
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
              title="Descargar comprobante de compra"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Descargar comprobante</span>
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
                      Compra registrada
                    </span>
                    <span className="text-[10px] font-mono text-zinc-400">
                      Registro de BeatsCloud
                    </span>
                  </div>
                  <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight mt-1">
                    COMPROBANTE DE COMPRA
                  </h1>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Resumen informativo de los datos de compra registrados en BeatsCloud.
                  </p>
                </div>
              </div>

              {/* Unique License Box */}
              <div className="bg-[#08090e] border border-amber-400/40 rounded-2xl p-4 text-center sm:text-right font-mono flex-shrink-0 shadow-lg">
                <span className="text-[10px] text-zinc-400 uppercase tracking-widest block font-bold">
                  Código de registro
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
                  Referencia: {contract.buyOrder}
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
                  Huella de verificación HMAC-SHA256
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
                  Productor
                </span>
              </div>
              <h4 className="text-sm font-bold text-white">{contract.producerName}</h4>
              <p className="text-xs text-zinc-400 font-mono">@{contract.producerUsername}</p>
              <div className="pt-2 border-t border-[#1e2436] text-[11px] text-zinc-400 flex justify-between">
                <span>Usuario:</span>
                <span className="font-mono text-zinc-300 font-bold">{contract.producerRut}</span>
              </div>
            </div>

            {/* Licensee (Artist) */}
            <div className="bg-[#10131e] border border-[#1e2436] rounded-2xl p-5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase">
                  Comprador
                </span>
              </div>
              <h4 className="text-sm font-bold text-white">{contract.buyerName}</h4>
              <p className="text-xs text-zinc-400 font-mono">@{contract.buyerUsername}</p>
              <div className="pt-2 border-t border-[#1e2436] text-[11px] text-zinc-400 flex justify-between">
                <span>Usuario:</span>
                <span className="font-mono text-zinc-300 font-bold">{contract.buyerRut}</span>
              </div>
            </div>
          </div>

          {/* Track Technical Card */}
          <div className="bg-[#10131e] border border-[#1e2436] rounded-2xl p-5 space-y-3">
            <span className="text-[10px] font-mono font-bold text-zinc-400 uppercase block">
              Pista asociada
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
                  ${contract.amountClp.toLocaleString('es-CL')} CLP
                </span>
              </div>
            </div>
          </div>

          <p className="text-xs text-zinc-400 leading-relaxed">
            Este comprobante resume únicamente la información registrada por BeatsCloud. Las condiciones
            de uso o licencia de la pista deben confirmarse por separado con el productor.
          </p>

          {/* Bottom Security Note */}
          <div className="pt-4 border-t border-[#1b2030] flex flex-col sm:flex-row items-center justify-between text-[11px] text-zinc-500 font-mono gap-3">
            <span>Fecha de emisión: {contract.issueDate}</span>
            <span>BeatsCloud · Registro de compra; no constituye un contrato legal</span>
          </div>
        </div>
      </div>
    </div>
  );
};
