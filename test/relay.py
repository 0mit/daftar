#!/usr/bin/env python3
"""Relays: a peer behind NAT dials out to an always-on peer, which relays one port to it (bin/relay.py, design §7.3).

Grows a garden of the core whose laptop sits behind NAT and whose always-on box relays it, recorded in the network
profile's own words — a `carry` through ssh at each end, the box's loopback port a `serve` its link carries, the
laptop's own ssh what the laptop's carries — and saved through the gate. Then: the relay is read from those statements
and nothing else; the laptop's command dials the box's public ssh, forwards the box's loopback port to its own ssh,
never prompts, exits when its forward cannot be had and notices a dead link (a unit started again until it holds); the
box is given an account of the laptop's name, a Match block that allows one remote forward on one address and nothing
else, with keep-alives, which OpenSSH's own sshd reads back as written (where this machine has one), and the key line
bound the same; and what is not a relay is refused: a port that listens beyond loopback, two peers on one port, a link
only one end records.

Run: python3 test/relay.py   (0 = green)
"""
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def write(g, rel, text):
    p = os.path.join(g, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def host(bid, title, lines):
    return (f'---\nbean: {bid}\nkind: host\ntitle: "{bid} — {title}"\nstatements:\n  - read: {{ by: sam, at: now }}\n'
            f'  - own: {{ by: sam, of: self }}\n' + ''.join(f'  - {ln}\n' for ln in lines) + '---\n' + title + '.\n')


LAPTOP = ["serve: { id: serves-ssh, by: self, at: [127.0.0.1, 'tcp-port:22'], through: ssh }",
          "carry: { id: relay-link, by: self, through: ssh, to: box, of: [serves-ssh] }"]
BOX = ["serve: { id: serves-ssh, by: self, at: [192.0.2.10, 'tcp-port:2222'], through: ssh }",
       "serve: { id: relays-laptop, by: self, at: [127.0.0.1, 'tcp-port:22101'], through: ssh }",
       "carry: { id: relay-laptop, by: self, through: ssh, to: laptop, of: [relays-laptop] }"]

T = tempfile.mkdtemp(prefix='core-relay-')
try:
    REL = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam')
    write(G, 'VOCAB.md', '---\nprofiles: [network]\n---\n# the garden\'s own rows\n')
    write(G, 'beans/laptop.md', host('laptop', 'a laptop behind NAT', LAPTOP))
    write(G, 'beans/box.md', host('box', 'the always-on box that relays it', BOX))
    r = grow.run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: the network profile; the laptop and the box that relays it',
                 '--body', '- action: RULE-CHANGE — VOCAB.md takes the network profile; wrote [[laptop]] and [[box]]: the '
                 'laptop dials out to the box, which relays one port to it', '- ratified_by: sam', cwd=G)
    check("the garden records the laptop, the box and the link between them, through its gate", r.returncode == 0,
          r.out[-1200:])

    def relay(*a):
        return grow.run(PY, 'bin/relay.py', *a, cwd=G)

    r = relay()
    check("read: the relay is read from the garden's carry and serve statements — who dials whom, on which port",
          r.returncode == 0 and 'laptop dials box at 192.0.2.10:2222 as laptop' in r.out
          and "box listens on 127.0.0.1:22101 and forwards it to laptop's ssh on :22" in r.out, r.out)
    r = relay('dial', 'laptop', '--key', '/home/sam/.ssh/relay')
    cmd = r.out.strip()
    check("dial: the laptop's ssh forwards the box's loopback port to its own ssh, never prompts, exits when its forward "
          "cannot be had, and notices a dead link in ninety seconds",
          r.returncode == 0 and cmd.startswith('ssh -N -T') and '-R 127.0.0.1:22101:localhost:22' in cmd
          and cmd.endswith('laptop@192.0.2.10') and '-p 2222' in cmd and 'BatchMode=yes' in cmd
          and 'ExitOnForwardFailure=yes' in cmd and 'ServerAliveInterval=30' in cmd and 'ServerAliveCountMax=3' in cmd
          and 'StrictHostKeyChecking=yes' in cmd and '-i /home/sam/.ssh/relay' in cmd, cmd)
    r = relay('dial', 'laptop', '--unit')
    check("dial --unit: started again until it holds, so an address that changes cuts the link and loses nothing",
          r.returncode == 0 and 'Restart=always' in r.out and 'ExecStart=/usr/bin/ssh -N' in r.out, r.out)
    pub = os.path.join(T, 'laptop.pub')
    with open(pub, 'w') as fh:
        fh.write('ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEXAMPLEEXAMPLEEXAMPLEEXAMPLEEXAMPLEEXAMPL sam@laptop\n')
    r = relay('relay', 'laptop', pub)
    out = r.out
    check("relay: the box is given an account of the laptop's name with no shell, a Match block that allows one remote "
          "forward on one address and nothing else, with keep-alives, and the key bound the same",
          r.returncode == 0 and 'useradd --system --create-home --shell /usr/sbin/nologin laptop' in out
          and 'Match User laptop' in out and 'AllowTcpForwarding remote' in out and 'PermitListen 127.0.0.1:22101' in out
          and 'PermitTTY no' in out and 'ForceCommand /usr/sbin/nologin' in out and 'ClientAliveInterval 30' in out
          and 'restrict,port-forwarding,permitlisten="127.0.0.1:22101" ssh-ed25519' in out, out)
    sshd = next((p for p in ('/usr/sbin/sshd', '/usr/bin/sshd') if os.access(p, os.X_OK)), None)
    if sshd:
        hk = os.path.join(T, 'hostkey')
        subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', hk], capture_output=True)
        conf = os.path.join(T, 'sshd_config')
        match = out.split('# 2. the sshd Match block\n', 1)[-1].split('\n# 3.', 1)[0]
        with open(conf, 'w') as fh:
            fh.write(f'HostKey {hk}\nPidFile none\nUsePAM no\n' + match)
        t = subprocess.run([sshd, '-T', '-f', conf, '-C', 'user=laptop,host=peer,addr=203.0.113.9'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        o = t.stdout.lower()
        check("relay: OpenSSH's own sshd reads the Match block back as written — for the laptop, one remote forward "
              "on one address, no terminal, the forced command, the keep-alives",
              t.returncode == 0 and 'allowtcpforwarding remote' in o and 'permitlisten 127.0.0.1:22101' in o
              and 'permittty no' in o and 'forcecommand /usr/sbin/nologin' in o and 'clientaliveinterval 30' in o
              and 'clientalivecountmax 3' in o and 'permitopen none' in o, t.stdout[-800:] + t.stderr[-400:])
        t = subprocess.run([sshd, '-T', '-f', conf, '-C', 'user=sam,host=peer,addr=203.0.113.9'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        check("...and for anyone else, nothing of it", t.returncode == 0
              and 'forcecommand /usr/sbin/nologin' not in t.stdout.lower()
              and 'permitlisten any' in t.stdout.lower(), t.stdout[-400:] + t.stderr[-400:])
    else:
        print("SKIP  relay: no sshd on this machine to read the Match block back")

    # ---- what is not a relay is refused
    keep = open(os.path.join(G, 'beans', 'box.md'), encoding='utf-8').read()
    write(G, 'beans/box.md', keep.replace("[127.0.0.1, 'tcp-port:22101']", "[192.0.2.10, 'tcp-port:22101']"))
    r = relay('dial', 'laptop')
    check("a relay port that listens beyond loopback is refused", r.returncode != 0 and 'loopback only' in r.out, r.out)
    write(G, 'beans/box.md', keep.replace(BOX[2], BOX[2] + "\n  - serve: { id: relays-desk, by: self, at: [127.0.0.1, "
                                          "'tcp-port:22101'], through: ssh }\n  - carry: { id: relay-desk, by: self, "
                                          "through: ssh, to: desk, of: [relays-desk] }"))
    write(G, 'beans/desk.md', host('desk', 'a second machine behind NAT', [
        "serve: { id: serves-ssh, by: self, at: [127.0.0.1, 'tcp-port:22'], through: ssh }",
        "carry: { id: relay-link, by: self, through: ssh, to: box, of: [serves-ssh] }"]))
    r = relay()
    check("two peers on one relay port are refused", r.returncode != 0 and "share a relay's port" in r.out, r.out)
    write(G, 'beans/box.md', keep)
    os.remove(os.path.join(G, 'beans', 'desk.md'))
    lap = open(os.path.join(G, 'beans', 'laptop.md'), encoding='utf-8').read()
    write(G, 'beans/laptop.md', lap.replace('  - ' + LAPTOP[1] + '\n', ''))
    r = relay('dial', 'laptop')
    check("a link only one end records is refused: a link is mutual", r.returncode != 0 and 'mutual' in r.out, r.out)
    write(G, 'beans/laptop.md', lap)
    g = grow.run(PY, 'bin/check.py', cwd=G)
    check("the garden is as it was, and passes its gate: the tool wrote nothing",
          g.returncode == 0 and grow.run('git', 'status', '--porcelain', cwd=G).out.strip() == '', g.out[-600:])
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check(f"the suite ran to its end ({type(e).__name__}: {e})", False)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nrelay: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
