export function uploadStatusReducer(state, action) {
  switch (action.type) {
    case 'start':
      return state === 'complete' ? state : 'uploading';
    case 'succeed':
      return state === 'uploading' ? 'complete' : state;
    case 'fail':
      return state === 'complete' ? state : 'error';
    case 'reset':
      return 'pending';
    default:
      return state;
  }
}

export function getUploadStatusLabel(status, configuredMode) {
  if (status === 'error') return configuredMode === 'hybrid' ? 'La subida a Django falló' : 'No se pudo crear el track de demostración';
  if (status === 'uploading') return configuredMode === 'hybrid' ? 'Subiendo a Django y esperando confirmación' : 'Creando track en el entorno de demostración…';
  if (status === 'complete') return configuredMode === 'hybrid' ? 'Subida completada y confirmada por Django' : 'Track creado en el entorno de demostración';
  return configuredMode === 'hybrid' ? 'Archivo pendiente de subida' : 'Track pendiente de creación en el entorno de demostración';
}
