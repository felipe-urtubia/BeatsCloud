import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { runInNewContext } from 'node:vm';

import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import ts from 'typescript';

const require = createRequire(import.meta.url);

const source = readFileSync(
  new URL('./PaymentMethodsNotice.tsx', import.meta.url),
  'utf8',
);

const compiled = ts.transpileModule(source, {
  compilerOptions: {
    jsx: ts.JsxEmit.ReactJSX,
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
});

const context = {
  exports: {},
  require,
};

runInNewContext(compiled.outputText, context);

const { PaymentMethodsNotice } = context.exports;

function render(compact = false) {
  return renderToStaticMarkup(
    React.createElement(PaymentMethodsNotice, { compact }),
  );
}

test('muestra credito, debito y prepago correctamente', () => {
  const html = render();

  assert.match(html, />Cr\u00e9dito<\/li>/);
  assert.match(html, />D\u00e9bito<\/li>/);
  assert.match(html, />Prepago<\/li>/);

  assert.doesNotMatch(html, /Cr\?dito|D\?bito/);
});

test('informa CLP, Webpay y seguridad', () => {
  const html = render();

  assert.match(html, /Webpay Plus/);
  assert.match(html, /Transbank/);
  assert.match(html, /CLP/);
  assert.match(html, /Medios de pago disponibles/);
  assert.match(
    html,
    /BeatsCloud no solicita ni almacena los datos de tu tarjeta/,
  );
});

test('admite presentacion normal y compacta', () => {
  const normal = render();
  const compacta = render(true);

  assert.match(normal, /bg-zinc-900\/60 p-4/);
  assert.match(compacta, /bg-zinc-900\/60 p-3/);
});

test('esta integrado en carrito y suscripciones', () => {
  const carrito = readFileSync(
    new URL('./CartPage.tsx', import.meta.url),
    'utf8',
  );

  const productor = readFileSync(
    new URL('./ProducerProfilePage.tsx', import.meta.url),
    'utf8',
  );

  assert.match(
    carrito,
    /import \{ PaymentMethodsNotice \} from '\.\/PaymentMethodsNotice'/,
  );

  assert.match(
    carrito,
    /<PaymentMethodsNotice \/>/,
  );

  assert.match(
    productor,
    /import \{ PaymentMethodsNotice \} from '\.\/PaymentMethodsNotice'/,
  );

  assert.match(
    productor,
    /<PaymentMethodsNotice compact \/>/,
  );
});
