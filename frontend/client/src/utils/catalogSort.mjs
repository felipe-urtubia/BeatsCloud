export function sortCatalogTracks(tracks, sortBy) {
  return [...tracks].sort((a, b) => {
    if (sortBy === 'genero_asc' || sortBy === 'genero_desc') {
      const genreOrder = a.genre.localeCompare(b.genre, 'es', { sensitivity: 'base', numeric: true });
      if (genreOrder !== 0) return sortBy === 'genero_asc' ? genreOrder : -genreOrder;
      return a.title.localeCompare(b.title, 'es', { sensitivity: 'base', numeric: true });
    }
    if (sortBy === 'bpm_asc') return a.bpm - b.bpm;
    if (sortBy === 'bpm_desc') return b.bpm - a.bpm;
    if (sortBy === 'likes') return b.likesCount - a.likesCount;
    if (sortBy === 'precio_menor') return a.price - b.price;
    if (sortBy === 'precio_mayor') return b.price - a.price;
    if (sortBy === 'nombre_asc') return a.title.localeCompare(b.title, 'es', { sensitivity: 'base', numeric: true });
    if (sortBy === 'nombre_desc') return b.title.localeCompare(a.title, 'es', { sensitivity: 'base', numeric: true });
    if (sortBy === 'antiguos') return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
  });
}
