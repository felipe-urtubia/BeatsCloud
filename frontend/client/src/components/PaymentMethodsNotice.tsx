import { CreditCard, ShieldCheck } from 'lucide-react';

interface PaymentMethodsNoticeProps {
  compact?: boolean;
}

export const PaymentMethodsNotice = ({
  compact = false,
}: PaymentMethodsNoticeProps) => (
  <section
    aria-label="Medios de pago aceptados"
    className={`rounded-xl border border-zinc-700/70 bg-zinc-900/60 ${
      compact ? 'p-3' : 'p-4'
    }`}
  >
    <div className="flex items-center gap-2 text-amber-400">
      <CreditCard className="h-4 w-4 shrink-0" />
      <h4 className="text-xs font-bold">
        Medios de pago disponibles
      </h4>
    </div>

    <ul className="mt-3 grid grid-cols-3 gap-2">
      {['Crédito', 'Débito', 'Prepago'].map((medio) => (
        <li
          key={medio}
          className="rounded-lg border border-zinc-700 bg-zinc-800/80 px-2 py-2 text-center text-xs font-semibold text-zinc-200"
        >
          {medio}
        </li>
      ))}
    </ul>

    <div className="mt-3 flex items-start gap-2">
      <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
      <p className="text-xs leading-relaxed text-zinc-400">
        Pago seguro en pesos chilenos (CLP) mediante Webpay Plus.
        Utiliza una tarjeta compatible y completa el pago
        directamente en Transbank.
      </p>
    </div>

    <p className="mt-2 text-xs text-zinc-500">
      BeatsCloud no solicita ni almacena los datos de tu tarjeta.
    </p>
  </section>
);
