const test = require('node:test');
const assert = require('node:assert/strict');
const { accessURL, localURL, externalURL } = require('./policy.cjs');
const address = 'http://127.0.0.1:49152/#access=' + 'a'.repeat(64);

test('startup accepts only the authenticated loopback endpoint', () => {
  assert.equal(accessURL(address).origin, 'http://127.0.0.1:49152');
  for (const invalid of [address.replace('127.0.0.1', 'localhost'), address.replace('http:', 'https:'),
    address.replace('127.0.0.1', '127.0.0.1.evil.invalid'), address.replace('/#', '/other#'),
    address.replace('/#', '/?url=evil#'), address.replace('127.0.0.1', 'user@127.0.0.1'),
    address.slice(0, -1), 'file:///C:/private', 'javascript:alert(1)']) {
    assert.throws(() => accessURL(invalid));
  }
});

test('navigation cannot move into another local service or remote origin', () => {
  const origin = accessURL(address).origin;
  assert.ok(localURL(origin + '/help?lang=tr', origin));
  for (const invalid of ['http://127.0.0.1:8765/', 'https://example.com/', 'file:///C:/private',
    'http://127.0.0.1.evil.invalid:49152/', 'not a URL']) assert.equal(localURL(invalid, origin), false);
});

test('external links never invoke files, commands, custom schemes or credentials', () => {
  assert.ok(externalURL('https://www.python.org/'));
  for (const invalid of ['file:///C:/app.exe', 'cmd:run', 'javascript:alert(1)', 'http://example.com/',
    'https://user:password@example.com/', 'not a URL']) assert.equal(externalURL(invalid), false);
});
