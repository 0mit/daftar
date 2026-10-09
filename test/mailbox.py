#!/usr/bin/env python3
"""Mailboxes: where another garden lays a proposal, by a key that can do nothing else (bin/mailbox.py, design §7.2).

Grows two gardens from this tree. Ana's garden proposes a bean to Ben's (bin/propose.py make); the proposal is laid in
Ben's mailbox through the forced command a peered garden's key runs (`receive`, standard input to the inbox), and read
there; the authorized_keys line for such a key allows that one command and nothing else; what is not a proposal, one for
another garden, one damaged in transit and one too large are refused, nothing kept; `put` hands a proposal to the
receiver's command over the transport (ssh, here a stand-in that runs it locally); and a mailbox lies outside every
garden.

Run: python3 test/mailbox.py   (0 = green)
"""
import os, re, shutil, stat, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1200:]))
    if not cond:
        FAILS.append(name)


T = tempfile.mkdtemp(prefix='core-mailbox-')
try:
    REL = grow.release(os.path.join(T, 'release'))
    A, B = os.path.join(T, 'garden-ana'), os.path.join(T, 'garden-ben')
    for g, who in ((A, 'ana'), (B, 'ben')):
        r = grow.garden(REL, g, who, '--gardener-name', who.title())
    IDB = grow.run(PY, 'bin/propose.py', 'id', cwd=B).out.split('"')[1]
    IDA = grow.run(PY, 'bin/propose.py', 'id', cwd=A).out.split('"')[1]
    BOX = os.path.join(T, 'mailboxes')
    env = dict(grow.ENV, DAFTAR_MAILBOX=BOX)
    # Ana's garden knows Ben's, and offers him a note under an agreement both are parties to
    with open(os.path.join(A, 'beans', 'garden-ben.md'), 'w', encoding='utf-8') as fh:
        fh.write(f'---\nbean: garden-ben\nkind: garden\ntitle: "garden-ben — the garden Ben keeps"\nstatements:\n'
                 f'  - say: {{ by: ana, at: now }}\n  - name: {{ by: garden-id, of: self, as: "{IDB}" }}\n'
                 f'  - own: {{ by: ben, of: self }}\n---\nBen\'s garden.\n')
    with open(os.path.join(A, 'beans', 'ben.md'), 'w', encoding='utf-8') as fh:
        fh.write(f'---\nbean: ben\nkind: person\ntitle: "Ben"\nstatements:\n  - say: {{ by: ana, at: now }}\n'
                 f'  - name: {{ by: garden, of: self, as: "{IDB}/person:ben" }}\n  - own: {{ by: theone, of: self }}\n'
                 f'  - answer: {{ by: self, of: self, as: law }}\n---\nBen.\n')
    with open(os.path.join(A, 'beans', 'pact.md'), 'w', encoding='utf-8') as fh:
        fh.write('---\nbean: pact\nkind: contract\ntitle: "pact — Ana and Ben share notes"\nstatements:\n'
                 '  - say: { by: ana, at: now }\n  - own: { by: theone, of: self }\n'
                 '  - answer: { by: ana, of: self, as: law }\n  - answer: { by: ben, of: self, as: law }\n'
                 '  - agree: { id: ana-agrees, by: ana, of: "notes shared", through: spoken }\n'
                 '  - agree: { id: ben-agrees, by: ben, of: "notes shared", through: spoken }\n'
                 f'  - name: {{ by: garden, of: self, as: "{IDA}/contract:pact" }}\n---\nA pact.\n')
    with open(os.path.join(A, 'beans', 'note.md'), 'w', encoding='utf-8') as fh:
        fh.write('---\nbean: note\nkind: document\ntitle: "note — a note for Ben"\nstatements:\n  - say: { by: ana, at: now }\n'
                 f'  - name: {{ by: garden, of: self, as: "{IDA}/document:note" }}\n---\nA note.\n')
    ana = open(os.path.join(A, 'beans', 'ana.md'), encoding='utf-8').read()
    with open(os.path.join(A, 'beans', 'ana.md'), 'w', encoding='utf-8') as fh:
        fh.write(ana.replace('\n---\n', f'\n  - name: {{ id: qualified, by: garden, of: self, as: "{IDA}/person:ana" }}\n'
                             f'  - say: {{ by: ana, of: [qualified], at: now }}\n---\n', 1)
                 if ana.count('---') >= 2 else ana)
    r = grow.run(PY, 'bin/save.py', 'ana', 'Ben, his garden, a pact and a note', '--body',
                 '- action: wrote [[garden-ben]], [[ben]], [[pact]] and [[note]], and named [[ana]] beyond this garden; Ben is kept here on his own word ([[pact]])',
                 cwd=A)
    out = os.path.join(T, 'outbox')
    os.makedirs(out)
    r2 = grow.run(PY, 'bin/propose.py', 'make', '--to', 'garden-ben', '--under', 'pact', 'note', '--out', out, cwd=A)
    props = [f for f in os.listdir(out) if f.startswith('PROPOSAL-')]
    check("a proposal is made in Ana's garden, to Ben's", r.returncode == 0 and r2.returncode == 0 and len(props) == 1,
          r.out[-1600:] + r2.out[-1600:])
    prop = os.path.join(out, props[0]) if props else ''
    raw = open(prop, 'rb').read() if prop else b''

    def receive(data, garden=IDB):
        return grow.run(PY, 'bin/mailbox.py', 'receive', garden, cwd=B, stdin=data.decode('utf-8', 'replace'), env=env)

    r = receive(raw)
    inbox = os.path.join(BOX, IDB, 'inbox')
    got = sorted(os.listdir(inbox)) if os.path.isdir(inbox) else []
    check("receive: a proposal on standard input is laid in the garden's inbox, whole, and a receipt said",
          r.returncode == 0 and got == props and open(os.path.join(inbox, got[0]), 'rb').read() == raw
          and 'received' in r.out, (r.out[-600:], got))
    rd = grow.run(PY, 'bin/propose.py', 'read', os.path.join(inbox, got[0]), cwd=B, env=env) if got else None
    check("...and Ben's garden reads it there — what taking it would do, a first contact its gardener records first",
          rd is not None and rd.returncode in (0, 1) and f'from garden-ana (garden {IDA})' in rd.out
          and 'Traceback' not in rd.out, rd.out[-800:] if rd else '')
    r = receive(raw)
    check("receive: the same proposal again is no second copy", r.returncode == 0 and len(os.listdir(inbox)) == 1, r.out)
    for name, data, says in (("what is not a proposal", b"#!/bin/sh\nrm -rf ~\n", 'not a proposal'),
                             ("one damaged in transit", raw.replace(b'A note.', b'A nite.'), 'fingerprint'),
                             ("one too large", raw + b'x' * (5 * 2 ** 20), 'large')):
        r = receive(data)
        check(f"receive: {name} is refused, nothing kept", r.returncode != 0 and says in r.out
              and len(os.listdir(inbox)) == 1, r.out[-400:])
    r = receive(raw, garden=IDA)
    check("receive: a proposal to another garden is refused at this one's box", r.returncode != 0 and 'to garden' in r.out
          and not os.path.isdir(os.path.join(BOX, IDA, 'inbox')) or not os.listdir(os.path.join(BOX, IDA, 'inbox')), r.out)
    pub = os.path.join(T, 'ana-key.pub')
    with open(pub, 'w') as fh:
        fh.write('ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEXAMPLEEXAMPLEEXAMPLEEXAMPLEEXAMPLEEXAMPL ana@laptop\n')
    r = grow.run(PY, 'bin/mailbox.py', 'key', IDB, pub, cwd=B, env=env)
    line = r.out.strip().splitlines()[-1] if r.out.strip() else ''
    check("key: a peered garden's key may run the one command — receive, for this garden — and nothing else",
          r.returncode == 0 and line.startswith('restrict,command="') and f'mailbox.py receive {IDB}"' in line
          and line.endswith('ana@laptop'), r.out)
    # put: the transport is ssh to the receiving peer; here a stand-in that runs what the forced command would
    fake = os.path.join(T, 'fake-ssh')
    with open(fake, 'w') as fh:
        fh.write(f'#!/bin/sh\nexec "{PY}" "{os.path.join(B, "bin", "mailbox.py")}" receive {IDB}\n')
    os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
    shutil.rmtree(inbox)
    r = grow.run(PY, 'bin/mailbox.py', 'put', 'ben@peer', prop, cwd=A, env=dict(env, DAFTAR_SSH=fake))
    check("put: a proposal is handed to the receiving peer's command, which lays it in the inbox",
          r.returncode == 0 and os.listdir(inbox) == props, r.out[-600:])
    r = grow.run(PY, 'bin/mailbox.py', 'list', IDB, cwd=B, env=env)
    check("list: what waits in a garden's inbox", r.returncode == 0 and props[0] in r.out, r.out)
    check("a mailbox lies outside every garden", not os.path.abspath(BOX).startswith(os.path.abspath(B) + os.sep)
          and grow.run('git', 'status', '--porcelain', cwd=B).out.strip() == '', BOX)
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check(f"the suite ran to its end ({type(e).__name__}: {e})", False)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nmailbox: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
