const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');

// Handle running as root - disable sandbox
app.commandLine.appendSwitch('--no-sandbox');
app.commandLine.appendSwitch('--disable-dev-shm-usage');

let mainWindow;

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: false, // Allow loading local resources
      allowRunningInsecureContent: true
    },
    icon: path.join(__dirname, 'favicon.ico'),
    title: 'LAN E-Learning Platform',
    show: false // Don't show until ready
  });

  // Load the app
  const startUrl = isDev 
    ? 'http://localhost:3000' 
    : `file://${path.join(__dirname, '../build/index.html')}`;
    
  mainWindow.loadURL(startUrl);

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    console.log('🖥️ LAN E-Learning Desktop Application started successfully!');
  });

  // Open DevTools in development only
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// This method will be called when Electron has finished initialization
app.whenReady().then(() => {
  createWindow();
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Handle file opening requests from renderer process
ipcMain.handle('open-file', async (event, filePath) => {
  try {
    console.log('📁 Opening file:', filePath);
    
    // Check if it's a URL
    if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
      await shell.openExternal(filePath);
      return { success: true, message: 'URL opened successfully' };
    } else {
      // For local files, use openPath
      const result = await shell.openPath(filePath);
      if (result === '') {
        console.log('✅ File opened successfully:', filePath);
        return { success: true, message: 'File opened successfully' };
      } else {
        console.log('❌ Error opening file:', result);
        return { success: false, message: `Error opening file: ${result}` };
      }
    }
  } catch (error) {
    console.error('❌ Error opening file:', error);
    return { success: false, message: `Error: ${error.message}` };
  }
});

// Handle showing file in folder
ipcMain.handle('show-file-in-folder', async (event, filePath) => {
  try {
    console.log('📂 Showing file in folder:', filePath);
    shell.showItemInFolder(filePath);
    return { success: true, message: 'File shown in folder' };
  } catch (error) {
    console.error('❌ Error showing file in folder:', error);
    return { success: false, message: `Error: ${error.message}` };
  }
});