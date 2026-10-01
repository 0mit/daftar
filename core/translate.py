#!/usr/bin/env python3
"""translate — today's law and beans (v0.48.0, std-vocab 32.0) written in the core's statements, by the `replaces` map.

    python3 core/translate.py levels > core/law/levels.yaml    # the bodies' levels, from the law's `complexity`
    python3 core/translate.py layers > core/law/layers.yaml    # the flow law's sources and the files' standing
    python3 core/translate.py kinds  > core/law/kinds.yaml     # the kinds, from the law's `gene`
    python3 core/translate.py garden <garden> <copy>           # a copy of the garden, its beans in statements, counted

THE LAW'S ROWS are generated from the law that has them, never typed. The detailed levels are rows of our knowledge tree
(Q3): `complexity` names `logos` where the core says `reason`, and `stands_on` where it says `stands`; the frame and λόγος
are the face's own. The kinds are `gene`: soma is a body, lekton the sayable, and `rung: logos` is `rung: reason`.

A GARDEN IS TRANSLATED INTO A COPY, never in place: every file is copied, the beans and mappings are rewritten in
statements, and VOCAB.md gains the rows the beans need (the garden's own kinds, the namespaces its names are given in, the
rows it added to the standards' tables). Each term goes the way verbs.yaml's `replaces` map sends it:

  provenance → a knowing act: observed → read, asserted-by-human → say, inferred and generated-by-tool → derive,
               stated-in-document → say; its `by` the bean the text names; an agent's, the session bean whose start
               and stop hold the act's moment, its reading then `derive` (ratified 2026-10-01); else `unknown` with the
               text as its note; its
               `at` the moment the clock wrote that day: the heading of the journal entry that names the bean, else the
               commit that first wrote the day. A party's own provenance is an act of its own.
  identity   → name (by the anchor's key as a namespace)        owned_by → own          responsibility → answer
  via        → come                  located_at, lives_in → be                           part_of → part
  instance_of, os → run              depends_on, consumes, reaches → need                knowledge → use, classify
  risks      → fail                  capabilities → can, on the two squares              roles → do
  produces   → produce (an artifact: a being, a position, or the words that say it)
  a unit     → its UCUM code (core/law/units.yaml), the law's English name attached there; a garden's own unit a row of
               VOCAB.md's `units`, its code composed from the law's (`gigabyte-per-day` is `GBy/d`)
  parties, over, words → agree       clauses → can, on the permission square            transactions → pay, bear
  endpoints  → serve                 timing start/stop → be, as presence                 workspace.opened_at → open

WHAT FITS NO VERB GOES TO `details`, WHOLE: a term no verb takes keeps its whole subtree there, under its name; what is
left of an entry a verb took stays there under the term and the statement's id. The front matter's comments go to
`details.comments`, each with the item it sat on.

THE COUNT IS THE PROOF. Every leaf of the old front matter — every value, as written — is given exactly one place: a
statement's role, the header, `details`, or a derivation the law makes (a bean's `nature` is its kind's; before the law,
the owner answers). The written file is read back and each place is checked to hold its value; the comments are counted
too. The command prints the count for the garden, and exits 1 if anything is unplaced or not found where it was put."""
import collections
import json
import os
import re
import shutil
import subprocess
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmparse  # noqa: E402 — today's reader of today's law, and the one splitter of a front matter
from core import frame  # noqa: E402

LAW = os.path.join(ROOT, 'seed', 'std-vocab.md')
FACE_LEVELS = {'space-time', 'logos'}       # the face's own: the frame of bodies, and reason
RENAMED = {'logos': 'reason'}               # the law's Greek word, where the core uses the role's
NATURES = {'soma': 'body', 'lekton': 'sayable'}
ACTS = {'observed': 'read', 'asserted-by-human': 'say', 'stated-in-document': 'say', 'inferred': 'derive',
        'generated-by-tool': 'derive'}
MODES = {'legal': 'law', 'technical': 'keeping', 'experience': 'meeting', 'financial': 'paying'}
PERMISSION = {'required': 'obligatory', 'omissible': 'omissible', 'permitted': 'permitted', 'forbidden': 'forbidden'}
FEASIBILITY = {'possible': 'possible', 'impossible': 'impossible', 'contingent': 'contingent'}
DOCUMENTS = ('beans', 'mappings')
AGENT = re.compile(r'\bagent\b', re.I)     # a provenance's `by` that names an agent, in the prose it is written in


def old_law(path=LAW):
    with open(path, encoding='utf-8') as fh:
        return dmparse.loads(dmparse.split_front_matter(fh.read())[0]) or {}


def _q(s):
    """A scalar as YAML writes it plainly where it can, quoted where it must be."""
    s = str(s)
    plain = s and all(c.isalnum() or c in '-_' for c in s) and s.lower() not in ('true', 'false', 'null', 'yes', 'no', 'on', 'off')
    return s if plain else '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


# ================================================================================================ the law's rows
def levels(law):
    """The text of core/law/levels.yaml: every level of `complexity` that is not the face's own, in its order."""
    out = ["# The bodies' levels: rows of our knowledge tree, the steps of the lines of bodies beside the face's own.",
           "# GENERATED by `python3 core/translate.py levels` from std-vocab " + str(law.get('version')) + "'s `complexity`;",
           "# a change is made there, or by a RULE-CHANGE that moves these rows, never by hand here.",
           "levels:"]
    for r in law.get('complexity') or []:
        lv = str(r['level'])
        if lv in FACE_LEVELS:
            continue
        stands = []
        for s in r.get('stands_on') or []:
            at = RENAMED.get(str(s['level']), str(s['level']))
            stands.append("{ at: %s, as: %s%s }" % (_q(at), _q(s['as']), f", while: {_q(s['while'])}" if s.get('while') else ''))
        out.append(f"  - {{ level: {_q(lv)}, line: {_q(RENAMED.get(str(r['line']), str(r['line'])))}, "
                   f"stands: [{', '.join(stands)}], meaning: {_q(r.get('meaning', ''))} }}")
    return '\n'.join(out) + '\n'


