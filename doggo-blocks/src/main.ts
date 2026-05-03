import type { ChildProcess } from 'child_process';
import { spawn } from 'child_process';
import { mkdtempSync, writeFileSync } from 'fs';
import { tmpdir } from 'os';
import path from 'path';

import { BrowserWindow, Menu, app, ipcMain } from 'electron';

let mainWindow: BrowserWindow | null = null;
let runningProcess: ChildProcess | null = null;

const createWindow = (): void => {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      devTools: !app.isPackaged,
    },
  });

  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`));
  }
}

app.whenReady().then(() => {
  const isMac = process.platform === 'darwin';
  Menu.setApplicationMenu(
    Menu.buildFromTemplate([
      ...(isMac
        ? [
            {
              label: app.name,
              submenu: [
                { role: 'about' as const },
                { type: 'separator' as const },
                { role: 'hide' as const },
                { role: 'hideOthers' as const },
                { role: 'unhide' as const },
                { type: 'separator' as const },
                { role: 'quit' as const },
              ],
            },
          ]
        : []),
      {
        label: 'View',
        submenu: [
          ...(!app.isPackaged
            ? [
                { role: 'reload' as const },
                { role: 'forceReload' as const },
                { role: 'toggleDevTools' as const },
                { type: 'separator' as const },
              ]
            : []),
          { role: 'resetZoom' as const },
          { role: 'zoomIn' as const },
          { role: 'zoomOut' as const },
          { type: 'separator' as const },
          { role: 'togglefullscreen' as const },
        ],
      },
      { role: 'windowMenu' as const },
      {
        role: 'help' as const,
        submenu: [{ role: 'about' as const }],
      },
    ]),
  );
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

ipcMain.handle('run-script', (_event, code: string) => {
  if (runningProcess) {
    return;
  }

  const tmpDir = mkdtempSync(path.join(tmpdir(), 'doggo-'));
  const scriptPath = path.join(tmpDir, 'script.py');
  writeFileSync(scriptPath, code, 'utf8');

  const proxyPath = app.isPackaged
    ? path.join(process.resourcesPath, 'webrepl_proxy.py')
    : path.join(app.getAppPath(), '..', 'webrepl_proxy.py');
  const proc = spawn('python', [proxyPath, 'run', scriptPath]);
  runningProcess = proc;

  proc.stdout?.on('data', (data: Buffer) => {
    mainWindow?.webContents.send('script-output', data.toString());
  });

  proc.stderr?.on('data', (data: Buffer) => {
    console.error('[doggo]', data.toString());
  });

  proc.on('close', (exitCode: number | null) => {
    runningProcess = null;
    mainWindow?.webContents.send('script-done', exitCode);
  });
});
