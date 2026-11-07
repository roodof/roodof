const test=require('node:test'),assert=require('node:assert/strict');
const {normalizeView}=require('./view-preferences.cjs');
const wanted={screen:'quota',filters:{days:'7',agent:'codex',project:'a'.repeat(24),sort:'tokens',quality:true},columns:[{field:'tokens',width:177,visible:true},{field:'project',width:470,visible:true},{field:'models',width:234,visible:false}]};
test('view choices preserve their order, visibility, preferred widths and filters',()=>{
 assert.deepEqual(normalizeView(wanted),wanted);assert.deepEqual(normalizeView(normalizeView(wanted)),wanted);
});
test('only bounded layout choices enter the durable record',()=>{
 const value=normalizeView({...wanted,access:'secret',draft:'private work',filters:{...wanted.filters,path:'private',search:'prompt text'},columns:[{field:'project',visible:false,width:999999,title:'private'}, {field:'project',width:300},{field:'tokens',width:NaN},{field:'secret',width:400}]});
 assert.deepEqual(value.columns,[{field:'project',visible:true},{field:'tokens',visible:true}]);
 assert.ok(!/secret|private|draft|search|title|access/.test(JSON.stringify(value)));
});
test('corrupt, future and oversized preferences fall back to usable defaults',()=>{
 for(const raw of [null,42,'wrong',[],{screen:'__proto__',filters:{days:'365',agent:'other',project:'C:/private',sort:'random',quality:'true'},columns:Array(100).fill({field:'project'})}]){
  const value=normalizeView(raw);assert.equal(value.screen,'sessions');assert.equal(value.filters.days,'30');assert.equal(value.filters.project,'all');assert.deepEqual(value.columns,[]);
 }
});
