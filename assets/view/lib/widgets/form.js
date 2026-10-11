// form: a value in one of the law's forms — what a clause holds beside its words (`clause`: the day it falls due, how it
// repeats, its notice, its state…), what a payment settles (`settlement`, one entry each) — drawn BY ITS ENTRIES: each
// attribute by the widget that implements its value (core/law/values.yaml), as the host resolves it from the form's own
// attribute in the law (view_engraved.py `form_def`): a day by moment.js, a repetition by recurrence.js, a choice of a
// table by choice.js, prose by text.js, a name by name.js, an amount as its number and unit, a length of time as its
// number and a unit of duration, an extent as its two days. Nothing about any one form is written here: the definition
// carries it, and what the definition cannot draw is kept as written, never dropped.
import { h, join } from './safe.js';
import { settings } from './settings.js';
import { say, toAscii } from './locale.js';
import * as moment from './moment.js';
import * as choice from './choice.js';
import * as text from './text.js';
import * as name from './name.js';
import * as number from './number.js';
import * as money from './money.js';
import * as recurrence from './recurrence.js';

// the widget of each value a form's attribute may hold, by the value its module says it implements; the composed ones
// (an amount, a length, an extent) are made of them here
const BY = {};
for (const w of [moment, choice, text, name, number, money, recurrence]) BY[w.implements] = w;
const of = value => BY[value] || (value === 'moment' ? BY.day : null);

// THE VALUE SHOWN, attribute by attribute: `{label} value` in the order the form gives its attributes
export function show(v, def, o = {}) {
  if (!v || typeof v !== 'object') return h`<span class="w-none">—</span>`;
  const attrs = (def && def.attrs) || {}, keys = Object.keys(attrs).filter(k => v[k] !== undefined)
    .concat(Object.keys(v).filter(k => !(k in attrs)));
  return h`<span class="w-form">${join(keys.map(k => h`<span class="w-form-attr" data-attr="${k}"><span class="w-form-key">${label(k, attrs[k], o, def)}</span> ${one(v[k], attrs[k], o)}</span>`), ' · ')}</span>`;
}
// an attribute by its name in the reader's language (the names layer's `forms:<form>.<attr>`, sent by the host in
// `o.names`), else the law's own word
function label(k, a, o, def) { return ((o && o.names) || {})[((def && def.name) ? def.name + '.' : '') + k] || k; }
function one(x, a, o) {
  const value = (a || {}).value;
  if (Array.isArray(x)) return join(x.map(y => one(y, a, o)), ', ');
  if (value === 'recurrence') return recurrence.show(x, o);
  if (value === 'form' && x && typeof x === 'object') return show(x, a, o);
  if (x && typeof x === 'object' && 'count' in x) return settings.places[x.unit] !== undefined ? money.show(x.count, x.unit, o)
    : h`${number.show(x.count, o)} <bdi dir="ltr" class="w-unit">${x.unit || ''}</bdi>`;
  if (x && typeof x === 'object' && 'measure' in x) return one(x.measure, {}, o);
  if (x && typeof x === 'object') return show(x, {}, o);
  if ((value === 'moment' || value === 'day' || value === 'extent') && typeof x === 'string') {
    const [a1, a2] = x.split('/');
    return a2 !== undefined ? h`${moment.show(a1, {...o, style: 'long'})} – ${moment.show(a2, {...o, style: 'long'})}` : moment.show(x, {...o, style: 'long'});
  }
  if (value === 'choice' && a.rows) return choice.show(x, a.rows, o);
  if (value === 'name' || value === 'statement') return name.show(x, o);
  return text.show(x, o);
}

