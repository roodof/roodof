'use strict';
const { app, BrowserWindow, dialog, shell, session, nativeTheme } = require('electron');
const { randomUUID } = require('node:crypto');
const { accessURL, localURL, externalURL } = require('./policy.cjs');

app.setName('PLER');
nativeTheme.themeSource = 'dark';
let window;
const fs = require('node:fs');
const path = require('node:path');
const control = process.env.PLER_DESKTOP_SESSION;
const parent = Number(process.env.PLER_DESKTOP_PARENT);
const startup = process.env.PLER_DESKTOP_URL;
delete process.env.PLER_DESKTOP_URL;
delete process.env.PLER_DESKTOP_SESSION;
delete process.env.PLER_DESKTOP_PARENT;
const timeout = setTimeout(() => app.exit(1), 30000);

function fail() {
  clearTimeout(timeout);
  dialog.showErrorBox('PLER', 'The desktop window could not open. Close PLER and extract the complete package again.');
  app.exit(1);
}

async function open(value) {
  const url = accessURL(value);
  await app.whenReady();
  const isolated = session.fromPartition('pler-' + randomUUID());
  isolated.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  isolated.setPermissionCheckHandler(() => false);
  isolated.webRequest.onBeforeRequest((details, callback) => {
    const permitted = localURL(details.url, url.origin) ||
      details.url.startsWith('blob:' + url.origin + '/') || details.url.startsWith('data:');
    callback({ cancel: !permitted });
  });
  window = new BrowserWindow({
    title: 'PLER', width: 1240, height: 850, minWidth: 420, minHeight: 480,
    backgroundColor: '#101012', show: false, autoHideMenuBar: true,
    webPreferences: { session: isolated, nodeIntegration: false, contextIsolation: true,
      sandbox: true, webSecurity: true, webviewTag: false, devTools: false }
  });
  window.setMenu(null);
  window.webContents.on('will-navigate', (event, target) => {
    if (!localURL(target, url.origin)) {
      event.preventDefault();
      if (externalURL(target)) shell.openExternal(target).catch(() => {});
    }
  });
  window.webContents.on('will-redirect', (event, target) => {
    if (!localURL(target, url.origin)) event.preventDefault();
  });
  window.webContents.setWindowOpenHandler(({ url: target }) => {
    if (localURL(target, url.origin)) {
      const child = new BrowserWindow({ parent: window, width: 900, height: 750,
        autoHideMenuBar: true, webPreferences: { session: isolated, nodeIntegration: false,
          contextIsolation: true, sandbox: true, webSecurity: true, devTools: false } });
      child.setMenu(null);
      child.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
      child.webContents.on('will-navigate', (event, dest) => {
        if (!localURL(dest, url.origin)) event.preventDefault();
      });
      child.webContents.on('will-redirect', (event, dest) => {
        if (!localURL(dest, url.origin)) event.preventDefault();
      });
      child.loadURL(target).catch(() => child.close());
    } else if (externalURL(target)) shell.openExternal(target).catch(() => {});
    return { action: 'deny' };
  });
  window.once('ready-to-show', () => { window.show(); window.focus(); });
  window.on('closed', () => app.quit());
  window.webContents.on('render-process-gone', () => app.exit(1));
  await window.loadURL(url.href);
  fs.writeFileSync(path.join(control, 'ready'), '1');
  clearTimeout(timeout);
}

if (!control || !path.isAbsolute(control) || !Number.isSafeInteger(parent) || parent <= 0) {
  app.exit(1);
} else {
  fs.mkdirSync(path.join(control, 'profile'), { recursive: true });
  app.setPath('userData', path.join(control, 'profile'));
  const lifetime = setInterval(() => {
    try {
      process.kill(parent, 0);
      if (!fs.existsSync(path.join(control, 'running'))) app.quit();
    } catch { app.quit(); }
  }, 500);
  app.on('will-quit', () => { clearInterval(lifetime); clearTimeout(timeout); });
  open(startup).catch(fail);
}
app.on('window-all-closed', () => app.quit());
