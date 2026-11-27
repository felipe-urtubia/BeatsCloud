import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve, extname, join, sep } from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const temporaryDir = process.env.D7_PLAYWRIGHT_DIR;

if (!temporaryDir) {
  throw new Error('D7_PLAYWRIGHT_DIR is required');
}

const require = createRequire(join(temporaryDir, 'package.json'));
const { chromium } = require('playwright-core');

const dist = fileURLToPath(new URL('../dist/', import.meta.url));
const origin = 'http://127.0.0.1:4317';

const mime = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.woff2': 'font/woff2',
  '.json': 'application/json',
};

const artist = {
  id: 42,
  username: 'artista_d7',
  first_name: 'Artista',
  last_name: 'Prueba',
  email: 'artista@example.test',
  tipo_usu: 1,
  nombre_artistico: 'Artista D7',
  descripcion: '',
  foto_perfil: null,
  foto_fondo: null,
  spotify: null,
  youtube: null,
  instagram: null,
  liked_track_ids: [],
  subscription_ids: [],
  subscription_periods: {},
};

const producer = {
  ...artist,
  id: 43,
  username: 'productor_d7',
  nombre_artistico: 'Productor D7',
  tipo_usu: 2,
  email: '',
};

const genre = { id: 1, descripcion: 'Hip-Hop' };

function makeTrack(id, title) {
  return {
    id_track: id,
    nombre_track: title,
    precio: 1000,
    track: `/media/d7-${id}.wav`,
    preview: null,
    descripcion: 'Fixture D7',
    foto: null,
    genero: genre,
    usuario: producer,
    likes_count: 0,
    resource_type: 'instrumental',
    bpm: 140,
    scale_key: 'Am',
    duration: 30,
    has_wav: true,
    has_stems: false,
    has_midi: false,
  };
}

const paidTrack = makeTrack(101, 'D7 Pista pagada');
const pendingTrack = makeTrack(102, 'D7 Pista pendiente');

const receipt = {
  status: 'AUTHORIZED',
  owner_id: '42',
  buy_order: 'orden-d7-browser',
  amount: '1190.00',
  currency: 'CLP',
  fulfilled_at: '2026-11-27T15:00:00Z',
};

const confirmedPurchase = {
  id: 'purchase-d7',
  transaction_id: 501,
  buy_order: receipt.buy_order,
  order_amount: 1190,
  line_amount: 1190,
  fecha_compra: receipt.fulfilled_at,
  status: 'AUTHORIZED',
  download_available: true,
  track: paidTrack,
};

function cartRow(track) {
  return {
    id: track.id_track + 1000,
    detalle: track.nombre_track,
    fecha: '2026-11-27',
    precio: 1000,
    iva: 190,
    precio_total: 1190,
    track: track.id_track,
  };
}

const wav = Buffer.alloc(46);

wav.write('RIFF', 0);
wav.writeUInt32LE(38, 4);
wav.write('WAVE', 8);
wav.write('fmt ', 12);
wav.writeUInt32LE(16, 16);
wav.writeUInt16LE(1, 20);
wav.writeUInt16LE(1, 22);
wav.writeUInt32LE(8000, 24);
wav.writeUInt32LE(16000, 28);
wav.writeUInt16LE(2, 32);
wav.writeUInt16LE(16, 34);
wav.write('data', 36);
wav.writeUInt32LE(2, 40);

