#!/usr/bin/env python3
"""dmreview — gather the evidence a Part B judgment needs. It does NOT judge.

Part A is what a machine checks. Part B is what only a person can. But "unenforceable" is not the same
as "unsupportable": a gate cannot tell whether provenance is HONEST or whether prose reads correctly
cold — and it can still put in front of you every place where that question arises, so the judging is
quick and complete instead of a hunt.

Everything printed here is a QUESTION, not a violation. Most of it will be fine, and that is expected:
these are the places where being wrong would be invisible to the gate, not places that are wrong.

IT ALWAYS EXITS 0, deliberately. A judgment aid that can fail a build becomes a rule, and a rule that
encodes a judgment nobody made is worse than no rule — it launders an opinion into an enforcement.
If a signal here ever earns enforcement, it belongs in the gate with evidence, and it leaves this file.

THE LAW'S OWN PRECONDITIONS (`--law`). The same stance, turned on the law, for whoever merges a change to it.
That one law is clearer, more general or more beautiful than another is a judgment, and a judgment is its
judge's: the person who ratifies. No count can make it — every proxy here that became a target drifted from
what it measured. What can be counted are the preconditions the record rules on, and those are printed as
evidence: SIZE, with no direction (a mechanism may make the law larger and better, and the cheapest way to
lower a count is to fold a structured fact into prose); CLOSURE (what the law offers that nothing takes up);
SECOND STATEMENTS (an enumeration the law owns, restated in a prose document, and whether the copy differs);
STORY IN THE LAW (when, who or where, told inside the law's data); STATED, NOT CHECKED (`enforced_by: none`);
and ONE ESTATE IN THE STANDARD (a standard vacancy whose reason is one garden's expectation). With
`--against <ref>` each line says how it moved since that ref. It reads seed/std-vocab.md and the tools, as
the working tree holds them and as git holds them at the ref; it names the law's structure, never a term.

Usage: python3 bin/dmreview.py [--all]     (--all lists every occurrence rather than a sample)
       python3 bin/dmreview.py --law [--against <git-ref>]
"""
import difflib, glob, os, re, subprocess, sys, textwrap
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALL = '--all' in sys.argv
FACTUAL = ('owns', 'attributes', 'details')

# ============================== THE LAW'S PRECONDITIONS (--law) ==============================
LAW_FILE, GATE_FILE = 'seed/std-vocab.md', 'bin/dmcheck.py'

# STORY IN THE LAW: a string the law TELLS a reader that says when something happened, who did it, or where — the
# journal's business, sitting one layer too high. The one definition: test/rationale.py holds the law to it as a
# ratchet, and `--law` lists what it finds, so the count the suite enforces is the count the ratifier reads.
STORY = re.compile(r"\b20\d\d-\d\d-\d\d\b|\bfirst draft\b|\bthe operator\b|\bthis estate\b|\bthis garden\b"
                   r"|\bwithin the hour\b|\b(until|since) \d+\.\d\b", re.I)
_DATE = re.compile(r'20\d\d-\d\d-\d\d')
_TICKS = re.compile(r'`[^`]*`')
# The keys whose value is told to a reader. A suffix counts as the key does (`form_note`, `pattern_why`,
# `values_meaning`): the law grows prose keys by suffix, and a list of whole names misses the one a release adds.
_TOLD = ('meaning', 'why', 'note', 'refusal', 'decision', 'case', 'instead')
_TOLD_SUFFIX = ('_meaning', '_why', '_note', '_directive')


def told(key):
    k = str(key)
    return k in _TOLD or k.endswith(_TOLD_SUFFIX)


_NAME = re.compile(r'[\w:./+-]{1,64}')     # a name, not a sentence: a row's `why` is unique too, and no label


def _label(seq, i):
    """How a path names item i of a list: by the first of its own scalar fields that no sibling shares — a spelling
    `bin/dmwhy.py` resolves — else by its position. A name, unlike a position, survives a row added above it, so a
    path read at two refs names the same item."""
    item = seq[i]
    if isinstance(item, dict):
        for k, v in item.items():
            if isinstance(v, (str, int)) and not isinstance(v, bool) and _NAME.fullmatch(str(v)) and \
                    sum(1 for o in seq if isinstance(o, dict) and o.get(k) == v) == 1:
                return f'[{v}]'
    return f'[{i}]'


