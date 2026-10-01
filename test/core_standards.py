#!/usr/bin/env python3
"""The core's law as generated: every file core/translate.py generates is what today's law generates, and loses nothing.

Until v1 retires std-vocab, the law's rows have one source, and core/law/ holds what is generated from it (v1 plan, part
1). Checks:
- each generated file (levels, kinds, layers, and the standards' tables) is byte for byte what the law generates now;
- each standard's table, read back as the core reads it, is the law's table, its values in the core's words, and its
  form the law's `registry_forms` entry;
- the core's names of tables (`systems`, `protocols`) are the ones the core reads, and no value names the law's;
- the units: every unit of today's law has its UCUM row, by its English name, measuring what the law says it does;
- the standards are read from core/law/ alone: a release with no seed/std-vocab.md still has its systems, protocols,
  quantities, currencies, zones and schemes — and its gate reads them;
- a value the core renamed (soma, lekton, derived, said) is written in the core's word, and prose as written;
- a scalar with a backslash, a quote or a line break comes back from the generated text as written.
"""
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core import read, standards, translate  # noqa: E402

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


LAW_DIR = os.path.join(ROOT, 'core', 'law')
LAW = translate.law_as_strings()

# ------------------------------------------------------------------------------------------- generated, byte for byte
stale = []
for name in translate.GENERATED:
    with open(os.path.join(LAW_DIR, name + '.yaml'), encoding='utf-8') as fh:
        if fh.read() != translate.generated(name):
            stale.append(name)
check(f"each of the {len(translate.GENERATED)} generated files of core/law/ ({', '.join(translate.GENERATED)}) is what the "
      f"law generates now", not stale,
      f"{', '.join(stale)}: run `python3 core/translate.py law`, and commit what it writes as a RULE-CHANGE")

# ------------------------------------------------------------------------------------------- the tables, read back
lost, forms_off = [], []
for name, (_what, tables) in translate.STANDARDS.items():
    held = read.data(os.path.join(LAW_DIR, name + '.yaml'))
    for new, old in tables:
        if held.get(new) != translate.in_core_words(LAW.get(old)):
            lost.append(f"{name}.yaml {new} (the law's `{old}`)")
        if old in (LAW.get('registry_forms') or {}) and (held.get('forms') or {}).get(new) != \
                translate.in_core_words(LAW['registry_forms'][old]):
            forms_off.append(f"{name}.yaml forms.{new}")
    extra = set(held) - {new for new, _old in tables} - {'forms'}
    if extra:
        lost.append(f"{name}.yaml holds {sorted(extra)}, which no table of it names")
n_tables = sum(len(t) for _w, t in translate.STANDARDS.values())
n_rows = sum(len(LAW.get(old) or []) for _w, t in translate.STANDARDS.values() for _n, old in t)
check(f"each of the {n_tables} standards' tables ({n_rows} rows and entries), read back as the core reads it, is the "
      f"law's, in the core's words", not lost, lost)
check("...and each carries its form: the law's `registry_forms` entry, its registries named as the core names them",
      not forms_off, forms_off)
names = translate.TABLE_NAMES
check("the law's `anchor_systems` is the core's `systems`, and `net_protocols` its `protocols` (the table verbs.yaml "
      "names)", names == {'anchor_systems': 'systems', 'net_protocols': 'protocols'}, names)
texts = ''.join(open(os.path.join(LAW_DIR, n + '.yaml'), encoding='utf-8').read() for n in translate.STANDARDS)
named = [w for w in names if f"registry: {w}" in texts]
check("...and no form in core/law/ names a table by the law's name", not named, named)

# ------------------------------------------------------------------------------------------- the core's words
shape = read.data(os.path.join(LAW_DIR, 'systems.yaml'))['system_shape']['sources']
check("a value the core renamed is written in its word: the shape's sources are acts `derive`, `read`, `say` of a "
      "`body` or a `sayable`, never derived/said/soma/lekton",
      shape['reckoning']['arithmetic'] == {'act': 'derive', 'nature': 'sayable'}
      and shape['reckoning']['astronomical'] == {'act': 'read', 'nature': 'body'}
      and shape['crosswalk']['table'] == {'act': 'say', 'nature': 'sayable'}
      and shape['datum']['host']['nature'] == ['body', 'sayable'], shape)
sysrow = standards.here().systems['unix-filesystem']
check("...and prose is kept as written, every value a string: `establishes` is the string `false`, a pattern its own "
      "backslashes", sysrow['establishes'] == 'false'
      and standards.here().systems['git-remote']['pattern'].endswith(r'[^ ]*\.git)|[a-z][a-z0-9+.-]*://[^ ]+)$'),
      sysrow)
