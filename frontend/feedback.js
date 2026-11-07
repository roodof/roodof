import {animate,stagger} from 'motion';

const reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
const spring={type:'spring',stiffness:400,damping:30};
export function enterPage(page){
 if(!reduced())animate(page,{opacity:[.35,1],y:[4,0]},{...spring,visualDuration:.22});
}
export function enterRows(rows){
 if(!reduced()&&rows.length)animate(rows.slice(0,8),{opacity:[.45,1],y:[4,0]},{...spring,delay:stagger(.04)});
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
   if(dialog.open&&!reduced())animate(dialog,{opacity:[.5,1],x:dialog.id==='usage-session-dialog'?[18,0]:[0,0],y:dialog.id==='usage-session-dialog'?[0,0]:[8,0]},spring);
  }).observe(dialog,{attributes:true,attributeFilter:['open']});
 }
 document.addEventListener('toggle',event=>{
  if(!(event.target instanceof HTMLDetailsElement)||!event.target.open||reduced())return;
  const children=[...event.target.children].filter(child=>child.tagName!=='SUMMARY'&&!child.hidden);
  if(children.length)animate(children,{opacity:[.3,1],y:[-3,0]},spring);
 },true);
}
