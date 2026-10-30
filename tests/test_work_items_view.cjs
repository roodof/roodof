'use strict';
// Run the shipped work panel against invented snapshots and controllable local replies.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test');
const source=fs.readFileSync(path.join(__dirname,'../src/pler/web/app.js'),'utf8');
const html=fs.readFileSync(path.join(__dirname,'../src/pler/web/index.html'),'utf8');
const words=JSON.parse(source.slice(source.indexOf('/*I18N*/')+8,source.indexOf('/*END*/')));
const actions=source.slice(source.indexOf('// Work titles are manual,'),source.indexOf('function reconnectFromAccessLink('));
const events=source.slice(source.indexOf("$('usage-work-create-title').addEventListener"),source.indexOf("$('usage-export-mask').addEventListener"));
const A='a'.repeat(24),B='b'.repeat(24),C='c'.repeat(24),D='d'.repeat(24),W='1'.repeat(24),X='2'.repeat(24),Y='3'.repeat(24);
const flags={tokens_complete:true,calls_complete:true,attribution_complete:true,models_complete:true,api_priced_share:1};
function work(id,title,sessions,selected,outside=[],missing=[],tokens=100){return {id,title,session_ids:sessions,selected_session_ids:selected,outside_session_ids:outside,missing_session_ids:missing,linked_sessions:sessions.length,selected_sessions:selected.length,outside_selection:outside.length,missing_sessions:missing.length,overlapping_sessions:1,total_tokens:tokens,calls:selected.length,api_usd:tokens/100,...flags};}
function snapshot(){return {has_snapshot:true,state:'ready',totals:{sessions:3,total_tokens:350},sessions:[{id:A,project:'Release',agent:'codex'},{id:B,project:'Review',agent:'claude-code'}],work_items:{readable:true,items:[work(W,'Ship the release',[A,C,D],[A],[C],[D]),work(X,'Review the release',[A,B],[A,B],[],[],300)],summary:{items:2,linked_sessions:4,selected_sessions:2,unassigned_sessions:1,outside_selection:1,missing_sessions:1,overlapping_sessions:1,total_tokens:300,calls:2,api_usd:3,...flags}}};}
function page(data=snapshot(),lang='en',restore){
  const elements={},requests=[],messages=[],opened=[],inspected=[],runs=[];
  const document={body:{},activeElement:null};document.activeElement=document.body;
  class Element{
    constructor(tag='div'){this.tagName=tag.toUpperCase();this.children=[];this.events={};this.attributes={};this.disabled=false;this.hidden=false;this.value='';this.open=false;this.isConnected=false;this._text='';}
    set id(value){this._id=value;if(this.isConnected)elements[value]=this;}get id(){return this._id;}
    set innerHTML(_){throw new Error('Work titles must never enter innerHTML');}
    set textContent(value){this.replaceChildren();this._text=String(value);}get textContent(){return this._text+this.children.map(child=>child.textContent).join('');}
    connect(value){this.isConnected=value;if(this.id){if(value)elements[this.id]=this;else if(elements[this.id]===this)delete elements[this.id];}for(const child of this.children)child.connect(value);}
    append(...children){for(const child of children){this.children.push(child);child.parent=this;child.connect(this.isConnected);}}
    replaceChildren(...children){for(const child of this.children)child.connect(false);this.children=[];this._text='';this.append(...children);}
    get options(){return this.children;}setAttribute(key,value){this.attributes[key]=String(value);}
    addEventListener(type,handler){(this.events[type]??=[]).push(handler);}
    fire(type,more={}){const event={preventDefault(){this.prevented=true;},...more};for(const handler of this.events[type]||[])handler(event);return event;}
    click(){if(!this.disabled)this.fire('click');}focus(){document.activeElement=this;}
    showModal(){this.open=true;}close(){this.open=false;this.fire('close');}
    querySelectorAll(selector){const tags=selector.split(',').map(tag=>tag.toUpperCase()),found=[];for(const child of this.children){if(tags.includes(child.tagName))found.push(child);found.push(...child.querySelectorAll(selector));}return found;}
  }
  const node=(tag,cls,text)=>{const item=new Element(tag);item.className=cls||'';if(text!=null)item.textContent=text;return item;};
  for(const match of html.matchAll(/<(\w+)[^>]*\sid="([^"]+)"/g)){const item=node(match[1]);item._id=match[2];item.connect(true);}
  const root=elements['usage-work-items'];
  for(const id of ['usage-work-reload','usage-work-create-title','usage-work-create','usage-work-select','usage-work-rename-title','usage-work-rename','usage-work-delete','usage-work-members','usage-work-more'])root.append(elements[id]);
  elements['usage-session-dialog'].append(elements['usage-session-detail']);
  let resolve,reject;const reply=new Promise((yes,no)=>{resolve=yes;reject=no;});
  const state={data,stopped:false,loading:false,workRestore:restore},p={elements,state,requests,messages,opened,inspected,runs,resolve,reject,reloads:0,nextData:null,Element};
  const context=vm.createContext({usageState:state,$:id=>elements[id],document,node,number:String,usageUsd:value=>'$'+value,usagePct:value=>value*100+'%',usageAgents:{codex:'Codex','claude-code':'Claude Code'},
    t:(key,values={})=>String(words[lang][key]??words.en[key]).replace(/\{(\w+)\}/g,(all,name)=>name in values?values[name]:all),notice:value=>messages.push(value),
    syncArchiveButton:()=>{},syncExportButton:()=>{},openUsageSession:row=>opened.push(row.id),inspectUsageSession:id=>inspected.push(id),
    post:(route,body)=>{requests.push({route,body:JSON.parse(JSON.stringify(body))});return reply;},loadUsage:async()=>{p.reloads++;if(p.nextData){state.data=p.nextData;context.renderWorkItems(p.nextData);}}});
  p.context=context;vm.runInContext(actions,context);vm.runInContext(events,context);
  const perform=context.performWorkAction;context.performWorkAction=(...args)=>{const run=perform(...args);runs.push(run);return run;};
  p.stateOfWork=()=>vm.runInContext('workState',context);p.session=id=>{p.stateOfWork().openSession=id;context.renderSessionWorkItems();};
  p.type=(id,text)=>{elements[id].value=text;elements[id].fire('input');};context.renderWorkItems(data);return p;
}

