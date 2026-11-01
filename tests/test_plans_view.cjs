'use strict';
// Run the shipped plan panel against a fake page; no browser or dependencies required.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test');
const source=fs.readFileSync(require('node:path').join(__dirname,'../src/pler/web/app.js'),'utf8');
const table=JSON.parse(source.split('/*I18N*/')[1].split('/*END*/')[0]);
const code=source.slice(source.indexOf('const planNames='),source.indexOf('function renderUsageQuota('));
function element(tag='div',cls='',text=''){
  return {tag,className:cls,textContent:text,id:'',value:'',dataset:{},attributes:{},children:[],handlers:{},disabled:false,hidden:false,
    setAttribute(name,value){this.attributes[name]=value;},append(...items){this.children.push(...items);},
    replaceChildren(...items){this.children=[...items];},addEventListener(name,handler){this.handlers[name]=handler;}};
}
function walk(item,found=[]){found.push(item);for(const child of item.children||[])if(typeof child==='object')walk(child,found);return found;}
function page(plans,{reply}={}){
  const box=element('section'),posts=[],messages=[],loads=[];
  const state={stopped:false},clock={now:Date.now()};
  class ClockDate extends Date{static now(){return clock.now;}}
  const context=vm.createContext({usageState:state,$:id=>id==='usage-plans'?box:null,LOCALE:'en',Intl,I18N:table,Date:ClockDate,
    t:(key,values)=>values?key+' '+JSON.stringify(values):key,number:String,usageAgents:{'claude-code':'Claude Code',codex:'Codex'},
    usageUsd:value=>'$'+Number(value).toFixed(2),usagePct:value=>Math.round(value*100)+'%',notice:text=>messages.push(text),
    loadUsage:async()=>{loads.push(true);},
    node:(tag,cls,text)=>element(tag,cls,text),document:{createElement:tag=>element(tag),querySelectorAll:()=>walk(box).filter(item=>(item.className||'').includes('plan-comparison'))},
    post:async(path,body)=>{posts.push([path,body]);if(reply)return reply(body);return {ok:true,plan:body.plan};}});
  vm.runInContext(code,context);
  context.renderUsagePlans({plans});
  return {box,posts,messages,loads,context,state,clock,texts:()=>walk(box).map(item=>item.textContent).filter(Boolean)};
}
const plain=value=>JSON.parse(JSON.stringify(value));
const codex={agent:'codex',plan:'plus',plan_word:'plus',price_usd:20,api_usd:214.66,api_priced_share:0.9,usage_partial:true,
  meter:[{window_minutes:300,full:9,periods:41},{window_minutes:10080,full:1,periods:12}],findings:['limits_reached','larger_ratio_unpublished']};
const claude={agent:'claude-code',plan:null,plan_word:null,price_usd:null,api_usd:464.38,api_priced_share:1,usage_partial:false,meter:[],
  findings:['choose_plan','no_meter']};
const value={rows:[claude,codex],prices_as_of:'2026-10-31',choices:['pro','max','ultra','api'],readable:true};

test('each agent gets its plan, API equivalent, limits and findings as plain text',()=>{
  const p=page(value),texts=p.texts();
  assert.equal(p.box.hidden,false);
  assert.ok(texts.includes('Claude Code: plan_unchosen'));
  assert.ok(texts.some(text=>text.startsWith('Codex: plan_named')&&text.includes('"name":"Plus"')&&text.includes('"price":"20"')));
  assert.ok(texts.some(text=>text.startsWith('plan_api_line')&&text.includes('$214.66')&&text.endsWith('plan_partial')));
  assert.ok(texts.some(text=>text.startsWith('plan_meter_line')&&text.includes('"five":"9"')&&text.includes('"week_total":"12"')));
  for(const key of ['plan_choose_plan','plan_no_meter','plan_larger_ratio_unpublished','plan_note'])assert.ok(texts.includes(key),key);
  assert.ok(texts.some(text=>text.startsWith('plan_period')&&text.includes('2026')));
  assert.equal(walk(p.box).filter(item=>(item.className||'').includes('plan-row warn')).length,1);  // only Codex reached a limit
});

test('choosing a Claude plan saves one word and reads the view again',async()=>{
  const p=page(value),select=walk(p.box).find(item=>item.tag==='select');
  assert.deepEqual(plain(select.children.map(option=>option.value)),['','pro','max','ultra','api']);
  assert.equal(select.value,'');
  select.value='max';await select.handlers.change();
  assert.deepEqual(plain(p.posts),[['/api/usage/plan',{plan:'max'}]]);
  assert.equal(p.loads.length,1);
  select.value='';await select.handlers.change();
  assert.deepEqual(plain(p.posts[1]),['/api/usage/plan',{plan:null}]);
});

