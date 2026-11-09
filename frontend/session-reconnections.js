// Explicit, previewed annotation transfer. The server owns conflicts and recovery.
export function mountReconnections({tr,settings,show,reveal}){
 const text=(local,en)=>tr?local:en;
 const el=(tag,cls,value)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(value)node.textContent=value;return node;};
 const number=value=>new Intl.NumberFormat(tr?'tr-TR':'en-US',{maximumFractionDigits:4}).format(value);
 const label=row=>row?.title||row?.works?.[0]?.title||'#'+(row?.id||'').slice(0,8);
 const verdict=value=>value==='useful'?text('Yararlı','Useful'):value==='wasted'?text('Boşa','Wasted'):text('Yok','None');
 const budget=value=>value?number(value.limit)+' '+(value.metric==='tokens'?'token':'USD · '+t('stat_api')):text('Yok','None');
 const reasons={unavailable:text('Önce kayıtların başarıyla okunmasını bekle.','Wait for a successful record read first.'),
  unreadable:text('Kayıtlı ayarlar veya geri alma kaydı okunamadı. Dosyalar korunuyor; aktarım kapalı.','Saved settings or recovery data could not be read. Files are preserved; transfer is disabled.'),
  recovery_conflict:text('Kesilen aktarım sırasında ayarlar dışarıdan değişmiş. Dosyalar korunuyor; mevcut özel yedeğini sakla.','Settings changed externally during an interrupted transfer. Files are preserved; keep your private backup.'),
  source_live:text('Eski kayıt hâlâ canlı görünüyor. Kaynakları kontrol edip kayıtları yeniden oku.','The old record still appears live. Check sources and read records again.'),
  target_missing:text('Hedef canlı kayıt bulunamadı. Kayıtları yeniden oku ve tekrar seç.','The live target record was not found. Read records again and select it again.'),
  agent_mismatch:text('Aynı araca ait canlı bir oturum seç.','Choose a live session from the same agent.'),
  missing:text('Bu eski koda bağlı taşınacak ayar kalmadı. Listeyi yenile.','No annotations remain under that old code. Reload the list.'),
  conflict:text('Ayarlar veya kayıt görünümü değişti. Yeniden önizleyip onayla.','Settings or the record snapshot changed. Preview again before confirming.'),
  changed:text('Aktarılan bağlantı veya ayarlar sonradan değişmiş. Güvenli geri alma kapalı; sonraki düzenlemeler korunuyor.','Transferred links or settings were edited afterwards. Undo is disabled to preserve later edits.'),
  no_undo:text('Geri alınabilecek son aktarım yok.','No last transfer to undo.'),
  demo:text('Demo gerçek kayıt bağlantılarını değiştirmez.','The demo does not change real record annotations.'),
  verdict_choice:text('Hangi değerlendirmenin kalacağını seç.','Choose which review to keep.'),budget_choice:text('Hangi uyarı eşiğinin kalacağını seç.','Choose which threshold to keep.'),
  invalid:text('Eski kayıt ve canlı hedef seçimini kontrol et.','Check the old record and live target selection.')};
 let state=null,busy=false,preview=null,previewTicket=0;
 const selected={sources:null,targets:null},pages={sources:0,targets:0},tickets={sources:0,targets:0},timers={};
 const section=el('section','reconnection-panel usage-panel');section.id='session-reconnections';
 const heading=el('h2','',text('Taşınan oturumun ayarlarını yeniden bağla','Reconnect a moved session’s settings'));heading.id='reconnect-title';heading.tabIndex=-1;section.setAttribute('aria-labelledby',heading.id);
 section.append(heading,el('p','section-note',text('Eski kaydın bulunamıyor veya yalnız saklanan geçmişte mi? İş bağlantılarını, değerlendirmeni ve uyarı eşiğini seçtiğin canlı oturuma taşı. Önce yeni kayıt klasörünü ekle ve kayıtları yenile.',
  'Old record missing or only in retained history? Move its work links, your review and alert threshold to a live session you choose. Add the new log folder and refresh records first.')));
 const message=el('p','reconnection-status');message.setAttribute('role','status');message.setAttribute('aria-live','polite');
 const retry=el('button','secondary',text('Listeyi yenile','Reload list'));retry.type='button';retry.dataset.reconnectAction='reload';
 section.append(message,retry);
 const fields=el('fieldset','reconnection-fields'),columns=el('div','reconnection-columns'),lists={};
 fields.append(el('legend','sr-only',text('Eski ve yeni kayıt seçimi','Old and new record selection')),columns);
 for(const kind of ['sources','targets']){
  const column=el('div','reconnection-column'),name=kind==='sources'?text('Eski kayıtlı ayarlar','Old saved settings'):text('Yeni canlı oturum','New live session');
  const searchLabel=el('label','',name),input=el('input');input.type='search';input.maxLength=160;input.autocomplete='off';input.id='reconnect-search-'+kind;
  input.placeholder=kind==='sources'?text('İş adı veya eski kod','Work name or old code'):text('Oturum adı, proje veya kod','Session name, project or code');searchLabel.append(input);
  const choice=el('p','reconnection-selection',text('Seçilmedi','Not selected')),rows=el('div','reconnection-rows');rows.setAttribute('role','group');rows.setAttribute('aria-label',name);
  const paging=el('div','reconnection-paging'),previous=el('button','quiet',text('Önceki','Previous')),next=el('button','quiet',text('Sonraki','Next')),count=el('span','');
  for(const button of [previous,next])button.type='button';
  previous.addEventListener('click',()=>{pages[kind]=Math.max(0,pages[kind]-20);loadRows(kind);});next.addEventListener('click',()=>{pages[kind]+=20;loadRows(kind);});
  input.addEventListener('input',()=>{clearTimeout(timers[kind]);pages[kind]=0;invalidate();timers[kind]=setTimeout(()=>loadRows(kind),200);});
  paging.append(previous,count,next);column.append(searchLabel,choice,rows,paging);columns.append(column);lists[kind]={input,choice,rows,previous,next,count};
 }
 const inspect=el('button','primary',text('Aktarımı önizle','Preview transfer'));inspect.type='button';inspect.dataset.reconnectAction='preview';fields.append(inspect);
 const previewBox=el('div','reconnection-preview');previewBox.hidden=true;fields.append(previewBox);section.append(fields);
 const history=el('div','reconnection-history');section.append(history);
 section.append(el('p','section-note reconnection-privacy',text('Bu işlem oturum kullanımını birleştirmez, dosya kimliğini doğrulamaz ve ajan kayıtlarını değiştirmez. Son aktarımı geri almak için özel yerel bir kopya tutulur; bu kopya normal rapora veya özel yedeğe eklenmez. Yedekler sonuçtaki iş, değerlendirme ve kullanım uyarısı ayarlarını içerir.',
  'This does not combine session usage, prove file identity or change agent records. A private local copy supports undoing the last transfer; it is absent from regular reports and private backups. Backups include the resulting work, review and usage alert settings.')));
 settings.append(section);
 function fail(error){message.textContent=reasons[error?.reason]||text('Bağlantı kurulamadı. Mevcut ayarlar korundu; listeyi yenile.','Could not connect. Existing settings were kept; reload the list.');message.dataset.state='error';}
 function sync(){
  fields.disabled=busy||!state?.readable||state.demo||!state.ready;retry.disabled=busy;
  inspect.disabled=busy||!selected.sources||!selected.targets||!state?.ready;
  const confirm=previewBox.querySelector('[data-reconnect-action=transfer]');
  if(confirm)confirm.disabled=busy||!previewBox.querySelector('.reconnect-consent')?.checked||[...previewBox.querySelectorAll('[data-choice]')].some(box=>!box.querySelector('input:checked'));
  const undo=history.querySelector('[data-reconnect-action=undo]'),clear=history.querySelector('[data-reconnect-action=clear]');
  if(undo)undo.disabled=busy||!state?.readable||!state.can_undo;
  if(clear)clear.disabled=busy||!state?.readable||state.demo;
 }
 function invalidate(){preview=null;previewTicket++;previewBox.replaceChildren();previewBox.hidden=true;sync();}
 async function loadRows(kind){
  const ticket=++tickets[kind],list=lists[kind];
  const query=new URLSearchParams({kind,q:list.input.value,offset:String(pages[kind]),lang:tr?'tr':'en'});
  if(kind==='targets'&&selected.sources)query.set('source',selected.sources.id);
  list.rows.setAttribute('aria-busy','true');
  try{
   const data=await api('/api/usage/reconnections?'+query);if(ticket!==tickets[kind])return;
   state=data;list.rows.replaceChildren();
   if(!data.readable||data.demo){fail({reason:data.demo?'demo':data.reason});renderHistory(data);return;}
   for(const row of data.items){
    const button=el('button','reconnection-row');button.type='button';button.dataset.reconnectKind=kind;button.dataset.id=row.id;button.setAttribute('aria-pressed',String(selected[kind]?.id===row.id));
    button.append(el('strong','',label(row)),el('span','',[(row.agent==='claude-code'?'Claude Code':row.agent==='codex'?'Codex':null),row.project,'#'+row.id.slice(0,8)].filter(Boolean).join(' · ')));
    if(kind==='sources')button.append(el('small','',text(row.works.length+' iş · değerlendirme: '+verdict(row.verdict)+' · eşik: '+budget(row.budget),row.works.length+' work items · review: '+verdict(row.verdict)+' · threshold: '+budget(row.budget))));
    else button.append(el('small','',number(row.total_tokens)+' token'+(row.started?' · '+new Date(row.started).toLocaleString(tr?'tr-TR':'en-US'):'')));
    button.addEventListener('click',()=>{selected[kind]=row;list.choice.textContent=label(row)+' · #'+row.id.slice(0,8);invalidate();loadRows(kind);if(kind==='sources'){pages.targets=0;loadRows('targets');}});list.rows.append(button);
   }
   if(!data.items.length)list.rows.append(el('p','section-note',kind==='sources'?text('Bu aramada taşınacak eski ayar bulunamadı. Yalnız canlı kaydı bulunmayan ayarlar listelenir.','No old settings match this search. Only settings without a live source are listed.'):text('Canlı hedef bulunamadı. Filtreyi değiştir veya yeni kayıt klasörünü ekle.','No live target found. Change the search or add the new log folder.')));
   list.count.textContent=data.total?number(data.offset+1)+'–'+number(Math.min(data.offset+20,data.total))+' / '+number(data.total):'0';
   list.previous.disabled=data.offset===0;list.next.disabled=data.offset+20>=data.total;
   renderHistory(data);
  }catch(error){if(ticket===tickets[kind])fail(error);}finally{if(ticket===tickets[kind]){list.rows.setAttribute('aria-busy','false');sync();}}
 }
 function renderHistory(data){
  history.replaceChildren();if(!data.latest)return;
  const last=data.latest;history.append(el('strong','',last.kind==='undo'?text('Son aktarım geri alındı','Last transfer was undone'):text('Son aktarım','Last transfer')),
   el('p','section-note','#'+last.source.slice(0,8)+' → #'+last.target.slice(0,8)+' · '+new Date(last.at*1000).toLocaleString(tr?'tr-TR':'en-US')));
  const undo=el('button','secondary',text('Son aktarımı geri al','Undo last transfer'));undo.type='button';undo.dataset.reconnectAction='undo';undo.disabled=busy||!data.can_undo;undo.addEventListener('click',()=>mutate({action:'undo',expected:state.revision}));
  const clear=el('button','quiet',text('Geri alma kaydını temizle','Clear undo copy'));clear.type='button';clear.dataset.reconnectAction='clear';clear.disabled=busy;clear.addEventListener('click',()=>mutate({action:'clear',expected:state.revision}));
  history.append(undo,clear);
  if(last.kind==='transfer'&&!data.can_undo)history.append(el('p','section-note',reasons.changed));
 }
 function choice(kind,local,en,oldValue,newValue){
  const box=el('fieldset','reconnection-choice');box.dataset.choice=kind;box.append(el('legend','',text(local,en)));
  for(const [value,caption] of [['source',text('Eski ayarı koru: ','Keep old setting: ')+oldValue],['target',text('Hedeftekini koru: ','Keep target setting: ')+newValue]]){
   const line=el('label','');const radio=el('input');radio.type='radio';radio.name='reconnect-'+kind;radio.value=value;radio.addEventListener('change',sync);line.append(radio,el('span','',caption));box.append(line);
  }
  previewBox.append(box);
 }
 inspect.addEventListener('click',async()=>{
  if(busy||!selected.sources||!selected.targets)return;busy=true;sync();const ticket=++previewTicket;
  try{
   const value=await post('/api/usage/reconnections',{action:'preview',source:selected.sources.id,target:selected.targets.id});if(ticket!==previewTicket)return;
   preview=value;previewBox.replaceChildren();previewBox.hidden=false;
   previewBox.append(el('h3','',text('Taşınacak ayarlar','Settings to transfer')),el('p','',label(value.source)+' · #'+value.source.id.slice(0,8)+' → '+label(value.target)+' · #'+value.target.id.slice(0,8)),
    el('p','section-note',text(value.source.works.length+' iş bağlantısı hedefe taşınır. Hedefin diğer iş bağlantıları korunur; aynı işte tek kez sayılır.',value.source.works.length+' work links move to the target. Its other work links remain; each work counts it once.')));
   const names=el('ul','reconnection-work-list');for(const work of value.source.works)names.append(el('li','',work.title));previewBox.append(names);
   previewBox.append(el('p','section-note',text('Eski değerlendirme: ','Old review: ')+verdict(value.source.verdict)+' · '+text('Eski eşik: ','Old threshold: ')+budget(value.source.budget)));
   previewBox.append(el('p','section-note',text('Hedefteki değerlendirme: ','Target review: ')+verdict(value.target.verdict)+' · '+text('Hedefteki eşik: ','Target threshold: ')+budget(value.target.budget)));
   if(value.verdict_conflict)choice('verdict','Hangi değerlendirme kalsın?','Which review should remain?',verdict(value.source.verdict),verdict(value.target.verdict));
   if(value.budget_conflict)choice('budget','Hangi uyarı eşiği kalsın?','Which threshold should remain?',budget(value.source.budget),budget(value.target.budget));
   previewBox.append(el('p','section-note',text('Uyarı geçmişi seçilen eşikle birlikte korunur. Kayıtlı kullanım bu işlemle birleştirilmez.','Notification history stays with the chosen threshold. Recorded usage is not combined by this action.')));
   previewBox.append(el('p','section-note',text('Hedefin kullanım veya kaynak bilgisi eksikse izleme duraklayabilir. Son kayıt okuma: ','Monitoring can remain paused if the target has incomplete usage or source information. Records last read: ')+new Date(value.snapshot_at).toLocaleString(tr?'tr-TR':'en-US')));
   const consent=el('label','reconnection-consent');const check=el('input','reconnect-consent');check.type='checkbox';check.addEventListener('change',sync);consent.append(check,el('span','',text('Ayarları bu hedef oturuma taşımak istiyorum.','I want to move these settings to this target session.')));
   const save=el('button','primary',text('Ayarları yeniden bağla','Reconnect settings'));save.type='button';save.dataset.reconnectAction='transfer';save.addEventListener('click',()=>{
    if(!preview||save.disabled)return;
    mutate({action:'transfer',source:preview.source.id,target:preview.target.id,expected:preview.expected,confirmed:true,
     verdict_choice:previewBox.querySelector('input[name=reconnect-verdict]:checked')?.value||'',budget_choice:previewBox.querySelector('input[name=reconnect-budget]:checked')?.value||''});
   });previewBox.append(consent,save);previewBox.tabIndex=-1;previewBox.focus({preventScroll:true});previewBox.scrollIntoView({block:'nearest',behavior:'instant'});
  }catch(error){fail(error);}finally{busy=false;sync();}
 });
 async function mutate(body){
  if(busy)return;busy=true;sync();
  try{
   state=await post('/api/usage/reconnections',body);
   invalidate();selected.sources=null;lists.sources.choice.textContent=text('Seçilmedi','Not selected');
   message.textContent=body.action==='undo'?text('Aktarım geri alındı. Sonraki bağımsız düzenlemeler korundu.','Transfer undone. Later independent edits were kept.'):body.action==='clear'?text('Yalnız geri alma kopyası temizlendi. Ayarlar yerinde.','Only the undo copy was cleared. Settings are unchanged.'):text('İş bağlantıları ve seçtiğin ayarlar hedef oturuma taşındı.','Work links and your chosen settings were moved to the target session.');message.dataset.state='ready';
   await loadUsage();await Promise.all([loadRows('sources'),loadRows('targets')]);
  }catch(error){invalidate();fail(error);try{await loadUsage();}catch{}await loadRows('sources');}finally{busy=false;sync();}
 }
 retry.addEventListener('click',()=>{invalidate();loadRows('sources');loadRows('targets');});
 function open(selection={}){
  if(reveal)reveal(section);else show('settings',true);fields.disabled=false;
  if(selection.source){lists.sources.input.value=selection.source;pages.sources=0;}
  if(selection.target){lists.targets.input.value=selection.target;pages.targets=0;}
  invalidate();loadRows('sources');loadRows('targets');heading.focus({preventScroll:true});section.scrollIntoView({block:'start',behavior:'instant'});
 }
 document.addEventListener('pler-screen-change',event=>{if(event.detail==='settings'){loadRows('sources');loadRows('targets');}});
 document.addEventListener('pler-reconnect-record',event=>open(event.detail||{}));
 if(window.plerUI?.get().screen==='settings'){loadRows('sources');loadRows('targets');}
 sync();return {open};
}
