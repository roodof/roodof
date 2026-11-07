'use strict';
const { app, BrowserWindow, dialog, shell, session, nativeTheme, screen } = require('electron');
const { randomUUID } = require('node:crypto');
const { accessURL, localURL, externalURL } = require('./policy.cjs');
const windowState = require('./window-state.cjs');
const { normalizeView } = require('./view-preferences.cjs');

app.setName('PLER');
nativeTheme.themeSource = 'dark';
let window;
const fs = require('node:fs');
const path = require('node:path');
// One taskbar identity: the running window, a pinned button and Start shortcuts group as PLER.
const APP_ID = 'PLER.Desktop';
if (process.platform === 'win32') app.setAppUserModelId(APP_ID);
const iconFile = path.join(__dirname, 'pler.ico');
const icon = fs.existsSync(iconFile) ? iconFile : undefined;

// A pinned taskbar button must start the stable PLER.exe launcher, never this inner window
// process (it needs a private session from the launcher). The topmost launcher within a few
// folders is used, so an updated version inside the installation still pins the stable one.
function launcherPath() {
  let found = null, folder = path.dirname(process.execPath);
  for (let level = 0; level < 4; level += 1) {
    folder = path.dirname(folder);
    const candidate = path.join(folder, 'PLER.exe');
    if (fs.existsSync(candidate)) found = candidate;
  }
  return found;
}
const control = process.env.PLER_DESKTOP_SESSION;
const parent = Number(process.env.PLER_DESKTOP_PARENT);
const startup = process.env.PLER_DESKTOP_URL;
const stateFile = process.env.PLER_DESKTOP_STATE;
delete process.env.PLER_DESKTOP_URL;
delete process.env.PLER_DESKTOP_STATE;
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
  // Size, position and language from the last run; the address and its key are never stored.
  const remembered = windowState.read(stateFile, screen.getAllDisplays().map(display => display.workArea));
  // On Windows the system title bar becomes part of the dark app; the page leaves room for its buttons.
  const titleBar = process.platform === 'win32'
    ? { titleBarStyle: 'hidden', titleBarOverlay: { color: '#101012', symbolColor: '#b0b0bb', height: 36 } } : {};
  window = new BrowserWindow({
    title: 'PLER', width: remembered.width, height: remembered.height, x: remembered.x, y: remembered.y,
    minWidth: windowState.LIMITS.minWidth, minHeight: windowState.LIMITS.minHeight, ...titleBar, icon,
    backgroundColor: '#101012', show: false, autoHideMenuBar: true,
    webPreferences: { session: isolated, nodeIntegration: false, contextIsolation: true,
      sandbox: true, webSecurity: true, webviewTag: false, devTools: false }
  });
  window.setMenu(null);
  const launcher = process.platform === 'win32' ? launcherPath() : null;
  if (launcher) {
    window.setAppDetails({ appId: APP_ID, appIconPath: icon || launcher, appIconIndex: 0,
      relaunchCommand: '"' + launcher + '"', relaunchDisplayName: 'PLER' });
  }
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
      const child = new BrowserWindow({ parent: window, width: 900, height: 750, icon,
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
  if (remembered.maximized) window.maximize();
  let language = remembered.lang, toured = remembered.tour, view = remembered.view, saved = false;
  // On close, collect language, tour and bounded view choices, then save and close for real.
  // A page that does not answer within 600 ms closes anyway with what is already known.
  window.on('close', event => {
    if (saved) return;
    event.preventDefault();
    let finished = false;
    const finish = () => {
      if (finished) return; finished = true; saved = true;
      windowState.write(stateFile, window.getNormalBounds(), window.isMaximized(), language, toured, view);
      window.destroy();
    };
    const timer = setTimeout(finish, 600);
    window.webContents.executeJavaScript('({lang:document.documentElement.lang,tour:document.documentElement.dataset.tourSeen==="1",view:typeof window.plerGetViewPreferences==="function"?window.plerGetViewPreferences():null})')
      .then(value => { if (value?.lang === 'en' || value?.lang === 'tr') language = value.lang; toured = toured || value?.tour === true; if (value?.view) view = normalizeView(value.view); })
      .catch(() => {}).finally(() => { clearTimeout(timer); finish(); });
  });
  window.once('ready-to-show', () => { window.show(); window.focus(); });
  window.on('closed', () => app.quit());
  window.webContents.on('render-process-gone', () => app.exit(1));
  // The page reads ?lang= before its own saved choice; the remembered language survives the fresh session.
  const first = new URL(url.href);
  const query = new URLSearchParams();
  if (remembered.lang) query.set('lang', remembered.lang);
  if (remembered.tour) query.set('tour', 'seen');
  if (remembered.view) query.set('view', JSON.stringify(remembered.view));
  first.search = query.toString() ? '?' + query : '';
  await window.loadURL(first.href);
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