def layers(law, face_layers):
    """The text of core/law/layers.yaml: the flow law's sources (every layer of `layers` the face does not name) and the
    standing of files (each layer's `holds`), from the law's `layers`."""
    rows = [r for r in law.get('layers') or [] if isinstance(r, dict) and r.get('layer')]
    out = ["# The layers beside the face's own, and which files stand in which: rows of the flow law and of the layer map.",
           "# GENERATED by `python3 core/translate.py layers` from std-vocab " + str(law.get('version')) + "'s `layers`;",
           "# a change is made there, or by a RULE-CHANGE that moves these rows, never by hand here.",
           "flow_sources: [" + ', '.join(_q(r['layer']) for r in rows if r['layer'] not in face_layers) + "]",
           "standing:"]
    for r in rows:
        holds = [str(h) for h in r.get('holds') or []]
        if holds:
            out.append(f"  - {{ layer: {_q(r['layer'])}, holds: [{', '.join(_q(h) for h in holds)}] }}")
    return '\n'.join(out) + '\n'


def kind_row(g):
    """A row of `gene` (or a garden's `local_gene`) as a row of the core's kinds."""
    row = {'kind': str(g['genos']), 'nature': NATURES.get(str(g.get('of_nature')), str(g.get('of_nature')))}
    if g.get('level'):
        row['level'] = RENAMED.get(str(g['level']), str(g['level']))
    if g.get('rung'):
        row['rung'] = RENAMED.get(str(g['rung']), str(g['rung']))
    return row


def kinds(law):
    out = ["# The kinds of being a bean records, each with its nature, and its level and rung where it has them.",
           "# GENERATED by `python3 core/translate.py kinds` from std-vocab " + str(law.get('version')) + "'s `gene`;",
           "# a change is made there, or by a RULE-CHANGE that moves these rows, never by hand here.",
           "kinds:"]
    for g in law.get('gene') or []:
        row = kind_row(g)
        out.append("  - { " + ', '.join(f"{k}: {_q(v)}" for k, v in row.items()) + " }")
    return '\n'.join(out) + '\n'


# ================================================================================================ a garden's beans
def leaves(x, path=()):
    """[(path, text)] of every value in `x` (read as strings): a scalar, or an empty map or list, which says something."""
    if isinstance(x, dict):
        if not x:
            return [(path, '{}')]
        return [l for k, v in x.items() for l in leaves(v, path + (str(k),))]
    if isinstance(x, list):
        if not x:
            return [(path, '[]')]
        return [l for i, v in enumerate(x) for l in leaves(v, path + (i,))]
    return [(path, x)]


def at_path(x, path):
    for p in path:
        if isinstance(x, dict) and (p in x or str(p) in x):
            x = x[p] if p in x else x[str(p)]
        elif isinstance(x, list) and isinstance(p, int) and p < len(x):
            x = x[p]
        else:
            return KeyError
    return x


def slug(s):
    s = re.sub(r'[^a-z0-9_-]+', '-', str(s).lower()).strip('-')
    return s if s and re.match(r'^[a-z0-9]', s) else 'x-' + s


class Journal:
    """The moments the clock wrote: each journal heading's moment and the text of its entry."""

    def __init__(self, root):
        self.entries = []
        try:
            with open(os.path.join(root, 'log', 'journal.md'), encoding='utf-8') as fh:
                cur = None
                for line in fh.read().split('\n'):
                    if line.startswith('## '):
                        cur = [line[3:].split(' · ', 1)[0].strip(), line]
                        self.entries.append(cur)
                    elif cur is not None:
                        cur[1] += '\n' + line
        except OSError:
            pass
        self.root = root

    def moment(self, bid, path, day):
        """(moment, how) for a bean's day of knowing: the last heading that day whose entry names the bean; else the
        moment of the commit that first wrote the day into the file; else (None, why)."""
        day = str(day)
        named = re.compile(r'(?<![\w-])' + re.escape(bid) + r'(?![\w-])')
        hits = [m for m, t in self.entries if m.startswith(day + ' ') and named.search(t)]
        if hits:
            return frame.one_form(hits[-1]), 'journal'
        for how in (['-S', day], ['--diff-filter=A']):     # the commit that wrote the day, else the one that made the file
            r = subprocess.run(['git', '-C', self.root, 'log', '--follow', '--format=%cI', *how, '--', path],
                               capture_output=True, text=True)
            first = (r.stdout.strip().split('\n') or [''])[-1].strip() if r.returncode == 0 else ''
            if first.startswith(day):
                return first, 'commit'
        # A BEAN MADE LATER THAN ITS DAY (split out of another, its `as_of` carried): its statements entered it when
        # the file was made, and that commit's moment is the act's; the day it carried stays in details, not lost
        if first:
            return first, f"made {first[:10]}, after its as_of {day}, which stays in details"
        return None, f"no heading names {bid} on {day}, and no commit wrote {day} into it or made it"


class Bean2:
    """One bean being written in statements, with the place each old leaf went to."""

    def __init__(self, bid, old, ctx, path):
        self.id, self.old, self.ctx, self.path = bid, old, ctx, path
        self.statements, self.ids = [], set()
        self.details = {}
        self.placed = {}                 # old leaf path -> (where, expected text)
        self.notes = []                  # what the translation could not do: a problem
        self.carried = []                # what it did another way, losing nothing: for the report

    # -- placing
    def take(self, path, where, text=None):
        """Old leaf `path` goes to `where`, holding `text` (its own value, unless transformed)."""
        if path in self.placed:
            raise ValueError(f"{self.id}: {path} placed twice")
        v = at_path(self.old, path) if text is None else text
        self.placed[path] = (where, '{}' if v == {} else '[]' if v == [] else v)

    def new_id(self, want):
        i, base = slug(want), slug(want)
        n = 2
        while i in self.ids:
            i, n = f"{base}-{n}", n + 1
        self.ids.add(i)
        return i

    def add(self, verb, roles, sid=None):
        roles = dict(roles)
        if sid:
            roles = dict(id=sid, **{k: v for k, v in roles.items() if k != 'id'})
        self.statements.append((verb, roles))
        return len(self.statements) - 1

    def role(self, i, *role):
        return ('statement', i) + role

    def leftover(self, base, dest):
        """What is left under old `base` goes to details at `dest`: a subtree no verb took, whole and in its own shape;
        of one a verb took part of, each part that is left, under the same keys (a list's index read as a key)."""
        sub = at_path(self.old, base)
        mine = leaves(sub, base)
        if all(p in self.placed for p, _v in mine):
            return
        if dest and not any(p in self.placed for p, _v in mine):
            self._put(dest, sub)
            for p, _v in mine:
                self.take(p, ('details',) + dest + p[len(base):])
            return
        for k in (range(len(sub)) if isinstance(sub, list) else list(sub)):
            self.leftover(base + (k,), dest + (k,))

    def _put(self, dest, v):
        d = self.details
        for k in dest[:-1]:
            k = str(k)
            if k in d and not isinstance(d[k], dict):
                raise ValueError(f"{self.id}: details.{'.'.join(map(str, dest))} collides with a value")
            d = d.setdefault(k, {})
        last = str(dest[-1])
        if last in d:
            raise ValueError(f"{self.id}: details.{'.'.join(map(str, dest))} is written twice — an old key and a term's "
                             f"leftover share a name")
        d[last] = v


