import {chromium,_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const report=fileURLToPath(new URL('../../reports/log-sources-v1/',import.meta.url));
const root=path.resolve(process.env.PLER_SOURCE_QA_ROOT||path.join(report,'source-ui'));
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim(),errors=[];
const extra=path.join(root,'fixtures/özel & kayıtlar/.codex');
const claude=path.join(root,'fixtures/Claude özel/.claude');
const browser=await chromium.launch({channel:'msedge',headless:true});
async function settled(page,count){await page.waitForFunction(n=>usageState.data?.has_snapshot&&usageState.data.state==='ready'&&!usageState.loading&&usageState.data.setup.sessions===n,count);}
async function addFolder(page,value){await page.locator('#source-path').fill(value);await page.locator('#source-check').click();await page.waitForFunction(()=>!document.querySelector('#source-add').disabled);await page.locator('#source-add').click();}
try{
 const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});page.on('pageerror',e=>errors.push(e.message));
 const url=new URL(startup);url.searchParams.set('lang','tr');await page.goto(url.href);await settled(page,1);
 await page.locator('#first-use-manage-sources').click();await page.locator('#source-folders').waitFor({state:'visible'});await page.waitForFunction(()=>!document.querySelector('#source-agent').disabled);
 assert.ok(await page.locator('#source-browse').isHidden());
 await page.locator('#source-agent').selectOption('codex');
 await page.locator('#source-path').fill(path.join(root,'missing-folder'));await page.locator('#source-check').click();await page.waitForFunction(()=>document.querySelector('#source-message').dataset.state==='error');assert.match(await page.locator('#source-message').textContent(),/bulunamadı/);assert.ok(await page.locator('#source-add').isDisabled());
 await addFolder(page,extra);await settled(page,3);assert.equal(await page.locator('.source-folder-row').count(),2);
 await page.locator('#source-agent').selectOption('claude-code');await addFolder(page,claude);await settled(page,4);assert.equal(await page.locator('.source-folder-row').count(),3);
 await page.screenshot({path:path.join(root,'sources-tr.png'),fullPage:true});
 await page.locator('#lang-toggle').click();await page.waitForSelector('html[lang=en]');await settled(page,4);await page.locator('[data-route=settings]').click();await page.waitForFunction(()=>document.querySelectorAll('.source-folder-row').length===3);
 assert.match(await page.locator('#source-folders h2').textContent(),/Log folders/);
 await page.locator('.source-guidance summary').click();assert.match(await page.locator('.source-guidance').textContent(),/Private backups can contain source paths/);
 for(const [lang,phrase] of [['en','Private backups can contain source paths'],['tr','Özel yedek, saklanan geçmişteki kaynak yollarını içerebilir']]){const help=await page.request.get(new URL('/help?lang='+lang,startup).href);assert.ok((await help.text()).includes(phrase));}
 await page.locator('#source-path').fill('\\\\example.invalid\\share');await page.locator('#source-check').click();await page.waitForFunction(()=>document.querySelector('#source-message').dataset.state==='error');assert.match(await page.locator('#source-message').textContent(),/Network shares/);
 await page.locator('.source-folder-row').filter({hasText:'Claude Code'}).locator('.source-remove').click();await settled(page,3);assert.equal(await page.locator('.source-folder-row').count(),2);
 await page.reload();await settled(page,3);await page.locator('[data-route=settings]').click();await page.waitForFunction(()=>document.querySelectorAll('.source-folder-row').length===2);
 assert.equal(await page.locator('.source-folder-row').filter({hasText:'Claude Code'}).count(),0);
 assert.ok(!(await page.evaluate(()=>JSON.stringify(usageState.data))).includes('özel & kayıtlar'));
 await page.setViewportSize({width:420,height:800});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await page.screenshot({path:path.join(root,'sources-mobile.png'),fullPage:true});
 await page.close();
}finally{await browser.close();}
// Native shell + the actual isolated preload/IPC. The dialog result is synthetic;
// real OS folder-dialog interaction and live WSL remain final machine acceptance.
const state=path.join(root,'native-window.json');await writeFile(state,JSON.stringify({width:1366,height:900,lang:'tr',tour:true,view:{setupDone:true,section:'settings'}}));
let app,control;
async function close(){if(app){await app.close();app=null;}if(control){assert.equal(path.dirname(control),root);assert.ok(path.basename(control).startsWith('control-'));await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});control=null;}}
async function launch(count=3){
 control=path.join(root,'control-'+randomUUID());await mkdir(control);await writeFile(path.join(control,'running'),'1');
 const env={...process.env,PLER_DESKTOP_URL:startup,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:state};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
 const pkg=process.env.PLER_QA_PACKAGE;
 app=await _electron.launch({executablePath:pkg?path.join(pkg,'desktop/PLER-Desktop.exe'):fileURLToPath(new URL('../desktop/node_modules/electron/dist/electron.exe',import.meta.url)),args:pkg?[]:[fileURLToPath(new URL('../desktop/main.cjs',import.meta.url))],env,timeout:20000});
 const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));await settled(page,count);if(await page.locator('#first-use').isVisible())await page.locator('.first-use-actions .primary').click();await page.locator('[data-route=settings]').click();await page.waitForFunction(()=>!document.querySelector('#source-agent').disabled);return page;
}
try{
 let page=await launch();assert.ok(await page.locator('#source-browse').isVisible());
 assert.deepEqual(await page.evaluate(()=>Object.keys(window.plerDesktop)),['chooseLogFolder']);
 assert.equal(await page.evaluate(()=>typeof window.require),'undefined');
 await app.evaluate(({dialog},chosen)=>{dialog.showOpenDialog=async(_parent,options)=>{if(options.properties.join(',')!=='openDirectory,dontAddToRecent')throw new Error('unexpected picker');return {canceled:false,filePaths:[chosen]};};},claude);
 await page.locator('#source-agent').selectOption('claude-code');await page.locator('#source-browse').click();await page.waitForFunction(value=>document.querySelector('#source-path').value===value,claude);await page.locator('#source-check').click();await page.waitForFunction(()=>!document.querySelector('#source-add').disabled);await page.locator('#source-add').click();await settled(page,4);
 const preferences=await app.evaluate(({BrowserWindow})=>{const w=BrowserWindow.getAllWindows()[0];const p=w.webContents.getLastWebPreferences();return {nodeIntegration:p.nodeIntegration,contextIsolation:p.contextIsolation,sandbox:p.sandbox,webSecurity:p.webSecurity};});assert.deepEqual(preferences,{nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true});
 await page.screenshot({path:path.join(root,'native-sources.png')});await close();
 page=await launch(4); // restored source preferences live in the server data folder
 await settled(page,4);await page.waitForFunction(()=>document.querySelectorAll('.source-folder-row').length===3);
 await page.locator('.source-folder-row').filter({hasText:'Claude Code'}).locator('.source-remove').click();await settled(page,3);await close();
 assert.deepEqual(errors,[]);
 await writeFile(path.join(root,'ui-check.json'),JSON.stringify({browser_tr_en_add_check_remove:true,automatic_additive_counts:[1,3,4,3],unicode_ampersand_paths:true,invalid_network_rejected:true,source_paths_omitted_from_report:true,private_backup_copy_accurate:true,reload_persistent:true,mobile_no_overflow:true,native_preload_ipc:true,native_picker_result:'mocked dialog result through real preload/IPC',native_reopen:true,renderer_preferences:preferences,packaged:Boolean(process.env.PLER_QA_PACKAGE),script_errors:errors,live_wsl:'not exercised; synthetic backend coverage',clean_windows_acceptance:'PENDING - LAST TASK'},null,2));
 console.log('Source-folder interface checks passed');
}finally{await close();}
