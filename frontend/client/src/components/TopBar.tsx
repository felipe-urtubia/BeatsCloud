import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import {
  ShoppingCart,
  Plus,
  Sliders,
  Bell,
  ChevronDown,
  User,
  LogIn,
  UserPlus,
  LogOut,
  UserCheck,
  Disc3,
  X,
  Menu,
} from 'lucide-react';

interface TopBarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  onOpenUpload: () => void;
  onOpenAuth: (mode: 'login' | 'register') => void;
  onOpenAccountDeletion: () => void;
  onToggleMobileMenu?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  currentTab,
  setCurrentTab,
  onOpenUpload,
  onOpenAuth,
  onOpenAccountDeletion,
  onToggleMobileMenu,
}) => {
  const {
    currentUser,
    users,
    switchUser,
    authorizedAccounts,
    isSwitchingAccount,
    addAuthorizedAccount,
    changeAuthorizedAccount,
    configuredMode,
    logout,
    cart,
  } = useApp();

  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [accountUsername, setAccountUsername] = useState('');
  const [accountPassword, setAccountPassword] = useState('');
  const [accountError, setAccountError] = useState<string | null>(null);
  const [isAddingAccount, setIsAddingAccount] = useState(false);

  const handleAddAccount = async () => {
    if (isAddingAccount || isSwitchingAccount || isLoggingOut) return;

    setAccountError(null);
    setIsAddingAccount(true);

    try {
      const result = await addAuthorizedAccount(
        accountUsername.trim(),
        accountPassword,
      );

      // No conservar la contrase?a despu?s del intento.
      setAccountPassword('');

      if (!result.success) {
        setAccountError(result.error);
        return;
      }

      setAccountUsername('');
      setShowAddAccount(false);
    } catch {
      setAccountPassword('');
      setAccountError('No fue posible agregar la cuenta.');
    } finally {
      setIsAddingAccount(false);
    }
  };

  const handleChangeAccount = async (userId: number) => {
    if (isSwitchingAccount || isAddingAccount || isLoggingOut) return;

    setAccountError(null);

    try {
      const result = await changeAuthorizedAccount(userId);
      if (!result.success) {
        setAccountError(result.error);
      }
      // Si Django confirma el cambio, AppContext recarga la pagina.
    } catch {
      setAccountError('No fue posible cambiar de cuenta.');
    }
  };

  const cartTotal = cart.reduce((sum, item) => sum + item.track.price, 0);

  const handleLogout = async () => {
    if (isLoggingOut || isAddingAccount || isSwitchingAccount) return;
    setLogoutError(null);
    setIsLoggingOut(true);

    try {
      const result = await logout();
      if (!result.success) {
        setLogoutError(result.error);
        return;
      }
      setShowUserDropdown(false);
    } finally {
      setIsLoggingOut(false);
    }
  };


  return (
    <header className="h-16 bg-[#0a0c10]/95 backdrop-blur-md border-b border-[#1a1e2b] px-4 sm:px-6 flex items-center justify-between sticky top-0 z-20 gap-3">
      {/* Mobile Toggle Button */}
      {onToggleMobileMenu && (
        <button
          onClick={onToggleMobileMenu}
          className="md:hidden p-2 rounded-xl bg-[#131620] border border-[#23283a] text-zinc-300 hover:text-white"
          title="Abrir menú"
        >
          <Menu className="w-4 h-4" />
        </button>
      )}

      <div className="flex-1" />
      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Upload Button for Producers */}
        {currentUser?.role === 'productor' && (
          <button
            onClick={onOpenUpload}
            className="flex items-center gap-1.5 bg-amber-400 hover:bg-amber-300 text-zinc-950 font-black px-3.5 py-2 rounded-xl text-xs transition-transform hover:scale-102 shadow-sm"
          >
            <Plus className="w-3.5 h-3.5 stroke-[3]" />
            <span>Subir Beat</span>
          </button>
        )}

        {/* Shopping Cart Button */}
        <button
          onClick={() => setCurrentTab('carrito')}
          className={`relative p-2.5 rounded-xl border transition-all flex items-center gap-2 ${
            currentTab === 'carrito'
              ? 'bg-amber-400/15 border-amber-400/50 text-amber-400'
              : 'bg-[#131620] border-[#23283a] text-zinc-300 hover:text-white hover:border-zinc-700'
          }`}
          title="Ver Carrito de Compras"
        >
          <ShoppingCart className="w-4 h-4" />
          {cart.length > 0 && (
            <>
              <span className="text-[11px] font-mono font-bold text-amber-400 hidden sm:inline">
                ${cartTotal.toLocaleString('es-CL')}
              </span>
              <span className="w-4 h-4 rounded-full bg-amber-400 text-zinc-950 text-[10px] font-black flex items-center justify-center -ml-1">
                {cart.length}
              </span>
            </>
          )}
        </button>

        {/* User Switcher Dropdown */}
        {currentUser ? (
          <div className="relative">
            <button
              onClick={() => setShowUserDropdown(!showUserDropdown)}
              className="flex items-center gap-2 p-1 pl-2.5 rounded-xl border border-[#23283a] bg-[#131620] hover:bg-[#1a1e2d] transition-colors"
            >
              <div className="text-right hidden sm:block">
                <p className="text-xs font-bold text-white leading-tight">
                  {currentUser.artistName}
                </p>
                <p className="text-[9px] text-zinc-400 uppercase font-mono">
                  {currentUser.role}
                </p>
              </div>
              <img
                src={currentUser.avatarUrl}
                alt={currentUser.username}
                className="w-8 h-8 rounded-lg object-cover ring-1 ring-amber-400/40"
              />
              <ChevronDown className="w-3.5 h-3.5 text-zinc-400 mr-1" />
            </button>

            {/* Dropdown Menu */}
            {showUserDropdown && (
              <div
                className="absolute right-0 mt-2 w-64 bg-[#141724] border border-[#23283a] rounded-2xl shadow-2xl py-2 z-50 animate-in fade-in zoom-in-95 duration-100"
                onMouseLeave={() => setShowUserDropdown(false)}
              >
                <div className="px-4 py-2 border-b border-[#23283a]">
                  <p className="text-xs font-bold text-white truncate">{currentUser.artistName}</p>
                  <p className="text-[11px] text-zinc-400 truncate">@{currentUser.username}</p>
                  <div className="mt-1.5 inline-block text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-400/20 text-amber-300">
                    Modo: {currentUser.role === 'productor' ? 'Productor Musical' : 'Artista / Cantante'}
                  </div>
                </div>

                <div className="py-1">
                  <button
                    onClick={() => {
                      setCurrentTab('perfil');
                      setShowUserDropdown(false);
                    }}
                    className="w-full text-left px-4 py-2 text-xs font-semibold text-zinc-200 hover:bg-zinc-800 flex items-center gap-2"
                  >
                    <User className="w-3.5 h-3.5 text-amber-400" />
                    <span>Ver Mi Perfil de {currentUser.role === 'productor' ? 'Productor' : 'Artista'}</span>
                  </button>
                </div>

                {configuredMode === 'hybrid' && (
                  <div className="border-t border-[#23283a] px-4 py-3">
                    <p className="text-[10px] font-mono font-bold text-zinc-400 uppercase tracking-wider mb-2">
                      Cambiar de cuenta
                    </p>

                    <div className="space-y-1 mb-2">
                      {authorizedAccounts.map((account) => (
                        <button
                          key={account.id}
                          type="button"
                          disabled={
                            account.is_current ||
                            isSwitchingAccount ||
                            isAddingAccount ||
                            isLoggingOut
                          }
                          onClick={() => void handleChangeAccount(account.id)}
                          className={`w-full flex items-center justify-between gap-2 px-2.5 py-2 rounded-lg text-xs transition-colors disabled:cursor-default ${
                            account.is_current
                              ? 'bg-amber-400/15 text-amber-300 font-bold'
                              : 'text-zinc-200 hover:bg-zinc-800 disabled:opacity-50'
                          }`}
                        >
                          <span className="truncate">@{account.username}</span>
                          <span className="shrink-0 text-[10px]">
                            {account.is_current ? 'Activa' : 'Cambiar'}
                          </span>
                        </button>
                      ))}
                    </div>

                    {showAddAccount ? (
                      <form
                        className="space-y-2"
                        onSubmit={(event) => {
                          event.preventDefault();
                          void handleAddAccount();
                        }}
                      >
                        <label className="block text-[11px] text-zinc-300">
                          Usuario de la otra cuenta
                          <input
                            type="text"
                            required
                            maxLength={150}
                            autoComplete="username"
                            value={accountUsername}
                            onChange={(event) => setAccountUsername(event.target.value)}
                            disabled={isAddingAccount || isSwitchingAccount}
                            className="mt-1 w-full rounded-lg border border-[#323748] bg-[#0a0c10] text-white px-3 py-2 text-xs outline-none focus:border-amber-400"
                          />
                        </label>

                        <label className="block text-[11px] text-zinc-300">
                          Contrase?a
                          <input
                            type="password"
                            required
                            autoComplete="current-password"
                            value={accountPassword}
                            onChange={(event) => setAccountPassword(event.target.value)}
                            disabled={isAddingAccount || isSwitchingAccount}
                            className="mt-1 w-full rounded-lg border border-[#323748] bg-[#0a0c10] text-white px-3 py-2 text-xs outline-none focus:border-amber-400"
                          />
                        </label>

                        <div className="flex gap-2">
                          <button
                            type="submit"
                            disabled={isAddingAccount || isSwitchingAccount || isLoggingOut}
                            className="flex-1 rounded-lg bg-amber-400 px-2 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
                          >
                            {isAddingAccount ? 'Agregando...' : 'Agregar cuenta'}
                          </button>

                          <button
                            type="button"
                            disabled={isAddingAccount}
                            onClick={() => {
                              setAccountPassword('');
                              setAccountUsername('');
                              setAccountError(null);
                              setShowAddAccount(false);
                            }}
                            className="rounded-lg px-2 py-2 text-xs text-zinc-300 hover:bg-zinc-800 disabled:opacity-50"
                          >
                            Cancelar
                          </button>
                        </div>
                      </form>
                    ) : (
                      <button
                        type="button"
                        disabled={isSwitchingAccount || isLoggingOut}
                        onClick={() => {
                          setAccountError(null);
                          setShowAddAccount(true);
                        }}
                        className="w-full flex items-center gap-2 px-2.5 py-2 text-xs font-semibold text-amber-400 hover:bg-zinc-800 rounded-lg disabled:opacity-50"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        Agregar otra cuenta
                      </button>
                    )}

                    {isSwitchingAccount && (
                      <p role="status" className="text-xs text-zinc-400 mt-2">
                        Cambiando de cuenta...
                      </p>
                    )}

                    {accountError && (
                      <p role="alert" className="text-xs text-rose-400 mt-2">
                        {accountError}
                      </p>
                    )}
                  </div>
                )}

                {/* Switch between demo accounts */}
                {configuredMode === 'mock' && <>
                <div className="border-t border-[#23283a] px-4 py-2">
                  <p className="text-[10px] font-mono font-bold text-zinc-400 uppercase tracking-wider mb-1.5">
                    Probar con otra cuenta demo:
                  </p>
                  <div className="space-y-1">
                    {users.map((u) => (
                      <button
                        key={u.id}
                        onClick={() => {
                          switchUser(u.id);
                          setShowUserDropdown(false);
                        }}
                        className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs flex items-center justify-between transition-colors ${
                          u.id === currentUser.id
                            ? 'bg-amber-400/20 text-amber-300 font-bold'
                            : 'text-zinc-300 hover:bg-zinc-800/80'
                        }`}
                      >
                        <span className="truncate">{u.artistName}</span>
                        <span className="text-[9px] font-mono uppercase text-zinc-400 ml-1">
                          {u.role}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
                </>}

                <div className="border-t border-[#23283a] pt-1">
                  <button
                    onClick={() => {
                      onOpenAuth('register');
                      setShowUserDropdown(false);
                    }}
                    className="w-full text-left px-4 py-2 text-xs text-amber-400 hover:bg-zinc-800 flex items-center gap-2 font-semibold"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Crear nueva cuenta</span>
                  </button>
                </div>

                {logoutError && (
                  <p role="alert" className="px-4 py-2 text-xs text-rose-400">
                    {logoutError}
                  </p>
                )}

                {configuredMode === 'hybrid' && (
                  <div className="border-t border-[#23283a] pt-1">
                    <button
                      type="button"
                      onClick={() => {
                        onOpenAccountDeletion();
                        setShowUserDropdown(false);
                      }}
                      className="w-full text-left px-4 py-2 text-xs text-red-400 hover:bg-zinc-800 flex items-center gap-2 font-semibold"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Eliminar cuenta</span>
                    </button>
                  </div>
                )}

                <div className="border-t border-[#23283a] pt-1">
                  <button
                    type="button"
                    disabled={isLoggingOut || isAddingAccount || isSwitchingAccount}
                    onClick={() => void handleLogout()}
                    className="w-full text-left px-4 py-2 text-xs text-red-400 hover:bg-zinc-800 flex items-center gap-2 font-semibold disabled:opacity-50"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>{isLoggingOut ? 'Cerrando sesión…' : 'Cerrar sesión'}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <button
              onClick={() => onOpenAuth('login')}
              className="inline-flex items-center gap-1.5 rounded-lg border border-amber-300/70 bg-amber-400 px-4 py-2 text-xs font-extrabold text-zinc-950 shadow-[0_0_18px_rgba(251,191,36,0.22)] transition-all hover:-translate-y-0.5 hover:bg-amber-300 hover:shadow-[0_0_24px_rgba(251,191,36,0.38)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0a0c10]"
            >
              <LogIn className="h-3.5 w-3.5" />
              Acceder
            </button>
            <button
              onClick={() => onOpenAuth('register')}
              className="inline-flex items-center gap-1.5 rounded-lg border border-orange-300 bg-orange-400 px-4 py-2 text-xs font-extrabold text-zinc-950 shadow-[0_0_20px_rgba(251,146,60,0.35)] transition-all hover:-translate-y-0.5 hover:bg-orange-300 hover:shadow-[0_0_26px_rgba(251,146,60,0.5)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-200 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0a0c10]"
            >
              <UserPlus className="h-3.5 w-3.5" />
              Registrarse
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