def being(ref, ctx):
    """The being a v0.48 reference names: `{bean: x}` → x; anything else None."""
    if isinstance(ref, dict) and set(ref) == {'bean'} and isinstance(ref['bean'], str):
        return ref['bean']
    return None


def position(system, at, ctx):
    """A position written short for a long one ({system, at}): bare where exactly that system reads it, else tagged;
    None where neither reads as that system."""
    for text in (str(at), f"{system}:{at}"):
        try:
            p = frame.read(text, ctx.systems, ctx.zone)
        except frame.Refused:
            continue
        if p.system == system:
            return text
    return None


def a_position(text, ctx):
    """`text` where it reads as a position, in whichever system reads it; None for an empty value (nobody said) or one
    no system reads, which then stays in details as written."""
    if not isinstance(text, str) or not text:
        return None
    try:
        frame.read(text, ctx.systems, ctx.zone)
        return text
    except frame.Refused:
        return None


def by_of(text, ctx):
    """(being, note) for a provenance's `by` prose: the bean it opens with, else unknown; the prose as the note, unless it
    is exactly the bean's id."""
    t = str(text)
    first = re.split(r'[\s,(;]', t, maxsplit=1)[0]
    if first in ctx.beans:
        return first, (None if t == first else t)
    return 'unknown', t


def knowing(b, prov, base, of=None):
    """A knowing act made from a provenance record at old path `base`; returns its statement index or None."""
    if not isinstance(prov, dict):
        return None
    act = ACTS.get(prov.get('src'))
    if act is None:
        return None
    who, note = by_of(prov.get('by', ''), b.ctx)
    moment, how = b.ctx.journal.moment(b.id, b.path, prov.get('as_of'))
    if who == 'unknown' and AGENT.search(str(prov.get('by', ''))) and moment:
        # AN AGENT'S ACT IS ITS SESSION'S (ratified 2026-10-01): the session bean whose start and stop hold the act's
        # moment, and only one; an agent's reading is `derive`, since `read` takes a body
        session = b.ctx.session_at(moment)
        if session:
            who = session
            act = 'derive' if act == 'read' else act
    roles = {'by': who}
    if of:
        roles['of'] = of
    if act == 'derive':
        roles['from'] = 'unknown'
    roles['at'] = moment if moment else 'unknown'
    if note is not None:
        roles['note'] = note
    i = b.add(act, roles)
    b.take(base + ('src',), ('verb', i), act)           # the act, with the nature of its `by`, is the src (§3)
    if 'by' in prov:
        b.take(base + ('by',), b.role(i, 'note') if note is not None else b.role(i, 'by'), prov['by'])
    if 'as_of' in prov:
        if moment and str(moment).startswith(str(prov['as_of'])):
            b.take(base + ('as_of',), b.role(i, 'at'), moment)
        elif moment:
            b.carried.append(f"{'.'.join(map(str, base))}.as_of: {how}")
        else:
            b.notes.append(f"{'.'.join(map(str, base))}.as_of: {how}")
    return i


def anchors_namespace(key):
    return f"anchor-{slug(key)}"


