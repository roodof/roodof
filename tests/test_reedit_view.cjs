'use strict';
// Exercise the actual observation renderer with synthetic metadata and a small DOM stand-in.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test');
const source=fs.readFileSync(require('node:path').join(__dirname,'../src/pler/web/app.js'),'utf8');
const table=JSON.parse(source.slice(source.indexOf('/*I18N*/')+8,source.indexOf('/*END*/')));
const renderer=source.slice(source.indexOf('function appendSubsequentEdit('),source.indexOf('function quotaWindowNow('));
function element(tag,cls,text){return {tag,className:cls,textContent:text??'',children:[],listeners:{},append(...items){this.children.push(...items);},addEventListener(name,run){this.listeners[name]=run;}};}
function descendants(root){return [root,...root.children.flatMap(descendants)];}
function page(lang='en'){
  const card=element('article'),opened=[],inspected=[];
  const t=(key,values={})=>table[lang][key].replace(/\{(\w+)\}/g,(match,name)=>name in values?values[name]:match);
  const context=vm.createContext({node:element,t,number:value=>String(value),usageDate:value=>value,usageDuration:value=>Math.floor(value)+' s',
    usageAgents:{'claude-code':'Claude Code',codex:'Codex'},openUsageSession:session=>opened.push(session),inspectUsageSession:id=>inspected.push(id)});
  vm.runInContext(renderer,context);
  return {card,opened,inspected,context,t,nodes:()=>descendants(card),text:()=>descendants(card).map(item=>item.textContent).join('\n')};
}
const origin='a'.repeat(24),later='b'.repeat(24);
const base={origin_sessions:4,eligible_sessions:2,timeline_eligible_sessions:5,timeline_sessions:8,observed_unmatched_sessions:1,
  cutoff:'2026-10-29T12:00:00+00:00',excluded:{uncertain_history:2},
  matches:[{origin_id:origin,later_id:later,origin_agent:'codex',later_agent:'claude-code',gap_seconds:0.5,matching_targets:1,
    origin_tokens:120,later_tokens:300,origin_usage_complete:true,later_usage_complete:false}]};
test('shows fixed observation coverage and positive subsecond gaps in both languages',()=>{
  for(const lang of ['en','tr']){
    const p=page(lang);p.context.appendSubsequentEdit(p.card,{sessions:[]},base);const text=p.text();
    assert(text.includes(base.cutoff));assert(text.includes(p.t('reedit_subsecond')));
    assert(text.includes(p.t('reedit_uncertain_history')+': 2'));
    assert(text.includes(p.t('reedit_partial')));assert(text.includes('120'));assert(text.includes('300'));
    assert(!text.includes('0 s'));assert(!text.includes('undefined'));
  }
});
test('opens selected sessions directly and looks up a session outside the filters by its code only',()=>{
  const p=page(),session={id:origin};p.context.appendSubsequentEdit(p.card,{sessions:[session]},base);
  const buttons=p.nodes().filter(item=>item.tag==='button');assert.equal(buttons.length,2);
  buttons[0].listeners.click();assert.deepEqual(p.opened,[session]);
  buttons[1].listeners.click();assert.deepEqual(p.inspected,[later]);
  assert(p.text().includes('aaaaaaaa'));assert(p.text().includes('bbbbbbbb'));assert(p.text().includes(p.t('open_outside')));
});
test('private extra fields never render and malformed identities or agents are not copied',()=>{
  const p=page();const privateText='C:/private-project/SECRET-CANARY.txt';
  const match={...base.matches[0],origin_id:privateText,origin_agent:privateText,files:[privateText],source:privateText};
  p.context.appendSubsequentEdit(p.card,{sessions:[]},{...base,private:privateText,matches:[match],excluded:{...base.excluded,[privateText]:9}});
  assert(!p.text().includes(privateText));assert(!p.text().includes('SECRET-CANARY'));assert(!p.nodes().some(item=>'innerHTML' in item));
});
test('caps displayed pairs and keeps empty observations understandable',()=>{
  const p=page();p.context.appendSubsequentEdit(p.card,{sessions:[]},{...base,matches:Array(9).fill(base.matches[0])});
  const pairs=p.nodes().find(item=>item.tag==='ol');assert.equal(pairs.children.length,5);
  const empty=page();empty.context.appendSubsequentEdit(empty.card,{sessions:[]},{...base,matches:[]});
  assert(!empty.nodes().some(item=>item.tag==='ol'));assert(empty.text().includes(base.cutoff));
});
test('snapshot clock preserves open investigations until a quota observation changes state',()=>{
  let state='fills_before_reset',quotaRenders=0,insightRenders=0,alertRenders=0;
  const context=vm.createContext({document:{hidden:false},usageState:{stopped:false,insightQuotaStates:'fills_before_reset',
    data:{has_snapshot:true,insights:[{kind:'quota',evidence:{}}]}},
    quotaWindowNow:()=>({state}),renderUsageQuota:()=>quotaRenders++,renderUsageInsights:()=>insightRenders++,
    renderQuotaAlerts:()=>alertRenders++});
  vm.runInContext(source.slice(source.indexOf('function quotaInsightStates('),source.indexOf('usageState.clock=')),context);
  context.updateSnapshotClock();context.updateSnapshotClock();
  assert.equal(quotaRenders,2);assert.equal(insightRenders,0);
  state='reset';context.updateSnapshotClock();assert.equal(insightRenders,1);
  // A hidden page skips drawing but still checks the quota warning, so a notification can reach the user.
  context.document.hidden=true;context.updateSnapshotClock();assert.equal(quotaRenders,3);assert.equal(alertRenders,4);
});
