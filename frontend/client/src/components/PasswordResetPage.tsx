import React, { useState } from 'react';
import { ArrowLeft, Eye, EyeOff, KeyRound, LoaderCircle, ShieldCheck } from 'lucide-react';
import DjangoApi from '../api/django.service';

interface PasswordResetPageProps {
  uidb64: string;
  token: string;
}

export const PasswordResetPage: React.FC<PasswordResetPageProps> = ({ uidb64, token }) => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [complete, setComplete] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (isSubmitting) return;
    setError(null);
    setIsSubmitting(true);
    try {
      await DjangoApi.confirmarRestauracionContrasena(
        uidb64,
        token,
        password,
        confirmPassword,
      );
      setComplete(true);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'No se pudo actualizar la contraseña.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0a0c10] px-4 py-8 text-zinc-100">
      <section className="w-full max-w-lg rounded-3xl border border-[#23283b] bg-[#14151e] p-7 shadow-2xl sm:p-9">
        <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-400 text-zinc-950">
          {complete ? <ShieldCheck className="h-7 w-7" /> : <KeyRound className="h-7 w-7" />}
        </div>
        <h1 className="text-2xl font-black">
          {complete ? 'Contraseña actualizada' : 'Crea una nueva contraseña'}
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-zinc-400">
          {complete
            ? 'Ya puedes volver a BeatsCloud e iniciar sesión con tu nueva contraseña.'
            : 'Elige una contraseña segura para recuperar el acceso a tu cuenta.'}
        </p>

        {error && (
          <div role="alert" className="mt-5 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300">
            {error}
          </div>
        )}

        {complete ? (
          <a
            href="/?auth=login"
            className="mt-6 inline-flex w-full items-center justify-center rounded-xl bg-amber-400 px-5 py-3 text-sm font-bold text-zinc-950 transition hover:bg-amber-300"
          >
            Ir a iniciar sesión
          </a>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label htmlFor="new-password" className="mb-1 block text-xs font-bold text-zinc-300">
                Nueva contraseña
              </label>
              <div className="relative">
                <input
                  id="new-password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="w-full rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 pr-12 text-sm text-white outline-none focus:border-amber-400"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((visible) => !visible)}
                  aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                  aria-pressed={showPassword}
                  className="absolute inset-y-0 right-0 flex items-center px-4 text-zinc-400 hover:text-amber-400"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <div>
              <label htmlFor="confirm-new-password" className="mb-1 block text-xs font-bold text-zinc-300">
                Confirmar nueva contraseña
              </label>
              <div className="relative">
                <input
                  id="confirm-new-password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  className="w-full rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 pr-12 text-sm text-white outline-none focus:border-amber-400"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((visible) => !visible)}
                  aria-label={showConfirmPassword ? 'Ocultar confirmación de contraseña' : 'Mostrar confirmación de contraseña'}
                  aria-pressed={showConfirmPassword}
                  className="absolute inset-y-0 right-0 flex items-center px-4 text-zinc-400 hover:text-amber-400"
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <p className="text-xs leading-relaxed text-zinc-500">
              La contraseña debe cumplir las reglas de seguridad de BeatsCloud.
            </p>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-amber-400 px-5 py-3 text-sm font-bold text-zinc-950 transition hover:bg-amber-300 disabled:cursor-wait disabled:opacity-60"
            >
              {isSubmitting && <LoaderCircle className="h-4 w-4 animate-spin" />}
              {isSubmitting ? 'Guardando…' : 'Guardar nueva contraseña'}
            </button>
            <a href="/" className="flex items-center justify-center gap-2 py-2 text-xs text-zinc-400 hover:text-amber-400">
              <ArrowLeft className="h-3 w-3" /> Volver a BeatCloud
            </a>
          </form>
        )}
      </section>
    </main>
  );
};
