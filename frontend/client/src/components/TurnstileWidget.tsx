import { useEffect, useRef, useState } from 'react';

interface TurnstileApi {
  render: (
    container: HTMLElement,
    options: {
      sitekey: string;
      theme: 'dark';
      callback: (token: string) => void;
      'expired-callback': () => void;
      'error-callback': () => void;
      'timeout-callback': () => void;
    },
  ) => string;
  reset: (widgetId: string) => void;
  remove: (widgetId: string) => void;
}

declare global {
  interface Window {
    turnstile?: TurnstileApi;
  }
}

interface Props {
  siteKey: string;
  onTokenChange: (token: string) => void;
  resetKey: number;
}

const SCRIPT_URL =
  'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';

export function TurnstileWidget({
  siteKey,
  onTokenChange,
  resetKey,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetRef = useRef<string | null>(null);
  const callbackRef = useRef(onTokenChange);
  const [message, setMessage] = useState('');

  useEffect(() => {
    callbackRef.current = onTokenChange;
  }, [onTokenChange]);

  useEffect(() => {
    let disposed = false;

    const clearToken = (errorMessage: string) => {
      if (!disposed) {
        callbackRef.current('');
        setMessage(errorMessage);
      }
    };

    const renderWidget = () => {
      if (
        disposed ||
        !containerRef.current ||
        !window.turnstile ||
        widgetRef.current
      ) {
        return;
      }

      try {
        widgetRef.current = window.turnstile.render(
          containerRef.current,
          {
            sitekey: siteKey,
            theme: 'dark',
            callback: (token) => {
              if (!disposed) {
                setMessage('');
                callbackRef.current(token);
              }
            },
            'expired-callback': () => {
              clearToken('La verificaci?n caduc?. Intenta nuevamente.');
            },
            'error-callback': () => {
              clearToken('No se pudo completar la verificaci?n.');
            },
            'timeout-callback': () => {
              clearToken('La verificaci?n agot? el tiempo disponible.');
            },
          },
        );
      } catch {
        clearToken('No se pudo iniciar la verificaci?n.');
      }
    };

    const scriptError = () => {
      clearToken('No se pudo cargar la verificaci?n de seguridad.');
    };

    let script = document.querySelector<HTMLScriptElement>(
      'script[data-beatcloud-turnstile]',
    );

    if (window.turnstile) {
      renderWidget();
    } else {
      const isNew = !script;

      if (!script) {
        script = document.createElement('script');
        script.dataset.beatcloudTurnstile = 'true';
        script.src = SCRIPT_URL;
        script.async = true;
      }

      script.addEventListener('load', renderWidget);
      script.addEventListener('error', scriptError);

      if (isNew) {
        document.head.appendChild(script);
      }
    }

    return () => {
      disposed = true;
      script?.removeEventListener('load', renderWidget);
      script?.removeEventListener('error', scriptError);

      if (widgetRef.current) {
        window.turnstile?.remove(widgetRef.current);
        widgetRef.current = null;
      }
    };
  }, [siteKey]);

  useEffect(() => {
    if (resetKey === 0 || !widgetRef.current) return;

    callbackRef.current('');
    setMessage('');
    window.turnstile?.reset(widgetRef.current);
  }, [resetKey]);

  return (
    <div className="my-3">
      <div ref={containerRef} />
      {message && (
        <p className="mt-2 text-xs text-rose-400" role="alert">
          {message}
        </p>
      )}
    </div>
  );
}
