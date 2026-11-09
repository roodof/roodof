import {_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_TERMS_ROOT),pkg=path.resolve(process.env.PLER_TERMS_PACKAGE);
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim(),state=path.join(root,'desktop-state.json');
let app,control;const errors=[],remote=[],results=[];
async function close(){if(app){await app.close();app=null;}if(control){assert.equal(path.dirname(control),root);assert.ok(path.basename(control).startsWith('desktop-control-'));await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});control=null;}}
try{
 for(const lang of ['tr','en']){
  const local=lang==='tr';await writeFile(state,JSON.stringify({width:1440,height:950,lang,tour:true,view:{setupDone:true}}));
  control=path.join(root,'desktop-control-'+randomUUID());await mkdir(control);await writeFile(path.join(control,'running'),'1');
  const env={...process.env,PLER_DESKTOP_URL:startup,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:state};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
  app=await _electron.launch({executablePath:path.join(pkg,'desktop/PLER-Desktop.exe'),args:[],env,timeout:20000});const page=await app.firstWindow();
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(new URL(r.url()).origin!==new URL(startup).origin)remote.push(new URL(r.url()).origin);});
  await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading&&document.querySelector('.settings-tabs'));
  assert.equal(await page.evaluate(()=>usageState.data.version),'0.9.18');assert.equal(await page.evaluate(()=>document.documentElement.lang),lang);
  assert.ok(await page.locator('#first-use').isHidden());
  const limits=local?'Hesap kotaları':'Account limits';
  assert.equal(await page.locator('[data-route=quota]').getAttribute('aria-label'),limits);
  await page.keyboard.press('Control+k');await page.locator('.ws-palette input').fill(limits);await page.keyboard.press('Enter');await page.locator('.ws-palette').waitFor({state:'hidden'});
  assert.equal(await page.locator('body').getAttribute('data-screen'),'quota');
  await page.locator('[data-route=sessions]').click();await page.locator('.grid-project-name').first().click();
  assert.equal(await page.locator('#session-budget h3').textContent(),local?'Kullanım uyarısı':'Usage alert');
  assert.equal(await page.locator('.wb-session-metrics>div:nth-child(2)>small:first-child').textContent(),local?'API fiyat karşılığı':'API price equivalent');
  assert.equal(await page.locator('#usage-session-detail .section-note').first().evaluate(n=>getComputedStyle(n).fontSize),'12px');
  await page.screenshot({path:path.join(root,'desktop-session-'+lang+'.png')});await page.keyboard.press('Escape');
  await page.locator('[data-route=settings]').click();await page.locator('#settings-tab-alerts').click();
  assert.equal(await page.locator('#budget-watch h2').textContent(),local?'Kullanım uyarıları':'Usage alerts');
  await page.locator('#usage-update-open').click();await page.locator('#usage-update-dialog').waitFor();
  assert.equal(await page.locator('#usage-update-dialog').evaluate(n=>getComputedStyle(n).paddingTop),'16px');
  assert.equal(await page.locator('#usage-update-auto').isChecked(),false);await page.locator('#usage-update-close').click();
  await close();results.push({lang,sharedNames:true,commandNavigation:true,sessionLabels:true,helperText12px:true,updatesCompactAndOffline:true,normalClose:true});
 }
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
 await writeFile(path.join(root,'desktop-check.json'),JSON.stringify({version:'0.9.18',actualPackagedElectron:true,packagedAssets:true,inventedSourcesOnly:true,results,scriptErrors:errors,remoteRequests:remote,acceptance:'Independent users and clean Windows remain LAST'},null,2));
 console.log('Packaged Electron TR/EN terminology and supporting screens passed');
}finally{await close();}