def _strings(node, path):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _strings(v, f'{path}.{k}')
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _strings(v, path + _label(node, i))
    elif isinstance(node, str):
        yield path, node


def story_in(law):
    """[(path, phrase, text)] for every string the law tells a reader that says when, who or where.

    Read from the PARSED law. A line grep sees only the first line of a folded `>` block: it counted fourteen while
    forty-five sat in the law. A date inside backticks is an example of a value — a `2026-01-01` in a pattern's
    explanation — not a moment in the law's own story, and is not counted."""
    out = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                p = f'{path}.{k}' if path else str(k)
                if not told(k):
                    walk(v, p)
                    continue
                for q, s in _strings(v, p):
                    ticks = [m.span() for m in _TICKS.finditer(s)]
                    hits = [m.group(0) for m in STORY.finditer(s)
                            if not (_DATE.fullmatch(m.group(0)) and any(a < m.start() < b for a, b in ticks))]
                    if hits:
                        out.append((q, hits[0], ' '.join(s.split())))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, path + _label(node, i))
    walk(law or {}, '')
    return out


def _git(*args):
    try:
        r = subprocess.run(['git', '-C', ROOT] + list(args), capture_output=True, timeout=30)
    except Exception:
        return None
    return r.stdout.decode('utf-8', 'replace') if r.returncode == 0 else None


class Tree:
    """The repository as the working tree holds it (ref None), or as git holds it at a ref. Paths are written with
    `/`, as git spells them, on every platform."""

    def __init__(self, ref=None):
        self.ref = ref

    def read(self, path):
        if self.ref is not None:
            return _git('show', f'{self.ref}:{path}')
        try:
            with open(os.path.join(ROOT, *path.split('/')), encoding='utf-8') as fh:
                return fh.read()
        except OSError:
            return None

    def files(self):
        out = _git('ls-files') if self.ref is None else _git('ls-tree', '-r', '--name-only', self.ref)
        if out is not None:
            return out.splitlines()
        if self.ref is not None:
            return []
        return sorted(os.path.relpath(os.path.join(d, f), ROOT).replace(os.sep, '/')
                      for d, _s, fs in os.walk(ROOT) if '.git' not in d.split(os.sep) for f in fs)


def law_at(ref=None):
    """The law's front matter, parsed — at a git ref, or in the working tree. None when it is not there."""
    text = Tree(ref).read(LAW_FILE)
    fm = dmparse.split_front_matter(text)[0] if text else None
    try:
        law = dmparse.loads(fm) if fm else None
    except Exception:
        return None
    return law if isinstance(law, dict) else None


def _terms(law):
    return [t for t in (law.get('terms') or []) if isinstance(t, dict) and t.get('term')]


def _profile_terms(law):
    return [(p, t) for p, prof in (law.get('profiles') or {}).items() if isinstance(prof, dict)
            for t in (prof.get('terms') or []) if isinstance(t, dict) and t.get('term')]


def _domain_of(d, domains):
    """The domain an attribute's `in:` names, in the law's own words: a list is `values`, a word names itself, a
    mapping names its domain by a key (`registry_from` is a `registry`)."""
    if isinstance(d, list):
        return 'values'
    if isinstance(d, str):
        return d
    if isinstance(d, dict):
        for k in d:
            if k in domains:
                return k
        for k in d:
            for name in domains:
                if str(k).startswith(name + '_'):
                    return name
    return None


def _domains_used(attrs, domains, into):
    for rec in (attrs or {}).values():
        if isinstance(rec, dict) and 'in' in rec:
            into.add(_domain_of(rec['in'], domains))
            if isinstance(rec['in'], dict) and isinstance(rec['in'].get('entries'), dict):
                _domains_used(rec['in']['entries'], domains, into)


def _tools_text(tree):
    tools = [f for f in tree.files() if f.startswith('bin/') and f != 'bin/dmreview.py'
             and (f.endswith(('.py', '.sh')) or f.startswith('bin/hooks/'))]
    return '\n'.join(tree.read(f) or '' for f in tools)


