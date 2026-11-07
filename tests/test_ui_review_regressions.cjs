const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const frontend=name=>fs.readFileSync(path.join(__dirname,'../frontend',name),'utf8');
const quota=frontend('quota-view.jsx');
function quotaContext(){
 const words={reset:'Reset; waiting',stale:'Sample is old',historical:'Reset time unknown',ambiguous:'Samples disagree',full:'Full',lasts:'Lasts',fills:'Fills',used:'used',gaugeLabel:(a,w,v)=>`${a} ${w}: ${v}%`};
 const el=(tag,cls,text)=>({tag,cls,text,attrs:{},children:[],append(...nodes){this.children.push(...nodes);},setAttribute(k,v){this.attrs[k]=v;}});
 const c={words,el,lang:'en-US'};vm.createContext(c);
 vm.runInContext(quota.slice(quota.indexOf('function stateText('),quota.indexOf('\n  function paint(')),c);return c;
}
test('expired, stale and conflicting quota samples never become a current percentage or full warning',()=>{
 const c=quotaContext();for(const state of ['reset','stale','historical','ambiguous']){
  c.row={state,used_percent:100,agent:'codex',window_minutes:300};
  const result=vm.runInContext('card(row)',c);
  assert.equal(result.used,null,state);assert.equal(result.tone,'muted',state);
  assert.ok(!result.gauge.attrs['aria-label'].includes('100%'),state);
 }
});
test('valid full and no-pace samples still show their recorded percentage',()=>{
 const c=quotaContext();for(const [state,used] of [['full',100],['no_pace',71]]){
  c.row={state,used_percent:used,agent:'codex',window_minutes:300};assert.equal(vm.runInContext('card(row).used',c),used);
 }
});
test('a formerly full sample becomes unknown as soon as its reset expires',()=>{
 const c=quotaContext(),app=fs.readFileSync(path.join(__dirname,'../src/pler/web/app.js'),'utf8');
 vm.runInContext(app.slice(app.indexOf('function quotaWindowNow('),app.indexOf('// Live quota warning:')),c);
 c.row={state:'full',used_percent:100,agent:'codex',window_minutes:300,at:'2026-11-07T12:00:00Z',resets_at:'2026-11-07T12:10:00Z'};
 assert.equal(vm.runInContext("card(quotaWindowNow(row,Date.parse('2026-11-07T12:09:00Z'))).used",c),100);
 assert.equal(vm.runInContext("card(quotaWindowNow(row,Date.parse('2026-11-07T12:10:00Z'))).used",c),null);
});
function group(data){
 const s=frontend('usage-time.js'),c={data};vm.createContext(c);
 vm.runInContext(`const pad=n=>String(n).padStart(2,'0');const dayKey=d=>d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());${s.slice(s.indexOf('function group(data) {'),s.indexOf('\n  function summary('))};result=group(data);`,c);return c.result;
}
function totals(g){return g.keys.reduce((v,key)=>{const d=g.perDay.get(key);if(d)for(const agent of ['claude-code','codex','unknown']){v[0]+=d[agent][0];v[1]+=d[agent][1];}return v;},[0,0]);}
test('a rolling seven-day chart includes its first partial day in tokens and calls',()=>{
 const g=group({filters:{days:7},dated_usage:{since:'2026-10-31T12:00:00Z',cutoff:'2026-11-07T12:00:00Z'},timeline:{rows:[['2026-10-31T13:00:00Z','codex',100,1],['2026-11-07T11:00:00Z','claude-code',200,2]]}});
 assert.deepEqual(totals(g),[300,3]);assert.equal(g.keys.length,8);
});
test('chart boundaries follow elapsed time across DST and preserve all retained buckets',()=>{
 for(const zone of ['Europe/Kyiv','America/New_York','Asia/Kolkata']){
  const previous=process.env.TZ;process.env.TZ=zone;
  try{
   const since='2026-10-24T22:30:00Z',cutoff='2026-10-31T22:30:00Z';
   const rows=[[since,'codex',17,1],[cutoff,'claude-code',23,2]];
   const g=group({filters:{days:7},dated_usage:{since,cutoff},timeline:{rows}});assert.deepEqual(totals(g),[40,3],zone);
  }finally{if(previous===undefined)delete process.env.TZ;else process.env.TZ=previous;}
 }
});
test('all-time and empty intervals keep valid chart dates without inventing usage',()=>{
 assert.deepEqual(totals(group({filters:{days:0},dated_usage:{since:null,cutoff:'2026-11-07T12:00:00Z'},timeline:{rows:[]}})),[0,0]);
 const g=group({filters:{days:0},dated_usage:{cutoff:'2026-11-07T12:00:00Z'},timeline:{rows:[['2026-01-01T12:00:00Z','codex',9,1]]}});assert.deepEqual(totals(g),[9,1]);
});
