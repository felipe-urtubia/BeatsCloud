import test from 'node:test';
import assert from 'node:assert/strict';
import { sortCatalogTracks } from './catalogSort.mjs';

const tracks = [
  { id: '1', genre: 'Trap', title: 'Zeta', bpm: 100, likesCount: 2, price: 5, createdAt: '2025-01-01' },
  { id: '2', genre: 'Pop', title: 'Beta', bpm: 90, likesCount: 4, price: 8, createdAt: '2025-03-01' },
  { id: '3', genre: 'Pop', title: 'Alfa', bpm: 110, likesCount: 1, price: 3, createdAt: '2025-02-01' },
];

test('orders genre alphabetically ascending and uses title as a deterministic tie breaker', () => {
  assert.deepEqual(sortCatalogTracks(tracks, 'genero_asc').map((track) => track.id), ['3', '2', '1']);
});

test('orders genre descending while preserving title order inside a genre', () => {
  assert.deepEqual(sortCatalogTracks(tracks, 'genero_desc').map((track) => track.id), ['1', '3', '2']);
});

test('supports ascending and descending BPM and price order', () => {
  assert.deepEqual(sortCatalogTracks(tracks, 'bpm_asc').map((track) => track.id), ['2', '1', '3']);
  assert.deepEqual(sortCatalogTracks(tracks, 'bpm_desc').map((track) => track.id), ['3', '1', '2']);
  assert.deepEqual(sortCatalogTracks(tracks, 'precio_menor').map((track) => track.id), ['3', '1', '2']);
  assert.deepEqual(sortCatalogTracks(tracks, 'precio_mayor').map((track) => track.id), ['2', '1', '3']);
});

test('does not mutate the fetched catalog array', () => {
  const originalOrder = tracks.map((track) => track.id);
  sortCatalogTracks(tracks, 'genero_asc');
  assert.deepEqual(tracks.map((track) => track.id), originalOrder);
});
