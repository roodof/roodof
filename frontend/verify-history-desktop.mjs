import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../../reports/history-recovery-v1/',import.meta.url));
const proof=path.join(root,'desktop-proof');await mkdir(proof,{recursive:true});
const runtime=path.join(root,'candidate/PLER-0.9.13-windows-x64/runtime/python.exe');
let child,exitPromise,log='';let startup;const errors=[];
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function active(old=''){
 for(let i=0;i<200;i++){
  try{const value=(await readFile(path.join(proof,'access.tmp'),'utf8')).trim();
   if(value!==old){const health=await fetch(new URL('/api/health',value));if(health.status===200)return value;}}
  catch{}await pause(150);
 }throw Error('Packaged desktop did not become ready');
}
function start(){child=spawn(runtime,['-I','-B',path.join(root,'desktop_harness.py')],{windowsHide:true,stdio:['ignore','pipe','pipe']});
 child.stdout.on('data',v=>log+=v);child.stderr.on('data',v=>log+=v);exitPromise=new Promise(resolve=>child.once('exit',resolve));}
async function request(route,body){
 const address=new URL(startup);const response=await fetch(new URL(route,address),{method:body?'POST':'GET',headers:{'X-PLER-Token':address.hash.slice(8),'Origin':address.origin,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});
 const value=await response.json();assert.equal(response.ok,true,JSON.stringify(value));return value;
}
async function stop(){await request('/api/quit',{});const code=await Promise.race([exitPromise,pause(20000).then(()=>-99)]);assert.equal(code,0,log);}
const browser=await chromium.launch({channel:'msedge',headless:true});
let page;
try{
 start();startup=await active();page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 page.on('pageerror',e=>errors.push(e.message));
 const first=new URL(startup);first.searchParams.set('lang','tr');await page.goto(first.href);
 await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading);
 if(await page.locator('#first-use').isVisible())await page.locator('.first-use-actions button.quiet').first().click();
 await page.locator('[data-route=settings]').click();
 await page.locator('#recovery-file').setInputFiles(path.join(root,'preview/trusted-backup.zip'));
 await page.locator('#recovery-inspect').click();await page.locator('#recovery-details').waitFor({state:'visible'});
 await page.locator('#recovery-parent').fill(proof);await page.locator('#recovery-plan').click();
 await page.waitForFunction(()=>document.getElementById('recovery-target').textContent.includes('PLER-history-'));
 await page.locator('#recovery-confirm').check();await page.locator('#recovery-restore').click();await page.locator('#recovery-success').waitFor({state:'visible'});
 const before=await request('/api/usage/recovery');assert.equal(before.remembered,true);assert.equal(before.desktop,true);
 const target=before.restored.target;assert.equal(await page.locator('#recovery-open').isDisabled(),true);
 await page.locator('#recovery-open-confirm').check();await page.locator('#recovery-open').click();
 const old=startup;startup=await active(old);assert.equal(child.exitCode,null,'owner process should reopen the selected history');
 const switched=await request('/api/usage/recovery');assert.equal(switched.current,target);assert.equal(switched.previous,before.current);
 assert.deepEqual(JSON.parse(await readFile(path.join(target,'work-items.json'),'utf8')),JSON.parse(await readFile(path.join(root,'preview/backup-source/work-items.json'),'utf8')));
 const selected=JSON.parse(await readFile(path.join(proof,'local/pler/desktop-history.json'),'utf8'));assert.equal(selected.selected,target);
 await page.goto(startup);await page.waitForFunction(()=>usageState.data?.has_snapshot&&!usageState.loading);
 await page.locator('[data-route=settings]').click();await page.locator('#recovery-previous').waitFor({state:'visible'});
 await page.locator('#history-recovery').screenshot({path:path.join(proof,'opened-history.png')});
 await stop();await page.close();
 start();startup=await active();assert.equal((await request('/api/usage/recovery')).current,target);
 await request('/api/usage/recovery',{action:'previous',confirmed:true});
 const previous=startup;startup=await active(previous);assert.equal((await request('/api/usage/recovery')).current,before.current);
 await stop();
 assert.deepEqual(errors,[]);
 const result={version:'0.9.13',packaged_modules:true,actual_electron_windows:true,isolated_default_profile:true,explicit_restore_and_open:true,same_owner_reopened:true,recovered_work_bytes_equal:true,normal_relaunch_remembers_selection:true,return_to_previous:true,normal_exit:true,script_errors:errors,clean_windows_real_user_acceptance:'PENDING - LAST TASK'};
 await writeFile(path.join(root,'desktop-check.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{
 if(child&&child.exitCode===null){try{await stop();}catch{child.kill();}}
 await browser.close();
}
