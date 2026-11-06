import React, { useState } from 'react';
import type { User } from '../types';
import type { ProfileUpdate } from '../context/AppContext';

interface ProfileEditFormProps {
  user: User;
  onSave: (data: ProfileUpdate) => Promise<void>;
  onCancel: () => void;
}

export const ProfileEditForm: React.FC<ProfileEditFormProps> = ({ user, onSave, onCancel }) => {
  const [bio, setBio] = useState(user.bio);
  const [spotify, setSpotify] = useState(user.spotify ?? '');
  const [youtube, setYoutube] = useState(user.youtube ?? '');
  const [instagram, setInstagram] = useState(user.instagram ?? '');
  const [avatarFile, setAvatarFile] = useState<File>();
  const [bannerFile, setBannerFile] = useState<File>();
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await onSave({ bio, spotify, youtube, instagram, avatarFile, bannerFile });
    } catch (saveError) {
      setError((saveError as Error).message || 'No se pudo guardar el perfil.');
    } finally {
      setSaving(false);
    }
  };

  const inputClass = 'w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-white';

  return (
    <form onSubmit={handleSubmit} className="mt-3 w-full max-w-xl space-y-2 text-left">
      <textarea
        value={bio}
        onChange={(event) => setBio(event.target.value)}
        maxLength={500}
        rows={3}
        aria-label="Biografía"
        placeholder="Biografía"
        className={inputClass}
      />
      <div className="grid gap-2 sm:grid-cols-3">
        <input type="url" value={spotify} onChange={(event) => setSpotify(event.target.value)} placeholder="Enlace Spotify" aria-label="Enlace Spotify" className={inputClass} />
        <input type="url" value={instagram} onChange={(event) => setInstagram(event.target.value)} placeholder="Enlace Instagram" aria-label="Enlace Instagram" className={inputClass} />
        <input type="url" value={youtube} onChange={(event) => setYoutube(event.target.value)} placeholder="Enlace YouTube" aria-label="Enlace YouTube" className={inputClass} />
      </div>
      <div className="grid gap-2 sm:grid-cols-2 text-[11px] text-zinc-400">
        <label>Foto de perfil<input type="file" accept="image/*" onChange={(event) => setAvatarFile(event.target.files?.[0])} className="mt-1 block w-full" /></label>
        <label>Imagen de fondo<input type="file" accept="image/*" onChange={(event) => setBannerFile(event.target.files?.[0])} className="mt-1 block w-full" /></label>
      </div>
      {error && <p role="alert" className="text-xs text-rose-400">{error}</p>}
      <div className="flex gap-2">
        <button disabled={saving} className="rounded-lg bg-amber-400 px-3 py-1.5 text-xs font-bold text-zinc-950 disabled:opacity-50">
          {saving ? 'Guardando…' : 'Guardar perfil'}
        </button>
        <button type="button" onClick={onCancel} className="rounded-lg bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300">
          Cancelar
        </button>
      </div>
    </form>
  );
};
