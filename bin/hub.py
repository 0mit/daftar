#!/usr/bin/env python3
"""hub — the gate again, at the hub: who pushed, what they may change, and the garden as it would stand (24.0; N32).

    python3 bin/hub.py install <repository> [--report] [--only <person>] [--each]   # the hub's init: hooks, own key
    python3 bin/hub.py key <repository>                               # the hub's key, shown again
    python3 bin/hub.py pre-receive [--report] [--only <person>] [--each]   # what the installed hook runs, reading stdin
    python3 bin/hub.py post-receive                                   # after a push is taken: each commit's receipt
    python3 bin/hub.py report <repository> [--since <moment>]         # what the hub judged, from its log
    python3 bin/hub.py receipts <repository> [<rev>]                  # each commit's receipt, and those with none
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
     name itself, and a captured view of another program (`captures/views/`), whose templates its client compiles into
     script (bin/pass.py `may`, and the layer map).
  4. THE GATE, in a checkout of the pushed tip — or of every commit, with `--each`; and every commit's OWN RULES,
     replayed against its parent by the code it carries (core 3.5, II.3: the one judge's scope `replay`), all but the
     clock's register of headings, a clone's — so a hub refuses what a commit's hook refused, and a commit made past
     its hook is judged here all the same.

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

A HUB FIRST REPORTS, then refuses (the next version's design, P3). Installed with `--report`, it judges every push as it
would — the four steps, every commit, past the first refusal — and refuses nothing of the garden's: the push is taken,
the writer is shown what it would refuse, and the log keeps it. It still runs no gate once a commit has failed steps
1-3, since the gate is the pushed tree's own code. What it took that it would refuse is then the garden's, and a later
push is judged by the garden as it stands, that included; so a window of reporting is read with `report`, and the hub
installed again without `--report` refuses. In either mode:
  - THE LOG: each ref update judged, one line of JSON in the hub's `daftar/hub.log` (beside its refs, in its git
    directory) — when, the mode, the ref, each commit with its writer, key and refusal, the gate, the verdict (taken,
    would refuse, refused). `report` counts it, and lists what was not simply taken.
  - THE RECEIPTS: for each commit a push that lands brought, its post-receive writes a note on refs/notes/daftar: the
    commit, the verdict and why, the writer and its key, what was judged and what not (the Contract's classes C, D, E
    and J are not judged at the hub), the gate that judged the garden it leaves, the law it was judged by (its pin and
    the SHA-256 of core/law/, VOCAB.md and GARDEN.md at the commit), the judge (this code's release and commit), the
    mode and the moment — signed by the hub's own key in the namespace `daftar-receipt`, so no commit's signature is
    one. `receipts` lists each commit with its receipt and whose key signed it, and each commit with none, which no door
    of this hub judged. The receipts' ref is the hub's alone: a push to it is refused in either mode.

A HUB HAS ITS OWN KEY, made when it is initialized for a garden (the operator's word, 2026-10-13: every commit the hub
itself writes — a merge with no conflict, its own records — is signed with it). `install <repository>` is that init:
on a bare repository it writes the hook (left as it is where it is that hook already); on a working copy — the hub
daftard keeps in step, which judges what it fetches (`receive`) — it writes none, since nothing is pushed into a
working copy and a hook there would be a file of the garden's tree. Either way it makes the hub's key where this
account has none for the garden: ed25519, with no passphrase, since nobody sits to give one, in this account's daftar
state folder — daftard's own: DAFTARD_STATE where it is set, %LOCALAPPDATA%\\Daftar on Windows, $XDG_STATE_HOME/daftar
(~/.local/state/daftar) elsewhere — under `hubs/<garden id>/key`, the folder 0700 and the key 0600: outside every
working copy and repository, so no copy, backup or synchronised folder of the garden carries it. One account on one
machine is one hub of a garden, however many repositories of it it keeps. It is made once and never over: a new key is
a new identity, the gardener's (class F). It prints the fingerprint, the public line and the statement the gardener
adds to the hub's bean (`name: { by: ssh, of: self, as: "SHA256:…" }`), and never the private key; `key` prints them
again. The key waits for the garden's first commit in an empty repository (it is the garden's id that names it), and
root makes none for a repository another account owns: the key is that account's, made by its own `install`. A hub's
commits are judged as any writer's are: by the bean its key names, within that bean's grants.

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
import check as dmcheck   # noqa: E402 — bin/check.py, the one reader of a garden's pin
import install as dminstall   # noqa: E402 — bin/install.py: the state folder, and the one maker of a key kept there
import importlib
dmpass = importlib.import_module('pass')    # noqa: E402 — bin/pass.py (`pass` is a keyword of Python)

HERE = os.path.abspath(__file__)
ROOT = os.path.dirname(os.path.dirname(HERE))
ZERO = '0' * 40
KEY_TERMS = ('ssh_key_fingerprint', 'openpgp_fingerprint')
KEY_NAMESPACES = {'ssh_key_fingerprint': 'ssh', 'openpgp_fingerprint': 'openpgp'}   # the core's namespace of each key
CODE = ('.py', '.pyc', '.pyw', '.pyd', '.pyz', '.so', '.sh', '.bash', '.ps1', '.psm1', '.cmd', '.bat')   # what runs
# what runs though it is kept as history: a captured view of another program, whose client compiles its templates into
# script where it runs (Odoo's Owl: an expression in a kanban card is JavaScript) — security audit 2026-10-10, 2.1
CODE_FOLDERS = ('captures/views/',)
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
        manifest = self.text('GARDEN.md') if 'GARDEN.md' in self.files else ''
        self.core = dmcheck.pin_of(manifest).startswith('core@')   # the law this commit pins

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
    a Python or shell file wherever it is, a drawing module a page names, and a captured view another program's client
    compiles into script. Only the gardener, or a writer granted `ratify:G`, changes one at the hub."""
    return (m.layer_of(path)[0] == 'gate' or m.keeper_of(path) == 'release' or path.lower().endswith(CODE)
            or path in drawn or path.startswith(CODE_FOLDERS))


