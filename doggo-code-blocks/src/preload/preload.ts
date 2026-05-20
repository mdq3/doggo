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
  openFile: (filePath?: string): Promise<{ filePath: string; content: string } | null> =>
    ipcRenderer.invoke('open-file', filePath),
  saveFile: (filePath: string | null, content: string): Promise<string | null> =>
    ipcRenderer.invoke('save-file', filePath, content),
  setTitle: (filePath: string | null, isEdited: boolean): void =>
    ipcRenderer.send('set-title', filePath, isEdited),
  getRecents: (): Promise<string[]> => ipcRenderer.invoke('get-recents'),
  addRecent: (filePath: string): Promise<void> => ipcRenderer.invoke('add-recent', filePath),
  clearRecents: (): Promise<void> => ipcRenderer.invoke('clear-recents'),
  onMenuNewFile: (cb: () => void) => ipcRenderer.on('menu-new-file', () => cb()),
  onMenuOpenFile: (cb: () => void) => ipcRenderer.on('menu-open-file', () => cb()),
  onMenuSaveFile: (cb: () => void) => ipcRenderer.on('menu-save-file', () => cb()),
  onMenuSaveFileAs: (cb: () => void) => ipcRenderer.on('menu-save-file-as', () => cb()),
  onMenuOpenRecent: (cb: (filePath: string) => void) =>
    ipcRenderer.on('menu-open-recent', (_event, filePath: string) => cb(filePath)),
  onBeforeQuit: (cb: () => void) => ipcRenderer.on('before-quit', () => cb()),
  confirmQuit: () => ipcRenderer.send('confirm-quit'),
});
