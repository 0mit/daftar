#!/usr/bin/env python3
"""install — this garden's git hooks and semantic merge driver into this clone, and with --daftard this machine's daftard.

    python3 bin/install.py            # from anywhere inside the clone
    python3 bin/install.py --sign     # the same, and this clone signs its commits with this machine's agent key
    python3 bin/install.py --daftard [--listen 127.0.0.1:8770] [--no-service] [--source <dir|url> | --binary-from <dir|url>]
                                      # the same, and this machine's daftard: its binary, this garden served, its routines
                                      # ticked each minute, and what keeps it running on this system

The gate (pre-commit, and pre-merge-commit for a merge git commits itself) runs bin/check.py, and the driver
bin/merge.py; each takes the law the garden runs — the core's for a garden of statements, today's for one in today's
words — so one install serves both (v1 part 3).

Hooks and merge-driver config live in .git/, which is NOT cloned, so every fresh clone runs this once.
There is exactly ONE installer, and this is it; `bin/install.sh` only hands over to it. The versioned
hooks in bin/hooks/ are the source of truth and this script only copies them — copied, never generated,
so what runs is what is reviewed. A `.sh` file there is no hook but a part the hooks source (python.sh), and
is copied beside them, so an installed hook never depends on what the working tree happens to hold.

EVERY COPY HAS LF LINE ENDS, whatever the checkout did. Git for Windows checks text out with CRLF by default
(core.autocrlf=true), and a hook with CR in it does not run: `#!/bin/sh` and a CR names no interpreter, and
the shell reads the CR as part of each line's last word, so the gate fails closed and nothing commits without
--no-verify.
`.gitattributes` asks for LF in bin/hooks/ and in every `.sh`; this is the second guard, for a checkout made
before that line arrived or with it overridden. Only line ends change: CR LF becomes LF, nothing else.

It is Python and not shell because a garden is grown on Windows too, where `sh` is not a given but the
Python that runs the gate is. The hooks themselves stay `sh`: git runs them with the shell it ships.

WHICH PYTHON the hooks and the merge driver run is CHOSEN, not assumed: the first that runs AND imports yaml,
of `git config daftar.python`, python3, python, `py -3` and, last, the Python running this. A name that is
found but does not run — on Windows, the Microsoft Store's App execution alias for `python3` or `python` — is
skipped, as is a Python without PyYAML. The choice is recorded per clone as `git config daftar.python`, which
bin/hooks/python.sh reads first; when nothing works, the refusal names each candidate and why.

THE MACHINE'S AGENT KEY (P2), in a garden: what every agent on this machine signs its commits with — it may write,
enact and propose, and never ratify. It is made where this account keeps none: ed25519, with no passphrase (an agent
signs with nobody there to give one), in this account's daftar state folder — daftard's own, where a hub keeps its key
too (bin/hub.py) — under `agent/key`, the folder 0700 and the key 0600: one key for the account on this machine,
whichever garden it writes, and never in a garden or a repository. It is made once and never over: a new key is a new
identity. Naming it is the gardener's (class F), so it is PROPOSED, never written into the garden here: install prints
its fingerprint and the `name` the gardener writes on the bean of this machine's agent harness, and writes the proposal
out whole in the clone's git directory (`daftar/agent-key.proposal.md`), off git, where no save sweeps it in. Until the
garden names it, a hub reads a commit signed with it as signed by a key no bean carries.

`--sign` sets this clone to sign with it (gpg.format ssh, user.signingkey, commit.gpgsign), where no other key is set
for it; a key set already, the gardener's or another's, is left as it is and named. bin/save.py signs where
commit.gpgsign is set, and refuses to sign with a key this clone is told is the gardener's ratifying key.

DAFTARD (`--daftard`), one per machine: it serves the gardens this account holds — their pages and board, their sync,
what waits and for whom — and is the clock of their routines. Asked for, never by default: an upgrade installs the
hooks again, and must not start a daemon on a machine whose daftard is kept otherwise. In the main working copy alone,
since a session's copy is gone when the session closes. In four steps:
  - ITS BINARY, laid in this account's daftar state folder as `bin/daftard` (`bin\\daftard.exe` on Windows), in place of
    one laid before (a daftard running from it is stopped first, a save under way finishing). Where Go is, it is BUILT
    from daftard/: this repository's own where it carries it (daftar's own clone), else the source of the release this
    garden runs (GARDEN.md `daftar_release`), fetched from daftar's repository and its tag's signature verified by a key
    this garden's seed/RELEASE-SIGNERS names before any of it is built, as bin/dmupgrade.py verifies a release; or from
    `--source`, a daftar tree on this machine taken as it stands, or a repository fetched at the release's tag and
    verified the same way. Where Go is not, or with `--binary-from`, it is the BINARY the release carries, built by
    daftar's CI from the tagged commit and attached to the tag's release with its SHA-256 (`daftard-<system>-<arch>`
    beside `daftard-<system>-<arch>.sha256`): taken only when its bytes have that SHA-256. The sum proves the transfer,
    not the build: a release's binaries are not signed yet, and the install says so.
  - THIS GARDEN SERVED, by daftard's own `install` (daftard.json in the state folder): its path, the Python chosen
    above, its name (GARDEN.md `garden`), and `routines: true`. What daftard.json already holds — other gardens, the
    machine's settings, this garden's own — is kept.
  - ITS ROUTINES: each minute daftard asks the garden's own `bin/routines.py tick`, which runs a routine whose window is
    open where the garden grants this machine `enact` of its walk, and nothing else (bin/routines.py). No routine needs
    a job of its own in the system's scheduler.
  - WHAT KEEPS IT RUNNING, by daftard's own `install`: on Windows the logon task «Daftar» (and the desktop icon); on Linux
    the systemd user unit `daftard.service`; on macOS the launchd agent `daftar.daftard` in ~/Library/LaunchAgents,
    started at login and again whenever it ends other than by `daftard stop`. On macOS, where a routine was a launchd
    job of its own, daftard is now the one job launchd keeps for daftar, and the clock of every routine: a routine
    another scheduler still runs is that scheduler's (`be … as: presence` on its walk), and daftard's tick leaves it
    alone, so it is never run twice; its job is retired once daftard ticks it. Where the system has no manager to ask
    (a container), or with `--no-service`, nothing is registered, and the install starts daftard itself, until the
    machine stops.
Then it waits until daftard answers on its loopback, and says where. `daftar serve` runs daftard's own commands,
`daftar board` opens a garden's board.
"""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

