import type { ChildProcess } from 'child_process';
import { spawn } from 'child_process';
import { mkdtempSync, readFileSync, writeFileSync } from 'fs';
import { tmpdir } from 'os';
import path from 'path';

import { BrowserWindow, Menu, app, dialog, ipcMain } from 'electron';

let mainWindow: BrowserWindow | null = null;
let runningProcess: ChildProcess | null = null;
let allowQuit = false;

// ── Recents ──────────────────────────────────────────────────────────────────

const MAX_RECENTS = 10;

const loadRecents = (): string[] => {
  try {
    const raw = readFileSync(path.join(app.getPath('userData'), 'recents.json'), 'utf8');
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.every((v) => typeof v === 'string') ? parsed : [];
  } catch {
    return [];
  }
};

const persistRecents = (recents: string[]): void => {
  writeFileSync(
    path.join(app.getPath('userData'), 'recents.json'),
    JSON.stringify(recents),
    'utf8',
  );
};

const addToRecents = (filePath: string): void => {
  const next = [filePath, ...loadRecents().filter((p) => p !== filePath)].slice(0, MAX_RECENTS);
  persistRecents(next);
  rebuildMenu();
};

const clearRecents = (): void => {
  persistRecents([]);
  rebuildMenu();
};

interface Settings {
  hostname: string;
  password: string;
}

const DEFAULT_SETTINGS: Settings = { hostname: 'doggo.local', password: 'doggo' };

const loadSettings = (): Settings => {
  try {
    const raw = readFileSync(path.join(app.getPath('userData'), 'settings.json'), 'utf8');
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
};

const saveSettings = (settings: Settings): void => {
  writeFileSync(
    path.join(app.getPath('userData'), 'settings.json'),
    JSON.stringify(settings, null, 2),
    'utf8',
  );
};

// ── Menu ─────────────────────────────────────────────────────────────────────

const rebuildMenu = (): void => {
  const isMac = process.platform === 'darwin';
  const recents = loadRecents();
  const recentSubmenu =
    recents.length > 0
      ? [
          ...recents.map((p) => ({
            label: path.basename(p),
            click: () => mainWindow?.webContents.send('menu-open-recent', p),
          })),
          { type: 'separator' as const },
          { label: 'Clear Recents', click: clearRecents },
        ]
      : [{ label: 'No Recent Files', enabled: false }];

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
        label: 'File',
        submenu: [
          {
            label: 'New',
            accelerator: 'CmdOrCtrl+N',
            click: () => mainWindow?.webContents.send('menu-new-file'),
          },
          { type: 'separator' as const },
          {
            label: 'Open…',
            accelerator: 'CmdOrCtrl+O',
            click: () => mainWindow?.webContents.send('menu-open-file'),
          },
          { label: 'Open Recent', submenu: recentSubmenu },
          { type: 'separator' as const },
          {
            label: 'Save',
            accelerator: 'CmdOrCtrl+S',
            click: () => mainWindow?.webContents.send('menu-save-file'),
          },
          {
            label: 'Save As…',
            accelerator: 'CmdOrCtrl+Shift+S',
            click: () => mainWindow?.webContents.send('menu-save-file-as'),
          },
        ],
      },
      {
        label: 'Edit',
        submenu: [
          { role: 'cut' as const },
          { role: 'copy' as const },
          { role: 'paste' as const },
          { role: 'selectAll' as const },
        ],
      },
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
};

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
    void mainWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    void mainWindow.loadFile(
      path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`),
    );
  }

  mainWindow.on('close', (event) => {
    if (!allowQuit) {
      event.preventDefault();
      mainWindow?.webContents.send('before-quit');
    }
  });
};

void app.whenReady().then(() => {
  rebuildMenu();
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

ipcMain.handle('open-file', async (_event, filePath?: string) => {
  let targetPath = filePath;
  if (!targetPath) {
    const result = await dialog.showOpenDialog({
      filters: [{ name: 'Python', extensions: ['py'] }],
      properties: ['openFile'],
    });
    if (result.canceled || !result.filePaths.length) {
      return null;
    }
    targetPath = result.filePaths[0];
  }
  try {
    const content = readFileSync(targetPath, 'utf8');
    return { filePath: targetPath, content };
  } catch {
    return null;
  }
});

ipcMain.on('set-title', (_event, filePath: string | null, isEdited: boolean) => {
  if (!mainWindow) {
    return;
  }
  const name = filePath ? path.basename(filePath) : null;
  mainWindow.setTitle(name ? `${name} — Doggo Code Blocks` : 'Doggo Code Blocks');
  if (process.platform === 'darwin') {
    mainWindow.setRepresentedFilename(filePath ?? '');
    mainWindow.setDocumentEdited(isEdited);
  }
});

ipcMain.handle('get-recents', () => loadRecents());
ipcMain.handle('add-recent', (_event, filePath: string) => addToRecents(filePath));
ipcMain.handle('clear-recents', () => clearRecents());

ipcMain.handle('save-file', async (_event, filePath: string | null, content: string) => {
  let targetPath = filePath;
  if (!targetPath) {
    const result = await dialog.showSaveDialog({
      filters: [{ name: 'Python', extensions: ['py'] }],
      defaultPath: 'program.py',
    });
    if (result.canceled || !result.filePath) {
      return null;
    }
    targetPath = result.filePath;
  }
  writeFileSync(targetPath, content, 'utf8');
  return targetPath;
});

ipcMain.handle('get-settings', () => loadSettings());

ipcMain.handle('save-settings', (_event, settings: Settings) => {
  saveSettings(settings);
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
  const { hostname, password } = loadSettings();
  const proc = spawn('python', [proxyPath, 'run', scriptPath], {
    env: { ...process.env, DOGGO_HOST: hostname, DOGGO_PASSWORD: password },
  });
  runningProcess = proc;

  proc.stdout?.on('data', (data: Buffer) => {
    mainWindow?.webContents.send('script-output', data.toString());
  });

  proc.stderr?.on('data', (data: Buffer) => {
    mainWindow?.webContents.send('script-output', data.toString());
  });

  proc.on('close', (exitCode: number | null) => {
    runningProcess = null;
    mainWindow?.webContents.send('script-done', exitCode);
  });
});

ipcMain.on('confirm-quit', () => {
  allowQuit = true;
  mainWindow?.close();
});
