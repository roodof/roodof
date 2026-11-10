import {getView,saveView} from './view-preferences.js';

// A source check, not a login wizard. Counts cover every retained session,
// independently of the currently selected agent, project or period.
export function mountFirstUse({tr,settings,show,tour}) {
 const $=id=>document.getElementById(id);
 const text=(en,local)=>tr?local:en;
 const make=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value)n.textContent=value;return n;};
 const words={
  title:text('Find your Claude Code and Codex work','Claude Code ve Codex çalışmalarını bul'),
  intro:text('Find sessions from the local records saved by Claude Code and Codex. No account connection is needed.','Claude Code ve Codex’in bu bilgisayarda tuttuğu kayıtlardan oturumlarını bul. Hesap bağlaman gerekmez.'),
  retry:text('Look for records again','Kayıtları yeniden ara'),
  reading:text('Reading local records…','Yerel kayıtlar okunuyor…'),
  later:text('Continue without records','Kayıt olmadan devam et'),
  privacy:text('No model call is made. This check does not upload your agent records. ChatGPT web conversations are not included.','Model çağrısı yapılmaz. Bu kontrol ajan kayıtlarını dışarı yüklemez. ChatGPT web sohbetleri dahil değildir.'),
  help:text('Source and WSL help','Kayıt kaynakları ve WSL yardımı')
 };
 let data=null,open=!getView().setupDone,nextAction='reading';
 const panel=make('section','first-use');panel.id='first-use';panel.setAttribute('aria-labelledby','first-use-title');
 const heading=make('h2','',words.title);heading.id='first-use-title';heading.tabIndex=-1;
 const caption=make('p','first-use-caption','Claude Code · Codex');
 const intro=make('p','first-use-intro',words.intro);
 const sources=make('div','first-use-sources');
 const status=make('p','first-use-status');status.setAttribute('role','status');status.setAttribute('aria-live','polite');
 const actions=make('div','first-use-actions');
 const primary=make('button','primary',words.reading);primary.type='button';primary.id='first-use-next';
 const sessionsButton=make('button','secondary',text('See your sessions','Oturumlarını gör'));sessionsButton.type='button';sessionsButton.id='first-use-sessions';
 const retry=make('button','secondary',words.retry);retry.type='button';retry.addEventListener('click',()=>{$('usage-refresh').click();update(data);});
 const later=make('button','quiet',words.later);later.type='button';
 const help=make('a','first-use-help',words.help);help.href='/help?lang='+(tr?'tr':'en')+'#coverage';
 const privacy=make('p','first-use-privacy',words.privacy);
 const leaveSetup=event=>{open=false;visibility();document.dispatchEvent(new CustomEvent(event));};
 const manage=make('button','secondary',text('Add a log folder','Kayıt klasörü ekle'));manage.type='button';manage.id='first-use-manage-sources';manage.addEventListener('click',()=>leaveSetup('pler-manage-sources'));
 const diagnose=make('button','quiet',text('Inspect read issues','Sorunu incele'));diagnose.type='button';diagnose.id='first-use-diagnostics';diagnose.hidden=true;diagnose.addEventListener('click',()=>leaveSetup('pler-open-diagnostics'));
 const options=make('details','first-use-options');options.id='first-use-options';
 options.append(make('summary','',text('Other options','Diğer seçenekler')));
 const optionalActions=make('div','first-use-optional-actions');optionalActions.append(sessionsButton,retry,manage,later,diagnose);options.append(optionalActions,help);
 actions.append(primary);panel.append(caption,heading,intro,sources,status,actions,options,privacy);
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
  text('If you already have sessions, check that their local records are still present and readable. Roodof can only show the records it can read.','Oturumların zaten varsa yerel kayıtlarının hâlâ bulunduğunu ve okunabildiğini kontrol et. Roodof yalnız okuyabildiği kayıtları gösterebilir.')
 ])guidance.append(make('p','',message));
 options.append(guidance);
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
 primary.addEventListener('click',()=>{
  if(nextAction==='sessions')sessions();
  else if(nextAction==='sources')leaveSetup('pler-manage-sources');
  else if(nextAction==='inspect')leaveSetup('pler-open-diagnostics');
 });
 sessionsButton.addEventListener('click',sessions);
 later.addEventListener('click',()=>{finish();show('sessions',true);});
 reopen.addEventListener('click',()=>{open=true;update(data);visibility(true);});
 tourButton.addEventListener('click',async()=>{await sessions();tour()?.start(usageState.data);});
 document.addEventListener('pler-screen-change',()=>{if(open){open=false;visibility();}});
 function update(value){
  data=value;
  const busy=Boolean(usageState.loading||value?.state==='scanning'||!$('usage-progress').hidden);
  const snapshot=Boolean(value?.has_snapshot),summary=value?.setup;
  const count=summary?.sessions||0,failed=value?.state==='error'||Boolean(usageState.readError);
  const unreadable=Boolean(value?.sources?.unreadable),files=(value?.sources?.claude_files||0)+(value?.sources?.codex_files||0);
  const issue=failed||unreadable||(snapshot&&!count&&files>0);
  nextAction=busy||(!snapshot&&!failed)?'reading':issue?'inspect':count?'sessions':'sources';
  panel.dataset.action=nextAction;
  heading.textContent=nextAction==='reading'?text('Looking for your sessions','Oturumların aranıyor'):
   nextAction==='sessions'?text('Your sessions are ready','Oturumların hazır'):
   nextAction==='sources'?text('Find your records','Kayıtlarını bulalım'):text('Check the read issue','Okuma sorununu inceleyelim');
  primary.textContent=nextAction==='reading'?words.reading:nextAction==='sessions'?text('See your sessions','Oturumlarını gör'):
   nextAction==='sources'?text('Add a log folder','Kayıt klasörü ekle'):text('Inspect the issue','Sorunu incele');
  primary.disabled=nextAction==='reading'||usageState.stopped;
  sessionsButton.hidden=nextAction==='sessions'||nextAction==='reading'||!snapshot||!count;
  sessionsButton.disabled=busy||!snapshot||!count||usageState.stopped;
  sessionsButton.textContent=issue?text('See available sessions','Bulunabilen oturumları gör'):text('See your sessions','Oturumlarını gör');
  manage.hidden=nextAction==='sources';diagnose.hidden=!issue||nextAction==='inspect';
  for(const [agent,{row,state}] of sourceRows){
   const info=summary?.agents?.find(item=>item.agent===agent);
   const n=info?.sessions||0;
   row.dataset.state=busy?'reading':!snapshot?'unknown':n?'ready':'missing';
   state.textContent=busy?words.reading:!snapshot?text('Not read yet','Henüz okunmadı'):n?
    (info.files?text(`${n} saved session${n===1?'':'s'}`,`${n} kayıtlı oturum`):text(`${n} session${n===1?'':'s'} in retained history`,`${n} oturum saklanan geçmişte`)):
    info?.files?text('Files found; no usable sessions','Dosya bulundu; kullanılabilir oturum yok'):text('No records found','Kayıt bulunamadı');
  }
  manage.disabled=busy||usageState.stopped;retry.disabled=busy||usageState.stopped;retry.textContent=busy?words.reading:words.retry;
  diagnose.disabled=busy||usageState.stopped;
  later.disabled=usageState.stopped;later.textContent=count?text('Continue to workspace','Çalışma alanına geç'):text('Skip for now','Şimdilik geç');
  status.textContent=busy?text('Checking both sources. Large histories can take a moment.','İki kaynak kontrol ediliyor. Büyük geçmişlerde bu biraz sürebilir.'):
   failed?text('The read could not finish. Inspect the issue; any previous snapshot is kept.','Okuma tamamlanamadı. Sorunu incele; varsa önceki kayıt görünümü korunur.'):
   value?.sources?.unreadable?text('Some records could not be read. Available sessions are under Other options.','Bazı kayıtlar okunamadı. Bulunabilen oturumlar Diğer seçenekler altında.'):
   snapshot&&count?text(`${count} session${count===1?'':'s'} across ${summary.projects} project${summary.projects===1?'':'s'}. Open a session to see its usage.`,`${summary.sessions} oturum, ${summary.projects} proje. Kullanımını görmek için bir oturum aç.`):
   snapshot&&files?text('Record files were found, but no usable sessions. Inspect read status to see why.','Kayıt dosyaları bulundu, fakat gösterilebilen oturum yok. Nedenini okuma durumunda incele.'):
   snapshot?text('No sessions found in the standard folders. Add the log folder if you use another installation.','Standart klasörlerde oturum kaydı bulunamadı. Farklı bir kurulum kullanıyorsan kayıt klasörünü ekle.'):'';
  guidance.hidden=snapshot&&count>0&&!value?.sources?.unreadable;
  tourButton.disabled=busy||!snapshot||!count||usageState.stopped;
  visibility();
 }
 visibility();update(typeof usageState==='undefined'?null:usageState.data);
 return {update};
}
