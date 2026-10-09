"""The law tools in a garden of the core (v1 part 9): rules, why, form, forms, catalog, review, facets — reading
core/law/ — and the law they read that moved out of std-vocab: the tools by their verbs (core/law/tools.yaml) and what
nothing takes up yet (core/law/vacancies.yaml).

Builds what it needs, as test/core_read.py does: a release of the core made from this tree (v1.0.0), and a GARDEN grown
from it, holding another person, her consent (an `agree` through `written`, which takes a vacancy of the law) and a kind
of the garden's own said vacant.

law: tools.yaml and vacancies.yaml are what std-vocab generates; every one of today's vacancies is placed in the core or
dropped with why; the law holds together, and refuses a vacancy at a place it lacks and a tool of no family; every entry
of std-vocab's `registry_forms` is carried by core/law/ or named where it went. launcher: `daftar` lists the core's
families and tools. rules: the twenty-one rules and the face, the verbs with their roles, the forms, the garden's own rows.
why: a verb with the reasons of the term it replaces, a form's attribute with its vacancies, a name nothing has refused.
form: a verb's valency and a form's attributes; a term's in today's language. forms: both pairs of guides derived by
their laws, and the core's four rules on a statement line. catalog: the core's law items and their relations, a reason
explaining a verb, a document stating one. review: Part B over statements, `--law` over core/law/ with a vacancy taken
here. facets: no facet in a garden of the core. The aliases run the same tools.

Run: python3 test/core_law.py   (0 = green; about a minute)
"""
import json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import read, translate  # noqa: E402
import grow  # noqa: E402 — a release of the core, and the release in today's words
from core.law import Law  # noqa: E402
import importlib
import parse as dmparse
dmpass = importlib.import_module('pass')  # noqa: E402

FAILS = []
PY = sys.executable
VERSION = str(read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml'))['version'])


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


class R:
    def __init__(self, p):
        self.returncode, self.out = p.returncode, p.stdout + p.stderr


def run(*a, cwd=None):
    e = dict(os.environ, GIT_AUTHOR_NAME='sam', GIT_AUTHOR_EMAIL='sam@x', GIT_COMMITTER_NAME='sam',
             GIT_COMMITTER_EMAIL='sam@x')
    return R(subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=e))


def text(path, root=None):
    with open(os.path.join(root or G, path), encoding='utf-8') as fh:
        return fh.read()


def write(path, t, root=None):
    p = os.path.join(root or G, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t)


T = tempfile.mkdtemp(prefix='core-law-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden')

VOCAB = """---
kinds:
  - { kind: allotment, nature: body, meaning: "a plot of ground let to a gardener", vacant: "prediction: expected with the first plot" }
---
# garden — the garden's own rows
"""

ALI = """---
bean: ali
kind: person
title: "Ali"
summary: "Ali, who keeps a garden of her own."
statements:
  - say:    { by: sam, at: now }
  - name:   { by: garden, of: self, as: "123456789abc/person:ali" }
  - own:    { by: theone, of: self }
  - answer: { by: self, of: self, as: law }
---
Ali keeps garden-ali.
"""

GARDEN_ALI = """---
bean: garden-ali
kind: garden
title: "garden-ali — the garden Ali keeps"
summary: "Ali's own daftar garden."
statements:
  - say:  { by: sam, at: now }
  - name: { by: garden-id, of: self, as: "123456789abc" }
  - own:  { by: ali, of: self }
---
Ali's garden.
"""

CONSENT = """---
bean: ali-consent
kind: contract
title: "Ali's consent"
summary: "Ali agreed, in writing, to be kept here by name."
statements:
  - say:     { by: sam, at: now }
  - own:     { by: theone, of: self }
  - answer:  { by: sam, of: self, as: law }
  - answer:  { by: ali, of: self, as: law }
  - agree:   { id: consent, by: [sam, ali], of: "Ali is kept in Sam's garden by name", through: written }
  - concern: { of: [ali] }
---
Agreed in a letter.
"""

