import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: parseInt(env.VITE_PORT || '3000'),  // From .env
      host: true, // Bind to all network interfaces
      // HMR configuration for better hot reload
      hmr: {
        overlay: true, // Show errors in overlay
      },
      // Watch configuration for WSL environment
      watch: {
        usePolling: true, // Enable polling for WSL file system
        interval: 100, // Check every 100ms
      },
      proxy: {
        // Proxy API requests to backend during development
        '/api': {
          target: env.VITE_PROXY_TARGET || 'http://192.168.5.12:8001',  // From .env
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      minify: 'esbuild',
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'query-vendor': ['@tanstack/react-query'],
            // Note: lucide-react removed from manual chunks to enable tree-shaking
            // Icons are imported individually throughout the app
            'ui-vendor': ['clsx', 'tailwind-merge'],
          },
        },
      },
      // Optimize chunk size
      chunkSizeWarningLimit: 500,
    },
  }
})
