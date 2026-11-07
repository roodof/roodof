import {chromium} from 'playwright';
import {readFile,rename,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const root=new URL('../../reports/sessions-grid-v3/',import.meta.url);
const log=await readFile(new URL('access.tmp',root),'utf8');const url=new URL(log.match(/http:\/\/127\.0\.0\.1:\d+\/#access=[a-f0-9]{64}/)[0]);url.search='?lang=tr';
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000},recordVideo:{dir:fileURLToPath(root),size:{width:1440,height:1000}}});
const page=await context.newPage();const video=page.video();
try {
 await page.goto(url.href);await page.waitForSelector('#sessions-grid .tabulator-row');await page.waitForTimeout(700);
 const agent=await page.locator('.tabulator-col[tabulator-field=agent]').boundingBox(),tokens=await page.locator('.tabulator-col[tabulator-field=tokens]').boundingBox();
 const order=()=>page.locator('.tabulator-header .tabulator-col[tabulator-field]').evaluateAll(cols=>cols.map(c=>c.getAttribute('tabulator-field')));
 const before=await order();
 await page.mouse.move(agent.x+35,agent.y+agent.height/2);await page.mouse.down();await page.waitForTimeout(250);await page.mouse.move(tokens.x+tokens.width-15,tokens.y+tokens.height/2,{steps:25});await page.waitForTimeout(300);await page.mouse.up();await page.waitForTimeout(700);
 const after=await order();await writeFile(new URL('column-move.json',root),JSON.stringify({before,after,moved:JSON.stringify(before)!==JSON.stringify(after)},null,2));
 await page.locator('.grid-options>summary').click();await page.waitForTimeout(600);
 await page.locator('.grid-column-menu label').filter({hasText:/^Son etkinlik$/}).locator('input').uncheck();await page.waitForTimeout(800);
 await page.locator('.grid-column-menu label').filter({hasText:/^Modeller$/}).locator('input').check();await page.waitForTimeout(900);
 await page.locator('.grid-reset').click();await page.waitForTimeout(600);await page.locator('.grid-options>summary').click();
 await page.locator('#sessions-grid .grid-project-name').first().click();await page.waitForTimeout(1000);
 await page.getByRole('button',{name:'Sonraki oturum',exact:true}).click();await page.waitForTimeout(1000);
 await page.keyboard.press('Escape');await page.locator('[data-select=usage-agent] button[data-value=codex]').click();await page.waitForTimeout(1000);
 await page.locator('#usage-session-search').fill('demo');await page.waitForTimeout(1000);
}finally{await context.close();await rename(await video.path(),fileURLToPath(new URL('interactions.webm',root)));await browser.close();}
console.log('Tabulator interaction recording saved');
