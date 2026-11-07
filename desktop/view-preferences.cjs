'use strict';
const SCREENS = ['sessions', 'work', 'overview', 'quota', 'settings'];
const FIELDS = ['project', 'tokens', 'status', 'verdict', 'agent', 'ended', 'models', 'calls', 'id'];
const object = value => value && typeof value === 'object' && !Array.isArray(value);
function normalizeView(raw) {
  raw = object(raw) ? raw : {};
  const filters = object(raw.filters) ? raw.filters : {};
  const seen = new Set(), columns = [];
  if (Array.isArray(raw.columns) && raw.columns.length <= FIELDS.length) {
    for (const column of raw.columns) {
      if (!object(column) || !FIELDS.includes(column.field) || seen.has(column.field)) continue;
      seen.add(column.field);
      const value = {field: column.field, visible: column.field === 'project' || column.visible !== false};
      if (Number.isFinite(column.width) && column.width >= 80 && column.width <= 1000) value.width = Math.round(column.width);
      columns.push(value);
    }
  }
  return {
    screen: SCREENS.includes(raw.screen) ? raw.screen : 'sessions',
    filters: {
      days: ['0','7','30','90'].includes(filters.days) ? filters.days : '30',
      agent: ['all','claude-code','codex'].includes(filters.agent) ? filters.agent : 'all',
      project: typeof filters.project === 'string' && /^(all|[a-f0-9]{24})$/.test(filters.project) ? filters.project : 'all',
      sort: ['recent','started','tokens','issues'].includes(filters.sort) ? filters.sort : 'recent',
      quality: filters.quality === true
    },
    columns
  };
}
module.exports = {normalizeView};
