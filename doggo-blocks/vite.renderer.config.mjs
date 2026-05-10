import { cpSync, readFileSync } from 'fs';
import { extname, join } from 'path';

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const SKIP = (src) => /\.(mp3|ogg|wav)$/.test(src) || src.includes('/extensions/');

function scratchBlocksMedia() {
  const mediaDir = join(process.cwd(), 'node_modules/scratch-blocks/media');
  const mimeTypes = {
    svg: 'image/svg+xml',
    png: 'image/png',
    gif: 'image/gif',
    cur: 'image/vnd.microsoft.icon',
  };
  let outDir;
  return {
    name: 'scratch-blocks-media',
    configResolved(config) {
      outDir = config.build.outDir;
    },
    configureServer(server) {
      server.middlewares.use('/media', (req, res, next) => {
        try {
          const data = readFileSync(join(mediaDir, req.url || '/'));
          res.setHeader('Content-Type', mimeTypes[extname(req.url).slice(1)] ?? 'application/octet-stream');
          res.end(data);
        } catch {
          next();
        }
      });
    },
    closeBundle() {
      cpSync(mediaDir, join(outDir, 'media'), { recursive: true, filter: (src) => !SKIP(src) });
    },
  };
}

export default defineConfig({
  plugins: [react(), scratchBlocksMedia()],
  optimizeDeps: {
    include: ['scratch-blocks'],
  },
  assetsInclude: ['**/*.wasm'],
  server: {
    fs: { allow: ['..'] },
  },
});