def _unread(keys, tools):
    """The keys no shipped tool names as a string literal. A LITERAL GREP of bin/, and it says so: a tool that reads
    a key only through the law's own list of keys reads it generically — whether that is reading it is the question."""
    return [k for k in keys if not re.search('[\'"]' + re.escape(str(k)) + '[\'"]', tools)]


def _enumerations(law):
    """{path: [values]} — every list of three or more names the law states, and the key column of each top-level
    table. What the law OWNS, and so what a prose document can only restate."""
    out = {}

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f'{path}.{k}' if path else str(k))
        elif isinstance(node, list):
            if len(node) >= 3 and all(isinstance(x, str) and re.fullmatch(r'[A-Za-z][\w.-]*', x) for x in node):
                out[path] = list(node)
            elif path and '.' not in path and '[' not in path and node and all(isinstance(x, dict) for x in node):
                key = next(iter(node[0]), None)
                col = [r.get(key) for r in node if isinstance(r.get(key), str)]
                if len(col) >= 3:
                    out[f'{path}[].{key}'] = col
            for i, v in enumerate(node):
                walk(v, path + _label(node, i))
    walk(law, '')
    return out


# A RESTATEMENT is a run of three or more names in backticks, joined as prose joins a list, of which at least three —
# and at least half of the law's list — are the law's. Fewer than half is an example, which is not a copy.
_SEP = r'(?:\s*(?:,|\||/|;|·)\s*(?:(?:or|and)\s+)?|\s+(?:or|and)\s+)'
_RUN = re.compile(r'`[^`\n]+`(?:' + _SEP + r'`[^`\n]+`){2,}')
_CHANGELOG = re.compile(r'(?im)^#+ .*changelog')


def _prose_documents(tree):
    """(path, text, offset) for every tracked prose document that states or explains law: not the history (whose
    job is to say what the law WAS), not a garden's beans, mappings or journal, and of the law's own file only the
    body above its changelog."""
    for f in tree.files():
        if not f.endswith('.md') or f == 'HISTORY.md' or f.split('/')[0] in ('beans', 'mappings', 'log'):
            continue
        text = tree.read(f)
        if text is None:
            continue
        start = 0
        if f == LAW_FILE:
            fm = dmparse.split_front_matter(text)[0]
            start = text.find(fm) + len(fm) if fm else 0
            m = _CHANGELOG.search(text, start)
            text = text[:m.start()] if m else text
        yield f, text, start


def _restatements(law, tree):
    enums, found = _enumerations(law), []
    for f, text, start in _prose_documents(tree):
        for m in _RUN.finditer(text, start):
            names = re.findall(r'`([^`]+)`', m.group(0))
            for path, vals in enums.items():
                have = set(vals)
                ours = {n for n in names if n in have}
                if len(ours) < 3 or 2 * len(ours) < len(have):
                    continue
                found.append({'id': f"{f} {path}", 'where': f"{f}:{text.count(chr(10), 0, m.start()) + 1}",
                              'path': path, 'of': (len(ours), len(have)),
                              'extra': [n for n in names if n not in have]})
    return found


# A vacancy's reason says whose it is. `prediction` is the one reason that is a garden's own expectation, and the law
# does not yet say that of it in a column a tool could read; until it does, the name is here, and this is why.
_ONE_GARDENS_REASON = 'prediction'


