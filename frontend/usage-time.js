// Usage over time: the dated responses PLER already counts, by local day and by hour of the week.
// The engine sends UTC hours (usage/timeline.py); grouping into the viewer's own days happens here.
// Sums always equal the dated total; whole-session totals are never spread over time.
import { init, use } from 'echarts/core';
import { BarChart, HeatmapChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, AriaComponent, VisualMapComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { mountSegments } from './primitives.jsx';

use([BarChart, HeatmapChart, GridComponent, TooltipComponent, AriaComponent, VisualMapComponent, CanvasRenderer]);

const AGENTS = [['claude-code', 'Claude Code', 'agent-claude'], ['codex', 'Codex', 'agent-codex']];

function el(tag, cls, text) { const node = document.createElement(tag); if (cls) node.className = cls; if (text) node.textContent = text; return node; }
const pad = n => String(n).padStart(2, '0');
const dayKey = date => date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate());
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

// Odometer after motion-primitives' SlidingNumber: each digit is a 0-9 reel moved by a CSS variable,
// so it works under the app's strict style-src policy. The text itself stays readable to assistive tech.
function odometer(host) {
  let shape = '';
  return text => {
    if (shape !== text.replace(/\d/g, '0')) {
      shape = text.replace(/\d/g, '0');
      const spoken = el('span', 'sr-only'), reels = el('span', 'ws-odometer');
      reels.setAttribute('aria-hidden', 'true');
      for (const char of text) {
        if (!/\d/.test(char)) { reels.append(el('span', 'ws-odometer-sep', char)); continue; }
        const digit = el('span', 'ws-digit'), reel = el('span', 'ws-reel');
        for (let n = 0; n < 10; n++) reel.append(el('span', '', String(n)));
        digit.append(reel); reels.append(digit);
      }
      host.replaceChildren(spoken, reels);
    }
    host.firstChild.textContent = text;
    let index = 0;
    const reels = host.querySelectorAll('.ws-reel');
    for (const char of text) if (/\d/.test(char)) reels[index++].style.setProperty('--d', char);
  };
}

