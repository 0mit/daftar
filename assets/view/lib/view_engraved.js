/* view_engraved.js — the archetypes ENGRAVED FROM READINGS, mounted (core/law/profiles.yaml `archetypes`: queue,
   timeline, flows, sheet). A classic script — no module system, no build step — so the view's own page, which is one
   file, and a host that serves files (daftard) load the same file, as they load widgets/direction.js.

     daftarEngraved.mount(el, view, state)   draws a drawing at a lens that is not its story: `view` is the drawing's
                                             entry (view.engraved: its archetype, axes, layouts, forms, kinds it makes),
                                             state.engraved the page's reading for its reader (drawings, sheets, empty
                                             sheets, settings), state.write(body) a served page's write (a Promise of
                                             {status, answer}), absent offline; state.act(body) its start of a run
                                             from an action, or a decision on its plan (likewise); state.places a host's place lookup
                                             ({here(q, {near}), far(q, {near})}, each a Promise of {places, sources}),
                                             absent offline, when a place is looked up among the garden's own alone
     daftarEngraved.open(bean | {kind}, state)  the sheet of a being, or an empty sheet of a kind, in a dialog

   EVERY VALUE THROUGH ITS WIDGET, EVERY LINE OF HTML THROUGH safe.js. The widgets come from `window.daftarWidgets`
   (each ES module, written into one classic script by view_widgets.py for a page of one file; set by a host's own
   module that imports them). HTML is built only with `h```, put in the page only with `mount`; a position a page
   computes is a data attribute `mount` sets through the CSSOM (no style attribute, no inline script or handler).
   EVERY DIRECTION FROM `orientations`: an order's run is asked of widgets/direction.js, a glyph by its meaning. */
