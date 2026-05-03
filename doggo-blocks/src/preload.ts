import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('doggo', {
  runScript: (code: string) => ipcRenderer.invoke('run-script', code),
  onOutput: (cb: (line: string) => void) =>
    ipcRenderer.on('script-output', (_event, line: string) => cb(line)),
  onDone: (cb: (exitCode: number | null) => void) =>
    ipcRenderer.on('script-done', (_event, code: number | null) => cb(code)),
});
