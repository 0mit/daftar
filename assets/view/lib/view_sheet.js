/* view_sheet.js — the `sheet` archetype: one being as it stands, and the ONE place it is changed (the view finished for
   a handplace, its §4). It shows the facts the page's `fields` names for the being's kind: its title and summary, and
   each verb's statements in the order the bean holds them — each with the statements that take it as their `of` beneath
   it (a payment with its shares, and the clauses that ask it), who knows it, and, sealed, where it is kept.

   ONE EDIT. Where the reader may write the being, or a part of it a grant's `cover` opens, one Edit turns every fact
   they may write into the widget of its shape — read from the verb's row (`verbs` in the sheet's data: the roles, their
   shapes, what is required), never typed here — with a remove mark on each statement and an add for each verb. ONE SAVE
   is one write, `{bean, ops}` (or `{kind, ops}` for a new being), which the server writes as one commit with one journal
   entry and the gate judges; a refusal is shown at the fact it names, and nothing is kept. Cancel drops the draft. A copy
   of the page offers no Edit. A classic script, built only through safe.js; every value through its widget. */
(function (root) {
  'use strict';
  var A = root.daftarArchetypes = root.daftarArchetypes || {};
  var BESIDE = ['note', 'why'];

  function canon(x) {
    if (Array.isArray(x)) return '[' + x.map(canon).join(',') + ']';
    if (x && typeof x === 'object') return '{' + Object.keys(x).sort().map(function (k) { return JSON.stringify(k) + ':' + canon(x[k]); }).join(',') + '}';
    return JSON.stringify(x == null ? null : String(x));
  }

  A.sheet = function (el, data, t, view) {
    if (data && !data.rows) data = data.bean ? (t.E.sheets || {})[data.bean] : null;   // a sheet drawing: its being's
    var h = t.h, w = t.w;
    if (!data) { t.mount(el, h`<p class="eg-empty">—</p>`); return; }
    var editing = false, n = 0, fo = {names: (t.E.names || {}).forms || {}};   // a form's attributes in the reader's language
    var mayAny = data.may_write || data.rows.some(function (r) { return r.may_add || r.statements.some(function (s) { return s.may; }); })
      || Object.keys(data.header || {}).some(function (k) { return data.header[k].may; });
    var said = data.said || {}, labels = data.labels || {}, courses = data.courses || {};

    // THE PAGE'S WORD FOR A FACT (its `fields` … `label`, in the page's language), else the law's word as the names layer
    // names it in the reader's language, else the law's own
    function word(group, x) { return t.name(group, x); }
    function heading(verb) { return labels[verb] || word('verbs', verb); }
    // A ROLE THAT IS STRUCTURE, NOT A FACT A READER KEEPS: the being itself (`self`), or a link to another statement of
    // this being (a clause to what it asks, a move to the course it is on). Kept as written, never shown, never edited.
    function structural(v) {
      var local = function (x) { return typeof x === 'string' && (x === 'self' || (data.statements || []).indexOf(x) >= 0); };
      return Array.isArray(v) ? v.length > 0 && v.every(local) : local(v);
    }
    function showRole(v, spec) { return spec.form && (data.forms || {})[spec.form] ? shown(v, spec) : root.daftarEngraved.show(t, v, spec, {said: said}); }
    var DAY = /^\d{4}-\d{2}-\d{2}$/;

    function label(verb, k) {
      var row = data.verbs[verb] || {roles: {}, qualifiers: {}};
      return t.name(k in (row.roles || {}) ? 'roles' : k in (row.qualifiers || {}) ? 'qualifiers' : 'beside_roles', k);
    }
    // a value as it is shown: a form's value by its entries (widgets/form.js), one or many, every other by its shape
    function shown(v, spec) {
      var def = spec.form && (data.forms || {})[spec.form];
      if (!def) return root.daftarEngraved.show(t, v, spec);
      return Array.isArray(v) ? t.join(v.map(function (e) { return w.form.show(e, def, fo); }), '; ') : w.form.show(v, def, fo);
    }
    function known(s) {
      if (!s.known || !s.known.by) return '';
      var who = t.titleOf(s.known.by) || s.known.by;
      return h`<div class="eg-known">${t.say('known-' + s.known.act, {by: who})}${s.known.at ? h` · ${w.moment.show(s.known.at, {style: 'long'})}` : ''}</div>`;
    }
    function rolesOf(verb, roles) {
      var row = data.verbs[verb] || {roles: {}, qualifiers: {}}, specs = Object.assign({}, row.roles, row.qualifiers);
      var keys = Object.keys(specs).filter(function (k) { return roles && k in roles; }).concat(BESIDE.filter(function (k) { return roles && k in roles; }))
        .filter(function (k) { return !structural(roles[k]); });
      return t.join(keys.map(function (k) {
        return h`<span class="eg-role" data-role="${k}"><span class="eg-role-name">${label(verb, k)}</span> ${showRole(roles[k], specs[k] || {shape: ['text']})}</span>`;
      }), ' ');
    }
    function readOne(s) {
      var held = s.held ? h`<span class="eg-held">${s.held.here ? t.say('sheet-held') : s.held.host ? t.say('sheet-kept-on', {host: t.titleOf(s.held.host) || s.held.host}) : t.say('sheet-kept-off')}</span>` : '';
      return h`<li class="eg-statement${s.held ? ' eg-sealed' : ''}" data-fact="${s.key}">
        <div class="eg-roles">${s.roles ? rolesOf(s.verb, s.roles) : ''} ${held}</div>${known(s)}
        ${(s.defaults || []).map(function (d) {
          return h`<div class="eg-default">${heading(d.verb)}: ${w.being.show(d.by, t.titleOf(d.by) || d.title || d.by, {action: 'open'})} — ${t.say('sheet-default', {says: d.says})}</div>`; })}
        ${(s.dependents || []).length ? h`<ol class="eg-dependents">${s.dependents.map(function (d) {
          return h`<li class="eg-dependent" data-fact="${d.key}"><span class="eg-verb">${heading(d.verb)}</span> ${d.roles ? rolesOf(d.verb, d.roles) : ''}${known(d)}</li>`;
        })}</ol>` : ''}</li>`;
    }

    /* ---------------- editing: a widget per role, by its shape ---------------- */
    function nameOf(prefix, role) { return prefix + '.' + role; }
    // WHERE A PERSON WILL BE IS LOOKED UP HERE ALONE (design §12): a happening's place, or a being's that holds an
    // `attend`, is never sent to a place service beyond the machine; nor is a place held off git (editOne)
    var whereabouts = data.kind === 'event' || (data.rows || []).some(function (r) { return r.verb === 'attend'; }), sealed = whereabouts;
    // a `be` that says where a being is — placed as a location or a place, or not yet said, or at a position a place
    // lookup reads — and never one that says when (a happening's time)
    function placeLike(roles, v) {
      var as = roles && roles.as, list = v === undefined ? [] : [].concat(v);
      if (as === 'location' || as === 'place') return true;
      return !as && (!list.length || list.some(function (x) { return /^(EPSG:|osm:|geonames:)/.test(String(x)); }));
    }
    // where a being is: a place to change by the lookup, already said or not — a position, but no moment as the law writes it
    function placeField(verb, k, roles, v) { return verb === 'be' && k === 'at' && !!w.place && placeLike(roles, v); }
    // A FIELD FOR EACH FACT THE READER KEEPS, by its shape: what holds a value and what the verb requires are drawn, the
    // rest waits under «more»; what is structure (`structural`) and what is history (a moment written, a step a move
    // reached) is shown as it is and kept as written — never an id, never a moment typed as the law writes it
    function editor(verb, roles, prefix, may) {
      var row = data.verbs[verb] || {roles: {}, qualifiers: {}, required: []}, specs = Object.assign({}, row.roles, row.qualifiers);
      var keys = Object.keys(specs).concat(BESIDE).filter(function (k) { return !(roles && k in roles && structural(roles[k])); });
      function field(k) {
        var spec = specs[k] || {shape: ['text']}, v = roles ? roles[k] : undefined, shapes = spec.shape || ['text'];
        var req = (row.required || []).indexOf(k) >= 0, nm = nameOf(prefix, k), input;
        var asIs = h`<span class="eg-role" data-role="${k}" data-kept=""><span class="eg-role-name">${label(verb, k)}</span> ${showRole(v, spec)}</span>`;
        if (!may) return v === undefined ? '' : asIs;
        var def = shapes.indexOf('form') >= 0 && spec.form && (data.forms || {})[spec.form];
        if (!def && shapes.indexOf('position') >= 0 && v !== undefined && !(typeof v === 'string' && DAY.test(v))
            && !placeField(verb, k, roles, v)) return asIs;
        if (def) {                                  // a form's value, drawn by its entries (widgets/form.js)
          input = spec.many === 'true'
            ? t.join((Array.isArray(v) ? v : []).concat([{}]).map(function (e, i) { return h`<span class="eg-form-entry">${w.form.edit(nm + '.' + i, e, def, fo)}</span>`; }), '')
            : w.form.edit(nm, v, def, fo);
        } else if (placeField(verb, k, roles, v)) {   // where a being is (widgets/place.js)
          input = w.place.edit(nm, v, {sealed: sealed, label: typeof v === 'string' ? t.titleOf(v) || '' : ''});
        } else if (shapes.indexOf('being') >= 0 && (v === undefined || typeof v === 'string') && spec.many !== 'true') {
          var rows = (t.E.beings || []).filter(function (b) { return !spec.kind || [].concat(spec.kind).indexOf(b.kind) >= 0; })
            .map(function (b) { return {value: b.id, label: b.opaque ? t.say('being-opaque') : b.title || b.id}; });
          [['theone', t.say('being-theone')], ['unknown', t.say('sheet-unknown')]].forEach(function (x) { rows.push({value: x[0], label: x[1]}); });
          if (v && !rows.some(function (r) { return r.value === v; })) rows.push({value: v, label: t.titleOf(v) || t.say('being-opaque')});
          input = w.choice.edit(nm, v || '', rows, {none: '—'});
        } else if (spec.many === 'true' || Array.isArray(v)) {
          if (v !== undefined && (shapes.indexOf('being') >= 0 || shapes.indexOf('statement') >= 0)) return asIs;
          input = w.name.edit(nm, Array.isArray(v) ? v.join(', ') : (v || ''));
        } else if (shapes.indexOf('quantity') >= 0 && (v === undefined || (v && typeof v === 'object'))) {
          input = h`${w.number.edit(nm + '.count', v ? v.count : '')} ${w.name.edit(nm + '.unit', v ? v.unit : '')}`;
        } else if (shapes.indexOf('statement') >= 0 && (v === undefined || typeof v === 'string') && shapes.length === 1) {
          if (v !== undefined) return asIs;
          input = w.choice.edit(nm, '', (data.statements || []).map(function (x) { return {value: x, label: said[x] || x}; }), {none: '—'});
        } else if (shapes.indexOf('row') >= 0 && spec.rows && (v === undefined || spec.rows.indexOf(v) >= 0)) {
          input = w.choice.edit(nm, v || '', spec.rows, {none: '—'});
        } else if (shapes.indexOf('position') >= 0) {
          input = w.moment.edit(nm, v || '');
        } else if (shapes.indexOf('form') >= 0 && v && typeof v === 'object') {
          input = w.name.edit(nm + '.json', JSON.stringify(v));
        } else if (shapes.indexOf('text') >= 0 || BESIDE.indexOf(k) >= 0) {
          input = w.text.edit(nm, v || '');
        } else {
          input = w.name.edit(nm, typeof v === 'string' ? v : v === undefined ? '' : JSON.stringify(v));
        }
        return h`<label class="eg-field${req ? ' eg-req' : ''}" data-role="${k}"><span class="eg-role-name">${label(verb, k)}${req ? h` <span class="eg-req-word">(${t.say('sheet-required')})</span>` : ''}</span> ${input}<span class="eg-err" data-err="${nm}"></span></label>`;
      }
      var main = keys.filter(function (k) { return (roles && roles[k] !== undefined && roles[k] !== '') || (row.required || []).indexOf(k) >= 0; });
      var more = keys.filter(function (k) { return main.indexOf(k) < 0; });
      // a statement holding nothing but its structure (a clause not yet given a day) offers what it may hold, open
      if (!main.length) return h`${t.join(more.map(field), '')}`;
      return h`${t.join(main.map(field), '')}${may && more.length ? h`<details class="eg-more"><summary>${t.say('sheet-more')}</summary>${t.join(more.map(field), '')}</details>` : ''}`;
    }
    // what a statement keeps as written whatever the fields say: its structure, and what is shown as it is
    function keptOf(verb, roles) {
      var row = data.verbs[verb] || {roles: {}, qualifiers: {}}, specs = Object.assign({}, row.roles, row.qualifiers), out = {};
      Object.keys(roles || {}).forEach(function (k) {
        var v = roles[k], shapes = (specs[k] || {}).shape || [];
        if (placeField(verb, k, roles, v)) return;   // a place is the lookup's field, read back from it
        if (structural(v) || (shapes.indexOf('position') >= 0 && !(typeof v === 'string' && DAY.test(v)))
            || ((Array.isArray(v) || (specs[k] || {}).many === 'true') && (shapes.indexOf('being') >= 0 || shapes.indexOf('statement') >= 0))
            || (shapes.indexOf('statement') >= 0 && shapes.length === 1 && typeof v === 'string')) out[k] = v;
      });
      return out;
    }
    // A MOVE ALONG A WALK is history once made: shown as it is; a new one is a step chosen by the walk's own words, from
    // now, on the course the being is on
    function moveFields(prefix) {
      var ids = Object.keys(courses);
      if (!ids.length) return '';
      var c = courses[ids[0]];
      return h`<label class="eg-field eg-req" data-role="at"><span class="eg-role-name">${heading('move')}</span> ${
        w.choice.edit(prefix + '.step', '', c.steps.map(function (x) { return {value: x.ref, label: x.says}; }), {none: '—'})}<span class="eg-err" data-err="${prefix}.step"></span></label>
        <label class="eg-field" data-role="note"><span class="eg-role-name">${label('move', 'note')}</span> ${w.text.edit(prefix + '.note', '')}</label>`;
    }
    function editOne(s, parentId) {
      var p = 's' + (n++), may = s.may && !!s.roles && s.verb !== 'move';
      sealed = whereabouts || !!s.held;
      return h`<li class="eg-statement eg-editing" data-fact="${s.key}" data-prefix="${p}" data-verb="${s.verb}" data-kept="${JSON.stringify(keptOf(s.verb, s.roles))}"${may ? '' : h` data-asis=""`}${s.held ? h` data-held=""` : ''}>
        ${parentId ? h`<span class="eg-verb">${heading(s.verb)}</span>` : ''}
        <div class="eg-fields">${may ? editor(s.verb, s.roles, p, true) : h`<div class="eg-roles">${s.roles ? rolesOf(s.verb, s.roles) : ''}</div>`}</div>
        ${s.held && !s.roles ? h`<span class="eg-held">${s.held.host ? t.say('sheet-kept-on', {host: t.titleOf(s.held.host) || s.held.host}) : t.say('sheet-kept-off')}</span>` : ''}
        ${s.may && (!s.held || s.held.here) ? h`<label class="eg-remove"><input type="checkbox" data-remove="${s.key}"> ${t.say('sheet-remove')}</label>` : ''}
        ${(s.dependents || []).length ? h`<ol class="eg-dependents">${s.dependents.map(function (d) { return editOne(d, s.id); })}</ol>` : ''}
        ${s.may && s.id ? t.join(Object.keys(depVerbs(s)).map(function (v) {
          return h`<button type="button" class="eg-btn eg-add" data-add="${v}" data-of="${s.id}">+ ${t.say('sheet-add')} ${heading(v)}</button>`; }), ' ') : ''}
        <span class="eg-err" data-err-fact="${s.key}"></span></li>`;
    }
    function depVerbs(s) {
      var out = {};
      (s.dependents || []).forEach(function (d) { out[d.verb] = true; });
      return out;
    }
    function blankOne(verb, of) {
      var p = 'a' + (n++), preset = of ? {of: of} : {}, me = ((t.E.settings || {}).garden || {}).me;
      sealed = whereabouts;
      if (verb === 'move' && Object.keys(courses).length) {
        preset = {of: 'self', through: Object.keys(courses)[0]};
        if (me) preset.by = me;
        return h`<li class="eg-statement eg-editing eg-added" data-prefix="${p}" data-verb="${verb}" data-add-op="" data-move="" data-kept="${JSON.stringify(preset)}">
          <div class="eg-fields">${moveFields(p)}</div><span class="eg-err" data-err-op=""></span></li>`;
      }
      return h`<li class="eg-statement eg-editing eg-added" data-prefix="${p}" data-verb="${verb}" data-add-op="" data-kept="${JSON.stringify(keptOf(verb, preset))}">
        <div class="eg-fields">${editor(verb, preset, p, true)}</div><span class="eg-err" data-err-op=""></span></li>`;
    }

    // A PERSON KEPT OFF GIT BY NAME: their contact, sent by the host that keeps it to a reader who may read them —
    // shown here as kept on this machine only, never written into the page's own copy or the ledger
    function contact() {
      var c = data.contact;
      if (!c) return '';
      return h`<section class="eg-row eg-contact" data-fact="contact"><h4>${t.say('sheet-contact')}</h4>${Object.keys(c).map(function (k) {
        return h`<div class="eg-detail"><span class="eg-role-name">${w.text.show(k)}</span> ${/^[+\d][\d\s()-]{5,}$/.test(String(c[k])) ? w.name.show(c[k], {kind: 'phone'}) : w.text.show(c[k])}</div>`;
      })}<p class="eg-held">${t.say('sheet-held')}</p></section>`;
    }
    // WHAT A PAGE NAMES OF `details` (its `fields`): what fits no verb yet, kept whole until one is proposed — drawn as it
    // is held, key by key, each value by the widget of what it looks like (a day, an amount, words), and never edited
    // here: a sheet changes statements and the header, and what `details` keeps waits for its verb
    function details() {
      var keys = Object.keys(data.details || {});
      if (!keys.length) return '';
      function one(v) {
        if (v && typeof v === 'object' && !Array.isArray(v) && !('count' in v)) {
          return h`<dl class="eg-details-map">${Object.keys(v).map(function (k) { return h`<dt>${w.text.show(k)}</dt><dd>${one(v[k])}</dd>`; })}</dl>`;
        }
        return root.daftarEngraved.show(t, v, {shape: ['position', 'text']});
      }
      return h`<section class="eg-row eg-details" data-fact="details"><h4>${t.say('sheet-details')}</h4>${keys.map(function (k) {
        return h`<div class="eg-detail" data-detail="${k}"><span class="eg-role-name">${w.text.show(labels[k] || k)}</span> ${one(data.details[k])}</div>`;
      })}<p class="eg-known">${t.say('sheet-details-kept')}</p></section>`;
    }
    // THE TAGS, a set of words the page names among a being's facts: each a word of its own, in its own isolate
    function tagsOf(tags) {
      return tags && (tags.value || []).length ? h`<p class="eg-tags" data-fact="header:tags">${t.join(tags.value.map(function (x) { return h`<span class="eg-tag">${w.text.show(x)}</span>`; }), ' ')}</p>` : '';
    }
    function draw() {
      n = 0;
      var hd = data.header || {}, title = hd.title || {}, summary = hd.summary, tags = hd.tags;
      var named = data.new ? (t.say('sheet-new') + ' ' + t.name('kinds', data.kind)) : data.title;
      var head = editing
        ? h`<div class="eg-sheet-head">${title.may ? h`<label class="eg-field" data-fact="header:title"><span class="eg-role-name">${labels.title || word('header', 'title')}</span> ${w.text.edit('header.title', title.value === data.bean ? '' : (title.value || ''), {placeholder: data.title})}<span class="eg-err" data-err-fact="header:title"></span></label>` : h`<h3>${w.text.show(named)}</h3>`}
            ${tags ? (tags.may ? h`<label class="eg-field" data-fact="header:tags"><span class="eg-role-name">${labels.tags || word('header', 'tags')}</span> ${w.text.edit('header.tags', (tags.value || []).join(t.say('sheet-tags-sep')))}<span class="eg-err" data-err-fact="header:tags"></span></label>` : tagsOf(tags)) : ''}
            ${summary ? (summary.may ? h`<label class="eg-field" data-fact="header:summary"><span class="eg-role-name">${labels.summary || word('header', 'summary')}</span> ${w.text.edit('header.summary', summary.value || '', {lines: true})}<span class="eg-err" data-err-fact="header:summary"></span></label>` : h`<p class="eg-summary">${w.text.show(summary.value)}</p>`) : ''}</div>${details()}`
        : h`<div class="eg-sheet-head"><h3 data-fact="header:title">${w.text.show(named)}</h3>${summary && summary.value ? h`<p class="eg-summary" data-fact="header:summary">${w.text.show(summary.value)}</p>` : ''}${tagsOf(tags)}</div>${contact()}${details()}`;
      // a verb whose statements are each shown beneath the one they are `of` (a clause beneath what it asks) has no row of
      // its own: it is added there
      var ownRows = data.rows.filter(function (r) {
        var dependent = ((data.verbs[r.verb] || {}).roles || {}).of && (((data.verbs[r.verb] || {}).roles.of.shape) || []).join() === 'statement';
        return r.statements.length || (editing && r.may_add && !dependent);
      });
      var rows = ownRows.length ? ownRows.map(function (r) {
        var meaning = (data.verbs[r.verb] || {}).meaning || '';
        return h`<section class="eg-row" data-verb="${r.verb}"><h4 title="${meaning}">${heading(r.verb)}</h4><ol class="eg-statements">${
          editing ? r.statements.map(function (s) { return editOne(s); }) : r.statements.map(function (s) { return readOne(s); })}</ol>${
          editing && r.may_add ? h`<button type="button" class="eg-btn eg-add" data-add="${r.verb}">+ ${t.say('sheet-add')} ${heading(r.verb)}</button>` : ''}</section>`;
      }) : h`<p class="eg-empty">${t.say('sheet-none', {kind: t.name('kinds', data.kind)})}</p>`;
      var bar = !t.write ? h`<p class="eg-copy">${t.say('sheet-copy')}</p>`
        : !mayAny ? ''
          : editing ? h`<div class="eg-bar"><button type="button" class="eg-btn eg-primary" data-do="save">${t.say('sheet-save')}</button> <button type="button" class="eg-btn" data-do="cancel">${t.say('sheet-cancel')}</button> <span class="eg-said" data-said=""></span></div>`
            : h`<div class="eg-bar"><button type="button" class="eg-btn eg-primary" data-do="edit">${t.say('sheet-edit')}</button></div>`;
      t.mount(el, h`${head}${rows}${bar}<p class="eg-err eg-general" data-err-general=""></p>`);
      wire();
    }

    // a place field's lookup: the garden's own places the page carries, then the host's, where it has one
    function wirePlaces(within) {
      if (!w.place) return;
      within.querySelectorAll('[data-place]').forEach(function (box) {
        w.place.wire(box, {own: t.E.places || [], here: t.places && t.places.here, far: t.places && t.places.far},
          {sealed: box.classList.contains('w-place-sealed')});
      });
    }
    function wire() {
      t.wire(el);
      wirePlaces(el);
      el.querySelectorAll('[data-do]').forEach(function (b) {
        b.addEventListener('click', function () {
          var d = b.getAttribute('data-do');
          if (d === 'edit') { editing = true; draw(); }
          else if (d === 'cancel') { editing = false; draw(); }
          else save();
        });
      });
      el.querySelectorAll('[data-add]').forEach(function (b) {
        b.addEventListener('click', function () {
          var holder = document.createElement('div');
          t.mount(holder, blankOne(b.getAttribute('data-add'), b.getAttribute('data-of')));
          var li = holder.firstElementChild, list = b.previousElementSibling && b.previousElementSibling.tagName === 'OL'
            ? b.previousElementSibling : b.parentNode.querySelector('ol');
          (list || b.parentNode).appendChild(li);
          wirePlaces(li);
        });
      });
    }

    /* what a field holds, as the law writes it — or an error said at the field */
    function readFields(li, verb, errs, known) {
      var p = li.getAttribute('data-prefix'), row = data.verbs[verb] || {roles: {}, qualifiers: {}}, specs = Object.assign({}, row.roles, row.qualifiers);
      var roles = {}, area = false;
      if (li.hasAttribute('data-move')) {
        var step = li.querySelector('[name="' + p + '.step"]'), note = li.querySelector('[name="' + p + '.note"]');
        if (!step || !step.value) { errs.push([p + '.step', t.say('sheet-step-needed')]); return {}; }
        roles = Object.assign({}, JSON.parse(li.getAttribute('data-kept') || '{}'), {at: ['now', step.value]});
        if (note && note.value.trim()) roles.note = note.value.trim();
        return roles;
      }
      Object.keys(specs).concat(BESIDE).forEach(function (k) {
        var nm = p + '.' + k, spec = specs[k] || {shape: ['text']}, q = function (x) { return li.querySelector('[name="' + x + '"]'); };
        var pl = li.querySelector('[data-place="' + nm + '"]');
        if (pl) {                                   // a place: the one picked, or a position typed with its system
          var r = w.place.take(w.place.collect(pl), {free: true});
          if (r.error) { errs.push([nm, r.error]); return; }
          if (r.value.length) roles[k] = r.value.length === 1 ? r.value[0] : r.value;
          if (r.read && known) known.read = r.read;  // where it was read: the save's `read` of that source
          area = area || !!r.area;
          return;
        }
        if (q(nm + '.count')) {
          var c = w.number.take(q(nm + '.count').value), u = w.name.take(q(nm + '.unit').value);
          if (c.error) { errs.push([nm, c.error]); return; }
          if (c.value !== '' || u.value) roles[k] = {count: c.value, unit: u.value};
          return;
        }
        var def = spec.form && (data.forms || {})[spec.form];
        if (def) {                                  // a form's value, as the law writes it, or an error at its field
          var takeOne = function (n2) {
            var r = w.form.take(w.form.collect(li, n2), def);
            if (r.error) { errs.push([n2 + '.' + r.at, r.error]); return undefined; }
            return Object.keys(r.value).length ? r.value : undefined;
          };
          if (spec.many === 'true') {
            var list = [];
            for (var i = 0; li.querySelector('[data-name="' + nm + '.' + i + '"]'); i++) { var e = takeOne(nm + '.' + i); if (e) list.push(e); }
            if (list.length) roles[k] = list;
          } else {
            var one = takeOne(nm);
            if (one) roles[k] = one;
          }
          return;
        }
        if (q(nm + '.json')) {
          var s = q(nm + '.json').value.trim();
          if (s) { try { roles[k] = JSON.parse(s); } catch (e) { errs.push([nm, String(e.message || e)]); } }
          return;
        }
        var el2 = q(nm);
        if (!el2) return;
        var v = el2.value;
        if (el2.classList.contains('w-moment-input')) {
          var m = w.moment.take(v);
          if (m.error) { errs.push([nm, m.error]); return; }
          v = m.value;
        } else if (spec.many === 'true') {            // many fillers: written as the bean writes them, a comma between
          v = v.split(',').map(function (x) { return x.trim(); }).filter(Boolean);
          if (v.length) roles[k] = v;
          return;
        } else {
          v = v.trim();
        }
        if (v !== '') roles[k] = v;
      });
      var kept = JSON.parse(li.getAttribute('data-kept') || '{}');
      Object.keys(kept).forEach(function (k) { roles[k] = kept[k]; });
      // AN AREA PICKED where a `be` says nothing of how it places is placed as a place: an area holds many, and two
      // bodies are not in one room only at a point (the room rule; each system's `covers`)
      if (area && verb === 'be' && !roles.as) roles.as = 'place';
      return roles;
    }

    function save() {
      var ops = [], where = [], errs = [];
      el.querySelectorAll('[data-err],[data-err-fact],[data-err-op],[data-err-general]').forEach(function (e) { e.textContent = ''; });
      var hd = data.header || {};
      ['title', 'summary'].forEach(function (k) {
        var f = el.querySelector('[name="header.' + k + '"]'), was = (hd[k] || {}).value || '';
        if (k === 'title' && was === data.bean) was = '';          // offered empty: left so, it stays as it was
        if (f && was !== f.value.trim()) {
          ops.push({op: 'change', header: k, value: f.value.trim()}); where.push(f.closest('[data-fact]'));
        }
      });
      var tf = el.querySelector('[name="header.tags"]');
      if (tf) {                                     // the tags: words, as the reader's language separates a list of them
        var words = tf.value.split(new RegExp('[' + t.say('sheet-tags-sep').trim() + ',]')).map(function (x) { return x.trim(); }).filter(Boolean);
        if (JSON.stringify(words) !== JSON.stringify((hd.tags || {}).value || [])) { ops.push({op: 'change', header: 'tags', value: words}); where.push(tf.closest('[data-fact]')); }
      }
      var originals = {};
      data.rows.forEach(function (r) { r.statements.forEach(function (s) { originals[s.key] = s; (s.dependents || []).forEach(function (d) { originals[d.key] = d; }); }); });
      el.querySelectorAll('[data-remove]').forEach(function (c) {
        if (c.checked) { ops.push({op: 'remove', key: c.getAttribute('data-remove')}); where.push(c.closest('[data-fact]')); }
      });
      el.querySelectorAll('li.eg-editing').forEach(function (li) {
        var verb = li.getAttribute('data-verb'), key = li.getAttribute('data-fact');
        var known = {};
        if (li.hasAttribute('data-add-op')) {
          var roles = readFields(li, verb, errs, known);
          if (Object.keys(roles).length) { ops.push(Object.assign({op: 'add', verb: verb, roles: roles}, known.read ? {read: known.read} : {})); where.push(li); }
          return;
        }
        var s = originals[key];
        if (!s || !s.may || !s.roles || li.hasAttribute('data-asis') || (el.querySelector('[data-remove="' + key + '"]') || {}).checked) return;
        var now = readFields(li, verb, errs, known);
        if (canon(now) !== canon(s.roles)) {
          ops.push(Object.assign({op: 'change', key: key, roles: now}, s.held ? {held: true} : {}, known.read ? {read: known.read} : {})); where.push(li);
        }
      });
      if (errs.length) {
        errs.forEach(function (e) { var x = el.querySelector('[data-err="' + e[0] + '"]'); if (x) x.textContent = e[1]; });
        return;
      }
      if (!ops.length) { editing = false; draw(); return; }
      var said = el.querySelector('[data-said]');
      t.write(data.new ? {kind: data.kind, ops: ops} : {bean: data.bean, ops: ops}).then(function (r) {
        var a = r.answer || {};
        if (a.ok) {
          if (said) said.textContent = t.say('sheet-saved');
          if (root.location && root.location.reload) setTimeout(function () { root.location.reload(); }, 400);
          return;
        }
        var general = [];
        (a.refusals || []).forEach(function (x) {
          var at = x.op != null && where[x.op] ? where[x.op] : x.fact ? el.querySelector('[data-fact="' + x.fact + '"]') : null;
          var slot = at && (at.querySelector('[data-err-fact],[data-err-op]') || at);
          if (slot && slot !== at) slot.textContent = (slot.textContent ? slot.textContent + ' · ' : '') + x.message;
          else general.push(x.message);
          if (at) at.classList.add('eg-refused');
        });
        var g = el.querySelector('[data-err-general]');
        if (g) g.textContent = t.say('sheet-refused') + (general.length ? ' ' + general.join(' · ') : '');
      });
    }
    draw();
  };
})(typeof window !== 'undefined' ? window : this);
