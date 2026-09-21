import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// Build output is copied by `make frontend-build` into
// src/bailian_rag_demo/static/ so it ships inside the wheel and is served by
// FastAPI (see src/bailian_rag_demo/app/api.py) at the app root "/".
const backendTarget = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [vue()],
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      // Local dev convenience: `npm run dev` proxies API calls to the
      // FastAPI backend. Override the port with `VITE_BACKEND_URL`, e.g.
      // `VITE_BACKEND_URL=http://127.0.0.1:8500 npm run dev`.
      '/process': backendTarget,
      '/health': backendTarget,
    },
  },
});

