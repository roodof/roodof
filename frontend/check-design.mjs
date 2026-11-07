import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const root=new URL('./',import.meta.url);
const read=name=>readFile(new URL(name,root),'utf8');
const [tokens,css,grid,design,primitives,feedback]=await Promise.all([read('tokens.json').then(JSON.parse),read('workspace.css'),read('sessions-grid.css'),read('../DESIGN.md'),read('primitives.jsx'),read('feedback.js')]);
for(const [key,value] of Object.entries(tokens))assert.ok(design.includes(`  ${key}: "${value}"`),`DESIGN.md differs from token ${key}`);
for(const [name,source] of [['workspace.css',css],['sessions-grid.css',grid]]){
 assert.ok(!/#[\da-f]{3,8}\b/i.test(source),`${name} has a hard-coded color outside tokens.json`);
 assert.ok(!/shadow-(?:lg|xl)|\bp-(?:8|10)\b|(?:purple|indigo|fuchsia|magenta)/i.test(source),`${name} violates a design exclusion`);
 assert.ok(!/box-shadow\s*:\s*(?!inset)[^;{}]*\b(?:30|40|50|60|90)px/i.test(source),`${name} has a heavy drop shadow`);
}
assert.match(css,/\.workspace-redesign \.usage-panel,\.workspace-redesign \.task-section\{padding:16px/);
assert.match(css,/:focus-visible/);assert.match(css,/font-variant-numeric:tabular-nums/);
assert.match(primitives,/layoutId="active-route"/);assert.match(primitives,/layoutId="active-segment"/);
assert.match(primitives,/stiffness:400, damping:30/);assert.match(primitives,/reducedMotion="user"/);
assert.match(feedback,/prefers-reduced-motion: reduce/);assert.match(css,/prefers-reduced-motion:reduce/);
const luminance=hex=>{const c=hex.slice(1).match(/../g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return .2126*c[0]+.7152*c[1]+.0722*c[2];};
const ratio=(a,b)=>{const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);};
const contrast={};for(const text of ['text','secondary','muted'])for(const bg of ['canvas','surface','selected']){const value=ratio(tokens[text],tokens[bg]);contrast[text+'/'+bg]=+value.toFixed(2);assert.ok(value>=4.5,`Text contrast ${text}/${bg}: ${value}`);}
assert.ok(ratio(tokens['primary-fg'],tokens['primary-bg'])>=4.5);
console.log(JSON.stringify({design_contract:'passed',token_count:Object.keys(tokens).length,normal_text_contrast:contrast}));
