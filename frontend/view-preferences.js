import {normalizeView} from '../desktop/view-preferences.cjs';
const KEY='pler-ui-view-v1';
let state;
let serialized=null;
try{state=normalizeView(JSON.parse(sessionStorage.getItem(KEY)||new URLSearchParams(location.search).get('view')||localStorage.getItem(KEY)||'null'));}catch{state=normalizeView(null);}
export const getView=()=>normalizeView(state);
export function saveView(patch){
 state=normalizeView({...state,...patch,filters:{...state.filters,...patch.filters}});
 const value=JSON.stringify(state);
 if(value===serialized)return false;
 try{sessionStorage.setItem(KEY,value);localStorage.setItem(KEY,value);serialized=value;}catch{return false;}
 return true;
}
export function installViewPreferences(){
 const ui=window.plerUI;
 function filters(){return ui.get().restoring?state.filters:ui.get().filters;}
 window.plerGetViewPreferences=()=>normalizeView({...state,filters:filters()});
 const saveFilters=window.PlerUIState.coalesce(()=>{if(!ui.get().restoring)saveView({filters:filters()});});
 ui.subscribe(['filters','restoring'],saveFilters);
 if(!ui.get().restoring)saveView({filters:filters()});
}
