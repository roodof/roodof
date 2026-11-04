'use strict';
// Only local authenticated APIs. The server owns release URLs and signature checks.
(()=>{
  if(document.querySelector('meta[name="pler-updater"]')?.getAttribute('content')!=='1')return;
  const tr=document.documentElement.lang==='tr',words=tr?{
    title:'Güncellemeler',ready:'Yeni sürüm hazır',check:'Güncellemeleri kontrol et',install:'İndir ve güncelle',later:'Daha sonra',
    automatic:'Uygulamayı açtığımda güncellemeleri kontrol et',privacy:'Kontrol ve indirme internete bağlanır. Ajan kayıtların, konuşmaların ve proje bilgilerin gönderilmez.',
    idle:'Güncellemeyi kontrol etmek için düğmeye bas. Kullanım analizi çevrimdışı çalışmaya devam eder.',checking:'Yeni sürüm kontrol ediliyor…',
    current:'Güncel sürümü kullanıyorsun.',available:'Yeni sürümü indirip kurabilirsin. PLER yedek alacak ve yeniden açılacak.',
    manual_required:'Bu sürüm veri biçimi değişikliği gerektiriyor. Bu güncelleyici onu otomatik kurmayacak; sürümün geçiş rehberini kullan.',
    downloading:'Güncelleme indiriliyor ve doğrulanıyor…',activating:'Güncellenmiş PLER açılıyor…',preparing:'Yeni sürüm ayrı klasörde hazırlanıp sınanıyor…',backing_up:'Özel PLER verisinin doğrulanmış yedeği hazırlanıyor…',
    restarting:'PLER yeniden açılıyor. Yeni pencere hazır olduğunda bu sekmeyi kapatabilirsin.',error:'Güncelleme tamamlanamadı. Mevcut uygulama ve veriler korundu.',
    network:'Yayın hizmetine ulaşılamadı. Bağlantını kontrol edip yeniden dene.',verify:'Güvenilir ve güncel sürüm bilgisi doğrulanamadı. Paket kurulmadı.',
    package:'İndirilen paket doğrulamadan geçmedi. Paket kurulmadı.',prepare:'Yeni sürümün güvenli açılışı hazırlanamadı. Tekrar deneyebilirsin.',
    busy:'Aynı kurulum başka bir süreçte kullanılıyor veya önceki güncelleme inceleme bekliyor. Diğer PLER örneğini kapatıp yeniden dene.',
    space:'Güncelleme için yeterli boş alan yok.',folder:'Kurulum veya veri klasörüne güvenli biçimde erişilemiyor.',settings:'Güncelleme tercihleri okunamadı veya kaydedilemedi.',
    drafts:'Kaydedilmemiş iş veya takip girdilerin var. Güncellemeden önce kaydet veya açıkça vazgeç.',saving:'PLER önce mevcut işlemi tamamlamalı. Birazdan yeniden dene.',
    updated:'Güncelleme tamamlandı. Verilerin aynı klasörde korundu.',rolled_back:'Yeni sürüm açılamadı; önceki uygulama geri açıldı. Verilerin geri yüklenerek ezilmedi.',
    version:'Mevcut sürüm',newversion:'Yeni sürüm',size:'İndirme',close:'Güncelleme penceresini kapat'
  }:{
    title:'Updates',ready:'Update available',check:'Check for updates',install:'Download and update',later:'Later',
    automatic:'Check for updates when I open the app',privacy:'Checking and downloading connect to the Internet. Agent logs, conversations and project information are not sent.',
    idle:'Choose Check for updates to look for a release. Usage analysis continues to work offline.',checking:'Checking for a new release…',
    current:'You are using the current release.',available:'You can download and install this release. PLER will back up its data and reopen.',
    manual_required:'This release changes the data format. This updater will not install it automatically; follow the release migration instructions.',
    downloading:'Downloading and verifying the update…',activating:'Opening the updated PLER…',preparing:'Preparing and testing the new version in a separate folder…',backing_up:'Preparing a verified backup of private PLER data…',
    restarting:'PLER is reopening. You can close this tab when the new window is ready.',error:'The update could not finish. The current application and data were preserved.',
    network:'The release service could not be reached. Check your connection and try again.',verify:'Trusted, current release information could not be verified. Nothing was installed.',
    package:'The downloaded package failed verification. Nothing was installed.',prepare:'The new version could not be prepared safely. You can try again.',
    busy:'This installation is in use by another process or an earlier update needs review. Close the other PLER instance and try again.',
    space:'There is not enough free disk space for the update.',folder:'The installation or data folder could not be accessed safely.',settings:'Update preferences could not be read or saved.',
    drafts:'You have unsaved work or follow-up inputs. Save or explicitly discard them before updating.',saving:'PLER needs to finish its current action first. Try again shortly.',
    updated:'Update complete. Your data was kept in the same folder.',rolled_back:'The new version could not start; the previous app reopened. Your data was not overwritten with a backup.',
    version:'Current version',newversion:'New version',size:'Download',close:'Close update window'
  };
  const by=id=>document.getElementById(id),dialog=by('usage-update-dialog'),open=by('usage-update-open');
  let data=null,timer=null,requesting=false,actionError=null;
  const busy=()=>Boolean(data&&['checking','downloading','preparing','backing_up','restarting','activating'].includes(data.state));
  const installing=()=>busy()&&data.state!=='checking';
  function drafts(){
    if(typeof workState==='undefined')return false;
    const items=typeof usageState==='undefined'?[]:usageState.data?.work_items?.items||[];
    return Boolean(workState.createDraft?.trim()||Object.values(workState.sessionDrafts||{}).some(value=>value.trim())||Object.entries(workState.renameDrafts||{}).some(([id,title])=>title.trim()!==(items.find(i=>i.id===id)?.title||''))
      ||items.some(item=>typeof changedWorkDetails==='function'&&changedWorkDetails(item,workState.detailDrafts?.[item.id]))
      ||typeof followState!=='undefined'&&Object.values(followState.drafts||{}).some(d=>d.observation?.trim()||d.change?.trim()||Object.values(d.reviews||{}).some(r=>r.note?.trim()||r.context&&r.context!=='unknown')));
  }
  function render(){
    if(!data||typeof data.supported!=='boolean')return;
    open.hidden=!data.supported;if(!data.supported)return;
    open.textContent=data.state==='available'?words.ready+' · '+data.available_version:words.title;
    by('usage-update-title').textContent=words.title;
    by('usage-update-version').textContent=words.version+': '+data.current_version+(data.available_version?' · '+words.newversion+': '+data.available_version:'');
    let message=words[data.state]||words.error;
    if(data.last_result&&words[data.last_result]&&data.state==='idle')message=words[data.last_result];
    if(data.state==='error'){
      const key={network:'network',invalid_release:'verify',untrusted_release:'verify',expired_release:'verify',older_release:'verify',trust_unavailable:'verify',
        package_hash:'package',package_size:'package',invalid_package:'package',preflight:'prepare',prepare_failed:'prepare',busy_installation:'busy',application_busy:'busy',
        disk_space:'space',unsafe_path:'folder',preferences:'settings'}[data.error]||'error';message=words[key];
    }
    by('usage-update-status').textContent=actionError||message;
    by('usage-update-notes').textContent=data.notes?.[tr?'tr':'en']||'';
    const size=Number.isSafeInteger(data.size)&&data.size>0?data.size:0,received=Number.isSafeInteger(data.received)?Math.max(0,Math.min(data.received,size)):0;
    by('usage-update-size').textContent=size?words.size+': '+(size/1000000).toFixed(2)+' MB':'';
    by('usage-update-progress').hidden=data.state!=='downloading';by('usage-update-progress').max=size||1;by('usage-update-progress').value=received;
    by('usage-update-progress').setAttribute('aria-label',tr?'Güncelleme indiriliyor':'Update download');
    by('usage-update-check').textContent=words.check;by('usage-update-check').disabled=busy()||requesting;
    by('usage-update-install').textContent=words.install;by('usage-update-install').hidden=!data.installable;by('usage-update-install').disabled=busy()||requesting;
    by('usage-update-later').textContent=words.later;by('usage-update-later').disabled=installing();
    by('usage-update-close').disabled=installing();by('usage-update-close').setAttribute('aria-label',words.close);
    by('usage-update-auto-label').textContent=words.automatic;by('usage-update-auto').checked=data.automatic;by('usage-update-auto').disabled=busy()||requesting;
    by('usage-update-privacy').textContent=words.privacy;dialog.setAttribute('aria-busy',String(busy()));
    if(data.last_result==='rolled_back'&&!dialog.open)dialog.showModal();
  }
  function poll(){clearTimeout(timer);if(busy()&&data.state!=='restarting')timer=setTimeout(load,600);}
  async function load(){try{data=await api('/api/updates');render();poll();}catch(_){if(data?.state!=='restarting'){actionError=words.network;render();}}}
  async function action(path,body={}){
    if(requesting||busy())return;
    if(path==='install'&&typeof usageState!=='undefined'&&(usageState.workBusy||usageState.planSaving||usageState.metadataChanging||usageState.backupBusy)){
      actionError=words.saving;render();return;
    }
    if(path==='install'&&drafts()){actionError=words.drafts;render();return;}
    requesting=true;actionError=null;render();
    try{data=await post('/api/updates/'+path,body);render();poll();}
    catch(_){actionError=words.error;}
    finally{requesting=false;render();}
  }
  open.addEventListener('click',()=>{render();dialog.showModal();});
  by('usage-update-check').addEventListener('click',()=>action('check'));
  by('usage-update-install').addEventListener('click',()=>action('install'));
  by('usage-update-auto').addEventListener('change',event=>action('preferences',{automatic:event.target.checked}));
  for(const id of ['usage-update-close','usage-update-later'])by(id).addEventListener('click',()=>{if(!installing())dialog.close();});
  dialog.addEventListener('cancel',event=>{if(installing())event.preventDefault();});
  dialog.addEventListener('close',()=>open.focus());
  load();
})();
