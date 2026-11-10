import {animate} from 'motion';

const reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
const spring={type:'spring',stiffness:400,damping:30};
let pageEntry;
export function enterPage(page){
 // Rapid navigation must not leave multiple page entrances running behind hidden views.
 pageEntry?.cancel();pageEntry=null;
 if(!reduced())pageEntry=animate(page,{opacity:[.9,1],y:[3,0]},{duration:.18,ease:[.22,1,.36,1]});
}
const rowEntries=new Map();
export function cancelRowEntry(){
 for(const animation of rowEntries.values())animation.cancel();
 rowEntries.clear();
}
export function enterRows(rows){
 cancelRowEntry();
 if(reduced())return;
 // Virtual rows are recycled while scrolling: never translate their hit targets.
 for(const [index,row] of rows.slice(0,8).entries()){
  const animation=row.animate([{opacity:.75},{opacity:1}],{duration:140,delay:index*12,easing:'ease-out'});
  rowEntries.set(row,animation);
  animation.finished.then(()=>{if(rowEntries.get(row)===animation)rowEntries.delete(row);},()=>{});
 }
}
export function installFeedback(){
 const controls='button:not(:disabled),summary,a[href],.tabulator-row';
 document.addEventListener('pointermove',event=>{
  const surface=event.target.closest('.tabulator-row,.ws-command,.usage-rank button');if(!surface)return;
  const rect=surface.getBoundingClientRect();surface.style.setProperty('--pointer-x',`${event.clientX-rect.left}px`);surface.style.setProperty('--pointer-y',`${event.clientY-rect.top}px`);
 },{passive:true});
 document.addEventListener('pointerdown',event=>{
  const control=event.target.closest(controls);if(!control||control.closest('.ws-nav,.wb-segmented')||control.matches('.tabulator-row')||reduced())return;
  animate(control,{scale:.98},{duration:.06});
  const release=()=>{if(control.isConnected)animate(control,{scale:1},spring);};
  document.addEventListener('pointerup',release,{once:true});document.addEventListener('pointercancel',release,{once:true});
 });
 for(const dialog of document.querySelectorAll('dialog')){
  new MutationObserver(()=>{
   if(dialog.open&&!reduced()){
    if(dialog.id==='usage-session-dialog')animate(dialog,{opacity:[.75,1]},{duration:.16,ease:'easeOut'});
    else animate(dialog,{opacity:[.5,1],x:[0,0],y:[8,0]},spring);
   }
  }).observe(dialog,{attributes:true,attributeFilter:['open']});
 }
 document.addEventListener('toggle',event=>{
  if(!(event.target instanceof HTMLDetailsElement)||!event.target.open||reduced())return;
  const children=[...event.target.children].filter(child=>child.tagName!=='SUMMARY'&&!child.hidden);
  if(children.length)animate(children,{opacity:[.3,1],y:[-3,0]},spring);
 },true);
}
