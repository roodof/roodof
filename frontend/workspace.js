import {mountSessionsGrid} from './sessions-grid.js';
import {mountNavigation,mountSegments} from './primitives.jsx';
import {enterPage,installFeedback} from './feedback.js';
import { init, use } from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, AriaComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { createElement, LayoutDashboard, ListFilter, Layers, Gauge, Settings2, Search, ShieldCheck, ArrowUpRight, ChartNoAxesCombined } from 'lucide';

use([BarChart, GridComponent, TooltipComponent, AriaComponent, CanvasRenderer]);
const tr = document.documentElement.lang === 'tr';
const words = tr ? {
  overview:'Kullanım',sessions:'Oturumlar',work:'İşlerim',quota:'Kotalar',settings:'Ayarlar',
  warning:'Kota uyarısı',workspace:'Çalışma alanı',find:'Bir bölüme git…',local:'Verilerin bu bilgisayarda',localNote:'Yerel kayıtlar · Model çağrısı yok',
  overviewIntro:'Kullanımını anla. Bir sonraki işine odaklan.',sessionsIntro:'Oturumlarını bul, ayrıntılarını incele ve işlerine bağla.',
  workIntro:'Bir işe ait oturumlar, hedefler ve sonuçlar bir arada.',quotaIntro:'Kota gözlemleri ve model kullanımının ayrıntıları.',settingsIntro:'Yerel geçmişini sakla, yedekle ve yönet.',
  chart:'Kullanımın nerede yoğunlaşıyor?',chartNote:'Seçili oturumların kaydedilmiş toplam tokenları. Bir projeye tıklayarak oturumlarını aç.',
  chartEmpty:'Projelerin burada görünecek',chartEmptyNote:'Kayıtlar okunduğunda seçili projelerin dağılımını görebilirsin.',
  export:'Dışa aktarma seçenekleri',allSessions:'Oturumları incele',chartLabel:'Projelere göre kaydedilmiş toplam tokenlar',noMatch:'Bölüm bulunamadı',close:'Kapat'
} : {
  overview:'Usage',sessions:'Sessions',work:'My work',quota:'Limits',settings:'Settings',
  warning:'Quota warning',workspace:'Workspace',find:'Jump to a section…',local:'Your data stays here',localNote:'Local records · No model calls',
  overviewIntro:'Understand your usage. Focus on your next piece of work.',sessionsIntro:'Find sessions, explore their details and connect them to your work.',
  workIntro:'The sessions, goals and outcomes behind each piece of work.',quotaIntro:'Quota observations and a closer look at model usage.',settingsIntro:'Keep, back up and manage your local history.',
  chart:'Where is your usage going?',chartNote:'Recorded total tokens in the selected sessions. Click a project to explore its sessions.',
  chartEmpty:'Your projects will appear here',chartEmptyNote:'Read your records to see how usage is distributed across your selected projects.',
  export:'Export options',allSessions:'Explore sessions',chartLabel:'Recorded total tokens by project',noMatch:'No matching section',close:'Close'
};
const $ = id => document.getElementById(id);
function el(tag, cls, text) { const item=document.createElement(tag); if(cls)item.className=cls; if(text)item.textContent=text; return item; }
function icon(node) { const svg=createElement(node,{width:19,height:19,'stroke-width':1.65,'aria-hidden':'true'}); return svg; }
const pages = {};
const routes=[['sessions',ListFilter],['work',Layers],['overview',LayoutDashboard],['quota',Gauge],['settings',Settings2]];
const sidebar=el('aside','ws-sidebar');
const brand=el('a','ws-brand','PLER');brand.href='/';brand.prepend(el('span','ws-symbol','∥')); sidebar.append(brand);
const find=el('button','ws-find');find.type='button';find.append(icon(Search),el('span','',words.find),el('kbd','','Ctrl K'));sidebar.append(find,el('p','ws-nav-label',words.workspace));
find.setAttribute('aria-label',words.find);
const nav=el('nav','ws-nav');nav.setAttribute('aria-label',words.workspace);sidebar.append(nav);
const local=el('div','ws-local');local.append(icon(ShieldCheck),el('strong','',words.local),el('small','',words.localNote));sidebar.append(local);
document.body.prepend(sidebar);document.body.classList.add('workspace-redesign');
const content=$('usage-content');
for(const [name,node] of routes) {
  const section=el('div','ws-page');section.dataset.page=name;section.hidden=true;pages[name]=section;content.append(section);
}
const navigation=mountNavigation(nav,routes,words,name=>show(name,true));
const groups={overview:['usage-totals','usage-dated','usage-data-guidance','usage-insights','usage-columns','usage-coverage'],sessions:['usage-session-section'],work:['usage-work-items'],quota:['usage-quota','usage-plans','usage-mix','usage-live'],settings:['usage-archive-controls']};
for(const [name,ids] of Object.entries(groups)) for(const id of ids) if($(id))pages[name].append($(id));
const chartCard=el('section','ws-chart usage-panel');
const chartHead=el('div','ws-chart-heading');const chartWords=el('div');chartWords.append(el('h2','',words.chart),el('p','section-note',words.chartNote));
const chartLink=el('button','secondary',words.allSessions);chartLink.append(icon(ArrowUpRight));chartLink.addEventListener('click',()=>show('sessions',true));chartHead.append(chartWords,chartLink);
const chartNode=el('div','ws-chart-canvas');chartNode.setAttribute('role','img');chartNode.setAttribute('aria-label',words.chartLabel);
const chartEmpty=el('div','ws-chart-empty');chartEmpty.append(icon(ChartNoAxesCombined),el('strong','',words.chartEmpty),el('p','',words.chartEmptyNote));chartCard.append(chartHead,chartNode,chartEmpty);
pages.overview.insertBefore(chartCard,$('usage-dated'));
const options=document.querySelector('.export-options');const exportDetails=el('details','ws-export-options');exportDetails.append(el('summary','',words.export));exportDetails.append(options);pages.settings.append(exportDetails);
const coverage=el('details','ws-coverage');const coverageSummary=el('summary','',tr?'Veri kapsamı ve uyarılar':'Data coverage & warnings');coverage.append(coverageSummary);$('usage-data-guidance').before(coverage);coverage.append($('usage-data-guidance'));
const h1=document.querySelector('.workspace-head h1');const intro=document.querySelector('.usage-intro');
let current='overview',chart=null,lastData=null,linkingWork=null;
function show(name,focus=false) {
  if(!pages[name])name='sessions';current=name;
  if($('notice').dataset.kind==='success')notice('');
  if(name!=='sessions'&&$('usage-session-dialog').open)$('usage-session-dialog').close();
  for(const [id,page] of Object.entries(pages))page.hidden=id!==name;
  navigation.setActive(name);
  h1.textContent=words[name];intro.textContent=words[name+'Intro'];
  document.dispatchEvent(new CustomEvent('pler-screen-change',{detail:name}));
  document.title='PLER · '+words[name];
  if(name==='settings')$('usage-archive-controls').open=true;
  document.querySelector('.workspace-head .eyebrow').textContent=words.workspace+' / '+words[name];
  document.body.dataset.screen=name;
  try{sessionStorage.setItem('pler-screen',name);}catch{}
  enterPage(pages[name]);
  if(focus){h1.tabIndex=-1;h1.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}
  if(name==='overview')requestAnimationFrame(()=>chart?.resize());
}
$('usage-quality-show').addEventListener('click',()=>show('sessions'),true);
function redraw() {
  const data=typeof usageState==='undefined'?null:usageState.data;
  coverage.hidden=$('usage-data-guidance').hidden;
  const warningCount=$('usage-data-guidance-items').children.length;coverageSummary.textContent=(tr?'Veri kapsamı ve uyarılar':'Data coverage & warnings')+(warningCount?' · '+warningCount:'');
  if(data?.sources?.unreadable)coverage.open=true;
  if(!data?.has_snapshot){chartCard.hidden=true;return;}chartCard.hidden=false;
  const palette=getComputedStyle(document.body);const token=name=>palette.getPropertyValue('--ui-'+name).trim();
  const rows=(data.projects||[]).slice(0,6);chartEmpty.hidden=rows.length>0;chartNode.hidden=!rows.length;
  if(!rows.length)return;
  if(!chart){chart=init(chartNode,null,{renderer:'canvas'});chart.on('click',event=>{const row=lastData?.[event.dataIndex];if(!row)return;$('usage-project').value=row.id;$('usage-project').dispatchEvent(new Event('change',{bubbles:true}));show('sessions',true);});}
  lastData=rows;
  chart.setOption({animation:!matchMedia('(prefers-reduced-motion: reduce)').matches,aria:{enabled:true},grid:{left:16,right:60,top:18,bottom:22,containLabel:true},tooltip:{trigger:'axis',renderMode:'richText',axisPointer:{type:'shadow'},valueFormatter:value=>Number(value).toLocaleString(tr?'tr-TR':'en-US')+' tokens'},xAxis:{type:'value',axisLabel:{color:token('muted'),formatter:n=>n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?(n/1e3).toFixed(0)+'k':n},splitLine:{lineStyle:{color:token('border')}},axisLine:{show:false}},yAxis:{type:'category',inverse:true,data:rows.map(p=>p.name),axisLine:{show:false},axisTick:{show:false},axisLabel:{color:token('secondary'),width:150,overflow:'truncate',fontSize:12}},series:[{type:'bar',barMaxWidth:25,data:rows.map((p,i)=>({value:p.total_tokens,itemStyle:{color:i===0?token('text'):token('muted'),borderRadius:[0,5,5,0]}})),emphasis:{itemStyle:{color:token('text')}}}]},true);
}
let timer;const observer=new MutationObserver(()=>{clearTimeout(timer);timer=setTimeout(redraw,60);});observer.observe($('usage-totals'),{childList:true});observer.observe(content,{attributes:true,attributeFilter:['hidden']});
new ResizeObserver(()=>{if(current==='overview')chart?.resize();}).observe(chartNode);
const palette=el('dialog','ws-palette');palette.setAttribute('aria-label',words.find);const search=el('input');search.type='search';search.placeholder=words.find;search.setAttribute('aria-label',words.find);const choices=el('div','ws-command-list');const close=el('button','quiet',words.close);close.addEventListener('click',()=>palette.close());palette.append(search,choices,close);document.body.append(palette);
function commands(){choices.replaceChildren();for(const [name,node] of routes){if(!words[name].toLocaleLowerCase().includes(search.value.toLocaleLowerCase()))continue;const button=el('button','ws-command');button.append(icon(node),el('span','',words[name]));button.addEventListener('click',()=>{palette.close();show(name,true);});choices.append(button);}if(!choices.childElementCount)choices.append(el('p','section-note',words.noMatch));}
search.addEventListener('input',commands);search.addEventListener('keydown',event=>{if(event.key==='ArrowDown'){event.preventDefault();choices.querySelector('button')?.focus();}if(event.key==='Enter'){event.preventDefault();choices.querySelector('button')?.click();}});
find.addEventListener('click',()=>{search.value='';commands();palette.showModal();search.focus();});
document.addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();if(!palette.open)find.click();else palette.close();}});
let saved;try{saved=sessionStorage.getItem('pler-screen');}catch{}show(saved||'sessions');redraw();

