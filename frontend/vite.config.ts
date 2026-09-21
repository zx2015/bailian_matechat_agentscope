import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// Build output is copied by `make frontend-build` into
// src/bailian_rag_demo/static/ so it ships inside the wheel and is served by
// FastAPI (see src/bailian_rag_demo/app/api.py) at the app root "/".
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
      // FastAPI backend started via `make dev` (127.0.0.1:8000).
      '/process': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
});