def translate_bean(path, rel, ctx):
    """(text, Bean2) of the bean at `path` written in statements."""
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    head, body = dmparse.split_front_matter(text)
    from core import read
    old = read.loads(head or '') or {}
    bid = os.path.basename(path)[:-3]
    b = Bean2(bid, old, ctx, rel)
    header = {'bean': bid}
    is_mapping = 'mapping' in old and 'genos' not in old
    if is_mapping:
        header['kind'] = old.get('kind')
        if old.get('mapping') == bid:
            b.take(('mapping',), ('header', 'bean'), bid)
        b.take(('kind',), ('header', 'kind'))
    else:
        header['kind'] = old.get('genos')
        if 'genos' in old:
            b.take(('genos',), ('header', 'kind'))
        if old.get('bean') == bid:
            b.take(('bean',), ('header', 'bean'))
    for k in ('title', 'summary'):
        if k in old and isinstance(old[k], str):
            header[k] = old[k]
            b.take((k,), ('header', k))
    if isinstance(old.get('tags'), list) and all(isinstance(t, str) for t in old['tags']):
        header['tags'] = old['tags']
        for i, _t in enumerate(old['tags']):
            b.take(('tags', i), ('header', 'tags', i))
        if not old['tags']:
            b.take(('tags',), ('header', 'tags'), '[]')
    kind = ctx.kinds.get(header['kind']) or {}
    if 'nature' in old and NATURES.get(old['nature']) == kind.get('nature'):
        b.take(('nature',), ('derived', 'the nature of its kind'), old['nature'])

    # -- the knowing act of the whole bean
    blanket = knowing(b, old.get('provenance'), ('provenance',)) if 'provenance' in old else None

    # -- identity: each anchor a name
    for i, a in enumerate((old.get('identity') or {}).get('anchors') or []):
        if isinstance(a, dict) and isinstance(a.get('key'), str) and isinstance(a.get('value'), str):
            ns = anchors_namespace(a['key'])
            ctx.namespace(ns, a)
            sid = b.new_id(f"{a['key']}")
            j = b.add('name', {'by': ns, 'of': 'self', 'as': a['value']}, sid)
            b.take(('identity', 'anchors', i, 'key'), b.role(j, 'by'), ns)
            b.take(('identity', 'anchors', i, 'value'), b.role(j, 'as'))
            b.leftover(('identity', 'anchors', i), ('identity', 'anchors', sid))

    # -- the four questions
    ob = old.get('owned_by')
    owner = None
    if isinstance(ob, dict):
        roles, takes = {'of': 'self'}, []
        if being(ob.get('owner'), ctx):
            owner = roles['by'] = being(ob['owner'], ctx)
            takes.append((('owned_by', 'owner', 'bean'), ('by',)))
        elif ob.get('crown') == 'true':
            owner = roles['by'] = 'theone'
            takes.append((('owned_by', 'crown'), ('by',), 'theone'))
        elif isinstance(ob.get('external'), str):
            roles['by'] = 'unknown'
            roles['note'] = ob['external']
            takes.append((('owned_by', 'external'), ('note',)))
        elif being(ob.get('from'), ctx):
            roles['from'] = being(ob['from'], ctx)
            takes.append((('owned_by', 'from', 'bean'), ('from',)))
        if len(roles) > 1:
            if isinstance(ob.get('note'), str) and 'note' not in roles:
                roles['note'] = ob['note']
                takes.append((('owned_by', 'note'), ('note',)))
            j = b.add('own', roles, b.new_id('own'))
            for t in takes:
                b.take(t[0], b.role(j, *t[1]), *t[2:])
        b.leftover(('owned_by',), ('owned_by',))
    for facet, r in (old.get('responsibility') or {}).items() if isinstance(old.get('responsibility'), dict) else []:
        holder = being((r or {}).get('holder'), ctx) if isinstance(r, dict) else None
        if facet in MODES and holder:
            if MODES[facet] == 'law' and holder == owner:
                b.take(('responsibility', facet, 'holder', 'bean'), ('derived', 'before the law, the owner answers'), holder)
            else:
                j = b.add('answer', {'by': holder, 'of': 'self', 'as': MODES[facet]}, b.new_id(f"answer-{MODES[facet]}"))
                b.take(('responsibility', facet, 'holder', 'bean'), b.role(j, 'by'))
    if 'responsibility' in old:
        b.leftover(('responsibility',), ('responsibility',))
    if isinstance(old.get('via'), list):
        through, takes = [], []
        for i, v in enumerate(old['via']):
            if being(v, ctx):
                takes.append((('via', i, 'bean'), len(through)))
                through.append(being(v, ctx))
            elif isinstance(v, dict) and v.get('someone') in ctx.kinds:
                takes.append((('via', i, 'someone'), len(through), 'someone'))
                through.append({'someone': v['someone']})
        if through:
            j = b.add('come', {'by': 'self', 'through': through}, b.new_id('come'))
            for t in takes:
                b.take(t[0], b.role(j, 'through', t[1], *t[2:]))
        b.leftover(('via',), ('via',))

    # -- where it is
    for i, loc in enumerate(old.get('located_at') or []) if isinstance(old.get('located_at'), list) else []:
        if isinstance(loc, dict) and loc.get('system') and loc.get('at'):
            pos = position(loc['system'], loc['at'], ctx)
            if pos:
                sid = b.new_id(f"at-{i + 1}")
                roles = {'by': 'self', 'at': pos, 'as': 'location'}
                if isinstance(loc.get('note'), str):
                    roles['note'] = loc['note']
                j = b.add('be', roles, sid)
                b.take(('located_at', i, 'at'), b.role(j, 'at'), pos)
                b.take(('located_at', i, 'system'), b.role(j, 'at'), pos)
                if 'note' in roles:
                    b.take(('located_at', i, 'note'), b.role(j, 'note'))
                b.leftover(('located_at', i), ('located_at', sid))
    if 'located_at' in old:
        b.leftover(('located_at',), ('located_at',))
    for term, verb, roles_of in (('lives_in', 'be', lambda x: {'by': 'self', 'at': x, 'as': 'habitat'}),
                                 ('part_of', 'part', lambda x: {'by': 'self', 'of': x}),
                                 ('instance_of', 'run', lambda x: {'by': 'self', 'of': x})):
        x = being(old.get(term), ctx)
        if x:
            roles = roles_of(x)
            j = b.add(verb, roles, b.new_id(term.replace('_', '-')))
            b.take((term, 'bean'), b.role(j, 'at' if verb == 'be' else 'of'))
    if isinstance(old.get('os'), str) and old['os'] in ctx.beans:
        j = b.add('run', {'by': 'self', 'of': old['os']}, b.new_id('os'))
        b.take(('os',), b.role(j, 'of'))

    # -- what it needs
    for k, e in (old.get('depends_on') or {}).items() if isinstance(old.get('depends_on'), dict) else []:
        if being(e, ctx) or (isinstance(e, dict) and being({'bean': e.get('bean')}, ctx)):
            j = b.add('need', {'by': 'self', 'of': [e['bean']]}, b.new_id(f"needs-{k}"))
            b.take(('depends_on', k, 'bean'), b.role(j, 'of', 0))
            b.leftover(('depends_on', k), ('depends_on', b.statements[j][1]['id']))
    for i, e in enumerate(old.get('consumes') or []) if isinstance(old.get('consumes'), list) else []:
        if isinstance(e, dict) and isinstance(e.get('bean'), str):
            j = b.add('need', {'by': 'self', 'of': [e['bean']]}, b.new_id(f"consumes-{e['bean']}"))
            b.take(('consumes', i, 'bean'), b.role(j, 'of', 0))
            b.leftover(('consumes', i), ('consumes', b.statements[j][1]['id']))
    for k, e in (old.get('reaches') or {}).items() if isinstance(old.get('reaches'), dict) else []:
        to = being(e.get('to'), ctx) if isinstance(e, dict) else None
        to = to or (e.get('to') if isinstance(e, dict) and e.get('to') in ctx.beans else None)
        if to and e.get('protocol') in ctx.protocols:
            j = b.add('need', {'by': 'self', 'of': [to], 'through': e['protocol']}, b.new_id(f"reaches-{k}"))
            b.take(('reaches', k, 'to') + (('bean',) if isinstance(e.get('to'), dict) else ()), b.role(j, 'of', 0))
            b.take(('reaches', k, 'protocol'), b.role(j, 'through'))
            b.leftover(('reaches', k), ('reaches', b.statements[j][1]['id']))
    for i, e in enumerate(old.get('knowledge') or []) if isinstance(old.get('knowledge'), list) else []:
        if isinstance(e, dict) and isinstance(e.get('code'), str) and e.get('rel') in ('uses', 'draws_on', 'classified_as'):
            if e['rel'] == 'classified_as':
                j = b.add('classify', {'of': 'self', 'as': e['code']}, b.new_id(f"is-{e['code']}"))
                b.take(('knowledge', i, 'code'), b.role(j, 'as'))
            else:
                j = b.add('use', {'by': 'self', 'of': e['code']}, b.new_id(f"uses-{e['code']}"))
                b.take(('knowledge', i, 'code'), b.role(j, 'of'))
            b.take(('knowledge', i, 'rel'), ('verb', j), 'classify' if e['rel'] == 'classified_as' else 'use')
            b.leftover(('knowledge', i), ('knowledge', b.statements[j][1]['id']))

    # -- what can fail, and what it can do
    for k, e in (old.get('risks') or {}).items() if isinstance(old.get('risks'), dict) else []:
        if isinstance(e, dict) and isinstance(e.get('what'), str):
            roles = {'by': 'self', 'as': e['what']}
            if a_position(e.get('found'), ctx):
                roles['at'] = e['found']
            if isinstance(e.get('note'), str):
                roles['note'] = e['note']
            sid = b.new_id(k)
            j = b.add('fail', roles, sid)
            b.take(('risks', k, 'what'), b.role(j, 'as'))
            for r in ('at', 'note'):
                if r in roles:
                    b.take(('risks', k, 'found' if r == 'at' else 'note'), b.role(j, r))
            b.leftover(('risks', k), ('risks', sid))
    for k, e in (old.get('capabilities') or {}).items() if isinstance(old.get('capabilities'), dict) else []:
        if not isinstance(e, dict):
            continue
        sid = b.new_id(k)
        j = b.add('can', {'by': 'self', 'of': k}, sid)
        perm = PERMISSION.get(e.get('permission', 'permitted'))
        if perm:
            imposer = e.get('by') if e.get('by') in ctx.beans else 'unknown'
            roles = {'of': sid, 'through': imposer}
            if isinstance(e.get('why'), str):
                roles['why'] = e['why']
            jp = b.add(perm, roles)
            if 'permission' in e:
                b.take(('capabilities', k, 'permission'), ('verb', jp), perm)
            if imposer != 'unknown':
                b.take(('capabilities', k, 'by'), b.role(jp, 'through'))
            if 'why' in roles:
                b.take(('capabilities', k, 'why'), b.role(jp, 'why'))
        feas = FEASIBILITY.get(e.get('feasibility', 'possible'))
        if feas and 'feasibility' in e:
            roles = {'of': sid}
            if isinstance(e.get('feasibility_why'), str):
                roles['why'] = e['feasibility_why']
            jf = b.add(feas, roles)
            b.take(('capabilities', k, 'feasibility'), ('verb', jf), feas)
            if 'why' in roles:
                b.take(('capabilities', k, 'feasibility_why'), b.role(jf, 'why'))
        b.leftover(('capabilities', k), ('capabilities', sid))
    for i, e in enumerate(old.get('roles') or []) if isinstance(old.get('roles'), list) else []:
        if isinstance(e, dict) and e.get('role') in ctx.jobs:
            roles = {'by': 'self', 'as': e['role']}
            if isinstance(e.get('why'), str):
                roles['why'] = e['why']
            sid = b.new_id(f"does-{e['role']}")
            j = b.add('do', roles, sid)
            b.take(('roles', i, 'role'), b.role(j, 'as'))
            if 'why' in roles:
                b.take(('roles', i, 'why'), b.role(j, 'why'))
            b.leftover(('roles', i), ('roles', sid))
    for i, e in enumerate(old.get('endpoints') or []) if isinstance(old.get('endpoints'), list) else []:
        if not (isinstance(e, dict) and e.get('protocol') in ctx.protocols and e.get('system') and e.get('at')):
            continue
        ip = position(e['system'], e['at'], ctx)
        if not ip:
            continue
        at = [ip]
        if isinstance(e.get('port'), str):
            transport = ctx.transport.get(e['protocol'], 'tcp')
            port = position(f"{transport}-port", e['port'], ctx)
            if not port:
                continue
            at.append(port)
        sid = b.new_id(f"serves-{e['protocol']}")
        j = b.add('serve', {'by': 'self', 'at': at, 'through': e['protocol']}, sid)
        b.take(('endpoints', i, 'at'), b.role(j, 'at', 0), ip)
        b.take(('endpoints', i, 'system'), b.role(j, 'at', 0), ip)
        if len(at) > 1:
            b.take(('endpoints', i, 'port'), b.role(j, 'at', 1), at[1])
        b.take(('endpoints', i, 'protocol'), b.role(j, 'through'))
        b.leftover(('endpoints', i), ('endpoints', sid))

    # -- agreements
    parties = old.get('parties') if isinstance(old.get('parties'), dict) else {}
    words = old.get('words') if isinstance(old.get('words'), dict) else {}
    over = old.get('over') if isinstance(old.get('over'), dict) else {}
    things, over_takes = [], []
    for k, e in over.items():
        t = being((e or {}).get('thing'), ctx) if isinstance(e, dict) else None
        if t:
            over_takes.append((('over', k, 'thing', 'bean'), len(things)))
            things.append(t)
        elif isinstance(e, dict) and isinstance(e.get('what'), str):
            over_takes.append((('over', k, 'what'), len(things)))
            things.append(e['what'])
    party_bean = {}
    first_agree = None
    for k, e in parties.items():
        if not isinstance(e, dict):
            continue
        who = being(e.get('who'), ctx)
        roles = {'by': who or 'unknown'}
        if things:
            roles['of'] = list(things)
        if words.get('form') in ctx.forms:
            roles['through'] = words['form']
        if isinstance(e.get('role'), str):
            roles['as'] = e['role']
        if a_position(e.get('accepted'), ctx):
            roles['at'] = e['accepted']
        if not who and isinstance(e.get('external'), str):
            roles['note'] = e['external']
        sid = b.new_id(f"agreed-{k}")
        j = b.add('agree', roles, sid)
        party_bean[k] = who or 'unknown'
        if first_agree is None:
            first_agree = sid
            for p, n in over_takes:
                b.take(p, b.role(j, 'of', n))
            if 'through' in roles:
                b.take(('words', 'form'), b.role(j, 'through'))
        if who:
            b.take(('parties', k, 'who', 'bean'), b.role(j, 'by'))
        elif 'note' in roles:
            b.take(('parties', k, 'external'), b.role(j, 'note'))
        for r, o in (('as', 'role'), ('at', 'accepted')):
            if r in roles:
                b.take(('parties', k, o), b.role(j, r))
        if isinstance(e.get('provenance'), dict):
            knowing(b, e['provenance'], ('parties', k, 'provenance'), of=[sid])
        b.leftover(('parties', k), ('parties', sid))
    for term in ('parties', 'over', 'words'):
        if term in old:
            b.leftover((term,), (term,))
    for k, e in (old.get('clauses') or {}).items() if isinstance(old.get('clauses'), dict) else []:
        if not (isinstance(e, dict) and isinstance(e.get('what'), str) and first_agree):
            continue
        who = party_bean.get(e.get('by'), 'unknown')
        sid = b.new_id(k)
        roles = {'by': who, 'of': e['what']}
        if isinstance(e.get('note'), str):
            roles['note'] = e['note']
        j = b.add('can', roles, sid)
        b.take(('clauses', k, 'what'), b.role(j, 'of'))
        if 'by' in e and e['by'] in party_bean:
            b.take(('clauses', k, 'by'), b.role(j, 'by'), who)
        if 'note' in roles:
            b.take(('clauses', k, 'note'), b.role(j, 'note'))
        perm = PERMISSION.get(e.get('permission'))
        if perm:
            jp = b.add(perm, {'of': sid, 'through': first_agree})
            b.take(('clauses', k, 'permission'), ('verb', jp), perm)
        b.leftover(('clauses', k), ('clauses', sid))
    for k, e in (old.get('transactions') or {}).items() if isinstance(old.get('transactions'), dict) else []:
        if not isinstance(e, dict) or not isinstance(e.get('amount'), dict):
            continue
        payers = [p.get('party') for p in e.get('paid_by') or [] if isinstance(p, dict)]
        if len(payers) != 1 or payers[0] not in party_bean:
            continue
        sid = b.new_id(k)
        u = e['amount'].get('unit')
        code = u if u in ctx.std.currencies else (ucum_of(str(u), ctx.law) or u)     # a currency's code, or UCUM's
        roles = {'by': party_bean[payers[0]], 'of': {'count': e['amount'].get('count'), 'unit': code}}
        if a_position(e.get('day'), ctx):
            roles['at'] = e['day']
        if isinstance(e.get('what'), str):
            roles['note'] = e['what']
        j = b.add('pay', roles, sid)
        b.take(('transactions', k, 'paid_by', 0, 'party'), b.role(j, 'by'), roles['by'])
        b.take(('transactions', k, 'amount', 'count'), b.role(j, 'of', 'count'))
        b.take(('transactions', k, 'amount', 'unit'), b.role(j, 'of', 'unit'), code)
        for r, o in (('at', 'day'), ('note', 'what')):
            if r in roles:
                b.take(('transactions', k, o), b.role(j, r))
        for n, bb in enumerate(e.get('borne_by') or []):
            if isinstance(bb, dict) and bb.get('party') in party_bean:
                broles = {'by': party_bean[bb['party']], 'of': sid}
                if 'share' in bb:
                    broles['share'] = bb['share']
                jb = b.add('bear', broles, b.new_id(f"{sid}-borne-{n + 1}"))
                b.take(('transactions', k, 'borne_by', n, 'party'), b.role(jb, 'by'), broles['by'])
                if 'share' in bb:
                    b.take(('transactions', k, 'borne_by', n, 'share'), b.role(jb, 'share'))
        b.leftover(('transactions', k), ('transactions', sid))

    # -- time
    t = old.get('timing') if isinstance(old.get('timing'), dict) else {}
    ends = [t.get(x) for x in ('start', 'stop')]
    if isinstance(ends[0], dict) and ends[0].get('system') and ends[0].get('at'):
        a = position(ends[0]['system'], ends[0]['at'], ctx)
        z = position(ends[1]['system'], ends[1]['at'], ctx) if isinstance(ends[1], dict) and ends[1].get('at') else None
        whole = f"{a}/{z}" if a and z else a
        if whole and z:
            try:
                frame.read(whole, ctx.systems, ctx.zone)
            except frame.Refused:
                whole = None
        if whole:
            j = b.add('be', {'by': 'self', 'at': whole, 'as': 'presence'}, b.new_id('present'))
            for x, v in (('start', a), ('stop', z)):
                if v:
                    b.take(('timing', x, 'at'), b.role(j, 'at'), whole)
                    b.take(('timing', x, 'system'), b.role(j, 'at'), whole)
    if isinstance(old.get('produces'), str) and old['produces']:
        j = b.add('produce', {'by': 'self', 'of': [old['produces']]}, b.new_id('produces'))
        b.take(('produces',), b.role(j, 'of', 0))
    ws = old.get('workspace') if isinstance(old.get('workspace'), dict) else {}
    if isinstance(ws.get('opened_at'), str):
        try:
            frame.read(ws['opened_at'], ctx.systems, ctx.zone)
            j = b.add('open', {'of': 'self', 'at': ws['opened_at']}, b.new_id('opened'))
            b.take(('workspace', 'opened_at'), b.role(j, 'at'))
        except frame.Refused:
            pass

    # -- the rest, whole
    for k in old:
        b.leftover((k,), () if k == 'details' else (k,))     # the old details are the new details' own keys
    found = comments(head or '')
    kept = []
    for on, txt in found:
        if kept and kept[-1]['on'] == on:
            kept[-1]['text'] += '\n' + txt
        else:
            kept.append({'on': on, 'text': txt})
    if kept:
        if 'comments' in b.details:
            raise ValueError(f"{bid}: details.comments is a key already")
        b.details['comments'] = kept
    b.n_comments = len(found)
    b.header = header
    b.body = body
    return render(b), b