// A working session browser, not another dashboard landing page.
document.body.classList.add('session-workbench');
const scope=document.querySelector('.usage-scope');const scopeDetails=el('details','wb-scope');scopeDetails.append(el('summary','',tr?'Bu kayıtların kapsamı':'About these records'));scope.before(scopeDetails);scopeDetails.append(scope);for(const note of [$('usage-session-scope'),$('usage-verdict-summary'),document.querySelector('[data-i18n=quality_filter_note]')])if(note)scopeDetails.append(note);
const bar=el('div','wb-filterbar');
const segments=new Map();
function segmented(id,values){
 const group=el('div','wb-segmented');group.setAttribute('role','group');group.setAttribute('aria-label',$(id).previousElementSibling.textContent);group.dataset.select=id;
 const control=mountSegments(group,values,$(id).value,value=>{$(id).value=value;$(id).dispatchEvent(new Event('change',{bubbles:true}));});
 segments.set(id,control);$(id).addEventListener('change',()=>control.setValue($(id).value));return group;
}
bar.append(segmented('usage-agent',[['all',tr?'Tümü':'All agents'],['claude-code','Claude'],['codex','Codex']]),segmented('usage-period',[['7',tr?'7 gün':'7 days'],['30',tr?'30 gün':'30 days'],['90',tr?'90 gün':'90 days'],['0',tr?'Tümü':'All time']]));
document.querySelector('.usage-filters').prepend(bar);
const sessionTools=el('div','wb-list-tools');const listLabel=el('span','wb-list-label',tr?'OTURUMLAR':'SESSIONS');const listHint=el('span','wb-list-hint',tr?'Satırı aç · ↑ ↓ ile gezin':'Open a row · navigate with ↑ ↓');sessionTools.append(listLabel,$('usage-session-count'),listHint);$('usage-session-section').prepend(sessionTools);
const list=$('usage-sessions'), inspector=$('usage-session-dialog');
const inspectorTools=el('div','wb-inspector-tools');const prev=el('button','quiet','↑');const next=el('button','quiet','↓');prev.setAttribute('aria-label',tr?'Önceki oturum':'Previous session');next.setAttribute('aria-label',tr?'Sonraki oturum':'Next session');const position=el('span');inspectorTools.append(position,prev,next);inspector.insertBefore(inspectorTools,$('usage-session-detail'));
function selectedRow(){return [...list.children].find(row=>row.dataset.sessionId===(typeof workState==='undefined'?null:workState.openSession));}
function syncRows(){const selected=selectedRow();for(const row of list.children){const active=inspector.open&&row===selected;row.classList.toggle('wb-selected',active);row.querySelector('button')?.setAttribute('aria-expanded',String(active));}const index=[...list.children].indexOf(selected);position.textContent=index>=0?`${index+1} / ${list.children.length}`:'';prev.disabled=index<=0;next.disabled=index<0||index>=list.children.length-1;}
function stepRow(delta){const rows=[...list.children];const index=rows.indexOf(selectedRow());const target=rows[Math.max(0,Math.min(rows.length-1,index+delta))];target?.querySelector('button')?.click();}
prev.addEventListener('click',()=>stepRow(-1));next.addEventListener('click',()=>stepRow(1));
window.plerShowSession=(opened)=>{
const detail=$('usage-session-detail'),dl=detail.querySelector('dl');
const session=opened||usageState.data?.sessions.find(item=>item.id===workState.openSession);
if(dl&&!dl.closest('details')){
 const fields=el('details','wb-record-fields');fields.append(el('summary','',tr?'Tüm kayıt bilgileri':'All record details'));dl.before(fields);fields.append(dl);
 const provenance=el('details','wb-provenance');provenance.append(el('summary','',tr?'Veri kapsamı ve yöntem':'Data coverage and method'));
 for(const note of detail.querySelectorAll(':scope > .section-note,:scope > .session-detail-intro'))provenance.append(note);
 detail.append(provenance);
 if(session){
  const namedWork=usageState.data?.work_items?.items.find(w=>w.session_ids.includes(session.id));
  if(namedWork)$('usage-session-title').textContent=namedWork.title;
  const identity=el('div','wb-session-identity');
  if(namedWork)identity.append(el('span','',session.project));
  identity.append(el('strong','',session.agent==='codex'?'Codex':'Claude Code'),el('span','',usageDate(session.started)+' → '+usageDate(session.ended)),el('code','','#'+usageSessionCode(session)));
  detail.prepend(identity);
  const metrics=el('div','wb-session-metrics');
  for(const [label,value] of [[tr?'Kayıtlı token':'Recorded tokens',number(session.total_tokens)],[tr?'Model çağrısı':'Model calls',session.calls_complete?number(session.calls):tr?'Bilinmiyor':'Unknown']]){const stat=el('div');stat.append(el('small','',label),el('strong','',value));metrics.append(stat);}identity.after(metrics);
  const work=$('usage-session-work-items');if(work)fields.before(work);
  if(linkingWork&&usageState.data?.work_items?.items.some(w=>w.id===linkingWork&&!w.session_ids.includes(session.id))){workState.sessionChoices[session.id]=linkingWork;renderSessionWorkItems();}
 }
}
show('sessions');
const previous=document.activeElement;if(!inspector.open)inspector.show();document.body.classList.add('inspector-open');syncRows();if(previous?.closest('#usage-sessions'))previous.focus({preventScroll:true});inspector.scrollTop=0;
};
inspector.addEventListener('close',()=>{document.body.classList.remove('inspector-open');syncRows();});
list.addEventListener('click',event=>{const row=event.target.closest('tr');if(!row||event.target.closest('button,a,input,select'))return;row.querySelector('button')?.click();});
list.addEventListener('keydown',event=>{if(!['ArrowDown','ArrowUp'].includes(event.key)||event.target.closest('select,input'))return;const rows=[...list.children],index=rows.indexOf(event.target.closest('tr'));const target=rows[index+(event.key==='ArrowDown'?1:-1)];if(!target)return;event.preventDefault();const b=target.querySelector('button');b.click();b.focus({preventScroll:true});target.scrollIntoView({block:'nearest'});});
new MutationObserver(syncRows).observe(list,{childList:true});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&inspector.open&&!palette.open){event.preventDefault();inspector.close();}});
// Keep the existing data-quality filter, with a compact, explicit label.
const qualityLabel=$('usage-quality-only').closest('label');qualityLabel.classList.add('wb-quality');
mountSessionsGrid({tr,list,inspector});