try:
    # ---- THE LAW: its vacancies and tools, holding together
    vac = read.data(os.path.join(ROOT, 'core', 'law', 'vacancies.yaml'))
    check("law: each vacancy the law dropped says why",
          vac['vacancies'] and all(d.get('why') for d in vac['dropped']), vac['dropped'])
    check("law: a vacancy is at a table, a figure, a form or what `details` keeps — a unit by its UCUM code",
          all(re.match(r'(table|figure|form|details):', v['at']) for v in vac['vacancies'])
          and any(v['at'] == 'table:units' and v['position'] == '%' for v in vac['vacancies']))
    tools = read.data(os.path.join(ROOT, 'core', 'law', 'tools.yaml'))
    check("law: the tools by their verbs, each in a family the law names, keyed `tool`, each a tool of the release "
          "(`bin/<verb>.py`, the door `bin/dmupgrade.py` for `upgrade`)",
          {t['family'] for t in tools['tools']} <= {f['family'] for f in tools['families']}
          and all(os.path.isfile(os.path.join(ROOT, 'bin', f"{t['tool']}.py" if t['tool'] != 'upgrade' else 'dmupgrade.py'))
                  for t in tools['tools']), [t['tool'] for t in tools['tools']])
    L = Law.load()
    check("law: the law holds together with its tools and vacancies", not L.problems(), L.problems()[:3])
    types = {str(t.get('type')) for t in L.line_law.get('types') or [] if isinstance(t, dict)}
    vals = getattr(L, 'values', None) or {}
    check("law: the values tree (core/law/values.yaml) — every value a kind of another up to `value`, money a quantity "
          "and a quantity a number, and every written form a type of lines.yaml",
          vals.get('money', {}).get('is') == 'quantity' and vals.get('quantity', {}).get('is') == 'number'
          and 'is' not in vals.get('value', {'is': '?'})
          and all(v.get('written') in types for v in vals.values() if v.get('written')),
          sorted(vals)[:6])
    L2 = Law.load()
    L2.values = dict(getattr(L2, 'values', None) or {})
    L2.values['orphan'] = {'value': 'orphan', 'is': 'nothing', 'meaning': 'x'}
    L2.values['unwritten'] = {'value': 'unwritten', 'is': 'value', 'written': 'no-such-type', 'meaning': 'x'}
    L2.values['ring-a'] = {'value': 'ring-a', 'is': 'ring-b', 'meaning': 'x'}
    L2.values['ring-b'] = {'value': 'ring-b', 'is': 'ring-a', 'meaning': 'x'}
    got = [f"{w}: {m}" for _r, w, m in L2.problems()]
    check("law: a value that is a kind of no value, one written in no type of lines.yaml, and two that are kinds of "
          "each other are refused",
          any('orphan' in m and 'no value' in m for m in got) and any('no-such-type' in m for m in got)
          and any('ring-' in m and 'itself' in m for m in got), got)
    import unicodedata
    bc = getattr(dmparse, 'BIDI_CONTROL', frozenset())
    explicit = {chr(c) for c in range(0x110000) if unicodedata.bidirectional(chr(c)) in
                ('LRE', 'RLE', 'LRO', 'RLO', 'PDF', 'LRI', 'RLI', 'FSI', 'PDI')}
    check("law: the reader's Bidi_Control is Unicode's (PropList.txt): every character of an explicit bidi class, and "
          "the three implicit marks, each of category Cf — and the coding row names the property",
          explicit and explicit <= bc and {unicodedata.name(c) for c in bc - explicit} ==
          {'LEFT-TO-RIGHT MARK', 'RIGHT-TO-LEFT MARK', 'ARABIC LETTER MARK'}
          and all(unicodedata.category(c) == 'Cf' for c in bc)
          and next((t.get('holds_no') for t in L.line_law.get('types') or [] if t.get('type') == 'coding'), None)
          == 'Bidi_Control', sorted(f"U+{ord(c):04X}" for c in bc))
    hidden = []
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in ('.git', '__pycache__')]
        for fn in fns:
            try:
                with open(os.path.join(dp, fn), encoding='utf-8') as fh:
                    if dmparse.bidi_controls(fh.read()):
                        hidden.append(os.path.relpath(os.path.join(dp, fn), ROOT))
            except (UnicodeDecodeError, OSError):
                pass
    check("law: no file of this tree holds a bidi control character as itself — a test writes one as an escape "
          "(Trojan Source, CVE-2021-42574)", not hidden, hidden[:5])
    ns = L.namespaces
    shape = getattr(L, 'namespace_shape', None) or {}
    eight = ('ror', 'wikidata', 'orcid', 'ifc-guid', 'dicom-uid', 'gs1', 'tr-tckn', 'ir-national-code')
    check("law: the eight namespaces are the law's, each with its form; a `checked_by` one the shape lists and the "
          "reader has; the two government numbers kept held",
          all(n in ns and ns[n].get('pattern') for n in eight)
          and all(ns[n]['checked_by'] in (shape.get('checked_by') or []) and ns[n]['checked_by'] in dmparse.FORM_CHECKS
                  for n in ns if ns[n].get('checked_by'))
          and {n for n in ns if ns[n].get('kept') == 'held'} == {'tr-tckn', 'ir-national-code'},
          {n: (ns.get(n) or {}).get('checked_by') for n in eight})
    fc = dmparse.FORM_CHECKS
    cases = [('ror-checksum', '05dxps055', True), ('ror-checksum', '05dxps056', False),
             ('orcid-checksum', '0000-0002-1825-0097', True), ('orcid-checksum', '0000-0002-1825-0098', False),
             ('gs1-element', '(01)09520123456788', True), ('gs1-element', '(01)09520123456787', False),
             ('gs1-element', '(01)09520123456788(10)AB', False),
             ('tckimlik', '10000000146', True), ('tckimlik', '10000000147', False),
             ('uuid-integer', f'2.25.{2 ** 128 - 1}', True), ('uuid-integer', f'2.25.{2 ** 128}', False)]
    got = [(c, v, (fc[c](v) if c in fc else None)) for c, v, _want in cases]
    check("law: each check takes its publisher's own example and refuses an altered copy (python-stdnum, uuid) — one "
          "GS1 element string a name, never two",
          [g[2] for g in got] == [w for _c, _v, w in cases], got)
    saved = {k: v for k, v in sys.modules.items() if k == 'stdnum' or k.startswith('stdnum.')}
    for k in saved:
        del sys.modules[k]
    sys.modules['stdnum'] = None                     # as where python-stdnum is not installed
    try:
        fc['orcid-checksum']('0000-0002-1825-0097')
        unavailable = None
    except dmparse.CheckUnavailable as e:
        unavailable = str(e)
    finally:
        del sys.modules['stdnum']
        sys.modules.update(saved)
    check("law: where python-stdnum is not installed, its check says so — a name is never passed unchecked",
          unavailable and 'python-stdnum' in unavailable and 'pip install' in unavailable, unavailable)
    L3 = Law.load()
    L3.namespaces = dict(L3.namespaces)
    L3.namespaces['made-up'] = {'namespace': 'made-up', 'once': 'true', 'pattern': '^x$', 'checked_by': 'no-such-check',
                                'kept': 'nowhere', 'meaning': 'x'}
    got = [f"{w}: {m}" for _r, w, m in L3.problems()]
    check("law: a namespace checked by no check the shape lists, or kept nowhere the shape names, is refused",
          any('no-such-check' in m for m in got) and any('nowhere' in m for m in got), got)
    from core import lines as core_lines
    step = (L.forms.get('step') or {})
    got = core_lines.attrs_problems('s', {'is': 'isco-08:25\u202e22'}, step) if step else []
    check("law: a step's code (`is`, a coding) holding U+202E is refused by name, and never echoed",
          any('U+202E' in m and 'Bidi_Control' in m and '\u202e' not in m for _w, m in got), got)
    L._vacancies({'reasons': ['universal'], 'vacancies': [
        {'at': 'form:clause.state', 'position': 'adjourned', 'reason': 'universal', 'why': 'x'},
        {'at': 'table:units', 'position': 'percent', 'reason': 'universal', 'why': 'x'},
        {'at': 'figure:necessity', 'position': 'possible', 'reason': 'hunch', 'why': 'x'}]})
    L.tools['nowhere'] = {'tool': 'nowhere', 'family': 'elsewhere'}
    got = [m for _r, w, m in L.problems()]
    check("law: a vacancy at a value its place lacks is refused, a unit named by its English name too, a reason "
          "the law does not give, and a tool of no family",
          any("'adjourned' is not a value of clause.state" in m for m in got)
          and any("English name of `%`" in m for m in got) and any("'hunch' is none of" in m for m in got)
          and any("'elsewhere' is none of" in m for m in got), got)

    # ---- THE RELEASE: v1.0.0 of the core from this tree, and a garden grown from it
    grow.release(REL)
    r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam', cwd=T)
    TOOLS = ('rules', 'why', 'form', 'forms', 'catalog', 'review', 'facets')
    check(f"a garden grows from v1.0.0 in the core (core@{VERSION}), the law tools and their law in it",
          r.returncode == 0 and f'core@{VERSION}' in text('GARDEN.md')
          and all(os.path.isfile(os.path.join(G, 'bin', f"{v}.py")) and not os.path.exists(os.path.join(G, 'bin', f"dm{v}.py"))
                  for v in TOOLS) and os.path.isfile(os.path.join(G, 'core', 'law', 'tools.yaml'))
          and os.path.isfile(os.path.join(G, 'core', 'law', 'vacancies.yaml')), r.out[-800:])
    run(PY, 'bin/install.py')
    write('VOCAB.md', VOCAB)
    for p, t in (('beans/ali.md', ALI), ('beans/garden-ali.md', GARDEN_ALI), ('beans/ali-consent.md', CONSENT)):
        write(p, t)
    r = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: a kind of the garden own, vacant; Ali, her garden, her consent',
            '--body', '- action: RULE-CHANGE — VOCAB.md adds the kind allotment, vacant; wrote [[ali]], [[garden-ali]] '
                      'and [[ali-consent]]\n- ratified_by: sam, the gardener\n- why: a plot is expected')
    check("gate: the garden's beans and its own vacant kind saved through the core's gate", r.returncode == 0, r.out[-1200:])

    # ---- the launcher: the core's families and tools
    r = run(PY, 'bin/daftar.py')
    check("launcher: `daftar` lists the core's families and tools (core/law/tools.yaml)",
          r.returncode == 0 and 'law — read the law' in r.out and re.search(r'(?m)^  why\s+the law and its reasons', r.out)
          and 'between —' in r.out, r.out[:600])

    # ---- rules
    r = run(PY, 'bin/rules.py')
    check("rules: the twenty-one rules, each in its words, and the face they judge by",
          r.returncode == 0 and f'core@{VERSION}' in r.out and 'THE RULES — 21' in r.out
          and re.search(r'(?m)^  vacancy\s+every row a garden adds', r.out) and 'THE FIGURES' in r.out, r.out[:800])
    check("rules: each verb's roles, `*` where required — `pay` by* and of* — and the forms' attributes by bin/form.py",
          re.search(r'(?m)^  pay\b', r.out) and '      by*: being (nature body|sayable, rung reason)' in r.out
          and '      placement: point|bounds|preceding|following' in r.out, r.out[-2000:])
    check("rules: the garden's own rows, a vacant one with why", re.search(r'kinds\s+allotment\s+vacant: prediction', r.out),
          r.out[-600:])
    a, b = run(PY, 'bin/rules.py', '--core'), run(PY, 'bin/rules.py', '--core')
    check("rules: `--core` is the rules and the face alone, and the alias prints the same",
          a.returncode == 0 and a.out == b.out and 'THE VERBS' not in a.out and 'THE RULES' in a.out, b.out[:300])

    # ---- why
    r = run(PY, 'bin/why.py', 'own')
    check("why: a verb of the face, with its reasons, keyed by the core's path — those written of the term it replaces "
          "saying so (`terms[owned_by]`)",
          r.returncode == 0 and '== core/law/core.yaml: verbs[own]' in r.out and '-- core/law/core.yaml: verbs[own]' in r.out
          and "(std-vocab 32: `terms[owned_by]`)" in r.out, r.out[:800])
    r = run(PY, 'bin/why.py', 'clause.state')
    check("why: a form's attribute, named by its tail, with the law's vacancies at it",
          r.returncode == 0 and 'forms.clause.attrs.state' in r.out and 'VACANT disputed (universal)' in r.out, r.out[:800])
    r = run(PY, 'bin/why.py', 'percent')
    check("why: a unit by its English name is its UCUM row", r.returncode == 0 and 'units[%]' in r.out, r.out[:400])
    r = run(PY, 'bin/why.py', 'allotment')
    check("why: a row of the garden's own, from its VOCAB.md", r.returncode == 0 and 'VOCAB.md: kinds[allotment]' in r.out
          and 'vacant' in r.out, r.out[:400])
    r = run(PY, 'bin/why.py', 'no-such-item')
    check("why: a name nothing in the law has is said so, exit 1", r.returncode == 1 and 'no item' in r.out, r.out)

    # ---- form
    r = run(PY, 'bin/form.py', 'pay')
    check("form: a verb's valency", r.returncode == 0 and '  by*: being (nature body|sayable, rung reason)' in r.out
          and '  of*: quantity' in r.out, r.out)
    r = run(PY, 'bin/form.py', 'series')
    check("form: a form's attributes and its one-of", r.returncode == 0 and 'one of: grid, span, held' in r.out, r.out)
    r = run(PY, 'bin/form.py', 'owned_by', cwd=ROOT)
    check("form: a word of today's language is no verb and no form of the core's law, and says so, exit 1",
          r.returncode == 1 and 'is no verb and no form' in r.out,
          r.out)
    import form
    check("form: one module under both names, reading a core form as a term's schema",
          __import__('form') is form and form.core_form(read.data(os.path.join(ROOT, 'core', 'law', 'lines.yaml'))
                                                         ['forms']['series'])['one_of'] == ['grid', 'span', 'held'])

    # ---- forms
    r = run(PY, 'bin/forms.py', '--check', cwd=ROOT)
    check("forms: both pairs of guides are the forms of their cookbooks, each by its law", r.returncode == 0, r.out)
    import forms as forms_tool
    CL = Law.load()
    got = forms_tool.core_form_of('\n'.join((
        '  - say:   { by: sam, at: "2026-09-12 10:00+03:00" }',
        '  - name:  { by: garden, of: self, as: "123456789abc/event:dinner-2026-09-12" }',
        '  - be:    { by: self, at: "2026-09-12 19:30+03:00" }',
        '  - agree: { by: [sam, ali], of: "a loan", at: "2026-09-12" }')), CL).split('\n')
    check("forms: a knowing act's moment is `now`; a name's day is cut; a moment its verb requires keeps the example's, "
          "said so; one it does not is left out, said so",
          got[0] == '  - say:   { by: sam, at: now }' and got[1] == '  - name:  { by: garden, of: self, as: "123456789abc/event:dinner" }'
          and got[2].endswith("# at: the example's — write the moment someone said")
          and got[3] == '  - agree: { by: [sam, ali], of: "a loan" }   # at: left out unless said', got)
    bad = text('seed/FORMS.md', ROOT).replace('  - be:     { by: self, at: "2026-09-12 19:30+03:00" }   #',
                                                    '  - be:     { by: self, at: "2026-09-13 19:30+03:00" }   #')
    check("forms: a form that is not the cookbook's, by the core's law, is written back to it",
          bad != text('seed/FORMS.md', ROOT)
          and forms_tool.core_derive(bad, text('seed/COOKBOOK.md', ROOT), CL) == text('seed/FORMS.md', ROOT))

    # ---- catalog
    r = run(PY, 'bin/catalog.py', '--json')
    d = json.loads(r.out) if r.returncode == 0 else {}
    parts, rels = d.get('parts', {}), {(x['rel'], x['from'], x['to']) for x in d.get('relations', [])}
    check("catalog: the core's law items — rules, verbs, tables, forms, layers — each a part",
          d.get('catalogue', {}).get('law') == f'core@{VERSION}' and parts.get('rule:vacancy', {}).get('kind') == 'rule'
          and parts.get('verb:agree', {}).get('kind') == 'verb' and parts.get('form:clause', {}).get('kind') == 'form'
          and parts.get('table:tools', {}).get('kind') == 'table' and 'layer:law' in parts, r.out[:400])
    check("catalog: a verb uses the table its role takes, and the form its qualifier holds",
          ('uses', 'verb:answer', 'table:modes') in rels and ('uses', 'verb:can', 'form:clause') in rels)
    check("catalog: a reason explains a verb through what it replaces", ('explains', 'seed/RATIONALE.md', 'verb:own') in rels,
          sorted(rels)[:5])
    r = run(PY, 'bin/catalog.py', '--part', 'verb:take')
    check("catalog: one part, with the rule that names it", r.returncode == 0 and 'verb:take — verb' in r.out
          and '[THE RULES] knowing:' in r.out, r.out[:900])
    import catalog
    rc = catalog.Catalogue(ROOT)
    check("catalog: the core's guides (a release's core/guide/) state the verbs their examples write",
          ('states', 'seed/FORMS.md', 'verb:say', '') in rc.edges and ('states', 'seed/FORMS.md', 'verb:agree', '')
          in rc.edges)
    r = run(PY, 'bin/catalog.py')
    check("catalog: the report names the core's law and its findings", r.returncode == 0
          and f'(core@{VERSION})' in r.out and 'rules (21)' in r.out and 'findings' in r.out, r.out[-900:])

    # ---- review
    r = run(PY, 'bin/review.py')
    check("review: Part B over statements — the verbs nobody says, a key of `details` once — and exit 0",
          r.returncode == 0 and 'in a garden of the core' in r.out and 'VERBS NOBODY SAYS' in r.out
          and 'KNOWING HONEST' in r.out, r.out[-900:])
    r = run(PY, 'bin/review.py', '--law')
    check("review --law: the core's law counted, and the vacancy a statement here takes named",
          r.returncode == 0 and 'core/law/ core@' in r.out and re.search(r'(?m)^  rules\s+21', r.out)
          and 'table:forms written' in r.out and 'every rule of the core is strict' in r.out, r.out[-1500:])

    r = run(PY, 'bin/review.py', '--places')
    check("review --places: the fixed beings read from `be` as location", r.returncode == 0 and r.out.startswith('PLACES'),
          r.out)

    # ---- facets
    r = run(PY, 'bin/facets.py')
    check("facets: a garden of the core declares no merge facet; the statement merge keeps a set — by either name",
          r.returncode == 0 and 'declares no merge facet' in r.out and 'as a set' in r.out
          and run(PY, 'bin/facets.py').out == r.out, r.out)
except Exception as e:
    import traceback
    traceback.print_exc()
    FAILS.append(f"the suite raised {type(e).__name__}: {e}")
finally:
    shutil.rmtree(T, ignore_errors=True) if not os.environ.get("KEEP") else print("kept", T)

print(f"\ncore_law: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
