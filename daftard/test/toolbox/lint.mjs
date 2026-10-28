// node test/toolbox/lint.mjs — the new pages put HTML into the page only through toolbox/safe.js mount(): no
// innerHTML, outerHTML, insertAdjacentHTML or document.write anywhere else under web/toolbox and web/app.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
const root = new URL('../../web/', import.meta.url).pathname;
const files = [];
const walk = d => { for (const n of readdirSync(d)) { const p = join(d, n); statSync(p).isDirectory() ? walk(p) : p.endsWith('.js') && files.push(p); } };
['toolbox', 'app'].forEach(d => { try { walk(join(root, d)); } catch { /* not there yet */ } });
const bad = [];
for (const f of files) {
  if (f.endsWith('toolbox/safe.js')) continue;
  readFileSync(f, 'utf8').split('\n').forEach((line, i) => {
    if (/\.(innerHTML|outerHTML)\s*[+]?=|insertAdjacentHTML|document\.write/.test(line)) bad.push(`${f.slice(root.length)}:${i + 1}: ${line.trim().slice(0, 100)}`);
  });
}
if (bad.length) { console.log('FAIL: HTML put into the page outside safe.js mount():\n' + bad.join('\n')); process.exit(1); }
console.log(`PASS: lint — ${files.length} files put HTML into the page only through mount().`);
