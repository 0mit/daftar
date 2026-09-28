// The one page's script: it reads the data site/board.py wrote into site/index.html, and draws the boards — in each
// language the data carries. The law's words, the forms and what the gate printed are the release's own, and are
// shown as it states them, left to right, in every language.
const DATA = JSON.parse(document.getElementById('data').textContent);
(function(){
const L = DATA.lenses, M = DATA.mechanisms, ROPES = DATA.ropes || [];
const LANGS = (DATA.languages || []).length ? DATA.languages : [{ id: 'en', label: 'English', dir: 'ltr' }];
const FIRST = LANGS[0].id;
let li = 0, mi = 0, lang = FIRST;
const $ = s => document.querySelector(s);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const G = m => m.glyph + '︎';
const fmt = s => esc(s).replace(/`([^`]+)`/g, '<code dir="ltr">$1</code>');
const hue = i => `hsl(${Math.round(i * 36 + 200) % 360} var(--hue-s) var(--hue-l))`;
const idx = id => M.findIndex(x => x.id === id);
const rtl = () => (LANGS.find(x => x.id === lang) || {}).dir === 'rtl';
// a word of the page, in the reader's language; `{name}` filled as text (T), or as markup already escaped (H)
const U = (k, l) => ((DATA.ui || {})[l || lang] || {})[k] ?? ((DATA.ui || {})[FIRST] || {})[k] ?? '';
const T = (k, v, l) => U(k, l).replace(/\{(\w+)\}/g, (x, n) => (v && n in v) ? v[n] : x);
const H = (k, v, l) => esc(U(k, l)).replace(/\{(\w+)\}/g, (x, n) => (v && n in v) ? v[n] : x);
// a lens's or a mechanism's own words, in the reader's language where they are written
const tr = (o, k) => (lang !== FIRST && o[lang] && o[lang][k] != null) ? o[lang][k] : o[k];
const num = n => Number(n).toLocaleString(lang);
const sep = () => rtl() ? '، ' : ', ';
const ropesOf = i => ROPES.filter(r => r.a === M[i].id || r.b === M[i].id)
  .map(r => ({ j: idx(r.a === M[i].id ? r.b : r.a), n: r.n, files: r.files })).sort((x, y) => y.n - x.n);
const maxN = Math.max(1, ...ROPES.map(r => r.n));

// the language axis
const lg = $('#langs');
const langButtons = LANGS.map(x => { const b = document.createElement('button'); b.textContent = x.label;
  b.setAttribute('lang', x.id); b.addEventListener('click', () => setLang(x.id)); lg.appendChild(b); return b; });
if (LANGS.length < 2) lg.hidden = true;

// axis L
const lb = $('#lenses');
const lensButtons = L.map((l, i) => { const b = document.createElement('button'); b.id = 'lens-' + l.id;
  b.addEventListener('click', () => go(i, mi)); lb.appendChild(b); return b; });
$('#lprev').onclick = () => go((li + L.length - 1) % L.length, mi);
$('#lnext').onclick = () => go((li + 1) % L.length, mi);
$('#mprev').onclick = () => go(li, (mi + M.length - 1) % M.length);
$('#mnext').onclick = () => go(li, (mi + 1) % M.length);

// axis M: ten nodes on a ring, a chord for every pair that shares files, weighted by how many
const svg = $('#dial'), NS = 'http://www.w3.org/2000/svg', C = 180, R = 122;
const pos = i => { const a = -Math.PI / 2 + i * 2 * Math.PI / M.length; return [C + R * Math.cos(a), C + R * Math.sin(a), a]; };
const el = (n, at) => { const e = document.createElementNS(NS, n); for (const k in at) e.setAttribute(k, at[k]); return e; };
const chords = ROPES.map(r => { const i = idx(r.a), j = idx(r.b), [x1, y1] = pos(i), [x2, y2] = pos(j);
  const cx = C + ((x1 + x2) / 2 - C) * .18, cy = C + ((y1 + y2) / 2 - C) * .18;
  const p = el('path', { d: `M${x1.toFixed(1)},${y1.toFixed(1)} Q${cx.toFixed(1)},${cy.toFixed(1)} ${x2.toFixed(1)},${y2.toFixed(1)}`, class: 'chord' });
  p.setAttribute('stroke-width', (0.6 + 5.4 * r.n / maxN).toFixed(2)); p.dataset.a = i; p.dataset.b = j;
  svg.appendChild(p); return p; });
const labels = [];
const nodes = M.map((m, i) => { const [x, y, a] = pos(i), g = el('g', { class: 'node', tabindex: '0', role: 'button' });
  g.style.setProperty('--h', hue(i));
  const ca = Math.cos(a), sa = Math.sin(a), lr = R + 26;
  const anchor = ca > .3 ? 'start' : ca < -.3 ? 'end' : 'middle';
  const l = el('text', { x: (C + lr * ca).toFixed(1), y: (C + lr * sa + 4 + (Math.abs(ca) <= .3 ? 6 * Math.sign(sa) : 0)).toFixed(1), class: 'l', 'text-anchor': anchor });
  labels.push(l);
  const t = el('text', { x, y: y + 5, class: 'g' }); t.textContent = G(m);
  g.append(el('circle', { cx: x, cy: y, r: 17 }), t, l);
  g.addEventListener('click', () => go(li, i));
  g.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(li, i); } });
  svg.appendChild(g); return g; });

function board(l, m, i) {
  const k = m.keeper || [], rs = ropesOf(i);
  const nr = k.reduce((s, x) => s + x.nrules, 0), nc = k.reduce((s, x) => s + x.checks, 0);
  const nums = T('nums', { parts: num(k.length), rules: num(nr), checks: num(nc), files: num(m.files) });
  const whys = tr(m, 'staples') || {};
  const staples = Object.keys(m.staples || {}).map(t => { const j = idx(t); if (j < 0) return '';
    return `<button class="staple" data-m="${j}" data-c="${j}"><i>${esc(G(M[j]))}</i><span>${esc(tr(M[j], 'name'))} <em>· ${esc(whys[t] || m.staples[t])}</em></span></button>`; }).join('');
  let body = '';
  if (l.id === 'person') body = `<p class="prose">${fmt(tr(m, 'person'))}</p>`;
  if (l.id === 'gardener') body = `<p class="prose">${fmt(tr(m, 'gardener'))}</p><p class="note">${H('gardener_note')}</p>`;
  if (l.id === 'agent') body = `<p class="note">${fmt(tr(m, 'agent_note'))}</p>
    <div><p class="label">${H('form_label')}</p><pre dir="ltr" lang="${FIRST}">${esc(m.form)}</pre></div>
    <div><p class="label">${H('refusal_label')}</p><div class="refusal" dir="ltr" lang="${FIRST}"><b>ERROR</b>${fmt(m.error)}${m.fix ? `<span class="fix">— ${fmt(m.fix)}</span>` : ''}</div></div>
    <p class="note">${H('proved_note')}</p>
    <pre class="cmd" dir="ltr" lang="${FIRST}">python3 bin/dmsave.py "&lt;who&gt;" "&lt;what changed&gt;" --body "- action: …"
python3 bin/dmsave.py --again</pre>`;
  if (l.id === 'keeper') body = `<p class="note">${H('keeper_note')}</p>
    <div class="items" dir="ltr" lang="${FIRST}">${k.map(x => `<div class="item"><div class="top"><code>${esc(x.name)}</code><span class="k">${esc(x.kind)}</span>
      <span class="n"><span>${H('item_rules', { n: x.nrules }, FIRST)}</span><span>${H('item_checks', { n: x.checks }, FIRST)}</span><span>${H('item_relations', { n: x.relations }, FIRST)}</span></span></div>
      ${x.meaning ? `<p>${fmt(x.meaning)}</p>` : ''}${x.reason ? `<p class="why">${fmt(x.reason)}</p>` : ''}
      ${x.rules.length ? `<ul>${x.rules.map(r => `<li>${esc(r)}</li>`).join('')}${x.nrules > x.rules.length ? `<li>${H('more_rules', { n: x.nrules - x.rules.length, cmd: 'python3 bin/dmrules.py' }, FIRST)}</li>` : ''}</ul>` : ''}
      ${x.suites.length ? `<p class="note small">${H('checked_in', { suites: x.suites.map(s => `<code>${esc(s)}</code>`).join(', ') }, FIRST)}</p>` : ''}</div>`).join('')}</div>
    <div><p class="label">${H('rope_label')}</p><div class="ropes">${rs.map(r =>
      `<button class="rope" data-m="${r.j}" data-c="${r.j}"><span class="who">${esc(G(M[r.j]))} ${esc(tr(M[r.j], 'short') || tr(M[r.j], 'name'))}</span>
       <span class="bar" data-w="${Math.max(6, Math.round(44 * r.n / maxN))}" title="${esc(T('rope_files', { n: num(r.n) }))}"></span>
       <span class="fs" dir="ltr">${r.n} · ${r.files.map(esc).join(', ')}</span></button>`).join('')}</div>
    <p class="note small ground">${H('ground', { files: (DATA.ground || []).map(f => `<code dir="ltr">${esc(f)}</code>`).join(sep()) })}</p></div>`;
  return `<div class="crumb"><span>${esc(tr(l, 'who'))} · ${esc(tr(m, 'short') || tr(m, 'name'))}</span><span class="nums">${esc(nums)}</span></div>
    <h2><span class="gl">${esc(G(m))}</span><span>${esc(tr(m, 'name'))}</span></h2><p class="q">${esc(tr(l, 'label'))}</p>${body}
    <div class="foot"><p class="label">${H('stapled')}</p><div class="staples">${staples}</div></div>`;
}

function go(l, m, quiet) {
  li = l; mi = m; const lens = L[l], mech = M[m], h = hue(m), rs = ropesOf(m), near = new Set(rs.map(r => r.j)), staple = new Set(Object.keys(mech.staples || {}).map(idx));
  lensButtons.forEach((b, i) => b.setAttribute('aria-pressed', i === l ? 'true' : 'false'));
  nodes.forEach((n, i) => { n.classList.toggle('on', i === m); n.classList.toggle('near', staple.has(i)); });
  chords.forEach(c => { const a = +c.dataset.a, b = +c.dataset.b, on = a === m || b === m;
    c.classList.toggle('on', on); c.classList.toggle('hot', on && (staple.has(a === m ? b : a))); c.style.setProperty('--h', h);
    if (on) svg.insertBefore(c, nodes[0]); });
  $('#cap').innerHTML = `<b>${esc(G(mech))} ${esc(tr(mech, 'name'))}</b><br>${H('cap', { n: num(near.size), f: num(mech.files) })}`;
  const b = $('#board'); b.style.setProperty('--h', h); b.innerHTML = board(lens, mech, m);
  b.querySelectorAll('[data-m]').forEach(s => s.addEventListener('click', () => go(li, +s.dataset.m)));
  b.querySelectorAll('[data-c]').forEach(e => e.style.setProperty('--c', hue(+e.dataset.c)));
  b.querySelectorAll('[data-w]').forEach(e => { e.style.width = e.dataset.w + 'px'; });
  if (!quiet) { try { history.replaceState(null, '', `#${lang === FIRST ? '' : lang + '-'}${lens.id}-${mech.id}`); } catch (e) {} }
}