def comments(head):
    """[(top-level key, text)] of each comment line of a front matter, in order: the key whose item the comment sits on,
    or for a comment on a line of its own, the item on the next line that holds one (the last, at the end). A `#` inside
    a block scalar is the value's text, not a comment. dmparse.comments names the finest item, but loops without end on
    an item whose first value ends in a full stop or holds a lone bracket; the top-level key is enough here, where the
    comment is kept in `details.comments` and counted."""
    root = yaml.compose(head, Loader=yaml.BaseLoader)
    spans, block = [], set()
    for k, v in (root.value if isinstance(root, yaml.MappingNode) else []):
        spans.append((k.start_mark.line, v.end_mark.line, k.value))
        todo = [v]
        while todo:
            n = todo.pop()
            if isinstance(n, yaml.ScalarNode) and n.style in ('|', '>'):
                block.update(range(n.start_mark.line + 1, n.end_mark.line + (1 if n.end_mark.column else 0)))
            elif isinstance(n, yaml.MappingNode):
                todo += [x for kv in n.value for x in kv]
            elif isinstance(n, yaml.SequenceNode):
                todo += n.value
    lines = head.split('\n')

    def key_at(i):
        here = [s for s in spans if s[0] <= i <= max(s[1], s[0])]
        return here[-1][2] if here else ''
    content = [i for i, l in enumerate(lines) if l.strip() and i not in block
               and (dmparse.comment_start(l) < 0 or l[:dmparse.comment_start(l)].strip())]
    out = []
    for i, l in enumerate(lines):
        c = dmparse.comment_start(l) if i not in block else -1
        if c < 0:
            continue
        on = i if l[:c].strip() else next((j for j in content if j > i), next((j for j in reversed(content) if j < i), None))
        out.append((key_at(on) if on is not None else '', l[c:].lstrip('#').strip()))
    return out


