// Paths are displayed only in this local settings panel, never in reports.
export function mountSourceFolders({tr, settings, show, reveal}) {
 const text=(local,en)=>tr?local:en;
 const el=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value)n.textContent=value;return n;};
 const names={'claude-code':'Claude Code',codex:'Codex'};
 const reasons={
  missing:text('Klasör bulunamadı. Yolu kontrol et.','Folder not found. Check the path.'),
  not_folder:text('Bir dosya yerine kayıt klasörünü seç.','Choose a log folder, rather than a file.'),
  unsafe_path:text('Tam bir yerel klasör yolu veya WSL kayıt yolu kullan. Ağ paylaşımları ve disk kökü desteklenmez.','Use a full local folder path or WSL log path. Network shares and drive roots are unsupported.'),
  wsl_not_running:text('Bu WSL dağıtımı çalışmıyor. Kendin başlattıktan sonra yeniden kontrol et; Roodof dağıtımı başlatmaz.','This WSL distribution is stopped. Start it yourself, then check again; Roodof does not start distributions.'),
  wsl_unavailable:text('Çalışan WSL dağıtımları öğrenilemedi. WSL durumunu kontrol edip yeniden dene.','Could not check running WSL distributions. Check WSL, then retry.'),
  unreadable:text('Klasör veya kayıtlı kaynak tercihleri okunamadı. Mevcut tercihler korundu. Erişim izinlerini kontrol et.','The folder or saved source preferences could not be read. Existing preferences were kept. Check access permissions.'),
  unsaved:text('Tercihler kaydedilemedi. Roodof veri klasörünün yazılabilir olduğunu kontrol et.','Could not save preferences. Check that the Roodof data folder is writable.'),
  conflict:text('Klasör listesi başka bir pencerede değişti. Güncel liste yüklendi; kontrol edip yeniden dene.','The folder list changed in another window. The latest list was loaded; review it and retry.'),
  limit:text('En fazla 12 ek kayıt klasörü kaydedilebilir.','Up to 12 extra log folders can be saved.'),
  demo:text('Örnek görünümde gerçek kayıt klasörleri değiştirilmez.','Real log folders cannot be changed in the demo.'),
  invalid:text('Klasör yolunu ve ajan seçimini kontrol et.','Check the folder path and agent selection.')
 };
 let data=null,busy=false,checked=null,loading=false;
 const section=el('section','source-folders usage-panel');section.id='source-folders';
 const heading=el('h2','',text('Kayıt klasörleri','Log folders'));heading.tabIndex=-1;
 section.append(heading,el('p','section-note',text('Standart klasörler otomatik okunur. Başka bir kurulumdaki kayıtları buradan ekleyebilirsin.','Standard folders are read automatically. Add records from another installation here.')));
 const automatic=el('details','source-automatic');automatic.append(el('summary','',text('Otomatik aranan klasörler','Folders searched automatically')));
 const autoRows=el('div','source-auto-rows');automatic.append(autoRows);section.append(automatic);
 const rows=el('div','source-folder-rows');section.append(rows);
 const form=el('form','source-folder-form'),fields=el('fieldset','');
 const agentLabel=el('label','',text('Ajan','Agent')),agent=el('select','');agent.id='source-agent';agentLabel.htmlFor=agent.id;
 for(const [value,name] of Object.entries(names)){const option=el('option','',name);option.value=value;agent.append(option);}
 const pathLabel=el('label','',text('Kayıt klasörü yolu','Log folder path')),path=el('input','');path.id='source-path';pathLabel.htmlFor=path.id;path.type='text';path.maxLength=1024;path.required=true;path.autocomplete='off';path.spellcheck=false;
 const browse=el('button','secondary',text('Klasör seç…','Choose folder…'));browse.type='button';browse.id='source-browse';browse.hidden=typeof window.plerDesktop?.chooseLogFolder!=='function';
 const check=el('button','secondary',text('Kontrol et','Check folder'));check.type='submit';check.id='source-check';
 const add=el('button','primary',text('Klasörü ekle','Add folder'));add.type='button';add.id='source-add';
 const hint=el('p','section-note source-hint');hint.id='source-hint';path.setAttribute('aria-describedby',hint.id);
 function hintText(){hint.textContent=agent.value==='codex'?text('Codex için .codex ana klasörünü veya sessions / archived_sessions kayıt klasörünü seç.','For Codex, choose the .codex home or a sessions / archived_sessions log folder.'):text('Claude Code için .claude ana klasörünü veya projects kayıt klasörünü seç.','For Claude Code, choose the .claude home or its projects log folder.');}
 const agentField=el('div','source-field');agentField.append(agentLabel,agent);const pathField=el('div','source-field source-path-field');pathField.append(pathLabel,path);
 const actions=el('div','source-folder-actions');actions.append(browse,check,add);fields.append(agentField,pathField,actions);form.append(fields,hint);section.append(form);
 const message=el('p','source-message section-note');message.id='source-message';message.setAttribute('role','status');message.setAttribute('aria-live','polite');
 const preview=el('ul','source-preview');preview.hidden=true;section.append(message,preview);
 const retry=el('button','quiet',text('Listeyi yeniden yükle','Reload folder list'));retry.type='button';retry.id='source-reload';retry.addEventListener('click',load);section.append(retry);
 const guidance=el('details','source-guidance');guidance.append(el('summary','',text('WSL ve kayıtların saklanması','WSL and retained records')),
  el('p','section-note',text('WSL yolu örneği: \\\\wsl.localhost\\Ubuntu\\home\\kullanici\\.codex\\sessions. Yalnız zaten çalışan dağıtım okunur; diğer ağ paylaşımları okunmaz.','Example WSL path: \\\\wsl.localhost\\Ubuntu\\home\\user\\.codex\\sessions. Only already-running distributions are read; other network shares are refused.')),
  el('p','section-note',text('Kaldırılan klasör artık taranmaz; kaynak dosyaları ve saklanan özel geçmiş silinmez. Klasör seçimi bu bilgisayara özeldir; geçmişi geri yükledikten sonra yeniden ekle. Özel yedek, saklanan geçmişteki kaynak yollarını içerebilir.','Removed folders are no longer scanned; source files and retained private history are kept. Folder selection is specific to this computer; add it again after restoring history. Private backups can contain source paths from retained history.')));section.append(guidance);
 settings.prepend(section);
 function sync(){fields.disabled=busy||loading||!data?.readable||data?.demo||usageState.stopped;add.disabled=!checked||busy||loading;retry.disabled=busy||loading;rows.querySelectorAll('button').forEach(b=>b.disabled=busy||loading||!data?.readable||data?.demo||usageState.stopped);}
 function invalidate(){checked=null;preview.hidden=true;preview.replaceChildren();add.disabled=true;message.textContent='';hintText();}
 path.addEventListener('input',invalidate);agent.addEventListener('change',invalidate);hintText();
 async function request(body){try{return await post('/api/usage/sources',body);}catch(error){throw {reason:error.code||'connection'};}}
 function fail(error){message.textContent=reasons[error.reason]||text('Bağlantı kurulamadı. Klasör yolu korundu; yeniden dene.','Could not connect. Your folder path was kept; retry.');message.dataset.state='error';}
 async function inspect(){
  if(busy||!path.value.trim())return;busy=true;checked=null;sync();preview.hidden=true;
  message.textContent=text('Klasör kontrol ediliyor…','Checking folder…');message.dataset.state='checking';
  try{const result=await request({action:'check',agent:agent.value,path:path.value.trim()});checked={agent:agent.value,path:path.value.trim()};preview.replaceChildren(...result.roots.map(root=>el('li','',root)));preview.hidden=false;message.textContent=text('Klasör erişilebilir. Aşağıdaki kayıt klasörleri eklenecek; oturumlar ekledikten sonra taranır.','Folder is accessible. The log folders below will be added; sessions are scanned after adding.');message.dataset.state='ready';}
  catch(error){fail(error);}finally{busy=false;sync();}
 }
 form.addEventListener('submit',event=>{event.preventDefault();inspect();});
 browse.addEventListener('click',async()=>{
  if(busy)return;busy=true;sync();
  try{const value=await window.plerDesktop.chooseLogFolder();if(value){path.value=value;invalidate();}}
  catch{fail({});}finally{busy=false;sync();}
  if(path.value)path.focus();
 });
 async function mutate(body,control){
  if(busy)return;busy=true;sync();
  try{const result=await request({...body,expected:data.revision});data=result;render();invalidate();message.textContent=body.action==='remove'?text('Klasör kaldırıldı. Kaynak dosyaları korundu.','Folder removed. Source files were kept.'):text('Klasör eklendi. Kaynak listesi kaydedildi.','Folder added. Source list saved.');message.dataset.state='ready';if(body.action==='add')path.value='';await loadUsage();}
  catch(error){if(error.reason==='conflict')await load();fail(error);}finally{busy=false;sync();if(control?.isConnected)control.focus();else path.focus();}
 }
 add.addEventListener('click',()=>{if(checked)mutate({action:'add',...checked},add);});
 function render(){
  autoRows.replaceChildren(...(data?.automatic||[]).map(row=>{const item=el('div','source-auto-row');item.append(el('strong','',names[row.agent]),el('code','',row.path));return item;}));
  rows.replaceChildren();
  for(const row of data?.entries||[]){
   const item=el('div','source-folder-row');item.dataset.sourceId=row.id;
   const info=el('div','source-folder-info');info.append(el('strong','',names[row.agent]+(row.path.startsWith('\\\\')?' · WSL':'')),el('code','',row.path));
   const verify=el('button','quiet',text('Kontrol et','Check'));verify.type='button';verify.setAttribute('aria-label',text('Klasörü kontrol et: ','Check folder: ')+row.path);verify.addEventListener('click',()=>{agent.value=row.agent;path.value=row.path;invalidate();inspect();});
   const remove=el('button','quiet source-remove',text('Kaldır','Remove'));remove.type='button';remove.setAttribute('aria-label',text('Klasörü kaldır: ','Remove folder: ')+row.path);remove.addEventListener('click',()=>mutate({action:'remove',id:row.id},remove));item.append(info,verify,remove);rows.append(item);
  }
  if(!data?.entries?.length)rows.append(el('p','section-note source-none',text('Ek kayıt klasörü yok.','No extra log folders.')));
 }
 async function load(){
  if(loading)return;loading=true;sync();
  try{data=await api('/api/usage/sources');render();if(!data.readable)fail({reason:'unreadable'});else if(data.demo)fail({reason:'demo'});}
  catch{data=null;fail({});}finally{loading=false;sync();}
 }
 document.addEventListener('pler-screen-change',event=>{if(event.detail==='settings')load();});
 document.addEventListener('pler-manage-sources',()=>{if(reveal)reveal(section);else show('settings',true);heading.focus({preventScroll:true});section.scrollIntoView({block:'start',behavior:'instant'});});
 sync();load();
 return {load};
}
