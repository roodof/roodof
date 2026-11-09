import {chromium} from 'playwright';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_SETTINGS_ROOT);
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim();
const browser=await chromium.launch({channel:'msedge',headless:true});
const errors=[],remote=[],results=[];
async function ready(page){await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading&&document.querySelector('.settings-tabs'));if(await page.locator('#first-use').isVisible())await page.locator('.first-use-actions .primary').click();await page.waitForFunction(()=>!usageState.loading);}
async function group(page,key){await page.locator('#settings-tab-'+key).click();await page.waitForFunction(key=>document.querySelector('#settings-tab-'+key).getAttribute('aria-selected')==='true',key);}
async function visibleGroup(page,key){assert.deepEqual(await page.locator('.settings-group:visible').evaluateAll(nodes=>nodes.map(n=>n.dataset.settingsGroup)),[key]);}
try{
 for(const lang of ['tr','en']){
  const local=lang==='tr',page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(new URL(r.url()).origin!==new URL(startup).origin)remote.push(new URL(r.url()).origin);});
  const url=new URL(startup);url.searchParams.set('lang',lang);await page.goto(url.href);await ready(page);
  await page.locator('.grid-project-name').first().click();const session=await page.evaluate(()=>workState.openSession);
  assert.equal(await page.locator('#usage-session-work-editor').evaluate(n=>n.open),false);
  assert.equal(await page.locator('#usage-session-work-title').isVisible(),false);
  await page.screenshot({path:path.join(root,'compact-session-'+lang+'.png')});
  await page.locator('#usage-session-work-toggle').focus();await page.keyboard.press('Enter');
  // With no remaining work to link, creating is the sole visible form.
  const title='Release flow '+lang+' '+Date.now();
  const createMode=page.locator('.session-work-modes [data-mode=new]');if(await createMode.isVisible())await createMode.click();
  await page.locator('#usage-session-work-title').fill(title);
  await page.locator('#usage-session-work-toggle').click();await page.locator('#usage-session-work-toggle').click();assert.equal(await page.locator('#usage-session-work-title').inputValue(),title);
  await page.route('**/api/usage/work?*',route=>route.request().method()==='POST'?route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({error:'Invented conflict',code:'conflict'})}):route.continue());
  await page.locator('#usage-session-work-create').click();await page.waitForFunction(()=>!usageState.workBusy&&document.querySelector('#usage-session-work-status').textContent);
  assert.equal(await page.locator('#usage-session-work-title').inputValue(),title);await page.unrouteAll();
  await page.locator('#usage-session-work-create').click();await page.waitForFunction(title=>!usageState.workBusy&&usageState.data.work_items.items.some(w=>w.title===title),title);
  const work=await page.evaluate(title=>usageState.data.work_items.items.find(w=>w.title===title).id,title);
  assert.ok(await page.locator('#usage-session-work-items .work-member').filter({hasText:title}).isVisible());
  await page.keyboard.press('Escape');await page.locator('.grid-project-name').nth(1).click();const second=await page.evaluate(()=>workState.openSession);
  await page.locator('#usage-session-work-toggle').click();
  await page.locator('.session-work-modes [data-mode=existing]').click();
  assert.ok(await page.locator('#usage-session-work-select').isVisible());assert.equal(await page.locator('#usage-session-work-title').isVisible(),false);
  await page.locator('#usage-session-work-select').selectOption(work);
  await page.locator('.session-work-modes [data-mode=new]').click();await page.locator('#usage-session-work-title').fill('Preserved '+lang);
  await page.locator('.session-work-modes [data-mode=existing]').click();assert.equal(await page.locator('#usage-session-work-select').inputValue(),work);
  await page.locator('#usage-session-work-link').click();await page.waitForFunction(({work,second})=>!usageState.workBusy&&usageState.data.work_items.items.find(w=>w.id===work).session_ids.includes(second),{work,second});
  await page.screenshot({path:path.join(root,'linked-session-'+lang+'.png')});
  // Real Add sessions entrypoint keeps its chosen work and opens the compact editor.
  await page.keyboard.press('Escape');await page.locator('[data-route=work]').click();
  await page.evaluate(id=>{workState.selected=id;renderSelectedWork();},work);await page.locator('.wb-add-sessions').click();
  const target=await page.evaluate(({session,second})=>plerUI.get().sessions.items.find(s=>s.id!==session&&s.id!==second).id,{session,second});
  await page.evaluate(id=>openUsageSession(usageState.data.sessions.find(s=>s.id===id)),target);
  assert.ok(await page.locator('#usage-session-work-editor').evaluate(n=>n.open));assert.equal(await page.locator('#usage-session-work-select').inputValue(),work);
  await page.keyboard.press('Escape');await page.locator('.wb-link-banner button').click();
  await page.locator('[data-route=settings]').click();await visibleGroup(page,'sources');
  assert.equal(await page.getByRole('tab').count(),3);
  const posts=[];const capture=r=>{if(r.method()==='POST')posts.push(new URL(r.url()).pathname);};page.on('request',capture);
  await page.locator('#settings-tab-sources').focus();await page.keyboard.press('ArrowRight');await visibleGroup(page,'alerts');
  assert.equal(await page.locator('#settings-tab-alerts').evaluate(n=>n===document.activeElement),true);
  await page.keyboard.press('End');await visibleGroup(page,'support');assert.equal(await page.locator('#settings-tab-support').getAttribute('tabindex'),'0');
  assert.equal(await page.locator('.settings-tool[open]').count(),0);
  await page.screenshot({path:path.join(root,'settings-'+lang+'.png')});
  await group(page,'sources');await page.locator('#source-path').fill('C:\\invented\\draft-'+lang);
  await group(page,'alerts');await group(page,'sources');assert.equal(await page.locator('#source-path').inputValue(),'C:\\invented\\draft-'+lang);
  page.off('request',capture);assert.deepEqual(posts,[]);
  await group(page,'alerts');await page.locator('.budget-add').click();assert.equal(await page.locator('body').getAttribute('data-screen'),'sessions');assert.ok(await page.locator('#usage-session-search').evaluate(n=>n===document.activeElement));await page.locator('[data-route=settings]').click();
  // Shortcuts reveal the correct tab and enclosing disclosure before focusing content.
  await page.evaluate(()=>document.dispatchEvent(new CustomEvent('pler-open-diagnostics')));await visibleGroup(page,'support');assert.ok(await page.locator('#diagnostics').isVisible());
  assert.ok(await page.locator('[data-settings-tool=diagnostics]').evaluate(n=>n.open));
  await page.locator('#diagnostics .diagnostics-actions button').last().click();await visibleGroup(page,'sources');assert.ok(await page.locator('#source-folders').isVisible());
  await page.evaluate(()=>document.dispatchEvent(new CustomEvent('pler-reconnect-record')));await visibleGroup(page,'support');assert.ok(await page.locator('#session-reconnections').isVisible());
  // Backup preview/restore controls are reachable in the new group without touching current history.
  const backup=page.locator('[data-settings-tool=backup]');await backup.locator(':scope > summary').click();
  await page.locator('#recovery-file').setInputFiles(path.join(root,'trusted-backup.zip'));await page.locator('#recovery-inspect').click();await page.locator('#recovery-details').waitFor();
  await group(page,'alerts');await group(page,'support');assert.ok(await page.locator('#recovery-details').isVisible());
  await page.locator('#recovery-parent').fill(root);await page.locator('#recovery-plan').click();await page.waitForFunction(()=>document.getElementById('recovery-target').textContent.includes('PLER-history-'));
  assert.equal(await page.locator('#recovery-restore').isDisabled(),true);
  await page.locator('#recovery-confirm').check();const total=await page.evaluate(()=>JSON.stringify(usageState.data.totals));
  await page.locator('#recovery-restore').click();await page.locator('#recovery-success').waitFor();assert.equal(await page.evaluate(()=>JSON.stringify(usageState.data.totals)),total);
  await page.setViewportSize({width:390,height:844});await backup.locator(':scope > summary').scrollIntoViewIfNeeded();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await page.screenshot({path:path.join(root,'narrow-settings-'+lang+'.png'),fullPage:true});
  await page.locator('[data-route=sessions]').click();await page.evaluate(id=>openUsageSession(usageState.data.sessions.find(s=>s.id===id)),second);
  if(!(await page.locator('#usage-session-work-editor').evaluate(n=>n.open)))await page.locator('#usage-session-work-toggle').click();await page.locator('#usage-session-dialog').evaluate(n=>n.scrollTop=0);await page.screenshot({path:path.join(root,'narrow-work-'+lang+'.png')});
  assert.ok(await page.locator('#usage-session-work-items').evaluate(n=>n.scrollWidth<=n.clientWidth+1));
  await page.keyboard.press('Escape');
  // A recovery-selection issue at startup must reveal the backup row automatically.
  await page.route('**/api/usage/recovery',async route=>{if(route.request().method()!=='GET')return route.continue();const response=await route.fetch();const data=await response.json();data.issue='missing';await route.fulfill({response,json:data});});
  await page.reload();await ready(page);await page.locator('#history-recovery').waitFor();await visibleGroup(page,'support');
  await page.unrouteAll();
  results.push({lang,compactWorkDefault:true,keyboardDisclosure:true,oneWorkForm:true,failedCreateKeepsDraft:true,createLinkMembership:true,modeDraftsKept:true,addSessionsPreselect:true,threeGroups:true,keyboardTabs:true,noCategoryWrite:true,sourceDraftKept:true,diagnosticSourceReconnectRoutes:true,backupPreviewSurvivesGroupChange:true,backupRestoreAndTotals:true,narrowNoOverflow:true,recoveryStartupIssueReveals:true});
  await page.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
 await writeFile(path.join(root,'ui-check.json'),JSON.stringify({results,scriptErrors:errors,remoteRequests:remote,cleanWindowsAcceptance:'PENDING - LAST TASK'},null,2));console.log('TR/EN grouped settings and compact work flow passed');
}catch(error){
 const states=[];for(const page of browser.contexts().flatMap(c=>c.pages())){await page.screenshot({path:path.join(root,'failure.png'),fullPage:true});states.push(await page.evaluate(()=>({screen:document.body.dataset.screen,settings:[...document.querySelectorAll('.settings-group:not([hidden])')].map(n=>n.dataset.settingsGroup),notice:document.getElementById('notice')?.textContent})));}
 await writeFile(path.join(root,'failure.json'),JSON.stringify({error:error.message.replace(/#access=[a-f0-9]+/g,'#access=REDACTED'),errors,states},null,2));throw error;
}finally{await browser.close();}
