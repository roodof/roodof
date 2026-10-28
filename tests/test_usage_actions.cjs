'use strict';
// Run the shipped export action against a delayed local reply; no browser or dependencies required.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test');
const source=fs.readFileSync(require('node:path').join(__dirname,'../src/pler/web/app.js'),'utf8');
const actions=source.slice(source.indexOf('function clearUsageDownload('),source.indexOf('applyLanguage();'));
function page(){
  const elements={};
  for(const id of ['usage-export','usage-period','usage-agent','usage-project','usage-download-result','usage-download-status','usage-download-link']){
    elements[id]={disabled:false,hidden:true,attributes:{},setAttribute(name,value){this.attributes[name]=value;},removeAttribute(name){delete this[name];},click(){this.clicked=(this.clicked||0)+1;}};
  }
  elements['usage-period'].value='30';elements['usage-agent'].value='all';elements['usage-project'].value='all';
  const state={data:{has_snapshot:true,filters:{days:30,agent:'all',project:'all'}},exporting:false,loading:false,stopped:false,downloadUrl:null};
  let resolve,reject,calls=0,query='days=30&agent=all&project=all';
  const reply=new Promise((yes,no)=>{resolve=yes;reject=no;});
  const made=[],revoked=[],messages=[];
  const body={};const document={body,activeElement:body};
  for(const element of Object.values(elements)){element.isConnected=true;element.focus=()=>{document.activeElement=element;};}
  const context=vm.createContext({document,usageState:state,$:id=>elements[id],t:key=>key,notice:text=>messages.push(text),usageQuery:()=>query,
    Blob,URL:{createObjectURL:blob=>{made.push(blob);return 'blob:test-'+made.length;},revokeObjectURL:url=>revoked.push(url)},
    api:()=>{calls++;return reply;}});
  vm.runInContext(actions,context);
  return {context,elements,state,made,revoked,messages,resolve,reject,calls:()=>calls,query:value=>{query=value;}};
}
test('one pending export disables repeated downloads and keeps a reusable prepared JSON link',async()=>{
  const p=page(),run=p.context.exportUsage();
  await p.context.exportUsage();assert.equal(p.calls(),1);assert.equal(p.elements['usage-export'].disabled,true);
  assert.equal(p.elements['usage-export'].attributes['aria-busy'],'true');
  p.resolve({version:'0.2.1',totals:{total_tokens:150}});await run;
  assert.equal(p.elements['usage-export'].disabled,false);
  assert.equal(p.elements['usage-download-result'].hidden,false);
  assert.equal(p.elements['usage-download-link'].clicked,1);
  assert.equal(p.made[0].type,'application/json');
  assert.equal(JSON.parse(await p.made[0].text()).totals.total_tokens,150);
  assert.equal(p.revoked.length,0); // the retry link must remain usable, including on a slow download
});
test('changing selection during preparation discards the old result',async()=>{
  const p=page(),run=p.context.exportUsage();
  p.elements['usage-agent'].value='codex';p.query('days=30&agent=codex&project=all');p.resolve({totals:{total_tokens:150}});await run;
  assert.equal(p.made.length,0);assert.equal(p.elements['usage-download-result'].hidden,true);
  assert.equal(p.elements['usage-export'].disabled,true);
});
test('an unread new selection cannot export the previous selection',()=>{
  const p=page();p.elements['usage-period'].value='7';p.context.syncExportButton();
  assert.equal(p.elements['usage-export'].disabled,true);
  p.state.data.filters.days=7;p.context.syncExportButton();assert.equal(p.elements['usage-export'].disabled,false);
  p.state.loading=true;p.context.syncExportButton();assert.equal(p.elements['usage-export'].disabled,true);
});
test('request failure reports the error and permits retry',async()=>{
  const p=page(),run=p.context.exportUsage();p.reject(new Error('local read failed'));await run;
  assert.equal(p.elements['usage-export'].disabled,false);assert.equal(p.state.exporting,false);
  assert.equal(p.messages.at(-1),'local read failed');assert.equal(p.made.length,0);
});
test('closing while preparation is pending creates no download and keeps controls disabled',async()=>{
  const p=page(),run=p.context.exportUsage();p.state.stopped=true;p.resolve({});await run;
  assert.equal(p.made.length,0);assert.equal(p.elements['usage-export'].disabled,true);
});
test('discarding a prepared export revokes its URL and removes the outdated link',async()=>{
  const p=page(),run=p.context.exportUsage();p.resolve({});await run;p.context.clearUsageDownload();
  assert.deepEqual(p.revoked,['blob:test-1']);assert.equal(p.elements['usage-download-result'].hidden,true);
  assert.equal(p.elements['usage-download-link'].href,undefined);
});