// Keep reading metadata available without making it the first task on every screen.
scopeDetails.append($('usage-status'));
pages.sessions.append(scopeDetails);
const exportPanel=el('section','ws-report usage-panel');
exportPanel.append(el('h2','',tr?'Kullanım raporu':'Usage report'),el('p','section-note',tr?'JSON raporu seçili ajan, dönem ve projeyi kapsar. Oturum araması, liste sıralaması ve veri kalitesi filtresi raporu daraltmaz.':'The JSON report covers the selected agent, period and project. Session search, list sorting and the data-quality filter do not narrow the report.'));
const reportScope=el('p','ws-report-scope');exportPanel.append(reportScope,$('usage-export'),$('usage-download-result'),exportDetails);pages.settings.prepend(exportPanel);
function updateReportScope(){reportScope.textContent=[...document.querySelectorAll('.usage-filters select')].map(s=>s.selectedOptions[0]?.textContent).filter(Boolean).join(' · ');}
for(const id of ['usage-agent','usage-period','usage-project'])$(id).addEventListener('change',updateReportScope);
new MutationObserver(updateReportScope).observe($('usage-project'),{childList:true});updateReportScope();
const linkBanner=el('div','wb-link-banner');linkBanner.hidden=true;
const linkTitle=el('strong');const finishLink=el('button','secondary',tr?'İşe dön':'Back to work');
finishLink.addEventListener('click',()=>{linkingWork=null;linkBanner.hidden=true;show('work',true);});linkBanner.append(linkTitle,finishLink);pages.sessions.prepend(linkBanner);
const addSessions=el('button','primary wb-add-sessions',tr?'Oturum ekle →':'Add sessions →');addSessions.type='button';
addSessions.addEventListener('click',()=>{const work=selectedWork();if(!work)return;linkingWork=work.id;linkTitle.textContent=(tr?'Oturum eklenecek iş: ':'Adding sessions to: ')+work.title;linkBanner.hidden=false;show('sessions',true);$('usage-session-search').focus();});
$('usage-work-no-members').after(addSessions);
const workMembers=el('section','wb-work-sessions');workMembers.append(el('h3','',tr?'Bağlı oturumlar':'Linked sessions'),$('usage-work-counts'),$('usage-work-usage'),$('usage-work-quality'),$('usage-work-members'),$('usage-work-more'),$('usage-work-no-members'),addSessions);
$('usage-work-rename-form').after(workMembers);
// A compact, actionable badge keeps quota warnings discoverable in other sections.
function syncQuotaBadge(){const box=$('usage-quota-alert'),count=box.hidden?0:box.children.length;navigation.setWarning(count,box.textContent);}
new MutationObserver(syncQuotaBadge).observe($('usage-quota-alert'),{childList:true,subtree:true,attributes:true,attributeFilter:['hidden']});syncQuotaBadge();
installFeedback();

