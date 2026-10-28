#!/usr/bin/env python3
"""One install and one entry (core 4.15): `bin/install.py --daftard` lays this machine's daftard on this system — its
binary, the garden served, its routines ticked each minute — and `daftar serve`, `daftar board` and `daftar run` are
verbs of the one entry, each with its help.

A garden grown from this tree's release, with the view profile, in a home and a daftar state folder that hold nothing.
Its install without --daftard lays no daftard: an upgrade installs the hooks again, and starts no daemon. With
--daftard and this tree as the source, daftard is built from daftard/ by Go, laid in the state folder, and daftard.json
serves the garden with its routines, on the addresses written there before any garden (the machine's settings, built
on); with --no-service nothing is registered with the system, and the install starts daftard itself. It serves a page
on its loopback: the machine's key gives a one-time code at the door, the code opens the garden's handplace, and
another opens its board. The one entry runs daftard's own commands, and each verb gives its help. An install again
keeps what daftard.json holds, and puts the binary in place of the one running. The release's binary is taken only
when its bytes have the SHA-256 given beside it; the release's source is built only when its tag is signed by a key
the garden's seed/RELEASE-SIGNERS names. Stopped at the end, nothing listens, and the home holds nothing.

Needs Go (the version daftard/go.mod names), git and ssh-keygen; CI runs it on Linux, macOS and Windows.

Run: python3 test/install.py   (0 = green)
"""
import hashlib, http.cookiejar, json, os, pathlib, shutil, socket, subprocess, sys, tempfile, time
import urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GO = shutil.which('go')
if not GO:
    print("FAIL  Go is needed (the version daftard/go.mod names) to build daftard")
    sys.exit(1)
GOENV = {k: subprocess.run([GO, 'env', k], capture_output=True, text=True, encoding='utf-8').stdout.strip()
         for k in ('GOCACHE', 'GOMODCACHE', 'GOPATH')}            # Go's own caches, read before the home is emptied

for k in [k for k in os.environ if k.startswith(('XDG_', 'CLAUDE', 'ANTHROPIC')) or k == 'DAFTAR_GARDEN']:
    del os.environ[k]
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))
import grow  # noqa: E402 — the suite's own temporary folder and daftard state folder (test/machine.py)
import install as dminstall  # noqa: E402

T = tempfile.mkdtemp(prefix='install-')
STATE = os.environ['DAFTARD_STATE']
HOME = os.path.join(T, 'home')
os.makedirs(HOME)
os.environ.update(HOME=HOME, USERPROFILE=HOME, APPDATA=os.path.join(HOME, 'AppData', 'Roaming'),
                  LOCALAPPDATA=os.path.join(HOME, 'AppData', 'Local'), DAFTARD_NOTIFY='off',
                  GIT_CONFIG_NOSYSTEM='1', PYTHONNOUSERSITE='1', **{k: v for k, v in GOENV.items() if v})

FAILS = []
PY = sys.executable
G = os.path.join(T, 'garden-sam')
ENV = {**grow.ENV, **{k: os.environ[k] for k in ('HOME', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'DAFTARD_STATE',
                                                 'DAFTARD_NOTIFY', *[k for k, v in GOENV.items() if v])}}
EXE = dminstall.daftard_path()
if not os.path.realpath(EXE).startswith(os.path.realpath(os.environ['DAFTAR_SUITE_TMP'])):
    print(f"FAIL  daftard would be laid at {EXE}, outside the suite's own folder: nothing is run")
    sys.exit(1)


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]), flush=True)
    if not cond:
        FAILS.append(name)


def run(*a, cwd=G, timeout=900):
    p = subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd, env=ENV,
                       stdin=subprocess.DEVNULL, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


def free(port):
    with socket.socket() as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def ports():
    """A machine's address, its garden's (11 above it, as daftard.json gives the first garden) and Odoo's origin, all
    free here and none a daftard of this machine's own."""
    for base in range(18900, 19800, 37):
        if all(free(p) for p in (base, base + 11, base + 22)):
            return base, base + 11, base + 22
    raise SystemExit("FAIL  no three free ports on the loopback")


