#!/usr/bin/env python3
"""The map of the language on the site's one page: every part of the catalogue is on it, once, where the law places it,
and every relation a card counts is one the catalogue states.

site/atlas.py draws the map from a checkout's own catalogue (`bin/dmcatalog.py --json`). This draws it from THIS checkout
and reads the catalogue again by its own run, so that the map and the catalogue are checked against each other rather
than the drawer against itself:
  1. every part has one mark and one card, and no id is given twice;
  2. every mark stands in the stratum of the layer that holds its part, and the law's own items stand in the law;
  3. each kind of relation a card counts, both ways, is the number the catalogue states, and every link on a card or in
     the findings names a card that is there;
  4. the map runs no script and carries no inline style: the page's policy allows neither;
  5. the committed page carries the four blocks the build fills.
Whether a card reads well is still a reader's work. site.py checks that the committed page is what the release builds.
"""
import json, os, re, subprocess, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'site'))
import atlas  # noqa: E402 — site/atlas.py, the drawer this checks
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.hrefs, self.marks, self.cards, self.bad = [], [], [], [], []
        self.stratum, self.card = None, None
        self.rel = []            # (card id, heading words, count)
        self._h5 = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'script' or 'style' in a or tag == 'style':
            self.bad.append(tag)
        if tag == 'section' and 'stratum' in (a.get('class') or ''):
            self.stratum = re.search(r'st-([a-z-]+)', a['class']).group(1)
        if tag == 'a' and 'mk' in (a.get('class') or '').split():
            self.marks.append((self.stratum, a['href'][1:]))
        if tag == 'a' and a.get('href', '').startswith('#'):
            self.hrefs.append(a['href'][1:])
        if tag == 'article' and a.get('class') == 'pc':
            self.card = a['id']
            self.cards.append(a['id'])
        if tag == 'h5' and self.card:
            self._h5 = ''

    def handle_data(self, data):
        if self._h5 is not None:
            self._h5 += data

    def handle_endtag(self, tag):
        if tag == 'h5' and self._h5 is not None:
            m = re.match(r'\s*(.*?)\s+(\d+)\s*$', self._h5)
            if m:
                self.rel.append((self.card, m.group(1), int(m.group(2))))
            self._h5 = None
        if tag == 'article':
            self.card = None


r = subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'dmcatalog.py'), '--json'], cwd=ROOT, capture_output=True,
                   text=True, encoding='utf-8')
check("the catalogue of this checkout is read (bin/dmcatalog.py --json, exit 0)", r.returncode == 0, r.stderr[-400:])
cat = json.loads(r.stdout) if r.returncode == 0 else {'parts': {}, 'relations': [], 'findings': {}}
A = atlas.Atlas(cat)
page = '<div>' + A.field() + A.findings() + A.cards() + '</div>'
S = Scan()
S.feed(page)
parts = cat['parts']
ids = {p: atlas.slug(p) for p in parts}

# ---- 1. once each
marked = [m for _s, m in S.marks]
drawn = {ids[p] for p in parts if parts[p]['kind'] != 'layer'}
check(f"every part but the layers has one mark ({len(drawn)})", sorted(marked) == sorted(drawn),
      sorted(set(drawn) ^ set(marked))[:10])
check(f"every part has one card ({len(parts)})", sorted(S.cards) == sorted(ids.values()),
      sorted(set(ids.values()) ^ set(S.cards))[:10])
dup = sorted({i for i in S.ids if S.ids.count(i) > 1})
check("no id is given twice", not dup, dup[:10])

# ---- 2. where the law places it
wrong = []
for st, mid in S.marks:
    pid = next(p for p, i in ids.items() if i == mid)
    kind, lay = parts[pid]['kind'], (parts[pid].get('contents') or {}).get('layer')
    want = 'law' if kind in atlas.LAW_ITEMS else (lay if lay in atlas.CHAIN + atlas.BESIDE else 'elsewhere')
    if st != want:
        wrong.append((pid, st, want))
check("every mark stands in the stratum of the layer that holds its part, the law's items in the law", not wrong, wrong[:8])
order = [s for s in (atlas.CHAIN + atlas.BESIDE + ('elsewhere',)) if any(st == s for st, _m in S.marks)]
seen = []
for st, _m in S.marks:
    if not seen or seen[-1] != st:
        seen.append(st)
check("the strata stand in the chain's order — manifesto, law, reasoning, journal, history — then beside it",
      seen == order, seen)

# ---- 3. counts and links
want = {}
for rel in cat['relations']:
    o, i = atlas.REL[rel['rel']]
    want.setdefault((ids[rel['from']], o), set()).add(rel['to'])
    want.setdefault((ids[rel['to']], i), set()).add(rel['from'])
got = {(c, w): n for c, w, n in S.rel}
off = [(k, got.get(k), len(v)) for k, v in want.items() if got.get(k) != len(v)]
extra = [k for k in got if k not in want]
check(f"each kind of relation a card counts, both ways, is the catalogue's number ({len(want)} groups)",
      not off and not extra, (off + extra)[:8])
dangling = sorted({h for h in S.hrefs if h not in S.ids and h != 'map'})
check("every link on a card, a mark or a finding names a card that is there", not dangling, dangling[:10])

# ---- 4. the page's policy
check("the map runs no script and carries no inline style", not S.bad, S.bad[:5])

# ---- 5. the committed page
idx = open(os.path.join(ROOT, 'site', 'index.html'), encoding='utf-8').read()
blocks = re.findall(r'<!-- daftar:map id="([a-z]+)"', idx)
check("site/index.html carries the four blocks the build fills: counts, field, findings, cards",
      sorted(blocks) == ['cards', 'counts', 'field', 'findings'], blocks)

print(f"\natlas: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
