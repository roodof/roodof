import './check-design.mjs';
import { build } from 'esbuild';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
// Sonner adds its stylesheet with a <style> element at import. The app's CSP allows only its own
// stylesheet files, so that injection is switched off here and sonner's CSS file is bundled below.
const noInjectedStyles = {name:'no-injected-styles', setup(context) {
  // Same CSP reason: cmdk's dialog import is replaced, see stubs/radix-dialog.js.
  context.onResolve({filter:/^@radix-ui\/react-dialog$/}, () => ({path:fileURLToPath(new URL('stubs/radix-dialog.js', import.meta.url))}));
  context.onLoad({filter:/sonner[\\/]dist[\\/]index\.mjs$/}, async args => {
    const source = await readFile(args.path, 'utf8');
    if (!source.includes('function __insertCSS(code) {')) throw new Error('sonner style injector changed; review the CSP workaround');
    return {contents: source.replace('function __insertCSS(code) {', 'function __insertCSS(code) { return;'), loader:'js'};
  });
}};
const bundled = await build({entryPoints:['workspace.js'], bundle:true, minify:true, format:'iife', target:'chrome120', outfile:'../src/pler/web/workspace.js', legalComments:'eof', metafile:true, plugins:[noInjectedStyles]});
// Every package esbuild actually bundled needs its license notice; a new dependency cannot be missed.
const packages = new Set();
for (const file of Object.keys(bundled.metafile.inputs)) {
  const match = file.replace(/\\/g,'/').match(/node_modules\/((?:@[^/]+\/)?[^/]+)/);
  if (match) packages.add(match[1]);
}
packages.add('tabulator-tables');  // its stylesheet is copied below
const notices = await Promise.all([...packages].sort().map(async name => {
  const files = ['LICENSE','LICENSE.md','LICENSE.txt','License.txt','LICENSE.md.txt'];
  for (const file of files) { try { return `${name}\n${await readFile(`node_modules/${name}/${file}`, 'utf8')}`; } catch {} }
  throw new Error(`Missing license: ${name}`);
}));
await writeFile('../src/pler/web/THIRD-PARTY.txt', notices.join('\n\n'));

await writeFile('../src/pler/web/sessions-grid.css', (await readFile('node_modules/tabulator-tables/dist/css/tabulator_simple.min.css','utf8'))+'\n'+await readFile('sessions-grid.css','utf8'));

const tokens=JSON.parse(await readFile('tokens.json','utf8'));
const declarations=Object.entries(tokens).map(([name,value])=>`  --ui-${name}: ${value};`).join('\n');
await writeFile('../src/pler/web/workspace.css', ':root{\n'+declarations+'\n}\n'+await readFile('node_modules/sonner/dist/styles.css','utf8')+'\n'+await readFile('node_modules/driver.js/dist/driver.css','utf8')+'\n'+await readFile('workspace.css','utf8')+'\n'+await readFile('premium.css','utf8'));
