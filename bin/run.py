#!/usr/bin/env python3
"""run — every job a tool starts, tracked as a course on one walk and held by its identity: never by a bare pid, a
prefix of a name, or a pattern that can match the shell that asks (core 2.11; `python3 bin/daftar.py run`).

    python3 bin/run.py start [options] -- <command> [args...]   start a run; prints its id
    python3 bin/run.py start [options] --script <file|->         a shell script, kept in the run's folder and run there
    python3 bin/run.py list [--all] [--json]                     the runs, live ones first, children under their parent
    python3 bin/run.py show <run> [--json]                       one run: its moves, its process, its progress
    python3 bin/run.py wait <run> [--timeout S]                  until it ends, bounded; the exit code says how it ended
    python3 bin/run.py stop <run> [--why W] [--grace S] [--tree] stop it, all of it, and nothing else
    python3 bin/run.py tail <run> [-n N] [-f]                    its log
    python3 bin/run.py adopt (--pid P | --match RE) [options]    a process started elsewhere, held by its identity
    python3 bin/run.py find <RE> [--args]                        processes whose command matches: never this one or a caller
    python3 bin/run.py export <run> [--self]                     the run as statements: its course and its moves
    python3 bin/run.py progress [--done N] [--total N] [--unit U] [--phase P] [--note T]   a step of the run this is in
    python3 bin/run.py reconcile [--adopt]                       runs whose end nobody saw: moved to lost, or watched again
    python3 bin/run.py prune [--days N] [--dry]                  the folders of runs ended N days ago (30), statements kept
    python3 bin/run.py setup                                     the walk `walk-run` written into this garden's mappings

A <run> is its id (run-YYYYMMDD-HHMMSS-xxxx), or `--name N` / `--key K` naming exactly one run that has not ended.
A name is matched whole, never by its beginning.

A RUN IS A COURSE (the law's own words, MODEL.md "Lines"; bin/act.py and bin/routines.py say the same of an action).
What the run acts on — a volume, a model, a trial; `--of`, or the host — is placed on one walk, `walk-run`, and each
step it reaches is a move: when, by whom (the machine's engine, or who asked), a reason from the step's list, and why
in words. Where a run stands is read from its last move, never stored beside it. The walk:

    queued     asked for; waits for its key when another run holds it            -> starting
    starting   its supervisor is up, the process being started                  -> running
    running    the process runs, its identity held                               -> stopping, done
    stopping   asked to stop: signalled, given its grace                         -> stopped, done
    paused     frozen at someone's word (a pause: it returns to where it was)
    done       ended well: exit 0, and its check held where it has one           (final)
    failed     start-failed, exit-code, signal, check-failed, resource-gone, raised   (a way out, final)
    stopped    asked, timeout                                                    (a way out, final)
    lost       supervisor-gone, reboot, exit-unseen: its end was not seen        (a way out; it may be left again)

THE REGISTRY IS A STORE (core 2.10, bin/store.py): the store `runs`, `store.sqlite` in $DAFTAR_RUNS, else
~/.local/state/daftar-runs. A run's course is `be: { id: <run>, by: <being>, at: walk-run, as: order, note }` and
each step it reaches is `move: { by, of, through: <being>#<run>, at: [<moment>, walk-run#<step>], as: <reason>, why
}`, statements of the being it acts on, known by the run's own act, `make: { id: <run>-made, by: <the machine> }`.
What only the machine needs to hold the process — its identity, cgroup, key, log, the masked command, its exit — is
that being's detail `runs.<run>`. The store is kept with a rollback journal and readable by others, so a page that
runs as another user reads it with read permission alone. `export` prints a run's statements for a bean; they are the
same statements, so a run kept both here and in a bean is one (one universe). The walk is the standard's: its steps
and reasons are STEPS below, and `setup` writes them into a garden as mappings/walk-run.md, as the books' walks are
written by their tool.

IDENTITY. A process is (boot id, pid, start time in clock ticks from /proc/<pid>/stat): a pid alone names another
process once it is reused (pid_max is 32768 here). Nothing is ever signalled unless all three still match; a pidfd
holds the process while its supervisor lives. Each run gets its own freezer cgroup (cgroup v1, delegated to this user
at first use: `sudo mkdir /sys/fs/cgroup/freezer/daftar-runs` and a chown, nothing on disk), so what it starts cannot
leave it — setsid, a double fork, sudo — and a stop freezes it, signals every member, and thaws it: all of the run and
nothing else. Where there is no cgroup the run is its own session (setsid), and a stop is the session's.

THE SUPERVISOR is one small process per run, started by `start` and detached (its own session, its own cgroup of
supervisors), so a tool that stops or restarts does not take its runs with it. It holds the child's pidfd, writes the
moves, keeps the log (stdin is /dev/null unless --stdin says otherwise: a command inside a heredoc cannot eat the rest
of the script), kills what the run left behind when it ends, runs its check, and tells the desktop of a failure.

KEYS. `--key K` makes a run exclusive: while one holds K no other starts with it (`start` refuses, naming the holder;
`--wait-key` queues instead), and `holder(K)` gives a restarted tool the run to watch rather than a second one to
start. A key is a lock the kernel keeps (flock on /tmp/.daftar-runs-<uid>/keys/<hash>), held by the supervisor and by
the process itself, so it outlives a dead supervisor and is free only when the whole run is gone; and it is the same
lock for every registry on the machine, so a test pointed at the real catalogue by mistake is refused there.

THE ENVIRONMENT is the caller's, as it was when it asked, with --env NAME=VALUE and --pass NAME on top (--clean-env:
only those and PATH, HOME, LANG); what is recorded is the named variables, a value masked where its name says it is a
secret. The command is recorded masked too: a command line can carry a password.

Exit codes: 0 done (or the command did what it says), 1 failed, 2 usage, 3 key busy, 4 no such run or not exactly one,
5 refused (the process is not the run's any more), 6 stopped, 7 lost, 124 a wait's bound passed.
The registry is $DAFTAR_RUNS, else ~/.local/state/daftar-runs (beside daftard's own state, never in it: that folder is
private and holds its key); every command that lists says which. A supervisor writes its moves unjudged, their shapes
fixed here; `python3 bin/store.py check` judges them where the store is kept, against the walk.
"""
import argparse, contextlib, fcntl, hashlib, json, os, pwd, re, secrets, select, shutil, signal, socket, subprocess
import sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ME = os.path.abspath(__file__)
sys.path.insert(0, HERE)
import store as dmstore  # noqa: E402  the registry is the store `runs`
WALK = 'walk-run'
STEPS = {   # the walk, as mappings/walk-run.md says it
    'queued': {'to': ['starting'], 'machine': True},
    'starting': {'to': ['running'], 'machine': True},
    'running': {'to': ['stopping', 'done'], 'machine': True},
    'stopping': {'to': ['stopped', 'done'], 'machine': True},
    'paused': {'resumes': True, 'reasons': ['asked']},
    'done': {'final': True},
    'failed': {'exit': True, 'final': True,
               'reasons': ['start-failed', 'exit-code', 'signal', 'check-failed', 'resource-gone', 'raised']},
    'stopped': {'exit': True, 'final': True, 'reasons': ['asked', 'timeout']},
    'lost': {'exit': True, 'machine': True, 'reasons': ['supervisor-gone', 'reboot', 'exit-unseen']},
}
STEP_SAYS = {   # what is done at each step, as the walk's mapping says it
    'queued': 'asked for: it waits for its key while another run holds it, or to be started',
    'starting': 'its supervisor is up, and the process is being started',
    'running': 'the process runs, held by its identity: boot id, pid and start time',
    'stopping': 'asked to stop, or its time ran out, or what it needs is gone: every process of it signalled, and given '
                'its grace',
    'paused': "frozen at someone's word; it returns to where it was",
    'done': 'it ended well: exit 0, and its check held where it has one',
    'failed': 'it ended badly: it could not start, it exited non-zero or by a signal, its check did not hold, what it '
              'needs went, or the work done in its process raised',
    'stopped': "it was ended at someone's word, or when its time ran out",
    'lost': 'its end was not seen: its supervisor died, the machine restarted, or it was adopted and so its exit status '
            'is not ours to read; it may be left again, watched once more or judged by its check',
}


def walk_mapping(by, owner):
    """mappings/walk-run.md as this tool writes it: the steps and reasons of STEPS, made by `by`, owned by `owner`."""
    q = json.dumps
    lines = [f'  - make: {{ by: {by}, at: now, note: "written by bin/run.py setup: the standard walk of a run" }}',
             f'  - own: {{ id: own, by: {owner}, of: self }}']
    for st, d in STEPS.items():
        roles = [f'id: {st}', f'as: {q(STEP_SAYS[st])}']
        if d.get('to'):
            roles.append(f"to: [{', '.join(d['to'])}]")
        walk = {k: ('"true"' if v is True else '[' + ', '.join(v) + ']') for k, v in d.items() if k != 'to'}
        if walk:
            roles.append('walk: { ' + ', '.join(f'{k}: {v}' for k, v in walk.items()) + ' }')
        lines.append(f"  - step: {{ {', '.join(roles)} }}")
    return ('---\nbean: walk-run\nkind: procedure\ntitle: "walk-run — how a run goes: every job a tool starts, from asked to '
            'ended"\nsummary: "The one walk every run shares (bin/run.py): queued, starting, running, perhaps stopping or '
            'paused, then done, failed, stopped or lost. What a run acts on is placed on this walk as a course, and each '
            'step it reaches is a move, by the machine or by who asked."\nstatements:\n' + '\n'.join(lines) +
            '\n---\n\nThe steps of a run, as bin/run.py holds them (`STEPS`). A course on this walk is a `be` of the being '
            'the run acts on, `as: order`, its id the run\'s id; its moves are kept in the store `runs` of the machine that '
            'ran it. `lost` is a way out that is not final: a run whose supervisor died may still be running, and '
            '`run.py reconcile --adopt` watches it again. A run adopted from outside begins at `running`, a move the walk '
            'does not offer, and its first move says why.\n')


