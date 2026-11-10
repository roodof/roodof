'use strict';
// Exercise shipped backup actions with delayed replies, without browser/storage/provider access.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test');
const source=fs.readFileSync(path.join(__dirname,'../src/pler/web/app.js'),'utf8');
const actions=source.slice(source.indexOf('function clearUsageDownload('),source.indexOf('applyLanguage();'));
function page(){
  const elements={};
  for(const id of ['usage-backup-download','usage-backup-check','usage-backup-file','usage-backup-result','usage-backup-download-result','usage-backup-download-link',
    'usage-archive-clear','usage-retention','usage-cache-reset','usage-export','usage-period','usage-agent','usage-project','usage-refresh']){
    elements[id]={disabled:false,hidden:true,isConnected:true,attributes:{},setAttribute(k,v){this.attributes[k]=v;},removeAttribute(k){delete this[k];},click(){this.clicks=(this.clicks||0)+1;},focus(){}};
  }
  elements['usage-period'].value='30';elements['usage-agent'].value='all';elements['usage-project'].value='all';
  elements['usage-backup-file'].files=[new Blob(['invented ZIP bytes'])];
  const state={data:{has_snapshot:true,demo:false,archive:{available:true,stored_files:1},filters:{days:30,agent:'all',project:'all'}},stopped:false,loading:false,exporting:false};
  const made=[],revoked=[],requests=[],messages=[];let resolve,reject,answer=true;
  const reply=new Promise((yes,no)=>{resolve=yes;reject=no;});
  const document={body:{},querySelector:()=>({content:'1024'})};document.activeElement=document.body;
  const context=vm.createContext({usageState:state,$:id=>elements[id],document,LANG:'en',token:'a'.repeat(64),
    number:String,usageDate:String,t:(key,values={})=>key+JSON.stringify(values),notice:value=>messages.push(value),
    confirm:()=>answer,fetch:async(route,options)=>{requests.push({route,options});return reply;},
    Blob,URL:{createObjectURL:blob=>{made.push(blob);return 'blob:backup-'+made.length;},revokeObjectURL:url=>revoked.push(url)}});
  vm.runInContext(actions,context);context.syncArchiveButton();
  return {context,elements,state,made,revoked,requests,messages,resolve,reject,answer:value=>{answer=value;}};
}
test('private download requires acknowledgement and repeated clicks create only one request',async()=>{
  const p=page();p.answer(false);await p.context.downloadUsageBackup();assert.equal(p.requests.length,0);
  p.answer(true);const run=p.context.downloadUsageBackup();await p.context.downloadUsageBackup();
  assert.equal(p.requests.length,1);assert.equal(p.elements['usage-backup-check'].disabled,true);assert.equal(p.elements['usage-export'].disabled,true);
  const blob=new Blob(['invented ZIP bytes'],{type:'application/zip'});p.resolve({ok:true,blob:async()=>blob});await run;
  assert.equal(p.requests[0].route,'/api/usage/backup?lang=en');assert.equal(p.requests[0].options.body,'{}');
  assert.equal(p.requests[0].options.headers['X-PLER-Token'],'a'.repeat(64));
  assert.equal(p.made[0],blob);assert.equal(p.elements['usage-backup-download-link'].download,'Roodof-backup.zip');
  assert.equal(p.elements['usage-backup-download-link'].clicks,1);assert.equal(p.elements['usage-backup-download-result'].hidden,false);
  assert.equal(p.elements['usage-backup-download'].disabled,false);assert.equal(p.revoked.length,0);
});
test('backup checking sends exactly the selected bytes to the local fixed route and does not restore',async()=>{
  const p=page(),chosen=p.elements['usage-backup-file'].files[0],run=p.context.checkUsageBackup();
  assert.equal(p.requests.length,1);assert.equal(p.requests[0].route,'/api/usage/backup/check?lang=en');
  assert.equal(p.requests[0].options.body,chosen);assert.equal(p.requests[0].options.headers['Content-Type'],'application/octet-stream');
  p.resolve({ok:true,json:async()=>({backup:{version:'0.2.25',created_at:'2026-10-30T12:00:00Z',archive_files:2,verdicts:3,quota_samples:4,retention_enabled:false}})});await run;
  assert.equal(p.elements['usage-backup-result'].hidden,false);assert.match(p.elements['usage-backup-result'].textContent,/backup_checked/);
  assert.match(p.elements['usage-backup-result'].textContent,/"files":"2"/);assert.match(p.elements['usage-backup-result'].textContent,/retention_short_off/);
  assert.equal(p.state.data.archive.stored_files,1);assert.equal(p.made.length,0);assert.equal(p.requests.length,1);
});
test('empty or oversized selected files are rejected without uploading',async()=>{
  for(const value of [new Blob([]),new Blob(['x'.repeat(1025)])]){
    const p=page();p.elements['usage-backup-file'].files=[value];await p.context.checkUsageBackup();
    assert.equal(p.requests.length,0);assert.match(p.messages.at(-1),/backup_invalid_file/);
  }
});
test('checking failure hides old success and permits a retry without changing history',async()=>{
  const p=page();p.elements['usage-backup-result'].hidden=false;const run=p.context.checkUsageBackup();
  p.resolve({ok:false,json:async()=>({error:'Invented damaged backup'})});await run;
  assert.equal(p.elements['usage-backup-result'].hidden,true);assert.equal(p.messages.at(-1),'Invented damaged backup');
  assert.equal(p.elements['usage-backup-check'].disabled,false);assert.equal(p.state.backupBusy,null);assert.equal(p.state.data.archive.stored_files,1);
});
test('closed page creates no late download or inspection result',async()=>{
  for(const action of ['downloadUsageBackup','checkUsageBackup']){
    const p=page(),run=p.context[action]();p.state.stopped=true;
    p.resolve({ok:true,blob:async()=>new Blob(['invented']),json:async()=>({backup:{}})});await run;
    assert.equal(p.made.length,0);assert.equal(p.elements['usage-backup-result'].hidden,true);
    assert.equal(p.elements['usage-backup-download-result'].hidden,true);assert.equal(p.elements['usage-backup-download'].disabled,true);
  }
});
test('demo, unavailable history and absent snapshot disable both actions',async()=>{
  for(const alter of [p=>p.state.data.demo=true,p=>p.state.data.archive.available=false,p=>p.state.data.has_snapshot=false]){
    const p=page();alter(p);p.context.syncBackupControls();
    await p.context.downloadUsageBackup();await p.context.checkUsageBackup();
    assert.equal(p.requests.length,0);assert.equal(p.elements['usage-backup-file'].disabled,true);
  }
});
test('discarding the prepared private backup revokes only its URL',async()=>{
  const p=page(),run=p.context.downloadUsageBackup();p.resolve({ok:true,blob:async()=>new Blob(['invented'])});await run;
  p.state.downloadUrl='blob:masked-json';p.context.clearUsageBackupDownload();
  assert.deepEqual(p.revoked,['blob:backup-1']);assert.equal(p.state.downloadUrl,'blob:masked-json');
  assert.equal(p.elements['usage-backup-download-result'].hidden,true);assert.equal(p.elements['usage-backup-download-link'].href,undefined);
});
test('failed download reports the error and leaves no prepared file',async()=>{
  const p=page(),run=p.context.downloadUsageBackup();p.reject(new Error('invented disconnect'));await run;
  assert.match(p.messages.at(-1),/err_unreachable/);assert.equal(p.made.length,0);assert.equal(p.elements['usage-backup-download'].disabled,false);
});
