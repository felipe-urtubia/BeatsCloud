import assert from 'node:assert/strict';
import test from 'node:test';

import {
  readPaymentReturn,
  cleanPaymentReturnUrl,
  resolvePaymentReturn,
} from './webpayReturn.mjs';


const url = 'https://beatscloud.example/';

const sync = async () => ({
  userId: '42',
  purchasesSynced: true,
  orders: ['orden-d7'],
});

const receipt = {
  status: 'AUTHORIZED',
  owner_id: '42',
  buy_order: 'orden-d7',
  amount: '1190.00',
  currency: 'CLP',
  fulfilled_at: '2026-11-27T15:00:00Z',
};

const approved = {
  kind: 'approved',
  order: 'orden-d7',
};


test('approved waits for synchronization and private receipt', async () => {
  const calls = [];

  const output = await resolvePaymentReturn(
    approved,
    async () => {
      calls.push('sync');
      return sync();
    },
    async (order) => {
      calls.push('receipt');
      assert.equal(order, 'orden-d7');
      return receipt;
    },
  );

  assert.deepEqual(calls, ['sync', 'receipt']);
  assert.equal(output.ready, true);
  assert.equal(output.ownerId, '42');
  assert.deepEqual(output.receipt, receipt);
});


for (const [state, kind] of [
  ['rechazado', 'rejected'],
  ['cancelado', 'cancelled'],
  ['abandonado', 'abandoned'],
]) {
  test(`${kind} never requests a receipt or unlocks downloads`, async () => {
    const input = readPaymentReturn(
      `${url}?pago=fracaso&estado=${state}`
    );

    assert.equal(input.kind, kind);

    let calls = 0;

    const output = await resolvePaymentReturn(
      input,
      async () => {
        calls += 1;
        return sync();
      },
      async () => {
        assert.fail('Unexpected receipt request');
      },
    );

    assert.equal(calls, 1);
    assert.equal(output.ready, false);
    assert.equal(output.receipt, null);
    assert.ok(output.notice);
  });
}


test('ambiguous return remains under review', async () => {
  const input = readPaymentReturn(`${url}?pago=revision`);

  const output = await resolvePaymentReturn(
    input,
    sync,
    async () => assert.fail('Unexpected receipt'),
  );

  assert.equal(output.ready, false);
  assert.equal(output.receipt, null);
  assert.match(output.notice, /revisi/);
});


test('forged URL cannot manufacture an approved receipt', async () => {
  const output = await resolvePaymentReturn(
    approved,
    sync,
    async () => {
      throw new Error('404');
    },
  );

  assert.equal(output.ready, false);
  assert.equal(output.receipt, null);
});


test('wrong buy order is not accepted', async () => {
  const output = await resolvePaymentReturn(
    approved,
    sync,
    async () => ({ ...receipt, buy_order: 'other-order' }),
  );

  assert.equal(output.ready, false);
  assert.equal(output.receipt, null);
});


test('anonymous return cannot expose private receipt', async () => {
  const output = await resolvePaymentReturn(
    approved,
    async () => ({
      userId: null,
      purchasesSynced: false,
      orders: [],
    }),
    async () => assert.fail('Anonymous receipt request'),
  );

  assert.equal(output.ready, false);
  assert.equal(output.receipt, null);
});


test('partial purchase sync never unlocks downloads', async () => {
  const output = await resolvePaymentReturn(
    approved,
    async () => ({
      userId: '42',
      purchasesSynced: false,
      orders: [],
    }),
    async () => receipt,
  );

  assert.equal(output.ready, false);
  assert.deepEqual(output.receipt, receipt);
});


test('failed synchronization never claims approval', async () => {
  const output = await resolvePaymentReturn(
    approved,
    async () => {
      throw new Error('Network failure');
    },
    async () => assert.fail('Unexpected receipt'),
  );

  assert.equal(output.ready, false);
  assert.equal(output.receipt, null);
});


test('legacy subscription return does not create a cart receipt', async () => {
  const input = readPaymentReturn(`${url}?pago=exito`);

  assert.equal(input.kind, 'unverified');

  const output = await resolvePaymentReturn(
    input,
    sync,
    async () => assert.fail('Unexpected cart receipt'),
  );

  assert.equal(output.ready, false);
  assert.equal(output.receipt, null);
});


test('URL cleanup preserves SPA navigation without reload', () => {
  const cleaned = cleanPaymentReturnUrl(
    `${url}?tab=perfil&pago=exito&orden=orden-d7&estado=ok#compras`
  );

  assert.equal(cleaned, '/?tab=perfil#compras');
});


test('normal navigation is not interpreted as payment return', () => {
  assert.equal(readPaymentReturn(`${url}?tab=catalogo`), null);
});


test('receipt from a different active account is rejected', async () => {
  const output = await resolvePaymentReturn(
    approved,
    sync,
    async () => ({
      ...receipt,
      owner_id: '99',
    }),
  );

  assert.equal(output.ready, false);
  assert.equal(output.receipt, null);
  assert.equal(output.ownerId, null);
});
