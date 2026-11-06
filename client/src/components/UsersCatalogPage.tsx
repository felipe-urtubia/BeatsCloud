import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { UserType } from '../types';
import { Users, Search, Sliders, Mic2, Disc, ArrowRight } from 'lucide-react';

interface UsersCatalogPageProps {
  onSelectUser: (userId: string, role: UserType) => void;
}

export const UsersCatalogPage: React.FC<UsersCatalogPageProps> = ({ onSelectUser }) => {
  const { users, tracks } = useApp();
  const [filterRole, setFilterRole] = useState<'todos' | UserType>('todos');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredUsers = users.filter((u) => {
    const matchesRole = filterRole === 'todos' || u.role === filterRole;
    const matchesSearch =
      u.artistName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.bio.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesRole && matchesSearch;
  });

  return (
    <div className="py-6 pb-36 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-[#0e111a] border border-[#1b2030] p-6 rounded-3xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center gap-2.5 font-mono">
            <Users className="w-6 h-6 text-amber-400" />
            <span>DIRECTORIO DE CREADORES</span>
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            Conecta con productores independientes y artistas urbanos de la escena.
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
          <input
            type="text"
            placeholder="Buscar creador..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-[#121520] border border-[#23283b] rounded-xl text-xs text-white placeholder-zinc-400 focus:outline-none focus:border-amber-400"
          />
        </div>
      </div>

      {/* Role Toggle Pills */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setFilterRole('todos')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
            filterRole === 'todos'
              ? 'bg-amber-400 text-zinc-950 font-black'
              : 'bg-[#10131d] border border-[#1b2030] text-zinc-400 hover:text-white'
          }`}
        >
          Todos ({users.length})
        </button>
        <button
          onClick={() => setFilterRole('productor')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
            filterRole === 'productor'
              ? 'bg-amber-400 text-zinc-950 font-black'
              : 'bg-[#10131d] border border-[#1b2030] text-zinc-400 hover:text-white'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>Productores</span>
        </button>
        <button
          onClick={() => setFilterRole('artista')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
            filterRole === 'artista'
              ? 'bg-amber-400 text-zinc-950 font-black'
              : 'bg-[#10131d] border border-[#1b2030] text-zinc-400 hover:text-white'
          }`}
        >
          <Mic2 className="w-3.5 h-3.5" />
          <span>Artistas</span>
        </button>
      </div>

      {/* Users Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredUsers.map((user) => {
          const userTracks = tracks.filter((t) => t.producerId === user.id);

          return (
            <div
              key={user.id}
              className="bg-[#0e111a] border border-[#1b2030] hover:border-amber-400/40 rounded-2xl overflow-hidden shadow-md transition-all hover:-translate-y-0.5 flex flex-col justify-between"
            >
              <div>
                {/* Banner Header */}
                <div className="h-20 relative overflow-hidden bg-zinc-800">
                  <img
                    src={user.bannerUrl}
                    alt={user.artistName}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#0e111a] to-transparent" />
                </div>

                {/* Avatar & Info */}
                <div className="px-5 -mt-8 relative">
                  <img
                    src={user.avatarUrl}
                    alt={user.artistName}
                    className="w-16 h-16 rounded-xl object-cover ring-4 ring-[#0e111a] shadow-xl"
                  />
                  <div className="mt-2.5">
                    <span
                      className={`text-[9px] font-mono font-bold uppercase px-2 py-0.5 rounded border ${
                        user.role === 'productor'
                          ? 'text-amber-400 bg-amber-400/10 border-amber-400/20'
                          : 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20'
                      }`}
                    >
                      {user.role === 'productor' ? '🎧 Productor' : '🎤 Artista'}
                    </span>
                    <h3 className="text-base font-bold text-white mt-1 leading-tight">
                      {user.artistName || user.username}
                    </h3>
                    <p className="text-xs text-zinc-400 font-mono">@{user.username}</p>

                    <p className="text-xs text-zinc-300 mt-2.5 line-clamp-2 leading-relaxed">
                      {user.bio}
                    </p>
                  </div>
                </div>
              </div>

              {/* Card Footer */}
              <div className="p-5 pt-3 mt-3 border-t border-[#1b2030] flex items-center justify-between">
                <span className="text-xs text-zinc-400 font-mono">
                  {user.role === 'productor' ? (
                    <span className="flex items-center gap-1 text-zinc-300">
                      <Disc className="w-3.5 h-3.5 text-amber-400" />
                      {userTracks.length} pistas
                    </span>
                  ) : (
                    <span>{user.purchasedTrackIds.length} compras</span>
                  )}
                </span>

                <button
                  onClick={() => onSelectUser(user.id, user.role)}
                  className="bg-zinc-800 hover:bg-amber-400 hover:text-zinc-950 text-white font-bold px-3 py-1.5 rounded-lg text-xs transition-colors flex items-center gap-1"
                >
                  <span>Ver Perfil</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
