export type PaymentReturnInput =
  | { kind: 'approved'; order: string }
  | { kind: 'rejected' | 'cancelled' | 'abandoned' | 'failed' | 'review' | 'unverified' };

export interface WebpayReceipt {
  status: 'AUTHORIZED';
  owner_id: string;
  buy_order: string;
  amount: string;
  currency: 'CLP';
  fulfilled_at: string;
}

export interface PaymentSyncResult {
  userId: string | null;
  purchasesSynced: boolean;
  orders: string[];
}

export interface PaymentReturnResult {
  notice: string;
  receipt: WebpayReceipt | null;
  ownerId: string | null;
  ready: boolean;
}

export function readPaymentReturn(href: string): PaymentReturnInput | null;

export function cleanPaymentReturnUrl(href: string): string;

export function resolvePaymentReturn(
  input: PaymentReturnInput,
  synchronize: () => Promise<PaymentSyncResult | undefined>,
  getReceipt: (order: string) => Promise<WebpayReceipt>,
): Promise<PaymentReturnResult>;
