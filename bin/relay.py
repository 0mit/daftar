#!/usr/bin/env python3
"""relay — a peer behind NAT dials out to an always-on peer, which relays one port to it and nothing else.

    python3 bin/relay.py                          # every relay the garden records: who dials whom, on which port
    python3 bin/relay.py dial <peer> [--key <file>] [--unit]   # the command the peer runs (a systemd unit with --unit)
    python3 bin/relay.py relay <peer> [<public key file>]      # what the relaying host is given: the account, its
                                                               # sshd Match block, its authorized_keys line

A MACHINE BEHIND NAT IS REACHED BY DIALLING OUT (design §7.3). It cannot be reached, so it reaches: it opens an SSH
connection to an always-on peer of the same garden and asks that peer to listen on one loopback port and forward
what arrives there back down the connection to its own SSH. Any always-on peer may relay; none is privileged.

NOTHING HERE IS CONFIGURED: the relay is read from the garden, in the network profile's own words (MODEL; nothing here
is a new kind of fact). A link is mutual, each end records it as a `carry` through ssh `to` the other end, and what
rides on it is its `of`:

  on the peer   serve: { id: serves-ssh, by: self, at: [127.0.0.1, 'tcp-port:22'], through: ssh }   # what it reaches
                carry: { id: relay-link, by: self, through: ssh, to: <relay>, of: [serves-ssh] }
  on the relay  serve: { id: serves-ssh, by: self, at: [<address>, 'tcp-port:<n>'], through: ssh }   # where it is dialled
                serve: { id: relays-<peer>, by: self, at: [127.0.0.1, 'tcp-port:<port>'], through: ssh }
                carry: { id: relay-<peer>, by: self, through: ssh, to: <peer>, of: [relays-<peer>] }

The relay is the end whose `carry` names a `serve` of its own that the link brings into being, and that can be dialled
(an ssh `serve` on an address that is not loopback); the other end dials, and what it names, if anything, is the ssh
the relayed port reaches (else its own ssh `serve`, else port 22). The relay's port listens on loopback and nowhere else
(one listen address), and two peers never share a relay's port.

THE PATTERN, PROVED ON 2026-10-09: on the relay, an account of the peer's own name with no shell and no password; an
sshd Match block that lets it forward one remote port, on that one address, and nothing else — no local forwarding, no
terminal, no agent or X11, a forced command that does nothing — with keep-alives, so a dead link frees its port in about
ninety seconds instead of the two hours of TCP's own keep-alive; and its key bound to the same in authorized_keys. On
the peer, ssh that never prompts, exits when its forward cannot be had, notices a dead link in the same ninety seconds,
and is started again until it holds (`Restart=always`): an address that changes cuts the link and loses nothing.

THIS TOOL NEVER CHANGES A HOST. It writes what a person applies, or what a ratified action (bin/act.py) plans with.
"""
import ipaddress
import os
import re
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import parse as dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr
import importlib  # noqa: E402
dmpass = importlib.import_module('pass')  # noqa: E402 — `pass` is a keyword: imported by name

ALIVE, MISSES = 30, 3        # seconds between keep-alives, and how many missed before the link is called dead
ACCOUNT = re.compile(r'^[a-z_][a-z0-9_-]{0,31}$')


class Refused(Exception):
    """Why no relay could be read: said, and nothing written."""


def listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def where(serve):
    """(address, port) of a `serve`'s `at`: its address, and its tcp-port's number; either None where it names none."""
    addr = port = None
    for p in listed(serve.get('at')):
        p = str(p)
        if p.startswith('tcp-port:'):
            port = p.split(':', 1)[1]
        else:
            addr = p
    return addr, (int(port) if port and port.isdigit() else None)


def loopback(addr):
    try:
        return ipaddress.ip_address(addr).is_loopback
    except ValueError:
        return addr == 'localhost'


def serves(fm):
    """{id: roles} of a bean's `serve` statements through ssh."""
    return {str(r.get('id')): r for _i, v, r in dmpass.statements(fm) if v == 'serve' and r.get('through') == 'ssh'
            and r.get('id') is not None}


