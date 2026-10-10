// exact (core/law/values.yaml: number): amounts added up as they are written — decimals (`146.67`), or the fraction n/d (`9650/3`)
// a read value is when its decimals do not end — as fractions of two BigInts: never a float, never cut to a currency's
// places. A ledger's running balance, a report's totals and a voucher's two sides are summed here; the money widget
// shows the result, n/d where it is uneven.
const gcd = (a, b) => { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) [a, b] = [b, a % b]; return a || 1n; };
const norm = (n, d) => { if (d < 0n) { n = -n; d = -d; } const g = gcd(n, d); return [n / g, d / g]; };
export const ZERO = [0n, 1n];
// a written amount as [numerator, denominator], or null when it is not one
export function of(v) {
  const s = String(v ?? '').trim().replace(/^\u2212/, '-');
  let m = s.match(/^(-?\d+)\/(\d+)$/);
  if (m) return BigInt(m[2]) === 0n ? null : norm(BigInt(m[1]), BigInt(m[2]));
  m = s.match(/^(-?)(\d*)(?:\.(\d*))?$/);
  if (!m || !(m[2] || m[3])) return null;
  const frac = m[3] || '';
  return norm(BigInt((m[2] || '0') + frac) * (m[1] ? -1n : 1n), 10n ** BigInt(frac.length));
}
export const add = (a, b) => norm(a[0] * b[1] + b[0] * a[1], a[1] * b[1]);
export const neg = a => [-a[0], a[1]];
export const sub = (a, b) => add(a, neg(b));
export const sign = a => (a[0] > 0n) - (a[0] < 0n);
export const eq = (a, b) => a[0] === b[0] && a[1] === b[1];
// the sum of written amounts; what is not an amount counts as nothing
export const sum = values => values.reduce((s, v) => add(s, of(v) || ZERO), ZERO);
// back to the written form: decimals at `places` where it ends there, else n/d
export function text([n, d], places = 2) {
  const scale = 10n ** BigInt(places);
  if ((n * scale) % d) return `${n}/${d}`;
  const c = n * scale / d, a = (c < 0n ? -c : c).toString().padStart(places + 1, '0');
  return (c < 0n ? '-' : '') + a.slice(0, a.length - places) + (places ? '.' + a.slice(-places) : '');
}
