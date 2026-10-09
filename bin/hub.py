#!/usr/bin/env python3
"""hub — the gate again, at the hub: who pushed, what they may change, and the garden as it would stand (24.0; N32).

    python3 bin/hub.py install <bare repository> [--only <person>] [--each]
    python3 bin/hub.py pre-receive [--only <person>] [--each]        # what the installed hook runs, reading stdin
    python3 bin/hub.py receive <ref> [--each]                         # a peer judges what a fetch brought, as a hub

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
     name itself (bin/pass.py `may`, and the layer map).
  4. THE GATE, in a checkout of the pushed tip — or of every commit, with `--each`.

THE HUB RUNS ONLY CODE THE GARDENER LET IN. The gate it runs is the one the pushed tree carries, because a garden's
gate reads the law beside it; so no push reaches step 4 until every commit in it has passed step 3, and step 3 lets
no writer but the gardener, or one granted `ratify:G`, change a line of code. A writer who could change `bin/` could
make the hub run anything, and pass anything. For the same reason a commit with no parent is taken only by an empty
hub, and only from the gardener its own tree names: a root commit read as its own parent would name its own writers.

EVERY PEER JUDGES WHAT IT RECEIVES (design §7.1): `receive <ref>` judges what a fetch brought into <ref> — a quarantine
ref, never a branch — by the same four steps, every commit it holds that this clone's own branches do not, before
anything is merged; nothing fetched is counted as judged (a remote-tracking ref holds another's word, not this
clone's). Exit 0 and `taken` where every commit passes; the refusals otherwise, and nothing is merged.

`--only <person>` accepts pushes signed by the gardener and that one writer: the `view` host's own key (F5 (a)).
It writes nothing to the garden; a refusal names the commit, the writer and what was missing.

A PERSON'S LABELS (Y8) are their own words for the handplace's interface, on `refs/daftar/custom/<person>` beside the
garden's branch. The hub takes a commit there when it is signed by a key that person's bean carries (as the garden
stands at the hub's HEAD) and its tree holds only their customisation files (`labels.json`, a JSON object of theirs);
the ref moves only on top of what it was and is never deleted. Every commit it gains is judged, not only those new to
the hub; no gate runs, since nothing there is the garden's; and a garden's branch never counts such a commit as judged.

A GARDEN OF THE CORE (v1 part 10) is read at each commit by the law that commit's GARDEN.md pins, so the push that adopts
the core is judged as the garden stood before it, and the next by the core. There the writer is the bean whose `name`
the key's namespace gives (`name: { by: ssh, of: self, as: "SHA256:…" }`, or `openpgp`); class F is a change to a name
that establishes an identity (a namespace that gives a name once); the rights are `grant` statements (bin/pass.py
`may`); and the gate is `bin/check.py --all`, the gate of the law the pushed tree pins. (`bin/hub.py`, today's name,
runs this too until v1's part 13.)
"""
import io, json, os, posixpath, re, shutil, subprocess, sys, tarfile, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # the core beside it
import parse as dmparse   # noqa: E402 — bin/parse.py
import importlib
dmpass = importlib.import_module('pass')    # noqa: E402 — bin/pass.py (`pass` is a keyword of Python)

HERE = os.path.abspath(__file__)
ZERO = '0' * 40
KEY_TERMS = ('ssh_key_fingerprint', 'openpgp_fingerprint')
KEY_NAMESPACES = {'ssh_key_fingerprint': 'ssh', 'openpgp_fingerprint': 'openpgp'}   # the core's namespace of each key
CODE = ('.py', '.pyc', '.pyw', '.pyd', '.pyz', '.so', '.sh', '.bash', '.ps1', '.psm1', '.cmd', '.bat')   # what runs
# A PERSON'S CUSTOMISATIONS of the handplace (Y8): their own words for its interface, on a ref of their own beside the
# garden's branch, never in its tree — so they are never checked out, never judged as the garden, never merged into it.
CUSTOM_REF = re.compile(r'^refs/daftar/custom/([a-z0-9][a-z0-9-]{0,63})$')
CUSTOM_FILES = ('labels.json',)        # what such a ref's tree may hold: daftard's labels (internal/custom)


class Refused(Exception):
    pass


def git(*a, cwd=None, env=None, text=True):
    r = subprocess.run(['git', *a], capture_output=True, cwd=cwd, env=env)
    out = r.stdout.decode('utf-8', 'replace') if text else r.stdout
    return r.returncode, out, r.stderr.decode('utf-8', 'replace')