def carries(fm, to):
    """The roles of a bean's `carry` statements through ssh to `to`."""
    return [r for _i, v, r in dmpass.statements(fm) if v == 'carry' and r.get('through') == 'ssh' and r.get('to') == to]


def dialled_at(fm, but=None):
    """A bean's ssh `serve`s it can be dialled at: on an address that is not loopback."""
    return [s for s in serves(fm).values() if s is not but and where(s)[0] and not loopback(where(s)[0])]


def ends(beans):
    """(relay, peer, the relay's carry, the serve it names) for each link through ssh whose one end names a serve of its
    own in the link's `of`. Where both ends do (the peer may name the ssh the link reaches), the relay is the end that
    can be dialled — an ssh serve on an address that is not loopback — and the peer the end that cannot."""
    found = {}
    for rid, rfm in sorted(beans.items()):
        rs = serves(rfm)
        for c in [r for _i, v, r in dmpass.statements(rfm) if v == 'carry' and r.get('through') == 'ssh']:
            named = [rs[str(o)] for o in listed(c.get('of')) if str(o) in rs]
            peer = str(c.get('to') or '')
            if named and peer in beans:
                found[(rid, peer)] = (c, named[0])
    out, problems = [], []
    for (rid, peer), (c, s) in sorted(found.items()):
        if (peer, rid) in found:              # both ends name a serve: the one that can be dialled relays
            mine, theirs = bool(dialled_at(beans[rid], s)), bool(dialled_at(beans[peer], found[(peer, rid)][1]))
            if mine == theirs:
                if rid < peer:
                    problems.append((peer, f"{rid} and {peer} each name a serve of their own on the link between them, "
                                           f"and {'both' if mine else 'neither'} can be dialled: which relays is not said"))
                continue
            if not mine:
                continue
        out.append((rid, peer, c, s))
    return out, problems


def relays(beans=None):
    """Every relay the garden records, as dicts; problems as (peer, why)."""
    beans = dmpass.beans_here(ROOT) if beans is None else beans
    found, problems = ends(beans)
    out, ports = [], {}
    for rid, peer, _c, listen in found:
        addr, port = where(listen)
        if not loopback(addr or '') or not port:
            problems.append((peer, f"{rid} would relay it at {addr}:{port}, and a relay listens on loopback only, one "
                                   f"port — at: [127.0.0.1, 'tcp-port:<n>']"))
            continue
        if (rid, port) in ports:
            problems.append((peer, f"{rid} relays {ports[(rid, port)]} on port {port} already: two peers never share a "
                                   f"relay's port"))
            continue
        back = carries(beans[peer], rid)
        if not back:
            problems.append((peer, f"{rid} records a link to {peer}, and {peer} records none to {rid}: a link is mutual "
                                   f"— carry: {{ by: self, through: ssh, to: {rid} }}"))
            continue
        reach = dialled_at(beans[rid], listen)
        if not reach:
            problems.append((peer, f"{rid} records no ssh it is dialled at (a serve through ssh on an address that is "
                                   f"not loopback)"))
            continue
        if not ACCOUNT.match(peer):
            problems.append((peer, f"{peer!r} cannot name an account on {rid} (a-z, 0-9, _ and -, at most 32)"))
            continue
        ps = serves(beans[peer])
        target = next((ps[str(o)] for o in listed(back[0].get('of')) if str(o) in ps), None) or \
            next(iter(ps.values()), None)
        ports[(rid, port)] = peer
        out.append({'peer': peer, 'relay': rid, 'listen': (addr, port), 'account': peer,
                    'target': (where(target)[1] if target else None) or 22, 'reach': where(reach[0])})
    return out, problems


def one(peer):
    found, problems = relays()
    for r in found:
        if r['peer'] == peer:
            return r
    why = [w for p, w in problems if p == peer]
    raise Refused(f"no relay of {peer} can be read: " + ('; '.join(why) if why else
                  f"the garden records none (see `{os.path.basename(__file__)}` --help: a `carry` through ssh at each end)"))


