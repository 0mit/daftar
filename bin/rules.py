#!/usr/bin/env python3
"""rules — print the rules this garden currently enforces: the core's law, as its gate reads it.

DERIVED, never written by hand: everything below is read out of the law the gate enforces (core/law/, read through
core/law.py as bin/check.py reads it, with the garden's own rows), so this listing cannot drift from the law. If a rule
appears here it is checked; if it is checked it appears here.

Usage: python3 bin/rules.py [--terms] [--core] [--every-profile]     (no --terms or --core = both)

`--core` the rules and the face — the statement, the order, the figures, the tables, the layers and the flow law;
`--terms` the verbs with their roles and qualifiers, the kinds, the namespaces, the forms (their attributes read by
bin/form.py) and the rows the garden adds, each used or vacant. `--every-profile` lists what every profile the law
offers gives, as a garden that took them all would be held to it: the whole law for a reader of the release.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse as dmparse
import form as dmform          # a term's law keyed by attribute — the one reader of the schema constructs
import importlib
dmpass = importlib.import_module('pass')          # where a value comes from: acts, a domain's origin, a rank by source
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _product():
    """`daftar v<tag>` — DERIVED from git, because the version lives in an annotated tag and nowhere else.
    Every version this repo ever typed into prose rotted (four titles reading v1.0 over v2 bodies, two
    stale pins); the two that stayed correct were derived. A tag has no second copy to disagree with.

    IN A GARDEN, the release its GARDEN.md says it adopted (`daftar_release`, written by germination and
    bin/dmupgrade.py), as the gate reads it: a garden's history carries no daftar tag, and describing it
    named the garden's own commits."""
    _g = _front(os.path.join(ROOT, 'GARDEN.md'))[0] if os.path.isfile(os.path.join(ROOT, 'GARDEN.md')) else None
    if isinstance(_g, dict) and _g.get('daftar_release'):
        return f"daftar {_g['daftar_release']}"
    try:
        import subprocess as _sp
        v = _sp.run(['git', '-C', ROOT, 'describe', '--tags', '--always', '--dirty'],
                    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5).stdout.strip()
        return f"daftar {v}" if v else "daftar (untagged)"
    except Exception:
        return "daftar (untagged)"

def _front(path):
    """A document's front matter, read as the gate reads it: (mapping or None, why it does not read)."""
    try:
        head_ = dmparse.read(path)[0]
    except dmparse.NotUTF8 as e:
        return None, str(e)
    except OSError as e:
        return None, f"cannot be read ({e.strerror})"
    if head_ is None:
        return None, "no --- fences"
    try:
        fm = dmparse.loads(head_)
    except Exception as e:
        return None, dmparse.escaped(str(e).splitlines()[0] if str(e) else type(e).__name__)
    return (fm if isinstance(fm, dict) else None), (None if isinstance(fm, dict) or fm is None else "not a mapping")


# ---- a garden of the core (v1 part 9) -------------------------------------------------------------------------------
# The rules of the core are its law's: the twenty-one rules and the face they judge by (core/law/core.yaml), the verbs' rows
# (verbs.yaml) with their roles and qualifiers, the kinds, levels, namespaces, units, layers and the flow law, the forms
# of a line and of a measure, and the rows the garden adds (VOCAB.md) — each read through core/law.py `Law`, the gate's
# one reader of it, so that what is listed is what the gate holds. `--core` is the rules and the face; `--terms` the
# verbs, the kinds, the forms and the garden's own rows (a statement's verb is what a term was).

def _say(*a):
    print(*(dmparse.said(x) for x in a))           # spelt out, as every line here is: a garden's words reach it


def _title(s):
    print(f"\n\033[1m{dmparse.said(s)}\033[0m" if sys.stdout.isatty() else f"\n{dmparse.said(s)}")
    print('─' * len(s))


