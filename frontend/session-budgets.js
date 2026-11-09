// Session controls and a filter-independent watch list. The backend owns observation/alert state.
export function mountBudgets({tr, settings, before}) {
 const text=(a,b)=>tr?a:b;
 const el=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value)n.textContent=value;return n;};
 const fmt=n=>new Intl.NumberFormat(tr?'tr-TR':'en-US',{maximumFractionDigits:4}).format(n);
 const title=row=>row.title||usageState.data?.sessions.find(s=>s.id===row.id)?.title||'#'+row.id.slice(0,6);
 const stateNames={checking:text('İlk okuma bekleniyor','Waiting for first read'),watching:text('İzleniyor','Watching'),
  partial:text('Kullanım veya fiyat eksik · eşik uyarısı bekletiliyor','Incomplete usage or pricing · threshold alerts paused'),
  archive:text('Yalnız canlı kayıtlar izlenebilir · saklanan geçmiş var','Live records required · retained history present'),
  missing:text('Oturum bulunamadı · kayıtları yenile','Session not found · refresh records'),
  read_error:text('Kaynak okunamadı · izleme durakladı','Source unreadable · monitoring paused'),
  stale:text('Son okuma güncel değil · izlemeyi kontrol et','Last check is stale · check monitoring'),
  read_limit:text('Kayıt okuma sınırını aşıyor · izleme durakladı','Record read limit reached · monitoring paused')};
 let data={items:[],readable:true}, current=null, panel=null, busy=false, loading=false, failed=false, stopped=false;
 const banner=el('section','budget-banner');banner.hidden=true;banner.setAttribute('aria-label',text('Bütçe uyarıları','Budget alerts'));before.before(banner);
 const watch=el('section','budget-watch usage-panel');watch.id='budget-watch';
 watch.append(el('h2','',text('Oturum bütçe uyarıları','Session budget alerts')),
  el('p','section-note',text('PLER açıkken, ekran filtrelerinden bağımsız izlenir. Oturum ayrıntısından bir eşik ekle. En fazla 20 oturum.',
  'Watched while PLER is open, independently of screen filters. Add a threshold in session details. Up to 20 sessions.')));
 const watchStatus=el('p','section-note');watchStatus.setAttribute('role','status');
 const watchRows=el('div','budget-watch-rows');watch.append(watchStatus,watchRows);
 watch.append(el('p','section-note',text('Windows bildirim ayarları veya Rahatsız Etmeyin bildirimi gizleyebilir. Uyarılar uygulamada da görünür. Bütçe tercihleri özel yedeğe dahildir.',
  'Windows notification settings or Do not disturb may hide alerts. Alerts also remain visible in the app. Budget preferences are included in private backups.')));
 settings.prepend(watch);
 function metricName(row){return row.metric==='tokens'?'token':text('USD · API fiyat karşılığı','USD · API price equivalent');}
 function amountText(row){return (row.amount==null?'—':fmt(row.amount))+' / '+fmt(row.limit)+' '+metricName(row);}
 function stateText(row){return row.state==='watching'&&row.level?text('%'+row.level+' eşiğine ulaşıldı',row.level+'% threshold reached'):stateNames[row.state]||stateNames.checking;}
 function readout(row, box){
  box.replaceChildren();box.dataset.level=String(row?.level||0);
  if(!row){box.append(el('strong','',text('Uyarı kapalı','Alert off')));return;}
  box.append(el('strong','budget-amount',amountText(row)),el('span','budget-state',stateText(row)));
  if(row.state==='watching'&&row.amount!=null){
   const meter=el('progress','budget-progress');meter.max=row.limit;meter.value=Math.min(row.limit,row.amount);meter.setAttribute('aria-label',text('Kayıtlı kullanım / uyarı eşiği','Recorded use / alert threshold'));box.append(meter);
  }
  if(row.checked_at){const at=new Date(row.checked_at);box.append(el('small','budget-checked',text('Son okuma: ','Last checked: ')+at.toLocaleTimeString(tr?'tr-TR':'en-US')));}
 }
 function render(){
  const focused=document.activeElement;
  const focusedWatch=focused?.closest('.budget-watch-row')?.dataset.budgetId;
  const focusedAction=focused?.classList.contains('budget-remove')?'budget-remove':'budget-watch-open';
  const focusedBanner=focused?.closest('.budget-banner-item')?.dataset.budgetId;
  watchStatus.textContent=failed?text('Uyarı durumu alınamadı. Bağlantı gelince yeniden okunacak.','Could not read alert status. Retrying when connected.'):
   !data.readable?text('Kaydedilmiş eşikler okunamadı. Dosya korunuyor; yeni kayıt yapılmadı.','Saved thresholds could not be read. The file is preserved; no changes were made.'):
   data.items.length?text(data.items.length+' oturum izleme listesinde',data.items.length+' sessions on the watch list'):text('Henüz uyarı eşiği yok.','No thresholds yet.');
  watchRows.replaceChildren();banner.replaceChildren();
  for(const row of data.items){
   const item=el('div','budget-watch-row');item.dataset.budgetId=row.id;
   const name=el('button','text-button budget-watch-open',title(row));name.type='button';name.addEventListener('click',()=>window.plerOpenBudgetSession(row.id));
   const summary=el('div','budget-readout');readout(row,summary);
   const remove=el('button','quiet budget-remove',text('Kapat','Turn off'));remove.type='button';remove.disabled=busy||failed||!data.readable;
   remove.setAttribute('aria-label',text('Uyarıyı kapat: ','Turn off alert: ')+title(row));remove.addEventListener('click',()=>change(row.id,null,null,row.revision,remove));
   item.append(name,summary,remove);
   if(['missing','archive'].includes(row.state)){
    const reconnect=el('button','secondary',text('Yeniden bağla','Reconnect'));reconnect.type='button';reconnect.addEventListener('click',()=>document.dispatchEvent(new CustomEvent('pler-reconnect-record',{detail:{source:row.id}})));item.append(reconnect);
   }
   watchRows.append(item);
   if(row.level||row.state!=='watching'){
    const alert=el('button','budget-banner-item');alert.type='button';alert.dataset.level=String(row.level||0);alert.dataset.budgetId=row.id;
    alert.textContent=title(row)+' · '+stateText(row)+' · '+amountText(row);alert.addEventListener('click',()=>window.plerOpenBudgetSession(row.id));banner.append(alert);
   }
  }
  banner.hidden=!banner.childElementCount;
  if(focusedWatch)watchRows.querySelector(`[data-budget-id="${focusedWatch}"] .${focusedAction}`)?.focus({preventScroll:true});
  if(focusedBanner)banner.querySelector(`[data-budget-id="${focusedBanner}"]`)?.focus({preventScroll:true});
  if(panel?.isConnected&&current){
   const row=data.items.find(r=>r.id===current.id);readout(row,panel.querySelector('.budget-readout'));
   panel.querySelector('.budget-existing').hidden=Boolean(row);
   const error=panel.querySelector('.budget-connection');error.hidden=!failed&&data.readable;
   error.textContent=failed?text('Bağlantı yok; kaydedilmemiş değişiklikler korunuyor.','No connection; your unsaved changes are kept.'):
    text('Eşik dosyası okunamadı; kaydetme kapalı.','Threshold file unreadable; saving is disabled.');
   panel.querySelector('fieldset').disabled=busy||failed||!data.readable;
   panel.querySelector('.budget-off').disabled=busy||!row||failed||!data.readable;
  }
 }
 async function load(){
  if(stopped||loading)return;loading=true;
  try{data=await api('/api/usage/budgets');failed=false;}catch{failed=true;}
  finally{loading=false;render();}
 }
 async function change(id,metric,limit,expected,control){
  if(busy)return;busy=true;control.disabled=true;
  const targetPanel=panel, message=targetPanel?.querySelector('.budget-message');
  try{
   const result=await post('/api/usage/budgets',{id,metric,limit,expected});
   if(!result.ok)throw new Error(result.reason);
   await load();
   if(targetPanel?.isConnected&&id===current?.id){
    targetPanel.dataset.revision=data.items.find(r=>r.id===id)?.revision||'';
    message.textContent=metric===null?text('Uyarı kapatıldı.','Alert turned off.'):
     text('Eşik kaydedildi. %80 ve %100 için birer bildirim verilir.','Threshold saved. One notification each at 80% and 100%.');
   }
  }catch(error){
   if(message?.isConnected)message.textContent=text('Kaydedilemedi. Başka pencerede değiştirilmiş olabilir; son eşiği inceleyip tekrar dene.','Could not save. It may have changed in another window; review the latest threshold and try again.');
   else notice(text('Uyarı kapatılamadı. Yeniden dene.','Could not turn off the alert. Try again.'));
   await load();
   if(targetPanel?.isConnected)targetPanel.dataset.revision=data.items.find(r=>r.id===id)?.revision||'';
  }finally{busy=false;if(control.isConnected)control.disabled=false;render();}
 }
 function open(session, container){
  current=session;
  panel=el('section','session-budget');panel.id='session-budget';panel.dataset.revision=data.items.find(r=>r.id===session.id)?.revision||'';
  const heading=el('div','budget-heading');heading.append(el('h3','',text('Bütçe uyarısı','Budget alert')),el('span','budget-tag',text('80% / 100%','80% / 100%')));
  const summary=el('div','budget-readout');
  const description=el('p','section-note',text('Oturumun başından itibaren toplam kullanım. PLER açıkken yaklaşık 10 saniyede bir kontrol edilir.',
   'Total usage since the session began. Checked about every 10 seconds while PLER is open.'));
  const form=el('form','budget-form');const fieldset=el('fieldset','');
  const metricLabel=el('label','',text('Ölçü','Measure'));const select=el('select','');select.id='budget-metric';metricLabel.htmlFor=select.id;
  for(const [value,label] of [['tokens',text('Toplam token','Total tokens')],['usd',text('Dolar · API fiyat karşılığı','Dollars · API price equivalent')]]){const option=el('option','',label);option.value=value;select.append(option);}
  const limitLabel=el('label','',text('Uyarı eşiği','Alert threshold'));const input=el('input','');input.type='number';input.id='budget-limit';input.required=true;limitLabel.htmlFor=input.id;
  const row=data.items.find(r=>r.id===session.id);select.value=row?.metric||'tokens';input.value=String(row?.limit||(session.total_tokens>0?Math.ceil(session.total_tokens/100000)*100000:100000));
  const helper=el('p','section-note budget-metric-note');helper.id='budget-metric-note';input.setAttribute('aria-describedby',helper.id);
  function syncMetric(){input.step=select.value==='tokens'?'1':'0.001';input.min=select.value==='tokens'?'1':'0.001';input.max=select.value==='tokens'?'1000000000000':'1000000';helper.textContent=select.value==='tokens'?
   text('Girdi + önbellek + çıktı. Reasoning ikinci kez eklenmez; bağlam penceresi veya hesap kotası değildir.',
    'Input + cache + output. Reasoning is not added twice; this is not a context window or account quota.'):
   text('Gerçek fatura veya abonelik harcaması değildir. Fiyatı/kullanımı eksik oturumlarda uyarı bekletilir.',
    'Not an actual bill or subscription spend. Alerts pause when pricing or usage is incomplete.');}
  select.addEventListener('change',()=>{input.value=select.value==='tokens'?'100000':'5';syncMetric();});syncMetric();
  const metricGroup=el('div','budget-field');metricGroup.append(metricLabel,select);const limitGroup=el('div','budget-field');limitGroup.append(limitLabel,input);
  const save=el('button','primary',text('Eşiği kaydet','Save threshold'));save.type='submit';
  fieldset.append(metricGroup,limitGroup,save);form.append(fieldset);
  const off=el('button','quiet budget-off',text('Uyarıyı kapat','Turn off alert'));off.type='button';
  off.addEventListener('click',()=>change(session.id,null,null,panel.dataset.revision||null,off));
  form.addEventListener('submit',event=>{event.preventDefault();if(!input.reportValidity())return;change(session.id,select.value,input.valueAsNumber,panel.dataset.revision||null,save);});
  const message=el('p','budget-message');message.setAttribute('role','status');
  const connection=el('p','section-note budget-connection');connection.hidden=true;
  const existing=el('p','section-note budget-existing',text('Mevcut kayıtta: ','Currently recorded: ')+fmt(session.total_tokens)+' token');
  panel.append(heading,summary,existing,description,form,helper,off,message,connection,
   el('p','section-note',text('Bu bir uyarıdır; oturumu durdurmaz. Kayıt gecikebilir, eşik aşılabilir. Değişen eşik bildirimleri yeniden etkinleştirir. PLER kapanınca izleme durur.',
    'An alert, not a stop control. Logs may arrive late and usage may exceed the threshold. Changing the threshold re-enables notifications. Closing PLER stops monitoring.')));
  const anchor=container.querySelector('.wb-session-metrics');if(anchor)anchor.after(panel);else container.prepend(panel);
  render();load();
 }
 window.plerOpenBudgetSession=id=>{if(/^[a-f0-9]{24}$/.test(id))inspectUsageSession(id);};
 const timer=setInterval(load,5000);load();
 window.addEventListener('pagehide',()=>{stopped=true;clearInterval(timer);},{once:true});
 return {open,close(){current=null;panel=null;},load};
}
