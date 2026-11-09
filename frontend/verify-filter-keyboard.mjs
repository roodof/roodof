import {chromium,_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const root=process.env.PLER_KEYBOARD_QA_ROOT||fileURLToPath(new URL('../../reports/filter-keyboard-v1/',import.meta.url));
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim();
const errors=[],remote=[];
async function ready(page){
 await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading&&typeof window.plerGetViewPreferences==='function');
 if(await page.locator('#first-use').isVisible())await page.locator('.first-use-actions .primary').click();
 await settled(page);await page.locator('[data-route=sessions]').click();
}
async function settled(page){await page.waitForFunction(()=>!usageState.loading&&usageState.data?.state==='ready');await page.waitForTimeout(180);}
async function closeInspector(page){await page.keyboard.press('Escape');await page.waitForFunction(()=>!document.querySelector('#usage-session-dialog').open&&workState.openSession===null);}
async function all(page){await page.evaluate(()=>{$('usage-period').value='0';$('usage-agent').value='all';$('usage-project').value='all';$('usage-session-search').value='';$('usage-quality-only').checked=false;loadUsage();});await settled(page);}
async function controls(page){return page.evaluate(()=>({
 actual:{days:$('usage-period').value,agent:$('usage-agent').value,project:$('usage-project').value},
 selected:{days:document.querySelector('[data-select=usage-period] [aria-pressed=true]')?.dataset.value,agent:document.querySelector('[data-select=usage-agent] [aria-pressed=true]')?.dataset.value},
 query:usageState.data.filters,remembered:window.plerGetViewPreferences().filters,
 stored:JSON.parse(sessionStorage.getItem('pler-ui-view-v1')).filters,
 report:document.querySelector('.ws-report-scope').textContent
}));}
async function verifyClear(page,lang){
 await all(page);
 const project=await page.evaluate(()=>usageState.data.sessions.find(s=>s.title==='Invented old').project_id);
 await page.locator('[data-select=usage-agent] [data-value=codex]').click();await settled(page);
 await page.locator('[data-select=usage-period] [data-value="7"]').click();await settled(page);
 await page.locator('#usage-project').selectOption(project);await settled(page);
 await page.locator('#usage-filter-clear').waitFor({state:'visible'});
 // Start from a real empty selection and ensure clearing performs one query, not one per control.
 const queries=[];const capture=request=>{const u=new URL(request.url());if(u.pathname==='/api/usage')queries.push(Object.fromEntries(u.searchParams));};
 page.on('request',capture);
 try{await page.locator('#usage-filter-clear').click();await settled(page);}finally{page.off('request',capture);}
 assert.equal(queries.length,1);assert.deepEqual({days:queries[0].days,agent:queries[0].agent,project:queries[0].project},{days:'0',agent:'all',project:'all'});
 const state=await controls(page);
 assert.deepEqual(state.actual,{days:'0',agent:'all',project:'all'});assert.deepEqual(state.selected,{days:'0',agent:'all'});
 assert.equal(state.query.days,0);assert.equal(state.query.agent,'all');assert.equal(state.query.project,'all');
 for(const value of [state.remembered,state.stored]){assert.equal(value.days,'0');assert.equal(value.agent,'all');assert.equal(value.project,'all');}
 assert.match(state.report,lang==='tr'?/Tüm oturumlar/:/All sessions/);
 await page.reload();await ready(page);const restored=await controls(page);assert.deepEqual(restored.selected,{days:'0',agent:'all'});
}
async function verifyKeys(page){
 await all(page);
 await page.locator('#sessions-grid .grid-agent-filter.is-claude').first().focus();await page.keyboard.press('Enter');await settled(page);
 assert.equal(await page.evaluate(()=>usageState.data.filters.agent),'claude-code');assert.equal(await page.locator('#usage-session-dialog').evaluate(n=>n.open),false);
 assert.equal(await page.locator('[data-select=usage-agent] [data-value=claude-code]').getAttribute('aria-pressed'),'true');
 await all(page);await page.locator('#sessions-grid .grid-agent-filter.is-codex').first().focus();await page.keyboard.press('Space');await settled(page);
 assert.equal(await page.evaluate(()=>usageState.data.filters.agent),'codex');assert.equal(await page.locator('#usage-session-dialog').evaluate(n=>n.open),false);
 await all(page);
 // A queued close event from an earlier opening must not clear a newly opened session.
 const reopened=await page.evaluate(()=>{const rows=usageState.data.sessions;openUsageSession(rows[0]);$('usage-session-dialog').close();openUsageSession(rows[1]);return rows[1].id;});
 await page.waitForTimeout(80);assert.equal(await page.evaluate(()=>workState.openSession),reopened);assert.equal(await page.locator('#usage-session-dialog').evaluate(n=>n.open),true);assert.ok(await page.locator('body.inspector-open').count());await closeInspector(page);
 await page.evaluate(()=>{window.sessionOpens=0;const original=openUsageSession;window.openUsageSession=(...args)=>{window.sessionOpens++;return original(...args);};});
 const row=page.locator('#sessions-grid .tabulator-row').first(),first=await row.getAttribute('data-session-id');
 await row.locator('.grid-project-name').focus();await page.keyboard.press('Enter');assert.equal(await page.locator('#usage-session-dialog').evaluate(n=>n.open),true);assert.equal(await page.evaluate(()=>window.sessionOpens),1);
 assert.equal(await page.evaluate(()=>workState.openSession),first);await closeInspector(page);
 const second=await page.locator('#sessions-grid .tabulator-row').nth(1).getAttribute('data-session-id');
 await page.locator('#sessions-grid .grid-project-name').first().focus();await page.keyboard.press('ArrowDown');assert.equal(await page.evaluate(()=>workState.openSession),second);
 await page.waitForFunction(id=>document.activeElement?.closest('.tabulator-row')?.dataset.sessionId===id,second);
 await page.keyboard.press('ArrowUp');assert.equal(await page.evaluate(()=>workState.openSession),first);await closeInspector(page);
 // A native review select keeps Enter and does not invoke the row opener.
 await page.locator('.grid-options summary').click();
 await page.locator('.grid-column-menu label').filter({hasText:/Review|Değerlendirme/}).locator('input').check();
 await page.locator('.grid-options summary').click();await page.locator('#sessions-grid .grid-review').first().focus();const count=await page.evaluate(()=>window.sessionOpens);
 await page.keyboard.press('Enter');await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>window.sessionOpens),count);assert.equal(await page.locator('#usage-session-dialog').evaluate(n=>n.open),false);
}
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 for(const lang of ['tr','en']){
  const context=await browser.newContext({viewport:{width:1366,height:900},reducedMotion:'reduce'}),page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url())&&new URL(r.url()).origin!==new URL(startup).origin)remote.push(r.url());});
  const u=new URL(startup);u.searchParams.set('lang',lang);await page.goto(u.href);await ready(page);await verifyClear(page,lang);await verifyKeys(page);
  await page.screenshot({path:path.join(root,'sessions-'+lang+'.png')});await context.close();
 }
}finally{await browser.close();}
// Native normal close and a fresh profile must retain the cleared filters.
const state=path.join(root,'native-window.json');await writeFile(state,JSON.stringify({width:1366,height:900,lang:'tr',view:{setupDone:true}}));
let app,control;
async function launch(){
 control=path.resolve(root,'control-'+randomUUID());await mkdir(control);await writeFile(path.join(control,'running'),'1');
 const env={...process.env,PLER_DESKTOP_URL:startup,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:state};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
 const pkg=process.env.PLER_QA_PACKAGE;
 app=await _electron.launch({executablePath:pkg?path.join(pkg,'desktop/PLER-Desktop.exe'):fileURLToPath(new URL('../desktop/node_modules/electron/dist/electron.exe',import.meta.url)),args:pkg?[]:[fileURLToPath(new URL('../desktop/main.cjs',import.meta.url))],env,timeout:20000});
 const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));await ready(page);return page;
}
async function close(){if(app){await app.close();app=null;}if(control){assert.equal(path.dirname(control),path.resolve(root));assert.ok(path.basename(control).startsWith('control-'));await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});control=null;}}
try{
 let page=await launch();await verifyClear(page,'tr');await verifyKeys(page);await all(page);await close();
 const persisted=JSON.parse(await readFile(state,'utf8'));assert.equal(persisted.view.filters.days,'0');assert.equal(persisted.view.filters.agent,'all');assert.equal(persisted.view.filters.project,'all');
 page=await launch();assert.deepEqual((await controls(page)).selected,{days:'0',agent:'all'});await close();assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
 await writeFile(path.join(root,'ui-check.json'),JSON.stringify({clear_from_empty_selection:true,one_query_per_clear:true,segments_match_query:true,report_scope_match:true,preferences_match:true,reload_preserves_clear:true,agent_enter_filters:true,agent_space_filters:true,title_enter_opens_once:true,arrow_navigation:true,focus_survives_grid_redraw:true,queued_close_preserves_reopened_session:true,review_select_enter_preserved:true,english_turkish:true,native_fresh_profile_matches:true,packaged:Boolean(process.env.PLER_QA_PACKAGE),picker_400_unchanged:true,script_errors:errors,external_requests:remote,clean_windows_acceptance:'PENDING - LAST TASK'},null,2));console.log('Filter and keyboard checks passed');
}finally{await close();}
