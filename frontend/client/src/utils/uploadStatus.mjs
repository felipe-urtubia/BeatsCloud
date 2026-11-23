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
  if (status === 'error') return configuredMode === 'hybrid' ? 'No se pudo completar la subida' : 'No se pudo crear el track de demostración';
  if (status === 'uploading') return configuredMode === 'hybrid' ? 'Subiendo archivo y verificando su publicación…' : 'Creando track en el entorno de demostración…';
  if (status === 'complete') return configuredMode === 'hybrid' ? 'Subida completada correctamente' : 'Track creado en el entorno de demostración';
  return configuredMode === 'hybrid' ? 'Archivo pendiente de subida' : 'Track pendiente de creación en el entorno de demostración';
}