def _fm(text, core=False):
    """A document's front matter, read as the law it stands under reads it: the core's every value as written."""
    fm = dmparse.split_front_matter(text or '')[0]
    try:
        if core:
            from core import read
            d = read.loads(fm) if fm else None
        else:
            d = dmparse.loads(fm) if fm else None
    except Exception:
        return None
    return d if isinstance(d, dict) else None


def _statements(fm):
    return [next(iter(x.items())) for x in (fm or {}).get('statements') or [] if isinstance(x, dict) and len(x) == 1
            and isinstance(next(iter(x.values())), dict)]


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
        g = _fm(self.text('GARDEN.md')) if 'GARDEN.md' in self.files else None
        self.core = isinstance(g, dict) and str(g.get('extends') or '').startswith('core@')   # the law this commit pins

    def text(self, path):
        c, out, _e = git('show', f'{self.commit}:{path}', env=self.env)
        return out if c == 0 else None

    def beans(self):
        out = {}
        for p in self.files:
            if p.startswith('beans/') and p.endswith('.md'):
                fm = _fm(self.text(p), self.core)
                if fm:
                    out[str(fm.get('bean') or p[6:-3])] = fm
        return out

    def gardener(self):
        g = _fm(self.text('GARDEN.md'), self.core)
        return g.get('gardener') if isinstance(g, dict) else None

    def once(self):
        """The namespaces this commit's law gives a name in once — a name there establishes an identity (class F)."""
        if not self.core:
            return set()
        text = self.text('core/law/namespaces.yaml')
        if text is None:
            with open(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'core', 'law', 'namespaces.yaml'),
                      encoding='utf-8') as fh:
                text = fh.read()
        from core import read
        return {str(r.get('namespace')) for r in (read.loads(text) or {}).get('namespaces') or []
                if isinstance(r, dict) and r.get('once') == 'true'}

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
    """The bean that carries the key: today, as an identity anchor; in a garden of the core, a `name` the key's
    namespace gives it."""
    for bid, fm in sorted(beans.items()):
        for v, r in _statements(fm):
            if v == 'name' and 'held' not in r and r.get('by') == KEY_NAMESPACES[kind] and str(r.get('as')) == fpr \
                    and r.get('of') in (None, 'self', bid):
                return bid
        for a in ((fm.get('identity') or {}).get('anchors') or []) if isinstance(fm.get('identity'), dict) else []:
            if isinstance(a, dict) and a.get('key') == kind and str(a.get('value')) == fpr:
                return bid
    return None


def _anchors(fm, once=()):
    """What establishes the bean's identity, to compare: today's anchors; in a garden of the core, each name a
    namespace gives once (`once`), sealed or not."""
    a = ((fm or {}).get('identity') or {}).get('anchors') if isinstance((fm or {}).get('identity'), dict) else None
    names = [repr(sorted(r.items())) for v, r in _statements(fm) if v == 'name' and r.get('by') in once]
    return sorted([repr(x) for x in a or []] + names)


def _drawn(fm):
    """The file a page names as its drawing module (`view.drawings: file:<path>`), normalised, or None."""
    v = (fm or {}).get('view')
    if not isinstance(v, dict) and isinstance((fm or {}).get('details'), dict):
        v = fm['details'].get('view')                 # a garden of the core keeps a page's view in `details`
    d = v.get('drawings') if isinstance(v, dict) else None
    return posixpath.normpath(d[5:]) if isinstance(d, str) and d.startswith('file:') else None


def is_code(m, path, drawn=()):
    """True for a file whose change can make a machine run something: what the `gate` layer holds, what a release keeps,
    a Python or shell file wherever it is, and a drawing module a page names. Only the gardener, or a writer granted
    `ratify:G`, changes one at the hub."""
    return (m.layer_of(path)[0] == 'gate' or m.keeper_of(path) == 'release' or path.lower().endswith(CODE)
            or path in drawn)