def sha(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def conf():
    with open(os.path.join(STATE, 'daftard.json'), encoding='utf-8') as fh:
        return json.load(fh)


NOPROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def door(listen):
    """A one-time code from the door, asked with the machine's key in its header, as `daftard open` asks it."""
    with open(os.path.join(STATE, 'key'), encoding='utf-8') as fh:
        key = fh.read().strip()
    req = urllib.request.Request(f'http://{listen}/door', data=b'', method='POST', headers={'X-Daftard-Key': key})
    with NOPROXY.open(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))['once']


def page(listen, query):
    """The page the code opens, followed through its redirects with the cookie each sets: (final URL, its body)."""
    jar = http.cookiejar.CookieJar()
    o = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(jar))
    q = urllib.parse.urlencode({'once': door(listen), **query})
    with o.open(f'http://{listen}/?{q}', timeout=30) as resp:
        return resp.geturl(), resp.read().decode('utf-8', 'replace')


def listening(*addrs):
    """The addresses something answers a connection at — not a bind refused, which a closed listener's connections
    waiting out their time also refuse."""
    up = []
    for a in addrs:
        try:
            socket.create_connection(('127.0.0.1', int(a.rsplit(':', 1)[1])), timeout=2).close()
            up.append(a)
        except OSError:
            pass
    return up


