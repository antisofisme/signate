import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    // Proxy API requests to backend (if backend is accessible)
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
        // Log proxy requests for debugging
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('[Vite Proxy] Backend connection error:', err.message)
            console.log('[Vite Proxy] Please check backend URL in .env file')
          })
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            console.log('[Vite Proxy] Forwarding:', req.method, req.url)
          })
        }
      }
    }
  }
})
