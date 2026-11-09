import {chromium} from 'playwright';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_FIRST_ROOT),startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim();
const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],remote=[],results=[];
async function settled(page){await page.waitForFunction(()=>typeof plerGetViewPreferences==='function'&&!usageState.loading&&['ready','error'].includes(usageState.data?.state));}
async function mode(page,value){await writeFile(path.join(root,'mode.txt'),value);await page.evaluate(()=>refreshUsage());await settled(page);}
async function onePrimary(page,action,label){await page.waitForFunction(action=>document.getElementById('first-use')?.dataset.action===action,action);assert.equal(await page.locator('#first-use button.primary:visible').count(),1);assert.equal(await page.locator('#first-use button:visible').count(),1);assert.equal(await page.locator('#first-use-next').textContent(),label);}
try{
 for(const lang of ['tr','en']){
  const local=lang==='tr',page=await browser.newPage({viewport:{width:1440,height:950},reducedMotion:'reduce'});
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(new URL(r.url()).origin!==new URL(startup).origin)remote.push(new URL(r.url()).origin);});
  const url=new URL(startup);url.searchParams.set('lang',lang);await page.goto(url.href);await settled(page);
  await mode(page,'error');await onePrimary(page,'inspect',local?'Sorunu incele':'Inspect the issue');assert.equal(await page.locator('#first-use-next').isEnabled(),true);
  await page.locator('#first-use-next').click();assert.ok(await page.locator('#diagnostics').isVisible());assert.equal(await page.evaluate(()=>plerGetViewPreferences().setupDone),undefined);
  await page.locator('#settings-tab-sources').click();await page.locator('#first-use-reopen').click();
  await mode(page,'empty');await onePrimary(page,'sources',local?'Kayıt klasörü ekle':'Add a log folder');
  assert.ok(await page.locator('#first-use-options').evaluate(n=>!n.open));await page.screenshot({path:path.join(root,'empty-'+lang+'.png')});
  await page.locator('#first-use-next').focus();await page.keyboard.press('Enter');assert.ok(await page.locator('#source-folders').isVisible());assert.equal(await page.evaluate(()=>plerGetViewPreferences().setupDone),undefined);
  await page.locator('#first-use-reopen').click();await mode(page,'unusable');await onePrimary(page,'inspect',local?'Sorunu incele':'Inspect the issue');
  assert.match(await page.locator('.first-use-status').textContent(),local?/dosyaları bulundu/:/files were found/);
  await mode(page,'partial');await onePrimary(page,'inspect',local?'Sorunu incele':'Inspect the issue');
  await page.locator('#first-use-options>summary').click();assert.ok(await page.locator('#first-use-sessions').isEnabled());
  assert.match(await page.locator('#first-use-sessions').textContent(),local?/Bulunabilen/:/available/);
  await page.locator('#first-use-sessions').click();await settled(page);assert.ok(await page.locator('#first-use').isHidden());
  assert.equal(await page.evaluate(()=>plerGetViewPreferences().setupDone),true);
  await page.locator('[data-route=settings]').click();await page.locator('#settings-tab-sources').click();await page.locator('#first-use-reopen').click();
  await mode(page,'archive');if(await page.locator('#first-use-options').evaluate(n=>n.open))await page.locator('#first-use-options>summary').click();
  await onePrimary(page,'sessions',local?'Oturumlarını gör':'See your sessions');assert.match(await page.locator('[data-source-state=codex]').textContent(),local?/saklanan geçmişte/:/retained history/);
  await mode(page,'ready');await onePrimary(page,'sessions',local?'Oturumlarını gör':'See your sessions');
  assert.equal(await page.evaluate(()=>usageState.data.setup.sessions),3);assert.equal(await page.locator('.driver-popover').count(),0);
  await page.screenshot({path:path.join(root,'ready-'+lang+'.png')});await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await page.screenshot({path:path.join(root,'narrow-'+lang+'.png'),fullPage:true});await page.setViewportSize({width:1440,height:950});
  // During a pending read the one next-step button stays locked, never becoming Add folder.
  let release;const gate=new Promise(resolve=>release=resolve);
  await page.route('**/api/usage?*',async route=>{await gate;await route.continue();});
  const pending=page.evaluate(()=>loadUsage());await page.waitForFunction(()=>usageState.loading);assert.equal(await page.locator('#first-use-next').isDisabled(),true);assert.equal(await page.locator('#first-use').getAttribute('data-action'),'reading');release();await pending;await page.unrouteAll();await settled(page);
  // A failed later read keeps prior sessions as an explicit alternative.
  await page.locator('#first-use-options>summary').click();await page.route('**/api/usage/refresh?*',route=>route.abort());await page.locator('#first-use-options .secondary').filter({hasText:local?'Kayıtları yeniden ara':'Look for records again'}).click();
  await page.waitForFunction(()=>usageState.readError&&!usageState.loading);assert.equal(await page.locator('#first-use').getAttribute('data-action'),'inspect');assert.ok(await page.locator('#first-use-sessions').isEnabled());await page.unrouteAll();await mode(page,'ready');
  if(await page.locator('#first-use-options').evaluate(n=>n.open))await page.locator('#first-use-options>summary').click();
  await page.locator('#first-use-next').click();await settled(page);assert.equal(await page.evaluate(()=>usageState.data.filters.days),0);assert.equal(await page.evaluate(()=>usageState.data.totals.sessions),3);
  await page.reload();await settled(page);assert.ok(await page.locator('#first-use').isHidden());
  results.push({lang,oneMainAction:true,errorOpensDiagnostics:true,emptyOpensSources:true,noPrematureSetupCompletion:true,unusableOpensIssue:true,partialKeepsAvailableSessions:true,retainedHistoryAccurate:true,countsIgnoreFilters:true,optionalControlsCollapsed:true,noAutoTour:true,readingLocksPrimary:true,failedRetryKeepsSnapshotAlternative:true,allTimeSessionEntry:true,reloadRemembersCompletion:true,narrowNoOverflow:true});await page.close();
 }
 // Skip is deliberately secondary and still counts as an explicit completion.
 const skip=await browser.newPage({viewport:{width:1440,height:950},reducedMotion:'reduce'});await skip.goto(startup);await settled(skip);await mode(skip,'empty');await skip.locator('#first-use-options>summary').click();await skip.locator('#first-use-options .quiet').filter({hasText:/Şimdilik geç|Skip for now/}).click();assert.ok(await skip.locator('#first-use').isHidden());assert.equal(await skip.evaluate(()=>plerGetViewPreferences().setupDone),true);await skip.close();
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);await writeFile(path.join(root,'ui-check.json'),JSON.stringify({results,explicitSkip:true,scriptErrors:errors,remoteRequests:remote,acceptance:'Invented developer cases; real-user and clean-Windows acceptance remain LAST'},null,2));console.log('TR/EN single-action first-use flow passed');
}catch(error){const states=[];for(const page of browser.contexts().flatMap(c=>c.pages())){await page.screenshot({path:path.join(root,'failure.png'),fullPage:true});states.push(await page.evaluate(()=>({screen:document.body.dataset.screen,action:document.getElementById('first-use')?.dataset.action,status:document.querySelector('.first-use-status')?.textContent})));}await writeFile(path.join(root,'failure.json'),JSON.stringify({error:error.message.replace(/#access=[a-f0-9]+/g,'#access=REDACTED'),errors,states},null,2));throw error;}finally{await browser.close();}
