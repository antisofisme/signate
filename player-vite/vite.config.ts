import { defineConfig } from 'vite';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  // Path aliases (match tsconfig.json)
  resolve: {
    alias: {
      '@shared': path.resolve(__dirname, './src/shared'),
      '@shell': path.resolve(__dirname, './src/shell'),
      '@player': path.resolve(__dirname, './src/player'),
    },
  },

  // Build configuration
  build: {
    // Output directory
    outDir: 'dist',

    // Generate sourcemaps for debugging
    sourcemap: true,

    // Target ES2015 for WebOS TV compatibility
    target: 'es2015',

    // Minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: false, // Keep console logs for debugging
        drop_debugger: true,
      },
    },

    // Chunk size warnings
    chunkSizeWarningLimit: 500,

    // Rollup options
    rollupOptions: {
      output: {
        // Manual chunks for better caching
        manualChunks: {
          'vendor': ['hls.js'],
        },
      },
    },
  },

  // Development server
  server: {
    port: 8080,
    host: true, // Listen on all addresses (0.0.0.0)
    strictPort: true,

    // HMR configuration
    hmr: {
      overlay: true,
    },

    // Watch options (WSL2 compatibility)
    watch: {
      usePolling: true,
      interval: 1000, // Poll every 1 second (more reliable on WSL2)
      ignored: ['**/node_modules/**', '**/.git/**'],
    },

    // Proxy API requests to backend
    proxy: {
      '/api': {
        target: 'http://192.168.5.12:8001',
        changeOrigin: true,
        secure: false,
      },
    },
  },

  // Preview server (after build)
  preview: {
    port: 8080,
    host: true,
    strictPort: true,
  },

  // Environment variables prefix
  envPrefix: 'VITE_',

  // Optimize dependencies
  optimizeDeps: {
    include: ['hls.js'],
  },
});
