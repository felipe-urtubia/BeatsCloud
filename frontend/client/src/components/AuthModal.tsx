import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { UserType } from '../types';
import { X, LogIn, UserPlus, Sliders, Mic2, Sparkles, Check } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  mode: 'login' | 'register';
  onClose: () => void;
  onSwitchMode: (mode: 'login' | 'register') => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  mode,
  onClose,
  onSwitchMode,
}) => {
  const { login, registerUser, registerAccount, switchUser, users, configuredMode } = useApp();

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [artistName, setArtistName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<UserType>('artista');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    setError(null);
    setSuccessMessage(null);

    if (mode === 'login') {
      setIsSubmitting(true);
      try {
        const result = await login(username, password);
        if (!result.success) {
          setError(result.error || (configuredMode === 'mock'
            ? 'Usuario o correo no encontrado. Prueba con una cuenta demo o regístrate.'
            : 'No fue posible iniciar sesión.'));
          return;
        }
        onClose();
      } finally {
        setIsSubmitting(false);
      }
      return;
    }

    if (configuredMode === 'hybrid') {
      if (!username.trim() || !email.trim() || !artistName.trim() || !password || !confirmPassword) {
        setError('Completa los campos obligatorios del registro.');
        return;
      }

      if (password !== confirmPassword) {
        setError('Las contraseñas no coinciden.');
        return;
      }

      const form = new FormData();
      form.set('username', username.trim());
      form.set('email', email.trim());
      form.set('first_name', artistName.trim());
      form.set('last_name', lastName.trim());
      form.set('password1', password);
      form.set('password2', confirmPassword);
      form.set('tipo_usu', role === 'productor' ? '2' : '1');

      setIsSubmitting(true);
      try {
        const result = await registerAccount(form);
        if (!result.success) {
          const fieldErrors = result.errors
            ? Object.entries(result.errors)
                .map(([field, messages]) => `${field}: ${messages.join(' ')}`)
                .join(' ')
            : '';
          setError([result.error, fieldErrors].filter(Boolean).join(' '));
          return;
        }

        setSuccessMessage(result.message);
        setUsername('');
        setEmail('');
        setArtistName('');
        setLastName('');
        setPassword('');
        setConfirmPassword('');
      } finally {
        setIsSubmitting(false);
      }
      return;
    }

    // Registro de demostración: se conserva el comportamiento anterior.
    if (!username.trim() || !email.trim()) {
      setError('Por favor completa todos los campos requeridos.');
      return;
    }

    const displayName = [artistName.trim(), lastName.trim()].filter(Boolean).join(' ');
    registerUser(username, email, displayName, role);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-md bg-[#14151e] border border-zinc-700 rounded-3xl p-6 sm:p-8 shadow-2xl">
        <button
          onClick={onClose}
          disabled={isSubmitting}
          className="absolute top-5 right-5 text-zinc-400 hover:text-white p-2 rounded-full hover:bg-zinc-800"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-amber-400 text-zinc-950 font-black flex items-center justify-center mx-auto mb-3 shadow-lg shadow-amber-400/20">
            {mode === 'login' ? <LogIn className="w-6 h-6" /> : <UserPlus className="w-6 h-6" />}
          </div>
          <h2 className="text-2xl font-black text-white">
            {mode === 'login' ? 'Acceder a BeatsCloud' : 'Crear Cuenta en BeatsCloud'}
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            {mode === 'login'
              ? configuredMode === 'mock' ? 'Ingresa tus credenciales o selecciona una cuenta de prueba' : 'Ingresa tus credenciales'
              : 'Únete como productor de instrumentales o artista independiente'}
          </p>
        </div>

        {error && (
          <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs p-3 rounded-xl mb-4">
            {error}
          </div>
        )}

        {successMessage ? (
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-300">
            <p className="font-bold">Registro recibido</p>
            <p className="mt-2">{successMessage}</p>
            <p className="mt-2 text-xs text-emerald-200/80">
              La cuenta permanecerá inactiva hasta que confirmes el correo.
            </p>
            <button
              type="button"
              onClick={() => {
                setSuccessMessage(null);
                onSwitchMode('login');
              }}
              className="mt-4 rounded-lg bg-emerald-400 px-3 py-2 text-xs font-bold text-zinc-950"
            >
              Volver a iniciar sesión
            </button>
          </div>
        ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <>
              {/* Role Picker */}
              <div>
                <label className="text-xs font-bold text-zinc-300 block mb-2">
                  Tipo de Cuenta *
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setRole('artista')}
                    className={`p-3 rounded-2xl border text-left transition-all ${
                      role === 'artista'
                        ? 'border-amber-400 bg-amber-400/10 text-white'
                        : 'border-zinc-700 bg-zinc-900 text-zinc-400'
                    }`}
                  >
                    <Mic2
                      className={`w-5 h-5 mb-1.5 ${
                        role === 'artista' ? 'text-amber-400' : 'text-zinc-500'
                      }`}
                    />
                    <div className="text-xs font-bold">Artista</div>
                    <div className="text-[10px] text-zinc-400">Comprar beats</div>
                  </button>

                  <button
                    type="button"
                    onClick={() => setRole('productor')}
                    className={`p-3 rounded-2xl border text-left transition-all ${
                      role === 'productor'
                        ? 'border-amber-400 bg-amber-400/10 text-white'
                        : 'border-zinc-700 bg-zinc-900 text-zinc-400'
                    }`}
                  >
                    <Sliders
                      className={`w-5 h-5 mb-1.5 ${
                        role === 'productor' ? 'text-amber-400' : 'text-zinc-500'
                      }`}
                    />
                    <div className="text-xs font-bold">Productor</div>
                    <div className="text-[10px] text-zinc-400">Vender beats</div>
                  </button>
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-zinc-300 block mb-1">Nombre / nombre artístico *</label>
                <input
                  type="text"
                  required={configuredMode === 'hybrid'}
                  placeholder="Ej: MC Flow"
                  value={artistName}
                  onChange={(e) => setArtistName(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-400"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-zinc-300 block mb-1">Apellido</label>
                <input
                  type="text"
                  placeholder="Tu apellido"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-400"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-zinc-300 block mb-1">Correo Electrónico *</label>
                <input
                  type="email"
                  required
                  placeholder="tu@correo.cl"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-400"
                />
              </div>
            </>
          )}

          <div>
            <label className="text-xs font-bold text-zinc-300 block mb-1">
              Nombre de Usuario {mode === 'login' && 'o Correo'} *
            </label>
            <input
              type="text"
              required
              placeholder="mcflow, metrosantiago..."
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-400"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-zinc-300 block mb-1">Contraseña</label>
            <input
              type="password"
              required={configuredMode === 'hybrid'}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-400"
            />
          </div>

          {mode === 'register' && configuredMode === 'hybrid' && (
            <div>
              <label className="text-xs font-bold text-zinc-300 block mb-1">
                Confirmar contraseña *
              </label>
              <input
                type="password"
                required
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-400"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-amber-400 hover:bg-amber-300 text-zinc-950 font-black py-3 rounded-xl text-xs transition-all shadow-md shadow-amber-400/20 mt-2"
          >
            {isSubmitting ? 'Autenticando…' : mode === 'login' ? 'Iniciar Sesión' : 'Registrar Cuenta'}
          </button>
        </form>
        )}

        {/* Quick Demo Login Shortcut */}
        {configuredMode === 'mock' && <div className="mt-6 pt-5 border-t border-zinc-800">
          <p className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider mb-2 text-center">
            Acceso Rápido con Cuentas Demo:
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => {
                switchUser('user_prod_1');
                onClose();
              }}
              className="px-2.5 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-left text-xs text-zinc-300 flex items-center justify-between"
            >
              <span className="truncate">Metro Santiago</span>
              <span className="text-[9px] text-amber-400 uppercase font-bold ml-1">Prod</span>
            </button>
            <button
              onClick={() => {
                switchUser('user_art_1');
                onClose();
              }}
              className="px-2.5 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-left text-xs text-zinc-300 flex items-center justify-between"
            >
              <span className="truncate">MC Flow</span>
              <span className="text-[9px] text-emerald-400 uppercase font-bold ml-1">Artista</span>
            </button>
          </div>
        </div>}

        {/* Switch Mode Footer */}
        <div className="mt-4 text-center">
          {mode === 'login' ? (
            <button
              onClick={() => onSwitchMode('register')}
              className="text-xs text-zinc-400 hover:text-amber-400 transition-colors"
            >
              ¿No tienes cuenta? <span className="font-bold underline">Regístrate aquí</span>
            </button>
          ) : (
            <button
              onClick={() => onSwitchMode('login')}
              className="text-xs text-zinc-400 hover:text-amber-400 transition-colors"
            >
              ¿Ya tienes cuenta? <span className="font-bold underline">Inicia sesión</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
