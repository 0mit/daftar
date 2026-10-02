#!/usr/bin/env python3
"""site/board.py — the one page: daftar through four lenses and ten mechanisms, a board for every crossing.

    python3 site/board.py [--out site/index.html]

Reads site/boards.yaml (what a person writes: each lens's words for each mechanism) and the release itself — the core's
law (core/law/), its reasons (seed/RATIONALE.md, through bin/why.py), and the catalogue's parts, rules, checks and
relations (bin/catalog.py) — and writes ONE page, site/index.html: its data inline, as a JSON block, beside the style and
the script it links (site/assets/board.css, site/assets/board.js), so that its policy runs no code the site does not
hold. A keeper's board is never written by hand: it is read from the release it describes, so it cannot drift from it.

An agent's board is proved. The builder grows a garden from the release, writes the beans of site/garden.yaml, and
saves them with the command it shows; the gate must pass them. It then breaks each board's form once, as its `scene`
says, and shows the refusal the gate printed: the rule that refused it, and its line. When the gate refuses a form, or
does not refuse its break by the rule `rule` names with the words `refused` names, the page is not written."""
import atexit, html, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(ROOT, 'site', 'index.html')
try:
    RELEASE = open(os.path.join(ROOT, 'site', 'RELEASE'), encoding='utf-8').read().strip()
except OSError:
    RELEASE = ''

# The page describes the release site/RELEASE names, never the checkout beside it: its law, its catalogue and its gate
# are read from a clone of this repository at that tag, so a change to a tool reaches the page only through a release.
TMP = tempfile.mkdtemp(prefix='daftar-site-')
atexit.register(shutil.rmtree, TMP, True)
REL = os.path.join(TMP, 'release')
_c = subprocess.run(['git', 'clone', '-q', '--branch', RELEASE, ROOT, REL], capture_output=True, text=True,
                    encoding='utf-8', errors='replace')
if not RELEASE or _c.returncode:
    sys.exit(f"site/board.py: site/RELEASE names {RELEASE or 'nothing'}, and this repository cannot be cloned at it "
             f"({_c.stderr.strip() or 'no tag'}) — a shallow clone has no tags: git fetch --tags")
sys.path.insert(0, os.path.join(REL, 'bin'))
sys.path.insert(0, REL)
import parse   # noqa: E402 — the release's own loader
import why     # noqa: E402 — the release's one reader of the reasons
from core import read  # noqa: E402 — the core's law, every value read as written

# The tools the page names are the ones the builder runs: the save, its second try after a refusal, the gate, the rules.
SAVE, GATE, RULES = 'bin/save.py', 'bin/check.py', 'bin/rules.py'
for _t in (SAVE, GATE, RULES, 'bin/propose.py', 'seed/germinate.py'):
    if not os.path.isfile(os.path.join(REL, _t)):
        sys.exit(f"site/board.py: the release {RELEASE} has no {_t}, which the page names")

B = parse.loads(open(os.path.join(ROOT, 'site', 'boards.yaml'), encoding='utf-8').read())
VERSION = str(read.data(os.path.join(REL, 'core', 'law', 'core.yaml')).get('version'))
_cat = subprocess.run([sys.executable, os.path.join(REL, 'bin', 'daftar.py'), 'catalog', '--json'],
                      capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=REL)
if _cat.returncode:
    sys.exit(f"site/board.py: the release's catalogue did not print\n{_cat.stderr[-2000:]}")
CATJ = json.loads(_cat.stdout)
PARTS, RELS = CATJ['parts'], CATJ['relations']
REASONS = why.rationale()
# a part's reasons are the ones the catalogue says explain it, each keyed by the path of the item it explains
EXPLAINED = {}
for _r in RELS:
    if _r.get('rel') == 'explains':
        EXPLAINED.setdefault(_r['to'], []).append(_r.get('via'))
LAW_KINDS = ('rule', 'verb', 'table', 'section', 'form', 'layer', 'profile')


def _plain(text):
    text = re.sub(r'```.*?```', ' ', str(text), flags=re.S)
    text = re.sub(r'==[^=\n]*==', ' ', text).replace('**', '')
    return re.sub(r'\s+', ' ', text).strip()


OLD_KEY = re.compile(r'^\((?:std-vocab|[a-z-]+) [0-9.]+: `([^`]+)`\)\s*$', re.M)


