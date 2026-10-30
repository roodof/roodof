'use strict';
// Run the shipped verdict buttons against a fake page and a local reply; no browser or dependencies required.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test');
const source=fs.readFileSync(require('node:path').join(__dirname,'../src/pler/web/app.js'),'utf8');
const code=source.slice(source.indexOf('function usageVerdictSummary('),source.indexOf('function renderUsageSessions('));
function element(cls='',text=''){
  return {className:cls,textContent:text,dataset:{},attributes:{},children:[],handlers:{},disabled:false,hidden:false,type:'',
    setAttribute(name,value){this.attributes[name]=value;},getAttribute(name){return this.attributes[name];},
    append(...items){this.children.push(...items);},addEventListener(name,handler){this.handlers[name]=handler;}};
}
function page({readable=true,reply}={}){
  const summary=element('verdict-summary'),made=[],posts=[],messages=[];
  const sessions=[{id:'a'.repeat(24),total_tokens:100,api_usd:1.5,verdict:null},{id:'b'.repeat(24),total_tokens:50,api_usd:0.5,verdict:'wasted'}];
  const state={data:{sessions,verdicts:{readable},demo:false},stopped:false};
  const context=vm.createContext({usageState:state,$:id=>id==='usage-verdict-summary'?summary:null,
    t:(key,values)=>values?key+' '+JSON.stringify(values):key,count:(n,noun)=>n+' '+noun,usageShort:String,usageUsd:value=>'$'+value.toFixed(2),
    usageSessionCode:session=>session.id.slice(0,8),notice:text=>messages.push(text),number:String,usagePct:value=>Math.round(value*100)+'%',
    node:(tag,cls,text)=>{const item=element(cls,text);made.push(item);return item;},
    document:{querySelectorAll:()=>made.filter(item=>item.className.includes('verdict-button'))},
    post:async(path,body)=>{posts.push([path,body]);if(reply)return reply(body);return {ok:true,id:body.id,verdict:body.verdict};}});
  vm.runInContext(code,context);
  return {context,state,summary,posts,messages,sessions,buttons:()=>made.filter(item=>item.className.includes('verdict-button'))};
}
const plain=value=>JSON.parse(JSON.stringify(value));  // objects made inside the page context
const pressed=(buttons,id)=>buttons.filter(item=>item.dataset.verdictId===id&&item.attributes['aria-pressed']==='true').map(item=>item.dataset.verdict);
test('one click saves a verdict and updates the table row and an open dialog together',async()=>{
  const p=page(),[first]=p.sessions;
  p.context.verdictToggle(first);p.context.verdictToggle(first);  // table row and dialog
  p.context.usageVerdictSummary();
  assert.match(p.summary.textContent,/^verdict_summary /);
  const useful=p.buttons().find(item=>item.dataset.verdict==='useful');
  await useful.handlers.click();
  assert.deepEqual(plain(p.posts),[['/api/usage/verdict',{id:first.id,verdict:'useful'}]]);
  assert.deepEqual(plain(pressed(p.buttons(),first.id)),['useful','useful']);
  assert.equal(first.verdict,'useful');
  const values=JSON.parse(p.summary.textContent.slice('verdict_summary '.length));
  assert.equal(values.useful,'1 session');assert.equal(values.useful_tokens,'100');assert.equal(values.wasted_usd,'$0.50');assert.equal(values.none,'0 session');
});
test('clicking the pressed button removes the verdict',async()=>{
  const p=page(),second=p.sessions[1];
  p.context.verdictToggle(second);
  await p.buttons().find(item=>item.dataset.verdict==='wasted').handlers.click();
  assert.deepEqual(plain(p.posts[0][1]),{id:second.id,verdict:null});
  assert.deepEqual(plain(pressed(p.buttons(),second.id)),[]);
});
test('an unreadable verdict file disables the buttons and says why',()=>{
  const p=page({readable:false});
  p.context.verdictToggle(p.sessions[0]);p.context.usageVerdictSummary();
  assert.ok(p.buttons().every(item=>item.disabled));
  assert.equal(p.summary.textContent,'verdict_unreadable');
});
test('a failed save reports the error and leaves the shown verdict unchanged',async()=>{
  const p=page({reply:()=>{throw new Error('not saved');}}),[first]=p.sessions;
  p.context.verdictToggle(first);
  await p.buttons()[0].handlers.click();
  assert.deepEqual(plain(p.messages),['not saved']);
  assert.deepEqual(plain(pressed(p.buttons(),first.id)),[]);
  assert.equal(first.verdict,null);
});
test('no verdict yet shows how to start instead of zero totals',()=>{
  const p=page();p.sessions[1].verdict=null;p.context.usageVerdictSummary();
  assert.equal(p.summary.textContent,'verdict_hint');
});
test('a session shows how its last visible test and build ended, or that no result was visible',()=>{
  const p=page(),session={id:'c'.repeat(24),checks:{test:{runs:3,passed:1,failed:1,last:'failed'},build:{runs:2,passed:0,failed:0,last:null}}};
  const lines=p.context.checkSummaries(session);
  assert.deepEqual(plain(lines.map(line=>[line.className,line.textContent])),[
    ['session-check failed','check_test_failed {"runs":"3 run"}'],['session-check hidden','check_build_hidden {"runs":"2 run"}']]);
  assert.equal(p.context.checkSummaries({id:'d'.repeat(24)}).length,0);
  const detail=JSON.parse(p.context.checkDetail(session.checks.test).slice('check_detail '.length));
  assert.deepEqual(plain(detail),{runs:'3 run',last:'check_last_failed',passed:'1',failed:'1',hidden:'1'});
});
test('a session whose commits were measured shows how much of the added code is still in place',()=>{
  const p=page(),lines=p.context.checkSummaries({id:'e'.repeat(24),git_activity:{lines:{added:200,kept:150,commits:2,unmeasured:0}}});
  assert.deepEqual(plain(lines.map(line=>[line.className,line.textContent])),[['session-check lines','lines_kept_row {"share":"75%","added":"200"}']]);
  assert.equal(p.context.checkSummaries({id:'f'.repeat(24),git_activity:{lines:{added:0,kept:0,commits:0,unmeasured:1}}}).length,0);
});
