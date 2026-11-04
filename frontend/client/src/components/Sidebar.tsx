import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { LicenseContract, ResourceType } from '../types';
import { LicenseVerificationModal } from './LicenseVerificationModal';
import { LicenseCertificateModal } from './LicenseCertificateModal';
import {
  Compass,
  Disc3,
  Sliders,
  Mic2,
  FileMusic,
  ShoppingBag,
  DollarSign,
  Users,
  Sparkles,
  Music2,
  Layers,
  Heart,
  PlusCircle,
  Repeat,
  Radio,
  ChevronRight,
  ShieldCheck,
  UserCheck,
  BadgeCheck,
  X,
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  onOpenUpload: () => void;
  onOpenAuth: (mode: 'login' | 'register') => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  onOpenUpload,
  onOpenAuth,
  isMobileOpen = false,
  onCloseMobile,
}) => {
  const {
    currentUser,
    users,
    switchUser,
    configuredMode,
    activeResourceFilter,
    setActiveResourceFilter,
    cart,
    purchases,
    tracks,
  } = useApp();

  // Verificador público de licencias (registro oficial de transacciones)
  const [verifyOpen, setVerifyOpen] = useState(false);
  const [viewingContract, setViewingContract] = useState<LicenseContract | null>(null);

  const handleSelectResourceFilter = (filter: ResourceType) => {
    setActiveResourceFilter(filter);
    setCurrentTab('catalogo');
    onCloseMobile?.();
  };

  const handleTabChange = (tab: string) => {
    setCurrentTab(tab);
    onCloseMobile?.();
  };

  const isProducer = currentUser?.role === 'productor';

  const sidebarContent = (
    <div className="flex flex-col justify-between h-full bg-[#0d0f15]">
      {/* Brand Header */}
      <div>
        <div className="p-5 border-b border-[#1a1e2b] flex items-center justify-between">
          <button
            onClick={() => {
              setActiveResourceFilter('all');
              handleTabChange('descubrir');
            }}
            className="flex items-center gap-2.5 text-left group"
          >
            <div className="w-9 h-9 rounded-xl bg-amber-400 flex items-center justify-center text-zinc-950 font-black shadow-md shadow-amber-400/20 group-hover:scale-105 transition-transform">
              <Music2 className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <span className="text-base font-black tracking-tight text-white flex items-center gap-1">
                Beats<span className="text-amber-400">Cloud</span>
              </span>
              <span className="text-[10px] text-zinc-400 font-mono tracking-wider block">
                STUDIO APP v2.4
              </span>
            </div>
          </button>

          {/* Close button on mobile */}
          {onCloseMobile && (
            <button
              onClick={onCloseMobile}
              className="md:hidden text-zinc-400 hover:text-white p-1.5 rounded-lg hover:bg-zinc-800"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Navigation Sections */}
        <div className="p-3 space-y-6 overflow-y-auto max-h-[calc(100vh-210px)] scrollbar-none">
          {/* Main Exploratory Area */}
          <div>
            <span className="px-3 text-[10px] font-bold text-zinc-400 uppercase tracking-widest block mb-1.5 font-mono">
              Explorar
            </span>
            <div className="space-y-0.5">
              <button
                onClick={() => {
                  setActiveResourceFilter('all');
                  handleTabChange('descubrir');
                }}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
                  currentTab === 'descubrir'
                    ? 'bg-amber-400/15 text-amber-400 border border-amber-400/30 font-extrabold'
                    : 'text-zinc-300 hover:text-white hover:bg-zinc-800/50'
                }`}
              >
                <Compass className="w-4 h-4 text-amber-400" />
                <span>Descubrir & Trends</span>
              </button>

              <button
                onClick={() => {
                  setActiveResourceFilter('all');
                  handleTabChange('catalogo');
                }}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
                  currentTab === 'catalogo' && activeResourceFilter === 'all'
                    ? 'bg-amber-400/15 text-amber-400 border border-amber-400/30'
                    : 'text-zinc-300 hover:text-white hover:bg-zinc-800/50'
                }`}
              >
                <Disc3 className="w-4 h-4" />
                <span>Catálogo General</span>
                <span className="ml-auto text-[10px] font-mono text-zinc-400 bg-zinc-900 px-1.5 py-0.5 rounded">
                  {tracks.length}
                </span>
              </button>
            </div>
          </div>

          {/* Audio Resource Categories */}
          <div>
            <span className="px-3 text-[10px] font-bold text-zinc-400 uppercase tracking-widest block mb-1.5 font-mono">
              Tipos de Audio
            </span>
            <div className="space-y-0.5">
              <button
                onClick={() => handleSelectResourceFilter('instrumental')}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                  currentTab === 'catalogo' && activeResourceFilter === 'instrumental'
                    ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 font-bold'
                    : 'text-zinc-300 hover:text-white hover:bg-zinc-800/50'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-sky-400" />
                <span>Instrumentales</span>
              </button>

              <button
                onClick={() => handleSelectResourceFilter('loop')}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                  currentTab === 'catalogo' && activeResourceFilter === 'loop'
                    ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30 font-bold'
                    : 'text-zinc-300 hover:text-white hover:bg-zinc-800/50'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <span>Loops & Melodías</span>
              </button>

              <button
                onClick={() => handleSelectResourceFilter('acapella')}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                  currentTab === 'catalogo' && activeResourceFilter === 'acapella'
                    ? 'bg-purple-500/15 text-purple-400 border border-purple-500/30 font-bold'
                    : 'text-zinc-300 hover:text-white hover:bg-zinc-800/50'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-purple-400" />
                <span>Acapellas & Voces</span>
              </button>

              <button
                onClick={() => handleSelectResourceFilter('drumkit')}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                  currentTab === 'catalogo' && activeResourceFilter === 'drumkit'
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold'
                    : 'text-zinc-300 hover:text-white hover:bg-zinc-800/50'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span>Drum Kits & 808s</span>
              </button>
            </div>
          </div>

          {/* User Workspace (Dynamic per role) */}
          <div>
            <div className="flex items-center justify-between px-3 mb-1.5">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest font-mono">
                {isProducer ? 'Mi Estudio (Productor)' : 'Mi Biblioteca (Artista)'}
              </span>
            </div>

            <div className="space-y-0.5">
              {isProducer ? (
                <>
                  <button
                    onClick={() => handleTabChange('perfil')}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
                      currentTab === 'perfil'
                        ? 'bg-amber-400/15 text-amber-400 border border-amber-400/30'
                        : 'text-zinc-300 hover:text-white hover:bg-zinc-800/50'
                    }`}
                  >
                    <Sliders className="w-4 h-4 text-amber-400" />
                    <span>Mis Producciones</span>
                  </button>

                  <button
                    onClick={() => {
                      onOpenUpload();
                      onCloseMobile?.();
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold text-amber-300 bg-amber-400/10 hover:bg-amber-400/20 border border-amber-400/30 transition-colors"
                  >
                    <PlusCircle className="w-4 h-4 text-amber-400" />
                    <span>Subir Track + Análisis</span>
                  </button>

                  <button
                    onClick={() => handleTabChange('ventas')}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
                      currentTab === 'ventas'
                        ? 'bg-amber-400/15 text-amber-400 border border-amber-400/30'
                        : 'text-zinc-300 hover:text-white hover:bg-zinc-800/50'
                    }`}
                  >
                    <DollarSign className="w-4 h-4 text-emerald-400" />
                    <span>Ventas & Transacciones</span>
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => handleTabChange('perfil')}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
                      currentTab === 'perfil'
                        ? 'bg-amber-400/15 text-amber-400 border border-amber-400/30'
                        : 'text-zinc-300 hover:text-white hover:bg-zinc-800/50'
                    }`}
                  >
                    <FileMusic className="w-4 h-4 text-emerald-400" />
                    <span>Archivos Comprados</span>
                    <span className="ml-auto text-[10px] font-mono text-zinc-400 bg-zinc-900 px-1.5 py-0.5 rounded">
                      {purchases.length}
                    </span>
                  </button>

                  <button
                    onClick={() => handleTabChange('favoritos')}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
                      currentTab === 'favoritos'
                        ? 'bg-amber-400/15 text-amber-400 border border-amber-400/30'
                        : 'text-zinc-300 hover:text-white hover:bg-zinc-800/50'
                    }`}
                  >
                    <Heart className="w-4 h-4 text-rose-400" />
                    <span>Favoritos Guardados</span>
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Community Directory */}
          <div>
            <span className="px-3 text-[10px] font-bold text-zinc-400 uppercase tracking-widest block mb-1.5 font-mono">
              Comunidad
            </span>
            <button
              onClick={() => handleTabChange('usuarios')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
                currentTab === 'usuarios'
                  ? 'bg-amber-400/15 text-amber-400 border border-amber-400/30'
                  : 'text-zinc-300 hover:text-white hover:bg-zinc-800/50'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Directorio de Creadores</span>
            </button>
            <button
              onClick={() => setVerifyOpen(true)}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold transition-all mt-1 text-zinc-400 hover:text-amber-300 hover:bg-amber-400/5"
              title="Consultar el registro oficial de licencias emitidas por Webpay"
            >
              <BadgeCheck className="w-4 h-4" />
              <span>Verificar Licencia</span>
            </button>
            <button
              onClick={() => handleTabChange('sobre_nosotros')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold transition-all mt-1 ${
                currentTab === 'sobre_nosotros'
                  ? 'bg-amber-400/15 text-amber-400 border border-amber-400/30'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Sobre BeatsCloud</span>
            </button>
          </div>
        </div>
      </div>

      {/* Public License Verification Registry */}
      <LicenseVerificationModal
        isOpen={verifyOpen}
        onClose={() => setVerifyOpen(false)}
        onViewContract={(contract) => {
          setVerifyOpen(false);
          setViewingContract(contract);
        }}
      />

      {/* Official License Certificate (from public verifier) */}
      <LicenseCertificateModal
        isOpen={viewingContract !== null}
        onClose={() => setViewingContract(null)}
        contract={viewingContract}
      />

      {/* User Footer Profile & Demo Switcher */}
      <div className="p-3 border-t border-[#1a1e2b] bg-[#0a0c10]">
        {currentUser ? (
          <div className="bg-[#12151f] p-2.5 rounded-2xl border border-zinc-800/80">
            <div className="flex items-center gap-2.5 mb-2">
              <img
                src={currentUser.avatarUrl}
                alt={currentUser.username}
                className="w-8 h-8 rounded-xl object-cover ring-1 ring-amber-400/50"
              />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-bold text-white truncate leading-tight">
                  {currentUser.artistName || currentUser.username}
                </p>
                <span
                  className={`text-[9px] font-mono font-bold uppercase tracking-wider block ${
                    isProducer ? 'text-amber-400' : 'text-emerald-400'
                  }`}
                >
                  {isProducer ? '🎧 Productor' : '🎤 Artista'}
                </span>
              </div>
            </div>

            {/* Quick Demo Switcher Selector */}
            {configuredMode === 'mock' && <div className="pt-2 border-t border-zinc-800/60 flex items-center justify-between">
              <span className="text-[9px] text-zinc-400 font-mono">Alternar rol:</span>
              <button
                onClick={() => {
                  const nextId = isProducer ? 'user_art_1' : 'user_prod_1';
                  switchUser(nextId);
                }}
                className="text-[10px] font-bold text-amber-400 hover:text-amber-300 bg-zinc-800/80 hover:bg-zinc-700 px-2 py-0.5 rounded-md transition-colors flex items-center gap-1"
                title="Cambiar entre vista de Productor y vista de Artista"
              >
                <Repeat className="w-3 h-3" />
                <span>Ver como {isProducer ? 'Artista' : 'Productor'}</span>
              </button>
            </div>}
          </div>
        ) : (
          <button
            onClick={() => {
              onOpenAuth('login');
              onCloseMobile?.();
            }}
            className="w-full py-2 bg-amber-400 text-zinc-950 font-bold rounded-xl text-xs hover:bg-amber-300 transition-colors"
          >
            Iniciar Sesión
          </button>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden md:flex w-64 border-r border-[#1a1e2b] flex-col justify-between h-screen sticky top-0 select-none z-30 flex-shrink-0">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-black/75 backdrop-blur-sm"
            onClick={onCloseMobile}
          />
          <div className="relative w-72 max-w-[80vw] h-full shadow-2xl z-10 animate-in slide-in-from-left duration-200">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