test('a refused save is shown and an unreadable choice disables the selector',async()=>{
  const p=page(value,{reply:()=>{throw new Error('error.plan_save');}});
  const select=walk(p.box).find(item=>item.tag==='select');select.value='pro';await select.handlers.change();
  assert.deepEqual(p.messages,['error.plan_save']);assert.equal(p.loads.length,0);
  const locked=page({...value,readable:false});
  assert.equal(walk(locked.box).find(item=>item.tag==='select').disabled,true);
  assert.ok(locked.texts().includes('plan_unreadable'));
});

test('an observed lower-plan comparison uses the server figures without a fit verdict',()=>{
  const max={agent:'claude-code',plan:'max',plan_word:'max',price_usd:100,api_usd:150,api_priced_share:1,usage_partial:false,
    meter:[{window_minutes:300,full:0,periods:30},{window_minutes:10080,full:0,periods:3}],findings:['lower_observed'],
    lower_plan_comparison:{plan:'pro',usd:20,unmeasured:false,share:0.2,peak:15,assumed_plan:'max',observed_only:true,
      expires_at:new Date(Date.now()+60000).toISOString()}};
  const p=page({...value,rows:[max]});
  const text=p.texts().find(item=>item.startsWith('plan_lower_observed'));
  assert.ok(text.includes('"smaller":"Pro"')&&text.includes('"share":"20%"')&&text.includes('"peak":"15%"')&&text.includes('"price":"$20.00"'));
  const empty=page({...value,rows:[]});
  assert.equal(empty.box.hidden,true);
});

test('unpriced and empty periods show unknown rather than a zero-dollar price',()=>{
  for(const share of [0,null]){
    const p=page({...value,rows:[{...codex,api_priced_share:share,api_usd:0,findings:[],limitations:['unpriced_usage']}]});
    assert.ok(p.texts().includes('plan_api_unknown'));
    assert.ok(p.texts().includes('plan_limit_unpriced_usage'));
    assert.ok(p.texts().includes('plan_payment_unknown'));
    assert.ok(!p.texts().some(text=>text.startsWith('plan_api_line')));
  }
});

test('source limits are visible and unknown reason codes are ignored',()=>{
  const p=page({...value,rows:[{...codex,findings:[],limitations:['source_incomplete','multiple_source_groups','PRIVATE']} ]});
  assert.ok(p.texts().includes('plan_limit_source_incomplete'));
  assert.ok(p.texts().includes('plan_limit_multiple_source_groups'));
  assert.ok(!p.texts().some(text=>text.includes('PRIVATE')));
});

test('a comparison ages without rebuilding or changing the plan selector',()=>{
  const expiry=new Date(Date.now()+60000).toISOString();
  const p=page({...value,rows:[{...claude,plan:'max',findings:['lower_observed'],
    lower_plan_comparison:{plan:'pro',usd:20,peak:10,share:0.2,assumed_plan:'max',expires_at:expiry}}]});
  const select=walk(p.box).find(item=>item.tag==='select');
  p.clock.now=Date.parse(expiry)+1;p.context.agePlanComparisons();
  assert.ok(p.texts().includes('plan_comparison_expired'));
  assert.strictEqual(walk(p.box).find(item=>item.tag==='select'),select);
  assert.ok(!p.texts().some(text=>text.startsWith('plan_lower_observed')));
});

test('an already expired comparison or missing expiry is not presented on initial render',()=>{
  for(const expires_at of [undefined,'invalid',new Date(Date.now()-1000).toISOString()]){
    const p=page({...value,rows:[{...claude,findings:['lower_observed'],
      lower_plan_comparison:{plan:'pro',usd:20,peak:10,share:0.2,assumed_plan:'max',expires_at}}]});
    assert.ok(p.texts().includes('plan_comparison_expired'));
    assert.ok(!p.texts().some(text=>text.startsWith('plan_lower_observed')));
  }
});

test('missing Codex meters never suggest installing the Claude status line',()=>{
  const p=page({...value,rows:[{...codex,meter:[],findings:['no_meter']}]});
  assert.ok(p.texts().includes('plan_no_meter_codex'));
  assert.ok(!p.texts().includes('plan_no_meter'));
  const other=page({...value,rows:[claude]});
  assert.ok(other.texts().includes('plan_no_meter'));
  assert.ok(!other.texts().includes('plan_no_meter_codex'));
});
