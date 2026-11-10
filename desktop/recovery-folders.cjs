'use strict';
const { authorized } = require('./source-folders.cjs');
const CHANNEL = 'pler:choose-recovery-parent';
function install({ ipcMain, dialog, window, origin }) {
  let busy=false;
  ipcMain.handle(CHANNEL, async event => {
    if(busy || !authorized(event,window,origin))return null;
    busy=true;
    try {
      const result=await dialog.showOpenDialog(window,{
        title:'Roodof — Recovery location / Kurtarma konumu', properties:['openDirectory','dontAddToRecent']
      });
      if(!authorized(event,window,origin) || result.canceled || result.filePaths.length!==1)return null;
      return result.filePaths[0];
    } catch {return null;}
    finally {busy=false;}
  });
  window.once('closed',()=>ipcMain.removeHandler(CHANNEL));
}
module.exports={CHANNEL,install};
