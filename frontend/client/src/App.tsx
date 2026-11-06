import React, { useState, useEffect } from 'react';
import { useApp } from './context/AppContext';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { GlobalAudioPlayer } from './components/GlobalAudioPlayer';
import { DiscoverPage } from './components/DiscoverPage';
import { CatalogPage } from './components/CatalogPage';
import { CartPage } from './components/CartPage';
import { UsersCatalogPage } from './components/UsersCatalogPage';
import { ProducerProfilePage } from './components/ProducerProfilePage';
import { ArtistProfilePage } from './components/ArtistProfilePage';
import { AboutPage } from './components/AboutPage';
import { TrackDetailModal } from './components/TrackDetailModal';
import { UploadTrackModal } from './components/UploadTrackModal';
import { AuthModal } from './components/AuthModal';
import { Track, UserType } from './types';
import { BackendStatusBanner } from './components/BackendStatusBanner';
import { X } from 'lucide-react';
import { AccountDeletionModal } from './components/AccountDeletionModal';

export const App: React.FC = () => {
  const { currentUser, users, paymentNotice, clearPaymentNotice } = useApp();

  const [currentTab, setCurrentTab] = useState<string>(
    () => new URLSearchParams(window.location.search).get('profile')
      ? 'perfil_externo'
      : 'descubrir',
  );
  const [selectedTrackId, setSelectedTrackId] = useState<string | null>(
    () => new URLSearchParams(window.location.search).get('track') || null,
  );

  // Profile view state
  const [viewedProfileUsername, setViewedProfileUsername] = useState<string | null>(
    () => new URLSearchParams(window.location.search).get('profile')?.trim() || null,
  );

  const viewedProfile = viewedProfileUsername
    ? users.find((user) => user.username === viewedProfileUsername) || null
    : null;

  // Modals & Mobile state
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [trackToEdit, setTrackToEdit] = useState<Track | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(
    () => new URLSearchParams(window.location.search).get('auth') === 'login',
  );
  const [accountDeletionOpen, setAccountDeletionOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  useEffect(() => {
    const syncTrackFromUrl = () => {
      const params = new URLSearchParams(window.location.search);

      setSelectedTrackId(params.get('track') || null);

      const username = params.get('profile')?.trim() || null;

      setViewedProfileUsername(username);

      if (username) {
        setCurrentTab('perfil_externo');
      } else {
        const previousTab = window.history.state?.beatcloudTab;

        setCurrentTab((tab) =>
          tab === 'perfil_externo'
            ? typeof previousTab === 'string' &&
              previousTab !== 'perfil_externo'
              ? previousTab
              : 'descubrir'
            : tab
        );
      }
    };

    window.addEventListener('popstate', syncTrackFromUrl);

    return () => {
      window.removeEventListener('popstate', syncTrackFromUrl);
    };
  }, []);

  const handleOpenTrackDetail = (id: string) => {
    if (!id) return;

    const url = new URL(window.location.href);

    if (url.searchParams.get('track') !== id) {
      url.searchParams.set('track', id);

      const previousState = window.history.state;
      const state =
        typeof previousState === 'object' && previousState !== null
          ? { ...previousState, beatcloudTrackOverlay: true }
          : { beatcloudTrackOverlay: true };

      window.history.pushState(
        state,
        '',
        `${url.pathname}${url.search}${url.hash}`
      );
    }

    setSelectedTrackId(id);
  };

  const handleCloseTrackDetail = () => {
    const url = new URL(window.location.href);

    if (url.searchParams.has('track')) {
      if (window.history.state?.beatcloudTrackOverlay === true) {
        window.history.back();
      } else {
        url.searchParams.delete('track');
        window.history.replaceState(
          window.history.state,
          '',
          `${url.pathname}${url.search}${url.hash}`
        );
      }
    }

    setSelectedTrackId(null);
  };

  const handleOpenAuth = (mode: 'login' | 'register') => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  const handleOpenUpload = () => {
    setTrackToEdit(null);
    setUploadModalOpen(true);
  };

  const handleEditTrack = (track: Track) => {
    setTrackToEdit(track);
    setUploadModalOpen(true);
  };

  const handleNavigateTab = (tab: string) => {
    const url = new URL(window.location.href);

    if (url.searchParams.has('profile')) {
      url.searchParams.delete('profile');

      window.history.pushState(
        { beatcloudTab: tab },
        '',
        `${url.pathname}${url.search}${url.hash}`
      );
    }

    setViewedProfileUsername(null);
    setCurrentTab(tab);
  };

  const handleOpenPublicProfile = (userId: string, role: UserType) => {
    const target = users.find(
      (user) => user.id === userId && user.role === role
    );

    if (!target) return;

    const url = new URL(window.location.href);

    url.searchParams.delete('track');
    url.searchParams.set('profile', target.username);

    const destino = `${url.pathname}${url.search}${url.hash}`;
    const actual =
      `${window.location.pathname}${window.location.search}${window.location.hash}`;

    if (destino !== actual) {
      if (!new URLSearchParams(window.location.search).has('profile')) {
        const previousState = window.history.state;

        const state =
          typeof previousState === 'object' && previousState !== null
            ? previousState
            : {};

        window.history.replaceState(
          { ...state, beatcloudTab: currentTab },
          '',
          actual
        );
      }

      window.history.pushState(
        { beatcloudPublicProfile: true },
        '',
        destino
      );
    }

    setSelectedTrackId(null);
    setViewedProfileUsername(target.username);
    setCurrentTab('perfil_externo');
  };

  const handleOpenProducerProfile = (producerId: string) => {
    handleOpenPublicProfile(producerId, 'productor');
  };

  const handleSelectCommunityUser = (userId: string, role: UserType) => {
    handleOpenPublicProfile(userId, role);
  };

  return (
    <div className="min-h-screen bg-[#0a0c10] text-zinc-100 flex flex-row font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Studio Left Sidebar */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={handleNavigateTab}
        onOpenAuth={handleOpenAuth}
        onOpenUpload={handleOpenUpload}
        isMobileOpen={isMobileMenuOpen}
        onCloseMobile={() => setIsMobileMenuOpen(false)}
      />

      {/* Main App Workspace */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        {/* TopBar */}
        <TopBar
          currentTab={currentTab}
          setCurrentTab={handleNavigateTab}
          onOpenAuth={handleOpenAuth}
          onOpenAccountDeletion={() => setAccountDeletionOpen(true)}
          onOpenUpload={handleOpenUpload}
          onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        />
        <BackendStatusBanner />

        {/* Dynamic Main Views Container */}
        <main className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 pt-4 pb-28">
          {paymentNotice && (
            <div
              role="status"
              className="mb-4 flex items-center justify-between gap-3 rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm text-amber-100"
            >
              <span>{paymentNotice}</span>
              <button type="button" onClick={clearPaymentNotice} aria-label="Cerrar aviso de pago">
                <X className="h-4 w-4" />
              </button>
            </div>
          )}
          {(currentTab === 'descubrir' || currentTab === 'inicio') && (
            <DiscoverPage
              onNavigateCatalog={() => handleNavigateTab('catalogo')}
              onOpenTrackDetail={handleOpenTrackDetail}
              onOpenProducerProfile={handleOpenProducerProfile}
            />
          )}

          {currentTab === 'catalogo' && (
            <CatalogPage
              onOpenTrackDetail={handleOpenTrackDetail}
              onOpenProducerProfile={handleOpenProducerProfile}
            />
          )}

          {currentTab === 'carrito' && (
            <CartPage
              onNavigateCatalog={() => handleNavigateTab('catalogo')}
              onOpenTrackDetail={handleOpenTrackDetail}
            />
          )}

          {currentTab === 'usuarios' && (
            <UsersCatalogPage onSelectUser={handleSelectCommunityUser} />
          )}

          {currentTab === 'sobre_nosotros' && <AboutPage />}

          {/* Current Logged-in User Profile */}
          {currentTab === 'perfil' && (
            currentUser?.role === 'productor' ? (
              <ProducerProfilePage
                initialTab="beats"
                onOpenTrackDetail={handleOpenTrackDetail}
                onOpenUploadModal={handleOpenUpload}
                onEditTrack={handleEditTrack}
              />
            ) : (
              <ArtistProfilePage
                initialTab="compras"
                onOpenTrackDetail={handleOpenTrackDetail}
                onNavigateCatalog={() => handleNavigateTab('catalogo')}
              />
            )
          )}

          {/* Producer Sales View */}
          {currentTab === 'ventas' && (
            <ProducerProfilePage
              initialTab="ventas"
              onOpenTrackDetail={handleOpenTrackDetail}
              onOpenUploadModal={handleOpenUpload}
              onEditTrack={handleEditTrack}
            />
          )}

          {/* Artist Favorites View */}
          {currentTab === 'favoritos' && (
            <ArtistProfilePage
              initialTab="favoritos"
              onOpenTrackDetail={handleOpenTrackDetail}
              onNavigateCatalog={() => handleNavigateTab('catalogo')}
            />
          )}

          {/* External Viewed Profile */}
          {currentTab === 'perfil_externo' && viewedProfile && (
            viewedProfile.role === 'productor' ? (
              <ProducerProfilePage
                producerId={viewedProfile.id}
                onOpenTrackDetail={handleOpenTrackDetail}
                onOpenUploadModal={handleOpenUpload}
                onEditTrack={handleEditTrack}
              />
            ) : (
              <ArtistProfilePage
                artistId={viewedProfile.id}
                onOpenTrackDetail={handleOpenTrackDetail}
                onNavigateCatalog={() => handleNavigateTab('catalogo')}
              />
            )
          )}
          {currentTab === 'perfil_externo' && !viewedProfile && (
            <div
              role="status"
              className="rounded-2xl border border-zinc-700 bg-zinc-900 p-6 text-zinc-200"
            >
              <h2 className="text-lg font-bold mb-2">
                Perfil no disponible
              </h2>
              <p className="text-sm text-zinc-400">
                No pudimos encontrar este perfil entre los usuarios cargados.
                Comprueba el enlace y la conexion con el servidor.
              </p>
              <button
                type="button"
                className="mt-4 rounded-lg bg-amber-400 px-4 py-2 font-bold text-zinc-950"
                onClick={() => handleNavigateTab('usuarios')}
              >
                Ver comunidad
              </button>
            </div>
          )}
        </main>
      </div>

      {/* Track Detail Modal */}
      <TrackDetailModal
        trackId={selectedTrackId}
        onClose={handleCloseTrackDetail}
        onOpenProducerProfile={handleOpenProducerProfile}
      />

      {/* Upload Track Modal with Acoustic Analyzer Fallback */}
      <UploadTrackModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        trackToEdit={trackToEdit}
      />

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        mode={authMode}
        onClose={() => setAuthModalOpen(false)}
        onSwitchMode={(mode) => setAuthMode(mode)}
      />
      <AccountDeletionModal
        isOpen={accountDeletionOpen}
        onClose={() => setAccountDeletionOpen(false)}
      />

      {/* Global Persistent Audio Player */}
      <GlobalAudioPlayer onOpenTrackDetail={handleOpenTrackDetail} />
    </div>
  );
};
