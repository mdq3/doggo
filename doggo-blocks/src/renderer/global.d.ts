// Allow Vite-handled CSS and font package imports in TypeScript.
declare module '*.css';
declare module '*.wasm?url' {
  const url: string;
  export default url;
}
declare module '@fontsource-variable/sono';

// contextBridge API exposed by preload.ts.
interface Window {
  doggo: {
    runScript: (code: string) => Promise<void>;
    onOutput: (cb: (line: string) => void) => void;
    onDone: (cb: (exitCode: number | null) => void) => void;
    getSettings: () => Promise<{ hostname: string; password: string }>;
    saveSettings: (settings: { hostname: string; password: string }) => Promise<void>;
    setTitle: (filePath: string | null, isEdited: boolean) => void;
    openFile: (filePath?: string) => Promise<{ filePath: string; content: string } | null>;
    saveFile: (filePath: string | null, content: string) => Promise<string | null>;
    getRecents: () => Promise<string[]>;
    addRecent: (filePath: string) => Promise<void>;
    clearRecents: () => Promise<void>;
    onMenuNewFile: (cb: () => void) => void;
    onMenuOpenFile: (cb: () => void) => void;
    onMenuSaveFile: (cb: () => void) => void;
    onMenuSaveFileAs: (cb: () => void) => void;
    onMenuOpenRecent: (cb: (filePath: string) => void) => void;
  };
}
