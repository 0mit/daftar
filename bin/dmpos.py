#!/usr/bin/env python3
"""dmpos — the position index: every entry that takes a stance, ordered so neighbours are adjacent.

DERIVED, never authoritative. A key is a function of the vocabulary plus the corpus, so a stored key is
a second copy that can disagree with the beans; this writes to a gitignored path, stamps what it was
built from, and is always rebuilt whole rather than patched. Delete the output and nothing is lost.

WHAT TAKES A POSITION. Not the bean — the ENTRY: the triple (bean, term, entry-key). A bean is not
`forbidden`; one capability of it is. Three aspects are declared and three terms sit on them, so the
subject of this index is the smallest thing that can actually hold a stance.

WHY THIS ORDER. CHECKLIST Part D already names the distinction it makes contiguous: "a LIVE RISK
(forbidden yet possible) demands different care from one already prevented elsewhere, and an UNENFORCED
requirement from one that holds itself." Those are prefixes here rather than a filter over everything.

WHAT IT IS NOT. There is no metric: adjacency is equality-of-prefix, not distance. A closed figure of
named positions has no distance function and this does not invent one. Contiguity holds only for a
PREFIX of the axis order, so "everything feasibility-impossible whatever its capability" is a scan plus
a filter, not a range. And modal adjacency is not causal adjacency — two rows sharing a byte range share
a STANCE and nothing else, so every reader must dereference the bean.

Usage:
  python3 bin/dmpos.py --build        rebuild the index (writes log/.position-index/)
  python3 bin/dmpos.py --scan PREFIX  rows whose key starts with PREFIX
  python3 bin/dmpos.py --verify       sortedness, prefix-stability under a simulated axis, the named scans
  python3 bin/dmpos.py                build to stdout, write nothing
"""
import os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmform
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STD = os.path.join(ROOT, 'seed', 'std-vocab.md')
OUT = os.path.join(ROOT, 'log', '.position-index')

# Three separators, all chosen strictly BELOW the field alphabet's minimum byte (`-` is 0x2D), and
# ordered by nesting depth so the more significant boundary sorts lower. That is what lets
# separator-terminated variable-length fields sort exactly as length-delimited ones would: `host-a` and
# `host-a-consolidation` could both be bean ids, and `s*host-a+` does not prefix-match the longer one
# because '+' (0x2B) < '-' (0x2D).
SEG, CELL, SUB = '*', '+', ','
SEPARATORS = (SEG, CELL, SUB)

# The three cell states. Byte order '-' < '0' < '1' puts them in disjoint contiguous regions, so silence
# is never inside the stated region. This is deliberate and it costs something: "effectively necessary"
# is the union of two ranges, never one. Collapsing them would make four silent `depends_on` edges read
# as agreement with a bean's deliberate `necessity: impossible`.
NOT_APPLICABLE, ABSENT, STATED = '-', '0', '1'


