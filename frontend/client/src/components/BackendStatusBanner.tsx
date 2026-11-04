import React from 'react';
import { CheckCircle2, LoaderCircle, RefreshCw, WifiOff } from 'lucide-react';
import { useApp } from '../context/AppContext';

const phaseLabels = {
  session: 'sesión',
  catalog: 'catálogo',
  cart: 'carrito',
} as const;

export const BackendStatusBanner: React.FC = () => {
  const { configuredMode, backendStatus, backendError, isSyncing, refreshFromBackend } = useApp();
  if (configuredMode !== 'hybrid') return null;

  const retry = () => void refreshFromBackend().catch(() => {});
  const base = 'flex items-center justify-center gap-2 border-b px-4 py-2 text-xs font-semibold';

  if (backendStatus === 'checking') {
    return (
      <div role="status" className={`${base} border-sky-400/20 bg-sky-400/10 text-sky-200`}>
        <LoaderCircle className="h-4 w-4 animate-spin" />
        Django está comprobando la conexión y sincronizando los datos…
      </div>
    );
  }

  if (backendStatus === 'offline' && backendError) {
    const issue = backendError.type === 'network' ? 'Error de conexión' : 'Error de API';
    return (
      <div role="alert" className={`${base} flex-wrap border-rose-400/20 bg-rose-400/10 text-rose-200`}>
        <WifiOff className="h-4 w-4 shrink-0" />
        <span>{issue} en {phaseLabels[backendError.phase]}. {backendError.message}</span>
        <button onClick={retry} disabled={isSyncing} className="inline-flex items-center gap-1 rounded-lg border border-rose-200/30 px-2.5 py-1 hover:bg-rose-200/10 disabled:opacity-50">
          <RefreshCw className={`h-3.5 w-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
          Reintentar
        </button>
      </div>
    );
  }

  if (backendStatus === 'online') {
    return (
      <div role="status" className={`${base} border-emerald-400/15 bg-emerald-400/5 text-emerald-200/80`}>
        <CheckCircle2 className="h-4 w-4" />
        Sincronización con Django activa
      </div>
    );
  }

  return null;
};
