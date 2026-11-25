import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { getProtectedSectionNotice } from './authGuard.ts';

test('una visita al catálogo público no requiere sesión', () => {
  for (const tab of ['descubrir', 'catalogo', 'usuarios', 'sobre_nosotros']) {
    assert.equal(getProtectedSectionNotice(tab, null), null);
  }
});

test('el carrito anónimo solicita iniciar sesión y presenta acentos correctos', () => {
  const notice = getProtectedSectionNotice('carrito', null);
  assert.equal(notice?.title, 'Inicia sesión para ver tu carrito');
  assert.equal(notice?.requiresLogin, true);
  assert.match(notice?.description ?? '', /aún/);
  assert.doesNotMatch(notice?.title ?? '', /sesi\?n/);
});

test('el perfil anónimo requiere sesión', () => {
  assert.equal(getProtectedSectionNotice('perfil', undefined)?.requiresLogin, true);
});

test('el carrito y el perfil funcionan para ambos tipos de cuenta', () => {
  for (const role of ['artista', 'productor']) {
    assert.equal(getProtectedSectionNotice('carrito', role), null);
    assert.equal(getProtectedSectionNotice('perfil', role), null);
  }
});

test('ventas exige cuenta de productor', () => {
  assert.equal(getProtectedSectionNotice('ventas', 'productor'), null);
  assert.match(getProtectedSectionNotice('ventas', 'artista')?.title ?? '', /productores/);
  assert.equal(getProtectedSectionNotice('ventas', 'artista')?.requiresLogin, false);
});

test('favoritos exige cuenta de artista', () => {
  assert.equal(getProtectedSectionNotice('favoritos', 'artista'), null);
  assert.match(getProtectedSectionNotice('favoritos', 'productor')?.title ?? '', /artistas/);
  assert.equal(getProtectedSectionNotice('favoritos', 'productor')?.requiresLogin, false);
});

test('la vista de acceso ofrece acciones de inicio de sesión y registro', () => {
  const app = readFileSync(new URL('../App.tsx', import.meta.url), 'utf8');
  assert.match(app, /accessNotice\.requiresLogin/);
  assert.match(app, /handleOpenAuth\('login'\)/);
  assert.match(app, /handleOpenAuth\('register'\)/);
  assert.doesNotMatch(app, /Secci\?n de cuenta|Inicia sesi\?n/);
});
