#!/usr/bin/env python3
"""site/machinery/build.py — daftar's own mechanisms, drawn by factory, for the machinery page of daftar's site.

    python3 site/machinery/build.py CHECKOUT --garden GARDEN_SAM [--site SITE_DIR] [--keep DIR]

CHECKOUT is a checkout of factory, the application layer that draws a daftar garden's mechanisms, at a release tag and
with nothing uncommitted. This script is the one place it is run for the site, and the site publishes what it draws,
never its source. GARDEN_SAM is the demo garden-sam that `site/build.py` grows (`site/build.py --keep DIR` leaves it at
DIR/garden-sam); `site/build.py --machinery CHECKOUT` runs this script on it. SITE_DIR is the site written into, by
default the directory above this one. `--keep DIR` works in DIR, which must not exist, and leaves it there.

WHAT IT DOES, in a clone of GARDEN_SAM (a clone is the same garden, with the same id) in a temporary directory:

  1. records, from `record.yaml` beside this file, in one journalled commit: the `daftar` product bean with the wiring
     of its mechanisms, one `procedure` mapping per mechanism (gate, journal, merge, mycelium, ledger), the `factory`
     bean that says which mechanisms are drawn and how, the `design-factory` bean — the levels, archetypes and level
     patterns of the checkout's templates/levels.yaml and the pattern library of templates/pattern_library.yaml, with
     `drawing.boundary` added, because the kit draws a boundary the template library does not list — and
     `bin/mechanisms.py`, a copy of `composers.py`, the drawings. The glossary is README.md's "Words you will meet",
     read from this repository at the release the garden runs.
  2. vendors the checkout's release into the clone (`factory upgrade`), journals it and commits it.
  3. runs `factory check` and `factory report` on the real clock. Everything before runs under the held day of the
     demo gardens (`site/demo/clock/sitecustomize.py`, or the one the caller's PYTHONPATH carries, at
     $DAFTAR_DEMO_NOW, by default 2026-10-27 09:00 UTC), so the garden's journal agrees with the rest of the site.
  4. holds the drawings to the design: at most 18 elements and exactly one accent per figure, 960 wide and 280 to 340
     tall, no address; a story of 3 to 5 stages, labels of at most 5 words, doers of at most 14, technologies only
     git and python; no Operate archetype and no live binding anywhere, so every Operate tile reads "no signal"; the
     wiring of the gate, the journal, the merge and the mycelium present.
  5. refuses to write when the report or the transcript holds this machine's host name, the user's name, the real
     home directory, the temporary directory or any absolute path. Paths are shown as `~/garden-sam` and `~/factory`.
  6. writes SITE_DIR/machinery/report.html and SITE_DIR/machinery/drawn.json (the page's data: the levels, the
     mechanisms, what the demo cannot show, the commands run and what they printed), each through a temporary file.

The environment of every command is set here: HOME is a directory of its own, the clone commits as sam
<sam@example.org>, TZ=UTC, and no DAFTAR_*, GIT_* or FACTORY_* variable of the caller reaches a tool — the held moment
is set again from $DAFTAR_DEMO_NOW, for the garden's writes only.

Exit 0 drawn; 2 anything else — a checkout that is not exactly a tag or holds uncommitted changes, a garden that is not
the demo garden-sam, a refusal by the gate or by factory, a drawing out of the design, a leak — with nothing written.
"""
import datetime
import getpass
import hashlib
import html
import json
import os
import pwd
import re
import shutil
import site
import socket
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO_NOW = '2026-10-27T09:00:00+00:00'
MECHANISMS = ('gate', 'journal', 'merge', 'mycelium', 'ledger')
WIRED = ('gate', 'journal', 'merge', 'mycelium')
NEEDED_BEANS = ('sam', 'ali', 'garden-ali', 'shared-camera', 'washer-loan')
TECH = {'git', 'python'}
PY = sys.executable
CANNOT = [
    "Operate reads live data. The demo garden has no probe, no metric and no Prometheus, so no mechanism declares an "
    "archetype or a binding, and every part reads \u201cno signal\u201d, with the reason: that is the demo garden's true state.",
    "Actions: none is placed. A button in the report asks for a tool by name, and only a host's own configuration can "
    "make it run anything.",
    "Author edits a copy of the record in the reader's browser. What it exports is imported into a garden by a command "
    "run in that garden; nothing imports it here.",
    "Grafana and the live page are not part of this site.",
]


