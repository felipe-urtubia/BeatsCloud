import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  const djangoTarget = env.VITE_DJANGO_PROXY_TARGET || 'http://127.0.0.1:8000';

  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: '0.0.0.0',
      port: 3000,
      proxy: {
        '/api': {
          target: djangoTarget,
          changeOrigin: true,
          secure: false,
        },
        '/media': {
          target: djangoTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  };
});
