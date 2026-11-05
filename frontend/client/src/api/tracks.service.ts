import { Track } from '../types';

const API_BASE = '/api';

export const TracksService = {
  async getAll(): Promise<Track[]> {
    const res = await fetch(`${API_BASE}/tracks/`);
    if (!res.ok) {
      throw new Error(`Error ${res.status}: no se pudo cargar el catálogo`);
    }
    return res.json();
  },

  async getById(id: string | number): Promise<Track> {
    const res = await fetch(`${API_BASE}/tracks/${id}/`);
    if (!res.ok) {
      throw new Error(`Error ${res.status}: track no encontrado`);
    }
    return res.json();
  }
};

export const TrackService = TracksService;
export default TracksService;
