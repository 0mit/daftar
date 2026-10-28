'use strict';
// The garden's people and the private side of its consultation cases: a person's name and ways to reach them, a case's
// profile (age, education, where they live, their stay in Turkey, documents), and every contact, offer and follow-up
// she wrote before, corrected or taken out. What is private is held off git (bin/held.py, dashboard/model.py); a form
// shows it only on the machine that holds it.
Object.assign(schemas, {
  'person-contact': [['name', 'نام', 'text', true], ['phone', 'تلفن'], ['email', 'ایمیل', 'email'], ['address', 'نشانی', 'area'], ['notes', 'یادداشت', 'area']],
  'case-profile': [['age', 'سن'], ['education', 'تحصیلات'], ['current_area', 'محل سکونت'], ['turkey_stay', 'وضعیت حضور در ترکیه'],
                   ['original-diploma', 'اصل مدرک'], ['transcript', 'ریزنمرات'], ['diploma-photo', 'عکس مدرک'], ['diploma-translation', 'ترجمهٔ مدرک'],
                   ['notes', 'یادداشت', 'area']],
});
Object.assign(formTitles, {'person-contact': 'مشخصات تماس', 'case-profile': 'سن و مشخصات کلاینت'});
const ITEM_SECTIONS = {offer: 'offers', contact: 'contacts', followup: 'followups'};
const ITEM_TITLES = {offer: 'ویرایش پیشنهاد دانشگاه', contact: 'ویرایش تماس', followup: 'ویرایش پیگیری'};
let peopleQuery = '';

function personOf(id) { return (data.people || []).find(p => p.id === id); }
function openPeopleForm(kind, bean, values, title, extra = '', note = '') {
  if (stale) { notice('اطلاعات قدیمی است؛ ابتدا صفحه را به‌روزرسانی کنید.', true); return; }
  edit = {kind, bean, entry: '', head: data.head, request: crypto.randomUUID()};
  $('form-title').textContent = title;
  $('fields').innerHTML = schemas[kind].map(s => fieldHTML(s, values[s[0]] ?? '')).join('') + extra +
    (note ? `<p class="wide muted">${esc(note)}</p>` : '');
  $('form-error').textContent = ''; $('save').disabled = false;
  if (!$('editor').open) $('editor').showModal();
}
function openPerson(id) {
  const p = personOf(id);
  if (!p || p.state !== 'here') { notice(p?.state === 'erased' ? 'اطلاعات خصوصی این شخص به درخواست خودش حذف شده است.' : 'اطلاعات تماس این شخص روی این دستگاه نیست.', true); return; }
  openPeopleForm('person-contact', id, p, formTitles['person-contact'] + ' · ' + p.name, '',
    'نام و راه‌های تماس فقط در مخزن خصوصی همین لپ‌تاپ نگه داشته می‌شوند، نه در گیت؛ دفتر فقط ثبت می‌کند که تغییر کردند.');
}
function openProfile(caseId) {
  const c = data.cases.find(x => x.id === caseId); if (!c) return;
  if (!c.profileFields) { notice('مشخصات خصوصی این پرونده روی این دستگاه در دسترس نیست.', true); return; }
  openPeopleForm('case-profile', caseId, c.profileFields, formTitles['case-profile'] + ' · ' + c.name, '',
    (c.profileFields.held ? '' : 'این پرونده هنوز مشخصات خصوصی ندارد؛ با ذخیره، در مخزن خصوصی ساخته می‌شود. ') + 'خالی کردن یک فیلد آن را پاک می‌کند.');
}
function openItem(kind, caseId, key) {
  const c = data.cases.find(x => x.id === caseId); const item = c?.record[ITEM_SECTIONS[kind]]?.[key];
  if (!item) return;
  const values = {...item, ...(kind === 'offer' ? {count: item.tuition?.count || '', unit: item.tuition?.unit || ''} : {})};
  openPeopleForm(kind, caseId, values, ITEM_TITLES[kind] + ' · ' + c.name,
    `<input type="hidden" name="entry" value="${esc(key)}"><label class="wide remove-item"><span><input type="checkbox" name="remove" value="1"> این مورد را از پرونده بردار (اشتباه ثبت شده بود)</span></label>`,
    'تغییر در همین مورد ثبت می‌شود و نسخهٔ قبلی در تاریخچهٔ دفتر می‌ماند.');
}

function renderPeople() {
  const rows = (data.people || []).map(p => {
    const cases = p.cases.map(id => data.cases.find(c => c.id === id)).filter(Boolean);
    const state = p.state === 'here' ? '' : p.state === 'erased' ? badge('حذف‌شده به درخواست شخص', 'late') : badge('روی این دستگاه نیست', 'late');
    return `<tr data-person-row="${esc([p.name, p.phone, p.email, p.id].join(' ').toLowerCase())}"><td><b>${esc(p.name || p.id)}</b>${state}<small dir="ltr">${esc(p.id)}</small></td><td dir="ltr">${esc(p.phone)}</td><td dir="ltr">${esc(p.email)}</td><td>${cases.map(c => `<button class="text-button" data-client="${esc(c.id)}">${esc(c.type || 'پرونده')} · ${esc(c.status || '')}</button>`).join('<br>') || '—'}</td><td class="actions">${p.state === 'here' ? `<button class="text-button" data-people="person" data-bean="${esc(p.id)}">ویرایش</button>` : ''}</td></tr>`;
  }).join('');
  return `<section class="panel"><div class="panel-head"><div><h2>مخاطبان</h2><p>نام و راه‌های تماس هر کلاینت، که فقط در مخزن خصوصی همین لپ‌تاپ نگه داشته می‌شوند. سن و مشخصات هر پرونده از خود پرونده ویرایش می‌شود.</p></div><input type="search" id="people-search" placeholder="جستجوی نام یا تلفن" value="${esc(peopleQuery)}"></div>${rows ? `<div class="table-scroll"><table><thead><tr><th>نام</th><th>تلفن</th><th>ایمیل</th><th>پرونده‌ها</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>` : '<div class="empty">مخاطبی در این دستگاه نگه داشته نمی‌شود.</div>'}</section>`;
}
function filterPeople() {
  const q = peopleQuery.trim().toLowerCase();
  for (const r of document.querySelectorAll('[data-person-row]')) r.hidden = !!q && !r.dataset.personRow.includes(q);
}
extraTabs.people = {title: 'مخاطبان', render: () => { setTimeout(filterPeople); return renderPeople(); }};

document.addEventListener('click', e => {
  const b = e.target.closest('[data-people]'); if (!b || !data) return;
  const k = b.dataset.people;
  if (k === 'person') openPerson(b.dataset.bean);
  else if (k === 'profile') openProfile(b.dataset.bean);
  else if (ITEM_SECTIONS[k]) openItem(k, b.dataset.bean, b.dataset.entry);
});
document.addEventListener('input', e => { if (e.target.id === 'people-search') { peopleQuery = e.target.value; filterPeople(); } });
