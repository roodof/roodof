'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const code=fs.readFileSync(path.join(__dirname,'../src/pler/web/updates.js'),'utf8');
function page({lang='en',enabled=true,state='idle',draft=''}={}){
  const elements={},calls=[],posts=[],timers=[];
  for(const id of ['dialog','open','title','version','status','notes','size','progress','check','install','later','close','auto-label','auto','privacy']){
    elements['usage-update-'+id]={textContent:'',hidden:false,disabled:false,open:false,events:{},attributes:{},
      addEventListener(type,fn){this.events[type]=fn;},setAttribute(k,v){this.attributes[k]=v;},showModal(){this.open=true;},close(){this.open=false;},focus(){this.focused=true;}};
  }
  const snapshot={supported:true,state,error:null,current_version:'0.2.31',available_version:state==='available'?'0.2.32':null,
    size:5000000,received:0,notes:{en:'A useful update',tr:'Yararlı güncelleme'},automatic:false,installable:state==='available'};
  const context={document:{documentElement:{lang},querySelector:()=>({getAttribute:()=>enabled?'1':'0'}),getElementById:id=>elements[id]},
    api:async route=>{calls.push(route);return {...snapshot};},post:async(route,body)=>{posts.push([route,body]);return {...snapshot,state:route.endsWith('/install')?'downloading':route.endsWith('/check')?'checking':state,automatic:body.automatic??false};},
    workState:{createDraft:draft,renameDrafts:{},detailDrafts:{}},followState:{drafts:{}},usageState:{data:{work_items:{items:[]}}},
    setTimeout:fn=>{timers.push(fn);return timers.length;},clearTimeout:()=>{}};
  vm.createContext(context);vm.runInContext(code,context);
  return {elements,context,calls,posts,snapshot,timers};
}
async function settled(){await new Promise(resolve=>setImmediate(resolve));}
test('nonportable page does not read an update endpoint or opt into network checks',async()=>{
  const p=page({enabled:false});await settled();assert.deepEqual(p.calls,[]);assert.deepEqual(p.posts,[]);
});
test('idle page reads only local state and keeps automatic checking off',async()=>{
  const p=page();await settled();assert.deepEqual(p.calls,['/api/updates']);assert.deepEqual(p.posts,[]);
  assert.equal(p.elements['usage-update-auto'].checked,false);assert.match(p.elements['usage-update-status'].textContent,/offline/);
});
test('available release becomes a notification without opening a modal or downloading',async()=>{
  const p=page({state:'available'});await settled();assert.match(p.elements['usage-update-open'].textContent,/0.2.32/);
  assert.equal(p.elements['usage-update-dialog'].open,false);assert.equal(p.posts.length,0);
  p.elements['usage-update-open'].events.click();assert.equal(p.elements['usage-update-dialog'].open,true);
});
test('install is explicit, only posts an empty local action, and blocks closing during progress',async()=>{
  const p=page({state:'available'});await settled();p.elements['usage-update-install'].events.click();await settled();
  assert.equal(p.posts.length,1);assert.equal(p.posts[0][0],'/api/updates/install');assert.equal(JSON.stringify(p.posts[0][1]),'{}');
  assert.equal(p.elements['usage-update-later'].disabled,true);assert.equal(p.elements['usage-update-progress'].hidden,false);
  let prevented=false;p.elements['usage-update-dialog'].events.cancel({preventDefault(){prevented=true;}});assert.equal(prevented,true);
});
test('unsaved work blocks installation and keeps the user draft',async()=>{
  const p=page({state:'available',draft:'My unfinished work'});await settled();p.elements['usage-update-install'].events.click();await settled();
  assert.equal(p.posts.length,0);assert.match(p.elements['usage-update-status'].textContent,/unsaved/);assert.equal(p.context.workState.createDraft,'My unfinished work');
});
test('Turkish UI describes network scope and explicit automatic preference',async()=>{
  const p=page({lang:'tr'});await settled();assert.equal(p.elements['usage-update-title'].textContent,'Güncellemeler');
  assert.match(p.elements['usage-update-privacy'].textContent,/gönderilmez/);
  p.elements['usage-update-auto'].events.change({target:{checked:true}});await settled();
  assert.equal(p.posts[0][0],'/api/updates/preferences');assert.equal(JSON.stringify(p.posts[0][1]),'{"automatic":true}');
});
test('an unsaved weekly review or session title also blocks restart',async()=>{
  for(const kind of ['review','session']){
    const p=page({state:'available'});await settled();
    if(kind==='review')p.context.followState.drafts.work={reviews:{record:{context:'similar',note:'unsaved'}}};
    else p.context.workState.sessionDrafts={session:'unsaved session work'};
    p.elements['usage-update-install'].events.click();await settled();assert.equal(p.posts.length,0);assert.match(p.elements['usage-update-status'].textContent,/unsaved/);
  }
});
test('release notes remain text and incompatible formats have no install action',async()=>{
  const p=page({state:'manual_required'});p.snapshot.notes.en='<img src=x onerror=alert(1)>';await settled();
  assert.equal(p.elements['usage-update-install'].hidden,true);assert.match(p.elements['usage-update-notes'].textContent,/<img/);
  assert.match(p.elements['usage-update-status'].textContent,/will not install/);
});