def render(b):
    """The text of a bean in statements: its header, its statements one to a line, its details, and its body."""
    def flow(x):
        return yaml.safe_dump(x, default_flow_style=True, width=10 ** 9, allow_unicode=True, sort_keys=False).strip()
    out = ['---', yaml.safe_dump(b.header, allow_unicode=True, sort_keys=False, width=120).rstrip()]
    if b.statements:
        out.append('statements:')
        for verb, roles in b.statements:
            out.append(f"  - {verb}: {flow(roles)}")
    if b.details:
        out.append(yaml.safe_dump({'details': b.details}, allow_unicode=True, sort_keys=False, width=120).rstrip())
    return '\n'.join(out) + '\n---' + (b.body if b.body.startswith('\n') else '\n' + b.body)


def verify(b, text):
    """[problem] for a written bean: an old leaf with no place, or a place that does not hold its value."""
    from core import read
    head, _body = dmparse.split_front_matter(text)
    new = read.loads(head) or {}
    sts = [next(iter(s.values())) for s in new.get('statements') or []]
    verbs = [next(iter(s)) for s in new.get('statements') or []]
    out = []
    for p, v in leaves(b.old):
        if p not in b.placed:
            out.append(f"{b.id}: {'.'.join(map(str, p))} = {v!r} has no place")
            continue
        where, want = b.placed[p]
        if where[0] == 'header':
            got = at_path(new, where[1:])
        elif where[0] == 'details':
            got = at_path(new.get('details') or {}, where[1:])
            got = '{}' if got == {} else '[]' if got == [] else got
        elif where[0] == 'statement':
            got = at_path(sts[where[1]], where[2:]) if where[1] < len(sts) else KeyError
        elif where[0] == 'verb':
            got = verbs[where[1]]
        elif where[0] == 'derived':
            continue
        else:
            got = KeyError
        if got != want:
            out.append(f"{b.id}: {'.'.join(map(str, p))} = {v!r} is not at {where} (there: {got!r}, wanted {want!r})")
    kept = sum(len(c['text'].split('\n')) for c in (new.get('details') or {}).get('comments') or [])
    if kept != b.n_comments:
        out.append(f"{b.id}: {b.n_comments} comment lines, {kept} kept")
    return out


