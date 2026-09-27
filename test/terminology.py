#!/usr/bin/env python3
"""The terminology page: every word of the seed is on it, and every relation it draws is one the seed states.

site/terminology.py writes the body of site/terminology.html from a checkout's seed. This renders it from THIS checkout
and reads the law again by its own means, so that the page and the law are checked against each other rather than
the generator against itself:
  1. every term (and every term a profile adds), every registry of the law and each of its rows, every form, every
     manifesto clause, every RATIONALE entry and every CHANGELOG entry has its place on the page, and no id is twice;
  2. every relation drawn (`data-rel`, `data-from`, `data-to`) is stated by the law: an `in:` of the owner names the
     target, a column of a registry's form (`registry_forms`) joins the two, a system's row names the other in that field, an aspect names
     its figure and its poles, a layer the one beneath, a file's line cites the clause, a RATIONALE key names its item;
  3. every relation the law states between terms and registries, and every link a registry's form states, is drawn;
  4. the page runs no script, every disclosure is closed, every `popovertarget` and `#fragment` names an id on it.
Whether each word's gloss reads well is still a reader's work. site.py checks that the committed page is what the
release's seed builds.
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin'))
import dmparse  # noqa: E402
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.dup, self.rels, self.hrefs, self.targets, self.tags, self.open_details = [], [], [], [], [], set(), 0

    def handle_starttag(self, tag, a):
        a = dict(a)
        self.tags.add(tag)
        if 'id' in a:
            (self.dup if a['id'] in self.ids else self.ids).append(a['id'])
        if 'data-rel' in a:
            self.rels.append((a['data-rel'], a.get('data-from'), a.get('data-to')))
        if tag == 'a' and a.get('href', '').startswith('#'):
            self.hrefs.append(a['href'][1:])
        if 'popovertarget' in a:
            self.targets.append(a['popovertarget'])
        if tag == 'details' and 'open' in a:
            self.open_details += 1




def ins(node):
    """Every `in:` mapping inside a node of the law."""
    if isinstance(node, dict):
        if isinstance(node.get('in'), dict):
            yield node['in']
        for v in node.values():
            yield from ins(v)
    elif isinstance(node, list):
        for v in node:
            yield from ins(v)


def main():
    sys.path.insert(0, os.path.join(ROOT, 'site'))
    import terminology
    global slug
    slug = terminology.anchor           # the page's ids, one to one with what they name
    body = terminology.render(ROOT, 'HEAD')
    law = yaml.safe_load(read('seed/std-vocab.md').split('---\n')[1])
    s = Scan()
    s.feed(body)
    ids = set(s.ids)

    # 1. every word has its place
    terms = [t['term'] for t in law['terms']] + [t['term'] for p in (law.get('profiles') or {}).values()
                                                 for t in (p.get('terms') or [])]
    check('every term of the law and its profiles is on the page (%d)' % len(terms),
          all(slug('term:' + t) in ids for t in terms), [t for t in terms if slug('term:' + t) not in ids])
    regs = [k for k, v in law.items() if isinstance(v, list) and k != 'terms']
    check('every registry of the law is on the page (%d)' % len(regs), all(slug('registry:' + r) in ids for r in regs),
          [r for r in regs if slug('registry:' + r) not in ids])
    missing = []
    for r in regs:
        kf = next((next(iter(x)) for x in law[r] if isinstance(x, dict)), None)
        missing += [f'{r}[{x[kf]}]' for x in law[r] if isinstance(x, dict) and kf in x and slug(f'row:{r}:{x[kf]}') not in ids]
    check('every row of every registry is on the page', not missing, missing[:20])
    forms = [k for k, v in law.items() if isinstance(v, dict) and k != 'profiles']
    check('every form and section of the schema language is on the page (%d)' % len(forms),
          all(slug(('form:' if k.endswith('_form') else 'section:') + k) in ids for k in forms))
    clauses = re.findall(r'(?m)^### (\S+)\s*$', read('MANIFESTO.md'))
    check('every manifesto clause is on the page (%d)' % len(clauses), clauses and all(slug('clause:' + c) in ids for c in clauses),
          [c for c in clauses if slug('clause:' + c) not in ids])
    reasons = re.findall(r'(?m)^## (.+)$', read('seed/RATIONALE.md'))
    shown = [i for i in s.ids if i.startswith('tm-reason.')]
    check('every RATIONALE entry is on the page (%d), a key written twice twice' % len(reasons), len(shown) == len(reasons),
          f'{len(shown)} shown')
    entries = re.findall(r'(?m)^- \*\*', read('seed/CHANGELOG.md'))
    pops = len(re.findall(r'<div class="pop" popover id=', body))
    check('every CHANGELOG entry is a popover on the page (%d)' % len(entries), pops == len(entries), f'{pops} popovers')
    check('no id is on the page twice', not s.dup, s.dup[:10])

    # 2. every relation drawn is stated
    rows = lambda reg, kf: {str(x.get(kf)): x for x in law.get(reg) or [] if isinstance(x, dict)}
    items = {'term:' + t['term']: t for t in law['terms']}
    items.update({'term:' + t['term']: t for p in (law.get('profiles') or {}).values() for t in (p.get('terms') or [])})
    items.update({('form:' if k.endswith('_form') else 'section:') + k: law[k] for k in forms})
    items.update({'row:operations:' + str(o.get('op')): o for o in law.get('operations') or []})
    systems = {**rows('anchor_systems', 'system'), **rows('knowledge_schemes', 'scheme')}
    links = {(l['from'], l['to']) for l in dmparse.registry_links(law)}
    layers = rows('layers', 'layer')
    rat = read('seed/RATIONALE.md')
    name = lambda eid: eid.rsplit(':', 1)[-1]
    bad = []
    for rel, frm, to in s.rels:
        ok = False
        if rel == 'in':
            doms = list(ins(items.get(frm, {})))
            vals = {str(v) for d in doms for v in d.values()}
            ok = bool(doms) and (to == frm or name(to) in vals)
        elif rel == 'link':
            ok = (name(frm), name(to)) in links
        elif rel in ('resolves_through', 'within', 'same_ground_as', 'datum', 'cells_in', 'boundaries_in'):
            v = systems.get(name(frm), {}).get(rel)
            ok = v is not None and (to == frm or name(to) in str(v))
        elif rel == 'figure':
            ok = rows('aspects', 'aspect').get(name(frm), {}).get('figure') == name(to)
        elif rel == 'complement':
            ok = any(isinstance(p, dict) and p.get('complement') for p in rows('aspects', 'aspect').get(name(frm), {}).get('positions') or [])
        elif rel == 'poles':
            ok = frm == to and bool(rows('aspects', 'aspect').get(name(frm), {}).get('poles'))
        elif rel == 'beneath':
            ok = layers.get(name(frm), {}).get('beneath') == name(to)
        elif rel == 'carries':
            f, n = frm[len('doc:'):].rsplit(':', 1)
            line = read(f).split('\n')[int(n) - 1]
            ok = re.search(r'\bmanifesto:[^\n]*\b%s\b' % re.escape(name(to)), line) is not None
        elif rel == 'reason':
            key = frm[len('reason:'):].split('#')[0] if not frm.startswith('reason:doc:') else frm[len('reason:'):]
            key = re.sub(r'#\d+$', '', key)
            ok = ('\n## %s\n' % key) in rat and (to.startswith(('heading:', 'clause:', 'section:', 'form:', 'registry:', 'profile:'))
                                                 or name(to) in key)
        if not ok:
            bad.append((rel, frm, to))
    check('every relation drawn (%d) is one the law states' % len(s.rels), not bad, bad[:10])

    # 3. what the law states is drawn
    drawn = set(s.rels)
    lost = []
    for eid, t in items.items():
        if not eid.startswith('term:'):
            continue
        for d in ins(t):
            if d.get('registry') and not any(r == 'in' and f == eid and name(x) == str(d['registry']) for r, f, x in drawn):
                lost.append((eid, d['registry']))
    check('every registry a term takes its values from is drawn from it', not lost, lost[:10])
    lost = [l for l in links if not any(r == 'link' and name(f) == l[0] and name(x) == l[1] for r, f, x in drawn)]
    check('every link a registry form states is drawn (%d)' % len(links), not lost, lost)

    # 4. how the page behaves
    check('the page runs no script', 'script' not in s.tags and not re.search(r'<[^>]+\son[a-z]+=', body))
    check('every disclosure is closed', s.open_details == 0, s.open_details)
    check('every popovertarget names an id on the page', all(t in ids for t in s.targets),
          sorted(set(t for t in s.targets if t not in ids))[:10])
    check('every #fragment names an id on the page', all(h in ids for h in s.hrefs),
          sorted(set(h for h in s.hrefs if h not in ids))[:10])
    tmpl = read('site/terminology.html')
    check('site/terminology.html carries the marker the build fills', '<!-- daftar:terms id="all" -->' in tmpl)

    print('\nterminology: %d failed' % len(FAILS))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
