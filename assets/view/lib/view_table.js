/* view_table.js — the `table` archetype engraved from its reading, where the page names no drawing module: the members
   of the drawing's reading, one line each, a column per path (the server's reading, `view_engraved.py` `table`, each
   line one the reader may read). Every cell is shown by the widget of what it holds — a day in the reader's calendar, an
   amount at its currency's places, a being by its title — never as the text a path happened to give, and each line
   opens its being's sheet. Its lines run down the page and its columns along the reader's line (`axes: { inline:
   taxis, block: ordinal }`), so a right-to-left reader reads the first column at the right. A column's `stands` draws
   each line's course on its walk by the archetype `course` (view_course.js), the one way a course is drawn.
   OR A CHART'S CODES (the drawing's `chart`, `view_engraved.py` `chart_table`): per currency, a line for each account of
   the entity's books in the chart's order, each column a figure of it — its opening, debit, credit, balance — the totals
   beneath, and the ledger of each account that posts, opened from its line, each ledger line with its running balance
   and opening the sheet of what it rests on. Debit before credit as the page lists its columns, along the reader's line:
   a right-to-left reader reads the debit at the right, as their books are written. Every account by its name in the
   reader's language (the page's `codes`), its code beside it in its title. A classic script beside view_engraved.js,
   built only through safe.js. */
