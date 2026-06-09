import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true, // or '0.0.0.0'
    port: 5173,
    allowedHosts: [
      'aftermost-lustily-sprain.ngrok-free.dev',
    ],
    proxy: {
      '/api': {
        target: 'https://aftermost-lustily-sprain.ngrok-free.dev',
        changeOrigin: true,
      },
    },
  },
})