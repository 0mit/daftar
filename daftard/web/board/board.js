/* board.js — the board: one being or several, the cursor, kept still while the aspect around it turns (the view
 * profile's archetype `cursor`; its aspects, core/law/profiles.yaml `aspects`). daftard's page `/board?g=<garden>`.
 *
 * The CURSOR is one being or several, side by side; it stays at the centre. An ASPECT is a row of the law, read by the
 * garden's own release (assets/view/lib/view_board.py, through the worker's board_* methods): the relation it follows,
 * and the law's orientation it is laid out by (direction.js turns that row into an axis and a sense, so 'after' is below
 * for a walk and toward the line's end for a flow, mirrored for a right-to-left page), and the turn of its plane about
 * the cursor. Switching aspect turns the board: the old plane turns away and fades, the new one turns in, and a being in
 * both glides from its old place to its new one. Stepping to a neighbour pans it to the centre and keeps the aspect.
 * Every step is kept in the course, which is the browser's history: Back walks it. The page reads; it writes nothing.
 *
 * The planes, their grids and the lines are WebGL (three.js 0.186.1, vendored in /vendor/); the beings are an HTML
 * layer projected by the same camera, so their text stays crisp and their colours come from the page's tokens.
 */
import * as THREE from '/vendor/three-0.186.1/three.module.js';

const D = window.daftarDirection;
const $ = (s) => document.querySelector(s);
const ROWH = 23, COLW = 300, ROWS = 24, GAP = 48, FOV = 30;
const NEAR = { walk: 58, flow: 70 }, AFTER_FLOW = 330;   // how far a frame starts from the cursor
const SPREAD = { x: 600, y: 300 };                        // between the beings of a several-being cursor
const T_TURN = 800, T_STEP = 650;
const READABLE = 0.78;                                    // the camera never draws back by itself past this scale

const S = {
  lenses: [], lensBy: {}, by: null, starts: [], view: null, trail: [], at: -1, focus: null, token: 0,
  els: new Map(), anim: null, lineCap: 0, cam: { x: 0, y: 0, d: 1000 }, camTween: null, found: null,
};

// ---- talking to the API ----------------------------------------------------------------------------------------------
const GARDEN = new URLSearchParams(location.search).get('g') || '';
async function api(name, params = {}) {
  const q = new URLSearchParams({ g: GARDEN, ...params });
  const r = await fetch(`/api/board/${name}?${q}`, { credentials: 'same-origin' });
  const j = await r.json().catch(() => ({ error: `${r.status} ${r.statusText}` }));
  if (!r.ok || j.error) throw new Error(j.error || r.statusText);
  return j;
}
const enc = (ids) => ids.map(encodeURIComponent).join(',');
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const kindOf = (id) => id.split(':', 1)[0];

// ---- the scene -------------------------------------------------------------------------------------------------------
const board = $('#board'), layer = $('#labels');
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
board.prepend(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(FOV, 1, 1, 200000);
const TAN = Math.tan((FOV / 2) * Math.PI / 180);

function token(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || '#888'; }
function makeGrid() {
  const g = new THREE.GridHelper(12000, 120, token('--grid'), token('--grid'));
  g.rotation.x = Math.PI / 2;
  g.material.transparent = true;
  g.material.depthWrite = false;
  const pivot = new THREE.Group();
  pivot.add(g);
  scene.add(pivot);
  return pivot;
}
const grids = [makeGrid(), makeGrid()];   // the old plane and the new one, during a turn
const lineGeo = new THREE.BufferGeometry();
const lines = new THREE.LineSegments(lineGeo, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, depthWrite: false }));
scene.add(lines);
let edgeColor = new THREE.Color(token('--edge')), accentColor = new THREE.Color(token('--accent'));

function retheme() {
  for (const p of grids) {
    const g = p.children[0];
    g.material.dispose();
    p.remove(g);
    const n = new THREE.GridHelper(12000, 120, token('--grid'), token('--grid'));
    n.rotation.x = Math.PI / 2;
    n.material.transparent = true;
    n.material.depthWrite = false;
    p.add(n);
  }
  edgeColor = new THREE.Color(token('--edge'));
  accentColor = new THREE.Color(token('--accent'));
  draw();
}
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', retheme);

function size() {
  const w = board.clientWidth, h = board.clientHeight;
  renderer.setSize(w, h, false);
  renderer.domElement.style.width = w + 'px';
  renderer.domElement.style.height = h + 'px';
  camera.aspect = w / Math.max(1, h);
  camera.updateProjectionMatrix();
  draw();
}
new ResizeObserver(size).observe(board);
const unitD = () => board.clientHeight / (2 * TAN);      // the distance at which one unit is one pixel

// ---- layout: a lens's groups placed by the law's orientation ----------------------------------------------------------
function orientation(order) {
  const o = (D && D.axis(order)) || { axis: 'y', sign: 1 };
  const inline = (D && D.axis('taxis')) || { axis: 'x', sign: 1 };
  // world y points up, the page's block axis down: 'after' along a walk is world -y
  if (o.axis === 'x') return { along: 'x', sign: o.sign, cross: 'y', crossSign: -1 };
  return { along: 'y', sign: -o.sign, cross: 'x', crossSign: inline.sign };
}

