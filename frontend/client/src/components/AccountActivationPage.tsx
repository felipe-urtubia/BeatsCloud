import React, { useEffect, useState } from 'react';
import { CheckCircle2, LoaderCircle, XCircle } from 'lucide-react';
import DjangoApi from '../api/django.service';

interface AccountActivationPageProps {
  uidb64: string;
  token: string;
}

export const AccountActivationPage: React.FC<AccountActivationPageProps> = ({ uidb64, token }) => {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Estamos validando el enlace de activación.');

  useEffect(() => {
    let active = true;
    DjangoApi.activarCuenta(uidb64, token)
      .then((response) => {
        if (!active) return;
        setMessage(response.detail);
        setStatus('success');
      })
      .catch((error: unknown) => {
        if (!active) return;
        setMessage(error instanceof Error ? error.message : 'No se pudo activar la cuenta.');
        setStatus('error');
      });
    return () => {
      active = false;
    };
  }, [uidb64, token]);

  const StatusIcon = status === 'loading' ? LoaderCircle : status === 'success' ? CheckCircle2 : XCircle;

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0a0c10] px-4 text-zinc-100">
      <section className="w-full max-w-md rounded-3xl border border-[#23283b] bg-[#14151e] p-8 text-center shadow-2xl">
        <StatusIcon
          aria-hidden="true"
          className={`mx-auto mb-4 h-12 w-12 ${
            status === 'loading'
              ? 'animate-spin text-amber-400'
              : status === 'success'
                ? 'text-emerald-400'
                : 'text-rose-400'
          }`}
        />
        <h1 className="text-2xl font-black">
          {status === 'loading'
            ? 'Validando cuenta'
            : status === 'success'
              ? '¡Cuenta activada!'
              : 'No se pudo activar'}
        </h1>
        <p role={status === 'error' ? 'alert' : 'status'} className="mt-3 text-sm text-zinc-300">
          {message}
        </p>
        {status !== 'loading' && (
          <a
            href="/"
            className="mt-6 inline-flex rounded-xl bg-amber-400 px-5 py-3 text-sm font-bold text-zinc-950 transition hover:bg-amber-300"
          >
            Ir a BeatCloud
          </a>
        )}
      </section>
    </main>
  );
};
