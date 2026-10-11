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
      var keys = Object.keys(specs).filter(function (k) { return roles && k in roles; }).concat(BESIDE.filter(function (k) { return roles && k in roles; }));
      return t.join(keys.map(function (k) {
        return h`<span class="eg-role" data-role="${k}"><span class="eg-role-name">${label(verb, k)}</span> ${shown(roles[k], specs[k] || {shape: ['text']})}</span>`;
      }), ' ');
    }
    function readOne(s) {
      var held = s.held ? h`<span class="eg-held">${s.held.here ? t.say('sheet-held') : s.held.host ? t.say('sheet-kept-on', {host: t.titleOf(s.held.host) || s.held.host}) : t.say('sheet-kept-off')}</span>` : '';
      return h`<li class="eg-statement${s.held ? ' eg-sealed' : ''}" data-fact="${s.key}">
        <div class="eg-roles">${s.roles ? rolesOf(s.verb, s.roles) : ''} ${held}</div>${known(s)}
        ${(s.defaults || []).map(function (d) {
          return h`<div class="eg-default">${t.name('verbs', d.verb)}: ${w.being.show(d.by, d.title || d.by, {action: 'open'})} — ${t.say('sheet-default', {says: d.says})}</div>`; })}
        ${(s.dependents || []).length ? h`<ol class="eg-dependents">${s.dependents.map(function (d) {
          return h`<li class="eg-dependent" data-fact="${d.key}"><span class="eg-verb">${t.name('verbs', d.verb)}</span> ${d.roles ? rolesOf(d.verb, d.roles) : ''}${known(d)}</li>`;
        })}</ol>` : ''}</li>`;
    }

    /* ---------------- editing: a widget per role, by its shape ---------------- */
    function nameOf(prefix, role) { return prefix + '.' + role; }
    function editor(verb, roles, prefix, may) {
      var row = data.verbs[verb] || {roles: {}, qualifiers: {}, required: []}, specs = Object.assign({}, row.roles, row.qualifiers);
      var keys = Object.keys(specs).concat(BESIDE);
      return t.join(keys.map(function (k) {
        var spec = specs[k] || {shape: ['text']}, v = roles ? roles[k] : undefined, shapes = spec.shape || ['text'];
        var req = (row.required || []).indexOf(k) >= 0, nm = nameOf(prefix, k), input;
        if (!may) return v === undefined ? '' : h`<span class="eg-role"><span class="eg-role-name">${label(verb, k)}</span> ${shown(v, spec)}</span>`;
        var def = shapes.indexOf('form') >= 0 && spec.form && (data.forms || {})[spec.form];
        if (def) {                                  // a form's value, drawn by its entries (widgets/form.js)
          input = spec.many === 'true'
            ? t.join((Array.isArray(v) ? v : []).concat([{}]).map(function (e, i) { return h`<span class="eg-form-entry">${w.form.edit(nm + '.' + i, e, def, fo)}</span>`; }), '')
            : w.form.edit(nm, v, def, fo);
        } else if (spec.many === 'true' || Array.isArray(v)) {
          input = w.name.edit(nm, Array.isArray(v) ? v.join(', ') : (v || ''));
        } else if (shapes.indexOf('quantity') >= 0 && (v === undefined || (v && typeof v === 'object'))) {
          input = h`${w.number.edit(nm + '.count', v ? v.count : '')} ${w.name.edit(nm + '.unit', v ? v.unit : '')}`;
        } else if (shapes.indexOf('being') >= 0 && (v === undefined || typeof v === 'string')) {
          var rows = (t.E.beings || []).filter(function (b) { return !spec.kind || [].concat(spec.kind).indexOf(b.kind) >= 0; })
            .map(function (b) { return {value: b.id, label: b.title || b.id}; });
          ['self', 'theone', 'unknown'].concat(v ? [v] : []).forEach(function (x) { if (!rows.some(function (r) { return r.value === x; })) rows.push({value: x, label: x}); });
          input = w.choice.edit(nm, v || '', rows, {none: '—'});
        } else if (shapes.indexOf('statement') >= 0 && (v === undefined || typeof v === 'string') && shapes.length === 1) {
          input = w.choice.edit(nm, v || '', (data.statements || []).concat(v && data.statements.indexOf(v) < 0 ? [v] : []), {none: '—'});
        } else if (shapes.indexOf('row') >= 0 && spec.rows && (v === undefined || spec.rows.indexOf(v) >= 0)) {
          input = w.choice.edit(nm, v || '', spec.rows, {none: '—'});
        } else if (shapes.indexOf('position') >= 0 && (v === undefined || (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v)))) {
          input = w.moment.edit(nm, v || '');
        } else if (shapes.indexOf('form') >= 0 && v && typeof v === 'object') {
          input = w.name.edit(nm + '.json', JSON.stringify(v));
        } else if (shapes.indexOf('text') >= 0 || BESIDE.indexOf(k) >= 0) {
          input = w.text.edit(nm, v || '');
        } else {
          input = w.name.edit(nm, typeof v === 'string' ? v : v === undefined ? '' : JSON.stringify(v));
        }
        return h`<label class="eg-field${req ? ' eg-req' : ''}" data-role="${k}"><span class="eg-role-name">${label(verb, k)}${req ? h` <span class="eg-req-word">(${t.say('sheet-required')})</span>` : ''}</span> ${input}<span class="eg-err" data-err="${nm}"></span></label>`;
      }), '');
    }
    function editOne(s, parentId) {
      var p = 's' + (n++), may = s.may && !!s.roles;
      return h`<li class="eg-statement eg-editing" data-fact="${s.key}" data-prefix="${p}" data-verb="${s.verb}"${s.held ? h` data-held=""` : ''}>
        <div class="eg-fields">${editor(s.verb, s.roles, p, may)}</div>
        ${s.held && !s.roles ? h`<span class="eg-held">${s.held.host ? t.say('sheet-kept-on', {host: t.titleOf(s.held.host) || s.held.host}) : t.say('sheet-kept-off')}</span>` : ''}
        ${s.may && (!s.held || s.held.here) ? h`<label class="eg-remove"><input type="checkbox" data-remove="${s.key}"> ${t.say('sheet-remove')}</label>` : ''}
        ${(s.dependents || []).length ? h`<ol class="eg-dependents">${s.dependents.map(function (d) { return editOne(d, s.id); })}</ol>` : ''}
        ${s.may && s.id ? t.join(Object.keys(depVerbs(s)).map(function (v) {
          return h`<button type="button" class="eg-btn eg-add" data-add="${v}" data-of="${s.id}">+ ${t.say('sheet-add')} ${t.name('verbs', v)}</button>`; }), ' ') : ''}
        <span class="eg-err" data-err-fact="${s.key}"></span></li>`;
    }
    function depVerbs(s) {
      var out = {};
      (s.dependents || []).forEach(function (d) { out[d.verb] = true; });
      return out;
    }
    function blankOne(verb, of) {
      var p = 'a' + (n++);
      return h`<li class="eg-statement eg-editing eg-added" data-prefix="${p}" data-verb="${verb}" data-add-op="">
        <div class="eg-fields">${editor(verb, of ? {of: of} : {}, p, true)}</div><span class="eg-err" data-err-op=""></span></li>`;
    }

    function draw() {
      n = 0;
      var hd = data.header || {}, title = hd.title || {}, summary = hd.summary;
      var named = data.new ? (t.say('sheet-new') + ' ' + t.name('kinds', data.kind)) : data.title;
      var head = editing
        ? h`<div class="eg-sheet-head">${title.may ? h`<label class="eg-field" data-fact="header:title"><span class="eg-role-name">${t.name('header', 'title')}</span> ${w.text.edit('header.title', title.value || '')}<span class="eg-err" data-err-fact="header:title"></span></label>` : h`<h3>${w.text.show(named)}</h3>`}
            ${summary ? (summary.may ? h`<label class="eg-field" data-fact="header:summary"><span class="eg-role-name">${t.name('header', 'summary')}</span> ${w.text.edit('header.summary', summary.value || '', {lines: true})}<span class="eg-err" data-err-fact="header:summary"></span></label>` : h`<p class="eg-summary">${w.text.show(summary.value)}</p>`) : ''}</div>`
        : h`<div class="eg-sheet-head"><h3 data-fact="header:title">${w.text.show(named)}</h3>${summary && summary.value ? h`<p class="eg-summary" data-fact="header:summary">${w.text.show(summary.value)}</p>` : ''}</div>`;
      var rows = data.rows.length ? data.rows.map(function (r) {
        var meaning = (data.verbs[r.verb] || {}).meaning || '';
        return h`<section class="eg-row" data-verb="${r.verb}"><h4 title="${meaning}">${t.name('verbs', r.verb)}</h4><ol class="eg-statements">${
          editing ? r.statements.map(function (s) { return editOne(s); }) : r.statements.map(function (s) { return readOne(s); })}</ol>${
          editing && r.may_add ? h`<button type="button" class="eg-btn eg-add" data-add="${r.verb}">+ ${t.say('sheet-add')} ${t.name('verbs', r.verb)}</button>` : ''}</section>`;
      }) : h`<p class="eg-empty">${t.say('sheet-none', {kind: t.name('kinds', data.kind)})}</p>`;
      var bar = !t.write ? h`<p class="eg-copy">${t.say('sheet-copy')}</p>`
        : !mayAny ? ''
          : editing ? h`<div class="eg-bar"><button type="button" class="eg-btn eg-primary" data-do="save">${t.say('sheet-save')}</button> <button type="button" class="eg-btn" data-do="cancel">${t.say('sheet-cancel')}</button> <span class="eg-said" data-said=""></span></div>`
            : h`<div class="eg-bar"><button type="button" class="eg-btn eg-primary" data-do="edit">${t.say('sheet-edit')}</button></div>`;
      t.mount(el, h`${head}${rows}${bar}<p class="eg-err eg-general" data-err-general=""></p>`);
      wire();
    }

    function wire() {
      t.wire(el);
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
        });
      });
    }

    /* what a field holds, as the law writes it — or an error said at the field */
    function readFields(li, verb, errs) {
      var p = li.getAttribute('data-prefix'), row = data.verbs[verb] || {roles: {}, qualifiers: {}}, specs = Object.assign({}, row.roles, row.qualifiers);
      var roles = {};
      Object.keys(specs).concat(BESIDE).forEach(function (k) {
        var nm = p + '.' + k, spec = specs[k] || {shape: ['text']}, q = function (x) { return li.querySelector('[name="' + x + '"]'); };
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
      return roles;
    }

    function save() {
      var ops = [], where = [], errs = [];
      el.querySelectorAll('[data-err],[data-err-fact],[data-err-op],[data-err-general]').forEach(function (e) { e.textContent = ''; });
      var hd = data.header || {};
      ['title', 'summary'].forEach(function (k) {
        var f = el.querySelector('[name="header.' + k + '"]');
        if (f && ((hd[k] || {}).value || '') !== f.value.trim()) {
          ops.push({op: 'change', header: k, value: f.value.trim()}); where.push(f.closest('[data-fact]'));
        }
      });
      var originals = {};
      data.rows.forEach(function (r) { r.statements.forEach(function (s) { originals[s.key] = s; (s.dependents || []).forEach(function (d) { originals[d.key] = d; }); }); });
      el.querySelectorAll('[data-remove]').forEach(function (c) {
        if (c.checked) { ops.push({op: 'remove', key: c.getAttribute('data-remove')}); where.push(c.closest('[data-fact]')); }
      });
      el.querySelectorAll('li.eg-editing').forEach(function (li) {
        var verb = li.getAttribute('data-verb'), key = li.getAttribute('data-fact');
        if (li.hasAttribute('data-add-op')) {
          var roles = readFields(li, verb, errs);
          if (Object.keys(roles).length) { ops.push({op: 'add', verb: verb, roles: roles}); where.push(li); }
          return;
        }
        var s = originals[key];
        if (!s || !s.may || !s.roles || (el.querySelector('[data-remove="' + key + '"]') || {}).checked) return;
        var now = readFields(li, verb, errs);
        if (canon(now) !== canon(s.roles)) {
          ops.push(Object.assign({op: 'change', key: key, roles: now}, s.held ? {held: true} : {})); where.push(li);
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
