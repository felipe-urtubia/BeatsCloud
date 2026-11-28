import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve, extname, join, sep } from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const temporaryDir = process.env.REPORTS_PLAYWRIGHT_DIR;

if (!temporaryDir) {
  throw new Error('REPORTS_PLAYWRIGHT_DIR is required');
}

const require = createRequire(
  join(temporaryDir, 'package.json'),
);

const { chromium } = require('playwright-core');

const origin = 'http://127.0.0.1:4318';

const dist = fileURLToPath(
  new URL('../dist/', import.meta.url),
);

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

const start = new Date(
  Date.now() - 86400000,
).toISOString();

const end = new Date(
  Date.now() + 86400000 * 30,
).toISOString();

const contract = {
  detalle: 'Membresia Premium de prueba',
  descripcion: 'Servicios musicales de prueba',
  beneficios: ['Instrumentales exclusivas'],
  precio: 15000,
};

const artistA = {
  id: 42,
  username: 'report_artist_a',
  first_name: 'Artista',
  last_name: 'A',
  email: 'artist-a@example.test',
  tipo_usu: 1,
  nombre_artistico: 'Artista Reportes A',
  descripcion: '',
  foto_perfil: null,
  foto_fondo: null,
  spotify: null,
  youtube: null,
  instagram: null,
  liked_track_ids: [],
  subscription_ids: [71],
  subscription_periods: {
    '71': {
      starts_at: start,
      expires_at: end,
      active: true,
      duration_count: 1,
      duration_unit: 'meses',
      contract,
      amount_clp: '15000',
    },
  },
};

const artistB = {
  ...artistA,
  id: 44,
  username: 'report_artist_b',
  nombre_artistico: 'Artista Reportes B',
  email: 'artist-b@example.test',
};

const producer = {
  ...artistA,
  id: 43,
  username: 'report_producer',
  nombre_artistico: 'Productor Reportes',
  tipo_usu: 2,
  subscription_ids: [],
  subscription_periods: {},
};

function makeReport(id, status, changes = {}) {

  return {
    id,
    subscription_id: 71,
    subscription_title: contract.detalle,
    producer_name: producer.nombre_artistico,
    reason: 'MISSING_BENEFITS',
    reason_label: 'Beneficios no entregados',
    description: 'Descripcion privada de prueba.',
    status,
    status_label: status,
    resolution: '',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    contract_started_at: start,
    reviewed_at: null,
    ...changes,
  };
}

const originalDescription =
  'No se entregaron los beneficios musicales contratados.';

const privateA =
  'Contenido privado exclusivo de la cuenta A.';

const privateB =
  'Contenido privado exclusivo de la cuenta B.';

const resolution =
  'Se revisaron los antecedentes y se gestiono el caso.';

const scenarios = [
  {
    name: 'create report',
    type: 'create',
    reports: [],
  },
  {
    name: 'duplicate prevention',
    type: 'duplicate',
    reports: [makeReport(101, 'OPEN')],
  },
  {
    name: 'history and filters',
    type: 'history',
    reports: [
      makeReport(201, 'RESOLVED', {
        resolution,
        reviewed_at: start,
      }),
      makeReport(202, 'DISMISSED', {
        resolution: 'No se acredito el incumplimiento informado.',
        reviewed_at: start,
      }),
      makeReport(203, 'IN_REVIEW'),
      makeReport(204, 'OPEN'),
    ],
  },
  {
    name: 'failed submission',
    type: 'failure',
    reports: [],
  },
  {
    name: 'wrong owner response',
    type: 'wrongOwner',
    reports: [
      makeReport(301, 'OPEN', {
        description: privateB,
      }),
    ],
  },
  {
    name: 'pending GET cancellation',
    type: 'pendingGet',
    reports: [],
  },
  {
    name: 'pending POST during account switching',
    type: 'pendingPost',
    reports: [],
  },
  {
    name: 'account switching',
    type: 'switch',
    reports: [
      makeReport(401, 'RESOLVED', {
        description: privateA,
        resolution,
        reviewed_at: start,
      }),
    ],
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

    } catch {

      console.log('Unavailable browser:', channel);
    }
  }

  throw new Error('Edge or Chrome is required.');
}