def reason_of(pid):
    """The first two sentences of the reason keyed to the part itself (never one of its rows' or attributes'). A reason
    carried from an older law holds a paragraph for each key it was written under there, each opening with that key,
    `(std-vocab 32: `terms[owned_by].meaning`)`. The item's own old key is the one its reason opens with, to its first
    `.` (`terms[owned_by]`): that key's meaning paragraph is read, else that key's own — never the paragraph of one of
    its attributes, which says why that attribute is so, nor one of another old item folded in beside it."""
    kind, name = pid.split(':', 1)
    path = {'verb': f'verbs[{name}]', 'form': f'forms.{name}', 'rule': f'rules[{name}]'}.get(kind, name)
    paras = []
    for k in EXPLAINED.get(pid) or []:
        if k.split(': ', 1)[-1] != path:
            continue
        text = REASONS.get(k) or ''
        cuts = list(OLD_KEY.finditer(text))
        paras += [(c.group(1), text[c.end():cuts[i + 1].start() if i + 1 < len(cuts) else len(text)])
                  for i, c in enumerate(cuts)] or [(path, text)]
    root = paras[0][0].split('.', 1)[0] if paras else ''
    for _old, text in sorted(paras, key=lambda p: (not p[0].endswith('meaning'), len(p[0]))):
        if _old not in (root, root + '.meaning'):
            continue
        text = _plain(text)
        first = [x for x in re.split(r'(?<=[.!?])\s', text) if not re.match(r'^Its [^.]{0,30}\.$', x)]
        if first and len(' '.join(first)) > 60 and re.match(r'[A-Z`]', first[0]) and not first[0].startswith('NB '):
            said = ' '.join(first[:2])
            return said if len(said) <= 420 else said[:420].rsplit(' ', 1)[0].rstrip(',;:—–- ') + ' …'
    return ''


def meaning_of(pid):
    kind = pid.split(':', 1)[0]
    c = (PARTS.get(pid) or {}).get('contents') or {}
    if kind == 'rule':
        return _plain(c.get('says') or '')
    if kind == 'table':
        names = [str(x) for x in c.get('row_names') or []]
        return (f"{c.get('rows')} rows — " + ', '.join(names[:8]) + (' …' if len(names) > 8 else '')) if names else ''
    if kind == 'section':
        return f"{c.get('file')}: " + ', '.join(str(k) for k in c.get('keys') or [])
    return _plain(c.get('meaning') or '')


def valency_of(pid):
    """A verb's roles as the catalogue reads them from its row, `*` where required: `pay: by* of* through to at`."""
    c = (PARTS.get(pid) or {}).get('contents') or {}
    if not pid.startswith('verb:') or not isinstance(c.get('roles'), dict):
        return ''
    req = set(c.get('required') or [])
    return pid[5:] + ': ' + ' '.join(r + ('*' if r in req else '') for r in c['roles']) + \
        ''.join(f" +{q}" for q in c.get('qualifiers') or [])


def _fail(what, text=''):
    sys.exit(f"site/board.py: {what}" + (f"\n{text[-2500:]}" if text else ''))


def keeper(mech):
    out = []
    for pid in mech.get('items') or []:
        if pid not in PARTS or pid.split(':', 1)[0] not in LAW_KINDS:
            _fail(f"{mech['id']}: the release's catalogue has no part of the law {pid!r} — name it as "
                  f"`python3 bin/daftar.py catalog` does (rule:, verb:, table:, section:, form:, layer:, profile:)")
        part = PARTS[pid]
        cl = part.get('checklists') or {}
        meaning = meaning_of(pid)
        rules = [r.get('rule') if isinstance(r, dict) else str(r) for r in (cl.get('rules') or [])]
        checks = cl.get('checks') or []
        rel = sum(1 for r in RELS if r.get('to') == pid or r.get('from') == pid)
        suites = sorted({c.get('suite') for c in checks if isinstance(c, dict) and c.get('suite')})
        out.append({'id': pid, 'name': pid.split(':', 1)[1], 'kind': pid.split(':', 1)[0],
                    'meaning': meaning[:520], 'valency': valency_of(pid), 'reason': reason_of(pid),
                    'rules': [r for r in rules if _plain(r) != meaning][:5], 'nrules': len(rules),
                    'checks': len(checks), 'suites': suites[:4], 'relations': rel})
    return out


def files_of(mech):
    ids = set(mech.get('items') or [])
    out = set()
    for r in RELS:
        if r.get('to') in ids and str(r.get('from')).split(':')[0] not in LAW_KINDS:
            out.add(r['from'])
        if r.get('from') in ids and str(r.get('to')).split(':')[0] not in LAW_KINDS:
            out.add(r['to'])
    return out