// the language: every word of the page, the direction it reads in, and the digits it counts with
function setLang(x, quiet) {
  lang = LANGS.some(y => y.id === x) ? x : FIRST;
  const root = document.documentElement;
  root.lang = lang; root.dir = rtl() ? 'rtl' : 'ltr';
  langButtons.forEach(b => b.setAttribute('aria-pressed', b.getAttribute('lang') === lang ? 'true' : 'false'));
  document.querySelectorAll('[data-t]').forEach(e => { e.textContent = U(e.dataset.t); });
  document.querySelectorAll('[data-ta]').forEach(e => { e.setAttribute('aria-label', U(e.dataset.ta)); });
  const c = DATA.counts;
  $('#counts').textContent = T('counts', { terms: num(c.terms), registries: num(c.registries), relations: num(c.relations), reasons: num(c.reasons) });
  $('#boards').textContent = T('boards', { l: num(L.length), m: num(M.length), b: num(L.length * M.length) });
  lensButtons.forEach((b, i) => { b.innerHTML = `<b>${esc(tr(L[i], 'label'))}</b><span>${esc(tr(L[i], 'who'))}</span>`; });
  labels.forEach((t, i) => { t.textContent = tr(M[i], 'short') || tr(M[i], 'name'); });
  nodes.forEach((n, i) => n.setAttribute('aria-label', tr(M[i], 'name')));
  go(li, mi, quiet);
}

document.addEventListener('keydown', e => {
  if (e.altKey || e.ctrlKey || e.metaKey) return;
  const f = rtl() ? -1 : 1;
  const k = { ArrowRight: [0, f], ArrowLeft: [0, -f], ArrowDown: [1, 0], ArrowUp: [-1, 0] }[e.key];
  if (!k) return; e.preventDefault();
  go((li + k[0] + L.length) % L.length, (mi + k[1] + M.length) % M.length);
});
// where the reader arrives: the link's own lens, mechanism and language, else the browser's language where the page has it
const hm = /^#(?:([a-z]{2})-)?([a-z]+)-([a-z]+)$/.exec(location.hash || '');
const told = (navigator.language || '').toLowerCase().split('-')[0];
li = hm ? Math.max(0, L.findIndex(x => x.id === hm[2])) : 0;
mi = hm ? Math.max(0, idx(hm[3])) : 0;
setLang(hm && hm[1] ? hm[1] : (LANGS.some(y => y.id === told) ? told : FIRST), true);
})();
