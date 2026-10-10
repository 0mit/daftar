#!/usr/bin/env python3
"""view_report — the `view` asset's offline page: one self-contained HTML file that is both the page of drawings and
the AUTHOR MODE that edits what the page says.

THE PAGE. A Reference tab — the parts a reader looks up, each with the address the page chooses for it and, from the
understand lens on, the facts `view.fields` shows — and one tab per drawing, each mounted by the same runtime the
served page uses. A LENS switch — the law's `view_lenses`, orient · understand · operate · inspect — draws each lens in
its own form.

THE AUTHOR MODE ("Author" in the header) edits, in the browser, what the page's own terms say, and nothing else:
  - the drawings: their order, and each one's label;
  - per drawing: its story (purpose, outcome, stages, the beings and technologies of each), the question each lens asks,
    its live bindings and its actions;
  - the reference: which beings, in what order, the place system that stands for each, a line of what each is for;
  - which of a being's own facts a card shows, per genos, from which lens on.
A drawing, its archetype and what its shape reads stay as the page states them. The preview follows every change.
"Download" saves view-selection.json; bringing it into the ledger is

    python3 assets/view/bin/view.py import view-selection.json

which validates it, writes the page through safe, reads it back, and journals it. A draft survives a reload (the
browser's own storage); "Reset" returns to what the page says.

Usage:
  view report --out FILE      (required: a report is written where it is asked for, never inside the garden unasked)
"""
import datetime, html, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import view_model as vm
import view_kit as kit

SKIP_FIELDS = {"bean", "identity", "provenance", "nature", "responsibility", "open", "details", "genos"} | set(vm.TERMS)


def esc(s):
    return html.escape(str(s), quote=True)


def catalog():
    """Every bean: its genos, its organisation, and its own top-level facts, shortened — what the author mode chooses from."""
    out = {}
    for b in vm.bean_ids():
        f = vm.fm(b)
        if f:
            out[b] = {"genos": f.get("genos", ""), "org": vm.org_of(b), "title": vm._short(f.get("title", ""), 120),
                      "fields": {k: vm._short(v, 220) for k, v in f.items() if k not in SKIP_FIELDS}}
    return out


def units():
    """{unit: {q, f}} — every unit in force, for the runtime to format a value by."""
    out = {}
    for u in vm.law().UNITS:
        q, f = vm.unit(u)
        if f:
            out[u] = {"q": q, "f": f}
    return out


def payload():
    figs = vm.compose_all()
    views = {v["key"]: v for v in vm.views(figs)}
    pv = vm.page_view()
    k = vm.knowledge()
    ref = []
    for _i, r in vm.entries_of_view("reference"):
        b = r.get("being")
        f = vm.fm(b)
        ref.append({"being": b, "system": r.get("system") or "", "what": r.get("what") or "",
                    "address": vm.address(b, r.get("system")), "genos": f.get("genos", ""), "org": vm.org_of(b),
                    "title": vm._short(f.get("title", ""), 120)})
    return {
        "page": {"id": vm.PAGE, "title": str(vm.page().get("title") or vm.PAGE)},
        "garden": vm.garden_name(),
        "release": str(vm.fm_path(os.path.join(vm.ROOT, "GARDEN.md")).get("daftar_release") or ""),
        "opens_on": pv.get("opens_on") or "",
        "levels": vm.lenses(),
        "units": units(),
        "techcat": ({r["code"]: vm.tech(r["code"]) for r in k.rows("technology")} if k else {}),
        "views": views,
        "order": [key for key, _v in vm.views_raw() if key in views],
        "reference": ref,
        "where": dict(zip(("svg", "places"), vm.where_shown())),
        "palette_css": vm.palette_css(),
        "addresses": {r["being"]: vm.addresses(r["being"]) for r in ref if vm.fm(r["being"])},
        "beans": catalog(),
        "author": {"views": {key: {a: v.get(a) for a in vm.EDITABLE if v.get(a) is not None} for key, v in vm.views_raw()},
                   "bindings": {bk: b for bk, b in vm.entries("view_bindings")},
                   "reference": [dict(r) for _i, r in vm.entries_of_view("reference")],
                   "fields": [dict(f) for _i, f in vm.entries_of_view("fields")]},
    }


