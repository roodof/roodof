'use strict';
// Run the shipped live quota warning against a fake page, clock, storage and Notification; no browser needed.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test');
const source=fs.readFileSync(require('node:path').join(__dirname,'../src/pler/web/app.js'),'utf8');
const code=source.slice(source.indexOf('function quotaWindowNow('),source.indexOf('function usageOutlookText('));
const NOW=Date.parse('2026-10-31T12:00:00Z'),iso=offset=>new Date(NOW+offset).toISOString(),MIN=60e3,HOUR=3600e3;
function element(tag='div',cls='',text=''){
  return {tag,className:cls,textContent:text,hidden:false,checked:false,type:'',children:[],
    replaceChildren(...items){this.children=[...items];}};
}
function storage(initial={}){const values={...initial};return {getItem:key=>key in values?values[key]:null,setItem:(key,value)=>{values[key]=String(value);},values};}
function page({permission='granted',outlook=[],local={},session={},answer='granted'}={}){
  const ids={'usage-quota-alert':element('p'),'usage-live':element('div'),'usage-live-watch':element('input'),
    'usage-live-notify':element('button'),'usage-live-note':element('small')};
  const shown=[],posts=[],loads=[],intervals=[];
  class FakeNotification{constructor(title,options){shown.push([title,options.body,options.tag]);}
    static async requestPermission(){FakeNotification.permission=answer;return answer;}}
  FakeNotification.permission=permission;
  const state={stopped:false,loading:false,data:{has_snapshot:true,state:'ready',outlook}};
  const doc={activeElement:null,dialogOpen:false,querySelector:()=>doc.dialogOpen?{}:null};
  const context=vm.createContext({usageState:state,$:id=>ids[id],document:doc,Date:{now:()=>NOW,parse:Date.parse},
    t:(key,values)=>values?key+' '+JSON.stringify(values):key,usageAgents:{'claude-code':'Claude Code',codex:'Codex'},
    usageWindow:minutes=>minutes===300?'5-hour':'weekly',usageDate:value=>value,usageDuration:seconds=>Math.round(seconds/60)+' min',
    node:(tag,cls,text)=>element(tag,cls,text),localStorage:storage(local),sessionStorage:storage(session),Notification:FakeNotification,
    post:async(path,body)=>{posts.push(path);},loadUsage:async()=>{loads.push(true);},
    setInterval:(handler,every)=>{intervals.push([handler,every]);return intervals.length;},clearInterval:()=>{},JSON,Set,Number,Math});
  vm.runInContext(code,context);
  context.live=()=>vm.runInContext('liveState',context);  // a top-level const is not a context property
  return {context,ids,shown,posts,loads,intervals,state,doc,FakeNotification};
}
const window=(minutes,state,extra={})=>({agent:'codex',window_minutes:minutes,state,at:iso(-5*MIN),used_percent:90,resets_at:iso(3*HOUR),
  max_age_seconds:minutes<1440?1800:86400,...extra});

test('a full window, or one filling within the lead time, is a warning; later, stale or reset ones are not',()=>{
  const outlook=[window(300,'full',{used_percent:100}),window(300,'fills_before_reset',{full_at:iso(40*MIN),resets_at:iso(2*HOUR)}),
    window(10080,'fills_before_reset',{full_at:iso(20*HOUR),resets_at:iso(48*HOUR)}),
    window(300,'fills_before_reset',{agent:'claude-code',full_at:iso(2*HOUR),resets_at:iso(4*HOUR)}),
    window(300,'fills_before_reset',{agent:'claude-code',at:iso(-2*HOUR),full_at:iso(30*MIN)}),
    window(300,'full',{agent:'claude-code',resets_at:iso(-MIN)})];
  const p=page({outlook}),alerts=p.context.quotaAlerts(p.state.data);
  assert.deepEqual(JSON.parse(JSON.stringify(alerts.map(alert=>alert.level+':'+alert.window.agent+':'+alert.window.window_minutes))),
    ['full:codex:300','soon:codex:300','soon:codex:10080']);
  p.context.renderQuotaAlerts();
  assert.equal(p.ids['usage-quota-alert'].hidden,false);
  const texts=p.ids['usage-quota-alert'].children.map(item=>item.textContent);
  assert.match(texts[0],/^quota_alert_full /);
  assert.ok(texts[1].startsWith('quota_alert_soon')&&texts[1].includes('"left":"40 min"')&&texts[1].includes('"window":"5-hour"'));
  const calm=page({outlook:[window(300,'lasts_until_reset')]});calm.context.renderQuotaAlerts();
  assert.equal(calm.ids['usage-quota-alert'].hidden,true);
});

