'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {create,coalesce}=require('../src/pler/web/ui-state.js');
test('one canonical filter patch gives one notification; unchanged values are silent',()=>{
 const store=create();let calls=0;store.subscribe(['filters'],state=>{calls++;assert.equal(state.filters.agent,'codex');assert.equal(state.filters.days,'7');});
 assert.equal(store.publish('filters',{agent:'codex',days:'7'}),true);assert.equal(calls,1);
 assert.equal(store.publish('filters',{agent:'codex',days:'7'}),false);assert.equal(calls,1);
 assert.equal(store.get().filters.project,'all');assert.ok(Object.isFrozen(store.get().filters));
});
test('only supported screens and bounded filter fields enter runtime state',()=>{
 const store=create();store.publish('filters',{agent:'bad',days:'bad',project:'private/path',search:'x'.repeat(500),quality:'yes',token:'private'});
 assert.equal(store.get().filters.search.length,160);assert.equal(store.get().filters.agent,'all');assert.equal(store.get().filters.quality,false);assert.equal(store.get().filters.token,undefined);
 assert.equal(store.publish('screen','private/path'),false);assert.equal(store.get().screen,'sessions');assert.throws(()=>store.publish('token','private'));
});
test('topics and unsubscribe isolate consumers; restored snapshot data does not get copied',()=>{
 const store=create();let events=0;const remove=store.subscribe(['data'],()=>events++);const data={sessions:[]};
 store.publish('loading',true);assert.equal(events,0);store.publish('data',data);assert.equal(store.get().data,data);remove();store.publish('data',{});assert.equal(events,1);
});
test('same-turn changes coalesce; a later mutation still gets a new read',async()=>{
 let calls=0;const run=coalesce(()=>++calls);const a=run(),b=run(),c=run();assert.equal(a,b);assert.equal(b,c);assert.equal(await a,1);assert.equal(await run(),2);assert.equal(calls,2);
});
test('a rejected read does not poison the next queued read',async()=>{
 let fail=true;const run=coalesce(()=>{if(fail)throw new Error('invented');return 7;});await assert.rejects(run(),/invented/);fail=false;assert.equal(await run(),7);
});
