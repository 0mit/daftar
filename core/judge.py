"""judge — the one judge: every door of a garden asks it, and no other code computes a verdict (D13).

    judge(law, scope) -> [(rule, where, message)]       each one an error: the law is strict

A door is where a write enters a garden. Each asks this, with what it holds as the scope:

    Scope.tree(root, garden)        the beans as they stand              core/check.py, bin/check.py --all, propose's read
    Scope.staged(root)              what a commit would hold: the index,  the pre-commit hook (bin/check.py --staged), and so
                                    with the law it stages, and the       the save and its --again, which commit through it
                                    commit's own rules (core/commit.py)
    Scope.commits(shas, env)        what a push or a fetch brings: each   bin/hub.py, at a hub's receive and at a peer's
                                    commit's tree, checked out, judged by
                                    the gate it carries — its law and its
                                    judge, as the commit holds them
    Scope.union(garden, keepings)   git and what a host keeps beside it,  bin/store.py's check
                                    judged together

`law` is the law to judge by; None judges by the law the scope holds — the tree's (its VOCAB.md on the release it
carries, or on this one), the index's, each commit's own. A verdict is the law's own problems first, then the garden's,
in the order the rules are judged (core/engine.py, Judge.run); the commit's own rules after them; what a keeping adds
last, each finding once. The scope keeps what the door reports beside the verdict: the garden judged (`garden`), and for
each commit the gate's own words (`said`)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from core import engine, read, standards  # noqa: E402
from core.law import Law  # noqa: E402


def garden_law(root, release=None):
    """The law of the release at `release` (this one, if none), extended by the rows of the garden at `root` (its
    VOCAB.md, where it has one). The standards are the garden's where it carries a law (`standards.carried`): a scheme of
    codes it holds as its own is read there, as knowledge reads it."""
    p = os.path.join(root, 'VOCAB.md')
    ext = (('VOCAB.md', read.document(p)[0]),) if os.path.exists(p) else ()
    std = standards.here(root) if standards.carried(root) else None
    return Law.load(*ext, root=release, std=std)


def carried(root):
    """The release a tree carries, where it carries the core's law (`core/law/core.yaml`); else None, this one."""
    return root if os.path.isfile(os.path.join(root, 'core', 'law', 'core.yaml')) else None


class Scope:
    """What a door holds, to be judged: one of tree, staged, commits, union."""

    KINDS = ('tree', 'staged', 'commits', 'union')

    def __init__(self, kind, root=None, garden=None, commits=(), env=None, keepings=None):
        if kind not in self.KINDS:
            raise ValueError(f"a scope is one of {', '.join(self.KINDS)}, not {kind!r}")
        self.kind, self.root, self.garden, self.commits, self.env, self.keepings = \
            kind, root, garden, list(commits), env, keepings
        self.said = {}                     # commit -> what its own gate printed (commits)
        self.unread = None                 # why the index could not be read (staged)

    @classmethod
    def tree(cls, root=None, garden=None):
        """The beans at `root` as they stand, or the `garden` already read."""
        return cls('tree', root=root if root is not None else getattr(garden, 'root', None), garden=garden)

    @classmethod
    def staged(cls, root):
        """The index of the clone at `root`, as the commit would hold it."""
        return cls('staged', root=root)

    @classmethod
    def commits(cls, shas, env=None):
        """Each of `shas`, in the repository `env` names (GIT_DIR, its objects, a push's quarantine among them)."""
        return cls('commits', commits=shas, env=env)

    @classmethod
    def union(cls, garden, keepings, root=None):
        """The `garden` with what a host keeps beside it: `keepings(law, garden, base)` gives the findings the keepings
        add to git's own, `base`."""
        return cls('union', root=root if root is not None else getattr(garden, 'root', None), garden=garden,
                   keepings=keepings)


