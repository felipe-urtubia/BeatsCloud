import { DjangoApi } from '../api/django.service';
import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { getResourceBadgeInfo } from '../utils/resourceHelpers';
import {
  ShoppingCart,
  Trash2,
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
  const { cart, removeFromCart, clearCart, checkoutCart, configuredMode, currentUser } = useApp();

  const [isProcessing, setIsProcessing] = useState(false);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);
  const [checkoutNotice, setCheckoutNotice] = useState<string | null>(null);
  const [showCheckoutConfirm, setShowCheckoutConfirm] = useState(false);

  const [serverTotals, setServerTotals] = useState<{
    key: string;
    subtotal: number;
    iva: number;
    total: number;
  } | null>(null);

  const [totalsIssue, setTotalsIssue] = useState<string | null>(null);
  const [totalsRetry, setTotalsRetry] = useState(0);

  const cartIds = cart.map((item) => item.track.id).sort().join('|');
  const cartKey = `${currentUser?.id ?? ''}:${cartIds}`;

  const verifiedTotals =
    serverTotals?.key === cartKey ? serverTotals : null;

  const pendingTotals =
    configuredMode === 'hybrid' &&
    cart.length > 0 &&
    !verifiedTotals;

  useEffect(() => {
    if (configuredMode !== 'hybrid' || cart.length === 0) {
      setServerTotals(null);
      setTotalsIssue(null);
      return;
    }

    let active = true;

    setTotalsIssue(null);

    void DjangoApi.carrito()
      .then((response) => {
        if (!active) return;

        const remoteIds = response.items
          .map((item) => `dj-${item.track}`)
          .sort()
          .join('|');

        if (remoteIds !== cartIds) {
          setTotalsIssue(
            'El carrito del servidor cambi?. Actualiza los totales antes de pagar.'
          );
          return;
        }

        const values = [
          response.subtotal,
          response.iva,
          response.total,
        ];

        if (
          values.some((value) =>
            !Number.isSafeInteger(value) || value < 0
          ) ||
          response.subtotal + response.iva !== response.total
        ) {
          throw new Error('Django devolvi? totales no v?lidos.');
        }

        setServerTotals({
          key: cartKey,
          subtotal: response.subtotal,
          iva: response.iva,
          total: response.total,
        });

        setTotalsIssue(null);
      })
      .catch((error) => {
        if (!active) return;

        setTotalsIssue(
          error instanceof Error
            ? error.message
            : 'No fue posible consultar los totales del servidor.'
        );
      });

    return () => {
      active = false;
    };
  }, [configuredMode, cartKey, totalsRetry]);

  // En modo hybrid, Django es la ?nica fuente de los totales.
  // El c?lculo local se conserva exclusivamente para el modo de demostraci?n.
  const demoSubtotal = configuredMode !== 'hybrid'
    ? cart.reduce((sum, item) => sum + item.track.price, 0)
    : 0;

  const subtotal = configuredMode === 'hybrid'
    ? verifiedTotals?.subtotal ?? 0
    : demoSubtotal;

  const iva = configuredMode === 'hybrid'
    ? verifiedTotals?.iva ?? 0
    : Math.round(demoSubtotal * 0.19);

  const total = subtotal + iva;

  const formatCartAmount = (amount: number) =>
    pendingTotals ? '?' : amount.toLocaleString('es-CL');

  const openCheckoutConfirm = () => {
    if (isProcessing) return;

    if (configuredMode === 'hybrid' && !verifiedTotals) {
      setTotalsIssue(
        'Debes verificar los totales de Django antes de continuar.'
      );
      return;
    }
    setCheckoutError(null);
    setCheckoutNotice(null);

    if (cart.length === 0 || total <= 0) {
      setCheckoutError('El carrito no tiene productos de pago.');
      return;
    }

    setShowCheckoutConfirm(true);
  };

  useEffect(() => {
    if (!showCheckoutConfirm || isProcessing) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowCheckoutConfirm(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [showCheckoutConfirm, isProcessing]);

  useEffect(() => {
    if (cart.length === 0) {
      setShowCheckoutConfirm(false);
    }
  }, [cart.length]);

  const handleStartCheckout = async () => {
    if (isProcessing) return;

    if (configuredMode === 'hybrid' && !verifiedTotals) {
      setCheckoutError(
        'Los totales del servidor ya no est?n verificados.'
      );
      return;
    }
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

      {pendingTotals && (
        <div
          role="status"
          className="rounded-xl border border-amber-400/30 bg-zinc-900 p-4 text-sm text-zinc-300"
        >
          <p>
            {totalsIssue ??
              'Verificando subtotal, IVA y total oficiales con Django...'}
          </p>
          <button
            type="button"
            className="mt-2 text-amber-400 font-bold hover:underline"
            onClick={() => setTotalsRetry((value) => value + 1)}
          >
            Actualizar totales
          </button>
        </div>
      )}

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
                  <span className="font-semibold text-white">${formatCartAmount(subtotal)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">IVA (19%):</span>
                  <span className="font-semibold text-white">${formatCartAmount(iva)}</span>
                </div>
              </div>

              <div className="flex justify-between items-baseline font-mono">
                <span className="text-xs font-bold text-zinc-400 uppercase">Total Final:</span>
                <span className="text-xl font-black text-amber-400">
                  ${formatCartAmount(total)} CLP
                </span>
              </div>

              <button
                onClick={openCheckoutConfirm}
                disabled={isProcessing || total <= 0}
                className="w-full bg-amber-400 hover:bg-amber-300 disabled:opacity-50 disabled:cursor-not-allowed text-zinc-950 font-black py-3 px-4 rounded-xl text-xs transition-all hover:scale-102 flex items-center justify-center gap-2 shadow-sm font-mono uppercase"
              >
                <span>{isProcessing ? 'Conectando con Webpay...' : 'Revisar compra'}</span>
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

            </div>
          </div>
        </div>
      )}

      {showCheckoutConfirm && cart.length > 0 && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="checkout-confirm-title"
            className="w-full max-w-lg max-h-[90vh] overflow-y-auto bg-[#111520] border border-[#2d3546] rounded-3xl p-6 shadow-2xl space-y-5"
          >
            <div>
              <h2
                id="checkout-confirm-title"
                className="text-xl font-black text-white"
              >
                Confirmar compra
              </h2>
              <p className="text-xs text-zinc-400 mt-2">
                Revisa tu pedido antes de continuar a Webpay.
              </p>
            </div>

            <div className="space-y-2 max-h-52 overflow-y-auto">
              {cart.map((item) => (
                <div
                  key={item.track.id}
                  className="flex justify-between gap-4 rounded-xl bg-zinc-900 p-3"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-white truncate">
                      {item.track.title}
                    </p>
                    <p className="text-xs text-zinc-400 truncate">
                      {item.track.producerName}
                    </p>
                  </div>
                  <span className="text-sm font-bold text-amber-400 whitespace-nowrap">
                    ${item.track.price.toLocaleString('es-CL')}
                  </span>
                </div>
              ))}
            </div>

            <div className="border-t border-zinc-700 pt-4 space-y-2 text-sm">
              <div className="flex justify-between text-zinc-300">
                <span>Subtotal</span>
                <span>${formatCartAmount(subtotal)}</span>
              </div>
              <div className="flex justify-between text-zinc-300">
                <span>IVA (19%)</span>
                <span>${formatCartAmount(iva)}</span>
              </div>
              <div className="flex justify-between text-white font-black text-lg pt-2">
                <span>Total estimado</span>
                <span className="text-amber-400">
                  ${formatCartAmount(total)} CLP
                </span>
              </div>
            </div>

            <p className="text-xs text-zinc-400">
              Django verifica el monto definitivo al iniciar la orden.
              La compra solo se registra tras validar el pago con Webpay.
            </p>

            {checkoutError && (
              <p role="alert" className="text-xs text-rose-400">
                {checkoutError}
              </p>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                autoFocus
                disabled={isProcessing}
                onClick={() => setShowCheckoutConfirm(false)}
                className="rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white font-bold px-4 py-3 text-xs disabled:opacity-50"
              >
                Volver al carrito
              </button>

              <button
                type="button"
                disabled={isProcessing || total <= 0}
                onClick={handleStartCheckout}
                className="rounded-xl bg-amber-400 hover:bg-amber-300 text-zinc-950 font-black px-4 py-3 text-xs disabled:opacity-50"
              >
                {isProcessing ? 'Conectando...' : 'Confirmar e ir a Webpay'}
              </button>
            </div>
          </section>
        </div>
      )}

    </div>
  );
};
