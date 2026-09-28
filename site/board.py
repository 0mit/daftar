#!/usr/bin/env python3
"""site/board.py — the one page: daftar through four lenses and ten mechanisms, a board for every crossing.

    python3 site/board.py [--out site/index.html]

Reads site/boards.yaml (what a person writes: each lens's words for each mechanism) and the release itself — the law's
meanings (seed/std-vocab.md), their reasons (seed/RATIONALE.md), and the catalogue's parts, rules, checks and relations
(bin/dmcatalog.py) — and writes ONE page, site/index.html: its data inline, as a JSON block, beside the style and the
script it links (site/assets/board.css, site/assets/board.js), so that its policy runs no code the site does not hold.
A keeper's board is never written by hand: it is read from the release it describes, so it cannot drift from it.

An agent's board is proved. The builder grows a garden from the release, writes the beans of site/garden.yaml, and
saves them with the command it shows; the gate must pass them. It then breaks each board's form once, as its `scene`
says, and shows the refusal the gate printed. When the gate refuses a form, or does not refuse its break with the words
`refused` names, the page is not written."""
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
import dmparse  # noqa: E402 — the release's own
import dmwhy    # noqa: E402

B = dmparse.loads(open(os.path.join(ROOT, 'site', 'boards.yaml'), encoding='utf-8').read())
LAW = dmparse.loads(dmparse.split_front_matter(open(os.path.join(REL, 'seed', 'std-vocab.md'),
                                                   encoding='utf-8').read())[0])
VERSION = str(LAW.get('version'))
CATJ = json.loads(subprocess.run([sys.executable, os.path.join(REL, 'bin', 'daftar.py'), 'catalog', '--json'],
                                 capture_output=True, text=True, encoding='utf-8', cwd=REL).stdout)
PARTS, RELS = CATJ['parts'], CATJ['relations']
REASONS = dmwhy.rationale()

TERMS = {t['term']: t for t in LAW.get('terms') or [] if isinstance(t, dict)}
for _p, _v in (LAW.get('profiles') or {}).items():
    for t in (_v or {}).get('terms') or []:
        TERMS.setdefault(t['term'], dict(t, _profile=_p))


def resolve(item):
    name = item.split(':', 1)[-1]
    for c in (item, 'registry:' + name, 'section:' + name, 'term:' + name, 'profile:' + name):
        if c in PARTS:
            return c
    return None


def reason_of(pid):
    kind, name = pid.split(':', 1)
    keys = {'term': [f'terms[{name}]', f'terms[{name}].meaning'], 'registry': [name], 'section': [name],
            'profile': [f'profiles.{name}', f'profiles.{name}.overlays']}.get(kind, [name])
    stem = f'terms[{name}]' if kind == 'term' else name
    keys += sorted((k for k in REASONS if k.startswith(stem + '.') or k.startswith(stem + '[')),
                   key=lambda k: (not k.endswith('meaning'), len(k)))
    for k in keys:
        v = REASONS.get(k)
        if v:
            text = v if isinstance(v, str) else (v.get('text') if isinstance(v, dict) else str(v))
            text = re.sub(r'```.*?```', ' ', str(text), flags=re.S)
            text = re.sub(r'==[^=\n]*==', ' ', text).replace('**', '')
            text = re.sub(r'\s+', ' ', text).strip()
            first = [x for x in re.split(r'(?<=[.!?])\s', text) if not re.match(r'^Its [^.]{0,30}\.$', x)]
            if first and len(' '.join(first)) > 60 and re.match(r'[A-Z`]', first[0]) and not first[0].startswith('NB '):
                return ' '.join(first[:2])[:420]
    return ''


def meaning_of(pid):
    kind, name = pid.split(':', 1)
    if kind == 'term' and name in TERMS:
        return re.sub(r'\s+', ' ', str(TERMS[name].get('meaning') or '')).strip()
    if kind == 'profile':
        return re.sub(r'\s+', ' ', str(((LAW.get('profiles') or {}).get(name) or {}).get('meaning') or '')).strip()
    if kind == 'registry':
        rows = LAW.get(name)
        if isinstance(rows, list):
            ids = [str(next(iter(r.values()))) for r in rows if isinstance(r, dict) and r]
            return f"{len(rows)} rows — " + ', '.join(ids[:8]) + (' …' if len(ids) > 8 else '')
    part = PARTS.get(pid) or {}
    return re.sub(r'\s+', ' ', str(part.get('meaning') or (part.get('contents') or {}).get('meaning') or '')).strip()


def keeper(mech):
    out = []
    for item in mech.get('items') or []:
        pid = resolve(item)
        if not pid:
            _fail(f"{mech['id']}: the release's catalogue has no part {item!r} — "
                  f"name it as `bin/daftar.py catalog` does")
        part = PARTS[pid]
        cl = part.get('checklists') or {}
        rules = [r.get('rule') if isinstance(r, dict) else str(r) for r in (cl.get('rules') or [])]
        checks = cl.get('checks') or []
        rel = sum(1 for r in RELS if r.get('to') == pid or r.get('from') == pid)
        suites = sorted({c.get('suite') for c in checks if isinstance(c, dict) and c.get('suite')})
        out.append({'id': pid, 'name': pid.split(':', 1)[1], 'kind': pid.split(':', 1)[0],
                    'meaning': meaning_of(pid)[:520], 'reason': reason_of(pid), 'rules': rules[:5],
                    'nrules': len(rules), 'checks': len(checks), 'suites': suites[:4], 'relations': rel})
    return out


