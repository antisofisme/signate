import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        '*.config.ts',
        'dist/',
        'build/',
      ],
      thresholds: {
        lines: 85,
        functions: 85,
        branches: 80,
        statements: 85,
      },
    },
    testMatch: ['**/tests/unit/**/*.test.ts'],
  },
  resolve: {
    alias: {
      '@player': path.resolve(__dirname, './src/player'),
      '@shell': path.resolve(__dirname, './src/shell'),
      '@shared': path.resolve(__dirname, './src/shared'),
    },
  },
});
