// The garden's people: each client's name and ways to reach them, held off git on the machine that keeps them.
import { h } from '/toolbox/safe.js';
import * as name from '/toolbox/name.js';
import * as text from '/toolbox/text.js';
import { table } from '/toolbox/table.js';
import { badge, caseLink } from '../common.js';
let query = '';
const FA = '۰۱۲۳۴۵۶۷۸۹';
const ascii = s => String(s).replace(/[۰-۹]/g, d => FA.indexOf(d));
function filterRows() {
  const q = ascii(query.trim().toLowerCase());
  for (const r of document.querySelectorAll('[data-person-row]')) r.hidden = Boolean(q) && !r.dataset.personRow.includes(q);
}
export default {
  id: 'people', nav: 'مخاطبان', title: 'مخاطبان',
  render(ctx) {
    const d = ctx.data;
    setTimeout(filterRows);
    return h`<section class="panel"><div class="panel-head"><div><h2>مخاطبان</h2><p>نام و راه‌های تماس هر کلاینت، که فقط در مخزن خصوصی همین رایانه نگه داشته می‌شوند. سن و مشخصات هر پرونده از خود پرونده ویرایش می‌شود.</p></div>
      <input type="search" data-people-search aria-label="جستجوی مخاطب" placeholder="جستجوی نام یا تلفن" value="${query}"></div>
      ${table({empty: 'مخاطبی در این دستگاه نگه داشته نمی‌شود.', rows: d.people || [],
        rowAttrs: p => h` data-person-row="${ascii([p.name, p.phone, p.email, p.id].join(' ').toLowerCase())}"`,
        columns: [
          {title: 'نام', cell: p => h`<b>${text.show(p.name || p.id)}</b>${p.state === 'here' ? '' : badge(p.state === 'erased' ? 'حذف‌شده به درخواست شخص' : 'روی این دستگاه نیست', 'late')}<small>${name.show(p.id)}</small>`, sort: p => p.name || p.id},
          {title: 'تلفن', cell: p => name.show(p.phone, {kind: 'phone', link: true})},
          {title: 'ایمیل', cell: p => name.show(p.email, {kind: 'email', link: true})},
          {title: 'پرونده‌ها', cell: p => { const cs = (p.cases || []).map(id => d.cases.find(c => c.id === id)).filter(Boolean);
            return cs.length ? cs.map((c, i) => h`${i ? h`<br>` : ''}${caseLink({...c, name: (c.type || 'پرونده') + ' · ' + (c.status || '')})}`) : '—'; }},
          {title: '', cell: p => p.state === 'here' ? h`<button class="text-button" data-action="edit-person" data-person="${p.id}">ویرایش</button>` : ''},
        ]})}</section>`;
  },
  input(e) { if (e.target.matches('[data-people-search]')) { query = e.target.value; filterRows(); } },
};
