'use strict';
// Remembered window size, position, maximized state, interface language, bounded view preferences and whether the first-run
// tour was seen. Nothing else is kept:
// filter enums, an opaque project ID and column geometry. A damaged or foreign value is ignored.
const fs = require('node:fs');
const path = require('node:path');
const { normalizeView } = require('./view-preferences.cjs');

const DEFAULTS = { width: 1240, height: 850 };
const LIMITS = { minWidth: 420, minHeight: 480, max: 20000 };

function whole(value, low, high) { return Number.isSafeInteger(value) && value >= low && value <= high; }

// Keep a position only when at least 120x80 of the window lands on a current display's work area.
function visible(bounds, workAreas) {
  return workAreas.some(area => {
    const width = Math.min(bounds.x + bounds.width, area.x + area.width) - Math.max(bounds.x, area.x);
    const height = Math.min(bounds.y + bounds.height, area.y + area.height) - Math.max(bounds.y, area.y);
    return width >= 120 && height >= 80;
  });
}

function restore(raw, workAreas) {
  const result = { ...DEFAULTS, maximized: false, lang: null, tour: false };
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return result;
  if (whole(raw.width, LIMITS.minWidth, LIMITS.max) && whole(raw.height, LIMITS.minHeight, LIMITS.max)) {
    result.width = raw.width; result.height = raw.height;
    if (whole(raw.x, -LIMITS.max, LIMITS.max) && whole(raw.y, -LIMITS.max, LIMITS.max)
        && visible({ x: raw.x, y: raw.y, width: raw.width, height: raw.height }, workAreas)) {
      result.x = raw.x; result.y = raw.y;
    }
  }
  result.maximized = raw.maximized === true;
  if (raw.lang === 'en' || raw.lang === 'tr') result.lang = raw.lang;
  result.tour = raw.tour === true;
  if (raw.view && typeof raw.view === 'object' && !Array.isArray(raw.view)) result.view = normalizeView(raw.view);
  return result;
}

function read(file, workAreas) {
  try {
    if (!file || fs.statSync(file).size > 4096) return restore(null, workAreas);
    return restore(JSON.parse(fs.readFileSync(file, 'utf8')), workAreas);
  } catch { return restore(null, workAreas); }
}

function write(file, bounds, maximized, lang, tour = false, view) {
  if (!file) return false;
  const value = { x: Math.round(bounds.x), y: Math.round(bounds.y), width: Math.round(bounds.width),
    height: Math.round(bounds.height), maximized: Boolean(maximized), ...(lang === 'en' || lang === 'tr' ? { lang } : {}), tour: tour === true, ...(view && typeof view === 'object' ? {view: normalizeView(view)} : {}) };
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    const temporary = file + '.tmp';
    fs.writeFileSync(temporary, JSON.stringify(value));
    fs.renameSync(temporary, file);
    return true;
  } catch { return false; }
}

module.exports = { restore, read, write, visible, DEFAULTS, LIMITS };
