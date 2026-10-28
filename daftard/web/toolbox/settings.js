// Who a page is for and how it shows things, from the garden's own settings (daftard.json, via the payload): the
// gardener, how they are called, the garden's title and language, the reader's calendar, each currency's places.
// A widget asks here; it keeps no table of its own (a currency's places are the law's currencies table's).
import { T } from './say.js';
const s = {me: '', gardener: '', title: 'دفتر', lang: 'fa', calendar: 'persian', zone: 'Europe/Istanbul', places: {}, asOf: ''};
export function configure(data = {}) {
  const g = data.garden || {};
  s.gardener = g.gardener || s.gardener;
  s.me = g.me || g.gardener || s.me;
  s.title = g.title || s.title;
  s.lang = g.lang || s.lang;
  s.calendar = g.calendar || (s.lang === 'fa' ? 'persian' : 'gregory');
  s.zone = g.zone || s.zone;
  s.asOf = data.asOf || s.asOf;
  for (const c of data.currencies || []) if (/^\d+$/.test(String(c.digits ?? ''))) s.places[c.code] = Number(c.digits);
}
export const settings = s;
export const me = () => s.me || s.gardener || T('من', 'me');
export const gardenerId = () => s.gardener;
export const digitsOf = lang => (lang || s.lang) === 'fa' ? 'fa' : 'latn';
