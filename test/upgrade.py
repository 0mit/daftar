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
os.makedirs(REL)
pats = [l.strip() for l in open(os.path.join(ROOT, 'seed', 'LANGUAGE')) if l.strip() and not l.lstrip().startswith('#')]
import glob
for p in pats:
    for f in glob.glob(os.path.join(ROOT, p)):
        if os.path.isfile(f):
            rel = os.path.relpath(f, ROOT)
            os.makedirs(os.path.join(REL, os.path.dirname(rel)), exist_ok=True)
            shutil.copy2(f, os.path.join(REL, rel))
run('git', 'init', '-q', cwd=REL); run('git', 'add', '-A', cwd=REL)
run('git', 'commit', '-qm', 'v1', cwd=REL); run('git', 'tag', 'v0.1.0', cwd=REL)

# ---- the garden, germinated from v1
g = run('sh', os.path.join(REL, 'seed', 'germinate.sh'), GARDEN, cwd=REL)
check("a garden germinates from the release", g.returncode == 0 and '0 error(s)' in g.stdout, (g.stdout + g.stderr)[-300:])
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
check("NOTHING IS COMMITTED — adopting a release is the garden's own decision",
      run('git', 'log', '--oneline', cwd=GARDEN).stdout.count('\n') == 1 and run('git', 'status', '--porcelain', cwd=GARDEN).stdout.strip())
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

shutil.rmtree(TMP, ignore_errors=True)
print(f"\nupgrade: {sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