def preconditions(tree):
    """The measures, as [(section, [row])]; a row is {label, n, items, show, detail?, note?}. None with no law."""
    law = law_at(tree.ref)
    if law is None:
        return None
    terms, pterms = _terms(law), _profile_terms(law)
    every = terms + [t for _p, t in pterms]
    sl = law.get('schema_language') or {}
    domains = list(sl.get('attr_domains') or {})
    constructs = [k for k in sl if k != 'attr_domains']
    tables = [k for k, v in law.items() if isinstance(v, list) and k not in ('terms', 'kinds')]
    kinds = [k.get('kind') for k in law.get('kinds') or [] if isinstance(k, dict)]
    files = [r.get('registry') for r in law.get('registry_files') or [] if isinstance(r, dict)]
    gate = tree.read(GATE_FILE) or ''

    used, elsewhere = set(), {}
    for t in every:
        _domains_used((t.get('schema') or {}).get('attrs'), domains, used)
    for k, v in law.items():                  # the law judges more than terms by attrs: the manifest, for one
        if k not in ('terms', 'profiles', 'schema_language') and isinstance(v, dict) and \
                isinstance(v.get('attrs'), dict):
            here = set()
            _domains_used(v['attrs'], domains, here)
            for d in here:
                elsewhere.setdefault(d, []).append(k)
    idle = [d for d in domains if d not in used]
    tools = _tools_text(tree)
    anchor_attrs = list((law.get('identity_policy') or {}).get('anchor_attrs') or [])
    facets = list(dict.fromkeys(k for t in every if isinstance(t.get('anchor'), dict) for k in t['anchor']))
    manifest = list(((law.get('manifest') or {}).get('attrs') or {}))
    unread = [_unread(anchor_attrs, tools), _unread(facets, tools), _unread(manifest, tools)]

    restated = _restatements(law, tree)
    differ = [r for r in restated if r['extra']]
    story = story_in(law)
    unchecked = [t['term'] for t in terms if str(t.get('enforced_by')) == 'none'] + \
                [f"{p}:{t['term']}" for p, t in pterms if str(t.get('enforced_by')) == 'none']
    vacancies = [(None, v) for v in (law.get('vacancies') or [])] + \
                [(p, v) for p, prof in (law.get('profiles') or {}).items() if isinstance(prof, dict)
                 for v in (prof.get('vacancies') or [])]
    estate = [(p, v) for p, v in vacancies if isinstance(v, dict) and v.get('reason') == _ONE_GARDENS_REASON]
    tiers = Counter(p or 'standard' for p, _v in estate)

    def row(label, items, show, n=None, **kw):
        return dict(label=label, n=len(items) if n is None else n, items=items, show=show, **kw)

    return [
        ('SIZE — counted, with no direction', [
            row('terms, standard', [t['term'] for t in terms], 'delta'),
            row('terms, in profiles', [f"{p}:{t['term']}" for p, t in pterms], 'delta',
                note=' · '.join(f'{p} {n}' for p, n in sorted(Counter(p for p, _t in pterms).items()))),
            row('kinds', kinds, 'delta'),
            row('registries and tables (the top-level lists)', tables, 'delta'),
            row('registry files', files, 'delta'),
            row('schema-language constructs', constructs, 'delta'),
            row('attribute domains', domains, 'delta'),
            row('gate lines', None, 'none', n=gate.count('\n'), note=GATE_FILE),
        ]),
        ('CLOSURE — what the law offers that nothing takes up', [
            row('attribute domains no term uses', idle, 'names',
                note='; '.join(f"`{d}` is used by {', '.join(elsewhere[d])}" for d in idle if d in elsewhere)),
            row('anchor attributes no tool reads', unread[0], 'names',
                note=f'of {len(anchor_attrs)} in identity_policy.anchor_attrs; a literal grep of bin/'),
            row('anchor facets no tool reads', unread[1], 'names',
                note=f"of {len(facets)} keys a term's `anchor:` uses; a literal grep of bin/"),
            row('manifest keys no tool reads', unread[2], 'names',
                note=f'of {len(manifest)} in manifest.attrs; a literal grep of bin/'),
        ]),
        ('SECOND STATEMENTS — an enumeration the law owns, restated in a prose document', [
            row('restatements', [r['id'] for r in restated], 'lines',
                detail={r['id']: f"{r['where']}  {r['path']} — {r['of'][0]} of {r['of'][1]}" for r in restated}),
            row("...that name what the law's list does not", [r['id'] for r in differ], 'lines',
                detail={r['id']: f"{r['where']}  {r['path']} — names "
                                 f"{', '.join('`' + x + '`' for x in r['extra'])}" for r in differ}),
        ]),
        ('STORY IN THE LAW — when, who or where, told inside the law', [
            row('strings', [p for p, _h, _s in story], 'lines',
                detail={p: f"{p}  «{h}»  {s[:64]}{'…' if len(s) > 64 else ''}" for p, h, s in story}),
        ]),
        ('STATED, NOT CHECKED', [
            row('terms `enforced_by: none`', unchecked, 'names'),
        ]),
        ('ONE ESTATE IN THE STANDARD', [
            row(f'standard vacancies whose reason is `{_ONE_GARDENS_REASON}`',
                [f"{'profiles.' + p + '.' if p else ''}vacancies: {v.get('at')} {v.get('position')}"
                 for p, v in estate], 'lines', note=' · '.join(f'{p} {n}' for p, n in sorted(tiers.items()))),
        ]),
    ]