# The order bin/hooks/python.sh tries too; the recorded choice goes first, the running interpreter last.
CANDIDATES = (['python3'], ['python'], ['py', '-3'])
STORE_ALIAS = ("is the Microsoft Store alias (App execution aliases), which runs no Python — install Python from "
               "python.org, or turn the alias off in Settings > Apps > Advanced app settings > App execution aliases")


def git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')


# A CHILD PYTHON WRITES UTF-8 to us, and we read UTF-8. On Windows a Python writing to a pipe uses the old code page,
# and a path outside it (a per-user install under a profile named in Persian) cannot be printed: the probe then saw a
# Python that has PyYAML as one that lacks it. PYTHONIOENCODING overrides UTF-8 mode, so both are set.
CHILD_ENV = {'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'}


def _run(cmd, code):
    try:
        return subprocess.run(cmd + ['-c', code], capture_output=True, text=True, encoding='utf-8', errors='replace',
                              timeout=60, env={**os.environ, **CHILD_ENV})
    except (OSError, subprocess.SubprocessError):
        return None


def copy_lf(src, dst):
    """`src` to `dst` with every CR LF made LF — a hook runs under `sh`, which reads a CR as part of the word before it."""
    with open(src, 'rb') as fh:
        data = fh.read().replace(b'\r\n', b'\n')
    with open(dst, 'wb') as fh:
        fh.write(data)


def probe(cmd):
    """(the interpreter's own path, None) when `cmd` runs and imports yaml, else (None, why not)."""
    r = _run(cmd, 'import sys, yaml; print(sys.executable)')
    if r is not None and r.returncode == 0 and r.stdout.strip():
        # forward slashes: a path Git's sh (the hooks, the merge driver) and Windows both read
        return r.stdout.strip().splitlines()[-1].replace('\\', '/'), None
    shown = ' '.join(cmd) if cmd[0] == 'py' else (f'"{cmd[0]}"' if ' ' in cmd[0] else cmd[0])
    found = shutil.which(cmd[0])
    if not found and not os.path.isfile(cmd[0]):
        return None, 'not found'
    ran = _run(cmd, 'import sys')
    if ran is not None and ran.returncode == 0:
        return None, f'runs, but PyYAML is missing: {shown} -m pip install PyYAML'
    if 'WindowsApps' in (found or cmd[0]):
        return None, STORE_ALIAS
    return None, f'is at {found or cmd[0]} but does not run'