def setup(root, by, owner):
    """The walk in this garden: written where it has none; where it has one, its steps and reasons checked against
    STEPS. Returns (path, what was done)."""
    p = os.path.join(root, 'mappings', 'walk-run.md')
    vocab = os.path.join(root, 'VOCAB.md')
    if not re.search(r'kind:\s*procedure\b', open(vocab, encoding='utf-8').read() if os.path.isfile(vocab) else ''):
        raise Refused('setup needs, first, the kind of a walk in VOCAB.md (a RULE-CHANGE, saved as one): '
                      'kinds: - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }', 2)
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write(walk_mapping(by, owner))
        return p, 'written: save it with its journal entry (bin/save.py)'
    from core import engine
    b = engine._bean(p, 'walk-run')
    have = {r.get('id'): r for _i, v, r in b.items if v == 'step'}
    differ = []
    for st, d in STEPS.items():
        r = have.get(st)
        if r is None:
            differ.append(f'{st}: missing')
            continue
        w = r.get('walk') or {}
        if list(r.get('to') or []) != d.get('to', []):
            differ.append(f"{st}: leads to {r.get('to')}, the standard to {d.get('to', [])}")
        for k in ('final', 'exit', 'resumes', 'machine'):
            if (str(w.get(k)) == 'true') != bool(d.get(k)):
                differ.append(f'{st}: {k}')
        if list(w.get('reasons') or []) != d.get('reasons', []):
            differ.append(f"{st}: reasons {w.get('reasons')}, the standard's {d.get('reasons', [])}")
    for st in have:
        if st not in STEPS:
            differ.append(f'{st}: a step the standard does not have')
    if differ:
        raise Refused(f'{p} differs from the standard walk: ' + '; '.join(differ), 1)
    return p, "the garden's walk is the standard's"


FINAL = {s for s, d in STEPS.items() if d.get('final')}
ENDED = FINAL | {'lost'}
EXIT = {'done': 0, 'failed': 1, 'stopped': 6, 'lost': 7}
CG_FREEZER = '/sys/fs/cgroup/freezer'
CG_ROOT = f'{CG_FREEZER}/daftar-runs'
KEYS = f'/tmp/.daftar-runs-{os.getuid()}/keys'        # fixed for the machine and the user: no environment moves it
SECRET_NAME = re.compile(r'pass(word|wd|phrase)?|secret|token|api[_-]?key|private[_-]?key|credential|auth', re.I)
SECRET_FLAG = re.compile(r'^--?[\w.-]*(pass(word|wd|phrase)?|secret|token|api[_-]?key|credential|auth)[\w.-]*$', re.I)
USERINFO = re.compile(r'(\b[a-z][\w+.-]*://)([^/@\s:]*):([^/@\s]*)@', re.I)
class Refused(Exception):
    """What a command would not do, and why: said, nothing changed. `code` is the exit code."""
    def __init__(self, msg, code=5):
        super().__init__(msg)
        self.code = code


class Busy(Refused):
    """The key is held: by `holder` (a Run), or by a process no registry here knows."""
    def __init__(self, key, holder=None, pids=()):
        who = f"run {holder.id} ({holder.label()}, {holder.step()})" if holder else \
            (f"a run this registry does not know (the lock was taken by pid {', '.join(map(str, pids))})" if pids
             else 'another run')
        super().__init__(f"key {key!r} is held by {who}", 3)
        self.key, self.holder = key, holder


# ---- the machine and its processes ----------------------------------------------------------------------------------
def boot_id():
    with open('/proc/sys/kernel/random/boot_id') as f:
        return f.read().strip()


BOOT = boot_id()
HZ = os.sysconf('SC_CLK_TCK')
HOST = os.environ.get('DAFTAR_HOST') or socket.gethostname().split('.')[0]
LOGIN = pwd.getpwuid(os.getuid()).pw_name


def stat(pid):
    """(state, ppid, pgrp, session, start ticks) from /proc/<pid>/stat, or None when there is no such process."""
    try:
        with open(f'/proc/{pid}/stat') as f:
            s = f.read()
    except OSError:
        return None
    f = s.rsplit(')', 1)[1].split()                     # fields from the 3rd on; the name may hold spaces or ')'
    return f[0], int(f[1]), int(f[2]), int(f[3]), int(f[19])


def ticks_of(pid):
    s = stat(pid)
    return s[4] if s else None


def ident(boot, pid, ticks):
    """alive | zombie | gone | reused | other-boot | none: whether (boot, pid, ticks) still names a process."""
    if not pid:
        return 'none'
    if boot != BOOT:
        return 'other-boot'
    s = stat(pid)
    if s is None:
        return 'gone'
    if s[4] != ticks:
        return 'reused'
    return 'zombie' if s[0] in ('Z', 'X') else 'alive'


def comm_of(pid):
    try:
        with open(f'/proc/{pid}/comm') as f:
            return f.read().strip()
    except OSError:
        return None


def uid_of(pid):
    try:
        return os.stat(f'/proc/{pid}').st_uid
    except OSError:
        return None


def started_at(ticks):
    """The wall-clock moment a process with these start ticks began, on this boot."""
    with open('/proc/uptime') as f:
        up = float(f.read().split()[0])
    return time.time() - up + ticks / HZ


def cmdline(pid):
    try:
        with open(f'/proc/{pid}/cmdline', 'rb') as f:
            return [a.decode('utf-8', 'replace') for a in f.read().split(b'\0')[:-1]]
    except OSError:
        return None


def pids():
    return [int(p) for p in os.listdir('/proc') if p.isdigit()]


def ancestry(pid=None):
    """This process and every process it was started from, up to init: what a search must never find."""
    out, p = set(), pid or os.getpid()
    while p and p not in out:
        out.add(p)
        s = stat(p)
        p = s[1] if s else 0
    return out


def descendants(root):
    kids = {}
    for p in pids():
        s = stat(p)
        if s:
            kids.setdefault(s[1], []).append(p)
    out, todo = [], [root]
    while todo:
        p = todo.pop()
        out.append(p)
        todo += kids.get(p, [])
    return out


def mask_argv(argv, secret_idx=()):
    """The command as it may be shown: a value after a flag whose name says secret, a value given as --x-password=v,
    a URL's userinfo and the positions named are each '***'."""
    out, hide = [], False
    for i, a in enumerate(argv):
        if hide or i in secret_idx:
            out.append('***')
            hide = False
            continue
        m = re.match(r'^(--?[\w.-]+=)(.*)$', a)
        if m and SECRET_FLAG.match(m.group(1)[:-1]):
            out.append(m.group(1) + '***')
            continue
        if SECRET_FLAG.match(a):
            hide = True
        out.append(USERINFO.sub(lambda m: m.group(1) + m.group(2) + ':***@', a))
    return out


def mask_env(env):
    return {k: ('***' if SECRET_NAME.search(k) else v) for k, v in env.items()}


def moment(t):
    """An epoch time as the law writes a moment: local, to the second, with its offset."""
    s = time.strftime('%Y-%m-%dT%H:%M:%S%z', time.localtime(t))
    return s[:-2] + ':' + s[-2:]


def registry_path():
    return os.environ.get('DAFTAR_RUNS') or os.path.expanduser('~/.local/state/daftar-runs')


# ---- cgroups: a run's processes kept together, frozen while they are signalled -------------------------------------
def cgroup_root():
    """The delegated freezer cgroup, made at first use; None where there is none (then a run is its own session)."""
    if os.environ.get('DAFTAR_RUNS_NO_CGROUP') or not os.path.isdir(CG_FREEZER):
        return None
    if not (os.path.isdir(CG_ROOT) and os.access(CG_ROOT, os.W_OK)):
        me = f'{os.getuid()}:{os.getgid()}'
        files = [f'{CG_ROOT}/{f}' for f in ('cgroup.procs', 'tasks', 'freezer.state', 'cgroup.clone_children',
                                             'notify_on_release')]
        r = subprocess.run(['sudo', '-n', 'sh', '-c', 'mkdir -p "$1" && shift && chown "$@"', 'sh', CG_ROOT, me,
                            CG_ROOT, *files], capture_output=True, timeout=30)
        if r.returncode or not os.access(CG_ROOT, os.W_OK):
            return None
    for d in ('shims',):
        os.makedirs(f'{CG_ROOT}/{d}', exist_ok=True)
    return CG_ROOT


def cg_join(cg, pid=0):
    with open(f'{cg}/cgroup.procs', 'w') as f:
        f.write(str(pid))


def cg_procs(cg):
    try:
        with open(f'{cg}/cgroup.procs') as f:
            return [int(x) for x in f.read().split()]
    except OSError:
        return []


def cg_freeze(cg, state):
    """FROZEN or THAWED, waited for (bounded: a process in uninterruptible sleep can hold FREEZING a while)."""
    try:
        with open(f'{cg}/freezer.state', 'w') as f:
            f.write(state)
        for _ in range(40):
            with open(f'{cg}/freezer.state') as f:
                if f.read().strip() == state:
                    return True
            time.sleep(0.05)
    except OSError:
        pass
    return False


def send(targets, sig):
    """Signal processes already proved to be the run's: our own directly, another user's (root, bench) through sudo."""
    mine = [p for p in targets if uid_of(p) == os.getuid()]
    others = [p for p in targets if p not in mine and uid_of(p) is not None]
    for p in mine:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.kill(p, sig)
    if others:
        subprocess.run(['sudo', '-n', 'kill', '-s', signal.Signals(sig).name[3:], '--', *map(str, others)],
                       capture_output=True, timeout=30)


def members(c):
    """The pids that are the run now: its cgroup's, or its session's where it has no cgroup."""
    if c['cgroup']:
        return cg_procs(c['cgroup'])
    if not c['pid'] or ident(c['boot'], c['pid'], c['ticks']) == 'reused':
        return []
    out = []
    for p in pids():
        s = stat(p)
        if s and s[3] == c['pid']:
            out.append(p)
    if c['mode'] == 'adopted':                          # an adopted process's own tree, by parentage
        out = sorted(set(out) | set(descendants(c['pid'])))
    return out


