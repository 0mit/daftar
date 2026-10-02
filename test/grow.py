"""grow — the one way a suite grows a garden of the core (v1 part 12): a release of the core made from this tree, and a
garden germinated from it. Not a suite: the suites import it.

A garden of the core is grown from a release whose seed/GARDEN.md.template pins `core@` (seed/germinate.py, v1 part 4):
this makes one, the files this tree's seed/LANGUAGE ships with every profile the core offers (core/law/profiles.yaml),
committed and tagged in a repository of its own. A garden in today's words, which adopts the core, is grown from the
last release in them: `today()` makes it from this repository's tag v0.49.0, whole, as a clone of it would be.

    import grow
    rel = grow.release(os.path.join(T, 'release'))            # tagged v1.0.0
    old = grow.today(os.path.join(T, 'today'))                # v0.49.0, today's words: a garden that adopts grows here
    r = grow.garden(rel, os.path.join(T, 'g'), 'sam', '--profile', 'view')
    r.returncode, r.out                                       # germinate's, its output and its errors together
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
for _p in (ROOT, os.path.join(ROOT, 'bin')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import importlib
dmpass = importlib.import_module('pass')  # noqa: E402
from core import read as _read  # noqa: E402

VERSION = str(_read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml'))['version'])
ENV = dict(os.environ, GIT_AUTHOR_NAME='sam', GIT_AUTHOR_EMAIL='sam@x', GIT_COMMITTER_NAME='sam',
           GIT_COMMITTER_EMAIL='sam@x')


class Ran:
    """A command's exit code and what it printed, its output and its errors together."""

    def __init__(self, p):
        self.returncode, self.stdout, self.stderr = p.returncode, p.stdout, p.stderr
        self.out = p.stdout + p.stderr


def run(*a, cwd=None, stdin=None, env=None):
    return Ran(subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd,
                              env=env or ENV, input=stdin))


def _text(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def files():
    """What a release made from this tree carries: seed/LANGUAGE's lines over the tree, every profile the core offers."""
    offers = dmpass.offered_in(lambda p: _text(os.path.join(ROOT, p)) if os.path.isfile(os.path.join(ROOT, p)) else '')
    tree = [f for f in dmpass.tracked(ROOT) if os.path.isfile(os.path.join(ROOT, f))]
    return dmpass.kept(tree, dmpass.language(_text(os.path.join(ROOT, 'seed', 'LANGUAGE'))), offers)


def release(dst, tag='v1.0.0'):
    """A release of the core at `dst`: this tree's shipped files, committed and tagged."""
    os.makedirs(dst)
    for f in files():
        os.makedirs(os.path.join(dst, os.path.dirname(f)), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, f), os.path.join(dst, f))
    for a in (('init', '-q'), ('add', '-A'), ('commit', '-qm', 'the core'), ('tag', tag)):
        r = run('git', *a, cwd=dst)
        if r.returncode:
            raise RuntimeError(f"git {a[0]} in the release: {r.out}")
    return dst


TODAY = 'v0.49.0'          # the last release in today's words (std-vocab 32): what a garden that adopts the core runs


def today(dst, tag=TODAY):
    """The release in today's words at `dst`: this repository's tree at `tag`, whole, committed and tagged — the release a
    garden that adopts the core was grown from. It needs the tag (CI fetches every tag: `fetch-depth: 0`)."""
    os.makedirs(dst)
    arc = subprocess.run(['git', '-C', ROOT, 'archive', '--format=tar', tag], capture_output=True)
    if arc.returncode:
        raise RuntimeError(f"git archive {tag}: {arc.stderr.decode('utf-8', 'replace').strip()} — this checkout lacks the "
                           f"tag; fetch the tags (`git fetch --tags`)")
    x = subprocess.run(['tar', '-x', '-C', dst], input=arc.stdout, capture_output=True)
    if x.returncode:
        raise RuntimeError(f"tar: {x.stderr.decode('utf-8', 'replace').strip()}")
    for a in (('init', '-q'), ('add', '-A'), ('commit', '-qm', "today's words"), ('tag', tag)):
        r = run('git', *a, cwd=dst)
        if r.returncode:
            raise RuntimeError(f"git {a[0]} in the release in today's words: {r.out}")
    return dst


def garden(rel, target, gardener='sam', *extra):
    """A garden of the core germinated at `target` from the release `rel`, kept by `gardener` (planted and saved)."""
    return run(PY, os.path.join(rel, 'seed', 'germinate.py'), target, '--gardener', gardener, *extra,
               cwd=os.path.dirname(target))
