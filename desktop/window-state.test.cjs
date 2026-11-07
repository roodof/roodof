'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { restore, read, write, DEFAULTS } = require('./window-state.cjs');

const screen = [{ x: 0, y: 0, width: 1920, height: 1040 }];

test('a saved window on a visible display comes back with its language', () => {
  assert.deepEqual(restore({ x: 100, y: 80, width: 1300, height: 900, maximized: true, lang: 'tr', tour: true }, screen),
    { x: 100, y: 80, width: 1300, height: 900, maximized: true, lang: 'tr', tour: true });
});

test('a window left on a disconnected display keeps its size but is centered again', () => {
  const value = restore({ x: 4000, y: 100, width: 1300, height: 900 }, screen);
  assert.equal(value.x, undefined); assert.equal(value.y, undefined);
  assert.equal(value.width, 1300);
});

test('damaged, oversized or foreign values fall back to defaults', () => {
  for (const raw of [null, [], 'x', { width: 10, height: 10 }, { width: 1e9, height: 900 }, { width: 1300.5, height: 900 }]) {
    const value = restore(raw, screen);
    assert.equal(value.width, DEFAULTS.width); assert.equal(value.height, DEFAULTS.height);
  }
  assert.equal(restore({ lang: 'de', maximized: 'yes' }, screen).lang, null);
  assert.equal(restore({ lang: 'de', maximized: 'yes' }, screen).maximized, false);
});

test('write keeps only geometry and language, and read survives a broken file', () => {
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'pler-window-'));
  const file = path.join(folder, 'nested', 'desktop-window.json');
  assert.equal(write(file, { x: 10.4, y: 20, width: 1000, height: 700 }, false, 'en', 'yes'), true);
  assert.deepEqual(JSON.parse(fs.readFileSync(file, 'utf8')), { x: 10, y: 20, width: 1000, height: 700, maximized: false, lang: 'en', tour: false });
  assert.equal(read(file, screen).width, 1000);
  fs.writeFileSync(file, '{broken');
  assert.equal(read(file, screen).width, DEFAULTS.width);
  assert.equal(write(null, { x: 0, y: 0, width: 1, height: 1 }, false), false);
  fs.rmSync(folder, { recursive: true, force: true });
});