def _decided(merged, base, sides):
    """Whether a merge decided `merged` itself, for a value merged three ways as MERGE.md §3 merges a statement: a
    member of the base stays only where no side took it out, and one a side added is kept. `merged` and each side are
    sets; anything else (one value: a page's drawing module) is what the side that changed it from the base holds, or
    the base's where none did — and where two sides changed it apart, any value is the merge's own."""
    if isinstance(merged, (set, frozenset)):
        want = {x for x in set().union(*sides) | base if (all(x in s for s in sides) if x in base else True)}
        return merged != want
    moved = {s for s in sides if s != base}
    return len(moved) > 1 or merged != (moved.pop() if moved else base)


def rights(writer, commit, parent, env, tmp, others=()):
    """What the writer changed that its grants at the parent do not open: [(path, act)]. A MERGE (`others`, its other
    parents) brings what each side committed, judged when it was committed: what the merge itself changed — and its
    writer needs grants for — is a path that differs from every parent (MERGE.md §5, as the gate reads a merge). And
    within such a path, an identity anchor or a page's drawing module is the merge's own only where it is not what the
    merge of its parents makes of it (MERGE.md §3): an anchor one side added is the side's, judged then, whichever parent
    is first; one a side took out and the merge keeps, the merge decided."""
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
    # A MERGE OF TWO is read against its base, each side as it committed it; any other merge, against its first parent
    base = git('merge-base', parent, others[0], env=env)[1].strip() if len(others) == 1 else ''
    sides = [Tree(c, env) for c in [parent, *others]] if len(others) == 1 else []
    under = Tree(base, env) if base else None

    def ratify_g():
        return dmpass.may(writer, 'ratify:G', before.gardener() or '', root=root, beans=beans).granted

    def side(t, p):
        return _fm(t.text(p), t.core) if t is not None else None

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
            if sides:
                ours = [side(t, p) for t in sides]
                anchored = _decided(set(_anchors(now, once)), set(_anchors(side(under, p), once)),
                                    [set(_anchors(fm, once)) for fm in ours])
                redrawn = _decided(_drawn(now), _drawn(side(under, p)), [_drawn(fm) for fm in ours])
            else:
                anchored, redrawn = _anchors(was, once) != _anchors(now, once), _drawn(was) != _drawn(now)
            if anchored and not dmpass.may(writer, 'ratify:F', bid, root=root, beans=beans).granted:
                missing.append((p, 'ratify:F'))
            if redrawn and not ratify_g():
                missing.append((p, 'ratify:G'))
        elif p.startswith('series/') and p.count('/') >= 2:
            bid = p.split('/')[1]
            if not dmpass.may(writer, 'write', bid, root=root, beans=beans).granted:
                missing.append((p, 'write'))
    return missing


def gate(commit, env, tmp):
    """The gate on `commit`: the one judge's scope `commits` (core/judge.py) — the commit checked out in a fresh
    repository that borrows the hub's objects, the pushed ones still in quarantine among them, so no ref of the hub is
    touched, and judged there by the gate it carries."""
    sys.path.insert(0, ROOT)
    from core import judge as dmjudge
    scope = dmjudge.Scope.commits([commit], env)
    if dmjudge.judge(None, scope):
        said = scope.said.get(commit, '')
        if said.startswith('could not check out'):
            raise Refused(f"the hub {said}")
        raise Refused("the garden it leaves does not pass the gate:\n" + said.strip()[-1500:])


def replay(commit, env, v=None):
    """THE COMMIT'S OWN RULES, REPLAYED AGAINST ITS PARENT (core 3.5, II.3): the one judge's scope `replay` — the
    commit checked out with its parent as HEAD and its tree as the index, and its own gate run there with `--replay`: an
    entry naming each bean it changes, the moments its acts carry, RULE-CHANGE, kept, harm, consent's future
    whereabouts, the language held to its pin — all but the clock's register of headings, which is a clone's. So a hub
    refuses what the commit's hook refused, and a commit made past its hook (`--no-verify`) is judged after all. The
    refusal, or None; and with `v`, its judgment, what the replay was (`replay`), for the receipt."""
    sys.path.insert(0, ROOT)
    from core import judge as dmjudge
    scope = dmjudge.Scope.replay([commit], env)
    found = dmjudge.judge(None, scope)
    said = scope.said.get(commit, '').strip()
    if v is not None:
        v['replay'] = said if said.startswith(('not replayed', 'could not')) else 'replayed against its parent'
    if found:
        return "its own rules refuse it, replayed against its parent as its hook judged it:\n" + said[-1500:]
    return None


