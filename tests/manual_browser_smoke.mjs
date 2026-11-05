// Windows Chrome smoke test of the real file:// export. No server or browser driver dependency.
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';
const chrome = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const output = resolve(process.argv[2] || 'build/help');
const profile = await mkdtemp(join(tmpdir(), 'cyrs-cydoc-browser-'));
const child = spawn(chrome, ['--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
  '--remote-debugging-port=0','--user-data-dir='+profile,'--window-size=1440,1050','about:blank'], { stdio:'ignore', windowsHide:true });
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
let socket, sequence = 0;
const pending = new Map(), requests = [], exceptions = [];
async function call(method, params={}) {
  const id = ++sequence;
  return new Promise((resolve,reject) => { pending.set(id,{resolve,reject}); socket.send(JSON.stringify({id,method,params})); });
}
async function evaluate(expression) {
  const result = await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
  if(result.exceptionDetails) throw Error(result.exceptionDetails.text+': '+result.exceptionDetails.exception?.description);
  return result.result?.value;
}
async function wait(expression) {
  const until=Date.now()+8000;
  while(Date.now()<until) { if(await evaluate(expression)) return; await sleep(80); }
  throw Error('Timed out: '+expression);
}
const base = pathToFileURL(join(output,'index.html')).href;
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
    if(item.method==='Network.requestWillBeSent') requests.push(item.params.request.url);
    if(item.method==='Runtime.exceptionThrown') exceptions.push(item.params.exceptionDetails.text+': '+item.params.exceptionDetails.exception?.description);
  });
  await call('Page.enable'); await call('Runtime.enable'); await call('Network.enable');
  await call('Network.setBlockedURLs',{urls:['http://*','https://*']});
  await navigate(base);
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
  await navigate(pathToFileURL(join(output,'index.fr.html')).href+'#chat');
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
  await writeFile(resolve('build/cydoc-reader-fr.png'),Buffer.from(shot.data,'base64'));
  assert.deepEqual(requests.filter(url=>/^https?:/.test(url)),[]);
  assert.deepEqual(exceptions,[]);
  console.log('PASS: file:// EN default, FR switch, links/anchors/media, zoom, in-window enlargement/Escape, Ctrl+K/search, reading position, legacy redirect, responsive/touch emulation; no HTTP requests or JS exceptions.');
} finally {
  socket?.close();child.kill();
  await sleep(300);
  await rm(profile,{recursive:true,force:true}).catch(()=>{});
}
