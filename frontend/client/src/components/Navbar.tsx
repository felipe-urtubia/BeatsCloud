import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { ShoppingCart, Music2, User as UserIcon, LogOut, ChevronDown, Sparkles } from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  onOpenAuth: (mode: 'login' | 'register') => void;
  onOpenUpload: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  onOpenAuth,
  onOpenUpload,
}) => {
  const { currentUser, users, switchUser, cart, configuredMode } = useApp();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  const cartCount = cart.length;

  return (
    <nav className="sticky top-0 z-40 bg-[#121318]/95 backdrop-blur-md border-b border-zinc-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setCurrentTab('inicio')}
              className="flex items-center gap-2.5 text-left group focus:outline-none"
            >
              <div className="w-10 h-10 rounded-xl bg-amber-400 flex items-center justify-center text-zinc-950 font-black shadow-lg shadow-amber-400/20 group-hover:scale-105 transition-transform">
                <Music2 className="w-6 h-6 stroke-[2.5]" />
              </div>
              <div>
                <span className="text-xl font-black tracking-tight text-white flex items-center gap-1">
                  Beats<span className="text-amber-400">Cloud</span>
                </span>
                <span className="text-[10px] text-zinc-400 tracking-wider font-semibold block uppercase">
                  Music Marketplace
                </span>
              </div>
            </button>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-1 ml-8">
              <button
                onClick={() => setCurrentTab('inicio')}
                className={`px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                  currentTab === 'inicio'
                    ? 'bg-zinc-800 text-amber-400 shadow-inner'
                    : 'text-zinc-300 hover:text-white hover:bg-zinc-800/60'
                }`}
              >
                Inicio
              </button>
              <button
                onClick={() => setCurrentTab('catalogo')}
                className={`px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                  currentTab === 'catalogo'
                    ? 'bg-zinc-800 text-amber-400 shadow-inner'
                    : 'text-zinc-300 hover:text-white hover:bg-zinc-800/60'
                }`}
              >
                Catálogo
              </button>
              <button
                onClick={() => setCurrentTab('usuarios')}
                className={`px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                  currentTab === 'usuarios'
                    ? 'bg-zinc-800 text-amber-400 shadow-inner'
                    : 'text-zinc-300 hover:text-white hover:bg-zinc-800/60'
                }`}
              >
                Comunidad
              </button>
              <button
                onClick={() => setCurrentTab('sobre_nosotros')}
                className={`px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                  currentTab === 'sobre_nosotros'
                    ? 'bg-zinc-800 text-amber-400 shadow-inner'
                    : 'text-zinc-300 hover:text-white hover:bg-zinc-800/60'
                }`}
              >
                Sobre Nosotros
              </button>
            </div>
          </div>

          {/* Right Action Buttons */}
          <div className="flex items-center gap-3">
            {/* Quick Upload Button for Producers */}
            {currentUser?.role === 'productor' && (
              <button
                onClick={onOpenUpload}
                className="hidden sm:flex items-center gap-2 bg-amber-400 hover:bg-amber-300 text-zinc-950 font-bold px-3.5 py-1.5 rounded-lg text-xs transition-colors shadow-sm"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Subir Beat</span>
              </button>
            )}

            {/* Shopping Cart Button */}
            <button
              onClick={() => setCurrentTab('carrito')}
              className={`relative p-2 rounded-xl border transition-all ${
                currentTab === 'carrito'
                  ? 'border-amber-400/50 bg-amber-400/10 text-amber-400'
                  : 'border-zinc-700/60 bg-zinc-800/60 text-zinc-300 hover:text-white hover:border-zinc-600'
              }`}
              title="Carrito de compras"
            >
              <ShoppingCart className="w-5 h-5" />
              {cartCount > 0 && (
                <span className="absolute -top-1.5 -right-1.5 bg-amber-400 text-zinc-950 text-xs font-black w-5 h-5 rounded-full flex items-center justify-center ring-2 ring-[#121318]">
                  {cartCount}
                </span>
              )}
            </button>

            {/* User Profile / Quick Switcher */}
            {currentUser ? (
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 p-1.5 pl-2.5 rounded-xl border border-zinc-700/60 bg-zinc-800/60 hover:bg-zinc-800 transition-colors text-left"
                >
                  <div className="hidden sm:block">
                    <p className="text-xs font-bold text-white leading-tight">
                      {currentUser.artistName || currentUser.username}
                    </p>
                    <p className="text-[10px] text-amber-400 font-semibold uppercase tracking-wider">
                      {currentUser.role === 'productor' ? '🎧 Productor' : '🎤 Artista'}
                    </p>
                  </div>
                  <img
                    src={currentUser.avatarUrl}
                    alt={currentUser.username}
                    className="w-8 h-8 rounded-lg object-cover ring-1 ring-amber-400/40"
                  />
                  <ChevronDown className="w-3.5 h-3.5 text-zinc-400" />
                </button>

                {/* Dropdown Menu */}
                {showUserMenu && (
                  <div
                    className="absolute right-0 mt-2 w-64 bg-[#181a22] border border-zinc-700 rounded-xl shadow-2xl py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150"
                    onMouseLeave={() => setShowUserMenu(false)}
                  >
                    <div className="px-4 py-2 border-b border-zinc-700/60">
                      <p className="text-sm font-bold text-white truncate">
                        {currentUser.artistName}
                      </p>
                      <p className="text-xs text-zinc-400 truncate">@{currentUser.username}</p>
                      <span className="inline-block mt-1 text-[11px] font-bold px-2 py-0.5 rounded bg-amber-400/20 text-amber-300">
                        Cuenta de {currentUser.role === 'productor' ? 'Productor' : 'Artista'}
                      </span>
                    </div>

                    <div className="py-1">
                      <button
                        onClick={() => {
                          setCurrentTab('perfil');
                          setShowUserMenu(false);
                        }}
                        className="w-full text-left px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-800 flex items-center gap-2"
                      >
                        <UserIcon className="w-4 h-4 text-amber-400" />
                        Ver Mi Perfil
                      </button>
                    </div>

                    {/* Quick switch between demo accounts */}
                    {configuredMode === 'mock' && <>
                    <div className="border-t border-zinc-700/60 px-4 py-2">
                      <p className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider mb-1.5">
                        Cambio rápido de cuenta:
                      </p>
                      <div className="space-y-1">
                        {users.map((u) => (
                          <button
                            key={u.id}
                            onClick={() => {
                              switchUser(u.id);
                              setShowUserMenu(false);
                            }}
                            className={`w-full text-left px-2 py-1 rounded text-xs flex items-center justify-between transition-colors ${
                              u.id === currentUser.id
                                ? 'bg-amber-400/20 text-amber-300 font-bold'
                                : 'text-zinc-300 hover:bg-zinc-800'
                            }`}
                          >
                            <span className="truncate">{u.artistName}</span>
                            <span className="text-[10px] text-zinc-400 uppercase ml-1">
                              {u.role}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                    </>}

                    <div className="border-t border-zinc-700/60 pt-1">
                      <button
                        onClick={() => {
                          onOpenAuth('login');
                          setShowUserMenu(false);
                        }}
                        className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-zinc-800/80 flex items-center gap-2"
                      >
                        <LogOut className="w-4 h-4" />
                        Cambiar de sesión / Registrar
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onOpenAuth('login')}
                  className="px-3.5 py-1.5 text-xs font-bold text-zinc-200 hover:text-white rounded-lg hover:bg-zinc-800 transition-colors"
                >
                  Acceder
                </button>
                <button
                  onClick={() => onOpenAuth('register')}
                  className="px-3.5 py-1.5 text-xs font-bold bg-amber-400 hover:bg-amber-300 text-zinc-950 rounded-lg transition-colors shadow-sm"
                >
                  Registrarse
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Submenu Bar */}
      <div className="md:hidden border-t border-zinc-800/80 px-4 py-2 flex items-center justify-around bg-[#0f1014]">
        <button
          onClick={() => setCurrentTab('inicio')}
          className={`text-xs font-semibold py-1 px-2 rounded ${
            currentTab === 'inicio' ? 'text-amber-400 font-bold' : 'text-zinc-400'
          }`}
        >
          Inicio
        </button>
        <button
          onClick={() => setCurrentTab('catalogo')}
          className={`text-xs font-semibold py-1 px-2 rounded ${
            currentTab === 'catalogo' ? 'text-amber-400 font-bold' : 'text-zinc-400'
          }`}
        >
          Catálogo
        </button>
        <button
          onClick={() => setCurrentTab('usuarios')}
          className={`text-xs font-semibold py-1 px-2 rounded ${
            currentTab === 'usuarios' ? 'text-amber-400 font-bold' : 'text-zinc-400'
          }`}
        >
          Comunidad
        </button>
        <button
          onClick={() => setCurrentTab('perfil')}
          className={`text-xs font-semibold py-1 px-2 rounded ${
            currentTab === 'perfil' ? 'text-amber-400 font-bold' : 'text-zinc-400'
          }`}
        >
          Perfil
        </button>
      </div>
    </nav>
  );
};
