'use strict';

function accessURL(value) {
  const url = new URL(value);
  if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || !url.port ||
      url.username || url.password || url.pathname !== '/' || url.search ||
      !/^#access=[a-f0-9]{64}$/.test(url.hash)) throw new Error('Invalid local startup address');
  return url;
}

function localURL(value, origin) {
  try { return new URL(value).origin === origin; } catch { return false; }
}

function externalURL(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && !url.username && !url.password;
  } catch { return false; }
}

module.exports = { accessURL, localURL, externalURL };
