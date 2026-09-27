#!/usr/bin/env python3
"""site/atlas.py — the map of the language on the site's one page: every part of a release, where it sits, what it is
held to and what it touches, drawn from the release's own catalogue (`bin/dmcatalog.py --json`) and nothing else.

    python3 site/atlas.py <checkout> [field|cards|findings]     # print one block, as site/build.py writes it

THE FIELD. Each part is a mark in the stratum of the layer that holds it — the manifesto above the law, the law above
its reasoning, the reasoning above the journal, and beside them the guides and the gate's own tools — sized by how many
relations it has, both ways. A mark is a link to the part's card. The busiest parts of a stratum are named where they
stand; every other is named when it is pointed at.

THE CARDS. One for each part, shown when it is the page's target and hidden otherwise, so the map holds every part and
shows one at a time: what it is, what it is held to, and what it touches, each kind of relation a handful of its busiest
neighbours and a count of the rest. `dmcatalog --part <name>` gives any of them whole.

THE FINDINGS. What the catalogue found for a person to judge — candidates, never verdicts — each kind with its count and
a few examples.

No script and no inline style: the page's policy allows neither, so a card opens by its fragment (`:target`), and a
mark's size and colour are classes the stylesheet gives. It writes nothing and opens no network path.
"""
import html, json, os, re, subprocess, sys

esc = lambda s: html.escape(str(s), quote=False)                        # noqa: E731
attr = lambda s: html.escape(str(s), quote=True)                        # noqa: E731

# the strata, top to bottom: the chain the law draws first, then what stands beside it
CHAIN = ('manifesto', 'law', 'reasoning', 'journal', 'history')
BESIDE = ('guide', 'gate')
STRATUM_WORDS = {
    'manifesto': 'what daftar is for, and what it never does',
    'law': 'what is in force: the vocabulary, the model, how a write is made — and every term, registry and section of it',
    'reasoning': 'why the law says what it says, keyed by the path of what it explains',
    'journal': 'what each version of the law changed, and why',
    'history': 'the design steps before the reasoning was kept apart',
    'guide': 'written for the reader who arrives: how to start, the forms, the cookbook',
    'gate': 'the tools that judge, write and read, and the suites that hold them to it',
    'elsewhere': 'what the release carries that no layer of a garden holds: its pages, its licences, its own tests',
}
LAW_ITEMS = ('term', 'registry', 'section', 'profile', 'form', 'law')
FAMILY = {  # a part's kind -> the colour family the stylesheet gives it
    'term': 'law', 'registry': 'law', 'section': 'law', 'profile': 'law', 'form': 'law', 'law': 'law',
    'tool': 'tool', 'module': 'tool', 'hook': 'tool',
    'suite': 'suite', 'fixture': 'suite', 'workflow': 'suite',
    'document': 'doc', 'page': 'doc', 'template': 'doc',
}
REL = {  # relation -> (as its source says it, as its target does)
    'imports': ('imports', 'imported by'), 'runs': ('runs', 'run by'), 'mentions': ('mentions', 'mentioned in'),
    'names': ('names', 'named in'), 'explains': ('explains', 'explained by'), 'holds': ('holds', 'held by'),
    'uses': ('uses', 'used by'), 'covers': ('covers', 'covered by'), 'states': ('states', 'stated in'),
    'ships': ('ships', 'shipped by'),
}
FINDING_WORDS = {
    'unreferenced': 'items of the law that nothing references',
    'untested_tools': 'tools no suite imports, runs or names',
    'one_domain_many_names': 'one domain taken under two names whose meanings share their words',
    'odd_siblings': 'siblings shaped unlike the rest of their group',
    'one_name_many_items': 'names the law gives to more than one item',
    'own_bean_walks': 'files that list the beans themselves instead of reading them through the one garden model',
}
CHIPS = 8                      # the busiest neighbours a card names for each kind of relation; the rest are counted


def catalogue(checkout):
    r = subprocess.run([sys.executable, os.path.join(checkout, 'bin', 'dmcatalog.py'), '--json'], cwd=checkout,
                       capture_output=True, text=True, encoding='utf-8')
    if r.returncode:
        raise RuntimeError(f"bin/dmcatalog.py --json failed in {checkout}: {(r.stderr or r.stdout)[-400:]}")
    return json.loads(r.stdout)


def plural(k):
    return k[:-1] + 'ies' if k.endswith('y') else k if k.endswith('s') else k + 's'


def prose(s):
    """Words as the law writes them: a name in backticks is code."""
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', esc(s))


