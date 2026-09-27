#!/usr/bin/env python3
"""dmhub — the gate again, at the hub: who pushed, what they may change, and the garden as it would stand (24.0; N32).

    python3 bin/dmhub.py install <bare repository> [--only <person>] [--each]
    python3 bin/dmhub.py pre-receive [--only <person>] [--each]        # what the installed hook runs, reading stdin

A GARDEN WITH MORE THAN ONE WRITER HAS A HUB, a bare repository everyone pushes to, and the hub judges every push
again, commit by commit, oldest first:

  1. THE SIGNATURE. Every commit is signed. SSH: `ssh-keygen -Y check-novalidate -n git` on the commit's payload and
     its signature, and the SHA-256 fingerprint of the key the signature carries; OpenPGP: `gpg --verify`, its VALIDSIG
     fingerprint, the writers' public keys in the hub's keyring. An unsigned commit is refused.
  2. THE WRITER. The bean that carries that fingerprint as an anchor (`ssh_key_fingerprint`, `openpgp_fingerprint`) AS
     THE GARDEN STOOD AT THE PARENT COMMIT. A key no bean carries is refused. A key anchor added is itself a class-F
     change, so trust grows only through the gardener.
  3. THE RIGHTS, read at the parent: the gardener may do anything; any other writer needs `write` for every bean or
     mapping it changes (and for a bean's series files), `ratify:F` for an identity anchor it adds or changes, and
     `ratify:G` for a file in the `law` or `manifesto` layer — and for CODE: a file in the `gate` layer, one a release
     keeps (`seed/LANGUAGE`), any Python or shell file, the drawing module a page names (`view.drawings`) and the
     name itself (bin/dmpass.py `may`, and the layer map).
  4. THE GATE, in a checkout of the pushed tip — or of every commit, with `--each`.

THE HUB RUNS ONLY CODE THE GARDENER LET IN. The gate it runs is the one the pushed tree carries, because a garden's
gate reads the law beside it; so no push reaches step 4 until every commit in it has passed step 3, and step 3 lets
no writer but the gardener, or one granted `ratify:G`, change a line of code. A writer who could change `bin/` could
make the hub run anything, and pass anything. For the same reason a commit with no parent is taken only by an empty
hub, and only from the gardener its own tree names: a root commit read as its own parent would name its own writers.

`--only <person>` accepts pushes signed by the gardener and that one writer: the `view` host's own key (F5 (a)).
It writes nothing to the garden; a refusal names the commit, the writer and what was missing.
"""
import io, os, posixpath, re, shutil, subprocess, sys, tarfile, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse   # noqa: E402
import dmpass    # noqa: E402

HERE = os.path.abspath(__file__)
ZERO = '0' * 40
KEY_TERMS = ('ssh_key_fingerprint', 'openpgp_fingerprint')
CODE = ('.py', '.pyc', '.pyw', '.pyd', '.pyz', '.so', '.sh', '.bash', '.ps1', '.psm1', '.cmd', '.bat')   # what runs


class Refused(Exception):
    pass


def git(*a, cwd=None, env=None, text=True):
    r = subprocess.run(['git', *a], capture_output=True, cwd=cwd, env=env)
    out = r.stdout.decode('utf-8', 'replace') if text else r.stdout
    return r.returncode, out, r.stderr.decode('utf-8', 'replace')


def _fm(text):
    fm = dmparse.split_front_matter(text or '')[0]
    try:
        d = dmparse.loads(fm) if fm else None
    except Exception:
        return None
    return d if isinstance(d, dict) else None


def split_signature(raw):
    """(payload, signature) of a commit object: the payload is the object without its `gpgsig` header."""
    lines, payload, sig, i = raw.split(b'\n'), [], [], 0
    while i < len(lines):
        l = lines[i]
        if l.startswith(b'gpgsig ') or l.startswith(b'gpgsig-sha256 '):
            sig.append(l.split(b' ', 1)[1])
            i += 1
            while i < len(lines) and lines[i].startswith(b' '):
                sig.append(lines[i][1:])
                i += 1
            continue
        if l == b'':                      # the headers end: the message follows unchanged
            payload.extend(lines[i:])
            break
        payload.append(l)
        i += 1
    return b'\n'.join(payload), (b'\n'.join(sig) + b'\n') if sig else None


