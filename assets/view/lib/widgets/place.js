// place (core/law/values.yaml: place): where something is — by coordinates in a named system, or by an identifier
// resolved through them (a map's element, a gazetteer's feature) — taken in through a place lookup (the design's §12).
// Suggestions while a person types, each a main line (the place's own words) and a secondary one (where it is, and
// from whom): the garden's own places first, then what the machine holds, then what a place service beyond it finds,
// when the host asks one. The reader's own position goes with a lookup only when they ask for it, and is stored
// nowhere: it lives in the field while the page is open. Offline, the garden's own places answer alone.
//
// WHAT LANDS is a place as the law writes one. A place of the garden lands as the being it is (`at: <bean>`): its
// coordinates stay said once, in its own bean. Any other lands as a coordinate in its reference system, WGS 84
// (`EPSG:4326;<lat>,<lon>`, the ensemble the law states accurate to 2 m), with the identifier it was read from beside
// it (`osm:way/42`, `geonames:112931`) and the source it was read from, for the save's `read` — never as a `name`:
// a map's element says which object was meant, never which being. A position typed with its system is taken as
// written; a bare coordinate is refused, since a coordinate is never bare.
//
// NOTHING ABOUT WHERE A PERSON WILL BE IS SENT: a field the host marks `sealed` (a happening's place, a place held
// off git) is looked up on the machine alone, and the place service beyond it is never asked.
import { h, mount } from './safe.js';
import { say, toAscii, langOf } from './locale.js';
import { plain } from './number.js';
import { settings } from './settings.js';
const IMPL = 'place';
export { IMPL as implements };

// What OpenStreetMap, GeoNames and Photon give: WGS 84, latitude first — the law's row `EPSG:4326` (places.yaml).
const WGS84 = 'EPSG:4326';
const COORD = /^([A-Z][A-Z0-9_]*:[0-9]+(?:\+[0-9]+)?);(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)(?:,(-?\d+(?:\.\d+)?))?(?:@(\d{4}(?:\.\d+)?))?$/;
const OSM = /^osm:(node|way|relation)\/([1-9][0-9]*)$/;
const GEONAMES = /^geonames:([1-9][0-9]{0,9})$/;
const TAGGED = /^[A-Za-z][A-Za-z0-9_-]*:\S/;
const BARE = /^-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?$/;

// what one position says, for showing it
export function parse(p) {
  const s = String(p ?? '');
  let m = COORD.exec(s);
  if (m) return {is: 'coordinate', crs: m[1], a: m[2], b: m[3], c: m[4] || '', epoch: m[5] || ''};
  if ((m = OSM.exec(s))) return {is: 'osm', element: m[1] + '/' + m[2]};
  if ((m = GEONAMES.exec(s))) return {is: 'geonames', id: m[1]};
  return {is: 'other', text: s};
}

// THE FOLD a lookup of the garden's own places matches by: what a keyboard, a phone or a habit changes and a reader
// does not — compatibility forms (NFKC), case, marks, the reader's digits, and the letters one script writes two ways
// (an Arabic and a Persian yeh or kaf, a teh marbuta and a heh, an alef with a hamza or a madda and one without), each
// pair read as one. Written as escapes: an invisible difference is easy to lose in source.
const SAME = {'\u064A': '\u06CC', '\u0649': '\u06CC', '\u0626': '\u06CC', '\u0643': '\u06A9', '\u0629': '\u0647',
  '\u06C0': '\u0647', '\u0622': '\u0627', '\u0623': '\u0627', '\u0625': '\u0627', '\u0671': '\u0627', '\u0624': '\u0648'};
export function fold(s) {
  const t = toAscii(String(s ?? '').normalize('NFKC')).toLocaleLowerCase('und').normalize('NFKD')
    .replace(/\p{M}/gu, '').replace(/[\u064A\u0649\u0626\u0643\u0629\u06C0\u0622\u0623\u0625\u0671\u0624]/g, c => SAME[c]);
  return t.replace(/[\u200C\u200D\u0640]/g, ' ').split(/[^\p{L}\p{N}]+/u).filter(Boolean);
}

// the garden's own places a page carries, matched here: every word typed begins a word of its title; a title that is
// what was typed first, then one that begins with it, then the rest in the page's order
export function own(query, places, limit = 8) {
  const q = fold(query);
  if (!q.length) return [];
  const out = [];
  (places || []).forEach((p, i) => {
    const words = fold(p.title || p.id), joined = words.join(' '), typed = q.join(' ');
    if (!q.every(w => words.some(x => x.startsWith(w)))) return;
    out.push({p, rank: joined === typed ? 0 : joined.startsWith(typed) ? 1 : 2, i});
  });
  return out.sort((a, b) => a.rank - b.rank || a.i - b.i).slice(0, limit).map(x => fromOwn(x.p));
}

