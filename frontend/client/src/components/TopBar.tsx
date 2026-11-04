import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import {
  Search,
  ShoppingCart,
  Plus,
  Sliders,
  Bell,
  ChevronDown,
  User,
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
  onToggleMobileMenu?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  currentTab,
  setCurrentTab,
  onOpenUpload,
  onOpenAuth,
  onToggleMobileMenu,
}) => {
  const {
    currentUser,
    users,
    switchUser,
    configuredMode,
    cart,
    globalSearchQuery,
    setGlobalSearchQuery,
  } = useApp();

  const [showUserDropdown, setShowUserDropdown] = useState(false);

  const cartTotal = cart.reduce((sum, item) => sum + item.track.price, 0);

  const handleSearchChange = (val: string) => {
    setGlobalSearchQuery(val);
    if (val.trim() && currentTab !== 'catalogo') {
      setCurrentTab('catalogo');
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

      {/* Search Bar */}
      <div className="relative flex-1 max-w-lg">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
        <input
          type="text"
          placeholder="Buscar por beat, productor, BPM (ej: 140), escala (A Minor), género..."
          value={globalSearchQuery}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="w-full bg-[#131620] border border-[#23283a] focus:border-amber-400/80 pl-10 pr-9 py-2 rounded-xl text-xs text-white placeholder-zinc-400 focus:outline-none transition-all shadow-inner"
        />
        {globalSearchQuery && (
          <button
            onClick={() => setGlobalSearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

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
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <button
              onClick={() => onOpenAuth('login')}
              className="px-3 py-1.5 text-xs font-bold text-zinc-300 hover:text-white rounded-lg hover:bg-zinc-800 transition-colors"
            >
              Acceder
            </button>
            <button
              onClick={() => onOpenAuth('register')}
              className="px-3.5 py-1.5 text-xs font-bold bg-amber-400 hover:bg-amber-300 text-zinc-950 rounded-lg transition-colors"
            >
              Registrarse
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
