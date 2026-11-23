import {mountFirstUse} from './first-use.js';
import {mountHistoryRecovery} from './history-recovery.js';
import {mountSessionUsage} from './session-usage.js';
import {mountSettings} from './settings.js';
import {mountSearchRecovery} from './search-recovery.js';
import {mountBudgets} from './session-budgets.js';
import {mountSourceFolders} from './source-folders.js';
import {mountReconnections} from './session-reconnections.js';
import {mountDiagnostics,titleStatus} from './diagnostics.js';
import {getView,saveView,installViewPreferences} from './view-preferences.js';
import {mountSessionsGrid} from './sessions-grid.js';
import {mountNavigation,mountSegments} from './primitives.jsx';
import {enterPage,installFeedback} from './feedback.js';
import {mountUsageTime} from './usage-time.js';
import {mountQuota} from './quota-view.jsx';
import {mountWork} from './work-view.jsx';
import {mountTour} from './tour.js';
import {mountSelectMenus} from './select-menu.jsx';
import {mountReadingLayers} from './reading-layers.js';
import { init, use } from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, AriaComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { createElement, LayoutDashboard, ListFilter, Layers, Gauge, Settings2, Search, ShieldCheck, ArrowUpRight, ChartNoAxesCombined } from 'lucide';

use([BarChart, GridComponent, TooltipComponent, AriaComponent, CanvasRenderer]);
const tr = document.documentElement.lang === 'tr';
const words = tr ? {
  overview:'Kullanım',sessions:'Oturumlar',work:'İşlerim',quota:t('account_limits'),settings:'Ayarlar',review:'Kayıt incelemesi',reviewIntro:'Kapsam, gözlemler ve hesaplama yöntemleri.',
  warning:t('account_limit_warning'),workspace:'Çalışma alanı',find:'Bir bölüme git…',local:'Verilerin bu bilgisayarda',localNote:'Yerel kayıtlar · Model çağrısı yok',
  overviewIntro:'Kullanımını anla. Bir sonraki işine odaklan.',sessionsIntro:'Oturumunu bul. Kullanımını gör, uyarını kur.',
  workIntro:'Bir işe ait oturumlar, hedefler ve sonuçlar bir arada.',quotaIntro:'Sağlayıcının belirlediği hesap sınırları. Kayıtlardaki son ölçümler gösterilir.',settingsIntro:'Yerel geçmişini sakla, yedekle ve yönet.',
  chart:'Kullanımın nerede yoğunlaşıyor?',chartNote:'Seçili oturumların kaydedilmiş toplam tokenları. Bir projeye tıklayarak oturumlarını aç.',
  chartEmpty:'Projelerin burada görünecek',chartEmptyNote:'Kayıtlar okunduğunda seçili projelerin dağılımını görebilirsin.',
  export:'Dışa aktarma seçenekleri',allSessions:'Oturumları incele',chartLabel:'Projelere göre kaydedilmiş toplam tokenlar',noMatch:'Bölüm bulunamadı',close:'Kapat'
} : {
  overview:'Usage',sessions:'Sessions',work:'My work',quota:t('account_limits'),settings:'Settings',review:'Record review',reviewIntro:'Coverage, observations and calculation methods.',
  warning:t('account_limit_warning'),workspace:'Workspace',find:'Jump to a section…',local:'Your data stays here',localNote:'Local records · No model calls',
  overviewIntro:'Understand your usage. Focus on your next piece of work.',sessionsIntro:'Find a session. See its usage and set an alert.',
  workIntro:'The sessions, goals and outcomes behind each piece of work.',quotaIntro:'Limits set by your provider, shown from the latest recorded samples.',settingsIntro:'Keep, back up and manage your local history.',
  chart:'Where is your usage going?',chartNote:'Recorded total tokens in the selected sessions. Click a project to explore its sessions.',
  chartEmpty:'Your projects will appear here',chartEmptyNote:'Read your records to see how usage is distributed across your selected projects.',
  export:'Export options',allSessions:'Explore sessions',chartLabel:'Recorded total tokens by project',noMatch:'No matching section',close:'Close'
};
const $ = id => document.getElementById(id);
const ui=window.plerUI;
function el(tag, cls, text) { const item=document.createElement(tag); if(cls)item.className=cls; if(text)item.textContent=text; return item; }
function icon(node) { const svg=createElement(node,{width:19,height:19,'stroke-width':1.65,'aria-hidden':'true'}); return svg; }
const pages = {};
const routes=[['sessions',ListFilter],['work',Layers],['overview',LayoutDashboard],['quota',Gauge],['review',ShieldCheck],['settings',Settings2]];
const sidebar=el('aside','ws-sidebar');
const brand=el('a','ws-brand','Roodof');brand.href=location.pathname+location.search;brand.prepend(el('span','ws-symbol','∥')); sidebar.append(brand);
// Home stays inside the mounted workspace: no document reload, lost language or drafts.
function openHome(event){event.preventDefault();show('sessions',true);}
brand.addEventListener('click',openHome);
document.querySelector('.topbar>.brand')?.addEventListener('click',openHome);
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
const identityStatus=el('p','section-note');identityStatus.id='session-identity-status';identityStatus.hidden=true;identityStatus.setAttribute('role','status');pages.settings.append(identityStatus);
const chartCard=el('section','ws-chart usage-panel');
const chartHead=el('div','ws-chart-heading');const chartWords=el('div');chartWords.append(el('h2','',words.chart),el('p','section-note',words.chartNote));
const chartLink=el('button','secondary',words.allSessions);chartLink.append(icon(ArrowUpRight));chartLink.addEventListener('click',()=>show('sessions',true));chartHead.append(chartWords,chartLink);
const chartNode=el('div','ws-chart-canvas');chartNode.setAttribute('role','img');chartNode.setAttribute('aria-label',words.chartLabel);
const chartEmpty=el('div','ws-chart-empty');chartEmpty.append(icon(ChartNoAxesCombined),el('strong','',words.chartEmpty),el('p','',words.chartEmptyNote));chartCard.append(chartHead,chartNode,chartEmpty);
pages.overview.insertBefore(chartCard,$('usage-dated'));
const timeCard=mountUsageTime({tr,before:chartCard,loadDayProjects:ui.dayProjects});
const quotaView=mountQuota({tr,page:pages.quota});
const options=document.querySelector('.export-options');const exportDetails=el('details','ws-export-options');exportDetails.append(el('summary','',words.export));exportDetails.append(options);pages.settings.append(exportDetails);
const coverage=el('section','ws-coverage');const coverageSummary=el('h3','',tr?'Veri kapsamı ve uyarılar':'Data coverage & warnings');coverage.append(coverageSummary);$('usage-data-guidance').before(coverage);coverage.append($('usage-data-guidance'));
const h1=document.querySelector('.workspace-head h1');const intro=document.querySelector('.usage-intro');
let current=null,chart=null,lastData=null,linkingWork=null,workDirty=true;
const renderedViews={overview:new WeakSet(),quota:new WeakSet()};
// Mounted further down, once the work page is rearranged; redraw() may run before that.
let workView=null,tour=null,firstUse=null,budgetUI=null,diagnosticUI=null,reconnectionUI=null,settingsUI=null,readingLayers=null;
function revealSetting(target){show('settings',true);settingsUI?.reveal(target);}
function show(name,focus=false) {
  if(!Object.hasOwn(pages,name))name='sessions';
  if(current===name){if(focus){h1.tabIndex=-1;h1.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}return;}
  current=name;
  if($('notice').dataset.kind==='success')notice('');
  if(name!=='sessions'&&$('usage-session-dialog').open)$('usage-session-dialog').close();
  for(const [id,page] of Object.entries(pages))page.hidden=id!==name;
  navigation.setActive(name);
  h1.textContent=words[name];intro.textContent=words[name+'Intro'];
  document.dispatchEvent(new CustomEvent('pler-screen-change',{detail:name}));
  document.title='Roodof · '+words[name];
  document.querySelector('.workspace-head .eyebrow').textContent=words.workspace+' / '+words[name];
  document.body.dataset.screen=name;
  syncSettingsSurface();
  saveView({screen:name});
  enterPage(pages[name]);
  if(focus){h1.tabIndex=-1;h1.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}
  if(name==='overview')requestAnimationFrame(()=>{chart?.resize();timeCard?.resize();});
  if(name==='quota')requestAnimationFrame(()=>quotaView?.resize());
  ui.setScreen(name);
}
$('usage-quality-show').addEventListener('click',()=>show('sessions'),true);
function syncSettingsSurface(){
  const data=ui.get().data;
  const hidden=current!=='settings'&&!data?.has_snapshot;
  if(content.hidden!==hidden)content.hidden=hidden;
  const emptyHidden=current==='settings'||!data?.has_snapshot||Boolean(data?.totals?.sessions);
  if($('usage-empty').hidden!==emptyHidden)$('usage-empty').hidden=emptyHidden;
}
function redraw() {
  syncSettingsSurface();
  // Derived views consume the committed snapshot, after the controller's DOM update.
  const data=ui.get().data;
  const identity=data?.identity,uncertain=(identity?.unverified||0)+(identity?.conflicts||0);
  identityStatus.hidden=!identity?.limit_reached&&!uncertain&&!identity?.preserved&&!identity?.untracked;
  identityStatus.textContent=identity?.limit_reached?(tr?'Oturum kimliği izleme sınırına ulaşıldı. Yeni dosyaların taşınması otomatik korunamayabilir; mevcut bağlantılar saklanır.':'Session identity tracking reached its limit. Moves of new files may not be preserved automatically; existing links remain stored.'):uncertain?(tr?`${uncertain} oturumun eski kaynakla eşleşmesi doğrulanamadı. Eski bağlantılar ve ayarlar korundu; otomatik aktarılmadı.`:`${uncertain} sessions could not be verified against earlier sources. Previous links and settings were preserved, without automatic reassignment.`):identity?.untracked?(tr?`${identity.untracked} oturumda dosya kimliği doğrulanamadı. Bu kaynaklarda otomatik taşıma eşleştirmesi yapılamayabilir.`:`File identity could not be verified for ${identity.untracked} sessions. Automatic move matching may be unavailable for these sources.`):(tr?`${identity?.preserved||0} oturumda doğrulanmış dosya kimliği sayesinde bağlantı korundu.`:`Links were preserved for ${identity?.preserved||0} sessions using verified file identity.`);
  firstUse?.update(data);
  diagnosticUI?.update(data);
  coverage.hidden=$('usage-data-guidance').hidden;
  const warningCount=$('usage-data-guidance-items').children.length;coverageSummary.textContent=(tr?'Veri kapsamı ve uyarılar':'Data coverage & warnings')+(warningCount?' · '+warningCount:'');
  if(data?.sources?.unreadable)coverage.open=true;
  readingLayers?.update(data);
  if(current==='work'&&workView&&workDirty){workView.update();workDirty=false;}
  if(current==='quota'&&data?.has_snapshot&&!renderedViews.quota.has(data)){quotaView.update(data);renderedViews.quota.add(data);}
  if(current!=='overview')return;
  if(!data){chartCard.hidden=true;return;}
  if(renderedViews.overview.has(data))return;renderedViews.overview.add(data);
  timeCard.update(data,$('usage-totals'));
  if(!data?.has_snapshot){chartCard.hidden=true;return;}chartCard.hidden=false;
  const palette=getComputedStyle(document.body);const token=name=>palette.getPropertyValue('--ui-'+name).trim();
  const rows=(data.projects||[]).slice(0,6);chartEmpty.hidden=rows.length>0;chartNode.hidden=!rows.length;
  if(!rows.length)return;
  if(!chart){chart=init(chartNode,null,{renderer:'canvas'});chart.on('click',event=>{const row=lastData?.[event.dataIndex];if(!row)return;$('usage-project').value=row.id;$('usage-project').dispatchEvent(new Event('change',{bubbles:true}));show('sessions',true);});}
  lastData=rows;
  chart.setOption({animation:!matchMedia('(prefers-reduced-motion: reduce)').matches,aria:{enabled:true},animationDuration:620,animationDurationUpdate:420,animationEasing:'cubicOut',animationEasingUpdate:'cubicOut',grid:{left:4,right:56,top:18,bottom:12,containLabel:true},tooltip:{trigger:'axis',renderMode:'richText',axisPointer:{type:'shadow',shadowStyle:{color:token('highlight')}},backgroundColor:token('raised'),borderColor:token('border-strong'),textStyle:{color:token('text'),fontSize:12},valueFormatter:value=>Number(value).toLocaleString(tr?'tr-TR':'en-US')+' tokens'},xAxis:{type:'value',splitNumber:3,axisLabel:{hideOverlap:true,color:token('muted'),formatter:n=>n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?(n/1e3).toFixed(0)+'k':n},splitLine:{lineStyle:{color:token('border')}},axisLine:{show:false}},yAxis:{type:'category',inverse:true,data:rows.map(p=>p.name),axisLine:{show:false},axisTick:{show:false},axisLabel:{color:token('secondary'),width:Math.min(150,Math.max(64,chartNode.clientWidth*.3)),overflow:'truncate',fontSize:12}},series:[{id:'project-usage',type:'bar',barMaxWidth:18,animationDelay:at=>at*60,label:{show:true,position:'right',color:token('secondary'),fontSize:12,fontFamily:'Segoe UI',formatter:item=>item.value>=1e6?(item.value/1e6).toLocaleString(tr?'tr-TR':'en-US',{maximumFractionDigits:1})+'M':item.value>=1e3?Math.round(item.value/1e3).toLocaleString(tr?'tr-TR':'en-US')+'k':String(item.value)},data:rows.map((p,i)=>({name:p.id,value:p.total_tokens,itemStyle:{color:i===0?token('accent'):token('muted'),borderRadius:[0,4,4,0]}})),emphasis:{itemStyle:{color:token('text')}}}]});
}
new ResizeObserver(()=>{if(current==='overview'&&chart){chart.resize();chart.setOption({yAxis:{axisLabel:{width:Math.min(150,Math.max(64,chartNode.clientWidth*.3))}}});}}).observe(chartNode);
const palette=el('dialog','ws-palette');palette.setAttribute('aria-label',words.find);const search=el('input');search.type='search';search.placeholder=words.find;search.setAttribute('aria-label',words.find);const choices=el('div','ws-command-list');const close=el('button','quiet',words.close);close.addEventListener('click',()=>palette.close());palette.append(search,choices,close);document.body.append(palette);
function commands(){choices.replaceChildren();for(const [name,node] of routes){if(!words[name].toLocaleLowerCase().includes(search.value.toLocaleLowerCase()))continue;const button=el('button','ws-command');button.append(icon(node),el('span','',words[name]));button.addEventListener('click',()=>{palette.close();show(name,true);});choices.append(button);}if(!choices.childElementCount)choices.append(el('p','section-note',words.noMatch));}
search.addEventListener('input',commands);search.addEventListener('keydown',event=>{if(event.key==='ArrowDown'){event.preventDefault();choices.querySelector('button')?.focus();}if(event.key==='Enter'){event.preventDefault();choices.querySelector('button')?.click();}});
find.addEventListener('click',()=>{search.value='';commands();palette.showModal();search.focus();});
document.addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();if(!palette.open)find.click();else palette.close();}});
let saved;try{saved=sessionStorage.getItem('pler-screen');sessionStorage.removeItem('pler-screen');}catch{}show(routes.some(([id])=>id===saved)?saved:getView().screen);redraw();