def _spec(spec):
    """A role's or a qualifier's filler in words: its shapes, and the nature, rung, table or form it is held to."""
    if not isinstance(spec, dict):
        return str(spec)
    out = '|'.join(str(s) for s in (spec.get('shape') if isinstance(spec.get('shape'), list) else [spec.get('shape')]))
    held = [f"{k} {'|'.join(map(str, v)) if isinstance(v, list) else v}" for k in ('nature', 'rung', 'table', 'form')
            for v in [spec.get(k)] if v]
    return out + (f" ({', '.join(held)})" if held else '') + (' …many' if spec.get('many') == 'true' else '')


def _attrs(spec, ind='      '):
    """The lines of a form's attributes: `*` where required, and its domain in words — read by bin/form.py, the one
    reader of how an attribute is spelt."""
    f = dmform.core_form(spec)
    req = set(f['order'].get(('self', 'required'), []))
    out = [f"{ind}{k}{'*' if k in req else ''}: {dmform.label((rec or {}).get('in'))}"
           for k, rec in ((spec or {}).get('attrs') or {}).items()]
    return out + ([f"{ind}one of: {', '.join(f['one_of'])}"] if f['one_of'] else [])


def core_rules(argv):
    sys.path.insert(0, ROOT)
    from core.check import garden_law
    from core.law import Law
    from core.read import Unread
    try:
        L = garden_law(ROOT)
    except Unread as e:                    # VOCAB.md does not read: the law's rules are listed, and why without its rows
        _say(f"VOCAB.md does not read, so its rows are left out — {' '.join(str(e).split())}")
        L = Law.load()
    want = set(a for a in argv if a in ('--terms', '--core')) or {'--terms', '--core'}
    g = (_front(os.path.join(ROOT, 'GARDEN.md'))[0] if os.path.isfile(os.path.join(ROOT, 'GARDEN.md')) else None) or {}
    _say(f"{_product()} rules — core@{L.version} + garden '{g.get('garden')}', taking "
         + (', '.join(L.taken) or 'no profile') + (" — every profile listed" if '--every-profile' in argv else ''))
    if '--core' in want:
        _title(f"THE RULES — {len(L.rules)}, each strict: a breach is an error, and there are no warnings")
        for r in L.face.get('rules') or []:
            _say(f"  {str(r.get('rule')):12} {r.get('says')}")
        _title("THE STATEMENT — one verb, its roles from the seven, each filler of a shape")
        for r in L.face.get('roles') or []:
            _say(f"  {str(r.get('role')):8} {r.get('meaning')}")
        _say("  shapes: " + ' · '.join(str(s.get('shape')) for s in L.face.get('shapes') or []))
        _say("  beside the roles: " + ', '.join(sorted(L.beside)) + "; the words of a row: " + ', '.join(sorted(L.words)))
        _say("  the knowing acts: " + ', '.join(L.knowing) + " — every statement is the `of` of one in its bean")
        _title("THE ORDER — the natures, the lines and levels, the conditions, and the crown every chain ends at")
        for n in L.natures.values():
            _say(f"  nature {str(n.get('nature')):8} {n.get('meaning')}")
        for ln in L.lines.values():
            _say(f"  line {str(ln.get('line')):10} holds {', '.join(map(str, ln.get('holds') or [])) or '—'}")
        _say(f"  levels: {len(L.levels)} — `python3 bin/why.py <level>` says one")
        _say("  conditions: " + ', '.join(sorted(L.conditions)))
        for f in L.foundations:
            _say(f"  foundation {f.get('foundation')}: {f.get('meaning')}")
        for c in L.crown.values():
            _say(f"  crown: {c.get('crown')} — {c.get('law')}")
        _title("THE FIGURES — a position on a statement: contraries refused through one source, subcontraries both stand")
        for f in L.figures:
            _say(f"  {str(f.get('figure')):11} contraries "
                 + ' / '.join(f'{a}|{b}' for a, b in (f.get('positions') or {}).items()) + " · contradictories "
                 + ' / '.join(f'{a}|{b}' for a, b in (f.get('contradictory') or {}).items()))
        _title("THE TABLES — a role whose shape is `row` takes one of their rows")
        for t, rows in sorted(L.tables.items()):
            rows = [str(r) for r in rows]
            _say(f"  {t:13} {', '.join(rows[:16])}{' …' if len(rows) > 16 else ''}")
        _say("  the standards' (core/law/): " + ', '.join(sorted(L.standard_tables)) + f"; {len(L.units)} units, in UCUM")
        _title("LAYERS AND THE FLOW LAW — which passes between layers stand (rule layers)")
        _say("  layers: " + ', '.join(map(str, L.table('layers'))))
        for s in L.standing:
            _say(f"  {str(s.get('layer')):12} holds {', '.join(map(str, s.get('holds') or []))}")
        for f in L.flows:
            _say(f"  {str(f.get('grant')):9} {f.get('flow') or ''}: {f.get('from')} → {f.get('to')} through "
                 f"{f.get('through')}{' as ' + str(f['as']) if f.get('as') else ''}")
    if '--terms' in want:
        _title(f"THE VERBS — {len(L.verbs)}: each one's roles (`*` required), and the qualifiers its row declares")
        for name, v in L.verbs.items():
            req = set(map(str, v.get('required') or []))
            _say(f"  {name:10} {str(v.get('meaning') or '')[:150]}")
            for role, spec in (v.get('roles') or {}).items():
                _say(f"      {role}{'*' if role in req else ''}: {_spec(spec)}")
            for q, spec in (v.get('qualifiers') or {}).items():
                _say(f"      {q}{'*' if q in req else ''} (qualifier): {_spec(spec)}")
            if v.get('choice'):
                _say(f"      one of: {v.get('choice')}")
            if v.get('replaces'):
                _say(f"      replaces today's: {', '.join(map(str, v['replaces']))}")
        _title(f"THE KINDS — {len(L.kinds)}: what a bean records, each of a nature")
        for k, r in L.kinds.items():
            _say(f"  {k:22} {r.get('nature')}{' · ' + str(r.get('line')) if r.get('line') else ''}"
                 f"{' · ' + str(r.get('level')) if r.get('level') else ''}")
        _title(f"THE NAMESPACES — {len(L.namespaces)}: who gives a name, and whether once (rule names)")
        _say('  ' + ', '.join(f"{n}{' (once)' if r.get('once') == 'true' else ''}" for n, r in L.namespaces.items()))
        _title(f"THE PROFILES — {len(L.profiles)}: what a garden takes up beside the core (VOCAB.md `profiles`, rule "
               f"profile); this one takes {', '.join(L.taken) or 'none'}")
        for p, row in L.profiles.items():
            if p in L.taken or '--every-profile' in argv:
                verbs = [v for v in L.verbs if L.home(v) == p]
                _say(f"  {p:10} {'taken' if p in L.taken else 'not taken'} — verbs: {', '.join(verbs) or 'none'}"
                     + ''.join(f"; {k}: {', '.join(map(str, row[k]))}" for k in ('tables', 'forms') if row.get(k))
                     + ''.join(f"; adds to {f}: {', '.join(a.get('attrs') or {})}" for f, a in (row.get('adds') or {}).items())
                     + (f"; asset {row['asset']}" if row.get('asset') else ''))
        _title(f"THE FORMS — {len(L.forms)}: what a qualifier of the shape `form` holds (rules line, measured, profile)")
        for f, form in L.forms.items():
            _say(f"  {f}")
            for line in _attrs(form):
                _say(line)
        _title("THE GARDEN'S OWN ROWS — VOCAB.md, each used or said vacant (rule vacancy)")
        own = list(L.garden_rows) + [(k, r.get(next(iter(r))), r) for k, rs in L.own.items() for r in rs if r] \
            + [('flows', f.get('flow'), f) for f in L.garden_flows]
        for k, n, r in own:
            _say(f"  {k:10} {n}{'   vacant: ' + str(r.get('vacant')) if isinstance(r, dict) and r.get('vacant') else ''}")
        if not own:
            _say("  none: this garden adds no row to the law")
    if L.found:
        _title("NOT READ — what the law met in this garden's rows, and refuses")
        for _rule, where, msg in L.found:
            _say(f"  {where}: {msg}")
    return 0


if __name__ == '__main__':
    sys.exit(core_rules(sys.argv[1:]))