def choose_python(repo):
    """(path, None) for the Python this clone's tools run with, recorded as `git config daftar.python`;
    (None, the refusal naming each candidate and why) when none runs and imports yaml."""
    recorded = git('config', '--get', 'daftar.python', cwd=repo).stdout.strip()
    tried, why = [], []
    # a recorded `py -3` is the launcher and its switch; anything else is one name or path, which may hold a space
    cands = ([recorded.split() if recorded.startswith('py -') else [recorded]] if recorded else []) \
        + [list(c) for c in CANDIDATES] + [[sys.executable]]
    for cmd in cands:
        if cmd in tried:
            continue
        tried.append(cmd)
        exe, no = probe(cmd)
        if exe:
            if not (recorded and cmd == cands[0]):
                git('config', 'daftar.python', exe, cwd=repo)
            return exe, None
        label = ('git config daftar.python (' + recorded + ')' if recorded and cmd == cands[0] else
                 'the Python running this (' + sys.executable + ')' if cmd == [sys.executable] else ' '.join(cmd))
        why.append(f"  {label}: {no}")
    return None, ("no Python here runs the tools. Each candidate, and why:\n" + '\n'.join(why) +
                  "\nInstall Python 3 with PyYAML (pip install PyYAML), or name one that works:\n"
                  "  git config daftar.python <path-to-python>")


def state_dir():
    """This account's daftar state folder, which is daftard's own (daftard/internal/state): DAFTARD_STATE where it
    is set, %LOCALAPPDATA%\\Daftar on Windows, $XDG_STATE_HOME/daftar (~/.local/state/daftar) elsewhere."""
    if os.environ.get('DAFTARD_STATE'):
        return os.path.normpath(os.environ['DAFTARD_STATE'])
    if os.name == 'nt':
        return os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'Daftar')
    return os.path.join(os.environ.get('XDG_STATE_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'state'),
                        'daftar')


def _private(path, folder):
    """The key and its folder narrowed to this account again, as daftard narrows its state folder on each start."""
    if os.name != 'nt':
        os.chmod(folder, 0o700)
        os.chmod(path, 0o600)


def make_key(path, comment):
    """AN ED25519 KEY AT `path`, under the state folder, made once: (made, why not). No passphrase, since whoever signs
    with it — a hub, an agent — signs with nobody there to give one. The folders it makes are this account's alone
    (0700) and the key 0600; a key there already is narrowed again and kept, never made over: a new key is a new
    identity, the gardener's to name (class F)."""
    folder = os.path.dirname(path)
    if os.path.isfile(path):
        _private(path, folder)
        return False, ''
    if not shutil.which('ssh-keygen'):
        return False, "this machine has no ssh-keygen to make it with"
    top = state_dir()
    os.makedirs(os.path.dirname(top), exist_ok=True)
    steps = [s for s in os.path.relpath(folder, top).split(os.sep) if s not in ('', '.')]
    for i in range(len(steps) + 1):                 # what it makes of the state folder, this account's alone
        d = os.path.join(top, *steps[:i])
        if not os.path.isdir(d):
            os.mkdir(d, 0o700)
    r = subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-C', comment, '-f', path],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', stdin=subprocess.DEVNULL)
    if r.returncode != 0 or not os.path.isfile(path):
        return False, f"ssh-keygen did not make it: {(r.stdout + r.stderr).strip()[:300]}"
    _private(path, folder)
    return True, ''


