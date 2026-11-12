const {chromium}=require('playwright');
const fs=require('fs'),http=require('http'),assert=require('assert');
const bytes=fs.readFileSync(require('path').join(__dirname,'../index.html'));
(async()=>{const server=http.createServer((q,r)=>{r.setHeader('Content-Type','text/html;charset=utf-8');r.end(bytes)});await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;
try{browser=await chromium.launch();const base=`http://127.0.0.1:${server.address().port}/`;
let canonical;
for(const width of [390,1440])for(const lang of ['es','en','pt']){
 const page=await browser.newPage({viewport:{width,height:900}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('net::'))errors.push(m.text())});
 await page.addInitScript(()=>{window.sent=[];Object.defineProperty(navigator,'share',{configurable:true,value:async x=>window.sent.push(x)})});
 await page.goto(base+'?lang='+lang);await page.waitForTimeout(250);
 let ids=await page.locator('.share-target').evaluateAll(xs=>xs.map(x=>x.id));assert.equal(new Set(ids).size,ids.length,'Duplicate target IDs');
 let news=await page.locator('#news article').evaluateAll(xs=>xs.map(x=>x.id));assert(news.length>0);if(canonical)assert.deepEqual(news,canonical);else canonical=news;
 assert.equal(await page.locator('#news .item-share button').count(),news.length);
 await page.locator('#btn-share').dispatchEvent('click');const header=await page.evaluate(()=>window.sent.pop());assert.deepEqual(Object.keys(header),['url']);assert.equal(header.url,'https://matisandev.cl/kastigo?lang='+lang);
 await page.locator('#news .item-share button').first().click();let sent=await page.evaluate(()=>window.sent[0]);let url=new URL(sent.url);assert.equal(url.origin,'https://matisandev.cl');assert.equal(url.searchParams.get('lang'),lang);assert.equal(url.hash,'#'+news[0]);assert(url.searchParams.get('edition'));
 await page.evaluate(()=>{localStorage.setItem('kg-filter','calle');localStorage.setItem('kg-c-noticias','1')});
 await page.goto(base+url.search+url.hash);await page.waitForTimeout(300);assert(await page.locator('#'+news[0]).isVisible());assert.equal(await page.locator('#toggle-noticias').getAttribute('aria-expanded'),'true');assert.equal(await page.evaluate(()=>document.activeElement.id),news[0]);
 await page.screenshot({path:`/tmp/kastigo-share-${lang}-${width}.png`});
 await page.locator('#news .item-share button').first().scrollIntoViewIfNeeded();await page.screenshot({path:`/tmp/kastigo-share-button-${lang}-${width}.png`});
 assert.equal(await page.locator('section[data-share] > .h-row button[id^=share-],section[data-share] .h-row button[id^=share-]').count(),9);
 await page.goto(base+`?lang=${lang}&edition=2000-01-01#${news[0]}`);await page.waitForTimeout(250);assert.equal(await page.locator('#shared-notice').evaluate(n=>n.parentElement.id),news[0]);
 await page.goto(base+`?lang=${lang}&edition=2000-01-01#kg-noticia-missing`);await page.waitForTimeout(200);assert(await page.locator('#shared-notice').isVisible());
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);
 await page.close();console.log(lang,width,'OK',ids.length,'targets');
}
// Clipboard fallback and native share cancellation.
const p=await browser.newPage();await p.addInitScript(()=>{Object.defineProperty(navigator,'share',{value:undefined});Object.defineProperty(navigator,'clipboard',{value:{writeText:async u=>{window.copied=u}}})});await p.goto(base+'?lang=es');await p.locator('#news .item-share button').first().click();assert((await p.evaluate(()=>window.copied)).includes('#kg-noticia-'));await p.close();
const q=await browser.newPage();await q.addInitScript(()=>{Object.defineProperty(navigator,'share',{value:async()=>{throw new DOMException('cancelled','AbortError')}});Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{window.unwanted=true}}})});await q.goto(base);await q.locator('#news .item-share button').first().click();assert(!(await q.evaluate(()=>window.unwanted)));await q.close();console.log('Clipboard and cancellation OK');
}finally{if(browser)await browser.close();server.close()}})().catch(e=>{console.error(e);process.exitCode=1});
