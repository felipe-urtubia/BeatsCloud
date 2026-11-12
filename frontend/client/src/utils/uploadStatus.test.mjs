import test from 'node:test';
import assert from 'node:assert/strict';
import { getUploadStatusLabel, uploadStatusReducer } from './uploadStatus.mjs';

test('upload status reflects pending, active and failed states', () => {
  assert.equal(getUploadStatusLabel('pending', 'hybrid'), 'Archivo pendiente de subida');
  assert.equal(getUploadStatusLabel('uploading', 'hybrid'), 'Subiendo a Django y esperando confirmación');
  assert.equal(getUploadStatusLabel('error', 'hybrid'), 'La subida a Django falló');
  assert.equal(getUploadStatusLabel('pending', 'mock'), 'Track pendiente de creación en el entorno de demostración');
  assert.equal(getUploadStatusLabel('uploading', 'mock'), 'Creando track en el entorno de demostración…');
  assert.equal(getUploadStatusLabel('error', 'mock'), 'No se pudo crear el track de demostración');
});

test('successful upload wording reflects whether Django or local demo handled it', () => {
  assert.equal(getUploadStatusLabel('complete', 'hybrid'), 'Subida completada y confirmada por Django');
  assert.equal(getUploadStatusLabel('complete', 'mock'), 'Track creado en el entorno de demostración');
});

test('upload lifecycle only completes after start and resets after file selection or form reset', () => {
  assert.equal(uploadStatusReducer('pending', { type: 'succeed' }), 'pending');
  assert.equal(uploadStatusReducer('pending', { type: 'start' }), 'uploading');
  assert.equal(uploadStatusReducer('uploading', { type: 'succeed' }), 'complete');
  assert.equal(uploadStatusReducer('complete', { type: 'start' }), 'complete');
  assert.equal(uploadStatusReducer('uploading', { type: 'fail' }), 'error');
  assert.equal(uploadStatusReducer('error', { type: 'start' }), 'uploading');
  assert.equal(uploadStatusReducer('complete', { type: 'reset' }), 'pending');
});
