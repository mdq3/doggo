// Allow Vite-handled CSS and font package imports in TypeScript.
declare module '*.css';
declare module '@fontsource-variable/sono';

// Globals injected by @electron-forge/plugin-vite into the main process bundle.
declare const MAIN_WINDOW_VITE_DEV_SERVER_URL: string | undefined;
declare const MAIN_WINDOW_VITE_NAME: string;

// contextBridge API exposed by preload.ts.
interface Window {
  doggo: {
    runScript: (code: string) => Promise<void>;
    onOutput: (cb: (line: string) => void) => void;
    onDone: (cb: (exitCode: number | null) => void) => void;
    getSettings: () => Promise<{ hostname: string; password: string }>;
    saveSettings: (settings: { hostname: string; password: string }) => Promise<void>;
  };
}
