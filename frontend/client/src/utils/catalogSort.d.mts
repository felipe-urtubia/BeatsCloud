export type CatalogSortKey =
  | 'recientes' | 'antiguos' | 'bpm_asc' | 'bpm_desc' | 'likes'
  | 'precio_menor' | 'precio_mayor' | 'nombre_asc' | 'nombre_desc'
  | 'genero_asc' | 'genero_desc';

export interface CatalogSortableTrack {
  genre: string;
  title: string;
  bpm: number;
  likesCount: number;
  price: number;
  createdAt: string;
}

export function sortCatalogTracks<T extends CatalogSortableTrack>(tracks: readonly T[], sortBy: CatalogSortKey): T[];