// A SUGGESTION, whatever answered it: its lines, where it is, and what lands if it is picked.
//   source   own (the garden's), here (this machine's), far (a place service beyond it)
//   at       the positions that land; read: {from, through}, the source the place was read from (none for the
//            garden's own: it is the being itself)
function fromOwn(p) {
  return {source: 'own', key: 'own:' + p.id, label: p.title || p.id, detail: p.detail || '', what: p.kind || '',
          point: p.point || null, osm: p.osm || '', at: [p.id], read: null};
}
// a degree as a coordinate writes it: the digits the source gave, never an exponent (a number near zero prints as 1e-7)
const degrees = x => /e/i.test(String(x)) ? x.toFixed(12).replace(/\.?0+$/, '') : String(x);
// the garden's own place as a host answers it (daftard's /api/places: its bean as `code`, its title as `label`)
function fromHost(a) {
  return {source: 'own', key: 'own:' + a.code, label: a.label || a.code, detail: a.detail || '', what: a.kind || '',
          point: a.point || null, osm: a.osm || '', at: [a.code], read: null};
}
function fromAnswer(a, source, credit) {
  const ok = Array.isArray(a.point) && a.point.length === 2 && a.point.every(Number.isFinite)
    && Math.abs(a.point[0]) <= 90 && Math.abs(a.point[1]) <= 180;
  const point = ok ? a.point : null;
  const at = point ? [WGS84 + ';' + degrees(point[0]) + ',' + degrees(point[1])] : [];
  if (a.osm && OSM.test('osm:' + a.osm)) at.push('osm:' + a.osm);
  if (a.geonames && GEONAMES.test('geonames:' + a.geonames)) at.push('geonames:' + a.geonames);
  const named = a.osm ? 'OpenStreetMap ' + a.osm : a.geonames ? 'GeoNames ' + a.geonames : (credit.name || 'a place search');
  return {source, key: a.osm ? 'osm:' + a.osm : a.geonames ? 'geonames:' + a.geonames : source + ':' + (a.code || a.label),
          label: a.label || '', detail: a.detail || '', what: a.kind || '', point, osm: a.osm || '', at,
          read: point ? {from: credit.url ? {someone: 'org', at: 'uri:' + credit.url} : {someone: 'org'},
                         through: named + ', ' + (source === 'here' ? 'as this machine\u2019s place search holds it'
                           : 'as a place service beyond this machine found it') + (credit.attribution ? ' (' + credit.attribution
                           + (credit.licence ? ', ' + credit.licence : '') + ')' : '')} : null};
}

// suggestions, in the order they are offered: the garden's own first, then this machine's, then those from beyond it;
// a place offered twice (one map element, one feature) is offered once, where it came first; a place that would land
// nowhere (no coordinate, no being) is not offered
export function merge(answers = {}) {
  const credit = list => ((list || [])[0]) || {};
  const out = [], seen = new Set();
  const add = s => { if (!seen.has(s.key) && s.at.length && (s.source === 'own' || s.at.some(p => COORD.test(p)))) { seen.add(s.key); out.push(s); } };
  (answers.own || []).forEach(a => add(a.source === 'own' ? a : fromHost(a)));
  (answers.here || []).forEach(a => add(fromAnswer(a, 'here', credit(answers.hereSources))));
  (answers.far || []).forEach(a => add(fromAnswer(a, 'far', credit(answers.farSources))));
  return out;
}

// a coordinate in the reader's digits, in a left-to-right isolate, and what the law says of its system's accuracy, in
// the reader's words and in their own direction (in Persian, its metre reads right to left)
function coordinate(p, o) {
  const d = x => plain(x, {lang: o.lang, group: false}) || x;
  const row = (settings.crs || []).find(r => r && r.crs === p.crs);
  let acc = '';
  if (row && row.accuracy && row.accuracy.count) {
    try {
      acc = new Intl.NumberFormat(langOf(o), {style: 'unit', unit: String(row.accuracy.unit).replace(/^[a-z]+-/, ''),
        unitDisplay: 'short'}).format(Number(row.accuracy.count));
    } catch { acc = (d(row.accuracy.count) + ' ' + row.accuracy.unit); }
  }
  return h`<bdi dir="ltr" class="w-place-coord">${d(p.a)}, ${d(p.b)}${p.c ? h`, ${d(p.c)}` : ''}</bdi> <span class="w-place-crs"><bdi dir="ltr">${row && row.name || p.crs}</bdi>${acc ? h` <bdi dir="auto">\u00B1${acc}</bdi>` : ''}</span>`;
}

