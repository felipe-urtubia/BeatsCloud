export function classifyLicenseRecord(record: {
  record_type?: unknown;
  verified?: unknown;
}): 'paid_license' | 'legacy_free_receipt' {

  if (
    record.record_type === 'paid_license' &&
    record.verified === true
  ) {
    return 'paid_license';
  }

  if (
    record.record_type === 'legacy_free_receipt' &&
    record.verified === false
  ) {
    return 'legacy_free_receipt';
  }

  throw new Error('El servidor no confirmo un registro valido.');
}

export function licensePresentation(
  recordType: unknown,
  verified: unknown,
) {
  if (recordType === 'paid_license' && verified === true) {
    return {
      title: 'Licencia comercial verificada',
      status: 'Verificada por el servidor',
      showHash: true,
      official: true,
    };
  }

  if (recordType === 'legacy_free_receipt' && verified === false) {
    return {
      title: 'Comprobante de adquisici\u00f3n gratuita',
      status: 'Sin verificaci\u00f3n comercial',
      showHash: false,
      official: true,
    };
  }

  return {
    title: 'Documento de demostraci\u00f3n',
    status: 'Sin validez comercial',
    showHash: false,
    official: false,
  };
}
