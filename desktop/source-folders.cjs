'use strict';
const CHANNEL = 'pler:choose-log-folder';

function authorized(event, window, origin) {
  try {
    const url = new URL(event.senderFrame.url);
    return !window.isDestroyed() && event.sender === window.webContents &&
      event.senderFrame === window.webContents.mainFrame && url.origin === origin && url.pathname === '/';
  } catch { return false; }
}

function install({ ipcMain, dialog, window, origin }) {
  let busy = false;
  ipcMain.handle(CHANNEL, async event => {
    if (busy || !authorized(event, window, origin)) return null;
    busy = true;
    try {
      const result = await dialog.showOpenDialog(window, {
        title: 'PLER — Log folder / Kayıt klasörü', properties: ['openDirectory', 'dontAddToRecent']
      });
      if (!authorized(event, window, origin) || result.canceled || result.filePaths.length !== 1) return null;
      return result.filePaths[0];
    } catch { return null; }
    finally { busy = false; }
  });
  window.once('closed', () => ipcMain.removeHandler(CHANNEL));
}
module.exports = { CHANNEL, authorized, install };
