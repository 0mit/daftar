"""A garden hub's own key (bin/hub.py `install`, `key`): made once when a hub is initialized for a garden, in the
account's daftar state folder and never in the garden or any repository of it, shown again by `key`; and what the hub
then writes on its own, signed with it as the hub's bean, judged by the hub's four steps like any writer's.

Builds what it needs, as test/core_gate.py does: a release of the core made from this tree, a garden grown from it (the
shop's), a bare hub cloned from it with its hook, a peer's clone, and the hub's own working copy.

install: on a bare hub, the hook and the key — ed25519, no passphrase, under the state folder's `hubs/<garden id>/`,
the folder 0700 and the key 0600, its fingerprint, public line and the statement for the hub's bean printed and the
private key never; run again, the same key, never made over; the hook left as it is when it is already the one install
writes. On an empty hub, the hook and no key until the garden's first commit is there. On a working copy, the key and no
hook: nothing is pushed into a working copy, and a hook there would be a file of the garden's tree. key: the hub's key
shown again, or none said, exit 1. The hub: its key anchored on a bean of kind `instance` by the gardener (class F),
granted `write` through a reading kept in the gardener's bean that leaves out the beans deciding who may do what; its
merge of a bean both sides changed, signed with its key as its bean, taken by the bare hub; a hub's key no bean names,
refused; and the hub refused a grant to itself in the gardener's bean, which the reading leaves out. An agents'
harness granted `write` through a reading: its commit that makes a session bean taken — the grant as the garden stood
before the commit, its reading over the tree the commit leaves —, one that makes a person's bean refused, and one that
changes the gardener's bean refused.

Run: python3 test/hubkey.py   (0 = green; about two minutes, since a save waits for the next minute where its bean was
saved in this one)
"""
import os, re, shutil, stat, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import grow  # noqa: E402 — a release of the core, and a garden grown from it
import safe as dmsafe  # noqa: E402

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


class R:
    def __init__(self, p):
        self.returncode, self.out = p.returncode, p.stdout + p.stderr


T = tempfile.mkdtemp(prefix='hubkey-')
REL, G, HUB, W, H, STATE = (os.path.join(T, n) for n in ('release', 'garden', 'hub.git', 'peer', 'hub-copy', 'state'))


def run(*a, cwd=None, env=None):
    e = {**os.environ, 'GIT_AUTHOR_NAME': 'sam', 'GIT_AUTHOR_EMAIL': 'sam@x', 'GIT_COMMITTER_NAME': 'sam',
         'GIT_COMMITTER_EMAIL': 'sam@x', 'PYTHONIOENCODING': 'utf-8', 'DAFTARD_STATE': STATE, **(env or {})}
    return R(subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=e))


def write(path, t, root=None):
    p = os.path.join(root or G, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t)


def save(what, body, root=None, who='sam', env=None):
    return run(PY, 'bin/save.py', who, what, '--body', body, cwd=root or G, env=env)


def key(name):
    p = os.path.join(T, name + '-key')
    subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-C', name, '-f', p], capture_output=True)
    out = subprocess.run(['ssh-keygen', '-lf', p + '.pub'], capture_output=True, text=True, encoding='utf-8',
                         errors='replace').stdout
    return p, re.search(r'(SHA256:[A-Za-z0-9+/]{43})', out).group(1)


def signing(where, k):
    for a in (('gpg.format', 'ssh'), ('user.signingkey', k), ('commit.gpgsign', 'true')):
        run('git', 'config', *a, cwd=where)


def mode(p):
    return stat.S_IMODE(os.stat(p).st_mode) if os.path.exists(p) else None


def read(p, b=False):
    """A file's text (or bytes), or empty where it is not there: a check that fails says so, and the suite goes on."""
    try:
        with open(p, 'rb' if b else 'r') as fh:
            return fh.read()
    except OSError:
        return b'' if b else ''


BEAN = """---
bean: %s
kind: %s
title: "%s"
summary: "%s"
statements:
%s
---
%s
"""
SSH = bool(shutil.which('ssh-keygen')) and 'check-novalidate' in run('ssh-keygen', '-Y', 'x', cwd=T).out + \
    run('ssh-keygen', '-?', cwd=T).out