// a group's column is as wide as its own names and notes need: 245 file names take narrow columns, a disk with the
// path it holds a file at takes a wide one
function widths(g) {
  const ms = g.members.length ? g.members : g.head ? [g.head] : [];
  const lab = Math.max(0, ...ms.map((m) => (m.label || '').length)), sub = Math.max(0, ...ms.map((m) => (m.sub || '').length));
  const lw = Math.min(230, Math.max(70, lab * 7.6)), sw = Math.min(330, sub * 6.9);
  return { lw, sw, colw: Math.max(200, lw + sw + 44) };
}
function rowsFor(n, colw) { return Math.max(ROWS, Math.min(48, Math.ceil(Math.sqrt((n * colw) / ROWH / 1.6)))); }
function blockOf(g) {
  const { lw, sw, colw } = widths(g);
  const per = rowsFor(g.members.length, colw);
  const n = g.members.length, rows = Math.min(n, per), cols = Math.max(1, Math.ceil(n / per));
  const head = g.head ? 1 : 0;
  return { g, rows, per, cols, head, lw, sw, colw, w: Math.max(cols * colw, 240), h: (1 + head + 0.25 + rows) * ROWH };
}

function layout(data) {
  const L = S.lensBy[data.lens];
  const o = orientation(L.order);
  const v = { lens: data.lens, ids: data.cursor.map((c) => c.id), cursor: data.cursor, groups: data.groups,
              theta: (L.turn || 0) * Math.PI / 180, items: new Map(), edges: [], bounds: [], focus: [] };
  const n = Math.max(1, data.cursor.length);
  const cpos = (k) => (k - (n - 1) / 2) * SPREAD[o.cross] * o.crossSign;
  const P = (cross, along) => (o.cross === 'x' ? { x: cross, y: along } : { x: along, y: cross });
  const cursorIds = data.cursor.length ? v.ids : ['∅'];
  if (data.cursor.length) {
    data.cursor.forEach((c, k) => v.items.set(c.id, { ...P(cpos(k), 0), role: 'cursor', node: c, along: o.along }));
  } else {
    v.items.set('∅', { x: 0, y: 0, role: 'cursor', node: { id: '∅', kind: 'board', label: 'a blank board', sub: 'choose a being to begin', inert: true } });
  }
  // slots: (side, at) → blocks; a shared slot sits between the beings of the cursor, a side's slot on its outer side
  const slots = new Map();
  for (const g of data.groups) {
    const key = `${g.side}|${g.at}`;
    if (!slots.has(key)) slots.set(key, []);
    slots.get(key).push(blockOf(g));
  }
  const crossExt = (b) => (o.cross === 'x' ? b.w : b.h), alongExt = (b) => (o.along === 'x' ? b.w : b.h);
  const half = {};
  for (const [key, bs] of slots) {
    const [side, at] = key.split('|');
    if (side === 'shared') half[at] = (bs.reduce((s, b) => s + crossExt(b), 0) + GAP * (bs.length - 1)) / 2;
  }
  for (const [key, bs] of slots) {
    const [sideS, at] = key.split('|');
    const side = sideS === 'shared' ? 'shared' : +sideS;
    const dir = at === 'after' ? o.sign : -o.sign;
    const near = o.along === 'x' ? (dir > 0 ? AFTER_FLOW : NEAR.flow) : NEAR.walk;
    const c = side === 'shared' ? 0 : cpos(side);
    const out = side === 'shared' || n === 1 ? 0 : Math.sign(c);
    const total = bs.reduce((s, b) => s + crossExt(b), 0) + GAP * (bs.length - 1);
    // one cursor: its frames begin beside it and run on in the reader's order; several: what they share is centred
    // between them, and each one's own frames run outward from there
    const run = out === 0 ? o.crossSign : out;
    let start = side === 'shared' ? c - run * total / 2 : out === 0 ? c - run * 40 : out * Math.max(Math.abs(c) - 40, (half[at] || 0) + GAP);
    for (const b of bs) {
      let c0;
      if (run > 0) { c0 = start; start += crossExt(b) + GAP; } else { c0 = start - crossExt(b); start = c0 - GAP; }
      const a0 = dir > 0 ? near : -near - alongExt(b);
      // the block's rectangle in world units; its header at the top-left
      const x0 = o.cross === 'x' ? c0 : (o.along === 'x' ? a0 : 0);
      const top = o.cross === 'x' ? a0 + alongExt(b) : c0 + crossExt(b);
      // where a line from the cursor meets the block: on its side that faces the cursor
      const meet = o.along === 'y' ? (dir > 0 ? 'bottom' : 'corner') : (dir > 0 ? 'top' : 'end');
      place(v, b, x0, top, side, cursorIds, meet);
      if (b.g.key === 'found') v.focus.push([x0, top - b.h, x0 + b.w, top]);
      v.bounds.push([x0, top - b.h, x0 + b.w, top]);
    }
  }
  return v;
}

