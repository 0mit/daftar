#!/usr/bin/env python3
"""site/terminology.py — the terminology page's body, read from a checkout's seed and never written by hand.

    python3 site/terminology.py <checkout> [--release <tag>] [--out <file.html>]

WHAT IT READS. The five layers the law's `layers` names, as a checkout holds them: the manifesto (MANIFESTO.md, one
clause to a key), the law (seed/std-vocab.md — its terms, the terms its profiles add, its registries and their rows,
its aspects and figures, its systems, its forms — and the law's documents MODEL.md, CHECKLIST.md and MERGE.md), the
reasoning (seed/RATIONALE.md, one entry to the path of the item it supports), the journal (seed/CHANGELOG.md, one
entry to a version) and the history (what the seed keeps of it: the names the law retired).

WHAT IT DRAWS. A relation only where the seed's data states it, each with the reason the seed gives beside it:
  in            an attribute's domain: a registry, an aspect, a system, a sibling's registry (`form_of`,
                `registry_from`), a term's keys (`key_of`), a value type, a quantity — the reason is the attribute's
                own `meaning`
  link          a row of `registry_links`: one registry's field names rows of another — its `why`
  resolves_through, within, same_ground_as, datum, cells_in, boundaries_in
                between systems and schemes, or a system and the registry its cells come from — the row's `meaning`
  inverse_of    a relation that mirrors another
  figure, poles, complement
                an aspect's figure; each axis of poles it is oriented by — the figure's `meaning`; and a position's
                mutual complement — the position's `meaning`
  beneath       a layer on the one beneath it — the `why` of the registry link that declares it
  carries       a file of the law or the reasoning that names a manifesto clause (`manifesto: <key>`) — the line itself
  reason        a RATIONALE entry naming its item — the entry, behind a closed disclosure
Every relation is an element with `data-rel`, `data-from` and `data-to`; test/terminology.py reads them back and checks
each against the law by its own reading. The journal entries that name a term (`name` in code, in seed/CHANGELOG.md)
sit behind it, closed, and open as popovers: HTML only, since the site's pages run no script.

Exit 0 written; 2 the checkout has no seed/std-vocab.md or PyYAML is missing.
"""
import argparse, html, os, re, sys

LAW_DOCS = ('MODEL.md', 'CHECKLIST.md', 'MERGE.md')
GITHUB = 'https://github.com/0mit/daftar'
# the law's top-level mappings that are FORMS of a value or a record, and not sections of the schema language
FORM_SUFFIX = '_form'


def esc(s):
    return html.escape(str(s), quote=False)


def attr(s):
    return html.escape(str(s), quote=True)


def slug(*parts):
    return re.sub(r'[^a-z0-9-]+', '-', '-'.join(str(p) for p in parts).lower()).strip('-')


def inline(s):
    """Prose from the seed: escaped, with `code` spans kept as code."""
    return re.sub(r'`([^`]+)`', lambda m: '<code>%s</code>' % m.group(1), esc(' '.join(str(s).split())))


def front(text):
    parts = text.split('---\n')
    return parts[1] if text.startswith('---') and len(parts) > 2 else None


