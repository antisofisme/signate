import { defineConfig, Plugin } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';
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
  plugins: [
    versionPlugin(),

    // PWA Plugin for offline support
    VitePWA({
      // Use injectManifest strategy for custom SW
      strategies: 'injectManifest',
      srcDir: 'src/pwa',
      filename: 'sw.ts',

      // Registration type
      registerType: 'prompt',

      // Include scope
      scope: '/',
      base: '/',

      // Manifest configuration
      manifest: false, // We use our own manifest.json in public/

      // Development options
      devOptions: {
        enabled: true,
        type: 'module',
      },

      // InjectManifest options
      injectManifest: {
        // Files to precache
        globPatterns: [
          '**/*.{js,css,html,ico,png,svg,woff,woff2}',
        ],

        // Files to exclude from precaching
        globIgnores: [
          // HLS files - handled by IndexedDB caching
          '**/*.m3u8',
          '**/*.ts',
          // Existing HLS service worker
          'hls-service-worker.js',
          // Source maps
          '**/*.map',
          // Version file - always fetch fresh
          'version.json',
        ],

        // Maximum file size to precache (2MB)
        maximumFileSizeToCacheInBytes: 2 * 1024 * 1024,
      },
    }),
  ],
  // Path aliases (match tsconfig.json)
  resolve: {
    alias: {
      '@shared': path.resolve(__dirname, './src/shared'),
      '@shell': path.resolve(__dirname, './src/shell'),
      '@player': path.resolve(__dirname, './src/player'),
      '@pwa': path.resolve(__dirname, './src/pwa'),
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