def fingerprint(payload, sig, tmp):
    """(kind, fingerprint) of the key that made a good signature over payload — or raises Refused."""
    ps, ss = os.path.join(tmp, 'payload'), os.path.join(tmp, 'sig')
    with open(ps, 'wb') as fh:
        fh.write(payload)
    with open(ss, 'wb') as fh:
        fh.write(sig)
    if sig.startswith(b'-----BEGIN SSH SIGNATURE-----'):
        if not shutil.which('ssh-keygen'):
            raise Refused("an SSH signature, and this hub has no ssh-keygen to check it")
        with open(ps, 'rb') as fh:
            r = subprocess.run(['ssh-keygen', '-Y', 'check-novalidate', '-n', 'git', '-s', ss], stdin=fh, capture_output=True)
        out = (r.stdout + r.stderr).decode('utf-8', 'replace')
        m = re.search(r'(SHA256:[A-Za-z0-9+/]{43})', out)
        if r.returncode != 0 or not m:
            raise Refused(f"its SSH signature does not verify ({out.strip()[:200]})")
        return 'ssh_key_fingerprint', m.group(1)
    if sig.startswith(b'-----BEGIN PGP SIGNATURE-----'):
        r = subprocess.run(['gpg', '--status-fd', '1', '--verify', ss, ps], capture_output=True)
        m = re.search(r'\[GNUPG:\] VALIDSIG ([0-9A-F]{40,64})', r.stdout.decode('utf-8', 'replace'))
        if not m:
            raise Refused("its OpenPGP signature does not verify with a key in the hub's keyring")
        return 'openpgp_fingerprint', m.group(1)
    raise Refused("it carries a signature of a kind this hub does not read")


class Tree:
    """A commit's files as the hub reads them: front matters by path, the gardener, and a checkout when asked."""

    def __init__(self, commit, env):
        self.commit, self.env = commit, env
        _c, out, _e = git('ls-tree', '-r', '--name-only', commit, env=env)
        self.files = [p for p in out.split('\n') if p]

    def text(self, path):
        c, out, _e = git('show', f'{self.commit}:{path}', env=self.env)
        return out if c == 0 else None

    def beans(self):
        out = {}
        for p in self.files:
            if p.startswith('beans/') and p.endswith('.md'):
                fm = _fm(self.text(p))
                if fm:
                    out[str(fm.get('bean') or p[6:-3])] = fm
        return out

    def gardener(self):
        g = _fm(self.text('GARDEN.md'))
        return g.get('gardener') if isinstance(g, dict) else None

    def checkout(self, where):
        """The commit's files under `where`: `git archive`, read here, with no shell between — a link or a name that
        would land outside `where` is refused, not followed."""
        r = subprocess.run(['git', 'archive', '--format=tar', self.commit], capture_output=True, env=self.env)
        if r.returncode != 0:
            raise Refused(f"the hub could not check out {self.commit[:10]}: {r.stderr.decode('utf-8', 'replace')[:200]}")
        with tarfile.open(fileobj=io.BytesIO(r.stdout), mode='r:') as tar:
            try:
                if hasattr(tarfile, 'data_filter'):
                    tar.extractall(where, filter='data')
                else:
                    base = os.path.realpath(where)
                    for m in tar.getmembers():
                        dest = os.path.realpath(os.path.join(base, m.name))
                        if m.issym() or m.islnk() or os.path.commonpath([base, dest]) != base:
                            raise tarfile.TarError(f"{m.name} would land outside the checkout")
                    tar.extractall(where)
            except (tarfile.TarError, OSError) as x:
                raise Refused(f"the hub could not check out {self.commit[:10]}: {x}")


def writer_of(kind, fpr, beans):
    for bid, fm in sorted(beans.items()):
        for a in ((fm.get('identity') or {}).get('anchors') or []) if isinstance(fm.get('identity'), dict) else []:
            if isinstance(a, dict) and a.get('key') == kind and str(a.get('value')) == fpr:
                return bid
    return None