// options: lang; label (the place's own words, where a page knows them); titleOf (a bean's title, for a place of
// the garden)
export function show(v, o = {}) {
  const list = (Array.isArray(v) ? v : [v]).filter(x => x !== undefined && x !== null && x !== '');
  if (!list.length) return h`<span class="w-none">${o.empty ?? '\u2014'}</span>`;
  const parts = list.map(x => {
    const p = parse(x);
    if (p.is === 'coordinate') return coordinate(p, o);
    if (p.is === 'osm') return h`<bdi dir="ltr" class="w-place-id">OpenStreetMap ${p.element}</bdi>`;
    if (p.is === 'geonames') return h`<bdi dir="ltr" class="w-place-id">GeoNames ${p.id}</bdi>`;
    const title = o.titleOf && o.titleOf(p.text);
    return title ? h`<bdi dir="auto" class="w-being">${title}</bdi>` : h`<bdi dir="ltr" class="w-place-id">${p.text}</bdi>`;
  });
  const main = o.label ? h`<bdi dir="auto" class="w-place-main">${o.label}</bdi>` : '';
  return h`<span class="w-place-value">${main}${main ? h`<span class="w-place-sub">${parts.map((x, i) => i ? h` \u00B7 ${x}` : x)}</span>` : parts.map((x, i) => i ? h` \u00B7 ${x}` : x)}</span>`;
}
export const text = v => '\u2068' + (Array.isArray(v) ? v : [v]).join(' \u00B7 ') + '\u2069';

// What a field holds when it is saved: a suggestion picked (its positions, and the source it was read from), or what
// was typed — a position with its system, as written; a bare coordinate, never. options: required; free (a position
// of any system may be typed, and the gate judges it: a `be` that is a time, not a place)
export function take(input, o = {}) {
  if (input && typeof input === 'object' && Array.isArray(input.at)) {
    return input.at.length ? {value: input.at.slice(), read: input.read || null} : {error: say('place-nowhere', o)};
  }
  const s = toAscii(String(input ?? '').trim());
  if (!s) return o.required ? {error: say('required', o)} : {value: []};
  // a pair of numbers, however its script writes a decimal point and a comma (U+066B, U+060C), is a bare coordinate
  const pair = s.replace(/\u066B/g, '.').replace(/\u060C/g, ',');
  if (BARE.test(pair)) return {error: say('place-bare', o, {example: WGS84 + ';' + pair.replace(/\s*,\s*/, ',')})};
  if (TAGGED.test(s) || o.free) return {value: s.split(/\s*\|\s*/).filter(Boolean), read: null};
  return {error: say('place-pick', o)};
}

// The field: what is typed (its own direction), the suggestions as a list a keyboard moves through, the reader's
// position asked for only by its button, and the value that lands, kept in the form. options: sealed; required; label
// (what the field shows now); placeholder
export function edit(name, value, o = {}) {
  const list = (Array.isArray(value) ? value : value ? [value] : []);
  const id = 'w-place-' + String(name).replace(/[^A-Za-z0-9_-]/g, '-');
  return h`<span class="w-place${o.sealed ? ' w-place-sealed' : ''}" data-place="${name}">
<input class="w-input w-place-input" name="${name}.typed" dir="auto" autocomplete="off" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="${id}" value="${o.label || list.join(' | ')}"${o.placeholder ? h` placeholder="${o.placeholder}"` : ''}>
<button type="button" class="w-place-near" data-place-near="" aria-pressed="false">${say('place-near', o)}</button>
<input type="hidden" name="${name}" value="${JSON.stringify({at: list, read: null})}">
<ul class="w-place-list" role="listbox" id="${id}" hidden></ul>
${o.sealed ? h`<span class="w-place-note">${say('place-sealed', o)}</span>` : ''}
</span>`;
}

// the list of suggestions, each its main line and its secondary one, and whom the places are from
function options(id, found, active, credits, o) {
  const src = {own: say('place-own', o), here: say('place-here', o), far: say('place-far', o)};
  return h`${found.map((s, i) => h`<li role="option" id="${id}-${i}" class="w-place-option" data-i="${i}" aria-selected="${i === active ? 'true' : 'false'}"><bdi dir="auto" class="w-place-main">${s.label}</bdi><span class="w-place-sub">${s.detail ? h`<bdi dir="auto">${s.detail}</bdi> \u00B7 ` : ''}<span class="w-place-from">${src[s.source]}</span></span></li>`)}${found.length ? '' : h`<li class="w-place-empty" role="presentation">${say('place-none', o)}</li>`}${credits.length ? h`<li class="w-place-credit" role="presentation">${credits.map((c, i) => h`${i ? ' \u00B7 ' : ''}<bdi dir="auto">${c}</bdi>`)}</li>` : ''}`;
}

