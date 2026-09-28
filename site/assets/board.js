// The one page's script: it reads the data site/board.py wrote into site/index.html, and draws the boards.
const DATA = JSON.parse(document.getElementById('data').textContent);
(function(){
const L = DATA.lenses, M = DATA.mechanisms, ROPES = DATA.ropes || [];
let li = 0, mi = 0;
const $ = s => document.querySelector(s);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const G = m => m.glyph + '\uFE0E';
const fmt = s => esc(s).replace(/`([^`]+)`/g, '<code>$1</code>');
const hue = i => `hsl(${Math.round(i * 36 + 200) % 360} var(--hue-s) var(--hue-l))`;
const idx = id => M.findIndex(x => x.id === id);
const ropesOf = i => ROPES.filter(r => r.a === M[i].id || r.b === M[i].id)
  .map(r => ({ j: idx(r.a === M[i].id ? r.b : r.a), n: r.n, files: r.files })).sort((x, y) => y.n - x.n);
const maxN = Math.max(1, ...ROPES.map(r => r.n));
$('#counts').textContent = `${DATA.counts.terms} terms · ${DATA.counts.registries} registries · ${DATA.counts.relations.toLocaleString('en')} relations · ${DATA.counts.reasons} reasons`;

// axis L
const lb = $('#lenses');
L.forEach((l, i) => { const b = document.createElement('button'); b.id = 'lens-' + l.id;
  b.innerHTML = `<b>${esc(l.label)}</b><span>${esc(l.who)}</span>`; b.addEventListener('click', () => go(i, mi)); lb.appendChild(b); });
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
const nodes = M.map((m, i) => { const [x, y, a] = pos(i), g = el('g', { class: 'node', tabindex: '0', role: 'button', 'aria-label': m.name });
  g.style.setProperty('--h', hue(i));
  const ca = Math.cos(a), sa = Math.sin(a), lr = R + 26;
  const anchor = ca > .3 ? 'start' : ca < -.3 ? 'end' : 'middle';
  const l = el('text', { x: (C + lr * ca).toFixed(1), y: (C + lr * sa + 4 + (Math.abs(ca) <= .3 ? 6 * Math.sign(sa) : 0)).toFixed(1), class: 'l', 'text-anchor': anchor });
  l.textContent = m.short || m.name;
  const t = el('text', { x, y: y + 5, class: 'g' }); t.textContent = G(m);
  g.append(el('circle', { cx: x, cy: y, r: 17 }), t, l);
  g.addEventListener('click', () => go(li, i));
  g.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(li, i); } });
  svg.appendChild(g); return g; });

function board(l, m, i) {
  const k = m.keeper || [], rs = ropesOf(i);
  const nr = k.reduce((s, x) => s + x.nrules, 0), nc = k.reduce((s, x) => s + x.checks, 0);
  const nums = `${k.length} parts of the law · ${nr} rules · ${nc} checks · ${m.files} files of its own`;
  const staples = Object.entries(m.staples || {}).map(([t, why]) => { const j = idx(t); if (j < 0) return '';
    return `<button class="staple" data-m="${j}" data-c="${j}"><i>${esc(G(M[j]))}</i><span>${esc(M[j].name)} <em>· ${esc(why)}</em></span></button>`; }).join('');
  let body = '';
  if (l.id === 'person') body = `<p class="prose">${fmt(m.person)}</p>`;
  if (l.id === 'gardener') body = `<p class="prose">${fmt(m.gardener)}</p>
    <p class="note">You talk and the agent writes. What an agent may not decide, it asks you, and it carries on with the rest.</p>`;
  if (l.id === 'agent') body = `<p class="note">${fmt(m.agent_note)}</p>
    <div><p class="label">the form, as the gate passed it</p><pre>${esc(m.form)}</pre></div>
    <div><p class="label">written wrong, the gate printed</p><div class="refusal"><b>ERROR</b>${fmt(m.error)}${m.fix ? `<span class="fix">— ${fmt(m.fix)}</span>` : ''}</div></div>
    <p class="note">Both were proved when this page was built: the form in a garden grown from the release, where the gate passed it, and the refusal by breaking it once. Save with <code>python3 bin/dmsave.py "&lt;who&gt;" "&lt;what changed&gt;" --body "- action: …"</code>; after a refusal, fix what it names and run <code>python3 bin/dmsave.py --again</code>.</p>`;
  if (l.id === 'keeper') body = `<p class="note">Each part of the law this mechanism is made of, as the release states it: what it means, why it is so, the rules the gate derives from it, and the suites that check it.</p>
    <div class="items">${k.map(x => `<div class="item"><div class="top"><code>${esc(x.name)}</code><span class="k">${esc(x.kind)}</span>
      <span class="n"><span>${x.nrules} rules</span><span>${x.checks} checks</span><span>${x.relations} relations</span></span></div>
      ${x.meaning ? `<p>${fmt(x.meaning)}</p>` : ''}${x.reason ? `<p class="why">${fmt(x.reason)}</p>` : ''}
      ${x.rules.length ? `<ul>${x.rules.map(r => `<li>${esc(r)}</li>`).join('')}${x.nrules > x.rules.length ? `<li>and ${x.nrules - x.rules.length} more: python3 bin/dmrules.py</li>` : ''}</ul>` : ''}
      ${x.suites.length ? `<p class="note small">checked in ${x.suites.map(s => `<code>${esc(s)}</code>`).join(', ')}</p>` : ''}</div>`).join('')}</div>
    <div><p class="label">the rope: the files that hold it with each other mechanism</p><div class="ropes">${rs.map(r =>
      `<button class="rope" data-m="${r.j}" data-c="${r.j}"><span class="who">${esc(G(M[r.j]))} ${esc(M[r.j].short || M[r.j].name)}</span>
       <span class="bar" data-w="${Math.max(6, Math.round(44 * r.n / maxN))}" title="${r.n} files"></span>
       <span class="fs">${r.n} · ${r.files.map(esc).join(', ')}</span></button>`).join('')}</div>
    <p class="note small ground">Held by every mechanism, and so left out of the chords: ${(DATA.ground || []).map(f => `<code>${esc(f)}</code>`).join(', ')}.</p></div>`;
  return `<div class="crumb"><span>${esc(l.who)} · ${esc(m.short || m.name)}</span><span class="nums">${esc(nums)}</span></div>
    <h2><span class="gl">${esc(G(m))}</span><span>${esc(m.name)}</span></h2><p class="q">${esc(l.label)}</p>${body}
    <div class="foot"><p class="label">stapled to</p><div class="staples">${staples}</div></div>`;
}

function go(l, m, quiet) {
  li = l; mi = m; const lens = L[l], mech = M[m], h = hue(m), rs = ropesOf(m), near = new Set(rs.map(r => r.j)), staple = new Set(Object.keys(mech.staples || {}).map(idx));
  [...lb.children].forEach((b, i) => b.setAttribute('aria-pressed', i === l ? 'true' : 'false'));
  nodes.forEach((n, i) => { n.classList.toggle('on', i === m); n.classList.toggle('near', staple.has(i)); });
  chords.forEach(c => { const a = +c.dataset.a, b = +c.dataset.b, on = a === m || b === m;
    c.classList.toggle('on', on); c.classList.toggle('hot', on && (staple.has(a === m ? b : a))); c.style.setProperty('--h', h);
    if (on) svg.insertBefore(c, nodes[0]); });
  $('#cap').innerHTML = `<b>${esc(G(mech))} ${esc(mech.name)}</b><br>held with ${near.size} others by ${mech.files} files`;
  const b = $('#board'); b.style.setProperty('--h', h); b.innerHTML = board(lens, mech, m);
  b.querySelectorAll('[data-m]').forEach(s => s.addEventListener('click', () => go(li, +s.dataset.m)));
  b.querySelectorAll('[data-c]').forEach(e => e.style.setProperty('--c', hue(+e.dataset.c)));
  b.querySelectorAll('[data-w]').forEach(e => { e.style.width = e.dataset.w + 'px'; });
  if (!quiet) { try { history.replaceState(null, '', `#${lens.id}-${mech.id}`); } catch (e) {} }
}
document.addEventListener('keydown', e => {
  if (e.altKey || e.ctrlKey || e.metaKey) return;
  const k = { ArrowRight: [0, 1], ArrowLeft: [0, -1], ArrowDown: [1, 0], ArrowUp: [-1, 0] }[e.key];
  if (!k) return; e.preventDefault();
  go((li + k[0] + L.length) % L.length, (mi + k[1] + M.length) % M.length);
});
const hm = /^#([a-z]+)-([a-z]+)$/.exec(location.hash || '');
go(hm ? Math.max(0, L.findIndex(x => x.id === hm[1])) : 0, hm ? Math.max(0, idx(hm[2])) : 0, true);
})();
