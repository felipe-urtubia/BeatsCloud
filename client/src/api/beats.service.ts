import { apiFetch } from './client';

export interface Beat {
    id: number;
    title: string;
    producer: string;
    genre: string;
    bpm: number;
    scale: string;
    price: number;
    audioUrl: string;
    coverUrl: string;
}

// Interfaz cruda como viene de Django REST Framework
interface DjangoBeat {
    id: number;
    titulo: string;
    productor_nombre?: string;
    genero: string;
    bpm: number;
    escala?: string;
    precio_clp: number;
    archivo_audio: string;
    portada?: string;
}

export const BeatsService = {
    async getAll(): Promise<Beat[]> {
        const data = await apiFetch<DjangoBeat[]>('/beats/');
        return data.map((b) => ({
            id: b.id,
            title: b.titulo,
            producer: b.productor_nombre || 'Productor BeatsCloud',
            genre: b.genero,
            bpm: b.bpm,
            scale: b.escala || 'C Minor',
            price: b.precio_clp,
            audioUrl: b.archivo_audio,
            coverUrl: b.portada || 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=500',
        }));
    },

    async create(formData: FormData): Promise<Beat> {
        return apiFetch<Beat>('/beats/', {
            method: 'POST',
            body: formData,
        });
    }
};
