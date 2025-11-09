#!/usr/bin/env node

/**
 * Development Watch Script
 * Auto-restarts Vite dev server when files change (WSL2 workaround)
 *
 * Uses chokidar with polling for cross-filesystem compatibility
 *
 * Usage: npm run dev:watch
 */

import { spawn } from 'child_process';
import chokidar from 'chokidar';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

let viteProcess = null;
let restartTimeout = null;

const startVite = () => {
  if (viteProcess) {
    viteProcess.kill();
  }

  console.log('\n🚀 Starting Vite dev server...\n');

  viteProcess = spawn('npx', ['vite'], {
    cwd: __dirname,
    stdio: 'inherit',
    shell: true,
  });

  viteProcess.on('error', (err) => {
    console.error('❌ Failed to start Vite:', err);
  });
};

const restartVite = (filename) => {
  // Debounce restarts (wait 500ms after last change)
  if (restartTimeout) {
    clearTimeout(restartTimeout);
  }

  restartTimeout = setTimeout(() => {
    console.log('\n🔄 File changed, restarting Vite...\n');
    startVite();
  }, 500);
};

// Watch src directory for changes with polling (WSL2 compatible)
const srcPath = resolve(__dirname, 'src');
console.log('👀 Watching for changes in:', srcPath);
console.log('⚡ Using polling mode for WSL2 compatibility\n');

const watcher = chokidar.watch('src/**/*.{ts,tsx,css}', {
  ignored: ['**/node_modules/**', '**/.git/**', '**/*.js', '**/*.js.map'],
  persistent: true,
  usePolling: true,      // Enable polling for WSL2
  interval: 1000,        // Poll every 1 second
  binaryInterval: 3000,  // Poll binary files every 3 seconds
  awaitWriteFinish: {
    stabilityThreshold: 500,
    pollInterval: 100,
  },
});

watcher
  .on('ready', () => {
    console.log('✅ Watcher ready, starting Vite...\n');
    startVite();
  })
  .on('change', (path) => {
    console.log(`📝 Changed: ${path}`);
    restartVite(path);
  })
  .on('add', (path) => {
    console.log(`➕ Added: ${path}`);
    restartVite(path);
  })
  .on('unlink', (path) => {
    console.log(`🗑️  Removed: ${path}`);
    restartVite(path);
  })
  .on('error', (error) => {
    console.error('❌ Watcher error:', error);
  });

// Cleanup on exit
process.on('SIGINT', () => {
  console.log('\n👋 Shutting down...');
  watcher.close();
  if (viteProcess) {
    viteProcess.kill();
  }
  process.exit(0);
});

process.on('SIGTERM', () => {
  watcher.close();
  if (viteProcess) {
    viteProcess.kill();
  }
  process.exit(0);
});