// A working session browser, not another dashboard landing page.
document.body.classList.add('session-workbench');
const scope=document.querySelector('.usage-scope');const scopeDetails=el('details','wb-scope');scopeDetails.append(el('summary','',tr?'Bu kayıtların kapsamı':'About these records'));scope.before(scopeDetails);scopeDetails.append(scope);for(const note of [$('usage-session-scope'),$('usage-verdict-summary'),document.querySelector('[data-i18n=quality_filter_note]')])if(note)scopeDetails.append(note);
const bar=el('div','wb-filterbar');
const segments=new Map();
ui.subscribe(['filters'],state=>{for(const [id,control] of segments)control.setValue(state.filters[id==='usage-period'?'days':'agent']);});
function segmented(id,values){
 const group=el('div','wb-segmented');group.setAttribute('role','group');group.setAttribute('aria-label',$(id).previousElementSibling.textContent);group.dataset.select=id;
 const control=mountSegments(group,values,$(id).value,value=>{$(id).value=value;$(id).dispatchEvent(new Event('change',{bubbles:true}));});
 segments.set(id,control);return group;
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
 const fields=el('details','wb-record-fields');fields.append(el('summary','',tr?'Modeller ve tüm kayıt bilgileri':'Models and all record details'));dl.before(fields);fields.append(dl);
 for(const model of detail.querySelectorAll(':scope > .detail-model-title,:scope > .usage-rank'))fields.append(model);
 const provenance=el('details','wb-provenance');provenance.append(el('summary','',tr?'Veri kapsamı ve yöntem':'Data coverage and method'));
 for(const note of detail.querySelectorAll(':scope > .section-note,:scope > .session-detail-intro'))provenance.append(note);
 detail.append(provenance);
 if(session){
  const namedWork=usageState.data?.work_items?.items.find(w=>w.session_ids.includes(session.id));
  if(!session.title&&namedWork)$('usage-session-title').textContent=namedWork.title;
  const identity=el('div','wb-session-identity');
  identity.append(el('span','',session.project));
  identity.append(el('strong','',session.agent==='codex'?'Codex':'Claude Code'),el('span','',usageDate(session.started)+' → '+usageDate(session.ended)));
  detail.prepend(identity);
  const metrics=mountSessionUsage({session,tr});identity.after(metrics);
  const titleExplanation=titleStatus(session,tr);if(titleExplanation)metrics.after(titleExplanation);
  if(['unverified','conflict'].includes(session.identity_state)){
   const warning=el('div','section-note wb-identity-warning');warning.append(el('p','',tr?'Bu dosyanın önceki oturumla eşleşmesi doğrulanamadı. Kayıtlı ayarları inceleyerek elle yeniden bağlayabilirsin.':'This file could not be verified as the previous session. Review saved settings to reconnect them manually.'));
   const reconnect=el('button','secondary',tr?'Kayıtlı ayarları yeniden bağla':'Reconnect saved settings');reconnect.type='button';reconnect.addEventListener('click',()=>{inspector.close();reconnectionUI?.open({target:session.id});});warning.append(reconnect);metrics.after(warning);
  }
  const work=$('usage-session-work-items');if(work)fields.before(work);
  const verdict=detail.querySelector('.verdict-dialog');if(verdict)fields.before(verdict);
  if(linkingWork&&usageState.data?.work_items?.items.some(w=>w.id===linkingWork&&!w.session_ids.includes(session.id))){workState.sessionChoices[session.id]=linkingWork;workState.sessionForms[session.id].open=true;const editor=$('usage-session-work-editor');if(editor)editor.open=true;renderSessionWorkItems();}
 }
}
budgetUI?.open(session,detail);
$('usage-session-title').title=$('usage-session-title').textContent;
show('sessions');
const previous=document.activeElement;if(!inspector.open)inspector.show();document.body.classList.add('inspector-open');syncRows();if(previous?.closest('#usage-sessions'))previous.focus({preventScroll:true});inspector.scrollTop=0;detail.scrollTop=0;
};
inspector.addEventListener('close',()=>{if(inspector.open)return;budgetUI?.close();document.body.classList.remove('inspector-open');syncRows();});
list.addEventListener('click',event=>{const row=event.target.closest('tr');if(!row||event.target.closest('button,a,input,select'))return;row.querySelector('button')?.click();});
list.addEventListener('keydown',event=>{if(!['ArrowDown','ArrowUp'].includes(event.key)||event.target.closest('select,input'))return;const rows=[...list.children],index=rows.indexOf(event.target.closest('tr'));const target=rows[index+(event.key==='ArrowDown'?1:-1)];if(!target)return;event.preventDefault();const b=target.querySelector('button');b.click();b.focus({preventScroll:true});target.scrollIntoView({block:'nearest'});});
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
ui.subscribe(['filters','data'],updateReportScope);updateReportScope();
const linkBanner=el('div','wb-link-banner');linkBanner.hidden=true;
const linkTitle=el('strong');const finishLink=el('button','secondary',tr?'İşe dön':'Back to work');
finishLink.addEventListener('click',()=>{linkingWork=null;linkBanner.hidden=true;show('work',true);});linkBanner.append(linkTitle,finishLink);pages.sessions.prepend(linkBanner);
const addSessions=el('button','primary wb-add-sessions',tr?'Oturum ekle →':'Add sessions →');addSessions.type='button';
addSessions.addEventListener('click',()=>{const work=selectedWork();if(!work)return;linkingWork=work.id;linkTitle.textContent=(tr?'Oturum eklenecek iş: ':'Adding sessions to: ')+work.title;linkBanner.hidden=false;show('sessions',true);$('usage-session-search').focus();});
$('usage-work-no-members').after(addSessions);
const workMembers=el('section','wb-work-sessions');workMembers.append(el('h3','',tr?'Bağlı oturumlar':'Linked sessions'),$('usage-work-counts'),$('usage-work-usage'),$('usage-work-quality'),$('usage-work-members'),$('usage-work-more'),$('usage-work-no-members'),addSessions);
$('usage-work-rename-form').after(workMembers);
workView=mountWork({tr});
tour=mountTour({tr,show});
redraw();
// A compact, actionable badge keeps quota warnings discoverable in other sections.
function syncQuotaBadge(){const box=$('usage-quota-alert'),count=box.hidden?0:box.children.length;navigation.setWarning(count,box.textContent);}
ui.subscribe(['quota'],syncQuotaBadge);syncQuotaBadge();
installFeedback();