def signal_run(c, sig):
    """Every member of the run, and nothing else: frozen while they are listed and signalled, so none can exit and
    have its pid taken by another process in between."""
    cg = c['cgroup']
    if cg:
        cg_freeze(cg, 'FROZEN')
        try:
            send(cg_procs(cg), sig)
        finally:
            cg_freeze(cg, 'THAWED')
    else:
        send(members(c), sig)


# ---- keys: kernel locks, one per key, for every registry on the machine -----------------------------------------------
def key_path(key):
    os.makedirs(KEYS, mode=0o700, exist_ok=True)
    return f"{KEYS}/{hashlib.sha256(key.encode()).hexdigest()[:32]}.lock"


def key_take(key, block=False):
    """An open fd holding the key's lock, or None if another holds it. Whoever holds the fd (or a copy) holds the key."""
    fd = os.open(key_path(key), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | (0 if block else fcntl.LOCK_NB))
    except BlockingIOError:
        os.close(fd)
        return None
    os.ftruncate(fd, 0)
    os.write(fd, key.encode() + b'\n')
    return fd


def key_holders(key):
    """The pids /proc/locks names for the key's lock: the process that TOOK it, which may have handed it on and gone
    (the lock lives while any copy of its file description is open: the supervisor's, the process's, sudo's)."""
    try:
        ino = os.stat(key_path(key)).st_ino
        with open('/proc/locks') as f:
            return sorted({int(l.split()[4]) for l in f if l.split()[1] == 'FLOCK' and
                           int(l.split()[5].split(':')[2]) == ino})
    except (OSError, IndexError, ValueError):
        return []


# ---- the registry -----------------------------------------------------------------------------------------------------
COLUMNS = ('id', 'walk', 'being', 'host', 'name', 'key', 'parent', 'asked_by', 'mode', 'argv', 'cwd', 'env', 'user',
           'login', 'dir', 'log', 'progress', 'check_cmd', 'needs', 'timeout', 'grace', 'stdin', 'notify', 'boot', 'pid',
           'ticks', 'comm', 'shim_pid', 'shim_ticks', 'cgroup', 'exit_code', 'signal', 'result', 'inputs', 'stop_by',
           'stop_why', 'created')


def moment_ms(t):
    """An epoch time as a moment to the millisecond, local, with its offset: two moves within one second keep their
    order."""
    s = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(t)) + f'.{int(round(t * 1000)) % 1000:03d}'
    z = time.strftime('%z', time.localtime(t))
    return s + z[:-2] + ':' + z[-2:]


def epoch(m):
    import datetime
    return datetime.datetime.fromisoformat(m).timestamp()


class Registry:
    """The runs registry: the store `runs` (bin/store.py). A course's columns are its detail `runs.<run>` on the being
    it acts on, beside its statements; its moves are `move` statements, read in the order of their moments."""

    FILE = 'store.sqlite'

    def __init__(self, path=None, write=True):
        self.path = path or registry_path()
        f = f'{self.path}/{self.FILE}'
        if write:
            os.makedirs(self.path, exist_ok=True)
        self.S = dmstore.Store(f, root=ROOT, readers=['others'], readonly=not write, name='runs')
        self.write = write
        self._where = {}
        if write:
            with self.tx():
                self.S.being(HOST, 'host') if not self.S.has_bean(HOST) else self.S.being(HOST)

    @contextlib.contextmanager
    def tx(self):
        with self.S.batch():
            yield

    def _being_of(self, rid):
        b = self._where.get(rid)
        if b is None and 'be' in self.S.verbs():
            r = self.S.db.execute('SELECT b.id FROM v_be s JOIN being b ON b.n = s.being WHERE s.id = ?', (rid,)).fetchone()
            if r:
                b = self._where[rid] = r[0]
        return b

    def _detail(self, being, rid):
        r = self.S.db.execute('SELECT d.value FROM detail d JOIN being b ON b.n = d.being WHERE b.id = ? AND d.key = ?',
                              (being, f'runs.{rid}')).fetchone()
        return json.loads(r[0]) if r else None

    def course(self, rid):
        b = self._being_of(rid)
        d = self._detail(b, rid) if b else None
        if d is None:
            return None
        return {**{k: None for k in COLUMNS}, **d, 'id': rid, 'being': b}

    def add(self, **cols):
        """A course: the run's act, its `be` on the walk, and its columns as its being's detail."""
        rid, being = cols['id'], cols['being']
        with self.tx():
            self.S.being(being)
            self.S.put(being, 'make', {'id': f'{rid}-made', 'by': HOST, 'at': moment_ms(cols['created'])}, judge=False)
            note = cols.get('name') or ' '.join(json.loads(cols.get('argv') or '[]')[:3])[:120] or rid
            self.S.put(being, 'be', {'id': rid, 'by': being, 'at': WALK, 'as': 'order', 'note': note},
                       act=f'{being}#{rid}-made', judge=False)
            self.S.detail(being, f'runs.{rid}', {k: v for k, v in cols.items() if k not in ('id', 'being')})
            self._where[rid] = being

    def moves(self, rid):
        b = self._being_of(rid)
        if b is None or 'move' not in self.S.verbs():
            return []
        out = []
        cols = self.S.columns('move')
        for n, at, by_n, by_t, reason, why in self.S.db.execute(
                f"SELECT n, {cols['at'][1]}, {cols['by'][0]}, {cols['by'][1]}, {cols['as'][1]}, c_why FROM v_move "
                f"WHERE {cols['through'][1]} = ? ORDER BY n", (f'{b}#{rid}',)):
            pos = json.loads(at) if isinstance(at, (bytes, str)) and str(at[:1] if isinstance(at, str) else at[:1].decode()) == '[' else [at]
            m, step = pos[0], str(pos[1]).split('#', 1)[1] if len(pos) > 1 else None
            who = self.S._id_of(by_n) if by_n is not None else by_t
            if who is None and why and why.startswith('by '):      # an asker the garden holds no being of
                who, _, rest = why[3:].partition(': ')
                why = rest or None
            out.append({'course': rid, 'at': epoch(m), 'step': step, 'by': who or HOST, 'reason': reason, 'why': why,
                        'n': n})
        out.sort(key=lambda x: (x['at'], x['n']))
        return out

    def last(self, rid):
        mv = self.moves(rid)
        return mv[-1] if mv else None

    def move(self, rid, step, by, reason=None, why=None):
        """A move is kept, never rewritten; a course's moments never go back."""
        assert step in STEPS and (reason is None or reason in STEPS[step].get('reasons', ())), (step, reason)
        at = time.time()
        b = self._being_of(rid)
        with self.tx():
            prev = self.last(rid)
            if prev is not None and at <= prev['at']:
                at = prev['at'] + 0.001
            roles = {'of': b, 'through': f'{b}#{rid}', 'at': [moment_ms(at), f'{WALK}#{step}']}
            if by and (self.S.has_bean(by) or self.S.kind_of(by)):
                roles['by'] = by
            elif by:                                     # who asked, where the garden holds no being of them
                why = f'by {by}' + (f': {why}' if why else '')
            if reason:
                roles['as'] = reason
            if why:
                roles['why'] = why
            self.S.put(b, 'move', roles, act=f'{b}#{rid}-made', judge=False)
        return at

    def set(self, rid, **kw):
        b = self._being_of(rid)
        with self.tx():
            d = self._detail(b, rid) or {}
            d.update(kw)
            self.S.detail(b, f'runs.{rid}', d)

    def ids(self, where='1', args=()):
        """The runs whose columns match `where` — `1`, or conditions joined by AND, each `<column> = ?` or `<column> LIKE
        ?` (as SQL's: `%` any run of characters, `_` one, ASCII letters in either case), `?` the next of `args` or a
        `'<word>'` written in place — oldest first."""
        conds, it = [], iter(args)
        for c in ([] if where.strip() == '1' else where.split(' AND ')):
            m = re.match(r"^\s*(\w+)\s+(=|LIKE)\s+(\?|'[^']*')\s*$", c, re.I)
            if not m:
                raise Refused(f'no condition of the registry: {c!r} (`<column> = ?` or `<column> LIKE ?`)', 2)
            col, op, val = m.group(1), m.group(2).upper(), m.group(3)
            val = next(it) if val == '?' else val[1:-1]
            if op == 'LIKE':
                rx = re.compile('^' + ''.join('.*' if ch == '%' else '.' if ch == '_' else re.escape(ch)
                                              for ch in str(val)) + '$', re.I | re.S)
                conds.append((col, lambda x, rx=rx: x is not None and bool(rx.match(str(x)))))
            else:
                conds.append((col, lambda x, v=val: x == v))
        rows = []
        for being, key, value in self.S.db.execute("SELECT b.id, d.key, d.value FROM detail d JOIN being b ON "
                                                   "b.n = d.being WHERE d.key LIKE 'runs.%'"):
            d = json.loads(value)
            d['id'], d['being'] = key[5:], being
            if all(ok(d.get(c)) for c, ok in conds):
                rows.append(d)
        rows.sort(key=lambda d: (d.get('created') or 0, d['id']))
        for d in rows:
            self._where.setdefault(d['id'], d['being'])
        return [d['id'] for d in rows]


def mint():
    return f"run-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(2)}"