class Seed:
    """The five layers of one checkout, read once."""

    def __init__(self, root):
        import yaml
        self.root = root
        self.law_text = self.read('seed/std-vocab.md')
        self.law = yaml.safe_load(front(self.law_text)) or {}
        self.version = str(self.law.get('version', ''))
        self.lines = self.law_text.split('\n')
        self.spans = self._spans()
        self.items = {}           # entity id -> {kind, name, where, meaning, layer, ...}
        self.rels = []            # (rel, from, to, label, reason)
        self.read_law()
        self.read_manifesto()
        self.read_docs()
        self.read_rationale()
        self.read_changelog()

    def read(self, rel):
        p = os.path.join(self.root, rel)
        return open(p, encoding='utf-8').read() if os.path.isfile(p) else ''

    # ---------------------------------------------------------------- where in the law file an item is written
    def _spans(self):
        """Each top-level key's line range in seed/std-vocab.md (1-based, inclusive)."""
        starts = [(i + 1, m.group(1)) for i, ln in enumerate(self.lines) if (m := re.match(r'^([a-z_]+):', ln))]
        out = {}
        for n, (line, key) in enumerate(starts):
            out[key] = (line, (starts[n + 1][0] - 1) if n + 1 < len(starts) else len(self.lines))
        return out

    def line_of(self, section, keyfield=None, key=None):
        a, b = self.spans.get(section, (None, None))
        if a is None or key is None:
            return a
        pat = re.compile(r'(?:^\s*-\s*|\{\s*|,\s*|^\s+)%s:\s*"?%s"?\s*(?:[,}#]|$)' % (re.escape(keyfield), re.escape(str(key))))
        for i in range(a - 1, b):
            if pat.search(self.lines[i]):
                return i + 1
        return a

    def add(self, eid, **kw):
        kw.setdefault('layer', 'law')
        self.items[eid] = kw
        return eid

    def rel(self, rel, frm, to, label='', reason=''):
        self.rels.append((rel, frm, to, label, reason))

    # ---------------------------------------------------------------- the law
    def read_law(self):
        L = self.law
        for key, val in L.items():
            if key == 'version':
                continue
            where = ('seed/std-vocab.md', self.line_of(key))
            if isinstance(val, dict) and key != 'profiles':
                kind = 'form' if key.endswith(FORM_SUFFIX) else 'section'
                self.add(f'{kind}:{key}', kind=kind, name=key, where=where, meaning=val.get('meaning', ''),
                         keys=list(val))
            elif isinstance(val, list) and key not in ('terms',):
                keyfield = next((next(iter(r)) for r in val if isinstance(r, dict)), None)
                self.add(f'registry:{key}', kind='registry', name=key, where=where, keyfield=keyfield,
                         rows=[r.get(keyfield) if isinstance(r, dict) else r for r in val])
                for r in val:
                    if isinstance(r, dict) and keyfield in r:
                        self.add(f'row:{key}:{r[keyfield]}', kind='row', name=str(r[keyfield]), registry=key,
                                 where=('seed/std-vocab.md', self.line_of(key, keyfield, r[keyfield])),
                                 meaning=r.get('meaning') or r.get('why') or r.get('sense') or r.get('instead') or '')
        for t in L.get('terms', []):
            self.term(t, None)
        for prof, p in (L.get('profiles') or {}).items():
            self.add(f'profile:{prof}', kind='profile', name=prof, where=('seed/std-vocab.md', self.line_of('profiles', 'profiles', None) or self.spans.get('profiles', (None,))[0]),
                     meaning=p.get('meaning', '') if isinstance(p, dict) else '')
            for t in (p.get('terms') or []) if isinstance(p, dict) else []:
                self.term(t, prof)
        self.relations()

    def term(self, t, profile):
        name = t['term']
        where = ('seed/std-vocab.md', self.line_of('profiles' if profile else 'terms', 'term', name))
        self.add(f'term:{name}', kind='term', name=name, where=where, meaning=t.get('meaning', ''), profile=profile,
                 raw=t)

    def relations(self):
        L = self.law
        # `in:` — every attribute record of every term, form and section
        def walk(node, owner, path):
            if isinstance(node, dict):
                dom = node.get('in')
                if isinstance(dom, dict):
                    self.domain(dom, owner, path, node.get('meaning', ''), node)
                elif dom == 'bean_id' or dom is None:
                    pass
                for k, v in node.items():
                    if k in ('in',) and not isinstance(v, dict):
                        continue
                    walk(v, owner, path + [str(k)] if k not in ('attrs', 'schema', 'entries', 'in') else path)
            elif isinstance(node, list):
                for v in node:
                    walk(v, owner, path)
        for eid, it in list(self.items.items()):
            if it['kind'] == 'term':
                walk(it['raw'].get('schema') or {}, eid, [])
                inv = (it['raw'].get('schema') or {}).get('inverse_of') or it['raw'].get('inverse_of')
                if inv:
                    to = inv['term'] if isinstance(inv, dict) else inv
                    self.rel('inverse_of', eid, f'term:{to}', 'mirrors', it['meaning'])
            elif it['kind'] in ('form', 'section'):
                walk(L[it['name']], eid, [])
            elif it['kind'] == 'row' and it['registry'] == 'operations':
                walk(next(r for r in L['operations'] if r.get('op') == it['name']), eid, [])
        # registry links
        for r in L.get('registry_links') or []:
            if isinstance(r, dict) and r.get('from') and r.get('to'):
                self.rel('link', self.registry_id(r['from']), self.registry_id(r['to']), f'{r.get("field")} → {r.get("take")}',
                         r.get('why', ''))
        # between systems and schemes
        for reg, kf in (('anchor_systems', 'system'), ('knowledge_schemes', 'scheme')):
            for r in L.get(reg) or []:
                if not isinstance(r, dict) or kf not in r:
                    continue
                me = f'row:{reg}:{r[kf]}'
                for k in ('resolves_through', 'within', 'same_ground_as'):
                    v = r.get(k)
                    for to in (v if isinstance(v, list) else [v] if v else []):
                        self.rel(k, me, self.system_id(to), k, r.get('meaning', ''))
                if r.get('datum') is not None:
                    d = r['datum']
                    to = d if isinstance(d, str) else (d.get('on') or d.get('of') or d.get('system') or '')
                    to = f'row:gene:{to}' if f'row:gene:{to}' in self.items else self.system_id(to) \
                        if to != 'being' else me   # `being`: another being's own position, named by the value
                    self.rel('datum', me, to, 'datum', r.get('meaning', ''))
                for k in ('cells_in', 'boundaries_in'):
                    v = r.get(k)
                    if isinstance(v, dict) and v.get('registry'):
                        self.rel(k, me, self.registry_id(v['registry']), f'{k} → {v.get("take")}', r.get('meaning', ''))
        # aspects: figure and complements
        for a in L.get('aspects') or []:
            if not isinstance(a, dict):
                continue
            me = f'row:aspects:{a["aspect"]}'
            if a.get('figure'):
                self.rel('figure', me, f'row:figures:{a["figure"]}', 'is a', a.get('meaning', ''))
            fig = next((f for f in L.get('figures') or [] if isinstance(f, dict) and f.get('figure') == a.get('figure')), {})
            poles = a.get('poles') or []
            for pair in ([poles] if poles and all(isinstance(x, str) for x in poles) else poles):   # one axis, or several
                if isinstance(pair, list) and len(pair) == 2:
                    self.rel('poles', me, me, f'{pair[0]} ↔ {pair[1]}', fig.get('meaning', ''))
            for p in a.get('positions') or []:
                if isinstance(p, dict) and p.get('complement'):
                    self.rel('complement', me, me, f'{p["position"]} ↔ {p["complement"]}', p.get('meaning', ''))
        # layers
        why = next((r.get('why', '') for r in L.get('registry_links') or []
                    if isinstance(r, dict) and (r.get('from'), r.get('field')) == ('layers', 'beneath')), '')
        for lay in L.get('layers') or []:
            if isinstance(lay, dict) and lay.get('beneath'):
                self.rel('beneath', f'row:layers:{lay["layer"]}', f'row:layers:{lay["beneath"]}', 'stands on', why)

    def registry_id(self, name):
        if f'registry:{name}' in self.items:
            return f'registry:{name}'
        for r in self.law.get('registry_files') or []:
            if isinstance(r, dict) and r.get('registry') == name:
                return f'row:registry_files:{name}'
        return f'registry:{name}'

    def system_id(self, name):
        for reg in ('anchor_systems', 'knowledge_schemes'):
            if f'row:{reg}:{name}' in self.items:
                return f'row:{reg}:{name}'
        return f'row:anchor_systems:{name}'

    def domain(self, dom, owner, path, meaning, node):
        label = '.'.join(path) or '(entry)'
        if dom.get('registry'):
            self.rel('in', owner, self.registry_id(dom['registry']), f'{label} ∈ {dom["registry"]}', meaning)
        if dom.get('aspect'):
            self.rel('in', owner, f'row:aspects:{dom["aspect"]}', f'{label} on {dom["aspect"]}', meaning)
        if dom.get('system'):
            self.rel('in', owner, self.system_id(dom['system']), f'{label} in {dom["system"]}', meaning)
        if dom.get('form_of'):
            self.rel('in', owner, self.registry_id(dom['form_of']), f'{label}: form of {dom["form_of"]}, by {dom.get("keyed_by")}', meaning)
        if dom.get('registry_from'):
            self.rel('in', owner, owner, f'{label}: a row of the registry `{dom["registry_from"]}` names', meaning)
        if dom.get('key_of'):
            self.rel('in', owner, f'term:{dom["key_of"]}', f'{label}: a key of {dom["key_of"]}', meaning)
        if dom.get('type'):
            self.rel('in', owner, f'row:value_types:{dom["type"]}', f'{label}: {dom["type"]}', meaning)
        if dom.get('quantity') == 'any':
            self.rel('in', owner, owner, f'{label}: any quantity', meaning)
        elif dom.get('quantity'):
            self.rel('in', owner, f'row:quantities:{dom["quantity"]}', f'{label}: a {dom["quantity"]}', meaning)

    # ---------------------------------------------------------------- the manifesto
    def read_manifesto(self):
        t = self.read('MANIFESTO.md')
        group, lines = None, t.split('\n')
        for i, ln in enumerate(lines):
            if ln.startswith('## '):
                group = ln[3:].strip()
            elif ln.startswith('### '):
                key = ln[4:].strip()
                body = []
                for nxt in lines[i + 1:]:
                    if nxt.startswith('#'):
                        break
                    body.append(nxt)
                self.add(f'clause:{key}', kind='clause', name=key, group=group, layer='manifesto',
                         where=('MANIFESTO.md', i + 1), meaning=' '.join(' '.join(body).split()))
        cite = re.compile(r'\bmanifesto:\s*([a-z][a-z-]*(?:,\s*[a-z][a-z-]*)*)')
        for f in ('seed/std-vocab.md',) + LAW_DOCS + ('seed/RATIONALE.md',):
            for n, ln in enumerate(self.read(f).split('\n'), 1):
                for m in cite.finditer(ln):
                    for k in re.split(r',\s*', m.group(1)):
                        if f'clause:{k}' in self.items:
                            self.rel('carries', f'doc:{f}:{n}', f'clause:{k}', f'{f}:{n}', ln.strip())

    # ---------------------------------------------------------------- the law's documents
    def read_docs(self):
        for f in LAW_DOCS:
            for n, ln in enumerate(self.read(f).split('\n'), 1):
                m = re.match(r'^(#{2,3}) (.+)$', ln)
                if m:
                    self.add(f'heading:{f}:{n}', kind='heading', name=m.group(2).strip(), doc=f, depth=len(m.group(1)),
                             where=(f, n), meaning='')

    # ---------------------------------------------------------------- the reasoning
    def item_of_key(self, key):
        """The law item a RATIONALE key names: its path's first step, and the row it selects."""
        d = re.match(r'^doc:([A-Z]+\.md)(?:#(.+))?$', key)
        if d:
            f, h = d.groups()
            if f == 'MANIFESTO.md':
                return f'clause:{h}' if f'clause:{h}' in self.items else None
            for e, it in self.items.items():
                if it['kind'] == 'heading' and it['doc'] == f and (h is None or it['name'] == h or
                                                                  re.match(r'%s[.\s]' % re.escape(h), it['name'])):
                    return e
            return None
        m = re.match(r'^([a-z_]+)(?:\[([^\]]+)\])?', key)
        if not m:
            return None
        top, sel = m.group(1), m.group(2)
        if top == 'terms' and sel:
            return f'term:{sel}' if f'term:{sel}' in self.items else None
        if top == 'profiles':
            m2 = re.match(r'^profiles\.([a-z_]+)(?:\.terms\[([^\]]+)\])?', key)
            if m2 and m2.group(2) and f'term:{m2.group(2)}' in self.items:
                return f'term:{m2.group(2)}'
            return f'profile:{m2.group(1)}' if m2 and f'profile:{m2.group(1)}' in self.items else None
        if sel and f'row:{top}:{sel}' in self.items:
            return f'row:{top}:{sel}'
        for k in (f'registry:{top}', f'form:{top}', f'section:{top}'):
            if k in self.items:
                return k
        return None

    def read_rationale(self):
        t = self.read('seed/RATIONALE.md')
        heads = [(m.start(), m.group(1), t.count('\n', 0, m.start()) + 1) for m in re.finditer(r'(?m)^## (.+)$', t)]
        for n, (pos, key, line) in enumerate(heads):
            end = heads[n + 1][0] if n + 1 < len(heads) else len(t)
            body = t[pos:end].split('\n', 1)[1].strip() if '\n' in t[pos:end] else ''
            eid, k = f'reason:{key}', 1
            while eid in self.items:        # a key written twice keeps both entries; the second is numbered
                k += 1
                eid = f'reason:{key}#{k}'
            eid = self.add(eid, kind='reason', name=key, layer='reasoning', where=('seed/RATIONALE.md', line),
                           meaning=body)
            item = self.item_of_key(key)
            self.items[eid]['item'] = item
            if item:
                self.rel('reason', eid, item, key, body.split('\n\n')[0])

    # ---------------------------------------------------------------- the journal
    def read_changelog(self):
        t = self.read('seed/CHANGELOG.md')
        lines = t.split('\n')
        starts = [i for i, ln in enumerate(lines) if ln.startswith('- **')]
        self.entries = []
        for n, i in enumerate(starts):
            j = starts[n + 1] if n + 1 < len(starts) else len(lines)
            body = '\n'.join(lines[i:j]).strip()
            m = re.match(r'- \*\*([^*]+)\*\*', body)
            head = m.group(1).rstrip('.') if m else f'entry {n + 1}'
            eid = self.add(f'entry:{n + 1}', kind='entry', name=head, layer='journal', where=('seed/CHANGELOG.md', i + 1),
                           meaning=body[2:], names=set(re.findall(r'`([a-z_][a-z0-9_-]*)', body)))
            self.entries.append(eid)

    def journal_of(self, name):
        return [e for e in self.entries if name in self.items[e]['names']]