choices.addEventListener('keydown',event=>{const buttons=[...choices.querySelectorAll('button')],index=buttons.indexOf(document.activeElement);if(!buttons.length)return;if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?buttons.length-1:(index+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length;buttons[next].focus();}});
const commandHint=el('div','ws-command-hint');commandHint.append(el('kbd','','↑ ↓'),el('span','',tr?'Gezin':'Navigate'),el('kbd','','Enter'),el('span','',tr?'Aç':'Open'),el('kbd','','Esc'),el('span','',tr?'Kapat':'Close'));palette.append(commandHint);

// The placeholder is structural, never invented usage. Retain old data during refresh.
const skeleton=el('section','ws-skeleton');skeleton.setAttribute('aria-hidden','true');skeleton.hidden=true;skeleton.append(el('p','',tr?'Yerel kayıtlar okunuyor…':'Reading local records…'));
for(let i=0;i<5;i++){const row=el('div','ws-skeleton-row');row.append(el('span'),el('span'),el('span'));skeleton.append(row);}
content.before(skeleton);
// Keep the native indeterminate progress semantics, but draw one compositor-driven track.
const loadingTrack=el('div','ws-loading-track');loadingTrack.setAttribute('aria-hidden','true');loadingTrack.hidden=true;loadingTrack.append(el('span'));$('usage-progress').after(loadingTrack);
function syncLoading(){const state=ui.get(),data=state.data,busy=state.loading||data?.state==='scanning',initial=busy&&!data?.has_snapshot;skeleton.hidden=!initial;loadingTrack.hidden=!busy;$('usage-progress').hidden=!busy;document.body.classList.toggle('is-refreshing',Boolean(busy&&data?.has_snapshot));document.body.dataset.hasSessions=String(Boolean(data?.totals.sessions));}
syncLoading();
for(const target of [$('usage-empty'),$('usage-search-empty')]){const glyph=el('div','ws-empty-glyph');glyph.append(icon(ListFilter),el('kbd','','Ctrl K'));target.prepend(glyph);}
$('usage-session-search').addEventListener('keydown',event=>{if(event.key==='Escape'&&$('usage-session-search').value){event.preventDefault();$('usage-search-clear').click();}});

