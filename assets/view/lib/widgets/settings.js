// Who a page is for and how it shows things, from the garden's own settings sent with the page: the gardener, how
// they are called, the garden's title, the reader's language and calendar, the garden's zone, each currency's places,
// and the day the server read as today. A widget asks here; it keeps no table of its own (a currency's places are the
// law's currencies table's). Nothing is assumed: a setting not given is read from the page (its `lang`) or from the
// reader's own runtime, and no language, calendar or zone stands in for a missing one.
// A READER'S OWN WAY OF READING (`reader`, kept with their account on the host, never in the garden): their language as
// one BCP 47 tag whose Unicode keys say their calendar, digits, hour cycle and first day of the week (`locale`:
// `fa-u-ca-persian-nu-arabext`), the zone a moment is shown in (`zone`, from the tag's `tz`), how a day is written
// (`date`: short, medium, long, full) and how a currency is named (`currency`: symbol, narrowSymbol, code, name). What
// they did not set is their language's own, as CLDR says it.
const s = {me: '', gardener: '', title: '', lang: '', calendar: '', zone: '', places: {}, asOf: '',
           locale: '', readerZone: '', date: '', currency: ''};
export function configure(data = {}) {
  const g = data.garden || {};
  for (const k of ['gardener', 'title', 'lang', 'calendar', 'zone']) if (g[k]) s[k] = String(g[k]);
  if (data.reader) {                     // the reader's choice, whole: what they unset is unset
    const r = data.reader;
    s.locale = String(r.locale || ''); s.readerZone = String(r.zone || ''); s.date = String(r.date || ''); s.currency = String(r.currency || '');
  }
  s.me = g.me || g.gardener || s.me;
  s.asOf = data.asOf || s.asOf;
  for (const c of data.currencies || []) if (/^\d+$/.test(String(c.digits ?? ''))) s.places[c.code] = Number(c.digits);
  // the systems a repetition may be counted in, and the units of a length of time: the law's, as the host sends them
  if (Array.isArray(data.systems)) s.systems = data.systems;
  if (Array.isArray(data.durations)) s.durations = data.durations;
}
export const settings = s;
export const me = () => s.me || s.gardener;
export const gardenerId = () => s.gardener;
