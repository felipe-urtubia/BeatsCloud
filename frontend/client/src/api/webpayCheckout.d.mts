export interface WebpayInitializationResponse {
  url_webpay: string;
  token_ws: string;
}

export type WebpayCheckoutResult =
  | { status: 'redirecting' }
  | { status: 'error'; message: string };

export function startWebpayCheckout(
  initialize: () => Promise<WebpayInitializationResponse>,
  submit: (url: string, token: string) => void,
): Promise<WebpayCheckoutResult>;

export function submitWebpayForm(url: string, token: string): void;
