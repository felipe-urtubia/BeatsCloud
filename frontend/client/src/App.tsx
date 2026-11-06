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
  const { currentUser, paymentNotice, clearPaymentNotice } = useApp();

  const [currentTab, setCurrentTab] = useState<string>('descubrir');
  const [selectedTrackId, setSelectedTrackId] = useState<string | null>(
    () => new URLSearchParams(window.location.search).get('track') || null,
  );

  // Profile view state
  const [viewedProfileId, setViewedProfileId] = useState<string | null>(null);
  const [viewedProfileRole, setViewedProfileRole] = useState<UserType>('productor');

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
      const trackId = new URLSearchParams(
        window.location.search
      ).get('track');

      setSelectedTrackId(trackId || null);
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

  const handleOpenProducerProfile = (producerId: string) => {
    setViewedProfileId(producerId);
    setViewedProfileRole('productor');
    setCurrentTab('perfil_externo');
  };

  const handleSelectCommunityUser = (userId: string, role: UserType) => {
    setViewedProfileId(userId);
    setViewedProfileRole(role);
    setCurrentTab('perfil_externo');
  };

  return (
    <div className="min-h-screen bg-[#0a0c10] text-zinc-100 flex flex-row font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Studio Left Sidebar */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={(tab) => {
          setViewedProfileId(null);
          setCurrentTab(tab);
        }}
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
          setCurrentTab={(tab) => {
            setViewedProfileId(null);
            setCurrentTab(tab);
          }}
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
              onNavigateCatalog={() => setCurrentTab('catalogo')}
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
              onNavigateCatalog={() => setCurrentTab('catalogo')}
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
                onNavigateCatalog={() => setCurrentTab('catalogo')}
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
              onNavigateCatalog={() => setCurrentTab('catalogo')}
            />
          )}

          {/* External Viewed Profile */}
          {currentTab === 'perfil_externo' && viewedProfileId && (
            viewedProfileRole === 'productor' ? (
              <ProducerProfilePage
                producerId={viewedProfileId}
                onOpenTrackDetail={handleOpenTrackDetail}
                onOpenUploadModal={handleOpenUpload}
                onEditTrack={handleEditTrack}
              />
            ) : (
              <ArtistProfilePage
                artistId={viewedProfileId}
                onOpenTrackDetail={handleOpenTrackDetail}
                onNavigateCatalog={() => setCurrentTab('catalogo')}
              />
            )
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
