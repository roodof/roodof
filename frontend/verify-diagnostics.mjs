import {chromium,_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const report=fileURLToPath(new URL('../../reports/read-diagnostics-v1/',import.meta.url));
const root=path.resolve(process.env.PLER_DIAGNOSTIC_QA_ROOT||path.join(report,'source-ui'));
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim(),errors=[];
const PRIVATE='PRIVATE-DIAGNOSTIC-PATH-PROMPT-ID-TOKEN-CANARY';
const token=new URL(startup).hash.slice('#access='.length);
function privateFree(value){for(const part of [PRIVATE,token,root,'Named agent session','Early window title','codex-unnamed','claude-window'])assert.ok(!JSON.stringify(value).includes(JSON.stringify(part).slice(1,-1)),'private diagnostic content');}
async function ready(page){await page.waitForFunction(()=>usageState.data?.has_snapshot&&usageState.data.state==='ready'&&!usageState.loading);}
async function refresh(page,state='ready'){const revision=await page.evaluate(()=>usageState.revision);await page.locator('#usage-refresh').click();await page.waitForFunction(({state,revision})=>usageState.revision>revision&&usageState.data?.state===state&&!usageState.loading&&document.getElementById('usage-progress').hidden,{state,revision});await page.waitForTimeout(180);}
async function download(page,name){const event=page.waitForEvent('download');await page.locator('#diagnostics-download').click();const file=await event;const target=path.join(root,name);await file.saveAs(target);const data=JSON.parse(await readFile(target,'utf8'));privateFree(data);assert.equal(data.format,1);assert.ok(data.items.every(i=>/^[a-z_]+$/.test(i.code)&&i.next));return data;}
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce',acceptDownloads:true});page.on('pageerror',e=>errors.push(e.message));
 const url=new URL(startup);url.searchParams.set('lang','tr');await page.goto(url.href);await ready(page);await page.locator('.first-use-actions .primary').click();
 const original=await page.evaluate(()=>usageState.data.totals.total_tokens);
 const sessions=await page.evaluate(()=>usageState.data.sessions);assert.equal(sessions.length,4);
 const limited=sessions.find(s=>s.title_info.code==='title_window_limited');assert.ok(limited);
 await page.evaluate(id=>inspectUsageSession(id),limited.id);await page.locator('.session-title-status').waitFor({state:'visible'});assert.match(await page.locator('.session-title-status summary').textContent(),/başı ve sonuyla/);await page.locator('.session-title-status summary').click();assert.match(await page.locator('.session-title-status').textContent(),/64 KiB/);await page.keyboard.press('Escape');
 await page.locator('#diagnostics-shortcut').click();await page.locator('#diagnostics').waitFor({state:'visible'});
 assert.ok(await page.locator('[data-code=source_access_denied]').isVisible());assert.ok(await page.locator('[data-code=source_wsl_stopped]').isVisible());
 const before=await download(page,'diagnostics-tr.json');
 await page.evaluate(()=>{document.getElementById('usage-agent').value='claude-code';document.getElementById('usage-agent').dispatchEvent(new Event('change',{bubbles:true}));});await ready(page);
 assert.deepEqual((await page.evaluate(()=>usageState.data.diagnostics)).items,before.items);
 await page.locator('#lang-toggle').click();await page.waitForSelector('html[lang=en]');await ready(page);await page.locator('[data-route=settings]').click();assert.match(await page.locator('#diagnostics h2').textContent(),/Read status/);await download(page,'diagnostics-en.json');
 await writeFile(path.join(root,'mode.txt'),'fail');await refresh(page,'error');assert.equal(await page.evaluate(()=>usageState.data.has_snapshot),true);assert.equal(await page.evaluate(()=>usageState.data.diagnostics.snapshot),'previous');assert.ok(await page.locator('[data-code=logs_failed]').isVisible());privateFree(await page.evaluate(()=>usageState.data.diagnostics));
 // All-agent snapshot was retained; the current page filter is still Claude.
 assert.equal(await page.evaluate(()=>usageState.data.setup.sessions),4);
 await page.screenshot({path:path.join(root,'previous-read.png'),fullPage:true});
 await writeFile(path.join(root,'mode.txt'),'cold_fail');await refresh(page,'error');assert.equal(await page.evaluate(()=>usageState.data.has_snapshot),false);assert.ok(await page.locator('#diagnostics').isVisible());assert.ok(await page.locator('#usage-empty').isHidden());
 await download(page,'diagnostics-no-snapshot.json');
 const fresh=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});fresh.on('pageerror',e=>errors.push(e.message));await fresh.goto(url.href);await fresh.waitForFunction(()=>usageState.data?.state==='error'&&!usageState.loading);await fresh.locator('#first-use-diagnostics').click();assert.ok(await fresh.locator('#diagnostics').isVisible());assert.ok(await fresh.locator('#usage-empty').isHidden());await fresh.locator('[data-route=sessions]').click();assert.ok(await fresh.locator('#usage-content').isHidden());await fresh.close();
 await writeFile(path.join(root,'mode.txt'),'ready');await refresh(page);assert.ok(!(await page.evaluate(()=>usageState.data.diagnostics.items)).some(i=>i.code==='logs_failed'));
 await page.evaluate(()=>{document.getElementById('usage-agent').value='all';document.getElementById('usage-agent').dispatchEvent(new Event('change',{bubbles:true}));});await ready(page);assert.equal(await page.evaluate(()=>usageState.data.totals.total_tokens),original);
 await page.setViewportSize({width:420,height:800});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await page.screenshot({path:path.join(root,'diagnostics-mobile.png'),fullPage:true});await page.close();
}finally{await browser.close();}
const state=path.join(root,'native-window.json');await writeFile(state,JSON.stringify({width:1366,height:900,lang:'tr',tour:true,view:{setupDone:true,screen:'settings'}}));
let app,control;
async function close(){if(app){await app.close();app=null;}if(control){assert.equal(path.dirname(control),root);assert.ok(path.basename(control).startsWith('control-'));await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});control=null;}}
async function launch(){
 control=path.join(root,'control-'+randomUUID());await mkdir(control);await writeFile(path.join(control,'running'),'1');
 const env={...process.env,PLER_DESKTOP_URL:startup,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:state};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
 const pkg=process.env.PLER_QA_PACKAGE;app=await _electron.launch({executablePath:pkg?path.join(pkg,'desktop/PLER-Desktop.exe'):fileURLToPath(new URL('../desktop/node_modules/electron/dist/electron.exe',import.meta.url)),args:pkg?[]:[fileURLToPath(new URL('../desktop/main.cjs',import.meta.url))],env,timeout:20000});
 const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));await ready(page);if(await page.locator('#first-use').isVisible())await page.locator('.first-use-actions .primary').click();await page.locator('[data-route=settings]').click();return page;
}
try{
 let page=await launch();
 const target=path.join(root,'native-diagnostics.json');
 await app.evaluate(({BrowserWindow},target)=>{globalThis.qaDiagnosticDownload='waiting';BrowserWindow.getAllWindows()[0].webContents.session.once('will-download',(_event,item)=>{item.setSavePath(target);item.once('done',(_event,state)=>{globalThis.qaDiagnosticDownload=state;});});},target);
 await page.locator('#diagnostics-download').click();
 const deadline=Date.now()+15000;let state;do{state=await app.evaluate(()=>globalThis.qaDiagnosticDownload);if(state==='completed')break;await new Promise(r=>setTimeout(r,100));}while(Date.now()<deadline);assert.equal(state,'completed');privateFree(JSON.parse(await readFile(target,'utf8')));
 await page.locator('#diagnostics').evaluate(n=>n.scrollIntoView({block:'start',behavior:'instant'}));await page.screenshot({path:path.join(root,'native-diagnostics.png')});await close();page=await launch();assert.ok(await page.locator('#diagnostics').isVisible());await close();assert.deepEqual(errors,[]);
 await writeFile(path.join(root,'ui-check.json'),JSON.stringify({tr_en_reasons:true,window_limit_explained:true,download_content_free:true,filter_independent:true,previous_snapshot_retained:true,no_snapshot_settings_accessible:true,first_use_failure_recovery:true,successful_retry_clears_failure:true,usage_totals_unchanged:true,mobile_no_overflow:true,native_download_and_reopen:true,packaged:Boolean(process.env.PLER_QA_PACKAGE),script_errors:errors,real_agent_acceptance:'PENDING - LAST TASK',clean_windows_acceptance:'PENDING - LAST TASK'},null,2));console.log('Title and diagnostic interface checks passed');
}finally{await close();}
