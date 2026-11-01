'use strict';
// Exercise the shipped UI with synthetic server projections; no browser or dependencies.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test');
const source=fs.readFileSync(require('node:path').join(__dirname,'../src/pler/web/app.js'),'utf8');
const table=JSON.parse(source.split('/*I18N*/')[1].split('/*END*/')[0]);
const code=source.slice(source.indexOf('function renderCoverageGuidance('),source.indexOf('function restoreUsageSelection('));
function element(tag='div',cls='',text=''){
  return {tag,className:cls,textContent:text,children:[],hidden:false,
    append(...items){this.children.push(...items);},replaceChildren(...items){this.children=[...items];}};
}
function page(data,lang='en'){
  const elements={};
  for(const id of ['usage-data-guidance','usage-data-guidance-items','usage-coverage-help',
    'usage-quality-details','usage-quality','usage-quality-show'])elements[id]=element();
  const context=vm.createContext({I18N:table,LANG:lang,$:id=>elements[id],number:String,
    t:(key,values={})=>table[lang][key].replace(/\{(\w+)\}/g,(_,k)=>values[k]),
    node:element,document:{createTextNode:text=>({tag:'#text',textContent:text})},
    sessionHasQualityLimits:session=>session.quality?.tokens_complete===false});
  vm.runInContext(code,context);context.renderCoverageGuidance(data);
  return {elements,context};
}
const base={has_snapshot:true,sessions:[],quality:{issues:[]},coverage:{notices:[]}};
test('an access failure with zero sessions remains visible without an empty affected-session action',()=>{
  const p=page({...base,coverage:{notices:[{code:'source_access'}]}});
  assert.equal(p.elements['usage-data-guidance'].hidden,false);
  assert.equal(p.elements['usage-data-guidance-items'].children.length,1);
  assert.equal(p.elements['usage-quality-show'].hidden,true);
  assert.equal(p.elements['usage-quality-details'].hidden,true);
});
test('old-reader history offers preservation instead of a destructive repair control',()=>{
  const p=page({...base,quality_affected_sessions:2,quality:{issues:[{detail:'old interpretation'}]},
    coverage:{notices:[{code:'archive_old_parser'},{code:'retained_history'}]}});
  const rows=p.elements['usage-data-guidance-items'].children;
  assert.equal(rows.length,2);
  assert.match(rows[0].children[2].children[1].textContent,/preserve the archive/);
  assert.match(rows[1].children[2].children[1].textContent,/cannot recreate deleted originals/);
  assert.equal(rows.flatMap(row=>row.children).some(node=>['button','input'].includes(node.tag)),false);
  assert.equal(p.elements['usage-quality-show'].hidden,false);
  assert.match(p.elements['usage-quality-show'].textContent,/2/);
  assert.equal(p.elements['usage-quality'].textContent,'old interpretation');
});
test('both languages render translated effects and steps, with matching offline help links',()=>{
  for(const lang of ['en','tr']){
    const p=page({...base,coverage:{notices:[{code:'wsl_unavailable'}]}},lang);
    const row=p.elements['usage-data-guidance-items'].children[0];
    assert.equal(row.children[0].textContent,table[lang].coverage_wsl_unavailable_title);
    assert.equal(row.children[1].textContent,table[lang].coverage_wsl_unavailable_impact);
    assert.equal(row.children[2].children[1].textContent,table[lang].coverage_wsl_unavailable_next);
    assert.equal(p.elements['usage-coverage-help'].href,'/help?lang='+lang+'#coverage');
  }
});
test('a successful later read removes obsolete guidance and quality details',()=>{
  const p=page({...base,coverage:{notices:[{code:'source_access'}]},
    quality:{issues:[{detail:'previous warning'}]},quality_affected_sessions:1});
  p.context.renderCoverageGuidance(base);
  assert.equal(p.elements['usage-data-guidance'].hidden,true);
  assert.equal(p.elements['usage-data-guidance-items'].children.length,0);
  assert.equal(p.elements['usage-quality'].textContent,'');
  assert.equal(p.elements['usage-quality-show'].hidden,true);
});
test('future unknown notice codes do not inject server-supplied descriptions or HTML',()=>{
  const p=page({...base,coverage:{notices:[{code:'<script>private</script>',title:'PRIVATE'}, {code:'source_access'}]}});
  assert.equal(p.elements['usage-data-guidance-items'].children.length,1);
  assert.equal(JSON.stringify(p.elements).includes('PRIVATE'),false);
});
test('an initial or failed read without a snapshot does not present an invented coverage result',()=>{
  const p=page({...base,has_snapshot:false,coverage:{notices:[{code:'source_access'}]}});
  assert.equal(p.elements['usage-data-guidance'].hidden,true);
});
