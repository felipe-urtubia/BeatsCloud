import React from 'react';
import { FileText, ShieldCheck, X } from 'lucide-react';

interface LicenseVerificationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LicenseVerificationModal: React.FC<LicenseVerificationModalProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4 backdrop-blur-md">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="purchase-record-title"
        className="relative w-full max-w-xl space-y-5 rounded-3xl border border-[#232a40] bg-[#0e111a] p-6 shadow-2xl sm:p-8"
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar"
          className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full bg-zinc-800/80 text-zinc-400 transition-colors hover:bg-zinc-700 hover:text-white"
        >
          <X className="h-4 w-4" />
        </button>
        <div className="flex items-center gap-3 pr-8">
          <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl border border-amber-400/20 bg-amber-400/10 text-amber-400">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <h3 id="purchase-record-title" className="font-mono text-base font-black uppercase tracking-tight text-white">
              Comprobantes de compra
            </h3>
            <p className="text-xs text-zinc-400">Consulta los datos guardados por Django en tu biblioteca.</p>
          </div>
        </div>
        <div className="flex items-start gap-3 rounded-2xl border border-[#232a40] bg-[#121520] p-4 text-xs leading-relaxed text-zinc-300">
          <FileText className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-400" />
          <p>
            La verificación pública de códigos no está disponible. Si compraste una pista,
            abre tu perfil de artista y consulta el comprobante desde tu biblioteca. El comprobante
            muestra el registro de compra y no constituye un contrato ni define condiciones de licencia.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="w-full rounded-xl bg-zinc-800 px-4 py-2.5 text-xs font-bold text-zinc-200 transition-colors hover:bg-zinc-700"
        >
          Entendido
        </button>
      </div>
    </div>
  );
};
