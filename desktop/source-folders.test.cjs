'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { CHANNEL, authorized, install } = require('./source-folders.cjs');
function fixture() {
  const frame = { url: 'http://127.0.0.1:1234/?lang=tr' };
  const window = { webContents: { mainFrame: frame }, isDestroyed: () => false, once: (_name, cb) => { window.closed = cb; } };
  const event = { sender: window.webContents, senderFrame: frame };
  return { window, event, origin: 'http://127.0.0.1:1234' };
}
test('folder operation accepts only own top frame at the application page', () => {
  const f = fixture(); assert.equal(authorized(f.event, f.window, f.origin), true);
  for (const url of ['https://example.invalid/', 'http://127.0.0.1:1234/help', 'file:///C:/private']) {
    f.event.senderFrame.url = url; assert.equal(authorized(f.event, f.window, f.origin), false);
  }
  const other=fixture();assert.equal(authorized(other.event,f.window,f.origin),false);
  const child=fixture();child.event.senderFrame={url:child.event.senderFrame.url};assert.equal(authorized(child.event,child.window,child.origin),false);
});
test('one native parented directory picker, no renderer-provided options, cancel and cleanup', async () => {
  const f=fixture();let handler, calls=0, resolve;
  const ipcMain={handle:(channel,fn)=>{assert.equal(channel,CHANNEL);handler=fn;},removeHandler:channel=>assert.equal(channel,CHANNEL)};
  const dialog={showOpenDialog:(window,options)=>{calls++;assert.equal(window,f.window);assert.deepEqual(options.properties,['openDirectory','dontAddToRecent']);return new Promise(done=>resolve=done);}};
  install({...f,ipcMain,dialog});
  const first=handler(f.event,{path:'ignored',command:'ignored'});
  assert.equal(await handler(f.event),null);assert.equal(calls,1);
  resolve({canceled:false,filePaths:['C:\\invented\\logs']});assert.equal(await first,'C:\\invented\\logs');
  const canceled=handler(f.event);resolve({canceled:true,filePaths:[]});assert.equal(await canceled,null);
  f.window.closed();
});
