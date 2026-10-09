#!/usr/bin/env python3
"""mailbox — a garden's mailbox on this machine: where another garden lays a proposal, by a key that can do nothing else.

    python3 bin/mailbox.py receive <garden-id>                 # the forced command: a proposal on stdin, into the inbox
    python3 bin/mailbox.py key <garden-id> <public key file>   # the authorized_keys line for a peered garden's key
    python3 bin/mailbox.py put <ssh destination> <proposal>    # lay a proposal in a peer's mailbox, over ssh
    python3 bin/mailbox.py list <garden-id>                    # what waits in a garden's inbox here

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
larger than four megabytes; it is laid whole under its own name, once, and said in a receipt; anything else is
refused and nothing is kept.
"""
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


def receive(garden_id, data):
    """Lay the proposal `data` (bytes) in the garden's inbox: its file's name, and whether it was there already."""
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


def key_line(garden_id, pub):
    """The authorized_keys line that lets `pub` (a public key's text) run `receive` for this garden, and nothing else."""
    inbox(garden_id)                                  # a garden's id, or refused
    words = pub.strip().split()
    if len(words) < 2 or not words[0].startswith(('ssh-', 'ecdsa-', 'sk-')):
        raise Refused("that is no OpenSSH public key")
    cmd = f"{shlex.quote(sys.executable)} {shlex.quote(os.path.abspath(__file__))} receive {garden_id}"
    return f'restrict,command="{cmd}" ' + ' '.join(words)


def put(dest, path):
    """Hand the proposal at `path` to `dest`'s mailbox over ssh (DAFTAR_SSH, else ssh): the receiver's key runs its forced
    command, which reads the proposal from standard input."""
    ssh = shlex.split(os.environ.get('DAFTAR_SSH') or 'ssh')
    with open(path, 'rb') as fh:
        data = fh.read()
    r = subprocess.run(ssh + [dest], input=data, capture_output=True, timeout=300)
    out = (r.stdout + r.stderr).decode('utf-8', 'replace').strip()
    if r.returncode != 0:
        raise Refused(f"the receiving mailbox took nothing: {out[-400:]}")
    return out


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0 if argv else 2
    cmd = argv[0]
    try:
        if cmd == 'receive' and len(argv) == 2:
            name, already = receive(argv[1], sys.stdin.buffer.read(MOST + 1))
            print(f"mailbox: {name} {'was here already' if already else 'received'}, in the inbox of {argv[1]}")
        elif cmd == 'key' and len(argv) == 3:
            with open(argv[2], encoding='utf-8') as fh:
                print(key_line(argv[1], fh.read()))
        elif cmd == 'put' and len(argv) == 3:
            print(put(argv[1], argv[2]))
        elif cmd == 'list' and len(argv) == 2:
            box = inbox(argv[1])
            names = sorted(f for f in os.listdir(box) if f.startswith('PROPOSAL-')) if os.path.isdir(box) else []
            for n in names:
                print(n)
            print(f"mailbox: {len(names)} waiting in the inbox of {argv[1]} ({box})")
        else:
            print(__doc__)
            return 2
    except (Refused, OSError) as e:
        print(f"mailbox: REFUSED — {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
