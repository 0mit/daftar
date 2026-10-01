#!/usr/bin/env python3
"""The core engine (core/): the law proved whole, a garden written in statements, every verb row, and every rule.

Reads with every value a string, and refuses a key written twice. Reads positions in the standards' systems: a day that
does not exist, a bare number two systems read, an extent that runs backwards, a day with no zone to be reckoned in.
Proves the face, the verbs' rows and the levels consistent. Judges the refinery's example garden (with the corrections
the engine makes) and finds nothing; finds nothing in the cases that must pass beside it; and refuses each bad case by
the rule it names, every rule but `ratify` (the commit's) having one. Then, for each of the law's verbs, a statement
made from its own row — its required roles, then every role — passes; dropping a required role, adding one it does not
take, and filling a role with what fits no shape are each refused. Last, `core/check.py` judges a garden on disk.
"""
import os, shutil, subprocess, sys, tempfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core import engine, frame, read  # noqa: E402
from core.law import Law, listed, shapes_of  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


# ------------------------------------------------------------------------------------------------ reading
r = read.loads("on: 2026-10-01\nshare: 1\nflag: true\n")
check("every key and value is read as a string: `on`, a day, a number, a flag",
      r == {'on': '2026-10-01', 'share': '1', 'flag': 'true'}, r)
try:
    read.loads("a: 1\nb: 2\na: 3\n")
    check("a key written twice is refused", False)
except read.Unread as e:
    check("a key written twice is refused, before YAML can keep only the last", 'written twice' in str(e), e)

# ------------------------------------------------------------------------------------------------ the frame
LAW0 = Law.load()
S = LAW0.std.systems
ZONE = 'Asia/Tehran'
for text, system in [('2026-10-01', 'gregorian-civil'), ('persian:1405-07-09', 'persian-calendar'),
                     ('192.0.2.10', 'ipv4'), ('2001:db8::1', 'ipv6'), ('tcp-port:445', 'tcp-port'),
                     ('ordinal:3', 'ordinal-number'), ('EPSG:4326;35.6892,51.3890', 'geographic'),
                     ('2026-10-01/2027-09-30', 'gregorian-civil'), ('persian:1405-07-09/1406-07-08', 'persian-calendar'),
                     ('2026-10-01 10:00+03:30', 'gregorian-civil'), ('1727740800000', 'unix-epoch'),
                     ('ordinal:3/5', 'ordinal-number'), ('now', 'now')]:
    try:
        got = frame.read(text, S, ZONE).system
    except frame.Refused as e:
        got = f"refused: {e}"
    check(f"the frame reads {text!r} in {system}", got == system, got)
for text, why in [('445', 'read by 3 systems'), ('next tuesday', 'in no system'), ('persian:1404-12-30', 'not a day'),
                  ('2026-02-30', 'not a day'), ('2027-01-01/2026-01-01', 'starts after it ends'),
                  ('2026-10-01T24:30+03:30', 'no clock reading'), ('2001:DB8::1', 'in no system')]:
    try:
        frame.read(text, S, ZONE)
        check(f"the frame refuses {text!r}", False, 'read')
    except frame.Refused as e:
        check(f"the frame refuses {text!r}: {e}", why in str(e), e)
try:
    frame.read('2026-10-01', S, None)
    check("a day with no zone to be reckoned in is refused", False)
except frame.Refused as e:
    check("a day with no zone to be reckoned in is refused: its place half is the bearer's", 'names none' in str(e), e)

# ------------------------------------------------------------------------------------------------ the law
check("the law is whole: the face's 21 verbs, the 35 rows and the 22 levels, 0 problems",
      not LAW0.problems() and len(LAW0.verbs) == 56 and len(LAW0.levels) == 29, LAW0.problems())
CASES = read.data(os.path.join(ROOT, 'test', 'core-cases.yaml'))
LAW = Law.load(('VOCAB.md', CASES['vocab']))
check(f"...and with the cases' own rows ({len(LAW.kinds)} kinds, {len(LAW.namespaces)} namespaces, {len(LAW.flows)} "
      f"flows)", not LAW.problems(), LAW.problems())
units = LAW0.units
check(f"units are UCUM's, the law's English name attached: every one of the law's {len(LAW0.std.units)} units has its row "
      f"(kg is kilogram, GiBy gibibyte, {{item}} item), and the two attenuations UCUM cannot write (§22) say why",
      len(units) == len(LAW0.std.units) == 55 and units['kg']['name'] == 'kilogram' and units['GiBy']['name'] == 'gibibyte'
      and units['{item}']['name'] == 'item' and [u for u, r in units.items() if r.get('ucum') == 'false']
      == ['decibel-per-metre', 'decibel-per-kilometre'], len(units))
check("...a unit written by its English name is refused, naming its code; a currency is ISO 4217's",
      "English name of `kg`" in LAW0.has('units', 'kilogram') and not LAW0.has('units', 'XTS')
      and LAW0.has('units', 'dB/m'), LAW0.has('units', 'kilogram'))
