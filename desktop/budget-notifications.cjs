'use strict';
// Main-process polling keeps alerts alive while the renderer is minimized/throttled.
// Fixed loopback routes only; no renderer IPC or browser permission is opened.
const http = require('node:http');
const { accessURL } = require('./policy.cjs');

function localRequest(url, route, body) {
  const data = body === undefined ? null : JSON.stringify(body);
  return new Promise((resolve, reject) => {
    const request = http.request(new URL(route, url.origin), {
      method: data === null ? 'GET' : 'POST', timeout: 4000,
      headers: { 'X-PLER-Token': url.hash.slice(8), Origin: url.origin,
        ...(data === null ? {} : { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }) }
    }, response => {
      let value = '', bytes = 0;
      response.on('data', chunk => {
        bytes += chunk.length;
        if (bytes > 65536) response.destroy(new Error('budget response limit'));
        else value += chunk.toString('utf8');
      });
      response.on('error', reject);
      response.on('end', () => {
        try { if (response.statusCode !== 200) throw new Error('budget unavailable'); resolve(JSON.parse(value)); }
        catch (error) { reject(error); }
      });
    });
    request.on('timeout', () => request.destroy(new Error('budget request timeout')));
    request.on('error', reject);
    request.end(data);
  });
}

function start({ startup, Notification, window, icon, request = localRequest, interval = 5000 }) {
  const url = accessURL(startup), sent = new Set(), active = new Set(), retries = new Map();
  let busy = false, stopped = false;
  async function tick() {
    if (stopped || busy || window.isDestroyed()) return;
    busy = true;
    try {
      const value = await request(url, '/api/usage/budgets');
      if (!value.readable || !Array.isArray(value.items) || value.items.length > 20 || !Notification.isSupported()) return;
      const keys = new Set();
      for (const row of value.items) {
        if (!/^[a-f0-9]{24}$/.test(row.id) || !/^[a-f0-9]{24}$/.test(row.revision)
            || ![80, 100].includes(row.pending_level) || row.state !== 'watching') continue;
        const key = `${row.id}:${row.revision}:${row.pending_level}`;
        keys.add(key);
        const ack = () => request(url, '/api/usage/budgets/ack', { id: row.id, revision: row.revision, level: row.pending_level }).catch(() => {});
        if (sent.has(key)) { await ack(); continue; }
        if ((retries.get(key) || 0) > Date.now() || stopped) continue;
        const tr = new URL(window.webContents.getURL()).searchParams.get('lang') === 'tr';
        const metric = row.metric === 'tokens' ? 'token' : tr ? 'API fiyat karşılığı' : 'API price equivalent';
        const title = tr ? 'PLER · Oturum bütçe uyarısı' : 'PLER · Session budget alert';
        const body = tr ? `#${row.id.slice(0, 6)} · ${metric} eşiğinin %${row.pending_level} değerine ulaşıldı. PLER oturumu durdurmaz.`
          : `#${row.id.slice(0, 6)} · ${row.pending_level}% of the ${metric} threshold reached. PLER does not stop the session.`;
        const notification = new Notification({ title, body, icon, silent: false });
        active.add(notification);
        if (active.size > 40) { const oldest = active.values().next().value; oldest.close(); active.delete(oldest); }
        retries.set(key, Date.now() + 60000);
        notification.once('show', () => { sent.add(key); ack(); });
        notification.once('failed', () => active.delete(notification));
        notification.once('close', () => active.delete(notification));
        notification.once('click', () => {
          if (window.isDestroyed()) return;
          if (window.isMinimized()) window.restore();
          window.show(); window.focus();
          window.webContents.executeJavaScript(`window.plerOpenBudgetSession?.('${row.id}')`).catch(() => {});
        });
        notification.show();
      }
      // Bound memory when limits are edited repeatedly in one application lifetime.
      for (const key of sent) if (!keys.has(key)) sent.delete(key);
      for (const key of retries.keys()) if (!keys.has(key)) retries.delete(key);
    } catch { /* The in-app status remains available; never print the private access URL. */ }
    finally { busy = false; }
  }
  const timer = setInterval(tick, interval);
  tick();
  return { tick, close() { stopped = true; clearInterval(timer); for (const n of active) n.close(); active.clear(); } };
}

module.exports = { start, localRequest };
