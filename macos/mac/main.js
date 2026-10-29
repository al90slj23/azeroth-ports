'use strict';

// Local macOS wrapper adapted from:
// https://github.com/myslithell/azeroth-survivors/blob/a65664af64f4377159463cd128424eeb6f132102/mac/main.js
// Azeroth Survivors and the bundled browser game are by Aethus: https://wow.aethus.pl/.
const { app, BrowserWindow, dialog, shell, session } = require('electron');
const path = require('node:path');
const fs = require('node:fs/promises');
const { createStaticServer } = require('./static-server');
const { preparePendingProfile } = require('./profile-migration');
const { attachCoopProxy } = require('./coop-proxy');

const PORT = 47615;
const ORIGIN = `http://127.0.0.1:${PORT}`;
const EXTERNAL_HOSTS = new Set(['wow.aethus.pl', 'discord.gg', 'discord.com']);
let server;
let coop;
let mainWindow;

async function refreshFontCacheOnce() {
  const profile = app.getPath('userData');
  let stamp = 'base';
  try {
    const core = JSON.parse(await fs.readFile(path.join(process.resourcesPath, 'web-core-manifest.json'), 'utf8'));
    if (/^[a-f0-9]{8,64}$/.test(core.stamp)) stamp = core.stamp;
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  const marker = path.join(profile, `mac-assets-${stamp}-cjk-v3.cache`);
  try {
    await fs.access(marker);
    return;
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  // Font URLs existed before this patch and were cached as immutable. Clear only this
  // app's HTTP asset cache once; localStorage, saves, cookies and settings are preserved.
  await session.defaultSession.clearCache();
  await fs.mkdir(profile, { recursive: true });
  await fs.writeFile(marker, `${stamp}:official-cjk-v3\n`);
}

// Keep the existing Chromium profile and fixed origin: together they own the player's saves.
app.setName('Azeroth Survivors');
// Honor an explicitly selected profile before Chromium opens any storage. This also lets
// local smoke tests use a temporary profile without touching a player's progress.
const profileArgument = process.argv.find((argument) => argument.startsWith('--user-data-dir='));
let profileError;
if (profileArgument && profileArgument.slice('--user-data-dir='.length)) {
  app.setPath('userData', path.resolve(profileArgument.slice('--user-data-dir='.length)));
} else {
  // Complete the one-time handoff from an interactive test profile before Chromium
  // opens storage or takes its single-instance lock. Never copy a running profile.
  try {
    const selected = preparePendingProfile({
      pendingPath: path.join(app.getPath('appData'), 'Azeroth Survivors.pending-profile.json'),
      defaultProfile: app.getPath('userData'),
      isProcessAlive(pid) {
        try {
          process.kill(pid, 0);
          return true;
        } catch (error) {
          if (error.code === 'ESRCH') return false;
          if (error.code === 'EPERM') return true;
          throw error;
        }
      },
    });
    app.setPath('userData', selected.profile);
  } catch (error) {
    profileError = error;
  }
}

function isLocal(url) {
  try {
    return new URL(url).origin === ORIGIN;
  } catch {
    return false;
  }
}

function openOfficialLink(url) {
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    return;
  }
  if (parsed.protocol !== 'https:' || !EXTERNAL_HOSTS.has(parsed.hostname)
      || parsed.username || parsed.password || parsed.port) return;
  // Only these exact HTTPS hosts can leave the game window; never pass custom protocols through.
  shell.openExternal(parsed.href).catch((error) => console.error('Could not open external link:', error));
}

function showWindow() {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 900,
    title: 'Azeroth Survivors',
    backgroundColor: '#000000',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true,
      allowRunningInsecureContent: false,
    },
  });
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (isLocal(url)) return;
    event.preventDefault();
    openOfficialLink(url);
  });
  mainWindow.webContents.on('will-redirect', (event, url) => {
    if (!isLocal(url)) event.preventDefault();
  });
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    openOfficialLink(url);
    return { action: 'deny' };
  });
  mainWindow.on('closed', () => { mainWindow = undefined; });
  mainWindow.loadURL(ORIGIN + '/').catch((error) => {
    dialog.showErrorBox('Azeroth Survivors', `Could not load the bundled game: ${error.message}`);
    app.quit();
  });
}

if (profileError) {
  dialog.showErrorBox('Azeroth Survivors', `Could not preserve the existing game profile: ${profileError.message}`);
  app.quit();
} else if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (!mainWindow) return;
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.show();
    mainWindow.focus();
  });
  app.on('window-all-closed', () => app.quit());
  app.on('before-quit', () => {
    if (coop) coop.close();
    if (server) server.close();
  });
  app.whenReady().then(async () => {
    await refreshFontCacheOnce();
    server = createStaticServer({
      root: path.join(process.resourcesPath, 'www'),
      requestHandler: (req, res) => coop.handleRequest(req, res),
    });
    coop = attachCoopProxy(server, { localOrigin: ORIGIN });
    server.on('error', (error) => {
      dialog.showErrorBox('Azeroth Survivors', `Could not open ${ORIGIN}: ${error.message}`);
      app.quit();
    });
    server.listen(PORT, '127.0.0.1', showWindow);
  }).catch((error) => {
    dialog.showErrorBox('Azeroth Survivors', `Could not start the bundled game: ${error.message}`);
    app.quit();
  });
}