(function (root) {
  'use strict';
  var A = root.daftarArchetypes = root.daftarArchetypes || {};
  var configured = null;

  function tools(state) {
    var w = root.daftarWidgets, E = (state && state.engraved) || {};
    if (!w) throw new Error('daftarEngraved: the widgets are not on this page (window.daftarWidgets)');
    if (configured !== E.settings && E.settings) { w.settings.configure(E.settings); configured = E.settings; }
    var lang = w.locale.langOf({}), t = {
      w: w, h: w.safe.h, join: w.safe.join, mount: w.safe.mount, D: root.daftarDirection, E: E, state: state || {},
      lang: lang, dir: w.locale.dirOf(lang),
      say: function (key, vars) { return w.locale.say(key, {}, vars || {}); },
      write: state && typeof state.write === 'function' ? state.write : null,
      act: state && typeof state.act === 'function' ? state.act : null,
      places: state && state.places && typeof state.places === 'object' ? state.places : null,
      // a being by how the page calls it; a person kept under an opaque id whose name this host does not hold, by what
      // they are — never by the id
      titleOf: function (id) {
        var s = (E.sheets || {})[id], b = (E.beings || []).filter(function (x) { return x.id === id; })[0];
        if (b && b.opaque) return w.locale.say('being-opaque', {}, {});
        return s && s.title || b && b.title || null;
      }
    };
    // THE LAW'S WORDS IN THE READER'S LANGUAGE: a verb, a role, a qualifier, a key beside the roles, a kind, a header
    // key or a form's attribute, as the names layer names it (`names`, sent with the page for its reader); the law's
    // own word where none does
    t.name = function (group, word) { return (((E.names || {})[group] || {})[word]) || word; };
    t.open = function (what) { open(what, state); };
    t.wire = function (el) { wireOpen(t, el); };
    t.forward = function (order) { return forward(t, order); };
    return t;
  }

  /* A VALUE BY ITS SHAPE: a role's spec names the shapes that may fill it (core/law/core.yaml `shapes`), and the widget
     of each (core/law/values.yaml `implements`) shows it. A being by its title, reached by its id; a quantity in a
     currency by money.js at its places, another by number.js and its unit; a position by moment.js where it is a day or
     a moment, else as its namespace writes it (name.js); a row by its label (choice.js); prose by text.js. */
  function show(t, v, spec, o) {
    var w = t.w, h = t.h, shapes = (spec && spec.shape) || [];
    o = o || {};
    if (v === 'unknown') return h`<span class="w-none">${t.say('sheet-unknown')}</span>`;
    if (v === 'self') return h`<span class="eg-self">${t.say('sheet-self')}</span>`;   // the being this bean records
    if (Array.isArray(v)) return t.join(v.map(function (x) { return show(t, x, spec, o); }), ', ');
    if (v && typeof v === 'object' && 'count' in v) {
      var places = w.settings.settings.places[v.unit];
      return places !== undefined ? w.money.show(v.count, v.unit, o)
        : h`${w.number.show(v.count, o)} <bdi dir="ltr" class="w-unit">${v.unit || ''}</bdi>`;
    }
    if (v && typeof v === 'object') {
      if (v.someone) return h`<span class="eg-someone">${t.say('flows-someone')} (${v.someone})</span>`;
      return t.join(Object.keys(v).map(function (k) { return h`<span class="eg-form"><b>${k}</b> ${show(t, v[k], {shape: ['position', 'text']}, o)}</span>`; }), ' ');
    }
    var s = String(v == null ? '' : v);
    if (shapes.indexOf('being') >= 0 && (t.titleOf(s) || (t.E.beings || []).some(function (b) { return b.id === s; }))) {
      return w.being.show(s, t.titleOf(s) || s, {action: 'open'});
    }
    if (shapes.indexOf('position') >= 0 && w.moment.parse(s)) return w.moment.show(s, {style: 'long'});
    if (shapes.indexOf('row') >= 0 && spec.rows) return w.choice.show(s, spec.rows);
    if (shapes.indexOf('text') >= 0 && shapes.length === 1) return w.text.show(s);
    if (o.said && o.said[s]) return w.text.show(o.said[s]);   // a statement named by its words, never by its id
    if (shapes.indexOf('statement') >= 0 || shapes.indexOf('position') >= 0 || shapes.indexOf('row') >= 0) return w.name.show(s);
    return w.text.show(s);
  }

  /* where an order runs: true where the reader's line runs the order's way (so the order is written in reading order),
     false where it runs against it — asked of direction.js for the order the drawing's axes name, never a side */
  function forward(t, order) {
    var ax = t.D ? t.D.axis(order) : null;
    if (!ax || ax.axis !== 'x') return true;
    return (ax.sign > 0) === (t.D.frame().dir === 'ltr');
  }

  /* each being drawn opens its sheet, each `+ new` an empty sheet of its kind: wired once per element, so a renderer
     that draws again wires what it drew */
  function wireOpen(t, el) {
    el.querySelectorAll('[data-action="open"]:not([data-wired]),[data-new]:not([data-wired])').forEach(function (b) {
      b.setAttribute('data-wired', '');
      b.addEventListener('click', function (ev) {
        ev.preventDefault(); ev.stopPropagation();
        t.open(b.hasAttribute('data-new') ? {kind: b.getAttribute('data-new')} : b.getAttribute('data-id'));
      });
    });
  }

  function head(t, view) {
    var h = t.h, e = view.engraved || {};
    return h`<div class="eg-head">${(e.new || []).length ? h`<span class="eg-new">${e.new.map(function (k) {
      return h`<button type="button" class="eg-btn" data-new="${k}">+ ${t.say('sheet-new')} ${t.name('kinds', k)}</button>`; })}</span>` : ''}</div>`;
  }

  function mount(el, view, state) {
    var t = tools(state), e = view.engraved || {}, fn = A[e.archetype];
    var data = ((t.E.drawings || {})[view.key]) || null;
    var box = document.createElement('div');
    box.className = 'eg eg-' + e.archetype;
    el.appendChild(box);
    if (!fn || !data) {
      t.mount(box, t.h`<p class="vw-empty">${t.say('timeline-empty')}</p>`);
      return;
    }
    fn(box, data, t, view);
    var top = document.createElement('div');
    t.mount(top, head(t, view));
    box.insertBefore(top, box.firstChild);
    wireOpen(t, box);
  }

  var dialog = null;
  function open(what, state) {
    var t = tools(state), data = typeof what === 'string' ? (t.E.sheets || {})[what] : (t.E.blank || {})[what && what.kind];
    if (!data || !A.sheet) return;
    if (!dialog) {
      dialog = document.createElement('dialog');
      dialog.className = 'vw eg-dialog';
      document.body.appendChild(dialog);
      dialog.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') dialog.close(); });
    }
    while (dialog.firstChild) dialog.removeChild(dialog.firstChild);
    var box = document.createElement('div');
    box.className = 'eg eg-sheet';
    dialog.appendChild(box);
    A.sheet(box, data, t, null);
    var close = document.createElement('div');
    t.mount(close, t.h`<button type="button" class="eg-btn eg-close">${t.say('sheet-close')}</button>`);
    close.querySelector('button').addEventListener('click', function () { dialog.close(); });
    dialog.appendChild(close);
    wireOpen(t, box);
    if (!dialog.open) { if (dialog.showModal) dialog.showModal(); else dialog.setAttribute('open', ''); }
  }

  root.daftarEngraved = {mount: mount, open: open, show: show, forward: forward, tools: tools};
})(typeof window !== 'undefined' ? window : this);
