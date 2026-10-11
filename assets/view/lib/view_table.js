/* view_table.js — the `table` archetype engraved from its reading, where the page names no drawing module: the members
   of the drawing's reading, one line each, a column per path (the server's reading, `view_engraved.py` `table`, each
   line one the reader may read). Every cell is shown by the widget of what it holds — a day in the reader's calendar, an
   amount at its currency's places, a being by its title — never as the text a path happened to give, and each line
   opens its being's sheet. Its lines run down the page and its columns along the reader's line (`axes: { inline:
   taxis, block: ordinal }`), so a right-to-left reader reads the first column at the right. A classic script beside
   view_engraved.js, built only through safe.js. */
(function (root) {
  'use strict';
  var A = root.daftarArchetypes = root.daftarArchetypes || {};
  var ANY = {shape: ['being', 'position', 'text']};

  A.table = function (el, data, t) {
    var h = t.h, w = t.w, cols = data.columns || [], rows = data.rows || [];
    if (!rows.length) {
      t.mount(el, h`<p class="eg-empty">${t.say('table-empty')}</p>${(data.notes || []).map(function (n) { return h`<p class="eg-partial">${w.text.show(n)}</p>`; })}`);
      return;
    }
    function cell(vals) {
      var list = Array.isArray(vals) ? vals : [vals];
      return list.length ? t.join(list.map(function (v) { return root.daftarEngraved.show(t, v, ANY); }), ', ') : h`<span class="w-none">—</span>`;
    }
    // a line opens its being's sheet from its first cell: the title where the first column is the title, else a cell
    // of its own before the columns, holding the title
    var titled = cols.length && cols[0].path === 'title';
    t.mount(el, h`<div class="eg-table-wrap"><table class="eg-table"><thead><tr>${titled ? '' : h`<th scope="col"></th>`}${cols.map(function (c) {
      return h`<th scope="col" data-path="${c.path}">${w.text.show(c.label)}</th>`; })}</tr></thead><tbody>${rows.map(function (r) {
      var open = h`<th scope="row">${w.being.show(r.bean, r.title || r.bean, {action: 'open'})}</th>`;
      return h`<tr data-bean="${r.bean}">${titled ? '' : open}${cols.map(function (c, i) {
        return titled && i === 0 ? open : h`<td>${cell(r.cells[i])}</td>`;
      })}</tr>`;
    })}</tbody></table></div>${(data.notes || []).map(function (n) { return h`<p class="eg-partial">${w.text.show(n)}</p>`; })}`);
    t.wire(el);
  };
})(typeof window !== 'undefined' ? window : this);
