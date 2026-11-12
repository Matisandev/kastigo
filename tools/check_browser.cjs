const {chromium}=require(process.env.KASTIGO_PLAYWRIGHT_MODULE || 'playwright');
const fs=require('fs'),http=require('http'),crypto=require('crypto'),path=require('path');
const root=path.resolve(__dirname,'..'), bytes=fs.readFileSync(path.join(root,process.env.KASTIGO_CANDIDATE || '.kastigo-candidate.html'));
(async()=>{
const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end(bytes)});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
let browser;
try{
 browser=await chromium.launch({headless:true});
 const results=[];
 for(const width of [390,1440])for(const lang of ['es','en','pt']){
  const page=await browser.newPage({viewport:{width,height:900}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('net::'))errors.push(m.text())});
  await page.goto(`http://127.0.0.1:${server.address().port}/?lang=${lang}`,{waitUntil:'load'});
  await page.waitForTimeout(500);
  const result=await page.evaluate(()=>({lang:document.documentElement.lang,sections:[...document.querySelectorAll('main section')].map(s=>({id:s.id,length:s.innerText.trim().length})),overflow:document.documentElement.scrollWidth>innerWidth,text:document.body.innerText}));
  if(result.sections.length!==10||!result.lang.startsWith(lang)||errors.length||result.overflow||result.sections.some(s=>!s.length)||result.text.includes('undefined'))throw Error(JSON.stringify({width,lang,errors,result}));
  await page.screenshot({path:path.join(root,'.kastigo-update.lock',`${lang}-${width}.png`)});
  results.push({width,lang,sections:result.sections});await page.close();
 }
 fs.writeFileSync(path.join(root,'.kastigo-update.lock/browser-check.json'),JSON.stringify({passed:true,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),results},null,2));
 console.log(JSON.stringify(results));
}finally{if(browser)await browser.close();server.close()}
})().catch(e=>{console.error(e.message);process.exitCode=1});
