/* direction.js — the page's direction of movement, read from the law (DIRECTION.md; the view profile's `orientations`).
 *
 * A drawing keeps the frame of what it draws. A sayable — a page, a walk, a journal, a timeline — is laid out in the
 * taxis, which on a page is the reader's script: its inline axis runs from the start of the line to its end, mirrored
 * with the script. A body keeps its own frame: a ladder keeps its foundation below and gravitation's up up, a map keeps
 * north up, a magnitude grows upward — never mirrored, because the world does not turn around when its reader's
 * language does. Every key, glyph and gesture of a page is named by MEANING (next, later, up, in, north…) and bound
 * here, never by a physical side.
 *
 *   frame(doc)                 { dir: 'ltr'|'rtl' } — from <html dir>, never guessed
 *   axis(order, doc)           { axis: 'x'|'y'|'z'|'map', sign: 1|-1, mirrored } — where an order runs on this page
 *   command(event, orders)     the command a key means for these orders ('next', 'earlier', 'up', …), or null
 *   glyph(meaning, doc)        an arrow chosen by meaning and turned by the frame
 *   bind(el, orders, handlers) keys → handlers[command]; swipe(el, orders, handlers) the same for a swipe
 */
(function (root) {
  'use strict';
  // order: [screen axis, sense, follows the script]. inline + follows: the start of the line first.
  var ORIENTATIONS = {
    ordinal: ['inline', 1, true], taxis: ['inline', 1, true], routine: ['inline', 1, true], flow: ['inline', 1, true],
    time: ['inline', 1, true],
    walk: ['block', 1, true],                      // the whole at the block start; the indent on the reader's side
    ladder: ['vertical', -1, false],               // the foundation below: up is toward the top of the screen
    magnitude: ['vertical', -1, false],            // more is up
    place: ['map', 1, false],                      // north up, east right
    depth: ['z', 1, false]                         // in: its parts; out: its whole
  };
  var COMMANDS = {                                 // the commands an order answers to: [toward its end, toward its start]
    ordinal: ['next', 'previous'], taxis: ['next', 'previous'], routine: ['next', 'previous'], flow: ['next', 'previous'],
    walk: ['next', 'previous'], time: ['later', 'earlier'], ladder: ['up', 'down'], magnitude: ['up', 'down'],
    depth: ['in', 'out'], place: [null, null]
  };

  // The law's rows (core/law/profiles.yaml `orientations`), as a page carries them in <script id="orientations">: each
  // { order, axis, sense, follows, commands } — sense and follows as the law writes them ("1", "true"). Without them,
  // the same rows as written above.
  function rows(doc) {
    var d = doc || root.document, el = d && d.getElementById && d.getElementById('orientations');
    if (!el) return null;
    try { var t = JSON.parse(el.textContent); return Array.isArray(t) ? t : null; } catch (e) { return null; }
  }
  function table(doc) {
    var r = rows(doc);
    if (!r) return ORIENTATIONS;
    var out = {};
    r.forEach(function (x) { out[x.order] = [x.axis, +x.sense || 1, String(x.follows) === 'true']; });
    return out;
  }
  function commandsOf(order, doc) {
    var r = rows(doc);
    if (r) { for (var i = 0; i < r.length; i++) if (r[i].order === order) return r[i].commands || [null, null]; }
    return COMMANDS[order];
  }

  function frame(doc) {
    var d = doc || root.document, h = d && d.documentElement;
    var dir = h && (h.getAttribute('dir') || '').toLowerCase() === 'rtl' ? 'rtl' : 'ltr';
    return { dir: dir };
  }

  function axis(order, doc) {
    var row = table(doc)[order];
    if (!row) return null;
    var a = row[0], sense = row[1], follows = row[2], rtl = frame(doc).dir === 'rtl';
    if (a === 'inline') return { axis: 'x', sign: follows && rtl ? -sense : sense, mirrored: !!(follows && rtl) };
    if (a === 'block') return { axis: 'y', sign: sense, mirrored: false };
    if (a === 'vertical') return { axis: 'y', sign: sense, mirrored: false };
    if (a === 'z') return { axis: 'z', sign: sense, mirrored: false };
    return { axis: 'map', sign: 1, mirrored: false };
  }

  // A key's meaning for an order: the arrow that points the order's way on this page moves toward its end.
  function command(ev, orders, doc) {
    var k = ev.key, list = [].concat(orders || []);
    if (k === 'Home') return 'first';
    if (k === 'End') return 'last';
    for (var i = 0; i < list.length; i++) {
      var o = list[i], ax = axis(o, doc), c = commandsOf(o, doc);
      if (!ax || !c || !c[0]) continue;
      if (ax.axis === 'x') {
        if (k === 'ArrowRight') return ax.sign > 0 ? c[0] : c[1];
        if (k === 'ArrowLeft') return ax.sign > 0 ? c[1] : c[0];
      } else if (ax.axis === 'y') {
        if (k === 'ArrowDown') return ax.sign > 0 ? c[0] : c[1];
        if (k === 'ArrowUp') return ax.sign > 0 ? c[1] : c[0];
      } else if (ax.axis === 'z') {
        if (k === '+' || k === '=') return c[0];
        if (k === '-') return c[1];
      }
    }
    return null;
  }

  var ARROWS = { right: '→', left: '←', up: '↑', down: '↓' };
  // glyph by meaning: next/later point to the inline end of THIS page; up/down never turn
  function glyph(meaning, doc) {
    var rtl = frame(doc).dir === 'rtl';
    switch (meaning) {
      case 'next': case 'later': case 'forward': return rtl ? ARROWS.left : ARROWS.right;
      case 'previous': case 'earlier': case 'back': return rtl ? ARROWS.right : ARROWS.left;
      case 'up': return ARROWS.up;
      case 'down': return ARROWS.down;
      case 'in': return '⊕';
      case 'out': return '⊖';
      case 'north': return '↑'; case 'south': return '↓'; case 'east': return '→'; case 'west': return '←';
      default: return '';
    }
  }

  function bind(el, orders, handlers) {
    el.addEventListener('keydown', function (ev) {
      if (ev.altKey || ev.ctrlKey || ev.metaKey) return;
      var c = command(ev, orders, el.ownerDocument);
      if (c && handlers[c]) { ev.preventDefault(); handlers[c](); }
    });
  }

  // a swipe toward the inline end means what the arrow pointing there means
  function swipe(el, orders, handlers) {
    var x0 = null, y0 = null;
    el.addEventListener('pointerdown', function (e) { if (e.pointerType !== 'mouse') { x0 = e.clientX; y0 = e.clientY; } });
    el.addEventListener('pointerup', function (e) {
      if (x0 === null) return;
      var dx = e.clientX - x0, dy = e.clientY - y0; x0 = null;
      if (Math.abs(dx) < 40 || Math.abs(dx) < Math.abs(dy)) return;
      var c = command({ key: dx > 0 ? 'ArrowRight' : 'ArrowLeft' }, orders, el.ownerDocument);
      if (c && handlers[c]) handlers[c]();
    });
  }

  var api = { ORIENTATIONS: ORIENTATIONS, COMMANDS: COMMANDS, table: table, frame: frame, axis: axis, command: command,
              glyph: glyph, bind: bind, swipe: swipe };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.daftarDirection = api;
})(typeof window !== 'undefined' ? window : this);
