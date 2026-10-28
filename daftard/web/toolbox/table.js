// A table of rows whose cells are widgets. Sorting happens in the page, by each sortable column's data-v.
import { h } from './safe.js';
// columns: [{title, cell: row => Safe|string, sort?: row => string|number, align?: 'num', cls?}]; rowAttrs: row => Safe
// (attributes of a row, such as what a search looks in)
export function table({columns, rows, empty = 'موردی نیست.', cls = '', rowClass, rowAttrs, caption}) {
  if (!rows || !rows.length) return h`<div class="empty">${empty}</div>`;
  return h`<div class="table-scroll"><table class="w-table${cls ? ' ' + cls : ''}">${caption ? h`<caption>${caption}</caption>` : ''}<thead><tr>${columns.map((c, i) =>
    h`<th class="${c.align === 'num' ? 'num' : ''}"${c.sort ? h` data-sort-col="${i}" tabindex="0" aria-sort="none"` : ''}>${c.title}</th>`)}</tr></thead><tbody>${rows.map(r =>
    h`<tr${rowClass ? h` class="${rowClass(r) || ''}"` : ''}${rowAttrs ? rowAttrs(r) : ''}>${columns.map(c =>
      h`<td class="${c.align === 'num' ? 'num' : ''}${c.cls ? ' ' + c.cls : ''}"${c.sort ? h` data-v="${c.sort(r) ?? ''}"` : ''}>${c.cell(r)}</td>`)}</tr>`)}</tbody></table></div>`;
}
// clicking (or Enter on) a sortable header sorts its table's rows in place; again reverses
export function bindSort(root) {
  const sortBy = th => {
    const tbody = th.closest('table').tBodies[0], col = th.cellIndex;
    const asc = th.getAttribute('aria-sort') !== 'ascending';
    th.closest('tr').querySelectorAll('th').forEach(x => x.setAttribute('aria-sort', x.dataset.sortCol ? 'none' : x.getAttribute('aria-sort')));
    th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
    const key = tr => tr.cells[col]?.dataset.v ?? '';
    const num = v => v !== '' && !isNaN(Number(v));
    [...tbody.rows].sort((a, b) => {
      const x = key(a), y = key(b);
      const c = num(x) && num(y) ? Number(x) - Number(y) : x.localeCompare(y, 'fa');
      return asc ? c : -c;
    }).forEach(tr => tbody.appendChild(tr));
  };
  root.addEventListener('click', e => { const th = e.target.closest('th[data-sort-col]'); if (th) sortBy(th); });
  root.addEventListener('keydown', e => { const th = e.target.closest('th[data-sort-col]'); if (th && e.key === 'Enter') sortBy(th); });
}