def _wrap(words, lead):
    return textwrap.fill(' '.join(str(w) for w in words), width=112, initial_indent=lead, subsequent_indent=lead,
                         break_on_hyphens=False, break_long_words=False)


def _say(line=''):
    """Print, and never fail on a character the console cannot show: a Windows console writing cp1252 has no `→`,
    and the law's own text has one. This tool always exits 0, and a crash on a glyph would be an exit."""
    enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
    print(str(line).encode(enc, 'replace').decode(enc, 'replace'))


def law_report(against=None):
    _say("dmreview --law: the preconditions of beauty in the law, counted — the person who merges judges")
    now = preconditions(Tree())
    if now is None:
        _say(f"  no law at {LAW_FILE}: nothing to count")
        return 0
    old = preconditions(Tree(against)) if against else None
    if against and old is None:
        _say(f"  --against {against}: git holds no {LAW_FILE} at that ref here, so the counts stand alone")
    _say(f"  {LAW_FILE}, std-vocab {(law_at() or {}).get('version')}, as the working tree holds it"
          + (f" · against {against}, std-vocab {(law_at(against) or {}).get('version')}" if old else ''))
    _say(_wrap("Nothing here passes or fails, and no count has a direction: a mechanism may make the law larger and "
                "better, and the cheapest way to lower a count is to fold a structured fact into prose. Each line is "
                "a question for whoever ratifies; the merge is the judgment.".split(), '  '))
    before = {(s, r['label']): r for s, rows in (old or []) for r in rows}
    for section, rows in now:
        _say(f"\n{section}")
        for r in rows:
            o = before.get((section, r['label'])) if old else None
            delta = ''
            if old:
                d = r['n'] - o['n'] if o else 0
                delta = '(not counted there)' if not o else f"(was {o['n']}, {d:+d})" if d else '(unchanged)'
            note = f"  {r['note']}" if r.get('note') else ''
            _say(f"  {r['label']:<50}{r['n']:>6}  {delta}{note}".rstrip())
            items = r['items'] or []
            was = (o or {}).get('items') or []
            new = [x for x in items if o and x not in was]
            gone = [x for x in was if x not in items]
            # `+` new since the ref, `-` gone since it: ASCII, because a Windows console writing cp1252 has no `−`
            if r['show'] == 'delta' and (new or gone):
                _say(_wrap(['+' + x for x in new] + ['-' + x for x in gone], '      '))
            elif r['show'] == 'names' and (items or gone):
                _say(_wrap([('+' if x in new else '') + str(x) for x in items] + ['-' + str(x) for x in gone],
                            '      '))
            elif r['show'] == 'lines':
                for x in items:
                    _say(f"    {'+ ' if x in new else '  '}{(r.get('detail') or {}).get(x, x)}")
                for x in gone:
                    _say(f"    - {(o.get('detail') or {}).get(x, x)}")
    _say("\n— evidence, not a verdict. This always exits 0; whoever merges decides what any of it means.")
    return 0


# ============================== PART B: THE EVIDENCE OVER A GARDEN'S BEANS ==============================
def load_docs():
    docs = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) + \
             sorted(glob.glob(os.path.join(ROOT, 'mappings', '*.md'))):
        h, body = dmparse.read(f)
        if h is None:
            continue
        try:
            fm = dmparse.loads(h) or {}
        except Exception:
            continue
        i = fm.get('bean') or fm.get('mapping')
        if i:
            docs[i] = (fm, body)
    return docs


DOCS = {}