function place(v, b, x0, top, side, cursorIds, meet) {
  const g = b.g, gid = `g:${side}:${g.key}`;
  const more = g.total > g.members.length ? ` of ${g.total.toLocaleString()}` : '';
  v.items.set(gid, { x: x0, y: top, role: 'glabel', node: { label: g.label, sub: `${g.members.length.toLocaleString()}${more}${g.note ? ' · ' + g.note : ''}` } });
  let y = top - ROWH;
  let anchor = gid;
  if (g.head) {
    v.items.set(g.head.id, { x: x0, y, role: 'head', node: g.head, rel: g.relation, lw: b.lw, sw: b.sw });
    anchor = g.head.id;
    y -= ROWH;
  }
  y -= ROWH * 0.25;
  const from = side === 'shared' ? cursorIds : [cursorIds[side] ?? cursorIds[0]];
  let port = anchor;
  if (meet !== 'top') {
    port = `p:${side}:${g.key}`;
    const a = v.items.get(anchor);
    v.items.set(port, meet === 'end' ? { x: x0 + b.w - 14, y: a.y, role: 'port', node: {} }
                    : meet === 'corner' ? { x: x0 - 8, y: top + 10, role: 'port', node: {} }
                    : { x: x0 - 6, y: top - b.h + 6, role: 'port', node: {} });
  }
  for (const c of from) v.edges.push([c, port, 1]);
  let first = null, last = null;
  g.members.forEach((m, i) => {
    const col = Math.floor(i / b.per), row = i % b.per;
    v.items.set(m.id, { x: x0 + col * b.colw, y: y - row * ROWH, role: 'member', node: m, rel: g.relation, lw: b.lw, sw: b.sw });
    if (row === 0) { if (first && last) v.edges.push([first, last, 0]); first = m.id; }
    last = m.id;
  });
  if (first && last && first !== last) v.edges.push([first, last, 0]);
  if (g.members.length) v.edges.push([anchor, g.members[0].id, 0]);
}

// ---- drawing: the beings as HTML over the planes ---------------------------------------------------------------------
function elFor(id, item) {
  let e = S.els.get(id);
  if (!e) {
    e = document.createElement('div');
    e.dataset.id = id;
    layer.appendChild(e);
    S.els.set(id, e);
  }
  if (e._it === item) return e;     // rebuilt only when the view changes, never per frame: a click must find its target
  e._it = item;
  const n = item.node;
  if (item.role === 'glabel') {
    e.className = 'gl';
    e.innerHTML = `<div class="in"><span class="eb">${esc(n.label)}</span><small>${esc(n.sub)}</small></div>`;
  } else {
    const k = n.kind || kindOf(id);
    if (item.lw) { e.style.setProperty('--lw', item.lw + 'px'); e.style.setProperty('--sw', item.sw + 'px'); }
    e.className = `n k-${k} ${item.role === 'cursor' ? 'cur' : item.role === 'head' ? 'head' : ''} ${n.inert ? 'inert' : ''} ${k === 'pair' ? 'pair' : ''}`;
    const tip = [n.label, n.sub, n.title, item.rel ? `— ${item.rel}` : ''].filter(Boolean).join('\n');
    if (item.role === 'cursor' && item.along === 'x') {     // a flow runs through the cursor sideways: its label above
      e.classList.add('across');
      e.innerHTML = `<i class="at" title="${esc(tip)}"></i><div class="in" title="${esc(tip)}"><span>${esc(n.label)}</span>${n.sub ? `<small>${esc(n.sub)}</small>` : ''}</div>`;
    } else {
      e.innerHTML = `<div class="in" title="${esc(tip)}"><i></i><span>${esc(n.label)}</span>${n.sub ? `<small>${esc(n.sub)}</small>` : ''}</div>`;
    }
  }
  return e;
}

const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const wrap = (a) => { while (a > Math.PI) a -= 2 * Math.PI; while (a <= -Math.PI) a += 2 * Math.PI; return a; };
const turn = (p, a) => ({ x: p.x * Math.cos(a), y: p.y, z: p.x * Math.sin(a) });

// where each item is now: during a transition, between the old view and the new; else the view's own places
function frameState(now) {
  const A = S.anim, out = new Map();
  if (!A) {
    for (const [id, it] of S.view.items) out.set(id, { x: it.x, y: it.y, z: 0, o: 1, it });
    return { out, a: [0, null] };
  }
  const t = Math.min(1, (now - A.t0) / A.T), e = ease(t);
  const aOld = -A.dTheta * e, aNew = A.dTheta * (1 - e);
  const prev = A.prev ? A.prev.items : new Map(), next = A.next.items, sh = A.shift;
  for (const [id, it] of next) {
    const was = prev.get(id);
    if (was) {
      const p0 = { x: was.x - sh.x, y: was.y - sh.y };
      out.set(id, { x: p0.x + (it.x - p0.x) * e, y: p0.y + (it.y - p0.y) * e, z: Math.sin(Math.PI * e) * 40, o: 1, it });
    } else {
      const p = turn(it, aNew);
      out.set(id, { ...p, o: e * Math.max(0, Math.cos(aNew)), it });
    }
  }
  for (const [id, it] of prev) {
    if (next.has(id)) continue;
    const p = turn({ x: it.x - sh.x, y: it.y - sh.y }, aOld);
    out.set(id, { ...p, o: (1 - e) * Math.max(0, Math.cos(aOld)), it, leaving: true });
  }
  return { out, t, a: [aOld, aNew], e };
}

