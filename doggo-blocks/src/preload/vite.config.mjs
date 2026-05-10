import { fileURLToPath } from 'url';

import { defineConfig } from 'vite-plus';

export default defineConfig({
  root: fileURLToPath(new URL('../../', import.meta.url)),
  build: {
    lib: {
      entry: './src/preload/preload.ts',
      formats: ['cjs'],
      fileName: () => 'preload.js',
    },
    rollupOptions: {
      external: ['electron'],
    },
    outDir: '.vite/build',
    emptyOutDir: false,
  },
});
