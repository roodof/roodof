import {chromium} from 'playwright';
import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const root=new URL('../../reports/design-foundation-v1/',import.meta.url);
const address=(await readFile(new URL('access.tmp',root),'utf8')).match(/http:\/\/127\.0\.0\.1:\d+\/#access=[a-f0-9]{64}/)[0];
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1440,height:960}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(address);await page.waitForSelector('#sessions-grid .tabulator-row');await page.waitForTimeout(800);
 await page.locator('#lang-toggle').click();await page.waitForSelector('html[lang=tr]');await page.waitForSelector('#sessions-grid .tabulator-row');await page.waitForTimeout(600);
 for(const screen of ['sessions','work','overview','quota','settings']){await page.locator(`[data-route=${screen}]`).click();await page.waitForTimeout(650);await page.screenshot({path:fileURLToPath(new URL(screen+'.png',root)),fullPage:true});}
 await page.locator('[data-route=sessions]').click();await page.locator('.grid-project-name').first().click();await page.waitForTimeout(650);await page.screenshot({path:fileURLToPath(new URL('inspector.png',root))});
 await page.keyboard.press('Escape');await page.keyboard.press('Control+k');await page.waitForTimeout(400);await page.screenshot({path:fileURLToPath(new URL('command.png',root))});await page.keyboard.press('Escape');
 await page.setViewportSize({width:1100,height:720});await page.waitForTimeout(300);await page.screenshot({path:fileURLToPath(new URL('laptop.png',root))});
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);await page.screenshot({path:fileURLToPath(new URL('narrow.png',root)),fullPage:true});
 console.log(JSON.stringify({errors,width:await page.evaluate(()=>({viewport:innerWidth,scroll:document.documentElement.scrollWidth})),background:await page.evaluate(()=>getComputedStyle(document.body).backgroundColor),rowHeight:await page.locator('.tabulator-row').first().evaluate(e=>e.getBoundingClientRect().height)}));
 await writeFile(new URL('probe.json',root),JSON.stringify({errors},null,2));
}finally{await browser.close();}
