import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts', './tests/integration-setup.ts'],
    testMatch: ['**/tests/integration/**/*.test.ts'],
    testTimeout: 30000, // 30 seconds for integration tests
  },
  resolve: {
    alias: {
      '@player': path.resolve(__dirname, './src/player'),
      '@shell': path.resolve(__dirname, './src/shell'),
      '@shared': path.resolve(__dirname, './src/shared'),
    },
  },
});