def verdicts(old, new, only=None, each=False, env=None, known=('--exclude=refs/daftar/custom/*', '--all'),
             whole=False):
    """THE JUDGMENT OF ONE REF UPDATE, commit by commit: ([{commit, writer, key, refused, gate}], (tip, refusal)).
    Each commit no garden ref holds yet, oldest first, with the bean its key names, the key, its refusal (steps 1-3,
    and with --each its own gate) or None, and what judged the garden it leaves; then the gate at the push's tip, run
    where --each is not: (the tip, its refusal or None), or (None, why it did not run). A hub that refuses stops at the
    first refusal, and what follows it is neither judged nor listed. A hub that reports judges every commit (`whole`),
    and still runs no gate once a commit has failed steps 1-3: the gate is the pushed tree's own code, which runs only
    once every commit before it is let in."""
    env = env or dict(os.environ)
    if new == ZERO:
        return [], (None, "a ref deleted: nothing to judge")
    # the commits no garden ref holds yet: a person's labels ref holds commits never judged as the garden, so a commit
    # it holds is judged again before a garden's branch may hold it
    _c, out, _e = git('rev-list', '--reverse', new, '--not', *known, env=env)
    commits = [c for c in out.split('\n') if c]
    found, let_in = [], True
    unrun = "not run: a commit before it was refused at steps 1-3, and the hub runs no code the gardener did not let in"
    with tempfile.TemporaryDirectory(prefix='hub-') as tmp:
        for c in commits:
            v = {'commit': c, 'writer': None, 'key': None, 'refused': None,
                 'gate': 'this commit' if each else f'the push\'s tip, {new}'}
            _r, raw, _e = git('cat-file', 'commit', c, env=env, text=False)
            payload, sig = split_signature(raw)
            _r, parents, _e = git('rev-list', '--parents', '-n', '1', c, env=env)
            parent = (parents.split() + [None, None])[1]
            others = parents.split()[2:]                     # a merge's other parents
            try:
                if sig is None:
                    raise Refused("it is not signed: a hub accepts a commit signed by a key a writer's bean carries")
                kind, fpr = fingerprint(payload, sig, tmp)
                v['key'] = fpr
                if parent is None:
                    _r, refs, _e = git('for-each-ref', '--format=%(refname)', env=env)
                    if refs.strip():
                        raise Refused("it has no parent, and this hub already holds the garden: a garden has one root, "
                                      "and a commit with none would be judged by writers its own tree names")
                at = Tree(parent or c, env)
                beans, gardener = at.beans(), at.gardener()
                who = v['writer'] = writer_of(kind, fpr, beans)
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
            except Refused as x:
                v['refused'], let_in = str(x), False
            if each and not v['refused']:
                if let_in:
                    try:
                        gate(c, env, tmp)
                        v['refused'] = replay(c, env, v)
                    except Refused as x:
                        v['refused'] = str(x)
                else:
                    v['gate'] = unrun
            elif each:
                v['gate'] = unrun
            found.append(v)
            if v['refused'] and not whole:
                break
        if not each and let_in:                       # every commit let in: each one's own rules, then the tip's tree
            for v in found:
                v['refused'] = replay(v['commit'], env, v)
                if v['refused'] and not whole:
                    break
        if each or not commits:
            tip = (None, "each commit judged by its own gate" if commits else "no commit new to the hub")
        elif not let_in:
            tip = (None, unrun)
            for v in found:
                v['gate'] = unrun
        else:
            try:
                gate(new, env, tmp)
                tip = (new, None)
            except Refused as x:
                tip = (new, str(x))
    return found, tip


def judge(old, new, only=None, each=False, env=None, known=('--exclude=refs/daftar/custom/*', '--all')):
    """[str]: every refusal for one ref update; empty when the push is accepted. `known` is what counts as judged
    already: everything a hub holds but a person's labels; a peer's own branches alone (`receive`)."""
    return refusals(*verdicts(old, new, only, each, env, known))


def refusals(found, tip):
    """[str] of a judgment (`verdicts`): each commit refused, by its short name, and the gate refusing the push's tip."""
    return [f"{v['commit'][:10]}: {v['refused']}" for v in found if v['refused']] + \
        ([f"{tip[0][:10]}: {tip[1]}"] if tip[0] and tip[1] else [])


