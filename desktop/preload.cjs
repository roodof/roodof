'use strict';
const { contextBridge, ipcRenderer } = require('electron');
// A single fixed operation. No IPC object, arbitrary channel, path reader or shell is exposed.
contextBridge.exposeInMainWorld('plerDesktop', Object.freeze({
  chooseLogFolder: () => ipcRenderer.invoke('pler:choose-log-folder')
}));