def judge(law, scope):
    """[(rule, where, message)]: the verdict of `law` (None: the scope's own) over `scope`."""
    if scope.kind == 'tree':
        if scope.garden is None:
            scope.garden = engine.Garden.read(scope.root)
        if law is None:
            law = garden_law(scope.root)
        return list(law.problems()) + engine.Judge(law, scope.garden).run()
    if scope.kind == 'staged':
        return _staged(law, scope)
    if scope.kind == 'commits':
        return _commits(scope)
    base = judge(law, Scope.tree(scope.root, scope.garden))
    seen = set(base)
    out = list(base)
    for f in scope.keepings(law if law is not None else garden_law(scope.root), scope.garden, base):
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def instructions(law, scope, seed=None):
    """([guards.Instruction], [(rule, where, message)]): the gardener's standing instructions to agents in the garden
    `scope` holds (a tree) — each clause on the permission square whose `clause` names a guard, read by this judge's own
    reader and law, so no other code reads them. An instruction is the gardener's own word or nothing (CHECKLIST Part
    D): a clause counts where a `say` by the garden's gardener covers it, while it holds (its `while`, core/inforce.py;
    one not known to hold counts: the default is caution) and its `state` leaves it in force. The second list is what
    rule `measured` finds in those clauses: a door that cannot read an instruction refuses rather than guess it.

    `seed`, the path of the seed's agents' work agreement (seed/agents-work.md.template): for each guard no instruction
    of the garden names, the seed's clauses naming it, read as the gardener's (`Instruction.seed`) by this release's law
    — the default a garden starts at, until its gardener says otherwise."""
    from core import guards, inforce, measures
    if scope.garden is None:
        scope.garden = engine.Garden.read(scope.root)
    if law is None:
        law = garden_law(scope.root)
    G = scope.garden
    J = engine.Judge(law, G)
    F = inforce.InForce(scope.root, G=G, law=law)
    out, bad = [], []

    def read_bean(b, at, is_seed, J):
        for i, verb, r in b.items:
            c = r.get('clause')
            if verb not in guards.CONTRADICTORY or 'held' in r or not isinstance(c, dict) or c.get('guard') is None:
                continue
            said = G.gardener is not None and any(v == 'say' and rr.get('by') == G.gardener
                                                  for v, rr in J._acts_of(b, i, r))
            if not said or str(c.get('state') or 'in-force') != 'in-force' or F.holds(b.id, r) is False:
                continue
            found = measures.guard_problems(J, f"{at}[{i}] {verb}.clause", c, verb)
            if found:
                bad.extend(('measured', w, m) for w, m in found)
                continue
            hit = J.statement(r.get('of'), b)
            says = hit[3].get('of') if hit and isinstance(hit[3].get('of'), str) else None
            yield guards.Instruction(str(c['guard']), verb, c.get('operand') or {},
                                     f"{at}#{r['id']}" if isinstance(r.get('id'), str) else f"{at}[{i}]", says, is_seed)

    for b in G.beans.values():
        out += read_bean(b, b.id, False, J)
    if seed and os.path.isfile(seed) and G.gardener:
        with open(seed, encoding='utf-8') as fh:
            text = fh.read().replace('@@GARDENER@@', G.gardener)
        head, body = engine.dmparse.split_front_matter(text)
        sb = engine.Bean(str((read.loads(head, seed) or {}).get('bean') or 'seed'), seed, read.loads(head, seed),
                         body=body)
        named = {i.guard for i in out}
        rel = os.path.relpath(seed, ROOT).replace(os.sep, '/') if seed.startswith(ROOT) else seed
        # the seed is the release's, read by the release's own law and standards, whatever the garden carries
        out += [i for i in read_bean(sb, rel, True, engine.Judge(Law.load(), G)) if i.guard not in named]
    return out, bad