def _anchors(fm):
    a = ((fm or {}).get('identity') or {}).get('anchors') if isinstance((fm or {}).get('identity'), dict) else None
    return sorted(repr(x) for x in a or [])


def _drawn(fm):
    """The file a page names as its drawing module (`view.drawings: file:<path>`), normalised, or None."""
    v = (fm or {}).get('view')
    d = v.get('drawings') if isinstance(v, dict) else None
    return posixpath.normpath(d[5:]) if isinstance(d, str) and d.startswith('file:') else None


def is_code(m, path, drawn=()):
    """True for a file whose change can make a machine run something: what the `gate` layer holds, what a release keeps,
    a Python or shell file wherever it is, and a drawing module a page names. Only the gardener, or a writer granted
    `ratify:G`, changes one at the hub."""
    return (m.layer_of(path)[0] == 'gate' or m.keeper_of(path) == 'release' or path.lower().endswith(CODE)
            or path in drawn)


def rights(writer, commit, parent, env, tmp):
    """What the writer changed that its grants at the parent do not open: [(path, act)]."""
    before = Tree(parent, env) if parent else None
    if before is None or writer == before.gardener():
        return []
    root = os.path.join(tmp, 'parent')
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root)
    before.checkout(root)
    beans = before.beans()
    _c, out, _e = git('diff', '--name-only', '--no-renames', parent, commit, env=env)
    after = Tree(commit, env)
    m = dmpass.Map.here(root)
    drawn = {d for fm in list(beans.values()) + list(after.beans().values()) for d in [_drawn(fm)] if d}
    missing = []

    def ratify_g():
        return dmpass.may(writer, 'ratify:G', before.gardener() or '', root=root, beans=beans).granted

    for p in [x for x in out.split('\n') if x]:
        if m.layer_of(p)[0] in dmpass.RULED or is_code(m, p, drawn):
            if not ratify_g():
                missing.append((p, 'ratify:G'))
            continue
        if p.startswith(('beans/', 'mappings/')) and p.endswith('.md'):
            bid = p.split('/', 1)[1][:-3]
            was, now = _fm(before.text(p)), _fm(after.text(p))
            if not dmpass.may(writer, 'write', bid, root=root, beans=beans).granted:
                missing.append((p, 'write'))
            if _anchors(was) != _anchors(now) and \
                    not dmpass.may(writer, 'ratify:F', bid, root=root, beans=beans).granted:
                missing.append((p, 'ratify:F'))
            if _drawn(was) != _drawn(now) and not ratify_g():
                missing.append((p, 'ratify:G'))
        elif p.startswith('series/') and p.count('/') >= 2:
            bid = p.split('/')[1]
            if not dmpass.may(writer, 'write', bid, root=root, beans=beans).granted:
                missing.append((p, 'write'))
    return missing


def gate(commit, env, tmp):
    """The gate, run in a checkout of `commit`: a fresh repository that borrows the hub's objects — the pushed ones
    still in quarantine among them — so no ref of the hub is touched while the push is judged."""
    where = os.path.join(tmp, 'tip-' + commit[:10])
    objs = [os.path.abspath(env.get('GIT_OBJECT_DIRECTORY') or os.path.join(env.get('GIT_DIR') or '.', 'objects'))]
    objs += [os.path.abspath(p) for p in (env.get('GIT_ALTERNATE_OBJECT_DIRECTORIES') or '').split(os.pathsep) if p]
    objs.append(os.path.abspath(os.path.join(env.get('GIT_DIR') or '.', 'objects')))
    _e = {k: v for k, v in env.items() if not k.startswith(('GIT_DIR', 'GIT_QUARANTINE', 'GIT_OBJECT_DIRECTORY',
                                                            'GIT_ALTERNATE', 'GIT_WORK_TREE', 'GIT_INDEX'))}
    _e['GIT_ALTERNATE_OBJECT_DIRECTORIES'] = os.pathsep.join(dict.fromkeys(objs))
    for step in (('init', '-q', where), ('-C', where, 'update-ref', 'refs/heads/judged', commit),
                 ('-C', where, 'symbolic-ref', 'HEAD', 'refs/heads/judged'), ('-C', where, 'reset', '-q', '--hard')):
        c, _o, err = git(*step, env=_e)
        if c != 0:
            raise Refused(f"the hub could not check out {commit[:10]}: {err.strip()[:200]}")
    r = subprocess.run([sys.executable, os.path.join(where, 'bin', 'dmcheck.py'), '--all'], capture_output=True,
                       cwd=where, env=_e)
    out = (r.stdout + r.stderr).decode('utf-8', 'replace')
    if r.returncode != 0 or ' 0 error(s)' not in out:
        raise Refused("the garden it leaves does not pass the gate:\n" + out.strip()[-1500:])


