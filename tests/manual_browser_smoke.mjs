// Chrome smoke test of the complete file:// or HTTP(S) CyDoc export. No browser driver dependency.
import { spawn } from 'node:child_process';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createServer } from 'node:http';
import assert from 'node:assert/strict';
const chrome = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const argument = process.argv[2] || 'build/help';
const readmeLocale = process.argv.find(arg=>arg.startsWith('--readme='))?.split('=')[1];
if (readmeLocale) assert.ok(['en','fr'].includes(readmeLocale), 'README locale must be en or fr');
const remote = /^https?:/.test(argument);
const output = remote ? null : resolve(argument);
let server;
let base = remote ? new URL('index.html', argument.endsWith('/') ? argument : argument+'/').href : pathToFileURL(join(output,'index.html')).href;
if (process.argv.includes('--http') && !remote) {
  const prefix='/CyRSAssistant/';
  server = createServer(async (request,response)=>{
    try {
      const pathname=decodeURIComponent(new URL(request.url,'http://localhost').pathname);
      const file=resolve(output,pathname.slice(prefix.length) || 'index.html');
      if(!pathname.startsWith(prefix) || !file.startsWith(output+'/') && !file.startsWith(output+'\\')) throw Error('Outside export');
      response.setHeader('Content-Security-Policy', "default-src 'self' data: blob:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'none'; object-src 'none'");
      const types={html:'text/html',js:'text/javascript',css:'text/css',json:'application/json',png:'image/png'};
      response.setHeader('Content-Type',(types[file.split('.').pop()] || 'application/octet-stream')+'; charset=utf-8');
      response.end(await readFile(file));
    } catch { response.writeHead(404);response.end('Not found'); }
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  base='http://127.0.0.1:'+server.address().port+prefix+'index.html';
}
const online=base.startsWith('http');
const origin=online ? new URL(base).origin : null;
// Optional host-injected antivirus origin; never set by CI.
const injectedOrigin=process.env.BROWSER_INJECTED_ORIGIN || null;
const profile = await mkdtemp(join(tmpdir(), 'cyrs-cydoc-browser-'));
const child = spawn(chrome, ['--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
  '--remote-debugging-port=0','--user-data-dir='+profile,'--window-size=1440,1050','about:blank'], { stdio:'ignore', windowsHide:true });
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
let socket, sequence = 0;
const pending = new Map(), requests = [], exceptions = [], failedResources = [], readerRequests = new Set();
async function call(method, params={}) {
  const id = ++sequence;
  return new Promise((resolve,reject) => { pending.set(id,{resolve,reject}); socket.send(JSON.stringify({id,method,params})); });
}
async function evaluate(expression) {
  const result = await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
  if(result.exceptionDetails) throw Error(result.exceptionDetails.text+': '+result.exceptionDetails.exception?.description);
  return result.result?.value;
}
async function wait(expression, timeout=15000) {
  const until=Date.now()+timeout;
  while(Date.now()<until) { if(await evaluate(expression)) return; await sleep(80); }
  const state=await evaluate('JSON.stringify({url:location.href,title:document.title,heading:document.querySelector("main h1")?.textContent})');
  throw Error('Timed out: '+expression+'; state='+state);
}
async function navigate(url) { await call('Page.navigate',{url}); await wait("!!document.querySelector('main h1')"); }
try {
  let port;
  for(let i=0;i<200;i++) { try {port=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];break;}catch{await sleep(50);} }
  assert.ok(port,'Chrome did not expose a debugging endpoint');
  const target = await (await fetch('http://127.0.0.1:'+port+'/json/new?about:blank',{method:'PUT'})).json();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
  socket.addEventListener('message',event=>{
    const item=JSON.parse(event.data);
    if(item.id) { const promise=pending.get(item.id); pending.delete(item.id); item.error ? promise?.reject(Error(JSON.stringify(item.error))) : promise?.resolve(item.result); }
    if(item.method==='Network.requestWillBeSent' && (!readmeLocale || item.params.documentURL?.startsWith(origin+'/'))) { requests.push(item.params.request.url);readerRequests.add(item.params.requestId); }
    if(item.method==='Network.responseReceived' && (!readmeLocale || readerRequests.has(item.params.requestId)) && item.params.response.status>=400) failedResources.push(item.params.response.url+': '+item.params.response.status);
    if(item.method==='Runtime.exceptionThrown') exceptions.push(item.params.exceptionDetails.text+': '+item.params.exceptionDetails.exception?.description);
  });
  await call('Page.enable'); await call('Runtime.enable'); await call('Network.enable');
  if(!online) await call('Network.setBlockedURLs',{urls:['http://*','https://*']});
  await mkdir(resolve('build'),{recursive:true});
  if (readmeLocale) {
    assert.ok(online, 'The README journey requires the public site URL');
    const readmeUrl='https://github.com/MrMybal/CyRSAssistant'+(readmeLocale==='fr' ? '/blob/main/README.fr.md' : '');
    const expected=new URL('.',base).href+'#/'+readmeLocale+'/start';
    await call('Page.navigate',{url:readmeUrl});
    const selector='.markdown-body a[href='+JSON.stringify(expected)+']';
    await wait('!!document.querySelector('+JSON.stringify(selector)+')',30000);
    const link=await evaluate('(()=>{const a=document.querySelector('+JSON.stringify(selector)+');a.scrollIntoView({block:"center",behavior:"instant"});return {text:a.textContent,href:a.href,target:a.target};})()');
    assert.ok(link.target==='' || link.target==='_self', 'Unexpected README link target');
    console.log('Clicking published README ['+readmeLocale+']: '+link.text+' -> '+link.href);
    const before=await call('Page.captureScreenshot',{format:'png'});
    await writeFile(resolve('build/readme-'+readmeLocale+'.png'),Buffer.from(before.data,'base64'));
    requests.length=0;failedResources.length=0;exceptions.length=0;readerRequests.clear();
    await evaluate('document.querySelector('+JSON.stringify(selector)+').click()');
    await wait('location.href==='+JSON.stringify(expected)+' && !!document.querySelector("#app main h1")',30000);
    assert.equal(await evaluate('document.documentElement.lang'),readmeLocale);
    assert.ok(await evaluate('!!document.querySelector(".locale-control select") && !!document.querySelector(".search-form")'));
    console.log('PASS: actual README click opened the HTML reader in '+readmeLocale);
    if(readmeLocale==='fr') {
      await evaluate("var locale=document.querySelector('.locale-control select');locale.value='en';locale.dispatchEvent(new Event('change',{bubbles:true}))");
      await wait("document.documentElement.lang==='en' && location.hash==='#/en/start'");
    }
  } else await navigate(base);
  assert.equal(await evaluate('document.documentElement.lang'),'en');
  assert.equal(await evaluate("document.querySelector('#app').dataset.theme"),'nord');
  assert.ok(await evaluate("document.querySelector('main h1').textContent.includes('Start here')"));
  await evaluate("document.querySelector('main a[href=\"#/en/install\"]').click()");
  await wait("location.hash==='#/en/install' && document.querySelector('main h1').textContent.includes('Installation')");
  await evaluate("location.hash='#/en/protocol/permissions'");
  await wait("!!document.querySelector('main #permissions')");
  await evaluate("var locale=document.querySelector('.locale-control select');locale.value='fr';locale.dispatchEvent(new Event('change',{bubbles:true}))");
  await wait("document.documentElement.lang==='fr' && location.hash==='#/fr/protocol/permissions'");
  await evaluate("location.hash='#/fr/connect?media=connection-preview'");
  await wait("!!document.querySelector('[data-cydoc-id=\"connection-preview\"].cy-media')");
  await wait("[...document.querySelectorAll('.cy-media img')].every(i=>i.complete && i.naturalWidth>0)");
  await evaluate("document.querySelector('[data-action=\"in\"]').click()");
  assert.equal(await evaluate("document.querySelector('.zoom-value').textContent"),'125%');
  await evaluate("document.querySelector('[data-action=\"expand\"]').click()");
  assert.ok(await evaluate("!!document.querySelector('.media-expanded')"));
  assert.equal(await evaluate('document.fullscreenElement'),null);
  assert.ok(await evaluate("(()=>{const r=document.querySelector('.media-expanded').getBoundingClientRect();return r.left>=0&&r.top>=0&&r.right<=innerWidth&&r.bottom<=innerHeight;})()"));
  await call('Input.dispatchKeyEvent',{type:'rawKeyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  await wait("!document.querySelector('.media-expanded')");
  await evaluate("location.hash='#/fr/create'");
  await wait("document.querySelectorAll('main .diagram svg').length===1");
  assert.equal(await evaluate("document.querySelector('main .diagram svg').getAttribute('role')"),'img');
  await call('Input.dispatchKeyEvent',{type:'rawKeyDown',key:'k',code:'KeyK',modifiers:2,windowsVirtualKeyCode:75});
  await call('Input.dispatchKeyEvent',{type:'keyUp',key:'k',code:'KeyK',modifiers:2,windowsVirtualKeyCode:75});
  await wait("document.querySelector('dialog').open");
  await evaluate("var input=document.querySelector('.search-form input');input.value='précompil';input.dispatchEvent(new Event('input',{bubbles:true}))");
  assert.ok(await evaluate("document.querySelectorAll('.search-result').length>0"));
  await call('Input.dispatchKeyEvent',{type:'rawKeyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  await wait("!document.querySelector('dialog').open");
  await evaluate("location.hash='#/fr/protocol'");
  await wait("!!document.querySelector('main #help')");
  await evaluate("window.scrollTo({top:650,behavior:'instant'})");await sleep(150);
  const position=await evaluate('scrollY');
  await evaluate("location.hash='#/fr/create'");await wait("!!document.querySelector('main .diagram')");
  await evaluate("location.hash='#/fr/protocol'");await wait("!!document.querySelector('main #help')");
  await wait('Math.abs(scrollY-'+position+')<5');
  await navigate(new URL('index.fr.html',base).href+'#chat');
  await wait("location.hash==='#/fr/chat' && !!document.querySelector('main h1')");
  assert.equal(await evaluate('document.documentElement.lang'),'fr');
  await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await call('Emulation.setTouchEmulationEnabled',{enabled:true});
  await evaluate("location.hash='#/fr/connect?media=connection-preview'");
  await wait("!!document.querySelector('.cy-media')");
  await evaluate("document.querySelector('[data-action=\"expand\"]').click()");
  assert.ok(await evaluate("(()=>{const r=document.querySelector('.media-expanded').getBoundingClientRect();return r.left>=0&&r.top>=0&&r.right<=innerWidth&&r.bottom<=innerHeight;})()"));
  await evaluate("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))");
  await call('Emulation.clearDeviceMetricsOverride');
  await evaluate("location.hash='#/fr/create'");await wait("!!document.querySelector('main .diagram')");
  await evaluate("scrollTo({top:0,behavior:'instant'})");await sleep(150);
  const shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(resolve(readmeLocale ? 'build/cydoc-reader-from-readme-'+readmeLocale+'.png' : 'build/cydoc-reader-fr.png'),Buffer.from(shot.data,'base64'));
  const injected=requests.filter(url=>/^https?:/.test(url) && new URL(url).origin===injectedOrigin);
  if(injected.length) console.log('Host-injected antivirus requests excluded: '+injected.length);
  assert.deepEqual(requests.filter(url=>/^https?:/.test(url) && new URL(url).origin!==injectedOrigin && (!online || new URL(url).origin!==origin)),[]);
  assert.deepEqual(failedResources,[]);
  assert.deepEqual(exceptions,[]);
  console.log('PASS: '+(online ? 'HTTP(S)' : 'file://')+' EN default, FR switch, links/anchors/media, zoom, in-window enlargement/Escape, Ctrl+K/search, reading position, legacy redirect, responsive/touch emulation; no unexpected external requests, missing resources or JS exceptions.');
} finally {
  socket?.close();child.kill();server?.closeAllConnections();server?.close();
  await sleep(300);
  await rm(profile,{recursive:true,force:true}).catch(()=>{});
}
