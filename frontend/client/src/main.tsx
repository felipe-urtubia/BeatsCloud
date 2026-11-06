import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import { AppProvider } from './context/AppContext';
import { AccountActivationPage } from './components/AccountActivationPage';
import { PasswordResetPage } from './components/PasswordResetPage';
import './index.css';

const activationMatch = window.location.pathname.match(/^\/activar\/([^/]+)\/([^/]+)\/?$/);
const passwordResetMatch = window.location.pathname.match(/^\/restablecer\/([^/]+)\/([^/]+)\/?$/);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {activationMatch ? (
      <AccountActivationPage
        uidb64={activationMatch[1]}
        token={activationMatch[2]}
      />
    ) : passwordResetMatch ? (
      <PasswordResetPage uidb64={passwordResetMatch[1]} token={passwordResetMatch[2]} />
    ) : (
      <AppProvider>
        <App />
      </AppProvider>
    )}
  </React.StrictMode>
);
