import test from 'node:test';
import assert from 'node:assert/strict';
import { dismissNotification, enqueueNotification } from './notificationQueue.mjs';

test('limits the visible notification stack to the newest three messages', () => {
  const queue = [1, 2, 3, 4].reduce(
    (items, id) => enqueueNotification(items, { id, kind: 'success', message: `Aviso ${id}` }),
    [],
  );
  assert.deepEqual(queue.map((item) => item.id), [2, 3, 4]);
});

test('deduplicates repeated notifications with the same kind and message', () => {
  const item = { id: 1, kind: 'error', message: 'No se pudo guardar.' };
  assert.deepEqual(enqueueNotification([item], { ...item, id: 2 }), [item]);
});

test('dismisses only the selected notification', () => {
  const queue = [
    { id: 1, kind: 'success', message: 'Agregado.' },
    { id: 2, kind: 'error', message: 'Falló.' },
  ];
  assert.deepEqual(dismissNotification(queue, 1), [queue[1]]);
});