// EDITING: one field (or a few) per attribute, named `<name>.<attr>`; an attribute whose value has no widget here is
// carried as written in the definition's `keep`, so a Save writes it back untouched
export function edit(nm, v, def, o = {}) {
  v = v && typeof v === 'object' ? v : {};
  const attrs = (def && def.attrs) || {}, keep = {};
  for (const k of Object.keys(v)) if (!(k in attrs) || !drawable(attrs[k])) keep[k] = v[k];
  const one = k => h`<label class="w-form-field" data-attr="${k}"><span class="w-form-key">${label(k, attrs[k], o, def)}</span> ${field(nm + '.' + k, v[k], attrs[k], o)}<span class="eg-err" data-err="${nm + '.' + k}"></span></label>`;
  // the attributes the value holds and those the form requires are drawn; the rest wait under «more», a disclosure
  // the browser opens itself — an empty field there writes nothing
  const ks = Object.keys(attrs).filter(k => drawable(attrs[k]));
  const shown = ks.filter(k => v[k] !== undefined || attrs[k].required), rest = ks.filter(k => !shown.includes(k));
  return h`<span class="w-form-input" data-name="${nm}" data-keep="${JSON.stringify(keep)}">${join(shown.map(one), ' ')}${rest.length
    ? h`<details class="w-form-more"><summary>${say('form-more', o)}</summary>${join(rest.map(one), ' ')}</details>` : ''}</span>`;
}
function drawable(a) { return a && (['moment', 'day', 'extent', 'recurrence', 'choice', 'statement', 'text', 'name', 'quantity', 'duration'].includes(a.value)); }
function field(nm, x, a, o) {
  switch (a.value) {
    case 'moment': case 'day': return moment.edit(nm, typeof x === 'string' ? x.split(/[T ]/)[0] : '', {...o, placeholder: ''});
    case 'extent': {
      const [a1, a2] = typeof x === 'string' ? x.split('/') : ['', ''];
      return h`${moment.edit(nm + '.from', a1 || '', {...o, placeholder: ''})} – ${moment.edit(nm + '.to', a2 || '', {...o, placeholder: ''})}`;
    }
    case 'recurrence': return recurrence.edit(nm, x, o);
    case 'choice': case 'statement': return choice.edit(nm, x ?? '', a.rows || [], {none: '—'});
    case 'quantity': return h`${number.edit(nm + '.count', x && x.count || '', o)} ${name.edit(nm + '.unit', x && x.unit || '', o)}`;
    case 'duration': {
      const m = x && (x.measure || x) || {};
      return h`${number.edit(nm + '.count', m.count || '', o)} ${choice.edit(nm + '.unit', m.unit || '', recurrence.durations(o).map(d => ({value: d.unit, label: recurrence.unitWords(d.unit, o)})), {none: '—'})}`;
    }
    case 'name': return name.edit(nm, x ?? '', o);
    default: return text.edit(nm, x ?? '', o);
  }
}

// what the fields hold, as the law writes the form — or {error, at} where one does not take. `fields` is
// {<attr>: …, '<attr>.<part>': …} as `collect` gathers them from the page
export function take(fields, def, o = {}) {
  const attrs = (def && def.attrs) || {}, out = {};
  let keep = {};
  try { keep = JSON.parse(fields.keep || '{}'); } catch (e) { keep = {}; }
  for (const [k, a] of Object.entries(attrs)) {
    if (!drawable(a)) continue;
    const sub = Object.fromEntries(Object.entries(fields).filter(([f]) => f === k || f.startsWith(k + '.')).map(([f, x]) => [f === k ? '' : f.slice(k.length + 1), x]));
    const r = takeOne(sub, a, o);
    if (r.error) return {error: r.error, at: k};
    if (r.value !== undefined && r.value !== '' && !(typeof r.value === 'object' && !Object.keys(r.value).length)) out[k] = r.value;
  }
  for (const [k, x] of Object.entries(keep)) if (!(k in out)) out[k] = x;
  if (def && Array.isArray(def.one_of) && def.one_of.length && Object.keys(out).length && !def.one_of.some(k => k in out))
    return {error: say('form-one-of', o, {keys: def.one_of.join(' / ')}), at: def.one_of[0]};
  return {value: out};
}
function takeOne(f, a, o) {
  switch (a.value) {
    case 'moment': case 'day': return moment.take(f[''], o);
    case 'extent': {
      const x = moment.take(f.from, o), y = moment.take(f.to, o);
      if (x.error || y.error) return {error: x.error || y.error};
      return {value: x.value || y.value ? `${x.value}/${y.value}` : ''};
    }
    case 'recurrence': return recurrence.take(f, o);
    case 'choice': case 'statement': return choice.take(f[''], a.rows || [], o);
    case 'quantity': {
      const c = number.take(f.count, o), u = String(f.unit || '').trim();
      if (c.error) return c;
      return c.value || u ? (c.value && u ? {value: {count: c.value, unit: u}} : {error: say('form-amount', o)}) : {value: ''};
    }
    case 'duration': {
      const c = toAscii(String(f.count || '')).trim(), u = String(f.unit || '').trim();
      if (!c && !u) return {value: ''};
      return /^[1-9]\d*$/.test(c) && u ? {value: {count: c, unit: u}} : {error: say('form-length', o)};
    }
    case 'name': return name.take(f[''], o);
    default: return text.take(f[''], o);
  }
}

// THE FIELDS OF ONE FORM, gathered from the page by their names: `<name>.<attr>[.<part>]` → value; a group of
// checkboxes (a week's days) as the list of those checked
export function collect(root, nm) {
  const out = {};
  const box = root.querySelector(`[data-name="${nm}"]`);
  if (box && box.dataset.keep) out.keep = box.dataset.keep;
  root.querySelectorAll(`[name^="${nm}."]`).forEach(el => {
    const k = el.name.slice(nm.length + 1);
    if (el.type === 'checkbox') { (out[k] = out[k] || []); if (el.checked) out[k].push(el.value); }
    else out[k] = el.value;
  });
  root.querySelectorAll(`[data-name^="${nm}."]`).forEach(el => {
    const k = el.dataset.name.slice(nm.length + 1);
    if (el.dataset.keep) out[k + '.keep'] = el.dataset.keep;
    if (el.dataset.in) out[k + '.in'] = el.dataset.in;
  });
  return out;
}
