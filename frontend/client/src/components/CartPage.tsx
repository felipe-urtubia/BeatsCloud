import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { getResourceBadgeInfo } from '../utils/resourceHelpers';
import {
  ShoppingCart,
  Trash2,
  ShieldCheck,
  ArrowRight,
} from 'lucide-react';

interface CartPageProps {
  onNavigateCatalog: () => void;
  onOpenTrackDetail: (trackId: string) => void;
}

export const CartPage: React.FC<CartPageProps> = ({
  onNavigateCatalog,
  onOpenTrackDetail,
}) => {
  const { cart, removeFromCart, clearCart, checkoutCart } = useApp();

  const [isProcessing, setIsProcessing] = useState(false);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);
  const [checkoutNotice, setCheckoutNotice] = useState<string | null>(null);

  const subtotal = cart.reduce((sum, item) => sum + item.track.price, 0);
  const iva = Math.round(subtotal * 0.19);
  const total = subtotal + iva;

  const handleStartCheckout = async () => {
    if (isProcessing) return;
    setCheckoutError(null);
    setCheckoutNotice(null);
    if (total <= 0) {
      setCheckoutError('Webpay no puede iniciar un pago con total $0.');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await checkoutCart();
      if (result.status === 'error') {
        setCheckoutError(result.message);
        setIsProcessing(false);
        return;
      }

      setCheckoutNotice(
        'Continuando hacia Webpay. Django confirmará el resultado al recibir y validar el retorno de Transbank.',
      );
      // Keep the action disabled while the browser posts to Webpay.
      return;
    } catch (error) {
      setCheckoutError(error instanceof Error ? error.message : 'No fue posible iniciar el pago Webpay.');
      setIsProcessing(false);
    }
  };

  return (
    <div className="py-6 pb-36 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5 font-mono">
            <ShoppingCart className="w-6 h-6 text-amber-400" />
            <span>CARRITO DE COMPRAS</span>
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Django confirma el pago después de validar el retorno de Transbank.
          </p>
        </div>

        {cart.length > 0 && (
          <button
            onClick={clearCart}
            className="text-xs text-zinc-400 hover:text-rose-400 transition-colors flex items-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Vaciar Carrito</span>
          </button>
        )}
      </div>

      {cart.length === 0 ? (
        /* Empty Cart State */
        <div className="bg-[#0e111a] border border-[#1b2030] rounded-3xl p-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-zinc-800/80 text-zinc-500 flex items-center justify-center mx-auto mb-3">
            <ShoppingCart className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-white mb-1">Tu carrito de producción está vacío</h3>
          <p className="text-xs text-zinc-400 max-w-sm mx-auto mb-5">
            Aún no has agregado ninguna instrumental, loop o acapella a tu pedido.
          </p>
          <button
            onClick={onNavigateCatalog}
            className="bg-amber-400 hover:bg-amber-300 text-zinc-950 font-black px-5 py-2.5 rounded-xl text-xs transition-transform hover:scale-102 shadow-sm"
          >
            Explorar Catálogo de Audio
          </button>
        </div>
      ) : (
        /* Items & Summary Grid */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Cart Items List */}
          <div className="lg:col-span-2 space-y-3">
            {cart.map((item) => {
              const badge = getResourceBadgeInfo(item.track.resourceType);

              return (
                <div
                  key={item.track.id}
                  className="bg-[#0e111a] border border-[#1b2030] rounded-2xl p-3.5 flex items-center justify-between gap-4 group hover:border-amber-400/30 transition-all shadow-sm"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <img
                      src={item.track.coverUrl}
                      alt={item.track.title}
                      className="w-14 h-14 rounded-xl object-cover flex-shrink-0 cursor-pointer"
                      onClick={() => onOpenTrackDetail(item.track.id)}
                    />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[9px] font-mono font-bold uppercase px-1.5 py-0.2 rounded border ${badge.badgeClass}`}
                        >
                          {badge.label}
                        </span>
                        <span className="text-[11px] font-mono text-zinc-400">
                          {item.track.bpm} BPM · {item.track.scaleKey}
                        </span>
                      </div>
                      <h4
                        onClick={() => onOpenTrackDetail(item.track.id)}
                        className="font-bold text-white text-sm hover:text-amber-400 cursor-pointer truncate mt-0.5 transition-colors"
                      >
                        {item.track.title}
                      </h4>
                      <p className="text-[11px] text-zinc-400 truncate">
                        Productor: <span className="text-zinc-200">{item.track.producerName}</span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 flex-shrink-0">
                    <div className="text-right font-mono">
                      <span className="text-sm font-black text-amber-400 block">
                        ${item.track.price.toLocaleString('es-CL')} CLP
                      </span>
                      <span className="text-[9px] text-zinc-500 uppercase">Licencia Comercial</span>
                    </div>

                    <button
                      onClick={() => removeFromCart(item.track.id)}
                      className="p-1.5 text-zinc-500 hover:text-rose-400 transition-colors rounded-lg hover:bg-zinc-800"
                      title="Eliminar del carrito"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Checkout Breakdown */}
          <div>
            <div className="bg-[#0e111a] border border-[#1b2030] rounded-3xl p-5 sticky top-24 shadow-xl space-y-4">
              <h3 className="text-xs font-mono font-bold text-zinc-400 uppercase tracking-wider">
                Resumen de Facturación
              </h3>

              <div className="space-y-2.5 text-xs text-zinc-300 pb-3 border-b border-[#1b2030] font-mono">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Subtotal ({cart.length} productos):</span>
                  <span className="font-semibold text-white">${subtotal.toLocaleString('es-CL')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">IVA (19%):</span>
                  <span className="font-semibold text-white">${iva.toLocaleString('es-CL')}</span>
                </div>
              </div>

              <div className="flex justify-between items-baseline font-mono">
                <span className="text-xs font-bold text-zinc-400 uppercase">Total Final:</span>
                <span className="text-xl font-black text-amber-400">
                  ${total.toLocaleString('es-CL')} CLP
                </span>
              </div>

              <button
                onClick={handleStartCheckout}
                disabled={isProcessing || total <= 0}
                className="w-full bg-amber-400 hover:bg-amber-300 disabled:opacity-50 disabled:cursor-not-allowed text-zinc-950 font-black py-3 px-4 rounded-xl text-xs transition-all hover:scale-102 flex items-center justify-center gap-2 shadow-sm font-mono uppercase"
              >
                <span>{isProcessing ? 'Conectando con Webpay...' : 'Continuar a Webpay'}</span>
                {!isProcessing && <ArrowRight className="w-3.5 h-3.5" />}
              </button>

              {total <= 0 && (
                <p role="status" className="text-xs text-amber-300">
                  El checkout Webpay no admite un total de $0.
                </p>
              )}
              {checkoutError && (
                <p role="alert" className="text-xs text-rose-400">
                  {checkoutError}
                </p>
              )}
              {checkoutNotice && (
                <p role="status" className="text-xs text-zinc-400">
                  {checkoutNotice}
                </p>
              )}

              <div className="flex items-center justify-center gap-1.5 text-[10px] text-zinc-500 font-mono">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>La aprobación se valida en el retorno de Django</span>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
