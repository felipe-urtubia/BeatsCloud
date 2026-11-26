import test from 'node:test';
import assert from 'node:assert/strict';

import {
  classifyLicenseRecord,
  licensePresentation,
} from './licenseRecord.ts';

test('licencia comercial confirmada por el servidor', () => {
  assert.equal(classifyLicenseRecord({
    record_type: 'paid_license',
    verified: true,
  }), 'paid_license');
});

test('comprobante gratuito no es licencia comercial', () => {
  assert.equal(classifyLicenseRecord({
    record_type: 'legacy_free_receipt',
    verified: false,
  }), 'legacy_free_receipt');

  assert.equal(
    licensePresentation('legacy_free_receipt', false).showHash,
    false,
  );
});

test('licencia comercial sin verificar se rechaza', () => {
  assert.throws(() => classifyLicenseRecord({
    record_type: 'paid_license',
    verified: false,
  }));
});

test('respuesta incompleta no acredita licencia', () => {
  assert.throws(() => classifyLicenseRecord({}));
});

test('comprobante gratuito con estado inconsistente se rechaza', () => {
  assert.throws(() => classifyLicenseRecord({
    record_type: 'legacy_free_receipt',
    verified: true,
  }));
});

test('documento de demostracion no tiene validez comercial', () => {
  const documento = licensePresentation(undefined, undefined);

  assert.equal(documento.official, false);
  assert.equal(documento.showHash, false);
});

test('solo licencia comercial confirmada muestra firma', () => {
  assert.equal(
    licensePresentation('paid_license', true).showHash,
    true,
  );

  assert.equal(
    licensePresentation('paid_license', false).showHash,
    false,
  );
});