class Run:
    """One run, read from the registry each time it is asked."""

    def __init__(self, rid, reg=None):
        self.reg = reg or Registry()
        self.id = rid
        if self.reg.course(rid) is None:
            raise Refused(f'no run {rid} in {self.reg.path}', 4)

    @property
    def c(self):
        return self.reg.course(self.id)

    def __repr__(self):
        return f'<Run {self.id} {self.step()}>'

    def label(self):
        c = self.c
        return c['name'] or os.path.basename(json.loads(c['argv'] or '["?"]')[0])

    def step(self):
        m = self.reg.last(self.id)
        return m['step'] if m else None

    def ended(self):
        return self.step() in FINAL

    def process(self):
        c = self.c
        return ident(c['boot'], c['pid'], c['ticks'])

    def supervisor(self):
        c = self.c
        if c['mode'] == 'task':                          # a task's supervisor is the process it runs in
            return ident(c['boot'], c['pid'], c['ticks'])
        return ident(c['boot'], c['shim_pid'], c['shim_ticks'])

    def poll(self):
        """None while it has not ended; else what a Popen's returncode would say: the exit code, -signal, or 1."""
        st = self.step()
        if st not in ENDED or (st == 'lost' and self.process() == 'alive'):
            return None                                   # lost to its supervisor, but its process still works
        c = self.c
        if st == 'done':
            return 0
        if c['signal']:
            return -c['signal']
        return c['exit_code'] if c['exit_code'] not in (None, 0) else 1

    returncode = property(poll)

    def wait(self, timeout):
        """Until it ends, or `timeout` seconds: its end step, or None. A pidfd where the process is ours to see, the
        registry beside it (the end move is the supervisor's to write)."""
        end = time.time() + timeout
        c = self.c
        fd = None
        if self.process() == 'alive':
            with contextlib.suppress(OSError):
                fd = os.pidfd_open(c['pid'])
                if ticks_of(c['pid']) != c['ticks']:
                    os.close(fd)
                    fd = None
        try:
            while True:
                st = self.step()
                if st in ENDED and not (st == 'lost' and self.supervisor() == 'alive'):
                    return st
                left = end - time.time()
                if left <= 0:
                    return None
                if fd is not None:
                    if select.select([fd], [], [], min(left, 0.5))[0]:
                        os.close(fd)
                        fd = None
                else:
                    time.sleep(min(left, 0.2))
                if self.supervisor() not in ('alive', 'zombie') and self.step() not in ENDED:
                    reconcile_one(self)                   # nobody is left to write its end: say so, once
        finally:
            if fd is not None:
                os.close(fd)

    def stop(self, why=None, by=None, grace=None, tree=False, timeout=60):
        return stop(self, why=why, by=by, grace=grace, tree=tree, timeout=timeout)

    def progress(self):
        return progress_of(self.c['progress'])

    def tail(self, n=20):
        return tail_lines(self.c['log'], n)

    def children(self):
        return [Run(i, self.reg) for i in self.reg.ids('parent = ?', (self.id,))]


def get(ref, reg=None):
    return Run(ref, reg)


def one(reg, rid=None, name=None, key=None, live=True):
    """Exactly one run: by its id, or by a whole name or key among the runs that have not ended."""
    if rid:
        return Run(rid, reg)
    col, val = ('name', name) if name else ('key', key)
    hits = [i for i in reg.ids(f'{col} = ?', (val,)) if not live or Run(i, reg).step() not in FINAL]
    if len(hits) != 1:
        raise Refused(f"{col} {val!r} names {len(hits)} run(s) that have not ended" +
                      (f": {', '.join(hits)} — give the id" if hits else ''), 4)
    return Run(hits[0], reg)


HOLDING = ('starting', 'running', 'stopping', 'paused')


def holder(key, reg=None):
    """The run that holds the key, if this registry knows it: what a restarted tool watches instead of starting a
    second one. A run still queued for the key does not hold it; a lost run whose process still runs does."""
    reg = reg or Registry()
    for i in reversed(reg.ids('key = ?', (key,))):
        r = Run(i, reg)
        st = r.step()
        if (st in HOLDING and (r.process() in ('alive', 'zombie') or r.supervisor() == 'alive')) or \
                (st == 'lost' and r.process() == 'alive'):
            return r
    return None