class Context:
    """What a translation reads beside each bean: the garden's beans, its journal, the law's tables."""

    def __init__(self, root, law, std):
        self.root, self.law, self.std = root, law, std
        self.beans = set()
        for d in DOCUMENTS:
            if os.path.isdir(os.path.join(root, d)):
                self.beans |= {f[:-3] for f in os.listdir(os.path.join(root, d)) if f.endswith('.md')}
        self.journal = Journal(root)
        self.systems = std.systems
        try:
            from core import read
            self.zone = read.document(os.path.join(root, 'GARDEN.md'))[0].get('zone')
        except Exception:
            self.zone = None
        self.kinds = dict(law.kinds)
        self.protocols = set(std.protocols)
        self.transport = {str(r['protocol']): str(r.get('transport') or 'tcp') for r in std.old.get('net_protocols') or []
                          if isinstance(r, dict) and r.get('protocol')}
        self.jobs = set(law.table('jobs') or [])
        self.forms = set(law.table('forms') or [])
        self.namespaces = {}
        self.sessions = []                   # (start ms, stop ms, bean) of each session with both ends known
        from core import read
        p = os.path.join(root, 'beans')
        for f in sorted(os.listdir(p)) if os.path.isdir(p) else []:
            try:
                fm = read.document(os.path.join(p, f))[0] if f.endswith('.md') else {}
            except read.Unread:
                continue
            t = fm.get('timing') if fm.get('genos') == 'session' and isinstance(fm.get('timing'), dict) else {}
            ends = []
            for x in ('start', 'stop'):
                e = t.get(x) if isinstance(t.get(x), dict) else {}
                pos = position(e.get('system'), e.get('at'), self) if e.get('system') and e.get('at') else None
                try:
                    ends.append(frame.read(pos, self.systems, self.zone).moment if pos else None)
                except frame.Refused:
                    ends.append(None)
            if len(ends) == 2 and None not in ends:
                self.sessions.append((ends[0], ends[1], f[:-3]))

    def session_at(self, moment):
        """The one session whose start and stop hold `moment`, or None (none, or more than one)."""
        try:
            ms = frame.read(moment, self.systems, self.zone).moment
        except frame.Refused:
            return None
        hits = [s for a, z, s in self.sessions if ms is not None and a <= ms <= z]
        return hits[0] if len(hits) == 1 else None

    def namespace(self, ns, anchor):
        once = anchor.get('establishing') == 'true'
        self.namespaces[ns] = self.namespaces.get(ns, True) and once