function draw(now = performance.now()) {
  if (!S.view) { renderer.render(scene, camera); return; }
  const A = S.anim;
  const st = frameState(now);
  // the camera: a pan toward the new cursor after a step, a tween after `fit`
  if (A && A.cam0) {
    const e = st.e;
    for (const k of ['x', 'y', 'd']) S.cam[k] = A.cam0[k] + (A.cam1[k] - A.cam0[k]) * e;
  }
  if (S.camTween) {
    const T = S.camTween, e = ease(Math.min(1, (now - T.t0) / 450));
    for (const k of ['x', 'y', 'd']) S.cam[k] = T.from[k] + (T.to[k] - T.from[k]) * e;
    if (e >= 1) S.camTween = null;
  }
  camera.position.set(S.cam.x, S.cam.y, S.cam.d);
  camera.lookAt(S.cam.x, S.cam.y, 0);
  camera.updateMatrixWorld();
  // the planes: the active one faces the reader; during a turn the old turns away and the new turns in
  const [aOld, aNew] = st.a;
  grids[0].rotation.y = aOld;
  grids[0].children[0].material.opacity = A ? 0.9 * (1 - st.e) * Math.abs(Math.cos(aOld)) : 0.9;
  grids[1].visible = !!A && A.dTheta !== 0;
  if (A) {
    grids[1].rotation.y = aNew ?? 0;
    grids[1].children[0].material.opacity = 0.9 * st.e * Math.abs(Math.cos(aNew ?? 0));
  }
  const W = board.clientWidth, H = board.clientHeight, v = new THREE.Vector3();
  const finding = S.findText;
  for (const [id, s] of st.out) {
    if (s.it.role === 'port') continue;
    const e = elFor(id, s.it);
    if (s.o < 0.02) { e.style.visibility = 'hidden'; continue; }
    v.set(s.x, s.y, s.z).project(camera);
    const depth = S.cam.d - s.z;
    const k = H / (2 * Math.max(1, depth) * TAN);
    const sc = Math.max(0.22, Math.min(1.35, k));
    e.style.visibility = 'visible';
    e.style.opacity = s.o.toFixed(3);
    e.style.transform = `translate(${((v.x + 1) / 2 * W).toFixed(1)}px, ${((1 - v.y) / 2 * H).toFixed(1)}px) scale(${sc.toFixed(3)})`;
    e.classList.toggle('lod1', k < 0.62);
    e.classList.toggle('lod2', k < 0.36);
    e.style.pointerEvents = s.leaving ? 'none' : '';
    if (finding !== undefined) e.classList.toggle('hit', !!finding && matches(s.it, finding));
  }
  // the lines: cursor to each frame, and each frame's spine; their alpha follows their ends
  const segs = [];
  const add = (edges, weight) => {
    for (const [a, b, strong] of edges) {
      const p = st.out.get(a), q = st.out.get(b);
      if (!p || !q) continue;
      const al = Math.min(p.o, q.o) * weight * (strong ? 0.75 : 0.35);
      if (al > 0.01) segs.push([p, q, al, strong]);
    }
  };
  add(S.view.edges, 1);
  if (A && A.prev) add(A.prev.edges.filter(([a, b]) => st.out.get(a)?.leaving || st.out.get(b)?.leaving), 1);
  if (!S.lineCap || segs.length > S.lineCap) {   // made once, grown rarely; otherwise written in place
    S.lineCap = Math.max(1024, segs.length * 2);
    lineGeo.dispose();
    lineGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(S.lineCap * 6), 3).setUsage(THREE.DynamicDrawUsage));
    lineGeo.setAttribute('color', new THREE.BufferAttribute(new Float32Array(S.lineCap * 8), 4).setUsage(THREE.DynamicDrawUsage));
  }
  const pa = lineGeo.getAttribute('position'), ca = lineGeo.getAttribute('color');
  segs.forEach(([p, q, al, strong], i) => {
    pa.array.set([p.x, p.y, p.z, q.x, q.y, q.z], i * 6);
    const c = strong ? accentColor : edgeColor;
    ca.array.set([c.r, c.g, c.b, al, c.r, c.g, c.b, al], i * 8);
  });
  pa.needsUpdate = ca.needsUpdate = true;
  lineGeo.setDrawRange(0, segs.length * 2);
  lines.frustumCulled = false;
  renderer.render(scene, camera);
  if (A && st.t >= 1) finish();
}

let raf = 0;
function loop(now) {
  raf = 0;
  draw(now);
  if (S.anim || S.camTween) raf = requestAnimationFrame(loop);
}
function kick() { if (!raf) raf = requestAnimationFrame(loop); }

function finish() {
  const A = S.anim;
  S.anim = null;
  for (const [id, e] of S.els) if (!A.next.items.has(id)) { e.remove(); S.els.delete(id); }
  draw();
}

function transition(prev, next, shift, turnIt, keep) {
  const dTheta = prev && turnIt ? wrap(next.theta - prev.theta) : 0;
  // the world moves by -shift at once and the camera with it, so nothing jumps; then the camera goes where the new
  // frame wants it: a step centres the new cursor and fits the frame; a lens switch keeps the cursor where it is on
  // screen and only draws back, about the cursor, as far as the new frame needs
  const cam0 = { x: S.cam.x - shift.x, y: S.cam.y - shift.y, d: S.cam.d };
  const cam1 = reveal(keep ? drawBack(next, cam0) : centred(next), next.focus);
  S.anim = { prev, next, shift, dTheta, cam0, cam1, t0: performance.now(), T: dTheta ? T_TURN : T_STEP };
  S.view = next;
  kick();
}

