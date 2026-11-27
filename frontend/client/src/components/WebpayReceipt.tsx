import type { WebpayReceipt as Receipt } from '../api/webpayReturn.mjs';

interface Props {
  receipt: Receipt;
}

export function WebpayReceipt({ receipt }: Props) {
  const amount = new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: receipt.currency,
    maximumFractionDigits: 0,
  }).format(Number(receipt.amount));

  const date = new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(receipt.fulfilled_at));

  return (
    <section
      aria-label="Comprobante de compra"
      className="rounded-xl border border-emerald-500/30 bg-zinc-950 p-4 text-sm"
    >
      <h2 className="mb-3 font-bold text-emerald-400">
        Pago aprobado
      </h2>

      <dl className="grid gap-2 text-zinc-200">
        <div className="flex flex-wrap justify-between gap-3">
          <dt className="text-zinc-400">Número de orden</dt>
          <dd className="break-all font-mono">{receipt.buy_order}</dd>
        </div>

        <div className="flex justify-between gap-3">
          <dt className="text-zinc-400">Importe pagado</dt>
          <dd className="font-semibold">{amount} CLP</dd>
        </div>

        <div className="flex justify-between gap-3">
          <dt className="text-zinc-400">Fecha de entrega</dt>
          <dd>{date}</dd>
        </div>

        <div className="flex justify-between gap-3">
          <dt className="text-zinc-400">Estado</dt>
          <dd className="font-semibold text-emerald-400">Autorizado</dd>
        </div>
      </dl>
    </section>
  );
}
