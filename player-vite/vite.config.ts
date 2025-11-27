import { defineConfig, Plugin } from 'vite';
import path from 'path';
import fs from 'fs';

/**
 * Plugin to generate version.json on build
 * This allows the player to detect when a new build is deployed
 */
function versionPlugin(): Plugin {
  return {
    name: 'version-plugin',
    closeBundle() {
      const now = new Date();
      const versionInfo = {
        buildTime: now.toISOString(),
        buildTimestamp: now.getTime(),
        buildDate: now.toLocaleDateString('id-ID'),
        buildTimeLocal: now.toLocaleTimeString('id-ID'),
      };

      const outputPath = path.resolve(__dirname, 'dist/version.json');
      fs.writeFileSync(outputPath, JSON.stringify(versionInfo, null, 2));
      console.log(`\n[version-plugin] Generated version.json: ${versionInfo.buildTime}\n`);
    },
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  // Plugins
  plugins: [versionPlugin()],
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
        // Remove console.log and console.debug in production (~15 KB savings)
        // Keep console.warn and console.error for critical diagnostics
        drop_console: false, // Don't drop all console
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.debug', 'console.info'], // Remove verbose logs
      },
      format: {
        comments: false, // Remove comments in production
      },
    },

    // Chunk size warnings
    chunkSizeWarningLimit: 500,

    // Rollup options
    rollupOptions: {
      output: {
        // Add hash to filenames for cache busting
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',

        // Manual chunks for better caching
        manualChunks: {
          'vendor': ['video.js'],
        },
      },
    },
  },

  // Development server
  server: {
    port: 5174, // Changed from 8080 (conflict with viewer)
    host: true, // Listen on all addresses (0.0.0.0)
    strictPort: false, // Allow fallback to next available port

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
    include: ['video.js'],
  },
});