def slug(pid):
    return 'map-' + re.sub(r'[^a-z0-9]+', '-', pid.lower()).strip('-')


def short(pid):
    """A part as the map names it: a law item by its name, a file by its path."""
    return pid.split(':', 1)[1] if pid.split(':', 1)[0] in LAW_ITEMS + ('layer',) else pid


class Atlas:
    def __init__(self, cat):
        self.cat, self.parts = cat, cat['parts']
        self.out, self.inn = {}, {}
        for r in cat['relations']:
            self.out.setdefault(r['from'], []).append(r)
            self.inn.setdefault(r['to'], []).append(r)
        self.deg = {p: len(self.out.get(p, ())) + len(self.inn.get(p, ())) for p in self.parts}
        self.ids = {p: slug(p) for p in self.parts}
        if len(set(self.ids.values())) != len(self.ids):
            raise RuntimeError('two parts of the catalogue take one id on the map')

    def stratum(self, pid):
        p = self.parts[pid]
        if p['kind'] == 'layer':
            return None                                 # the strata themselves
        if p['kind'] in LAW_ITEMS:
            return 'law'
        lay = (p.get('contents') or {}).get('layer')
        return lay if lay in CHAIN + BESIDE else 'elsewhere'

    @staticmethod
    def size(d):
        return 1 if d <= 2 else 2 if d <= 8 else 3 if d <= 25 else 4 if d <= 80 else 5

    def mark(self, pid, named):
        p = self.parts[pid]
        fam = FAMILY.get(p['kind'], 'other')
        label = f"{short(pid)}, a {p['kind']}, {self.deg[pid]} relations"
        name = f'<span class="nm">{esc(short(pid))}</span>' if named else ''
        return (f'<li><a class="mk f-{fam} s{self.size(self.deg[pid])}{" named" if named else ""}" '
                f'href="#{self.ids[pid]}" title="{attr(label)}" aria-label="{attr(label)}">{name}</a></li>')

    def field(self):
        by = {}
        for pid in self.parts:
            s = self.stratum(pid)
            if s:
                by.setdefault(s, []).append(pid)
        rows = []
        for s in CHAIN + BESIDE + ('elsewhere',):
            ps = sorted(by.get(s, ()), key=lambda x: (FAMILY.get(self.parts[x]['kind'], 'zz'), self.parts[x]['kind'],
                                                      -self.deg[x], x))
            if not ps:
                continue
            top = set(sorted(ps, key=lambda x: -self.deg[x])[:5])
            kinds = {}
            for x in ps:
                kinds[self.parts[x]['kind']] = kinds.get(self.parts[x]['kind'], 0) + 1
            said = ', '.join(f"{n} {plural(k) if n > 1 else k}" for k, n in sorted(kinds.items(), key=lambda kv: -kv[1]))
            lay = f'layer:{s}'
            head = (f'<a href="#{self.ids[lay]}">{esc(s)}</a>' if lay in self.parts else esc(s))
            rows.append(f'<section class="stratum st-{s}" aria-label="{attr(s)}: {len(ps)} parts">'
                        f'<header><h4>{head}</h4><p>{prose(STRATUM_WORDS.get(s, ""))}</p><p class="said">{esc(said)}</p></header>'
                        f'<ul class="marks">{"".join(self.mark(x, x in top) for x in ps)}</ul></section>')
        return '<div class="field">' + ''.join(rows) + '</div>'

    def chips(self, pids):
        pids = sorted(set(pids), key=lambda x: (-self.deg.get(x, 0), x))
        shown = ''.join(f'<a href="#{self.ids[x]}">{esc(short(x))}</a>' for x in pids[:CHIPS] if x in self.ids)
        rest = len(pids) - min(len(pids), CHIPS)
        return shown + (f'<span class="more">and {rest} more</span>' if rest > 0 else '')

    def what(self, pid):
        p, c = self.parts[pid], self.parts[pid].get('contents') or {}
        said = c.get('meaning') or c.get('summary') or ''
        bits = [f'<p class="what">{prose(said)}</p>'] if said else []
        k = p['kind']
        if k == 'term' and isinstance(c.get('attributes'), dict) and c['attributes']:
            bits.append('<p class="holds"><span>its attributes</span> ' + ''.join(
                f'<code title="{attr(d)}">{esc(a)}</code>' for a, d in c['attributes'].items()) + '</p>')
        elif k == 'registry' and c.get('row_names'):
            names = c['row_names']
            bits.append(f'<p class="holds"><span>{esc(c.get("rows", len(names)))} rows</span> '
                        + ''.join(f'<code>{esc(n)}</code>' for n in names[:12])
                        + (f'<span class="more">and {len(names) - 12} more</span>' if len(names) > 12 else '') + '</p>')
        elif k == 'section' and c.get('keys'):
            bits.append('<p class="holds"><span>it says</span> ' + ''.join(f'<code>{esc(x)}</code>' for x in c['keys']) + '</p>')
        elif k == 'profile' and c.get('terms'):
            bits.append('<p class="holds"><span>its terms</span> ' + ''.join(
                f'<a href="#{self.ids["term:" + t]}">{esc(t)}</a>' if 'term:' + t in self.ids else f'<code>{esc(t)}</code>'
                for t in c['terms']) + '</p>')
        elif c.get('headings'):
            bits.append('<p class="holds"><span>its headings</span> ' + ''.join(
                f'<code>{esc(h)}</code>' for h in c['headings'][:10])
                + (f'<span class="more">and {len(c["headings"]) - 10} more</span>' if len(c['headings']) > 10 else '') + '</p>')
        ck = p.get('checklists') or {}
        held = [f"{len(ck.get('rules') or [])} rules the gate reads" if ck.get('rules') else '',
                f"{len(ck.get('checklist') or [])} checklist items" if ck.get('checklist') else '',
                f"{len(ck.get('checks') or [])} suite checks" if ck.get('checks') else '']
        held = [h for h in held if h]
        if held:
            bits.append(f'<p class="held"><span>held to</span> {esc("; ".join(held))}</p>')
        return ''.join(bits)

    def card(self, pid):
        p = self.parts[pid]
        groups = []
        for rel, (o_word, i_word) in REL.items():
            o = [r['to'] for r in self.out.get(pid, ()) if r['rel'] == rel]
            i = [r['from'] for r in self.inn.get(pid, ()) if r['rel'] == rel]
            if o:
                groups.append(f'<div class="rel"><h5>{esc(o_word)} <span>{len(set(o))}</span></h5><p>{self.chips(o)}</p></div>')
            if i:
                groups.append(f'<div class="rel"><h5>{esc(i_word)} <span>{len(set(i))}</span></h5><p>{self.chips(i)}</p></div>')
        where = self.stratum(pid) or 'the map itself'
        name = short(pid)
        return (f'<article class="pc" id="{self.ids[pid]}" aria-labelledby="{self.ids[pid]}-h">'
                f'<a class="close" href="#map">Back to the map</a>'
                f'<h4 id="{self.ids[pid]}-h">{esc(name)}</h4>'
                f'<p class="kind">a {esc(p["kind"])}, in {esc(where)}</p>'
                + self.what(pid) + ''.join(groups) +
                f'<p class="whole">Everything about it: <code>python3 bin/dmcatalog.py --part {esc(name)}</code></p>'
                '</article>')

    def cards(self):
        order = sorted(self.parts, key=lambda x: (self.stratum(x) or '', x))
        return '<div class="pcs">' + ''.join(self.card(p) for p in order) + '</div>'

    def findings(self):
        out = []
        for k, rows in self.cat.get('findings', {}).items():
            ex = []
            for r in rows[:6]:
                if isinstance(r, str):
                    ex.append(r)
                elif isinstance(r, dict):
                    ex.append(r.get('part') or r.get('file') or r.get('name') or
                              ' / '.join(r.get('names') or []) or next(iter(r.values()), ''))
            def chip(x):
                base = x.split('[', 1)[0]           # a row of a registry is shown on its registry's card
                if x in self.ids or base in self.ids:
                    return f'<a href="#{self.ids.get(x) or self.ids[base]}">{esc(short(x))}</a>'
                return f'<code>{esc(x)}</code>'
            chips = ''.join(chip(x) for x in ex)
            more = f'<span class="more">and {len(rows) - len(ex)} more</span>' if len(rows) > len(ex) else ''
            out.append(f'<div class="finding"><p class="n">{len(rows)}</p><p class="w">{esc(FINDING_WORDS.get(k, k))}</p>'
                       f'<p class="ex">{chips}{more}</p></div>')
        return '<div class="findings">' + ''.join(out) + '</div>'

    def counts(self):
        c = self.cat.get('catalogue', {})
        return (f"{c.get('parts', len(self.parts))} parts and {c.get('relations', 0)} relations, "
                f"daftar {c.get('release', '')}, the law {c.get('law', '')}")


def render(checkout, what):
    a = Atlas(catalogue(checkout))
    return {'field': a.field, 'cards': a.cards, 'findings': a.findings, 'counts': a.counts}[what]()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__.split('\n\n')[1])
    print(render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'field'))