try:
    if not SSH:
        print("SKIP  hubkey: this machine has no ssh-keygen that signs and checks (`ssh-keygen -Y`)")
        raise SystemExit
    grow.release(REL)
    r = grow.garden(REL, G, 'sam')
    check("a garden grows from this tree's release", r.returncode == 0, r.out[-600:])
    run(PY, 'bin/install.py')
    SAMK, SAMF = key('sam')
    signing(G, SAMK)
    write('beans/box.md', BEAN % ('box', 'host', "the shop's box", "The machine the garden is kept on.",
                                  '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }', 'The box.'))
    write('beans/notes.md', BEAN % ('notes', 'document', "the shop's notes", "What the shop keeps written down.",
                                    '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }', "The shop's notes."))
    dmsafe.add_statements(os.path.join(G, 'beans', 'sam.md'),
                          f'- name: {{ id: key, by: ssh, of: self, as: "{SAMF}" }}\n- say: {{ by: sam, of: [key], at: now }}\n')
    r = save("the gardener's key, the box and the notes", '- action: [[sam]] carries a key; wrote [[box]] and [[notes]]')
    check("the gardener's key, the box and the notes are committed, signed", r.returncode == 0, r.out[-600:])
    gid = run('git', 'rev-list', '--first-parent', '--max-parents=0', 'HEAD').out.strip()[:12]
    where = os.path.join(STATE, 'hubs', gid)

    # ---- INSTALL ON A BARE HUB: the hook, as before, and the hub's own key
    run('git', 'clone', '-q', '--bare', G, HUB, cwd=T)
    r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'install', HUB)
    fpr = (re.search(r'(SHA256:[A-Za-z0-9+/]{43})', r.out) or ['(no fingerprint printed)'])[0]
    check("install: a bare hub gets its hook, and its own key — made now, in the state folder under its garden's id",
          r.returncode == 0 and os.path.isfile(os.path.join(HUB, 'hooks', 'pre-receive'))
          and os.path.isfile(os.path.join(where, 'key')) and os.path.isfile(os.path.join(where, 'key.pub'))
          and 'made now' in r.out, r.out)
    check("install: the key is ed25519, with no passphrase (nobody sits to give one), and its comment names only the garden",
          (read(os.path.join(where, 'key.pub')).split() + ['', '', ''])[0] == 'ssh-ed25519'
          and (read(os.path.join(where, 'key.pub')).split() + ['', '', ''])[2] == f'hub@{gid}'
          and run('ssh-keygen', '-y', '-P', '', '-f', os.path.join(where, 'key')).returncode == 0)
    if os.name != 'nt':
        check("install: the state folder and the folders it makes in it are 0700, and the key 0600 — this account's alone",
              mode(STATE) == mode(os.path.join(STATE, 'hubs')) == mode(where) == 0o700
              and mode(os.path.join(where, 'key')) == 0o600,
              (mode(STATE), mode(os.path.join(STATE, 'hubs')), mode(where), mode(os.path.join(where, 'key'))))
    check("install: it prints the fingerprint, the public line and the statement for the hub's bean — never the private key",
          f'name: {{ by: ssh, of: self, as: "{fpr}" }}' in r.out and 'ssh-ed25519 AAAA' in r.out
          and 'PRIVATE KEY' not in r.out, r.out)
    secret = (read(os.path.join(where, 'key'), True).splitlines() + [b'', b''])[1]     # the private key's own first line
    inside = [os.path.join(p, f) for d in (G, HUB) for p, _ds, fs in os.walk(d) for f in fs
              if secret in read(os.path.join(p, f), True)]
    check("install: neither the garden nor the hub's repository holds the key", secret and not inside, inside)
    hook = read(os.path.join(HUB, 'hooks', 'pre-receive'))
    os.chmod(os.path.join(HUB, 'hooks', 'pre-receive'), 0o555)
    if os.name != 'nt':
        os.chmod(os.path.join(HUB, 'hooks'), 0o555)       # as a runbook leaves it: root's, which the hub's account cannot write
    r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'install', HUB)
    check("install again: the same key, kept and never made over; the hook it would write is there already, left as it is",
          r.returncode == 0 and fpr in r.out and 'kept' in r.out and 'made now' not in r.out
          and read(os.path.join(HUB, 'hooks', 'pre-receive')) == hook, r.out)
    if os.name != 'nt':
        os.chmod(os.path.join(HUB, 'hooks'), 0o755)
    r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'key', HUB)
    check("key: the hub's key shown again — its fingerprint and the statement for its bean",
          r.returncode == 0 and fpr in r.out and 'name: { by: ssh' in r.out and 'PRIVATE KEY' not in r.out, r.out)
    r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'key', HUB, env={'DAFTARD_STATE': os.path.join(T, 'elsewhere')})
    check("key: where this account keeps none, it says so, and what makes it — exit 1",
          r.returncode == 1 and 'install' in r.out and not os.path.exists(os.path.join(T, 'elsewhere')), r.out)

    # ---- AN EMPTY HUB, AND A WORKING COPY
    empty = os.path.join(T, 'empty.git')
    run('git', 'init', '-q', '--bare', empty, cwd=T)
    r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'install', empty, env={'DAFTARD_STATE': os.path.join(T, 's2')})
    r2 = run(PY, os.path.join(G, 'bin', 'hub.py'), 'key', empty, env={'DAFTARD_STATE': os.path.join(T, 's2')})
    check("install: an empty hub gets its hook, and no key until the garden's first commit is there — said so, by "
          "`key` too", r.returncode == 0 and os.path.isfile(os.path.join(empty, 'hooks', 'pre-receive'))
          and not os.path.exists(os.path.join(T, 's2', 'hubs')) and 'first commit' in r.out
          and r2.returncode == 1 and 'first commit' in r2.out, r.out + r2.out)
    run('git', 'clone', '-q', HUB, H, cwd=T)
    r = run(PY, os.path.join(H, 'bin', 'hub.py'), 'install', H)
    check("install: a working copy — the hub daftard keeps — gets the same key (one account, one hub of the garden) and "
          "no hook: nothing is pushed into it, and a hook there would be a file of the garden's tree",
          r.returncode == 0 and fpr in r.out and 'kept' in r.out and not os.path.exists(os.path.join(H, 'hooks'))
          and not os.path.exists(os.path.join(H, '.git', 'hooks', 'pre-receive'))
          and run('git', 'status', '--porcelain', cwd=H).out.strip() == '', r.out)
    r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'install', os.path.join(T, 'nowhere'))
    check("install: a folder that is no repository is refused, nothing written",
          r.returncode == 2 and not os.path.exists(os.path.join(T, 'nowhere')), r.out)

    # ---- THE HUB AS A WRITER: its key on its bean (class F, the gardener's), `write` through a reading that leaves
    # out what decides who may do what; its clean merge signed with its key, taken like any writer's
    hubk = os.path.join(where, 'key')
    write('beans/box-hub.md', BEAN % ('box-hub', 'instance', "the shop's garden hub on the box",
                                      "The garden kept and judged on the box: it merges what needs no person, and signs "
                                      "what it writes with its own key.",
                                      '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }\n'
                                      '  - be: { by: self, at: box, as: habitat }\n'
                                      f'  - name: {{ id: key, by: ssh, of: self, as: "{fpr}" }}', 'The hub.'))
    dmsafe.add_statements(os.path.join(G, 'beans', 'sam.md'),
                          '- reckon: { id: hub-merges, reading: { what: "the beans a merge by a hub may change: every '
                          'bean but the gardener\'s, a person\'s, an agreement\'s and the hubs\' own, whose statements '
                          'decide who may do what", steps: [ { id: all, op: select, where: [ { path: bean, "≠": sam }, '
                          '{ path: bean, "≠": box-hub } ] }, { id: people, op: select, kind: person }, { id: agreements, '
                          'op: select, kind: contract }, { id: some, op: minus, of: all, with: people }, { id: these, '
                          'op: minus, of: some, with: agreements } ] } }\n'
                          '- grant: { id: hub-writes, by: self, as: write, of: [hub-merges], to: [box-hub] }\n'
                          '- say: { by: sam, of: [hub-merges, hub-writes], at: now }\n')
    r = save("the box's hub, its key and what it may merge",
             "- action: wrote [[box-hub]], its key named (class F, the gardener's); [[sam]] grants it `write` through "
             "the reading `hub-merges`")
    run('git', 'remote', 'add', 'hub', HUB)
    r2 = run('git', 'push', '-q', 'hub', 'HEAD:master')
    may = run(PY, '-c', "import sys, importlib; sys.path.insert(0, 'bin'); p = importlib.import_module('pass'); "
                        "print([p.may('box-hub', 'write', b).granted for b in ('notes', 'box', 'sam', 'box-hub')])")
    check("the hub's bean, kind `instance`, carries its key; the gardener's grant opens `write` on the notes and the box, "
          "never on the gardener's bean or the hub's own", r.returncode == 0 and r2.returncode == 0
          and may.out.strip() == '[True, True, False, False]', r.out[-400:] + r2.out + may.out)
    for d in (H, W):
        if not os.path.isdir(d):
            run('git', 'clone', '-q', HUB, d, cwd=T)
        run('git', 'fetch', '-q', 'origin', cwd=d)
        run('git', 'reset', '-q', '--hard', 'origin/master', cwd=d)
        run(PY, 'bin/install.py', cwd=d)
        signing(d, SAMK)
    # the peer and the hub's copy both change the notes; the hub's copy merges, as the hub, signed with its own key
    dmsafe.add_statements(os.path.join(W, 'beans', 'notes.md'), '- use: { id: from-peer, by: self, of: box }\n'
                                                                '- say: { by: sam, of: [from-peer], at: now }\n')
    r = save('a note on the peer', '- action: [[notes]] on the peer', root=W)
    r2 = run('git', 'push', '-q', 'origin', 'HEAD:master', cwd=W)
    dmsafe.add_statements(os.path.join(H, 'beans', 'notes.md'), '- use: { id: from-hub, by: self, of: box }\n'
                                                                '- say: { by: sam, of: [from-hub], at: now }\n')
    r3 = save("a note on the hub's copy", "- action: [[notes]] on the hub's copy", root=H)
    as_hub = {'GIT_AUTHOR_NAME': 'box-hub', 'GIT_AUTHOR_EMAIL': 'box-hub@shop.daftar.invalid',
              'GIT_COMMITTER_NAME': 'box-hub', 'GIT_COMMITTER_EMAIL': 'box-hub@shop.daftar.invalid',
              'GIT_CONFIG_COUNT': '3', 'GIT_CONFIG_KEY_0': 'gpg.format', 'GIT_CONFIG_VALUE_0': 'ssh',
              'GIT_CONFIG_KEY_1': 'user.signingkey', 'GIT_CONFIG_VALUE_1': hubk,
              'GIT_CONFIG_KEY_2': 'commit.gpgsign', 'GIT_CONFIG_VALUE_2': 'true'}
    run('git', 'config', 'remote.origin.daftar-push', 'true', cwd=H)
    r4 = run(PY, 'bin/sync.py', '--by', 'box-hub', 'origin', cwd=H, env=as_hub)
    merge = run('git', 'cat-file', 'commit', 'HEAD', cwd=H).out
    allowed = os.path.join(T, 'allowed')
    write('allowed', 'box-hub@shop.daftar.invalid ' + read(hubk + '.pub'), root=T)
    verified = run('git', '-c', f'gpg.ssh.allowedSignersFile={allowed}', 'log', '--show-signature', '-1', cwd=H).out
    check("the hub merges what the peer brought beside its own, as its bean, signed with its own key; the bare hub takes it",
          r.returncode == 0 and r2.returncode == 0 and r3.returncode == 0 and r4.returncode == 0 and 'pushed' in r4.out
          and merge.count('\nparent ') == 2 and 'author box-hub' in merge
          and 'Good "git" signature for box-hub@shop.daftar.invalid' in verified,
          r.out[-300:] + r2.out + r3.out[-300:] + r4.out[-800:] + verified[-400:])
    # what the reading leaves out: the hub granting itself `ratify:G` in the gardener's bean, said as the gardener's
    run('git', 'fetch', '-q', 'origin', cwd=H)
    run('git', 'reset', '-q', '--hard', 'origin/master', cwd=H)
    dmsafe.add_statements(os.path.join(H, 'beans', 'sam.md'),
                          '- grant: { id: hub-code, by: self, as: ratify, class: G, of: [self], to: [box-hub] }\n'
                          '- say: { by: sam, of: [hub-code], at: now }\n')
    save('the hub grants itself', '- action: [[sam]]', root=H, who='box-hub', env=as_hub)
    r = run('git', 'push', '-q', 'origin', 'HEAD:master', cwd=H, env=as_hub)
    check("the hub may not write the gardener's bean, so it cannot grant itself there what the gardener did not — refused",
          r.returncode != 0 and 'beans/sam.md needs a grant of `write`' in r.out, r.out[-600:])
    # a key no bean names writes nothing
    run('git', 'reset', '-q', '--hard', 'origin/master', cwd=H)
    otherk, _f = key('another-hub')
    dmsafe.add_statements(os.path.join(H, 'beans', 'notes.md'), '- use: { id: from-another, by: self, of: box }\n'
                                                                '- say: { by: sam, of: [from-another], at: now }\n')
    save('a note by a hub no bean names', '- action: [[notes]]', root=H, who='box-hub',
         env={**as_hub, 'GIT_CONFIG_VALUE_1': otherk})
    r = run('git', 'push', '-q', 'origin', 'HEAD:master', cwd=H)
    check("a hub's key no bean names is no writer: its commit is refused", r.returncode != 0 and 'no bean carries' in r.out,
          r.out[-600:])

    # ---- AN AGENT'S NEW BEAN: its grant as the garden stood before the commit, the grant's reading over the tree the
    # commit leaves — a session bean it makes is in the reading and taken; a person's bean it makes is not, refused
    run('git', 'reset', '-q', '--hard', 'origin/master', cwd=H)
    agk, agf = key('agent')
    write('beans/claude-code-box.md', BEAN % ('claude-code-box', 'instance', "the agents' harness on the box",
                                              "The harness agents work in on the box, whose key signs their commits.",
                                              '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }\n'
                                              '  - be: { by: self, at: box, as: habitat }\n'
                                              f'  - name: {{ id: key, by: ssh, of: self, as: "{agf}" }}', 'The harness.'),
          root=H)
    dmsafe.add_statements(os.path.join(H, 'beans', 'sam.md'),
                          '- reckon: { id: agent-writes, reading: { what: "the beans an agent may write: every bean but '
                          'the gardener\'s, a person\'s, an agreement\'s and the agents\' own, whose statements decide who '
                          'may do what", steps: [ { id: all, op: select, where: [ { path: bean, "≠": sam }, { path: bean, '
                          '"≠": claude-code-box } ] }, { id: people, op: select, kind: person }, { id: agreements, op: '
                          'select, kind: contract }, { id: some, op: minus, of: all, with: people }, { id: these, op: '
                          'minus, of: some, with: agreements } ] } }\n'
                          '- grant: { id: agents-write, by: self, as: write, of: [agent-writes], to: [claude-code-box] }\n'
                          '- say: { by: sam, of: [agent-writes, agents-write], at: now }\n')
    r = save("the agents' harness, its key and what it may write",
             "- action: wrote [[claude-code-box]], its key named (class F, the gardener's); [[sam]] grants it `write` "
             "through the reading `agent-writes`", root=H)
    r2 = run('git', 'push', '-q', 'origin', 'HEAD:master', cwd=H)
    check("the gardener names an agents' harness by its key and grants it `write` through a reading", r.returncode == 0
          and r2.returncode == 0, r.out[-400:] + r2.out)
    as_agent = {**as_hub, 'GIT_AUTHOR_NAME': 'session-box-1', 'GIT_AUTHOR_EMAIL': 'session-box-1@shop.daftar.invalid',
                'GIT_COMMITTER_NAME': 'session-box-1', 'GIT_COMMITTER_EMAIL': 'session-box-1@shop.daftar.invalid',
                'GIT_CONFIG_VALUE_1': agk}
    write('beans/session-box-1.md', BEAN % ('session-box-1', 'session', "an agent's session on the box",
                                            "What one agent did on the box, and how the next learns it.",
                                            '  - make: { by: self, at: now }\n  - own: { by: sam, of: self }', 'Opened.'),
          root=H)
    r = save("an agent's session opened", '- action: opened [[session-box-1]]', root=H, who='session-box-1', env=as_agent)
    r2 = run('git', 'push', '-q', 'origin', 'HEAD:master', cwd=H, env=as_agent)
    check("an agent's commit that makes a session bean is taken: the bean is in the grant's reading as the commit leaves "
          "the garden", r.returncode == 0 and r2.returncode == 0, r.out[-400:] + r2.out[-800:])
    write('beans/p-0a1b2c3d.md', '---\nbean: p-0a1b2c3d\nkind: person\ntitle: "p-0a1b2c3d"\nsummary: "a person whose '
                                 'name and contacts are held off git"\nstatements:\n  - say: { by: sam, at: now }\n'
                                 '---\nA person.\n', root=H)
    r0 = save("a person written by an agent", '- action: wrote [[p-0a1b2c3d]]', root=H, who='session-box-1',
              env=as_agent)
    r = run('git', 'push', '-q', 'origin', 'HEAD:master', cwd=H, env=as_agent)
    check("an agent's commit that makes a person's bean is refused: the reading leaves a person out, read as the commit "
          "leaves the garden", r0.returncode == 0 and r.returncode != 0
          and 'beans/p-0a1b2c3d.md needs a grant of `write`' in r.out, r0.out[-600:] + r.out[-600:])
    run('git', 'reset', '-q', '--hard', 'origin/master', cwd=H)
    dmsafe.add_statements(os.path.join(H, 'beans', 'sam.md'),
                          '- grant: { id: agents-all, by: self, as: write, of: [self], to: [claude-code-box] }\n'
                          '- say: { by: sam, of: [agents-all], at: now }\n')
    r0 = save("the agent grants itself", '- action: [[sam]]', root=H, who='session-box-1', env=as_agent)
    r = run('git', 'push', '-q', 'origin', 'HEAD:master', cwd=H, env=as_agent)
    check("an agent's commit that changes the gardener's bean is refused", r0.returncode == 0 and r.returncode != 0
          and 'beans/sam.md needs a grant of `write`' in r.out, r0.out[-600:] + r.out[-600:])
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nhubkey: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