(function (root) {
  'use strict';
  var A = root.daftarArchetypes = root.daftarArchetypes || {};
  var ANY = {shape: ['being', 'position', 'text']};

  A.table = function (el, data, t) {
    if (data.chart) { chart(el, data, t); return; }
    var h = t.h, w = t.w, cols = data.columns || [], rows = data.rows || [];
    if (!rows.length) {
      t.mount(el, h`<p class="eg-empty">${t.say('table-empty')}</p>${(data.notes || []).map(function (n) { return h`<p class="eg-partial">${w.text.show(n)}</p>`; })}`);
      return;
    }
    function cell(vals) {
      if (vals && !Array.isArray(vals) && typeof vals === 'object' && 'course' in vals) {   // a column's `stands`: its course
        return root.daftarCourse ? root.daftarCourse.line(t, vals.course, {bare: true}) : h`<span class="w-none">—</span>`;
      }
      var list = Array.isArray(vals) ? vals : [vals];
      return list.length ? t.join(list.map(function (v) { return root.daftarEngraved.show(t, v, ANY); }), ', ') : h`<span class="w-none">—</span>`;
    }
    // a line opens its being's sheet from its first cell: the title where the first column is the title, else a cell
    // of its own before the columns, holding the title
    var titled = cols.length && cols[0].path === 'title';
    // EACH COLUMN SORTS ITS LINES (the operator, 2026-10-14): its head a button, once rising, again falling, by what the
    // cells hold — an amount by its exact value, a day as the law writes it, a being by its title, words in the reader's
    // language's order — never by the text drawn; an empty cell last either way. The lines are moved, nothing drawn again.
    t.mount(el, h`<div class="eg-table-wrap"><table class="eg-table"><thead><tr>${titled ? '' : h`<th scope="col"></th>`}${cols.map(function (c, i) {
      return h`<th scope="col" data-path="${c.path}" aria-sort="none"><button type="button" class="eg-sort" data-sort="${String(i)}">${w.text.show(c.label)}</button></th>`; })}</tr></thead><tbody>${rows.map(function (r, n) {
      var open = h`<th scope="row">${w.being.show(r.bean, r.title || r.bean, {action: 'open'})}</th>`;
      return h`<tr data-bean="${r.bean}" data-line="${String(n)}">${titled ? '' : open}${cols.map(function (c, i) {
        return titled && i === 0 ? open : h`<td>${cell(r.cells[i])}</td>`;
      })}</tr>`;
    })}</tbody></table></div>${(data.notes || []).map(function (n) { return h`<p class="eg-partial">${w.text.show(n)}</p>`; })}`);
    t.wire(el);
    sortable(el.querySelector('table.eg-table'), rows, titled, t);
  };

  // a cell's key to sort by: [kind, value] — an amount (exact, n/d), a day or moment (as the law writes it), or words
  var DAY = /^\d{4}-\d{2}-\d{2}/;
  function keyOf(v, r, titled, i, w) {
    if (titled && i === 0) return ['words', r.title || r.bean || ''];
    var x = Array.isArray(v) ? v[0] : v;
    if (x && typeof x === 'object' && 'course' in x) return x.course ? ['words', String(x.course.step || '')] : null;
    if (x === undefined || x === null || x === '') return null;
    if (typeof x === 'object' && x.count !== undefined) { var e = w.exact.of(x.count); return e ? ['amount', e] : null; }
    if (typeof x === 'object') return ['words', String(x.title || x.name || x.value || x.bean || '')];
    var s = String(x), e2 = /^-?\d+(\.\d+)?$|^-?\d+\/\d+$/.test(s) ? w.exact.of(s) : null;
    if (e2) return ['amount', e2];
    if (DAY.test(s)) return ['day', s];
    return ['words', s];
  }
  function sortable(table, rows, titled, t) {
    if (!table) return;
    var w = t.w, words = new Intl.Collator(t.lang || undefined, {numeric: true, sensitivity: 'base'});
    var by = {col: null, up: true};
    function cmp(a, b) {
      if (!a || !b) return a ? -1 : b ? 1 : 0;                       // an empty cell last
      if (a[0] !== b[0]) return a[0] < b[0] ? -1 : 1;                 // amounts, days and words each among their own
      if (a[0] === 'amount') { var l = a[1][0] * b[1][1], r = b[1][0] * a[1][1]; return l < r ? -1 : l > r ? 1 : 0; }
      if (a[0] === 'day') return a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0;
      return words.compare(a[1], b[1]);
    }
    table.addEventListener('click', function (ev) {
      var btn = ev.target.closest('button.eg-sort');
      if (!btn || !table.contains(btn)) return;
      var col = Number(btn.dataset.sort);
      by = {col: col, up: by.col === col ? !by.up : true};
      var body = table.tBodies[0], lines = Array.prototype.slice.call(body.rows);
      var keyed = lines.map(function (tr) {
        var n = Number(tr.dataset.line), r = rows[n] || {cells: []};
        return {tr: tr, n: n, k: keyOf(r.cells[col], r, titled, col, w)};
      });
      keyed.sort(function (a, b) {
        if (!a.k || !b.k) return cmp(a.k, b.k) || a.n - b.n;            // empty last, rising or falling
        return (by.up ? cmp(a.k, b.k) : cmp(b.k, a.k)) || a.n - b.n;
      });
      keyed.forEach(function (x) { body.appendChild(x.tr); });
      Array.prototype.forEach.call(table.tHead.rows[0].cells, function (th) {
        var b = th.querySelector('button.eg-sort');
        th.setAttribute('aria-sort', b && Number(b.dataset.sort) === col ? (by.up ? 'ascending' : 'descending') : 'none');
      });
    });
  }

  // A TABLE OF A CHART'S CODES: the books of one being, an account a line, its figures read by the accounting asset
  function chart(el, data, t) {
    var h = t.h, w = t.w, cols = data.columns || [], cur = data.currencies || [];
    var notes = (data.notes || []).map(function (n) { return h`<p class="eg-partial">${w.text.show(n)}</p>`; });
    if (!cur.length) {
      t.mount(el, h`<p class="eg-empty">${t.say('chart-empty')}</p>${notes}`);
      return;
    }
    function money(x, unit) {
      return x && x !== '0' ? root.daftarEngraved.show(t, {count: x, unit: unit}, {}) : h`<span class="w-none">—</span>`;
    }
    function account(code, name) {
      var c = (t.E.codes || {})[code];
      return h`<span class="eg-code" title="${code}${c && c.by ? ' · ' + c.by : ''}">${w.text.show(c ? c.name : name)}</span>`;
    }
    function figure(col, x, line, unit) {
      if (col.path === 'name') return account(line.code, line.name);
      if (col.path === 'code') return h`<bdi dir="ltr" class="eg-code">${w.text.show(line.code.split(':').slice(1).join(':'))}</bdi>`;
      if (col.path === 'element') return w.text.show(x || '');
      return money(x, unit);
    }
    // the first column names the account where it is its name or code; else the line opens with a cell of its own
    var named = cols.length && (cols[0].path === 'name' || cols[0].path === 'code');
    // the period in the reader's words, each of its days drawn as a day, in the reader's calendar and digits: a day
    // written into the sentence as text is read right to left in a right-to-left page (2026-10-14 as 14-10-2026)
    var days = {from: data.start, to: data.to};
    var period = t.say(data.start ? 'chart-period' : 'chart-through').split(/\{(\w+)\}/).map(function (part, i) {
      return i % 2 ? (days[part] ? w.moment.show(days[part], {style: 'long'}) : '') : part;
    });
    t.mount(el, h`<p class="eg-chart-period">${period}</p>${cur.map(function (c) {
      var head = h`<tr>${named ? '' : h`<th scope="col"></th>`}${cols.map(function (col) {
        return h`<th scope="col" data-path="${col.path}">${w.text.show(col.label)}</th>`; })}</tr>`;
      var E = root.daftarEngraved;
      var lines = c.lines.map(function (line) {
        // a party of an account that holds parties: its own line beneath the account, named as the page calls it, its
        // ledger its own; the lines naming nobody, where they hold anything, marked to be booked to a person
        var nobody = line.party && line.party.nobody;
        var label = line.party ? E.party(t, line.party)
          : named && cols[0].path === 'code' ? figure(cols[0], null, line, c.unit) : account(line.code, line.name);
        // the line opens its ledger; a person's own sheet opens from the ledger's heading (no button inside a button)
        var text = line.party && line.party.bean ? w.text.show(t.titleOf(line.party.bean) || line.party.title || '') : label;
        var opener = h`<th scope="row">${line.posts ? h`<button type="button" class="eg-link" data-ledger="${line.code}" data-unit="${c.unit}">${text}</button>` : label}</th>`;
        var quiet = nobody && (line.cells || []).every(function (x, i) { return cols[i].path === 'name' || !x || x === '0'; });
        return h`<tr data-depth="${String(Math.min(line.depth, 4))}" data-code="${line.code}" data-posts="${line.posts ? 'yes' : 'no'}"${line.party ? h` data-party="${line.party.bean || (nobody ? 'nobody' : 'someone')}"` : ''}${nobody && !quiet ? h` class="eg-warn" title="${t.say('chart-nobody-note')}"` : ''}>${named ? '' : opener}${cols.map(function (col, i) {
          return named && i === 0 ? opener : h`<td>${col.path === 'name' && line.party ? label : figure(col, line.cells[i], line, c.unit)}</td>`;
        })}</tr>`;
      });
      var foot = h`<tr><th scope="row">${t.say('chart-total')}</th>${cols.map(function (col, i) {
        return named && i === 0 ? '' : h`<td>${c.totals[i] != null ? money(c.totals[i], c.unit) : ''}</td>`; })}</tr>`;
      var ledgers = c.lines.filter(function (line) { return line.posts && c.ledgers[line.code]; }).map(function (line) {
        var L = c.ledgers[line.code];
        var name = line.party ? h`${account(line.account, (c.lines.filter(function (x) { return x.code === line.account; })[0] || {}).name || '')} · ${E.party(t, line.party)}` : account(line.code, line.name);
        return h`<details class="eg-ledger" data-ledger="${line.code}" data-unit="${c.unit}"><summary>${t.say('chart-ledger')}: ${name}</summary>${E.ledger(t, L, c.unit, {person: !!L.holds})}</details>`;
      });
      // ONE TRUTH OF WHO OWES WHOM: a person whose account here the agreements read otherwise, said under the table
      var dis = (c.disagree || []).map(function (d) {
        return h`<p class="eg-partial eg-disagree" data-party="${(d.party || {}).bean || ''}">${E.sentence(t, 'chart-disagree', {party: E.party(t, d.party), books: money(d.books, c.unit), agreements: money(d.agreements, c.unit)})}</p>`;
      });
      return h`<section class="eg-chart" data-unit="${c.unit}"><h3 class="eg-chart-unit"><bdi dir="ltr">${c.unit}</bdi></h3><div class="eg-table-wrap"><table class="eg-table eg-chart-table"><thead>${head}</thead><tbody>${lines}</tbody><tfoot>${foot}</tfoot></table></div>${c.balanced ? '' : h`<p class="eg-partial">${t.say('chart-unbalanced')}</p>`}${dis}${ledgers}</section>`;
    })}${notes}`);
    // an account that posts opens its ledger below the table
    el.querySelectorAll('button[data-ledger]').forEach(function (b) {
      b.addEventListener('click', function () {
        var d = el.querySelector('details[data-ledger="' + b.getAttribute('data-ledger') + '"][data-unit="' + b.getAttribute('data-unit') + '"]');
        if (d) { d.open = true; if (d.scrollIntoView) d.scrollIntoView({block: 'nearest'}); }
      });
    });
    t.wire(el);
  }
})(typeof window !== 'undefined' ? window : this);