def judge(old, new, only=None, each=False, env=None):
    """[str]: every refusal for one ref update; empty when the push is accepted."""
    env = env or dict(os.environ)
    if new == ZERO:
        return []
    _c, out, _e = git('rev-list', '--reverse', new, '--not', '--all', env=env)
    commits = [c for c in out.split('\n') if c]
    found = []
    with tempfile.TemporaryDirectory(prefix='dmhub-') as tmp:
        for c in commits:
            _r, raw, _e = git('cat-file', 'commit', c, env=env, text=False)
            payload, sig = split_signature(raw)
            _r, parents, _e = git('rev-list', '--parents', '-n', '1', c, env=env)
            parent = (parents.split() + [None, None])[1]
            try:
                if sig is None:
                    raise Refused("it is not signed: a hub accepts a commit signed by a key a writer's bean carries")
                kind, fpr = fingerprint(payload, sig, tmp)
                if parent is None:
                    _r, refs, _e = git('for-each-ref', '--format=%(refname)', env=env)
                    if refs.strip():
                        raise Refused("it has no parent, and this hub already holds the garden: a garden has one root, "
                                      "and a commit with none would be judged by writers its own tree names")
                at = Tree(parent or c, env)
                beans, gardener = at.beans(), at.gardener()
                who = writer_of(kind, fpr, beans)
                if parent is None and who != gardener:
                    raise Refused(f"it has no parent: an empty hub takes a garden's first commit only from the gardener "
                                  f"its tree names ({gardener})")
                if who is None:
                    raise Refused(f"it is signed by {fpr}, which no bean carries as an anchor as the garden stood before "
                                  f"it — the gardener adds a writer's key (a class-F change)")
                if only and who not in (only, gardener):
                    raise Refused(f"it is signed by {who}, and this hub accepts only {gardener} and {only}")
                miss = rights(who, c, parent, env, tmp)
                if miss:
                    raise Refused(f"{who} may not make it: " + '; '.join(f"{p} needs a grant of `{a}`" for p, a in miss))
                if each:
                    gate(c, env, tmp)
            except Refused as x:
                found.append(f"{c[:10]}: {x}")
                break
        if not found and commits and not each:
            try:
                gate(new, env, tmp)
            except Refused as x:
                found.append(f"{new[:10]}: {x}")
    return found


def install(bare, only=None, each=False):
    hook = os.path.join(bare, 'hooks', 'pre-receive')
    os.makedirs(os.path.dirname(hook), exist_ok=True)
    args = ' '.join(filter(None, [f"--only '{only}'" if only else '', '--each' if each else '']))
    with open(hook, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(f"#!/bin/sh\n# written by bin/dmhub.py install: the gate again, at the hub (N32)\n"
                 f"exec '{sys.executable}' '{HERE}' pre-receive {args}\n")
    os.chmod(hook, 0o755)
    return hook


def main(argv):
    argv = list(argv)
    only = argv[argv.index('--only') + 1] if '--only' in argv else None
    each = '--each' in argv
    if argv[:1] == ['install'] and len(argv) >= 2:
        print(f"dmhub: installed {install(os.path.abspath(argv[1]), only, each)}")
        return 0
    if argv[:1] == ['pre-receive']:
        refused = []
        for line in sys.stdin.read().split('\n'):
            parts = line.split()
            if len(parts) == 3:
                refused += [f"{parts[2]} {r}" for r in judge(parts[0], parts[1], only, each)]
        for r in refused:
            print(f"dmhub: REFUSED {r}", file=sys.stderr)
        return 1 if refused else 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