# ---- starting ---------------------------------------------------------------------------------------------------------
def start(argv=None, *, script=None, name=None, of=None, key=None, cwd=None, env=None, pass_env=(), clean_env=False,
          user=None, timeout=None, grace=10, check=None, needs=(), progress=None, parent=None, by=None, log=None,
          stdin=None, wait_key=False, notify=False, secret_args=(), reg=None, ready=30):
    """Start a run; returns it once its process runs (or it has failed to start, or waits for its key)."""
    reg = reg or Registry()
    if not argv and not script:
        raise Refused('nothing to run: a command after --, or --script', 2)
    rid = mint()
    d = f'{reg.path}/{rid}'
    if script is not None:                                # run from a file: nothing inside can read the rest of it
        argv = ['bash', f'{d}/script']
    env = dict(env or {})
    for n in pass_env:
        if n not in os.environ:
            raise Refused(f'--pass {n}: not set in the environment that asked', 2)
        env[n] = os.environ[n]
    child = {k: os.environ[k] for k in ('PATH', 'HOME', 'LANG', 'USER', 'LOGNAME') if k in os.environ} \
        if clean_env else dict(os.environ)
    child.update(env)
    prog = os.path.abspath(progress) if progress else f'{d}/progress.json'
    parent = parent or os.environ.get('DAFTAR_RUN') or None
    child.update(DAFTAR_RUN=rid, DAFTAR_RUN_PROGRESS=prog, DAFTAR_RUNS=reg.path)
    by = by or os.environ.get('DAFTAR_BY') or LOGIN
    fd = None
    with reg.tx():
        if key:
            h = holder(key, reg)
            if h and not wait_key:
                raise Busy(key, h)
            fd = None if h else key_take(key)
            if fd is None and not wait_key:
                raise Busy(key, None, key_holders(key))
        os.makedirs(d)
        if script is not None:
            with open(f'{d}/script', 'w') as f:
                f.write(script)
        reg.add(**dict(zip(('id', 'walk', 'being', 'host', 'name', 'key', 'parent', 'asked_by', 'mode', 'argv', 'cwd', 'env', 'user', 'login', 'dir', 'log', 'progress', 'check_cmd', 'needs', 'timeout', 'grace', 'stdin', 'notify', 'created'),
            (rid, WALK, of or HOST, HOST, name, key, parent, by, 'process', json.dumps(mask_argv(argv, secret_args)),
             os.path.abspath(cwd) if cwd else os.getcwd(), json.dumps(mask_env(env)), user, LOGIN, d,
             os.path.abspath(log) if log else f'{d}/log', prog, check, json.dumps(list(needs)), timeout, grace,
             os.path.abspath(stdin) if stdin else None, int(bool(notify)), time.time()))))
        holding = f'; waits for key {key!r}' if key and fd is None else ''
        reg.move(rid, 'queued', by, why=f'asked on {HOST} by {LOGIN}{holding}')
    # the real command line, unmasked, goes to the supervisor through a file only it reads, and is then removed
    with open(os.open(f'{d}/.argv', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as f:
        json.dump(argv, f)
    try:
        cmd = [sys.executable, '-I', ME, '_shim', rid] + (['--lockfd', str(fd)] if fd is not None else []) + \
              (['--wait-key', key] if key and fd is None else [])
        with open(f'{d}/shim.log', 'ab') as sl:
            subprocess.run(cmd, env=child, stdin=subprocess.DEVNULL, stdout=sl, stderr=sl, cwd='/',
                           pass_fds=(fd,) if fd is not None else (), timeout=30, check=True)
    finally:
        if fd is not None:
            os.close(fd)                                  # the supervisor has its own copy now
    r = Run(rid, reg)
    end = time.time() + ready
    waits = bool(key) and fd is None                      # queued for its key: back at once, its supervisor up
    while time.time() < end and (r.c['shim_pid'] is None or (not waits and r.step() in ('queued', 'starting'))):
        time.sleep(0.02)
    return r


# ---- the supervisor ---------------------------------------------------------------------------------------------------
def shim(rid, lockfd=None, wait_key=None, watch=False):
    """One run's supervisor (`_shim`): forks away from whoever started it, then starts the process (or, adopted,
    watches it), holds it, and writes its moves until it ends."""
    if os.fork():
        os._exit(0)                                       # the asker waits for this one only: no zombie left behind
    os.setsid()
    reg = Registry()
    c = reg.course(rid)
    cgr = cgroup_root()
    if cgr:
        with contextlib.suppress(OSError):
            cg_join(f'{cgr}/shims')                       # out of the asker's cgroup: stopping the asker spares this
    reg.set(rid, shim_pid=os.getpid(), shim_ticks=ticks_of(os.getpid()), boot=BOOT)
    flags = {'stop': False, 'pause': None}
    rp, wp = os.pipe()
    for p in (rp, wp):
        os.set_blocking(p, False)
    signal.set_wakeup_fd(wp)
    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(s, lambda *_: flags.__setitem__('stop', True))
    signal.signal(signal.SIGUSR1, lambda *_: flags.__setitem__('pause', True))
    signal.signal(signal.SIGUSR2, lambda *_: flags.__setitem__('pause', False))
    try:
        if wait_key:
            while lockfd is None:
                if flags['stop']:
                    reg.move(rid, 'stopped', reg.course(rid)['stop_by'] or HOST, 'asked',
                             reg.course(rid)['stop_why'] or 'stopped while it waited for its key')
                    return
                lockfd = key_take(wait_key)
                if lockfd is None:
                    time.sleep(0.5)
        if watch:
            supervise(reg, rid, None, flags, rp, lockfd)
            return
        reg.move(rid, 'starting', HOST)
        cg = None
        if cgr:
            cg = f'{cgr}/{rid}'
            os.makedirs(cg, exist_ok=True)
        reg.set(rid, cgroup=cg)
        with open(f"{c['dir']}/.argv") as f:
            argv = json.load(f)
        os.remove(f"{c['dir']}/.argv")
        if c['user'] and c['user'] != LOGIN:              # another user: through sudo, the named variables kept
            keep = sorted(set(json.loads(c['env'] or '{}')) | {'DAFTAR_RUN', 'DAFTAR_RUN_PROGRESS', 'DAFTAR_RUNS'})
            argv = ['sudo', '-n'] + ([] if c['user'] == 'root' else ['-u', c['user'], '-H']) + \
                   [f"--preserve-env={','.join(keep)}", '--'] + argv
        logf = open(c['log'], 'ab')
        inp = open(c['stdin'], 'rb') if c['stdin'] else subprocess.DEVNULL
        try:
            p = subprocess.Popen(argv, cwd=c['cwd'], stdin=inp, stdout=logf, stderr=subprocess.STDOUT,
                                 start_new_session=True, preexec_fn=(lambda: cg_join(cg)) if cg else None,
                                 pass_fds=(lockfd,) if lockfd is not None else ())
        except (OSError, subprocess.SubprocessError) as e:
            reg.move(rid, 'failed', HOST, 'start-failed', f'{type(e).__name__}: {e}')
            tell(reg.course(rid), 'failed', f'could not start: {e}')
            return
        reg.set(rid, pid=p.pid, ticks=ticks_of(p.pid), comm=os.path.basename(argv[0]))
        reg.move(rid, 'running', HOST, why=f'pid {p.pid}' + (f', cgroup {os.path.basename(cg)}' if cg else ''))
        supervise(reg, rid, p, flags, rp, lockfd)
    except Exception as e:                                # the supervisor's own fault: said, never silent
        print(f'{time.strftime("%F %T")} supervisor: {type(e).__name__}: {e}', file=sys.stderr, flush=True)
        raise


def supervise(reg, rid, p, flags, rp, lockfd):
    c = reg.course(rid)
    pid = c['pid']
    pidfd = os.pidfd_open(pid)
    if ticks_of(pid) != c['ticks']:                       # adopted, and gone before the pidfd was taken
        os.close(pidfd)
        reg.move(rid, 'lost', HOST, 'exit-unseen', 'it had ended before it could be watched')
        return
    poll = select.poll()
    poll.register(pidfd, select.POLLIN)
    poll.register(rp, select.POLLIN)
    needs = json.loads(c['needs'] or '[]')
    began, stopping, kill_at, why_end, last_probe = time.time(), None, None, None, 0
    named = False
    while True:
        ev = dict(poll.poll(1000))
        with contextlib.suppress(OSError):
            os.read(rp, 4096)
        if pidfd in ev:
            break
        now = time.time()
        if not named and p is not None and now - began > 0.5:
            named = True                                  # its name once it has exec'd, not the supervisor's fork
            reg.set(rid, comm=comm_of(pid) or c['comm'])
        if stopping is None:
            if flags['stop']:
                cc = reg.course(rid)
                stopping, why_end = 'asked', cc['stop_why']
                reg.move(rid, 'stopping', cc['stop_by'] or HOST, why=cc['stop_why'])
            elif c['timeout'] and now - began > c['timeout']:
                stopping, why_end = 'timeout', f"its time ran out: {c['timeout']:g} s"
                reg.move(rid, 'stopping', HOST, why=why_end)
            elif needs and now - last_probe >= 1:
                last_probe = now
                gone = [n for n in needs if not os.path.exists(n)]
                if gone:
                    stopping, why_end = 'resource-gone', f"what it needs is gone: {', '.join(gone)}"
                    reg.move(rid, 'stopping', HOST, why=why_end)
            if stopping:
                cc = reg.course(rid)                      # the grace a stop asked for, read now
                signal_run(cc, signal.SIGTERM)
                kill_at = now + (cc['grace'] if cc['grace'] is not None else 10)
            elif flags['pause'] is not None:
                cg = reg.course(rid)['cgroup']
                if cg and cg_freeze(cg, 'FROZEN' if flags['pause'] else 'THAWED'):
                    reg.move(rid, 'paused' if flags['pause'] else 'running', reg.course(rid)['stop_by'] or HOST,
                             'asked' if flags['pause'] else None)
                flags['pause'] = None
        elif kill_at and now > kill_at:
            signal_run(reg.course(rid), signal.SIGKILL)
            kill_at = now + 5
    rc = p.wait() if p is not None else None
    os.close(pidfd)
    cc = reg.course(rid)
    left = [x for x in members(cc) if x != pid]
    names = sorted({comm_of(x) or '?' for x in left})
    if left:                                              # what it left behind is still the run's: ended with it
        # (sudo's PAM session starts a gnome-keyring-daemon here, which would linger a minute or two on its own)
        signal_run(cc, signal.SIGTERM)
        for _ in range(30):
            if not [x for x in members(cc) if x != pid]:
                break
            time.sleep(0.1)
        else:
            signal_run(cc, signal.SIGKILL)
    result = {'leftovers': len(left), 'left_names': names} if left else {}
    if rc is None and stopping and stopping != 'resource-gone':   # adopted, and ended because it was asked to
        step, reason, why = 'stopped', stopping, (why_end + '; ' if why_end else '') + \
            'it was adopted, so its exit status was not seen'
    elif rc is None:                                      # adopted: watched, never its parent, so no exit status
        step, reason, why = ('failed', 'resource-gone', why_end) if stopping else \
            ('lost', 'exit-unseen', 'it ended; it was adopted, so its exit status was not seen')
    elif stopping == 'resource-gone':
        step, reason, why = 'failed', 'resource-gone', why_end
    elif stopping:                                        # ended at a word or by its time, however cleanly it left
        step, reason, why = 'stopped', stopping, (why_end + '; ' if why_end else '') + \
            (f'exit {rc}' if rc >= 0 else f'ended by {signal.Signals(-rc).name}')
    elif rc == 0:
        step, reason, why = 'done', None, 'exit 0'
    elif rc < 0:
        step, reason, why = 'failed', 'signal', f'killed by {signal.Signals(-rc).name}'
    else:
        step, reason, why = 'failed', 'exit-code', f'exit {rc}'
    if c['check_cmd'] and step in ('done', 'lost'):     # the end read from the world, not from the exit code
        k = subprocess.run(['bash', '-c', c['check_cmd']], cwd=c['cwd'], stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, encoding='utf-8', timeout=600)
        result['check'] = {'exit': k.returncode, 'said': (k.stdout + k.stderr).strip()[-300:]}
        if k.returncode == 0:
            step, reason, why = 'done', None, why + '; its check held'
        else:
            step, reason, why = 'failed', 'check-failed', f"{why}; its check did not hold: {result['check']['said'] or k.returncode}"
    reg.set(rid, exit_code=rc if rc is not None and rc >= 0 else None, signal=-rc if rc and rc < 0 else None,
            result=json.dumps(result) if result else None)
    if left:
        why += f"; {len(left)} process(es) it left behind ({', '.join(names)}) ended with it"
    reg.move(rid, step, HOST, reason, why)
    if cc['cgroup']:
        with contextlib.suppress(OSError):
            os.rmdir(cc['cgroup'])
    if lockfd is not None:
        os.close(lockfd)
    tell(reg.course(rid), step, why, reason)


NOTICE_EVERY = float(os.environ.get('DAFTAR_RUNS_NOTICE_EVERY', 1800))   # seconds between two notices of one run name


def throttled(c, step):
    """None where a notice of this run's name and step may be told now; else how many were held back since the last.
    A watcher whose pass fails every minute tells the desktop once in each window, not sixty times (`notices.json`
    beside the registry: per name and step, when the last was told and how many have been held back since)."""
    path = os.path.join(registry_path(), 'notices.json')
    key = f"{c['name'] or c['key'] or c['id']}|{step}"
    with contextlib.suppress(OSError), open(path, 'a+') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        try:
            d = json.loads(fh.read() or '{}')
        except ValueError:
            d = {}
        last = d.get(key) or {}
        now = time.time()
        if now - last.get('t', 0) < NOTICE_EVERY:
            last['held'] = last.get('held', 0) + 1
            d[key] = last
            held = last['held']
        else:
            held = None
            d[key] = {'t': now, 'held': 0, 'before': last.get('held', 0)}
        fh.seek(0)
        fh.truncate()
        fh.write(json.dumps(d))
        return held, (d[key].get('before') or 0)
    return None, 0


def tell(c, step, why, reason=None):
    """A failure, a run lost, or an end asked for (`--notify`), told to the desktop; kept until dismissed. One notice
    of a run's name and step in each window (NOTICE_EVERY), the next one saying how many were held back."""
    if os.environ.get('DAFTAR_RUNS_QUIET') or not (step in ('failed', 'lost') or reason == 'timeout' or c['notify']):
        return
    held, before = throttled(c, step)
    if held is not None:
        return
    if before:
        why = f'{why}\n({before} more {step} of {c["name"] or c["id"]} held back since the last notice)'
    env = dict(os.environ)
    r = subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'plasmashell'], capture_output=True, text=True, encoding='utf-8')
    for pid in r.stdout.split()[:1]:                      # the running desktop's bus, not an older session's
        with contextlib.suppress(OSError):
            for kv in open(f'/proc/{pid}/environ', 'rb').read().split(b'\0'):
                k, _, v = kv.decode(errors='replace').partition('=')
                if k in ('DBUS_SESSION_BUS_ADDRESS', 'DISPLAY', 'XAUTHORITY'):
                    env[k] = v
    name = c['name'] or c['id']
    subprocess.run(['notify-send', '-a', 'Runs', '-i', 'system-run', '-t', '0',
                    '-u', 'critical' if step in ('failed', 'lost') else 'normal',
                    f'{name}: {step}' + (f' ({reason})' if reason else ''), f"{why}\n{c['id']} on {c['host']}"],
                   env=env, capture_output=True, timeout=30)


# ---- tasks: work done in the asking process itself -------------------------------------------------------------------
class Task:
    """Work done in this process, as a run: its owner is this process, so a dead owner is a lost run. Ended by
    `done()` or `fail()`, or by leaving `with task(...)`; a lease (`begin`) is ended by its tool when it says so."""

    def __init__(self, reg, rid, path, fd=None):
        self.reg, self.id, self.path, self.fd = reg, rid, path, fd

    def progress(self, **kw):
        write_progress(self.path, kw)

    def step(self):
        return self.reg.last(self.id)['step']

    def _end(self, step, reason, why):
        if self.step() in ENDED:
            return
        self.reg.move(self.id, step, HOST, reason, why)
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        tell(self.reg.course(self.id), step, why or '', reason)

    def done(self, why=None):
        self._end('done', None, why)

    def fail(self, reason='raised', why=None):
        self._end('failed', reason, why)

    def stopped(self, why=None):
        self._end('stopped', 'asked', why)