PAGE_CSS = """
:root{--bg:#0f1319;--panel:#161c24;--line:#2a3644;--fg:#e8edf3;--muted:#93a1b2;--accent:#ff9d4a;--nfill:#1c2530}
@media(prefers-color-scheme:light){:root{--bg:#eef2f6;--panel:#fff;--line:#cfd8e2;--fg:#17202b;--muted:#5a6a7b;--nfill:#f5f8fb}}
*{box-sizing:border-box}html,body{margin:0}body{background:var(--bg);color:var(--fg);font:14px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{position:sticky;top:0;z-index:20;background:var(--panel);border-bottom:1px solid var(--line);padding:12px 20px}
h1{font-size:17px;margin:0;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.pill{font:600 11px ui-monospace,monospace;color:var(--muted);border:1px solid var(--line);border-radius:6px;padding:1px 6px}
.sub{color:var(--muted);font-size:12px;margin-top:2px}
.bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:10px}
.tabs{display:flex;gap:4px;flex-wrap:wrap}
.tab,.seg button,.btn{padding:6px 12px;border:1px solid var(--line);border-radius:8px;background:transparent;color:var(--muted);cursor:pointer;font:600 13px system-ui}
.tab.active,.seg button.active{background:var(--accent);color:#1a1206;border-color:var(--accent)}
.seg{display:flex;gap:0}.seg button{border-radius:0;margin-left:-1px}.seg button:first-child{border-radius:8px 0 0 8px}.seg button:last-child{border-radius:0 8px 8px 0}
.forms{margin:12px 0;display:flex;gap:8px;flex-wrap:wrap}a.btn{text-decoration:none}
.btn.primary{border-color:var(--accent);color:var(--accent)}.btn.on{background:var(--accent);color:#1a1206}
.spacer{flex:1}
main{max-width:1180px;margin:0 auto;padding:20px}
.lead{color:var(--muted);margin:0 0 12px}
table.ref{border-collapse:collapse;width:100%;font-size:13px}
table.ref th{text-align:left;color:var(--muted);font-weight:600;border-bottom:1px solid var(--line);padding:7px 10px}
table.ref td{border-bottom:1px solid var(--line);padding:7px 10px;vertical-align:top}
.mono{font-family:ui-monospace,monospace}.ipc{color:var(--accent)}
.kd{color:var(--muted);font-size:12px}.kd b{color:var(--fg);font-weight:600}
.reffilter{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:0 0 12px}
select,input{background:var(--panel);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:5px 7px;font:inherit;font-size:13px}
.org{font:11px ui-monospace,monospace;border-radius:6px;padding:1px 7px;border:1px solid var(--line);color:var(--muted)}
.ffnote{color:var(--muted);font-size:11px;margin-left:auto;max-width:44ch}
#author{display:none;margin-top:18px;border:1px dashed var(--accent);border-radius:14px;padding:14px 16px;background:var(--panel)}
body.authoring #author{display:block}
#author h3{margin:14px 0 6px;font-size:14px;color:var(--accent);letter-spacing:.02em}
#author h3:first-child{margin-top:0}
#author table{border-collapse:collapse;width:100%;font-size:12.5px}
#author th{text-align:left;color:var(--muted);font-weight:600;border-bottom:1px solid var(--line);padding:5px 6px}
#author td{border-bottom:1px solid var(--line);padding:4px 6px;vertical-align:middle}
#author input.w{width:100%}#author .note{color:var(--muted);font-size:12px;margin:4px 0 8px}
#author .mini{padding:2px 7px;font-size:12px}
.addr-more{position:relative;display:inline-block;margin-left:4px;font:600 10.5px ui-monospace,monospace;color:var(--muted);border:1px solid var(--line);border-radius:6px;padding:0 5px;cursor:help;outline:none}
.addr-more .addr-tip{position:absolute;left:0;top:130%;z-index:30;min-width:240px;white-space:nowrap;background:var(--panel);color:var(--fg);border:1px solid var(--accent);border-radius:9px;padding:8px 10px;font:12px/1.6 ui-monospace,monospace;box-shadow:0 8px 28px rgba(0,0,0,.35);visibility:hidden;opacity:0}
.addr-more:hover .addr-tip,.addr-more:focus .addr-tip{visibility:visible;opacity:1}.addr-more .addr-tip b{color:var(--accent);font-weight:600}
#livebar{margin-top:6px}#livebar a{color:var(--accent)}
#toast{display:none;position:fixed;right:18px;bottom:18px;z-index:60;max-width:520px;white-space:pre-wrap;background:var(--panel);border:1px solid var(--accent);border-radius:10px;padding:10px 14px;font:12.5px ui-monospace,monospace;box-shadow:0 8px 28px rgba(0,0,0,.4)}
#toast.bad{border-color:#f85149}
#exportbox{white-space:pre;overflow:auto;max-height:220px;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px;font:11.5px ui-monospace,monospace}
"""