FILES = {m['id']: {f for f in files_of(m) if not f.startswith('site/')} for m in B['mechanisms']}
# what holds every mechanism is the ground, not a rope: a file in more than half of them binds nothing in particular
_reach = {}
for _fs in FILES.values():
    for f in _fs:
        _reach[f] = _reach.get(f, 0) + 1
GROUND = sorted(f for f, n in _reach.items() if n > len(FILES) // 2)
FILES = {k: v - set(GROUND) for k, v in FILES.items()}
ROPES = []
_ids = [m['id'] for m in B['mechanisms']]
for i, a in enumerate(_ids):
    for b in _ids[i + 1:]:
        both = sorted(FILES[a] & FILES[b])
        if both:
            ROPES.append({'a': a, 'b': b, 'n': len(both), 'files': both[:12]})


def _run(args, cwd):
    return subprocess.run([sys.executable] + args, capture_output=True, text=True, encoding='utf-8', errors='replace',
                          cwd=cwd, env=dict(os.environ, PYTHONUTF8='1'))


def _shown(text, keys, verbs):
    """What a board shows of a bean: the header `keys` and the statements of `verbs`, each as it is written, under
    `statements:` — a statement written over several lines whole."""
    fm = text.split('---', 2)[1].strip('\n').split('\n')
    head, stmts, keep, cur = [], [], False, None
    for line in fm:
        if line and not line[0].isspace():
            keep, cur = line.split(':', 1)[0], None
            if keep in keys:
                head.append(line)
        elif keep == 'statements':
            m = re.match(r'  - ([a-z][a-z-]*):', line)
            if m:
                cur = m.group(1) in verbs
            if cur:
                stmts.append(line)
    return '\n'.join(head + (['statements:'] + stmts if stmts else []))


def scenes():
    """{mechanism: {form, rule, error}}: each form as a bean the release's gate passed, each refusal as it printed it."""
    GD = parse.loads(open(os.path.join(ROOT, 'site', 'garden.yaml'), encoding='utf-8').read())
    G = os.path.join(TMP, 'garden-' + GD['gardener']['id'])
    grow = ['seed/germinate.py', G, '--gardener', GD['gardener']['id'], '--gardener-name', GD['gardener']['name']]
    for p in GD.get('profiles') or []:
        grow += ['--profile', p]
    r = _run(grow, REL)
    if r.returncode:
        _fail('the scene garden did not grow', r.stdout + r.stderr)
    for dst, src in (GD.get('files') or {}).items():
        os.makedirs(os.path.dirname(os.path.join(G, dst)), exist_ok=True)
        shutil.copyfile(os.path.join(G, src), os.path.join(G, dst))
    for b, text in GD['beans'].items():
        open(os.path.join(G, 'beans', b + '.md'), 'w', encoding='utf-8', newline='\n').write(text)
    sv = GD['save']
    r = _run([SAVE, sv['who'], sv['what'], '--body', sv['body']], G)
    gate = _run([GATE, '--all'], G).stdout
    if r.returncode or not re.search(r' — 0 error\(s\)\s*$', gate):
        _fail("the scene garden's forms do not pass their gate cleanly", r.stdout + r.stderr + gate)
    gid = re.search(r'garden_id: "?([0-9a-f]{12})', _run(['bin/propose.py', 'id'], G).stdout)
    save = f'python3 {SAVE} "{sv["who"]}" "{sv["what"]}" \\\n  --body "{sv["body"]}"'
    out = {}
    for m in B['mechanisms']:
        sc = m['scene']
        forms = []
        for sh in sc['show']:
            if sh.get('save'):
                forms.append(save)
            else:
                forms.append((f"# beans/{sh['bean']}.md\n" if len(sc['show']) > 1 else '')
                             + _shown(GD['beans'][sh['bean']], sh.get('keys') or [], sh.get('verbs') or []))
        bk = sc['break']
        path = os.path.join(G, 'beans', bk['bean'] + '.md')
        orig = open(path, encoding='utf-8').read() if os.path.exists(path) else None
        text = orig
        if bk.get('copy_of'):
            text = GD['beans'][bk['copy_of']].replace(f"bean: {bk['copy_of']}\n", f"bean: {bk['bean']}\n", 1)
        pairs = bk.get('replace') or []
        for a, b in (pairs if pairs and isinstance(pairs[0], list) else [pairs] if pairs else []):
            if a not in text:
                _fail(f"{m['id']}: the break replaces {a!r}, which beans/{bk['bean']}.md does not hold")
            text = text.replace(a, b, 1)
        for prefix in bk.get('drop') or []:
            lines = text.split('\n')
            at = next((i for i, x in enumerate(lines) if x.lstrip().startswith(prefix)), None)
            if at is None:
                _fail(f"{m['id']}: the break drops a line beginning {prefix!r}, which beans/{bk['bean']}.md does not hold")
            text = '\n'.join(lines[:at] + lines[at + 1:])
        open(path, 'w', encoding='utf-8', newline='\n').write(text)
        if bk.get('staged'):
            subprocess.run(['git', 'add', '-A'], cwd=G, capture_output=True)
        said = _run([GATE, '--staged' if bk.get('staged') else '--all'], G).stdout
        if bk.get('staged'):
            subprocess.run(['git', 'reset', '-q'], cwd=G, capture_output=True)
        if orig is None:
            os.remove(path)
        else:
            open(path, 'w', encoding='utf-8', newline='\n').write(orig)
        found = None
        for line in said.splitlines():
            rm = re.match(r'([a-z][a-z-]*)\s{2,}(\S.*)$', line)
            if rm and rm.group(1) == sc['rule'] and sc['refused'] in rm.group(2):
                found = rm.group(2)
                break
        if not found:
            _fail(f"{m['id']}: the gate did not refuse the break by rule {sc['rule']!r} with {sc['refused']!r}", said)
        clean = found.replace(G, '.')
        if gid:
            clean = clean.replace(gid.group(1), '<garden id>')
        out[m['id']] = {'form': '\n'.join(forms), 'rule': sc['rule'], 'error': clean}
    return out


SCENES = scenes()
LANGS = [x['id'] for x in B.get('languages') or [{'id': 'en'}]]
DATA = {'version': VERSION, 'release': RELEASE, 'languages': B.get('languages') or [], 'ui': B.get('ui') or {},
        'lenses': B['lenses'], 'mechanisms': [],
        'commands': {'save': f'python3 {SAVE} "<who>" "<what changed>" --body "- action: …"',
                     'again': f'python3 {SAVE} --again', 'rules': f'python3 {RULES}'}}
for m in B['mechanisms']:
    DATA['mechanisms'].append({k: m.get(k) for k in ['id', 'name', 'short', 'glyph', 'staples', 'person', 'gardener',
                                                     'agent_note'] + LANGS[1:] if k in m}
                              | {'keeper': keeper(m)} | SCENES[m['id']])
counts = {kind + 's': sum(1 for k in PARTS if k.startswith(kind + ':')) for kind in ('rule', 'verb', 'table')}
counts |= {'relations': len(RELS), 'reasons': len(REASONS)}
DATA['counts'] = counts
DATA['ropes'] = ROPES
DATA['ground'] = GROUND
for m in DATA['mechanisms']:
    m['files'] = len(FILES[m['id']])

page = open(os.path.join(ROOT, 'site', 'board.html'), encoding='utf-8').read()
# The first language's words stand in the page as written, for a reader whose browser runs no script. They are filled
# in before the data is, so that nothing in the data is ever read as a placeholder.
UI0 = dict((B.get('ui') or {}).get(LANGS[0]) or {})
UI0['boards'] = UI0.get('boards', '').replace('{l}', str(len(B['lenses']))).replace(
    '{m}', str(len(B['mechanisms']))).replace('{b}', str(len(B['lenses']) * len(B['mechanisms'])))
page = re.sub(r'\{\{(\w+)\}\}', lambda x: html.escape(UI0[x.group(1)]) if x.group(1) in UI0
              else _fail(f"site/board.html names {x.group(0)}, which ui.{LANGS[0]} in site/boards.yaml lacks"), page)
page = page.replace('__VERSION__', html.escape(VERSION)).replace('__RELEASE__', html.escape(RELEASE or 'the release'))
page = page.replace('/*__DATA__*/', json.dumps(DATA, ensure_ascii=False).replace('</', '<\\/'))
open(OUT, 'w', encoding='utf-8').write(page)
print(f"site/board.py: {len(DATA['mechanisms'])} mechanisms × {len(DATA['lenses'])} lenses = "
      f"{len(DATA['mechanisms']) * len(DATA['lenses'])} boards, core {VERSION}; "
      f"wrote {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT):,} bytes)")
