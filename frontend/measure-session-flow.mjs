// Same invented history and machine for before/after; no real-log performance claim.
import {chromium} from 'playwright';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_FLOW_ROOT);
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim();
const browser=await chromium.launch({channel:'msedge',headless:true});
const runs=[];
try{
 for(let repeat=0;repeat<3;repeat++){
  const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'}),errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.addInitScript(()=>{
   sessionStorage.setItem('pler-ui-view-v1',JSON.stringify({setupDone:true,screen:'sessions',filters:{days:'0',agent:'all',project:'all'}}));
   window.qaRowElements=0;const clone=Element.prototype.cloneNode;
   Element.prototype.cloneNode=function(...args){if(this.classList?.contains('tabulator-row'))window.qaRowElements++;return clone.apply(this,args);};
  });
  const cdp=await page.context().newCDPSession(page);await cdp.send('Performance.enable');
  const began=Date.now();await page.goto(startup);
  await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading&&document.querySelector('.grid-project-name'));
  await page.waitForTimeout(150);
  const startupMs=Date.now()-began;
  // Exercise the existing load-more path at large scale as well as its first 20 rows.
  const expandStart=Date.now();
  await page.evaluate(()=>{usageState.pageSize=5000;renderUsageSessions();});
  await page.waitForTimeout(250);
  const expandedMs=Date.now()-expandStart;
  await cdp.send('HeapProfiler.collectGarbage');
  const metrics=Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(m=>[m.name,m.value]));
  const id=await page.evaluate(()=>plerUI.get().sessions.items[0].id);
  const opens=[];
  for(let i=0;i<5;i++){
   opens.push(await page.evaluate(id=>{const start=performance.now();openUsageSession(usageState.data.sessions.find(s=>s.id===id));return performance.now()-start;},id));
   await page.keyboard.press('Escape');
  }
  assert.deepEqual(errors,[]);
  runs.push({startupMs,expandedMs,rowElements:await page.evaluate(()=>qaRowElements),heapBytes:metrics.JSHeapUsedSize,nodes:metrics.Nodes,openSyncMs:opens,rows:await page.evaluate(()=>usageState.data.setup.sessions),scriptErrors:errors});
  await page.close();
 }
 await writeFile(path.join(root,'flow-measurements.json'),JSON.stringify({scope:'Same developer machine, 5000 invented sessions; renderer only, not real-log or clean-Windows acceptance',runs},null,2));
 console.log(JSON.stringify(runs.map(r=>({startupMs:r.startupMs,rowElements:r.rowElements,heapMiB:+(r.heapBytes/1048576).toFixed(2),openSyncMs:r.openSyncMs}))));
}finally{await browser.close();}
