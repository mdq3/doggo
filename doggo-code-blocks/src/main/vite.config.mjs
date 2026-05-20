import { fileURLToPath } from 'url';

import { defineConfig } from 'vite-plus';

export default defineConfig({
  root: fileURLToPath(new URL('../../', import.meta.url)),
  build: {
    lib: {
      entry: './src/main/main.ts',
      formats: ['cjs'],
      fileName: () => 'main.js',
    },
    rollupOptions: {
      external: ['electron', 'child_process', 'path', 'fs', 'os'],
    },
    outDir: '.vite/build',
    emptyOutDir: false,
  },
});