def lease(rid, reg=None):
    """A lease begun earlier by this process, by its id (as a tool keeps it in its own state)."""
    reg = reg or Registry()
    c = reg.course(rid)
    if c is None or c['mode'] != 'task':
        raise Refused(f'no task {rid}', 4)
    return Task(reg, rid, c['progress'])


def begin(name, *, of=None, key=None, inputs=None, by=None, parent=None, reg=None):
    """A task begun now and ended later by its tool (`done`, `fail`): a lease on a disk held from its mount to its
    power-off, say. Its key, if any, is held by this process until it ends."""
    reg = reg or Registry()
    rid = mint()
    d = f'{reg.path}/{rid}'
    by = by or os.environ.get('DAFTAR_BY') or LOGIN
    me = os.getpid()
    fd = None
    with reg.tx():
        if key:
            h = holder(key, reg)
            if h:
                raise Busy(key, h)
            fd = key_take(key)
            if fd is None:
                raise Busy(key, None, key_holders(key))
        os.makedirs(d)
        reg.add(**dict(zip(('id', 'walk', 'being', 'host', 'name', 'key', 'parent', 'asked_by', 'mode', 'argv', 'cwd', 'user', 'login', 'dir', 'log', 'progress', 'inputs', 'boot', 'pid', 'ticks', 'comm', 'shim_pid', 'shim_ticks', 'created'),
            (rid, WALK, of or HOST, HOST, name, key, parent or os.environ.get('DAFTAR_RUN'), by, 'task',
             json.dumps(mask_argv(sys.argv)), os.getcwd(), LOGIN, LOGIN, d, None, f'{d}/progress.json',
             json.dumps(inputs) if inputs is not None else None, BOOT, me, ticks_of(me), comm_of(me), me,
             ticks_of(me), time.time()))))
        reg.move(rid, 'queued', by)
    reg.move(rid, 'starting', HOST)
    reg.move(rid, 'running', HOST, why=f'in process {me}')
    return Task(reg, rid, f'{d}/progress.json', fd)


@contextlib.contextmanager
def task(name, **kw):
    """A pass, a copy, a step done in this process: a run all the same. An exception ends it `failed` (raised) and
    goes on up; leaving it otherwise ends it `done`, unless it was ended inside."""
    t = begin(name, **kw)
    try:
        yield t
    except BaseException as e:
        t.fail('raised', f'{type(e).__name__}: {e}'[:300])
        raise
    else:
        t.done()


def passes(inputs, do_pass, *, name, of=None, key=None, every=30, stop=lambda: False, reg=None):
    """A watcher: a pass whenever what it reads changes. What the next pass is judged against is what this pass USED,
    read once before it began — never read again after it, when something that came during the pass would be taken
    for done. Each pass is a task run that records its inputs."""
    last = None
    while not stop():
        now = inputs()
        if now != last:
            try:
                with task(f'{name} pass', of=of, key=key, inputs=now, reg=reg) as t:
                    do_pass(now, t)
                last = now
            except Exception as e:                        # the pass is failed (raised) on its run; tried again
                print(f"{time.strftime('%H:%M:%S')} {name}: a pass failed: {type(e).__name__}: {e}", file=sys.stderr,
                      flush=True)
        for _ in range(int(every * 10)):
            if stop():
                break
            time.sleep(0.1)


# ---- stopping, adopting, finding --------------------------------------------------------------------------------------
def stop(r, why=None, by=None, grace=None, tree=False, timeout=60):
    """Stop the run, all of it and nothing else. Refused when its process is not the run's any more."""
    by = by or os.environ.get('DAFTAR_BY') or LOGIN
    reg = r.reg
    if tree:
        for k in r.children():
            if k.step() not in ENDED:
                stop(k, why=why or f'its parent {r.id} was stopped', by=by, grace=grace, tree=True, timeout=timeout)
    st = r.step()
    c = r.c
    if st in FINAL:
        return st
    if c['mode'] == 'task':
        raise Refused(f"{r.id} is a task done inside process {c['pid']}: stop the run that process is", 5)
    proc, sup = r.process(), r.supervisor()
    if proc == 'reused':
        if st != 'lost':
            reg.move(r.id, 'lost', HOST, 'supervisor-gone' if sup != 'alive' else 'exit-unseen',
                     f"pid {c['pid']} is now another process: nothing was signalled")
        when = lambda t: time.strftime('%F %T', time.localtime(started_at(t)))
        raise Refused(f"refused: pid {c['pid']} is now another process (started {when(ticks_of(c['pid']) or 0)}), "
                      f"not the run's (started {when(c['ticks'])}): nothing was signalled", 5)
    if sup == 'alive' and c['shim_pid']:
        reg.set(r.id, stop_by=by, stop_why=why, **({'grace': grace} if grace is not None else {}))
        fd = os.pidfd_open(c['shim_pid'])                 # held first, then proved: the signal reaches that process
        try:
            if ticks_of(c['shim_pid']) != c['shim_ticks']:
                raise Refused(f"refused: the supervisor's pid {c['shim_pid']} is another process now", 5)
            signal.pidfd_send_signal(fd, signal.SIGTERM)
        finally:
            os.close(fd)
        return r.wait(timeout + (grace or c['grace'] or 10))
    if proc in ('alive', 'zombie'):                       # nobody supervises it: stopped here, by identity
        reg.move(r.id, 'stopping', by, why=why)
        signal_run(c, signal.SIGTERM)
        end = time.time() + (grace if grace is not None else (c['grace'] or 10))
        while time.time() < end and r.process() == 'alive':
            time.sleep(0.1)
        if r.process() == 'alive':
            signal_run(c, signal.SIGKILL)
            time.sleep(0.5)
        reg.move(r.id, 'stopped', HOST, 'asked', (why + '; ' if why else '') +
                 'its supervisor was gone, so its exit status was not seen')
        return 'stopped'
    if st != 'lost':
        reconcile_one(r)
    return r.step()


def adopt(pid=None, *, match=None, name=None, of=None, key=None, by=None, check=None, needs=(), reg=None):
    """A process started outside runs, held by its identity from now on and watched to its end. Its exit status is
    not this one's to see, so it ends `lost` (exit-unseen), or `done`/`failed` by its --check."""
    reg = reg or Registry()
    if match:
        hits = [h for h in find(match)]
        if len(hits) != 1:
            raise Refused(f"{match!r} matches {len(hits)} process(es)" + (': ' + ', '.join(
                f"{h['pid']} ({h['user']}, {h['comm']}, {h['age']})" for h in hits) + ' — give --pid' if hits else ''), 4)
        pid = hits[0]['pid']
    if pid in ancestry():
        raise Refused(f'pid {pid} is this command or one of its callers', 5)
    t = ticks_of(pid)
    if t is None:
        raise Refused(f'no process {pid}', 4)
    for i in reg.ids('pid = ? AND ticks = ? AND boot = ?', (pid, t, BOOT)):
        if Run(i, reg).step() not in ENDED:
            raise Refused(f'pid {pid} is run {i} already', 5)
    rid = mint()
    d = f'{reg.path}/{rid}'
    by = by or os.environ.get('DAFTAR_BY') or LOGIN
    user = pwd.getpwuid(uid_of(pid)).pw_name
    cgr = cgroup_root()
    cg = f'{cgr}/{rid}' if cgr else None
    fd = None
    with reg.tx():
        if key:
            h = holder(key, reg)
            if h:
                raise Busy(key, h)
            fd = key_take(key)
            if fd is None:
                raise Busy(key, None, key_holders(key))
        os.makedirs(d)
        if cg:                                            # its tree into a cgroup of its own: contained from now on
            os.makedirs(cg)
            for x in descendants(pid):
                if uid_of(x) == os.getuid():
                    with contextlib.suppress(OSError):
                        cg_join(cg, x)
                else:
                    subprocess.run(['sudo', '-n', 'sh', '-c', 'echo "$1" > "$2"', 'sh', str(x), f'{cg}/cgroup.procs'],
                                   capture_output=True, timeout=30)
        reg.add(**dict(zip(('id', 'walk', 'being', 'host', 'name', 'key', 'parent', 'asked_by', 'mode', 'argv', 'cwd', 'env', 'user', 'login', 'dir', 'log', 'progress', 'check_cmd', 'needs', 'grace', 'boot', 'pid', 'ticks', 'comm', 'cgroup', 'created'),
            (rid, WALK, of or HOST, HOST, name, key, None, by, 'adopted', json.dumps(mask_argv(cmdline(pid) or [])),
             None, None, user, LOGIN, d, None, f'{d}/progress.json', check, json.dumps(list(needs)), 10, BOOT, pid,
             t, comm_of(pid), cg, time.time()))))
        reg.move(rid, 'running', by, why=f"adopted: pid {pid} ({comm_of(pid)}, {user}) running since "
                                         f"{time.strftime('%F %T', time.localtime(started_at(t)))}, started outside runs")
    try:
        cmd = [sys.executable, '-I', ME, '_shim', rid, '--watch'] + (['--lockfd', str(fd)] if fd is not None else [])
        with open(f'{d}/shim.log', 'ab') as sl:
            subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=sl, stderr=sl, cwd='/', timeout=30, check=True,
                           pass_fds=(fd,) if fd is not None else (), env=dict(os.environ, DAFTAR_RUNS=reg.path))
    finally:
        if fd is not None:
            os.close(fd)
    r = Run(rid, reg)
    for _ in range(100):
        if r.supervisor() == 'alive':
            break
        time.sleep(0.02)
    return r


def age(t):
    s = int(time.time() - t)
    return f'{s // 86400}d{s % 86400 // 3600:02d}h' if s >= 86400 else f'{s // 3600}h{s % 3600 // 60:02d}m' \
        if s >= 3600 else f'{s // 60}m{s % 60:02d}s'


