import {_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_SEARCH_ROOT),pkg=path.resolve(process.env.PLER_SEARCH_PACKAGE);
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim();
const control=path.join(root,'desktop-control-'+randomUUID()),state=path.join(root,'desktop-state.json');
await mkdir(control);await writeFile(path.join(control,'running'),'1');await writeFile(state,JSON.stringify({width:1440,height:950,lang:'tr',tour:true,view:{screen:'sessions',setupDone:true,filters:{days:'0',agent:'all',project:'all'}}}));
const env={...process.env,PLER_DESKTOP_URL:startup,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:state};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
let app;const errors=[];
try{
 app=await _electron.launch({executablePath:path.join(pkg,'desktop/PLER-Desktop.exe'),args:[],env,timeout:20000});
 const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading&&document.querySelector('#search-recovery-title'));
 assert.equal(await page.evaluate(()=>usageState.data.version),'0.9.16');
 const project=await page.evaluate(()=>usageState.data.project_options.find(p=>p.name.includes('alpha')).id);
 await page.evaluate(async project=>{plerUI.setFilters({days:'7',agent:'codex',project,search:'needle-model'});await loadUsage();},project);
 await page.locator('#search-recovery-period').waitFor();await page.screenshot({path:path.join(root,'desktop-search-tr.png')});
 await page.locator('#search-recovery-period').click();await page.waitForFunction(()=>!usageState.loading&&plerUI.get().sessions.total===1);
 assert.deepEqual(await page.evaluate(()=>({days:plerUI.get().filters.days,agent:plerUI.get().filters.agent,project:plerUI.get().filters.project,search:plerUI.get().filters.search})),{days:'0',agent:'codex',project,search:'needle-model'});
 await page.locator('.grid-project-name').click();assert.equal(await page.locator('#usage-session-dialog').evaluate(n=>n.open),true);await page.keyboard.press('Escape');
 assert.deepEqual(errors,[]);
 await writeFile(path.join(root,'desktop-check.json'),JSON.stringify({version:'0.9.16',actualPackagedElectron:true,packagedAssets:true,inventedSourcesOnly:true,emptySearch:true,periodRecoveryKeepsQueryAgentProject:true,matchingSessionOpen:true,scriptErrors:errors,acceptance:'Clean Windows and independent users remain LAST'},null,2));console.log('Packaged Electron search recovery passed');
}finally{if(app)await app.close();assert.equal(path.dirname(control),root);assert.ok(path.basename(control).startsWith('desktop-control-'));await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});}
