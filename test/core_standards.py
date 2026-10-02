#!/usr/bin/env python3
"""The core's law is its own source (v1 part 13): what the files of core/law/ promise, held to them.

Until v1.0.0 the standards' tables were generated from today's law, and this suite held them equal to it. std-vocab is
gone; the files are the law, and this holds what they promise of themselves:
- no file of core/law/ says it is generated, and none names today's law as its source;
- every table of rows has its form — the standards' files under `forms`, the files of a line, a measure and the flow law
  under `columns` — and every row holds its form's required columns and no other: a stray column, or a required one
  missing, is refused by the law's own proof (core/check.py --law);
- the core's names of tables are the ones the core reads (`systems`, `protocols`, `types`, `gaps`), and no form names a
  table by today's name;
- a value the core renamed (soma, lekton, derived, said) is written in the core's word, and prose as written;
- the units: every unit measures a quantity of quantities.yaml, by its English name, with a factor of two whole numbers;
- the standards are read from core/law/ alone: a release's systems, protocols, quantities, currencies, zones and schemes,
  and its gate reads them.
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core import read, standards  # noqa: E402
from core.law import columns_problems  # noqa: E402

FAILS = []
PY = sys.executable
LAW_DIR = os.path.join(ROOT, 'core', 'law')


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


def text(name):
    with open(os.path.join(LAW_DIR, name), encoding='utf-8') as fh:
        return fh.read()


FILES = sorted(f for f in os.listdir(LAW_DIR) if f.endswith('.yaml'))

# ------------------------------------------------------------------------------------------- the source
said = [f for f in FILES if 'GENERATED' in text(f) or 'std-vocab' in text(f)]
check(f"no file of core/law/ ({len(FILES)}) says it is generated, or names today's law as its source", not said, said)
check("...and no generator is left: core/translate.py writes a garden's copy, never a file of the law",
      not re.search(r"(?m)^def (generated|law_as_strings|old_law)\(", open(os.path.join(ROOT, 'core', 'translate.py'),
                                                                        encoding='utf-8').read()))

# ------------------------------------------------------------------------------------------- each table in its form
found = columns_problems(LAW_DIR)
n_tables = sum(1 for f in FILES for k, v in read.data(os.path.join(LAW_DIR, f)).items()
               if f in ('systems.yaml', 'places.yaml', 'protocols.yaml', 'quantities.yaml', 'registries.yaml', 'lines.yaml',
                        'measures.yaml', 'flows.yaml') and isinstance(v, list) and v and all(isinstance(r, dict) for r in v))
check(f"every one of the {n_tables} tables of rows has its form, and every row holds the required columns and no other",
      n_tables >= 25 and not found, found[:6])

tmp = tempfile.mkdtemp(prefix='core-standards-')
try:
    rel = os.path.join(tmp, 'release')
    shutil.copytree(ROOT, rel, ignore=shutil.ignore_patterns('.git', '__pycache__', 'site'))
    r = subprocess.run([PY, os.path.join(rel, 'core', 'check.py'), '--law'], capture_output=True, text=True,
                       encoding='utf-8', cwd=rel)
    check("the core's law is whole in a release's copy: core/check.py --law, 0 errors", r.returncode == 0,
          (r.stdout + r.stderr)[-800:])
    for name, old, new, says in (
            ('systems.yaml', '    neighbours: none\n', '    neighbours: none\n    remark: x\n', "column `remark` is not in"),
            ('flows.yaml', '  - { method: ', '  - { stray: y, method: ', "column `stray` is not in"),
            ('lines.yaml', '  - { aggregate: ', '  - { meaningless: z, aggregate: ', "column `meaningless` is not in")):
        p = os.path.join(rel, 'core', 'law', name)
        was = open(p, encoding='utf-8').read()
        with open(p, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(was.replace(old, new, 1))
        r = subprocess.run([PY, os.path.join(rel, 'core', 'check.py'), '--law'], capture_output=True, text=True,
                           encoding='utf-8', cwd=rel)
        check(f"...a row of {name} holding a column its form lacks is refused by the law's proof, naming it",
              r.returncode == 1 and says in r.stdout, r.stdout[-600:])
        with open(p, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(was)
    p = os.path.join(rel, 'core', 'law', 'measures.yaml')
    was = open(p, encoding='utf-8').read()
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(re.sub(r'(?m)^(  - \{ placement: place), takes: none \}', r'\1 }', was, count=1))
    r = subprocess.run([PY, os.path.join(rel, 'core', 'check.py'), '--law'], capture_output=True, text=True,
                       encoding='utf-8', cwd=rel)
    check("...and a row missing a required column is refused, naming it", r.returncode == 1 and "holds no `takes`" in r.stdout,
          r.stdout[-600:])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ------------------------------------------------------------------------------------------- the core's names
texts = ''.join(text(f) for f in FILES)
old_names = [w for w in ('anchor_systems', 'net_protocols', 'value_types', 'gap_tokens') if f"registry: {w}" in texts]
check("no form in core/law/ names a table by today's name (anchor_systems, net_protocols, value_types, gap_tokens)",
      not old_names, old_names)
L = read.data(os.path.join(LAW_DIR, 'lines.yaml'))
check("the forms a value is written in and a series' gaps are the core's tables, `types` and `gaps`, each with its form",
      {'count', 'kebab', 'text', 'rows'} <= {r.get('type') for r in L.get('types') or []}
      and {'-', '?', '_'} <= {r.get('token') for r in L.get('gaps') or []}
      and set(L.get('columns') or {}) >= {'types', 'gaps'})
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

# ------------------------------------------------------------------------------------------- the units
quantities = {q['quantity'] for q in read.data(os.path.join(LAW_DIR, 'quantities.yaml'))['quantities']}
units = read.data(os.path.join(LAW_DIR, 'units.yaml'))['units']
bad = [u['unit'] for u in units if u.get('quantity') not in quantities or not u.get('name')
       or not (isinstance(u.get('factor'), list) and len(u['factor']) == 2 and all(str(x).isdigit() for x in u['factor']))]
check(f"every one of the core's {len(units)} units in UCUM measures a quantity of quantities.yaml, by its English name, "
      f"with a factor of two whole numbers", len(units) >= 55 and not bad, bad)

# ------------------------------------------------------------------------------------------- read from core/law/ alone
S = standards.here()
check(f"the standards read from core/law/: {len(S.systems)} systems, {len(S.protocols)} protocols, {len(S.quantities)} "
      f"quantities, {len(S.currencies)} currencies, {len(S.zones)} zones, {len(S.knowledge.schemes)} schemes",
      len(S.systems) > 50 and len(S.protocols) > 20 and len(S.quantities) > 15 and 'EUR' in S.currencies
      and 'Asia/Tehran' in S.zones and {'isco-08', 'isced-f-2013'} <= set(S.knowledge.schemes)
      and not S.code('isco-08:2522'),
      (len(S.systems), len(S.protocols), len(S.quantities), len(S.currencies), len(S.zones), S.code('isco-08:2522')))
check("...and the release carries no today's law: seed/std-vocab.md is gone",
      not os.path.exists(os.path.join(ROOT, 'seed', 'std-vocab.md')))

print(f"\ncore_standards: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
