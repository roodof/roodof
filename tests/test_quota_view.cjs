'use strict';
// Exercise the actual clock helper shipped to the browser, without changing the page clock or adding a dependency.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test');
const source=fs.readFileSync(require('node:path').join(__dirname,'../src/pler/web/app.js'),'utf8');
const start=source.indexOf('function quotaWindowNow('),end=source.indexOf('function usageOutlookText(',start);
assert(start>=0&&end>start);
const context=vm.createContext({});vm.runInContext(source.slice(start,end),context);
const now=Date.parse('2026-10-26T12:00:00Z');
const base={at:'2026-10-26T11:50:00Z',resets_at:'2026-10-26T15:00:00Z',window_minutes:300,used_percent:30,state:'no_pace',max_age_seconds:1800};
const read=(row,time=now)=>context.quotaWindowNow(row,time);
test('fresh snapshot remains usable and is never mutated',()=>{const input={...base};assert.equal(read(input).state,'no_pace');assert.deepEqual(input,base);});
test('a tab left open ages without a fetch or log read',()=>{assert.equal(read(base,now+21*60000).state,'stale');});
test('reset takes precedence over an old full sample',()=>{assert.equal(read({...base,state:'full',used_percent:100},Date.parse(base.resets_at)).state,'reset');});
test('legacy percentage without a reset time is only historical',()=>{const {resets_at,...legacy}=base;assert.equal(read(legacy).state,'historical');});
test('past deadlines are never displayed as future forecasts',()=>{assert.equal(read({...base,state:'fills_before_reset',full_at:'2026-10-26T11:55:00Z'}).state,'stale');});
test('weekly samples have a separate age policy',()=>{const row={...base,window_minutes:10080,max_age_seconds:86400,resets_at:'2026-11-01T12:00:00Z'};assert.equal(read(row,now+23*3600000).state,'no_pace');assert.equal(read(row,now+25*3600000).state,'stale');});