LAW_KINDS = ('term', 'registry', 'section', 'profile', 'layer')


def files_of(mech):
    ids = {resolve(i) for i in mech.get('items') or []} - {None}
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


def _keys(text, keys):
    """The lines of a bean's front matter that write `keys`, each block as it is written."""
    fm, out, keep = text.split('---', 2)[1].strip('\n').split('\n'), [], False
    for line in fm:
        if line and not line[0].isspace():
            keep = line.split(':', 1)[0] in keys
        if keep:
            out.append(line)
    return '\n'.join(out)


def _fail(what, text=''):
    sys.exit(f"site/board.py: {what}" + (f"\n{text[-2500:]}" if text else ''))


def scenes():
    """{mechanism: {form, error, fix}}: each form as a bean the release's gate passed, each refusal as it printed it."""
    GD = dmparse.loads(open(os.path.join(ROOT, 'site', 'garden.yaml'), encoding='utf-8').read())
    G = os.path.join(TMP, 'garden-' + GD['gardener']['id'])
    grow = ['seed/germinate.py', G, '--gardener', GD['gardener']['id'], '--gardener-name', GD['gardener']['name']]
    for p in GD.get('profiles') or []:
        grow += ['--profile', p]
    r = _run(grow, REL)
    if r.returncode:
        _fail('the scene garden did not grow', r.stdout + r.stderr)
    for b, text in GD['beans'].items():
        open(os.path.join(G, 'beans', b + '.md'), 'w', encoding='utf-8', newline='\n').write(text)
    sv = GD['save']
    r = _run(['bin/dmsave.py', sv['who'], sv['what'], '--body', sv['body']], G)
    gate = _run(['bin/dmcheck.py', '--all'], G).stdout
    if r.returncode or not re.search(r' 0 error\(s\), 0 warning\(s\)', gate):
        _fail("the scene garden's forms do not pass their gate cleanly", r.stdout + r.stderr + gate)
    gid = re.search(r'garden ([0-9a-f]{12})\)', gate).group(1)
    save = f'python3 bin/dmsave.py "{sv["who"]}" "{sv["what"]}" \\\n  --body "{sv["body"]}"'
    out = {}
    for m in B['mechanisms']:
        sc = m['scene']
        forms = []
        for sh in sc['show']:
            if sh.get('save'):
                forms.append(save)
            else:
                forms.append((f"# beans/{sh['bean']}.md\n" if len(sc['show']) > 1 else '')
                             + _keys(GD['beans'][sh['bean']], sh['keys']))
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
        open(path, 'w', encoding='utf-8', newline='\n').write(text)
        if bk.get('staged'):
            subprocess.run(['git', 'add', '-A'], cwd=G, capture_output=True)
        said = _run(['bin/dmcheck.py', '--staged' if bk.get('staged') else '--all'], G).stdout
        if bk.get('staged'):
            subprocess.run(['git', 'reset', '-q'], cwd=G, capture_output=True)
        if orig is None:
            os.remove(path)
        else:
            open(path, 'w', encoding='utf-8', newline='\n').write(orig)
        lines, found = said.splitlines(), None
        for i, line in enumerate(lines):
            if line.startswith('ERROR '):
                j = i + 1
                while j < len(lines) and lines[j][:1].isspace():
                    j += 1
                block = lines[i:j]
                if sc['refused'] in ' '.join(block):
                    found = block
                    break
        if not found:
            _fail(f"{m['id']}: the gate did not refuse the break with {sc['refused']!r}", said)
        clean = lambda s: s.replace(G, '.').replace(gid, '<garden id>')
        out[m['id']] = {'form': '\n'.join(forms), 'error': clean(found[0][len('ERROR '):]),
                        'fix': clean(' '.join(l.strip() for l in found[1:])).lstrip('— ').strip()}
    return out


SCENES = scenes()
DATA = {'version': VERSION, 'release': RELEASE, 'lenses': B['lenses'], 'mechanisms': []}
for m in B['mechanisms']:
    DATA['mechanisms'].append({k: m.get(k) for k in ('id', 'name', 'short', 'glyph', 'staples', 'person', 'gardener',
                                                     'agent_note')} | {'keeper': keeper(m)} | SCENES[m['id']])
counts = {'terms': sum(1 for k in PARTS if k.startswith('term:')),
          'registries': sum(1 for k in PARTS if k.startswith('registry:')),
          'relations': len(RELS), 'reasons': len(REASONS)}
DATA['counts'] = counts
DATA['ropes'] = ROPES
DATA['ground'] = GROUND
for m in DATA['mechanisms']:
    m['files'] = len(FILES[m['id']])

page = open(os.path.join(ROOT, 'site', 'board.html'), encoding='utf-8').read()
page = page.replace('/*__DATA__*/', json.dumps(DATA, ensure_ascii=False).replace('</', '<\\/'))
page = page.replace('__VERSION__', html.escape(VERSION)).replace('__RELEASE__', html.escape(RELEASE or 'the release'))
open(OUT, 'w', encoding='utf-8').write(page)
print(f"site/board.py: {len(DATA['mechanisms'])} mechanisms × {len(DATA['lenses'])} lenses = "
      f"{len(DATA['mechanisms']) * len(DATA['lenses'])} boards, std-vocab {VERSION}; "
      f"wrote {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT):,} bytes)")