// THE LOOKUP, wired to a field `edit` drew. sources: own (the garden's own places the page carries: [{id, title,
// kind, point?, osm?}]), here(q, {near}) and far(q, {near}) — each a Promise of {places, sources}, given by the host,
// absent offline. Returns {ask, pick, value} for a page and a test to drive as a person does.
export function wire(root, sources = {}, o = {}) {
  const box = root.matches && root.matches('[data-place]') ? root : root.querySelector('[data-place]');
  const input = box.querySelector('.w-place-input'), list = box.querySelector('.w-place-list');
  const kept = box.querySelector('input[type="hidden"]'), near = box.querySelector('[data-place-near]');
  const id = list.id;
  let found = [], active = -1, at = null, asked = 0, credits = [], timer = null;
  const draw = () => {
    mount(list, options(id, found, active, credits, o));
    list.hidden = !input.value.trim();
    input.setAttribute('aria-expanded', list.hidden ? 'false' : 'true');
    if (active >= 0) input.setAttribute('aria-activedescendant', id + '-' + active); else input.removeAttribute('aria-activedescendant');
  };
  const credit = r => { for (const c of (r && r.sources) || []) { const t = c.attribution || c.name; if (t && !credits.includes(t)) credits.push(t); } };
  async function ask(q) {
    const n = ++asked, opt = at ? {near: at} : {};
    const answers = {own: own(q, sources.own, o.limit || 8)};
    found = merge(answers); active = found.length ? 0 : -1; credits = []; draw();
    const settle = async (key, fn) => {
      if (typeof fn !== 'function') return;
      let r;
      try { r = await fn(q, opt); } catch { return; }        // a source that does not answer is offline: the rest stand
      if (n !== asked || !r) return;                          // a later keystroke asked again
      if (key === 'here' && Array.isArray(r.own)) answers.own = answers.own.concat(r.own);   // the host's read of the garden
      answers[key] = r.places || []; answers[key + 'Sources'] = r.sources || [];
      credit(r);
      found = merge(answers); active = found.length ? 0 : -1; draw();
    };
    await settle('here', sources.here);
    if (!o.sealed) await settle('far', sources.far);          // where a person will be is never asked beyond the machine
    return found;
  }
  function pick(i) {
    const s = found[i];
    if (!s) return null;
    kept.value = JSON.stringify({at: s.at, read: s.read});
    input.value = s.label;
    list.hidden = true; input.setAttribute('aria-expanded', 'false');
    return s;
  }
  input.addEventListener('input', () => {
    kept.value = JSON.stringify({at: [], read: null, typed: true});
    clearTimeout(timer);
    timer = setTimeout(() => ask(input.value), 150);
  });
  input.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {          // a list runs down the page in every script
      if (!found.length) return;
      e.preventDefault();
      active = (active + (e.key === 'ArrowDown' ? 1 : found.length - 1)) % found.length; draw();
    } else if (e.key === 'Enter' && !list.hidden && active >= 0) { e.preventDefault(); pick(active); }
    else if (e.key === 'Escape') { list.hidden = true; input.setAttribute('aria-expanded', 'false'); }
  });
  list.addEventListener('click', e => { const li = e.target.closest && e.target.closest('[data-i]'); if (li) pick(Number(li.getAttribute('data-i'))); });
  if (near) near.addEventListener('click', () => {               // the reader's own position: only now, only if they let it
    if (at) { at = null; near.setAttribute('aria-pressed', 'false'); return; }
    const g = typeof navigator !== 'undefined' && navigator.geolocation;
    if (!g) return;
    g.getCurrentPosition(p => { at = p.coords.latitude.toFixed(5) + ',' + p.coords.longitude.toFixed(5); near.setAttribute('aria-pressed', 'true'); if (input.value.trim()) ask(input.value); },
      () => {}, {maximumAge: 600000, timeout: 10000});
  });
  return {ask, pick, value: () => JSON.parse(kept.value), near: v => { at = v || null; }, found: () => found};
}

// what the field holds, for a form's Save: the picked place, or what was typed
export function collect(root) {
  const box = root.matches && root.matches('[data-place]') ? root : root.querySelector('[data-place]');
  const kept = JSON.parse(box.querySelector('input[type="hidden"]').value || '{}');
  const typed = box.querySelector('.w-place-input').value;
  return kept.typed || !Array.isArray(kept.at) || (!kept.at.length && typed.trim()) ? typed : kept;
}
