import { createLink } from 'cydoc';
const locale = document.documentElement.lang || 'en';
const target = new URL('index.html', location.href);
if (location.hash.startsWith('#/')) target.hash = location.hash;
else {
  const pageId = decodeURIComponent(location.hash.slice(1) || 'start');
  const q = new URLSearchParams(location.search).get('q');
  target.hash = createLink({ locale, pageId, state: q ? { q: q.slice(0, 255) } : undefined });
}
location.replace(target.href);