// ---- moving: lens, step, course --------------------------------------------------------------------------------------
async function go(lens, ids, how = {}) {
  const my = ++S.token;
  $('#busy').hidden = false;
  let data;
  try {
    data = await api('lens', { aspect: lens, cursor: ids.join(',') });
  } catch (err) {
    if (my === S.token) { $('#busy').hidden = true; note(`<b>could not read this frame:</b> ${esc(err.message)}`); }
    return false;
  }
  if (my !== S.token) return false;
  $('#busy').hidden = true;
  if (how.found) {                   // what was found inside the cursor sits nearest it; what the board has is not drawn twice
    const has = new Set(data.groups.flatMap((g) => [...g.members.map((m) => m.id), ...(g.head ? [g.head.id] : [])]));
    data.groups.unshift(...how.found.map((f) => ({ ...f, members: f.members.filter((m) => !has.has(m.id)) })));
  }
  const prev = S.view, next = layout(data);
  let shift = { x: 0, y: 0 };
  if (prev && how.from && prev.items.has(how.from)) {
    const p = prev.items.get(how.from);
    shift = { x: p.x, y: p.y };
  } else if (prev && !how.keepPlace) {
    const had = next.ids.filter((i) => prev.items.has(i) && prev.items.get(i).role !== 'cursor');
    if (had.length) shift = had.map((i) => prev.items.get(i)).reduce((s, p) => ({ x: s.x + p.x / had.length, y: s.y + p.y / had.length }), { x: 0, y: 0 });
  }
  const sameCursor = prev && prev.ids.join(',') === next.ids.join(',');
  if (!prev) Object.assign(S.cam, centred(next));
  transition(prev, next, shift, !!prev && prev.lens !== next.lens, !!prev && !!how.keepPlace);
  S.found = how.found || null;
  if (how.record !== false) record(lens, data.cursor, how.via);
  if (!sameCursor) sheet(next.ids[0] || null);
  chrome(data);
  return true;
}

function record(lens, cursor, via) {
  const entry = { lens, ids: cursor.map((c) => c.id), labels: cursor.map((c) => c.label), at: new Date(), via };
  const cur = S.trail[S.at];
  if (cur && cur.lens === entry.lens && cur.ids.join(',') === entry.ids.join(',')) return;
  S.trail = S.trail.slice(0, S.at + 1);
  S.trail.push(entry);
  S.at = S.trail.length - 1;
  const url = '#' + hashOf(entry);
  if (S.at === 0) history.replaceState({ i: 0 }, '', url); else history.pushState({ i: S.at }, '', url);
  drawTrail();
}

