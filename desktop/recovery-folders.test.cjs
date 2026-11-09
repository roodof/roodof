'use strict';
const test=require('node:test');const assert=require('node:assert/strict');
const {CHANNEL,install}=require('./recovery-folders.cjs');
test('recovery picker is single, parent-owned, cancellable, and removed on close',async()=>{
 const frame={url:'http://127.0.0.1:1234/'};
 const window={webContents:{mainFrame:frame},isDestroyed:()=>false,once:(_event,fn)=>window.closed=fn};
 const event={sender:window.webContents,senderFrame:frame};let handler,resolve,calls=0;
 install({window,origin:'http://127.0.0.1:1234',ipcMain:{handle:(name,fn)=>{assert.equal(name,CHANNEL);handler=fn;},removeHandler:name=>assert.equal(name,CHANNEL)},dialog:{showOpenDialog:()=>{calls++;return new Promise(r=>resolve=r);}}});
 assert.equal(await handler({sender:{},senderFrame:frame}),null);assert.equal(calls,0);
 const first=handler(event);assert.equal(await handler(event),null);assert.equal(calls,1);
 resolve({canceled:false,filePaths:['C:\\invented\\recovery']});assert.equal(await first,'C:\\invented\\recovery');
 const second=handler(event);frame.url='http://127.0.0.1:1234/help';resolve({canceled:false,filePaths:['C:\\invented']});assert.equal(await second,null);
 window.closed();
});
