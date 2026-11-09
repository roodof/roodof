import {chromium,_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../../reports/first-use-desktop-v1/',import.meta.url));
const u=new URL((await readFile(path.join(root,'access.tmp'),'utf8')).trim());u.searchParams.set('lang','tr');
const address=u.href,errors=[];const browser=await chromium.launch({channel:'msedge',headless:true});
async function ready(page){await page.waitForFunction(()=>typeof refreshUsage==='function'&&typeof window.plerGetViewPreferences==='function');await page.evaluate(()=>refreshUsage());await page.waitForFunction(()=>!usageState.loading&&usageState.data?.state!=='scanning');await page.waitForTimeout(120);}
try{
 for(const mode of ['error','empty','partial','archive','ready']){
  await writeFile(path.join(root,'mode.txt'),mode);
  const context=await browser.newContext({viewport:{width:1366,height:900},reducedMotion:'reduce'});const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(address);await ready(page);assert.ok(await page.locator('#first-use').isVisible());assert.equal(await page.locator('.driver-popover').count(),0);
  const primary=page.locator('.first-use-actions .primary');
  if(mode==='error'){if(!await page.evaluate(()=>usageState.data.has_snapshot))assert.ok(await primary.isDisabled());assert.match(await page.locator('.first-use-status').textContent(),/tamamlanamadı/);}
  if(mode==='empty'){
   assert.ok(await primary.isDisabled());assert.equal(await page.locator('.first-use-source-state').filter({hasText:'Kayıt bulunamadı'}).count(),2);
   await page.locator('.first-use-guidance summary').click();assert.ok(await page.getByText('Yalnızca uygulamayı kurmak',{exact:false}).count()||await page.locator('.first-use-guidance[open]').count());
   await page.screenshot({path:path.join(root,'empty.png')});
   await page.locator('.first-use-actions .quiet').click();assert.ok(await page.locator('#first-use').isHidden());assert.equal(await page.evaluate(()=>window.plerGetViewPreferences().setupDone),true);
  }
  if(mode==='partial'){assert.match(await page.locator('.first-use-status').textContent(),/Bazı kayıtlar okunamadı/);assert.ok(await primary.isEnabled());}
  if(mode==='archive'){assert.match(await page.locator('[data-source-state=codex]').textContent(),/saklanan geçmişte/);}
  if(mode==='ready'){
   assert.match(await primary.textContent(),/3 oturumu/);assert.equal(await page.evaluate(()=>usageState.data.totals.sessions),2);
   await page.screenshot({path:path.join(root,'ready.png')});
   await page.locator('#lang-toggle').click();await page.waitForSelector('html[lang=en]');await page.waitForFunction(()=>!usageState.loading);await page.waitForTimeout(150);
   assert.ok(await page.locator('#first-use').isVisible());assert.match(await page.locator('#first-use-title').textContent(),/Find your/);
   await primary.click();await page.waitForFunction(()=>usageState.data.filters.days===0&&!usageState.loading);assert.equal(await page.evaluate(()=>usageState.data.totals.sessions),3);assert.equal(await page.locator('[data-select=usage-period] [data-value="0"]').getAttribute('aria-pressed'),'true');assert.ok(await page.locator('#first-use').isHidden());
   assert.equal(await page.evaluate(()=>window.plerGetViewPreferences().setupDone),true);
   await page.reload();await page.waitForFunction(()=>window.plerGetViewPreferences?.().setupDone===true);assert.ok(await page.locator('#first-use').isHidden());
   await page.locator('[data-route=settings]').click();await page.locator('#first-use-reopen').click();assert.ok(await page.locator('#first-use').isVisible());
   await primary.click();await page.waitForFunction(()=>!usageState.loading);await page.locator('[data-route=settings]').click();await page.locator('.first-use-tour').click();await page.waitForSelector('.driver-popover');await page.keyboard.press('Escape');await page.waitForSelector('.driver-popover',{state:'hidden'});await page.locator('[data-route=settings]').click();await page.locator('#first-use-reopen').click();
   await page.route('**/api/usage/refresh*',route=>route.abort());await page.locator('.first-use-actions .secondary').click();await page.waitForFunction(()=>usageState.readError===true);await page.waitForTimeout(150);assert.match(await page.locator('.first-use-status').textContent(),/could not finish/);
   await page.unrouteAll();
  }
  await context.close();
 }
 const mobile=await browser.newContext({viewport:{width:420,height:800},reducedMotion:'reduce'});const mp=await mobile.newPage();await mp.goto(address);await ready(mp);assert.ok(await mp.locator('#first-use').isVisible());assert.ok(await mp.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await mp.screenshot({path:path.join(root,'mobile.png'),fullPage:true});await mobile.close();
}finally{await browser.close();}
// Real native close + fresh profile: completion belongs to the existing bounded preference file.
await writeFile(path.join(root,'mode.txt'),'ready');const stateFile=path.join(root,'native-window.json');await writeFile(stateFile,JSON.stringify({width:1366,height:900,lang:'tr',tour:true}));
let app,control;
async function launch(){
 control=path.resolve(root,'control-'+randomUUID());await mkdir(control);await writeFile(path.join(control,'running'),'1');
 const env={...process.env,PLER_DESKTOP_URL:new URL(address).origin+'/'+new URL(address).hash,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:stateFile};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
 const packaged=process.env.PLER_QA_PACKAGE;
 app=await _electron.launch({executablePath:packaged?path.join(packaged,'desktop/PLER-Desktop.exe'):fileURLToPath(new URL('../desktop/node_modules/electron/dist/electron.exe',import.meta.url)),args:packaged?[]:[fileURLToPath(new URL('../desktop/main.cjs',import.meta.url))],env,timeout:20000});
 const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading&&typeof window.plerGetViewPreferences==='function');await page.waitForTimeout(150);return page;
}
async function close(){if(app){await app.close();app=null;}if(control){assert.equal(path.dirname(control),path.resolve(root));assert.ok(path.basename(control).startsWith('control-'));await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});control=null;}}
try{
 let page=await launch();assert.ok(await page.locator('#first-use').isVisible());await page.locator('.first-use-actions .primary').click();await page.waitForFunction(()=>usageState.data.filters.days===0&&!usageState.loading);await close();
 assert.equal(JSON.parse(await readFile(stateFile,'utf8')).view.setupDone,true);
 page=await launch();assert.ok(await page.locator('#first-use').isHidden());assert.equal(await page.evaluate(()=>window.plerGetViewPreferences().setupDone),true);await close();assert.deepEqual(errors,[]);
 await writeFile(path.join(root,'ui-check.json'),JSON.stringify({source_counts_ignore_filters:true,empty_guidance:true,scan_error:true,partial_read:true,retained_history_label:true,retry_network_error:true,all_sessions_action:true,continue_without_records:true,optional_tour:true,language_switch:true,settings_reopen:true,mobile_no_overflow:true,native_fresh_profile_remembers_completion:true,packaged:Boolean(process.env.PLER_QA_PACKAGE),script_errors:errors},null,2));console.log('First-use flow checks passed');
}finally{await close();}
