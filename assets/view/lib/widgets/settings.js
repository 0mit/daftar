// Who a page is for and how it shows things, from the garden's own settings sent with the page: the gardener, how
// they are called, the garden's title, the reader's language and calendar, the garden's zone, each currency's places,
// and the day the server read as today. A widget asks here; it keeps no table of its own (a currency's places are the
// law's currencies table's). Nothing is assumed: a setting not given is read from the page (its `lang`) or from the
// reader's own runtime, and no language, calendar or zone stands in for a missing one.
const s = {me: '', gardener: '', title: '', lang: '', calendar: '', zone: '', places: {}, asOf: ''};
export function configure(data = {}) {
  const g = data.garden || {};
  for (const k of ['gardener', 'title', 'lang', 'calendar', 'zone']) if (g[k]) s[k] = String(g[k]);
  s.me = g.me || g.gardener || s.me;
  s.asOf = data.asOf || s.asOf;
  for (const c of data.currencies || []) if (/^\d+$/.test(String(c.digits ?? ''))) s.places[c.code] = Number(c.digits);
}
export const settings = s;
export const me = () => s.me || s.gardener;
export const gardenerId = () => s.gardener;
