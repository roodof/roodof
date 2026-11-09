import {chromium,_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm,rename,copyFile,unlink,realpath,readdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const root=process.env.PLER_IDENTITY_QA_ROOT||fileURLToPath(new URL('../../reports/session-identity-v1/',import.meta.url));
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim(),errors=[];
async function ready(page){await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading&&typeof window.plerGetViewPreferences==='function');if(await page.locator('#first-use').isVisible())await page.locator('.first-use-actions .primary').click();await settled(page);}
async function settled(page){await page.waitForFunction(()=>!usageState.loading&&usageState.data?.state==='ready');await page.waitForTimeout(180);}
async function refresh(page){await page.evaluate(()=>refreshUsage());await page.waitForFunction(()=>!usageState.loading&&usageState.data?.state==='ready'&&document.querySelector('#usage-progress').hidden);await page.waitForTimeout(180);}
async function closeInspector(page){if(await page.locator('#usage-session-dialog').evaluate(n=>n.open)){await page.keyboard.press('Escape');await page.waitForFunction(()=>!document.querySelector('#usage-session-dialog').open&&workState.openSession===null);}}
async function open(page,id){await page.evaluate(id=>inspectUsageSession(id),id);await page.locator('#session-budget').waitFor({state:'visible'});}
async function move(source,target){const base=await realpath(root),a=await realpath(source),parent=await realpath(path.dirname(target));for(const p of [a,parent])assert.ok(p===base||p.startsWith(base+path.sep));assert.ok(path.resolve(target).startsWith(base+path.sep));await rename(source,target);}
async function budgets(page){return page.evaluate(()=>api('/api/usage/budgets'));}
async function assertLinked(page,expected){
 const data=await page.evaluate(()=>usageState.data);
 for(const [agent,item] of Object.entries(expected)){
  const row=data.sessions.find(s=>s.agent===agent);assert.equal(row.id,item.id);assert.equal(row.verdict,'useful');
  const work=data.work_items.items.find(w=>w.id===item.work);assert.ok(work.session_ids.includes(item.id));assert.equal(work.missing_sessions,0);
 }
 const end=Date.now()+18000;let watched;
 do{watched=(await budgets(page)).items;if(watched.length===2&&watched.every(r=>r.state==='watching'))break;await new Promise(r=>setTimeout(r,250));}while(Date.now()<end);
 assert.equal(watched.length,2);for(const row of watched){assert.equal(row.state,'watching');assert.equal(row.limit,100000);}
}
const browser=await chromium.launch({channel:'msedge',headless:true});
const expected={};
try{
 const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});page.on('pageerror',e=>errors.push(e.message));
 const url=new URL(startup);url.searchParams.set('lang','tr');await page.goto(url.href);await ready(page);
 for(const agent of ['codex','claude-code']){
  const row=await page.evaluate(a=>usageState.data.sessions.find(s=>s.agent===a),agent);await open(page,row.id);
  await page.locator('#usage-session-work-title').fill('Identity '+agent);await page.locator('#usage-session-work-create').click();
  await page.waitForFunction(id=>!usageState.workBusy&&usageState.data.work_items.items.some(w=>w.session_ids.includes(id)),row.id);
  const work=await page.evaluate(id=>usageState.data.work_items.items.find(w=>w.session_ids.includes(id)).id,row.id);
  await page.locator('.verdict-dialog [data-verdict=useful]').click();await page.waitForFunction(id=>!usageState.verdictSaving&&usageState.data.sessions.find(s=>s.id===id)?.verdict==='useful',row.id);
  await page.locator('#budget-limit').fill('100000');await page.locator('#session-budget button[type=submit]').click();await page.waitForFunction(()=>document.querySelector('.budget-message')?.textContent.includes('kaydedildi'));
  expected[agent]={id:row.id,work};await closeInspector(page);
 }
 await assertLinked(page,expected);
 await writeFile(path.join(root,'expected.json'),JSON.stringify(expected,null,2));
 const files={codex:{old:path.join(root,'fixtures/codex/sessions/rollout-original.jsonl'),moved:path.join(root,'fixtures/codex/sessions/rollout-taşınan & kayıt.jsonl')},claude:{old:path.join(root,'fixtures/claude/projects/invented/original.jsonl'),moved:path.join(root,'fixtures/claude/projects/invented/taşınan & kayıt.jsonl')}};
 const durable=['work-items.json','session-verdicts.json','session-budgets.json'];const before=await Promise.all(durable.map(name=>readFile(path.join(root,'cache',name),'utf8')));
 await move(files.codex.old,files.codex.moved);await move(files.claude.old,files.claude.moved);await refresh(page);await assertLinked(page,expected);
 assert.equal((await page.evaluate(()=>usageState.data.identity)).preserved,2);
 for(let i=0;i<durable.length;i++)assert.equal(await readFile(path.join(root,'cache',durable[i]),'utf8'),before[i]);
 await open(page,expected.codex.id);assert.match(await page.locator('#usage-session-work-items').textContent(),/Identity codex/);assert.equal(await page.locator('.verdict-dialog [data-verdict=useful]').getAttribute('aria-pressed'),'true');await page.screenshot({path:path.join(root,'preserved-tr.png')});await closeInspector(page);
 await page.locator('#lang-toggle').click();await page.waitForSelector('html[lang=en]');await ready(page);await assertLinked(page,expected);await page.locator('[data-route=settings]').click();assert.match(await page.locator('#session-identity-status').textContent(),/preserved/);await page.screenshot({path:path.join(root,'preserved-en.png')});
 // A copy is a different file object. Keep the real source parked outside discovery while inspecting it.
 const copy=path.join(root,'fixtures/codex/sessions/rollout-copy.jsonl'),parked=path.join(root,'parked-original.jsonl');await copyFile(files.codex.moved,copy);await move(files.codex.moved,parked);await refresh(page);
 const unverified=await page.evaluate(()=>usageState.data.sessions.find(s=>s.agent==='codex'));assert.notEqual(unverified.id,expected.codex.id);assert.equal(unverified.identity_state,'unverified');
 await open(page,unverified.id);assert.ok(await page.locator('.wb-identity-warning').isVisible());await page.screenshot({path:path.join(root,'copy-unverified.png')});await closeInspector(page);
 // Restore only the exact original object; remove only this fixture's explicitly named copy.
 await move(parked,files.codex.moved);const copyReal=await realpath(copy);assert.ok(copyReal.startsWith((await realpath(root))+path.sep));await unlink(copy);await refresh(page);await assertLinked(page,expected);
 assert.deepEqual(errors,[]);await writeFile(path.join(root,'browser-check.json'),JSON.stringify({two_agents_preserved:true,unicode_ampersand_rename:true,work_review_budget_unchanged:true,no_annotation_migration:true,retained_old_names_do_not_pause_verified_live_budget:true,copy_not_reassigned:true,copy_warning_visible:true,restoring_original_recovers_links:true,english_turkish:true,script_errors:errors},null,2));
}finally{await browser.close();}

