import { defineConfig } from 'vite-plus';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  assetsInclude: ['**/*.wasm'],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/vitest.setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
  },
});
