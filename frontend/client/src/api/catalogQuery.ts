import type { CatalogoParams } from './django.service';

export interface CatalogFilters {
  search: string;
  genre: string;
  resource: string;
  mood: string;
  scale: string;
  minBpm: number;
  maxBpm: number;
  stems: boolean;
  price: string;
  sort: NonNullable<CatalogoParams['orden']>;
  pageSize: number;
}

export function buildCatalogQuery(
  filters: CatalogFilters,
  page = 1,
): CatalogoParams {
  const prices: Record<string, string> = {
    free: 'free',
    paid: 'paid',
    '0_5000': '0-5000',
    '5001_10000': '5001-10000',
    '10001_20000': '10001-20000',
    '20001_plus': '20001-mas',
  };

  return {
    q: filters.search.trim() || undefined,
    genero: filters.genre === 'Todos' ? undefined : filters.genre,
    tipo: filters.resource === 'all' ? undefined : filters.resource,
    mood: filters.mood === 'Todos' ? undefined : filters.mood,
    tonalidad: filters.scale === 'Todas' ? undefined : filters.scale,
    bpm_min: filters.minBpm,
    bpm_max: filters.maxBpm,
    has_stems: filters.stems ? 'true' : undefined,
    precio: prices[filters.price],
    orden: filters.sort,
    page,
    page_size: filters.pageSize,
  };
}