def ucum_of(name, law):
    """The UCUM code of a unit the law names, or of one named `<a>-per-<b>` from two it names (`gigabyte-per-day` is
    `GBy/d`); None where neither."""
    for code, row in law.units.items():
        if row.get('name') == name and row.get('ucum') != 'false':
            return code
    parts = name.split('-per-')
    for i in range(1, len(parts)):
        a, b = ucum_of('-per-'.join(parts[:i]), law), ucum_of('-per-'.join(parts[i:]), law)
        if a and b:
            return f"{a}/{b}" if not any(c in b for c in './') else f"{a}/({b})"
    return None


def unit_row(name, quantity, law):
    """A garden's own unit (today's `registry_additions.units`) as a row of the core's units: its UCUM code composed from
    the law's rows where its name is made of theirs, else its name kept as its code, saying why."""
    code = ucum_of(name, law)
    if code:
        return {'unit': code, 'name': name, 'quantity': quantity}
    return {'unit': name, 'name': name, 'quantity': quantity, 'ucum': 'false',
            'why': "its name is made of no units the law writes in UCUM: give its UCUM code"}


def garden(src, dst):
    """Copy the garden at `src` to `dst` with its beans in statements; returns (counts, problems)."""
    from core import read, standards
    from core.law import Law
    if os.path.exists(dst):
        raise SystemExit(f"translate: {dst} exists — a translation is written into a new copy")
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('.git', '__pycache__'))
    std = standards.here(src) if os.path.isfile(os.path.join(src, 'seed', 'std-vocab.md')) else standards.here()
    vocab = read.document(os.path.join(src, 'VOCAB.md'))[0] if os.path.exists(os.path.join(src, 'VOCAB.md')) else {}
    oldv = dmparse.loads(dmparse.split_front_matter(open(os.path.join(src, 'VOCAB.md'), encoding='utf-8').read())[0]) \
        if vocab else {}
    rows = {'kinds': [kind_row(g) for g in oldv.get('local_gene') or [] if isinstance(g, dict) and g.get('genos')]}
    mkinds = set()
    for d in DOCUMENTS:
        p = os.path.join(src, d)
        for f in sorted(os.listdir(p)) if os.path.isdir(p) else []:
            if f.endswith('.md'):
                fm = read.document(os.path.join(p, f))[0]
                if 'mapping' in fm and 'genos' not in fm and isinstance(fm.get('kind'), str):
                    mkinds.add(fm['kind'])
    rows['kinds'] += [{'kind': k, 'nature': 'sayable'} for k in sorted(mkinds)]
    adds = oldv.get('registry_additions') or {}
    tables = {}
    if adds.get('net_protocols'):
        tables['protocols'] = [str(r['protocol']) for r in adds['net_protocols'] if isinstance(r, dict) and r.get('protocol')]
    if tables:
        rows['tables'] = tables
    base = Law.load(std=std)
    units = [unit_row(str(r['unit']), str(r.get('quantity')), base) for r in adds.get('units') or []
             if isinstance(r, dict) and r.get('unit')]
    if units:
        rows['units'] = units
    law = Law.load(('VOCAB.md', rows), std=std)
    ctx = Context(src, law, std)
    for k in tables.get('protocols', []):
        ctx.protocols.add(k)
    counts = collections.Counter()
    problems = []
    for d in DOCUMENTS:
        p = os.path.join(src, d)
        for f in sorted(os.listdir(p)) if os.path.isdir(p) else []:
            if not f.endswith('.md'):
                continue
            text, b = translate_bean(os.path.join(p, f), f"{d}/{f}", ctx)
            with open(os.path.join(dst, d, f), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(text)
            problems += verify(b, text)
            counts['beans'] += 1
            counts['statements'] += len(b.statements)
            counts['leaves'] += len(leaves(b.old))
            for where, _v in b.placed.values():
                counts['to ' + where[0]] += 1
            counts['comment lines'] += b.n_comments
            for n in b.notes:
                problems.append(f"{b.id}: {n}")
            counts['acts at the moment their bean was made'] += len(b.carried)
    rows['namespaces'] = [{'namespace': ns, 'once': 'true' if once else 'false'} for ns, once in sorted(ctx.namespaces.items())]
    # THE GARDEN'S ROWS go into its VOCAB.md beside today's keys, which the core's law passes by
    vp = os.path.join(dst, 'VOCAB.md')
    vtext = open(vp, encoding='utf-8').read()
    vhead, vbody = dmparse.split_front_matter(vtext)
    add = yaml.safe_dump({k: v for k, v in rows.items() if v}, allow_unicode=True, sort_keys=False, width=120)
    with open(vp, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('---\n' + vhead.rstrip('\n') + '\n# == THE CORE\'S ROWS: written by core/translate.py ==\n' + add + '---'
                 + vbody)
    return counts, problems


def main(argv):
    if argv[:1] == ['levels']:
        sys.stdout.write(levels(old_law()))
        return 0
    if argv[:1] == ['kinds']:
        sys.stdout.write(kinds(old_law()))
        return 0
    if argv[:1] == ['layers']:
        from core import read
        sys.stdout.write(layers(old_law(), read.data(os.path.join(HERE, 'law', 'core.yaml')).get('layers') or []))
        return 0
    if argv[:1] == ['garden'] and len(argv) == 3:
        counts, problems = garden(os.path.abspath(argv[1]), os.path.abspath(argv[2]))
        for p in problems:
            print(p)
        placed = sum(v for k, v in counts.items() if k.startswith('to '))
        print(f"translate: {counts['beans']} beans, {counts['statements']} statements; {counts['leaves']} values, "
              f"{placed} placed (" + ', '.join(f"{v} {k}" for k, v in sorted(counts.items()) if k.startswith('to '))
              + f"); {counts['comment lines']} comment lines kept; {counts['acts at the moment their bean was made']} acts "
              f"at the moment their bean was made, their day in details — {len(problems)} problem(s)")
        return 1 if problems else 0
    print(__doc__.strip().split('\n\n')[0])
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
