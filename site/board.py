#!/usr/bin/env python3
"""site/board.py — the one page: daftar through four lenses and ten mechanisms, a board for every crossing.

    python3 site/board.py [--out site/index.html]

Reads site/boards.yaml (what a person writes: each lens's words for each mechanism) and the release itself — the law's
meanings (seed/std-vocab.md), their reasons (seed/RATIONALE.md), and the catalogue's parts, rules, checks and relations
(bin/dmcatalog.py) — and writes ONE self-contained page: its style, its script and its data inline. A keeper's board is
never written by hand: it is read from the release it describes, so it cannot drift from it."""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmparse  # noqa: E402
import dmwhy    # noqa: E402

OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(ROOT, 'site', 'index.html')
B = dmparse.loads(open(os.path.join(ROOT, 'site', 'boards.yaml'), encoding='utf-8').read())
LAW = dmparse.loads(dmparse.split_front_matter(open(os.path.join(ROOT, 'seed', 'std-vocab.md'), encoding='utf-8').read())[0])
VERSION = str(LAW.get('version'))
try:
    RELEASE = open(os.path.join(ROOT, 'site', 'RELEASE'), encoding='utf-8').read().strip()
except OSError:
    RELEASE = ''

import subprocess  # noqa: E402
CATJ = json.loads(subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'daftar.py'), 'catalog', '--json'],
                                 capture_output=True, text=True, cwd=ROOT).stdout)
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
            continue
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


def files_of(mech):
    ids = {resolve(i) for i in mech.get('items') or []} - {None}
    out = set()
    for r in RELS:
        if r.get('to') in ids and not str(r.get('from')).split(':')[0] in ('term', 'registry', 'section', 'profile', 'layer'):
            out.add(r['from'])
        if r.get('from') in ids and not str(r.get('to')).split(':')[0] in ('term', 'registry', 'section', 'profile', 'layer'):
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


DATA = {'version': VERSION, 'release': RELEASE, 'lenses': B['lenses'], 'mechanisms': []}
for m in B['mechanisms']:
    DATA['mechanisms'].append({k: m.get(k) for k in ('id', 'name', 'short', 'glyph', 'staples', 'person', 'gardener', 'agent_form',
                                                     'agent_note', 'refusal')} | {'keeper': keeper(m)})
counts = {'terms': sum(1 for k in PARTS if k.startswith('term:')), 'registries': sum(1 for k in PARTS if k.startswith('registry:')),
          'relations': len(RELS), 'reasons': len(REASONS)}
DATA['counts'] = counts
DATA['ropes'] = ROPES
DATA['ground'] = GROUND
for m in DATA['mechanisms']:
    m['files'] = len(FILES[m['id']])

page = open(os.path.join(ROOT, 'site', 'board.html'), encoding='utf-8').read()
page = page.replace('/*__DATA__*/', 'const DATA = ' + json.dumps(DATA, ensure_ascii=False) + ';')
page = page.replace('__VERSION__', html.escape(VERSION)).replace('__RELEASE__', html.escape(RELEASE or 'the release'))
open(OUT, 'w', encoding='utf-8').write(page)
print(f"site/board.py: {len(DATA['mechanisms'])} mechanisms × {len(DATA['lenses'])} lenses = "
      f"{len(DATA['mechanisms']) * len(DATA['lenses'])} boards, std-vocab {VERSION}; wrote {os.path.relpath(OUT, ROOT)} "
      f"({os.path.getsize(OUT):,} bytes)")