def find(rx, show_args=False):
    """Processes whose command line (or name) matches: never this process, nor any process it was started from — the
    shell that asks contains the pattern too. Names, users and ages; a command line only with show_args, masked."""
    rx = re.compile(rx)
    mine = ancestry()
    group = os.getpgrp()                                  # and the pipeline it is in: `find x | grep x` is not news
    out = []
    for p in sorted(pids()):
        s = stat(p)
        if p in mine or (s and s[2] == group):
            continue
        a, cm = cmdline(p), comm_of(p)
        if a is None or cm is None:
            continue
        if rx.search(' '.join(a)) or rx.search(cm):
            t = ticks_of(p)
            if t is None:
                continue
            u = uid_of(p)
            out.append({'pid': p, 'ticks': t, 'user': pwd.getpwuid(u).pw_name if u is not None else '?', 'comm': cm,
                        'age': age(started_at(t)), **({'args': ' '.join(mask_argv(a))} if show_args else {})})
    return out


def reconcile_one(r):
    """A run that has not ended, whose supervisor is gone: lost, once (its process may still run: `adopt` it back)."""
    st, c = r.step(), r.c
    if st in ENDED:
        return st
    if c['shim_pid'] is None and c['mode'] != 'task' and time.time() - c['created'] < 60:
        return st                                         # just asked: its supervisor is still coming up
    if c['boot'] and c['boot'] != BOOT:
        r.reg.move(r.id, 'lost', HOST, 'reboot', 'the machine was restarted after it began')
    elif r.supervisor() not in ('alive', 'zombie'):
        alive = r.process() in ('alive', 'zombie')
        r.reg.move(r.id, 'lost', HOST, 'supervisor-gone', 'its supervisor is gone' +
                   ('; its process still runs: `runs.py reconcile --adopt` watches it again' if alive else
                    ', and so is its process: its end was not seen'))
    return r.step()


def sweep_cgroups(older=60):
    """Empty run cgroups left by a supervisor that died (a run's own is removed at its end), a minute old at least so
    that one made for a process about to join it is never taken. Returns their names."""
    if not os.path.isdir(CG_ROOT):
        return []
    out = []
    for d in os.listdir(CG_ROOT):
        p = f'{CG_ROOT}/{d}'
        if d.startswith('run-') and os.path.isdir(p) and not cg_procs(p) and time.time() - os.stat(p).st_mtime > older:
            with contextlib.suppress(OSError):
                os.rmdir(p)
                out.append(d)
    return out


def prune(days=30, reg=None, dry=False):
    """The folders of runs that ended more than `days` ago (their log, progress and script), taken out; each run's
    statements stay in the store, and the last run of each name keeps its folder. Returns the folders taken out."""
    reg = reg or Registry()
    cut = time.time() - days * 86400
    last_of = {}
    out = []
    rows = []
    for i in reg.ids():
        c = reg.course(i)
        mv = reg.last(i)
        rows.append((i, c, mv))
        if c and c['name']:
            last_of[c['name']] = i
    for i, c, mv in rows:
        if not c or not mv or mv['step'] not in FINAL or mv['at'] > cut or last_of.get(c['name']) == i:
            continue
        d = c['dir']
        if d and os.path.isdir(d) and os.path.dirname(os.path.abspath(d)) == os.path.abspath(reg.path):
            if not dry:
                shutil.rmtree(d, ignore_errors=True)
                reg.set(i, pruned=time.time())
            out.append(d)
    return out


def reconcile(reg=None, readopt=False):
    reg = reg or Registry()
    sweep_cgroups()
    out = []
    for i in reg.ids():
        r = Run(i, reg)
        st = r.step()
        if st in FINAL:
            continue
        if st != 'lost':
            st = reconcile_one(r)
        if st == 'lost' and readopt and r.process() == 'alive' and r.supervisor() != 'alive' and r.c['mode'] != 'task':
            reg.move(r.id, 'running', HOST, why='watched again by a new supervisor (reconcile --adopt)')
            with open(f"{r.c['dir']}/shim.log", 'ab') as sl:  # a file, not a pipe: the supervisor outlives this call
                subprocess.run([sys.executable, '-I', ME, '_shim', r.id, '--watch'], stdin=subprocess.DEVNULL,
                               stdout=sl, stderr=sl, cwd='/', timeout=30, check=True,
                               env=dict(os.environ, DAFTAR_RUNS=reg.path))
            st = 'running'
        out.append((i, st))
    return out


# ---- progress and logs ------------------------------------------------------------------------------------------------
def write_progress(path, kw):
    p = {k: v for k, v in kw.items() if v is not None}
    p['updated'] = time.time()
    tmp = f'{path}.tmp'
    with open(tmp, 'w') as f:
        json.dump(p, f)
    os.replace(tmp, path)


def progress_of(path):
    """A tool's progress in one shape: phase, done, total, unit, rate (per second), eta (seconds), note, updated.
    Read from the shape the tool writes: this one's, scan.py's (hashed_bytes of to_hash_bytes), a download's."""
    try:
        with open(path) as f:
            p = json.load(f)
    except (OSError, ValueError, TypeError):
        return None
    pick = lambda *ks: next((p[k] for k in ks if p.get(k) is not None), None)
    out = {'phase': p.get('phase'), 'done': pick('done', 'hashed_bytes', 'have'),
           'total': pick('total', 'to_hash_bytes', 'want'), 'unit': p.get('unit') or (
               'B' if any(k in p for k in ('hashed_bytes', 'have')) else None),
           'rate': pick('rate', 'rate_bps'), 'eta': pick('eta', 'eta_s'), 'note': p.get('note'),
           'files': p.get('files'), 'updated': p.get('updated')}
    return {k: v for k, v in out.items() if v is not None}


def tail_lines(path, n=20):
    try:
        with open(path, 'rb') as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 65536))
            return f.read().decode('utf-8', 'replace').splitlines()[-n:]
    except (OSError, TypeError):
        return []


# ---- reading for people and pages -------------------------------------------------------------------------------------
def describe(r):
    c, mv = r.c, r.reg.moves(r.id)
    last = mv[-1] if mv else None
    st = last['step'] if last else None
    proc, sup = r.process(), r.supervisor()
    began = next((m['at'] for m in mv if m['step'] == 'running'), c['created'])
    end = last['at'] if st in ENDED else None
    return {'id': r.id, 'name': c['name'], 'label': r.label(), 'step': st, 'reason': last['reason'] if last else None,
            'why': last['why'] if last else None, 'being': c['being'], 'host': c['host'], 'key': c['key'],
            'parent': c['parent'], 'mode': c['mode'], 'user': c['user'] or c['login'], 'asked_by': c['asked_by'],
            'command': json.loads(c['argv'] or '[]'), 'env': json.loads(c['env'] or '{}'), 'cwd': c['cwd'],
            'pid': c['pid'], 'process': proc, 'supervisor': sup, 'cgroup': c['cgroup'], 'comm': c['comm'],
            'created': c['created'], 'began': began, 'ended': end, 'took': (end or time.time()) - began,
            'exit_code': c['exit_code'], 'signal': c['signal'], 'result': json.loads(c['result'] or 'null'),
            'inputs': json.loads(c['inputs'] or 'null'), 'progress': progress_of(c['progress']), 'log': c['log'],
            'moves': [{'at': m['at'], 'step': m['step'], 'by': m['by'], 'reason': m['reason'], 'why': m['why']}
                      for m in mv]}


def listing(reg=None, all_=False, hours=24, limit=60):
    """The runs as a tree: those that have not ended, and those that ended in the last `hours` (all with all_)."""
    reg = reg or Registry(write=False)
    rows = [describe(Run(i, reg)) for i in reg.ids()]
    keep = [d for d in rows if all_ or d['step'] not in ENDED or (d['ended'] or 0) > time.time() - hours * 3600
            or (d['step'] == 'lost' and d['process'] == 'alive')]
    keep = sorted(keep, key=lambda d: (d['step'] in ENDED, -(d['ended'] or d['created'])))[:limit if not all_ else None]
    ids = {d['id'] for d in keep}
    kids = {}
    for d in keep:
        kids.setdefault(d['parent'] if d['parent'] in ids else None, []).append(d)
    out = []

    def walk(p, depth):
        for d in kids.get(p, []):
            d['depth'] = depth
            out.append(d)
            walk(d['id'], depth + 1)
    walk(None, 0)
    return out


def human(n, unit=None):
    if n is None:
        return '—'
    if unit != 'B':
        return f'{n:,.0f}' + (f' {unit}' if unit else '')
    n = float(n)
    for u in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1000 or u == 'TB':
            return f'{n:.0f} {u}' if u == 'B' else f'{n:.1f} {u}'
        n /= 1000


def line(d):
    p = d['progress'] or {}
    pr = ''
    if p.get('total'):
        pr = f" {100 * (p.get('done') or 0) / p['total']:.0f}% of {human(p['total'], p.get('unit'))}"
    elif p.get('done') is not None:
        pr = f" {human(p['done'], p.get('unit'))}"
    flag = ''
    if d['step'] not in ENDED and d['supervisor'] != 'alive':
        flag = ' UNSUPERVISED'
    if d['step'] == 'lost' and d['process'] == 'alive':
        flag = ' (still running)'
    st = d['step'] + (f" ({d['reason']})" if d['reason'] else '')
    return (f"{'  ' * d.get('depth', 0)}{d['id']}  {st:<24} {age(time.time() - d['took']) if d['took'] else '':>7}  "
            f"{d['label'][:30]:<30} {d['being'][:34]:<34}{pr}{flag}")


def export(r, self_=False):
    """The run as the store keeps it — its course, a `be` of the being on walk-run as order, and each move — written as
    the being's bean writes them (`self` with --self, else the being), so that a run kept in both is one statement in
    both: the same moments, to the millisecond, and the same words."""
    reg = r.reg
    b = reg._being_of(r.id)
    out = []
    for v, roles, _acts in reg.S.get(b):
        if not ((v == 'be' and roles.get('id') == r.id) or (v == 'move' and roles.get('through') == f'{b}#{r.id}')):
            continue
        d = reg.S.denormalize(b, v, roles)
        if v == 'move':
            d.pop('id', None)                   # named by its form: a move needs no name of its own in a bean
        if not self_:
            d = {k: (b if x == 'self' else x) for k, x in d.items()}
        out.append(dmstore.statement_line({v: d}))
    return '\n'.join(out)


