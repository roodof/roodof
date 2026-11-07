import {normalizeView} from '../desktop/view-preferences.cjs';
const KEY='pler-ui-view-v1';
let state;
try{state=normalizeView(JSON.parse(sessionStorage.getItem(KEY)||new URLSearchParams(location.search).get('view')||localStorage.getItem(KEY)||'null'));}catch{state=normalizeView(null);}
export const getView=()=>normalizeView(state);
export function saveView(patch){
 state=normalizeView({...state,...patch,filters:{...state.filters,...patch.filters}});
 const value=JSON.stringify(state);
 try{sessionStorage.setItem(KEY,value);localStorage.setItem(KEY,value);}catch{}
}
export function installViewPreferences(){
 const $=id=>document.getElementById(id);
 function filters(){return {days:$('usage-period').value,agent:$('usage-agent').value,project:$('usage-project').value||state.filters.project,sort:$('usage-session-sort').value,quality:$('usage-quality-only').checked};}
 window.plerGetViewPreferences=()=>normalizeView({...state,filters:filters()});
 for(const id of ['usage-period','usage-agent','usage-project','usage-session-sort','usage-quality-only'])$(id).addEventListener('change',()=>saveView({filters:filters()}));
 // Also capture controller actions such as clearing filters and a removed project fallback.
 new MutationObserver(()=>{if(!usageState.restore)saveView({filters:filters()});}).observe($('usage-project'),{childList:true});
}