def rights(writer, commit, parent, env, tmp, others=()):
    """What the writer changed that its grants at the parent do not open: [(path, act)]. A MERGE (`others`, its other
    parents) brings what each side committed, judged when it was committed: what the merge itself changed — and its
    writer needs grants for — is a path that differs from every parent (MERGE.md §5, as the gate reads a merge)."""
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
    paths = [x for x in out.split('\n') if x]
    if others:
        def blob(ref, p):
            return git('rev-parse', '-q', '--verify', f"{ref}:{p}", env=env)[1].strip()
        paths = [p for p in paths if all(blob(o, p) != blob(commit, p) for o in others)]
    after = Tree(commit, env)
    once = before.once() | after.once()
    m = dmpass.Map.here(root)
    drawn = {d for fm in list(beans.values()) + list(after.beans().values()) for d in [_drawn(fm)] if d}
    missing = []

    def ratify_g():
        return dmpass.may(writer, 'ratify:G', before.gardener() or '', root=root, beans=beans).granted

    for p in paths:
        if m.layer_of(p)[0] in dmpass.RULED or is_code(m, p, drawn):
            if not ratify_g():
                missing.append((p, 'ratify:G'))
            continue
        if p.startswith(('beans/', 'mappings/')) and p.endswith('.md'):
            bid = p.split('/', 1)[1][:-3]
            was, now = _fm(before.text(p), before.core), _fm(after.text(p), after.core)
            if not dmpass.may(writer, 'write', bid, root=root, beans=beans).granted:
                missing.append((p, 'write'))
            if _anchors(was, once) != _anchors(now, once) and \
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
    c, own, _e = git('rev-parse', '--git-path', 'objects', env=env)   # a working clone's are under .git/ (`receive`)
    if c == 0 and own.strip():
        objs.append(os.path.abspath(own.strip()))
    _e = {k: v for k, v in env.items() if not k.startswith(('GIT_DIR', 'GIT_QUARANTINE', 'GIT_OBJECT_DIRECTORY',
                                                            'GIT_ALTERNATE', 'GIT_WORK_TREE', 'GIT_INDEX'))}
    _e['GIT_ALTERNATE_OBJECT_DIRECTORIES'] = os.pathsep.join(dict.fromkeys(objs))
    for step in (('init', '-q', where), ('-C', where, 'update-ref', 'refs/heads/judged', commit),
                 ('-C', where, 'symbolic-ref', 'HEAD', 'refs/heads/judged'), ('-C', where, 'reset', '-q', '--hard')):
        c, _o, err = git(*step, env=_e)
        if c != 0:
            raise Refused(f"the hub could not check out {commit[:10]}: {err.strip()[:200]}")
    gate = next((g for g in ('check.py', 'dmcheck.py') if os.path.isfile(os.path.join(where, 'bin', g))), 'dmcheck.py')   # a commit of a garden in today's words is judged by its own gate
    r = subprocess.run([sys.executable, os.path.join(where, 'bin', gate), '--all'], capture_output=True,
                       cwd=where, env=_e)
    out = (r.stdout + r.stderr).decode('utf-8', 'replace')
    if r.returncode != 0 or ' 0 error(s)' not in out:
        raise Refused("the garden it leaves does not pass the gate:\n" + out.strip()[-1500:])


def judge(old, new, only=None, each=False, env=None, known=('--all',)):
    """[str]: every refusal for one ref update; empty when the push is accepted. `known` is what counts as judged
    already: everything a hub holds; a peer's own branches alone (`receive`)."""
    env = env or dict(os.environ)
    if new == ZERO:
        return []
    # the commits no garden ref holds yet: a person's labels ref holds commits never judged as the garden, so a commit
    # it holds is judged again before a garden's branch may hold it
    _c, out, _e = git('rev-list', '--reverse', new, '--not', '--exclude=refs/daftar/custom/*', '--all', env=env)
    _c, out, _e = git('rev-list', '--reverse', new, '--not', *known, env=env)
    commits = [c for c in out.split('\n') if c]
    found = []
    with tempfile.TemporaryDirectory(prefix='hub-') as tmp:
        for c in commits:
            _r, raw, _e = git('cat-file', 'commit', c, env=env, text=False)
            payload, sig = split_signature(raw)
            _r, parents, _e = git('rev-list', '--parents', '-n', '1', c, env=env)
            parent = (parents.split() + [None, None])[1]
            others = parents.split()[2:]                     # a merge's other parents
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
                miss = rights(who, c, parent, env, tmp, others)
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