def dial(r, key=None):
    """The argv the peer runs: ssh that never prompts, holds its forward or exits, and notices a dead link."""
    addr, port = r['reach']
    listen_addr, listen_port = r['listen']
    argv = ['ssh', '-N', '-T', '-o', 'BatchMode=yes', '-o', 'ExitOnForwardFailure=yes',
            '-o', f'ServerAliveInterval={ALIVE}', '-o', f'ServerAliveCountMax={MISSES}',
            '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=30']
    if key:
        argv += ['-i', key, '-o', 'IdentitiesOnly=yes']
    if port and port != 22:
        argv += ['-p', str(port)]
    return argv + ['-R', f"{listen_addr}:{listen_port}:localhost:{r['target']}", f"{r['account']}@{addr}"]


def unit(r, argv):
    return (f"# /etc/systemd/system/daftar-relay-{r['relay']}.service — {r['peer']} dials out to {r['relay']}\n"
            f"[Unit]\nDescription=daftar relay: {r['peer']} reached through {r['relay']}\n"
            f"After=network-online.target\nWants=network-online.target\n\n"
            f"[Service]\nExecStart=/usr/bin/{shlex.join(argv)}\nRestart=always\nRestartSec=10\n\n"
            f"[Install]\nWantedBy=multi-user.target\n")


def relay_side(r, pub=None):
    """What the relaying host is given: the account, the sshd Match block, the authorized_keys line."""
    a, (la, lp) = r['account'], r['listen']
    match = (f"Match User {a}\n    AllowTcpForwarding remote\n    PermitListen {la}:{lp}\n    PermitOpen none\n"
             f"    GatewayPorts no\n    PermitTTY no\n    X11Forwarding no\n    AllowAgentForwarding no\n"
             f"    AllowStreamLocalForwarding no\n    PermitTunnel no\n    ForceCommand /usr/sbin/nologin\n"
             f"    ClientAliveInterval {ALIVE}\n    ClientAliveCountMax {MISSES}\n")
    words = (pub or '').strip().split()
    if pub is not None and (len(words) < 2 or not words[0].startswith(('ssh-', 'ecdsa-', 'sk-'))):
        raise Refused("that is no OpenSSH public key")
    line = (f'restrict,port-forwarding,permitlisten="{la}:{lp}" ' + ' '.join(words)) if words else \
        f'restrict,port-forwarding,permitlisten="{la}:{lp}" <the key {r["peer"]} dials with>'
    return {'account': f"useradd --system --create-home --shell /usr/sbin/nologin {a}   # and no password",
            'match': match, 'authorized_keys': line,
            'where': f"~{a}/.ssh/authorized_keys (mode 600, the directory 700, both {a}'s); the Match block appended LAST "
                     f"to /etc/ssh/sshd_config, then `sshd -t` and a reload — and a fresh login of your own, before you "
                     f"close the one you have"}


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__)
        return 0
    try:
        if not argv:
            found, problems = relays()
            for r in found:
                la, lp = r['listen']
                print(f"{r['peer']} dials {r['relay']} at {r['reach'][0]}:{r['reach'][1] or 22} as {r['account']}; "
                      f"{r['relay']} listens on {la}:{lp} and forwards it to {r['peer']}'s ssh on :{r['target']}")
            for p, why in problems:
                print(f"PROBLEM {p}: {why}")
            print(f"relay: {len(found)} relay(s), {len(problems)} problem(s)")
            return 1 if problems else 0
        cmd, peer, rest = argv[0], argv[1] if len(argv) > 1 else '', argv[2:]
        if cmd == 'dial' and peer:
            key = rest[rest.index('--key') + 1] if '--key' in rest[:-1] else None
            r = one(peer)
            a = dial(r, key)
            print(unit(r, a) if '--unit' in rest else shlex.join(a))
        elif cmd == 'relay' and peer and len(rest) <= 1:
            pub = None
            if rest:
                with open(rest[0], encoding='utf-8') as fh:
                    pub = fh.read()
            r = one(peer)
            s = relay_side(r, pub)
            print(f"# on {r['relay']}: {peer} dials it as the account {r['account']}, and it relays one port\n")
            print(f"# 1. the account\n{s['account']}\n\n# 2. the sshd Match block\n{s['match']}\n"
                  f"# 3. the key, in {s['where']}\n{s['authorized_keys']}")
        else:
            print(__doc__)
            return 2
    except (Refused, OSError) as e:
        print(f"relay: REFUSED — {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
