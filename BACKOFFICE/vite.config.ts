import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Build servido pelo backend na porta da consola (http://127.0.0.1:8300/).
// npm run dev (5174) envia /api para o backend.
export default defineConfig({
  plugins: [react()],
  server: { port: 5174, proxy: { '/api': 'http://127.0.0.1:8300' } },
  build: { outDir: 'dist', emptyOutDir: true, chunkSizeWarningLimit: 900 },
})
