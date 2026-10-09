#!/usr/bin/env python3
"""mailbox — a garden's mailbox on this machine: where another garden lays a proposal, by a key that can do nothing else.

    python3 bin/mailbox.py key <garden-id> <their garden-id> <public key file>  # the line for a peered garden's key
    python3 bin/mailbox.py serve <garden-id> <their garden-id>  # the forced command that key runs: receive | receipts
    python3 bin/mailbox.py receive <garden-id>                  # a proposal on stdin, into the inbox (on this machine)
    python3 bin/mailbox.py list <garden-id>                     # what lies in a garden's inbox here, waiting or taken
    python3 bin/mailbox.py outbox                               # where this garden's proposals wait to be delivered
    python3 bin/mailbox.py deliver <their garden-id> <ssh destination>  # deliver them, until each is acknowledged
    python3 bin/mailbox.py put <ssh destination> <proposal>     # hand one proposal over, once

GARDENS MEET ONLY BY PROPOSAL (bin/propose.py), and a proposal is a file laid OUTSIDE every garden. A mailbox is that
place, on each machine of the receiving garden: `<mailboxes>/<garden-id>/inbox/`, where `<mailboxes>` is
DAFTAR_MAILBOX, else `%LOCALAPPDATA%\\daftar\\mailbox` on Windows, else `$XDG_DATA_HOME/daftar/mailbox`
(`~/.local/share/daftar/mailbox`). What lies there is read with `propose.py read`, taken with `take`, and saved by the
receiving gardener — the ratification; the mailbox itself writes nothing in the garden.

WHO MAY DROP INTO IT (design §7.2): at first contact (class F) each garden gives the other one key, and that key may
run one command on the receiving machine — `receive`, for that garden — and nothing else: OpenSSH's `restrict` (no
shell, no forwarding, no terminal) and a forced command, `key` writes the line. So a peered garden can lay a proposal,
and never read, list or write anything of the receiver's. `receive` takes only a proposal: one that names this garden
as its `to`, whose envelope has the shape `make` gives it and whose fingerprint holds (nothing changed in transit), no
larger than four megabytes, and from the garden the key was given to; it is laid whole under its own name, once, and
said in a receipt; anything else is refused and nothing is kept. `receipts` says, of that garden's proposals only, which
wait and which were taken — a proposal is taken when a bean at this garden's HEAD holds `take: { …, through: <its
fingerprint> }`, the receiving gardener's save (bin/propose.py).

DELIVERED UNTIL ACKNOWLEDGED (design §7.3): `make` lays a proposal in this garden's outbox (`propose.py make --out
"$(python3 bin/mailbox.py outbox)"`); `deliver` hands each one addressed to that garden to its peer and moves it to
`sent/` only when the receiver's receipt names it. A transfer cut midway leaves it in the outbox for the next run; one
that arrived and whose receipt was lost is said "was here already" the next time, so delivering again is always safe.
Then it asks for the receipts, and a proposal the receiver has taken is marked so in `sent/` — the sender is told.
"""
import glob
import os
import shlex
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse as dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr
import propose as dmpropose  # noqa: E402 — the one reader of a proposal: its envelope, its fingerprint

MOST = 4 * 2 ** 20            # the largest proposal a mailbox takes, in bytes


class Refused(Exception):
    """Why a mailbox took nothing: said to whoever sent it, and nothing kept."""