const scenarios = [
  {
    name: 'approved - empty cart',
    query: 'pago=exito&orden=orden-d7-browser',
    approved: true,
    cart: [],
    notice: /Pago aprobado\. Tu compra fue confirmada/,
  },
  {
    name: 'approved - selective cart removal',
    query: 'pago=exito&orden=orden-d7-browser',
    approved: true,
    cart: [pendingTrack],
    notice: /Pago aprobado\. Tu compra fue confirmada/,
  },
  {
    name: 'rejected',
    query: 'pago=fracaso&estado=rechazado',
    cart: [paidTrack, pendingTrack],
    notice: /pago fue rechazado/,
  },
  {
    name: 'cancelled',
    query: 'pago=fracaso&estado=cancelado',
    cart: [paidTrack, pendingTrack],
    notice: /pago fue cancelado/,
  },
  {
    name: 'abandoned',
    query: 'pago=fracaso&estado=abandonado',
    cart: [paidTrack, pendingTrack],
    notice: /pago no fue completado dentro del plazo/,
  },
  {
    name: 'review',
    query: 'pago=revision',
    cart: [paidTrack, pendingTrack],
    notice: /Pago en revisi.n/,
  },
  {
    name: 'forged URL',
    query: 'pago=exito&orden=orden-falsa',
    cart: [paidTrack, pendingTrack],
    invalidReceipt: true,
    notice: /No pudimos verificar el comprobante/,
  },
  {
    name: 'receipt from another account',
    query: 'pago=exito&orden=orden-d7-browser',
    cart: [paidTrack, pendingTrack],
    wrongOwner: true,
    notice: /No pudimos verificar el comprobante/,
  },
];

async function launchBrowser() {
  for (const channel of ['msedge', 'chrome']) {
    try {
      const browser = await chromium.launch({
        channel,
        headless: true,
      });
      console.log('Browser:', channel);
      return browser;
    } catch (error) {
      console.log('Unavailable browser:', channel);
    }
  }

  throw new Error('Microsoft Edge or Google Chrome is required.');
}