SCRIPT = r"""
const P = JSON.parse(document.getElementById('viewdata').textContent);
const LS = 'view-author-draft:' + P.page.id;
function fresh(){ return JSON.parse(JSON.stringify({order: P.order, views: (P.author||{}).views || {}, bindings: (P.author||{}).bindings || {},
  reference: (P.author||{}).reference || [], fields: (P.author||{}).fields || []})); }
let S = fresh(); try { const d = localStorage.getItem(LS); if (d && P.author) S = Object.assign(fresh(), JSON.parse(d)); } catch (e) {}
let level = ((P.levels||[]).find(l => l.form === 'schematic') || (P.levels||[])[0] || {}).id, tab = 'ref';
const HIST = {}, HISTT = {}, LIVE = P.live || null, VALS = {};
function lvDepth(){ const l = (P.levels||[]).find(x => x.id === level); return l ? +l.depth : 1; }
function toast(t, bad){ let d = document.getElementById('toast'); if (!d) { d = document.createElement('div'); d.id = 'toast'; document.body.appendChild(d); }
  d.className = bad ? 'bad' : ''; d.textContent = t; d.style.display = 'block'; clearTimeout(d._t); d._t = setTimeout(() => d.style.display = 'none', 12000); }
function doAction(a){
  if (!LIVE.actions) { toast('You may view but not act.', true); return; }
  if (!confirm(a.confirm + '\n\n(tool: ' + a.tool + ')')) return;
  // WHAT THE LAW ASKS FOR, ASKED: each input the action declares, given by the viewer; a reason where a grant asks one
  const inputs = {}; for (const i of (a.inputs || [])) { if (i.origin && i.origin.act && i.origin.act !== 'said') continue;
    const x = prompt((i.note || i.name) + (i.quantity ? ' (' + i.quantity + ')' : ''), ''); if (x === null) return; inputs[i.name] = x; }
  let reason = null; if (a.reason) { reason = prompt('The reason for running ' + a.tool + ' (recorded):', ''); if (!reason) return; }
  fetch('/api/action', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-View-CSRF': LIVE.csrf}, body: JSON.stringify({m: tab, el: a.el, inputs, reason})})
   .then(r => r.json().then(j => [r.status, j])).then(([st, j]) => toast(st !== 200 ? ('Refused: ' + j.error) : j.mode === 'dry-run' ? j.message : ('Ran ' + j.tool + ' — exit ' + j.rc + '\n' + (j.output || '').slice(-600)), st !== 200 || (j.rc && j.rc !== 0)))
   .catch(e => toast('Failed: ' + e, true)); }
// AN ENTRY FORM (24.0, N37): each attribute the law's form of the term asks, then the gate's answer, whatever it is
function doWrite(f){
  if (!LIVE.actions) { toast('You may view but not act.', true); return; }
  const v = P.views[tab] || {}; const bean = prompt('The being the ' + f.term + ' entry is written on:', v.draws_bean || ''); if (!bean) return;
  let entry = ''; if (f.keyed) { entry = prompt('A short kebab name for the entry:', ''); if (!entry) return; }
  const values = {}; for (const a of f.attrs) { const x = prompt(a.attr + (a.required ? ' (required)' : '') + (a.meaning ? ' — ' + a.meaning.slice(0, 160) : ''), '');
    if (x === null) return; if (x !== '') values[a.attr] = x; }
  fetch('/api/write', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-View-CSRF': LIVE.csrf}, body: JSON.stringify({m: tab, w: f.w, bean, entry, values})})
   .then(r => r.json().then(j => [r.status, j])).then(([st, j]) => toast(st !== 200 ? ('Refused: ' + j.error + (j.output ? '\n' + j.output.slice(-900) : '')) : 'Saved.\n' + (j.output || '').slice(-400), st !== 200))
   .catch(e => toast('Failed: ' + e, true)); }
function renderForms(){ const v = P.views[tab] || {}, op = v.operate || {}; if (tab === 'ref') return;
  const fs = LIVE ? (v.writes || []) : [], t = op.table; if (!fs.length && !t) return;
  const d = document.createElement('div'); d.className = 'forms';
  d.innerHTML = fs.map((f, i) => '<button class="btn" data-w="' + i + '">add ' + esc(f.term) + '</button>').join(' ') +
    (t ? ' <a class="btn" href="' + (LIVE ? '/api/csv?m=' + encodeURIComponent(tab) : esc((P.csv || {})[tab] || '')) + '" download>lines as CSV</a>' : '');
  $('#view').appendChild(d); d.querySelectorAll('[data-w]').forEach(b => b.onclick = () => doWrite(fs[+b.dataset.w])); }
function poll(){ if (!LIVE || tab === 'ref') return;
  fetch('/api/values?m=' + encodeURIComponent(tab)).then(r => r.status === 401 ? (location.href = '/login') : r.json()).then(j => { if (j && j.values) { VALS[tab] = j.values; mountView(); } }).catch(() => {});
  // history: once per tab for the sparklines, and again each minute where the drawing correlates values over time
  const corr = (((P.views[tab] || {}).operate || {}).correlate || []).length, age = Date.now() - (HISTT[tab] || 0);
  if (!HIST[tab] || (corr && age > 60000)) { HIST[tab] = HIST[tab] || {}; HISTT[tab] = Date.now(); fetch('/api/history?m=' + encodeURIComponent(tab)).then(r => r.ok ? r.json() : null).then(j => { if (j && j.history) { HIST[tab] = j.history; mountView(); } }).catch(() => {}); } }
const $ = s => document.querySelector(s), esc = s => String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function save(){ try { localStorage.setItem(LS, JSON.stringify(S)); } catch (e) {} }
function ed(k){ S.views[k] = S.views[k] || {}; return S.views[k]; }
function num(v){ return v == null || v === '' ? null : +v; }
// the drawing as the AUTHOR sees it now, draft included, over what the page draws
function viewFor(k){
  const v = P.views[k], e = S.views[k] || {}, byId = {}; v.elements.forEach(x => byId[x.id] = x);
  const binds = !P.author ? v.binds : Object.entries(S.bindings).filter(([bk, b]) => b.view === k && byId[b.element]).map(([bk, b]) => {
    const was = v.binds.find(x => x.id === bk) || {}, u = (P.units || {})[b.unit] || {};
    return Object.assign({}, was, {id: bk, el: b.element, live: b.live, name: b.label || byId[b.element].label, short: b.short || '',
      unit: b.unit || '', q: u.q || null, f: u.f || null, warn: num(b.warn), crit: num(b.crit), item_names: b.item_names || {}}); });
  return Object.assign({}, v, {title: esc(e.label || v.title), binds, story: storyFor(e) || v.story,
    questions: Object.fromEntries((e.questions || []).map(q => [q.lens, q.ask]))});
}
function storyFor(e){ if (!e.stages) return null; const F = {};
  const stages = e.stages.map(x => ({label: x.label || '', doer: x.doer || '', parts: (x.beings || []).map(b => ({title: b.being, role: ''})),
    tech: (x.uses || []).map(u => { const t = P.techcat[u.technology] || {code: u.technology, name: u.technology}; (t.fields || []).forEach(f => { (F[f.code] = F[f.code] || {scheme: '', code: f.code, label: f.label, path: [f.label], techs: []}).techs.includes(t.name) || F[f.code].techs.push(t.name); }); return t; })}));
  return {purpose: e.purpose || '', outcome: e.outcome || '', stages, fields: Object.values(F).sort((a, b) => a.code < b.code ? -1 : 1)};
}
function renderTabs(){
  $('#tabs').innerHTML = '<button class="tab'+(tab==='ref'?' active':'')+'" data-t="ref">Reference</button>' +
    S.order.filter(k => P.views[k]).map(k => '<button class="tab'+(tab===k?' active':'')+'" data-t="'+esc(k)+'">'+esc((S.views[k]||{}).label || P.views[k].title)+'</button>').join('');
  document.querySelectorAll('.tab').forEach(b => b.onclick = () => { tab = b.dataset.t; render(); });
}
function renderLenses(){
  $('#lens').innerHTML = (P.levels || []).map(l => '<button class="'+(level===l.id?'active':'')+'" data-l="'+esc(l.id)+'" title="'+esc(l.question)+'">'+esc(l.depth)+' · '+esc(l.name)+'</button>').join('');
  document.querySelectorAll('#lens button').forEach(b => b.onclick = () => { level = b.dataset.l; render(); });
}
function lensDepth(id){ const l = (P.levels||[]).find(x => x.id === id); return l ? +l.depth : 9; }
function renderRef(){
  const rows = S.reference.map(r => Object.assign({}, P.reference.find(x => x.being === r.being) || {}, r)).filter(r => P.beans[r.being]);
  const orgs = [...new Set(rows.map(r => (P.beans[r.being]||{}).org || ''))].sort();
  const gene = [...new Set(rows.map(r => (P.beans[r.being]||{}).genos || ''))].sort();
  const def = P.opens_on || '';
  let o = '<p class="lead">What each part is for and where to find it — deeper lenses add what its own record says.</p>';
  if (P.where && P.where.svg) o += '<h3>Where this page is shown — engraved from its own record</h3><div class="vw"><div class="vw-fig">' + P.where.svg + '</div></div>';
  o += '<div class="reffilter"><select id="f-org"><option value="">organisation: all</option>'+orgs.map(x => '<option value="'+esc(x)+'"'+(x===def?' selected':'')+'>'+esc(x || 'none derived')+'</option>').join('')+'</select>'+
       '<select id="f-genos"><option value="">genos: all</option>'+gene.map(x => '<option>'+esc(x)+'</option>').join('')+'</select>'+
       '<input id="f-q" type="search" placeholder="search"><span id="f-count" class="kd"></span>'+
       '<span class="ffnote">the organisation is read from ownership; a being none can be derived for belongs to none</span></div>';
  o += '<table class="ref"><thead><tr><th>being</th><th>address</th>'+(lvDepth()>=1?'<th>organisation</th><th>genos</th><th>for</th><th>from its record</th>':'')+'</tr></thead><tbody>';
  for (const r of rows) {
    const b = P.beans[r.being] || {fields:{}}, shown = S.fields.filter(f => f.genos === b.genos && lensDepth(f.shown_from) <= lvDepth() && b.fields[f.term] != null);
    const al = ((P.addresses || {})[r.being] || []).filter(x => x.address !== r.address);
    const tipA = al.length ? '<span class="addr-more" tabindex="0">+' + al.length + '<span class="addr-tip">' + al.map(x => '<b>' + esc(x.address) + '</b> ' + esc((x.what || []).join(' · '))).join('<br>') + '</span></span>' : '';
    o += '<tr data-org="'+esc(b.org || '')+'" data-genos="'+esc(b.genos)+'"><td class="mono">'+esc(r.being)+'</td><td class="mono ipc">'+esc(r.address || '')+' '+tipA+'</td>'+
         (lvDepth()>=1?'<td><span class="org">'+esc(b.org || 'none derived')+'</span></td><td>'+esc(b.genos)+'</td><td>'+esc(r.what)+'</td><td class="kd">'+shown.map(f => '<div><b>'+esc(f.term)+'</b> '+esc(b.fields[f.term])+'</div>').join('')+'</td>':'')+'</tr>';
  }
  o += '</tbody></table>';
  $('#view').innerHTML = o;
  const trs = [...document.querySelectorAll('.ref tbody tr')];
  function apply(){ const og = $('#f-org').value, g = $('#f-genos').value, q = $('#f-q').value.toLowerCase(); let n = 0;
    trs.forEach(tr => { const ok = (!og || tr.dataset.org===og) && (!g || tr.dataset.genos===g) && (!q || tr.textContent.toLowerCase().includes(q));
      tr.style.display = ok ? '' : 'none'; if (ok) n++; }); $('#f-count').textContent = n+' / '+trs.length+' shown'; }
  ['#f-org','#f-genos'].forEach(s => $(s).onchange = apply); $('#f-q').oninput = apply; apply();
}
function state(){ return {level, live: !!LIVE, values: VALS[tab] || {}, history: HIST[tab] || {}, onAction: LIVE ? doAction : null, historyUrl: LIVE && LIVE.history,
  onOpen: k => { if ((P.order || []).includes(k)) { tab = k; render(); } }}; }
function mountView(){ const root = document.querySelector('#view > div'); if (!root || tab === 'ref') return; window.viewMount(root, viewFor(tab), state()); }
function render(){
  renderTabs(); renderLenses(); if (LIVE) renderLive();
  if (tab === 'ref') renderRef();
  else { const root = document.createElement('div'); $('#view').innerHTML = ''; $('#view').appendChild(root);
    if (window.matchMedia && matchMedia('(prefers-color-scheme: light)').matches) root.classList.add('light');
    window.viewMount(root, viewFor(tab), state()); renderForms();
    if (LIVE && !VALS[tab]) poll(); }
  if (document.body.classList.contains('authoring')) renderAuthor();
}
/* ------------------------------ author mode ------------------------------ */
function sel(opts, cur, attrs){ return '<select '+attrs+'>'+opts.map(o => '<option value="'+esc(o[0])+'"'+(String(o[0])===String(cur)?' selected':'')+'>'+esc(o[1])+'</option>').join('')+'</select>'; }
const csv = v => v.split(',').map(x => x.trim()).filter(Boolean);
function renderAuthor(){
  let o = '<h3>Drawings — in what order, under what name</h3><table><thead><tr><th>order</th><th>key</th><th>label</th><th>draws</th></tr></thead><tbody>';
  S.order.forEach((k, i) => o += '<tr><td><button class="btn mini" data-mv="'+i+'" data-dir="-1">↑</button> <button class="btn mini" data-mv="'+i+'" data-dir="1">↓</button></td>'+
    '<td class="mono">'+esc(k)+'</td><td><input class="w" data-label="'+esc(k)+'" value="'+esc((S.views[k]||{}).label || '')+'" placeholder="'+esc(P.views[k] ? P.views[k].title : '')+'"></td><td class="kd">'+esc(P.views[k] ? P.views[k].source : '')+'</td></tr>');
  o += '</tbody></table>';
  if (tab !== 'ref') {
    const e = ed(tab), v = P.views[tab], st = e.stages || [];
    o += '<h3>'+esc(e.label || v.title)+' — the story (orient)</h3><p class="note">Plain words for a newcomer: what it guarantees, three to five stages in the order work flows, what is true when it works. '+
         'A technology is a code of the catalogue ('+Object.keys(P.techcat).length+' known), and opens its own documentation.</p>'+
         '<table><tbody><tr><td style="width:90px">purpose</td><td><input class="w" data-sf="purpose" value="'+esc(e.purpose)+'"></td></tr>'+
         '<tr><td>outcome</td><td><input class="w" data-sf="outcome" value="'+esc(e.outcome)+'"></td></tr></tbody></table>'+
         '<table><thead><tr><th>#</th><th>stage</th><th>who or what does it</th><th>beings</th><th>technologies</th><th></th></tr></thead><tbody>';
    st.forEach((x, i) => o += '<tr><td>'+(i+1)+'</td><td><input class="w" data-ss="'+i+'" data-f="label" value="'+esc(x.label)+'"></td><td><input class="w" data-ss="'+i+'" data-f="doer" value="'+esc(x.doer)+'"></td>'+
      '<td><input class="w" data-ss="'+i+'" data-f="beings" value="'+esc((x.beings||[]).map(b => b.being).join(', '))+'"></td>'+
      '<td><input class="w" data-ss="'+i+'" data-f="uses" list="techlist" value="'+esc((x.uses||[]).map(u => u.technology).join(', '))+'"></td><td><button class="btn mini" data-ssdel="'+i+'">✕</button></td></tr>');
    o += '</tbody></table><button class="btn mini" id="ssadd">+ stage</button><datalist id="techlist">'+Object.keys(P.techcat).map(c => '<option value="'+esc(c)+'">').join('')+'</datalist>';
    o += '<h3>the question each lens asks</h3><table><tbody>'+(P.levels||[]).map(l => { const q = (e.questions || []).find(x => x.lens === l.id) || {};
      return '<tr><td style="width:90px">'+esc(l.id)+'</td><td><input class="w" data-q="'+esc(l.id)+'" value="'+esc(q.ask || '')+'" placeholder="'+esc(l.question)+'"></td></tr>'; }).join('')+'</tbody></table>';
    const ids = v.elements.map(x => [x.id, x.id]), mine = Object.entries(S.bindings).filter(([bk, b]) => b.view === tab);
    o += '<h3>live bindings</h3><p class="note">A live-state reads whether a being answers its monitor; a live-value or a live-series is computed by a query in the monitor\'s own language. A unit is a row of the law\'s `units`.</p>'+
      '<table><thead><tr><th>key</th><th>on element</th><th>live</th><th>being</th><th>label</th><th>unit</th><th>warn</th><th>crit</th><th>technology</th><th>query</th><th></th></tr></thead><tbody>';
    mine.forEach(([bk, b]) => { const q = (b.query || [])[0] || {};
      o += '<tr><td class="mono">'+esc(bk)+'</td><td>'+sel(ids, b.element, 'data-b="'+esc(bk)+'" data-f="element"')+'</td><td>'+sel([['live-state','live-state'],['live-value','live-value'],['live-series','live-series']], b.live, 'data-b="'+esc(bk)+'" data-f="live"')+'</td>'+
        ['being','label','unit','warn','crit'].map(f => '<td><input class="w" data-b="'+esc(bk)+'" data-f="'+f+'" value="'+esc(b[f]==null?'':b[f])+'"></td>').join('')+
        '<td><input class="w" data-b="'+esc(bk)+'" data-f="technology" list="techlist" value="'+esc(q.technology || '')+'"></td><td><input class="w" data-b="'+esc(bk)+'" data-f="says" value="'+esc(q.says || '')+'"></td>'+
        '<td><button class="btn mini" data-bdel="'+esc(bk)+'">✕</button></td></tr>'; });
    o += '</tbody></table><button class="btn mini" id="badd">+ binding</button>';
    const acts = v.elements.filter(x => x.pattern === 'action');
    if (acts.length) {
      o += '<h3>actions</h3><p class="note">Where a button asks for which tool. What a tool RUNS is the host\'s configuration, never the page\'s.</p><table><thead><tr><th>button</th><th>tool</th><th>confirm</th><th>acts on</th></tr></thead><tbody>';
      acts.forEach(x => { const a = (e.actions || []).find(y => y.element === x.id) || {};
        o += '<tr><td class="mono">'+esc(x.id)+'</td>'+['tool','confirm','acts_on'].map(f => '<td><input class="w" data-act="'+esc(x.id)+'" data-f="'+f+'" value="'+esc(a[f] || '')+'"></td>').join('')+'</tr>'; });
      o += '</tbody></table>';
    }
  }
  o += '<h3>Reference — which beings, in what order, the system that stands for each, what each is for</h3><table><thead><tr><th>order</th><th>being</th><th>genos</th><th>system</th><th>for</th><th></th></tr></thead><tbody>';
  S.reference.forEach((r, i) => o += '<tr><td><button class="btn mini" data-rmv="'+i+'" data-dir="-1">↑</button> <button class="btn mini" data-rmv="'+i+'" data-dir="1">↓</button></td><td class="mono">'+esc(r.being)+'</td><td class="kd">'+esc((P.beans[r.being]||{}).genos)+'</td>'+
    '<td><input data-r="'+i+'" data-f="system" value="'+esc(r.system || '')+'"></td><td><input class="w" data-r="'+i+'" data-f="what" value="'+esc(r.what || '')+'"></td><td><button class="btn mini" data-rdel="'+i+'">✕</button></td></tr>');
  const notIn = Object.keys(P.beans).filter(b => !S.reference.some(r => r.being === b)).sort();
  o += '</tbody></table>'+sel([['','+ add a being…']].concat(notIn.map(b => [b, b+'  ('+P.beans[b].genos+')'])), '', 'id="radd"');
  const gene = [...new Set(Object.values(P.beans).map(b => b.genos).filter(Boolean))].sort();
  o += '<h3>Facts on a card — per genos, which of a being\'s own facts show, from which lens on</h3>';
  gene.forEach(g => { const terms = [...new Set(Object.values(P.beans).filter(b => b.genos === g).flatMap(b => Object.keys(b.fields)))].sort();
    o += '<div style="overflow-x:auto"><table><thead><tr><th style="width:140px">'+esc(g)+'</th>'+terms.map(t => '<th>'+esc(t)+'</th>').join('')+'</tr></thead><tbody><tr><td class="kd">from lens</td>'+
      terms.map(t => { const f = S.fields.find(x => x.genos === g && x.term === t) || {}; return '<td>'+sel([['','—']].concat((P.levels||[]).map(l => [l.id, l.id])), f.shown_from || '', 'data-kg="'+esc(g)+'" data-kt="'+esc(t)+'"')+'</td>'; }).join('')+'</tr></tbody></table></div><br>'; });
  o += '<h3>Export</h3><p class="note">Download the selection, then bring it into the ledger: <span class="mono">python3 assets/view/bin/view.py import view-selection.json</span> — it validates it, writes the page through safe, reads it back and journals it.</p>'+
       '<button class="btn primary" id="dl">Download view-selection.json</button> <button class="btn" id="cp">Copy</button> <button class="btn" id="reset">Reset to the page</button> <span id="dirty" class="kd"></span><div id="exportbox"></div>';
  $('#author').innerHTML = o;
  const ex = exportOf(S); $('#exportbox').textContent = JSON.stringify(ex, null, 1);
  $('#dirty').textContent = JSON.stringify(ex) === JSON.stringify(exportOf(fresh())) ? 'no change from the page' : 'changed from the page — export and import to keep it';
  wire();
}
function exportOf(s){ return {order: s.order, views: s.views, bindings: s.bindings, reference: s.reference, fields: s.fields}; }
function wire(){
  const A = s => document.querySelectorAll('#author '+s), go = () => { save(); render(); };
  A('[data-mv]').forEach(b => b.onclick = () => { const i = +b.dataset.mv, j = i + +b.dataset.dir; if (j<0||j>=S.order.length) return; [S.order[i], S.order[j]] = [S.order[j], S.order[i]]; go(); });
  A('[data-label]').forEach(c => c.onchange = () => { const e = ed(c.dataset.label); if (c.value) e.label = c.value; else delete e.label; go(); });
  A('[data-sf]').forEach(c => c.onchange = () => { ed(tab)[c.dataset.sf] = c.value; go(); });
  A('[data-ss]').forEach(c => c.onchange = () => { const x = ed(tab).stages[+c.dataset.ss], f = c.dataset.f;
    if (f === 'beings') x.beings = csv(c.value).map(b => ({being: b})); else if (f === 'uses') x.uses = csv(c.value).map(t => ({technology: t})); else x[f] = c.value;
    if (x.beings && !x.beings.length) delete x.beings; if (x.uses && !x.uses.length) delete x.uses; go(); });
  A('[data-ssdel]').forEach(c => c.onclick = () => { ed(tab).stages.splice(+c.dataset.ssdel, 1); go(); });
  const sa = $('#ssadd'); if (sa) sa.onclick = () => { const e = ed(tab); e.stages = e.stages || []; e.stages.push({label: '', doer: ''}); go(); };
  A('[data-q]').forEach(c => c.onchange = () => { const e = ed(tab); e.questions = (e.questions || []).filter(q => q.lens !== c.dataset.q); if (c.value) e.questions.push({lens: c.dataset.q, ask: c.value}); go(); });
  A('[data-b]').forEach(c => c.onchange = () => { const b = S.bindings[c.dataset.b], f = c.dataset.f;
    if (f === 'technology' || f === 'says') { const q = (b.query || [])[0] || {}; q[f] = c.value; b.query = q.technology ? [q] : []; if (!b.query.length) delete b.query; }
    else if (c.value === '') delete b[f]; else b[f] = c.value; go(); });
  A('[data-bdel]').forEach(c => c.onclick = () => { delete S.bindings[c.dataset.bdel]; go(); });
  const ba = $('#badd'); if (ba) ba.onclick = () => { let n = 1; while (S.bindings[tab + '-' + n]) n++; S.bindings[tab + '-' + n] = {view: tab, element: P.views[tab].elements[0].id, live: 'live-state'}; go(); };
  A('[data-act]').forEach(c => c.onchange = () => { const e = ed(tab); e.actions = (e.actions || []).filter(x => x.element !== c.dataset.act);
    const cur = {element: c.dataset.act}; A('[data-act="' + c.dataset.act + '"]').forEach(i => { if (i.value) cur[i.dataset.f] = i.value; });
    if (cur.tool) e.actions.push(cur); go(); });
  A('[data-rmv]').forEach(b => b.onclick = () => { const i = +b.dataset.rmv, j = i + +b.dataset.dir; if (j<0||j>=S.reference.length) return; [S.reference[i], S.reference[j]] = [S.reference[j], S.reference[i]]; go(); });
  A('[data-r]').forEach(c => c.onchange = () => { const r = S.reference[+c.dataset.r]; if (c.value) r[c.dataset.f] = c.value; else delete r[c.dataset.f]; go(); });
  A('[data-rdel]').forEach(c => c.onclick = () => { S.reference.splice(+c.dataset.rdel, 1); go(); });
  $('#radd').onchange = e => { if (e.target.value) { S.reference.push({being: e.target.value}); go(); } };
  A('[data-kg]').forEach(c => c.onchange = () => { S.fields = S.fields.filter(f => !(f.genos === c.dataset.kg && f.term === c.dataset.kt));
    if (c.value) S.fields.push({genos: c.dataset.kg, term: c.dataset.kt, shown_from: c.value}); go(); });
  $('#dl').onclick = () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(exportOf(S), null, 1)], {type: 'application/json'})); a.download = 'view-selection.json'; a.click(); };
  $('#cp').onclick = () => navigator.clipboard && navigator.clipboard.writeText(JSON.stringify(exportOf(S), null, 1));
  $('#reset').onclick = () => { S = fresh(); try { localStorage.removeItem(LS); } catch (e) {} render(); };
}
function renderLive(){
  $('#livebar').innerHTML = 'live · signed in as <b>' + esc(LIVE.user) + '</b> · ledger ' + esc(LIVE.head) +
    (LIVE.history && P.views[tab] ? ' · <a href="' + esc(LIVE.history) + '/d/' + esc(P.views[tab].uid) + '" target="_blank" rel="noopener">history ↗</a>' : '') + ' · <a href="/logout">sign out</a>'; }
if (LIVE || !P.author) { $('#authbtn').style.display = 'none'; }
if (LIVE) { setInterval(poll, (LIVE.poll || 30) * 1000); }
$('#authbtn').onclick = () => { document.body.classList.toggle('authoring'); $('#authbtn').classList.toggle('on'); render(); };
render();
"""


