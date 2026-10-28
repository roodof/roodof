'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test');
const source=fs.readFileSync(require('node:path').join(__dirname,'../src/pler/web/app.js'),'utf8');
const bootstrap=source.slice(source.indexOf("let token='';"),source.indexOf('const number='));
const api=source.slice(source.indexOf('async function api('),source.indexOf('async function post('));
const key='a'.repeat(64);
function page(hash='',blocked=false,stored=null){
  const changes=[],requests=[];
  const context=vm.createContext({location:{hash,pathname:'/',search:'?lang=tr'},
    history:{replaceState:(...args)=>changes.push(args)},
    sessionStorage:{setItem:(name,value)=>{if(blocked)throw Error('disabled');stored=value;},getItem:()=>{if(blocked)throw Error('disabled');return stored;}},
    fetch:async(path,options)=>{requests.push({path,options});return {ok:true,json:async()=>({ready:true})};},t:value=>value});
  vm.runInContext(bootstrap+api,context);
  return {context,changes,requests};
}
test('startup fragment is removed and authenticated read carries its token',async()=>{
  const p=page('#access='+key);assert.equal(p.changes[0][2],'/?lang=tr');
  assert.equal((await vm.runInContext("api('/api/usage')",p.context)).ready,true);
  assert.equal(p.requests[0].options.headers['X-PLER-Token'],key);
});
test('reload reuses only the tab session token',async()=>{
  const p=page('',false,key);await vm.runInContext("api('/api/usage/export')",p.context);
  assert.equal(p.requests[0].options.headers['X-PLER-Token'],key);
});
test('disabled storage still removes the fragment and permits the current page',async()=>{
  const p=page('#access='+key,true);await vm.runInContext("api('/api/usage')",p.context);
  assert.equal(p.changes.length,1);assert.equal(p.requests[0].options.headers['X-PLER-Token'],key);
});
test('missing or malformed links never fabricate credentials',async()=>{
  for(const hash of ('#access=bad #access='+key).split(' ')){
    const p=page(hash+'extra',true);await vm.runInContext("api('/api/usage')",p.context);
    assert.equal(p.requests[0].options.headers['X-PLER-Token'],'');
  }
});
test('authenticated fetch preserves POST content headers',async()=>{
  const p=page('#access='+key);await vm.runInContext("api('/api/quit',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})",p.context);
  assert.equal(p.requests[0].options.headers['Content-Type'],'application/json');
  assert.equal(p.requests[0].options.headers['X-PLER-Token'],key);
});
test('opening a new startup link in the same tab reloads so the new credential is consumed',()=>{
  const start=source.indexOf('function reconnectFromAccessLink('),end=source.indexOf('applyLanguage();',start);
  let reloads=0;const location={hash:'#access='+key,reload:()=>reloads++};
  const context=vm.createContext({location});vm.runInContext(source.slice(start,end),context);
  context.reconnectFromAccessLink();assert.equal(reloads,1);
  for(const hash of ['#workspace','#access=invalid','']){location.hash=hash;context.reconnectFromAccessLink();}
  assert.equal(reloads,1);
});
