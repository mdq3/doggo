import { MakerZIP } from '@electron-forge/maker-zip';
import { VitePlugin } from '@electron-forge/plugin-vite';

export default {
  packagerConfig: { asar: false, extraResource: ['../webrepl_proxy.py'], icon: 'assets/icon' },
  rebuildConfig: {},
  makers: [new MakerZIP({}, ['darwin', 'linux', 'win32'])],
  plugins: [
    new VitePlugin({
      build: [
        { entry: 'src/main/main.ts', config: 'vite.main.config.mjs', target: 'main' },
        { entry: 'src/preload/preload.ts', config: 'vite.preload.config.mjs', target: 'preload' },
      ],
      renderer: [
        { name: 'main_window', config: 'vite.renderer.config.mjs' },
      ],
    }),
  ],
};
