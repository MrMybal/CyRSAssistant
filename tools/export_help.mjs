// Application host integration. All CyDoc APIs are public package entry points.
import { execFileSync } from 'node:child_process';
import { copyFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { build } from 'esbuild';
const root = process.cwd(), output = resolve(root, 'build/help');
execFileSync(process.execPath, [resolve(root, 'node_modules/cydoc/tools/cli.mjs'), process.argv[2] === 'check' ? 'check' : 'build', resolve(root, 'cydoc.config.json')], { stdio: 'inherit' });
await Promise.all([
  build({ entryPoints: ['tools/docs_reader.mjs'], bundle: true, format: 'iife', minify: true, target: 'es2020', outfile: resolve(output, 'viewer.js'), legalComments: 'eof' }),
  build({ entryPoints: ['tools/help_redirect.mjs'], bundle: true, format: 'iife', minify: true, target: 'es2020', outfile: resolve(output, 'legacy.js'), legalComments: 'eof' }),
  copyFile('docs/reader.html', resolve(output, 'index.html')),
  copyFile('docs/reader.css', resolve(output, 'reader.css')),
  copyFile('node_modules/cydoc/LICENSE', resolve(output, 'LICENSE.CyDoc.txt'))
]);
for (const locale of ['en', 'fr']) {
  const text = locale === 'fr' ? 'Ouvrir la documentation locale' : 'Open the local documentation';
  await writeFile(resolve(output, 'index.' + locale + '.html'), '<!doctype html><html lang="' + locale + '"><meta charset="utf-8"><title>CyRSAssistant</title><script src="legacy.js" defer></script><a href="index.html#/' + locale + '/start">' + text + '</a></html>\n');
}
