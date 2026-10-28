"""The writers' keys and a hub that reports (the next version's design, P2 and P3's code): this machine's agent key,
made by bin/install.py and its name proposed to the gardener; the save signing with the key the clone names, and
refusing one it is told is the gardener's ratifying key; and bin/hub.py installed `--report`, judging every push as it
would, refusing nothing of the garden's, logging what it would refuse, and writing a receipt signed by its key on each
commit it judged — then installed again without it, refusing.

Builds what it needs, as test/hubkey.py does: a release of the core made from this tree, a garden grown from it (the
shop's, its gardener Sam), a bare hub cloned from it, and an agent's clone of the hub on the same machine.

The agent key: made by install where the state folder holds none, ed25519 with no passphrase, under `agent/`, 0700 and
0600; its fingerprint and the `name` for the bean of this machine's agent harness printed, and the proposal written out
in the clone's git directory, off git; made once, kept after; `--sign` sets a clone to sign with it, and leaves a clone
set to another key as it is. The save: a commit signed where commit.gpgsign is set, said with which key; refused before
anything is written for a key this clone is told is the gardener's ratifying key, by its fingerprint or its public key
file, and for a key ssh-keygen reads no fingerprint of. The hub, reporting: a good commit taken, with a receipt signed
by the hub's key; a commit the gate refuses, pushed with --no-verify, taken and logged as it would be refused, its
receipt saying so; the agent's commit, its key named on its harness's bean and granted `write`, taken; the agent's
change to the law reported for `ratify:G`; a forced push over the receipts' ref refused; `report` counting it all,
`receipts` naming the commits no receipt is on. Refusing: the gate's refusal and the agent's change to the law refused,
no receipt written, a good commit taken. A merge the agent makes whose second parent brought the gardener's anchor,
taken (#195), each commit of that push given its own receipt. A receipt where the hub keeps no key, written and said to
be unsigned. The report's day: `--since <day>` the garden's day, from its midnight in GARDEN.md's zone, and a moment
compared as an instant, each said with the instant it was read as; in UTC where the garden names no zone, said so.

Run: python3 test/hubreport.py   (0 = green; about three minutes)
"""
import json, os, re, shutil, stat, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import grow  # noqa: E402 — a release of the core, and a garden grown from it
import safe as dmsafe  # noqa: E402
import install as dminstall  # noqa: E402 — the harness bean's name, as install proposes it

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


class R:
    def __init__(self, p):
        self.returncode, self.out = p.returncode, p.stdout + p.stderr


T = tempfile.mkdtemp(prefix='hubreport-')
REL, G, HUB, A, STATE = (os.path.join(T, n) for n in ('release', 'garden', 'hub.git', 'agent', 'state'))
AGENT = f"claude-code-{dminstall.machine()}"


def run(*a, cwd=None, env=None):
    e = {**os.environ, 'GIT_AUTHOR_NAME': 'sam', 'GIT_AUTHOR_EMAIL': 'sam@x', 'GIT_COMMITTER_NAME': 'sam',
         'GIT_COMMITTER_EMAIL': 'sam@x', 'PYTHONIOENCODING': 'utf-8', 'DAFTARD_STATE': STATE, **(env or {})}
    return R(subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=e))


AS_AGENT = {'GIT_AUTHOR_NAME': 'agent', 'GIT_AUTHOR_EMAIL': 'agent@x', 'GIT_COMMITTER_NAME': 'agent',
            'GIT_COMMITTER_EMAIL': 'agent@x'}


def write(path, t, root=None):
    p = os.path.join(root or G, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t)


