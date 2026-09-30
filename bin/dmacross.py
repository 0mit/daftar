#!/usr/bin/env python3
"""dmacross — a reading across gardens: a value another garden holds, read at a commit it published and granted (24.0, N35).

    python3 bin/dmacross.py read <garden-bean> <bean>:<field path> [--commit <sha>]

A reading here may take an input whose origin is `garden` (`selection_form.inputs`): a value another garden holds —
a share of a candle two gardens burn, a reading of a series kept there. It is READ, never copied: the other garden's
repository is found through its `garden` bean here (a `located_at` position, `root:` resolved by this host's `roots`),
and the file is read at one commit with `git show`, which writes nothing in that repository or in this one. Between
gardens is exterior: this garden writes nothing into another, and what it reads it may read only because the other
garden said so.

A COMMIT IS READ ONLY WHEN IT IS
  HERE       the garden bean names a repository this host reaches, and it holds the commit (`NotHere`);
  PUBLISHED  reachable from what that garden publishes — the branch its repository has checked out, `HEAD` — so a
             commit it kept on a side branch, or never made, is not read (`NotPublished`);
  GRANTED    that garden, AT THAT COMMIT, grants `read` over the bean read to the person its own `garden` bean for THIS
             garden is owned by — this garden's gardener as that garden knows them (`dmpass.may`, the grant question,
             asked of the other garden's own beans at that commit) (`NotGranted`).

The act that fixes such a reading records `pin: {commit, at, garden}` (`pin_form`), so the reading can be read again.
"""
import os, subprocess, sys, tempfile, shutil, tarfile, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmpass


class NotHere(Exception):
    pass


class NotPublished(Exception):
    pass


class NotGranted(Exception):
    pass


def _git(repo, *a, binary=False):
    r = subprocess.run(['git', '-C', repo, *a], capture_output=True, timeout=30)
    if r.returncode != 0:
        return None
    return r.stdout if binary else r.stdout.decode('utf-8', 'replace')


def _bean(root, bid):
    try:
        head, _ = dmparse.read(os.path.join(root, 'beans', f"{bid}.md"))
    except OSError:
        return None
    return (dmparse.loads(head) or {}) if head is not None else None


def _anchor(fm, key):
    for a in ((fm.get('identity') or {}).get('anchors') or []) if isinstance(fm, dict) else []:
        if isinstance(a, dict) and a.get('key') == key:
            return str(a.get('value'))
    return None


def repository(garden, *, root=ROOT):
    """The path of the other garden's repository on this host, from its `garden` bean's `located_at`, or NotHere."""
    fm = _bean(root, garden)
    if not isinstance(fm, dict) or fm.get('genos') != 'garden':
        raise NotHere(f"'{garden}' is no `garden` bean here — a garden read from is one this garden records")
    import dmstale
    tried = []
    for loc in fm.get('located_at') or []:
        if isinstance(loc, dict) and loc.get('at'):
            p = dmstale.resolve_here(str(loc['at']))
            tried.append(str(loc['at']))
            if p and os.path.isdir(p) and _git(p, 'rev-parse', '--git-dir') is not None:
                return p
    raise NotHere(f"the garden '{garden}' is not reached from this host" +
                  (f" — tried {', '.join(tried)}; a `root:` position resolves through this host's `roots`" if tried else
                   " — its bean states no `located_at` position"))


def published(repo, commit):
    """The full commit, when it is reachable from what the garden publishes (its checked-out branch); else NotPublished."""
    full = _git(repo, 'rev-parse', '--verify', '--quiet', f"{commit}^{{commit}}")
    if not full:
        raise NotHere(f"the other garden holds no commit {commit}")
    full = full.strip()
    r = subprocess.run(['git', '-C', repo, 'merge-base', '--is-ancestor', full, 'HEAD'], capture_output=True, timeout=30)
    if r.returncode != 0:
        raise NotPublished(f"{full[:12]} is not reachable from what the other garden publishes (its checked-out branch): "
                           f"a commit it did not publish is not read")
    return full


def granted(repo, commit, bean, *, root=ROOT):
    """Why the other garden, at `commit`, grants `read` over `bean` to this garden's gardener as it knows them — or
    NotGranted. The grant question is asked of ITS beans at that commit, extracted read-only to a place of this run's."""
    here = dmparse.garden_id(root)
    tmp = tempfile.mkdtemp(prefix='dmacross-')
    try:
        data = _git(repo, 'archive', '--format=tar', commit, 'beans', 'GARDEN.md', binary=True)
        if data is None:
            raise NotHere(f"the other garden's beans cannot be read at {commit[:12]}")
        with tarfile.open(fileobj=io.BytesIO(data)) as t:
            t.extractall(tmp, filter='data')
        beans = dmpass.beans_here(tmp)
        me = [b for b, fm in beans.items() if fm.get('genos') == 'garden' and _anchor(fm, 'garden_id') == here]
        if not me:
            raise NotGranted(f"the other garden, at {commit[:12]}, records no garden with this garden's id ({here}): "
                             f"it has not met this one, so nothing of it is granted here")
        who = dmpass.owner_of(beans[me[0]])
        ans = dmpass.may(who, 'read', bean, root=tmp, beans=beans, gardener=dmpass.gardener_of(tmp))
        if not ans.granted:
            raise NotGranted(f"the other garden, at {commit[:12]}, does not grant `read` over '{bean}' to {who} "
                             f"(this garden's gardener as it knows them): {ans.why}")
        return ans.why
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def read(garden, commit, path, *, root=ROOT):
    """[values] at `path` (`<bean>:<field path>`) in the other garden at `commit` (None: what it publishes now) —
    published and granted, or NotHere / NotPublished / NotGranted. Returns (values, full commit) as `.values`/`.commit`
    on the list."""
    repo = repository(garden, root=root)
    full = published(repo, commit or 'HEAD')
    bean, _, fpath = str(path).partition(':')
    granted(repo, full, bean, root=root)
    text = _git(repo, 'show', f"{full}:beans/{bean}.md")
    if text is None:
        raise NotHere(f"the other garden holds no bean '{bean}' at {full[:12]}")
    head, _ = dmparse.split_front_matter(text.replace('\r\n', '\n'))
    fm = dmparse.loads(head) or {}
    import dmreckon
    try:
        vals = [v for v, _w in dmreckon.walk(None, fm, fpath, at=bean)] if fpath else [fm]
    except (AttributeError, dmreckon.Refused) as e:
        raise NotHere(f"`{fpath}` is read inside the one bean read; it follows no ref across gardens ({e})")
    out = _Read(vals)
    out.commit = full
    return out


class _Read(list):
    commit = None


def main(argv):
    if len(argv) < 3 or argv[0] != 'read':
        print(__doc__.strip().split('\n\n')[1])
        return 2
    commit = argv[argv.index('--commit') + 1] if '--commit' in argv else None
    try:
        vals = read(argv[1], commit, argv[2])
    except (NotHere, NotPublished, NotGranted) as e:
        print(f"dmacross: REFUSED ({type(e).__name__}) — {e}")
        return 1
    print(f"read at {vals.commit[:12]}, published and granted:")
    for v in vals:
        print(f"  {v!r}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