def judge_custom(person, old, new, env=None):
    """[str]: every refusal for an update of `refs/daftar/custom/<person>`; empty when it is taken. Each new commit is
    signed by a key the person's bean carries, as the garden stands at the hub now (its HEAD), and its tree holds only
    their customisation files, each a JSON object of theirs; the ref only moves on top of what it was, and is never
    deleted. No gate runs: nothing on it is the garden's."""
    env = env or dict(os.environ)
    if new == ZERO:
        return ["a person's customisations are never deleted at the hub: a word set back to the page's own is kept, and "
                "the ref's history keeps what each was"]
    if old != ZERO and git('merge-base', '--is-ancestor', old, new, env=env)[0] != 0:
        return [f"{new[:10]}: it is not on top of what the ref held ({old[:10]}): a person's labels move on, merged word "
                f"by word, and their history keeps every word"]
    c, tip, _e = git('rev-parse', '--verify', '-q', 'HEAD^{commit}', env=env)
    if c != 0 or not tip.strip():
        return [f"{new[:10]}: this hub holds no garden yet, so no bean carries {person}'s key"]
    beans = Tree(tip.strip(), env).beans()
    # EVERY COMMIT THE REF GAINS, not only those new to the hub: a chain already on another person's ref, pushed onto
    # this one, is judged again — by this person's key
    _c, out, _e = git('rev-list', '--reverse', new, *(['--not', old] if old != ZERO else []), env=env)
    found = []
    with tempfile.TemporaryDirectory(prefix='hub-') as tmp:
        for c in [x for x in out.split('\n') if x]:
            _r, raw, _e = git('cat-file', 'commit', c, env=env, text=False)
            payload, sig = split_signature(raw)
            try:
                if sig is None:
                    raise Refused("it is not signed: a person's labels are signed by a key their bean carries")
                kind, fpr = fingerprint(payload, sig, tmp)
                who = writer_of(kind, fpr, beans)
                if who != person:
                    raise Refused(f"it is signed by {who or fpr}, and {person}'s customisations are signed by "
                                  f"{person}'s own key")
                _r, files, _e = git('ls-tree', '-r', '--name-only', c, env=env)
                stray = [f for f in files.split('\n') if f and f not in CUSTOM_FILES]
                if stray:
                    raise Refused(f"its tree holds {', '.join(stray[:5])}: a labels ref holds only "
                                  f"{', '.join(CUSTOM_FILES)}")
                for f in [f for f in files.split('\n') if f]:
                    _r, body, _e = git('show', f'{c}:{f}', env=env)
                    try:
                        doc = json.loads(body)
                    except ValueError:
                        doc = None
                    if not isinstance(doc, dict) or doc.get('person') not in (None, person):
                        raise Refused(f"{f} is no JSON object of {person}'s customisations")
            except Refused as x:
                found.append(f"{c[:10]}: {x}")
                break
    return found
def receive(ref, each=False, env=None):
    """[str]: every refusal for what a fetch brought into `ref`, judged as a hub judges a push: the commits it holds that
    this clone's own branches do not."""
    env = env or dict(os.environ)
    c, sha, _e = git('rev-parse', '--verify', '-q', ref + '^{commit}', env=env)
    if c != 0 or not sha.strip():
        return [f"{ref} names no commit"]
    return judge(ZERO, sha.strip(), None, each, env, known=('--branches',))


def install(bare, only=None, each=False):
    hook = os.path.join(bare, 'hooks', 'pre-receive')
    os.makedirs(os.path.dirname(hook), exist_ok=True)
    args = ' '.join(filter(None, [f"--only '{only}'" if only else '', '--each' if each else '']))
    with open(hook, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(f"#!/bin/sh\n# written by bin/hub.py install: the gate again, at the hub (N32)\n"
                 f"exec '{sys.executable}' '{HERE}' pre-receive {args}\n")
    os.chmod(hook, 0o755)
    return hook


def main(argv):
    argv = list(argv)
    only = argv[argv.index('--only') + 1] if '--only' in argv else None
    each = '--each' in argv
    if argv[:1] == ['install'] and len(argv) >= 2:
        print(f"hub: installed {install(os.path.abspath(argv[1]), only, each)}")
        return 0
    if argv[:1] == ['receive'] and len(argv) >= 2:
        refused = receive(argv[1], each)
        for r in refused:
            print(f"hub: REFUSED {argv[1]} {r}", file=sys.stderr)
        if not refused:
            print(f"hub: {argv[1]}: taken — every commit it brings is signed by a writer, within their rights, and the "
                  f"garden passes its gate")
        return 1 if refused else 0
    if argv[:1] == ['pre-receive']:
        refused = []
        for line in sys.stdin.read().split('\n'):
            parts = line.split()
            if len(parts) == 3:
                m = CUSTOM_REF.match(parts[2])
                refused += [f"{parts[2]} {r}" for r in (judge_custom(m.group(1), parts[0], parts[1]) if m else
                                                        judge(parts[0], parts[1], only, each))]
        for r in refused:
            print(f"hub: REFUSED {r}", file=sys.stderr)
        return 1 if refused else 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
