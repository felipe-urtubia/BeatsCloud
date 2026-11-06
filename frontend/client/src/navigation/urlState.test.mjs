import test from 'node:test';
import assert from 'node:assert/strict';

import {
  readNavigation,
  makeTrackUrl,
  makeProfileUrl,
  makeLeaveProfileUrl,
  lookupPublicProfile,
  lookupPublicProfileForRoute,
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