odd = {'k': 'a "quoted" back\\slash\nand a line', 'n': ['-', '', 'true', '2015.0', 'ü: x', '#']}
back = read.loads('\n'.join(translate._block('t', odd, '')), 'the odd scalars')
check("a scalar with a quote, a backslash, a line break, a lone dash, an empty string, a word YAML 1.1 reads as a "
      "boolean, a colon or a hash comes back from the generated text as written", back == {'t': odd}, back)

# ------------------------------------------------------------------------------------------- the units
old_units = {str(u['unit']): str(u['quantity']) for u in LAW.get('units') or []}
by_name = {}
for row in read.data(os.path.join(LAW_DIR, 'units.yaml'))['units']:
    by_name.setdefault(row.get('name'), []).append(row)
missing = [n for n in old_units if n not in by_name]
wrong = [f"{n}: {q} in the law, {by_name[n][0].get('quantity')} in its row" for n, q in old_units.items()
         if n in by_name and by_name[n][0].get('quantity') != q]
check(f"every one of the law's {len(old_units)} units has its UCUM row in core/law/units.yaml, by its English name, "
      f"measuring what the law says it measures", old_units and not missing and not wrong, missing + wrong)

# ------------------------------------------------------------------------------------------- read from core/law/ alone
S = standards.here()
check(f"the standards read from core/law/: {len(S.systems)} systems, {len(S.protocols)} protocols, {len(S.quantities)} "
      f"quantities, {len(S.currencies)} currencies, {len(S.zones)} zones, {len(S.knowledge.schemes)} schemes",
      len(S.systems) == len(LAW['anchor_systems']) and len(S.protocols) == len(LAW['net_protocols'])
      and len(S.quantities) == len(LAW['quantities']) and 'EUR' in S.currencies and 'Asia/Tehran' in S.zones
      and {'isco-08', 'isced-f-2013'} <= set(S.knowledge.schemes) and not S.code('isco-08:2522'),
      (len(S.systems), len(S.protocols), len(S.quantities), len(S.currencies), len(S.zones), S.code('isco-08:2522')))

tmp = tempfile.mkdtemp(prefix='core-standards-')
try:
    rel = os.path.join(tmp, 'release')
    shutil.copytree(ROOT, rel, ignore=shutil.ignore_patterns('.git', '__pycache__', 'site'))
    os.remove(os.path.join(rel, 'seed', 'std-vocab.md'))
    probe = ("import sys; sys.path.insert(0, %r); from core import standards; S = standards.Standards(%r); "
             "print(len(S.systems), len(S.protocols), len(S.quantities), 'EUR' in S.currencies, 'Asia/Tehran' in S.zones, "
             "repr(S.code('isco-08:2522')))" % (rel, rel))
    r = subprocess.run([PY, '-c', probe], capture_output=True, text=True, encoding='utf-8')
    want = f"{len(LAW['anchor_systems'])} {len(LAW['net_protocols'])} {len(LAW['quantities'])} True True ''"
    check("a release with no seed/std-vocab.md reads every standard from core/law/ alone", r.stdout.strip() == want,
          (r.stdout + r.stderr)[-800:])
    r = subprocess.run([PY, os.path.join(rel, 'core', 'check.py'), '--law'], capture_output=True, text=True, encoding='utf-8', cwd=rel)
    check("...and the core's law is whole there: core/check.py --law, 0 errors", r.returncode == 0,
          (r.stdout + r.stderr)[-800:])
    # a law changed after its rows were generated: the generated file is stale, and this suite says which
    with open(os.path.join(ROOT, 'seed', 'std-vocab.md'), encoding='utf-8') as fh:
        text = fh.read()
    changed = text.replace('meaning: "the Earth"', 'meaning: "the Earth, our body"', 1)
    with open(os.path.join(rel, 'seed', 'std-vocab.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(changed)
    probe = ("import sys; sys.path.insert(0, %r); from core import translate; "
             "print([n for n in translate.GENERATED if open('core/law/' + n + '.yaml', encoding='utf-8').read() "
             "!= translate.generated(n)])" % rel)
    r = subprocess.run([PY, '-c', probe], capture_output=True, text=True, encoding='utf-8', cwd=rel)
    check("a row of the law changed after it was generated leaves its file stale, and only that file: places.yaml",
          changed != text and r.stdout.strip() == "['places']", (r.stdout + r.stderr)[-800:])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\ncore_standards: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