test('each warning is notified once, also after a reload, and only when notifications are on',()=>{
  const outlook=[window(300,'fills_before_reset',{full_at:iso(30*MIN)})];
  const off=page({outlook});off.context.liveLoad();off.context.renderQuotaAlerts();assert.equal(off.shown.length,0);
  const p=page({outlook,local:{'pler-live':JSON.stringify({watch:false,notify:true})}});
  p.context.liveLoad();p.context.renderQuotaAlerts();p.context.renderQuotaAlerts();
  assert.equal(p.shown.length,1);assert.equal(p.shown[0][0],'quota_alert_title');assert.match(p.shown[0][1],/^quota_alert_soon /);
  const again=page({outlook,local:{'pler-live':JSON.stringify({notify:true})},session:{'pler-quota-notified':p.context.sessionStorage.values['pler-quota-notified']}});
  again.context.liveLoad();again.context.renderQuotaAlerts();assert.equal(again.shown.length,0);
  const revoked=page({outlook,permission:'denied',local:{'pler-live':JSON.stringify({notify:true})}});
  revoked.context.liveLoad();revoked.context.renderQuotaAlerts();assert.equal(revoked.shown.length,0);
});

test('turning notifications on asks the browser once; a refusal is explained and the page warning stays',async()=>{
  const p=page({permission:'default',answer:'granted',outlook:[window(300,'full')]});
  await p.context.toggleQuotaNotifications();
  assert.equal(p.context.live().notify,true);assert.equal(p.shown.length,1);
  assert.equal(p.ids['usage-live-note'].textContent,'live_notify_active');assert.equal(p.ids['usage-live-notify'].textContent,'live_notify_off');
  await p.context.toggleQuotaNotifications();assert.equal(p.context.live().notify,false);
  const refused=page({permission:'default',answer:'denied'});
  await refused.context.toggleQuotaNotifications();
  assert.equal(refused.context.live().notify,false);
  assert.equal(refused.ids['usage-live-note'].textContent,'live_notify_blocked');assert.equal(refused.ids['usage-live-notify'].hidden,true);
});

test('live watching reads again on a timer, never while the user is busy, and remembers the choice',async()=>{
  const p=page();
  p.context.setLiveWatch(true);
  assert.deepEqual(JSON.parse(p.context.localStorage.values['pler-live']),{watch:true,notify:false});
  assert.equal(p.intervals[0][1],5*60e3);assert.equal(p.ids['usage-live-watch'].checked,true);
  const tick=p.intervals[0][0];
  p.doc.activeElement={tagName:'INPUT',type:'text'};await tick();
  p.doc.activeElement={tagName:'INPUT',type:'checkbox'};p.doc.dialogOpen=true;await tick();
  p.doc.dialogOpen=false;p.state.loading=true;await tick();
  p.state.loading=false;p.state.data.state='scanning';await tick();
  assert.equal(p.posts.length,0);
  p.state.data.state='ready';await tick();
  assert.deepEqual(p.posts,['/api/usage/refresh']);assert.equal(p.loads.length,1);
  p.context.setLiveWatch(false);await tick();assert.equal(p.posts.length,1);
});