LISTEN = GARDEN = ODOO = None
try:
    rel = grow.release(os.path.join(T, 'release'))
    r = grow.garden(rel, G, 'sam', '--gardener-name', 'Sam', '--zone', 'Europe/Istanbul', '--profile', 'view')
    check("a garden grown from this tree's release, with the view profile, in a home that holds nothing",
          r.returncode == 0, r.out[-800:])
    name = dminstall.manifest(G, 'garden')
    tag = dminstall.manifest(G, 'daftar_release')

    # ---- the install as it was: no daftard unless it is asked for
    rc, out = run(PY, 'bin/install.py')
    check("an install without --daftard installs the hooks, the merge driver and the agent key, and lays no daftard",
          rc == 0 and 'merge driver' in out and 'agent key' in out and not os.path.exists(EXE)
          and not os.path.exists(os.path.join(STATE, 'daftard.json')), out[-800:])
    rc, out = run(PY, 'bin/install.py', '--listen', '127.0.0.1:1')
    check("...and an option of daftard's alone is refused without --daftard", rc == 2 and '--daftard' in out, out[-300:])

    # ---- the machine's settings, written before any garden: its addresses, none a daftard's of this machine
    p, gp, op = ports()
    LISTEN, GARDEN, ODOO = f'127.0.0.1:{p}', f'127.0.0.1:{gp}', f'127.0.0.1:{op}'
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, 'daftard.json'), 'w', encoding='utf-8') as fh:
        json.dump({'listen': LISTEN, 'odoo_listen': ODOO}, fh)

    # ---- the install: daftard built from this tree, laid, the garden served with its routines, started here
    rc, out = run(PY, 'bin/install.py', '--daftard', '--no-service', '--listen', LISTEN, '--source', ROOT)
    c = conf()
    g = (c.get('gardens') or [{}])[0]
    check("install --daftard builds daftard from daftard/ with Go and lays it in the state folder",
          rc == 0 and os.path.isfile(EXE) and os.path.dirname(EXE) == os.path.join(STATE, 'bin')
          and 'built from' in out and 'laid at' in out, out[-1500:])
    check("...daftard.json serves the garden: its path, the Python chosen, its name, its routines ticked; the machine's "
          "settings kept", os.path.samefile(g.get('path', T), G) and g.get('name') == name and g.get('routines') is True
          and g.get('python') and c.get('listen') == LISTEN and c.get('odoo_listen') == ODOO, json.dumps(c)[:800])
    check("...with --no-service nothing is registered: the install starts daftard itself, and says where it serves",
          'started now' in out and f'serving at http://{LISTEN}' in out and 'daftar board' in out, out[-800:])
    rc2, ver = run(EXE, 'version')
    commit = subprocess.run(['git', '-C', ROOT, 'rev-parse', 'HEAD'], capture_output=True, text=True,
                            encoding='utf-8').stdout.strip()
    check("...the binary is the commit it was built from (`daftard version`)", rc2 == 0 and commit in ver, ver)

    # ---- it serves a page on its loopback
    health = json.loads(NOPROXY.open(f'http://{LISTEN}/health', timeout=10).read().decode('utf-8'))
    check("it answers on its loopback: its health, its build, the garden's own daemon",
          health.get('build') == commit and name in (health.get('gardens') or {}), health)
    url, body = page(LISTEN, {'g': name})
    check("a page: the door's one-time code opens the garden's handplace on its own daemon",
          url.startswith(f'http://{GARDEN}/') and '<html' in body.lower() and 'once=' not in url, (url, body[:300]))
    url, body = page(LISTEN, {'to': f'/board?g={name}'})
    check("...and the garden's board, the address `daftar board` opens", url == f'http://{GARDEN}/board?g={name}'
          and 'board.js' in body, (url, body[:300]))

    # ---- the one entry
    rc, out = run(PY, 'bin/daftar.py', 'serve', 'status')
    st = json.loads(out[out.index('{'):]) if '{' in out else {}
    check("`daftar serve status`: daftard's own command, through the entry — running, at its build",
          rc == 0 and st.get('running') is True and st.get('serving') == commit, out[-600:])
    for verb, said in (('serve', "daftard serve"), ('board', '/board?g=<garden>'), ('run', 'run')):
        rc, out = run(PY, 'bin/daftar.py', 'help', verb)
        check(f"`daftar help {verb}`: its own help", rc == 0 and said in out and verb in out, out[:400])
    rc, out = run(PY, 'bin/daftar.py', 'help', 'serve')
    check("...`daftar help serve` gives daftard's own commands too", 'daftard install --garden' in out
          and 'daftard status' in out, out[-800:])
    rc, out = run(PY, 'bin/daftar.py')
    check("`daftar` lists serve in its family and board among the readings", rc == 0 and '\nserve — ' in out
          and '  serve ' in out and '  board ' in out, out[-1200:])
    other = os.path.join(T, 'not-served')
    shutil.copytree(G, other, ignore=shutil.ignore_patterns('.git'))
    rc, out = run(PY, os.path.join(other, 'bin', 'board.py'), cwd=other)
    check("`daftar board` in a garden this machine's daftard does not serve: refused, the install named",
          rc == 2 and 'does not serve' in out and 'install.py --daftard' in out, out[-400:])

    # ---- an install again: what daftard.json holds is kept; the binary put in place of the one running
    c = conf()
    c['gardens'][0]['quiet'] = True
    with open(os.path.join(STATE, 'daftard.json'), 'w', encoding='utf-8') as fh:
        json.dump(c, fh)
    before = sha(EXE)
    rc, out = run(PY, 'bin/install.py', '--daftard', '--no-service', '--listen', LISTEN, '--source', ROOT)
    c = conf()
    check("an install again keeps what daftard.json holds, and daftard answers again with the binary laid",
          rc == 0 and c['gardens'][0].get('quiet') is True and len(c['gardens']) == 1 and c.get('odoo_listen') == ODOO
          and f'serving at http://{LISTEN}' in out, out[-1000:])

    # ---- the release's binary: taken only when its bytes have the SHA-256 given beside it
    rb = os.path.join(T, 'release-binaries')
    os.makedirs(rb)
    asset = dminstall.asset()
    shutil.copy(EXE, os.path.join(rb, asset))
    good = sha(EXE)
    with open(os.path.join(rb, asset + '.sha256'), 'w', encoding='ascii') as fh:
        fh.write(f"{good}  {asset}\n")
    out_ = os.path.join(T, 'taken')
    ok, how = dminstall.downloaded(rb, out_)
    check(f"the release's {asset}: taken when its bytes have the SHA-256 beside it, and said to prove the transfer alone",
          ok and sha(out_) == good and 'not signed' in how, how)
    with open(os.path.join(rb, asset + '.sha256'), 'w', encoding='ascii') as fh:
        fh.write(f"{'0' * 64}  {asset}\n")
    os.remove(out_)
    ok, why = dminstall.downloaded(rb, out_)
    check("...and refused, nothing written, when they do not", not ok and 'not laid' in why and not os.path.exists(out_),
          why)
    with open(os.path.join(rb, asset + '.sha256'), 'w', encoding='ascii') as fh:
        fh.write(f"{good}  {asset}\n")
    rc, out = run(PY, 'bin/install.py', '--daftard', '--no-service', '--listen', LISTEN, '--binary-from', rb)
    check("install --daftard --binary-from: the release's binary laid, the sum checked, daftard serving again",
          rc == 0 and "the release's" in out and good in out and f'serving at http://{LISTEN}' in out and sha(EXE) == good,
          out[-800:])

    # ---- the release's source: built only when its tag is signed by a key the garden's RELEASE-SIGNERS names
    src = os.path.join(T, 'daftar-src')
    shutil.copytree(os.path.join(ROOT, 'daftard'), os.path.join(src, 'daftard'),
                    ignore=shutil.ignore_patterns('node_modules'))
    keys = {}
    for who in ('release', 'other'):
        k = os.path.join(T, f'{who}-key')
        subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-C', who, '-f', k], check=True,
                       stdin=subprocess.DEVNULL)
        keys[who] = k
    with open(keys['release'] + '.pub', encoding='utf-8') as fh:
        pub = ' '.join(fh.read().split()[:2])
    with open(os.path.join(G, 'seed', 'RELEASE-SIGNERS'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(f'daftar-release namespaces="git" {pub}\n')

    for a in (('init', '-q'), ('add', '-A'), ('commit', '-qm', 'daftard')):
        subprocess.run(['git', '-C', src, *a], check=True, capture_output=True, env=ENV)
    head = subprocess.run(['git', '-C', src, 'rev-parse', 'HEAD'], capture_output=True, text=True,
                          encoding='utf-8').stdout.strip()

    def tagged(key, t):
        subprocess.run(['git', '-C', src, '-c', 'gpg.format=ssh', '-c', f'user.signingkey={key}', 'tag', '-s', '-f',
                        '-m', t, t], check=True, capture_output=True, env=ENV)
    url = pathlib.Path(src).as_uri()
    tagged(keys['other'], tag)
    built = os.path.join(T, 'built')
    with tempfile.TemporaryDirectory(dir=T) as t:
        got, why = dminstall.fetched_source(url, tag, G, os.path.join(t, 'd'))
    check("the release's source, its tag signed by a key the garden's seed/RELEASE-SIGNERS does not name: refused "
          "before any of it is built", got is None and 'not built' in why, why)
    tagged(keys['release'], tag)
    with tempfile.TemporaryDirectory(dir=T) as t:
        got, why = dminstall.fetched_source(url, tag, G, os.path.join(t, 'd'))
        ok, berr = dminstall.go_build(got, built) if got else (False, why)
    rc, ver = run(built, 'version') if ok else (1, berr)
    check("...signed by the key it names: fetched at its tag, verified, built — the binary that commit",
          got is not None and 'signed by a key' in why and ok and head in ver, f"{why} {berr} {ver}")

    # ---- stopped
    rc, out = run(PY, 'bin/daftar.py', 'serve', 'stop')
    time.sleep(1)
    check("`daftar serve stop` stops it: nothing listens at its addresses after", rc == 0 and 'stopped' in out
          and not listening(LISTEN, GARDEN), (out, listening(LISTEN, GARDEN)))
    left = sorted(r for r in (os.path.relpath(os.path.join(d, f), HOME) for d, _ds, fs in os.walk(HOME) for f in fs)
                  if not r.startswith('.gitconfig') and f'go{os.sep}telemetry' not in r)     # Go's own counters aside
    check("with --no-service the home holds nothing of daftard's: no unit, no agent, no task, no link", left == [], left)
finally:
    if os.path.isfile(EXE) and LISTEN and listening(LISTEN):
        subprocess.run([EXE, 'stop'], env=ENV, capture_output=True, timeout=330)
    shutil.rmtree(T, ignore_errors=True)

print(f"\ninstall: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
