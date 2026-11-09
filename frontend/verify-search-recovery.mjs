import {chromium} from 'playwright';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_SEARCH_ROOT),emptyRoot=path.resolve(process.env.PLER_SEARCH_EMPTY_ROOT);
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim(),emptyStartup=(await readFile(path.join(emptyRoot,'access.tmp'),'utf8')).trim();
const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],remote=[],results=[];
async function settled(page){await page.waitForFunction(()=>usageState.data?.has_snapshot&&usageState.data.state==='ready'&&!usageState.loading&&document.querySelector('#search-recovery-title'));}
async function scope(page,patch){await page.evaluate(async patch=>{plerUI.setFilters(patch);usageState.pageSize=20;await loadUsage();},patch);await settled(page);}
const filters=page=>page.evaluate(()=>plerUI.get().filters);
try{
 for(const lang of ['tr','en']){
  const local=lang==='tr',page=await browser.newPage({viewport:{width:1440,height:950},reducedMotion:'reduce'});
  await page.addInitScript(()=>sessionStorage.setItem('pler-ui-view-v1',JSON.stringify({setupDone:true,screen:'sessions',filters:{days:'0',agent:'all',project:'all'}})));
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(new URL(r.url()).origin!==new URL(startup).origin)remote.push(new URL(r.url()).origin);});
  const url=new URL(startup);url.searchParams.set('lang',lang);await page.goto(url.href);await settled(page);
  const projects=await page.evaluate(()=>({alpha:usageState.data.project_options.find(p=>p.name.includes('alpha')).id,beta:usageState.data.project_options.find(p=>p.name.includes('beta')).id}));
  await scope(page,{days:'7',agent:'codex',project:projects.alpha,sort:'tokens',quality:false,search:'needle-model'});
  await page.locator('#usage-search-empty').waitFor();assert.equal(await page.locator('#sessions-grid').isVisible(),false);
  await page.screenshot({path:path.join(root,'search-'+lang+'.png')});
  const gets=[],posts=[];const capture=r=>{const u=new URL(r.url());if(u.pathname==='/api/usage')gets.push(u);if(r.method()==='POST')posts.push(u.pathname);};page.on('request',capture);
  await page.locator('#search-recovery-period').click();await settled(page);await page.locator('.grid-project-name').waitFor();
  const f=await filters(page);assert.deepEqual({days:f.days,agent:f.agent,project:f.project,search:f.search,sort:f.sort},{days:'0',agent:'codex',project:projects.alpha,search:'needle-model',sort:'tokens'});
  assert.equal(gets.length,1);assert.deepEqual(posts,[]);assert.equal(gets[0].searchParams.has('search'),false);page.off('request',capture);
  assert.equal(await page.evaluate(()=>plerUI.get().sessions.total),1);
  assert.equal(await page.locator('[data-select=usage-period] [data-value="0"]').getAttribute('aria-pressed'),'true');
  assert.equal(await page.evaluate(()=>plerGetViewPreferences().filters.days),'0');
  assert.equal(await page.evaluate(()=>sessionStorage.getItem('pler-ui-view-v1').includes('needle-model')),false);
  // Removing a local quality filter requires no server read and keeps the query/scope.
  await scope(page,{quality:true});gets.length=0;page.on('request',capture);
  await page.locator('#search-recovery-quality').click();await page.locator('.grid-project-name').waitFor();page.off('request',capture);
  assert.equal(gets.length,0);assert.equal((await filters(page)).search,'needle-model');assert.equal((await filters(page)).quality,false);
  await scope(page,{quality:true,search:'not-a-session',sort:'started'});await page.locator('#usage-session-search').focus();await page.keyboard.press('Escape');
  assert.equal((await filters(page)).search,'');assert.equal((await filters(page)).quality,true);assert.equal((await filters(page)).sort,'started');
  // Base-scope emptiness uses the same one-constraint contract.
  await scope(page,{days:'7',agent:'claude-code',project:projects.alpha,quality:false,search:'needle-model'});
  await page.locator('#usage-empty').waitFor();await page.locator('#empty-recovery-period').click();await settled(page);
  assert.equal((await filters(page)).agent,'claude-code');assert.equal((await filters(page)).project,projects.alpha);assert.equal((await filters(page)).search,'needle-model');
  await page.locator('#empty-recovery-agent').click();await settled(page);await page.locator('.grid-project-name').waitFor();assert.equal((await filters(page)).agent,'all');assert.equal((await filters(page)).project,projects.alpha);
  await scope(page,{days:'0',agent:'codex',project:projects.beta,quality:false,search:'needle-model'});
  await page.locator('#empty-recovery-project').click();await settled(page);await page.locator('.grid-project-name').waitFor();assert.equal((await filters(page)).project,'all');assert.equal((await filters(page)).agent,'codex');assert.equal((await filters(page)).search,'needle-model');
  await scope(page,{days:'7',agent:'claude-code',project:projects.alpha,quality:true,search:'needle-model'});
  await page.locator('#usage-empty .search-recovery-more>summary').click();gets.length=0;page.on('request',capture);
  await page.locator('#usage-filter-clear').click();await settled(page);page.off('request',capture);
  assert.equal(gets.length,1);const reset=await filters(page);assert.deepEqual({days:reset.days,agent:reset.agent,project:reset.project,quality:reset.quality,search:reset.search},{days:'0',agent:'all',project:'all',quality:false,search:''});
  // A failed broaden keeps the user's new selection and offers a read-only retry.
  await scope(page,{days:'7',agent:'all',project:'all',search:'not-a-session'});
  await page.route('**/api/usage?*',route=>route.abort());await page.locator('#search-recovery-period').click();await page.waitForFunction(()=>plerUI.get().readError&&!usageState.loading);
  assert.match(await page.locator('#search-recovery-title').textContent(),local?/okunamadı/:/Could not read/);assert.equal((await filters(page)).days,'0');assert.equal((await filters(page)).search,'not-a-session');
  await page.screenshot({path:path.join(root,'retry-'+lang+'.png')});await page.unrouteAll();await page.locator('#search-recovery-retry').click();await settled(page);assert.equal(await page.evaluate(()=>plerUI.get().readError),false);
  await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await page.screenshot({path:path.join(root,'narrow-'+lang+'.png'),fullPage:true});
  await page.close();
  // The empty-source server never held any sessions. Exercise real empty/error projections.
  await writeFile(path.join(emptyRoot,'scenario.txt'),'empty');
  const empty=await browser.newPage({viewport:{width:1440,height:950},reducedMotion:'reduce'});empty.on('pageerror',e=>errors.push(e.message));
  await empty.addInitScript(()=>sessionStorage.setItem('pler-ui-view-v1',JSON.stringify({setupDone:true,screen:'sessions',filters:{days:'0',agent:'all',project:'all'}})));
  const emptyURL=new URL(emptyStartup);emptyURL.searchParams.set('lang',lang);await empty.goto(emptyURL.href);await settled(empty);await empty.evaluate(()=>refreshUsage());await settled(empty);
  await empty.locator('#usage-empty').waitFor();assert.ok(await empty.locator('#empty-recovery-source').isVisible());
  await empty.screenshot({path:path.join(root,'no-records-'+lang+'.png')});await empty.locator('#empty-recovery-source').click();assert.ok(await empty.locator('#source-folders').isVisible());assert.equal(await empty.locator('#settings-tab-sources').getAttribute('aria-selected'),'true');
  await empty.locator('[data-route=sessions]').click();await writeFile(path.join(emptyRoot,'scenario.txt'),'unreadable');await empty.evaluate(()=>refreshUsage());await settled(empty);
  assert.equal(await empty.evaluate(()=>usageState.data.sources.unreadable),1);await empty.locator('#empty-recovery-inspect').click();assert.ok(await empty.locator('#diagnostics').isVisible());
  await empty.locator('[data-route=sessions]').click();await writeFile(path.join(emptyRoot,'scenario.txt'),'unusable');await empty.evaluate(()=>refreshUsage());await settled(empty);
  assert.match(await empty.locator('#empty-recovery-title').textContent(),local?/Gösterilebilen/:/No usable/);assert.ok(await empty.locator('#empty-recovery-inspect').isVisible());
  await empty.close();
  results.push({lang,periodKeepsQueryAgentProjectSort:true,periodOneGetNoPost:true,periodSegmentAndPreferenceSync:true,queryNotPersistedOrSent:true,qualityLocalNoGet:true,clearKeepsQuality:true,baseEmptyPeriodAgentProjectRecovery:true,readFailureKeepsSelectionAndRetries:true,emptySourceShortcut:true,unreadableDiagnosticsShortcut:true,unusableRecordsAccurate:true,narrowNoOverflow:true});
 }
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
 await writeFile(path.join(root,'ui-check.json'),JSON.stringify({results,scriptErrors:errors,remoteRequests:remote,acceptance:'Invented developer fixtures; real users and clean Windows remain LAST'},null,2));console.log('TR/EN search recovery actions passed');
}catch(error){
 const states=[];for(const page of browser.contexts().flatMap(c=>c.pages())){await page.screenshot({path:path.join(root,'failure.png'),fullPage:true});states.push(await page.evaluate(()=>({screen:document.body.dataset.screen,title:document.getElementById('search-recovery-title')?.textContent,emptyTitle:document.getElementById('empty-recovery-title')?.textContent,notice:document.getElementById('notice')?.textContent})));}
 await writeFile(path.join(root,'failure.json'),JSON.stringify({error:error.message.replace(/#access=[a-f0-9]+/g,'#access=REDACTED'),errors,states},null,2));throw error;
}finally{await browser.close();}