async function runScenario(browser, scenario) {
  const context = await browser.newContext({
    acceptDownloads: true,
    serviceWorkers: 'block',
    locale: 'es-CL',
    viewport: { width: 1440, height: 1000 },
  });

  const page = await context.newPage();

  page.setDefaultTimeout(15000);

  const requests = [];
  const mutations = [];
  const pageErrors = [];

  let documentRequests = 0;

  page.on('pageerror', error => {
    pageErrors.push(error.message);
  });

  page.on('request', request => {
    if (
      request.isNavigationRequest() &&
      request.frame() === page.mainFrame()
    ) {
      documentRequests += 1;
    }
  });

  await context.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());

    // Never connect to production or external services.
    if (url.origin !== origin) {
      return route.abort();
    }

    const path = url.pathname;

    const json = (value, status = 200) =>
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(value),
      });

    if (path.startsWith('/api/')) {
      requests.push(path);

      if (request.method() !== 'GET') {
        mutations.push(`${request.method()} ${path}`);
        return json({ detail: 'Blocked test mutation' }, 405);
      }

      if (path === '/api/csrf/') {
        return json({ detail: 'd7-test-csrf' });
      }

      if (path === '/api/session/') {
        return json(artist);
      }

      if (path === '/api/catalogo/') {
        return json({
          page_size: 6,
          tracks: [paidTrack, pendingTrack],
          total_resultados: 2,
          pagina_actual: 1,
          total_paginas: 1,
          tracks_comprados: scenario.approved ? [101] : [],
          generos: [genre],
        });
      }

      if (path === '/api/usuarios/') {
        return json([artist, producer]);
      }

      if (path === '/api/auth/accounts/') {
        return json({
          active_user_id: 42,
          accounts: [],
        });
      }

      if (
        path === '/api/suscripciones/' ||
        path === '/api/mis-ventas/'
      ) {
        return json([]);
      }

      if (path === '/api/mis-compras/confirmadas/') {
        return json(
          scenario.approved ? [confirmedPurchase] : [],
        );
      }

      if (path === '/api/mis-compras/') {
        return json([]);
      }

      if (path === '/api/carrito/') {
        return json({
          items: scenario.cart.map(cartRow),
          subtotal: scenario.cart.length * 1000,
          iva: scenario.cart.length * 190,
          total: scenario.cart.length * 1190,
        });
      }

      if (path === '/api/webpay/receipt/') {
        if (
          scenario.invalidReceipt ||
          url.searchParams.get('buy_order') !== receipt.buy_order
        ) {
          return json({ detail: 'Not found' }, 404);
        }

        if (scenario.wrongOwner) {
          return json({ ...receipt, owner_id: '99' });
        }

        if (!scenario.approved) {
          return json({ detail: 'Not found' }, 404);
        }

        return json(receipt);
      }

      if (path === '/api/track/101/descargar/') {
        if (!scenario.approved) {
          return json({ detail: 'Forbidden' }, 403);
        }

        return route.fulfill({
          status: 200,
          headers: {
            'content-type': 'audio/wav',
            'content-disposition': 'attachment; filename="d7-test.wav"',
          },
          body: wav,
        });
      }

      return json({ detail: `Unknown test endpoint ${path}` }, 404);
    }

    if (path.startsWith('/media/')) {
      return route.fulfill({ status: 404, body: '' });
    }

    const root = resolve(dist);

    const file = resolve(
      root,
      path === '/' ? 'index.html' : `.${path}`,
    );

    if (!file.startsWith(root + sep)) {
      return route.abort();
    }

    try {
      return route.fulfill({
        status: 200,
        contentType: mime[extname(file)] || 'application/octet-stream',
        body: await readFile(file),
      });
    } catch {
      return route.fulfill({ status: 404, body: '' });
    }
  });

  try {
    await page.goto(
      `${origin}/?tab=carrito&${scenario.query}`,
      { waitUntil: 'domcontentloaded' },
    );

    await page.getByText(scenario.notice).waitFor({
      state: 'visible',
    });

    await page.waitForURL(
      url =>
        url.searchParams.get('tab') === 'carrito' &&
        !url.searchParams.has('pago') &&
        !url.searchParams.has('orden') &&
        !url.searchParams.has('estado'),
    );

    const receiptPanel = page.getByRole('region', {
      name: 'Comprobante de compra',
    });

    const purchasesButton = page.getByRole('button', {
      name: 'Ir a mis compras y descargas',
      exact: true,
    });

    if (scenario.cart.length === 0) {
      await page.getByText(
        'Tu carrito de producción está vacío',
        { exact: true },
      ).waitFor();
    } else {
      for (const track of scenario.cart) {
        await page.getByRole('heading', {
          name: track.nombre_track,
          exact: true,
        }).waitFor();
      }
    }

    if (scenario.approved) {
      await receiptPanel.waitFor();

      assert.ok(
        (await receiptPanel.innerText()).includes(receipt.buy_order),
      );

      assert.equal(
        await page.getByRole('heading', {
          name: paidTrack.nombre_track,
          exact: true,
        }).count(),
        0,
      );

      await purchasesButton.waitFor();

      assert.equal(await purchasesButton.isEnabled(), true);

      // A marker survives SPA navigation, but not a document reload.
      await page.evaluate(() => {
        window.__D7_DOCUMENT_MARKER = 'same-document';
      });

      await purchasesButton.click();

      await page.waitForURL(
        url => url.searchParams.get('tab') === 'perfil',
      );

      const downloadButton = page.getByRole('button', {
        name: 'Descargar audio',
        exact: true,
      });

      await downloadButton.waitFor();

      assert.equal(await downloadButton.isEnabled(), true);

      assert.equal(
        await page.evaluate(() => window.__D7_DOCUMENT_MARKER),
        'same-document',
      );

      assert.equal(documentRequests, 1);

      const downloaded = page.waitForEvent('download');

      await downloadButton.click();

      const file = await downloaded;

      assert.equal(file.suggestedFilename(), 'd7-test.wav');
      assert.equal(await file.failure(), null);

      assert.ok(
        requests.includes('/api/track/101/descargar/'),
      );

    } else {
      assert.equal(await receiptPanel.count(), 0);
      assert.equal(await purchasesButton.count(), 0);

      assert.equal(
        requests.includes('/api/track/101/descargar/'),
        false,
      );

      if (!scenario.invalidReceipt && !scenario.wrongOwner) {
        assert.equal(
          requests.includes('/api/webpay/receipt/'),
          false,
        );
      } else {
        assert.ok(
          requests.includes('/api/webpay/receipt/'),
        );
      }
    }

    assert.deepEqual(mutations, []);
    assert.deepEqual(pageErrors, []);

    console.log('PASS:', scenario.name);

  } finally {
    await context.close();
  }
}

const browser = await launchBrowser();

try {
  for (const scenario of scenarios) {
    await runScenario(browser, scenario);
  }

  console.log('D7 BROWSER: 8/8 PASS');

} finally {
  await browser.close();
}
