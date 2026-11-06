import { createDocumentation, parseLink, hasAnchor } from 'cydoc';
import { readFile, readdir, lstat } from 'node:fs/promises';
import { resolve, relative } from 'node:path';
import assert from 'node:assert/strict';
const root=resolve(process.argv[2] || '../Documentation'), resources=resolve(root,'DocData');
const data=JSON.parse(await readFile(resolve(resources,'manifest.json'),'utf8'));
const docs=createDocumentation(data);
const report=JSON.parse(await readFile(resolve(resources,'translation-report.json'),'utf8'));
for(const key of ['missing','outdated','untracked']) assert.deepEqual(report[key],[],key);
assert.equal(data.defaultLocale,'en');
assert.deepEqual(docs.availableLocales().map(l=>l.code),['en','fr']);
assert.equal(data.logo,'assets/cyrsassistant-logo-turquoise.png');
const pages=Object.fromEntries(['en','fr'].map(locale=>[locale,new Map(data.pages.filter(p=>p.locale===locale).map(p=>[p.id,p]))]));
assert.deepEqual([...pages.en.keys()].sort(),[...pages.fr.keys()].sort());
assert.ok(data.pages.every(p=>p.kind!=='source' && !p.id.startsWith('source-')),'Raw source listing');
assert.ok(!data.pages.some(p=>['authoring','translation-report'].includes(p.id)),'Internal page');
assert.ok(data.pages.filter(p=>p.parent).length>=30,'Missing navigation hierarchy');
assert.ok(docs.resolve('python-client','fr'));
let links=0,diagrams=0;
async function asset(value,base=resources) {
  if(value.startsWith('data:')) return;
  assert.ok(!/^(?:[a-z]+:|\/|\\)/i.test(value),'Remote/absolute resource: '+value);
  const path=resolve(base,decodeURIComponent(value.split(/[?#]/)[0]));
  assert.ok(!relative(root,path).startsWith('..'),'Resource escapes export');
  assert.ok((await lstat(path)).isFile(),'Missing resource: '+value);
}
for(const page of data.pages) {
  const other=pages[page.locale==='en'?'fr':'en'].get(page.id);
  assert.equal(page.parent,other.parent,page.id);
  assert.deepEqual(page.headings.map(h=>h.id),other.headings.map(h=>h.id),page.id);
  const media=html=>[...html.matchAll(/data-cydoc-id="([^"]+)"/g)].map(m=>m[1]);
  assert.deepEqual(media(page.html),media(other.html),page.id);
  diagrams+=(page.html.match(/class="diagram"/g)||[]).length;
  for(const href of page.links || []) {
    if(!href.startsWith('#/')) continue;
    const route=docs.canonicalRoute(parseLink(href)),target=docs.resolve(route.pageId,route.locale);
    assert.ok(target && (!route.anchor || hasAnchor(target.page,route.anchor)),'Broken route: '+href);links++;
  }
  for(const src of page.assets || []) await asset(src);
  for(const m of page.html.matchAll(/<(?:img|source|script)\b[^>]*\bsrc="([^"]+)"/g)) await asset(m[1]);
}
assert.ok(diagrams>=18);
assert.ok(docs.search('threshold','en').length && docs.search('précompil','fr').length);
const assets=['assets/cyrsassistant-logo-turquoise.png','assets/screenshots/chat-preview.png','assets/screenshots/connection-preview.png'];
const allowed=new Set(['Documentation.html','DocAI.md','index.html','index.en.html','index.fr.html',...['legacy.js','data.js','manifest.json','viewer.js','viewer.css','reader.css','media-image.js','LICENSE.CyDoc.txt','translation-report.json',...assets].map(p=>'DocData/'+p)]);
const actual=[];
async function walk(folder){for(const e of await readdir(folder,{withFileTypes:true})) {assert.ok(!e.isSymbolicLink(),'Filesystem link');const path=resolve(folder,e.name);if(e.isDirectory()) await walk(path);else {const name=relative(root,path).replaceAll('\\','/');assert.ok(allowed.has(name),'Unexpected export file: '+name);actual.push(name);}}}
await walk(root);assert.deepEqual(actual.sort(),[...allowed].sort());
for(const name of ['Documentation.html','index.html','index.en.html','index.fr.html']) {
 const html=await readFile(resolve(root,name),'utf8');
 for(const m of html.matchAll(/<(?:img|script|link)\b[^>]*\b(?:src|href)="([^"]+)"/g)) await asset(m[1],root);
}
for(const name of ['viewer.css','reader.css']) {
 const css=await readFile(resolve(resources,name),'utf8');
 for(const m of css.matchAll(/url\(['"]?([^)'"\s]+)['"]?\)/g)) await asset(m[1]);
}
assert.ok((await readFile(resolve(resources,'LICENSE.CyDoc.txt'),'utf8')).includes('MIT License'));
const ai=await readFile(resolve(root,'DocAI.md'),'utf8');assert.ok(ai.includes('Documentation.html') && ai.includes('DocData/manifest.json'));
assert.ok(data.pages.every(p=>!p.text.includes('Documentation integration notes for coding assistants')));
console.log('PASS: '+data.pages.length+' EN/FR pages, '+links+' routes, '+diagrams+' diagrams, full translations, API-only reference, navigation tree and '+actual.length+' local files.');
