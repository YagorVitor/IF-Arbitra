import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { AuthProvider } from './contexts/AuthContext.jsx';
import App from './App.jsx';
import './styles/index.css';

const CHUNK_RELOAD_KEY = 'if-arbitra:chunk-reload-at';

window.addEventListener('vite:preloadError', (event) => {
  try {
    const now = Date.now();
    const previousReload = Number(sessionStorage.getItem(CHUNK_RELOAD_KEY));
    if (previousReload && now - previousReload < 30_000) return;
    sessionStorage.setItem(CHUNK_RELOAD_KEY, String(now));
  } catch {
    return;
  }

  event.preventDefault();
  window.location.reload();
});

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>
);
