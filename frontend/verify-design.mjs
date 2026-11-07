import {chromium} from 'playwright';
import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=new URL('../../reports/design-foundation-v1/',import.meta.url);
const address=(await readFile(new URL('access.tmp',root),'utf8')).match(/http:\/\/127\.0\.0\.1:\d+\/#access=[a-f0-9]{64}/)[0];
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const context=await browser.newContext({viewport:{width:1366,height:900},reducedMotion:'reduce'});
 const page=await context.newPage(),errors=[],remote=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url())&&!r.url().startsWith(new URL(address).origin))remote.push(r.url());});
 await page.goto(address);await page.waitForSelector('#sessions-grid .tabulator-row');
 assert.equal(await page.locator('#usage-sessions').isVisible(),false);
 assert.equal(await page.locator('#usage-export').isVisible(),false);
 // A maximum outside the first loaded page must still sort to the top.
 const maximum=await page.evaluate(()=>{
  const original=structuredClone(usageState.data.sessions[0]),rows=[];
  for(let i=0;i<41;i++){const s=structuredClone(original);s.id=i.toString(16).padStart(64,'0');s.ended=new Date(Date.now()-i*3600000).toISOString();s.total_tokens=i===40?99999999:i+1;rows.push(s);}
  usageState.data.sessions=rows;usageState.pageSize=20;$('usage-session-sort').value='recent';renderUsageSessions();return rows[40].id;
 });
 await page.waitForFunction(()=>document.querySelectorAll('#sessions-grid .tabulator-row').length>0);
 await page.locator('#usage-session-sort').selectOption('tokens');
 await page.waitForFunction(id=>document.querySelector('#sessions-grid .tabulator-row')?.dataset.sessionId===id,maximum);
 await page.locator('.tabulator-col[tabulator-field=tokens]').click();
 assert.equal(await page.locator('#usage-session-sort').inputValue(),'tokens');
 assert.equal(await page.locator('.tabulator-row').first().getAttribute('data-session-id'),maximum);
 await page.reload();await page.waitForSelector('#sessions-grid .tabulator-row');
 // A real saved work label makes a session recognizable and searchable.
 await page.locator('[data-route=work]').click();await page.locator('#usage-work-create-title').fill('API yayını');await page.locator('#usage-work-create').click();
 await page.waitForFunction(()=>!usageState.workBusy&&selectedWork()?.title==='API yayını');
 assert.equal(await page.locator('#notice').getAttribute('data-kind'),'success');
 await page.locator('.wb-add-sessions').click();await page.waitForFunction(()=>document.body.dataset.screen==='sessions');
 assert.ok(await page.locator('.wb-link-banner').isVisible());
 const first=await page.locator('.tabulator-row').first().getAttribute('data-session-id');
 await page.locator('.grid-project-name').first().click();
 assert.ok(await page.locator('.wb-session-identity').isVisible());
 assert.equal(await page.locator('#usage-session-work-select').inputValue(),await page.evaluate(()=>selectedWork().id));
 await page.locator('#usage-session-work-link').click();
 await page.waitForFunction(id=>!usageState.workBusy&&selectedWork()?.session_ids.includes(id),first);
 await page.keyboard.press('Escape');
 await page.locator('#usage-session-search').fill('API yayını');await page.waitForFunction(()=>document.querySelectorAll('#sessions-grid .tabulator-row').length===1);
 assert.equal(await page.locator('.grid-project-name').first().textContent(),'API yayını');
 await page.locator('#usage-session-search').fill('');await page.waitForFunction(()=>document.querySelectorAll('#sessions-grid .tabulator-row').length>1);
 // Optional review remains authenticated and does not pretend a failed save worked.
 await page.locator('.grid-options>summary').click();await page.locator('.grid-column-menu label').filter({hasText:/^Review$/}).locator('input').check();await page.locator('.grid-options>summary').click();
 await page.locator('.grid-review').first().selectOption('useful');await page.waitForFunction(id=>usageState.data.sessions.find(s=>s.id===id)?.verdict==='useful',first);
 await page.route('**/api/usage/verdict*',r=>r.fulfill({status:500,contentType:'application/json',body:'{"error":"Fixture refusal"}'}));
 await page.locator('.grid-review').first().selectOption('wasted');await page.waitForFunction(()=>!usageState.verdictSaving&&$('notice').textContent==='Fixture refusal');
 assert.equal(await page.locator('.grid-review').first().inputValue(),'useful');
 await page.unroute('**/api/usage/verdict*');await page.evaluate(()=>notice(''));
 await page.locator('.grid-options>summary').click();await page.locator('.grid-reset').click();await page.locator('.grid-options>summary').click();
 // The same identity remains visible while the inspector opens and the window resizes.
 await page.locator('.grid-project-name').first().click();
 const second=await page.locator('.tabulator-row').nth(1).getAttribute('data-session-id');
 await page.getByRole('button',{name:'Next session',exact:true}).click();assert.equal(await page.locator('.grid-row-open').getAttribute('data-session-id'),second);
 assert.ok(await page.locator('.grid-session-meta').first().isVisible());
 await page.keyboard.press('Escape');await page.locator('.wb-link-banner button').click();
 await page.locator('[data-route=sessions]').click();
 await page.locator('#usage-session-sort').selectOption('tokens');await page.locator('#lang-toggle').click();await page.waitForSelector('html[lang=tr]');await page.waitForSelector('#sessions-grid .tabulator-row');
 assert.match(await page.locator('.tabulator-col[tabulator-field=project]').innerText(),/Oturum/);assert.equal(await page.locator('#usage-session-sort').inputValue(),'tokens');await page.locator('#usage-session-sort').selectOption('recent');await page.waitForTimeout(100);
 await page.screenshot({path:fileURLToPath(new URL('preview.png',root))});
 await page.locator('.grid-project-name').first().click();await page.screenshot({path:fileURLToPath(new URL('inspector.png',root))});
 const cols=await page.locator('.tabulator-col[tabulator-field=tokens]').boundingBox();const grid=await page.locator('#sessions-grid').boundingBox();
 assert.ok(cols.x+cols.width<=grid.x+grid.width+2,'tokens lost behind the inspector');
 await page.keyboard.press('Escape');await page.setViewportSize({width:1100,height:720});await page.waitForTimeout(150);
 const firstBox=await page.locator('.tabulator-row').first().boundingBox();assert.ok(firstBox.y<390,JSON.stringify(firstBox));
 const tokenBox=await page.locator('.tabulator-col[tabulator-field=tokens]').boundingBox();assert.ok(tokenBox.x+tokenBox.width<=1100,'laptop token column is off screen');
 await page.screenshot({path:fileURLToPath(new URL('laptop.png',root))});
 await page.locator('#usage-session-search').fill('no-such-session');await page.waitForFunction(()=>document.querySelectorAll('#sessions-grid .tabulator-row').length===0);
 assert.ok(await page.locator('#usage-search-empty').isVisible());assert.equal(await page.locator('#usage-session-count').textContent(),'0 oturum');
 await page.locator('#usage-search-clear').click();
 await page.locator('[data-route=settings]').click();assert.ok(await page.locator('#usage-export').isVisible());assert.ok(await page.locator('.ws-report-scope').isVisible());
 await page.screenshot({path:fileURLToPath(new URL('settings.png',root))});
 await page.locator('[data-route=sessions]').click();await page.setViewportSize({width:390,height:844});await page.waitForTimeout(150);
 const width=await page.evaluate(()=>({viewport:innerWidth,scroll:document.documentElement.scrollWidth}));assert.ok(width.scroll<=width.viewport);
 await page.screenshot({path:fileURLToPath(new URL('narrow.png',root)),fullPage:true});
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
 await writeFile(new URL('ui-check.json',root),JSON.stringify({one_sort_for_complete_snapshot:true,maximum_outside_first_page_found:true,linked_work_title:true,search_by_work_title:true,work_to_session_flow:true,success_style:true,verdict_save:true,failed_save_preserves_value:true,inspector_navigation:true,agent_and_date_stay_visible:true,laptop_first_row:firstBox.y,tokens_visible_on_laptop_and_with_inspector:true,single_empty_result:true,export_scope_separate:true,turkish:true,narrow:width,script_errors:errors,external_requests:remote},null,2));
 console.log('UX pass 1 interaction checks passed');
}finally{await browser.close();}
