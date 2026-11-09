import {chromium} from 'playwright';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_TERMS_ROOT);
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim();
const browser=await chromium.launch({channel:'msedge',headless:true});
const errors=[],remote=[],results=[];
async function readable(page,selector){
 const result=await page.locator(selector).evaluate(root=>{
  const small=[],overflow=[];const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  while(walker.nextNode()){
   const node=walker.currentNode,el=node.parentElement;if(!node.textContent.trim()||!el.checkVisibility()||!el.getClientRects().length)continue;
   const range=document.createRange();range.selectNodeContents(node);if(!range.getBoundingClientRect().height)continue;
   const style=getComputedStyle(el);if(parseFloat(style.fontSize)<12)small.push({tag:el.tagName,cls:el.className,size:style.fontSize,text:node.textContent.trim().slice(0,90)});
  }
  for(const el of root.querySelectorAll('p,small,code,.ws-gauge-state,.recovery-path,.budget-readout')){
   if(el.checkVisibility()&&el.clientWidth&&el.scrollWidth>el.clientWidth+2)overflow.push({cls:el.className,width:el.clientWidth,scroll:el.scrollWidth});
  }
  return {small,overflow};
 });
 assert.deepEqual(result.small,[],selector+' small text');assert.deepEqual(result.overflow,[],selector+' overflow');
 return result;
}
async function screen(page,name){await page.locator('[data-route='+name+']').click();await page.waitForFunction(name=>document.body.dataset.screen===name,name);}
try{
 for(const lang of ['tr','en']){
  const local=lang==='tr',page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(new URL(r.url()).origin!==new URL(startup).origin)remote.push(new URL(r.url()).origin);});
  const url=new URL(startup);url.searchParams.set('lang',lang);await page.goto(url.href);
  await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading&&document.querySelector('.settings-tabs'));
  if(await page.locator('#first-use').isVisible())await page.locator('#first-use-next').click();
  await page.waitForFunction(()=>!usageState.loading);
  const limits=local?'Hesap kotaları':'Account limits',alert=local?'Kullanım uyarısı':'Usage alert',price=local?'API fiyat karşılığı':'API price equivalent';
  assert.equal(await page.locator('[data-route=quota]').getAttribute('aria-label'),limits);
  assert.equal(await page.locator('[data-route=quota] .ws-route-label').textContent(),limits);
  await page.keyboard.press('Control+k');await page.locator('.ws-palette input').fill(limits);
  assert.equal(await page.locator('.ws-command').count(),1);assert.equal(await page.locator('.ws-command').textContent(),limits);await page.keyboard.press('Enter');await page.locator('.ws-palette').waitFor({state:'hidden'});
  await screen(page,'quota');
  assert.ok(await page.locator('.ws-gauge-card').count());await readable(page,'.ws-page[data-page=quota]');
  await page.screenshot({path:path.join(root,'limits-'+lang+'.png')});
  const info=page.locator('#usage-quota .ws-info');if(await info.count()){await info.first().click();await page.locator('.ws-info-popup').waitFor();await readable(page,'.ws-info-popup');await page.keyboard.press('Escape');}
  await screen(page,'sessions');await page.locator('.grid-project-name').first().click();
  assert.equal(await page.locator('#session-budget h3').textContent(),alert);
  assert.equal(await page.locator('.wb-session-metrics>div:nth-child(2)>small:first-child').textContent(),price);
  await page.locator('.budget-editor>summary').click();await page.locator('#budget-metric').selectOption('usd');
  assert.ok((await page.locator('#budget-metric option:checked').textContent()).includes(price));
  assert.ok((await page.locator('#budget-metric-note').textContent()).includes(local?'fatura':'bill'));
  await readable(page,'#usage-session-detail');await page.screenshot({path:path.join(root,'session-'+lang+'.png')});await page.keyboard.press('Escape');
  await screen(page,'settings');await page.locator('#settings-tab-alerts').click();
  assert.equal(await page.locator('#budget-watch h2').textContent(),local?'Kullanım uyarıları':'Usage alerts');
  assert.equal(await page.locator('.budget-banner').getAttribute('aria-label'),local?'Kullanım uyarıları':'Usage alerts');
  await readable(page,'#settings-panel-alerts');
  await page.locator('#settings-tab-support').click();
  for(const key of ['backup','history','reconnect','diagnostics','report']){
   const row=page.locator('[data-settings-tool='+key+']');await row.locator(':scope>summary').click();await readable(page,'[data-settings-tool='+key+']');
  }
  await page.locator('#recovery-file').setInputFiles(path.join(root,'trusted-backup.zip'));await page.locator('#recovery-inspect').click();await page.locator('#recovery-details').waitFor();
  await page.locator('#recovery-parent').fill(root);await page.locator('#recovery-plan').click();await page.waitForFunction(()=>document.getElementById('recovery-target').textContent.includes('PLER-history-'));
  assert.equal(await page.locator('#recovery-restore').isDisabled(),true);
  await readable(page,'#settings-panel-support');await page.screenshot({path:path.join(root,'support-'+lang+'.png'),fullPage:true});
  await page.locator('#usage-update-open').click();await page.locator('#usage-update-dialog').waitFor();await readable(page,'#usage-update-dialog');
  assert.equal(await page.locator('#usage-update-dialog').evaluate(n=>getComputedStyle(n).paddingTop),'16px');
  assert.equal(await page.locator('#usage-update-auto').isChecked(),false);await page.screenshot({path:path.join(root,'updates-'+lang+'.png')});await page.locator('#usage-update-close').click();
  for(const width of [1000,390]){
   await page.setViewportSize({width,height:844});await readable(page,'#settings-panel-support');
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'support horizontal overflow');
   await screen(page,'quota');await readable(page,'.ws-page[data-page=quota]');
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'limits horizontal overflow');
   await page.screenshot({path:path.join(root,'limits-'+lang+'-'+width+'.png'),fullPage:true});await screen(page,'settings');
  }
  const help=new URL('/help',startup);help.searchParams.set('lang',lang);await page.goto(help.href);await page.locator('#terms').waitFor();
  assert.deepEqual(await page.locator('#terms dt').allTextContents(),[limits,alert,price]);
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:844});await readable(page,'body');
   assert.equal(await page.locator('body').evaluate(n=>getComputedStyle(n).backgroundColor),'rgb(16, 16, 18)');
   assert.equal(await page.locator('body').evaluate(n=>getComputedStyle(n).paddingLeft),'0px');
   assert.ok(await page.locator('.brand').isVisible());assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   await page.screenshot({path:path.join(root,'help-'+lang+'-'+width+'.png')});
  }
  results.push({lang,sharedNavigationAndPalette:true,providerLimitVsOwnAlert:true,canonicalPriceLabel:true,supportingTextMin12:true,backupPreviewAndConsent:true,updatesOfflineIdle:true,helpGlossaryAndTheme:true,widths:[1440,1000,390],noHorizontalOverflow:true});await page.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
 await writeFile(path.join(root,'ui-check.json'),JSON.stringify({version:'0.9.18',results,scriptErrors:errors,remoteRequests:remote,acceptance:'Developer fixtures only; real agents, users and clean Windows remain LAST'},null,2));
 console.log('TR/EN terminology and supporting-screen readability passed');
}catch(error){
 for(const page of browser.contexts().flatMap(c=>c.pages()))await page.screenshot({path:path.join(root,'failure.png'),fullPage:true});
 await writeFile(path.join(root,'failure.json'),JSON.stringify({error:error.message.replace(/#access=[a-f0-9]+/g,'#access=REDACTED'),scriptErrors:errors},null,2));throw error;
}finally{await browser.close();}