class Refused(Exception):
    pass


def refuse(msg):
    raise Refused(msg)


def argv():
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0 if a else 2)
    opts, pos, i = {}, [], 0
    while i < len(a):
        if a[i] in ('--garden', '--site', '--keep'):
            if i + 1 >= len(a):
                refuse('%s needs a value' % a[i])
            opts[a[i][2:]] = a[i + 1]
            i += 2
        elif a[i].startswith('-'):
            refuse('unknown option %s' % a[i])
        else:
            pos.append(a[i])
            i += 1
    if len(pos) != 1 or 'garden' not in opts:
        refuse('usage: build.py CHECKOUT --garden GARDEN_SAM [--site SITE_DIR] [--keep DIR]')
    return (os.path.abspath(pos[0]), os.path.abspath(opts['garden']),
            os.path.abspath(opts.get('site') or os.path.dirname(HERE)), opts.get('keep'))


def git(*a, cwd):
    return subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')


# ---------------------------------------------------------------------------------------------------------------------
# refusals before any work
# ---------------------------------------------------------------------------------------------------------------------
def check_checkout(co):
    for f in ('bin/factory', 'lib/fxmodel.py', 'lib/fxdraw.py', 'templates/levels.yaml', 'templates/pattern_library.yaml'):
        if not os.path.isfile(os.path.join(co, f)):
            refuse('%s is not a checkout of the drawing tool: it has no %s' % (co, f))
    r = git('describe', '--exact-match', '--tags', 'HEAD', cwd=co)
    if r.returncode != 0 or not r.stdout.strip():
        refuse("the checkout's HEAD is not exactly a tag — check out a release (git checkout vX.Y.Z)")
    tag = r.stdout.strip()
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        refuse('the checkout is at tag %r, which is not a release (vX.Y.Z)' % tag)
    if git('status', '--porcelain', cwd=co).stdout.strip():
        refuse('the checkout has uncommitted changes — a release is what its tag says, nothing else')
    m = re.search(r'(?m)^CONTRACT = (\d+)', open(os.path.join(co, 'lib', 'fxmodel.py'), encoding='utf-8').read())
    if not m:
        refuse("cannot read the contract number from the checkout's lib/fxmodel.py")
    return tag, int(m.group(1))


def check_garden(g):
    gm = os.path.join(g, 'GARDEN.md')
    if not os.path.isfile(gm):
        refuse('%s is not a garden: it has no GARDEN.md' % g)
    text = open(gm, encoding='utf-8').read()
    name = re.search(r'(?m)^garden:\s*"?([^"\s#]+)', text)
    rel = re.search(r'(?m)^daftar_release:\s*"?([^"#\n]+?)"?\s*(#|$)', text)
    if not name or name.group(1) != 'garden-sam':
        refuse('%s is not the demo garden-sam (its GARDEN.md names %r)' % (g, name and name.group(1)))
    if not rel or not re.fullmatch(r'v\d+\.\d+\.\d+', rel.group(1).strip()):
        refuse('the garden records daftar_release %r, not a release: grow it from a clone at a tag (site/build.py '
               'does)' % (rel and rel.group(1)))
    missing = [b for b in NEEDED_BEANS if not os.path.isfile(os.path.join(g, 'beans', b + '.md'))]
    if missing:
        refuse('the garden has no %s — it is not the demo garden-sam site/build.py grows' % ', '.join(missing))
    if git('rev-parse', '--verify', '-q', 'HEAD', cwd=g).returncode != 0:
        refuse('%s is not a git repository with a commit' % g)
    return name.group(1), rel.group(1).strip()


