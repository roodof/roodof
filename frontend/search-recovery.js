// Recovery actions broaden one constraint at a time. They never change source files.
export function mountSearchRecovery({tr}){
 const $=id=>document.getElementById(id),ui=window.plerUI;
 const text=(local,en)=>tr?local:en;
 const el=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value)n.textContent=value;return n;};
 const configs=[['search',$('usage-search-empty')],['empty',$('usage-empty')]];
 const host=$('sessions-grid'),footer=document.querySelector('.grid-footer');
 host.before($('usage-search-empty'));
 for(const [prefix,card] of configs){
  const heading=card.querySelector('h2')||el('h3');heading.id=prefix+'-recovery-title';heading.tabIndex=-1;
  const note=card.querySelector('p')||el('p');note.className='search-recovery-note';
  const scope=el('p','search-recovery-scope');scope.id=prefix+'-recovery-scope';
  const actions=el('div','search-recovery-actions'),more=el('details','search-recovery-more');
  more.append(el('summary','',text('Diğer seçenekler','Other options')));const other=el('div','search-recovery-actions');more.append(other);
  const clear=prefix==='search'?$('usage-search-clear'):null,reset=prefix==='empty'?$('usage-filter-clear'):null;
  const buttons={};
  const labels={period:text('Tüm dönemlerde ara','Search all time'),quality:text('Kayıt durumu filtresini kaldır','Remove record-status filter'),
   project:text('Tüm projelerde ara','Search all projects'),agent:text('İki ajanda ara','Search both agents'),
   clear:text('Aramayı temizle','Clear search'),source:text('Kayıt klasörü ekle','Add a log folder'),
   inspect:text('Okuma sorununu incele','Inspect read issues'),retry:text('Yeniden dene','Try again'),refresh:text('Kayıtları yeniden oku','Read records again')};
  for(const kind of Object.keys(labels)){
   const button=kind==='clear'&&clear?clear:el('button','secondary',labels[kind]);button.type='button';button.className='secondary';button.textContent=labels[kind];button.dataset.recoveryAction=kind;
   if(!button.id)button.id=prefix+'-recovery-'+kind;buttons[kind]=button;
   if(kind==='clear'&&clear)continue; // the controller owns the existing clear action
   button.addEventListener('click',async()=>{
    if(kind==='source')return document.dispatchEvent(new CustomEvent('pler-manage-sources'));
    if(kind==='inspect')return document.dispatchEvent(new CustomEvent('pler-open-diagnostics'));
    if(kind==='refresh'){const original=$('usage-refresh');if(!original.disabled)original.click();return;}
    if(kind==='clear'){ui.setFilters({search:''});usageState.pageSize=20;renderUsageSessions();}
    else if(kind!=='retry'){
     const patches={period:{days:'0'},quality:{quality:false},project:{project:'all'},agent:{agent:'all'}};
     ui.setFilters(patches[kind]);usageState.pageSize=20;
     if(kind==='quality')renderUsageSessions();else await loadUsage();
    }else await loadUsage();
    const input=$('usage-session-search');if(input.offsetParent)input.focus({preventScroll:true});else heading.focus({preventScroll:true});
   });
  }
  if(reset){reset.textContent=text('Tüm filtreleri temizle','Clear all filters');reset.className='secondary';}
  card.replaceChildren(heading,note,scope,actions,more);card.classList.add('search-recovery');card.setAttribute('aria-labelledby',heading.id);
  if(clear)other.append(clear);if(reset)other.append(reset); // retain controller-owned IDs before the first snapshot
  card.setAttribute('aria-describedby',scope.id);
  function update(){
   const state=ui.get(),data=state.data;if(!data?.has_snapshot)return;
   // A new projection is committed before data. Wait for its matching snapshot.
   if(data!==usageState.data)return;
   const f=state.filters,selected=data.filters||{},mismatch=Number(f.days)!==selected.days||f.agent!==selected.agent||f.project!==selected.project;
   const busy=state.loading||data.state==='scanning'||state.restoring||(!state.readError&&mismatch),failed=state.readError;
   const all=data.setup?.sessions??data.totals.sessions,files=(data.sources.claude_files||0)+(data.sources.codex_files||0),unreadable=Boolean(data.sources.unreadable);
   const hasQuery=Boolean(f.search.trim()),noRecords=all===0;
   const active=[...(f.days!=='0'?['period']:[]),...(f.quality?['quality']:[]),...(f.project!=='all'?['project']:[]),...(f.agent!=='all'?['agent']:[]),...(hasQuery?['clear']:[])];
   const candidates=failed?['retry','inspect']:
    noRecords&&unreadable?['inspect',...(!data.demo?['source']:[]),'refresh']:
    noRecords&&!files?[...(!data.demo?['source']:[]),'refresh',...active]:
    noRecords?['inspect',...(!data.demo?['source']:[]),'refresh']:
    [...active,...(!data.demo?['source']:[]),...(unreadable?['inspect']:[]),'refresh'];
   const unique=[...new Set(candidates)];
   if(reset)reset.hidden=!active.length;
   heading.textContent=busy?text('Sonuçlar güncelleniyor…','Updating results…'):failed?text('Sonuçlar okunamadı','Could not read results'):
    noRecords&&unreadable?text('Bazı kayıtlar okunamadı','Some records could not be read'):
    noRecords&&!files?text('Henüz oturum kaydı bulunamadı','No session records found yet'):noRecords?text('Gösterilebilen oturum yok','No usable sessions to show'):
    hasQuery?text('Bu aramada oturum bulunamadı','No sessions match this search'):text('Bu filtrelerde oturum bulunamadı','No sessions match these filters');
   note.textContent=failed?text('Seçimin korunuyor. Yeniden deneyebilir veya okuma sorununu inceleyebilirsin.','Your selection is kept. Try again or inspect the read issue.'):
    noRecords&&unreadable?text('Eksik kayıtların nedenini incele; klasör erişimini düzelttikten sonra yeniden oku.','Inspect why records are missing, then read again after fixing folder access.'):
    noRecords&&!files?text('Roodof bu bilgisayardaki Claude Code ve Codex kayıtlarını okur. Başka bir kurulum kullanıyorsan kayıt klasörünü ekle.','Roodof reads Claude Code and Codex records on this computer. Add the log folder if you use another installation.'):
    noRecords?text('Kayıt dosyaları bulundu. Kullanılabilir oturum çıkmamasının nedenini okuma durumunda incele.','Record files were found. Inspect read status to see why no usable sessions were available.'):
    f.days!=='0'?text('Dönemi genişleterek devam et. Arama metnin, ajan ve proje seçimin korunur.','Widen the period to continue. Your search text, agent and project stay selected.'):
    text('Bir filtreyi genişletebilir veya arama metnini değiştirebilirsin. Başka bir kurulumdaki kayıtlar için klasör ekle.','Broaden a filter or change your search text. Add a folder for records from another installation.');
   const project=$('usage-project').selectedOptions[0]?.textContent||text('Tüm projeler','All projects');
   const period=f.days==='0'?text('Tüm dönemler','All time'):text('Son '+f.days+' gün','Last '+f.days+' days');
   scope.textContent=[period,f.agent==='all'?text('İki ajan','Both agents'):f.agent==='codex'?'Codex':'Claude Code',project,...(f.quality?[text('Sınırlı kayıtlar','Limited records')]:[])].join(' · ');
   // Keep focusable buttons mounted; only move them when the action order actually changes.
   const primary=unique.slice(0,2),remaining=unique.slice(2);
   if(actions.dataset.order!==primary.join(',')){actions.replaceChildren(...primary.map(key=>buttons[key]));actions.dataset.order=primary.join(',');}
   const parkedClear=clear&&!unique.includes('clear');if(clear)clear.hidden=Boolean(parkedClear);
   const resetVisible=Boolean(reset&&active.length);
   const rest=[...remaining.map(key=>buttons[key]),...(parkedClear?[clear]:[]),...(reset?[reset]:[])];
   const restOrder=remaining.join(',')+'|'+parkedClear+'|'+resetVisible;
   if(other.dataset.order!==restOrder){other.replaceChildren(...rest);other.dataset.order=restOrder;}
   more.hidden=!remaining.length&&!resetVisible;
   for(const [kind,button] of Object.entries(buttons)){button.disabled=busy||usageState.stopped;button.className=kind===unique[0]?'primary':'secondary';}
   if(reset)reset.disabled=busy||usageState.stopped;
   card.setAttribute('aria-busy',String(busy));
   if(prefix==='search'){const empty=state.sessions?.total===0;host.hidden=empty;if(footer)footer.hidden=empty;}
  }
  ui.subscribe(['data','sessions','filters','loading','readError','restoring'],update);update();
 }
}
