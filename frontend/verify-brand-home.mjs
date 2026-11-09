import {chromium,_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_TERMS_ROOT),pkg=process.env.PLER_BRAND_PACKAGE;
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim();
const errors=[],results=[];let browser,app,control;
try{
 for(const lang of ['tr','en']){
  let page;
  if(pkg){
   control=path.join(root,'brand-control-'+lang);await mkdir(control);await writeFile(path.join(control,'running'),'1');const state=path.join(root,'brand-state.json');await writeFile(state,JSON.stringify({width:1440,height:950,lang,tour:true,view:{setupDone:true}}));
   const env={...process.env,PLER_DESKTOP_URL:startup,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:state};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
   app=await _electron.launch({executablePath:path.join(pkg,'desktop/PLER-Desktop.exe'),args:[],env});page=await app.firstWindow();
  }else{browser??=await chromium.launch({channel:'msedge',headless:true});page=await browser.newPage();const url=new URL(startup);url.searchParams.set('lang',lang);await page.goto(url.href);}
  page.on('pageerror',e=>errors.push(e.message));await page.waitForFunction(()=>typeof usageState!=='undefined'&&usageState.data?.has_snapshot&&!usageState.loading&&document.querySelector('.settings-tabs'));
  if(await page.locator('#first-use').isVisible())await page.locator('#first-use-next').click();await page.waitForFunction(()=>!usageState.loading);
  await page.locator('[data-route=settings]').click();await page.locator('#settings-tab-sources').click();await page.locator('#source-path').fill('C:\\invented\\unsaved-brand-draft');
  const url=page.url(),totals=await page.evaluate(()=>JSON.stringify(usageState.data.totals));
  await page.evaluate(()=>{window.__brandDocumentMarker='same-document';});let navigations=0,posts=0;
  page.on('framenavigated',f=>{if(f===page.mainFrame())navigations++;});page.on('request',r=>{if(r.method()==='POST')posts++;});
  for(const keyboard of [false,true]){
   if(keyboard){await page.locator('[data-route=work]').click();await page.locator('.ws-brand').focus();await page.keyboard.press('Enter');}else await page.locator('.ws-brand').click();
   await page.waitForFunction(()=>document.body.dataset.screen==='sessions');
   assert.equal(await page.evaluate(()=>window.__brandDocumentMarker),'same-document');assert.equal(navigations,0);assert.equal(page.url(),url);assert.equal(await page.evaluate(()=>document.documentElement.lang),lang);
   assert.ok(await page.locator('.ws-sidebar').isVisible());assert.ok(await page.locator('#usage-session-grid').count()||await page.locator('.tabulator').count());
   assert.equal(await page.evaluate(()=>JSON.stringify(usageState.data.totals)),totals);
  }
  await page.locator('[data-route=settings]').click();assert.equal(await page.locator('#source-path').inputValue(),'C:\\invented\\unsaved-brand-draft');assert.equal(posts,0);
  results.push({lang,mouseAndEnter:true,noDocumentReload:true,modernUiRetained:true,languageUrlTotalsAndDraftPreserved:true,noPosts:true});
  if(app){await app.close();app=null;assert.equal(path.dirname(control),root);await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});control=null;}else await page.close();
 }
 assert.deepEqual(errors,[]);await writeFile(path.join(root,pkg?'brand-desktop-check.json':'brand-ui-check.json'),JSON.stringify({results,scriptErrors:errors,packagedDesktop:Boolean(pkg)},null,2));console.log('TR/EN brand mouse/Enter regression passed');
}finally{if(app)await app.close();if(browser)await browser.close();if(control){assert.equal(path.dirname(control),root);await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});}}
