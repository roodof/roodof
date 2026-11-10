// Usage over time: the dated responses PLER already counts, by local day and by hour of the week.
// The engine sends UTC hours (usage/timeline.py); grouping into the viewer's own days happens here.
// Sums always equal the dated total; whole-session totals are never spread over time.
import { init, use } from 'echarts/core';
import { BarChart, HeatmapChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, AriaComponent, VisualMapComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { mountSegments } from './primitives.jsx';

use([BarChart, HeatmapChart, GridComponent, TooltipComponent, AriaComponent, VisualMapComponent, CanvasRenderer]);

const AGENTS = [['claude-code', 'Claude Code', 'agent-claude'], ['codex', 'Codex', 'agent-codex'], ['unknown', 'Unknown agent', 'muted']];

function el(tag, cls, text) { const node = document.createElement(tag); if (cls) node.className = cls; if (text) node.textContent = text; return node; }
const pad = n => String(n).padStart(2, '0');
const dayKey = date => date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate());
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

// Commit the exact value immediately; animate its surface, never intermediate counts.
// Switching metric or period slides the new value in; pointing at days swaps it at once.
function metricNumber(host) {
  let previous = '', animation;
  return (text, instant) => {
    if (text === previous) return;
    animation?.cancel();
    host.textContent = text;
    if (previous && !instant && !reduced()) animation = host.animate(
      [{ opacity: 0, transform: 'translateY(9px)' }, { opacity: 1, transform: 'translateY(0)' }],
      { duration: 320, easing: 'cubic-bezier(.22,1,.36,1)' }
    );
    previous = text;
  };
}

