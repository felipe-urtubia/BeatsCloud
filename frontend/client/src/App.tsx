import React, { useState } from 'react';
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

export const App: React.FC = () => {
  const { currentUser } = useApp();

  const [currentTab, setCurrentTab] = useState<string>('descubrir');
  const [selectedTrackId, setSelectedTrackId] = useState<string | null>(null);

  // Profile view state
  const [viewedProfileId, setViewedProfileId] = useState<string | null>(null);
  const [viewedProfileRole, setViewedProfileRole] = useState<UserType>('productor');

  // Modals & Mobile state
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [trackToEdit, setTrackToEdit] = useState<Track | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

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
          onOpenUpload={handleOpenUpload}
          onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        />
        <BackendStatusBanner />

        {/* Dynamic Main Views Container */}
        <main className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 pt-4 pb-28">
          {(currentTab === 'descubrir' || currentTab === 'inicio') && (
            <DiscoverPage
              onNavigateCatalog={() => setCurrentTab('catalogo')}
              onOpenTrackDetail={(id) => setSelectedTrackId(id)}
              onOpenProducerProfile={handleOpenProducerProfile}
            />
          )}

          {currentTab === 'catalogo' && (
            <CatalogPage
              onOpenTrackDetail={(id) => setSelectedTrackId(id)}
              onOpenProducerProfile={handleOpenProducerProfile}
            />
          )}

          {currentTab === 'carrito' && (
            <CartPage
              onNavigateCatalog={() => setCurrentTab('catalogo')}
              onOpenTrackDetail={(id) => setSelectedTrackId(id)}
              onNavigateProfile={() => setCurrentTab('perfil')}
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
                onOpenTrackDetail={(id) => setSelectedTrackId(id)}
                onOpenUploadModal={handleOpenUpload}
                onEditTrack={handleEditTrack}
              />
            ) : (
              <ArtistProfilePage
                initialTab="compras"
                onOpenTrackDetail={(id) => setSelectedTrackId(id)}
                onNavigateCatalog={() => setCurrentTab('catalogo')}
              />
            )
          )}

          {/* Producer Sales View */}
          {currentTab === 'ventas' && (
            <ProducerProfilePage
              initialTab="ventas"
              onOpenTrackDetail={(id) => setSelectedTrackId(id)}
              onOpenUploadModal={handleOpenUpload}
              onEditTrack={handleEditTrack}
            />
          )}

          {/* Artist Favorites View */}
          {currentTab === 'favoritos' && (
            <ArtistProfilePage
              initialTab="favoritos"
              onOpenTrackDetail={(id) => setSelectedTrackId(id)}
              onNavigateCatalog={() => setCurrentTab('catalogo')}
            />
          )}

          {/* External Viewed Profile */}
          {currentTab === 'perfil_externo' && viewedProfileId && (
            viewedProfileRole === 'productor' ? (
              <ProducerProfilePage
                producerId={viewedProfileId}
                onOpenTrackDetail={(id) => setSelectedTrackId(id)}
                onOpenUploadModal={handleOpenUpload}
                onEditTrack={handleEditTrack}
              />
            ) : (
              <ArtistProfilePage
                artistId={viewedProfileId}
                onOpenTrackDetail={(id) => setSelectedTrackId(id)}
                onNavigateCatalog={() => setCurrentTab('catalogo')}
              />
            )
          )}
        </main>
      </div>

      {/* Track Detail Modal */}
      <TrackDetailModal
        trackId={selectedTrackId}
        onClose={() => setSelectedTrackId(null)}
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

      {/* Global Persistent Audio Player */}
      <GlobalAudioPlayer onOpenTrackDetail={(id) => setSelectedTrackId(id)} />
    </div>
  );
};