def ssh_fingerprint(key):
    """The SHA-256 fingerprint of an SSH key as git names one to sign with (user.signingkey): a file, private or public
    (its `.pub` beside it read first, so a key with a passphrase is never opened), or `key::<its public line>`; or a
    fingerprint given as one. None where ssh-keygen reads none."""
    key = (key or '').strip()
    if re.fullmatch(r'SHA256:[A-Za-z0-9+/]{43}', key):
        return key
    if not key or not shutil.which('ssh-keygen'):
        return None
    if key.startswith('key::'):
        r = subprocess.run(['ssh-keygen', '-l', '-f', '-'], input=key[5:] + '\n', capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
    else:
        p = os.path.expanduser(key)
        p = p + '.pub' if os.path.isfile(p + '.pub') else p
        if not os.path.isfile(p):
            return None
        r = subprocess.run(['ssh-keygen', '-l', '-f', p], capture_output=True, text=True, encoding='utf-8',
                           errors='replace', stdin=subprocess.DEVNULL)
    m = re.search(r'(SHA256:[A-Za-z0-9+/]{43})', r.stdout)
    return m.group(1) if r.returncode == 0 and m else None


def shown(path):
    """(fingerprint, public line) of the key at `path`, read from its public half."""
    with open(path + '.pub', encoding='utf-8') as fh:
        return ssh_fingerprint(path), fh.read().strip()


AGENT_KEY = ('agent', 'key')       # under the state folder: one key for the account on this machine, whatever it writes


def agent_key_path():
    return os.path.join(state_dir(), *AGENT_KEY)


def machine():
    """This machine's name as a bean would carry it: its host name, lower case, in kebab-case."""
    return re.sub(r'[^a-z0-9]+', '-', platform.node().split('.')[0].lower()).strip('-') or 'this-machine'


def agent_key(repo, git_dir, say, sign=False, harness='claude-code'):
    """THIS MACHINE'S AGENT KEY: made where this account keeps none, its name proposed to the gardener (class F) and
    written out in the clone's git directory; with `sign`, this clone set to sign with it where no other key is set."""
    path = agent_key_path()
    made, why = make_key(path, f'agent@{machine()}')
    if why:
        say(f"agent key: none made — {why}; commits here stay unsigned")
        return None
    fpr, pub = shown(path)
    bean = f"{harness}-{machine()}"
    name = f'name: {{ id: agent-key, by: ssh, of: self, as: "{fpr}" }}'
    proposal = os.path.join(git_dir, 'daftar', 'agent-key.proposal.md')
    os.makedirs(os.path.dirname(proposal), exist_ok=True)
    with open(proposal, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(f"# Proposed: this machine's agent key, named (class F, the gardener's)\n\n"
                 f"Made by bin/install.py on {machine()}, kept in {os.path.dirname(path)} — this account's alone, never "
                 f"in a garden.\n\n- fingerprint: {fpr}\n- public half: {pub}\n\n"
                 f"Every agent on this machine signs its commits with it: it may write, enact and propose, and never "
                 f"ratify. A hub reads the writer from a signature only once the garden names the key, which is the "
                 f"gardener's to do:\n\n"
                 f"- on the bean of this machine's agent harness, `beans/{bean}.md` (kind `instance`, at "
                 f"{machine()} as its habitat):\n\n      - {name}\n\n"
                 f"- in the gardener's bean, its grants: `as: write` and `as: enact`, `to: [{bean}]`, over what agents "
                 f"may write — never `as: ratify`.\n\n"
                 f"Until then a hub reads a commit signed with it as signed by a key no bean carries.\n")
    say(f"agent key of this machine: {fpr} — " + ("made now" if made else "kept: made before, and never made over"))
    say(f"  proposed for the gardener (class F): `{name}` on beans/{bean}.md — written out in "
        f"{os.path.relpath(proposal, repo)}")
    if sign:
        have = git('config', '--get', 'user.signingkey', cwd=repo).stdout.strip()
        if have and ssh_fingerprint(have) != fpr:
            say(f"  signing: this clone is set to sign with {have} already — left as it is")
        else:
            for k, v in (('gpg.format', 'ssh'), ('user.signingkey', path), ('commit.gpgsign', 'true')):
                git('config', k, v, cwd=repo)
            say("  signing: this clone signs its commits with it (gpg.format ssh, user.signingkey, commit.gpgsign)")
    return fpr


def main_worktree(repo):
    """The repository's main working tree. A clone's config is SHARED by every worktree of it (bin/session.py makes one
    a session), so the merge driver must be named by a path that outlives them all: installed from a session's worktree
    — as bin/dmupgrade.py installs after an upgrade — the worktree's own path would point at nothing once the session
    closed, and every later merge would fail to start its driver. A main tree without bin/merge.py (a bare one) leaves
    the worktree's own."""
    for line in git('worktree', 'list', '--porcelain', cwd=repo).stdout.splitlines():
        if line.startswith('worktree '):
            main = line[len('worktree '):].strip()
            return main if os.path.isfile(os.path.join(main, 'bin', 'merge.py')) else repo
    return repo


def install(repo=None, quiet=False, sign=False, daftard=None):
    say = (lambda *a: None) if quiet else print
    if repo is None:
        r = git('rev-parse', '--show-toplevel')
        if r.returncode != 0:
            raise SystemExit("install: not inside a git repository")
        repo = r.stdout.strip()
    git_dir = git('rev-parse', '--git-common-dir', cwd=repo).stdout.strip() or '.git'
    if not os.path.isabs(git_dir):
        git_dir = os.path.join(repo, git_dir)
    hooks_dst = os.path.join(git_dir, 'hooks')
    os.makedirs(hooks_dst, exist_ok=True)

    # 1) the versioned hooks, and what they source
    for name in sorted(os.listdir(os.path.join(repo, 'bin', 'hooks'))):
        src, dst = os.path.join(repo, 'bin', 'hooks', name), os.path.join(hooks_dst, name)
        if name.endswith('.sh'):
            copy_lf(src, dst)                               # sourced by the hooks, never run by git
            continue
        # THE GATE IS FOR A GARDEN. This repository can also BE the language itself (the daftar repo, or a
        # clone of it), which has no GARDEN.md and no beans: there the gate has nothing to judge and dies on
        # the missing vocabulary, taking the commit with it. The pre-push leak check belongs in BOTH.
        if name in ('pre-commit', 'pre-merge-commit') and not os.path.isfile(os.path.join(repo, 'GARDEN.md')):
            say(f"skipped {os.path.relpath(hooks_dst, repo)}/{name} — no GARDEN.md here, so this repo is the language, not a garden")
            continue
        copy_lf(src, dst)
        os.chmod(dst, os.stat(dst).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        say(f"installed {os.path.relpath(dst, repo)}")

    # 2) the Python they run: chosen once here, recorded for the hooks (they check it again on every run).
    py, refusal = choose_python(repo)
    if py:
        say(f"python for this clone: {py}  (git config daftar.python)")

    # 3) the semantic merge driver, referenced by .gitattributes (merge=daftar). Git does NOT warn when an
    #    attribute names a driver that is not configured — it silently text-merges instead. The attribute
    #    and this config must therefore always change together. The interpreter is named by its full path,
    #    because `python3` is not a name every machine has, and not every name on a PATH is a Python.
    #    bin/merge.py merges a bean by the statement merge (core/merge.py); %P is the path, which it names when it
    #    refuses.
    driver = os.path.join(main_worktree(repo), 'bin', 'merge.py')
    git('config', 'merge.daftar.name', 'daftar merge (bin/merge.py: the statement merge)', cwd=repo)
    git('config', 'merge.daftar.driver', f'"{py or sys.executable}" "{driver}" --file %O %A %B %P', cwd=repo)
    say("configured merge driver 'daftar' -> bin/merge.py")
    if refusal:
        # The hooks are installed all the same: a hook that refuses with this message is the gate still
        # standing; no hook at all would let every commit through unjudged.
        print(f"install: {refusal}", file=sys.stderr)
        return 1
    say(f"installed: pre-commit gate + semantic merge driver in {os.path.relpath(git_dir, repo)}")
    # 4) THE AGENT'S OWN DOOR, in a garden: the guards before each act of an agent in another maker's loop, and the shell
    #    its harness runs commands in, in the clone's own settings (bin/hook.py install), named from the main working
    #    tree as the merge driver is. A shell it cannot set leaves the guards refusing every command until it is set.
    #    From a session's copy it installs nothing: the main tree's bin/hook.py may be an older release's, and the settings
    #    it writes are the main copy's, which other sessions read at once (T1 of the second build run: an upgrade in a
    #    session copy wrote four older hooks there). The main copy installs its own door after the merge.
    main = main_worktree(repo)
    top = git('rev-parse', '--show-toplevel', cwd=repo).stdout.strip() or repo
    if os.path.realpath(main) != os.path.realpath(top):
        say(f"the agent's door is not installed from a session's copy: run `python3 bin/install.py` in {main} after the "
            f"merge")
    elif os.path.isfile(os.path.join(main, 'GARDEN.md')) and os.path.isfile(os.path.join(main, 'bin', 'hook.py')):
        r = subprocess.run([py, os.path.join(main, 'bin', 'hook.py'), 'install', 'claude-code'], cwd=main,
                           capture_output=True, text=True, encoding='utf-8', errors='replace', env={**os.environ, **CHILD_ENV})
        for line in r.stdout.splitlines():
            say(line)
        if r.returncode != 0:
            print(f"install: {r.stderr.strip() or r.stdout.strip()}", file=sys.stderr)
    # 5) THE MACHINE'S AGENT KEY, in a garden: made where none is, its name proposed to the gardener (class F)
    if os.path.isfile(os.path.join(main, 'GARDEN.md')):
        agent_key(repo, git_dir, say, sign)
    # 6) DAFTARD, where it is asked for: its binary, this garden served, its routines ticked, and what keeps it running
    if daftard is not None:
        return install_daftard(repo, py, say, **daftard)
    return 0


# ---- DAFTARD: this machine's daemon, laid and started (--daftard) ---------------------------------------------------
UPSTREAM = 'https://github.com/0mit/daftar.git'                  # where a release is fetched from, as bin/dmupgrade.py
RELEASES = 'https://github.com/0mit/daftar/releases/download'    # where CI attaches each tag's binaries


def daftard_path():
    """Where daftard's binary is laid: in this account's daftar state folder, `bin/daftard` (`bin\\daftard.exe`)."""
    return os.path.join(state_dir(), 'bin', 'daftard.exe' if os.name == 'nt' else 'daftard')


def asset():
    """This system's binary among a release's assets, `daftard-<system>-<arch>` (`.exe` on Windows); None where the
    release builds none."""
    system = {'linux': 'linux', 'darwin': 'darwin', 'win32': 'windows'}.get(sys.platform)
    arch = {'x86_64': 'amd64', 'amd64': 'amd64', 'arm64': 'arm64', 'aarch64': 'arm64'}.get(platform.machine().lower())
    if not system or not arch:
        return None
    return f"daftard-{system}-{arch}" + ('.exe' if system == 'windows' else '')


def manifest(garden, key):
    """A plain value of GARDEN.md's front matter (`garden`, `daftar_release`), read without a parser; None where absent."""
    try:
        with open(os.path.join(garden, 'GARDEN.md'), encoding='utf-8') as fh:
            m = re.search(rf'^{key}:\s*"?([^"\s#]+)', fh.read(), re.M)
    except OSError:
        return None
    return m.group(1) if m else None


def go_build(src, out):
    """daftard built from the daftar tree at `src` into `out`, as daftar's CI builds a release's: (True, '') or (False,
    why). The Go this machine has, never one fetched (GOTOOLCHAIN=local); daftard's one outside package is vendored."""
    go = shutil.which('go')
    mod = os.path.join(src, 'daftard')
    if not go:
        return False, "this machine has no Go to build it with"
    if not os.path.isfile(os.path.join(mod, 'go.mod')):
        return False, f"{src} holds no daftard/ to build"
    commit = git('rev-parse', 'HEAD', cwd=src).stdout.strip() or 'dev'
    flags = f'-X main.Build={commit}' + (' -H=windowsgui' if os.name == 'nt' else '')
    env = {**os.environ, 'CGO_ENABLED': '0', 'GOTOOLCHAIN': 'local', 'GOFLAGS': '-mod=vendor'}
    r = subprocess.run([go, 'build', '-trimpath', '-ldflags', flags, '-o', out, './cmd/daftard'], cwd=mod, env=env,
                       capture_output=True, text=True, encoding='utf-8', errors='replace', stdin=subprocess.DEVNULL)
    if r.returncode != 0 or not os.path.isfile(out):
        return False, f"`go build` did not build it: {(r.stdout + r.stderr).strip()[-600:]}"
    return True, ''


def fetched_source(src, tag, garden, into):
    """The release's source at `tag`, fetched from `src` into `into`, its tag's signature verified by a key the garden's
    seed/RELEASE-SIGNERS names before any of it is built — bin/dmupgrade.py's own check: (path, how) or (None, why)."""
    r = git('clone', '--quiet', '--depth', '1', '--branch', tag, src, into)
    if r.returncode != 0:
        return None, f"{tag} was not fetched from {src}: {(r.stdout + r.stderr).strip()[:300]}"
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import dmupgrade
    except ImportError as e:
        return None, f"this Python cannot check the release's signature ({e}): run the install with the Python chosen above"
    signed = dmupgrade.tag_signature(into, tag)
    signers = os.path.join(garden, 'seed', 'RELEASE-SIGNERS')
    if signed is None or signed[2] != 'ssh':
        return None, f"{tag} from {src} carries no SSH signature: its source is not built"
    if not os.path.isfile(signers):
        return None, "this garden's release names no keys (seed/RELEASE-SIGNERS): the source is not built"
    ok, why = dmupgrade.verify_signature(signed[0], signed[1], signers)
    if not ok:
        return None, f"{tag} from {src}: {why}; its source is not built"
    return into, f"built from {tag}'s source, fetched from {src}: {why}"


def _get(where):
    """The bytes at a URL, or a file's: a release's asset, or one in a folder on this machine."""
    if re.match(r'^[a-z][a-z0-9+.-]*://', where, re.I) and not where.lower().startswith('file:'):
        with urllib.request.urlopen(where, timeout=300) as resp:
            return resp.read()
    path = urllib.request.url2pathname(urllib.parse.urlparse(where).path) if where.lower().startswith('file:') else where
    with open(path, 'rb') as fh:
        return fh.read()


def downloaded(base, out):
    """The release's binary for this system, from `base` (a release's download URL, or a folder), into `out` — only when
    its bytes have the SHA-256 the release gives beside it: (True, how) or (False, why)."""
    name = asset()
    if not name:
        return False, f"no binary of daftard is built for {sys.platform} on {platform.machine()}: build it with Go"
    sep = '' if base.endswith(('/', '\\')) else ('/' if '://' in base else os.sep)
    try:
        data = _get(base + sep + name)
        said = _get(base + sep + name + '.sha256').decode('ascii', 'replace')
    except (OSError, ValueError) as e:
        return False, f"{name} was not fetched from {base}: {e}"
    m = re.match(r'\s*([0-9a-fA-F]{64})(\s|$)', said)
    if not m:
        return False, f"{name}.sha256 from {base} holds no SHA-256: the binary is not laid"
    have = hashlib.sha256(data).hexdigest()
    if have != m.group(1).lower():
        return False, f"{name} from {base} has the SHA-256 {have}, not the {m.group(1).lower()} the release gives: not laid"
    with open(out, 'wb') as fh:
        fh.write(data)
    os.chmod(out, 0o755)
    return True, (f"the release's {name} from {base}, its SHA-256 {have} as the release gives it (the sum proves the "
                  f"transfer, not the build: the release's binaries are not signed)")


def daftard_run(exe, *args, timeout=600):
    return subprocess.run([exe, *args], capture_output=True, text=True, encoding='utf-8', errors='replace',
                          stdin=subprocess.DEVNULL, timeout=timeout)


def lay(new, dst):
    """The binary at `new` put at `dst`: a daftard running from the one there is stopped first, a save under way
    finishing; on Windows the running file is moved aside, since it cannot be written over."""
    if os.path.isfile(dst):
        try:
            daftard_run(dst, 'stop', timeout=330)
        except (OSError, subprocess.SubprocessError):
            pass
        if os.name == 'nt':
            old = dst + '.old'
            if os.path.exists(old):
                os.remove(old)
            os.replace(dst, old)
    os.replace(new, dst)
    if os.name == 'nt':
        try:
            os.remove(dst + '.old')
        except OSError:
            pass


def answers(listen, wait=0.0):
    """The build of the daftard that answers at `listen` on this machine (its /health), waiting up to `wait` seconds;
    None where none does. Asked directly, never through a proxy the environment names."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    end = time.monotonic() + wait
    while True:
        try:
            with opener.open(f'http://{listen}/health', timeout=3) as resp:
                return str(json.loads(resp.read().decode('utf-8')).get('build') or 'unknown')
        except (OSError, ValueError):
            pass
        if time.monotonic() >= end:
            return None
        time.sleep(0.5)


def start_detached(exe):
    """`daftard serve`, started apart from this process, its output to nothing: daftard keeps its own log."""
    kw = {'stdin': subprocess.DEVNULL, 'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}
    if os.name == 'nt':
        kw['creationflags'] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kw['start_new_session'] = True
    subprocess.Popen([exe, 'serve'], **kw)


def install_daftard(repo, py, say, listen=None, service=True, source=None, binary_from=None):
    """THIS MACHINE'S DAFTARD (see DAFTARD above): its binary laid, this garden served with its routines, what keeps it
    running, and its answer on the loopback. 0 when it answers; 1, having said why, when a step could not be done."""
    def refuse(why):
        print(f"install: daftard: {why}", file=sys.stderr)
        return 1
    main = main_worktree(repo)
    top = git('rev-parse', '--show-toplevel', cwd=repo).stdout.strip() or repo
    if os.path.realpath(main) != os.path.realpath(top):
        return refuse(f"daftard serves a garden's main working copy, not a session's: run `python3 bin/install.py "
                      f"--daftard` in {main}")
    garden = main if os.path.isfile(os.path.join(main, 'GARDEN.md')) else None
    tag = manifest(main, 'daftar_release') if garden else None
    dst = daftard_path()
    folder = os.path.dirname(dst)
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
        if os.name != 'nt':
            os.chmod(folder, 0o700)
    new = dst + '.new'
    # 1) ITS BINARY: built where Go is (or a source is named), else the release's own
    if binary_from is None and (source or shutil.which('go')):
        with tempfile.TemporaryDirectory(prefix='daftard-src-') as t:
            if source and os.path.isdir(source):
                src, how = os.path.abspath(source), f"built from {os.path.abspath(source)}, as it stands"
            elif not source and os.path.isfile(os.path.join(main, 'daftard', 'go.mod')):
                src, how = main, "built from this repository's daftard/"
            elif not tag:
                return refuse("this garden records no release (GARDEN.md `daftar_release`) to build daftard from")
            else:
                src, how = fetched_source(source or UPSTREAM, tag, main, os.path.join(t, 'daftar'))
                if src is None:
                    return refuse(how)
            ok, why = go_build(src, new)
    else:
        if binary_from is None and not tag:
            return refuse("this garden records no release (GARDEN.md `daftar_release`) whose binary to take")
        ok, how = downloaded(binary_from or f"{RELEASES}/{tag}", new)
        why = how
    if not ok:
        if os.path.exists(new):
            os.remove(new)
        return refuse(why)
    lay(new, dst)
    r = daftard_run(dst, 'version', timeout=60)
    laid = (r.stdout.split() + ['', ''])[1]
    say(f"daftard: {how} — laid at {dst} ({r.stdout.strip() or 'its version unread'})")
    if not garden:
        say("daftard: no garden here to serve (no GARDEN.md): run `python3 bin/install.py --daftard` in a garden")
        return 0
    # 2) THIS GARDEN SERVED, ITS ROUTINES TICKED, AND WHAT KEEPS IT RUNNING: daftard's own install
    args = ['install', '--garden', main, '--python', py, '--routines']
    name = manifest(main, 'garden')
    args += ['--name', name] if name else []
    args += ['--listen', listen] if listen else []
    args += [] if service else ['--no-service']
    r = daftard_run(dst, *args, timeout=300)
    for line in (r.stdout + r.stderr).splitlines():
        say(f"  {line}")
    if r.returncode != 0:
        return refuse("its own install did not finish (above)")
    # 3) IT ANSWERS on its loopback: started by the service where one took it, else here
    try:
        with open(os.path.join(state_dir(), 'daftard.json'), encoding='utf-8') as fh:
            at = json.load(fh).get('listen') or '127.0.0.1:8770'
    except (OSError, ValueError) as e:
        return refuse(f"daftard.json does not read: {e}")
    build = answers(at, wait=15)
    if build is None:
        start_detached(dst)
        say("daftard: no service started it here; started now, until this machine stops")
        build = answers(at, wait=90)
    if build is None:
        return refuse(f"it does not answer at {at}: its log is daftard.log in {state_dir()}")
    if laid and build != laid:
        # another daftard holds the address — another account's state, another binary — and is left alone: it is
        # never stopped, nor taken for the one laid
        return refuse(f"another daftard answers at {at} (build {build}), not the one laid ({laid}): it is left as it "
                      f"is; give this one another address (--listen), or stop that one with its own `daftard stop`")
    say(f"daftard: serving at http://{at} (build {build}) — `daftar board` opens this garden's board, "
        f"`daftar serve status` says how it runs, `daftar serve stop` stops it")
    return 0


def main(argv):
    ap = argparse.ArgumentParser(prog='install', description=__doc__.split('\n', 1)[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sign', action='store_true', help="this clone signs its commits with this machine's agent key")
    ap.add_argument('--daftard', action='store_true', help="this machine's daftard: its binary, this garden served, "
                                                           "its routines, what keeps it running")
    ap.add_argument('--listen', help='with --daftard: where its own page listens, on 127.0.0.1 (127.0.0.1:8770)')
    ap.add_argument('--no-service', action='store_true', help='with --daftard: register nothing with the system; '
                                                              'daftard is started here, until the machine stops')
    how = ap.add_mutually_exclusive_group()
    how.add_argument('--source', help='with --daftard: build it from this daftar tree, or this repository at the '
                                      "release's tag")
    how.add_argument('--binary-from', help="with --daftard: take the release's binary from this URL or folder")
    a = ap.parse_args(argv)
    if (a.listen or a.no_service or a.source or a.binary_from) and not a.daftard:
        ap.error('--listen, --no-service, --source and --binary-from go with --daftard')
    d = ({'listen': a.listen, 'service': not a.no_service, 'source': a.source, 'binary_from': a.binary_from}
         if a.daftard else None)
    return install(sign=a.sign, daftard=d)


if __name__ == '__main__':
    for _s in (sys.stdout, sys.stderr):              # a path the console's code page lacks is shown escaped, never a crash
        try:
            _s.reconfigure(errors='backslashreplace')
        except (AttributeError, ValueError):
            pass
    sys.exit(main(sys.argv[1:]))
