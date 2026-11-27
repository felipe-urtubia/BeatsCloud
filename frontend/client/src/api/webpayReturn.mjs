/**
 * D7: los parametros de URL son avisos, no autorizaciones.
 * Un pago solo se presenta como aprobado tras verificar
 * su comprobante privado con Django.
 */

export function readPaymentReturn(href) {
  const params = new URL(href).searchParams;

  if (!params.has('pago')) return null;

  const pago = params.get('pago');
  const estado = params.get('estado');
  const order = params.get('orden')?.trim() || '';

  if (pago === 'exito') {
    if (order && order.length <= 50) {
      return { kind: 'approved', order };
    }

    return { kind: 'unverified' };
  }

  if (pago === 'fracaso') {
    if (estado === 'rechazado') return { kind: 'rejected' };
    if (estado === 'cancelado') return { kind: 'cancelled' };
    if (estado === 'abandonado') return { kind: 'abandoned' };

    return { kind: 'failed' };
  }

  if (pago === 'cancelado') return { kind: 'cancelled' };

  return { kind: 'review' };
}


export function cleanPaymentReturnUrl(href) {
  const url = new URL(href);

  if (url.searchParams.has('pago')) {
    for (const key of ['pago', 'estado', 'orden']) {
      url.searchParams.delete(key);
    }
  }

  return `${url.pathname}${url.search}${url.hash}`;
}


const notices = {
  rejected: 'Webpay informó que el pago fue rechazado. Tu carrito no se ha vaciado por esta operación.',
  cancelled: 'Webpay informó que el pago fue cancelado. Tu carrito se conserva.',
  abandoned: 'El pago no fue completado dentro del plazo. Tu carrito se conserva.',
  failed: 'Webpay informó que el pago no fue aprobado. Revisa tu carrito.',
  review: 'Pago en revisión: no vuelvas a pagar hasta verificar el estado de tu operación.',
  unverified: 'Retorno de Webpay recibido. Consulta el estado de tus compras o suscripciones.',
};


function result(notice, receipt = null, ownerId = null, ready = false) {
  return { notice, receipt, ownerId, ready };
}


export async function resolvePaymentReturn(input, synchronize, getReceipt) {
  let synced;

  try {
    synced = await synchronize();
  } catch {
    return result(
      input.kind === 'approved'
        ? 'No pudimos verificar el pago. Revisa tu historial antes de volver a pagar.'
        : notices[input.kind]
    );
  }

  if (input.kind !== 'approved') {
    return result(notices[input.kind]);
  }

  if (!synced?.userId) {
    return result(
      'Inicia sesión y consulta tus compras para verificar esta operación.'
    );
  }

  try {
    const receipt = await getReceipt(input.order);

    if (
      !receipt ||
      receipt.status !== 'AUTHORIZED' ||
      receipt.owner_id !== synced.userId ||
      receipt.buy_order !== input.order ||
      receipt.currency !== 'CLP' ||
      typeof receipt.amount !== 'string' ||
      !/^\d+(\.\d{1,2})?$/.test(receipt.amount) ||
      !Number.isFinite(Date.parse(receipt.fulfilled_at))
    ) {
      throw new Error('Comprobante invalido');
    }

    const ready = synced.purchasesSynced &&
      synced.orders.includes(input.order);

    return result(
      ready
        ? 'Pago aprobado. Tu compra fue confirmada y puedes consultar tus descargas.'
        : 'Pago aprobado. No pudimos confirmar todas tus descargas; consulta tus compras antes de volver a pagar.',
      receipt,
      synced.userId,
      ready,
    );

  } catch {
    return result(
      'No pudimos verificar el comprobante. No vuelvas a pagar hasta revisar tu operación.'
    );
  }
}
