import React from 'react';
import { CheckCircle2, LoaderCircle, RefreshCw, WifiOff } from 'lucide-react';
import { useApp } from '../context/AppContext';

const phaseLabels = {
  session: 'sesión',
  catalog: 'catálogo',
  cart: 'carrito',
} as const;

export const BackendStatusBanner: React.FC = () => {
  const { configuredMode, currentUser, backendStatus, backendError, isSyncing, refreshFromBackend } = useApp();

  const retry = () => void refreshFromBackend().catch(() => {});
  const base = 'flex items-center justify-center gap-2 border-b px-4 py-2 text-xs font-semibold';
  const mode = configuredMode === 'mock' ? 'DEMO · MOCK' : 'API REAL';
  const session = currentUser ? `Sesión: ${currentUser.username}` : configuredMode === 'mock' ? 'Cuenta demo' : 'Sin sesión';

  if (configuredMode === 'mock') {
    return <div role="status" className={`${base} border-amber-400/20 bg-amber-400/10 text-amber-100`}>
      <span className="font-mono">{mode}</span><span>·</span><span>{session}</span>
    </div>;
  }

  if (backendStatus === 'checking') {
    return (
      <div role="status" className={`${base} border-sky-400/20 bg-sky-400/10 text-sky-200`}>
        <LoaderCircle className="h-4 w-4 animate-spin" />
        <span className="font-mono">{mode}</span><span>·</span><span>{session}</span><span>·</span>
        Django está comprobando la conexión y sincronizando los datos…
      </div>
    );
  }

  if (backendStatus === 'offline' && backendError) {
    const issue = backendError.type === 'network' ? 'Error de conexión' : 'Error de API';
    return (
      <div role="alert" className={`${base} flex-wrap border-rose-400/20 bg-rose-400/10 text-rose-200`}>
        <WifiOff className="h-4 w-4 shrink-0" />
        <span className="font-mono">{mode}</span><span>·</span><span>{session}</span><span>·</span>
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
        <span className="font-mono">{mode}</span><span>·</span><span>{session}</span><span>·</span>
        Sincronización con Django activa
      </div>
    );
  }

  return <div role="status" className={`${base} border-zinc-700 bg-zinc-900 text-zinc-300`}>
    <span className="font-mono">{mode}</span><span>·</span><span>{session}</span>
  </div>;
};
