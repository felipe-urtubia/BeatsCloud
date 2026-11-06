import test from 'node:test';
import assert from 'node:assert/strict';

import {
  readNavigation,
  makeTrackUrl,
  makeProfileUrl,
  makeLeaveProfileUrl,
  lookupPublicProfile,
  lookupPublicProfileForRoute,
  readPageNavigation,
  makeTabUrl,
} from './urlState.ts';

const users = [
  { id: '11', username: 'productor_demo', role: 'productor' },
  { id: '12', username: 'artista_demo', role: 'artista' },
];

test('lee el enlace directo a una cancion', () => {
  assert.deepEqual(
    readNavigation('?track=dj-42'),
    { trackId: 'dj-42', profileUsername: null }
  );
});

test('lee el enlace directo a un perfil', () => {
  assert.deepEqual(
    readNavigation('?profile=artista_demo'),
    { trackId: null, profileUsername: 'artista_demo' }
  );
});

test('conserva otros parametros al enlazar canciones', () => {
  assert.equal(
    makeTrackUrl(
      'http://localhost:3000/?auth=login#inicio',
      'dj-42'
    ),
    '/?auth=login&track=dj-42#inicio'
  );
});

test('cambia una cancion sin duplicar el parametro', () => {
  assert.equal(
    makeTrackUrl(
      'http://localhost:3000/?track=dj-1',
      'dj-2'
    ),
    '/?track=dj-2'
  );
});

test('abrir un perfil elimina track y conserva otros parametros', () => {
  assert.equal(
    makeProfileUrl(
      'http://localhost:3000/?auth=login&track=dj-42',
      'productor_demo'
    ),
    '/?auth=login&profile=productor_demo'
  );
});

test('salir del perfil quita profile sin eliminar otros parametros', () => {
  assert.equal(
    makeLeaveProfileUrl(
      'http://localhost:3000/?auth=login&profile=artista_demo'
    ),
    '/?auth=login'
  );
});

test('resuelve el perfil de productor correcto', () => {
  const encontrado = lookupPublicProfile(
    users, 'productor_demo'
  );

  assert.equal(encontrado?.id, '11');
  assert.equal(encontrado?.role, 'productor');
});

test('resuelve el perfil de artista correcto', () => {
  const encontrado = lookupPublicProfile(
    users, 'artista_demo'
  );

  assert.equal(encontrado?.id, '12');
  assert.equal(encontrado?.role, 'artista');
});

test('un perfil inexistente nunca devuelve otro usuario', () => {
  assert.equal(
    lookupPublicProfile(users, 'no_existe_99999'),
    null
  );
});

test('rechaza un ID con rol incorrecto', () => {
  assert.equal(
    lookupPublicProfileForRoute(
      users, '11', 'artista'
    ),
    null
  );
});

test('permite buscar un productor por ID y rol', () => {
  assert.equal(
    lookupPublicProfileForRoute(
      users, '11', 'productor'
    )?.username,
    'productor_demo'
  );
});


test('cada seccion principal tiene enlace propio', () => {
  for (const tab of [
    'descubrir','catalogo','usuarios','sobre_nosotros',
    'carrito','perfil','ventas','favoritos'
  ]) {
    const url = makeTabUrl('http://localhost:3000/', tab);
    assert.equal(readPageNavigation(new URL(url, 'http://localhost:3000').search).tab, tab);
  }
});

test('enlaces directos de las cuatro categorias de audio', () => {
  for (const resource of ['instrumental','loop','acapella','drumkit']) {
    const url = makeTabUrl('http://localhost:3000/', 'catalogo', resource);
    assert.deepEqual(readPageNavigation(new URL(url, 'http://localhost:3000').search), {tab:'catalogo',resource});
  }
});

test('catalogo general no arrastra filtros de audio', () => {
  assert.equal(
    makeTabUrl('http://localhost:3000/?tab=catalogo&resource=loop', 'catalogo'),
    '/?tab=catalogo'
  );
});

test('navegar a otra pagina limpia filtros, perfil y cancion', () => {
  assert.equal(
    makeTabUrl('http://localhost:3000/?tab=catalogo&resource=loop&track=dj-2&profile=demo', 'carrito'),
    '/?tab=carrito'
  );
});

test('rutas invalidas vuelven a inicio sin aceptar filtros no soportados', () => {
  assert.deepEqual(
    readPageNavigation('?tab=catalogo&resource=inesperado'),
    { tab:'catalogo',resource:'all' }
  );
  assert.equal(readPageNavigation('?tab=desconocido').tab, 'descubrir');
});

test('enlaces publicos de perfil no arrastran apartados privados', () => {
  assert.equal(
    makeProfileUrl('http://localhost:3000/?tab=carrito&resource=loop','productor_demo'),
    '/?profile=productor_demo'
  );
});

test('enlace de cancion conserva la seccion y su filtro', () => {
  assert.equal(
    makeTrackUrl('http://localhost:3000/?tab=catalogo&resource=instrumental', 'dj-11'),
    '/?tab=catalogo&resource=instrumental&track=dj-11'
  );
});

test('el historial se puede representar con los enlaces generados', () => {
  const first = makeTabUrl('http://localhost:3000/', 'usuarios');
  const next = makeTabUrl(`http://localhost:3000${first}`, 'carrito');
  assert.equal(readPageNavigation(new URL(first, 'http://localhost:3000').search).tab, 'usuarios');
  assert.equal(readPageNavigation(new URL(next, 'http://localhost:3000').search).tab, 'carrito');
});
