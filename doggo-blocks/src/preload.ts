import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('doggo', {
  runScript: (code: string) => ipcRenderer.invoke('run-script', code),
  onOutput: (cb: (line: string) => void) =>
    ipcRenderer.on('script-output', (_event, line: string) => cb(line)),
  onDone: (cb: (exitCode: number | null) => void) =>
    ipcRenderer.on('script-done', (_event, code: number | null) => cb(code)),
  getSettings: (): Promise<{ hostname: string; password: string }> =>
    ipcRenderer.invoke('get-settings'),
  saveSettings: (settings: { hostname: string; password: string }): Promise<void> =>
    ipcRenderer.invoke('save-settings', settings),
  openFile: (): Promise<{ filePath: string; content: string } | null> =>
    ipcRenderer.invoke('open-file'),
  saveFile: (filePath: string | null, content: string): Promise<string | null> =>
    ipcRenderer.invoke('save-file', filePath, content),
  onMenuOpenFile: (cb: () => void) => ipcRenderer.on('menu-open-file', () => cb()),
  onMenuSaveFile: (cb: () => void) => ipcRenderer.on('menu-save-file', () => cb()),
  onMenuSaveFileAs: (cb: () => void) => ipcRenderer.on('menu-save-file-as', () => cb()),
});
