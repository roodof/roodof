// Actual packaged Electron + packaged assets served with isolated invented records.
import {_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_FLOW_ROOT),pkg=path.resolve(process.env.PLER_FLOW_PACKAGE);
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim();
const control=path.join(root,'desktop-control-'+randomUUID()),state=path.join(root,'desktop-state.json');
await mkdir(control);await writeFile(path.join(control,'running'),'1');
await writeFile(state,JSON.stringify({width:1440,height:1000,lang:'tr',tour:true,view:{screen:'sessions',setupDone:true,filters:{days:'0',agent:'all',project:'all'}}}));
const env={...process.env,PLER_DESKTOP_URL:startup,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:state};
delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
const errors=[],remote=[];let app;
try{
 app=await _electron.launch({executablePath:path.join(pkg,'desktop/PLER-Desktop.exe'),args:[],env,timeout:20000});
 const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(new URL(r.url()).origin!==new URL(startup).origin)remote.push(new URL(r.url()).origin);});
 await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading&&document.querySelector('.grid-project-name'));
 assert.equal(await page.evaluate(()=>usageState.data.version),'0.9.14');
 await page.keyboard.press('/');assert.equal(await page.locator('#usage-session-search').evaluate(n=>n===document.activeElement),true);
 await page.locator('#usage-session-search').fill('· 122');await page.waitForFunction(()=>plerUI.get().sessions.items.length>0&&plerUI.get().sessions.items.every(s=>s.title.includes('· 122')));
 await page.locator('.grid-project-name').first().click();await page.locator('.wb-session-usage').waitFor();
 assert.equal(await page.locator('#budget-limit').isVisible(),false);
 await page.locator('.budget-editor>summary').click();await page.locator('.budget-preset').first().click();
 const limit=Number(await page.locator('#budget-limit').inputValue()),id=await page.evaluate(()=>workState.openSession);
 await page.getByRole('button',{name:'Uyarıyı kaydet',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('.budget-message').textContent.includes('kaydedildi'));
 assert.equal(await page.evaluate(async id=>(await api('/api/usage/budgets')).items.find(r=>r.id===id).limit,id),limit);
 assert.match(await page.locator('.budget-saved-label').textContent(),/Kaydedilmiş uyarı/);
 await page.locator('.budget-editor>summary').click();await page.screenshot({path:path.join(root,'desktop-flow-tr.png')});
 await page.locator('.wb-inspector-tools button').last().click();await page.waitForFunction(id=>workState.openSession!==id,id);
 await page.keyboard.press('Escape');assert.equal(await page.locator('#usage-session-dialog').evaluate(n=>n.open),false);
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
 await writeFile(path.join(root,'desktop-check.json'),JSON.stringify({version:'0.9.14',actualPackagedElectron:true,packagedAssets:true,inventedSourcesOnly:true,searchShortcut:true,searchBeyondFirstPage:true,usageThenAlert:true,presetSaveBackend:true,savedStateLabel:true,nextSession:true,escapeCloses:true,scriptErrors:errors,remoteRequests:remote,cleanWindowsAcceptance:'PENDING - LAST TASK'},null,2));
 console.log('Packaged Electron session flow passed');
}finally{
 if(app)await app.close();
 assert.equal(path.dirname(control),root);assert.ok(path.basename(control).startsWith('desktop-control-'));
 await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});
}