def _staged(law, scope):
    """The index, copied into a temporary directory and judged there with the law it stages; then the commit's own
    rules, between the index and the last commit."""
    from core import commit
    root = scope.root
    snap = tempfile.mkdtemp(prefix='daftar-core-staged-')
    try:
        r = subprocess.run(['git', '-C', root, 'checkout-index', '--all', '--prefix=' + snap.replace(os.sep, '/') + '/'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            scope.unread = f"the index could not be read — {r.stderr.strip()}"
            return [('form', 'index', scope.unread)]
        try:
            law = law if law is not None else garden_law(snap, carried(snap))
        except read.Unread as e:
            return [('form', 'VOCAB.md', str(e))]
        garden = engine.Garden.read(snap)
        try:                       # THE GARDEN'S ID is its clone's: the copy of the index has no history to read it from
            garden.gid = engine.dmparse.garden_id(root)
        except Exception:
            garden.gid = None
        scope.garden = garden
        return judge(law, Scope.tree(snap, garden)) + commit.findings(root, law, garden=garden)
    finally:
        shutil.rmtree(snap, ignore_errors=True)


def checkout(commit, env, tmp):
    """`commit` checked out under `tmp` in a fresh repository that borrows the objects `env` names — a hub's, the
    pushed ones still in quarantine among them — so no ref of the repository is touched while it is judged. (The
    checkout, the environment to run in there), or ValueError naming why it could not be made."""
    where = os.path.join(tmp, 'tip-' + commit[:10])
    objs = [os.path.abspath(env.get('GIT_OBJECT_DIRECTORY') or os.path.join(env.get('GIT_DIR') or '.', 'objects'))]
    objs += [os.path.abspath(p) for p in (env.get('GIT_ALTERNATE_OBJECT_DIRECTORIES') or '').split(os.pathsep) if p]
    objs.append(os.path.abspath(os.path.join(env.get('GIT_DIR') or '.', 'objects')))
    r = subprocess.run(['git', 'rev-parse', '--git-path', 'objects'], capture_output=True, text=True, env=env)
    if r.returncode == 0 and r.stdout.strip():                    # a working clone's are under .git/ (a peer's receive)
        objs.append(os.path.abspath(r.stdout.strip()))
    e = {k: v for k, v in env.items() if not k.startswith(('GIT_DIR', 'GIT_QUARANTINE', 'GIT_OBJECT_DIRECTORY',
                                                           'GIT_ALTERNATE', 'GIT_WORK_TREE', 'GIT_INDEX'))}
    e['GIT_ALTERNATE_OBJECT_DIRECTORIES'] = os.pathsep.join(dict.fromkeys(objs))
    for step in (('init', '-q', where), ('-C', where, 'update-ref', 'refs/heads/judged', commit),
                 ('-C', where, 'symbolic-ref', 'HEAD', 'refs/heads/judged'), ('-C', where, 'reset', '-q', '--hard')):
        r = subprocess.run(['git', *step], capture_output=True, text=True, env=e)
        if r.returncode != 0:
            raise ValueError(f"could not check out {commit[:10]}: {r.stderr.strip()[:200]}")
    return where, e


def _commits(scope):
    """Each commit's tree, checked out, judged by the gate the commit carries: the release in its tree judges it with
    its own law and its own judge, as its pre-commit hook did. A tree whose judge is this one's (it carries
    core/judge.py) gives its findings; an older tree's gate gives its words, one finding `gate` where they are a
    refusal."""
    env = dict(scope.env or os.environ)
    out = []
    with tempfile.TemporaryDirectory(prefix='judge-commits-') as tmp:
        for c in scope.commits:
            try:
                where, e = checkout(c, env, tmp)
            except ValueError as x:
                scope.said[c] = str(x)
                out.append(('gate', c[:10], str(x)))
                continue
            ours = os.path.isfile(os.path.join(where, 'core', 'judge.py'))
            gate = next((g for g in ('check.py', 'dmcheck.py') if os.path.isfile(os.path.join(where, 'bin', g))),
                        'dmcheck.py')       # a commit of a garden in today's words is judged by its own gate
            r = subprocess.run([sys.executable, os.path.join(where, 'bin', gate), '--all'] + (['--json'] if ours else []),
                               capture_output=True, cwd=where, env=e)
            text = (r.stdout + r.stderr).decode('utf-8', 'replace')
            if ours:
                try:
                    d = json.loads(r.stdout.decode('utf-8'))
                    scope.said[c] = d['printed'] + r.stderr.decode('utf-8', 'replace')
                    out += [tuple(f) for f in d['found']]
                    continue
                except (ValueError, KeyError, TypeError):
                    pass                    # it printed no verdict: what it printed is the refusal
            scope.said[c] = text
            if r.returncode != 0 or ' 0 error(s)' not in text:
                out.append(('gate', c[:10], text.strip()))
    return out
