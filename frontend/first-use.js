import {getView,saveView} from './view-preferences.js';

// A source check, not a login wizard. Counts cover every retained session,
// independently of the currently selected agent, project or period.
export function mountFirstUse({tr,settings,show,tour}) {
 const $=id=>document.getElementById(id);
 const text=(en,local)=>tr?local:en;
 const make=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value)n.textContent=value;return n;};
 const words={
  title:text('Find your Claude Code and Codex work','Claude Code ve Codex çalışmalarını bul'),
  intro:text('Find past sessions, see usage by project and keep related work together. PLER reads the local records these apps already save. No account connection is needed.','Geçmiş oturumlarını bul, proje kullanımını gör ve ilgili çalışmaları bir araya getir. PLER bu uygulamaların kaydettiği yerel kayıtları okur. Hesap bağlaman gerekmez.'),
  retry:text('Look for records again','Kayıtları yeniden ara'),
  reading:text('Reading local records…','Yerel kayıtlar okunuyor…'),
  later:text('Continue without records','Kayıt olmadan devam et'),
  privacy:text('No model call is made. This check does not upload your agent records. ChatGPT web conversations are not included.','Model çağrısı yapılmaz. Bu kontrol ajan kayıtlarını dışarı yüklemez. ChatGPT web sohbetleri dahil değildir.'),
  help:text('Source and WSL help','Kayıt kaynakları ve WSL yardımı')
 };
 let data=null,open=!getView().setupDone;
 const panel=make('section','first-use');panel.id='first-use';panel.setAttribute('aria-labelledby','first-use-title');
 const heading=make('h2','',words.title);heading.id='first-use-title';heading.tabIndex=-1;
 const caption=make('p','first-use-caption',text('LOCAL WORKSPACE','YEREL ÇALIŞMA ALANI'));
 const intro=make('p','first-use-intro',words.intro);
 const sources=make('div','first-use-sources');
 const status=make('p','first-use-status');status.setAttribute('role','status');status.setAttribute('aria-live','polite');
 const actions=make('div','first-use-actions');
 const primary=make('button','primary',text('Open sessions','Oturumları aç'));primary.type='button';
 const retry=make('button','secondary',words.retry);retry.type='button';retry.addEventListener('click',()=>{$('usage-refresh').click();update(data);});
 const later=make('button','quiet',words.later);later.type='button';
 const help=make('a','first-use-help',words.help);help.href='/help?lang='+(tr?'tr':'en')+'#coverage';
 const privacy=make('p','first-use-privacy',words.privacy);
 const leaveSetup=event=>{open=false;visibility();document.dispatchEvent(new CustomEvent(event));};
 const manage=make('button','secondary',text('Add a log folder','Kayıt klasörü ekle'));manage.type='button';manage.id='first-use-manage-sources';manage.addEventListener('click',()=>leaveSetup('pler-manage-sources'));
 const diagnose=make('button','quiet',text('Inspect read issues','Sorunu incele'));diagnose.type='button';diagnose.id='first-use-diagnostics';diagnose.hidden=true;diagnose.addEventListener('click',()=>leaveSetup('pler-open-diagnostics'));
 actions.append(primary,retry,manage,later,diagnose);panel.append(caption,heading,intro,sources,status,actions,help,privacy);
 document.querySelector('.workspace-head').after(panel);
 const sourceRows=new Map();
 for(const [agent,name] of [['claude-code','Claude Code'],['codex','Codex']]){
  const row=make('div','first-use-source');row.dataset.agent=agent;
  const mark=make('span','first-use-mark',agent==='codex'?'>_':'C');mark.setAttribute('aria-hidden','true');
  const identity=make('div','first-use-source-name');identity.append(make('strong','',name));
  const state=make('span','first-use-source-state');state.dataset.sourceState=agent;
  row.append(mark,identity,state);sources.append(row);sourceRows.set(agent,{row,state});
 }
 const guidance=make('details','first-use-guidance');
 guidance.append(make('summary','',text('Where do these records come from?','Bu kayıtlar nereden geliyor?')));
 for(const message of [
  text('Use Claude Code or Codex for a session on this Windows account, then look for records again. Installing the app alone does not create a session.','Bu Windows hesabında Claude Code veya Codex ile bir oturum kullan, ardından kayıtları yeniden ara. Yalnızca uygulamayı kurmak oturum oluşturmaz.'),
  text('For another local installation or a running WSL distribution, choose Add a log folder. Records on another computer are not read remotely.','Başka bir yerel kurulum veya çalışan WSL dağıtımı için Kayıt klasörü ekle seçeneğini kullan. Başka bilgisayardaki kayıtlar uzaktan okunmaz.'),
  text('If you already have sessions, check that their local records are still present and readable. PLER can only show the records it can read.','Oturumların zaten varsa yerel kayıtlarının hâlâ bulunduğunu ve okunabildiğini kontrol et. PLER yalnız okuyabildiği kayıtları gösterebilir.')
 ])guidance.append(make('p','',message));
 panel.insertBefore(guidance,status);
 const reopen=make('button','secondary',text('Check record sources','Kayıt kaynaklarını kontrol et'));reopen.id='first-use-reopen';reopen.type='button';
 const tourButton=make('button','quiet first-use-tour',text('Show the interface tour','Kısa arayüz turunu aç'));tourButton.type='button';
 const settingsBlock=make('section','first-use-settings');settingsBlock.append(make('h2','',text('Getting started','Başlangıç')),reopen,tourButton);settings.prepend(settingsBlock);
 function visibility(focus=false){
  panel.hidden=!open;document.body.dataset.setupOpen=String(open);
  if(open&&focus)heading.focus({preventScroll:true});
 }
 function finish(){open=false;saveView({setupDone:true});visibility();}
 async function sessions(){
  finish();show('sessions',true);
  window.plerUI.setFilters({days:'0',agent:'all',project:'all',quality:false,search:'',sort:'recent'});
  usageState.restore=null;usageState.pageSize=20;
  saveView({filters:{days:'0',agent:'all',project:'all',sort:'recent',quality:false}});
  await loadUsage();
 }
 primary.addEventListener('click',sessions);
 later.addEventListener('click',()=>{finish();show('sessions',true);});
 reopen.addEventListener('click',()=>{open=true;update(data);visibility(true);});
 tourButton.addEventListener('click',async()=>{await sessions();tour()?.start(usageState.data);});
 document.addEventListener('pler-screen-change',()=>{if(open){open=false;visibility();}});
 function update(value){
  data=value;
  const busy=Boolean(usageState.loading||value?.state==='scanning'||!$('usage-progress').hidden);
  const snapshot=Boolean(value?.has_snapshot),summary=value?.setup;
  const count=summary?.sessions||0,failed=value?.state==='error'||Boolean(usageState.readError);
  diagnose.hidden=!failed&&!value?.sources?.unreadable;
  for(const [agent,{row,state}] of sourceRows){
   const info=summary?.agents?.find(item=>item.agent===agent);
   const n=info?.sessions||0;
   row.dataset.state=busy?'reading':!snapshot?'unknown':n?'ready':'missing';
   state.textContent=busy?words.reading:!snapshot?text('Not read yet','Henüz okunmadı'):n?
    (info.files?text(`${n} saved sessions`,`${n} kayıtlı oturum`):text(`${n} sessions in retained history`,`${n} oturum saklanan geçmişte`)):
    info?.files?text('Files found; no usable sessions','Dosya bulundu; kullanılabilir oturum yok'):text('No records found','Kayıt bulunamadı');
  }
  manage.disabled=busy||usageState.stopped;retry.disabled=busy||usageState.stopped;retry.textContent=busy?words.reading:words.retry;
  primary.disabled=busy||!snapshot||!count||usageState.stopped;
  primary.textContent=count?text(`Explore ${count} sessions`,`${count} oturumu incele`):text('Open sessions','Oturumları aç');
  later.textContent=count?text('Continue to workspace','Çalışma alanına geç'):words.later;
  status.textContent=busy?text('Checking both sources. Large histories can take a moment.','İki kaynak kontrol ediliyor. Büyük geçmişlerde bu biraz sürebilir.'):
   failed?text('The read could not finish. Try again; any previous snapshot is kept.','Okuma tamamlanamadı. Yeniden dene; önceki kayıt görünümü korunur.'):
   value?.sources?.unreadable?text('Some records could not be read. You can explore the readable sessions; see source help for missing records.','Bazı kayıtlar okunamadı. Okunabilen oturumları inceleyebilirsin; eksikler için kaynak yardımını aç.'):
   snapshot&&count?text(`${count} sessions across ${summary.projects} projects. Open a session to see its details.`,`${summary.sessions} oturum, ${summary.projects} proje. Ayrıntıları görmek için bir oturum aç.`):
   snapshot?text('No sessions to show yet. Open the guidance below the source list, then try again.','Henüz gösterilecek oturum yok. Kaynak listesinin altındaki açıklamayı açıp yeniden dene.'):'';
  guidance.hidden=snapshot&&count>0&&!value?.sources?.unreadable;
  tourButton.disabled=busy||!snapshot||!count||usageState.stopped;
  visibility();
 }
 visibility();update(typeof usageState==='undefined'?null:usageState.data);
 return {update};
}
