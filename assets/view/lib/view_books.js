/* view_books.js — the `books` archetype engraved from the books' reading (view_engraved.py `books`, the accounting
   profile's asset): per currency, the trial balance — each account in its chart's order, what it held before the
   period (its opening), what arrived (debit), what left (credit) and its balance in its element's sense, with the totals
   — and the ledger of each account that posts, opened from its line, each line with its running balance. Its columns
   run along the reader's line (`axes: { inline: taxis, block: ordinal }`), debit before credit, so a right-to-left reader
   reads the debit at the right, as books are written in their script. Every amount by money.js at its currency's
   places, every day in the reader's calendar, every account by its name in the reader's language (the page's `codes`),
   its code beside it in its title. A classic script beside view_engraved.js, built only through safe.js. */
(function (root) {
  'use strict';
  var A = root.daftarArchetypes = root.daftarArchetypes || {};

  A.books = function (el, data, t) {
    var h = t.h, w = t.w, cur = data.currencies || [];
    var notes = (data.notes || []).map(function (n) { return h`<p class="eg-partial">${w.text.show(n)}</p>`; });
    if (!cur.length) {
      t.mount(el, h`<p class="eg-empty">${t.say('books-empty')}</p>${notes}`);
      return;
    }
    function money(x, unit) {
      return x && x !== '0' ? root.daftarEngraved.show(t, {count: x, unit: unit}, {}) : h`<span class="w-none">—</span>`;
    }
    function account(code, name) {
      var c = (t.E.codes || {})[code];
      return h`<span class="eg-code" title="${code}${c && c.by ? ' · ' + c.by : ''}">${w.text.show(c ? c.name : name)}</span>`;
    }
    var period = data.start ? t.say('books-period', {from: data.start, to: data.to}) : t.say('books-through', {to: data.to});
    var head = h`<tr><th scope="col">${t.say('books-account')}</th><th scope="col">${t.say('books-opening')}</th><th scope="col">${t.say('books-debit')}</th><th scope="col">${t.say('books-credit')}</th><th scope="col">${t.say('books-balance')}</th></tr>`;
    t.mount(el, h`<p class="eg-books-period">${w.text.show(period)}</p>${cur.map(function (c) {
      var rows = c.rows.map(function (r) {
        var name = r.posts ? h`<button type="button" class="eg-link" data-ledger="${r.code}" data-unit="${c.unit}">${account(r.code, r.name)}</button>` : account(r.code, r.name);
        return h`<tr data-depth="${String(Math.min(r.depth, 4))}" data-code="${r.code}" data-posts="${r.posts ? 'yes' : 'no'}"><th scope="row">${name}</th><td>${money(r.opening, c.unit)}</td><td>${money(r.dr, c.unit)}</td><td>${money(r.cr, c.unit)}</td><td>${money(r.balance, c.unit)}</td></tr>`;
      });
      var tot = c.totals || {};
      var ledgers = c.rows.filter(function (r) { return r.posts && c.ledgers[r.code]; }).map(function (r) {
        var L = c.ledgers[r.code];
        return h`<details class="eg-ledger" data-ledger="${r.code}" data-unit="${c.unit}"><summary>${t.say('books-ledger')}: ${account(r.code, r.name)}</summary><table class="eg-table"><thead><tr><th scope="col">${t.say('books-day')}</th><th scope="col">${t.say('books-what')}</th><th scope="col">${t.say('books-debit')}</th><th scope="col">${t.say('books-credit')}</th><th scope="col">${t.say('books-balance')}</th></tr></thead><tbody><tr class="eg-books-opening"><td></td><td>${t.say('books-opening')}</td><td></td><td></td><td>${money(L.opening, c.unit)}</td></tr>${L.lines.map(function (x) {
          return h`<tr><td>${x.day ? w.moment.show(x.day, {style: 'long'}) : ''}</td><td>${x.bean ? w.being.show(x.bean, x.title || x.bean, {action: 'open'}) : h`<span class="w-none">${t.say('books-hidden')}</span>`}${x.memo ? h` <span class="eg-memo">${w.text.show(x.memo)}</span>` : ''}</td><td>${money(x.dr, c.unit)}</td><td>${money(x.cr, c.unit)}</td><td>${money(x.balance, c.unit)}</td></tr>`;
        })}</tbody></table></details>`;
      });
      return h`<section class="eg-books" data-unit="${c.unit}"><h3 class="eg-books-unit"><bdi dir="ltr">${c.unit}</bdi></h3><div class="eg-table-wrap"><table class="eg-table eg-books-trial"><thead>${head}</thead><tbody>${rows}</tbody><tfoot><tr><th scope="row">${t.say('books-total')}</th><td>${money(tot.opening, c.unit)}</td><td>${money(tot.dr, c.unit)}</td><td>${money(tot.cr, c.unit)}</td><td></td></tr></tfoot></table></div>${c.balanced ? '' : h`<p class="eg-partial">${t.say('books-unbalanced')}</p>`}${ledgers}</section>`;
    })}${notes}`);
    // an account that posts opens its ledger below the balance
    el.querySelectorAll('button[data-ledger]').forEach(function (b) {
      b.addEventListener('click', function () {
        var d = el.querySelector('details[data-ledger="' + b.getAttribute('data-ledger') + '"][data-unit="' + b.getAttribute('data-unit') + '"]');
        if (d) { d.open = true; if (d.scrollIntoView) d.scrollIntoView({block: 'nearest'}); }
      });
    });
    t.wire(el);
  };
})(typeof window !== 'undefined' ? window : this);
