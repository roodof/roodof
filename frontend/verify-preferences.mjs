import {_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../../reports/view-preferences-v1/',import.meta.url));
const address=(await readFile(path.join(root,'access.tmp'),'utf8')).match(/http:\/\/127\.0\.0\.1:\d+\/#access=[a-f0-9]{64}/)[0];
const stateFile=path.join(root,'desktop-window.json');
const packaged=process.env.PLER_QA_PACKAGE;
await writeFile(stateFile,JSON.stringify({width:1366,height:900,lang:'en',tour:true}));
let app,control;const errors=[];
async function launch(){
 control=path.resolve(root,'control-'+randomUUID());await mkdir(control);await writeFile(path.join(control,'running'),'1');
 const env={...process.env,PLER_DESKTOP_URL:address,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:stateFile};
 delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
 app=await _electron.launch({executablePath:packaged?path.join(packaged,'desktop/PLER-Desktop.exe'):fileURLToPath(new URL('../desktop/node_modules/electron/dist/electron.exe',import.meta.url)),args:packaged?[]:[fileURLToPath(new URL('../desktop/main.cjs',import.meta.url))],env,timeout:20000});
 const page=await app.firstWindow();page.setDefaultTimeout(15000);page.on('pageerror',e=>errors.push(e.message));
 await page.waitForFunction(()=>typeof window.plerGetViewPreferences==='function'&&usageState.data?.has_snapshot&&!usageState.loading);
 return page;
}
async function close(){
 if(app){await app.close();app=null;}
 if(control){assert.equal(path.dirname(control),path.resolve(root));assert.ok(path.basename(control).startsWith('control-'));await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});control=null;}
}
try{
 let page=await launch();console.log('Native window loaded');await page.locator('[data-route=sessions]').click();await page.waitForSelector('.tabulator-row');
 async function resize(field,delta){const h=page.locator(`.tabulator-col[tabulator-field=${field}]`);const b=await h.boundingBox();await page.mouse.move(b.x+b.width-2,b.y+b.height/2);await page.mouse.down();await page.mouse.move(b.x+b.width+delta,b.y+b.height/2,{steps:12});await page.mouse.up();}
 await resize('project',-100);await resize('tokens',45);
 const preferred=await page.evaluate(()=>window.plerGetViewPreferences().columns.find(c=>c.field==='project').width);assert.ok(preferred>=260);
 await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].setSize(1000,760));await page.waitForTimeout(250);
 assert.equal(await page.evaluate(()=>window.plerGetViewPreferences().columns.find(c=>c.field==='project').width),preferred);
 await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].setSize(1366,900));await page.waitForTimeout(200);
 const model=await page.locator('.tabulator-col[tabulator-field=models]').boundingBox(),tokens=await page.locator('.tabulator-col[tabulator-field=tokens]').boundingBox();
 await page.mouse.move(model.x+30,model.y+model.height/2);await page.mouse.down();await page.waitForTimeout(300);await page.mouse.move(tokens.x+10,tokens.y+tokens.height/2,{steps:25});await page.waitForTimeout(300);await page.mouse.up();await page.waitForTimeout(300);
 await page.locator('.grid-options>summary').click();await page.locator('.grid-column-menu label').filter({hasText:/^Model calls$/}).locator('input').uncheck();await page.locator('.grid-options>summary').click();
 const modified=await page.evaluate(()=>window.plerGetViewPreferences());
 assert.ok(modified.columns.findIndex(c=>c.field==='models')<modified.columns.findIndex(c=>c.field==='tokens'),'column did not move');
 await page.locator('[data-select=usage-agent] [data-value=codex]').click();await page.waitForFunction(()=>!usageState.loading&&usageState.data.filters.agent==='codex');
 await page.locator('[data-select=usage-period] [data-value="7"]').click();await page.waitForFunction(()=>!usageState.loading&&usageState.data.filters.days===7);
 const project=await page.locator('#usage-project option').filter({hasText:'work/docs'}).getAttribute('value');await page.locator('#usage-project').selectOption(project);
 await page.waitForFunction(p=>!usageState.loading&&usageState.data.filters.project===p,project);
 await page.locator('#usage-session-sort').selectOption('tokens');await page.locator('#usage-quality-only').check();
 await page.locator('[data-route=settings]').click();await page.locator('#lang-toggle').click();await page.waitForSelector('html[lang=tr]');
 await page.waitForFunction(p=>!usageState.loading&&usageState.data?.filters.project===p,project);
 const wanted=await page.evaluate(()=>window.plerGetViewPreferences());assert.equal(wanted.screen,'settings');assert.equal(wanted.filters.quality,true);
 await close();const saved=JSON.parse(await readFile(stateFile,'utf8'));assert.deepEqual(saved.view,wanted);assert.equal(saved.lang,'tr');
 console.log('Saved native view; opening a fresh profile');page=await launch();
 await page.waitForFunction(p=>!usageState.loading&&usageState.data?.filters.project===p,project);
 assert.deepEqual(await page.evaluate(()=>window.plerGetViewPreferences()),wanted);
 assert.equal(await page.locator('html').getAttribute('lang'),'tr');assert.equal(await page.evaluate(()=>document.body.dataset.screen),'settings');
 await page.locator('[data-route=sessions]').click();await page.waitForSelector('.tabulator-row');
 assert.equal(await page.locator('#usage-session-sort').inputValue(),'tokens');assert.ok(await page.locator('#usage-quality-only').isChecked());
 assert.equal(await page.locator('.tabulator-col[tabulator-field=calls]').isVisible(),false);
 const width=(await page.locator('.tabulator-col[tabulator-field=tokens]').boundingBox()).width;
 assert.ok(Math.abs(width-wanted.columns.find(c=>c.field==='tokens').width)<2);
 await page.screenshot({path:path.join(root,'restored.png')});
 await page.locator('.grid-options>summary').click();await page.locator('.grid-reset').click();await page.locator('.grid-options>summary').click();
 const reset=await page.evaluate(()=>window.plerGetViewPreferences());assert.equal(reset.columns.find(c=>c.field==='project').width,undefined);await close();
 page=await launch();await page.waitForFunction(p=>!usageState.loading&&usageState.data?.filters.project===p,project);await page.locator('[data-route=sessions]').click();
 assert.ok(await page.locator('.tabulator-col[tabulator-field=calls]').isVisible());await close();
 await writeFile(stateFile,'{broken');page=await launch();
 const fallback=await page.evaluate(()=>window.plerGetViewPreferences());assert.equal(fallback.screen,'sessions');assert.equal(fallback.filters.agent,'all');assert.equal(fallback.filters.days,'30');await close();
 assert.deepEqual(errors,[]);
 await writeFile(path.join(root,'reopen-check.json'),JSON.stringify({packaged_application:Boolean(packaged),native_close_and_fresh_profile_restore:true,columns_reordered:true,column_visibility:true,column_widths:true,preferred_identity_width_survives_narrowing:true,agent_period_project_sort_quality:true,last_section:true,language_preserved:true,column_reset_survives_reopen:true,broken_file_fallback:true,script_errors:errors},null,2));console.log('Native view persistence checks passed');
}finally{await close();}