# where each order runs on the page: the law's rows and the one module that reads them (widgets/direction.js)
DIRECTION_JS = open(os.path.join(HERE, "widgets", "direction.js"), encoding="utf-8").read()


def build_html(p):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    title = esc(p["page"]["title"])
    data = json.dumps(p, ensure_ascii=False).replace("</", "<\\/")
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>%s</title><style>%s%s</style></head><body>'
            '<header><h1>%s <span class="pill">%s</span></h1><div class="sub">how the parts work together · %s · daftar %s · drawn %s · '
            'a word with a dotted underline, and a part of a drawing, carry a definition — hover or tap</div>'
            '<div class="bar"><div class="tabs" id="tabs"></div><span class="spacer"></span><span class="kd">lens</span>'
            '<div class="seg" id="lens"></div><button class="btn" id="authbtn">Author</button></div><div id="livebar" class="kd"></div></header>'
            '<main><div id="view"></div><section id="author"></section></main>'
            '<script type="application/json" id="viewdata">%s</script>'
            '<script type="application/json" id="orientations">%s</script><script>%s</script><script>%s</script><script>%s</script></body></html>'
            % (title, PAGE_CSS, kit.SCHEMA_CSS + p.get("palette_css", ""), title, esc(p["page"]["id"]), esc(p.get("garden", "")), esc(p.get("release", "")),
               stamp, data, json.dumps(vm.orientations()).replace("</", "<\\/"), DIRECTION_JS, kit.RUNTIME_JS, SCRIPT))


