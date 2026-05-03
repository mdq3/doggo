import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    lib: {
      entry: './src/main.ts',
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
