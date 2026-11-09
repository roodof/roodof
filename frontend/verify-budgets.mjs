import {chromium,_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../../reports/session-budgets-v1/',import.meta.url));
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim();
const url=new URL(startup);url.searchParams.set('lang','tr');const errors=[];
const headers={'X-PLER-Token':new URL(startup).hash.slice(8),Origin:new URL(startup).origin,'Content-Type':'application/json'};
async function get(){const r=await fetch(new URL('/api/usage/budgets',startup),{headers});assert.ok(r.ok);return r.json();}
async function change(body){const r=await fetch(new URL('/api/usage/budgets',startup),{method:'POST',headers,body:JSON.stringify(body)});assert.ok(r.ok);return r.json();}
async function ready(page){await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading&&typeof window.plerOpenBudgetSession==='function');if(await page.locator('#first-use').isVisible())await page.locator('.first-use-actions .primary').click();await page.waitForFunction(()=>!usageState.loading);}
async function openAgent(page,agent){await page.evaluate(a=>openUsageSession(usageState.data.sessions.find(s=>s.agent===a)),agent);await page.locator('.budget-editor>summary').click();await page.locator('#budget-limit').waitFor();}
async function waitRow(id,predicate,timeout=25000){const end=Date.now()+timeout;while(Date.now()<end){const row=(await get()).items.find(r=>r.id===id);if(row&&predicate(row))return row;await new Promise(r=>setTimeout(r,250));}throw new Error('Budget observation timed out');}
const browser=await chromium.launch({channel:'msedge',headless:true});
let codexId,claudeId;
try{
 await setTokens(79000);
 await fetch(new URL('/api/usage/refresh',startup),{method:'POST',headers,body:'{}'});
 // Start from an explicit isolated preference state; this never addresses real cache files.
 for(const row of (await get()).items)await change({id:row.id,metric:null,limit:null,expected:row.revision});
 const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});page.on('pageerror',e=>errors.push(e.message));await page.goto(url.href);await ready(page);
 ({codexId,claudeId}=await page.evaluate(()=>({codexId:usageState.data.sessions.find(s=>s.agent==='codex').id,claudeId:usageState.data.sessions.find(s=>s.agent==='claude-code').id})));
 await openAgent(page,'codex');await page.locator('#budget-limit').fill('100000');await page.getByRole('button',{name:'Uyarıyı kaydet',exact:true}).click();
 await waitRow(codexId,r=>r.state==='watching'&&r.amount===79000&&r.level===0);
 await page.waitForTimeout(5200);assert.match(await page.locator('#session-budget .budget-amount').textContent(),/79.000/);
 // A rejected save keeps the editor and saved threshold intact.
 await page.route('**/api/usage/budgets?*',route=>route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({ok:false,reason:'conflict'})}));
 await page.locator('#budget-limit').fill('120000');await page.getByRole('button',{name:'Uyarıyı kaydet',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.budget-message')?.textContent.includes('Kaydedilemedi'));
 assert.equal((await get()).items.find(r=>r.id===codexId).limit,100000);assert.equal(await page.locator('#budget-limit').inputValue(),'120000');await page.unrouteAll();
 await page.screenshot({path:path.join(root,'inspector-tr.png')});
 await page.keyboard.press('Escape');await page.locator('[data-route=settings]').click();await page.locator('.budget-watch-open').first().focus();await page.waitForTimeout(5500);assert.equal(await page.locator('.budget-watch-open').first().evaluate(n=>n===document.activeElement),true);
 await openAgent(page,'claude-code');await page.locator('#budget-metric').selectOption('usd');assert.match(await page.locator('.budget-metric-note').textContent(),/Gerçek fatura/);await page.locator('#budget-limit').fill('0.01');await page.getByRole('button',{name:'Uyarıyı kaydet',exact:true}).click();await waitRow(claudeId,r=>r.metric==='usd'&&r.amount>0);
 await page.keyboard.press('Escape');await page.locator('[data-route=settings]').click();await page.screenshot({path:path.join(root,'watch-list-tr.png')});
 await page.locator('#lang-toggle').click();await page.waitForSelector('html[lang=en]');await ready(page);await openAgent(page,'claude-code');assert.match(await page.locator('#session-budget').textContent(),/API price equivalent/);await page.screenshot({path:path.join(root,'inspector-en.png')});
 await page.keyboard.press('Escape');await page.locator('[data-route=settings]').click();
 await page.locator(`[data-budget-id="${claudeId}"] .budget-remove`).click();await page.waitForFunction(()=>!document.querySelector('.budget-watch-row .budget-remove:disabled'));assert.equal((await get()).items.some(r=>r.id===claudeId),false);
 const mobile=await browser.newPage({viewport:{width:420,height:800},reducedMotion:'reduce'});mobile.on('pageerror',e=>errors.push(e.message));await mobile.goto(url.href);await ready(mobile);await openAgent(mobile,'codex');assert.ok(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));assert.ok(await mobile.locator('#session-budget').evaluate(n=>n.scrollWidth<=n.clientWidth+1));await mobile.screenshot({path:path.join(root,'mobile.png'),fullPage:true});await mobile.close();
 await page.close();
}finally{await browser.close();}