def judge_custom(person, old, new, env=None):
    """[str]: every refusal for an update of `refs/daftar/custom/<person>`; empty when it is taken. Each new commit is
    signed by a key the person's bean carries, as the garden stands at the hub now (its HEAD), and its tree holds only
    their customisation files, each a JSON object of theirs; the ref only moves on top of what it was, and is never
    deleted. No gate runs: nothing on it is the garden's."""
    found, whole = custom_verdicts(person, old, new, env)
    return [whole] if whole else [f"{v['commit'][:10]}: {v['refused']}" for v in found if v['refused']]


def custom_verdicts(person, old, new, env=None, whole=False):
    """The judgment of an update of a person's labels ref, commit by commit, as `verdicts` gives a garden's: ([{commit,
    writer, key, refused, gate}], the refusal of the update as a whole or None). `whole`: every commit judged, as a
    hub that reports judges them."""
    env = env or dict(os.environ)
    if new == ZERO:
        return [], ("a person's customisations are never deleted at the hub: a word set back to the page's own is kept, "
                    "and the ref's history keeps what each was")
    if old != ZERO and git('merge-base', '--is-ancestor', old, new, env=env)[0] != 0:
        return [], (f"{new[:10]}: it is not on top of what the ref held ({old[:10]}): a person's labels move on, merged "
                    f"word by word, and their history keeps every word")
    c, tip, _e = git('rev-parse', '--verify', '-q', 'HEAD^{commit}', env=env)
    if c != 0 or not tip.strip():
        return [], f"{new[:10]}: this hub holds no garden yet, so no bean carries {person}'s key"
    beans = Tree(tip.strip(), env).beans()
    # EVERY COMMIT THE REF GAINS, not only those new to the hub: a chain already on another person's ref, pushed onto
    # this one, is judged again — by this person's key
    _c, out, _e = git('rev-list', '--reverse', new, *(['--not', old] if old != ZERO else []), env=env)
    found = []
    with tempfile.TemporaryDirectory(prefix='hub-') as tmp:
        for c in [x for x in out.split('\n') if x]:
            v = {'commit': c, 'writer': None, 'key': None, 'refused': None,
                 'gate': "none: a person's labels, nothing there the garden's"}
            _r, raw, _e = git('cat-file', 'commit', c, env=env, text=False)
            payload, sig = split_signature(raw)
            try:
                if sig is None:
                    raise Refused("it is not signed: a person's labels are signed by a key their bean carries")
                kind, fpr = fingerprint(payload, sig, tmp)
                who = v['writer'] = writer_of(kind, fpr, beans)
                v['key'] = fpr
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
                v['refused'] = str(x)
            found.append(v)
            if v['refused'] and not whole:
                break
    return found, None


def receive(ref, each=False, env=None):
    """[str]: every refusal for what a fetch brought into `ref`, judged as a hub judges a push: the commits it holds that
    this clone's own branches do not."""
    env = env or dict(os.environ)
    c, sha, _e = git('rev-parse', '--verify', '-q', ref + '^{commit}', env=env)
    if c != 0 or not sha.strip():
        return [f"{ref} names no commit"]
    return judge(ZERO, sha.strip(), None, each, env, known=('--branches',))


def hooks(only=None, each=False, report=False):
    """{name: text} of the hooks a bare hub runs, written by this hub's code: the gate again before a push is taken, in
    the mode given, and each judged commit's receipt after."""
    args = ' '.join(filter(None, [f"--only '{only}'" if only else '', '--each' if each else '',
                                  '--report' if report else '']))
    return {'pre-receive': (f"#!/bin/sh\n# written by bin/hub.py install: the gate again, at the hub (N32)\n"
                            f"exec '{sys.executable}' '{HERE}' pre-receive {args}\n"),
            'post-receive': (f"#!/bin/sh\n# written by bin/hub.py install: a receipt for each commit the hub judged\n"
                             f"exec '{sys.executable}' '{HERE}' post-receive\n")}


def install(repo, only=None, each=False, report=False):
    """The hooks of a bare repository, written by this hub's code: [(path, written, why not)]. A hook that is already
    the one this would write is left as it is (a runbook makes it root's, which the hub's own account may not write),
    and one it cannot write is named, never a crash. A working copy gets none: []."""
    if git('-C', repo, 'rev-parse', '--is-bare-repository')[1].strip() != 'true':
        return []
    out = []
    for name, text in hooks(only, each, report).items():
        hook = os.path.join(repo, 'hooks', name)
        try:
            with open(hook, encoding='utf-8', newline='') as fh:
                if fh.read() == text:
                    out.append((hook, False, ''))
                    continue
        except OSError:
            pass
        try:
            os.makedirs(os.path.dirname(hook), exist_ok=True)
            with open(hook, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(text)
            os.chmod(hook, 0o755)
            out.append((hook, True, ''))
        except OSError as x:
            out.append((hook, False, f"not written: {x.strerror or x}"))
    return out


# ---- WHAT THE HUB KEEPS OF WHAT IT JUDGED: a log beside it, and a receipt on each commit it judged

NOTES = 'refs/notes/daftar'        # the hub's receipts, one note to a commit, written by the hub alone
SIGNED_AS = 'daftar-receipt'       # the namespace a receipt is signed in, so no signature over one is a commit's
WHOLE = ("the signature, the writer, the rights (`write`, `ratify:F`, `ratify:G`), the commit's own rules replayed "
         "against its parent where its gate replays them (`replay`: all but the clock's register of headings); not "
         "judged at the hub: the Contract's classes C, D, E and J")


def _gitdir(env=None):
    """The hub's own git directory, as the hook runs in it."""
    return os.path.abspath(git('rev-parse', '--absolute-git-dir', env=env)[1].strip() or '.')


def _kept(gitdir, *names):
    d = os.path.join(gitdir, 'daftar', *names[:-1])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, names[-1])