export function mountUsageTime({ tr, before }) {
  const lang = tr ? 'tr-TR' : 'en-US';
  const words = tr ? {
    title: 'Zaman içinde kullanım', note: 'Zamanı kayıtlı yanıtlar, senin saatine göre. Bir güne gel, o günü gör; tıkla, sabitle.',
    tokens: 'Token', calls: 'Çağrı', period: 'Seçili dönem', unitTokens: 'token', unitCalls: 'çağrı',
    average: 'Aktif gün ortalaması', share: 'Dönemdeki payı', perDay: 'günde', pinned: 'sabitlendi · bırakmak için tıkla', busiest: 'En yoğun gün', active: 'Aktif gün', none: '—',
    rhythm: 'Ne zaman çalışıyorsun?', rhythmNote: 'Haftanın günü ve saatine göre toplam. Koyu: az, açık: çok.',
    empty: 'Bu dönemde zamanı kayıtlı yanıt yok.', chart: 'Günlere göre kayıtlı kullanım, ajanlara ayrılmış',
    heat: 'Haftanın günü ve saatine göre kayıtlı kullanım',
    partial: n => `Grafik yalnız zamanı kayıtlı yanıtları gösterir. ${n} oturumun kullanımının bir kısmı bir zamana bağlanamadı; bu yüzden toplam karttaki değerden küçük olabilir.`,
    days: ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
  } : {
    title: 'Usage over time', note: 'Responses with a recorded time, in your local time. Point at a day to see it; click to pin it.',
    tokens: 'Tokens', calls: 'Calls', period: 'Selected period', unitTokens: 'tokens', unitCalls: 'calls',
    average: 'Average per active day', share: 'Share of the period', perDay: 'a day', pinned: 'pinned · click to release', busiest: 'Busiest day', active: 'Active days', none: '—',
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
  const main = stat(words.period), callStat = stat(words.average), busiest = stat(words.busiest), active = stat(words.active);
  const showMain = metricNumber(main.strong), showCalls = metricNumber(callStat.strong);
  const chartNode = el('div', 'ws-time-chart'); chartNode.setAttribute('role', 'img'); chartNode.setAttribute('aria-label', words.chart);
  const legend = el('div', 'ws-time-legend');
  const legendItems = new Map();
  for (const [agent, name, token] of AGENTS) { const item = el('span', 'ws-legend-item'); item.append(el('i', 'ws-swatch ws-swatch-' + token), document.createTextNode(agent === 'unknown' && tr ? 'Bilinmeyen ajan' : name)); legend.append(item); legendItems.set(agent, item); }
  const empty = el('p', 'ws-time-empty', words.empty);
  const rhythm = el('div', 'ws-rhythm'), rhythmText = el('div');
  rhythmText.append(el('h3', '', words.rhythm), el('p', 'section-note', words.rhythmNote));
  const heatNode = el('div', 'ws-rhythm-chart'); heatNode.setAttribute('role', 'img'); heatNode.setAttribute('aria-label', words.heat);
  rhythm.append(rhythmText, heatNode);
  const coverage = el('p', 'section-note ws-time-coverage'); coverage.hidden = true;
  card.append(head, stats, chartNode, legend, empty, rhythm, coverage);
  before.before(card);

  let metric = 'tokens', series = null, bars = null, heat = null, focusDay = null, pinned = null;
  card.dataset.metric = metric;
  const metricControl = mountSegments(metricHost, [['tokens', words.tokens], ['calls', words.calls]], metric, value => {
    if (value === metric) return;
    metric = value; metricControl.setValue(value); card.dataset.metric = value;
    bars?.dispatchAction({ type: 'hideTip' }); heat?.dispatchAction({ type: 'hideTip' });
    draw();
  });

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

  function showStats(label, tokens, calls, period) {
    const value = metric === 'tokens' ? tokens : calls, unit = metric === 'tokens' ? words.unitTokens : words.unitCalls, day = focusDay !== null;
    main.small.textContent = label;
    showMain(number(value), day); main.unit.textContent = unit;
    if (day) {
      const whole = period ? (metric === 'tokens' ? period.tokens : period.calls) : 0;
      callStat.small.textContent = words.share;
      showCalls(whole ? (value / whole).toLocaleString(lang, { style: 'percent', maximumFractionDigits: 1 }) : words.none, true);
      callStat.unit.textContent = '';
    } else {
      const days = period?.activeDays || 0;
      callStat.small.textContent = words.average;
      showCalls(days ? (metric === 'tokens' ? compact(Math.round(value / days)) : (value / days).toLocaleString(lang, { maximumFractionDigits: 1 })) : words.none);
      callStat.unit.textContent = days ? unit + ' · ' + words.perDay : '';
    }
  }

  function draw() {
    if (!series) return;
    const { keys, perDay, grid, gridCalls, rows } = series;
    const index = metric === 'tokens' ? 0 : 1, values = keys.map(key => [key, perDay.get(key)]).filter(([, day]) => day);
    const total = summary(values);
    if (pinned !== null) bars?.dispatchAction({ type: 'downplay' });
    focusDay = null; pinned = null;
    showStats(words.period, total.tokens, total.calls, total);
    busiest.strong.textContent = total.best ? dateLabel(total.best.key, true) : words.none;
    busiest.unit.textContent = total.best ? (metric === 'tokens' ? compact(total.best.value) + ' ' + words.unitTokens : number(total.best.value) + ' ' + words.unitCalls) : '';
    active.strong.textContent = number(total.activeDays) + ' / ' + number(keys.length);
    active.unit.textContent = '';
    const hasRows = rows.length > 0;
    empty.hidden = hasRows; chartNode.hidden = !hasRows; legend.hidden = !hasRows; rhythm.hidden = !hasRows;
    if (!hasRows) return;
    for (const [agent, item] of legendItems) item.hidden = agent === 'unknown' && !values.some(([, day]) => day.unknown[index]);
    const animation = !reduced(), muted = token('muted'), border = token('border');
    const text = { color: muted, fontFamily: 'Segoe UI', fontSize: 12 };
    bars = bars || init(chartNode, null, { renderer: 'canvas' });
    bars.setOption({
      animation, animationDuration: 620, animationDurationUpdate: 420, animationEasing: 'cubicOut', animationEasingUpdate: 'cubicOut', aria: { enabled: true },
      grid: { left: 4, right: 8, top: 10, bottom: 4, containLabel: true },
      // richText tooltips draw on the canvas: no inline style attributes, so the strict style-src policy holds.
      tooltip: { trigger: 'axis', renderMode: 'richText', axisPointer: { type: 'shadow', shadowStyle: { color: token('highlight') } }, backgroundColor: token('raised'), borderColor: token('border-strong'), textStyle: { color: token('text'), fontSize: 12 },
        formatter: items => { const key = keys[items[0].dataIndex]; const lines = items.filter(item => item.value).map(item => item.marker + item.seriesName + '  ' + (index ? number(item.value) + ' ' + words.unitCalls : number(item.value) + ' ' + words.unitTokens)); return dateLabel(key, true) + '\n' + (lines.length ? lines.join('\n') : words.none); } },
      xAxis: { type: 'category', data: keys.map(key => dateLabel(key)), axisLine: { lineStyle: { color: border } }, axisTick: { show: false }, axisLabel: { ...text, hideOverlap: true } },
      yAxis: { type: 'value', minInterval: index ? 1 : 0, splitNumber: 3, axisLabel: { ...text, formatter: value => index ? number(value) : compact(value) }, splitLine: { lineStyle: { color: border } } },
      series: AGENTS.map(([agent, name, color]) => ({ id: agent, name: agent === 'unknown' && tr ? 'Bilinmeyen ajan' : name, type: 'bar', stack: 'day', barMaxWidth: 22, emphasis: { focus: 'series' }, animationDelay: at => Math.min(at * 14, 140),
        // Calls use their own cool colours, so the two views cannot be mistaken for each other.
        itemStyle: { color: token(index ? color.replace('agent-', 'calls-') : color), borderRadius: 2 },
        data: keys.map(key => perDay.get(key)?.[agent][index] || 0) }))
    });
    heat = heat || init(heatNode, null, { renderer: 'canvas' });
    const source = index ? gridCalls : grid, cells = [];
    let max = 0;
    source.forEach((hours, day) => hours.forEach((value, hour) => { cells.push([hour, day, value || '-']); max = Math.max(max, value); }));
    heat.setOption({
      animation, animationDuration: 520, animationDurationUpdate: 420, animationEasingUpdate: 'cubicOut', aria: { enabled: true },
      grid: { left: 4, right: 8, top: 4, bottom: 4, containLabel: true },
      tooltip: { renderMode: 'richText', backgroundColor: token('raised'), borderColor: token('border-strong'), textStyle: { color: token('text'), fontSize: 12 },
        formatter: item => words.days[item.value[1]] + ' ' + pad(item.value[0]) + ':00  ' + (item.value[2] === '-' ? words.none : (index ? number(item.value[2]) + ' ' + words.unitCalls : number(item.value[2]) + ' ' + words.unitTokens)) },
      xAxis: { type: 'category', data: Array.from({ length: 24 }, (_, h) => pad(h)), splitArea: { show: false }, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { ...text, interval: 2 } },
      yAxis: { type: 'category', data: words.days, inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: text },
      visualMap: { show: false, min: 0, max: Math.max(1, max), inRange: { color: [1, 2, 3, 4, 5].map(step => token((index ? 'calls-heat-' : 'heat-') + step)) } },
      series: [{ id: 'weekly-rhythm', type: 'heatmap', data: cells, itemStyle: { borderColor: token('surface'), borderWidth: 2, borderRadius: 3 }, emphasis: { itemStyle: { borderColor: token('text'), borderWidth: 1 } } }]
    });
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
  const period = () => summary(series.keys.map(key => [key, series.perDay.get(key)]).filter(([, day]) => day));
  function showPeriod() {
    focusDay = null;
    const total = period();
    showStats(words.period, total.tokens, total.calls, total);
  }
  function showDay(key) {
    focusDay = key; const day = series.perDay.get(key);
    const tokens = day ? day['claude-code'][0] + day.codex[0] + day.unknown[0] : 0, calls = day ? day['claude-code'][1] + day.codex[1] + day.unknown[1] : 0;
    showStats(dateLabel(key, true) + (pinned === key ? ' · ' + words.pinned : ''), tokens, calls, period());
  }
  function mark(key, on) {
    const dataIndex = series.keys.indexOf(key);
    if (dataIndex >= 0) bars?.dispatchAction({ type: on ? 'highlight' : 'downplay', dataIndex });
  }
  chartNode.addEventListener('pointerleave', () => {
    if (!series) return;
    bars?.dispatchAction({ type: 'hideTip' });
    if (pinned !== null) { if (focusDay !== pinned) showDay(pinned); mark(pinned, true); }
    else if (focusDay !== null) showPeriod();
  });
  const hover = () => {
    bars?.on('updateAxisPointer', event => {
      const axis = event.axesInfo?.[0]; if (!axis || !series) return;
      const key = series.keys[axis.value]; if (key === undefined || key === focusDay) return;
      showDay(key);
    });
    // A click keeps one day in the figures above until it is clicked again or another day is chosen.
    bars?.getZr().on('click', event => {
      if (!series || !bars.containPixel('grid', [event.offsetX, event.offsetY])) return;
      const key = series.keys[bars.convertFromPixel({ xAxisIndex: 0 }, event.offsetX)];
      if (key === undefined) return;
      if (pinned !== null) mark(pinned, false);
      pinned = pinned === key ? null : key;
      if (pinned !== null) mark(pinned, true);
      focusDay = null; showDay(key);
    });
  };
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