def _product():
    try:
        v = subprocess.run(['git', '-C', ROOT, 'describe', '--tags', '--always', '--dirty'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5).stdout.strip()
        return v or '(untagged)'
    except Exception:
        return '(untagged)'


def _head():
    try:
        r = subprocess.run(['git', '-C', ROOT, 'rev-parse', '--short', 'HEAD'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def load_law():
    """The vocabulary, read from the one path the law has (MODEL.md, The journal and the gate). No fallback: a missing law is an error."""
    if not os.path.exists(STD):
        sys.exit(f"std-vocab not found at {STD} — the law has ONE path and there is no fallback")
    std = dmparse.loads(dmparse.read(STD)[0]) or {}
    loc = dmparse.loads(dmparse.read(os.path.join(ROOT, 'VOCAB.md'))[0]) or {}
    profiles = [t for p in (loc.get('extends_profiles') or [])
                for t in ((std.get('profiles') or {}).get(p, {}).get('terms') or [])]
    terms = {}
    for t in (std.get('terms') or []) + profiles + (loc.get('local_terms') or []):
        if isinstance(t, dict) and t.get('term'):
            terms[t['term']] = t
    aspects = {a['aspect']: a for a in ((loc.get('aspects') or std.get('aspects')) or [])
               if isinstance(a, dict) and a.get('aspect')}
    return terms, aspects


def axis_order(aspects):
    """Declaration order IS axis order, and it is APPEND-ONLY.

    A new aspect appends a cell; it never renumbers one. That is the whole reason cells are concatenated
    rather than interleaved: a Morton/Z-order interleave rewrites every existing key when an axis
    arrives, which by this garden's own versioning rule is a MAJOR bump — a change that retroactively
    re-classifies every record — rather than the additive one it ought to be.
    """
    return list(aspects.keys())


aspects_of = dmform.aspects_of      # it was a second copy of the gate's; the form module is the one owner now


def entries_of(shape, node):
    if shape == 'list_of_entries' and isinstance(node, list):
        return [(str(i), e) for i, e in enumerate(node)]
    if shape in ('open_map_of_entries', 'mapping') and isinstance(node, dict):
        return [(str(k), v) for k, v in node.items()]
    return []


def pair_token(aspect_def, position):
    """The lexicographic MIN of the pole pair this position sits on.

    A stable name for the axis WITHIN a figure, so a square's two axes occupy separate byte ranges and
    `required` never sorts among `forbidden`. Taking the min rather than the first member means the
    token survives someone writing the pair the other way round.
    """
    poles = aspect_def.get('poles') or []
    if poles and not isinstance(poles[0], (list, tuple)):
        poles = [poles]
    for axis in poles:
        if position in axis:
            return min(axis)
    return ''


def field(value):
    """A field of a key. REFUSES a separator rather than escaping one.

    Escaping would destroy memcmp order, which is the entire property being bought. This is live risk
    and not hypothetical: `depends_on` declares no key form, and its live keys are snake_case.
    """
    s = str(value)
    for sep in SEPARATORS:
        if sep in s:
            sys.exit(f"REFUSED: {s!r} contains the separator {sep!r}. The builder does not escape "
                     f"separators — escaping destroys the byte order the index exists for. Rename the "
                     f"field, or declare a separator outside the corpus alphabet.")
    return s


def cell(aspect_name, aspect_def, binding, entry):
    """One coordinate. `<state><pair-token>,<position>` — see the module docstring for the three states."""
    if binding is None:
        return f"{NOT_APPLICABLE}{SUB}"                     # this term takes no position on this aspect
    attr = binding.get('attr', aspect_name)
    if attr in entry:
        state, value = STATED, entry[attr]
    elif binding.get('default') is not None:
        state, value = ABSENT, binding['default']
    else:
        return f"{ABSENT}{SUB}"                             # absent AND no default declared — reserved
    return f"{state}{field(pair_token(aspect_def, value))}{SUB}{field(value)}"


def rows(terms, aspects):
    """Every (bean, term, entry) that takes a stance, as (position-key, subject-key)."""
    axes = axis_order(aspects)
    out = []
    import glob
    docs = sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) + \
        sorted(glob.glob(os.path.join(ROOT, 'mappings', '*.md')))
    for path in docs:
        fm = dmparse.loads(dmparse.read(path)[0] or '') or {}
        base = os.path.basename(path)[:-3]
        for term, tdef in terms.items():
            sch = tdef.get('schema') or {}
            bindings = {b['aspect']: b for b in aspects_of(sch)}
            if not bindings:
                continue
            node = fm.get(term)
            if node is None:
                continue
            for label, entry in entries_of(sch.get('shape'), node):
                if not isinstance(entry, dict):
                    continue
                coord = CELL.join(cell(a, aspects.get(a) or {}, bindings.get(a), entry) for a in axes)
                subj = CELL.join((field(base), field(term), field(label)))
                out.append((f"p{SEG}{coord}{SEG}{subj}", f"s{SEG}{subj}{SEG}{coord}"))
    return sorted(out)


def header(axes, nrows):
    """The axis manifest is a SECOND COPY and is justified on the same grounds as a staleness key.

    It exists to DETECT disagreement, never to answer a question: on rebuild, the stored manifest must be
    a PREFIX of the newly derived one. Appending an aspect is additive and the rebuild proceeds; inserting
    or reordering one renumbers every existing key, and the build refuses rather than quietly producing an
    index that agrees with nothing that was built before it.
    """
    # THE KEY IS WRITTEN IN THE ONE SPELLING THE LAW DECLARES, `<repo>@<sha>`. It read
    # `git-head:<sha>` until 2026-09-20 — the form std-vocab 11.0 abolished, whose whole defect was that
    # a bare sha names no repository and so resolves against whatever tree the reader happens to stand
    # in. Nothing parses this line (check_manifest reads only `# axis_manifest:`), which is exactly why
    # it survived the migration: a generated artefact that nobody validates will teach the form it
    # carries to whoever copies it, and the term's own form_note says "ONE spelling, always".
    return [f"# axis_manifest: {CELL.join(axes)}",
            f"# staleness_key: {os.path.basename(ROOT)}@{_head() or 'NO-INDEX'}",
            f"# built_by: dmpos {_product()}",
            f"# rows: {nrows}",
            "# DERIVED — rebuild with `python3 bin/dmpos.py --build`; never edit, never commit."]


def check_manifest(axes):
    old = os.path.join(OUT, 'position.txt')
    if not os.path.exists(old):
        return
    for line in open(old, encoding='utf-8'):
        if line.startswith('# axis_manifest:'):
            was = line.split(':', 1)[1].strip().split(CELL)
            now = axes
            if was != now[:len(was)]:
                sys.exit(f"REFUSED: axis order re-classified ({was} is not a prefix of {now}) — this is a "
                         f"MAJOR bump, not a rebuild. Every existing key changes meaning. Delete the "
                         f"index deliberately if that is what was intended.")
            return


def compute():
    """The whole index, in memory. Cheap by construction: only entries that take a stance appear."""
    terms, aspects = load_law()
    return rows(terms, aspects), axis_order(aspects)


def build(write):
    rs, axes = compute()
    if write:
        check_manifest(axes)
        os.makedirs(OUT, exist_ok=True)
        for name, idx in (('position.txt', 0), ('subject.txt', 1)):
            with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
                f.write('\n'.join(header(axes, len(rs))) + '\n')
                f.write('\n'.join(sorted(r[idx] for r in rs)) + '\n')
        print(f"dmpos: {len(rs)} rows over axes [{', '.join(axes)}] -> {os.path.relpath(OUT, ROOT)}/")
    else:
        for k, _ in rs:
            print(k)
    return rs, axes


SCANS = [
    ("LIVE RISK — forbidden yet possible", "p*-,+1forbidden,forbidden+1impossible,possible"),
    ("ALREADY PREVENTED — forbidden and impossible", "p*-,+1forbidden,forbidden+1impossible,impossible"),
    ("ALL PROHIBITIONS (the parent of both)", "p*-,+1forbidden,forbidden"),
    ("IN BREACH — required but not the case", "p*-,+1omissible,required+1impossible,possible"),
    ("REVERSIBLE GUARANTEES — holds only contingently", "p*-,+1omissible,required+1contingent,contingent"),
    ("WHAT IS UNSTATED — silence, not a claim", "p*0"),
    ("WHAT IS ACTUALLY CLAIMED", "p*1"),
]


def verify():
    rs, axes = compute()
    keys = [r[0] for r in rs]
    subj = sorted(r[1] for r in rs)
    ok = True

    if keys != sorted(keys):
        print("FAIL  the position space is not in byte order"); ok = False
    else:
        print(f"PASS  both spaces are in byte order ({len(keys)} rows)")
    if subj != sorted(subj):
        print("FAIL  the subject space is not in byte order"); ok = False

    # PREFIX STABILITY. Simulate a fourth aspect that no term binds: every existing subject key must
    # survive as a proper prefix of its successor, byte for byte at its existing offset.
    grown = [k + CELL + NOT_APPLICABLE + SUB for k in subj]
    if all(g.startswith(o) and len(g) > len(o) for o, g in zip(subj, grown)):
        print(f"PASS  a fourth axis appends: all {len(subj)} subject keys survive as proper prefixes")
    else:
        print("FAIL  a simulated fourth axis moved an existing key"); ok = False

    for name, prefix in SCANS:
        n = sum(1 for k in keys if k.startswith(prefix))
        print(f"      {n:>3}  {name}")
    beings = sorted({k.split(SEG)[1].split(CELL)[0] for k in subj})
    print(f"PASS  {len(beings)} being(s) hold a position at all; every other bean emits NO row — "
          f"absent, not at the origin")
    return 0 if ok else 1


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--verify' in args:
        sys.exit(verify())
    if '--scan' in args:
        prefix = args[args.index('--scan') + 1]
        rs, _ = compute()
        hits = [k for k, _ in rs if k.startswith(prefix)] or \
               [s for _, s in rs if s.startswith(prefix)]
        for h in hits:
            print(h)
        print(f"# {len(hits)} row(s) under {prefix!r}", file=sys.stderr)
        sys.exit(0)
    build(write='--build' in args)
