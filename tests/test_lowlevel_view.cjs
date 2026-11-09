'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test');
const source=fs.readFileSync(require('node:path').join(__dirname,'../src/pler/web/app.js'),'utf8');
const inspect=source.slice(source.indexOf('async function inspectUsageSession('),source.indexOf('function clearUsageDownload('));
function investigation(){
  const waiting=[],opened=[],notices=[],state={revision:1,stopped:false};
  const context=vm.createContext({usageState:state,LANG:'en',URLSearchParams,notice:value=>notices.push(value),
    api:()=>new Promise((resolve,reject)=>waiting.push({resolve,reject})),
    openUsageSession:value=>{state.sessionRequest++;opened.push(value);}});
  vm.runInContext(inspect,context);return {context,waiting,opened,notices,state};
}
test('out-of-order session responses cannot replace the newest investigation',async()=>{
  const p=investigation(),first=p.context.inspectUsageSession('a'),second=p.context.inspectUsageSession('b');
  p.waiting[1].resolve({session:{id:'b'}});await second;
  p.waiting[0].resolve({session:{id:'a'}});await first;
  assert.deepEqual(p.opened,[{id:'b'}]);
});
test('a changed selection or directly opened row cancels a pending investigation',async()=>{
  for(const action of [p=>p.state.revision++,p=>p.context.openUsageSession({id:'direct'})]){
    const p=investigation(),run=p.context.inspectUsageSession('a');action(p);
    p.waiting[0].resolve({session:{id:'a'}});await run;
    assert(!p.opened.some(row=>row.id==='a'));
  }
});
test('an obsolete failed investigation does not overwrite the latest notice',async()=>{
  const p=investigation(),first=p.context.inspectUsageSession('a'),second=p.context.inspectUsageSession('b');
  p.waiting[1].resolve({session:{id:'b'}});await second;
  p.waiting[0].reject(new Error('obsolete'));await first;assert.deepEqual(p.notices,[]);
});
test('project selection survives a language reload while the server is still scanning',()=>{
  const project='a'.repeat(24),state={restore:{project}},element={value:'all'};let reads=0;
  const usageUI=require('../src/pler/web/ui-state.js').create();
  const context=vm.createContext({usageState:state,usageUI,setUsageFilters:patch=>{usageUI.publish('filters',patch);element.value=usageUI.get().filters.project;},$:()=>element,loadUsage:()=>reads++});
  vm.runInContext(source.slice(source.indexOf('function restoreUsageSelection('),source.indexOf('function renderDatedUsage(')),context);
  assert.equal(context.restoreUsageSelection({has_snapshot:false,project_options:[],filters:{project:'all'}}),false);
  assert.equal(state.restore.project,project);
  assert.equal(context.restoreUsageSelection({has_snapshot:true,project_options:[{id:project}],filters:{project:'all'}}),true);
  assert.equal(reads,1);assert.equal(element.value,project);assert.equal(state.restore,null);
  assert.equal(usageUI.get().filters.project,project);
});
test('a removed project recovers without retrying an unavailable selection',()=>{
  const state={restore:{project:'a'.repeat(24)}};
  const context=vm.createContext({usageState:state,usageUI:require('../src/pler/web/ui-state.js').create(),$:()=>({}),loadUsage:()=>assert.fail('unexpected retry')});
  vm.runInContext(source.slice(source.indexOf('function restoreUsageSelection('),source.indexOf('function renderDatedUsage(')),context);
  assert.equal(context.restoreUsageSelection({has_snapshot:true,project_options:[],filters:{project:'all'}}),false);
  assert.equal(state.restore,null);
});
test('data quality filtering does not mistake agent errors for incomplete records',()=>{
  const context=vm.createContext({});
  vm.runInContext(source.slice(source.indexOf('function sessionHasQualityLimits('),source.indexOf('function renderUsageSessions(')),context);
  assert.equal(context.sessionHasQualityLimits({errors:4,aborted:2,quality:{tokens_complete:true,calls_complete:true}}),false);
  assert.equal(context.sessionHasQualityLimits({errors:0,quality:{attribution_complete:false}}),true);
  assert.equal(context.sessionHasQualityLimits({quality:{counts_complete:false}}),true);
});
test('live-only retention and paused retention remain visible before any source disappears',()=>{
  const elements={};for(const id of ['usage-archive-controls','usage-archive-status','usage-retention-summary','usage-retention','usage-archive-clear'])elements[id]={};
  const context=vm.createContext({$:id=>elements[id],number:String,t:(key,values)=>key+JSON.stringify(values||{}),syncArchiveButton:()=>{}});
  vm.runInContext(source.slice(source.indexOf('function renderUsageArchive('),source.indexOf('async function changeMetadata(')),context);
  const archive={available:true,enabled:true,retention_enabled:true,stored_files:2,stored_bytes:8192,max_days:365,max_files:2048,max_bytes:67108864};
  context.renderUsageArchive({has_snapshot:true,archive});
  assert.equal(elements['usage-archive-controls'].hidden,false);assert.equal(elements['usage-retention'].checked,true);
  context.renderUsageArchive({has_snapshot:true,archive:{...archive,enabled:false,retention_enabled:false}});
  assert.equal(elements['usage-archive-controls'].hidden,false);assert.equal(elements['usage-retention'].checked,false);
  assert.equal(elements['usage-archive-clear'].hidden,false);
  context.renderUsageArchive({demo:true,has_snapshot:true,archive});assert.equal(elements['usage-archive-controls'].hidden,true);
});
test('changing export masking while a file is prepared discards that old response',async()=>{
  const elements={'usage-export':{disabled:false},'usage-export-mask':{checked:true}},made=[],requests=[];
  let resolve;const reply=new Promise(yes=>{resolve=yes;});
  const state={data:{has_snapshot:true},revision:4,stopped:false};
  const context=vm.createContext({usageState:state,$:id=>elements[id],usageQuery:()=> 'days=7&agent=all&project=all',
    rememberActionFocus:()=>{},clearUsageDownload:()=>{},syncExportButton:()=>{},syncArchiveButton:()=>{},notice:()=>{},restoreActionFocus:()=>{},
    api:path=>{requests.push(path);return reply;},Blob,URL:{createObjectURL:()=>{made.push(true);return 'blob:test';}}});
  vm.runInContext(source.slice(source.indexOf('async function exportUsage('),source.indexOf('function showMoreUsageSessions(')),context);
  const run=context.exportUsage();elements['usage-export-mask'].checked=false;resolve({project_names_masked:true});await run;
  assert.equal(requests[0],'/api/usage/export?days=7&agent=all&project=all&mask_projects=1');assert.equal(made.length,0);
});