def main(args):
    bad = [a for a in args if a.startswith("-") and a not in ("--out",)]
    if bad:
        print("view report: unknown arguments %s — nothing written" % bad, file=sys.stderr)
        sys.exit(2)
    if "--out" not in args or args.index("--out") + 1 >= len(args):
        print("view report: --out FILE is required — a report is written where it is asked for; nothing written",
              file=sys.stderr)
        sys.exit(2)
    errs, warns = vm.check()
    for w in warns:
        print("  warn: " + w)
    if errs:
        print("view report: the page and its drawings disagree — nothing written:", file=sys.stderr)
        for e in errs:
            print("  - " + e, file=sys.stderr)
        sys.exit(2)
    out = args[args.index("--out") + 1]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    p = payload()
    import view_export
    stem = os.path.splitext(out)[0]
    csvs, p["csv"] = [], {}
    for key, t in view_export.tables().items():
        with open("%s.%s.csv" % (stem, key), "w", encoding="utf-8", newline="") as fh:
            fh.write(view_export.csv_text(t))
        csvs.append("%s.%s.csv" % (stem, key))
        p["csv"][key] = os.path.basename(csvs[-1])
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(vm.surface("html").render(p))           # the surface of one file
    print("view report: %d drawings + reference + author mode -> %s%s" % (len(p["views"]), out,
          "" if not csvs else "; %d table(s) as CSV beside it" % len(csvs)))