function hashOf(e) { return `l=${encodeURIComponent(e.lens)}${e.ids.length ? '&c=' + enc(e.ids) : ''}`; }
function parseHash() {
  const out = { lens: '', ids: [] };
  for (const part of location.hash.replace(/^#/, '').split('&')) {
    const [k, v] = part.split('=');
    if (k === 'l' && v) out.lens = decodeURIComponent(v);
    if (k === 'c' && v) out.ids = v.split(',').filter(Boolean).map(decodeURIComponent);
  }
  return out;
}

async function walk(i) {
  const e = S.trail[i];
  if (!e) return;
  S.at = i;
  drawTrail();
  await go(e.lens, e.ids, { record: false, via: 'course' });
}
window.addEventListener('popstate', (ev) => {
  const i = ev.state && Number.isInteger(ev.state.i) ? ev.state.i : null;
  if (i !== null && S.trail[i]) { walk(i); return; }
  const h = parseHash();
  go(h.lens, h.ids, { via: 'link' });
});

function step(ids, from) { return go(S.view.lens, ids, { from, via: S.view.lens }); }
function setLens(lens) { if (S.view && lens !== S.view.lens) go(lens, S.view.ids, { keepPlace: true, via: 'lens' }); }

// ---- the chrome: chips, lenses, note, course -------------------------------------------------------------------------
function chrome(data) {
  const chips = $('#chips');
  chips.innerHTML = data.cursor.length ? data.cursor.map((c) => `<span class="chip k-${esc(c.kind)}" data-id="${esc(c.id)}" title="${esc(c.label + (c.sub ? '\n' + c.sub : ''))}">
      <i></i><span>${esc(c.label)}</span>${data.cursor.length > 1 ? `<button type="button" data-drop="${esc(c.id)}" title="take it out of the cursor">×</button>` : ''}</span>`).join('')
    : '<span class="who">nothing yet</span>';
  const e = S.trail[S.at];
  $('#who').textContent = S.by && e ? `opened by ${S.by} · ${e.at.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : '';
  const kinds = new Set(data.cursor.map((c) => c.kind));
  $('#lenses').innerHTML = S.lenses.map((L, i) => `<button type="button" data-lens="${esc(L.lens)}" aria-pressed="${L.lens === data.lens}"
      class="${data.cursor.length && !L.of.some((k) => kinds.has(k)) ? 'idle' : ''}" title="${esc(L.says)}">${esc(L.label)}<kbd>${i + 1}</kbd></button>`).join('');
  const L = S.lensBy[data.lens];
  const drawn = data.groups.reduce((s, g) => s + g.members.length + (g.head ? 1 : 0), 0);
  if (!data.cursor.length) {
    note('<b>A blank board.</b> Choose a being to begin' + (S.starts.length ? ': ' + S.starts.map((s) =>
      `<a data-start="${esc(s.id)}" title="${esc(s.sub || '')}">${esc(s.label)}</a>`).join(' · ') : ': this host keeps no store, so name one in the link (#c=<id>)') + '.');
  } else if (data.note) {
    note(`<b>${esc(L.label)}</b>: ${esc(data.note)}`);
  } else if (!drawn) {
    const fits = L.of.some((k) => kinds.has(k));
    note(`<b>${esc(L.label)}</b>: ${fits ? 'nothing in this frame for this cursor.' : `this aspect reads ${esc(L.of.join(', '))}; the cursor is ${esc([...kinds].join(', '))}.`} The cursor stays; turn to another aspect or step back.`);
  } else {
    note(`<b>${esc(L.label)}</b> · ${esc(L.says)}`);
  }
}

function note(html) { $('#note').innerHTML = html; }

function drawTrail() {
  $('#trail').innerHTML = S.trail.map((e, i) => `<li class="${i > S.at ? 'ahead' : ''}"><button type="button" data-i="${i}" ${i === S.at ? 'aria-current="step"' : ''}
      title="${esc(e.labels.join(' + ') || 'a blank board')}\n${esc(e.lens)} · ${e.at.toLocaleTimeString()}">${esc(e.labels.join(' + ') || 'blank board')}<small>${esc(S.lensBy[e.lens]?.label || e.lens)}</small></button></li>`).join('');
  $('#trail').querySelector('[aria-current]')?.scrollIntoView({ block: 'nearest', inline: 'nearest' });
}

// ---- the sheet: one per being, the same in every lens ----------------------------------------------------------------
async function sheet(id) {
  S.focus = id;
  const box = $('#sheet');
  if (!id) {
    box.innerHTML = '<p class="eyebrow">the sheet</p><p class="muted">Each being has one sheet, the same in every lens. Choose a being on the board.</p>';
    return;
  }
  box.innerHTML = '<p class="muted">reading…</p>';
  let s;
  try { s = await api('being', { id }); } catch (err) {
    if (S.focus === id) box.innerHTML = `<p class="muted">could not read this being: ${esc(err.message)}</p>`;
    return;
  }
  if (S.focus !== id) return;
  const inCursor = S.view && S.view.ids.includes(id);
  const acts = inCursor ? '' : `<div class="acts"><button type="button" data-goto="${esc(id)}">make it the cursor</button>
      <button type="button" data-beside="${esc(id)}">beside the cursor</button></div>`;
  const facts = s.facts.length ? `<dl>${s.facts.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>` : '';
  const lists = s.lists.map((l) => `<h3>${esc(l.title)}</h3>${l.rows.length ? `<table><tr>${l.cols.map((c) => `<th>${esc(c)}</th>`).join('')}</tr>
      ${l.rows.map((r) => `<tr>${r.map((c) => `<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</table>` : '<p class="muted">none</p>'}`).join('');
  const g = s.garden ? `<h3>in the garden · beans/${esc(s.garden.bean)}.md</h3><p>${esc(s.garden.title || '')}</p>
      <p class="muted">${esc(s.garden.summary || '')}</p><ul class="st">${s.garden.statements.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>` : '';
  const from = s.from.length ? `<h3>read from</h3><ul class="from">${s.from.map((f) => `<li>${esc(f)}</li>`).join('')}</ul>` : '';
  box.innerHTML = `<p class="eyebrow kind k-${esc(s.kind)}"><i></i>${esc(s.kind)}${inCursor ? ' · in the cursor' : ''}</p>
    <h2>${esc(s.title)}</h2><p class="sub">${esc(s.sub || '')}</p>${acts}${facts}${lists}${g}${from}`;
}

// ---- finding ---------------------------------------------------------------------------------------------------------
function matches(it, q) {
  const n = it.node || {};
  return `${n.label || ''} ${n.sub || ''}`.toLowerCase().includes(q);
}
$('#find').addEventListener('input', (e) => {
  const q = e.target.value.trim().toLowerCase();
  S.findText = q;
  layer.classList.toggle('finding', !!q);
  draw();
});
$('#find').addEventListener('keydown', async (e) => {
  if (e.key === 'Escape') { e.target.value = ''; e.target.dispatchEvent(new Event('input')); e.target.blur(); return; }
  if (e.key !== 'Enter' || !S.view) return;
  const q = e.target.value.trim();
  const ids = S.view.ids;
  if (S.view.cursor.some((c) => ['host', 'volume', 'folder'].includes(c.kind)) && q.length >= 3) {
    $('#busy').hidden = false;
    try {
      const found = await api('find', { cursor: ids.join(','), q });
      await go(S.view.lens, ids, { found: found.groups, keepPlace: true, record: false });
    } catch (err) { note(`<b>find:</b> ${esc(err.message)}`); }
    $('#busy').hidden = true;
    return;
  }
  const hit = [...S.view.items].find(([id, it]) => it.role !== 'cursor' && it.role !== 'glabel' && !it.node.inert && matches(it, q.toLowerCase()));
  if (hit) step(hit[1].node.step || [hit[0]], hit[0]);
});

// ---- the hands: clicks, keys, dragging, zoom -------------------------------------------------------------------------
layer.addEventListener('click', (e) => {
  const el = e.target.closest('.n');
  if (!el || S.moved) return;
  const it = S.view.items.get(el.dataset.id);
  if (!it || it.role === 'glabel') return;
  if (it.role === 'cursor') { sheet(it.node.id === '∅' ? null : it.node.id); return; }
  if (it.node.inert) { sheet(null); return; }
  if (e.shiftKey && !it.node.step) {
    go(S.view.lens, [...S.view.ids, it.node.id], { keepPlace: true, via: 'beside' });
    return;
  }
  step(it.node.step || [it.node.id], it.node.id);
});
layer.addEventListener('contextmenu', (e) => {
  const el = e.target.closest('.n');
  if (!el) return;
  const it = S.view.items.get(el.dataset.id);
  if (!it || it.node.inert || it.node.step || it.node.id === '∅') return;
  e.preventDefault();
  sheet(it.node.id);
  document.body.classList.add('sheet-open');
});
$('#note').addEventListener('click', (e) => {
  const st = e.target.closest('[data-start]');
  if (st) go(S.view ? S.view.lens : S.lenses[0].lens, [st.dataset.start], { via: 'start' });
});
$('#chips').addEventListener('click', (e) => {
  const drop = e.target.closest('[data-drop]');
  if (drop) { go(S.view.lens, S.view.ids.filter((i) => i !== drop.dataset.drop), { keepPlace: true, via: 'drop' }); return; }
  const chip = e.target.closest('.chip');
  if (chip) { sheet(chip.dataset.id); document.body.classList.add('sheet-open'); }
});
$('#lenses').addEventListener('click', (e) => { const b = e.target.closest('[data-lens]'); if (b) setLens(b.dataset.lens); });
$('#trail').addEventListener('click', (e) => {
  const b = e.target.closest('[data-i]');
  if (b) { const i = +b.dataset.i; if (i !== S.at) history.go(i - S.at); }
});
$('#sheet').addEventListener('click', (e) => {
  const g = e.target.closest('[data-goto]'), b = e.target.closest('[data-beside]');
  if (g) step([g.dataset.goto], g.dataset.goto);
  if (b) go(S.view.lens, [...S.view.ids, b.dataset.beside], { keepPlace: true, via: 'beside' });
});
$('#fit').addEventListener('click', () => S.view && fitTo(S.view));
$('#link').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(location.href); note('<b>link copied:</b> the cursor and the aspect travel in it.'); }
  catch { prompt('the link to this cursor and aspect', location.href); }
});
$('#sheetbtn').addEventListener('click', () => document.body.classList.toggle('sheet-open'));

document.addEventListener('keydown', (e) => {
  if (e.target.closest('input, textarea') || e.altKey || e.ctrlKey || e.metaKey) return;
  if (/^[1-9]$/.test(e.key) && S.lenses[+e.key - 1]) { setLens(S.lenses[+e.key - 1].lens); return; }
  if (e.key === 'f') { S.view && fitTo(S.view); return; }
  if (e.key === '/') { e.preventDefault(); $('#find').focus(); return; }
  if (e.key === 'Backspace') { e.preventDefault(); if (S.at > 0) history.back(); return; }
  const c = D && D.command(e, ['time']);
  if (c === 'earlier' && S.at > 0) { e.preventDefault(); history.back(); }
  if (c === 'later' && S.at < S.trail.length - 1) { e.preventDefault(); history.forward(); }
});

// dragging pans, the wheel and a pinch zoom about the pointer
const pointers = new Map();
let pinch = null;
function worldAt(px, py) {
  const k = (2 * S.cam.d * TAN) / board.clientHeight, r = board.getBoundingClientRect();
  return { x: S.cam.x + (px - r.left - r.width / 2) * k, y: S.cam.y - (py - r.top - r.height / 2) * k };
}
function zoomAt(px, py, f) {
  const before = worldAt(px, py);
  S.cam.d = Math.max(unitD() * 0.25, Math.min(unitD() * 12, S.cam.d * f));
  const after = worldAt(px, py);
  S.cam.x += before.x - after.x;
  S.cam.y += before.y - after.y;
  draw();
}
board.addEventListener('pointerdown', (e) => {
  if (e.target.closest('.n .in, .note a')) { S.moved = false; return; }
  pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
  board.setPointerCapture(e.pointerId);
  S.moved = false;
  if (pointers.size === 2) {
    const [a, b] = [...pointers.values()];
    pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), cd: S.cam.d };
  }
  board.classList.add('dragging');
});
board.addEventListener('pointermove', (e) => {
  const p = pointers.get(e.pointerId);
  if (!p) return;
  const dx = e.clientX - p.x, dy = e.clientY - p.y;
  if (Math.abs(dx) + Math.abs(dy) > 3) S.moved = true;
  p.x = e.clientX; p.y = e.clientY;
  if (pointers.size === 2 && pinch) {
    const [a, b] = [...pointers.values()];
    const d = Math.hypot(a.x - b.x, a.y - b.y);
    zoomAt((a.x + b.x) / 2, (a.y + b.y) / 2, (pinch.cd * pinch.d / Math.max(1, d)) / S.cam.d);
    return;
  }
  const k = (2 * S.cam.d * TAN) / board.clientHeight;
  S.cam.x -= dx * k;
  S.cam.y += dy * k;
  draw();
});
const up = (e) => {
  pointers.delete(e.pointerId);
  if (pointers.size < 2) pinch = null;
  if (!pointers.size) board.classList.remove('dragging');
  setTimeout(() => { S.moved = false; }, 0);
};
board.addEventListener('pointerup', up);
board.addEventListener('pointercancel', up);
board.addEventListener('wheel', (e) => { e.preventDefault(); zoomAt(e.clientX, e.clientY, Math.exp(e.deltaY * 0.0015)); }, { passive: false });

// the extent of a frame about its cursor (world 0, 0): [left, bottom, right, top]
function extent(v) {
  let x0 = -20, y0 = -20, x1 = 320, y1 = 20;
  for (const it of v.items.values()) if (it.role === 'cursor') { x0 = Math.min(x0, it.x - 20); x1 = Math.max(x1, it.x + 320); y1 = Math.max(y1, it.y + 60); }
  for (const [a, b, c, d] of v.bounds) { x0 = Math.min(x0, a); y0 = Math.min(y0, b); x1 = Math.max(x1, c); y1 = Math.max(y1, d); }
  return [x0, y0, x1, y1];
}
function centred(v) {
  const [x0, y0, x1, y1] = extent(v), W = board.clientWidth, H = board.clientHeight;
  const half = Math.max(Math.max(-x0, x1) / (W / H), Math.max(-y0, y1)) * 1.06;     // the cursor stays at the centre
  const d = Math.max(unitD() * 0.85, Math.min(unitD() / READABLE, half / TAN));
  if (W >= 700) return { x: 0, y: 0, d };
  // a phone: the centre would leave most of a frame off the screen, so the cursor moves toward a side, still in view
  const k = (2 * d * TAN) / H, hw = (W / 2) * k, hh = (H / 2) * k;
  const clamp = (v, m) => Math.max(-m, Math.min(m, v));
  return { x: clamp((x0 + x1) / 2, hw * 0.62), y: clamp((y0 + y1) / 2, hh * 0.5), d };
}
function drawBack(v, cam) {
  const [x0, y0, x1, y1] = extent(v), W = board.clientWidth, H = board.clientHeight;
  const k = (2 * cam.d * TAN) / H;                                   // world units per pixel now
  const sx = W / 2 - cam.x / k, sy = H / 2 + cam.y / k;               // where the cursor is on screen
  if (sx < W * 0.08 || sx > W * 0.92 || sy < H * 0.08 || sy > H * 0.92) return centred(v);
  const need = Math.max(-x0 / sx, x1 / (W - sx), y1 / sy, -y0 / (H - sy)) * 1.04;
  const k1 = Math.max(k, Math.min(need, 1 / READABLE));
  return { x: -(sx - W / 2) * k1, y: (sy - H / 2) * k1, d: (k1 * H) / (2 * TAN) };
}

// what was asked for comes into view: the camera pans (never zooms) just as far as the first such block needs
function reveal(cam, rects) {
  if (!rects.length) return cam;
  const [x0, y0, x1, y1] = rects[0], H = board.clientHeight, W = board.clientWidth;
  const k = (2 * cam.d * TAN) / H, hw = (W / 2) * k * 0.94, hh = (H / 2) * k * 0.9;
  const out = { ...cam };
  if (x1 - x0 > 2 * hw) out.x = x0 + hw; else if (x0 < cam.x - hw) out.x = x0 + hw; else if (x1 > cam.x + hw) out.x = x1 - hw;
  if (y1 - y0 > 2 * hh) out.y = y1 - hh; else if (y1 > cam.y + hh) out.y = y1 - hh; else if (y0 < cam.y - hh) out.y = y0 + hh;
  return out;
}

function fitTo(v, now) {
  let x0 = 0, x1 = 0, y0 = 0, y1 = 0;
  [x0, y0, x1, y1] = extent(v);
  const W = board.clientWidth, H = board.clientHeight;
  const need = Math.max((x1 - x0) / (W / H), y1 - y0) * 1.08;
  const to = { x: (x0 + x1) / 2, y: (y0 + y1) / 2, d: Math.max(unitD() * 0.6, Math.min(unitD() * 12, need / (2 * TAN))) };
  if (now) { Object.assign(S.cam, to); return; }
  S.camTween = { from: { ...S.cam }, to, t0: performance.now() };
  kick();
}

// ---- beginning -------------------------------------------------------------------------------------------------------
window.boardState = S;               // for a test driver (CDP) to read where the board is; nothing reads it back
(async function begin() {
  size();
  S.cam.d = unitD();
  try {
    const A = await api('aspects');
    const rows = document.createElement('script');      // the law's orientations, where direction.js reads them
    rows.type = 'application/json';
    rows.id = 'orientations';
    rows.textContent = JSON.stringify(A.orientations || []);
    document.head.appendChild(rows);
    S.lenses = A.aspects;
    S.lensBy = Object.fromEntries(A.aspects.map((l) => [l.lens, l]));
    S.by = A.gardener;
    S.starts = A.starts || [];
  } catch (err) {
    note(`<b>the board’s API does not answer:</b> ${esc(err.message)}`);
    return;
  }
  const h = parseHash();
  if (!S.lenses.length) { note('<b>this garden’s board has no aspect:</b> its law gives none of the profiles it takes'); return; }
  if (!S.lensBy[h.lens]) h.lens = S.lenses[0].lens;
  await go(h.lens, h.ids, { via: 'link' });
})();
