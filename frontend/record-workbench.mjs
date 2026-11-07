import {chromium} from 'playwright';
import {readFile,rename} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const root=new URL('../../reports/workbench-v2/',import.meta.url);
const log=await readFile(new URL('access.tmp',root),'utf8');
const address=new URL(log.match(/http:\/\/127\.0\.0\.1:\d+\/#access=[a-f0-9]{64}/)[0]);address.search='?lang=tr';
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:900},recordVideo:{dir:fileURLToPath(root),size:{width:1440,height:900}}});
const page=await context.newPage();const video=page.video();
try {
 await page.goto(address.href);await page.waitForSelector('#usage-sessions tr');await page.waitForTimeout(900);
 await page.locator('[data-select="usage-agent"] button[data-value="codex"]').click();await page.waitForTimeout(1100);
 await page.locator('[data-select="usage-agent"] button[data-value="all"]').click();await page.waitForTimeout(900);
 await page.locator('#usage-sessions tr').nth(0).locator('td').first().click();await page.waitForTimeout(1400);
 await page.getByRole('button',{name:'Sonraki oturum',exact:true}).click();await page.waitForTimeout(1000);
 await page.getByRole('button',{name:'Sonraki oturum',exact:true}).click();await page.waitForTimeout(1000);
 await page.locator('.verdict-dialog button').first().click();await page.waitForTimeout(1300);
 await page.keyboard.press('Escape');await page.waitForTimeout(500);
 await page.locator('#usage-session-search').fill('shop');await page.waitForTimeout(1000);
 await page.locator('#usage-session-search').fill('');await page.waitForTimeout(700);
 await page.keyboard.press('Control+k');await page.waitForTimeout(800);
 await page.locator('.ws-palette input').fill('İş');await page.waitForTimeout(600);await page.locator('.ws-command').click();await page.waitForTimeout(1000);
} finally {await context.close();await rename(await video.path(),fileURLToPath(new URL('interactions.webm',root)));await browser.close();}
console.log('Real interaction recording saved');
