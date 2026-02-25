<<<<<<< HEAD
import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
=======
import { app, BrowserWindow } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
>>>>>>> b77603ccca528f233f6ce3688c4be5faf77979b3

const __dirname = path.dirname(fileURLToPath(import.meta.url));

process.env.APP_ROOT = path.join(__dirname, '../..');

export const VITE_DEV_SERVER_URL = process.env.VITE_DEV_SERVER_URL;
export const RENDERER_DIST = path.join(process.env.APP_ROOT, 'dist');

let mainWindow: BrowserWindow | null = null;

function createWindow() {
<<<<<<< HEAD
  const preloadPath = path.resolve(__dirname, '../preload/index.js');
  console.log('Main: Resolving preload path:', preloadPath);
  console.log('Main: Preload file exists:', fs.existsSync(preloadPath));

=======
>>>>>>> b77603ccca528f233f6ce3688c4be5faf77979b3
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: 'OpenAgents',
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    trafficLightPosition: { x: 16, y: 16 },
    webPreferences: {
<<<<<<< HEAD
      preload: preloadPath,
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
=======
      preload: path.join(__dirname, '../preload/index.js'),
      nodeIntegration: false,
      contextIsolation: true,
>>>>>>> b77603ccca528f233f6ce3688c4be5faf77979b3
    },
  });

  // Maximize window by default
  mainWindow.maximize();

  // Load the app
  if (VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(VITE_DEV_SERVER_URL);
    // Open DevTools in development
    mainWindow.webContents.openDevTools({ mode: 'right' });
  } else {
    mainWindow.loadFile(path.join(RENDERER_DIST, 'index.html'));
  }

  // Open external links in browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https:') || url.startsWith('http:')) {
      require('electron').shell.openExternal(url);
    }
    return { action: 'deny' };
  });
}

// Single instance lock
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(() => {
    createWindow();

<<<<<<< HEAD
    // Register IPC handlers
    ipcMain.handle('select-directory', async () => {
      console.log('IPC: select-directory handler called');
      if (!mainWindow) {
        console.error('IPC: mainWindow is null');
        return null;
      }
      try {
        const result = await dialog.showOpenDialog(mainWindow, {
          properties: ['openDirectory'],
          title: 'Select Base Directory',
          buttonLabel: 'Select Directory'
        });
        console.log('IPC: dialog result:', result.canceled ? 'canceled' : result.filePaths[0]);
        if (result.canceled) return null;
        return result.filePaths[0];
      } catch (err) {
        console.error('IPC: dialog error:', err);
        return null;
      }
    });

=======
>>>>>>> b77603ccca528f233f6ce3688c4be5faf77979b3
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  });
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