def _moment():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _log(gitdir, entry):
    """One line of JSON appended to the hub's log, `<git dir>/daftar/hub.log`, under a lock where the system gives one."""
    with open(_kept(gitdir, 'hub.log'), 'a', encoding='utf-8', newline='\n') as fh:
        try:
            import fcntl
            fcntl.flock(fh, fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass
        fh.write(json.dumps(entry, ensure_ascii=False) + '\n')


_RELEASE = []


def release():
    """What judged: this hub's own code — its checkout's tag and commit, or, where it is no checkout, the version of the
    law beside it. Asked of its own folder, never of the hub the hook runs in."""
    if not _RELEASE:
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        c, sha, _e = git('-C', ROOT, 'rev-parse', 'HEAD', env=env)
        if c == 0 and sha.strip():
            _c, tag, _e = git('-C', ROOT, 'describe', '--tags', '--always', '--dirty', env=env)
            _RELEASE.append(f"bin/hub.py of {tag.strip()} ({sha.strip()})")
        else:
            m = None
            try:
                with open(os.path.join(ROOT, 'core', 'law', 'core.yaml'), encoding='utf-8') as fh:
                    m = re.search(r'^version:\s*"?([0-9.]+)', fh.read(), re.M)
            except OSError:
                pass
            _RELEASE.append(f"bin/hub.py of core {m.group(1) if m else 'unknown'} (no checkout)")
    return _RELEASE[0]


def law_of(commit, env=None):
    """The law a commit's garden is judged by: its pin and the SHA-256 of its law's files and its own rows as git holds
    them at the commit (core/law/, VOCAB.md, GARDEN.md: each file's path and blob)."""
    import hashlib
    _c, out, _e = git('ls-tree', '-r', '--full-tree', commit, '--', 'core/law', 'VOCAB.md', 'GARDEN.md', env=env)
    _c, manifest, _e = git('show', f'{commit}:GARDEN.md', env=env)
    pin = dmcheck.pin_of(manifest or '') or 'no pin'
    return f"{pin}, sha256:{hashlib.sha256(out.encode('utf-8')).hexdigest()}"


def _pending(gitdir, ref, old, new):
    import hashlib
    return _kept(gitdir, 'hub-judged', hashlib.sha256(f"{ref} {old} {new}".encode()).hexdigest()[:32] + '.json')


def pre_receive(lines, only=None, each=False, report=False, env=None):
    """THE HUB'S JUDGMENT OF A PUSH: (exit code, lines to show the writer). Each ref update judged; each written to the
    log; what may land kept for the receipts its post-receive writes. A hub that refuses refuses the push for any
    refusal; one that REPORTS refuses nothing of the garden's, and shows and logs what it would refuse. The receipts'
    ref is the hub's own, refused in either mode."""
    env = env or dict(os.environ)
    dmcheck.differs(ROOT, 'hub')          # its own copy, said first where it is not its release's (core 3.5, II.2)
    gitdir, at, mode = _gitdir(env), _moment(), 'reporting' if report else 'refusing'
    shown, judged, refused, own = [], [], False, False
    for old, new, ref in lines:
        if ref == NOTES:
            why = "the hub's receipts are its own: written after a push it judged, signed with its key, never pushed"
            _log(gitdir, {'at': at, 'mode': mode, 'ref': ref, 'old': old, 'new': new, 'verdict': 'refused',
                          'refusals': [why]})
            shown.append(f"hub: REFUSED {ref} {why}")
            own = True
            continue
        m = CUSTOM_REF.match(ref)
        if m:
            found, whole = custom_verdicts(m.group(1), old, new, env, whole=report)
            tip, said = (None, "none: a person's labels, nothing there the garden's"), ([whole] if whole else []) + \
                [f"{v['commit'][:10]}: {v['refused']}" for v in found if v['refused']]
        else:
            found, tip = verdicts(old, new, only, each, env, whole=report)
            said = refusals(found, tip)
        verdict = 'taken' if not said else 'would refuse' if report else 'refused'
        _log(gitdir, {'at': at, 'mode': mode, 'ref': ref, 'old': old, 'new': new, 'verdict': verdict,
                      'commits': [{k: v[k] for k in ('commit', 'writer', 'key', 'refused')} for v in found],
                      'gate': {'at': tip[0], 'said': tip[1]}, 'refusals': said})
        shown += [f"hub: {'WOULD REFUSE' if report else 'REFUSED'} {ref} {r}" for r in said]
        refused = refused or bool(said)
        if found:
            judged.append((ref, old, new, {'ref': ref, 'mode': mode, 'at': at, 'commits': found,
                                           'gate': {'at': tip[0], 'said': tip[1]}}))
    if report and refused:
        shown.append(f"hub: this hub reports, and refuses nothing of the garden's: taken, and what it would refuse is "
                     f"logged in {os.path.join(gitdir, 'daftar', 'hub.log')}")
    code = 1 if own or (refused and not report) else 0
    if code == 0:
        for ref, old, new, rec in judged:                 # what lands, for the receipts the post-receive writes
            with open(_pending(gitdir, ref, old, new), 'w', encoding='utf-8') as fh:
                json.dump(rec, fh, ensure_ascii=False)
    return code, shown


def receipt_text(rec, v, env=None):
    """A receipt's words, before its signature: what was judged, by what law and what code, and the verdict."""
    tip = rec['gate']
    why = v['refused'] or (tip['said'] if tip['at'] and tip['said'] else None)
    verdict = 'taken' if not why else 'taken, and would be refused' if rec['mode'] == 'reporting' else 'refused'
    gate = v['gate'] + ((', which refused' if tip['said'] else ', which passed') if tip['at'] and
                        v['gate'].startswith("the push's tip") else '')
    lines = ["daftar: a hub's receipt", f"commit: {v['commit']}", f"ref: {rec['ref']}", f"verdict: {verdict}"]
    lines += [f"why: {' '.join(why.split())[:1500]}"] if why else []
    lines += [f"writer: {v['writer'] or 'none'}, by the key {v['key'] or 'none'}", f"judged: {WHOLE}",
              f"gate: {gate}", f"replay: {' '.join(str(v.get('replay') or 'not run: the gate did not run').split())[:300]}",
              f"law: {law_of(v['commit'], env)}", f"judge: {release()}", f"mode: {rec['mode']}",
              f"at: {rec['at']}"]
    return '\n'.join(lines) + '\n'


def sign_receipt(text, key, tmp):
    """The receipt with its SSH signature by the hub's key appended, or with the reason it carries none."""
    if not key or not os.path.isfile(key):
        return text + "signed: no — this account keeps no key of this hub (`bin/hub.py install` makes it)\n"
    body = os.path.join(tmp, 'receipt')
    with open(body, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    if os.path.exists(body + '.sig'):
        os.remove(body + '.sig')            # ssh-keygen never writes over a signature: the last receipt's would stay
    r = subprocess.run(['ssh-keygen', '-Y', 'sign', '-f', key, '-n', SIGNED_AS, body], capture_output=True,
                       stdin=subprocess.DEVNULL)
    try:
        if r.returncode != 0:
            raise OSError
        with open(body + '.sig', encoding='utf-8') as fh:
            return text + fh.read()
    except OSError:
        return text + f"signed: no — ssh-keygen did not sign it ({r.stderr.decode('utf-8', 'replace').strip()[:200]})\n"


def post_receive(lines, env=None):
    """THE RECEIPTS of a push taken: for each commit its pre-receive judged, a note on refs/notes/daftar, signed by the
    hub's key. Returns the lines to show. It never fails the push, which has landed."""
    env = env or dict(os.environ)
    gitdir = _gitdir(env)
    key = key_of(gitdir)[0]
    gid = (key_of(gitdir)[1] or 'garden')
    who = {**env, 'GIT_AUTHOR_NAME': 'daftar hub', 'GIT_AUTHOR_EMAIL': f'hub@{gid}.daftar.invalid',
           'GIT_COMMITTER_NAME': 'daftar hub', 'GIT_COMMITTER_EMAIL': f'hub@{gid}.daftar.invalid'}
    shown, n = [], 0
    with tempfile.TemporaryDirectory(prefix='hub-') as tmp:
        for old, new, ref in lines:
            p = _pending(gitdir, ref, old, new)
            try:
                with open(p, encoding='utf-8') as fh:
                    rec = json.load(fh)
            except (OSError, ValueError):
                continue
            for v in rec['commits']:
                if git('notes', '--ref', NOTES, 'list', v['commit'], env=env)[0] == 0:
                    continue                                   # one receipt to a commit: the first door that judged it
                note = os.path.join(tmp, 'note')
                with open(note, 'w', encoding='utf-8', newline='\n') as fh:
                    fh.write(sign_receipt(receipt_text(rec, v, env), key, tmp))
                for _try in range(5):                          # another push's receipts may hold the ref a moment
                    c, _o, e = git('notes', '--ref', NOTES, 'add', '-F', note, v['commit'], env=who)
                    if c == 0 or 'lock' not in e:
                        break
                    import time
                    time.sleep(0.2)
                if c == 0:
                    n += 1
                else:
                    shown.append(f"hub: no receipt written for {v['commit'][:10]}: {e.strip()[:200]}")
            os.remove(p)
    if n:
        shown.append(f"hub: {n} receipt{'s' if n != 1 else ''} written on {NOTES}" +
                     ("" if key and os.path.isfile(key) else ", unsigned: this account keeps no key of this hub"))
    return shown


def read_receipt(text, tmp):
    """(the receipt's words, the fingerprint whose signature over them verifies, or None, and why not)."""
    mark = '-----BEGIN SSH SIGNATURE-----'
    if mark not in text:
        return text, None, 'it carries no signature'
    body, sig = text.split(mark, 1)
    ps, ss = os.path.join(tmp, 'body'), os.path.join(tmp, 'body.sig')
    with open(ps, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(body)
    with open(ss, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(mark + sig)
    with open(ps, 'rb') as fh:
        r = subprocess.run(['ssh-keygen', '-Y', 'check-novalidate', '-n', SIGNED_AS, '-s', ss], stdin=fh,
                           capture_output=True)
    m = re.search(r'(SHA256:[A-Za-z0-9+/]{43})', (r.stdout + r.stderr).decode('utf-8', 'replace'))
    return body, (m.group(1) if r.returncode == 0 and m else None), ('' if r.returncode == 0 and m else
                                                                    'its signature does not verify')


def receipts(repo, rev=None):
    """(exit code, lines): every commit `rev` reaches (every branch, unset) and its receipt — taken, would be refused,
    refused — with whose key signed it: this hub's, and the bean that names that key as the garden stands now (HEAD);
    and each commit no receipt is on, which no door of this hub judged. 0 where each has one, signed by this hub's
    key."""
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    _c, out, _e = git('-C', repo, 'rev-list', *([rev] if rev else ['--branches']), env=env)
    commits = [c for c in out.split('\n') if c]
    _c, notes, _e = git('-C', repo, 'notes', '--ref', NOTES, 'list', env=env)
    note = {c: b for b, c in (l.split() for l in notes.split('\n') if len(l.split()) == 2)}
    path = key_of(repo)[0]
    ours = dminstall.ssh_fingerprint(path) if path and os.path.isfile(path) else None
    c, head, _e = git('-C', repo, 'rev-parse', '--verify', '-q', 'HEAD^{commit}', env=env)
    beans = Tree(head.strip(), {**env, 'GIT_DIR': _gitdir_of(repo)}).beans() if c == 0 and head.strip() else {}
    lines, bad, none = [], 0, []
    with tempfile.TemporaryDirectory(prefix='hub-') as tmp:
        for c in commits:
            if c not in note:
                none.append(c)
                continue
            _r, text, _e = git('-C', repo, 'cat-file', 'blob', note[c], env=env)
            body, fpr, why = read_receipt(text, tmp)
            verdict = (re.search(r'^verdict: (.*)$', body, re.M) or [None, '?'])[1]
            named = writer_of('ssh_key_fingerprint', fpr, beans) if fpr else None
            ok = bool(fpr) and fpr == ours
            bad += 0 if ok else 1
            whose = ("this hub's key" if ok else "not this hub's key") + \
                (f", named by {named}" if named else ", named by no bean")
            lines.append(f"{c[:10]} {verdict}; " + (f"signed by {fpr} ({whose})" if fpr else why))
    unsigned = f" ({bad} not signed by this hub's key)" if bad else ''
    head = (f"hub: {len(commits)} commit{'s' if len(commits) != 1 else ''}: {len(commits) - len(none)} with a receipt"
            f"{unsigned}, {len(none)} with none — which no door of this hub judged")
    return (0 if not bad and not none else 1), [head] + lines + [f"{c[:10]} no receipt" for c in none]


def _gitdir_of(repo):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    return os.path.abspath(git('-C', repo, 'rev-parse', '--absolute-git-dir', env=env)[1].strip() or repo)


def report(repo, since=None):
    """(exit code, lines): what the hub's log holds — each ref update judged since `since` (a moment, `2026-10-24`, or
    all), how many were taken, would have been refused, and were refused, and each that was not simply taken."""
    try:
        with open(os.path.join(_gitdir_of(repo), 'daftar', 'hub.log'), encoding='utf-8') as fh:
            rows = [json.loads(l) for l in fh if l.strip()]
    except OSError:
        return 1, [f"hub: {repo} keeps no log: no push has been judged here since a release that writes one"]
    except ValueError as x:
        return 2, [f"hub: the log is not one JSON object to a line: {x}"]
    rows = [r for r in rows if not since or str(r.get('at', '')) >= since]
    count = {k: sum(1 for r in rows if r.get('verdict') == k) for k in ('taken', 'would refuse', 'refused')}
    lines = [f"hub: {len(rows)} ref update{'s' if len(rows) != 1 else ''} judged{f' since {since}' if since else ''}: "
             f"{count['taken']} taken, {count['would refuse']} would have been refused (reporting), "
             f"{count['refused']} refused"]
    for r in rows:
        if r.get('verdict') != 'taken':
            lines += [f"{r.get('at')} {r.get('verdict')} {r.get('ref')} {x}" for x in r.get('refusals') or []]
    return 0, lines


state_dir = dminstall.state_dir      # this account's daftar state folder: the agent's key and each hub's are kept there


def key_of(repo):
    """(the path of the hub's key of the garden `repo` holds, the garden's id), or (None, None) where it holds no garden
    yet — no commit, or a shallow clone that cannot see its root."""
    gid = dmparse.garden_id(repo)
    return (os.path.join(state_dir(), 'hubs', gid, 'key'), gid) if gid else (None, None)


def make_key(repo):
    """THE HUB'S OWN KEY, made once where this account has none for the garden: (path, made, why not). Never made over:
    a new key is a new identity, the gardener's to name (class F)."""
    path, gid = key_of(repo)
    if path is None:
        return None, False, ("the repository holds no garden yet: the hub's key is named by the garden's id, and is made "
                             "when `install` runs again after the garden's first commit is here")
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        owner = os.stat(repo).st_uid
        if owner != 0:
            try:
                import pwd
                who = pwd.getpwuid(owner).pw_name
            except (ImportError, KeyError):
                who = f"uid {owner}"
            return None, False, (f"the hub's key is its own account's ({who}, who owns {repo}), never root's: that "
                                 f"account's own `install` makes it")
    made, why = dminstall.make_key(path, f'hub@{gid}')
    return (None, False, why) if why else (path, made, '')


def key_lines(path, made):
    """What a person is shown of the hub's key: its fingerprint, its public line and the statement for the hub's bean
    — never the private key."""
    fpr, pub = dminstall.shown(path)
    return [f"hub: the key of this hub: {fpr} — " + ("made now" if made else
                                                    "kept: made before, and never made over (a new one is the "
                                                    "gardener's to name)"),
            f"hub: its public half: {pub}",
            f"hub: the gardener adds it to the hub's bean, a name that establishes an identity (class F): "
            f"name: {{ by: ssh, of: self, as: \"{fpr}\" }}",
            f"hub: kept in {os.path.dirname(path)}, this account's alone: never in the garden, and never copied to "
            f"another machine"]


def main(argv):
    argv = list(argv)
    only = argv[argv.index('--only') + 1] if '--only' in argv else None
    each, reporting = '--each' in argv, '--report' in argv
    if argv[:1] in (['report'], ['receipts']) and len(argv) >= 2:
        repo = os.path.abspath(argv[1])
        if git('-C', repo, 'rev-parse', '--git-dir')[0] != 0:
            print(f"hub: {repo} is no git repository", file=sys.stderr)
            return 2
        rest = [a for a in argv[2:] if a != '--since']
        since = argv[argv.index('--since') + 1] if '--since' in argv[:-1] else None
        code, lines = report(repo, since) if argv[0] == 'report' else receipts(repo, rest[0] if rest else None)
        print('\n'.join(lines))
        return code
    if argv[:1] in (['install'], ['key']) and len(argv) >= 2:
        repo = os.path.abspath(argv[1])
        if git('-C', repo, 'rev-parse', '--git-dir')[0] != 0:
            print(f"hub: {repo} is no git repository — nothing written", file=sys.stderr)
            return 2
        if argv[0] == 'key':
            path = key_of(repo)[0]
            if not path:
                print("hub: the repository holds no garden yet, so no hub's key: `install` makes it once the garden's "
                      "first commit is here", file=sys.stderr)
                return 1
            if not os.path.isfile(path):
                print("hub: this account keeps no key of this hub of the garden — `install` makes it", file=sys.stderr)
                return 1
            print('\n'.join(key_lines(path, False)))
            return 0
        written = install(repo, only, each, reporting)
        for hook, wrote, why in written:
            print(f"hub: installed {hook}" if wrote else f"hub: {hook} {why}" if why else
                  f"hub: the hook is there already, as it should be: {hook}")
        if not written:
            print(f"hub: {repo} is a working copy: nothing is pushed into it, and it judges what it fetches "
                  f"(`receive`, bin/sync.py) — no hook")
        elif reporting:
            print("hub: it REPORTS: it judges every push as it would and refuses nothing of the garden's, logging what it "
                  "would refuse in the hub's daftar/hub.log (`bin/hub.py report`); install again without --report to "
                  "refuse")
        path, made, why = make_key(repo)
        print('\n'.join(key_lines(path, made)) if path else f"hub: no key made — {why}")
        return 1 if any(why for _h, _w, why in written) else 0
    if argv[:1] == ['receive'] and len(argv) >= 2:
        refused = receive(argv[1], each)
        for r in refused:
            print(f"hub: REFUSED {argv[1]} {r}", file=sys.stderr)
        if not refused:
            print(f"hub: {argv[1]}: taken — every commit it brings is signed by a writer, within their rights, and the "
                  f"garden passes its gate")
        return 1 if refused else 0
    if argv[:1] in (['pre-receive'], ['post-receive']):
        lines = [tuple(l.split()) for l in sys.stdin.read().split('\n') if len(l.split()) == 3]
        if argv[0] == 'post-receive':
            for r in post_receive(lines):
                print(r, file=sys.stderr)
            return 0
        code, shown = pre_receive(lines, only, each, reporting)
        for r in shown:
            print(r, file=sys.stderr)
        return code
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