def boxes():
    """Where this machine keeps its gardens' mailboxes — outside every garden."""
    if os.environ.get('DAFTAR_MAILBOX'):
        return os.environ['DAFTAR_MAILBOX']
    if os.name == 'nt' and os.environ.get('LOCALAPPDATA'):
        return os.path.join(os.environ['LOCALAPPDATA'], 'daftar', 'mailbox')
    return os.path.join(os.environ.get('XDG_DATA_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'share'),
                        'daftar', 'mailbox')


def inbox(garden_id):
    if not dmpropose.id_ok(garden_id):
        raise Refused(f"{garden_id!r} is no garden's id (twelve hexadecimal digits)")
    return os.path.join(boxes(), garden_id, 'inbox')


def outbox():
    """Where this garden's proposals wait to be delivered: its own mailbox's outbox, outside every garden."""
    own, why = dmpropose.identity()
    if not own:
        raise Refused(f"this garden has no id: {why}")
    return os.path.join(boxes(), own, 'outbox')


def envelope(path):
    """A proposal's envelope, read as `read` reads it; None for what is not one."""
    try:
        return dmpropose.load_proposal(path)[0]
    except dmpropose.SetupError:
        return None


def garden_of(env, side):
    x = env.get(side) if isinstance(env, dict) else None
    return x.get('garden') if isinstance(x, dict) else None


def receive(garden_id, data, sender=None):
    """Lay the proposal `data` (bytes) in the garden's inbox: its file's name, and whether it was there already.
    `sender`, when given, is the only garden it may come from (the garden the key was given to)."""
    box = inbox(garden_id)
    if len(data) > MOST:
        raise Refused(f"it is too large: {len(data)} bytes, and a mailbox takes a proposal of at most {MOST}")
    os.makedirs(box, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.arriving-', dir=box)
    try:
        with os.fdopen(fd, 'wb') as fh:
            fh.write(data)
        try:
            env, _beans, _stubs, _journal, body, _prose = dmpropose.load_proposal(tmp)
        except dmpropose.SetupError as e:
            raise Refused(f"it is not a proposal: {str(e).replace(tmp, 'what arrived')}") from None
        shape = dmpropose.envelope_shape(env)
        if shape:
            raise Refused("its envelope is not in the shape a proposal's is: " + '; '.join(shape))
        to = (env.get('to') or {}).get('garden') if isinstance(env.get('to'), dict) else None
        if to != garden_id:
            raise Refused(f"it is to garden {to!r}, and this is the mailbox of {garden_id}")
        if sender and garden_of(env, 'from') != sender:
            raise Refused(f"it is from garden {garden_of(env, 'from')!r}, and this key was given to {sender}")
        if env.get('fingerprint') != dmpropose.fingerprint(env, body):
            raise Refused("its fingerprint does not hold: what arrived is not what was made (damaged in transit, or "
                          "changed)")
        pid = str(env.get('proposal') or '')
        if not pid or os.sep in pid or (os.altsep and os.altsep in pid) or pid.startswith('.'):
            raise Refused("its envelope names no proposal file")
        dest = os.path.join(box, f"PROPOSAL-{pid}.md" if not pid.startswith('PROPOSAL-') else f"{pid}.md")
        if os.path.exists(dest):
            with open(dest, 'rb') as fh:
                if fh.read() == data:
                    return os.path.basename(dest), True
            raise Refused(f"{os.path.basename(dest)} lies here already, with other words: nothing was replaced")
        os.replace(tmp, dest)
        return os.path.basename(dest), False
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def taken(fingerprint):
    """The moment this garden took the proposal with `fingerprint` — a bean at HEAD holding `take … through:` it — or
    None while it waits."""
    rc, out, _ = dmpropose._git(['grep', '-l', '-F', str(fingerprint), 'HEAD', '--', 'beans'])
    for hit in (out.split() if rc == 0 else []):
        head = dmpropose.core_head(os.path.basename(hit.split(':', 1)[-1])[:-3])
        for st in ((head[0].get('statements') or []) if head else []):
            roles = st.get('take') if isinstance(st, dict) else None
            if isinstance(roles, dict) and str(roles.get('through')) == str(fingerprint):
                return str(roles.get('at') or 'taken')
    return None


def receipts(garden_id, sender):
    """Of the proposals `sender` laid in this garden's inbox, which wait and which were taken: lines of `<name> <state>`."""
    box, lines = inbox(garden_id), []
    for path in sorted(glob.glob(os.path.join(box, 'PROPOSAL-*.md'))):
        env = envelope(path)
        if env is None or garden_of(env, 'from') != sender:
            continue
        when = taken(env.get('fingerprint'))
        lines.append(f"{os.path.basename(path)} " + (f"taken {when}" if when else 'waiting'))
    return lines


def key_line(garden_id, sender, pub):
    """The authorized_keys line that lets `pub` (a public key's text), the key given to the garden `sender`, run this
    garden's mailbox — `receive` and `receipts`, for that garden only — and nothing else."""
    inbox(garden_id)                                  # a garden's id, or refused
    inbox(sender)
    words = pub.strip().split()
    if len(words) < 2 or not words[0].startswith(('ssh-', 'ecdsa-', 'sk-')):
        raise Refused("that is no OpenSSH public key")
    cmd = f"{shlex.quote(sys.executable)} {shlex.quote(os.path.abspath(__file__))} serve {garden_id} {sender}"
    return f'restrict,command="{cmd}" ' + ' '.join(words)


def serve(garden_id, sender):
    """The forced command: what the peered garden's ssh asked for (SSH_ORIGINAL_COMMAND), if it is one of the two."""
    asked = (os.environ.get('SSH_ORIGINAL_COMMAND') or '').strip()
    if asked == 'receive':
        name, already = receive(garden_id, sys.stdin.buffer.read(MOST + 1), sender)
        return f"mailbox: {name} {'was here already' if already else 'received'}, in the inbox of {garden_id}"
    if asked == 'receipts':
        return '\n'.join(receipts(garden_id, sender) + [f"mailbox: receipts for {sender}, from the inbox of {garden_id}"])
    raise Refused(f"this key may ask for `receive` or `receipts`, and asked for {asked[:60]!r}")


def ssh(dest, asked, data=b''):
    """Run `asked` at `dest` over ssh (DAFTAR_SSH, else ssh that never prompts and notices a dead link)."""
    cmd = shlex.split(os.environ.get('DAFTAR_SSH') or
                      'ssh -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=15 -o ServerAliveCountMax=4')
    try:
        r = subprocess.run(cmd + [dest, asked], input=data, capture_output=True, timeout=600)
    except subprocess.TimeoutExpired:
        raise Refused(f"{dest} did not answer within ten minutes") from None
    out = (r.stdout + r.stderr).decode('utf-8', 'replace').strip()
    if r.returncode != 0:
        raise Refused(f"{dest} took nothing: {out[-400:] or f'ssh ended {r.returncode}'}")
    return out


def put(dest, path):
    """Hand the proposal at `path` to `dest`'s mailbox, once: the receiver's forced command reads it from standard input."""
    with open(path, 'rb') as fh:
        return ssh(dest, 'receive', fh.read())


def deliver(to, dest):
    """Every proposal in this garden's outbox addressed to garden `to`, handed to `dest` until its receipt names it; then
    the receipts read back. Returns (what was said, how many still wait)."""
    box, said = outbox(), []
    sent = os.path.join(box, 'sent')
    waiting = 0
    for path in sorted(glob.glob(os.path.join(box, 'PROPOSAL-*.md'))):
        env, name = envelope(path), os.path.basename(path)
        if env is None or garden_of(env, 'to') != to:
            continue
        try:
            receipt = put(dest, path)
        except Refused as e:
            waiting += 1
            said.append(f"{name}: not delivered, it waits for the next run — {e}")
            continue
        if name not in receipt:
            waiting += 1
            said.append(f"{name}: no receipt names it, so it waits for the next run — {receipt[-200:]}")
            continue
        os.makedirs(sent, exist_ok=True)
        with open(os.path.join(sent, name + '.receipt'), 'w', encoding='utf-8') as fh:
            fh.write(receipt + '\n')
        os.replace(path, os.path.join(sent, name))
        said.append(f"{name}: delivered — {receipt.splitlines()[-1]}")
    if os.path.isdir(sent):
        try:
            lines = ssh(dest, 'receipts').splitlines()
        except Refused as e:
            lines = []
            said.append(f"receipts not read this time — {e}")
        for ln in lines:
            name, _, state = ln.partition(' ')
            mark = os.path.join(sent, name + '.taken')
            if state.startswith('taken') and os.path.isfile(os.path.join(sent, name)) and not os.path.exists(mark):
                with open(mark, 'w', encoding='utf-8') as fh:
                    fh.write(state + '\n')
                said.append(f"{name}: {state}, by the receiving garden")
    return said, waiting


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0 if argv else 2
    cmd = argv[0]
    try:
        if cmd == 'receive' and len(argv) == 2:
            name, already = receive(argv[1], sys.stdin.buffer.read(MOST + 1))
            print(f"mailbox: {name} {'was here already' if already else 'received'}, in the inbox of {argv[1]}")
        elif cmd == 'serve' and len(argv) == 3:
            print(serve(argv[1], argv[2]))
        elif cmd == 'key' and len(argv) == 4:
            with open(argv[3], encoding='utf-8') as fh:
                print(key_line(argv[1], argv[2], fh.read()))
        elif cmd == 'put' and len(argv) == 3:
            print(put(argv[1], argv[2]))
        elif cmd == 'outbox' and len(argv) == 1:
            print(outbox())
        elif cmd == 'deliver' and len(argv) == 3:
            inbox(argv[1])
            said, waiting = deliver(argv[1], argv[2])
            for s in said:
                print(f"mailbox: {s}")
            print(f"mailbox: {waiting} still waiting in the outbox for {argv[1]}")
            return 1 if waiting else 0
        elif cmd == 'list' and len(argv) == 2:
            box = inbox(argv[1])
            names = sorted(f for f in os.listdir(box) if f.startswith('PROPOSAL-')) if os.path.isdir(box) else []
            for n in names:
                env = envelope(os.path.join(box, n))
                when = taken(env.get('fingerprint')) if env else None
                print(f"{n}  from {garden_of(env, 'from')}  " + (f"taken {when}" if when else 'waiting'))
            print(f"mailbox: {len(names)} in the inbox of {argv[1]} ({box})")
        else:
            print(__doc__)
            return 2
    except (Refused, OSError) as e:
        print(f"mailbox: REFUSED — {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