const state=path.join(root,'native-window.json');await writeFile(state,JSON.stringify({width:1366,height:900,lang:'tr',view:{screen:'sessions',setupDone:true}}));let app,control;
async function close(){if(app){await app.close();app=null;}if(control){assert.equal(path.dirname(control),path.resolve(root));assert.ok(path.basename(control).startsWith('control-'));await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});control=null;}}
async function launch(){
 control=path.resolve(root,'control-'+randomUUID());await mkdir(control);await writeFile(path.join(control,'running'),'1');
 const env={...process.env,PLER_DESKTOP_URL:startup,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:state};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
 const pkg=process.env.PLER_QA_PACKAGE;
 app=await _electron.launch({executablePath:pkg?path.join(pkg,'desktop/PLER-Desktop.exe'):fileURLToPath(new URL('../desktop/node_modules/electron/dist/electron.exe',import.meta.url)),args:pkg?[]:[fileURLToPath(new URL('../desktop/main.cjs',import.meta.url))],env,timeout:20000});
 const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));await ready(page);return page;
}
try{
 let page=await launch();await assertLinked(page,expected);await open(page,expected.codex.id);await close();
 page=await launch();await assertLinked(page,expected);await open(page,expected['claude-code'].id);await page.screenshot({path:path.join(root,'native-preserved.png')});await close();
 assert.deepEqual(errors,[]);const report=JSON.parse(await readFile(path.join(root,'browser-check.json'),'utf8'));
 await writeFile(path.join(root,'ui-check.json'),JSON.stringify({...report,native_fresh_profile_preserves_all:true,packaged:Boolean(process.env.PLER_QA_PACKAGE),script_errors:errors,clean_windows_acceptance:'PENDING - LAST TASK'},null,2));console.log('Identity preservation interface checks passed');
}finally{await close();}