choices.addEventListener('keydown',event=>{const buttons=[...choices.querySelectorAll('button')],index=buttons.indexOf(document.activeElement);if(!buttons.length)return;if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?buttons.length-1:(index+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length;buttons[next].focus();}});
const commandHint=el('div','ws-command-hint');commandHint.append(el('kbd','','↑ ↓'),el('span','',tr?'Gezin':'Navigate'),el('kbd','','Enter'),el('span','',tr?'Aç':'Open'),el('kbd','','Esc'),el('span','',tr?'Kapat':'Close'));palette.append(commandHint);

// The placeholder is structural, never invented usage. Retain old data during refresh.
const skeleton=el('section','ws-skeleton');skeleton.setAttribute('aria-hidden','true');skeleton.hidden=true;skeleton.append(el('p','',tr?'Yerel kayıtlar okunuyor…':'Reading local records…'));
for(let i=0;i<5;i++){const row=el('div','ws-skeleton-row');row.append(el('span'),el('span'),el('span'));skeleton.append(row);}
content.before(skeleton);
function syncLoading(){const data=usageState.data,busy=usageState.loading||!$('usage-progress').hidden,initial=busy&&!data?.has_snapshot;skeleton.hidden=!initial;document.body.classList.toggle('is-refreshing',Boolean(busy&&data?.has_snapshot));document.body.dataset.hasSessions=String(Boolean(data?.totals.sessions));}
new MutationObserver(syncLoading).observe($('usage-progress'),{attributes:true,attributeFilter:['hidden']});new MutationObserver(syncLoading).observe(content,{attributes:true,attributeFilter:['hidden','aria-busy']});syncLoading();
for(const target of [$('usage-empty'),$('usage-search-empty')]){const glyph=el('div','ws-empty-glyph');glyph.append(icon(ListFilter),el('kbd','','Ctrl K'));target.prepend(glyph);}
$('usage-session-search').addEventListener('keydown',event=>{if(event.key==='Escape'&&$('usage-session-search').value){event.preventDefault();$('usage-search-clear').click();}});

const workScope=el('details','wb-work-scope');workScope.append(el('summary','',tr?'İş kapsamı ve gizlilik':'Work scope and privacy'));
for(const key of ['work_scope','work_api_note','work_privacy']){const paragraph=$('usage-work-items').querySelector(':scope > [data-i18n='+key+']');if(paragraph)workScope.append(paragraph);}
$('usage-work-items').append(workScope);
const workGlyph=el('div','ws-empty-glyph');workGlyph.append(icon(Layers));$('usage-work-empty').before(workGlyph);
new MutationObserver(()=>{workGlyph.hidden=$('usage-work-empty').hidden;}).observe($('usage-work-empty'),{attributes:true,attributeFilter:['hidden']});workGlyph.hidden=$('usage-work-empty').hidden;
