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
 const banner=el('section','budget-banner');banner.hidden=true;banner.setAttribute('aria-label',t('usage_alerts'));before.before(banner);
 const watch=el('section','budget-watch usage-panel');watch.id='budget-watch';
 watch.append(el('h2','',t('usage_alerts')),
  el('p','section-note',text('Bir oturum için kendi token veya dolar eşiğini belirle; hesap kotaların değişmez. PLER açıkken %80 ve %100’de haber verir. En fazla 20 oturum.',
  'Set your own token or dollar threshold for a session; account limits stay unchanged. Get notified at 80% and 100% while PLER is open. Up to 20 sessions.')));
 const add=el('button','secondary budget-add',text('Oturum bul ve uyarı kur','Find a session and set an alert'));add.type='button';
 add.addEventListener('click',()=>{window.plerUI.setScreen('sessions');document.getElementById('usage-session-search').focus();});watch.append(add);
 const watchStatus=el('p','section-note');watchStatus.setAttribute('role','status');
 const watchRows=el('div','budget-watch-rows');watch.append(watchStatus,watchRows);
 const watchHelp=el('details','budget-help');watchHelp.append(el('summary','',text('Bildirim ayrıntıları','Notification details')),el('p','section-note',text('Ekran filtreleri izlemeyi etkilemez. Windows bildirim ayarları veya Rahatsız Etmeyin bildirimi gizleyebilir. Uyarılar uygulamada da görünür. Kullanım uyarısı ayarları özel yedeğe dahildir.',
  'Screen filters do not affect monitoring. Windows notification settings or Do not disturb may hide alerts. Alerts also remain visible in the app. Usage alert settings are included in private backups.')));watch.append(watchHelp);
 settings.prepend(watch);
 function metricName(row){return row.metric==='tokens'?'token':'USD · '+t('stat_api');}
 function amountText(row){return (row.amount==null?'—':fmt(row.amount))+' / '+fmt(row.limit)+' '+metricName(row);}
 function stateText(row){return row.state==='watching'&&row.level?text('%'+row.level+' eşiğine ulaşıldı',row.level+'% threshold reached'):stateNames[row.state]||stateNames.checking;}
 function readout(row, box){
  box.replaceChildren();box.dataset.level=String(row?.level||0);
  if(!row){box.append(el('strong','',text('Uyarı kapalı','Alert off')));return;}
  if(box.closest('#session-budget'))box.append(el('small','budget-saved-label',text('Kaydedilmiş uyarı','Saved alert')));
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
   const row=data.items.find(r=>r.id===current.id),summary=panel.querySelector('.budget-readout');readout(row,summary);summary.hidden=!row;
   panel.querySelector('.budget-editor > summary').textContent=row?text('Uyarıyı düzenle','Edit alert'):text('Uyarı kur','Set an alert');
   const error=panel.querySelector('.budget-connection');error.hidden=!failed&&data.readable;
   error.textContent=failed?text('Bağlantı yok; kaydedilmemiş değişiklikler korunuyor.','No connection; your unsaved changes are kept.'):
    text('Eşik dosyası okunamadı; kaydetme kapalı.','Threshold file unreadable; saving is disabled.');
   panel.querySelector('fieldset').disabled=busy||failed||!data.readable;
   panel.querySelector('.budget-off').hidden=!row;
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
     text('Uyarı kaydedildi. %80 ve %100 için birer bildirim verilir.','Alert saved. One notification each at 80% and 100%.');
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
  const heading=el('div','budget-heading');heading.append(el('h3','',t('usage_alert')));
  const summary=el('div','budget-readout');
  const description=el('p','section-note',text('PLER açıkken %80 ve %100’de haber verir. Oturumu durdurmaz.',
   'Notifies you at 80% and 100% while PLER is open. Does not stop the session.'));
  const editor=el('details','budget-editor');editor.append(el('summary','',text('Uyarı kur','Set an alert')));
  const form=el('form','budget-form');const fieldset=el('fieldset','');
  const metricLabel=el('label','',text('Uyarı türü','Alert type'));const select=el('select','');select.id='budget-metric';metricLabel.htmlFor=select.id;
  for(const [value,label] of [['tokens',text('Toplam token','Total tokens')],['usd',text('Dolar · API fiyat karşılığı','Dollars · API price equivalent')]]){const option=el('option','',label);option.value=value;select.append(option);}
  const limitLabel=el('label','',text('Uyarı eşiği','Alert threshold'));const input=el('input','');input.type='number';input.id='budget-limit';input.required=true;limitLabel.htmlFor=input.id;
  const row=data.items.find(r=>r.id===session.id);select.value=row?.metric||'tokens';input.value=String(row?.limit||(Math.floor(session.total_tokens/100000)+1)*100000);
  const helper=el('p','section-note budget-metric-note');helper.id='budget-metric-note';input.setAttribute('aria-describedby',helper.id);
  const presets=el('div','budget-presets');presets.setAttribute('role','group');presets.setAttribute('aria-label',text('Hızlı eşik seçimi','Quick threshold choices'));
  const warning=el('p','budget-limit-warning');warning.id='budget-limit-warning';warning.hidden=true;input.setAttribute('aria-describedby',helper.id+' '+warning.id);
  function syncLimit(){
   const amount=select.value==='tokens'?session.total_tokens:session.api_priced_share?session.api_usd:null;
   const past=amount!=null&&Number(input.value)>0&&amount>=Number(input.value);warning.hidden=!past;
   warning.textContent=past?text('Kayıtlı kullanım bu eşiğe ulaşmış. Kaydedince ilk uygun kontrolde uyarı gelebilir.','Recorded usage has already reached this threshold. Saving may trigger an alert on the first eligible check.'):'';
   for(const button of presets.children)button.setAttribute('aria-pressed',String(Number(button.dataset.limit)===Number(input.value)));
  }
  function buildPresets(){
   presets.replaceChildren();const tokens=select.value==='tokens',step=tokens?100000:5;
   const amount=tokens?session.total_tokens:session.api_priced_share?session.api_usd:0;
   const base=(Math.floor(amount/step)+1)*step;
   for(const multiple of [1,2,5]){const value=base*multiple;if(value>Number(input.max))continue;const button=el('button','budget-preset',(tokens?'':'$')+fmt(value));button.type='button';button.dataset.limit=String(value);button.addEventListener('click',()=>{input.value=String(value);syncLimit();message.textContent='';});presets.append(button);}
   syncLimit();
  }
  function syncMetric(){input.step=select.value==='tokens'?'1':'0.001';input.min=select.value==='tokens'?'1':'0.001';input.max=select.value==='tokens'?'1000000000000':'1000000';helper.textContent=select.value==='tokens'?
   text('Oturumun başından itibaren toplam token: girdi + önbellek + çıktı.',
    'Total tokens since the session began: input + cache + output.'):
   text('Gerçek fatura veya abonelik harcaması değildir. Fiyatı/kullanımı eksik oturumlarda uyarı bekletilir.',
    'Not an actual bill or subscription spend. Alerts pause when pricing or usage is incomplete.');buildPresets();}
  select.addEventListener('change',()=>{syncMetric();input.value=presets.firstElementChild?.dataset.limit||(select.value==='tokens'?'100000':'5');syncLimit();message.textContent='';});input.addEventListener('input',()=>{syncLimit();message.textContent='';});syncMetric();
  const metricGroup=el('div','budget-field');metricGroup.append(metricLabel,select);const limitGroup=el('div','budget-field');limitGroup.append(limitLabel,input);
  const save=el('button','primary',text('Uyarıyı kaydet','Save alert'));save.type='submit';
  fieldset.append(metricGroup,limitGroup,presets,helper,warning,save);form.append(fieldset);
  const off=el('button','quiet budget-off',text('Uyarıyı kapat','Turn off alert'));off.type='button';
  const ownPanel=panel;
  off.addEventListener('click',()=>change(session.id,null,null,ownPanel.dataset.revision||null,off));
  form.addEventListener('submit',event=>{event.preventDefault();if(!input.reportValidity())return;change(session.id,select.value,input.valueAsNumber,ownPanel.dataset.revision||null,save);});
  const message=el('p','budget-message');message.setAttribute('role','status');
  const connection=el('p','section-note budget-connection');connection.hidden=true;
  const help=el('details','budget-help');help.append(el('summary','',text('Uyarı nasıl çalışır?','How does the alert work?')),
   el('p','section-note',text('Yaklaşık 10 saniyede bir kontrol edilir. Kayıt gecikebilir, eşik aşılabilir. Reasoning ikinci kez eklenmez; token eşiği bağlam penceresi veya hesap kotası değildir. Değişen eşik bildirimleri yeniden etkinleştirir. PLER kapanınca izleme durur.',
    'Checked about every 10 seconds. Logs may arrive late and usage may exceed the threshold. Reasoning is not counted twice; a token threshold is not a context window or account quota. Changing the threshold re-enables notifications. Closing PLER stops monitoring.')));
  editor.append(form,off,help);panel.append(heading,description,summary,editor,message,connection);
  const anchor=container.querySelector('.wb-session-usage,.wb-session-metrics');if(anchor)anchor.after(panel);else container.prepend(panel);
  render();load();
 }
 window.plerOpenBudgetSession=id=>{if(/^[a-f0-9]{24}$/.test(id))inspectUsageSession(id);};
 const timer=setInterval(load,5000);load();
 window.addEventListener('pagehide',()=>{stopped=true;clearInterval(timer);},{once:true});
 return {open,close(){current=null;panel=null;},load};
}
