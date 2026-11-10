// Limits page: one gauge per quota window with a "when does it fill" time track, from the forecast Roodof
// already computes (outlook). Long explanatory notes move into Base UI popovers next to their heading.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { Popover } from '@base-ui/react/popover';
import { init, use } from 'echarts/core';
import { GaugeChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import { createElement as createIcon, Info } from 'lucide';

use([GaugeChart, CanvasRenderer]);

function el(tag, cls, text) { const node = document.createElement(tag); if (cls) node.className = cls; if (text) node.textContent = text; return node; }
const token = name => getComputedStyle(document.body).getPropertyValue('--ui-' + name).trim();

// Base UI popover: real focus management, Escape and outside click, positioned by Floating UI.
function InfoTip({ label, nodes }) {
  return <Popover.Root>
    <Popover.Trigger className="ws-info" aria-label={label} ref={element => { if (element && !element.firstChild) element.append(createIcon(Info, { width: 14, height: 14, 'stroke-width': 1.8, 'aria-hidden': 'true' })); }} />
    <Popover.Portal>
      <Popover.Positioner sideOffset={8} align="start" collisionPadding={12}>
        <Popover.Popup className="ws-info-popup">
          <div ref={element => { if (element && !element.firstChild) element.append(...nodes); }} />
        </Popover.Popup>
      </Popover.Positioner>
    </Popover.Portal>
  </Popover.Root>;
}

export function mountQuota({ tr, page }) {
  const lang = tr ? 'tr-TR' : 'en-US';
  const words = tr ? {
    info: 'Açıklama', limit: 'sınır', unlinked: 'Bağlı değil', unlinkedTitle: 'Kota kaynağı yok', unlinkedWhy: 'Claude Code kota yüzdesini kayıtlarına yazmaz. Terminaldeki Claude Code için bir kez şunu çalıştır; ayar değişmeden önce onayın sorulur:', unlinkedDesktop: 'Claude masaüstü uygulamasından kota verisi geldiği doğrulanmadı.', copy: 'Kopyala', copied: 'Kopyalandı', pace: 'hız', resetIn: 'Sıfırlanmaya', resetAt: 'sıfırlanma', fillsAt: 'Bu hızla dolma zamanı', now: 'şimdi', sampled: 'son ölçüm',
    no_pace: 'Tahmin için yeterli geçmiş yok', ago: 'önce', lasts: 'Sıfırlanmaya kadar yeter', fills: 'Sıfırlanmadan dolabilir', full: 'Dolu', stale: 'Ölçüm eski',
    reset: 'Sıfırlandı; yeni ölçüm bekleniyor', historical: 'Sıfırlanma zamanı bilinmiyor', ambiguous: 'Ölçümler çelişiyor', used: 'kullanıldı',
    gaugeLabel: (agent, window, value) => `${agent} ${window}: yüzde ${value} kullanıldı`
  } : {
    info: 'About this', limit: 'limit', unlinked: 'Not connected', unlinkedTitle: 'No quota source', unlinkedWhy: 'Claude Code does not write its quota percentage to its logs. For Claude Code in a terminal, run this once; you are asked before any setting changes:', unlinkedDesktop: 'Quota data from the Claude desktop app is not confirmed.', copy: 'Copy', copied: 'Copied', pace: 'pace', resetIn: 'Resets in', resetAt: 'reset', fillsAt: 'At this pace it fills at', now: 'now', sampled: 'last sample',
    no_pace: 'Not enough history for a forecast', ago: 'ago', lasts: 'Lasts until the reset', fills: 'May fill before the reset', full: 'Full', stale: 'Sample is old',
    reset: 'Reset; waiting for a new sample', historical: 'Reset time unknown', ambiguous: 'Samples disagree', used: 'used',
    gaugeLabel: (agent, window, value) => `${agent} ${window}: ${value} percent used`
  };
  const strip = el('section', 'ws-quota-gauges');
  strip.hidden = true;
  page.prepend(strip);
  const time = value => new Date(value).toLocaleTimeString(lang, { hour: '2-digit', minute: '2-digit' });
  const day = value => new Date(value).toLocaleDateString(lang, { weekday: 'short', day: 'numeric', month: 'short' });
  const span = ms => {
    const minutes = Math.max(0, Math.round(ms / 60000)), d = Math.floor(minutes / 1440), h = Math.floor(minutes % 1440 / 60), m = minutes % 60;
    return tr ? (d ? `${d} g ${h} sa` : h ? `${h} sa ${m} dk` : `${m} dk`) : (d ? `${d}d ${h}h` : h ? `${h}h ${m}m` : `${m}m`);
  };
  const charts = [];
  let windows = [], claudeUnlinked = false;

  function stateText(row) {
    if (['reset', 'stale', 'historical', 'ambiguous'].includes(row.state)) return [words[row.state], 'muted'];
    if (row.state === 'fills_before_reset') return [words.fills, 'warn'];
    if (row.state === 'full' || row.used_percent >= 100) return [words.full, 'warn'];
    if (row.state === 'lasts_until_reset') return [words.lasts, 'ok'];
    return [words[row.state] || words.stale, 'muted'];
  }

  function card(row) {
    const box = el('article', 'ws-gauge-card');
    const agent = row.agent === 'claude-code' ? 'Claude Code' : 'Codex', windowName = typeof usageWindow === 'function' ? usageWindow(row.window_minutes) : row.window_minutes + ' min';
    const head = el('div', 'ws-gauge-head'), title = el('div');
    // The window names the card; the agent is a small coloured tag, so two windows of one agent
    // do not read as the same card twice.
    const who = el('span', 'ws-gauge-agent');
    who.append(el('i', 'ws-swatch ws-swatch-' + (row.agent === 'claude-code' ? 'agent-claude' : 'agent-codex')), el('span', '', agent));
    title.append(el('strong', '', windowName + ' ' + words.limit), who);
    const [label, tone] = stateText(row);
    head.append(title, el('span', 'ws-gauge-state ' + tone, label));
    const gauge = el('div', 'ws-gauge');
    const used = !['reset', 'stale', 'historical', 'ambiguous'].includes(row.state) && Number.isFinite(row.used_percent) ? Math.round(row.used_percent * 10) / 10 : null;
    gauge.setAttribute('role', 'img');
    gauge.setAttribute('aria-label', used === null ? agent + ' ' + windowName + ': ' + label : words.gaugeLabel(agent, windowName, used.toLocaleString(lang)));
    const track = el('div', 'ws-track'), bar = el('div', 'ws-track-bar'), marks = el('div', 'ws-track-marks');
    track.append(bar, marks);
    const alert = el('p', 'ws-gauge-alert'); alert.hidden = true;
    const meta = el('p', 'ws-gauge-meta');
    box.append(head, gauge, track, alert, meta);
    return { box, row, gauge, bar, marks, alert, meta, used, tone };
  }

  // Claude Code keeps no quota percentage in its logs. Say so where its card would be, with the one
  // command that adds the source, instead of a paragraph further down the page.
  function unlinked() {
    const box = el('article', 'ws-gauge-card is-unlinked'), head = el('div', 'ws-gauge-head'), title = el('div'), who = el('span', 'ws-gauge-agent');
    who.append(el('i', 'ws-swatch ws-swatch-agent-claude'), el('span', '', 'Claude Code'));
    title.append(el('strong', '', words.unlinkedTitle), who);
    head.append(title, el('span', 'ws-gauge-state muted', words.unlinked));
    const body = el('div', 'ws-unlinked-body'), command = el('div', 'ws-unlinked-command'), code = el('code', '', 'pler statusline --install'), copy = el('button', '', words.copy);
    copy.type = 'button';
    copy.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(code.textContent); copy.textContent = words.copied; setTimeout(() => { copy.textContent = words.copy; }, 1600); }
      catch { const range = document.createRange(); range.selectNodeContents(code); const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range); }
    });
    command.append(code, copy);
    body.append(el('p', '', words.unlinkedWhy), command, el('p', 'is-muted', words.unlinkedDesktop));
    box.append(head, body);
    return box;
  }

  function paint(item, now = Date.now()) {
    const { row, bar, marks, meta } = item;
    const reset = Date.parse(row.resets_at), full = Date.parse(row.full_at), sample = Date.parse(row.at);
    bar.replaceChildren(); marks.replaceChildren();
    const lines = [];
    item.alert.hidden = true;
    if (item.used !== null && Number.isFinite(reset) && reset > now) {
      // The track is the time left until the reset; the warm part is the time it would be full.
      const fill = Number.isFinite(full) && full > now && full < reset && row.state === 'fills_before_reset' ? (full - now) / (reset - now) : null;
      const used = el('span', 'ws-track-fill');
      used.style.setProperty('--to', fill === null ? '100%' : (fill * 100).toFixed(1) + '%');
      bar.append(used);
      if (fill !== null) { const blocked = el('span', 'ws-track-blocked'); blocked.style.setProperty('--from', (fill * 100).toFixed(1) + '%'); bar.append(blocked); }
      const start = el('span', '', words.now), end = el('span', '', words.resetAt + ' ' + (reset - now > 864e5 ? day(reset) + ' ' : '') + time(reset));
      marks.append(start, end);
      item.alert.hidden = fill === null;
      if (fill !== null) {
        const tick = el('span', 'ws-track-tick'); tick.style.setProperty('--at', (fill * 100).toFixed(1) + '%'); bar.append(tick);
        item.alert.textContent = words.fillsAt + ' ~' + time(full) + ' (' + span(full - now) + ')';
      }
      lines.push(words.resetIn + ' ' + span(reset - now));
    }
    if (item.used !== null && Number.isFinite(row.percent_per_hour)) lines.push(words.pace + ' ' + (tr ? 'saatte %' : '') + row.percent_per_hour.toLocaleString(lang, { maximumFractionDigits: 1 }) + (tr ? '' : '%/hour'));
    else if (item.used !== null && Number.isFinite(row.percent_per_day)) lines.push(words.pace + ' ' + (tr ? 'günde %' : '') + row.percent_per_day.toLocaleString(lang, { maximumFractionDigits: 1 }) + (tr ? '' : '%/day'));
    if (Number.isFinite(sample)) lines.push(words.sampled + ' ' + span(now - sample) + ' ' + words.ago);
    meta.textContent = lines.join(' · ');
  }

  function draw() {
    for (const chart of charts.splice(0)) chart.dispose();
    const items = windows.map(row => card(current(row)));
    strip.replaceChildren(...items.map(item => item.box), ...(claudeUnlinked && items.length ? [unlinked()] : []));
    strip.hidden = !items.length;
    document.body.classList.toggle('has-unlinked-agent', claudeUnlinked && items.length > 0);
    document.body.classList.toggle('has-quota-gauges', items.length > 0);
    const animation = !matchMedia('(prefers-reduced-motion: reduce)').matches;
    for (const item of items) {
      const chart = init(item.gauge, null, { renderer: 'canvas' });
      const color = item.tone === 'warn' ? token('warning') : item.tone === 'ok' ? token('text') : token('muted');
      chart.setOption({
        animation, animationDuration: 900, animationEasing: 'cubicOut',
        series: [{
          type: 'gauge', startAngle: 210, endAngle: -30, min: 0, max: 100, radius: '96%', center: ['50%', '58%'],
          progress: { show: item.used !== null, roundCap: true, width: 10, itemStyle: { color } },
          axisLine: { roundCap: true, lineStyle: { width: 10, color: [[1, token('raised')]] } },
          pointer: { show: false }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false }, anchor: { show: false },
          title: { show: true, offsetCenter: [0, '34%'], color: token('muted'), fontSize: 12, fontFamily: 'Segoe UI' },
          detail: { valueAnimation: animation, offsetCenter: [0, '-2%'], color: token('text'), fontSize: 28, fontWeight: 600, fontFamily: 'Segoe UI',
            formatter: value => item.used === null ? '—' : (tr ? '%' : '') + Number(value).toLocaleString(lang, { maximumFractionDigits: 1 }) + (tr ? '' : '%') },
          data: [{ value: item.used ?? 0, name: item.used === null ? '' : words.used }]
        }]
      });
      charts.push(chart);
      paint(item);
    }
    draw.items = items;
  }

  const current = row => typeof quotaWindowNow === 'function' ? quotaWindowNow(row) : row;
  function refreshClock() {
    if (strip.hidden || document.body.dataset.screen !== 'quota') return;
    if (windows.some((row, index) => current(row).state !== draw.items?.[index]?.row.state)) draw();
    else for (const item of draw.items || []) paint(item);
  }
  setInterval(refreshClock, 30000);
  new ResizeObserver(() => charts.forEach(chart => chart.resize())).observe(strip);

  // Notes become an ⓘ beside the section heading. The text is unchanged; it waits one click away.
  function tuck(section) {
    if (!section || section.querySelector(':scope > h2 .ws-info-host')) return;
    const heading = section.querySelector(':scope > h2'), notes = [...section.querySelectorAll(':scope > p.section-note')];
    if (!heading || !notes.length) return;
    const host = el('span', 'ws-info-host');
    heading.append(host);
    notes.forEach(note => note.remove());
    createRoot(host).render(<InfoTip label={words.info} nodes={notes} />);
  }

  return {
    update(data) {
      const outlook = data?.outlook || [], codex = outlook.filter(row => row.agent !== 'claude-code'), claude = outlook.filter(row => row.agent === 'claude-code');
      const rows = [...(codex.length ? codex : data?.quota?.latest || []), ...claude];
      windows = rows;
      claudeUnlinked = data?.claude_statusline === false && !claude.length && !rows.some(row => row.agent === 'claude-code');
      draw();
      for (const id of ['usage-quota', 'usage-plans', 'usage-mix']) tuck(document.getElementById(id));
    },
    resize() { refreshClock(); charts.forEach(chart => chart.resize()); }
  };
}
