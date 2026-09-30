import path from 'node:path'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    // 127.0.0.1, not localhost: Box login redirects to 127.0.0.1, and the
    // session cookie only reaches the app if both use the same host.
    host: '127.0.0.1',
    // Same-origin API in dev, matching the /api rewrite in render.yaml.
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
