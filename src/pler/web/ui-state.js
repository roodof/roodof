// Shared runtime state for the controller and desktop views. No storage, network or credentials.
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.PlerUIState=api;})(globalThis,function(){
 'use strict';
 const screens=['sessions','work','overview','quota','settings'];
 const defaults={days:'30',agent:'all',project:'all',sort:'recent',quality:false,search:''};
 function filters(value={},previous=defaults){
  const pick=(key,allowed)=>allowed.includes(value[key])?value[key]:previous[key];
  return Object.freeze({days:pick('days',['0','7','30','90']),agent:pick('agent',['all','codex','claude-code']),
   project:typeof value.project==='string'&&/^(all|[a-f0-9]{24})$/.test(value.project)?value.project:previous.project,
   sort:pick('sort',['recent','started','tokens','issues']),quality:typeof value.quality==='boolean'?value.quality:previous.quality,
   search:typeof value.search==='string'?value.search.slice(0,160):previous.search});
 }
 function create(initial={}){
  let state=Object.freeze({filters:filters(initial.filters),screen:screens.includes(initial.screen)?initial.screen:'sessions',
   data:null,sessions:null,loading:false,restoring:false,readError:false,selection:null,work:null,quota:null,revision:0});
  const listeners=new Set();
  function publish(topic,value,force=false){
   if(!Object.hasOwn(state,topic)||topic==='revision')throw new TypeError('Unknown UI topic');
   if(topic==='filters')value=filters(value,state.filters);
   if(topic==='screen'&&!screens.includes(value))return false;
   if(!force&&(topic==='filters'?Object.keys(defaults).every(k=>state.filters[k]===value[k]):state[topic]===value))return false;
   state=Object.freeze({...state,[topic]:value,revision:state.revision+1});
   for(const row of listeners)if(row.topics.has(topic))row.callback(state,topic);
   return true;
  }
  return Object.freeze({get:()=>state,publish,
   subscribe(topics,callback){const row={topics:new Set(topics),callback};listeners.add(row);return()=>listeners.delete(row);}});
 }
 // Same-turn filter changes share one read. A later edit starts a new read;
 // the controller aborts that superseded GET and keeps mutation POSTs separate.
 function coalesce(run){let queued=null;return function(){if(queued)return queued;queued=new Promise((resolve,reject)=>queueMicrotask(()=>{queued=null;Promise.resolve().then(run).then(resolve,reject);}));return queued;};}
 return {create,filters,coalesce};
});
