// Shared host export for installed offline help and GitHub Pages.
import { execFileSync } from 'node:child_process';
import { copyFile, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import { build } from 'esbuild';
const toolRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export async function exportHelp({ projectRoot = toolRoot, output = resolve(projectRoot, 'build/help'), command = 'build' } = {}) {
  execFileSync(process.execPath, [resolve(toolRoot, 'node_modules/cydoc/tools/cli.mjs'), command, resolve(projectRoot, 'cydoc.config.json')], { cwd: projectRoot, stdio: 'inherit' });
  const bundle = (entry, name) => build({ entryPoints: [resolve(toolRoot, entry)], bundle: true, format: 'iife', minify: true, target: 'es2020', outfile: resolve(output, name), legalComments: 'eof' });
  await Promise.all([
    bundle('tools/docs_reader.mjs', 'viewer.js'),
    bundle('tools/help_redirect.mjs', 'legacy.js'),
    copyFile(resolve(toolRoot, 'docs/reader.html'), resolve(output, 'index.html')),
    copyFile(resolve(toolRoot, 'docs/reader.css'), resolve(output, 'reader.css')),
    copyFile(resolve(toolRoot, 'node_modules/cydoc/LICENSE'), resolve(output, 'LICENSE.CyDoc.txt'))
  ]);
  for (const locale of ['en', 'fr']) {
    const text = locale === 'fr' ? 'Ouvrir la documentation' : 'Open the documentation';
    await writeFile(resolve(output, 'index.' + locale + '.html'), '<!doctype html><html lang="' + locale + '"><meta charset="utf-8"><title>CyRSAssistant</title><script src="legacy.js" defer></script><a href="index.html#/' + locale + '/start">' + text + '</a></html>\n');
  }
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const { values, positionals } = parseArgs({ options: { project: { type: 'string' }, output: { type: 'string' } }, allowPositionals: true });
  const projectRoot = values.project ? resolve(values.project) : toolRoot;
  await exportHelp({ projectRoot, output: values.output ? resolve(values.output) : resolve(projectRoot, 'build/help'), command: positionals[0] === 'check' ? 'check' : 'build' });
}