bad_law = Law.load(('VOCAB.md', {'kinds': [{'kind': 'poem', 'nature': 'sayable', 'line': 'made', 'level': 'device'},
                                            {'kind': 'stone', 'nature': 'body', 'line': 'said', 'level': 'discourse'}],
                                 'verbs': [{'verb': 'pay', 'roles': {}}],
                                 'tables': {'modes': ['grudging'], 'units': ['furlong']},
                                 'units': [{'unit': 'fur', 'name': 'furlong', 'quantity': 'distance'}]}))
probs = bad_law.problems()
check("the law refuses a sayable placed on the made and a body on the said, a verb of a name taken, a row added to the "
      "face's table, a unit added as a bare name, and a unit of a quantity the law has not",
      sum('a kind' in m for _r, _w, m in probs) == 2 and any('declared already' in m for _r, _w, m in probs)
      and any('a table of the face' in m for _r, _w, m in probs) and any('a row of `units`' in m for _r, _w, m in probs)
      and any("'distance' is no quantity" in m for _r, _w, m in probs), probs)


# ------------------------------------------------------------------------------------------------ a garden
def bean(bid, kind, statements, header=None):
    h = {'bean': bid, 'kind': kind, 'title': bid, 'statements': statements}
    h.update(header or {})
    return engine.Bean(bid, header=h)


def garden(extra=(), base=True, zone=ZONE):
    beans = {bid: bean(bid, b['kind'], b['statements']) for bid, b in CASES['garden'].items()} if base else {}
    for b in extra:
        beans[b.id] = b
    return engine.Garden(beans, zone, files=['VOCAB.md', 'GARDEN.md', 'log/journal.md'])


def judge(g, law=LAW):
    return engine.Judge(law, g).run()


G0 = garden()
found = judge(G0)
n = sum(len(b.statements) for b in G0.beans.values())
check(f"the example garden ({len(G0.beans)} beans, {n} statements) passes", not found, found)
for c in CASES['good']:
    found = judge(garden([bean(c['bean'], c['kind'], c['statements'])]))
    check(f"passes: {c['name']}", not found, found)
for c in CASES['bad']:
    found = judge(garden([bean(c['bean'], c['kind'], c['statements'], c.get('header'))]))
    hit = next((f"{w}: {m}" for rule, w, m in found if rule == c['rule']), None)
    check(f"rule {c['rule']}: {c['bean']} is refused — {hit}", hit is not None, found)
tested = {c['rule'] for c in CASES['bad']}
check("every rule but `ratify` has a case refused", tested == set(LAW.rules) - {'ratify'}, set(LAW.rules) - tested)
found = judge(garden([bean('z1', 'document', [{'say': {'by': 'sam', 'at': 'now'}}, {'mark': {'by': 'sam', 'at': '2026-10-01'}}])],
                     zone=None))
check("a garden that names no zone leaves a day nowhere, and the day is refused", any(r == 'frame' for r, _w, _m in found), found)
found = judge(garden(zone='Mars/Olympus'))
check("a zone the time zone database does not name is refused", any(w == 'GARDEN.md' for _r, w, _m in found), found)

# ------------------------------------------------------------------------------------------------ every verb's row
# A statement is made from each row by the row alone, so the gate is seen to read what a verb takes from the law. The
# beings are four of known kinds; a role takes the first that fits it, in an order that keeps the rules quiet (`come`
# through hands, `stand` at another being); a statement filler names `s1`, in the same bean.
POOL = {'by': ['box', 'firm', 'pat'], 'of': ['firm', 'box', 'pat'], 'through': ['pat', 'firm', 'box'],
        'to': ['firm', 'pat', 'box'], 'from': ['firm', 'pat', 'box'], 'at': ['firm', 'box', 'pat'], 'as': ['firm']}
STANDARD = {'protocols': 'smb', 'knowledge': 'isco-08:2511', 'properties': 'length', 'units': 'kg'}
OVERRIDE = {('pass', 'from'): 'world', ('pass', 'to'): 'journal', ('pass', 'through'): 'read'}
CONTEXT = [bean('pat', 'person', [{'say': {'by': 'pat', 'at': 'now'}}]),
           bean('firm', 'org', [{'say': {'by': 'pat', 'at': 'now'}}]),
           bean('box', 'host', [{'say': {'by': 'pat', 'at': 'now'}}])]
J = engine.Judge(LAW, garden(CONTEXT, base=False))
T = bean('t', 'document', [])


def filler(verb, role, spec):
    if (verb, role) in OVERRIDE:
        return OVERRIDE[(verb, role)]
    shape = shapes_of(spec)[0]
    if shape == 'being':
        x = next((b for b in POOL.get(role, POOL['by']) if not J.why_not('being', b, spec, T)), None)
    elif shape == 'statement':
        x = 's1'
    elif shape == 'position':
        x = 'now' if verb in LAW.knowing else '2026-10-01'
    elif shape == 'quantity':
        x = {'count': '1', 'unit': 'XTS'}
    elif shape == 'row':
        t = spec.get('table')
        x = STANDARD.get(t) or (LAW.table(t) or [None])[0]
    else:
        x = 'words'
    return [x] if spec.get('many') == 'true' else x


