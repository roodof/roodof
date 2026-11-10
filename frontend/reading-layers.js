// Original information lives in a dedicated destination; no content is discarded.
export function mountReadingLayers({tr,pages,show}){
 const text=(local,en)=>tr?local:en;
 const make=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value)n.textContent=value;return n;};
 const review=pages.review,nav=make('nav','review-index');nav.setAttribute('aria-label',text('İnceleme bölümleri','Review sections'));review.append(nav);
 // Presentation only: a page index that follows the reader, and chapters with nothing to show stay out of the way.
 review.classList.add('review-page');nav.append(make('span','review-index-title',text('Bu sayfada','On this page')));
 const chapters=[];let hold=0,queued=false;
 const mark=current=>{for(const item of chapters){if(item.section===current)item.link.setAttribute('aria-current','location');else item.link.removeAttribute('aria-current');}};
 const spy=()=>{queued=false;const open=chapters.filter(item=>!item.section.hidden);if(!open.length||Date.now()<hold)return;if(!review.offsetParent){mark(open[0].section);return;}
  const end=innerHeight+scrollY>=document.documentElement.scrollHeight-4;mark((end?open[open.length-1]:open.filter(item=>item.section.getBoundingClientRect().top<=140).pop()||open[0]).section);};
 addEventListener('scroll',()=>{if(!queued){queued=true;requestAnimationFrame(spy);}},{passive:true});
 function chapter(id,label){const section=make('section','review-chapter');section.id=id;section.append(make('h2','',label));review.append(section);const link=make('a','',label);link.href='#'+id;link.append(make('span','review-count'));nav.append(link);chapters.push({section,link});
  link.addEventListener('click',event=>{event.preventDefault();hold=Date.now()+900;mark(section);section.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});});return section;}
 chapter('review-quality',text('Kapsam ve uyarılar','Coverage & warnings')).append(document.querySelector('.ws-coverage'),document.getElementById('usage-coverage'));
 chapter('review-observations',text('Kayıt gözlemleri','Record observations')).append(document.getElementById('usage-insights'));
 chapter('review-time',text('Zaman kapsamı','Time coverage')).append(document.getElementById('usage-dated'));
 const calculations=chapter('review-calculations',text('Hesaplama yöntemi','Calculation method')),charts=chapter('review-charts',text('Grafik rehberi','Chart guide'));
 for(const heading of pages.overview.querySelectorAll('.ws-chart-heading>div:first-child,.ws-rhythm>div:first-child')){
  const notes=[...heading.querySelectorAll(':scope>p.section-note')];if(!notes.length)continue;const item=make('div','review-explanation');item.append(make('h3','',heading.querySelector('h2,h3')?.textContent||''),...notes);charts.append(item);
 }
 const entry=make('button','review-entry');entry.type='button';entry.addEventListener('click',()=>show('review',true));pages.overview.prepend(entry);
 return {update(data){
  if(!data)return;
  const warnings=document.querySelectorAll('#usage-insights .usage-insight.warn').length,count=(data.coverage?.notices?.length||0)+(data.quality?.issues?.length||0)+warnings;
  entry.textContent=count?count+' '+text('kayıt uyarısı · İncele →','record warnings · Review →'):text('Kayıt incelemesi →','Record review →');entry.classList.toggle('has-warnings',count>0);
  const notes=[];
  for(const [index,card] of [...document.querySelectorAll('#usage-totals .usage-stat')].entries()){
   const note=card.querySelector(':scope>small:not(.reading-price-state)');if(!note?.textContent||index===3)continue;
   if(index===4){const priced=make('small','reading-price-state',text('Fatura değil','Not a bill')),share=data.totals?.api_priced_share;if(typeof share==='number'&&share<.9995)priced.textContent=Number(share).toLocaleString(tr?'tr-TR':'en-US',{style:'percent',maximumFractionDigits:1})+' '+text('fiyatlandı · Fatura değil','priced · Not a bill');note.before(priced);}
   const item=make('div','review-explanation');item.append(make('h3','',card.querySelector(':scope>span').textContent),note);notes.push(item);
  }
  if(notes.length){calculations.querySelectorAll('.review-explanation').forEach(n=>n.remove());calculations.append(...notes);}
  for(const item of chapters){const empty=![...item.section.children].some(n=>n.tagName!=='H2'&&!n.hidden&&(n.childElementCount||n.textContent.trim()));item.section.hidden=empty;item.link.hidden=empty;}
  const totalObservations=document.querySelectorAll('#usage-insights .usage-insight').length;
  const observationCount=totalObservations?(String(totalObservations)+(warnings?' · '+warnings+' '+text('uyarı','warnings'):'')):'';
  const counts=[document.querySelectorAll('#usage-data-guidance:not([hidden]) #usage-data-guidance-items>li').length,observationCount];
  counts.forEach((value,index)=>{chapters[index].link.lastChild.textContent=value?String(value):'';});
  hold=0;spy();
 }};
}
