// The server holds one verified, ten-minute preview. No backup is sent off this computer.
export function mountHistoryRecovery({tr,settings,show}){
 const text=(local,en)=>tr?local:en;
 const el=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value)n.textContent=value;return n;};
 const button=(id,label,cls='secondary')=>{const n=el('button',cls,label);n.type='button';n.id=id;return n;};
 const number=n=>new Intl.NumberFormat(tr?'tr-TR':'en-US').format(n??0);
 const panel=el('section','history-recovery');panel.id='history-recovery';panel.setAttribute('aria-labelledby','history-recovery-title');
 const title=el('h3','',text('Yedekten geçmiş kurtar','Recover history from a backup'));title.id='history-recovery-title';title.tabIndex=-1;
 const intro=el('p','section-note',text('Güvendiğin PLER yedeğini seç. İçeriği incele, ayrı bir klasöre kurtar ve hazır olduğunda o geçmişi aç.','Choose a trusted PLER backup. Review its contents, recover it into a separate folder, then open that history when ready.'));
 const current=el('p','recovery-current section-note');current.id='recovery-current';
 const status=el('p','recovery-status section-note');status.id='recovery-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');
 const inputLabel=el('label','',text('PLER yedek dosyası','PLER backup file'));inputLabel.htmlFor='recovery-file';
 const file=el('input','');file.id='recovery-file';file.type='file';file.accept='.zip,application/zip';
 const inspect=button('recovery-inspect',text('İçeriği incele','Review contents'));
 const choose=el('div','recovery-file-row');choose.append(inputLabel,file,inspect);
 const details=el('div','recovery-details');details.id='recovery-details';details.hidden=true;
 const summary=el('dl','recovery-summary');summary.id='recovery-summary';
 const parentLabel=el('label','',text('Yeni klasörün oluşturulacağı konum','Location for the new folder'));parentLabel.htmlFor='recovery-parent';
 const parent=el('input','');parent.id='recovery-parent';parent.type='text';parent.maxLength=2048;parent.autocomplete='off';parent.spellcheck=false;
 const browse=button('recovery-browse',text('Konum seç…','Choose location…'));browse.hidden=typeof window.plerDesktop?.chooseRecoveryParent!=='function';
 const plan=button('recovery-plan',text('Konumu hazırla','Prepare location'));
 const destination=el('div','recovery-destination');destination.append(parentLabel,parent,browse,plan);
 const target=el('p','recovery-path section-note');target.id='recovery-target';
 function consent(id,label){const row=el('label','recovery-consent');const input=el('input','');input.type='checkbox';input.id=id;row.append(input,el('span','',label));return {row,input};}
 const agreed=consent('recovery-confirm',text('Yedeğin yeni klasöre kurtarılmasını onaylıyorum. Açık geçmişimin üzerine yazılmayacak.','Recover this backup into the new folder. My open history will be kept.'));
 const restore=button('recovery-restore',text('Yeni klasöre kurtar','Recover into new folder'),'primary');
 const discard=button('recovery-discard',text('İncelemeyi kapat','Close review'),'quiet');
 const recoveryActions=el('div','recovery-actions');recoveryActions.append(restore,discard);
 details.append(summary,destination,target,agreed.row,recoveryActions);
 const success=el('div','recovery-success');success.id='recovery-success';success.hidden=true;
 const successTitle=el('strong','',text('Yedek kurtarıldı','Backup recovered'));const recoveredPath=el('code','recovery-path');recoveredPath.id='recovery-restored-path';success.append(successTitle,recoveredPath);
 const switching=consent('recovery-open-confirm',text('Taslaklarımı kaydettim. Bu pencerenin kapanıp seçtiğim geçmişle yeniden açılmasını onaylıyorum.','I have saved my drafts. Close this window and reopen it with the selected history.'));
 const open=button('recovery-open',text('Kurtarılan geçmişi aç','Open recovered history'),'primary');
 const previous=button('recovery-previous',text('Önceki geçmişe dön','Return to previous history'));
 const openActions=el('div','recovery-actions');openActions.append(open,previous);
 const switchArea=el('div','recovery-switch');switchArea.append(switching.row,openActions);
 const persistence=el('p','section-note');persistence.id='recovery-persistence';
 const retry=button('recovery-reload',text('Durumu yenile','Reload status'),'quiet');
 const limits=el('p','section-note',text('Yedek özel yollar ve iş notları içerebilir; şifreli değildir. Asıl ajan kayıtlarını içermez. Kontrol, dosyanın güvenilir bir kişiden geldiğini kanıtlamaz. İnceleme 10 dakika sonra bellekten kaldırılır. Özel kayıt klasörlerini kurtarılan geçmişte yeniden ekle.','Backups can contain private paths and work notes; they are not encrypted. Original agent logs are excluded. Validation does not establish who supplied a file. The review is removed from memory after ten minutes. Add custom log folders again in recovered history.'));
 panel.append(title,intro,current,choose,status,details,success,switchArea,persistence,retry,limits);
 const backupPanel=settings.querySelector('.backup-controls');(backupPanel||settings).append(panel);
 // Keep the old standalone check available to the legacy page, with one file workflow here.
 for(const node of [document.querySelector('.backup-check'),document.getElementById('usage-backup-check-help'),document.getElementById('usage-backup-result')])if(node)node.hidden=true;
 let data=null,busy=false,loading=false,destinationDirty=false,fileDirty=false;
 const reasons={invalid:text('Yedek veya istek geçersiz. Güvendiğin özgün PLER yedeğini seç.','Invalid backup or request. Choose a trusted original PLER backup.'),
  unsupported:text('Yedeğin sürümü ya da veri biçimi bu uygulamayla uyumlu değil.','This backup version or data format is not supported.'),
  limit:text('Dosya desteklenen boyut veya içerik sınırını aşıyor.','The file exceeds a supported size or content limit.'),
  unsafe_path:text('Var olan yerel bir konum seç. Açık veri veya uygulama klasörünün içine kurtarma yapılamaz.','Choose an existing local location outside the open data and application folders.'),
  exists:text('Hedef konum artık var. Konumu yeniden hazırla; mevcut klasör değiştirilmedi.','The destination now exists. Prepare the location again; the existing folder was kept.'),
  conflict:text('İnceleme süresi dolmuş veya başka bir pencerede değişmiş. Durumu yenile ve dosyayı yeniden incele.','The review expired or changed in another window. Reload status and review the file again.'),
  busy:text('Başka bir işlem sürüyor. Tamamlanınca yeniden dene.','Another operation is running. Retry when it finishes.'),
  demo:text('Deneme modunda kurtarma kapalı. Normal PLER penceresini aç.','Recovery is disabled in demo mode. Open the normal PLER window.'),
  desktop_required:text('Geçmişi açmak için PLER masaüstü uygulamasını kullan.','Use the PLER desktop app to open this history.'),
  io:text('Dosya işlemi tamamlanamadı. Konumu ve boş alanı kontrol edip durumu yenile.','The file operation could not finish. Check the location and free space, then reload status.')};
 function message(value,error=false){status.textContent=value;status.dataset.state=error?'error':'ready';}
 function sync(){
  const blocked=busy||loading||usageState.stopped||data?.demo;
  details.hidden=!data?.preview||fileDirty;
  file.disabled=blocked;inspect.disabled=blocked||!file.files?.length;
  parent.disabled=blocked||!data?.preview;browse.disabled=parent.disabled;plan.disabled=parent.disabled||!parent.value.trim();
  agreed.input.disabled=blocked||!data?.preview?.target||destinationDirty||fileDirty;restore.disabled=agreed.input.disabled||!agreed.input.checked;
  discard.disabled=blocked;retry.disabled=busy||loading;
  const closingBlocked=blocked||!data?.desktop||usageState.loading||usageState.workBusy;
  switching.input.disabled=closingBlocked;open.disabled=closingBlocked||!switching.input.checked;
  previous.disabled=closingBlocked||!switching.input.checked;
  panel.setAttribute('aria-busy',String(busy||loading));
 }
 function render(){
  const p=data?.preview;details.hidden=!p;summary.replaceChildren();
  if(p){const s=p.summary;for(const [label,value] of [[text('Yedek tarihi','Backup date'),new Date(s.created_at).toLocaleString(tr?'tr-TR':'en-US')],[text('PLER sürümü','PLER version'),s.version],[text('Saklanan kaynak','Retained sources'),number(s.archive_files)],[text('İş / bağlantı','Works / links'),number(s.work_items)+' / '+number(s.work_links)],[text('Değerlendirme / kota örneği','Reviews / quota samples'),number(s.verdicts)+' / '+number(s.quota_samples)]])summary.append(el('dt','',label),el('dd','',value));}
  target.textContent=p?.target?text('Oluşturulacak klasör: ','Folder to create: ')+p.target:text('Bir üst konum seç; PLER orada yeni bir klasör hazırlayacak.','Choose a parent location; PLER will prepare a new folder there.');
  success.hidden=!data?.restored;recoveredPath.textContent=data?.restored?.target||'';
  open.hidden=!data?.restored;previous.hidden=!data?.previous;switchArea.hidden=!data?.restored&&!data?.previous;
  current.textContent=data?.current?text('Açık geçmiş: ','Open history: ')+data.current:'';
  persistence.textContent=data?.remembered?text('Geçmiş açma seçimin normal masaüstü açılışlarında hatırlanır. Önceki geçmişin ayrıca korunur.','Your history choice is remembered for normal desktop launches. Previous history is kept separately.'):text('Bu açılış için özel bir veri klasörü seçilmiş veya tarayıcı kullanılıyor. Geçmiş değiştirme seçimi yalnız bu çalıştırma için geçerlidir.','This launch uses an explicit data folder or a browser. Switching history applies to this run only.');
  if(data?.issue)message(text('Seçilen geçmiş açılamadı; başlangıç geçmişi açıldı. Kayıtlar silinmedi. Kurtarma konumunu kontrol et.','The selected history was unavailable; the starting history was opened. No history was deleted. Check the recovery location.'),true);
  sync();
 }
 async function load(){loading=true;sync();try{data={...data,...await api('/api/usage/recovery')};render();}catch{message(text('Kurtarma durumu okunamadı. Yeniden dene.','Could not read recovery status. Retry.'),true);}finally{loading=false;sync();}}
 async function run(action,body){
  if(busy)return;busy=true;usageState.backupBusy='recovery';syncArchiveButton();syncExportButton();syncWorkControls();sync();
  message(text('İşlem sürüyor…','Working…'));
  try{
   let result;
   if(action==='inspect'){
    const chosen=file.files?.[0],maximum=Number(document.querySelector('meta[name="pler-backup-max"]')?.content);
    if(!chosen||chosen.size<=0||chosen.size>maximum)throw {reason:'limit'};
    const response=await fetch('/api/usage/recovery/preview',{method:'POST',headers:{'Content-Type':'application/octet-stream','X-PLER-Token':token},body:chosen,cache:'no-store'});
    result=await response.json();if(!response.ok)throw result;
   }else result=await post('/api/usage/recovery',body);
   data={...data,...result};agreed.input.checked=false;
   if(action==='inspect'){fileDirty=false;destinationDirty=false;}
   if(action==='destination')destinationDirty=false;
   render();
   message(action==='restore'&&data.restored?.summary.durability_uncertain?text('Klasörün içeriği doğrulandı; diske kalıcı yazma onayı alınamadı. Özgün yedeğini sakla.','Folder contents were verified, but durable disk sync could not be confirmed. Keep the original backup.'):action==='restore'?text('Kurtarma tamamlandı. Hazır olduğunda kurtarılan geçmişi aç.','Recovery complete. Open the recovered history when ready.'):action==='inspect'?text('Yedek doğrulandı. Kurtarma konumunu seç.','Backup verified. Choose a recovery location.'):action==='destination'?text('Konum hazır. Yeni klasör yolunu inceleyip kurtarmayı onayla.','Location prepared. Review the new folder path and confirm recovery.'):'');
  }catch(error){await load();message(reasons[error.reason||error.code]||text('Bağlantı kesildi. İşlem tamamlanmış olabilir; durumu yenilemeden tekrar kurtarma başlatma.','Connection lost. The operation may have completed; reload status before trying recovery again.'),true);}
  finally{busy=false;usageState.backupBusy=null;syncArchiveButton();syncExportButton();syncWorkControls();sync();}
 }
 inspect.addEventListener('click',()=>run('inspect'));
 plan.addEventListener('click',()=>run('destination',{action:'destination',ticket:data.preview.ticket,expected:data.preview.expected,parent:parent.value.trim()}));
 restore.addEventListener('click',()=>run('restore',{action:'restore',ticket:data.preview.ticket,expected:data.preview.expected,confirmed:agreed.input.checked}));
 discard.addEventListener('click',()=>run('discard',{action:'discard',ticket:data.preview.ticket,expected:data.preview.expected}));
 parent.addEventListener('input',()=>{agreed.input.checked=false;destinationDirty=true;target.textContent=text('Konum değişti. Devam etmeden konumu yeniden hazırla.','Location changed. Prepare it again before continuing.');sync();});
 file.addEventListener('change',()=>{fileDirty=true;agreed.input.checked=false;message(text('Dosya seçildi. İçeriği incele ile devam et.','File selected. Continue with Review contents.'));sync();});
 agreed.input.addEventListener('change',sync);switching.input.addEventListener('change',sync);
 browse.addEventListener('click',async()=>{if(busy)return;busy=true;sync();try{const chosen=await window.plerDesktop.chooseRecoveryParent();if(chosen){parent.value=chosen;destinationDirty=true;agreed.input.checked=false;}}finally{busy=false;sync();}parent.focus();});
 async function switchHistory(action){
  if(busy||!switching.input.checked)return;
  busy=true;sync();message(text('Geçmiş değiştiriliyor…','Switching history…'));
  try{await post('/api/usage/recovery',{action,confirmed:true,...(action==='open'?{token:data.restored.token}:{})});usageState.stopped=true;}
  catch(error){busy=false;message(reasons[error.reason||error.code]||text('Geçmiş açılamadı. Durumu yenileyip tekrar dene.','Could not open history. Reload status and retry.'),true);sync();}
 }
 open.addEventListener('click',()=>switchHistory('open'));previous.addEventListener('click',()=>switchHistory('previous'));retry.addEventListener('click',load);
 window.plerUI.subscribe(['loading','stopped'],sync);
 load().then(()=>{if(data?.issue){show('settings',true);title.focus();}});
 return {open(){show('settings',true);title.focus();}};
}