# ---- the command ------------------------------------------------------------------------------------------------------
def pick(reg, a):
    return one(reg, getattr(a, 'run', None), getattr(a, 'name', None), getattr(a, 'key', None),
               live=not getattr(a, 'run', None))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('start')
    s.add_argument('--name'), s.add_argument('--of'), s.add_argument('--key'), s.add_argument('--cwd')
    s.add_argument('--env', action='append', default=[], metavar='NAME=VALUE')
    s.add_argument('--pass', dest='pass_env', action='append', default=[], metavar='NAME')
    s.add_argument('--require-env', action='append', default=[], metavar='NAME',
                   help='refuse to start unless NAME is set: a test that must not run on the real thing')
    s.add_argument('--clean-env', action='store_true'), s.add_argument('--user')
    s.add_argument('--timeout', type=float), s.add_argument('--grace', type=float, default=10)
    s.add_argument('--check', help='a shell command whose exit 0 is what "done" means, read after the run')
    s.add_argument('--needs', action='append', default=[], metavar='PATH',
                   help='a path the run needs (a device, a mount): when it is gone, the run is stopped, failed')
    s.add_argument('--progress'), s.add_argument('--log'), s.add_argument('--stdin'), s.add_argument('--parent')
    s.add_argument('--by'), s.add_argument('--wait-key', action='store_true'), s.add_argument('--notify',
                                                                                              action='store_true')
    s.add_argument('--secret-arg', type=int, action='append', default=[], metavar='N')
    s.add_argument('--script', metavar='FILE|-')
    s.add_argument('--wait', type=float, metavar='S', help='then wait for it, at most S seconds')
    s.add_argument('--json', action='store_true')
    s.add_argument('command', nargs=argparse.REMAINDER)
    for c in ('show', 'wait', 'stop', 'tail', 'export'):
        x = sub.add_parser(c)
        x.add_argument('run', nargs='?')
        x.add_argument('--name'), x.add_argument('--key')
        if c == 'show':
            x.add_argument('--json', action='store_true')
        if c == 'wait':
            x.add_argument('--timeout', type=float, default=600, help='the bound, in seconds (600 unless given)')
        if c == 'stop':
            x.add_argument('--why'), x.add_argument('--grace', type=float), x.add_argument('--by')
            x.add_argument('--tree', action='store_true', help='its child runs first')
        if c == 'tail':
            x.add_argument('-n', type=int, default=20), x.add_argument('-f', action='store_true')
        if c == 'export':
            x.add_argument('--self', dest='self_', action='store_true', help="`self` for the being: in its own bean")
    x = sub.add_parser('list')
    x.add_argument('--all', action='store_true'), x.add_argument('--json', action='store_true')
    x = sub.add_parser('adopt')
    x.add_argument('--pid', type=int), x.add_argument('--match'), x.add_argument('--name'), x.add_argument('--of')
    x.add_argument('--key'), x.add_argument('--by'), x.add_argument('--check')
    x.add_argument('--needs', action='append', default=[])
    x = sub.add_parser('find')
    x.add_argument('pattern'), x.add_argument('--args', action='store_true')
    x = sub.add_parser('progress')
    for k in ('done', 'total', 'rate', 'eta'):
        x.add_argument(f'--{k}', type=float)
    x.add_argument('--unit'), x.add_argument('--phase'), x.add_argument('--note')
    x = sub.add_parser('reconcile')
    x.add_argument('--adopt', action='store_true')
    x = sub.add_parser('prune')
    x.add_argument('--days', type=float, default=30), x.add_argument('--dry', action='store_true')
    x = sub.add_parser('setup')
    x.add_argument('--by', help='who writes the walk: a session, or a person (default: the login)')
    x.add_argument('--owner', help="whose it is (default: the garden's gardener)")
    x = sub.add_parser('_shim')
    x.add_argument('run'), x.add_argument('--lockfd', type=int), x.add_argument('--wait-key')
    x.add_argument('--watch', action='store_true')
    a = ap.parse_args(argv)
    try:
        return command(a)
    except Refused as e:
        print(f'runs: {e}', file=sys.stderr)
        return e.code


def command(a):
    if a.cmd == '_shim':
        shim(a.run, a.lockfd, a.wait_key, a.watch)
        return 0
    if a.cmd == 'prune':
        out = prune(a.days, dry=a.dry)
        print(f"run prune: {len(out)} folder(s) of runs ended more than {a.days:g} day(s) ago "
              f"{'would be ' if a.dry else ''}taken out; their statements stay in the store")
        return 0
    if a.cmd == 'setup':
        sys.path.insert(0, ROOT)
        from core import read as core_read
        gardener = None
        with contextlib.suppress(Exception):
            gardener = core_read.document(os.path.join(ROOT, 'GARDEN.md'))[0].get('gardener')
        p, said = setup(ROOT, a.by or LOGIN, a.owner or gardener or LOGIN)
        print(f'run setup: {os.path.relpath(p, ROOT)}: {said}')
        return 0
    if a.cmd == 'progress':
        path = os.environ.get('DAFTAR_RUN_PROGRESS')
        if not path:
            raise Refused('not inside a run: DAFTAR_RUN_PROGRESS is not set', 2)
        write_progress(path, {k: getattr(a, k) for k in ('done', 'total', 'rate', 'eta', 'unit', 'phase', 'note')})
        return 0
    if a.cmd == 'find':
        for h in find(a.pattern, a.args):
            print(f"{h['pid']:>7}  {h['user']:<8} {h['age']:>7}  {h['comm']}" + (f"  {h['args']}" if a.args else ''))
        return 0
    if a.cmd == 'list':
        rows = listing(Registry(), a.all)
        if a.json:
            print(json.dumps(rows, indent=1))
        else:
            print(f'registry {registry_path()} on {HOST}')
            for d in rows:
                print(line(d))
        return 0
    reg = Registry()
    if a.cmd == 'start':
        for n in a.require_env:
            if not os.environ.get(n):
                raise Refused(f'--require-env {n}: not set, so not started', 2)
        cmd = a.command[1:] if a.command[:1] == ['--'] else a.command
        script = None
        if a.script:
            script = sys.stdin.read() if a.script == '-' else open(a.script).read()
        env = dict(kv.split('=', 1) for kv in a.env)
        r = start(cmd or None, script=script, name=a.name, of=a.of, key=a.key, cwd=a.cwd, env=env,
                  pass_env=a.pass_env, clean_env=a.clean_env, user=a.user, timeout=a.timeout, grace=a.grace,
                  check=a.check, needs=a.needs, progress=a.progress, parent=a.parent, by=a.by, log=a.log,
                  stdin=a.stdin, wait_key=a.wait_key, notify=a.notify, secret_args=a.secret_arg, reg=reg)
        if a.json:
            print(json.dumps(describe(r)))
        else:
            print(r.id)
        if a.wait is not None:
            st = r.wait(a.wait)
            return 124 if st is None else EXIT.get(st, 1)
        return 1 if r.step() == 'failed' else 0
    if a.cmd == 'reconcile':
        for i, st in reconcile(reg, a.adopt):
            print(f'{i}  {st}')
        return 0
    if a.cmd == 'adopt':
        if bool(a.pid) == bool(a.match):
            raise Refused('adopt takes --pid or --match', 2)
        r = adopt(a.pid, match=a.match, name=a.name, of=a.of, key=a.key, by=a.by, check=a.check, needs=a.needs,
                  reg=reg)
        print(r.id)
        return 0
    if not (a.run or a.name or a.key):
        raise Refused(f'{a.cmd}: which run? its id, or --name / --key', 2)
    r = pick(reg, a)
    if a.cmd == 'show':
        d = describe(r)
        if a.json:
            print(json.dumps(d, indent=1))
            return 0
        print(line(dict(d, depth=0)))
        for k in ('being', 'key', 'parent', 'mode', 'user', 'asked_by', 'cwd', 'pid', 'process', 'supervisor',
                  'cgroup', 'exit_code', 'signal', 'result', 'inputs', 'progress', 'log'):
            if d[k] not in (None, '', {}, []):
                print(f'  {k:<11} {d[k]}')
        print(f"  {'command':<11} {' '.join(d['command'])}")
        for k, v in d['env'].items():
            print(f"  {'env':<11} {k}={v}")
        for m in d['moves']:
            print(f"  {moment(m['at'])}  {m['step']:<9} by {m['by']}" + (f" ({m['reason']})" if m['reason'] else '')
                  + (f": {m['why']}" if m['why'] else ''))
        return 0
    if a.cmd == 'wait':
        st = r.wait(a.timeout)
        if st is None:
            print(f'runs: {r.id} has not ended after {a.timeout:g} s (the bound); it is {r.step()}', file=sys.stderr)
            return 124
        print(f'{r.id} {st}')
        return EXIT.get(st, 1)
    if a.cmd == 'stop':
        st = stop(r, why=a.why, by=a.by, grace=a.grace, tree=a.tree)
        print(f'{r.id} {st or r.step()}')
        return 0 if (st or r.step()) in ENDED else 124
    if a.cmd == 'tail':
        for l in r.tail(a.n):
            print(l)
        if a.f:
            path, pos = r.c['log'], os.path.getsize(r.c['log']) if r.c['log'] and os.path.exists(r.c['log']) else 0
            while r.step() not in ENDED:
                time.sleep(0.5)
                with contextlib.suppress(OSError), open(path, 'rb') as f:
                    f.seek(pos)
                    chunk = f.read()
                    pos += len(chunk)
                    sys.stdout.write(chunk.decode('utf-8', 'replace'))
                    sys.stdout.flush()
        return 0
    if a.cmd == 'export':
        print(export(r, a.self_))
        return 0


if __name__ == '__main__':
    sys.exit(main())