test('work summary uses the union, selected work follows main scope, and general totals stay unchanged',()=>{
  const p=page(),before=structuredClone(p.state.data);
  assert.match(p.elements['usage-work-summary'].textContent,/300 known tokens/);
  assert.doesNotMatch(p.elements['usage-work-summary'].textContent,/400 known tokens/);
  assert.match(p.elements['usage-work-usage'].textContent,/100 known tokens/);
  assert.match(p.elements['usage-work-counts'].textContent,/Linked: 3 · Available: 2 · In the main filters: 1 · Outside the main filters: 1/);
  assert.deepEqual(p.state.data,before);
});

test('outside-filter sessions open by saved ID and missing links remain visible and removable',async()=>{
  const p=page(),members=p.elements['usage-work-members'].children;
  members[0].children[0].children[0].click();members[1].children[0].children[0].click();
  assert.deepEqual(p.opened,[A]);assert.deepEqual(p.inspected,[C]);
  assert.match(members[2].textContent,/Session unavailable/);assert.equal(members[2].children[0].children[0].tagName,'SPAN');
  members[2].children[1].click();assert.deepEqual(p.requests,[{route:'/api/usage/work',body:{action:'unlink',id:W,session:D}}]);
  p.reject(new Error('Invented write failure'));await p.runs.at(-1);
  assert.deepEqual(p.state.data.work_items.items[0].session_ids,[A,C,D]);
  assert.match(p.messages.at(-1),/Invented write failure/);
});

test('manual titles render literally in options, member labels and the delete dialog in both languages',()=>{
  for(const lang of ['en','tr']){
    const data=snapshot(),title='<img src=x onerror="attack()"> & <script>bad()</script>';data.work_items.items[0].title=title;
    const p=page(data,lang);assert.equal(p.elements['usage-work-select'].children[0].textContent,title+' · #11111111');
    p.session(A);assert.equal(p.elements['usage-session-work-items'].children[2].children[0].children[0].textContent,title+' · #11111111');
    p.context.requestWorkDelete();assert.equal(p.elements['usage-work-delete-name'].textContent,title+' · #11111111');assert.equal(p.elements['usage-work-delete-dialog'].open,true);
    assert.equal(p.requests.length,0);
  }
});

test('one pending create disables duplicates and a failed save preserves the draft and previous snapshot',async()=>{
  const p=page(),before=p.state.data;p.type('usage-work-create-title','Prepare publication');
  const run=p.context.createWork();await p.context.createWork();
  assert.equal(p.requests.length,1);assert.equal(p.elements['usage-work-create'].disabled,true);
  p.reject(new Error('Invented disk full'));await run;
  assert.equal(p.state.data,before);assert.equal(p.stateOfWork().createDraft,'Prepare publication');
  assert.equal(p.elements['usage-work-create-title'].value,'Prepare publication');assert.equal(p.elements['usage-work-create'].disabled,false);assert.equal(p.reloads,0);
});

