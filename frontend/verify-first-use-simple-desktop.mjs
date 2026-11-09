import {_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_FIRST_ROOT),pkg=path.resolve(process.env.PLER_FIRST_PACKAGE);
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim(),state=path.join(root,'desktop-state.json');
await writeFile(path.join(root,'mode.txt'),'ready');await writeFile(state,JSON.stringify({width:1440,height:950,lang:'tr',tour:true}));
let app,control;const errors=[];
async function launch(){
 control=path.join(root,'desktop-control-'+randomUUID());await mkdir(control);await writeFile(path.join(control,'running'),'1');
 const env={...process.env,PLER_DESKTOP_URL:startup,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:state};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
 app=await _electron.launch({executablePath:path.join(pkg,'desktop/PLER-Desktop.exe'),args:[],env,timeout:20000});const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading&&document.querySelector('#first-use-next'));return page;
}
async function close(){if(app){await app.close();app=null;}if(control){assert.equal(path.dirname(control),root);assert.ok(path.basename(control).startsWith('desktop-control-'));await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});control=null;}}
try{
 let page=await launch();await page.evaluate(()=>refreshUsage());await page.waitForFunction(()=>usageState.data?.state==='ready'&&!usageState.loading);
 assert.equal(await page.evaluate(()=>usageState.data.version),'0.9.17');assert.equal(await page.locator('#first-use-next').textContent(),'Oturumlarını gör');assert.equal(await page.locator('#first-use button:visible').count(),1);
 assert.equal(await page.evaluate(()=>usageState.data.setup.sessions),3);assert.equal(await page.evaluate(()=>usageState.data.totals.sessions),2);
 await page.screenshot({path:path.join(root,'desktop-first-use-tr.png')});await page.locator('#first-use-next').click();await page.waitForFunction(()=>usageState.data.filters.days===0&&!usageState.loading);assert.equal(await page.evaluate(()=>usageState.data.totals.sessions),3);await close();
 assert.equal(JSON.parse(await readFile(state,'utf8')).view.setupDone,true);
 page=await launch();assert.ok(await page.locator('#first-use').isHidden());assert.equal(await page.evaluate(()=>plerGetViewPreferences().setupDone),true);assert.equal(await page.locator('.driver-popover').count(),0);
 await page.locator('[data-route=settings]').click();await page.locator('#settings-tab-sources').click();await page.locator('.first-use-tour').click();await page.locator('.driver-popover').waitFor();await page.keyboard.press('Escape');await page.locator('.driver-popover').waitFor({state:'hidden'});
 await close();assert.deepEqual(errors,[]);
 await writeFile(path.join(root,'desktop-check.json'),JSON.stringify({version:'0.9.17',actualPackagedElectron:true,packagedAssets:true,inventedSourcesOnly:true,onePrimary:true,setupCountIgnoresPeriod:true,allTimeSessionEntry:true,normalCloseSavesCompletion:true,freshProfileRemembersCompletion:true,noAutoTour:true,explicitTourStillWorks:true,scriptErrors:errors,acceptance:'Independent users and clean Windows remain LAST'},null,2));console.log('Packaged Electron first-use and remembered completion passed');
}finally{await close();}