def held_clock():
    """(the directory holding sitecustomize.py, the moment): the site's own, else the one the caller passes."""
    now = os.environ.get('DAFTAR_DEMO_NOW') or DEMO_NOW
    try:
        datetime.datetime.fromisoformat(now)
    except ValueError:
        refuse('DAFTAR_DEMO_NOW=%r is not an ISO moment' % now)
    cands = [os.path.join(os.path.dirname(HERE), 'demo', 'clock')] + \
        [p for p in os.environ.get('PYTHONPATH', '').split(os.pathsep) if p]
    for c in cands:
        if os.path.isfile(os.path.join(c, 'sitecustomize.py')):
            return os.path.abspath(c), now
    refuse('the held clock is missing: no site/demo/clock/sitecustomize.py, and none on the caller\'s PYTHONPATH')


def readme_glossary(release):
    """README.md's "Words you will meet", at the release the garden runs, as {term: meaning} with Markdown taken out."""
    r = git('show', '%s:README.md' % release, cwd=HERE)
    if r.returncode != 0:
        refuse('cannot read README.md at %s from this repository: %s' % (release, r.stderr.strip()))
    sec = re.search(r'(?ms)^## Words you will meet\n(.*?)(?=^## )', r.stdout)
    if not sec:
        refuse('README.md at %s has no "Words you will meet" section' % release)

    def plain(s):
        s = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', s)
        return re.sub(r'\*\*|`', '', s).strip()
    out = {}
    for line in sec.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) != 2 or not cells[0].startswith('**'):
            continue
        for term in plain(cells[0]).split(' / '):
            out[term.strip()] = plain(cells[1])
    if len(out) < 10:
        refuse("README.md's word table read as %d terms; expected its whole table" % len(out))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# the run
# ---------------------------------------------------------------------------------------------------------------------
class Run:
    def __init__(self, root, checkout, clock, now):
        self.root, self.checkout, self.clock, self.now = root, checkout, clock, now
        self.home = os.path.join(root, '.home')
        os.makedirs(self.home)
        with open(os.path.join(self.home, '.gitconfig'), 'w', encoding='utf-8') as fh:
            fh.write('[init]\n\tdefaultBranch = master\n[advice]\n\tdetachedHead = false\n')
        self.transcript = []

    def env(self, held):
        e = {k: v for k, v in os.environ.items()
             if not k.startswith(('DAFTAR_', 'GIT_', 'FACTORY_')) and k not in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP')}
        e.update(HOME=self.home, GIT_CONFIG_NOSYSTEM='1', TZ='UTC', LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONUTF8='1',
                 PYTHONDONTWRITEBYTECODE='1', PYTHONUSERBASE=os.environ.get('PYTHONUSERBASE') or site.getuserbase())
        if held:
            e.update(PYTHONPATH=self.clock, DAFTAR_DEMO_NOW=self.now, GIT_AUTHOR_DATE=self.now, GIT_COMMITTER_DATE=self.now)
        return e

    def shown(self, s):
        """A path as the page shows it: the checkout as ~/factory, the temporary root as ~."""
        return s.replace(self.checkout, '~/factory').replace(self.root, '~')

    def run(self, argv, cwd, held=True, show=None, elide=None, ok=(0,)):
        """Run one command. `show` is the command as the transcript records it (None: not recorded); `elide` a regex
        of output lines the transcript folds into one `…` line (never edits one)."""
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace',
                           env=self.env(held))
        out = (r.stdout + r.stderr).strip('\n')
        if r.returncode not in ok:
            refuse('`%s` exited %d:\n%s' % (show or ' '.join(argv), r.returncode, self.shown(out)[-3000:]))
        if show is not None:
            lines, kept = out.splitlines(), []
            for ln in lines:
                if elide and re.match(elide, ln):
                    if not kept or kept[-1] != '…':
                        kept.append('…')
                else:
                    kept.append(ln)
            self.transcript.append({'cwd': self.shown(cwd), 'cmd': show, 'out': self.shown('\n'.join(kept)),
                                    'exit': r.returncode})
        return out


def front(d):
    """Front matter as YAML. A day is written as a plain YAML date — also when the caller's held clock has put its own
    subclass of `datetime.date` in this process, which PyYAML would otherwise refuse to write."""
    import yaml

    class Dumper(yaml.SafeDumper):
        pass
    for cls in datetime.date.__mro__[:-1]:        # the real class, and the held clock's subclass when there is one
        Dumper.add_multi_representer(cls, lambda r, v: r.represent_scalar('tag:yaml.org,2002:timestamp', v.isoformat()))
    return yaml.dump(d, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=100000, default_flow_style=False)


