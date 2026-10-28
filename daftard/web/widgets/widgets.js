'use strict';
// daftar's widgets: one for each value of the data types tree (daftar design/TYPES.md, core/law/values.yaml draft),
// each saying which value it `implements` and answering to the law rows that value rests on. The guide is daftar
// design/TEXT.md: every value is isolated, a number is a left-to-right isolate holding only number characters, and
// every output goes through the one escape of its context. A widget keeps no table of its own: a currency's places
// come from the law's currencies table, sent by the server (W.configure).
const W = (() => {
  // ------------------------------------------------------------------------------------------- escaping (TEXT.md)
  class Safe { constructor(html) { this.html = html; } toString() { return this.html; } }
  const ESC = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'};
  const escape = v => v instanceof Safe ? v.html : String(v ?? '').replace(/[&<>"']/g, c => ESC[c]);
  // h`<b>${value}</b>`: every interpolation escaped unless a widget made it; the only way HTML is built from data
  const h = (strings, ...values) => new Safe(strings.reduce((out, s, i) => out + s + (i < values.length ? escape(values[i]) : ''), ''));
  const join = (parts, sep = '') => new Safe(parts.map(escape).join(escape(sep)));
  // plain text has no markup: a value goes between FSI and PDI (or LRI … PDI for a number), so it cannot reorder the
  // sentence around it (TEXT.md rule 5)
  const FSI = '\u2068', LRI = '\u2066', PDI = '\u2069';
  const isolated = v => FSI + String(v ?? '') + PDI;

  // ------------------------------------------------------------------------------------------------ the law's data
  const law = {places: {}};
  function configure({currencies} = {}) {
    for (const c of currencies || []) if (/^\d+$/.test(String(c.digits ?? ''))) law.places[c.code] = Number(c.digits);
  }

  // ---------------------------------------------------------------------------------------- number (value: number)
  // The wire form is the law's: a count as written (`-1950`, `260.50`), or an exact fraction n/d (`9650/3`) when the
  // value was read and its decimals do not end. Parsed exactly, into BigInts and digit strings; never a float.
  const FA = '۰۱۲۳۴۵۶۷۸۹';
  function parse(v) {
    const s = String(v ?? '').trim();
    let m = s.match(/^(-?)(\d+)\/(\d+)$/);
    if (m) {
      const n = BigInt(m[2]), d = BigInt(m[3]);
      if (d === 0n) return null;
      return {neg: m[1] === '-' && n !== 0n, whole: n / d, rest: n % d, den: d, decimals: ''};
    }
    m = s.match(/^(-?)(\d+)(?:\.(\d+))?$/);
    if (!m) return null;
    return {neg: m[1] === '-' && /[1-9]/.test(m[2] + (m[3] || '')), whole: BigInt(m[2]), rest: 0n, den: 1n, decimals: m[3] || ''};
  }
  const digitsOf = (s, o) => o.digits === 'latn' ? s : String(s).replace(/[0-9]/g, d => FA[d]);
  const sepOf = o => o.digits === 'latn' ? {group: ',', decimal: '.'} : {group: '٬', decimal: '٫'};
  function grouped(s, o) { return o.group === false ? s : s.replace(/\B(?=(\d{3})+(?!\d))/g, '\u0001'); }
  // a fraction that ends in `places` decimals is shown as those decimals (2/8 of a lira at 2 places is 0.25)
  function ending(p, places) {
    if (!p.rest || places === undefined) return p;
    const scale = 10n ** BigInt(places);
    if ((p.rest * scale) % p.den) return p;
    return {...p, rest: 0n, den: 1n, decimals: String(p.rest * scale / p.den).padStart(places, '0')};
  }
  function parts(v, o = {}) {
    let p = parse(v);
    if (!p) return null;
    p = ending(p, o.places);
    const sep = sepOf(o);
    let decimals = p.decimals;
    if (o.places !== undefined && !p.rest && decimals.length < o.places) decimals = decimals.padEnd(o.places, '0');
    const whole = digitsOf(grouped(String(p.whole), o), o).replace(/\u0001/g, sep.group);
    return {neg: p.neg, whole, decimal: decimals ? sep.decimal + digitsOf(decimals, o) : '',
            num: p.rest ? digitsOf(String(p.rest), o) : '', den: p.rest ? digitsOf(String(p.den), o) : '',
            showWhole: !p.rest || p.whole !== 0n, uneven: Boolean(p.rest)};
  }
  const MINUS = '−';
  const number = {
    implements: 'number',
    parse, parts,
    // options: digits 'fa'|'latn'; group; places; fraction 'mixed'|'math'|'inline'; className
    show(v, o = {}) {
      const p = parts(v, o);
      if (!p) return h`<bdi class="w-num w-bad">${v ?? '—'}</bdi>`;
      const style = o.fraction || 'mixed';
      let frac = new Safe('');
      if (p.uneven) {
        frac = style === 'inline'
          ? h`<span class="w-inline">${p.num}⁄${p.den}</span>`
          // numerator over denominator; the hidden slash keeps a copy readable as «۲۷٬۹۶۶ ۱/۶»
          : h`<span class="w-frac"><span class="w-n">${p.num}</span><span class="w-x">⁄</span><span class="w-d">${p.den}</span></span>`;
      }
      const gap = p.uneven && p.showWhole ? ' ' : '';
      const label = (p.neg ? MINUS : '') + (p.showWhole ? p.whole + p.decimal : '') + gap + (p.uneven ? p.num + '/' + p.den : '');
      return h`<bdi dir="ltr" class="w-num${o.className ? ' ' + o.className : ''}" aria-label="${label}">${p.neg ? MINUS : ''}${p.showWhole ? p.whole + p.decimal : ''}${gap}${frac}</bdi>`;
    },
    // a count in running text that its caller escapes and isolates (a badge, a heading): the characters alone, or null
    // when v is not a number in the wire form
    plain(v, o = {}) {
      const p = parts(String(v ?? ''), o);
      if (!p) return null;
      return (p.neg ? MINUS : '') + (p.showWhole ? p.whole + p.decimal : '') + (p.uneven ? (p.showWhole ? '\u202f' : '') + p.num + '/' + p.den : '');
    },
    // for CSV, a notification or a log: the same characters, isolated left to right
    text(v, o = {}) {
      const p = parts(v, o);
      if (!p) return isolated(v);
      return LRI + (p.neg ? MINUS : '') + (p.showWhole ? p.whole + p.decimal : '') + (p.uneven ? (p.showWhole ? ' ' : '') + p.num + '/' + p.den : '') + PDI;
    },
    // what a person typed, as the law writes a count, or a refusal: Persian and Arabic digits, ٫ and a grouping
    // ٬ or , are read; a fraction is refused, since a count is written in decimals (lines.yaml types: count)
    take(input, o = {}) {
      let s = String(input ?? '').trim().replace(/[۰-۹]/g, d => FA.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d))
        .replace(/[\u200E\u200F\u2066-\u2069\u202A-\u202E]/g, '').replace(/^[−−]/, '-').replace(/٫/g, '.');
      if (/[٬,]/.test(s)) {
        if (!/^-?\d{1,3}([٬,]\d{3})+(\.\d+)?$/.test(s)) return {error: 'جداکنندهٔ هزارگان سر جایش نیست.'};
        s = s.replace(/[٬,]/g, '');
      }
      if (!/^-?(0|[1-9]\d{0,39})(\.\d{1,40})?$/.test(s)) return {error: 'عدد را با رقم و حداکثر یک ممیز بنویسید.'};
      if (o.places !== undefined && (s.split('.')[1] || '').length > o.places) return {error: `حداکثر ${digitsOf(String(o.places), o)} رقم اعشار.`};
      if (o.positive && (s.startsWith('-') || /^0(\.0+)?$/.test(s))) return {error: 'مبلغ باید بزرگ‌تر از صفر باشد.'};
      return {value: s.replace(/^-0(\.0+)?$/, '0')};
    },
  };

  // ------------------------------------------------------------------------------------------ money (value: money)
  // The number widget is its digits, at the currency's places (quantities.yaml money: units_from currencies, digits);
  // the currency's label stays outside the number's isolate, in the sentence's own direction (TEXT.md rule 3). An
  // amount that does not come out even in those places is shown as the fraction it is and says so, never rounded.
  const UNEVEN = 'به رقم‌های اعشار این ارز سرراست نمی‌شود؛ اینکه باقی‌مانده با کیست را بند توافق می‌گوید، نه گرد کردن';
  const names = {};
  function currencyName(code, lang) {
    try { return (names[lang] ||= new Intl.DisplayNames([lang], {type: 'currency'})).of(code); } catch { return code; }
  }
  const money = {
    implements: 'money',
    UNEVEN,
    places: unit => law.places[unit],
    // options: label 'code'|'name'|'none'; lang (for the name, CLDR's); everything number takes; abs (no sign)
    show(v, unit, o = {}) {
      const places = o.places ?? law.places[unit];
      let value = v;
      if (o.abs) value = String(v ?? '').trim().replace(/^-/, '');
      const p = parts(value, {...o, places});
      const n = number.show(value, {...o, places});
      const label = o.label === 'none' || !unit ? '' : o.label === 'name' ? currencyName(unit, o.lang || 'fa') : unit;
      const flag = p && p.uneven ? h`<span class="w-uneven" title="${UNEVEN}" aria-label="${UNEVEN}">*</span>` : '';
      return label ? h`<span class="w-money">${n}${flag} <span class="w-unit">${label}</span></span>`
                   : h`<span class="w-money">${n}${flag}</span>`;
    },
    text(v, unit, o = {}) {
      const label = o.label === 'none' || !unit ? '' : o.label === 'name' ? currencyName(unit, o.lang || 'fa') : unit;
      return number.text(v, {...o, places: o.places ?? law.places[unit]}) + (label ? ' ' + label : '');
    },
    take(input, unit, o = {}) { return number.take(input, {...o, places: law.places[unit]}); },
    negative: v => (parse(v) || {}).neg === true,
    uneven: (v, unit) => Boolean((parts(v, {places: law.places[unit]}) || {}).uneven),
  };

  return {Safe, h, escape, join, isolated, configure, number, money};
})();
if (typeof module !== 'undefined') module.exports = W;