def made(verb, roles):
    return [{'say': {'by': 'pat', 'at': 'now'}}, {'do': {'id': 's1', 'by': 'firm', 'as': 'web'}}, {verb: roles}]


def verdict(verb, roles):
    return judge(garden(CONTEXT + [bean('t', 'document', made(verb, roles))], base=False))


for verb, v in LAW.verbs.items():
    specs = dict(v.get('roles') or {})
    specs.update(v.get('qualifiers') or {})
    req = listed(v.get('required'))
    left_out = set(listed((v.get('choice') or {}).get('one_of'))[1:])
    minimal = {k: filler(verb, k, specs[k]) for k in req}
    for k in listed((v.get('choice') or {}).get('one_of'))[:1]:
        minimal[k] = filler(verb, k, specs[k])
    full = {k: filler(verb, k, s) for k, s in specs.items() if k not in left_out}
    problems = []
    got = verdict(verb, minimal)
    if verb == 'necessary':            # the rule `necessity`: only the crown is necessary by itself
        if [r for r, _w, _m in got] != ['necessity']:
            problems.append(('minimal, refused only by necessity', got))
    elif got:
        problems.append(('minimal', minimal, got))
    got = verdict(verb, full)
    if got:
        problems.append(('full', full, got))
    for k in req + listed((v.get('choice') or {}).get('one_of'))[:1]:
        less = {x: y for x, y in full.items() if x != k}
        if 'valency' not in {r for r, _w, _m in verdict(verb, less)}:
            problems.append(('without', k))
    if 'form' not in {r for r, _w, _m in verdict(verb, dict(full, colour='blue'))}:
        problems.append(('a role it does not take', 'colour'))
    for k in full:
        rules = {r for r, _w, _m in verdict(verb, dict(full, **{k: {'nonsense': 'x'}}))}
        if not rules & {'valency', 'frame'}:
            problems.append(('no shape in', k, rules))
    alone = "refused only by `necessity` with its required role alone" if verb == 'necessary' else \
        f"passes with its required roles only ({', '.join(minimal)})"
    check(f"verb {verb}: its row's statement {alone} and whole ({len(full)} roles); "
          f"each of {len(req)} required roles is required; a role it does not take and a filler of no shape are refused",
          not problems, problems)

# ------------------------------------------------------------------------------------------------ on disk
TMP = tempfile.mkdtemp(prefix='dmcore-')
try:
    os.makedirs(os.path.join(TMP, 'beans'))
    os.makedirs(os.path.join(TMP, 'log'))

    def write(rel, head, body=''):
        with open(os.path.join(TMP, rel), 'w', encoding='utf-8') as fh:
            fh.write('---\n' + yaml.safe_dump(head, allow_unicode=True, sort_keys=False) + '---\n' + body)
    write('GARDEN.md', {'garden': 'core-test', 'gardener': 'sam', 'zone': ZONE})
    write('VOCAB.md', dict({'vocab': 'core-test'}, **CASES['vocab']))
    with open(os.path.join(TMP, 'log', 'journal.md'), 'w', encoding='utf-8') as fh:
        fh.write('# journal\n')
    for bid, b in CASES['garden'].items():
        write(f"beans/{bid}.md", {'bean': bid, 'kind': b['kind'], 'title': bid, 'statements': b['statements']}, '\nWords.\n')
    run = subprocess.run([sys.executable, os.path.join(ROOT, 'core', 'check.py'), TMP], capture_output=True, text=True,
                         encoding='utf-8')
    check("core/check.py judges the garden on disk: 0 errors, exit 0", run.returncode == 0 and '— 0 error(s)' in run.stdout,
          run.stdout + run.stderr)
    write('beans/x13.md', {'bean': 'x13', 'kind': 'document', 'statements': [{'say': {'by': 'sam', 'at': 'now'}},
                                                                             {'mark': {'by': 'sam', 'at': 'next tuesday'}}]})
    with open(os.path.join(TMP, 'beans', 'x16.md'), 'w', encoding='utf-8') as fh:
        fh.write('---\nbean: x16\nkind: document\nkind: host\n---\n')
    run = subprocess.run([sys.executable, os.path.join(ROOT, 'core', 'check.py'), TMP], capture_output=True, text=True,
                         encoding='utf-8')
    check("...and refuses a bad bean, and one with a key written twice, by name, exit 1",
          run.returncode == 1 and 'frame       x13[1] mark' in run.stdout and 'form        x16' in run.stdout, run.stdout)
    run = subprocess.run([sys.executable, os.path.join(ROOT, 'core', 'check.py'), '--law'], capture_output=True, text=True,
                         encoding='utf-8')
    check("core/check.py --law: the law alone, 0 errors", run.returncode == 0, run.stdout + run.stderr)
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print(f"\ncore: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
