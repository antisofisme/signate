import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: true, // Allow network access
    watch: {
      usePolling: true, // Enable polling for WSL/Windows
      interval: 100, // Check for changes every 100ms
    },
    hmr: {
      overlay: true, // Show error overlay
    },
    proxy: {
      '/api': {
        target: 'http://192.168.5.12:8001',
        changeOrigin: true,
      },
    },
  },
})