test('session creation links atomically and refreshes the view without asking to scan sources',async()=>{
  const p=page();p.session(A);p.type('usage-session-work-title','New job');
  const run=p.context.createWork(A),updated=snapshot();updated.work_items.items.push(work(Y,'New job',[A],[A]));p.nextData=updated;
  assert.deepEqual(p.requests,[{route:'/api/usage/work',body:{action:'create',title:'New job',session:A}}]);
  p.resolve({ok:true,id:Y});await run;
  assert.equal(p.reloads,1);assert.equal(p.requests.length,1);assert.equal(p.stateOfWork().selected,Y);assert.equal(p.elements['usage-session-work-title'].value,'');
  assert.equal(p.state.data.totals.total_tokens,350);assert.match(p.elements['usage-session-work-items'].textContent,/New job/);
});

test('membership controls support several works and never optimistically unlink on failure',async()=>{
  const p=page();p.session(A);const box=p.elements['usage-session-work-items'];
  assert.match(box.textContent,/Ship the release/);assert.match(box.textContent,/Review the release/);
  assert.equal(p.elements['usage-session-work-select'].disabled,true);
  box.children[2].children[0].children[1].click();
  assert.deepEqual(p.requests[0].body,{action:'unlink',id:W,session:A});
  assert.match(box.textContent,/Ship the release/);p.reject(new Error('Invented save error'));await p.runs.at(-1);
  assert.match(box.textContent,/Ship the release/);assert.deepEqual(p.state.data.work_items.items[0].session_ids,[A,C,D]);
  assert.equal(p.elements['usage-session-work-status'].textContent,'Invented save error');
});

test('deleting a work requires explicit dialog confirmation and removes only its record',async()=>{
  const p=page(),totals=p.state.data.totals;p.context.requestWorkDelete();
  assert.equal(p.requests.length,0);assert.equal(p.elements['usage-work-delete-dialog'].open,true);
  p.context.cancelWorkDelete();assert.equal(p.requests.length,0);assert.equal(p.elements['usage-work-delete-dialog'].open,false);
  p.context.requestWorkDelete();p.elements['usage-work-delete-confirm'].click();
  assert.deepEqual(p.requests,[{route:'/api/usage/work',body:{action:'delete',id:W}}]);
  assert.equal(p.elements['usage-work-delete-cancel'].disabled,true);
  const updated=snapshot();updated.work_items.items.shift();p.nextData=updated;p.resolve({ok:true,id:W});await p.runs.at(-1);
  assert.equal(p.elements['usage-work-delete-dialog'].open,false);assert.equal(p.stateOfWork().selected,X);assert.deepEqual(p.state.data.totals,totals);
});

test('a saved action with failed refresh locks changes and offers a read-only retry',async()=>{
  const p=page();p.type('usage-work-create-title','Saved remotely');const run=p.context.createWork();p.resolve({ok:true,id:Y});await run;
  assert.equal(p.reloads,1);assert.equal(p.stateOfWork().needsRefresh,true);assert.equal(p.elements['usage-work-create'].disabled,true);
  assert.equal(p.elements['usage-work-reload'].hidden,false);assert.equal(p.elements['usage-work-reload'].disabled,false);
  assert.match(p.messages.at(-1),/Work saved, but the view could not be refreshed/);
  const updated=snapshot();updated.work_items.items.push(work(Y,'Saved remotely',[],[]));p.nextData=updated;
  p.elements['usage-work-reload'].click();await Promise.resolve();
  assert.equal(p.reloads,2);assert.equal(p.requests.length,1);assert.equal(p.stateOfWork().needsRefresh,false);assert.equal(p.elements['usage-work-select'].value,Y);
});

test('closing the app or switching language discards a late reply without refreshing or changing drafts',async()=>{
  for(const stop of [p=>p.state.stopped=true,p=>p.stateOfWork().navigation=true]){
    const p=page();p.type('usage-work-create-title','Do not repeat');const run=p.context.createWork();stop(p);p.resolve({ok:true,id:Y});await run;
    assert.equal(p.reloads,0);assert.equal(p.stateOfWork().selected,W);assert.equal(p.stateOfWork().createDraft,'Do not repeat');assert.deepEqual(p.messages,['']);assert.equal(p.elements['usage-work-create'].disabled,true);
  }
});

