import { defineConfig } from 'vite-plus';

export default defineConfig({
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