const workScope=el('details','wb-work-scope');workScope.append(el('summary','',tr?'İş kapsamı ve gizlilik':'Work scope and privacy'));
for(const key of ['work_scope','work_api_note','work_privacy']){const paragraph=$('usage-work-items').querySelector(':scope > [data-i18n='+key+']');if(paragraph)workScope.append(paragraph);}
$('usage-work-items').append(workScope);
const workGlyph=el('div','ws-empty-glyph');workGlyph.append(icon(Layers));$('usage-work-empty').before(workGlyph);
ui.subscribe(['work'],()=>{workGlyph.hidden=$('usage-work-empty').hidden;});workGlyph.hidden=$('usage-work-empty').hidden;

installViewPreferences();
firstUse=mountFirstUse({tr,settings:pages.settings,show,tour:()=>tour});
budgetUI=mountBudgets({tr,settings:pages.settings,before:content});
mountSourceFolders({tr,settings:pages.settings,show,reveal:revealSetting});
reconnectionUI=mountReconnections({tr,settings:pages.settings,show,reveal:revealSetting});
diagnosticUI=mountDiagnostics({tr,settings:pages.settings,show,reveal:revealSetting});
mountHistoryRecovery({tr,settings:pages.settings,show,reveal:revealSetting});
settingsUI=mountSettings({tr,page:pages.settings,show});
mountSearchRecovery({tr});
readingLayers=mountReadingLayers({tr,pages,show});
ui.subscribe(['screen'],state=>{if(state.screen!==current)show(state.screen);});
ui.subscribe(['data','loading','readError','filters','restoring','screen','work'],(_state,topic)=>{if(topic==='work')workDirty=true;redraw();syncLoading();});
redraw();
// Drawn menus replace the browser's own list for the main dropdowns; the selects stay the source of truth.
mountSelectMenus();
