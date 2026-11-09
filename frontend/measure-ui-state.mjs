import {chromium} from 'playwright';
import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_UI_QA_ROOT||fileURLToPath(new URL('../../reports/ui-state-v1/baseline/',import.meta.url)));
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim();
const browser=await chromium.launch({channel:'msedge',headless:true});
const errors=[];
try{
 const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});
 const session=await page.context().newCDPSession(page);await session.send('Performance.enable');
 page.on('pageerror',error=>errors.push(error.message));
 await page.addInitScript(()=>{
  window.qaMetrics={observers:0,callbacks:0,storageWrites:0};
  const Native=window.MutationObserver;
  window.MutationObserver=class extends Native{constructor(callback){window.qaMetrics.observers++;super((records,observer)=>{window.qaMetrics.callbacks++;callback(records,observer);});}};
  const set=Storage.prototype.setItem;Storage.prototype.setItem=function(key,value){if(key==='pler-ui-view-v1')window.qaMetrics.storageWrites++;return set.call(this,key,value);};
 });
 const began=Date.now();await page.goto(startup);await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading,{timeout:90000});
 if(await page.locator('#first-use').isVisible())await page.locator('.first-use-actions .primary').click();
 await page.waitForFunction(()=>!usageState.loading&&usageState.data?.filters.days===0,{timeout:90000});await page.waitForTimeout(250);
 const startupMs=Date.now()-began;
 await session.send('HeapProfiler.collectGarbage');const allMetrics=await session.send('Performance.getMetrics');const allHeapBytes=allMetrics.metrics.find(m=>m.name==='JSHeapUsedSize').value;
 await page.evaluate(()=>{window.qaFilterCalls=0;const original=filteredUsageSessions;window.filteredUsageSessions=(...args)=>{window.qaFilterCalls++;return original(...args);};});
 const projections=[];
 for(let i=0;i<3;i++){
  const before=Object.fromEntries((await session.send('Performance.getMetrics')).metrics.map(m=>[m.name,m.value]));
  await page.evaluate(()=>{window.qaFilterCalls=0;qaMetrics.callbacks=0;qaMetrics.storageWrites=0;const began=performance.now();renderUsageSessions();window.qaRenderMs=performance.now()-began;});
  await page.waitForTimeout(180);const after=Object.fromEntries((await session.send('Performance.getMetrics')).metrics.map(m=>[m.name,m.value]));projections.push({...await page.evaluate(()=>({syncMs:qaRenderMs,filterPasses:qaFilterCalls,mutationCallbacks:qaMetrics.callbacks,storageWrites:qaMetrics.storageWrites})),pipelineScriptMs:(after.ScriptDuration-before.ScriptDuration)*1000,layoutMs:(after.LayoutDuration-before.LayoutDuration)*1000});
 }
 const queries=[];page.on('request',request=>{const url=new URL(request.url());if(url.pathname==='/api/usage')queries.push(Object.fromEntries(url.searchParams));});
 await page.evaluate(()=>{qaMetrics.storageWrites=0;for(const [id,value] of [['usage-period','7'],['usage-agent','codex'],['usage-project','all']]){const control=document.getElementById(id);control.value=value;control.dispatchEvent(new Event('change',{bubbles:true}));}});
 await page.waitForFunction(()=>!usageState.loading&&usageState.data?.filters.days===7&&usageState.data?.filters.agent==='codex',{timeout:90000});await page.waitForTimeout(250);
 const filterWrites=await page.evaluate(()=>qaMetrics.storageWrites);
 await page.locator('[data-route=settings]').click();await page.waitForTimeout(100);
 await page.evaluate(()=>{qaMetrics.storageWrites=0;for(let i=0;i<3;i++)document.querySelector('[data-route=settings]').click();});await page.waitForTimeout(180);
 const navWrites=await page.evaluate(()=>qaMetrics.storageWrites);
 await session.send('HeapProfiler.collectGarbage');const raw=await session.send('Performance.getMetrics');const metric=Object.fromEntries(raw.metrics.map(m=>[m.name,m.value]));
 assert.deepEqual(errors,[]);
 const result={kind:'developer machine, invented history; indicative timings, not clean-Windows acceptance',version:await page.evaluate(()=>usageState.data.version),rows:await page.evaluate(()=>usageState.data.setup.sessions),startupMs,projections,allHeapBytes,compoundFilterRequests:queries.length,compoundFilterQueries:queries,filterPreferenceWrites:filterWrites,repeatedSameScreenWrites:navWrites,constructedMutationObservers:await page.evaluate(()=>qaMetrics.observers),heapBytes:metric.JSHeapUsedSize,nodes:metric.Nodes,legacyRows:await page.locator('#usage-sessions > tr').count(),scriptErrors:errors};
 if(process.env.PLER_UI_ENFORCE_GUARDRAILS==='1'){
  const guards={firstInventedReadUnder15s:startupMs<15000,projectionSyncUnder100ms:Math.max(...projections.map(p=>p.syncMs))<100,allHistoryJsHeapUnder128MiB:allHeapBytes<128*1024*1024,oneFilterPass:projections.every(p=>p.filterPasses===1),oneCompoundGet:queries.length===1,noRepeatScreenWrites:navWrites===0,noHiddenDuplicateTable:result.legacyRows===0};assert.ok(Object.values(guards).every(Boolean),JSON.stringify(guards));result.guardrails=guards;
 }
 await writeFile(path.join(root,'measurements.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({rows:result.rows,projections,compoundFilterRequests:queries.length,repeatedSameScreenWrites:navWrites}));
}finally{await browser.close();}
