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
import { Track, UserType, ResourceType } from './types';
import {
  readNavigation,
  makeTrackUrl,
  makeProfileUrl,
  readPageNavigation,
  makeTabUrl,
  lookupPublicProfile,
  lookupPublicProfileForRoute,
} from './navigation/urlState';
import { BackendStatusBanner } from './components/BackendStatusBanner';
import { X } from 'lucide-react';
import { AccountDeletionModal } from './components/AccountDeletionModal';

export const App: React.FC = () => {
  const { currentUser, users, paymentNotice, paymentReturnReady, clearPaymentNotice, setActiveResourceFilter } = useApp();

  const [currentTab, setCurrentTab] = useState<string>(
    () => readNavigation(window.location.search).profileUsername
      ? 'perfil_externo'
      : readPageNavigation(window.location.search).tab,
  );
  const [selectedTrackId, setSelectedTrackId] = useState<string | null>(
    () => readNavigation(window.location.search).trackId,
  );

  // Profile view state
  const [viewedProfileUsername, setViewedProfileUsername] = useState<string | null>(
    () => readNavigation(window.location.search).profileUsername,
  );

  const viewedProfile = lookupPublicProfile(
    users, viewedProfileUsername
  );

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
      const { trackId, profileUsername: username } =
        readNavigation(window.location.search);

      setSelectedTrackId(trackId);

      setViewedProfileUsername(username);
      const page = readPageNavigation(window.location.search);
      setActiveResourceFilter(page.resource);

      setCurrentTab(username ? 'perfil_externo' : page.tab);
    };

    syncTrackFromUrl();
    window.addEventListener('popstate', syncTrackFromUrl);

    return () => {
      window.removeEventListener('popstate', syncTrackFromUrl);
    };
  }, [setActiveResourceFilter]);

  const handleOpenTrackDetail = (id: string) => {
    if (!id) return;

    const url = new URL(window.location.href);

    if (url.searchParams.get('track') !== id) {
      const previousState = window.history.state;
      const state =
        typeof previousState === 'object' && previousState !== null
          ? { ...previousState, beatcloudTrackOverlay: true }
          : { beatcloudTrackOverlay: true };

      window.history.pushState(
        state,
        '',
        makeTrackUrl(window.location.href, id)
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

  const handleNavigateTab = (tab: string, resource?: ResourceType) => {
    const chosenResource = tab === 'catalogo' ? resource ?? 'all' : 'all';
    const destination = makeTabUrl(window.location.href, tab, chosenResource);
    const actual =
      `${window.location.pathname}${window.location.search}${window.location.hash}`;

    if (destination !== actual) {
      window.history.pushState({ beatcloudTab: tab }, '', destination);
    }

    setActiveResourceFilter(chosenResource);
    setSelectedTrackId(null);
    setViewedProfileUsername(null);
    setCurrentTab(readPageNavigation(new URL(destination, window.location.origin).search).tab);
  };

  const handleOpenPublicProfile = (userId: string, role: UserType) => {
    const target = lookupPublicProfileForRoute(
      users, userId, role
    );

    if (!target) return;

    const destino = makeProfileUrl(
      window.location.href, target.username
    );
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
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
                <span>{paymentNotice}</span>
                {paymentReturnReady && currentUser?.role === 'artista' && (
                  <button
                    type="button"
                    onClick={() => {
                      handleNavigateTab('perfil');
                      clearPaymentNotice();
                    }}
                    className="w-fit shrink-0 rounded-lg bg-amber-400 px-3 py-2 text-xs font-bold text-zinc-950 hover:bg-amber-300"
                  >
                    Ir a mis compras y descargas
                  </button>
                )}
              </div>
              <button type="button" onClick={clearPaymentNotice} aria-label="Cerrar aviso de pago">
                <X className="h-4 w-4" />
              </button>
            </div>
          )}
          {(
            (currentTab === 'perfil' && !currentUser) ||
            (currentTab === 'ventas' && currentUser?.role !== 'productor') ||
            (currentTab === 'favoritos' && currentUser?.role !== 'artista')
          ) && (
            <div role="status" className="rounded-2xl border border-zinc-700 bg-zinc-900 p-6 text-zinc-200">
              <h2 className="text-lg font-bold mb-2">Secci?n de cuenta no disponible</h2>
              <p className="text-sm text-zinc-400">
                Inicia sesi?n con la cuenta y el rol correspondientes para acceder.
              </p>
              <button type="button" onClick={() => handleNavigateTab('descubrir')}
                className="mt-4 rounded-lg bg-amber-400 px-4 py-2 font-bold text-zinc-950">
                Volver al inicio
              </button>
            </div>
          )}
          {(currentTab === 'descubrir' || currentTab === 'inicio') && (
            <DiscoverPage
              onNavigateCatalog={(resource) => handleNavigateTab('catalogo', resource)}
              onOpenTrackDetail={handleOpenTrackDetail}
              onOpenProducerProfile={handleOpenProducerProfile}
            />
          )}

          {currentTab === 'catalogo' && (
            <CatalogPage
              onSelectResource={(resource) => handleNavigateTab('catalogo', resource === 'all' ? undefined : resource)}
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
          {currentTab === 'perfil' && currentUser && (
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
          {currentTab === 'ventas' && currentUser?.role === 'productor' && (
            <ProducerProfilePage
              initialTab="ventas"
              onOpenTrackDetail={handleOpenTrackDetail}
              onOpenUploadModal={handleOpenUpload}
              onEditTrack={handleEditTrack}
            />
          )}

          {/* Artist Favorites View */}
          {currentTab === 'favoritos' && currentUser?.role === 'artista' && (
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
