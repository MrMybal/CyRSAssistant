// Application generation through CyDoc's public CLI and comment adapter.
import { execFileSync } from 'node:child_process';
import { copyFile, writeFile, readFile, mkdir, cp, rm } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { extractComments } from 'cydoc/extract';
import { build } from 'esbuild';
const work=dirname(fileURLToPath(import.meta.url)), root=resolve(work,'..');
const settings=JSON.parse(await readFile(resolve(work,'cydoc.config.json'),'utf8'));
const output=resolve(work,'generated/export'), content=resolve(work,'generated/content');
await mkdir(resolve(work,'generated'),{recursive:true});
await rm(content,{recursive:true,force:true});
await cp(resolve(work,'manual'),content,{recursive:true});
const pages=extractComments(await readFile(resolve(root,'companion/transport.py'),'utf8'),'companion/transport.py');
const reviewed=JSON.parse(await readFile(resolve(work,'api-revisions.json'),'utf8'));
if(pages.length!==2 || pages.some(p=>p.id!=='python-client') || !pages.some(p=>p.locale==='en') || !pages.some(p=>p.locale==='fr')) throw Error('Expected the complete EN/FR Python client reference');
for(const page of pages) {
  const hash=createHash('sha256').update(page.markdown).digest('hex');
  if(reviewed[page.locale]!==hash) throw Error('Review the '+page.locale+' API translation and update api-revisions.json');
  const metadata={id:page.id,title:page.title,description:page.description,section:page.section,parent:'protocol',kind:'api',order:100,symbol:page.symbol,[page.locale==='en'?'revision':'sourceRevision']:String(reviewed.revision)};
  const markdown='---\n'+Object.entries(metadata).map(([key,value])=>key+': '+value).join('\n')+'\n---\n\n'+page.markdown+'\n';
  await writeFile(resolve(content,page.locale,'python-client.md'),markdown);
}
const temporary=resolve(work,'cydoc.build-config.json');
try {
  await writeFile(temporary,JSON.stringify({...settings,content:'generated/content',sources:[],out:'generated/export'},null,2));
  execFileSync(process.execPath,[resolve(work,'node_modules/cydoc/tools/cli.mjs'),process.argv.includes('--check')?'check':'build',temporary],{cwd:work,stdio:'inherit'});
} finally { await rm(temporary,{force:true}); }
const bundle=(entry,name)=>build({entryPoints:[resolve(work,entry)],bundle:true,format:'iife',minify:true,target:'es2020',outfile:resolve(output,'DocData',name),legalComments:'eof'});
await Promise.all([
  bundle('reader.mjs','viewer.js'),bundle('redirect.mjs','legacy.js'),
  copyFile(resolve(work,'reader.html'),resolve(output,'Documentation.html')),
  copyFile(resolve(work,'reader.css'),resolve(output,'DocData/reader.css')),
  copyFile(resolve(work,'node_modules/cydoc/LICENSE'),resolve(output,'DocData/LICENSE.CyDoc.txt'))
]);
for(const locale of ['en','fr']) {
  const text=locale==='fr'?'Ouvrir la documentation':'Open documentation';
  const html='<!doctype html><html lang="'+locale+'"><meta charset="utf-8"><title>CyRSAssistant</title><script src="DocData/legacy.js" defer></script><a href="Documentation.html#/'+locale+'/start">'+text+'</a></html>\n';
  await writeFile(resolve(output,'index.'+locale+'.html'),html);
  if(locale==='en') await writeFile(resolve(output,'index.html'),html);
}
