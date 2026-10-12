/* view_flows.js — the `flows` archetype: who owes whom, per currency, netted as bin/ledger.py nets it (the server's
   reading, `view_engraved.py` `flows`, from `ledger.reading`), or what went between gardens. Each arrow is a line: the
   one it runs from at the start of the reader's line, the glyph of `next` (widgets/direction.js: it points to the line's
   end in either script), the one it runs to, and its amount, exact, by money.js — an uneven one shown as the fraction it
   is. Flow runs along the reader's line (`axes: { inline: flow }`). A party the reader may not read is `someone`, never
   named. A classic script, built only through safe.js. */
(function (root) {
  'use strict';
  var A = root.daftarArchetypes = root.daftarArchetypes || {};

  A.flows = function (el, data, t, view) {
    var h = t.h, w = t.w, nodes = {};
    var axes = (view && view.engraved && view.engraved.axes) || {inline: 'flow'};
    var fwd = t.forward(axes.inline || 'flow');
    (data.nodes || []).forEach(function (n) { nodes[n.id] = n; });
    var glyph = t.D ? t.D.glyph(fwd ? 'next' : 'previous') : '';
    function node(id) {
      var n = nodes[id] || {};
      if (n.here && !n.title) return h`<span class="eg-node eg-here" title="${id}">${t.say('flows-here')}</span>`;
      if (n.unnamed) return h`<span class="eg-node eg-unnamed" title="${id}">${unnamedWord(n)}</span>`;
      if (n.someone || n.title === null && !n.here) return h`<span class="eg-node eg-someone">${t.say('flows-someone')}</span>`;
      var title = n.title || id;
      return (t.E.sheets || {})[id] ? w.being.show(id, title, {action: 'open'}) : h`<bdi class="eg-node">${title}</bdi>`;
    }
    // a garden whose bean says no more of it than its id is called another garden — its place among them, in the
    // reader's digits, where there are several; this garden is the one the page is read in
    function unnamedWord(n) { return n.n ? t.say('flows-garden-n', {n: w.number.count(n.n)}) : t.say('flows-garden'); }
    function plain(id) {
      var n = nodes[id] || {};
      return n.here && !n.title ? t.say('flows-here') : n.unnamed ? unnamedWord(n) : n.someone ? t.say('flows-someone') : (n.title || id);
    }
    function line(a) {
      var ends = fwd ? [node(a.from), node(a.to)] : [node(a.to), node(a.from)];
      var said = data.nodes_are === 'gardens' ? t.say('flows-went', {from: plain(a.from), to: plain(a.to)})
        : t.say('flows-owes', {from: plain(a.from), to: plain(a.to)});
      var what = data.nodes_are === 'gardens'
        ? h`<span class="eg-what">${t.join((a.what || []).map(function (b) {     // each being by how the page calls it
          var called = t.titleOf(b);
          return called ? w.being.show(b, called, (t.E.sheets || {})[b] ? {action: 'open'} : {}) : w.name.show(b);
        }), ', ')}</span>`
        : h`<span class="eg-amount">${w.money.show(a.count, a.unit)}</span>`;
      return h`<li class="eg-flow" data-from="${a.from}" data-to="${a.to}" title="${said}"><span class="eg-ends">${ends[0]} <span class="eg-arrow" aria-label="${said}">${glyph}</span> ${ends[1]}</span> ${what}</li>`;
    }
    var arrows = data.arrows || [];
    var units = [];
    arrows.forEach(function (a) { if (a.unit && units.indexOf(a.unit) < 0) units.push(a.unit); });
    var body = !arrows.length ? h`<p class="eg-empty">${t.say('flows-empty')}</p>`
      : data.nodes_are === 'gardens' ? h`<ol class="eg-flows">${arrows.map(line)}</ol>`
        : h`${units.map(function (u) {
          return h`<section class="eg-currency" data-unit="${u}"><h4><bdi dir="ltr">${u}</bdi></h4><ol class="eg-flows">${
            arrows.filter(function (a) { return a.unit === u; }).map(line)}</ol></section>`;
        })}`;
    t.mount(el, h`${body}${data.partial ? h`<p class="eg-partial">${t.say('flows-partial')}</p>` : ''}`);
    t.wire(el);
  };
})(typeof window !== 'undefined' ? window : this);