def leaves(node, prefix=''):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from leaves(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from leaves(v, f"{prefix}[{i}]")
    elif isinstance(node, str):
        yield prefix, node


def factual():
    for b, (fm, _) in DOCS.items():
        for p, v in leaves(fm):
            if p.split('.')[0] in FACTUAL:
                yield b, p, v


def head(item, question):
    print(f"\n\033[1m{item}\033[0m" if sys.stdout.isatty() else f"\n{item}")
    print(f"  ? {question}")


def sample(rows, n=6):
    for r in (rows if ALL else rows[:n]):
        print(f"    {r}")
    if not ALL and len(rows) > n:
        print(f"    … {len(rows) - n} more (--all)")


def part_b():
    """The Part B evidence over this garden's beans: every signal a question, none a violation."""
    global DOCS
    DOCS = load_docs()
    print("dmreview — evidence for the judgments the gate cannot make. Nothing here is a violation.")

    # ---- Rule 6: paper-durable ----------------------------------------------------------------------
    head("CAPSULE / PAPER-DURABLE",
         "does this still read correctly cold, years later? A relative time word fixes prose to the day "
         "it was written, and the reader will not know which day that was.")
    REL = re.compile(r'\b(currently|current|today|yesterday|recently|now|at present|these days|soon|lately)\b', re.I)
    rows = [f"{b}.{p} -> '{REL.search(v).group(0)}'  {v[:70]}…" for b, p, v in factual() if REL.search(v)]
    print(f"  {len(rows)} occurrence(s) of a relative time word in a recorded fact")
    sample(rows)

    # ---- Rule 6: a key that carries a date ------------------------------------------------------------
    head("CAPSULE / KEY NAMES",
         "a key with a date in its NAME cannot be superseded — the next reader adds a second dated key "
         "rather than correcting the first. Is the date part of the fact, or part of when you learned it?")
    dated = [f"{b}.{sect}.{k}" for b, (fm, _) in DOCS.items() for sect in ('details', 'attributes', 'owns')
             for k in (fm.get(sect) or {}) if re.search(r'\d{4}[_-]\d{2}', str(k))]
    print(f"  {len(dated)} key(s) with a date baked into the name")
    sample(dated)

    # ---- external truth referenced, not mirrored -------------------------------------------------------
    head("EXTERNAL TRUTH REFERENCED, NOT MIRRORED",
         "the gate catches a VERBATIM duplicate. This is the paraphrase it cannot: two beans saying nearly "
         "the same thing, where one should own the fact and the other point at it. Structural similarity "
         "(sibling addons sharing a manifest shape) is fine — restated CONTENT is not.")
    # A transcription of external truth that is POINTED AT by a staleness-keyed cache entry is a CACHE,
    # not a mirror: it knows when it goes stale, and bin/dmstale.py checks. That is the legitimate form the
    # Part B item asks for, so those are marked rather than raised — an aid that keeps surfacing a settled
    # case teaches the reader to skim past the ones that matter.
    # THE FORM IS THE TERM'S, READ FROM IT. This test was a literal tuple of prefixes until 2026-09-20 —
    # `('git-head:', 'digest:')` — and std-vocab 11.0 replaced both with `<repo>@<sha>` without anyone
    # coming back here. Every tracked cache then failed the test, so this aid reported 0 CACHES and asked
    # the reader to judge 38 pairs it had already settled: the exact harm the note above warns about,
    # produced by the aid itself. `manual:` keys count too — an entry a person re-checks by hand is
    # tracked, just not machine-checkable, which is a different question and dmstale's to answer.
    import dmcheck as _law
    _STALENESS = dict(_law.dmform.facet(_law.form_of('analysis_cache'), 'pattern', 'entry')
                      ).get('staleness_key') or r'(?!)'   # no pattern in the law -> nothing matches, and
                                                           # the law's absence shows rather than passing
    cached = set()
    for _b, (_fm, _) in DOCS.items():
        for _ct, _e in (_fm.get('analysis_cache') or {}).items():
            if not re.match(_STALENESS, str(_e.get('staleness_key', ''))):
                continue
            _r = _e.get('summary_ref') or []
            for _ptr in (_r if isinstance(_r, list) else [_r]):
                if isinstance(_ptr, str) and '.' in _ptr:
                    cached.add(f"{_b}.{_ptr}")

    vals = [(b, p, v) for b, p, v in factual() if len(v) > 80]
    pairs = []
    _LO = 0.72
    # NEAR-DUPLICATE DETECTION, PAIRWISE — and difflib.ratio() is O(n*m) in the STRING LENGTHS, not in the
    # number of values. On 2026-08-07 this stopped terminating: the pair count grows as the square of the
    # corpus while each comparison grows as the product of two prose lengths, and a release that added a
    # lot of long prose pushed it past any useful runtime. It was NOT introduced by that release — the
    # committed version hangs on the same corpus — it was made reachable by it.
    #
    # THE FILTERS BELOW CHANGE NOTHING THAT IS REPORTED. Both are EXACT upper bounds on ratio():
    #   - 2*min(len)/(len_a+len_b) is the best ratio two strings of those lengths could possibly reach,
    #     since ratio() = 2*M/T and M cannot exceed the shorter string;
    #   - quick_ratio() is documented as an upper bound, computed on the multiset of characters, O(n).
    # A pair whose upper bound cannot reach the threshold cannot be a finding, so skipping it is not a
    # heuristic and loses no pair. Verified by comparing the full output against the unfiltered
    # implementation on a subset the slow one can still finish.
    #
    # seq2 is held fixed in the outer loop because SequenceMatcher caches the b2j index for its SECOND
    # sequence; varying seq1 inside reuses that work instead of rebuilding it for every pair.
    #
    # `autojunk` is left at its DEFAULT. An earlier attempt here passed autojunk=False, which is not a
    # speed knob: it changes which elements ratio() treats as junk and therefore changes the ratio itself,
    # so it would have silently altered which pairs are reported. A performance fix that moves a finding
    # is not a performance fix.
    _sm = difflib.SequenceMatcher(None)
    _ctr = [Counter(v) for _b, _p, v in vals]      # the character multiset, computed ONCE per value rather
                                                   # than rebuilt inside every pair, which is what
                                                   # SequenceMatcher.quick_ratio() has to do after set_seq1
    for j in range(len(vals)):
        _sm.set_seq2(vals[j][2])
        _lj, _cj = len(vals[j][2]), _ctr[j]
        for i in range(j):
            if vals[i][0] == vals[j][0]:
                continue
            _li = len(vals[i][2])
            if 2.0 * min(_li, _lj) / (_li + _lj) <= _LO:      # exact length bound — cannot reach threshold
                continue
            if 2.0 * sum((_ctr[i] & _cj).values()) / (_li + _lj) <= _LO:   # quick_ratio's bound, cached
                continue
            _sm.set_seq1(vals[i][2])
            r = _sm.ratio()
            if _LO < r < 1.0:
                pairs.append((r, f"{vals[i][0]}.{vals[i][1]}", f"{vals[j][0]}.{vals[j][1]}"))
    pairs.sort(reverse=True)
    tracked = [p for p in pairs if p[1] in cached and p[2] in cached]
    raw = [p for p in pairs if p not in tracked]
    bykey = Counter(p[1].split('.', 1)[1] for p in raw)
    print(f"  {len(tracked)} pair(s) are staleness-keyed CACHES of external truth — tracked, not mirrored, "
          f"and dmstale verifies them. Not a question.")
    print(f"  {len(raw)} pair(s) remain to judge"
          + (f"; most concentrated in: " + ", ".join(f"{k} ({n})" for k, n in bykey.most_common(3))
             if raw else ""))
    sample([f"{r:.0%}  {a}\n           {b}" for r, a, b in raw])

    # ---- provenance honest -----------------------------------------------------------------------------
    head("PROVENANCE HONEST",
         "an anchor may carry its own provenance where its source differs from its bean's — the model supports it, "
         "and the gate deliberately does NOT judge it (a rule to do so was tested and rejected). But it is "
         "also exactly where an agent can write `asserted-by-human` on a value it minted itself. Did a "
         "person actually assert these?")
    rows = [f"{b}: anchor {a['key']} provenance={a['provenance']}  (bean provenance src={src}, by={by[:44]})"
            for b, (fm, _) in DOCS.items()
            for src, by in [((fm.get('provenance') or {}).get('src'), str((fm.get('provenance') or {}).get('by', '')))]
            for a in ((fm.get('identity') or {}).get('anchors') or [])
            if isinstance(a.get('provenance'), dict) and a['provenance'].get('src') == 'asserted-by-human' and src != 'asserted-by-human']
    print(f"  {len(rows)} anchor(s) asserted by a person on a bean a person did not assert")
    sample(rows)

    # ---- abstraction, not force-fit ---------------------------------------------------------------------
    head("ABSTRACTION, NOT FORCE-FIT",
         "a key used exactly once is either a genuinely unique datum kept intact — which is correct — or a "
         "fact bent to fit a shape that nearly suited it. Only a reader can tell which.")
    kc = Counter(f"{sect}.{k}" for _b, (fm, _) in DOCS.items() for sect in ('attributes', 'details')
                 for k in (fm.get(sect) or {}))
    once = sorted(k for k, n in kc.items() if n == 1)
    print(f"  {len(once)} of {len(kc)} keys in attributes/details are used exactly once")
    sample(once, 8)

    # ---- the safety/risk split (added 2026-08-08, human-ratified reservation) ------------------------
    head("SAFETY NOTES THAT LOOK LIKE FINDINGS",
         "`details.safety` is RESERVED for mechanisms, lessons and constraints — how a thing works and what "
         "breaks it. A live defect belongs in `risks`, on the bean that owns the failing thing. Only a reader "
         "can tell which a sentence is, so these are the ones worth re-reading, not the ones that are wrong.")
    # WHY THIS SIGNAL EXISTS. On 2026-08-08 a consolidation swept every STRUCTURED risk carrier and missed
    # four live risks sitting in prose — the worst on a bean that already carried `risks` after the sweep.
    # The words below are the ones those four actually used; this is a regex over English and it will both
    # over- and under-fire, which is exactly why it prints questions and never fails a build.
    RISKY = re.compile(r'STILL OPEN|remains? open|rotation (is )?(still )?owed|is owed|un(pinned|guarded'
                       r'|proven|rotated)\b|SPOF|not (yet )?(fixed|closed|rotated)', re.I)
    flagged = []
    for _b, (fm, _) in DOCS.items():
        notes = (fm.get('details') or {}).get('safety') or []
        if isinstance(notes, str):
            notes = [notes]
        has_risks = 'risks' in fm
        for s in notes:
            if isinstance(s, str) and RISKY.search(s):
                flagged.append(f"{_b}{'' if has_risks else '  (no `risks` term at all)'}: {s[:96]}")
    print(f"  {len(flagged)} safety note(s) carry risk-shaped language")
    sample(flagged, 8)
    if not flagged:
        print("    none — which is a claim about this REGEX, not about the prose. A finding worded in words "
              "it does not match is still sitting there.")

    # ---- Tier-0 relations this garden has not drawn (moved here from the gate, 2026-09-17) ------------------
    head("TIER-0 RELATIONS NOBODY DRAWS",
         "the standard offers these edges and no bean in this garden uses one. A young or small garden may never "
         "need them, which is why the gate no longer warns. Is one of them the right way to say something a "
         "bean currently says in prose?")
    _gate = _law                         # already imported above, for the staleness form
    _gate.build_docs()
    _drawn = set(_gate.drawn_edges())
    _undrawn = sorted(t for t, s in _gate.SCHEMAS.items()
                      if (lambda _f: _gate.dmform.ref_attrs(_f, 'self') or _gate.dmform.ref_attrs(_f, 'entry'))(
                          _gate.dmform.attribute_form(None, s)) and t in _gate.TIER0_TERMS and t not in _drawn)
    print(f"  {len(_undrawn)} Tier-0 relation(s) drawn by no bean")
    sample(_undrawn, 12)

    print("\n— nothing above is a finding. If any of it becomes checkable with evidence, it belongs in the "
          "gate and leaves this file.")


def main(argv):
    if '--law' in argv:
        i = argv.index('--against') + 1 if '--against' in argv else None
        return law_report(argv[i] if i is not None and i < len(argv) else None)
    part_b()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