test('an unreadable store is never presented as an empty list and blocks all edits',async()=>{
  const data=snapshot();data.work_items={readable:false,items:[],summary:{}};const p=page(data);
  assert.equal(p.elements['usage-work-unavailable'].hidden,false);assert.equal(p.elements['usage-work-empty'].hidden,true);
  p.type('usage-work-create-title','Keep the broken store');await p.context.createWork();p.context.requestWorkDelete();
  assert.equal(p.requests.length,0);assert.equal(p.elements['usage-work-create'].disabled,true);assert.equal(p.elements['usage-work-reload'].disabled,false);
  p.session(A);assert.match(p.elements['usage-session-work-items'].textContent,/Saved work could not be read/);assert.equal(p.elements['usage-session-work-create'],undefined);
});

test('scanning, loading, closing and other history writes prevent concurrent work mutations',async()=>{
  for(const alter of [p=>p.state.data.state='scanning',p=>p.state.loading=true,p=>p.state.stopped=true,p=>p.state.backupBusy='check',p=>p.state.metadataChanging=true,p=>p.state.archiveClearing=true]){
    const p=page();p.type('usage-work-create-title','Wait');alter(p);await p.context.createWork();assert.equal(p.requests.length,0);
  }
});

test('work selection and draft titles survive a language reload without replacing manual titles',()=>{
  const p=page(snapshot(),'tr',{selected:X,create:'Taslak iş',rename:{[X]:'Düzenlenen başlık'}});
  assert.equal(p.elements['usage-work-select'].value,X);assert.equal(p.elements['usage-work-create-title'].value,'Taslak iş');assert.equal(p.elements['usage-work-rename-title'].value,'Düzenlenen başlık');
  const saved=JSON.parse(JSON.stringify(p.context.workViewMemory()));assert.deepEqual(saved,{selected:X,create:'Taslak iş',rename:{[X]:'Düzenlenen başlık'}});
  const reloaded=page(snapshot(),'en',saved);assert.equal(reloaded.elements['usage-work-rename-title'].value,'Düzenlenen başlık');assert.equal(reloaded.state.data.work_items.items[1].title,'Review the release');
});

test('unpriced models do not look free and partial prices keep their coverage',()=>{
  for(const [share,expected] of [[0,/Unpriced/],[0.25,/\$1 \(25% of tokens priced\)/],[1,/\$1 API equivalent/]]){
    const data=snapshot();data.work_items.items[0].api_priced_share=share;const p=page(data);assert.match(p.elements['usage-work-usage'].textContent,expected);
  }
  const data=snapshot();data.work_items.items[0].selected_sessions=0;const p=page(data);assert.match(p.elements['usage-work-usage'].textContent,/No usage total/);assert.doesNotMatch(p.elements['usage-work-usage'].textContent,/\$/);
});

test('large work stores render a selector and one bounded member page',()=>{
  const data=snapshot(),ids=Array.from({length:2000},(_,index)=>index.toString(16).padStart(24,'0'));
  data.work_items.items=Array.from({length:200},(_,index)=>work((index+1).toString(16).padStart(24,'0'),'Job '+index,ids,[],ids));
  const p=page(data);assert.equal(p.elements['usage-work-select'].children.length,200);assert.equal(p.elements['usage-work-members'].children.length,20);
  assert.equal(p.elements['usage-work-more'].hidden,false);p.elements['usage-work-more'].click();assert.equal(p.elements['usage-work-members'].children.length,40);
});

test('title limits count Unicode characters and reject core-forbidden separators and lone surrogates',async()=>{
  const p=page(),title='🚀'.repeat(120);p.type('usage-work-create-title',title);
  assert.equal(p.elements['usage-work-create'].disabled,false);
  p.type('usage-work-create-title',title+'🚀');assert.equal(p.elements['usage-work-create'].disabled,true);
  await p.context.createWork();assert.equal(p.requests.length,0);
  for(const forbidden of ['a\u2028b','a\u2029b','a\ud800b','a\udfffb','a\u0000b','a\u0085b']){
    p.type('usage-work-create-title',forbidden);assert.equal(p.elements['usage-work-create'].disabled,true);await p.context.createWork();
  }
  assert.equal(p.requests.length,0);
  p.session(A);assert.equal(p.elements['usage-session-work-title'].maxLength,240);
  p.type('usage-session-work-title',title);assert.equal(p.elements['usage-session-work-create'].disabled,false);
  p.type('usage-session-work-title',title+'🚀');assert.equal(p.elements['usage-session-work-create'].disabled,true);
  p.type('usage-work-create-title',title);const run=p.context.createWork();
  assert.equal(p.requests[0].body.title,title);p.reject(new Error('Invented save failure'));await run;
  for(const id of ['usage-work-create-title','usage-work-rename-title'])assert.match(html,new RegExp('id="'+id+'" maxlength="240"'));
});
