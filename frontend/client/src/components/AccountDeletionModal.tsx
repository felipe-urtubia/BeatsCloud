import React, { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import DjangoApi from '../api/django.service';

interface AccountDeletionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AccountDeletionModal: React.FC<AccountDeletionModalProps> = ({ isOpen, onClose }) => {
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [verificationStarted, setVerificationStarted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleStart = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await DjangoApi.iniciarEliminacionCuenta(password);
      setVerificationStarted(true);
    } catch (requestError) {
      setError((requestError as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handleConfirm = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await DjangoApi.confirmarEliminacionCuenta(code);
      window.location.reload();
    } catch (requestError) {
      setError((requestError as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 p-4" role="presentation">
      <section role="dialog" aria-modal="true" aria-labelledby="delete-account-title" className="w-full max-w-md rounded-2xl border border-red-500/30 bg-[#14151f] p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 id="delete-account-title" className="flex items-center gap-2 text-lg font-black text-white">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            Eliminar cuenta
          </h2>
          <button type="button" onClick={onClose} aria-label="Cerrar" className="text-zinc-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        <p className="mb-4 text-sm text-zinc-300">
          Esta acción es permanente. Django conservará anonimizados los registros necesarios para compras anteriores.
        </p>
        <form onSubmit={verificationStarted ? handleConfirm : handleStart} className="space-y-3">
          {!verificationStarted ? (
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Confirma tu contraseña"
              aria-label="Confirma tu contraseña"
              className="w-full rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-white"
            />
          ) : (
            <>
              <p className="text-xs text-amber-200">Ingresa el código enviado al correo de tu cuenta (vence en 15 minutos).</p>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                required
                value={code}
                onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
                placeholder="Código de 6 dígitos"
                aria-label="Código de verificación"
                className="w-full rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-white"
              />
            </>
          )}
          {error && <p role="alert" className="text-xs text-rose-400">{error}</p>}
          <button disabled={busy} className="w-full rounded-xl bg-red-500 px-4 py-3 text-sm font-bold text-white disabled:opacity-50">
            {busy ? 'Procesando…' : verificationStarted ? 'Eliminar definitivamente' : 'Enviar código de verificación'}
          </button>
        </form>
      </section>
    </div>
  );
};
