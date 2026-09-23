#!/usr/bin/env python3
"""test/upgrade.py — a garden adopts a release through bin/dmupgrade.py, and nothing else moves.

Builds everything it needs: a RELEASE (a git repo made from this tree, tagged, then changed and tagged
again — a tool added, a tool retired, the vocabulary version moved) and a GARDEN germinated from the first
tag. Needs no beans from any estate, so it runs in the public repository's CI as well as in a garden.

Run: python3 test/upgrade.py   (0 = green)
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results = []


def check(name, ok, detail=''):
    ok = bool(ok)
    results.append(ok)
    print(("PASS " if ok else "*** FAIL *** ") + name + (f"  [{detail}]" if detail and not ok else ''))


def run(*a, cwd):
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@x', GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@x')
    return subprocess.run(a, capture_output=True, text=True, cwd=cwd, env=env)


TMP = tempfile.mkdtemp(prefix='dmupg-')
REL, GARDEN = os.path.join(TMP, 'release'), os.path.join(TMP, 'garden')

# ---- the release, v1: this tree's language exactly as seed/LANGUAGE declares it
import glob
def release_from_tree(dst, tag):
    os.makedirs(dst)
    pats = [l.strip() for l in open(os.path.join(ROOT, 'seed', 'LANGUAGE')) if l.strip() and not l.lstrip().startswith('#')]
    for p in pats:
        for f in glob.glob(os.path.join(ROOT, p)):
            if os.path.isfile(f):
                rel = os.path.relpath(f, ROOT)
                os.makedirs(os.path.join(dst, os.path.dirname(rel)), exist_ok=True)
                shutil.copy2(f, os.path.join(dst, rel))
    run('git', 'init', '-q', cwd=dst); run('git', 'add', '-A', cwd=dst)
    run('git', 'commit', '-qm', tag, cwd=dst); run('git', 'tag', tag, cwd=dst)
release_from_tree(REL, 'v0.1.0')

# ---- the garden, germinated from v1
g = run('sh', os.path.join(REL, 'seed', 'germinate.sh'), GARDEN, "--gardener", "keeper", cwd=REL)
check("a garden germinates from the release", g.returncode == 0 and '0 error(s)' in g.stdout, (g.stdout + g.stderr)[-300:])
_commits_before = run('git', 'log', '--oneline', cwd=GARDEN).stdout.count('\n')
ver1 = re.search(r'^version: "([^"]+)"', open(os.path.join(REL, 'seed', 'std-vocab.md')).read(), re.M).group(1)

# ---- the release, v2: a tool added, a tool retired, the vocabulary version moved
open(os.path.join(REL, 'bin', 'dmhello.py'), 'w').write('print("hello")\n')
os.remove(os.path.join(REL, 'bin', 'dmdigest.py'))
sv = os.path.join(REL, 'seed', 'std-vocab.md')
_major, _minor = ver1.split('.')
ver2 = f"{_major}.{int(_minor) + 1}"
_text = open(sv).read()                 # read BEFORE opening for write: 'w' truncates first
open(sv, 'w').write(_text.replace(f'version: "{ver1}"', f'version: "{ver2}"', 1))
run('git', 'add', '-A', cwd=REL); run('git', 'commit', '-qm', 'v2', cwd=REL); run('git', 'tag', 'v0.2.0', cwd=REL)

up = lambda *extra, tag='v0.2.0': run(sys.executable, os.path.join(GARDEN, 'bin', 'dmupgrade.py'), tag, '--from', REL, *extra, cwd=GARDEN)
check("germination records the release the garden grew from",
      'daftar_release: "v0.1.0"' in open(os.path.join(GARDEN, 'GARDEN.md')).read())

# ---- a dirty garden is refused, and nothing is touched
open(os.path.join(GARDEN, 'VOCAB.md'), 'a').write('\n')
r = up()
check("an upgrade over uncommitted changes is REFUSED", r.returncode != 0 and 'REFUSING' in (r.stdout + r.stderr)
      and os.path.isfile(os.path.join(GARDEN, 'bin', 'dmdigest.py')), (r.stdout + r.stderr)[-300:])
run('git', 'checkout', '--', '.', cwd=GARDEN)

# ---- the upgrade
r = up()
out = r.stdout + r.stderr
check("the upgrade runs and the gate passes on the result", r.returncode == 0 and '0 error(s)' in out, out[-400:])
check("a tool the release added arrives", os.path.isfile(os.path.join(GARDEN, 'bin', 'dmhello.py')))
check("a tool the release retired leaves", not os.path.exists(os.path.join(GARDEN, 'bin', 'dmdigest.py')))
check("both pins move to the release's vocabulary",
      all(f'extends: std-vocab@{ver2}' in open(os.path.join(GARDEN, d)).read() for d in ('VOCAB.md', 'GARDEN.md')))
j = open(os.path.join(GARDEN, 'log', 'journal.md')).read()
check("a RULE-CHANGE journal entry names the tag, the vocabulary move and the files",
      'RULE-CHANGE' in j and 'daftar v0.2.0' in j and f'{ver1} -> {ver2}' in j and 'bin/dmhello.py' in j and 'bin/dmdigest.py' in j)
check("a release that does not cross into std-vocab 21.0 translates nothing", '- translated: none' in j, j[-600:])
check("NOTHING IS COMMITTED — adopting a release is the garden's own decision",
      run('git', 'log', '--oneline', cwd=GARDEN).stdout.count('\n') == _commits_before and run('git', 'status', '--porcelain', cwd=GARDEN).stdout.strip())
check("...and GARDEN.md now records the adopted release",
      'daftar_release: "v0.2.0"' in open(os.path.join(GARDEN, 'GARDEN.md')).read())
run('git', 'add', '-A', cwd=GARDEN)
_c = run('git', 'commit', '-qm', 'adopt v0.2.0', cwd=GARDEN)
check("committing with the journal entry's '(fill in' fields left unfilled is REFUSED",
      _c.returncode != 0 and "(fill in" in (_c.stdout + _c.stderr), (_c.stdout + _c.stderr)[-300:])
_jp = os.path.join(GARDEN, 'log', 'journal.md')
_jt = open(_jp).read()
open(_jp, 'w').write(_jt.replace('(fill in who ratified — merging the release\'s pull request, or the word given here)', 'human (test)')
                        .replace('(fill in — what this release brings that this garden adopts)', 'the test release'))
run('git', 'add', '-A', cwd=GARDEN)
_c = run('git', 'commit', '-qm', 'adopt v0.2.0', cwd=GARDEN)
check("once a human fills them in, the adoption commits cleanly through the hook", _c.returncode == 0,
      (_c.stdout + _c.stderr)[-300:])
r = up()
check("a second run finds nothing to do", r.returncode == 0 and 'nothing to do' in r.stdout, (r.stdout + r.stderr)[-300:])
r = up(tag='v0.1.0')
check("an OLDER tag is refused — a downgrade would silently remove fixes",
      r.returncode != 0 and 'OLDER' in (r.stdout + r.stderr) and os.path.isfile(os.path.join(GARDEN, 'bin', 'dmhello.py')),
      (r.stdout + r.stderr)[-300:])
r = up('--allow-downgrade', tag='v0.1.0')
check("...unless --allow-downgrade says it is meant",
      r.returncode == 0 and os.path.isfile(os.path.join(GARDEN, 'bin', 'dmdigest.py')), (r.stdout + r.stderr)[-300:])

# ---- the release, v0.3.0: its OWN upgrade tool differs, and must be the one that runs
_tool = os.path.join(REL, 'bin', 'dmupgrade.py')
_src = open(_tool).read()
open(_tool, 'w').write(_src.replace('def main():\n', 'def main():\n    print("RELEASE-TOOL-RAN")\n', 1))
run('git', 'add', '-A', cwd=REL); run('git', 'commit', '-qm', 'v3', cwd=REL); run('git', 'tag', 'v0.3.0', cwd=REL)
run('git', 'reset', '-q', '--hard', cwd=GARDEN); run('git', 'clean', '-qfd', cwd=GARDEN)
r = up(tag='v0.3.0')
check("a release whose upgrade tool differs is applied BY ITS OWN TOOL, not by the garden's older copy",
      r.returncode == 0 and 'RELEASE-TOOL-RAN' in r.stdout and 'handing over' in r.stdout
      and 'daftar_release: "v0.3.0"' in open(os.path.join(GARDEN, 'GARDEN.md')).read(), (r.stdout + r.stderr)[-400:])
check("...and the journal records where the release came from, not the temporary clone it was applied from",
      f"from {REL} at" in open(os.path.join(GARDEN, 'log', 'journal.md')).read())

# ---- a garden grown before v0.4.0: no release line, a commented pin, a hook that lost its executable bit
run('git', 'reset', '-q', '--hard', cwd=GARDEN); run('git', 'clean', '-qfd', cwd=GARDEN)
_gp = os.path.join(GARDEN, 'GARDEN.md')
_g = re.sub(r'^daftar_release:.*\n', '', open(_gp).read(), count=1, flags=re.M)
_g = re.sub(r'^(extends: std-vocab@\S+).*$', r'\1    # an old comment on the pin', _g, count=1, flags=re.M)
open(_gp, 'w').write(_g)
os.chmod(os.path.join(GARDEN, 'bin', 'hooks', 'pre-commit'), 0o644)
run('git', 'add', '-A', cwd=GARDEN); run('git', 'commit', '-qm', 'old garden', '--no-verify', cwd=GARDEN)
r = up('--allow-downgrade', tag='v0.2.0')
_g = open(_gp).read()
check("an old garden gets its release recorded on a line of its own, and the pin keeps its comment",
      re.search(r'^extends: std-vocab@\S+    # an old comment on the pin$', _g, re.M)
      and re.search(r'^daftar_release: "v0.2.0"', _g, re.M), _g[:300])
check("a file whose bytes match but whose executable bit does not is restored",
      os.access(os.path.join(GARDEN, 'bin', 'hooks', 'pre-commit'), os.X_OK), (r.stdout + r.stderr)[-300:])

# ---- a release the garden cannot live under is NOT applied: every file is put back (v0.5.0)
run('git', 'reset', '-q', '--hard', cwd=GARDEN); run('git', 'clean', '-qfd', cwd=GARDEN)
_readme = open(os.path.join(ROOT, 'seed', 'README.md')).read() + open(os.path.join(ROOT, 'seed', 'COOKBOOK.md')).read()
_ex = dict(re.findall(r'<!-- example: (beans/[a-z0-9-]+\.md) -->\n```markdown\n(.*?)\n```', _readme, re.S))
os.makedirs(os.path.join(GARDEN, 'beans'), exist_ok=True)   # git clean removed the empty directory
open(os.path.join(GARDEN, 'beans', 'sam.md'), 'w').write(_ex['beans/sam.md'] + '\n')
open(os.path.join(GARDEN, 'beans', 'vps-a.md'), 'w').write(_ex['beans/vps-a.md'].replace('provides_habitat: linux-vm\n', 'provides_habitat: linux-vm\nos: debian\n') + '\n')
_gp = os.path.join(GARDEN, 'GARDEN.md')
_gtext = open(_gp).read()                       # read FIRST: open(..., 'w') truncates before the read would run
open(_gp, 'w').write(re.sub(r'^(extends: std-vocab@.*)$', r'\1\ndaftar_release: "v0.2.0"', _gtext, count=1, flags=re.M))
subprocess.run([sys.executable, os.path.join(GARDEN, 'bin', 'dmjournal.py'), 'human (test)',
                '[[sam]] and [[vps-a]], a debian VPS; RULE-CHANGE: release v0.2.0 recorded', '--body', '- action: added both.'],
               cwd=GARDEN, check=True, capture_output=True)
run('git', 'add', '-A', cwd=GARDEN)
_c = run('git', 'commit', '-qm', 'a debian vps', cwd=GARDEN)
check("(setup) a VPS on a standard OS commits", _c.returncode == 0, (_c.stdout + _c.stderr)[-300:])
_t = open(sv).read()
open(sv, 'w').write(_t.replace(', debian', '', 1).replace('  - { os: debian,', '  # removed in this test release:', 1))
run('git', 'add', '-A', cwd=REL); run('git', 'commit', '-qm', 'no debian', cwd=REL); run('git', 'tag', 'v0.0.9', cwd=REL)
_before = run('git', 'rev-parse', 'HEAD', cwd=GARDEN).stdout
r = up('--allow-downgrade', tag='v0.0.9')
check("a release under which the garden FAILS its gate is refused, and says why",
      r.returncode != 0 and 'NOT DOWNGRADED' in r.stdout and "'debian'" in r.stdout, (r.stdout + r.stderr)[-400:])
check("...and nothing is left half-applied: the working tree is exactly as it was",
      not run('git', 'status', '--porcelain', '--untracked-files=all', cwd=GARDEN).stdout.strip()
      and run('git', 'rev-parse', 'HEAD', cwd=GARDEN).stdout == _before,
      run('git', 'status', '--porcelain', cwd=GARDEN).stdout[:300])
r = up('--allow-downgrade', tag='v0.1.0')
check("a downgrade that succeeds is reported as a DOWNGRADE, in the output and in the journal",
      r.returncode == 0 and 'downgraded to v0.1.0' in r.stdout
      and 'language downgraded to daftar v0.1.0' in open(os.path.join(GARDEN, 'log', 'journal.md')).read(),
      (r.stdout + r.stderr)[-300:])

# ==== CROSSING INTO std-vocab 21.0: a garden grown under 20.0 is translated, and names who keeps it ===============
# The fixture is a garden grown from this tree and then AGED into the shape 20.0 gave it — its vocabulary labelled
# 20.0, `scope` on its anchors, `seeds_from`/`created`/`models` in its manifest, `attributes:` on its beans, and no
# gardener — so the test needs no 20.0 release and runs where the history is shallow.
import datetime
R21, G20 = os.path.join(TMP, 'release21'), os.path.join(TMP, 'garden20')
release_from_tree(R21, 'v9.0.0')
g = run(sys.executable, os.path.join(R21, 'seed', 'germinate.py'), G20, cwd=R21)
check("(setup) a garden grows from a release at std-vocab 21.0 or later", g.returncode == 0, (g.stdout + g.stderr)[-300:])


def path20(rel):
    return os.path.join(G20, *rel.split('/'))


def put(rel, text):
    os.makedirs(os.path.dirname(path20(rel)), exist_ok=True)
    with open(path20(rel) + '.tmp', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    os.replace(path20(rel) + '.tmp', path20(rel))


def get(rel):
    return open(path20(rel), encoding='utf-8').read()


_sv = get('seed/std-vocab.md')
ver21 = re.search(r'^version: "([^"]+)"', _sv, re.M).group(1)
put('seed/std-vocab.md', re.sub(r'^version: "[^"]+"', 'version: "20.0"', _sv, count=1, flags=re.M))
put('VOCAB.md', re.sub(r'^(extends: std-vocab@)\S+', r'\g<1>20.0', get('VOCAB.md'), count=1, flags=re.M))
_g = re.sub(r'^(extends: std-vocab@)\S+', r'\g<1>20.0', get('GARDEN.md'), count=1, flags=re.M)
_g = re.sub(r'^gardener:.*\n', '', _g, count=1, flags=re.M)
_g = re.sub(r'^daftar_release:.*$', 'daftar_release: "v0.32.0"  # the daftar release this garden runs; bin/dmupgrade.py moves it\n'
            'created: "git-metadata"    # NEVER a canonical value; the real timestamp lives in git\n'
            'seeds_from: [garden-b]     # gardens merged in, per MERGE.md\n'
            'models: [model-a]', _g, count=1, flags=re.M)
put('GARDEN.md', _g)
_readme = open(os.path.join(ROOT, 'seed', 'README.md'), encoding='utf-8').read()
_ex = dict(re.findall(r'<!-- example: (beans/[a-z0-9-]+\.md) -->\n```markdown\n(.*?)\n```', _readme, re.S))
# sam: a flow anchor carrying `scope`, and `attributes:` beside `details:` — one key in both, alike
put('beans/sam.md', _ex['beans/sam.md']
    .replace('establishing: true }', 'establishing: true, scope: global }', 1)
    .replace('responsibility: { legal: { self: true } }\n',
             'responsibility: { legal: { self: true } }\n'
             'attributes:\n  # kept here until a term holds them\n  shoe_size: 44\n  desk: "by the window"\n'
             'details:\n  desk: "by the window"\n  languages: [en, tr]\n', 1) + '\n')
# laptop: a flow anchor and a BLOCK anchor carrying `scope`, `attributes:` alone, and a pointer into it
put('beans/laptop.md', _ex['beans/laptop.md']
    .replace('class: hardware, establishing: true }', 'class: hardware, establishing: true, scope: global }', 1)
    .replace('    - { key: hostname, value: "laptop", class: network, establishing: false }\n',
             '    - key: hostname\n      value: "laptop"\n      class: network\n      scope: local        # 20.0 wrote it\n'
             '      establishing: false\n', 1)
    .replace('responsibility: {', 'attributes:\n  luks_root: true\nbeanger:\n  luks-root:\n'
             '    defines: "whether the root filesystem is encrypted"\n    tracks: "attributes.luks_root"\n'
             '    source: "lsblk -f"\n    records:\n'
             '      - { seq: 1, at: 1786245253747, op: add, value: true, prev: null, who: "tool:probe" }\n'
             'responsibility: {', 1) + '\n')
run('git', 'add', '-A', cwd=G20)
_c = run('git', 'commit', '-qm', 'a garden as std-vocab 20.0 left it', '--no-verify', cwd=G20)
check("(setup) the garden is aged into std-vocab 20.0's shape", _c.returncode == 0, (_c.stdout + _c.stderr)[-300:])
_aged = run('git', 'rev-parse', 'HEAD', cwd=G20).stdout.strip()


def up21(*extra, env=None, tag='v9.0.0'):
    e = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@x', GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@x')
    for k in ('DAFTAR_GARDENER', 'DAFTAR_GARDENER_NAME', 'PYTHONIOENCODING', 'PYTHONUTF8'):
        e.pop(k, None)
    e.update(env or {})
    return subprocess.run([sys.executable, path20('bin/dmupgrade.py'), tag, '--from', R21, *extra],
                          capture_output=True, text=True, cwd=G20, env=e)


def commit20(msg):
    run('git', 'add', '-A', cwd=G20); run('git', 'commit', '-qm', msg, '--no-verify', cwd=G20)
    return run('git', 'rev-parse', 'HEAD', cwd=G20).stdout.strip()


def untouched(head):
    return (not run('git', 'status', '--porcelain', '--untracked-files=all', cwd=G20).stdout.strip()
            and run('git', 'rev-parse', 'HEAD', cwd=G20).stdout.strip() == head)


def reset(to):
    run('git', 'reset', '-q', '--hard', to, cwd=G20); run('git', 'clean', '-qfdx', '-e', '.git', cwd=G20)


r = up21()
out = r.stdout + r.stderr
check("crossing into 21.0 with no gardener is REFUSED, with the one line that fixes it and the people it could be",
      r.returncode != 0 and 'GARDENER' in out and '--gardener <id>' in out and 'sam' in out and untouched(_aged), out[-600:])
r = up21('--gardener', 'laptop')
check("...a gardener that is a machine is refused: a garden is kept by a person or an organisation",
      r.returncode != 0 and "'laptop' is a host" in r.stdout + r.stderr and untouched(_aged), (r.stdout + r.stderr)[-300:])
r = up21('--gardener', 'ada')
check("...a gardener with no bean here is refused, saying --gardener-name plants one",
      r.returncode != 0 and '--gardener-name' in r.stdout + r.stderr and untouched(_aged), (r.stdout + r.stderr)[-300:])
r = up21('--gardener', 'sam', '--gardener-name', 'Sam')
check("...and --gardener-name for a bean that exists is refused rather than planted over it",
      r.returncode != 0 and 'already a bean' in r.stdout + r.stderr and untouched(_aged), (r.stdout + r.stderr)[-300:])

# ---- what a translation may not decide: a key both bags hold differently, and an agreement in the old words
put('beans/nas.md', _ex['beans/laptop.md'].replace('bean: laptop', 'bean: nas').replace('PF-12345', 'NAS-1')
    .replace('value: "laptop"', 'value: "nas"').replace('responsibility: {', 'attributes: { bays: 4 }\ndetails: { bays: 2 }\nresponsibility: {', 1) + '\n')
put('beans/deal.md', '---\nbean: deal\nkind: contract\ntitle: "a deal"\nbetween: [sam, nas]\nbalance: 3\n---\nA deal.\n')
run('git', 'add', '-A', cwd=G20); run('git', 'commit', '-qm', 'two beans a person must re-express', '--no-verify', cwd=G20)
_both = run('git', 'rev-parse', 'HEAD', cwd=G20).stdout.strip()
r = up21('--gardener', 'sam')
out = r.stdout + r.stderr
check("a key `attributes` and `details` hold with different values is REFUSED, naming it; nothing is touched",
      r.returncode != 0 and 'beans/nas.md' in out and 'bays' in out and untouched(_both), out[-600:])
check("...and a bean still carrying the old agreement words is refused with the cookbook's agreement recipe",
      'beans/deal.md' in out and '`between`' in out and '`balance`' in out and 'seed/COOKBOOK.md' in out, out[-600:])
r = up21('--gardener', 'sam', '--keep-on-failure')
out = r.stdout + r.stderr
_nas, _deal = get('beans/nas.md'), get('beans/deal.md')
check("with --keep-on-failure the rest is applied, and what is the person's is left, named, in the journal",
      r.returncode != 0 and 'attributes: { bays: 4 }' in _nas and 'between:' in _deal and 'scope' not in get('beans/sam.md')
      and 'LEFT FOR A PERSON' in get('log/journal.md'), out[-600:])
reset(_aged)

# ---- the translation, with an existing person as the gardener
r = up21('--gardener', 'sam')
out = r.stdout + r.stderr
check("the upgrade crosses into 21.0 and the gate passes on the result", r.returncode == 0 and '0 error(s)' in out, out[-700:])
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmparse
_fms = {os.path.basename(p)[:-3]: dmparse.loads(dmparse.read(p)[0]) for p in glob.glob(path20('beans/*.md'))}
check("`scope` has left every anchor", all('scope' not in a for fm in _fms.values()
                                              for a in (fm.get('identity') or {}).get('anchors') or []), _fms.keys())
_gm = dmparse.loads(dmparse.read(path20('GARDEN.md'))[0])
check("GARDEN.md loses `seeds_from`, `created` and `models`, and names its gardener",
      not {'seeds_from', 'created', 'models'} & set(_gm) and _gm.get('gardener') == 'sam', _gm)
check("`attributes` joins `details` where both are: every value kept, the key both held alike kept once, the comment kept",
      'attributes' not in _fms['sam'] and _fms['sam']['details'] == {'desk': 'by the window', 'languages': ['en', 'tr'], 'shoe_size': 44}
      and '# kept here until a term holds them' in get('beans/sam.md'), _fms['sam'].get('details'))
check("...becomes `details` where it was alone, and a pointer into it follows it",
      'attributes' not in _fms['laptop'] and _fms['laptop']['details'] == {'luks_root': True}
      and _fms['laptop']['beanger']['luks-root']['tracks'] == 'details.luks_root', _fms['laptop'])
j = get('log/journal.md').split('\n## ')[-1]
_tl = next((l for l in j.splitlines() if l.startswith('- translated:')), '')
check("the journal's `translated:` line says what the step did, bean by bean",
      'std-vocab 21.0' in _tl and '`scope` removed from 3 anchor(s)' in _tl and '[[sam]]' in _tl and '[[laptop]]' in _tl
      and 'seeds_from' in _tl and 'models' in _tl and '`attributes` moved into `details`' in _tl and 'gardener [[sam]]' in _tl, _tl)
check("...and quotes what each removed manifest key said, the gardens taken in left for a person to record",
      '`seeds_from` (was ["garden-b"])' in _tl and '`models` (was ["model-a"])' in _tl
      and 'as a `garden` bean' in _tl and "a person's to write" in _tl, _tl)
check("NOTHING IS COMMITTED by the translation either", run('git', 'rev-parse', 'HEAD', cwd=G20).stdout.strip() == _aged)
_jt = get('log/journal.md')
put('log/journal.md', _jt.replace("(fill in who ratified — merging the release's pull request, or the word given here)", 'human (test)')
    .replace('(fill in — what this release brings that this garden adopts)', 'the test release'))
run('git', 'add', '-A', cwd=G20)
_c = run('git', 'commit', '-qm', 'adopt 21.0', cwd=G20)
check("once a human fills it in, the translated garden commits through its hook — every bean and removed key journalled",
      _c.returncode == 0, (_c.stdout + _c.stderr)[-600:])

# ---- a CRLF checkout — Git for Windows' default — still installs hooks that run, and commits go through them
_shf = ['bin/hooks/pre-commit', 'bin/hooks/pre-push', 'bin/hooks/python.sh', 'bin/install.sh', 'seed/germinate.sh']
for f in _shf:
    os.remove(path20(f))
run('git', '-c', 'core.autocrlf=true', 'checkout', '--', *_shf, cwd=G20)
_cr = [f for f in _shf if b'\r' in open(path20(f), 'rb').read()]
check("`.gitattributes` keeps the shell LF in a checkout that turns text to CRLF (core.autocrlf=true)", not _cr, _cr)
_ca = run('git', 'check-attr', 'text', 'eol', '--', 'captures/probe.sh', cwd=G20).stdout
check("...and a captured `.sh` stays byte-for-byte: `captures/** -text` is not overridden", 'text: unset' in _ca
      and 'eol: unspecified' in _ca, _ca)
for f in _shf:                          # ...and a checkout made before that line, or with it overridden
    _b = open(path20(f), 'rb').read()
    with open(path20(f), 'wb') as fh:
        fh.write(_b.replace(b'\n', b'\r\n'))
_i = run(sys.executable, path20('bin/install.py'), cwd=G20)
_gd = run('git', 'rev-parse', '--git-common-dir', cwd=G20).stdout.strip()
_hd = os.path.join(G20 if not os.path.isabs(_gd) else '', _gd, 'hooks')
_cr = [n for n in ('pre-commit', 'pre-push', 'python.sh') if b'\r' in open(os.path.join(_hd, n), 'rb').read()]
check("bin/install.py installs the hooks with LF from a CRLF checkout", _i.returncode == 0 and not _cr,
      (_cr, _i.stdout + _i.stderr))
put('beans/sam.md', get('beans/sam.md').replace('shoe_size: 44', 'shoe_size: 45', 1))
run('git', 'add', 'beans/sam.md', cwd=G20)
_c = run('git', 'commit', '-qm', 'a change with no journal entry', cwd=G20)
check("...the hook installed from it RUNS: a bean change with no journal entry is refused",
      _c.returncode != 0 and 'journal' in (_c.stdout + _c.stderr) and 'cannot exec' not in _c.stderr
      and "\\r'" not in _c.stderr and '$\'\\r' not in _c.stderr, (_c.stdout + _c.stderr)[-400:])
subprocess.run([sys.executable, path20('bin/dmjournal.py'), 'human (test)', '[[sam]] shoe size',
                '--body', '- action: corrected [[sam]].'], cwd=G20, check=True, capture_output=True)
run('git', 'add', 'beans/sam.md', 'log/journal.md', cwd=G20)
_c = run('git', 'commit', '-qm', 'a journalled change', cwd=G20)
check("...and a journalled one commits through it", _c.returncode == 0, (_c.stdout + _c.stderr)[-400:])

# ---- a new gardener planted, exactly as seed/germinate.py plants one — qualified by this garden's id, as at birth
reset(_aged)
r = up21('--gardener', 'ada', '--gardener-name', 'Ada')
out = r.stdout + r.stderr
import importlib.util
_spec = importlib.util.spec_from_file_location('germinate_for_test', os.path.join(ROOT, 'seed', 'germinate.py'))
_germ = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_germ)
_gid20 = run('git', 'rev-list', '--first-parent', '--max-parents=0', 'HEAD', cwd=G20).stdout.split()[-1][:12]
check("--gardener-name plants the gardener's person bean exactly as seed/germinate.py --gardener does",
      r.returncode == 0 and os.path.isfile(path20('beans/ada.md'))
      and get('beans/ada.md') == _germ.gardener_bean('ada', 'Ada', datetime.date.today().isoformat(), _gid20)
      and f'value: "{_gid20}/person:ada"' in get('beans/ada.md')
      and re.search(r'^gardener: ada\b', get('GARDEN.md'), re.M) and '[[ada]]' in get('log/journal.md').split('\n## ')[-1], out[-600:])
# a Persian name keeps its zero-width non-joiner, and a name with both kinds of quote is still one YAML string
for _nm in ('آدا\u200cبانو', 'Ada "the elder" O\'Neil'):
    reset(_aged)
    r = up21('--gardener', 'ada', '--gardener-name', _nm)
    _pfm = dmparse.loads(dmparse.read(path20('beans/ada.md'))[0]) if os.path.isfile(path20('beans/ada.md')) else {}
    check(f"...the planted title is the name exactly, character for character ({_nm!a})",
          r.returncode == 0 and _pfm.get('title') == _nm and '0 error(s)' in r.stdout, (r.stdout + r.stderr)[-400:])
# a release whose germinate spells the name wrongly (Python's repr turns the non-joiner into six characters) is refused
_gp21 = os.path.join(R21, 'seed', 'germinate.py')
_gt21 = open(_gp21, encoding='utf-8').read()
with open(_gp21, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(_gt21.replace('title: {json.dumps(name, ensure_ascii=False)}', 'title: {name!r}', 1))
run('git', 'add', '-A', cwd=R21); run('git', 'commit', '-qm', 'a germinate that writes repr', cwd=R21); run('git', 'tag', 'v9.0.1', cwd=R21)
reset(_aged)
r = up21('--gardener', 'ada', '--gardener-name', 'آدا\u200cبانو', tag='v9.0.1')
check("...and a planted bean that would not say the name asked for is REFUSED before anything is touched",
      _gt21.count('json.dumps(name') == 1 and r.returncode != 0 and 'does not say what was asked' in r.stdout + r.stderr
      and '`title`' in r.stdout + r.stderr and untouched(_aged), (r.stdout + r.stderr)[-400:])

# ---- a translated garden that still fails its gate is put back WHOLE: the beans, the manifest, the planted gardener
reset(_aged)
put('VOCAB.md', get('VOCAB.md').replace('local_terms: []', 'local_terms: [ { term: facets, meaning: "the facet lattice, as 20.0 let a garden overlay it" } ]', 1))
run('git', 'add', '-A', cwd=G20); run('git', 'commit', '-qm', 'a retired overlay', '--no-verify', cwd=G20)
_overlay = run('git', 'rev-parse', 'HEAD', cwd=G20).stdout.strip()
r = up21('--gardener', 'ada', '--gardener-name', 'Ada')
check("a garden the release's gate still refuses after the translation is NOT upgraded, and says why",
      r.returncode != 0 and 'NOT UPGRADED' in r.stdout and 'facets' in r.stdout, (r.stdout + r.stderr)[-600:])
check("...and every file is put back, the planted gardener's bean with them",
      untouched(_overlay) and not os.path.exists(path20('beans/ada.md')), run('git', 'status', '--porcelain', cwd=G20).stdout[:300])

# ---- a garden whose own tool is OLDER than the flags hands over, and the environment carries the gardener
reset(_aged)
# (the tool as it was: it knows no `--gardener`, and an argument it does not know is an error, not handed over)
_old = (get('bin/dmupgrade.py').replace("add_argument('--gardener', ", "add_argument('--gardener', dest='gardener', ")
        .replace("add_argument('--gardener-name', ", "add_argument('--gardener-name', dest='gardener_name', ")
        .replace('--gardener', '--steward').replace('a, unknown = ap.parse_known_args()', 'a, unknown = ap.parse_args(), []'))
put('bin/dmupgrade.py', _old)
run('git', 'add', '-A', cwd=G20); run('git', 'commit', '-qm', 'an upgrade tool from before the gardener', '--no-verify', cwd=G20)
_oldtool = run('git', 'rev-parse', 'HEAD', cwd=G20).stdout.strip()
r = up21()
out = r.stdout + r.stderr
check("an older tool hands over, and the refusal prints the form it can pass on: the environment",
      r.returncode != 0 and 'handing over' in out and 'DAFTAR_GARDENER=<id>' in out and untouched(_oldtool), out[-600:])
r = up21(env={'DAFTAR_GARDENER': 'sam', 'DAFTAR_GARDENER_NAME': 'Sam'})
out = r.stdout + r.stderr
check("...a refusal names the variable a value came from, and every fix it prints is one this garden's tool accepts",
      r.returncode != 0 and 'DAFTAR_GARDENER_NAME plants a NEW one' in out and 'unset DAFTAR_GARDENER_NAME' in out
      and 'DAFTAR_GARDENER=sam python3 bin/dmupgrade.py' in out and '--gardener' not in out and untouched(_oldtool), out[-600:])
# the printed line, for sh and for PowerShell, from what THIS garden's tool knows — quoted, and with no [optional] parts
import dmupgrade as _du
_du.ROOT = G20
_st = _du.Step21(R21, 'v9.0.0', os.path.join(TMP, 'a release'), (None, None, None, None), False)
_line_sh = _st.fix_line('<id>', '<how they are called>')
_saved_os = os.name
try:
    os.name = 'nt'
    _line_ps = _st.fix_line('<id>', '<how they are called>')
finally:
    os.name = _saved_os
check("...on PowerShell the line clears the variables it set, which a session would keep for the next garden",
      _line_ps.startswith('$env:DAFTAR_GARDENER = "<id>"; $env:DAFTAR_GARDENER_NAME = "<how they are called>"; python bin\\dmupgrade.py v9.0.0 --from \'')
      and _line_ps.endswith('; Remove-Item Env:DAFTAR_GARDENER, Env:DAFTAR_GARDENER_NAME -ErrorAction SilentlyContinue')
      and _line_sh == f'DAFTAR_GARDENER=<id> DAFTAR_GARDENER_NAME="<how they are called>" python3 bin/dmupgrade.py v9.0.0 --from '
                      f"'{os.path.join(TMP, 'a release')}'" and '[' not in _line_sh + _line_ps, (_line_sh, _line_ps))
r = up21(env={'DAFTAR_GARDENER': 'sam'})
check("...and with DAFTAR_GARDENER set, the release's own tool translates the garden, saying where the gardener came from",
      r.returncode == 0 and re.search(r'^gardener: sam\b', get('GARDEN.md'), re.M) and '0 error(s)' in r.stdout
      and "the gardener: 'sam', taken from DAFTAR_GARDENER" in r.stdout, (r.stdout + r.stderr)[-600:])

# ---- a GARDEN.md and a bean saved with a byte-order mark, as PowerShell 5.1 saves UTF-8, are translated and keep it
reset(_aged)
_BOM = '\ufeff'
put('GARDEN.md', _BOM + get('GARDEN.md'))
put('beans/laptop.md', _BOM + get('beans/laptop.md'))
_bom = commit20('two files saved with a byte-order mark')
r = up21('--gardener', 'sam')
_lfm = dmparse.loads(dmparse.read(path20('beans/laptop.md'))[0])
check("a manifest and a bean with a byte-order mark are translated, and keep the mark",
      r.returncode == 0 and '0 error(s)' in r.stdout and get('GARDEN.md').startswith(_BOM) and get('beans/laptop.md').startswith(_BOM)
      and _lfm.get('details') == {'luks_root': True} and 'attributes' not in _lfm
      and re.search(r'^gardener: sam\b', get('GARDEN.md'), re.M), (r.stdout + r.stderr)[-600:])

# ---- a gate that quotes Persian, read through a pipe in an old code page (as on Windows), still says why
reset(_aged)
put('beans/cai.md', _ex['beans/sam.md'].replace('bean: sam', 'bean: cai').replace('"person:sam"', '"person:cai"')
    .replace('title: "Sam', 'title: "Cai').replace('status: active', 'status: فعال') + '\n')
_fa = commit20('a status in Persian')
r = up21('--gardener', 'sam', env={'PYTHONIOENCODING': 'cp1252'})
out = r.stdout + r.stderr
check("read through a pipe in an old code page, a gate that quotes Persian still says why the garden was not upgraded",
      r.returncode != 0 and 'NOT UPGRADED' in out and re.search(r'ERROR.*cai.*status', out) and 'Traceback' not in out
      and untouched(_fa), out[-600:])

# ---- anything that stops the upgrade midway — here a folder it cannot write — puts every file back, and says so
if os.name != 'nt' and os.geteuid() != 0:
    reset(_aged)
    os.chmod(path20('beans'), 0o555)
    try:
        r = up21('--gardener', 'sam')
    finally:
        os.chmod(path20('beans'), 0o755)
    out = r.stdout + r.stderr
    check("a write that fails midway puts back the release's files, the pins and every bean, and says so",
          r.returncode != 0 and 'PermissionError' in out and 'every file was put back' in out and untouched(_aged), out[-600:])

# ---- the text edits, each on the form a garden may hold: refused never, damaged never
def _fm(t):
    return dmparse.loads(dmparse.split_front_matter(t)[0])
_t = '---\nbean: x\nidentity:\n  anchors:\n    - scope: global\n      key: hostname\n      value: "x"\n---\nbody\n'
check("a block anchor that OPENS with `- scope:` loses it, the next key moving up onto the dash",
      _fm(_du.drop_anchor_key(_t, 'scope')) == {'bean': 'x', 'identity': {'anchors': [{'key': 'hostname', 'value': 'x'}]}},
      _du.drop_anchor_key(_t, 'scope'))
_t = ('---\nbean: x\nidentity:\n  anchors:\n    - { key: path, value: "C:\\\\data\\\\", class: logical, scope: global }\n'
      '    - { key: p, value: \'it\'\'s, {x}\', scope: global }\n---\n')
check("a flow anchor whose value ends in a backslash (a Windows path) loses `scope`, and nothing else",
      _fm(_du.drop_anchor_key(_t, 'scope')) == {'bean': 'x', 'identity': {'anchors': [
          {'key': 'path', 'value': 'C:\\data\\', 'class': 'logical'}, {'key': 'p', 'value': "it's, {x}"}]}},
      _du.drop_anchor_key(_t, 'scope'))
_t = '---\nbean: x\nattributes:\n  "desk": 1\n  b: 2\ndetails:\n  desk: 1\n---\n'
_n, _why = _du.move_attributes(_t, _fm(_t))
check("a key both bags hold alike is kept once, whether or not it is quoted",
      not _why and _fm(_n) == {'bean': 'x', 'details': {'desk': 1, 'b': 2}}
      and not dmparse.duplicate_keys(dmparse.split_front_matter(_n)[0]), _n)
_t = '---\nbean: x\nattributes: { a: 1 }  # from the old form\ndetails:\n  b: 2\n---\n'
_n, _why = _du.move_attributes(_t, _fm(_t))
check("the comment on a one-line `attributes: {…}` comes with it into `details`",
      not _why and '# from the old form' in _n and _fm(_n) == {'bean': 'x', 'details': {'b': 2, 'a': 1}}, _n)
_u = os.path.join(TMP, 'unit')
os.makedirs(os.path.join(_u, 'beans'))
with open(os.path.join(_u, 'beans', 'x.md'), 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('---\nbean: x\nattributes:\n  luks_root: true\nbeanger:\n  luks-root:\n    tracks: "attributes.luks_root"\n---\n'
             'Moved from: attributes.luks_root\n')
_du.ROOT = _u
_n, _form, _facts, _probs = _du.plan_doc(os.path.join(_u, 'beans', 'x.md'))
check("a pointer is followed in the front matter only; a body line naming the old place is prose, left as written",
      _n and not _probs and 'tracks: "details.luks_root"' in _n and _n.endswith('Moved from: attributes.luks_root\n'),
      (_n, _probs))

# ==== WHICH PYTHON runs the hooks and the merge driver: the first that RUNS and IMPORTS yaml =======================
# A Windows machine's `python3` may be the Store's App execution alias: found on the PATH, running no Python. Faked
# here as a script under a `WindowsApps` directory that answers as the alias does, beside a `python` without PyYAML.
if os.name != 'nt':
    FAKE, TOOLS = os.path.join(TMP, 'fake', 'WindowsApps'), os.path.join(TMP, 'fake', 'tools')
    os.makedirs(FAKE); os.makedirs(TOOLS)
    with open(os.path.join(FAKE, 'python3'), 'w', newline='\n') as fh:
        fh.write('#!/bin/sh\necho "Python was not found; run without arguments to install from the Microsoft Store" >&2\nexit 9009\n')
    with open(os.path.join(TOOLS, 'python'), 'w', newline='\n') as fh:
        fh.write(f'#!/bin/sh\nexec "{sys.executable}" -S -I "$@"\n')      # a Python that cannot see PyYAML
    for f in (os.path.join(FAKE, 'python3'), os.path.join(TOOLS, 'python')):
        os.chmod(f, 0o755)
    for tool in ('git', 'dirname'):
        os.symlink(shutil.which(tool), os.path.join(TOOLS, tool))
    SH, PYSH = shutil.which('sh'), os.path.join(G20, 'bin', 'hooks', 'python.sh')
    _path = os.pathsep.join([FAKE, TOOLS])

    def choose(config=None):
        run('git', 'config', '--unset', 'daftar.python', cwd=G20)
        if config:
            run('git', 'config', 'daftar.python', config, cwd=G20)
        r = subprocess.run([SH, '-c', '. "$1"; daftar_choose_python && echo "PY=$DAFTAR_PY"', 'sh', PYSH],
                           capture_output=True, text=True, cwd=G20, env=dict(os.environ, PATH=_path))
        return r, run('git', 'config', '--get', 'daftar.python', cwd=G20).stdout.strip()

    r, _cfg = choose()
    check("the hook refuses when no Python runs, naming each candidate and why: the Store alias, a missing PyYAML, none",
          r.returncode != 0 and 'python3: is the Microsoft Store alias (App execution aliases)' in r.stderr
          and 'python: runs, but PyYAML is missing: python -m pip install PyYAML' in r.stderr and 'py -3: not found' in r.stderr
          and not _cfg, r.stdout + r.stderr)
    _real = sys.executable.replace('\\', '/')
    r, _cfg = choose('/nowhere/python')
    check("...a recorded Python that no longer runs is named as such", 'git config daftar.python (/nowhere/python): not found'
          in r.stderr, r.stderr)
    r, _cfg = choose(_real)
    check("...and the one recorded in `git config daftar.python` is used when it runs, and kept",
          r.returncode == 0 and 'PY=' in r.stdout and _cfg == _real, r.stdout + r.stderr)
    import importlib.util as _iu
    _sp = _iu.spec_from_file_location('install_for_test', os.path.join(G20, 'bin', 'install.py'))
    _inst = _iu.module_from_spec(_sp); _sp.loader.exec_module(_inst)
    run('git', 'config', '--unset', 'daftar.python', cwd=G20)
    _saved = os.environ['PATH']
    os.environ['PATH'] = _path
    try:
        _py, _why = _inst.choose_python(G20)
    finally:
        os.environ['PATH'] = _saved
    _cfg = run('git', 'config', '--get', 'daftar.python', cwd=G20).stdout.strip()
    check("bin/install.py skips the alias and the Python without PyYAML, takes the one running it, and records it per clone",
          _py and not _why and _cfg == _py and os.path.samefile(_py, sys.executable), (_py, _why, _cfg))
    # a Python under a folder named outside the old code page (a Windows profile named in Persian), probed through
    # pipes in that code page: it has PyYAML, and is found to have it
    _fa_dir = os.path.join(TMP, 'دفتر-py')
    os.makedirs(_fa_dir)
    os.symlink(sys.executable, os.path.join(_fa_dir, 'python3'))
    os.environ['PYTHONIOENCODING'] = 'cp1252'
    try:
        _got = _inst.probe([os.path.join(_fa_dir, 'python3')])
    finally:
        del os.environ['PYTHONIOENCODING']
    check("...and a Python whose path the pipe's code page cannot spell is still found to run and import yaml",
          _got[0] and 'دفتر-py' in _got[0] and not _got[1], _got)
    # seed/germinate.sh chooses as the hooks do: the alias is named as such, never run as if it were Python
    _gt = os.path.join(TMP, 'never-grown')
    r = subprocess.run([SH, os.path.join(ROOT, 'seed', 'germinate.sh'), _gt, '--gardener', 'keeper'],
                       capture_output=True, text=True, cwd=TMP, env=dict(os.environ, PATH=_path))
    check("seed/germinate.sh refuses where no Python runs, naming the Store alias, and grows nothing",
          r.returncode != 0 and 'python3: is the Microsoft Store alias' in r.stderr and not os.path.exists(_gt),
          r.stdout + r.stderr)

shutil.rmtree(TMP, ignore_errors=True)
print(f"\nupgrade: {sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
