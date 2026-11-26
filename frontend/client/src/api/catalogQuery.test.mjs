import test from 'node:test';
import assert from 'node:assert/strict';
import { buildCatalogQuery } from './catalogQuery.ts';

const defaults = {
  search: '',
  genre: 'Todos',
  resource: 'all',
  mood: 'Todos',
  scale: 'Todas',
  minBpm: 1,
  maxBpm: 300,
  stems: false,
  price: 'all',
  sort: 'recientes',
  pageSize: 12,
};

test('envia filtros combinados al servidor', () => {
  const query = buildCatalogQuery({
    ...defaults,
    search: ' beat ',
    genre: 'Trap',
    resource: 'instrumental',
    mood: 'Oscuro',
    scale: 'Am',
    minBpm: 120,
    maxBpm: 150,
    stems: true,
  });

  assert.equal(query.q, 'beat');
  assert.equal(query.genero, 'Trap');
  assert.equal(query.tipo, 'instrumental');
  assert.equal(query.mood, 'Oscuro');
  assert.equal(query.tonalidad, 'Am');
  assert.equal(query.bpm_min, 120);
  assert.equal(query.bpm_max, 150);
  assert.equal(query.has_stems, 'true');
});

test('omite filtros no seleccionados', () => {
  const query = buildCatalogQuery(defaults);

  for (const key of [
    'q', 'genero', 'tipo', 'mood',
    'tonalidad', 'has_stems', 'precio',
  ]) {
    assert.equal(query[key], undefined);
  }
});

test('utiliza paginacion del servidor', () => {
  const query = buildCatalogQuery({
    ...defaults,
    pageSize: 24,
  }, 3);

  assert.equal(query.page, 3);
  assert.equal(query.page_size, 24);
});

test('traduce correctamente rangos de precio', () => {
  const cases = {
    '0_5000': '0-5000',
    '5001_10000': '5001-10000',
    '10001_20000': '10001-20000',
    '20001_plus': '20001-mas',
    free: 'free',
    paid: 'paid',
  };

  for (const [price, expected] of Object.entries(cases)) {
    assert.equal(
      buildCatalogQuery({
        ...defaults,
        price,
      }).precio,
      expected,
    );
  }
});

test('envia ordenamientos al backend', () => {
  for (const sort of [
    'recientes', 'antiguos', 'bpm_asc', 'bpm_desc',
    'genero_asc', 'genero_desc', 'nombre_asc',
    'nombre_desc', 'likes', 'precio_menor',
    'precio_mayor',
  ]) {
    assert.equal(
      buildCatalogQuery({ ...defaults, sort }).orden,
      sort,
    );
  }
});

test('cada consulta comienza en pagina uno por defecto', () => {
  assert.equal(buildCatalogQuery(defaults).page, 1);

  assert.equal(
    buildCatalogQuery({
      ...defaults,
      mood: 'Bailable',
    }).page,
    1,
  );
});
