import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { getResourceBadgeInfo } from '../utils/resourceHelpers';
import {
  ShoppingCart,
  Trash2,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  CreditCard,
  Lock,
  Disc3,
  FileText,
} from 'lucide-react';
import { LicenseCertificateModal } from './LicenseCertificateModal';
import { LicenseContract } from '../types';

interface CartPageProps {
  onNavigateCatalog: () => void;
  onOpenTrackDetail: (trackId: string) => void;
  onNavigateProfile: () => void;
}

export const CartPage: React.FC<CartPageProps> = ({
  onNavigateCatalog,
  onOpenTrackDetail,
  onNavigateProfile,
}) => {
  const { cart, removeFromCart, clearCart, checkoutCart, currentUser, purchases, getContractForPurchase } = useApp();

  const [isProcessing, setIsProcessing] = useState(false);
  const [checkoutModalOpen, setCheckoutModalOpen] = useState(false);
  const [viewingContract, setViewingContract] = useState<LicenseContract | null>(null);
  const [paymentSuccessData, setPaymentSuccessData] = useState<{
    buyOrder: string;
    amount: number;
  } | null>(null);

  // Orden de compra FIJA al abrir la pasarela (espejo de WebpayTransaction:
  // el buy_order se genera una vez en create() y se reutiliza hasta el commit).
  const [pendingBuyOrder, setPendingBuyOrder] = useState<string>('');

  const subtotal = cart.reduce((sum, item) => sum + item.track.price, 0);
  const iva = Math.round(subtotal * 0.19);
  const total = subtotal + iva;

  const handleStartCheckout = () => {
    setPendingBuyOrder('BC-' + Math.floor(100000 + Math.random() * 900000));
    setCheckoutModalOpen(true);
  };

  const handleConfirmWebpayPayment = () => {
    setIsProcessing(true);
    setTimeout(() => {
      const result = checkoutCart(pendingBuyOrder || undefined);
      setIsProcessing(false);
      if (result.success) {
        setPaymentSuccessData({
          buyOrder: result.buyOrder,
          amount: result.amount,
        });
        setPendingBuyOrder('');
      }
    }, 1500);
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
            Módulo de Checkout preparado para Webpay Plus (Transbank).
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

      {paymentSuccessData ? (
        /* Success Receipt Screen */
        <div className="bg-[#0e111a] border border-emerald-500/40 rounded-3xl p-8 sm:p-10 text-center shadow-2xl animate-in zoom-in-95 duration-200">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <span className="text-[10px] font-mono font-black uppercase tracking-widest text-emerald-400 bg-emerald-950/80 px-2.5 py-1 rounded-md border border-emerald-500/30">
            Transacción Autorizada
          </span>

          <h2 className="text-2xl font-black text-white mt-3 mb-1">
            ¡Pago Realizado con Éxito!
          </h2>
          <p className="text-xs text-zinc-300 max-w-md mx-auto mb-6">
            Tu compra ha sido procesada correctamente a través de Webpay Plus. Las pistas y stems ya están habilitados en tu biblioteca personal.
          </p>

          <div className="bg-[#121520] rounded-2xl p-5 max-w-md mx-auto mb-6 border border-[#1f2538] text-left space-y-2.5 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-zinc-500">Orden de Compra:</span>
              <span className="text-amber-400 font-bold">{paymentSuccessData.buyOrder}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500">Monto Total Pagado:</span>
              <span className="text-white font-bold">
                ${paymentSuccessData.amount.toLocaleString('es-CL')} CLP
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500">Método de Pago:</span>
              <span className="text-zinc-300">Webpay Plus (Débito/Crédito)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500">Estado Transbank:</span>
              <span className="text-emerald-400 font-bold">AUTHORIZED (Código 0)</span>
            </div>
          </div>

          <div className="flex flex-wrap justify-center gap-3">
            <button
              onClick={() => {
                const latestPurchase =
                  purchases.find((p) => p.buyOrder === paymentSuccessData.buyOrder) || purchases[0];
                if (latestPurchase) {
                  setViewingContract(getContractForPurchase(latestPurchase));
                }
              }}
              className="bg-[#181d2c] hover:bg-[#20273a] text-amber-300 font-bold px-5 py-2.5 rounded-xl text-xs border border-amber-400/30 transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <FileText className="w-3.5 h-3.5 text-amber-400" />
              <span>Ver Certificado de Licencia Oficial</span>
            </button>
            <button
              onClick={() => {
                setPaymentSuccessData(null);
                onNavigateProfile();
              }}
              className="bg-amber-400 hover:bg-amber-300 text-zinc-950 font-black px-5 py-2.5 rounded-xl text-xs transition-colors shadow-sm"
            >
              Ir a Mi Biblioteca y Descargar Stems
            </button>
            <button
              onClick={() => {
                setPaymentSuccessData(null);
                onNavigateCatalog();
              }}
              className="bg-zinc-800 hover:bg-zinc-700 text-white font-bold px-5 py-2.5 rounded-xl text-xs border border-zinc-700 transition-colors"
            >
              Seguir explorando el Catálogo
            </button>
          </div>
        </div>
      ) : cart.length === 0 ? (
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
                className="w-full bg-amber-400 hover:bg-amber-300 text-zinc-950 font-black py-3 px-4 rounded-xl text-xs transition-all hover:scale-102 flex items-center justify-center gap-2 shadow-sm font-mono uppercase"
              >
                <span>{total === 0 ? 'Confirmar Descargas Gratuitas' : 'Proceder al Pago con Webpay'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              <div className="flex items-center justify-center gap-1.5 text-[10px] text-zinc-500 font-mono">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Transacción cifrada Transbank Webpay</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Webpay Checkout Simulation Modal */}
      {checkoutModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-150">
          <div className="w-full max-w-md bg-[#0e111a] border border-[#232a40] rounded-3xl p-6 sm:p-7 shadow-2xl relative">
            <div className="flex items-center justify-between pb-3.5 border-b border-[#1b2030]">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-red-600 text-white font-black flex items-center justify-center text-[10px] font-mono">
                  TBK
                </div>
                <div>
                  <h4 className="text-xs font-black text-white leading-tight font-mono">
                    Webpay Plus
                  </h4>
                  <span className="text-[10px] text-zinc-400">Pasarela Oficial de Pagos</span>
                </div>
              </div>
              <span className="text-xs font-mono font-bold text-amber-400">
                ${total.toLocaleString('es-CL')} CLP
              </span>
            </div>

            <div className="py-4 space-y-3">
              <div className="bg-[#121520] p-3.5 rounded-2xl border border-[#1b2030] space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Comercio:</span>
                  <span className="text-zinc-200">BeatsCloud Chile SpA</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Orden de Compra:</span>
                  <span className="text-zinc-200">{pendingBuyOrder}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Usuario Comprador:</span>
                  <span className="text-amber-400 font-bold">{currentUser?.username || 'Invitado'}</span>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[11px] font-bold text-zinc-300 block font-mono">
                  Tarjeta Bancaria Simulada:
                </label>
                <div className="flex items-center gap-2.5 p-2.5 bg-zinc-900 border border-zinc-700/80 rounded-xl text-xs text-zinc-300 font-mono">
                  <CreditCard className="w-4 h-4 text-amber-400" />
                  <span>•••• •••• •••• 4242 (Redcompra / Débito)</span>
                </div>
              </div>
            </div>

            <div className="flex gap-2.5 pt-1">
              <button
                type="button"
                onClick={() => setCheckoutModalOpen(false)}
                disabled={isProcessing}
                className="flex-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-bold py-2.5 rounded-xl text-xs transition-colors"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleConfirmWebpayPayment}
                disabled={isProcessing}
                className="flex-1 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-zinc-950 font-black py-2.5 rounded-xl text-xs transition-all flex items-center justify-center gap-1.5 shadow-sm"
              >
                {isProcessing ? (
                  <span>Autorizando...</span>
                ) : (
                  <>
                    <Lock className="w-3.5 h-3.5" />
                    <span>Autorizar Pago</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Official License Certificate Modal */}
      <LicenseCertificateModal
        isOpen={Boolean(viewingContract)}
        onClose={() => setViewingContract(null)}
        contract={viewingContract}
      />
    </div>
  );
};
