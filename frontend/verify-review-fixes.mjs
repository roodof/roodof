import {chromium} from 'playwright';
import {readFile,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const root=new URL('../../reports/review-fixes-v1/',import.meta.url);
const address=(await readFile(new URL('access.tmp',root),'utf8')).match(/http:\/\/127\.0\.0\.1:\d+\/#access=[a-f0-9]{64}/)[0];
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 page.setDefaultTimeout(15000);await page.clock.install();console.log('Loading demo');await page.goto(address);await page.waitForSelector('#sessions-grid .tabulator-row');
 console.log('Quota fixture');
 await page.locator('[data-route=quota]').click();
 await page.evaluate(()=>{const now=Date.now();usageState.data.outlook=[{agent:'codex',window_minutes:300,state:'full',used_percent:100,at:new Date(now).toISOString(),resets_at:new Date(now+1000).toISOString()}];renderUsage(usageState.data);});
 await page.waitForFunction(()=>document.querySelector('.ws-gauge-state')?.textContent==='Full');
 console.log('Full gauge seen');await page.clock.fastForward(31000);console.log('Clock advanced');
 await page.waitForFunction(()=>document.querySelector('.ws-gauge-state')?.textContent==='Reset; waiting for a new sample');
 assert.ok(!(await page.locator('.ws-gauge').first().getAttribute('aria-label')).includes('100'));
 await page.evaluate(()=>{usageState.data.outlook[0]={...usageState.data.outlook[0],state:'stale',used_percent:71,resets_at:new Date(Date.now()+3600000).toISOString(),at:new Date(Date.now()-3600000).toISOString()};renderUsage(usageState.data);});
 await page.waitForFunction(()=>document.querySelector('.ws-gauge-state')?.textContent==='Sample is old');
 assert.ok(!(await page.locator('.ws-gauge').first().getAttribute('aria-label')).includes('71'));
 console.log('Quota assertions passed');await page.locator('[data-route=overview]').click();
 await page.evaluate(()=>{usageState.data.filters.days=7;Object.assign(usageState.data.dated_usage,{since:'2026-10-31T12:00:00Z',cutoff:'2026-11-07T12:00:00Z'});usageState.data.timeline={unit:'hour_utc',rows:[['2026-10-31T13:00:00Z','codex',100,1],['2026-11-07T11:00:00Z','claude-code',200,1]]};renderUsage(usageState.data);});
 await page.waitForFunction(()=>document.querySelector('.ws-time-stat strong .sr-only')?.textContent==='300');
 // Return to a real demo snapshot for authenticated linking writes.
 console.log('Timeline assertion passed');await page.reload();await page.locator('[data-route=sessions]').click();await page.waitForSelector('#sessions-grid .tabulator-row',{state:'attached'});await page.locator('[data-route=work]').click();
 await page.locator('#usage-work-create-title').fill('Review regression');await page.locator('#usage-work-create').click();
 await page.waitForFunction(()=>!usageState.workBusy&&selectedWork()?.title==='Review regression');
 let release,firstStarted;let started=new Promise(r=>firstStarted=r),gate=new Promise(r=>release=r),links=[];
 await page.route(url=>url.pathname==='/api/usage/work',async route=>{const body=route.request().postDataJSON();if(body.action==='link'){links.push(body.session);if(links.length===1){firstStarted();await gate;}}await route.continue();});
 async function chooseTwo(){await page.locator('.ws-link-open').click();const available=page.locator('.ws-cmdk-item:not([aria-disabled=true])');await available.nth(0).click();await available.nth(1).click();await page.locator('.ws-cmdk-foot .primary').click();await started;}
 console.log('Linking fixture');await chooseTwo();console.log('First write held');await page.keyboard.press('Escape');assert.ok(await page.locator('.ws-link-dialog').isVisible());
 await page.mouse.click(2,2);assert.ok(await page.locator('.ws-link-dialog').isVisible());assert.equal(links.length,1);
 assert.ok(await page.locator('.ws-link-dialog').getAttribute('aria-busy')==='true');
 release();console.log('Released first write');await page.waitForFunction(()=>!document.querySelector('.ws-link-dialog').open&&selectedWork()?.linked_sessions===2);assert.equal(links.length,2);
 // Programmatic shutdown must stop the remaining queue after the in-flight checked write.
 links=[];started=new Promise(r=>firstStarted=r);gate=new Promise(r=>release=r);
 await chooseTwo();await page.locator('.ws-link-dialog').evaluate(d=>d.close());release();
 await page.waitForFunction(()=>!usageState.workBusy&&selectedWork()?.linked_sessions===3);assert.equal(links.length,1);
 await page.unrouteAll({behavior:'wait'});assert.deepEqual(errors,[]);
 await writeFile(new URL('regression-check.json',root),JSON.stringify({quota_full_to_reset_on_clock:true,stale_percentage_withheld:true,rolling_chart_total:300,escape_blocked_during_linking:true,backdrop_blocked_during_linking:true,batch_links_completed:2,programmatic_close_stops_queue:true,script_errors:errors},null,2));
 await page.evaluate(()=>post('/api/quit',{}));console.log('All three review regressions passed in the running UI');
}finally{await browser.close();}
