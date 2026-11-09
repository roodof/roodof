export function titleStatus(session,tr){
 const info=session.title_info;
 if(!info||info.state==='available')return null;
 const detail=document.createElement('details');detail.className='session-title-status';detail.dataset.code=info.code;
 const summary=document.createElement('summary');summary.textContent=info.title;
 const note=document.createElement('p');note.className='section-note';note.textContent=session.title?
  (tr?'Gösterilen başlığın en son adlandırma olduğu doğrulanamadı.':'The displayed title could not be verified as the latest rename.'):
  (tr?'Oturum adı için iş veya proje adı kullanılıyor. Bu durum tek başına kullanım kaybı anlamına gelmez.':'A work or project name is used for this session. This alone does not mean usage records are missing.');
 const action=document.createElement('p');action.className='section-note';action.textContent=info.next;
 detail.append(summary,note,action);return detail;
}

export function mountDiagnostics({tr,settings,show,reveal}){
 const text=(local,en)=>tr?local:en;
 const el=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value!=null)n.textContent=value;return n;};
 const stages={logs:text('Kayıt kaynakları','Log sources'),titles:text('Oturum başlıkları','Session titles'),history:text('Saklanan geçmiş','Retained history'),git:text('Git gözlemi','Git observation'),settings:text('Kayıtlı tercihler','Saved preferences'),summary:text('Görünüm hazırlama','Report preparation')};
 const units={sources:text('kaynak','sources'),sessions:text('oturum','sessions'),repositories:text('depo','repositories'),operations:text('işlem','operations')};
 const panel=el('section','diagnostics usage-panel');panel.id='diagnostics';
 const head=el('div','diagnostics-heading'),heading=el('h2','',text('Okuma durumu ve tanılama','Read status & diagnostics'));heading.tabIndex=-1;
 const download=el('button','secondary',text('Tanılama dosyasını indir','Download diagnostics'));download.type='button';download.id='diagnostics-download';head.append(heading,download);panel.append(head);
 panel.append(el('p','section-note',text('Tüm seçili kaynakları kapsar; ekran filtrelerinden bağımsızdır. Başlık yokluğu ile kullanım okuma sorunları ayrı gösterilir.','Covers all selected sources, independently of screen filters. Missing titles are separate from usage-read issues.')));
 const state=el('p','section-note diagnostics-state');state.id='diagnostics-state';state.setAttribute('role','status');
 const groups=el('div','diagnostics-groups');panel.append(state,groups);
 const actions=el('div','diagnostics-actions'),retry=el('button','quiet',text('Kayıtları yenile','Refresh records')),sources=el('button','quiet',text('Kayıt klasörlerini aç','Open log folders'));
 retry.type=sources.type='button';retry.addEventListener('click',()=>document.getElementById('usage-refresh').click());sources.addEventListener('click',()=>document.dispatchEvent(new CustomEvent('pler-manage-sources')));actions.append(retry,sources);panel.append(actions);
 panel.append(el('p','section-note diagnostics-privacy',text('İndirilen dosyada yalnız sürüm, okuma zamanı, sabit kodlar ve sayılar bulunur. Konuşma, başlık, kimlik, özel yol ve erişim anahtarı bulunmaz. Dosya otomatik gönderilmez. Özel geçmiş yedeğinden farklıdır.','The download contains only version, read time, fixed codes and counts. It contains no conversations, titles, identifiers, private paths or access keys. It is not sent automatically and is separate from a private history backup.')));
 const message=el('p','section-note');message.id='diagnostics-message';message.setAttribute('role','status');panel.append(message);settings.append(panel);
 let previous='',busy=false;
 function update(data){
  const value=data?.diagnostics;
  download.disabled=busy||usageState.stopped;retry.disabled=usageState.loading||data?.state==='scanning'||usageState.stopped;sources.disabled=usageState.stopped;
  if(!value){state.textContent=text('Henüz tanılama bilgisi alınmadı.','No diagnostic information yet.');return;}
  const signature=JSON.stringify(value);if(signature===previous)return;previous=signature;
  const opened=new Map([...groups.querySelectorAll('details')].map(n=>[n.dataset.stage,n.open]));
  const focused=document.activeElement?.closest('.diagnostics-group')?.dataset.stage;
  groups.replaceChildren();
  for(const [stage,label] of Object.entries(stages)){
   const items=value.items.filter(item=>item.stage===stage);if(!items.length)continue;
   const group=el('details','diagnostics-group');group.dataset.stage=stage;
   group.open=opened.has(stage)?opened.get(stage):items.some(item=>item.level==='error'||stage==='logs');
   const summary=el('summary',''),count=el('span','diagnostics-group-count',String(items.length));summary.append(el('span','',label),count);group.append(summary);
   const list=el('ul','diagnostics-items');
   for(const item of items){
    const row=el('li','diagnostic-item');row.dataset.code=item.code;row.dataset.level=item.level;
    const line=el('div','diagnostic-line');line.append(el('strong','',item.title),el('span','diagnostic-count',item.count+' '+(units[item.unit]||'')));
    row.append(line,el('p','section-note',item.next),el('code','diagnostic-code',item.code));list.append(row);
   }
   group.append(list);groups.append(group);
  }
  const at=value.scanned_at?new Date(value.scanned_at).toLocaleString(tr?'tr-TR':'en-GB'):null;
  state.textContent=value.snapshot==='previous'?text('Son deneme tamamlanmadı veya sürüyor. Kaynak sayıları önceki başarılı okumaya ait: ','The latest attempt did not finish or is still running. Source counts come from the previous successful read: ')+at:
   !value.has_snapshot?text('Henüz başarılı bir okuma yok. Aşağıda son denemenin bilinen durumu gösterilir.','No successful read yet. Known status from the latest attempt is shown below.'):
   value.items.length?text('Son başarılı okuma: ','Last successful read: ')+at:
   text('Bu okumada bildirilen bir sorun yok. Bu, hesabın bütün geçmişinin kapsandığı anlamına gelmez.','No issue was reported in this read. This does not prove complete account-history coverage.');
  if(focused)groups.querySelector(`[data-stage="${focused}"] > summary`)?.focus({preventScroll:true});
 }
 download.addEventListener('click',async()=>{
  if(busy)return;busy=true;download.disabled=true;message.textContent='';
  try{
   const value=await api('/api/usage/diagnostics?lang='+(tr?'tr':'en'));
   const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)+'\n'],{type:'application/json'}));
   const link=el('a');link.href=url;link.download='pler-diagnostics-'+value.version+'.json';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
   message.textContent=text('Tanılama dosyası hazırlandı. Otomatik gönderilmedi.','Diagnostic file prepared. It was not sent automatically.');
  }catch{message.textContent=text('Tanılama indirilemedi. PLER bağlantısını kontrol edip yeniden dene.','Could not download diagnostics. Check the PLER connection and retry.');}
  finally{busy=false;download.disabled=usageState.stopped;}
 });
 document.addEventListener('pler-open-diagnostics',()=>{if(reveal)reveal(panel);else show('settings',true);heading.focus({preventScroll:true});panel.scrollIntoView({block:'start',behavior:'instant'});});
 const shortcut=el('button','quiet',text('Sorunu incele','Inspect read issues'));shortcut.type='button';shortcut.id='diagnostics-shortcut';shortcut.hidden=true;shortcut.addEventListener('click',()=>document.dispatchEvent(new CustomEvent('pler-open-diagnostics')));document.querySelector('.workspace-head').after(shortcut);
 return {update:data=>{shortcut.hidden=!(data?.state==='error'||data?.sources?.unreadable);update(data);}};
}