def write_md(path, fm, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('---\n' + front(fm) + '---\n' + body.strip() + '\n')


def record(g, rec, checkout, tag, contract, day, glossary):
    """Write the record of §4.1 into the clone `g`."""
    import yaml
    prov = {'src': 'observed', 'by': 'sam', 'as_of': day}
    p = rec['product']
    write_md(os.path.join(g, 'beans', 'daftar.md'), {
        'bean': 'daftar', 'genos': 'product', 'title': p['title'], 'status': 'active', 'summary': p['summary'],
        'nature': 'lekton',
        'identity': {'status': 'confirmed', 'anchors': [
            {'key': 'product_id', 'value': 'product:daftar', 'class': 'logical', 'establishing': True}]},
        'provenance': prov, 'owned_by': {'legal': {'external': 'the daftar project'}},
        'responsibility': {'legal': {'holder': {'bean': 'sam'}}}, 'details': p['details']}, p['body'])
    for key in MECHANISMS:
        m = rec['mappings'][key]
        write_md(os.path.join(g, 'mappings', key + '.md'), {
            'mapping': key, 'kind': 'procedure', 'summary': m['summary'], 'provenance': prov, 'steps': m['steps']},
            "daftar's %s, as the machinery page draws it. Its drawing is bin/mechanisms.py's." % key)
    lv = yaml.safe_load(open(os.path.join(checkout, 'templates', 'levels.yaml'), encoding='utf-8'))
    lib = yaml.safe_load(open(os.path.join(checkout, 'templates', 'pattern_library.yaml'), encoding='utf-8'))['pattern_library']
    if 'boundary' not in lib['drawing']:
        lib['drawing']['boundary'] = {'depth': 1, 'meaning': lv['level_patterns']['understand']['boundary']}
    write_md(os.path.join(g, 'beans', 'design-factory.md'), {
        'bean': 'design-factory', 'genos': 'design',
        'title': 'design-factory — the levels of detail factory draws this garden at',
        'status': 'active',
        'summary': "factory's default levels, archetypes and pattern library, copied from its templates, with the "
                   "boundary its kit draws.",
        'nature': 'lekton',
        'identity': {'status': 'confirmed', 'anchors': [
            {'key': 'product_id', 'value': 'design:levels-of-detail', 'class': 'logical', 'establishing': True}]},
        'provenance': prov, 'owned_by': {'legal': {'owner': {'bean': 'sam'}}},
        'responsibility': {'legal': {'holder': {'bean': 'sam'}}},
        'details': {'levels': lv['levels'], 'archetypes': lv['archetypes'], 'level_patterns': lv['level_patterns'],
                    'pattern_library': lib}},
        "The levels of detail, their archetypes and the pattern library, as the templates of factory %s give them; "
        "`drawing.boundary` is added, with the meaning the understand level gives a boundary." % tag)
    d = rec['drawing']
    mechs = []
    for m in d['mechanisms']:
        m = {k: v for k, v in m.items() if k != 'demo'}
        mechs.append(m)
    write_md(os.path.join(g, 'beans', 'factory.md'), {
        'bean': 'factory', 'genos': 'product', 'title': "factory — draws daftar's mechanisms at four levels",
        'status': 'active',
        'summary': "Which of daftar's mechanisms this garden draws, in what order, and what each level asks of them.",
        'nature': 'lekton',
        'identity': {'status': 'confirmed', 'anchors': [
            {'key': 'product_id', 'value': 'product:mechanism-drawings', 'class': 'logical', 'establishing': True}]},
        'provenance': prov, 'owned_by': {'legal': {'external': 'the factory project'}},
        'responsibility': {'legal': {'holder': {'bean': 'sam'}}},
        'details': {'factory_contract': contract, 'factory_release': tag, 'garden_module': 'bin/mechanisms.py',
                    'live_base': d['live_base'], 'report': d['report'], 'mechanisms': mechs,
                    'reference': d['reference'], 'kind_details': d['kind_details'], 'glossary': glossary}},
        "What factory draws in this garden: daftar's own mechanisms, for the machinery page of daftar's site.")
    shutil.copyfile(os.path.join(HERE, 'composers.py'), os.path.join(g, 'bin', 'mechanisms.py'))


def fxdata(report):
    m = re.search(r'<script type="application/json" id="fxdata">(.*?)</script>', report, re.S)
    if not m:
        refuse('the report carries no data block (id="fxdata")')
    return json.loads(m.group(1))


def plain(s):
    s = re.sub(r'<span class="tip">.*?</span>', '', s or '', flags=re.S)
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def hold_to_design(p, rec):
    """Refusals when a drawing, a story or a level strays from the design (SITE-DESIGN §4.3)."""
    probs = []
    views = p['views']
    keys = [m['key'] for m in p['mechanisms']]
    if keys != list(MECHANISMS) or not all(m['include'] for m in p['mechanisms']):
        probs.append('the report shows %s, not the five mechanisms in order' % keys)
    recd = {m['key']: m for m in rec['drawing']['mechanisms']}
    for k in MECHANISMS:
        v = views.get(k)
        if not v:
            probs.append('%s: no view in the report' % k)
            continue
        els = v['elements']
        acc = [e['id'] for e in els if e['pattern'] == 'accent' or 'accent' in e['mods']]
        if len(els) > 18:
            probs.append('%s: %d elements drawn, at most 18' % (k, len(els)))
        if len(acc) != 1:
            probs.append('%s: %d accents (%s), exactly one' % (k, len(acc), ', '.join(acc)))
        vb = re.search(r'viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"', v['svg'])
        if not vb or float(vb.group(1)) != 960 or not 280 <= float(vb.group(2)) <= 340:
            probs.append('%s: the figure is %s, not 960 wide and 280 to 340 tall' % (k, vb and vb.groups()))
        if re.search(r'(?<![\w.])\d{1,3}(\.\d{1,3}){3}(?![\w.])|(?<![\w:])[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{0,4}){2,}', v['svg']):
            probs.append('%s: the drawing shows an address' % k)
        if sorted(v['patterns']) != sorted(recd[k]['schema_patterns']):
            probs.append('%s: drawn %s, recorded %s' % (k, v['patterns'], recd[k]['schema_patterns']))
        st = recd[k]['story']['stages']
        if not 3 <= len(st) <= 5:
            probs.append('%s: %d story stages, 3 to 5' % (k, len(st)))
        for i, s in enumerate(st, 1):
            if len(s['label'].split()) > 5:
                probs.append('%s: stage %d label has more than 5 words' % (k, i))
            if len(s['doer'].split()) > 14:
                probs.append('%s: stage %d doer has more than 14 words' % (k, i))
            if set(s.get('tech') or []) - TECH:
                probs.append('%s: stage %d names technology outside %s' % (k, i, sorted(TECH)))
        if v['binds'] or v['live_patterns'] or (v['operate'] or {}).get('archetype') or v['actions']:
            probs.append('%s: a live binding, an Operate archetype or an action is declared; the demo has no live data' % k)
        if not v['tiles'] or not all(t.get('blind') for t in v['tiles']):
            probs.append('%s: an Operate tile does not read "no signal"' % k)
        w = v.get('wiring') or {}
        if k in WIRED and not (w.get('pipes') or w.get('processes')):
            probs.append('%s: no wiring at the Inspect level' % k)
        if set(v['questions']) != {'orient', 'understand', 'operate', 'inspect'}:
            probs.append('%s: questions for %s, not the four levels' % (k, sorted(v['questions'])))
    if [l['id'] for l in p['levels']] != ['orient', 'understand', 'operate', 'inspect']:
        probs.append('the levels are %s' % [l['id'] for l in p['levels']])
    if probs:
        refuse('the drawings stray from the design:\n  - ' + '\n  - '.join(probs))


def leaks(texts, run, paths):
    """What in the published text would say where or by whom it was built."""
    real_home = pwd.getpwuid(os.getuid()).pw_dir
    host = socket.gethostname()
    users = {getpass.getuser(), pwd.getpwuid(os.getuid()).pw_name}
    found = []
    literal = {real_home: 'the real home directory', run.root: 'the temporary directory', '/tmp': '/tmp',
               tempfile.gettempdir(): 'the temporary directory'}
    literal.update({p: 'a path of this machine' for p in paths if p})
    words = {w: 'the host name' for w in {host, host.split('.')[0]} if w}
    words.update({u: "the user's name" for u in users if u})
    for name, t in texts.items():
        for s, what in literal.items():
            if s and len(s) > 1 and s in t:
                found.append('%s holds %s (%s)' % (name, what, s))
        for w, what in words.items():
            if re.search(r'(?<![\w.-])%s(?![\w-])' % re.escape(w), t, re.I):
                found.append('%s holds %s (%s)' % (name, what, w))
        m = re.search(r'(?<![\w.~:/])/(?:home|Users|root|tmp|var|private|mnt|srv|opt|media|run|nix|etc|usr)/[^\s"\'<]*'
                      r'|\b[A-Za-z]:\\[^\s"\'<]*', t)
        if m:
            found.append('%s holds an absolute path (%s)' % (name, m.group(0)[:80]))
    if found:
        refuse('nothing written — the output would say where or by whom it was built:\n  - ' + '\n  - '.join(found))


def main():
    t0 = time.time()
    checkout, garden, site_dir, keep = argv()
    try:
        import yaml
    except ImportError:
        refuse('PyYAML is required (pip install PyYAML)')
    tag, contract = check_checkout(checkout)
    gname, daftar_release = check_garden(garden)
    clock, now = held_clock()
    rec = yaml.safe_load(open(os.path.join(HERE, 'record.yaml'), encoding='utf-8'))
    glossary = readme_glossary(daftar_release)
    day = datetime.datetime.fromisoformat(now).date()
    os.makedirs(os.path.join(site_dir, 'machinery'), exist_ok=True)

    if keep:
        if os.path.exists(keep):
            refuse('--keep %s exists; name a directory to create' % keep)
        os.makedirs(keep)
        root = os.path.realpath(keep)
    else:
        root = os.path.realpath(tempfile.mkdtemp(prefix='daftar-machinery-'))
    try:
        run = Run(root, checkout, clock, now)
        g = os.path.join(root, 'garden-sam')
        run.run(['git', 'clone', '-q', garden, g], cwd=root)
        run.run([PY, 'bin/install.py'], cwd=g)
        run.run(['git', 'config', 'user.name', 'sam'], cwd=g)
        run.run(['git', 'config', 'user.email', 'sam@example.org'], cwd=g)

        # 1. the record, in one journalled commit, under the held day
        record(g, rec, checkout, tag, contract, day, glossary)
        what = "daftar's mechanisms recorded, and how they are drawn"
        body = ("- action: [[daftar]], with the wiring of its mechanisms; the mappings [[gate]], [[journal]], [[merge]], "
                "[[mycelium]] and [[ledger]]; [[factory]] and [[design-factory]], which draw them; bin/mechanisms.py, "
                "the drawings (site/machinery/composers.py).\n"
                "- why: the machinery page of daftar's site shows these mechanisms, drawn at four levels.")
        head = run.run([PY, 'bin/dmjournal.py', 'sam', what, '--body', body], cwd=g,
                       show='python3 bin/dmjournal.py sam "%s" --body "%s"' % (what, body))
        if day.isoformat() not in head:
            refuse('the journal heading %r does not carry the held day %s: the clock was not held' % (head, day))
        run.run(['git', 'add', '-A'], cwd=g, show='git add -A')
        run.run(['git', 'commit', '-q', '-m', what], cwd=g, show='git commit -q -m "%s"' % what, elide=r'PASS ')

        # 2. the drawing tool's release, vendored into the clone, journalled and committed
        up = [PY, os.path.join(checkout, 'bin', 'factory'), 'upgrade', '--from', checkout, '--garden', '.']
        run.run(up, cwd=g, show='python3 ~/factory/bin/factory upgrade --from ~/factory --garden .')
        what = 'factory %s vendored' % tag
        body = ('- action: factory %s vendored into factory/ by factory upgrade, which mirrors its skill at '
                '.claude/skills/factory/SKILL.md; [[factory]] already pins %s.' % (tag, tag))
        run.run([PY, 'bin/dmjournal.py', 'sam', what, '--body', body], cwd=g,
                show='python3 bin/dmjournal.py sam "%s" --body "%s"' % (what, body))
        run.run(['git', 'add', '-A'], cwd=g, show='git add -A')
        run.run(['git', 'commit', '-q', '-m', what], cwd=g, show='git commit -q -m "%s"' % what, elide=r'PASS ')
        last = run.run([PY, 'bin/dmcheck.py', '--all'], cwd=g).splitlines()[-1]
        if not last.endswith('0 error(s), 0 warning(s)'):
            refuse('the clone does not pass its gate: %s' % last)

        # 3. check and report, on the real clock
        fx = [PY, 'factory/bin/factory']
        out = run.run(fx + ['check'], cwd=g, held=False, show='python3 factory/bin/factory check')
        if 'the record and the drawings agree' not in out:
            refuse('factory check: %s' % out)
        out = run.run(fx + ['report', '--out', '../report.html'], cwd=g, held=False,
                      show='python3 factory/bin/factory report --out ../report.html')
        n = len(MECHANISMS)
        if '%d mechanisms (%d shown)' % (n, n) not in out:
            refuse('factory report: %s' % out)
        report = open(os.path.join(root, 'report.html'), encoding='utf-8').read()

        # 4. the drawings against the design
        p = fxdata(report)
        hold_to_design(p, rec)
        stamp = re.search(r'generated (\d{4}-\d\d-\d\d \d\d:\d\d)', report)
        if not stamp:
            refuse('the report carries no "generated" stamp')

        # 5. drawn.json, from the report's own data
        demo = {m['key']: m['demo'] for m in rec['drawing']['mechanisms']}
        raw = report.encode('utf-8')
        drawn = {
            'tool': 'factory', 'tool_release': tag, 'tool_contract': contract,
            'daftar_release': daftar_release, 'demo_day': day.isoformat(), 'garden': gname,
            'drawn_at': stamp.group(1) + ' UTC',
            'report': 'machinery/report.html', 'report_bytes': len(raw),
            'report_sha256': hashlib.sha256(raw).hexdigest(),
            'title': (p.get('report') or {}).get('title', ''),
            'levels': [{k: l.get(k) for k in ('id', 'depth', 'name', 'audience', 'question')} for l in p['levels']],
            'mechanisms': [{
                'key': k, 'title': p['views'][k]['title'], 'claim': plain(p['views'][k]['claim']),
                'questions': {lv: p['views'][k]['questions'].get(lv) for lv in ('orient', 'understand', 'operate', 'inspect')},
                'parts': [x['bean'] for x in p['views'][k]['parts']],
                'patterns': p['views'][k]['patterns'],
                'operate': {'archetype': None, 'would_take': demo[k].get('would_take'), 'why_none': demo[k]['why_none']},
            } for k in MECHANISMS],
            'cannot': CANNOT,
            'transcript': run.transcript,
        }
        dj = json.dumps(drawn, ensure_ascii=False, indent=1) + '\n'
        leaks({'report.html': report, 'drawn.json': dj}, run, [checkout, garden, site_dir, os.getcwd(), HERE])

        # 6. write, each through a temporary file beside its place
        dest = os.path.join(site_dir, 'machinery')
        tmp = []
        for name, data in (('report.html', raw), ('drawn.json', dj.encode('utf-8'))):
            fd, t = tempfile.mkstemp(prefix='.' + name + '.', dir=dest)
            with os.fdopen(fd, 'wb') as fh:
                fh.write(data)
            os.chmod(t, 0o644)
            tmp.append((t, os.path.join(dest, name)))
        for t, final in tmp:
            os.replace(t, final)
        print('machinery: drawn by factory %s at %s from %s (daftar %s): %d mechanisms, %d bytes; wrote %s and %s in %.0f s'
              % (tag, drawn['drawn_at'], gname, daftar_release, n, len(raw), os.path.relpath(tmp[0][1]),
                 os.path.relpath(tmp[1][1]), time.time() - t0))
    finally:
        if not keep:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == '__main__':
    try:
        main()
    except Refused as e:
        print('machinery: %s' % e, file=sys.stderr)
        sys.exit(2)
