import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['localhost', '.verienv.com'],
    proxy: {
      '/api': {
        target: 'http://localhost:12054',
        changeOrigin: true,
      },
    },
  },
  preview: {
    allowedHosts: ['localhost', '.verienv.com'],
  },
})
