#!/usr/bin/env python3
"""A cold start (design check C10, the drill's half that needs no model): someone with no memory of the garden — an
empty home, no harness's files, no settings — finds from the garden alone where the work stands and what waits for its
gardener, and the gardener meets what waits with one action.

A garden grown from this tree's release as INSTALL.md says, in a home that holds nothing. The commands its own
AGENTS.md tells an arriving agent to run first are read from that file and run as written: the gate's last line says
how many errors, the garden's id and its gardener are named, and where the work stands is read. A need parked on the
gardener's bean, as the forms write one, is then what waits, with its words. The gardener meets it with the one action
daftard's landing takes (daftard/python/garden_worker.py `decide_pending`), and nothing waits after. The home is as
empty at the end as at the start: nothing was read from it, and nothing written to it.

The drill's other half, an agent of some make set down in a fresh container with the public repository and nothing
else, needs a model and its harness, and is run outside daftar's suites.

Run: python3 test/cold_start.py   (0 = green)
"""
import json, os, re, shutil, subprocess, sys, tempfile

T = tempfile.mkdtemp(prefix='cold-')
HOME = os.path.join(T, 'home')
os.makedirs(HOME)
for k in [k for k in os.environ if k.startswith(('XDG_', 'CLAUDE', 'ANTHROPIC', 'DAFTAR'))]:
    del os.environ[k]
os.environ.update(HOME=HOME, USERPROFILE=HOME, GIT_CONFIG_NOSYSTEM='1', PYTHONNOUSERSITE='1')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))
import grow  # noqa: E402

FAILS = []
PY = sys.executable
G = os.path.join(T, 'garden-sam')


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def run(*a):
    p = subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=G, env=grow.ENV)
    return p.returncode, p.stdout + p.stderr


def home():
    return sorted(os.path.relpath(os.path.join(d, f), HOME) for d, _ds, fs in os.walk(HOME) for f in fs)


try:
    rel = grow.release(os.path.join(T, 'release'))
    r = grow.garden(rel, G, 'sam', '--gardener-name', 'Sam', '--zone', 'Europe/Istanbul')
    check("a garden grown from the release as INSTALL.md says, in a home that holds nothing", r.returncode == 0,
          r.out[-800:])

    # ---- the door: what the garden's own AGENTS.md tells an arriving agent to run first
    door = open(os.path.join(G, 'AGENTS.md'), encoding='utf-8').read()
    first = door[:door.index('## Before writing')] if '## Before writing' in door else door
    cmds = re.findall(r'^    (python3 [^\n]+?)\s*$', first, re.M)
    check("the door names its first commands, each a tool of the garden", cmds[:3] == [
        'python3 core/check.py', 'python3 bin/propose.py id', 'python3 bin/now.py'], cmds)
    said = {}
    for c in cmds:
        rc, out = run(PY, *c.split()[1:])
        said[c] = (rc, out)
    rc, out = said.get('python3 core/check.py', (1, ''))
    check("the gate over the whole garden: its last line says how many errors", rc == 0
          and re.search(r'— 0 error\(s\)\s*$', out), out[-600:])
    rc, out = said.get('python3 bin/propose.py id', (1, ''))
    check("...the garden named, its id and its gardener", rc == 0 and re.search(r'^garden_id: "[0-9a-f]{12}"$', out, re.M)
          and re.search(r'^gardener: sam$', out, re.M), out)
    rc, out = said.get('python3 bin/now.py', (1, ''))
    check("...and where the work stands, read from the garden: no session open, nothing waiting", rc == 0
          and 'where the work stands' in out and 'open sessions: 0' in out
          and 'waiting on the gardener (sam): 0 need(s)' in out, out)

    # ---- a need parked, as the forms write one: what waits is read from the garden alone
    p = os.path.join(G, 'beans', 'sam.md')
    text = open(p, encoding='utf-8').read()
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text.replace('\n---\n', '\n  - need: { id: roof-mended, by: self, of: "the roof mended before winter", '
                                         'from: sam, note: "class D" }\n  - say: { by: sam, of: [roof-mended], at: now }'
                                         '\n---\n', 1))
    rc, out = run(PY, 'bin/save.py', 'sam', 'a need waiting on Sam', '--body',
                  '- action: [[sam]] needs the roof mended before winter')
    check("a need parked on the gardener's bean, saved", rc == 0, out[-800:])
    rc, out = run(PY, *cmds[2].split()[1:])
    check("...is what waits for the gardener, with its words, when the work is read again", rc == 0
          and 'waiting on the gardener (sam): 1 need(s)' in out and 'the roof mended before winter' in out, out)

    # ---- the gardener meets it with one action: the landing's, as daftard asks the garden's worker
    env = dict(grow.ENV, DAFTAR_KIND='core', DAFTARD_NOTIFY='off', PYTHONUTF8='1')
    w = subprocess.Popen([PY, os.path.join(ROOT, 'daftard', 'python', 'garden_worker.py')], cwd=G, env=env, text=True,
                         encoding='utf-8', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = [0]

    def ask(method, params=None):
        n[0] += 1
        w.stdin.write(json.dumps({'id': n[0], 'method': method, 'params': params or {}}) + '\n')
        w.stdin.flush()
        return json.loads(w.stdout.readline() or '{}')
    leads = ask('leads').get('result') or []
    need = next((x for x in leads if x.get('kind') == 'pending' and str(x.get('id')).endswith('.roof-mended')), None)
    landing = ask('pending', {'id': need['id']}).get('result') or {} if need else {}
    met = ask('decide_pending', {'id': need['id'], 'decision': 'acked', 'digest': landing.get('digest', ''),
                                 'words': 'done before the first frost', 'request': 'a' * 32}) if need else {}
    w.stdin.close()
    w.wait(timeout=60)
    check("its landing shows the need as its bean says it", need is not None
          and 'the roof mended before winter' in json.dumps(landing, ensure_ascii=False), (leads, landing))
    rc, out = run(PY, *cmds[2].split()[1:])
    last = run('git', 'show', '--format=%an %s', '-U0', 'HEAD')[1]
    check("...one action meets it — its bean holds the gardener's `meet`, known by their words — and nothing waits",
          met.get('ok') and 'waiting on the gardener (sam): 0 need(s)' in out
          and '+  - meet: { id: roof-mended-met, by: sam, '
          'of: roof-mended }' in last and 'done before the first frost' in last, (met, out, last))

    # ---- no memory: nothing read from the home, nothing written to it
    check("the home holds nothing after: no memory, no settings, no harness's files were made or needed", home() == [],
          home())
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncold_start: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
