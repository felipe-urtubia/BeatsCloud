import assert from 'node:assert/strict';
import test from 'node:test';
import { startWebpayCheckout, submitWebpayForm } from './webpayCheckout.mjs';

test('successful initialization submits the server URL and token, without claiming approval', async () => {
  const submitted = [];
  const result = await startWebpayCheckout(
    async () => ({ url_webpay: 'https://webpay.example/init', token_ws: 'server-token' }),
    (url, token) => submitted.push({ url, token }),
  );

  assert.deepEqual(submitted, [{ url: 'https://webpay.example/init', token: 'server-token' }]);
  assert.deepEqual(result, { status: 'redirecting' });
  assert.equal('approved' in result, false);
});

test('initialization errors are returned as errors and do not submit to Webpay', async () => {
  let submitted = false;
  const result = await startWebpayCheckout(
    async () => { throw new Error('Django no pudo iniciar Webpay.'); },
    () => { submitted = true; },
  );

  assert.deepEqual(result, { status: 'error', message: 'Django no pudo iniciar Webpay.' });
  assert.equal(submitted, false);
});

test('an incomplete initialization response does not become a successful checkout', async () => {
  let submitted = false;
  const result = await startWebpayCheckout(
    async () => ({ url_webpay: 'https://webpay.example/init' }),
    () => { submitted = true; },
  );

  assert.equal(result.status, 'error');
  assert.equal(submitted, false);
  assert.equal('approved' in result, false);
});

test('Webpay receives token_ws in a POST form', () => {
  const appended = [];
  let submitted = false;
  const fakeDocument = {
    createElement(tag) {
      return {
        tag,
        children: [],
        appendChild(child) { this.children.push(child); },
        submit() { submitted = true; },
      };
    },
    body: { appendChild(element) { appended.push(element); } },
  };
  const originalDocument = globalThis.document;
  globalThis.document = fakeDocument;

  try {
    submitWebpayForm('https://webpay.example/init', 'server-token');
  } finally {
    if (originalDocument === undefined) delete globalThis.document;
    else globalThis.document = originalDocument;
  }

  assert.equal(appended.length, 1);
  assert.equal(appended[0].method, 'POST');
  assert.equal(appended[0].action, 'https://webpay.example/init');
  assert.equal(appended[0].children[0].name, 'token_ws');
  assert.equal(appended[0].children[0].value, 'server-token');
  assert.equal(submitted, true);
});
