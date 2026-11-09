'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const { start } = require('./budget-notifications.cjs');
const startup = `http://127.0.0.1:41234/#access=${'a'.repeat(64)}`;
const row = { id: 'b'.repeat(24), revision: 'c'.repeat(24), metric: 'tokens', state: 'watching', pending_level: 100 };

test('native delivery acknowledges only after show and does not repeat on the next poll', async () => {
 const calls = [], shown = [], scripts = [];
 class Notification extends EventEmitter {
  static isSupported() { return true; }
  constructor(options) { super(); this.options = options; shown.push(this); }
  show() {} close() {}
 }
 const window = { isDestroyed: () => false, isMinimized: () => true, restore() { calls.push('restore'); }, show() {}, focus() {},
  webContents: { getURL: () => startup.replace('/#','/?lang=tr#'), executeJavaScript: async script => scripts.push(script) } };
 let pending = true;
 const request = async (_url, route, body) => { if (body) { calls.push(body); pending = false; return { ok: true }; } return { readable: true, items: pending ? [row] : [] }; };
 const monitor = start({ startup, Notification, window, request, interval: 100000 });
 try {
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(shown.length, 1); assert.equal(calls.length, 0);
  assert.match(shown[0].options.title, /bütçe/);
  assert.ok(!shown[0].options.body.includes('a'.repeat(64)));
  shown[0].emit('show'); await monitor.tick();
  assert.equal(shown.length, 1); assert.equal(calls[0].level, 100);
  shown[0].emit('click'); assert.ok(calls.includes('restore')); assert.match(scripts[0], /plerOpenBudgetSession/);
 } finally { monitor.close(); }
});

test('failed native delivery is not acknowledged; malformed events cannot run script', async () => {
 const calls = [], shown = [];
 class Notification extends EventEmitter {
  static isSupported() { return true; }
  constructor() { super(); shown.push(this); } show() { this.emit('failed'); } close() {}
 }
 const window = { isDestroyed: () => false, webContents: { getURL: () => startup } };
 const request = async (_url, _route, body) => { if (body) calls.push(body); return { readable: true, items: [row, { ...row, id: "x');evil()" }] }; };
 const monitor = start({ startup, Notification, window, request, interval: 100000 });
 try { await new Promise(resolve => setImmediate(resolve)); await monitor.tick(); assert.equal(shown.length, 1); assert.equal(calls.length, 0); }
 finally { monitor.close(); }
});
