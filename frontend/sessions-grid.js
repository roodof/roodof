import {enterRows} from './feedback.js';
import {TabulatorFull as Tabulator} from 'tabulator-tables';

// The controller filters and orders the complete snapshot, and owns every write.
// The grid renders that order without adding a second, page-local sort.
export function mountSessionsGrid({tr,list,inspector}) {
 const $=id=>document.getElementById(id);
 const text=(en,turkish)=>tr?turkish:en;
 const node=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value!=null)n.textContent=value;return n;};
 const legacy=list.closest('.table-scroll');
 const host=node('div','sessions-grid');host.id='sessions-grid';legacy.before(host);
 const tools=document.querySelector('.wb-list-tools');
 const options=node('details','grid-options');options.append(node('summary','',text('Customize view','Görünümü düzenle')));
 const menu=node('div','grid-column-menu');options.append(menu);
 document.querySelector('.session-controls').append(options);
 const footer=node('div','grid-footer');
 const count=$('usage-session-count');footer.append(count);
 const hint=node('span','grid-scroll-hint',text('Scroll sideways for the other columns →','Diğer sütunlar için yana kaydır →'));
 footer.append(hint);host.after(footer);tools.hidden=true;
 const activeId=()=>inspector.open&&typeof workState!=='undefined'?workState.openSession:null;
 const open=id=>{const before=document.activeElement;const session=usageState.data?.sessions.find(s=>s.id===id);if(session)openUsageSession(session);syncSelection();if(before?.closest('#sessions-grid'))before.focus({preventScroll:true});};
 const formatNum=n=>Number(n).toLocaleString(tr?'tr-TR':'en-US');
 const safeDate=v=>{if(!v)return text('Not recorded','Kaydedilmedi');const d=new Date(v);return Number.isFinite(d.getTime())?new Intl.DateTimeFormat(tr?'tr-TR':'en-GB',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}).format(d):text('Unknown','Bilinmiyor');};
 const filterAgent=value=>{$('usage-agent').value=value;$('usage-agent').dispatchEvent(new Event('change',{bubbles:true}));};
 const project=cell=>{
  const row=cell.getRow().getData(),wrap=node('div','grid-project'),label=node('div','grid-identity');
  const button=node('button','grid-project-name',row.workTitles[0]||row.project);button.type='button';
  button.title=text('Open session','Oturumu aç')+' · #'+row.id.slice(0,8);button.setAttribute('aria-label',button.textContent+' · '+row.agentName+' · '+safeDate(row.ended)+' · '+text('Open session','Oturumu aç'));
  button.addEventListener('click',e=>{e.stopPropagation();open(row.id);});
  const meta=node('div','grid-session-meta');
  const agent=node('button','grid-agent-filter '+(row.agent==='codex'?'is-codex':'is-claude'),row.agentName);agent.type='button';agent.title=text('Show only ','Yalnızca ')+row.agentName;
  agent.addEventListener('click',e=>{e.stopPropagation();filterAgent(row.agent);});
  const time=node('time','',safeDate(row.ended));if(row.ended)time.dateTime=row.ended;
  meta.append(agent,node('span','grid-meta-divider','·'),time);
  label.append(button,meta);
  if(row.workTitles.length)label.append(node('span','grid-project-path',row.project+(row.workTitles.length>1?' · +'+(row.workTitles.length-1)+' '+text('work','iş'):'')));
  wrap.append(label);return wrap;
 };
 const review=cell=>{
  const row=cell.getRow().getData(),select=node('select','grid-review');select.setAttribute('aria-label',text('Review session ','Oturumu değerlendir ')+row.id.slice(0,8));
  for(const [value,label] of [['',text('Not reviewed','Değerlendirilmedi')],['useful',text('Useful','İşe yaradı')],['wasted',text('Wasted','Boşa gitti')]]){const o=node('option','',label);o.value=value;select.append(o);}
  select.value=['useful','wasted'].includes(row.verdict)?row.verdict:'';select.disabled=usageState.stopped||usageState.data?.verdicts?.readable===false;
  select.addEventListener('change',async()=>{
   const desired=select.value||null;select.value=['useful','wasted'].includes(row.verdict)?row.verdict:'';select.disabled=true;
   await setVerdict(row.id,desired);
   const saved=usageState.data?.sessions.find(s=>s.id===row.id)?.verdict;
   if(select.isConnected){select.value=['useful','wasted'].includes(saved)?saved:'';select.disabled=usageState.stopped||usageState.data?.verdicts?.readable===false;}
   refresh();
  });return select;
 };
 const fields=[
  {title:text('Session · click to open','Oturum · açmak için tıkla'),field:'project',minWidth:260,widthGrow:3,formatter:project},
  {title:text('Recorded tokens','Kayıtlı token'),field:'tokens',width:133,hozAlign:'right',headerHozAlign:'right',formatter:cell=>node('span','grid-number',formatNum(cell.getValue()))},
  {title:text('Record status','Kayıt durumu'),field:'status',width:150,formatter:cell=>node('span','grid-status '+cell.getRow().getData().statusKind,cell.getValue())},
  {title:text('Review','Değerlendirme'),field:'verdict',width:178,visible:false,formatter:review},
  {title:text('Agent','Ajan'),field:'agent',width:112,visible:false,formatter:cell=>cell.getRow().getData().agentName},
  {title:text('Last active','Son etkinlik'),field:'ended',width:165,visible:false,formatter:cell=>safeDate(cell.getValue())},
  {title:text('Models','Modeller'),field:'models',width:225,minWidth:180,visible:true,formatter:'plaintext'},
  {title:text('Model calls','Model çağrıları'),field:'calls',width:140,visible:true,hozAlign:'right',formatter:cell=>cell.getValue()==null?text('Unknown','Bilinmiyor'):formatNum(cell.getValue())},
  {title:text('Session code','Oturum kodu'),field:'id',width:140,visible:false,formatter:cell=>node('code','grid-code',cell.getValue().slice(0,8))}
 ];
 let ready=false,signature='',lastWidth=0;
 const grid=new Tabulator(host,{
  height:470,layout:'fitColumns',rowHeight:64,index:'id',data:[],columns:fields.map(f=>({...f})),movableColumns:true,
  columnDefaults:{resizable:true,vertAlign:'middle',headerSort:false},placeholder:'',
  persistence:{columns:true},persistenceID:'pler-sessions-columns-v4',persistenceMode:'local',
  persistenceWriterFunc:(id,type,data)=>{try{if(type==='columns')localStorage.setItem(id+'-'+type,JSON.stringify(data.map(c=>({field:c.field,...(c.field!=='project'?{width:c.width}:{}),visible:c.visible}))));}catch{}},
  persistenceReaderFunc:(id,type)=>{try{
   const data=JSON.parse(localStorage.getItem(id+'-'+type));if(type!=='columns'||!Array.isArray(data))return false;
   return data.filter(c=>fields.some(f=>f.field===c.field)).map(c=>({field:c.field,...(c.field!=='project'&&Number.isFinite(c.width)&&c.width>=80&&c.width<=1000?{width:c.width}:{}),visible:c.field==='project'?true:c.visible!==false}));
  }catch{return false;}},
  rowFormatter:row=>{row.getElement().dataset.sessionId=row.getData().id;},renderVertical:'virtual'
 });
 function resize(){
  if(!ready||!host.offsetWidth)return;
  const room=innerHeight-host.getBoundingClientRect().top-62;grid.setHeight(Math.max(245,Math.min(760,room)));const changed=Math.abs(lastWidth-host.clientWidth)>2;lastWidth=host.clientWidth;grid.redraw(changed);
  requestAnimationFrame(()=>{const holder=host.querySelector('.tabulator-tableholder');hint.hidden=!holder||holder.scrollWidth<=holder.clientWidth+2;});
 }
 function syncSelection(){
  if(!ready)return;const selected=activeId(),visible=grid.getRows('active'),index=visible.findIndex(r=>r.getData().id===selected);
  const buttons=[...document.querySelectorAll('.wb-inspector-tools button')];
  if(buttons.length===2){buttons[0].disabled=index<=0;buttons[1].disabled=index<0||index>=visible.length-1;}
  const counter=document.querySelector('.wb-inspector-tools>span');if(counter)counter.textContent=index<0?'':`${index+1} / ${visible.length}`;
  for(const row of grid.getRows()){const yes=row.getData().id===selected;row.getElement().classList.toggle('grid-row-open',yes);row.getElement().setAttribute('aria-selected',String(yes));}
 }
 function refresh(){
  if(!ready)return;
  const sessions=filteredUsageSessions(),works=usageState.data?.work_items?.readable===true?usageState.data.work_items.items:[];
  const titles=new Map();for(const work of works)for(const id of work.session_ids){if(!titles.has(id))titles.set(id,[]);titles.get(id).push(work.title);}
  const data=sessions.slice(0,usageState.pageSize).map(s=>{
   let status=text('Recorded','Kayıtlı'),kind='neutral';
   if(sessionHasQualityLimits(s)){status=text('Partial records','Sınırlı kayıt');kind='limited';}
   else if(s.errors||s.aborted){status=text('Errors / stops','Hata / kesinti');kind='limited';}
   else if(s.checks?.test?.last==='failed'){status=text('Test failed','Test kaldı');kind='failed';}
   else if(s.checks?.test?.last==='passed'){status=text('Test passed','Test geçti');kind='passed';}
   return {id:s.id,project:s.project,agent:s.agent,agentName:s.agent==='codex'?'Codex':'Claude Code',ended:s.ended,tokens:s.total_tokens,verdict:s.verdict||'',status,statusKind:kind,models:s.models.map(m=>m.model==='unknown'?text('Unknown','Bilinmiyor'):m.model).join(', '),calls:s.calls_complete?s.calls:null,workTitles:titles.get(s.id)||[]};
  });
  count.textContent=sessions.length===data.length?text(`${formatNum(sessions.length)} sessions`,`${formatNum(sessions.length)} oturum`):text(`${formatNum(data.length)} of ${formatNum(sessions.length)} sessions`,`${formatNum(sessions.length)} oturumdan ${formatNum(data.length)} gösteriliyor`);
  const next=JSON.stringify(data);
  if(next!==signature){signature=next;grid.replaceData(data).then(()=>{syncSelection();resize();enterRows(grid.getRows('visible').map(r=>r.getElement()));});}else{syncSelection();resize();}
 }
 function renderMenu(){
  menu.replaceChildren(node('p','grid-menu-note',text('Drag column headings to reorder. Drag their edges to resize.','Sıralamak için sütun başlığını, genişletmek için kenarını sürükle.')));
  for(const field of fields){
   const label=node('label'),input=node('input');input.type='checkbox';input.checked=grid.getColumn(field.field)?.isVisible()??field.visible!==false;input.disabled=field.field==='project';
   input.addEventListener('change',()=>{const col=grid.getColumn(field.field);input.checked?col.show():col.hide();resize();});label.append(input,node('span','',field.title));menu.append(label);
  }
  const reset=node('button','grid-reset',text('Reset view','Görünümü sıfırla'));reset.type='button';reset.addEventListener('click',()=>{grid.setColumns(fields.map(f=>({...f})));renderMenu();resize();});menu.append(reset);
 }
 options.addEventListener('toggle',()=>{if(options.open&&ready)renderMenu();});
 document.addEventListener('click',event=>{if(options.open&&!options.contains(event.target))options.open=false;});
 grid.on('tableBuilt',()=>{ready=true;legacy.hidden=true;document.body.classList.add('tabulator-sessions');refresh();resize();});
 grid.on('rowClick',(event,row)=>{if(event.target.closest('button,select,input,a'))return;open(row.getData().id);row.getElement().querySelector('button')?.focus({preventScroll:true});});
 grid.on('columnResized',()=>{if(options.open)renderMenu();resize();});
 new MutationObserver(refresh).observe(list,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-pressed']});
 new MutationObserver(syncSelection).observe(inspector,{attributes:true,attributeFilter:['open']});
 const showSession=window.plerShowSession;window.plerShowSession=(...args)=>{showSession(...args);syncSelection();requestAnimationFrame(resize);};
 inspector.addEventListener('close',()=>requestAnimationFrame(resize));
 new ResizeObserver(resize).observe(host);
 window.addEventListener('resize',resize);
 host.addEventListener('keydown',event=>{
  if(!['ArrowUp','ArrowDown','Enter'].includes(event.key)||event.target.closest('select,input'))return;
  const visible=grid.getRows('active'),current=visible.findIndex(r=>r.getData().id===event.target.closest('.tabulator-row')?.dataset.sessionId);if(current<0)return;event.preventDefault();
  const row=visible[Math.max(0,Math.min(visible.length-1,current+(event.key==='ArrowDown'?1:event.key==='ArrowUp'?-1:0)))];open(row.getData().id);row.getElement().querySelector('button')?.focus({preventScroll:true});
 });
 const step=delta=>{const rows=grid.getRows('active'),i=rows.findIndex(r=>r.getData().id===activeId());if(i<0)return;const row=rows[Math.max(0,Math.min(rows.length-1,i+delta))];open(row.getData().id);row.scrollTo().catch(()=>{});};
 for(const [i,button] of [...document.querySelectorAll('.wb-inspector-tools button')].entries())button.addEventListener('click',event=>{event.stopImmediatePropagation();step(i===0?-1:1);},true);
 refresh();return grid;
}