# ==================================================================== rendering
def anchor(eid):
    """An id for an entity, one to one: letters, digits, `_` and `-` kept, `:` as `.`, and anything else as `~<hex>~`."""
    return 'tm-' + ''.join(c if re.match(r'[A-Za-z0-9_-]', c) else '.' if c == ':' else '~%x~' % ord(c) for c in eid)


class Page:
    def __init__(self, seed, release):
        self.s, self.release = seed, release
        self.out_rels = {}
        for r in seed.rels:
            self.out_rels.setdefault(r[1], []).append(r)
        self.in_rels = {}
        for r in seed.rels:
            if r[2] != r[1]:
                self.in_rels.setdefault(r[2], []).append(r)

    def src(self, where):
        f, n = where
        url = f'{GITHUB}/blob/{self.release}/{f}' + (f'#L{n}' if n else '')
        return '<a class="src" href="%s">%s%s</a>' % (attr(url), esc(f), f':{n}' if n else '')

    def ref(self, eid):
        it = self.s.items.get(eid)
        if it is None:
            return '<code>%s</code>' % esc(eid.split(':')[-1])
        if it['kind'] == 'row':
            return '<a href="#%s"><code>%s</code></a> <span class="muted">(%s)</span>' % (anchor(eid), esc(it['name']), esc(it['registry']))
        return '<a href="#%s"><code>%s</code></a>' % (anchor(eid), esc(it['name']))

    def rel_li(self, r, outgoing=True):
        rel, frm, to, label, reason = r
        other = to if outgoing else frm
        why = ' — <span class="why">%s</span>' % inline(reason) if reason and rel != 'reason' else ''
        return ('<li data-rel="%s" data-from="%s" data-to="%s"><span class="rk">%s</span> %s%s%s</li>'
                % (attr(rel), attr(frm), attr(to), esc(rel if outgoing else 'from'),
                   ('<code>%s</code> ' % esc(label)) if label and rel not in ('reason', 'carries') else '',
                   '' if other == (frm if outgoing else to) and rel in ('complement', 'poles', 'in') else ('→ ' if outgoing else '← ') + self.ref(other), why))

    def relations(self, eid):
        outs = [r for r in self.out_rels.get(eid, []) if r[0] != 'reason']
        ins = [r for r in self.in_rels.get(eid, []) if r[0] not in ('reason', 'carries')]
        if not outs and not ins:
            return ''
        parts = []
        if outs:
            parts.append('<ul class="rels">%s</ul>' % ''.join(self.rel_li(r) for r in outs))
        if ins:
            parts.append('<details class="back"><summary>named by %d</summary><ul class="rels">%s</ul></details>'
                         % (len(ins), ''.join(self.rel_li(r, False) for r in ins)))
        return ''.join(parts)

    def reasons(self, eid):
        rs = [r for r in self.in_rels.get(eid, []) if r[0] == 'reason']
        if not rs:
            return ''
        items = ''.join('<li data-rel="reason" data-from="%s" data-to="%s"><a href="#%s"><code>%s</code></a> — %s</li>'
                        % (attr(r[1]), attr(eid), anchor(r[1]), esc(r[3]), inline(r[4][:400] + ('…' if len(r[4]) > 400 else '')))
                        for r in rs)
        return '<details class="why"><summary>reasons (%d)</summary><ul>%s</ul></details>' % (len(rs), items)

    def journal(self, name):
        es = self.s.journal_of(name)
        if not es:
            return ''
        btns = ''.join('<li><button type="button" popovertarget="%s">%s</button></li>'
                       % (anchor(e), esc(self.s.items[e]['name'])) for e in es)
        return '<details class="jr"><summary>journal (%d)</summary><ul class="jl">%s</ul></details>' % (len(es), btns)

    def history(self, name):
        rows = [r for r in self.s.law.get('retired') or [] if isinstance(r, dict) and
                (r.get('name') == name or re.search(r'`%s`' % re.escape(name), str(r.get('instead', ''))))]
        if not rows:
            return ''
        return ('<p class="hist">history: %s</p>' % '; '.join('<code>%s</code> retired → %s' % (esc(r['name']), inline(r.get('instead', '')))
                                                              for r in rows))

    def entry(self, eid, title_html=None, body=''):
        it = self.s.items[eid]
        return ('<div class="term" id="%s"><div class="th"><h4>%s</h4> <span class="lay">%s</span> %s</div>%s%s%s%s%s%s</div>'
                % (anchor(eid), title_html or '<code>%s</code>' % esc(it['name']), esc(it['layer']), self.src(it['where']),
                   self.meaning(it), body, self.relations(eid),
                   self.reasons(eid), self.history(it['name']) if it['kind'] in ('term', 'registry', 'row', 'form') else '',
                   self.journal(it['name']) if it['kind'] in ('term', 'registry', 'form', 'section', 'row') else ''))

    def meaning(self, it):
        """A clause is quoted between the manifesto quote markers (bin/dmreview.py MANIFESTO_QUOTE): test/manifesto.py holds it to the clause word for
        word, and does not count it as a second statement."""
        if not it.get('meaning'):
            return ''
        p = '<p>%s</p>' % inline(it['meaning'])
        return '<!-- manifesto: %s -->%s<!-- /manifesto -->' % (it['name'], p) if it['kind'] == 'clause' else p

    # ---------------------------------------------------------------- sections
    def html(self):
        s = self.s
        by = lambda k: [e for e, it in s.items.items() if it['kind'] == k]
        counts = {k: len(by(k)) for k in ('clause', 'term', 'registry', 'row', 'form', 'section', 'heading', 'reason', 'entry')}
        out = []
        out.append('<p class="lede">Every word daftar\'s seed uses, in the five layers it stands on, and every relation between '
                   'them that the seed itself states, each with the reason it gives. Read from the seed of daftar '
                   '<code>%s</code> (std-vocab <code>%s</code>) by <code>site/terminology.py</code>; nothing here is written '
                   'by hand.</p>' % (esc(self.release), esc(s.version)))
        out.append('<p class="meta">%d manifesto clauses · %d terms · %d registries with %d rows · %d forms · %d sections of the '
                   'schema language · %d headings of the law\'s documents · %d reasons · %d journal entries · %d relations</p>'
                   % (counts['clause'], counts['term'], counts['registry'], counts['row'], counts['form'], counts['section'],
                      counts['heading'], counts['reason'], counts['entry'], len(s.rels)))
        out.append('<nav class="toc" aria-label="on this page"><ol>%s</ol></nav>' % ''.join(
            '<li><a href="#%s">%s</a></li>' % (i, t) for i, t in (
                ('layers', 'The layers'), ('manifesto', 'Manifesto'), ('terms', 'Law: terms'), ('aspects', 'Law: aspects and figures'),
                ('systems', 'Law: systems'), ('forms', 'Law: forms and the schema language'), ('registries', 'Law: registries'),
                ('documents', 'Law: its documents'), ('reasoning', 'Reasoning'), ('journal', 'Journal'), ('history', 'History'))))
        out.append(self.sec_layers())
        out.append(self.sec_manifesto())
        out.append(self.sec_terms())
        out.append(self.sec_registry('aspects', 'Law: aspects and figures', ['aspects', 'figures'],
                                     'Where a value is a position: the aspects, the figure each is, and each position with its mutual complement.'))
        out.append(self.sec_registry('systems', 'Law: systems', ['anchor_systems', 'knowledge_schemes'],
                                     'The systems a position is written in, and the published schemes a code is taken from: what each resolves through, lies within, shares ground with, and where its cells and boundaries come from.'))
        out.append(self.sec_forms())
        rest = [e for e in by('registry') if s.items[e]['name'] not in ('aspects', 'figures', 'anchor_systems', 'knowledge_schemes', 'layers')]
        out.append(self.sec_registry('registries', 'Law: registries', [s.items[e]['name'] for e in rest],
                                     'Every other table of the law: its rows are the values a position may take.'))
        out.append(self.sec_documents())
        out.append(self.sec_reasoning())
        out.append(self.sec_journal())
        out.append(self.sec_history())
        return '\n'.join(out)

    def sec_layers(self):
        s = self.s
        rows = [e for e in s.items if e.startswith('row:layers:')]
        five = [e for e in rows if s.items[e]['name'] in ('manifesto', 'law', 'reasoning', 'journal', 'history')]
        body = ''.join(self.entry(e) for e in five)
        others = ''.join(self.entry(e) for e in rows if e not in five)
        if 'registry:layers' not in s.items:   # a law older than its `layers` table
            return ('<section aria-labelledby="layers"><h2 id="layers">The layers</h2><p class="measure">This release\'s law '
                    'does not yet name its layers in a table: the manifesto, the law, the reasoning, the journal and the '
                    'history below are the files this checkout holds.</p></section>')
        reg = s.items['registry:layers']
        return ('<section aria-labelledby="layers"><h2 id="layers">The layers</h2><div class="reg" id="%s"><p class="measure">The '
                'five layers of daftar\'s own words, each on the one beneath, as the law\'s <code>layers</code> table states them; '
                'the other rows place what is not daftar\'s own words. %s</p>%s%s</div>%s<details><summary>the other %d places the '
                'law names</summary>%s</details></section>'
                % (anchor('registry:layers'), self.src(reg['where']), self.relations('registry:layers'),
                   self.reasons('registry:layers'), body, len(rows) - len(five), others))

    def sec_manifesto(self):
        s = self.s
        groups = {}
        for e, it in s.items.items():
            if it['kind'] == 'clause':
                groups.setdefault(it['group'], []).append(e)
        parts = []
        for g, es in groups.items():
            items = []
            for e in es:
                carried = [r for r in s.rels if r[0] == 'carries' and r[2] == e]
                c = ('<details class="back"><summary>carried in %d places</summary><ul class="rels">%s</ul></details>'
                     % (len(carried), ''.join('<li data-rel="carries" data-from="%s" data-to="%s">%s — <span class="why">%s</span></li>'
                                              % (attr(r[1]), attr(e), self.src(self.cite_where(r[1])), esc(r[4][:220]))
                                              for r in carried))) if carried else ''
                items.append(self.entry(e, body=c))
            parts.append('<h3>%s</h3>%s' % (esc(g), ''.join(items)))
        return ('<section aria-labelledby="manifesto"><h2 id="manifesto">Manifesto</h2>%s</section>'
                % (''.join(parts) or '<p class="measure">This release carries no <code>MANIFESTO.md</code>.</p>'))

    def sec_terms(self):
        s = self.s
        terms = [e for e, it in s.items.items() if it['kind'] == 'term']
        core = [e for e in terms if not s.items[e]['profile']]
        prof = {}
        for e in terms:
            if s.items[e]['profile']:
                prof.setdefault(s.items[e]['profile'], []).append(e)
        parts = ['<h3>In every garden</h3>', ''.join(self.entry(e) for e in sorted(core, key=lambda e: s.items[e]['name']))]
        for p, es in prof.items():
            parts.append('<h3 id="%s">Profile <code>%s</code></h3><p class="measure">%s</p>%s'
                         % (anchor('profile:' + p), esc(p), inline(s.items[f'profile:{p}']['meaning']),
                            ''.join(self.entry(e) for e in es)))
        return ('<section aria-labelledby="terms"><h2 id="terms">Law: terms</h2><p class="measure">What a bean may say: each term '
                'of <code>seed/std-vocab.md</code>, and the terms a profile adds for a garden that extends it.</p>%s</section>'
                % ''.join(parts))

    @staticmethod
    def cite_where(did):
        f, n = did[len('doc:'):].rsplit(':', 1)
        return f, int(n)

    def rows_table(self, reg):
        s = self.s
        es = [e for e in s.items if e.startswith(f'row:{reg}:')]
        return ''.join(self.entry(e) for e in es)

    def sec_registry(self, sid, title, regs, lede):
        s = self.s
        parts = []
        for r in regs:
            eid = f'registry:{r}'
            if eid not in s.items:
                continue
            it = s.items[eid]
            n = len([e for e in s.items if e.startswith(f'row:{r}:')])
            parts.append('<div class="reg" id="%s"><h3><code>%s</code></h3><p class="meta">%d rows, keyed by <code>%s</code> · %s</p>%s%s%s<details%s><summary>its rows</summary>%s</details></div>'
                         % (anchor(eid), esc(r), n, esc(it.get('keyfield')), self.src(it['where']), self.relations(eid),
                            self.reasons(eid), self.journal(r), '', self.rows_table(r)))
        return ('<section aria-labelledby="%s"><h2 id="%s">%s</h2><p class="measure">%s</p>%s</section>'
                % (sid, sid, esc(title), esc(lede), ''.join(parts)))

    def sec_forms(self):
        s = self.s
        es = [e for e, it in s.items.items() if it['kind'] in ('form', 'section')]
        body = ''.join(self.entry(e, body='<p class="meta">keys: %s</p>' % ', '.join('<code>%s</code>' % esc(k) for k in s.items[e]['keys']))
                       for e in es)
        return ('<section aria-labelledby="forms"><h2 id="forms">Law: forms and the schema language</h2><p class="measure">The shapes a '
                'value or a record takes, and the sections of the law that are not tables.</p>%s</section>' % body)

    def sec_documents(self):
        s = self.s
        parts = []
        for f in LAW_DOCS:
            hs = [e for e, it in s.items.items() if it['kind'] == 'heading' and it['doc'] == f]
            li = ''.join('<li class="d%d" id="%s">%s %s%s</li>' % (s.items[e]['depth'], anchor(e), inline(s.items[e]['name']),
                                                                   self.src(s.items[e]['where']), self.reasons(e)) for e in hs)
            parts.append('<h3><code>%s</code></h3><ul class="heads">%s</ul>' % (esc(f), li))
        return ('<section aria-labelledby="documents"><h2 id="documents">Law: its documents</h2><p class="measure">The law in prose: '
                'the model, the checklist and the merge, by their headings.</p>%s</section>' % ''.join(parts))

    def sec_reasoning(self):
        s = self.s
        es = [e for e, it in s.items.items() if it['kind'] == 'reason']
        loose = [e for e in es if not s.items[e].get('item')]
        li = ''.join('<li id="%s"><details><summary><code>%s</code>%s</summary><div class="rtext">%s</div> %s</details></li>'
                     % (anchor(e), esc(s.items[e]['name']),
                        (' → ' + self.ref(s.items[e]['item'])) if s.items[e].get('item') else ' <span class="muted">(an item this page does not list)</span>',
                        '<br>'.join(inline(p) for p in s.items[e]['meaning'].split('\n\n')), self.src(s.items[e]['where'])) for e in es)
        return ('<section aria-labelledby="reasoning"><h2 id="reasoning">Reasoning</h2><p class="measure">Why the law is as it is: '
                '<code>seed/RATIONALE.md</code>, one entry to the path of the item it supports. %d of %d name an item this page '
                'lists; each is also shown beside its item.</p><ul class="reasons">%s</ul></section>' % (len(es) - len(loose), len(es), li))

    def sec_journal(self):
        s = self.s
        if not s.entries:
            return ('<section aria-labelledby="journal"><h2 id="journal">Journal</h2><p class="measure">This release carries no '
                    '<code>seed/CHANGELOG.md</code>.</p></section>')
        btns = ''.join('<li><button type="button" popovertarget="%s">%s</button></li>' % (anchor(e), esc(s.items[e]['name']))
                       for e in s.entries)
        pops = ''.join('<div class="pop" popover id="%s"><div class="ph"><strong>%s</strong> %s <button type="button" popovertarget="%s" popovertargetaction="hide">close</button></div><div class="ptext">%s</div></div>'
                       % (anchor(e), esc(s.items[e]['name']), self.src(s.items[e]['where']), anchor(e),
                          inline(s.items[e]['meaning'])) for e in s.entries)
        return ('<section aria-labelledby="journal"><h2 id="journal">Journal</h2><p class="measure">What each version of the law '
                'changed, and why: <code>seed/CHANGELOG.md</code>. A term\'s own list is behind it, closed; each entry opens '
                'here.</p><ul class="jl">%s</ul>%s</section>' % (btns, pops))

    def sec_history(self):
        s = self.s
        rows = [r for r in s.law.get('retired') or [] if isinstance(r, dict)]
        li = ''.join('<li><a href="#%s"><code>%s</code></a> <span class="muted">(%s)</span> → %s</li>'
                     % (anchor('row:retired:' + str(r.get('name'))), esc(r.get('name')), esc(r.get('at', '')), inline(r.get('instead', '')))
                     for r in rows)
        return ('<section aria-labelledby="history"><h2 id="history">History</h2><p class="measure">The history layer holds the '
                'exact record a journal is written from — the commits, and the copies a bean points at. The seed carries no '
                'captures of its own; what it keeps of its history is the names it retired, each with what took its place.</p>'
                '<ul class="retired">%s</ul></section>' % li)


def render(root, release):
    return '<div class="tm">\n%s\n</div>' % Page(Seed(root), release).html()


def main():
    ap = argparse.ArgumentParser(description='Write the terminology page body from a checkout\'s seed.')
    ap.add_argument('checkout')
    ap.add_argument('--release', default='HEAD')
    ap.add_argument('--out')
    a = ap.parse_args()
    if not os.path.isfile(os.path.join(a.checkout, 'seed', 'std-vocab.md')):
        print(f'site/terminology.py: {a.checkout} has no seed/std-vocab.md', file=sys.stderr)
        return 2
    try:
        body = render(a.checkout, a.release)
    except ImportError:
        print('site/terminology.py: PyYAML is required', file=sys.stderr)
        return 2
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(body)
    else:
        sys.stdout.write(body)
    return 0


if __name__ == '__main__':
    sys.exit(main())