// Use the actual main-process notification class, while observing show/failed events.
const state=path.join(root,'native-window.json');await writeFile(state,JSON.stringify({width:1366,height:900,lang:'tr',tour:true,view:{screen:'sessions',setupDone:true}}));
let app,control;
async function launch(){
 control=path.resolve(root,'control-'+randomUUID());await mkdir(control);await writeFile(path.join(control,'running'),'1');
 const env={...process.env,PLER_DESKTOP_URL:startup,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:state};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
 const pkg=process.env.PLER_QA_PACKAGE;
 app=await _electron.launch({executablePath:pkg?path.join(pkg,'desktop/PLER-Desktop.exe'):fileURLToPath(new URL('../desktop/node_modules/electron/dist/electron.exe',import.meta.url)),args:pkg?[]:[fileURLToPath(new URL('../desktop/main.cjs',import.meta.url))],env,timeout:20000});
 const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));await ready(page);
 await app.evaluate(({Notification})=>{
  globalThis.budgetNativeEvents=[];const original=Notification.prototype.show;
  Notification.prototype.show=function(){const n=this;budgetNativeEvents.push({event:'created',title:n.title,body:n.body});n.once('show',()=>budgetNativeEvents.push({event:'show'}));n.once('failed',()=>budgetNativeEvents.push({event:'failed'}));return original.call(n);};
 });
 return page;
}
async function close(){if(app){await app.close();app=null;}if(control){assert.equal(path.dirname(control),path.resolve(root));assert.ok(path.basename(control).startsWith('control-'));await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});control=null;}}
async function setTokens(n){const file=path.join(root,'fixtures/codex/sessions/rollout-watch.jsonl');const lines=(await readFile(file,'utf8')).trim().split('\n').map(JSON.parse);lines[2].payload.usage.input_tokens=n;await writeFile(file,lines.map(JSON.stringify).join('\n')+'\n');}
const nativeEvents=[];
try{
 const page=await launch();
 await page.evaluate(()=>{$('usage-agent').value='claude-code';$('usage-agent').dispatchEvent(new Event('change',{bubbles:true}));});
 await page.waitForFunction(()=>usageState.data.filters.agent==='claude-code'&&!usageState.loading);
 await page.evaluate(()=>{$('usage-period').value='7';$('usage-period').dispatchEvent(new Event('change',{bubbles:true}));});
 await page.waitForFunction(()=>usageState.data.filters.days===7&&!usageState.loading);
 assert.equal(await page.evaluate(id=>usageState.data.sessions.some(s=>s.id===id),codexId),false);
 await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].minimize());
 await setTokens(81000);await waitRow(codexId,r=>r.level===80&&r.notified.includes(80),30000);
 nativeEvents.push(...await app.evaluate(()=>budgetNativeEvents));assert.ok(nativeEvents.some(r=>r.event==='show'));assert.ok(!nativeEvents.some(r=>r.event==='failed'));
 await setTokens(110000);await waitRow(codexId,r=>r.level===100&&r.notified.includes(100),30000);
 const delivered=await app.evaluate(()=>budgetNativeEvents);assert.equal(delivered.filter(r=>r.event==='created').length,2);assert.equal(delivered.filter(r=>r.event==='show').length,2);
 // A frontend filter cannot hide the watch: both notifications above arrived while minimized.
 await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].restore());await page.locator('[data-route=settings]').click();await page.waitForTimeout(5500);assert.match(await page.locator('#budget-watch').textContent(),/110.000/);await page.screenshot({path:path.join(root,'threshold-reached.png')});
 await close();await launch();await new Promise(r=>setTimeout(r,6000));assert.equal((await app.evaluate(()=>budgetNativeEvents)).filter(r=>r.event==='created').length,0);await close();assert.deepEqual(errors,[]);
 await writeFile(path.join(root,'ui-check.json'),JSON.stringify({token_editor:true,usd_editor:true,failed_save_preserves_draft:true,watch_keyboard_focus:true,english_turkish:true,mobile_no_overflow:true,filtered_independent:true,native_minimized_delivery_80_100:true,native_events:delivered,native_restart_no_repeat:true,packaged:Boolean(process.env.PLER_QA_PACKAGE),script_errors:errors,clean_windows_acceptance:'PENDING - LAST TASK'},null,2));console.log('Budget interface and native alerts passed');
}finally{await close();}
