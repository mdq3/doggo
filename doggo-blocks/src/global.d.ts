// Allow Vite-handled CSS imports in TypeScript.
declare module '*.css';

// Globals injected by @electron-forge/plugin-vite into the main process bundle.
declare const MAIN_WINDOW_VITE_DEV_SERVER_URL: string | undefined;
declare const MAIN_WINDOW_VITE_NAME: string;

// contextBridge API exposed by preload.ts.
interface Window {
  doggo: {
    runScript: (code: string) => Promise<void>;
    stopScript: () => Promise<void>;
    onOutput: (cb: (line: string) => void) => void;
    onDone: (cb: (exitCode: number | null) => void) => void;
  };
}
