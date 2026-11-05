import { mountViewer } from 'cydoc/viewer';
import { createDocumentation, createLink, parseLink } from 'cydoc';
const data = globalThis.CYDOC_DATA, packed = globalThis.CYDOC_OPTIONS || {};
const docs = createDocumentation(data);
const root = document.getElementById('app');
if (!location.hash.startsWith('#/')) {
  const pageId = decodeURIComponent(location.hash.slice(1) || 'start');
  const q = new URLSearchParams(location.search).get('q');
  history.replaceState(null, '', createLink({ locale: 'en', pageId: docs.resolve(pageId, 'en') ? pageId : 'start', state: q ? { q: q.slice(0, 255) } : undefined }));
}
const pending = new Map();
function loadAsset(src) {
  if (pending.has(src)) return pending.get(src);
  const file = packed.assets?.[src];
  if (!file) return Promise.reject(new Error('Local asset is not packaged: ' + src));
  const promise = new Promise((resolve, reject) => {
    const script = document.createElement('script'); script.src = file;
    script.onload = () => { const asset = globalThis.CYDOC_ASSETS?.[src]; delete globalThis.CYDOC_ASSETS?.[src]; script.remove(); pending.delete(src); asset ? resolve(asset) : reject(new Error('Invalid packed asset')); };
    script.onerror = () => { script.remove(); pending.delete(src); reject(new Error('Cannot load local asset')); };
    document.head.append(script);
  });
  pending.set(src, promise); return promise;
}
const modules = Object.fromEntries((packed.modules || []).map(name => [name, () => new Promise((resolve, reject) => {
  const script = document.createElement('script'); script.src = 'media-' + name + '.js';
  script.onload = () => resolve(globalThis['CyDocMedia_' + name].default);
  script.onerror = () => reject(new Error('Cannot load local media module'));
  document.head.append(script);
})]));
let theme = 'nord';
try { if (localStorage.getItem('cydoc:theme')) theme = undefined; } catch {}
const viewer = mountViewer(root, data, { homePage: 'start', initialLocale: 'en', initialTheme: theme, storageId: 'cyrsassistant-help', modules, loadAsset });
function brand() {
  const fr = document.documentElement.lang.startsWith('fr');
  const tag = root.querySelector('.mit-tag');
  if (tag) tag.textContent = 'CyDoc · MIT';
  const license = root.querySelector('.footer > div > span:last-child');
  if (license) license.textContent = fr ? 'Application : GPL-3.0 · Lecteur CyDoc : MIT' : 'Application: GPL-3.0 · CyDoc reader: MIT';
}
brand();
new MutationObserver(brand).observe(root, { childList: true });
window.addEventListener('hashchange', () => { queueMicrotask(brand); });
window.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    const dialog = root.querySelector('dialog[open]');
    if (dialog) { event.preventDefault(); dialog.close(); }
  }
  if (event.key === 'F1') { event.preventDefault(); location.hash = createLink({ locale: parseLink(location.hash, 'en', 'start').locale, pageId: 'start' }); }
});
const query = parseLink(location.hash, 'en', 'start').state?.q;
if (query) {
  root.querySelector('[data-search]')?.click();
  const input = root.querySelector('.search-form input');
  if (input) { input.value = query.slice(0, 255); input.dispatchEvent(new Event('input', { bubbles: true })); }
}
window.addEventListener('pagehide', () => viewer.destroy(), { once: true });