export function mountUsageTime({ tr, before }) {
  const lang = tr ? 'tr-TR' : 'en-US';
  const words = tr ? {
    title: 'Zaman içinde kullanım', note: 'Zamanı kayıtlı yanıtlar, senin saatine göre. Bir güne gel, o günü gör.',
    tokens: 'Token', calls: 'Çağrı', period: 'Seçili dönem', unitTokens: 'token', unitCalls: 'çağrı',
    callsLabel: 'Model çağrısı', busiest: 'En yoğun gün', active: 'Aktif gün', none: '—',
    rhythm: 'Ne zaman çalışıyorsun?', rhythmNote: 'Haftanın günü ve saatine göre toplam. Koyu: az, açık: çok.',
    empty: 'Bu dönemde zamanı kayıtlı yanıt yok.', chart: 'Günlere göre kayıtlı kullanım, ajanlara ayrılmış',
    heat: 'Haftanın günü ve saatine göre kayıtlı kullanım',
    partial: n => `Grafik yalnız zamanı kayıtlı yanıtları gösterir. ${n} oturumun kullanımının bir kısmı bir zamana bağlanamadı; bu yüzden toplam karttaki değerden küçük olabilir.`,
    days: ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
  } : {
    title: 'Usage over time', note: 'Responses with a recorded time, in your local time. Point at a day to see it.',
    tokens: 'Tokens', calls: 'Calls', period: 'Selected period', unitTokens: 'tokens', unitCalls: 'calls',
    callsLabel: 'Model calls', busiest: 'Busiest day', active: 'Active days', none: '—',
    rhythm: 'When do you work?', rhythmNote: 'Totals by weekday and hour. Dark: little, light: a lot.',
    empty: 'No responses with a recorded time in this period.', chart: 'Recorded usage by day, split by agent',
    heat: 'Recorded usage by weekday and hour',
    partial: n => `The chart shows only responses with a recorded time. Part of the usage of ${n} ${n === '1' ? 'session' : 'sessions'} could not be placed in time, so it can be lower than the total above.`,
    days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  };
  const number = value => Number(value).toLocaleString(lang);
  const compact = value => value >= 1e6 ? (value / 1e6).toLocaleString(lang, { maximumFractionDigits: 1 }) + 'M' : value >= 1e3 ? Math.round(value / 1e3).toLocaleString(lang) + 'k' : String(value);
  const dateLabel = (key, long) => new Date(key + 'T12:00:00').toLocaleDateString(lang, long ? { weekday: 'short', day: 'numeric', month: 'short' } : { day: 'numeric', month: 'short' });

  const card = el('section', 'ws-time usage-panel');
  const head = el('div', 'ws-chart-heading'), headText = el('div');
  headText.append(el('h2', '', words.title), el('p', 'section-note', words.note));
  const metricHost = el('div', 'wb-segmented ws-time-metric');
  metricHost.setAttribute('role', 'group'); metricHost.setAttribute('aria-label', words.title);
  head.append(headText, metricHost);
  const stats = el('div', 'ws-time-stats');
  const stat = (label) => { const box = el('div', 'ws-time-stat'), small = el('small', '', label), strong = el('strong'), unit = el('span'); box.append(small, strong, unit); stats.append(box); return { small, strong, unit }; };
  const main = stat(words.period), callStat = stat(words.callsLabel), busiest = stat(words.busiest), active = stat(words.active);
  const showMain = odometer(main.strong), showCalls = odometer(callStat.strong);
  const chartNode = el('div', 'ws-time-chart'); chartNode.setAttribute('role', 'img'); chartNode.setAttribute('aria-label', words.chart);
  const legend = el('div', 'ws-time-legend');
  for (const [, name, token] of AGENTS) { const item = el('span', 'ws-legend-item'); item.append(el('i', 'ws-swatch ws-swatch-' + token), document.createTextNode(name)); legend.append(item); }
  const empty = el('p', 'ws-time-empty', words.empty);
  const rhythm = el('div', 'ws-rhythm'), rhythmText = el('div');
  rhythmText.append(el('h3', '', words.rhythm), el('p', 'section-note', words.rhythmNote));
  const heatNode = el('div', 'ws-rhythm-chart'); heatNode.setAttribute('role', 'img'); heatNode.setAttribute('aria-label', words.heat);
  rhythm.append(rhythmText, heatNode);
  const coverage = el('p', 'section-note ws-time-coverage'); coverage.hidden = true;
  card.append(head, stats, chartNode, legend, empty, rhythm, coverage);
  before.before(card);

  let metric = 'tokens', series = null, bars = null, heat = null, focusDay = null;
  mountSegments(metricHost, [['tokens', words.tokens], ['calls', words.calls]], metric, value => { metric = value; draw(); });

  const token = name => getComputedStyle(document.body).getPropertyValue('--ui-' + name).trim();

  function group(data) {
    const rows = data?.timeline?.rows || [];
    const cutoff = new Date(data?.dated_usage?.cutoff || Date.now());
    const days = data?.filters?.days || 0;
    const perDay = new Map(), grid = Array.from({ length: 7 }, () => Array(24).fill(0)), gridCalls = Array.from({ length: 7 }, () => Array(24).fill(0));
    let first = null;
    for (const [hour, agent, tokens, calls] of rows) {
      const at = new Date(hour), key = dayKey(at);
      if (!first || at < first) first = at;
      const day = perDay.get(key) || { 'claude-code': [0, 0], codex: [0, 0], unknown: [0, 0] };
      (day[agent] || day.unknown)[0] += tokens; (day[agent] || day.unknown)[1] += calls; perDay.set(key, day);
      const weekday = (at.getDay() + 6) % 7;
      grid[weekday][at.getHours()] += tokens; gridCalls[weekday][at.getHours()] += calls;
    }
    const end = new Date(cutoff.getFullYear(), cutoff.getMonth(), cutoff.getDate());
    // A rolling N-day interval can touch N+1 local dates. Keep both partial boundary days.
    const since = data?.dated_usage?.since ? new Date(data.dated_usage.since) : days ? new Date(cutoff.getTime() - days * 864e5) : first || end;
    let start = new Date(since.getFullYear(), since.getMonth(), since.getDate());
    // Hour buckets are rounded down on the server; never discard a retained boundary bucket.
    if (first && first < start) start = new Date(first.getFullYear(), first.getMonth(), first.getDate());
    if (start > end) start = end;
    const keys = [];
    for (let at = start; at <= end; at = new Date(at.getFullYear(), at.getMonth(), at.getDate() + 1)) keys.push(dayKey(at));
    return { keys, perDay, grid, gridCalls, rows };
  }

  function summary(dayValues) {
    const index = metric === 'tokens' ? 0 : 1;
    let tokens = 0, calls = 0, best = null, activeDays = 0;
    for (const [key, day] of dayValues) {
      const t = day['claude-code'][0] + day.codex[0] + day.unknown[0], c = day['claude-code'][1] + day.codex[1] + day.unknown[1];
      tokens += t; calls += c; if (t || c) activeDays++;
      const value = index ? c : t;
      if (value && (!best || value > best.value)) best = { key, value };
    }
    return { tokens, calls, best, activeDays };
  }

  function showStats(label, tokens, calls) {
    main.small.textContent = label;
    showMain(number(metric === 'tokens' ? tokens : calls)); main.unit.textContent = metric === 'tokens' ? words.unitTokens : words.unitCalls;
    showCalls(number(metric === 'tokens' ? calls : tokens)); callStat.small.textContent = metric === 'tokens' ? words.callsLabel : words.tokens;
    callStat.unit.textContent = metric === 'tokens' ? words.unitCalls : words.unitTokens;
  }

  function draw() {
    if (!series) return;
    const { keys, perDay, grid, gridCalls, rows } = series;
    const index = metric === 'tokens' ? 0 : 1, values = keys.map(key => [key, perDay.get(key)]).filter(([, day]) => day);
    const total = summary(values);
    focusDay = null;
    showStats(words.period, total.tokens, total.calls);
    busiest.strong.textContent = total.best ? dateLabel(total.best.key, true) : words.none;
    busiest.unit.textContent = total.best ? (metric === 'tokens' ? compact(total.best.value) + ' ' + words.unitTokens : number(total.best.value) + ' ' + words.unitCalls) : '';
    active.strong.textContent = number(total.activeDays) + ' / ' + number(keys.length);
    active.unit.textContent = '';
    const hasRows = rows.length > 0;
    empty.hidden = hasRows; chartNode.hidden = !hasRows; legend.hidden = !hasRows; rhythm.hidden = !hasRows;
    if (!hasRows) return;
    const animation = !reduced(), muted = token('muted'), border = token('border');
    const text = { color: muted, fontFamily: 'Segoe UI', fontSize: 12 };
    bars = bars || init(chartNode, null, { renderer: 'canvas' });
    bars.setOption({
      animation, animationDuration: 500, animationEasing: 'cubicOut', aria: { enabled: true },
      grid: { left: 4, right: 8, top: 10, bottom: 4, containLabel: true },
      // richText tooltips draw on the canvas: no inline style attributes, so the strict style-src policy holds.
      tooltip: { trigger: 'axis', renderMode: 'richText', axisPointer: { type: 'shadow', shadowStyle: { color: token('highlight') } }, backgroundColor: token('raised'), borderColor: token('border-strong'), textStyle: { color: token('text'), fontSize: 12 },
        formatter: items => { const key = keys[items[0].dataIndex]; const lines = items.filter(item => item.value).map(item => item.marker + item.seriesName + '  ' + (index ? number(item.value) + ' ' + words.unitCalls : number(item.value) + ' ' + words.unitTokens)); return dateLabel(key, true) + '\n' + (lines.length ? lines.join('\n') : words.none); } },
      xAxis: { type: 'category', data: keys.map(key => dateLabel(key)), axisLine: { lineStyle: { color: border } }, axisTick: { show: false }, axisLabel: { ...text, hideOverlap: true } },
      yAxis: { type: 'value', splitNumber: 3, axisLabel: { ...text, formatter: value => index ? value : compact(value) }, splitLine: { lineStyle: { color: border } } },
      series: AGENTS.map(([agent, name, color], i) => ({ name, type: 'bar', stack: 'day', barMaxWidth: 22, emphasis: { focus: 'series' },
        itemStyle: { color: token(color), borderRadius: i === AGENTS.length - 1 ? [3, 3, 0, 0] : 0 },
        data: keys.map(key => perDay.get(key)?.[agent][index] || 0) }))
    }, true);
    heat = heat || init(heatNode, null, { renderer: 'canvas' });
    const source = index ? gridCalls : grid, cells = [];
    let max = 0;
    source.forEach((hours, day) => hours.forEach((value, hour) => { cells.push([hour, day, value || '-']); max = Math.max(max, value); }));
    heat.setOption({
      animation, aria: { enabled: true },
      grid: { left: 4, right: 8, top: 4, bottom: 4, containLabel: true },
      tooltip: { renderMode: 'richText', backgroundColor: token('raised'), borderColor: token('border-strong'), textStyle: { color: token('text'), fontSize: 12 },
        formatter: item => words.days[item.value[1]] + ' ' + pad(item.value[0]) + ':00  ' + (item.value[2] === '-' ? words.none : (index ? number(item.value[2]) + ' ' + words.unitCalls : number(item.value[2]) + ' ' + words.unitTokens)) },
      xAxis: { type: 'category', data: Array.from({ length: 24 }, (_, h) => pad(h)), splitArea: { show: false }, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { ...text, interval: 2 } },
      yAxis: { type: 'category', data: words.days, inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: text },
      visualMap: { show: false, min: 0, max: Math.max(1, max), inRange: { color: [token('heat-1'), token('heat-2'), token('heat-3'), token('heat-4'), token('heat-5')] } },
      series: [{ type: 'heatmap', data: cells, itemStyle: { borderColor: token('surface'), borderWidth: 2, borderRadius: 3 }, emphasis: { itemStyle: { borderColor: token('text'), borderWidth: 1 } } }]
    }, true);
  }

  function update(data) {
    if (!data?.has_snapshot || !data.timeline) { card.hidden = true; return; }
    card.hidden = false;
    series = group(data);
    const partial = data.dated_usage?.unallocated_sessions || 0;
    coverage.hidden = !partial; coverage.textContent = partial ? words.partial(number(partial)) : '';
    draw();
    requestAnimationFrame(() => { bars?.resize(); heat?.resize(); });
  }

  // Hovering a day shows that day in the stat row; leaving the chart returns to the period.
  chartNode.addEventListener('pointerleave', () => { if (focusDay !== null) draw(); });
  const hover = () => bars?.on('updateAxisPointer', event => {
    const axis = event.axesInfo?.[0]; if (!axis || !series) return;
    const key = series.keys[axis.value]; if (key === undefined || key === focusDay) return;
    focusDay = key; const day = series.perDay.get(key);
    const tokens = day ? day['claude-code'][0] + day.codex[0] + day.unknown[0] : 0, calls = day ? day['claude-code'][1] + day.codex[1] + day.unknown[1] : 0;
    showStats(dateLabel(key, true), tokens, calls);
  });
  new ResizeObserver(() => { bars?.resize(); heat?.resize(); }).observe(card);

  // A small trend line in the first total card: the same daily totals, no axis, no extra claim.
  function sparkline(container) {
    const host = container?.querySelector('.usage-stat');
    if (!host || !series) return;
    host.querySelector('.ws-spark')?.remove();
    const values = series.keys.map(key => { const day = series.perDay.get(key); return day ? day['claude-code'][0] + day.codex[0] + day.unknown[0] : 0; });
    if (values.length < 2 || !values.some(Boolean)) return;
    const max = Math.max(...values), ns = 'http://www.w3.org/2000/svg', svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('class', 'ws-spark'); svg.setAttribute('viewBox', '0 0 100 24'); svg.setAttribute('preserveAspectRatio', 'none'); svg.setAttribute('aria-hidden', 'true');
    const points = values.map((value, i) => [(i / (values.length - 1)) * 100, 22 - (value / max) * 20]);
    const line = points.map(([x, y], i) => (i ? 'L' : 'M') + x.toFixed(2) + ' ' + y.toFixed(2)).join('');
    const area = document.createElementNS(ns, 'path'); area.setAttribute('class', 'ws-spark-area'); area.setAttribute('d', line + 'L100 24L0 24Z');
    const path = document.createElementNS(ns, 'path'); path.setAttribute('class', 'ws-spark-line'); path.setAttribute('d', line); path.setAttribute('vector-effect', 'non-scaling-stroke');
    svg.append(area, path); host.append(svg);
  }

  let hooked = false;
  return {
    update(data, totals) { update(data); if (!hooked && bars) { hover(); hooked = true; } sparkline(totals); },
    resize() { bars?.resize(); heat?.resize(); }
  };
}