async function runScenario(browser, scenario) {

  const context = await browser.newContext({
    serviceWorkers: 'block',
    locale: 'es-CL',
    viewport: {
      width: 1440,
      height: 1000,
    },
  });

  const page = await context.newPage();

  page.setDefaultTimeout(15000);

  const pageErrors = [];
  const unexpectedMutations = [];
  const reportPosts = [];

  let activeArtist = artistA;
  let switches = 0;
  let reportGetCount = 0;

  let releaseGet;
  let releasePost;
  let releaseSwitch;

  const getGate = new Promise(resolve => {
    releaseGet = resolve;
  });

  const postGate = new Promise(resolve => {
    releasePost = resolve;
  });

  const switchGate = new Promise(resolve => {
    releaseSwitch = resolve;
  });

  const reportsByOwner = {
    '42': scenario.reports.map(item => ({ ...item })),
    '44': [
      makeReport(402, 'OPEN', {
        description: privateB,
      }),
    ],
  };

  const accountResponse = () => ({
    active_user_id: activeArtist.id,
    accounts: [artistA, artistB].map(artist => ({
      id: artist.id,
      username: artist.username,
      is_current: artist.id === activeArtist.id,
    })),
  });

  page.on('pageerror', error => {
    pageErrors.push(error.message);
  });

  await context.route('**/*', async route => {

    const request = route.request();

    const url = new URL(request.url());

    // Bloquear todos los servicios externos y produccion.
    if (url.origin !== origin) {
      return route.abort();
    }

    const path = url.pathname;
    const method = request.method();

    const json = (value, status = 200) =>
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(value),
      });

    if (path.startsWith('/api/')) {

      if (
        path === '/api/auth/accounts/switch/' &&
        method === 'POST' &&
        (
          scenario.type === 'switch' ||
          scenario.type === 'pendingPost'
        )
      ) {

        assert.equal(
          request.postDataJSON().user_id,
          artistB.id,
        );

        if (scenario.type === 'pendingPost') {
          await switchGate;
        }

        activeArtist = artistB;
        switches += 1;

        return json(accountResponse());
      }

      if (path === '/api/subscription-reports/') {

        const expectedOwner =
          request.headers()['x-report-owner'];

        if (expectedOwner !== String(activeArtist.id)) {

          return json({
            detail: 'La identidad de la sesion ha cambiado.',
          }, 409);
        }

        if (method === 'GET') {

          reportGetCount += 1;

          if (
            scenario.type === 'pendingGet' &&
            reportGetCount === 1
          ) {

            await getGate;

            // La respuesta pertenece a una vista desmontada.
            return json({
              owner_id: '42',
              reports: [
                makeReport(701, 'OPEN', {
                  description: privateA,
                }),
              ],
            }).catch(() => {});
          }

          return json({
            owner_id: scenario.type === 'wrongOwner'
              ? '99'
              : String(activeArtist.id),
            reports: reportsByOwner[String(activeArtist.id)],
          });
        }

        if (method === 'POST') {

          const data = request.postDataJSON();

          reportPosts.push(data);

          assert.equal(
            request.headers()['x-csrftoken'],
            'reports-test-csrf',
          );

          assert.deepEqual(
            Object.keys(data).sort(),
            [
              'description',
              'reason',
              'subscription_id',
            ],
          );

          assert.equal(data.subscription_id, 71);

          if (scenario.type === 'failure') {

            return json({
              detail: 'Error de comunicacion de prueba.',
            }, 503);
          }

          if (
            scenario.type !== 'create' &&
            scenario.type !== 'pendingPost'
          ) {

            unexpectedMutations.push(
              `${method} ${path}`,
            );

            return json({
              detail: 'Unexpected report mutation',
            }, 405);
          }

          const created = makeReport(
            501,
            'OPEN',
            {
              reason: data.reason,
              description: data.description,
            },
          );

          reportsByOwner[String(activeArtist.id)]
            .unshift(created);

          if (scenario.type === 'pendingPost') {

            // Simular que el servidor guardo el reporte,
            // aunque la respuesta al navegador siga pendiente.
            await postGate;

            return json({
              detail: 'Reporte creado.',
              owner_id: '42',
              report: created,
            }, 201).catch(() => {});
          }

          return json({
            detail: 'Reporte creado.',
            owner_id: String(activeArtist.id),
            report: created,
          }, 201);
        }
      }

      if (method !== 'GET') {

        unexpectedMutations.push(
          `${method} ${path}`,
        );

        return json({
          detail: 'Blocked test mutation',
        }, 405);
      }

      if (path === '/api/csrf/') {

        return json({
          detail: 'reports-test-csrf',
        });
      }

      if (path === '/api/session/') {
        return json(activeArtist);
      }

      if (path === '/api/usuarios/') {
        return json([artistA, artistB, producer]);
      }

      if (path === '/api/auth/accounts/') {
        return json(accountResponse());
      }

      if (path === '/api/catalogo/') {

        return json({
          page_size: 6,
          tracks: [],
          total_resultados: 0,
          pagina_actual: 1,
          total_paginas: 1,
          tracks_comprados: [],
          generos: [],
        });
      }

      if (path === '/api/carrito/') {

        return json({
          items: [],
          subtotal: 0,
          iva: 0,
          total: 0,
        });
      }

      if ([
        '/api/suscripciones/',
        '/api/mis-compras/',
        '/api/mis-compras/confirmadas/',
        '/api/mis-ventas/',
      ].includes(path)) {
        return json([]);
      }

      return json({
        detail: `Unknown test endpoint ${path}`,
      }, 404);
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
        contentType:
          mime[extname(file)] ||
          'application/octet-stream',
        body: await readFile(file),
      });

    } catch {

      return route.fulfill({
        status: 404,
        body: '',
      });
    }
  });

  const history = page.getByRole('region', {
    name: 'Mis reportes',
    exact: true,
  });

  const reportButton = page.getByRole('button', {
    name: 'Reportar incumplimiento',
    exact: true,
  });

  const refreshButton = page.getByRole('button', {
    name: 'Actualizar reportes',
    exact: true,
  });

  async function openMemberships() {

    await page.getByRole('button', {
      name: /MEMBRES.AS VIP/i,
    }).click();

    await page.getByRole('heading', {
      name: 'Mis membres\u00edas',
      exact: true,
    }).waitFor();
  }

  async function fillReport(description) {

    await reportButton.click();

    const form = page.getByRole('form', {
      name: 'Reportar incumplimiento',
    });

    await form.waitFor();

    const send = form.getByRole('button', {
      name: 'Enviar reporte',
      exact: true,
    });

    assert.equal(await send.isEnabled(), false);

    await form.getByRole('combobox')
      .selectOption('MISSING_BENEFITS');

    await form.getByRole('textbox')
      .fill('Muy corto');

    assert.equal(await send.isEnabled(), false);

    await form.getByRole('textbox')
      .fill(description);

    assert.equal(await send.isEnabled(), true);

    return send;
  }

  try {

    await page.goto(
      `${origin}/?tab=perfil`,
      { waitUntil: 'domcontentloaded' },
    );

    const pendingGetRequest =
      scenario.type === 'pendingGet'
        ? page.waitForRequest(request =>
            request.url().includes('/api/subscription-reports/') &&
            request.method() === 'GET',
          )
        : null;

    await openMemberships();

    if (scenario.type === 'pendingGet') {

      await pendingGetRequest;

      const cancelled = page.waitForEvent(
        'requestfailed',
        {
          predicate: request =>
            request.url().includes('/api/subscription-reports/') &&
            request.method() === 'GET',
        },
      );

      await page.getByRole('button', {
        name: /BEATS GUARDADOS/i,
      }).click();

      await cancelled;

      assert.equal(await history.count(), 0);

      releaseGet();

      await openMemberships();

      await history.waitFor();

      assert.equal(
        await history.getByRole('article').count(),
        0,
      );

      assert.equal(
        await page.getByText(privateA, {
          exact: true,
        }).count(),
        0,
      );

      assert.equal(reportGetCount, 2);

    } else if (scenario.type === 'wrongOwner') {

      await page.getByText(
        'No se pudo verificar la identidad de los reportes.',
        { exact: true },
      ).waitFor();

      assert.equal(await history.count(), 0);
      assert.equal(await reportButton.count(), 0);

      assert.equal(
        await page.getByText(privateB, {
          exact: true,
        }).count(),
        0,
      );

    } else {

      await history.waitFor();

      if (scenario.type === 'create') {

        const send = await fillReport(
          originalDescription,
        );

        await send.click();

        await page.getByText(
          /Reporte #501 enviado correctamente/,
        ).waitFor();

        await history.getByRole('article', {
          name: 'Reporte #501',
        }).waitFor();

        assert.equal(
          reportPosts.length,
          1,
        );

        assert.deepEqual(reportPosts[0], {
          subscription_id: 71,
          reason: 'MISSING_BENEFITS',
          description: originalDescription,
        });

        assert.equal(
          await reportButton.count(),
          0,
        );

      } else if (scenario.type === 'duplicate') {

        await page.getByText(
          'Ya existe un reporte abierto para esta membres\u00eda.',
          { exact: true },
        ).waitFor();

        assert.equal(
          await reportButton.count(),
          0,
        );

      } else if (scenario.type === 'history') {

        assert.equal(
          await history.getByRole('article').count(),
          4,
        );

        const filter = history.getByRole('combobox');

        for (const status of [
          'OPEN',
          'IN_REVIEW',
          'RESOLVED',
          'DISMISSED',
        ]) {

          await filter.selectOption(status);

          assert.equal(
            await history.getByRole('article').count(),
            1,
          );

          if (status === 'RESOLVED') {

            await history.getByText(resolution, {
              exact: true,
            }).waitFor();
          }
        }

        await filter.selectOption('ALL');

        assert.equal(
          await history.getByRole('article').count(),
          4,
        );

      } else if (scenario.type === 'failure') {

        const send = await fillReport(
          originalDescription,
        );

        await send.click();

        await page.getByText(
          /Actualiza tus reportes antes de volver a enviar/,
        ).waitFor();

        assert.equal(await reportButton.count(), 0);

        assert.equal(
          await page.getByRole('button', {
            name: 'Enviar reporte',
            exact: true,
          }).count(),
          0,
        );

        assert.equal(reportPosts.length, 1);

        await refreshButton.click();

        await history.waitFor();

        assert.equal(
          await history.getByRole('article').count(),
          0,
        );

      } else if (scenario.type === 'pendingPost') {

        const send = await fillReport(
          originalDescription,
        );

        const pendingRequest = page.waitForRequest(
          request =>
            request.url().includes('/api/subscription-reports/') &&
            request.method() === 'POST',
        );

        await send.click();

        await pendingRequest;

        const cancelled = page.waitForEvent(
          'requestfailed',
          {
            predicate: request =>
              request.url().includes('/api/subscription-reports/') &&
              request.method() === 'POST',
          },
        );

        await page.getByRole('button', {
          name: /Artista Reportes A.*artista/i,
        }).click();

        const switchButton = page.getByRole('button', {
          name: /@report_artist_b.*Cambiar/i,
        });

        await switchButton.click();

        // Debe cancelarse antes de confirmar el cambio
        // de cuenta y antes de recargar la pagina.
        await cancelled;

        assert.equal(await history.count(), 0);
        assert.equal(await reportButton.count(), 0);

        assert.equal(
          await page.getByRole('form', {
            name: 'Reportar incumplimiento',
          }).count(),
          0,
        );

        const reload = page.waitForEvent(
          'domcontentloaded',
        );

        releasePost();
        releaseSwitch();

        await reload;

        await openMemberships();

        await history.getByText(privateB, {
          exact: true,
        }).waitFor();

        assert.equal(
          await history.getByRole('article', {
            name: 'Reporte #501',
          }).count(),
          0,
        );

        assert.equal(
          reportsByOwner['42'].length,
          1,
        );

        assert.equal(
          reportsByOwner['44'].length,
          1,
        );

        assert.equal(switches, 1);

      } else if (scenario.type === 'switch') {

        await history.getByText(privateA, {
          exact: true,
        }).waitFor();

        await fillReport(
          'Borrador exclusivo de la cuenta anterior.',
        );

        await page.getByRole('button', {
          name: /Artista Reportes A.*artista/i,
        }).click();

        const switchButton = page.getByRole('button', {
          name: /@report_artist_b.*Cambiar/i,
        });

        await switchButton.waitFor();

        const reload = page.waitForEvent(
          'domcontentloaded',
        );

        await switchButton.click();

        await reload;

        await openMemberships();

        await history.getByText(privateB, {
          exact: true,
        }).waitFor();

        assert.equal(
          await page.getByText(privateA, {
            exact: true,
          }).count(),
          0,
        );

        assert.equal(
          await page.getByRole('textbox', {
            name: 'Descripci\u00f3n del incumplimiento',
          }).count(),
          0,
        );

        assert.equal(switches, 1);
      }
    }

    const expectedPosts = (
      scenario.type === 'create' ||
      scenario.type === 'failure' ||
      scenario.type === 'pendingPost'
    ) ? 1 : 0;

    assert.equal(
      reportPosts.length,
      expectedPosts,
    );

    assert.deepEqual(unexpectedMutations, []);
    assert.deepEqual(pageErrors, []);

    console.log('PASS:', scenario.name);

  } finally {

    releaseGet();
    releasePost();
    releaseSwitch();

    await context.close();
  }
}

const browser = await launchBrowser();

try {

  for (const scenario of scenarios) {
    await runScenario(browser, scenario);
  }

  console.log('REPORTS BROWSER: 8/8 PASS');

} finally {

  await browser.close();
}
