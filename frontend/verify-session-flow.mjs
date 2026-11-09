import {chromium} from 'playwright';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_FLOW_ROOT);
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim();
const browser=await chromium.launch({channel:'msedge',headless:true});
const errors=[],remote=[],results=[];
const settle=async page=>{await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading&&document.querySelector('.grid-project-name'));};
const opened=async page=>{await page.waitForFunction(()=>document.querySelector('#usage-session-dialog').open&&document.querySelector('.wb-session-usage'));};
try{
 for(const lang of ['tr','en']){
  const local=lang==='tr';
  const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(new URL(r.url()).origin!==new URL(startup).origin)remote.push(new URL(r.url()).origin);});
  const url=new URL(startup);url.searchParams.set('lang',lang);await page.goto(url.href);await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading);
  if(await page.locator('#first-use').isVisible())await page.locator('.first-use-actions .primary').click();await settle(page);
  assert.equal(await page.locator('.tabulator-col[tabulator-field=models]').isVisible(),false);
  assert.equal(await page.locator('.tabulator-col[tabulator-field=calls]').isVisible(),false);
  await page.keyboard.press('/');assert.equal(await page.locator('#usage-session-search').evaluate(n=>n===document.activeElement),true);
  await page.locator('#usage-session-search').fill('· 122');
  await page.waitForFunction(()=>plerUI.get().sessions.items.length>0&&plerUI.get().sessions.items.every(s=>s.title.includes('· 122')));
  await page.locator('.grid-project-name').first().click();await opened(page);
  const id=await page.evaluate(()=>workState.openSession);
  assert.match(await page.locator('.session-usage-notes').textContent(),local?/gerçek faturan/:/actual bill/);
  assert.equal(await page.locator('.budget-editor').getAttribute('open'),null);
  assert.equal(await page.locator('#budget-limit').isVisible(),false);
  assert.equal(await page.locator('.wb-record-fields').getAttribute('open'),null);
  await page.screenshot({path:path.join(root,'flow-'+lang+'.png')});
  // Native details semantics: keyboard opens the editor without rebuilding its draft.
  await page.locator('.budget-editor>summary').focus();await page.keyboard.press('Enter');
  await page.locator('.budget-preset').nth(1).click();
  const chosen=Number(await page.locator('#budget-limit').inputValue());assert.ok(chosen>0);
  await page.locator('#budget-limit').fill('1');assert.ok(await page.locator('.budget-limit-warning').isVisible());
  await page.locator('#budget-limit').fill(String(chosen));
  await page.locator('.budget-editor>summary').click();await page.locator('.budget-editor>summary').click();
  assert.equal(Number(await page.locator('#budget-limit').inputValue()),chosen);
  await page.getByRole('button',{name:local?'Uyarıyı kaydet':'Save alert',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.budget-message').textContent.includes(document.documentElement.lang==='tr'?'kaydedildi':'saved'));
  const saved=await page.evaluate(async id=>(await api('/api/usage/budgets')).items.find(r=>r.id===id),id);assert.equal(saved.limit,chosen);
  await page.locator('#budget-limit').fill(String(chosen+100));
  await page.route('**/api/usage/budgets?*',route=>route.request().method()==='POST'?route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({ok:false,reason:'conflict'})}):route.continue());
  await page.getByRole('button',{name:local?'Uyarıyı kaydet':'Save alert',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.budget-message').textContent.includes(document.documentElement.lang==='tr'?'Kaydedilemedi':'Could not save'));
  assert.equal(Number(await page.locator('#budget-limit').inputValue()),chosen+100);
  assert.equal(await page.evaluate(async id=>(await api('/api/usage/budgets')).items.find(r=>r.id===id).limit,id),chosen);await page.unrouteAll();
  await page.locator('#budget-metric').selectOption('usd');
  assert.match(await page.locator('.budget-metric-note').textContent(),local?/Gerçek fatura/:/actual bill/);
  assert.match(await page.locator('.budget-preset').first().textContent(),/^\$/);
  await page.screenshot({path:path.join(root,'alert-'+lang+'.png')});
  // Explicit saved column choices keep precedence over the new defaults.
  await page.keyboard.press('Escape');await page.locator('.grid-options>summary').click();
  await page.locator('.grid-column-menu label').filter({hasText:local?'Modeller':'Models'}).locator('input').check();
  await page.reload();await settle(page);assert.equal(await page.locator('.tabulator-col[tabulator-field=models]').isVisible(),true);
  await page.locator('[data-route=settings]').click();await page.locator('#settings-tab-alerts').click();await page.locator('.budget-add').click();
  assert.equal(await page.locator('body').getAttribute('data-screen'),'sessions');assert.equal(await page.locator('#usage-session-search').evaluate(n=>n===document.activeElement),true);
  // Known, partial and unavailable prices remain visibly distinct. Rendering doesn't alter totals.
  const before=await page.evaluate(()=>usageState.data.totals.total_tokens);
  for(const [share,partial] of [[1,false],[.5,true],[0,false]]){
   await page.evaluate(({share,partial})=>{const s=structuredClone(usageState.data.sessions[0]);s.api_priced_share=share;s.api_usd=1.25;s.quality={...s.quality,tokens_complete:!partial};openUsageSession(s);},{share,partial});await opened(page);
   if(share)assert.match(await page.locator('.wb-session-metrics').textContent(),/1[.,]25/);
   else assert.match(await page.locator('.wb-session-metrics').textContent(),local?/Fiyat eksik/:/Price unavailable/);
   assert.equal(await page.locator('.session-usage-partial').count(),partial?1:0);
   if(share===.5)assert.match(await page.locator('.session-usage-notes').textContent(),/50/);
  }
  assert.equal(await page.evaluate(()=>usageState.data.totals.total_tokens),before);
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(root,'narrow-'+lang+'.png'),fullPage:true});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  assert.ok(await page.locator('#usage-session-dialog').evaluate(n=>n.scrollWidth<=n.clientWidth+1));
  await page.locator('.budget-editor>summary').click();await page.locator('.budget-preset').last().click();
  assert.ok(await page.locator('#session-budget').evaluate(n=>n.scrollWidth<=n.clientWidth+1));
  await page.keyboard.press('Escape');
  // No hidden-row allocation when 5000 records are projected. Scrolling still paints selection.
  await page.setViewportSize({width:1440,height:1000});
  await page.evaluate(()=>{usageState.pageSize=5000;renderUsageSessions();});await page.waitForTimeout(300);
  const count=await page.locator('.tabulator-row').count();assert.ok(count<100,'virtual rows must remain bounded: '+count);
  await page.locator('.grid-project-name').first().click();await opened(page);
  const first=await page.evaluate(()=>workState.openSession);
  await page.locator('.tabulator-tableholder').evaluate(n=>n.scrollTop=8000);await page.waitForTimeout(100);
  const selectedRow=await page.locator('.tabulator-row').last().getAttribute('data-session-id');
  await page.evaluate(id=>openUsageSession(usageState.data.sessions.find(s=>s.id===id)),selectedRow);
  await page.locator('.tabulator-tableholder').evaluate(n=>n.scrollTop=0);await page.waitForTimeout(100);
  assert.equal(await page.locator(`.tabulator-row[data-session-id="${first}"]`).getAttribute('aria-selected'),'false');
  results.push({lang,defaultColumns:true,searchBeyondFirstPage:true,keyboardSearch:true,readUsageBeforeAlert:true,keyboardEditor:true,presetAndReachedWarning:true,draftSurvivesToggleAndRejectedSave:true,savedThreshold:true,savedColumnsPreserved:true,settingsAlertEntry:true,partialPriceAndTokenLabels:true,unchangedAccountingTotals:true,narrowNoOverflow:true,virtualRows:count,offscreenSelectionFresh:true});
  await page.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
 await writeFile(path.join(root,'ui-check.json'),JSON.stringify({results,scriptErrors:errors,remoteRequests:remote,acceptance:'Developer fixtures only; clean Windows / real agents / real users remain LAST'},null,2));
 console.log('TR/EN session find, usage and alert flows passed');
}catch(error){
 const pages=browser.contexts().flatMap(context=>context.pages());
 const states=[];
 for(const page of pages){await page.screenshot({path:path.join(root,'failure.png'),fullPage:true});states.push(await page.evaluate(()=>({screen:document.body.dataset.screen,ready:typeof usageState==='undefined'?null:{loading:usageState.loading,state:usageState.data?.state,hasSnapshot:usageState.data?.has_snapshot},grid:document.querySelectorAll('.grid-project-name').length,notice:document.querySelector('#notice')?.textContent})));}
 await writeFile(path.join(root,'failure.json'),JSON.stringify({message:error.message.replace(/#access=[a-f0-9]+/g,'#access=REDACTED'),errors,states},null,2));throw error;
}finally{await browser.close();}
