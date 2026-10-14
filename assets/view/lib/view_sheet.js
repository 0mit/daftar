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
      || Object.keys(data.header || {}).some(function (k) { return data.header[k].may; }) || (data.records || []).length > 0;
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
    // WHO BEARS A PAYMENT, IN ONE LINE (view_engraved.py `shares_of`): each bearer, their part as the fraction it is and
    // as an amount, where the shares come from — the payment's own, its agreement's, or the law's default — and what each
    // then owes each payer; who said each share is the line's title, never a line of its own
    function sharesLine(s) {
      var sh = s.shares, E = root.daftarEngraved;
      if (!sh) return '';
      var said = (s.dependents || []).filter(function (d) { return d.verb === 'bear' && d.known; }).map(function (d) {
        return t.say('sheet-said-by', {who: t.titleOf(d.known.by) || d.known.by || '', at: d.known.at || ''});
      }).join(' · ');
      var parts = t.join(sh.bearers.map(function (b) {
        return h`<span class="eg-bearer">${E.party(t, b)} ${w.number.show(b.share, {fraction: 'inline'})} (${E.show(t, {count: b.amount, unit: sh.unit}, {})})</span>`;
      }), ' · ');
      var from = sh.source === 'agreement' ? h` <span class="eg-share-from">${t.say('shares-from-agreement')}</span>`
        : sh.source === 'default' ? h` <span class="eg-share-from">${t.say('shares-default')}</span>` : '';
      var owes = t.join((sh.owes || []).map(function (o) {
        return h`<span class="eg-owes">${E.sentence(t, 'shares-owes', {from: E.party(t, o.from), to: E.party(t, o.to), amount: E.show(t, {count: o.amount, unit: sh.unit}, {})})}</span>`;
      }), ' · ');
      return h`<div class="eg-shares" data-source="${sh.source}"${said ? h` title="${said}"` : ''}><span class="eg-verb">${heading('bear')}:</span> ${parts}${from}${(sh.owes || []).length ? h` → ${owes}` : ''}</div>`;
    }
    function readOne(s) {
      var held = s.held ? h`<span class="eg-held">${s.held.here ? t.say('sheet-held') : s.held.host ? t.say('sheet-kept-on', {host: t.titleOf(s.held.host) || s.held.host}) : t.say('sheet-kept-off')}</span>` : '';
      var deps = (s.dependents || []).filter(function (d) { return !(s.shares && d.verb === 'bear'); });
      return h`<li class="eg-statement${s.held ? ' eg-sealed' : ''}" data-fact="${s.key}">
        <div class="eg-roles">${s.roles ? rolesOf(s.verb, s.roles) : ''} ${held}</div>${known(s)}${rowActions(s)}
        ${s.shares ? sharesLine(s) : (s.defaults || []).map(function (d) {
          return h`<div class="eg-default">${heading(d.verb)}: ${w.being.show(d.by, t.titleOf(d.by) || d.title || d.by, {action: 'open'})} — ${t.say('sheet-default', {says: d.says})}</div>`; })}
        ${deps.length ? h`<ol class="eg-dependents">${deps.map(function (d) {
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
        return h`<div class="eg-detail"><span class="eg-role-name">${w.text.show(fieldWord('contact', k))}</span> ${/^[+\d][\d\s()-]{5,}$/.test(String(c[k])) ? w.name.show(c[k], {kind: 'phone'}) : w.text.show(c[k])}</div>`;
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
    // WHAT THE PAGE READS FOR THIS BEING (its `fields` … `reading`): read as the sheet is opened, never stored. A person's
    // account in the books says who owes whom in a sentence of the reader's words — the reader themselves as "you" where
    // the books are theirs — and opens its lines: each with the record it rests on and why it is there
    function readings() {
      var rs = data.readings || [], E = root.daftarEngraved;
      if (!rs.length) return '';
      return rs.map(function (r) {
        var notes = (r.notes || []).map(function (x) { return h`<p class="eg-partial">${w.text.show(x)}</p>`; });
        var body = '';
        if (r.books) {
          body = (r.accounts || []).length ? r.accounts.map(function (a) {
            var amount = E.show(t, {count: String(a.balance).replace(/^-/, ''), unit: a.unit}, {});
            var you = r.entity && r.entity.you;
            var key = a.owes === 'party' ? (you ? 'account-owes-you' : 'account-owes')
              : a.owes === 'entity' ? (you ? 'account-you-owe' : 'account-entity-owes') : 'account-settled';
            var name = ((t.E.codes || {})[a.code] || {}).name || a.name;
            return h`<div class="eg-account" data-account="${a.code}" data-unit="${a.unit}" data-owes="${a.owes || 'none'}"><p class="eg-account-says">${E.sentence(t, key, {party: E.party(t, r.party), entity: E.party(t, r.entity), amount: amount})}</p><details class="eg-ledger"><summary>${t.say('account-lines')} · ${w.text.show(name)}</summary>${E.ledger(t, {lines: a.lines}, a.unit, {noOpening: true})}</details></div>`;
          }) : h`<p class="eg-empty">${t.say('account-none')}</p>`;
        } else if ((r.groups || []).length) {
          body = h`<table class="eg-table"><tbody>${r.groups.map(function (g) {
            return h`<tr><th scope="row">${E.show(t, g.key, {shape: ['text']})}</th><td>${g.unit ? E.show(t, {count: g.amount, unit: g.unit}, {}) : w.text.show(g.amount)}</td></tr>`;
          })}</tbody></table>`;
        } else if ((r.members || []).length) {
          body = h`<ul class="eg-members">${r.members.map(function (m) { return h`<li>${w.being.show(m.bean, m.title || m.bean, {action: 'open'})}</li>`; })}</ul>`;
        } else if (r.value) {
          body = h`<p>${r.value.unit ? E.show(t, {count: r.value.amount, unit: r.value.unit}, {}) : w.text.show(r.value.amount)}</p>`;
        }
        return h`<section class="eg-row eg-reading" data-fact="${r.fact}" data-reading="${r.reading}"><h4>${w.text.show(r.label || r.fact)}</h4>${body}${notes}</section>`;
      });
    }
    // WHAT A PERSON MAY START FROM THIS SHEET: each action of the drawing it was opened from that the reader may act by
    // (the page's `actions`; its button its `note`), its inputs drawn by their form — a day in the reader's calendar, a
    // number in their digits, words — started by the host, its plan shown, then ratified or declined: nothing is changed
    // until a person ratifies it
    // an action on the sheet's being (a table's line, the sheet), or on each row of a verb it shows (a statement)
    function onRow(a) { return a.el !== 'line' && a.el !== 'sheet'; }
    function actionsOf() {
      if (!t.act || editing || !(data.actions || []).some(function (a) { return !onRow(a); })) return '';
      return h`<section class="eg-row eg-actions" data-fact="actions">${(data.actions || []).map(function (a, n) {
        return onRow(a) ? '' : h`<div class="eg-action" data-action-n="${n}"><button type="button" class="eg-btn" data-act-open="${n}">${w.text.show(a.note || a.tool)}</button><div class="eg-act-body"></div></div>`;
      })}</section>`;
    }
    // ON A ROW: a button for each action that sits on the row's verb, its statement what the action acts on
    function rowActions(s) {
      if (!t.act || editing || !s.id) return '';
      var acts = (data.actions || []).map(function (a, n) { return [a, n]; }).filter(function (x) { return onRow(x[0]) && x[0].el === s.verb; });
      return acts.length ? h`<div class="eg-actions eg-row-actions">${acts.map(function (x) {
        return h`<span class="eg-action"><button type="button" class="eg-btn" data-act-row="${s.id}" data-act-n="${x[1]}">${w.text.show(x[0].note || x[0].tool)}</button><span class="eg-act-body" data-act-box=""></span></span>`;
      })}</div>` : '';
    }
    // a choice's rows: a reading's members by title; a scheme's by its code's name in the reader's language (`codes`)
    function choicesOf(i) {
      return (i.choices || []).map(function (c) {
        var named = ((t.E.codes || {})[c.value] || {}).name;
        return {value: c.value, label: named || c.label || c.value, disabled: !!c.disabled};
      });
    }
    function actInput(i) {
      var nm = 'act.' + i.name, ty = String(i.type || ''), many = i.many === 'true' || i.many === true;
      if (i.choices && many) {
        return h`<span class="eg-choices">${choicesOf(i).map(function (c) {
          return h`<label class="eg-choice"><input type="checkbox" name="${nm}" value="${c.value}"${c.disabled ? h` disabled` : ''}> ${w.text.show(c.label)}</label>`;
        })}</span>`;
      }
      if (i.choices) return w.choice.edit(nm, '', choicesOf(i));
      if (ty === 'file') return h`<input type="file" class="w-input w-file-input" name="${nm}">`;
      if (/position|day|date|moment/.test(ty)) return w.moment.edit(nm, '');
      if (i.quantity || /count|number|decimal/.test(ty)) return w.number.edit(nm, '');
      return w.text.edit(nm, '', many ? {lines: true} : {});
    }
    // an input a person may leave empty (the law's `optional`): left so, the host gives the tool nothing of that name;
    // any other is marked as the entry form marks a required role, and asked before anything is sent
    function optional(i) { return i.optional === 'true' || i.optional === true; }
    // A LIST BESIDE A LIST (the law's `beside`, ratified 2026-10-14): the lists one stands beside drawn as one table, a
    // row each — where the first chooses among a reading's members or a scheme's rows, every one of them listed, a
    // field of each other list beside it; a row left empty is not given. A person beside their share.
    function besides(a, i) { return (a.inputs || []).filter(function (x) { return x.beside === i.name; }); }
    function pairsOf(a) {
      var out = {};
      (a.inputs || []).forEach(function (i) { if (i.beside) (out[i.beside] = out[i.beside] || []).push(i); });
      return out;
    }
    function rowsInput(a, i) {
      var with_ = besides(a, i), opts = i.choices ? choicesOf(i) : [0, 1, 2, 3, 4].map(function () { return null; });
      var head = h`<tr><th scope="col">${w.text.show(i.note || i.name)}</th>${with_.map(function (b) { return h`<th scope="col">${w.text.show(b.note || b.name)}</th>`; })}</tr>`;
      return h`<table class="eg-rows" data-rows-of="${i.name}"><thead>${head}</thead><tbody>${opts.map(function (c) {
        var first = c ? h`<th scope="row" data-row-value="${c.value}">${w.text.show(c.label)}</th>` : h`<td>${w.text.edit('rowv.' + i.name, '')}</td>`;
        return h`<tr>${first}${with_.map(function (b) { return h`<td>${actInput(b)}</td>`; })}</tr>`;
      })}</tbody></table>`;
    }
    function actForm(a) {
      var said = (a.inputs || []).filter(function (i) { var o = i.origin || {}; return !(o.act === 'read' && o.by === 'reader') && !i.from && !i.beside; });
      var paired = pairsOf(a);
      return h`${a.confirm ? h`<p class="eg-known">${w.text.show(a.confirm)}</p>` : ''}${said.map(function (i) {
        var req = !optional(i);
        return h`<label class="eg-field${req ? ' eg-req' : ''}" data-role="${i.name}"><span class="eg-role-name">${w.text.show(i.note || i.name)}${req ? h` <span class="eg-req-word">(${t.say('sheet-required')})</span>` : ''}</span> ${paired[i.name] ? rowsInput(a, i) : actInput(i)}<span class="eg-err" data-err="${'act.' + i.name}"></span></label>`;
      })}${a.reason ? h`<label class="eg-field" data-role="reason"><span class="eg-role-name">${t.say('act-reason')}</span> ${w.text.edit('act.reason', '', {lines: true})}</label>` : ''}<div class="eg-bar"><button type="button" class="eg-btn eg-primary" data-act-start="">${t.say('act-start')}</button> <span class="eg-err" data-err-act=""></span></div>`;
    }
    function wireActions() {
      el.querySelectorAll('[data-act-open]').forEach(function (b) {
        b.addEventListener('click', function () {
          var a = data.actions[Number(b.getAttribute('data-act-open'))], box = b.nextElementSibling;
          t.mount(box, actForm(a));
          box.querySelector('[data-act-start]').addEventListener('click', function () { startAct(a, box); });
        });
      });
      el.querySelectorAll('[data-act-row]').forEach(function (b) {
        b.addEventListener('click', function () {
          var a = data.actions[Number(b.getAttribute('data-act-n'))], box = b.nextElementSibling, row = b.getAttribute('data-act-row');
          t.mount(box, actForm(a));
          sharesForm(box, statementOf(row));
          box.querySelector('[data-act-start]').addEventListener('click', function () { startAct(a, box, row); });
        });
      });
    }
    function statementOf(id) {
      var hit = null;
      data.rows.forEach(function (r) { r.statements.forEach(function (s) { if (s.id === id) hit = s; }); });
      return hit;
    }
    // EXACT, NEVER THROUGH A FLOAT: a count as written (`3`, `1250.50`, `9650/3`) as [numerator, denominator] in BigInt
    function frac(x) {
      var latin = String(x == null ? '' : x).trim().replace(/[\u06F0-\u06F9]/g, function (c) { return String(c.charCodeAt(0) - 0x06F0); })
        .replace(/[\u0660-\u0669]/g, function (c) { return String(c.charCodeAt(0) - 0x0660); }).replace(/[\u066B\u060C]/g, '.');
      var m = latin.match(/^(\d+)(?:\.(\d+))?(?:\/(\d+))?$/);
      if (!m) return null;
      var d = m[2] ? 10n ** BigInt(m[2].length) : 1n;
      return [BigInt(m[1] + (m[2] || '')), d * (m[3] ? BigInt(m[3]) : 1n)];
    }
    function gcd(a, b) { while (b) { var r = a % b; a = b; b = r; } return a < 0n ? -a : a; }
    function text(n, d) { var g = gcd(n, d) || 1n; n /= g; d /= g; return d === 1n ? String(n) : n + '/' + d; }
    // A PAYMENT'S SHARES, IN ITS FORM (the share walk's, on the payment's own line — its `share` beside each one who bears
    // it): each one's share as it stands now,
    // and, as the form is filled, each one's part of the whole as the fraction it is and the amount it comes to — what
    // the walk will write, before it is started; shares that add up to the payment are each one's amount
    function sharesForm(box, s) {
      // the share walk's form: a person beside their `share`, the input the walk takes by that name (books_walks.py)
      var sh = s && s.shares, tbl = box.querySelector('table.eg-rows'), of = s && s.roles && s.roles.of;
      if (!sh || !tbl || !tbl.querySelector('[name="act.share"]')) return;
      var W = of && typeof of === 'object' ? frac(of.count) : null, unit = of && of.unit;
      var den = sh.bearers.reduce(function (acc, b) { var f = frac(b.share); return f ? acc * f[1] / gcd(acc, f[1]) : acc; }, 1n);
      var rows = [].slice.call(tbl.querySelectorAll('tbody tr'));
      rows.forEach(function (tr) {
        var th = tr.querySelector('[data-row-value]'), input = tr.querySelector('input, textarea');
        var b = th && sh.bearers.filter(function (x) { return x.bean === th.getAttribute('data-row-value'); })[0];
        if (b && input && !input.value) {            // in the reader's digits, as they would type it
          var f = frac(b.share);
          if (f) input.value = w.locale.inDigits(text(f[0] * den / f[1], 1n), w.locale.digitsOf({}));
        }
        tr.appendChild(document.createElement('td')).className = 'eg-part';
      });
      var head = tbl.querySelector('thead tr');
      if (head) { var c = document.createElement('th'); c.setAttribute('scope', 'col'); c.textContent = t.say('shares-part'); head.appendChild(c); }
      function live() {
        var vals = rows.map(function (tr) { var i = tr.querySelector('input, textarea'); return frac(i && i.value); });
        var sum = vals.reduce(function (acc, f) { return f ? [acc[0] * f[1] + f[0] * acc[1], acc[1] * f[1]] : acc; }, [0n, 1n]);
        rows.forEach(function (tr, k) {
          var f = vals[k], cell = tr.querySelector('td.eg-part');
          if (!f || !f[0] || !sum[0]) { t.mount(cell, ''); return; }
          var n = f[0] * sum[1], d = f[1] * sum[0];         // its part of the whole: its share over the shares' sum
          t.mount(cell, t.h`${w.number.show(text(n, d))}${W && unit ? t.h` (${root.daftarEngraved.show(t, {count: text(W[0] * n, W[1] * d), unit: unit}, {})})` : ''}`);
        });
      }
      tbl.addEventListener('input', live);
      live();
    }
    // a file chosen, as the host takes it: its name and its bytes (base64)
    function fileOf(f) {
      return new Promise(function (ok, no) {
        var rd = new FileReader();
        rd.onload = function () { var u = String(rd.result || ''); ok({name: f.name, data: u.slice(u.indexOf(',') + 1)}); };
        rd.onerror = function () { no(rd.error); };
        rd.readAsDataURL(f);
      });
    }
    function startAct(a, box, row) {
      var inputs = {}, bad = false, files = [], say = function (x) { var e = box.querySelector('[data-err-act]'); if (e) e.textContent = x; };
      var err = function (name, x) { var e = box.querySelector('[data-err="act.' + name + '"]'); if (e) e.textContent = x; bad = true; };
      box.querySelectorAll('[data-err^="act."]').forEach(function (e) { e.textContent = ''; });
      // the lists given row by row: each row whose fields beside are given, its first value and theirs, aligned
      var paired = pairsOf(a);
      Object.keys(paired).forEach(function (name) {
        var first = (a.inputs || []).filter(function (x) { return x.name === name; })[0] || {}, cols = paired[name];
        var lists = [[]].concat(cols.map(function () { return []; })), table = box.querySelector('[data-rows-of="' + name + '"]');
        [].slice.call(table ? table.tBodies[0].rows : []).forEach(function (tr) {
          var cells = cols.map(function (b, k) { return tr.cells[k + 1].querySelector('[name="act.' + b.name + '"]'); });
          var vals = cells.map(function (f) { return String(f && f.value || '').trim(); });
          if (!vals.some(Boolean)) return;
          var key = tr.cells[0].getAttribute('data-row-value') || String((tr.cells[0].querySelector('input') || {}).value || '').trim();
          if (!key) { err(name, t.say('required')); return; }
          var got = [key];
          for (var k = 0; k < cols.length; k++) {
            var f = cells[k], v = vals[k], x = v;
            if (!v) { err(cols[k].name, t.say('required')); return; }
            if (f.classList.contains('w-num-input')) { var nn = w.number.take(v); if (nn.error) { err(cols[k].name, nn.error); return; } x = nn.value; }
            got.push(x);
          }
          got.forEach(function (x, k) { lists[k].push(x); });
        });
        if (!lists[0].length) { if (!optional(first)) err(name, t.say('required')); return; }
        inputs[name] = lists[0];
        cols.forEach(function (b, k) { inputs[b.name] = lists[k + 1]; });
      });
      (a.inputs || []).forEach(function (i) {
        var o = i.origin || {}, name = i.name, many = i.many === 'true' || i.many === true;
        if (i.from || (o.act === 'read' && o.by === 'reader')) return;      // the host's to fill, or the clock's
        if (paired[name] || i.beside) return;                             // given row by row, above
        var fs = [].slice.call(box.querySelectorAll('[name="act.' + name + '"]'));
        if (!fs.length) return;
        // left empty: nothing sent of it — the tool's own meaning where it is optional, else asked for here
        var none = function () { if (!optional(i)) err(name, t.say('required')); };
        if (String(i.type || '') === 'file') {
          if (fs[0].files && fs[0].files[0]) files.push(fileOf(fs[0].files[0]).then(function (x) { inputs[name] = x; }));
          else none();
          return;
        }
        if (i.choices && many) {
          var got = fs.filter(function (f) { return f.checked; }).map(function (f) { return f.value; });
          if (got.length) inputs[name] = got;
          else none();
          return;
        }
        var v = String(fs[0].value || '').trim();
        if (!v) return none();
        if (i.choices) {
          var c = w.choice.take(v, choicesOf(i));
          if (c.error) return err(name, c.error);
          inputs[name] = c.value;
        } else if (fs[0].classList.contains('w-moment-input')) {
          var m = w.moment.take(v);
          if (m.error) return err(name, m.error);
          inputs[name] = m.value;
        } else if (fs[0].classList.contains('w-num-input')) {
          var n = w.number.take(v);
          if (n.error) return err(name, n.error);
          inputs[name] = n.value;
        } else {
          inputs[name] = many ? v.split('\n').map(function (x) { return x.trim(); }).filter(Boolean) : v;
        }
      });
      if (bad) return;
      var why = box.querySelector('[name="act.reason"]');
      Promise.all(files).then(function () {
        return t.act(Object.assign({m: a.drawing, el: a.el, tool: a.tool, bean: row ? a.bean + '#' + row : a.bean, inputs: inputs},
                                   why && why.value.trim() ? {reason: why.value.trim()} : {}));
      }, function () { say(t.say('act-file-unread')); return null; })
        .then(function (r) {
          if (!r) return;
          var ans = r.answer || {};
          if (r.status !== 200) { say(t.say('act-refused') + ' ' + (ans.error || '')); return; }
          t.mount(box, h`<p class="eg-known">${t.say('act-plan')}</p><pre class="eg-plan" dir="auto">${ans.plan || ''}</pre><p class="eg-known">${t.say('act-waits', {at: ans.stands || ''})}</p><div class="eg-bar"><button type="button" class="eg-btn eg-primary" data-act-do="ratify">${t.say('act-ratify')}</button> <button type="button" class="eg-btn" data-act-do="decline">${t.say('act-decline')}</button> <span class="eg-err" data-err-act=""></span></div>`);
          box.querySelectorAll('[data-act-do]').forEach(function (d) {
            d.addEventListener('click', function () {
              t.act({do: d.getAttribute('data-act-do'), bean: ans.bean, course: ans.course}).then(function (r2) {
                var a2 = r2.answer || {};
                if (r2.status !== 200) { say(t.say('act-refused') + ' ' + (a2.error || '')); return; }
                t.mount(box, h`<p class="eg-said">${w.text.show(a2.said || a2.mode || '')}</p>`);
                if (root.location && root.location.reload) setTimeout(function () { root.location.reload(); }, 600);
              });
            });
          });
        });
    }
    // WHAT IS HELD OF IT OFF GIT, IN EDIT: each record this host keeps of the being that the reader may write — a
    // person's contact, a record of `details` — its fields by the page's words for them (`<key>.<field>`), else the
    // release's for a contact's, else the field's own name; one a map one level down. One the being has none of yet is
    // offered empty. Saved as `held` ops by the one write path, into the store, never into the ledger
    function fieldWord(key, f) {
      if (labels[key + '.' + f]) return labels[key + '.' + f];
      var said_ = key === 'contact' ? t.say('held-' + f) : '';
      return said_ && said_ !== 'held-' + f ? said_ : f;
    }
    function heldInput(name, v, f) {
      return /phone|mail|tel/.test(f) ? w.name.edit(name, v == null ? '' : String(v)) : w.text.edit(name, v == null ? '' : String(v));
    }
    function heldEdit() {
      return t.join((data.records || []).map(function (r) {
        var head = labels[r.key] || (r.key === 'contact' ? t.say('sheet-contact') : r.key), e = r.entry || {}, maps = r.maps || {};
        return h`<section class="eg-row eg-held-record" data-fact="held:${r.key}" data-held-key="${r.key}"><h4>${w.text.show(head)}</h4>${
          r.new ? h`<p class="eg-held">${t.say('sheet-held-new')}</p>` : ''}${(r.fields || []).map(function (f) {
          var v = e[f];
          // a map: each field of it the record holds, and each the page names, held yet or not
          if ((v && typeof v === 'object' && !Array.isArray(v)) || maps[f]) {
            var m = (v && typeof v === 'object' && !Array.isArray(v)) ? v : {};
            var keys = Object.keys(m).concat((maps[f] || []).filter(function (g) { return !(g in m); }));
            return h`<fieldset class="eg-held-map"><legend>${w.text.show(fieldWord(r.key, f))}</legend>${keys.map(function (g) {
              return h`<label class="eg-field" data-role="${f}.${g}"><span class="eg-role-name">${w.text.show(labels[r.key + '.' + f + '.' + g] || g)}</span> ${heldInput('held.' + r.key + '.' + f + '.' + g, m[g], g)}</label>`;
            })}</fieldset>`;
          }
          return h`<label class="eg-field" data-role="${f}"><span class="eg-role-name">${w.text.show(fieldWord(r.key, f))}</span> ${heldInput('held.' + r.key + '.' + f, v, f)}</label>`;
        })}<p class="eg-held">${t.say('sheet-held')}</p><span class="eg-err" data-err-fact="held:${r.key}"></span></section>`;
      }), '');
    }
    // THE TAGS, a set of words the page names among a being's facts: each a word of its own, in its own isolate
    function tagsOf(tags) {
      return tags && (tags.value || []).length ? h`<p class="eg-tags" data-fact="header:tags">${t.join(tags.value.map(function (x) { return h`<span class="eg-tag">${w.text.show(x)}</span>`; }), ' ')}</p>` : '';
    }
    function draw() {
      n = 0;
      var hd = data.header || {}, title = hd.title || {}, summary = hd.summary, tags = hd.tags;
      var named = data.new ? t.say('sheet-new-kind', {kind: t.name('kinds', data.kind)}) : data.title;
      var head = editing
        ? h`<div class="eg-sheet-head">${title.may ? h`<label class="eg-field" data-fact="header:title"><span class="eg-role-name">${labels.title || word('header', 'title')}</span> ${w.text.edit('header.title', title.value === data.bean ? '' : (title.value || ''), {placeholder: data.title})}<span class="eg-err" data-err-fact="header:title"></span></label>` : h`<h3>${w.text.show(named)}</h3>`}
            ${tags ? (tags.may ? h`<label class="eg-field" data-fact="header:tags"><span class="eg-role-name">${labels.tags || word('header', 'tags')}</span> ${w.text.edit('header.tags', (tags.value || []).join(t.say('sheet-tags-sep')))}<span class="eg-err" data-err-fact="header:tags"></span></label>` : tagsOf(tags)) : ''}
            ${summary ? (summary.may ? h`<label class="eg-field" data-fact="header:summary"><span class="eg-role-name">${labels.summary || word('header', 'summary')}</span> ${w.text.edit('header.summary', summary.value || '', {lines: true})}<span class="eg-err" data-err-fact="header:summary"></span></label>` : h`<p class="eg-summary">${w.text.show(summary.value)}</p>`) : ''}</div>${details()}${heldEdit()}`
        : h`<div class="eg-sheet-head"><h3 data-fact="header:title">${w.text.show(named)}</h3>${summary && summary.value ? h`<p class="eg-summary" data-fact="header:summary">${w.text.show(summary.value)}</p>` : ''}${tagsOf(tags)}</div>${contact()}${details()}${readings()}`;
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
      }) : (data.readings || []).length && !editing ? '' : h`<p class="eg-empty">${t.say('sheet-none', {kind: t.name('kinds', data.kind)})}</p>`;
      var bar = !t.write ? h`<p class="eg-copy">${t.say('sheet-copy')}</p>`
        : !mayAny ? ''
          : editing ? h`<div class="eg-bar"><button type="button" class="eg-btn eg-primary" data-do="save">${t.say('sheet-save')}</button> <button type="button" class="eg-btn" data-do="cancel">${t.say('sheet-cancel')}</button> <span class="eg-said" data-said=""></span></div>`
            : h`<div class="eg-bar"><button type="button" class="eg-btn eg-primary" data-do="edit">${t.say('sheet-edit')}</button></div>`;
      t.mount(el, h`${head}${rows}${actionsOf()}${bar}<p class="eg-err eg-general" data-err-general=""></p>`);
      wire();
      wireActions();
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
      (data.records || []).forEach(function (r) {   // a held record: the fields changed, one given empty taken out
        var box = el.querySelector('[data-held-key="' + r.key + '"]');
        if (!box) return;
        var was = r.entry || {}, changed = {};
        box.querySelectorAll('[name^="held.' + r.key + '."]').forEach(function (f) {
          var path = f.getAttribute('name').slice(('held.' + r.key + '.').length).split('.'), v = f.value.trim();
          if (path.length === 1) {
            if (v !== (was[path[0]] == null ? '' : String(was[path[0]]))) changed[path[0]] = v;
          } else {
            var inner = (was[path[0]] && typeof was[path[0]] === 'object') ? was[path[0]] : {};
            if (v !== (inner[path[1]] == null ? '' : String(inner[path[1]]))) {
              changed[path[0]] = Object.assign({}, inner, changed[path[0]] || {});
              changed[path[0]][path[1]] = v;
            }
          }
        });
        if (r.new) Object.keys(changed).forEach(function (k) { if (changed[k] === '') delete changed[k]; });
        if (Object.keys(changed).length) { ops.push({op: 'held', key: r.key, entry: changed}); where.push(box); }
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
