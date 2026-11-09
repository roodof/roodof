import {chromium,_electron} from 'playwright';
import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.PLER_TERMS_ROOT),pkg=process.env.PLER_MOTION_PACKAGE,before=process.env.PLER_MOTION_EXPECT==='before';
const startup=(await readFile(path.join(root,'access.tmp'),'utf8')).trim();
let browser,app,control;const results=[],errors=[];
try{
 for(const reduced of [false,true]){
  let page,mode='initial';
  if(pkg){control=path.join(root,'motion-control-'+reduced);await mkdir(control);await writeFile(path.join(control,'running'),'1');const state=path.join(root,'motion-state.json');await writeFile(state,JSON.stringify({width:1440,height:950,lang:'en',tour:true,view:{setupDone:true,screen:'quota'}}));const env={...process.env,PLER_DESKTOP_URL:startup,PLER_DESKTOP_SESSION:control,PLER_DESKTOP_PARENT:String(process.pid),PLER_DESKTOP_STATE:state};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;app=await _electron.launch({executablePath:path.join(pkg,'desktop/PLER-Desktop.exe'),args:[],env});page=await app.firstWindow();await page.emulateMedia({reducedMotion:reduced?'reduce':'no-preference'});await page.waitForFunction(()=>typeof usageState!=='undefined'&&document.querySelector('.settings-tabs'));await page.bringToFront();
  }else{browser??=await chromium.launch({channel:'msedge',headless:true});page=await browser.newPage({viewport:{width:2560,height:1528},reducedMotion:reduced?'reduce':'no-preference'});}
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/api/usage?*',async route=>{const response=await route.fetch();const data=await response.json();if(mode!=='ready'){data.state='scanning';data.has_snapshot=mode==='refresh';}await route.fulfill({response,json:data});});
  if(!pkg){const url=new URL(startup);url.searchParams.set('lang','en');url.searchParams.set('view',JSON.stringify({setupDone:true,screen:'quota'}));await page.goto(url.href);}else await page.reload();
  await page.waitForFunction(()=>typeof usageState!=='undefined'&&usageState.data?.state==='scanning'&&document.body.classList.contains('workspace-redesign'));
  await page.locator('.ws-skeleton').waitFor();
  let cdp,frames=[],events=[];
  if(!pkg){
  cdp=await page.context().newCDPSession(page);await cdp.send('Emulation.setCPUThrottlingRate',{rate:6});await page.waitForTimeout(500);
  const finished=new Promise(resolve=>cdp.once('Tracing.tracingComplete',resolve));await cdp.send('Tracing.start',{categories:'devtools.timeline',transferMode:'ReturnAsStream'});
  frames=await page.evaluate(()=>new Promise(resolve=>{const times=[];setTimeout(()=>resolve(times),2400);let previous=performance.now(),start=previous;function tick(now){times.push(now-previous);previous=now;if(now-start<2000)requestAnimationFrame(tick);else resolve(times);}requestAnimationFrame(tick);}));
  await cdp.send('Tracing.end');const {stream}=await finished;let trace='';for(;;){const part=await cdp.send('IO.read',{handle:stream});trace+=part.data;if(part.eof)break;}await cdp.send('IO.close',{handle:stream});
  events=JSON.parse(trace).traceEvents;
  }else await page.waitForTimeout(300);
  const paints=events.filter(e=>e.name==='Paint'),layouts=events.filter(e=>e.name==='Layout');
  const animation=await page.evaluate(()=>({bars:[...document.querySelectorAll('.ws-skeleton-row>span')].map(n=>getComputedStyle(n).animationName),sheen:getComputedStyle(document.querySelector('.ws-skeleton'),'::after').animationName,track:document.querySelector('.ws-loading-track>span')?getComputedStyle(document.querySelector('.ws-loading-track>span')).animationName:null}));
  if(!before){assert.ok(animation.bars.every(v=>v==='none'));assert.equal(animation.track,reduced?'none':'ws-loading-travel');assert.equal(animation.sheen,reduced?'none':'ws-loading-sheen');assert.equal(await page.locator('#usage-progress').getAttribute('value'),null);}
  await page.screenshot({path:path.join(root,'loading-'+reduced+'.png')});if(cdp)await cdp.send('Emulation.setCPUThrottlingRate',{rate:1});
  mode='ready';await page.evaluate(()=>loadUsage());await page.waitForFunction(()=>usageState.data?.has_snapshot&&usageState.data.state==='ready'&&!usageState.loading);
  assert.ok(await page.locator('.ws-skeleton').isHidden());if(!before)assert.ok(await page.locator('.ws-loading-track').isHidden());
  const totals=await page.evaluate(()=>JSON.stringify(usageState.data.totals));mode='refresh';await page.evaluate(()=>loadUsage());assert.ok(await page.locator('.ws-skeleton').isHidden());assert.ok(await page.locator('#usage-content').isVisible());assert.equal(await page.evaluate(()=>JSON.stringify(usageState.data.totals)),totals);
  if(!before){assert.ok(await page.locator('.ws-loading-track').isVisible());if(!reduced){const current=await page.locator('.ws-loading-track>span').evaluate(n=>n.getAnimations()[0].currentTime);await page.evaluate(()=>{for(let i=0;i<8;i++)usageUI.publish('loading',true);});await page.waitForTimeout(150);assert.ok(await page.locator('.ws-loading-track>span').evaluate(n=>n.getAnimations()[0].currentTime)>current);}}
  mode='ready';await page.evaluate(()=>loadUsage());
  for(let i=0;i<5;i++){await page.locator('[data-route=settings]').click();await page.locator('[data-route=quota]').click();}
  await page.waitForTimeout(400);assert.equal(await page.locator('body').getAttribute('data-screen'),'quota');if(!before)assert.equal(await page.locator('.ws-page:visible').evaluate(n=>n.getAnimations().length),0);
  results.push({reducedMotion:reduced,tracePaintEvents:paints.length,traceLayoutEvents:layouts.length,frameSamples:frames.length,frameP95Ms:frames.sort((a,b)=>a-b)[Math.floor(frames.length*.95)],animation,initialAndRefresh:true,existingDataKept:true,rapidNavigation:true});
  if(app){await app.close();app=null;assert.equal(path.dirname(control),root);await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});control=null;}else await page.close();
 }
 assert.deepEqual(errors,[]);await writeFile(path.join(root,pkg?'motion-desktop-check.json':'motion-ui-check.json'),JSON.stringify({before,packagedDesktop:Boolean(pkg),results,scriptErrors:errors,scope:'Developer fixtures and 6x CPU throttle; not user hardware or clean Windows acceptance'},null,2));console.log('Loading, refresh, reduced motion and rapid navigation passed');
}finally{if(app)await app.close();if(browser)await browser.close();if(control){assert.equal(path.dirname(control),root);await rm(control,{recursive:true,force:true,maxRetries:10,retryDelay:100});}}
