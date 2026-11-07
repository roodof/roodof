import './check-design.mjs';
import { build } from 'esbuild';
import { readFile, writeFile } from 'node:fs/promises';
await build({entryPoints:['workspace.js'], bundle:true, minify:true, format:'iife', target:'chrome120', outfile:'../src/pler/web/workspace.js', legalComments:'eof'});
const notices = await Promise.all(['motion','framer-motion','motion-dom','motion-utils','echarts','lucide','zrender','tslib','tabulator-tables','react','react-dom','scheduler'].map(async name => {
  const files = ['LICENSE','LICENSE.md','LICENSE.txt','License.txt','LICENSE.md.txt'];
  for (const file of files) { try { return `${name}\n${await readFile(`node_modules/${name}/${file}`, 'utf8')}`; } catch {} }
  throw new Error(`Missing license: ${name}`);
}));
await writeFile('../src/pler/web/THIRD-PARTY.txt', notices.join('\n\n'));

await writeFile('../src/pler/web/sessions-grid.css', (await readFile('node_modules/tabulator-tables/dist/css/tabulator_simple.min.css','utf8'))+'\n'+await readFile('sessions-grid.css','utf8'));

const tokens=JSON.parse(await readFile('tokens.json','utf8'));
const declarations=Object.entries(tokens).map(([name,value])=>`  --ui-${name}: ${value};`).join('\n');
await writeFile('../src/pler/web/workspace.css', ':root{\n'+declarations+'\n}\n'+await readFile('workspace.css','utf8'));