def read(p):
    try:
        with open(p, encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return ''


def save(what, body, root=None, who='sam', env=None):
    return run(PY, 'bin/save.py', who, what, '--body', body, cwd=root or G, env=env)


def push(root=None, env=None, ref='HEAD:master'):
    return run('git', 'push', 'hub' if (root or G) == G else 'origin', ref, cwd=root or G, env=env)


def key(name):
    p = os.path.join(T, name + '-key')
    subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-C', name, '-f', p], capture_output=True)
    out = subprocess.run(['ssh-keygen', '-lf', p + '.pub'], capture_output=True, text=True, encoding='utf-8',
                         errors='replace').stdout
    return p, re.search(r'(SHA256:[A-Za-z0-9+/]{43})', out).group(1)


def mode(p):
    return stat.S_IMODE(os.stat(p).st_mode) if os.path.exists(p) else None


def receipt(sha):
    return run('git', 'notes', '--ref', 'refs/notes/daftar', 'show', sha, cwd=HUB).out


def last_log():
    lines = [l for l in read(os.path.join(HUB, 'daftar', 'hub.log')).split('\n') if l.strip()]
    return json.loads(lines[-1]) if lines else {}


def head(root=None):
    return run('git', 'rev-parse', 'HEAD', cwd=root or G).out.strip()


def bad_commit(root=None, env=None):
    """A bean the gate refuses — a verb no row of the law has — committed past the clone's gate."""
    write('beans/bad.md', '---\nbean: bad\nkind: document\ntitle: "bad"\nsummary: "A bean the gate refuses."\n'
                          'statements:\n  - frobnicate: { by: sam }\n---\nBad.\n', root=root)
    run('git', 'add', '-A', cwd=root, env=env)
    return run('git', 'commit', '-q', '--no-verify', '-m', 'a bean the gate refuses', cwd=root, env=env)


def law_commit(root, env):
    """The agent's change to the law: a line of VOCAB.md, committed past the clone's gate."""
    with open(os.path.join(root, 'VOCAB.md'), 'a', encoding='utf-8', newline='\n') as fh:
        fh.write("\n<!-- an agent's line -->\n")
    run('git', 'add', '-A', cwd=root, env=env)
    return run('git', 'commit', '-q', '--no-verify', '-m', 'the law, changed by an agent', cwd=root, env=env)


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
        print("SKIP  hubreport: this machine has no ssh-keygen that signs and checks (`ssh-keygen -Y`)")
        raise SystemExit
    grow.release(REL)
    r = grow.garden(REL, G, 'sam')
    check("a garden grows from this tree's release", r.returncode == 0, r.out[-600:])

    # ---- THE AGENT KEY: made by install where none is, its name proposed, never written into the garden
    r = run(PY, 'bin/install.py')
    ak = os.path.join(STATE, 'agent', 'key')
    afpr = (re.search(r'agent key of this machine: (SHA256:[A-Za-z0-9+/]{43})', r.out) or [None, None])[1]
    proposal = os.path.join(G, '.git', 'daftar', 'agent-key.proposal.md')
    check("install: this machine's agent key, made now in the state folder under agent/, ed25519 with no passphrase",
          r.returncode == 0 and afpr and 'made now' in r.out and os.path.isfile(ak)
          and read(ak + '.pub').split()[:1] == ['ssh-ed25519']
          and run('ssh-keygen', '-y', '-P', '', '-f', ak).returncode == 0, r.out)
    if os.name != 'nt':
        check("install: the agent's folder 0700 and its key 0600 — this account's alone",
              mode(os.path.join(STATE, 'agent')) == 0o700 and mode(ak) == 0o600,
              (mode(os.path.join(STATE, 'agent')), mode(ak)))
    check("install: the `name` for the bean of this machine's agent harness is proposed to the gardener (class F), and "
          "written out whole in the clone's git directory — never in the garden's tree",
          f'name: {{ id: agent-key, by: ssh, of: self, as: "{afpr}" }}' in r.out and f'beans/{AGENT}.md' in r.out
          and 'class F' in r.out and afpr in read(proposal) and 'never `as: ratify`' in read(proposal)
          and run('git', 'status', '--porcelain').out.strip() == '' and 'PRIVATE KEY' not in r.out, r.out)
    r2 = run(PY, 'bin/install.py')
    check("install again: the same key, kept, never made over", r2.returncode == 0 and afpr in r2.out and 'kept' in r2.out
          and 'made now' not in r2.out, r2.out)

    SAMK, SAMF = key('sam')
    for a in (('gpg.format', 'ssh'), ('user.signingkey', SAMK), ('commit.gpgsign', 'true')):
        run('git', 'config', *a)
    r = run(PY, 'bin/install.py', '--sign')
    check("install --sign: a clone set to sign with another key — the gardener's — is left as it is, and told so",
          'left as it is' in r.out and run('git', 'config', 'user.signingkey').out.strip() == SAMK, r.out)

    # the gardener's key, the box, the notes, and the agents' harness on this machine — its key named and its grants
    # given by the gardener: `write` and `enact` on every bean but those that decide who may do what, never `ratify`
    write('beans/box.md', BEAN % ('box', 'host', "the shop's box", "The machine the garden is kept on.",
                                  '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }', 'The box.'))
    write('beans/notes.md', BEAN % ('notes', 'document', "the shop's notes", "What the shop keeps written down.",
                                    '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }', "The shop's notes."))
    write(f'beans/{AGENT}.md', BEAN % (AGENT, 'instance', "the agents' harness on the box",
                                       "Where the shop's agents run: each signs with this machine's agent key.",
                                       '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }\n'
                                       '  - be: { by: self, at: box, as: habitat }\n'
                                       f'  - name: {{ id: agent-key, by: ssh, of: self, as: "{afpr}" }}', 'The agents.'))
    dmsafe.add_statements(os.path.join(G, 'beans', 'sam.md'),
                          f'- name: {{ id: key, by: ssh, of: self, as: "{SAMF}" }}\n'
                          '- reckon: { id: agent-writes, reading: { what: "the beans an agent may write: every bean but '
                          'the gardener\'s, a person\'s, an agreement\'s and the agents\' own, whose statements decide '
                          'who may do what", steps: [ { id: all, op: select, where: [ { path: bean, "≠": sam }, '
                          f'{{ path: bean, "≠": {AGENT} }} ] }}, {{ id: people, op: select, kind: person }}, '
                          '{ id: agreements, op: select, kind: contract }, { id: some, op: minus, of: all, with: people },'
                          ' { id: these, op: minus, of: some, with: agreements } ] } }\n'
                          f'- grant: {{ id: agents-write, by: self, as: write, of: [agent-writes], to: [{AGENT}] }}\n'
                          f'- grant: {{ id: agents-enact, by: self, as: enact, of: [agent-writes], to: [{AGENT}] }}\n'
                          '- say: { by: sam, of: [key, agent-writes, agents-write, agents-enact], at: now }\n')
    r = save("the gardener's key, the box, the notes, and the agents' harness",
             f"- action: [[sam]] carries a key and grants [[{AGENT}]] `write` and `enact`; wrote [[box]], [[notes]] and "
             f"[[{AGENT}]], its key named (class F, the gardener's)")
    check("save: a clone that signs — the gardener's commit is signed, and the save says with which key",
          r.returncode == 0 and f'signed with {SAMF}' in r.out and 'gpgsig' in run('git', 'cat-file', 'commit',
                                                                                   'HEAD').out, r.out[-800:])

    # ---- THE SAVE REFUSES THE GARDENER'S RATIFYING KEY, as this clone is told it
    entries = read(os.path.join(G, 'log', 'journal.md'))
    for told, how in ((SAMF, 'by its fingerprint'), (SAMK + '.pub', 'by its public key file')):
        run('git', 'config', 'daftar.ratifyingKey', told)
        write('beans/notes.md', read(os.path.join(G, 'beans', 'notes.md')).replace("written down.", "written down!"))
        r = save('the notes, saved with the ratifying key', '- action: [[notes]]')
        check(f"save: refused before anything is written, signing with a key this clone is told ({how}) is the "
              f"gardener's ratifying key", r.returncode == 2 and 'ratifying key' in r.out and SAMF in r.out
              and read(os.path.join(G, 'log', 'journal.md')) == entries, r.out[-800:])
        run('git', 'checkout', '-q', '--', 'beans/notes.md')
    run('git', 'config', '--unset-all', 'daftar.ratifyingKey')
    run('git', 'config', 'user.signingkey', os.path.join(T, 'no-such-key'))
    write('beans/notes.md', read(os.path.join(G, 'beans', 'notes.md')).replace("written down.", "written down!"))
    r = save('the notes, with no key to sign', '- action: [[notes]]')
    check("save: refused before anything is written where commit.gpgsign is set and the key is no SSH key it can read",
          r.returncode == 2 and 'no SSH key' in r.out and read(os.path.join(G, 'log', 'journal.md')) == entries,
          r.out[-800:])
    run('git', 'checkout', '-q', '--', 'beans/notes.md')
    run('git', 'config', 'user.signingkey', SAMK)

    # ---- THE HUB, REPORTING
    run('git', 'clone', '-q', '--bare', G, HUB, cwd=T)
    r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'install', HUB, '--report')
    pre, post = read(os.path.join(HUB, 'hooks', 'pre-receive')), read(os.path.join(HUB, 'hooks', 'post-receive'))
    gid = run('git', 'rev-list', '--first-parent', '--max-parents=0', 'HEAD').out.strip()[:12]
    hubk = os.path.join(STATE, 'hubs', gid, 'key')
    hubf = dminstall.ssh_fingerprint(hubk)
    check("install --report: the hook judges and reports, a second hook writes the receipts, and the hub's key is made",
          r.returncode == 0 and 'pre-receive --report' in pre and 'post-receive' in post and 'REPORTS' in r.out
          and os.path.isfile(hubk) and hubf, r.out)
    run('git', 'remote', 'add', 'hub', HUB)
    write('beans/notes.md', read(os.path.join(G, 'beans', 'notes.md')).replace("written down.", "written down, by Sam."))
    save('the notes, by the gardener', '- action: [[notes]]')
    good = head()
    r = push()
    rc = receipt(good)
    check("reporting: the gardener's good commit is taken, and its receipt — the verdict, the writer and the key, the law "
          "and the judge — is on refs/notes/daftar, signed by the hub's key",
          r.returncode == 0 and 'verdict: taken' in rc and f'writer: sam, by the key {SAMF}' in rc
          and re.search(r'^law: core@[0-9.]+, sha256:[0-9a-f]{64}$', rc, re.M) and 'judge: bin/hub.py of ' in rc
          and 'mode: reporting' in rc and 'not judged at the hub' in rc and '-----BEGIN SSH SIGNATURE-----' in rc
          and 'receipt written' in r.out, r.out + rc)
    check("...and it says the commit's own rules were replayed against its parent (core 3.5, II.3)",
          re.search(r'^replay: replayed against its parent$', rc, re.M), rc)
    r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'receipts', HUB, f'{good}^!')
    check("receipts: the commit's receipt verifies, signed by this hub's key", r.returncode == 0 and good[:10] in r.out
          and f'signed by {hubf}' in r.out and "this hub's key" in r.out and 'with none' in r.out, r.out)

    c = bad_commit()
    bad = head()
    r = push()
    rc, log = receipt(bad), last_log()
    check("reporting: a commit the gate refuses, pushed past the clone's gate with --no-verify, is taken — shown to the "
          "writer and logged as it would be refused, its receipt saying so",
          c.returncode == 0 and r.returncode == 0 and 'WOULD REFUSE' in r.out and 'does not pass the gate' in r.out
          and log.get('verdict') == 'would refuse' and log.get('mode') == 'reporting'
          and 'verdict: taken, and would be refused' in rc and 'why: ' in rc,
          c.out + r.out[-1200:] + json.dumps(log)[:600] + rc)
    run('git', 'rm', '-q', 'beans/bad.md')
    save('the bean the gate refuses, taken out', '- action: [[bad]] taken out')
    r = push()
    check("reporting: the gardener's commit that takes it out is taken, the gate passing at its tip",
          r.returncode == 0 and 'WOULD REFUSE' not in r.out and last_log().get('verdict') == 'taken', r.out[-800:])

    run('git', 'clone', '-q', HUB, A, cwd=T)
    for k, v in (('user.name', 'agent'), ('user.email', 'agent@x')):
        run('git', 'config', k, v, cwd=A)
    r = run(PY, 'bin/install.py', '--sign', cwd=A)
    check("install --sign in the agent's clone: the same key, kept, and the clone signs with it",
          r.returncode == 0 and 'kept' in r.out and afpr in r.out and 'signs its commits with it' in r.out
          and run('git', 'config', 'user.signingkey', cwd=A).out.strip() == ak
          and run('git', 'config', 'commit.gpgsign', cwd=A).out.strip() == 'true', r.out)
    dmsafe.add_statements(os.path.join(A, 'beans', 'notes.md'), '- use: { id: from-agent, by: self, of: box }\n'
                                                                '- say: { by: sam, of: [from-agent], at: now }\n')
    r = save("a note, by an agent", '- action: [[notes]]', root=A, who=AGENT, env=AS_AGENT)
    mine = head(A)
    r2 = push(A, AS_AGENT)
    rc = receipt(mine)
    check("reporting: the agent's commit, signed with this machine's agent key, which its harness's bean names and the "
          "gardener grants `write`, is taken — its receipt names the harness as the writer",
          r.returncode == 0 and f'signed with {afpr}' in r.out and r2.returncode == 0 and 'WOULD REFUSE' not in r2.out
          and f'writer: {AGENT}, by the key {afpr}' in rc, r.out[-600:] + r2.out[-800:] + rc)
    c = law_commit(A, AS_AGENT)
    law = head(A)
    r = push(A, AS_AGENT)
    check("reporting: the agent's change to the law is reported, `ratify:G`, and taken",
          c.returncode == 0 and r.returncode == 0 and 'WOULD REFUSE' in r.out and 'VOCAB.md needs a grant of `ratify:G`'
          in r.out and 'verdict: taken, and would be refused' in receipt(law), c.out + r.out[-1200:])
    run('git', 'notes', '--ref', 'refs/notes/daftar', 'add', '-m', 'a receipt nobody judged', 'HEAD', cwd=A,
        env=AS_AGENT)
    r = push(A, AS_AGENT, '+refs/notes/daftar:refs/notes/daftar')        # forced: git refuses no forced push itself
    check("a forced push over the receipts' ref is refused, reporting or not: they are the hub's own",
          r.returncode != 0 and "receipts are its own" in r.out
          and run('git', 'rev-parse', '-q', '--verify', 'refs/notes/daftar', cwd=A).out.strip() !=
          run('git', 'rev-parse', '-q', '--verify', 'refs/notes/daftar', cwd=HUB).out.strip(), r.out[-800:])
    r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'report', HUB)
    check("report: the log counted — six ref updates, three taken, two that would have been refused, one refused — and "
          "each that was not simply taken listed",
          r.returncode == 0 and '6 ref updates judged: 3 taken, 2 would have been refused (reporting), 1 refused' in r.out
          and 'ratify:G' in r.out and 'does not pass the gate' in r.out, r.out[-1500:])
    r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'receipts', HUB)
    check("receipts: the commits the hub judged carry one, and those it held before it reported carry none — named, "
          "exit 1", r.returncode == 1 and 'with none' in r.out and 'no receipt' in r.out and good[:10] in r.out, r.out)

    # ---- THE HUB, REFUSING
    r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'install', HUB)
    check("install without --report: the hook refuses from now on", r.returncode == 0 and '--report' not in
          read(os.path.join(HUB, 'hooks', 'pre-receive')) and 'installed' in r.out, r.out)
    run('git', 'fetch', '-q', 'hub')
    run('git', 'reset', '-q', '--hard', 'hub/master')
    bad_commit()
    bad = head()
    r = push()
    check("refusing: the commit the gate refuses, pushed with --no-verify, is refused, logged, and given no receipt",
          r.returncode != 0 and 'REFUSED' in r.out and 'does not pass the gate' in r.out
          and last_log().get('verdict') == 'refused' and run('git', 'cat-file', '-e', bad, cwd=HUB).returncode != 0,
          r.out[-1200:])
    run('git', 'reset', '-q', '--hard', 'hub/master')
    # THE COMMIT'S OWN RULES, REPLAYED (core 3.5, II.3): a tree the gate takes, made by a commit its hook refuses
    write('beans/notes.md', read(os.path.join(G, 'beans', 'notes.md')).replace("by Sam.", "by Sam, unsaid."))
    run('git', 'add', '-A')
    run('git', 'commit', '-q', '--no-verify', '-m', 'a change no entry names')
    unsaid = head()
    r = push()
    check("refusing: a commit whose tree the gate takes but whose own rules its hook refuses — a bean changed and named "
          "by no entry, pushed with --no-verify — is refused at the hub, its rules replayed against its parent",
          r.returncode != 0 and 'its own rules refuse it, replayed against its parent' in r.out
          and 'named by no journal entry it adds' in r.out and 'does not pass the gate' not in r.out
          and run('git', 'cat-file', '-e', unsaid, cwd=HUB).returncode != 0, r.out[-1200:])
    run('git', 'reset', '-q', '--hard', 'hub/master')
    run('git', 'fetch', '-q', 'origin', cwd=A)
    run('git', 'reset', '-q', '--hard', 'origin/master', cwd=A)
    law_commit(A, AS_AGENT)
    r = push(A, AS_AGENT)
    check("refusing: the agent's change to the law, signed with the agent key, is refused for `ratify:G`",
          r.returncode != 0 and 'REFUSED' in r.out and 'VOCAB.md needs a grant of `ratify:G`' in r.out, r.out[-1200:])
    run('git', 'reset', '-q', '--hard', 'origin/master', cwd=A)
    write('beans/notes.md', read(os.path.join(G, 'beans', 'notes.md')).replace("by Sam.", "by Sam, again."))
    save('the notes, again', '- action: [[notes]]')
    r = push()
    check("refusing: the gardener's good commit is taken, its receipt saying the hub refuses",
          r.returncode == 0 and 'mode: refusing' in receipt(head()) and 'verdict: taken' in receipt(head()), r.out)

    # ---- A MERGE ANSWERS FOR WHAT IT DECIDED ITSELF (#195): the gardener names the notes once (class F), the agent
    # writes beside it and merges; the merge brings the gardener's anchor and decides nothing of its own — taken
    run('git', 'fetch', '-q', 'origin', cwd=A)
    run('git', 'reset', '-q', '--hard', 'origin/master', cwd=A)
    uid = '0b6c4e9a-3f1d-4c2b-9a7e-5d8f1e2a3b4c'
    dmsafe.add_statements(os.path.join(G, 'beans', 'notes.md'), f'- name: {{ id: notes-id, by: uuid, of: self, as: '
                                                                f'"{uid}" }}\n- say: {{ by: sam, of: [notes-id], at: now }}\n')
    r0 = save("the notes' uuid, the gardener's", '- action: [[notes]] named once')
    r1 = push()
    dmsafe.add_statements(os.path.join(A, 'beans', 'notes.md'), '- use: { id: beside-name, by: self, of: box }\n'
                                                                '- say: { by: sam, of: [beside-name], at: now }\n')
    r2 = save('beside the name', '- action: [[notes]]', root=A, who=AGENT, env=AS_AGENT)
    r = run(PY, 'bin/sync.py', '--by', AGENT, 'origin', cwd=A, env=AS_AGENT)
    merge = run('git', 'cat-file', 'commit', 'HEAD', cwd=A).out
    first = run('git', 'rev-parse', 'HEAD^1', cwd=A).out.strip()
    r3 = push(A, AS_AGENT)
    check("hub: the agent's clean merge, whose second parent brought the gardener's anchor, is taken from a writer "
          "granted `write` alone — the merge decided nothing of class F",
          r0.returncode == 0 and r1.returncode == 0 and r2.returncode == 0 and r.returncode == 0
          and merge.count('\nparent ') == 2 and 'gpgsig' in merge
          and uid not in run('git', 'show', f'{first}:beans/notes.md', cwd=A).out and r3.returncode == 0,
          r0.out[-300:] + r1.out + r2.out[-300:] + r.out[-600:] + r3.out[-800:])
    merged = head(A)
    r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'receipts', HUB, f'{merged}^2..{merged}')
    check("receipts: a push of two commits — the agent's and its merge — gives each its own receipt, each signed by the "
          "hub's key", r.returncode == 0 and '2 commits: 2 with a receipt, 0 with none' in r.out
          and r.out.count(f'signed by {hubf}') == 2 and 'not signed' not in r.out, r3.out + r.out)

    # ---- A HUB THAT KEEPS NO KEY writes its receipts all the same, and says they are unsigned
    run('git', 'fetch', '-q', 'hub')
    run('git', 'reset', '-q', '--hard', 'hub/master')
    write('beans/notes.md', read(os.path.join(G, 'beans', 'notes.md')).replace("again.", "again and again."))
    save('the notes, once more', '- action: [[notes]]')
    r = push(env={'DAFTARD_STATE': os.path.join(T, 'elsewhere')})
    check("a hub whose account keeps no key of it writes the receipt unsigned, and says so",
          r.returncode == 0 and 'unsigned' in r.out and 'signed: no' in receipt(head())
          and '-----BEGIN SSH SIGNATURE-----' not in receipt(head()), r.out + receipt(head()))

    # ---- THE REPORT'S DAY: a day is the garden's, from its midnight in GARDEN.md's zone; the log's moments are UTC
    Z = os.path.join(T, 'zoned')
    run('git', 'init', '-q', Z, cwd=T)
    write('GARDEN.md', '---\ngarden: zoned\ngardener: sam\nzone: Asia/Tokyo\n---\n', root=Z)
    run('git', 'add', '-A', cwd=Z)
    run('git', 'commit', '-q', '--no-verify', '-m', 'a garden in Tokyo', cwd=Z)
    write('.git/daftar/hub.log', ''.join(json.dumps({'at': at, 'mode': 'refusing', 'ref': 'refs/heads/master',
                                                      'verdict': 'taken', 'refusals': []}) + '\n'
                                         for at in ('2026-10-23T14:59:00Z', '2026-10-23T15:00:00Z',
                                                    '2026-10-24T10:00:00Z')), root=Z)
    hub = os.path.join(G, 'bin', 'hub.py')
    r = run(PY, hub, 'report', Z, '--since', '2026-10-24', cwd=Z)
    check("report --since <day>: the garden's day in its zone, from its midnight there (15:00 UTC the day before), "
          "said with the instant it was read as", r.returncode == 0 and '2 ref updates judged since 2026-10-24 (the '
          "day in Asia/Tokyo, the garden's zone), from 2026-10-23T15:00:00Z" in r.out, r.out)
    r = run(PY, hub, 'report', Z, '--since', '2026-10-23T23:59:30+09:00', cwd=Z)
    r2 = run(PY, hub, 'report', Z, '--since', '2026-10-23 23:59:30', cwd=Z)
    check("report --since <moment>: by its offset, compared as an instant and not as text; a clock reading with none "
          "in the garden's zone", r.returncode == 0 and '2 ref updates judged since 2026-10-23T23:59:30+09:00, from '
          '2026-10-23T14:59:30Z' in r.out and r2.returncode == 0 and "2 ref updates judged since 2026-10-23 23:59:30 "
          "(in Asia/Tokyo, the garden's zone), from 2026-10-23T14:59:30Z" in r2.out, r.out + r2.out)
    write('GARDEN.md', '---\ngarden: zoned\ngardener: sam\n---\n', root=Z)
    run('git', 'commit', '-q', '--no-verify', '-am', 'no zone said', cwd=Z)
    r = run(PY, hub, 'report', Z, '--since', '2026-10-24', cwd=Z)
    r2 = run(PY, hub, 'report', Z, '--since', 'yesterday', cwd=Z)
    check("report --since <day> where GARDEN.md names no zone: the day in UTC, and said so; what names no day or moment, "
          "exit 2", r.returncode == 0 and '1 ref update judged since 2026-10-24 (the day in UTC: GARDEN.md names no '
          'zone), from 2026-10-24T00:00:00Z' in r.out and r2.returncode == 2 and 'no day or moment' in r2.out,
          r.out + r2.out)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nhubreport: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
