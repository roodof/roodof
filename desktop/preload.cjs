'use strict';
const { contextBridge, ipcRenderer } = require('electron');
// Fixed directory pickers only. No IPC object, path reader or shell is exposed.
contextBridge.exposeInMainWorld('plerDesktop', Object.freeze({
  chooseLogFolder: () => ipcRenderer.invoke('pler:choose-log-folder'),
  chooseRecoveryParent: () => ipcRenderer.invoke('pler:choose-recovery-parent')
}));
