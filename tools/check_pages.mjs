// Validate the actual export using CyDoc's public routing/search APIs.
import { createDocumentation, parseLink, hasAnchor } from 'cydoc';
import { readFile, readdir, lstat } from 'node:fs/promises';
import { resolve, relative } from 'node:path';
import assert from 'node:assert/strict';
const root = resolve(process.argv[2] || 'build/pages-project/site');
const data = JSON.parse(await readFile(resolve(root, 'manifest.json'), 'utf8'));
const docs = createDocumentation(data);
const report = JSON.parse(await readFile(resolve(root, 'translation-report.json'), 'utf8'));
for (const key of ['missing','outdated','untracked']) assert.deepEqual(report[key], [], key);
assert.equal(data.defaultLocale, 'en');
assert.deepEqual(data.locales.map(l=>l.code), ['en','fr']);
const pages = Object.fromEntries(['en','fr'].map(locale=>[locale,new Map(data.pages.filter(p=>p.locale===locale).map(p=>[p.id,p]))]));
assert.deepEqual([...pages.en.keys()].sort(), [...pages.fr.keys()].sort());
let links = 0, diagrams = 0;
const expectedAssets = new Set(['assets/cyrsassistant-logo-turquoise.png','assets/screenshots/chat-preview.png','assets/screenshots/connection-preview.png']);
async function asset(value) {
  if (value.startsWith('data:')) return;
  assert.ok(!/^(?:[a-z]+:|\/|\\)/i.test(value), 'Nonlocal resource: '+value);
  const path = resolve(root, decodeURIComponent(value.split(/[?#]/)[0]));
  assert.ok(!relative(root,path).startsWith('..'), 'Resource escapes export');
  assert.ok((await lstat(path)).isFile(), 'Missing resource: '+value);
}
for (const page of data.pages) {
  const other = pages[page.locale==='en'?'fr':'en'].get(page.id);
  assert.deepEqual(page.headings.map(h=>h.id), other.headings.map(h=>h.id), page.id);
  const media = html=>[...html.matchAll(/data-cydoc-id="([^"]+)"/g)].map(m=>m[1]);
  assert.deepEqual(media(page.html),media(other.html),page.id);
  diagrams += (page.html.match(/class="diagram"/g)||[]).length;
  for (const link of page.links || []) {
    if (!link.startsWith('#/')) continue;
    const route = parseLink(link), target = docs.resolve(route.pageId,route.locale);
    assert.ok(target && (!route.anchor || hasAnchor(target.page,route.anchor)), 'Broken route: '+link);
    links++;
  }
  for (const path of page.assets || []) await asset(path);
  for (const match of page.html.matchAll(/<(?:img|script|source)\b[^>]*\bsrc="([^"]+)"/g)) await asset(match[1]);
}
assert.ok(diagrams >= 16, 'Bilingual SVG diagrams missing');
assert.ok(docs.search('threshold','en').length && docs.search('précompil','fr').length, 'Bilingual search');
assert.equal(docs.canonicalRoute({locale:'fr',pageId:'quickstart'}).pageId,'install');
const allowed = new Set(['.nojekyll','index.html','index.en.html','index.fr.html','legacy.js','data.js','manifest.json','viewer.js','viewer.css','reader.css','media-image.js','LICENSE.CyDoc.txt','translation-report.json',...expectedAssets]);
const actual = [];
async function walk(folder) {
  for (const entry of await readdir(folder,{withFileTypes:true})) {
    const path = resolve(folder,entry.name);
    assert.ok(!entry.isSymbolicLink(), 'Symlink in export');
    if(entry.isDirectory()) await walk(path);
    else { const name=relative(root,path).replaceAll('\\','/'); assert.ok(allowed.has(name),'Unnecessary artifact file: '+name); actual.push(name); }
  }
}
await walk(root);
assert.deepEqual(actual.sort(), [...allowed].sort());
for (const name of ['index.html','index.en.html','index.fr.html']) {
  const html = await readFile(resolve(root,name),'utf8');
  for(const match of html.matchAll(/<(?:img|script|link)\b[^>]*\b(?:src|href)="([^"]+)"/g)) await asset(match[1]);
}
for(const name of ['viewer.css','reader.css']) {
  const css=await readFile(resolve(root,name),'utf8');
  for(const match of css.matchAll(/url\(['"]?([^)'"\s]+)['"]?\)/g)) await asset(match[1]);
}
assert.ok((await readFile(resolve(root,'LICENSE.CyDoc.txt'),'utf8')).includes('MIT License'));
console.log('PASS: '+data.pages.length+' bilingual pages, '+links+' routes, '+diagrams+' SVG diagrams, search, aliases, translations and '+actual.length+' local artifact files; image module only.');
