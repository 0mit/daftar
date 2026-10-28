// A form is a list of fields, each a widget's edit; collecting it takes every field back through that widget's take,
// so what is saved is exactly the value's written form, or the field says what is wrong with it.
import { h } from './safe.js';
import * as number from './number.js';
import * as money from './money.js';
import * as moment from './moment.js';
import * as text from './text.js';
import * as name from './name.js';
import * as choice from './choice.js';
// a field: {name, label, type, required, options, none, placeholder, places, unit, kind, max, hint, wide, readonly, suggest}
// types: text, lines, number, money, date, time, choice, check, phone, email, id, hidden, show (a widget, read only)
function input(f, v) {
  switch (f.type) {
    case 'lines': return text.edit(f.name, v, {lines: true, max: f.max});
    case 'number': return number.edit(f.name, v, {required: f.required});
    case 'money': return money.edit(f.name, v, f.unit, {required: f.required});
    case 'date': return moment.edit(f.name, v);
    case 'time': return h`<input class="w-input w-time-input" name="${f.name}" dir="ltr" inputmode="numeric" placeholder="08:30" value="${v ?? ''}">`;
    case 'choice': return choice.edit(f.name, v, f.options, {required: f.required, none: f.none, placeholder: f.placeholder});
    case 'check': return h`<input type="checkbox" name="${f.name}" value="true"${v === true || v === 'true' ? h` checked` : ''}>`;
    case 'phone': return name.edit(f.name, v, {kind: 'phone'});
    case 'email': return name.edit(f.name, v, {kind: 'email'});
    case 'id': return name.edit(f.name, v, {kind: 'id'});
    default: return text.edit(f.name, v, {max: f.max, suggest: f.suggest, placeholder: f.placeholder});
  }
}
export function form(fields, values = {}) {
  return h`${fields.map(f => {
    const v = values[f.name] ?? f.value ?? '';
    if (f.type === 'hidden') return h`<input type="hidden" name="${f.name}" value="${v}">`;
    if (f.type === 'show') return h`<div class="fact${f.wide ? ' wide' : ''}"><small>${f.label}</small>${f.widget}</div>`;
    return h`<label class="w-field${f.wide || f.type === 'lines' ? ' wide' : ''}${f.type === 'check' ? ' w-check' : ''}" data-field="${f.name}">
      <span class="w-label">${f.label}${f.required ? ' *' : ''}</span>${input(f, v)}${f.hint ? h`<small class="w-hint">${f.hint}</small>` : ''}<small class="w-field-error" hidden></small></label>`;
  })}`;
}
function take(f, raw) {
  switch (f.type) {
    case 'lines': return text.take(raw, {lines: true, required: f.required, max: f.max});
    case 'number': return number.take(raw, {required: f.required, positive: f.positive, places: f.places});
    case 'money': return money.take(raw, f.unit, {required: f.required, positive: f.positive});
    case 'date': return moment.take(raw, {required: f.required});
    case 'time': return moment.takeTime(raw, {required: f.required});
    case 'choice': return choice.take(raw, f.options, {required: f.required, free: f.free});
    case 'check': return {value: raw === 'true'};
    case 'phone': return name.take(raw, {kind: 'phone', required: f.required});
    case 'email': return name.take(raw, {kind: 'email', required: f.required});
    case 'id': return name.take(raw, {kind: 'id', required: f.required});
    case 'hidden': return {value: raw ?? ''};
    case 'show': return {value: undefined};
    default: return text.take(raw, {required: f.required, max: f.max});
  }
}
// {values, errors}: values in their written forms; errors {name: sentence}
export function collect(formEl, fields) {
  const data = new FormData(formEl), values = {}, errors = {};
  for (const f of fields) {
    if (f.type === 'show') continue;
    const r = take(f, f.type === 'check' ? (data.get(f.name) ? 'true' : '') : data.get(f.name));
    if (r.error) errors[f.name] = r.error; else values[f.name] = r.value;
  }
  return {values, errors};
}
export function showErrors(formEl, errors) {
  formEl.querySelectorAll('[data-field]').forEach(label => {
    const msg = errors[label.dataset.field], small = label.querySelector('.w-field-error');
    label.classList.toggle('w-invalid', Boolean(msg));
    if (small) { small.textContent = msg || ''; small.hidden = !msg; }
  });
  const first = formEl.querySelector('.w-invalid .w-input');
  if (first) first.focus();
  return Object.keys(errors).length === 0;
}
