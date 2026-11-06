/**
 * Begin the real Webpay redirect. This reports only that Webpay was opened;
 * approval is validated later by Django and is never inferred here.
 * @param {() => Promise<{url_webpay?: unknown, token_ws?: unknown}>} initialize
 * @param {(url: string, token: string) => void} submit
 * @returns {Promise<{status: 'redirecting'} | {status: 'error', message: string}>}
 */
export async function startWebpayCheckout(initialize, submit) {
  try {
    const response = await initialize();
    if (typeof response?.url_webpay !== 'string' || !response.url_webpay ||
        typeof response?.token_ws !== 'string' || !response.token_ws) {
      return {
        status: 'error',
        message: 'Django no devolvió los datos necesarios para abrir Webpay.',
      };
    }

    submit(response.url_webpay, response.token_ws);
    return { status: 'redirecting' };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'No fue posible iniciar el pago Webpay.',
    };
  }
}

/** Submit the token returned by Django to Transbank using its required POST form. */
export function submitWebpayForm(url, token) {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = url;
  form.hidden = true;

  const input = document.createElement('input');
  input.type = 'hidden';
  input.name = 'token_ws';
  input.value = token;
  form.appendChild(input);

  document.body.appendChild(form);
  form.submit();
}
