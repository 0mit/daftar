#!/usr/bin/env python3
"""clock — whether this machine's clock may stamp: within half the stamp's resolution of its time sources (the method
`stamp`'s meaning, core/law/flows.yaml), so that what a save writes where `now` stood is the moment it was.

    python3 bin/clock.py        # what each source shows of this clock, and whether it may stamp (exit 0), or not (1)

A save stamps to the minute (bin/journal.py), so the tolerance is half a minute: thirty seconds. A clock that cannot be
shown within it stamps nothing — the save is refused before anything is written, naming this machine and its keeper —
while every reading and showing goes on. It is the save's to check and not the gate's: a gate judges files the same on
every machine, and a clock is a property of one.

THE SOURCES ARE SIBLINGS, none privileged (manifesto: sibling):
  the kernel   on Linux, the kernel's own discipline (adjtimex, read only): when a time daemon keeps it synchronised,
               it states a bound on its error, which holds offline until it grows past the tolerance
  SNTP         (RFC 4330) to the servers this host was given — the ones its time daemon is configured with (chrony,
               ntpd, systemd-timesyncd, OpenNTPD; on Windows, w32time's NtpServer). Asked when the kernel shows nothing,
               so a machine inside a cut asks the servers it has inside it
  its keeper's `DAFTAR_TIME_SOURCES` (`host[:port]`, by spaces or commas): when set, these ARE this machine's sources, in
               place of the others — what a keeper names where the host's own are unreachable, and what a test names
A source that answers shows the clock within the tolerance or beyond it: the offset it measures, widened by the
round trip's half and the server's own bound on its error (its root delay's half and its root dispersion). One that
does not answer shows nothing. The clock may stamp when at least one source shows it within, and none shows it beyond.
"""
import os
import random
import re
import socket
import struct
import sys
import threading
import time

TOLERANCE = 30.0          # seconds: half the stamp's resolution, a minute (core/law/flows.yaml, the method `stamp`)
NTP_EPOCH = 2208988800    # 1900-01-01 to 1970-01-01, in seconds
WAIT = 1.5                # seconds a server is waited for
MOST = 4                  # servers asked at once
STA_UNSYNC, TIME_ERROR = 0x0040, 5


class Reading:
    """What one source shows: `within`, `beyond` or `nothing`, and the words that say so."""

    def __init__(self, source, shows, said):
        self.source, self.shows, self.said = source, shows, said

    def __repr__(self):
        return f"{self.source}: {self.shows} — {self.said}"


def kernel():
    """What the kernel shows of its own discipline (Linux), or None where it has none to show."""
    if not sys.platform.startswith('linux'):
        return None
    try:
        import ctypes
        import ctypes.util

        class Timeval(ctypes.Structure):
            _fields_ = [('tv_sec', ctypes.c_long), ('tv_usec', ctypes.c_long)]

        class Timex(ctypes.Structure):                     # struct timex, <sys/timex.h>
            _fields_ = [('modes', ctypes.c_uint), ('offset', ctypes.c_long), ('freq', ctypes.c_long),
                        ('maxerror', ctypes.c_long), ('esterror', ctypes.c_long), ('status', ctypes.c_int),
                        ('constant', ctypes.c_long), ('precision', ctypes.c_long), ('tolerance', ctypes.c_long),
                        ('time', Timeval), ('tick', ctypes.c_long), ('ppsfreq', ctypes.c_long),
                        ('jitter', ctypes.c_long), ('shift', ctypes.c_int), ('stabil', ctypes.c_long),
                        ('jitcnt', ctypes.c_long), ('calcnt', ctypes.c_long), ('errcnt', ctypes.c_long),
                        ('stbcnt', ctypes.c_long), ('tai', ctypes.c_int), ('_', ctypes.c_int * 11)]
        libc = ctypes.CDLL(ctypes.util.find_library('c') or None, use_errno=True)
        tx = Timex()                                        # modes 0: read, change nothing
        state = libc.adjtimex(ctypes.byref(tx))
    except (OSError, AttributeError, ValueError):
        return None
    if state < 0 or tx.maxerror < 0:
        return None
    if state == TIME_ERROR or tx.status & STA_UNSYNC:
        return Reading('the kernel', 'nothing', "no time daemon keeps it synchronised (adjtimex: unsynchronised)")
    bound = tx.maxerror / 1e6
    if bound > TOLERANCE:
        return Reading('the kernel', 'nothing', f"synchronised, its error bound {bound:.1f} s past the tolerance "
                                                f"(offline too long, or not yet settled)")
    return Reading('the kernel', 'within', f"synchronised, its error at most {bound:.3f} s")


def _hosts_in(path, keys):
    out = []
    try:
        with open(path, encoding='utf-8', errors='replace') as fh:
            for ln in fh:
                w = ln.split('#', 1)[0].split()
                if len(w) >= 2 and w[0] in keys:
                    out.append(w[1])
    except OSError:
        pass
    return out


def _listed_dir(d, suffix):
    try:
        return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(suffix)]
    except OSError:
        return []


def host_servers():
    """The time servers this host was given, as its time daemon's configuration names them, in order, each once."""
    found = []
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\W32Time\Parameters') as k:
                found += [s.split(',')[0] for s in str(winreg.QueryValueEx(k, 'NtpServer')[0]).split()]
        except OSError:
            pass
    else:
        for p in ['/etc/chrony/chrony.conf', '/etc/chrony.conf'] + _listed_dir('/etc/chrony/sources.d', '.sources') \
                + _listed_dir('/etc/chrony/conf.d', '.conf'):
            found += _hosts_in(p, ('server', 'pool', 'peer'))
        for p in ('/etc/ntp.conf', '/etc/ntpsec/ntp.conf', '/private/etc/ntp.conf'):
            found += _hosts_in(p, ('server', 'pool', 'peer'))
        found += _hosts_in('/etc/ntpd.conf', ('server', 'servers'))     # OpenNTPD
        for p in ['/etc/systemd/timesyncd.conf'] + _listed_dir('/etc/systemd/timesyncd.conf.d', '.conf'):
            try:
                with open(p, encoding='utf-8', errors='replace') as fh:
                    for ln in fh:
                        m = re.match(r'\s*(?:NTP|FallbackNTP)\s*=\s*(.*)', ln)
                        if m:
                            found += m.group(1).split()
            except OSError:
                pass
    out = []
    for h in found:            # 127.127.x.x is ntpd's name for a reference clock — the local clock among them — no server
        if h and not h.startswith('127.127.') and h not in out:
            out.append(h)
    return out


def named_sources():
    """The sources this machine's keeper names in DAFTAR_TIME_SOURCES, or None where it names none."""
    v = os.environ.get('DAFTAR_TIME_SOURCES', '').strip()
    return [s for s in re.split(r'[\s,]+', v) if s] if v else None


def _split(source):
    m = re.fullmatch(r'\[([^\]]+)\](?::(\d+))?|([^:\s]+)(?::(\d+))?|([0-9a-fA-F:]+)', source)
    if not m:
        return source, 123
    if m.group(1):
        return m.group(1), int(m.group(2) or 123)
    if m.group(3):
        return m.group(3), int(m.group(4) or 123)
    return m.group(5), 123


def sntp(source, wait=WAIT):
    """What an SNTP server shows of this clock (RFC 4330): a Reading, `nothing` when it does not answer as a server."""
    host, port = _split(source)
    try:
        family, _t, _p, _c, addr = socket.getaddrinfo(host, port, 0, socket.SOCK_DGRAM)[0]
        with socket.socket(family, socket.SOCK_DGRAM) as s:
            s.settimeout(wait)
            nonce = random.getrandbits(64)          # the transmit time sent is a nonce: it says nothing of this clock
            t1 = time.time()
            s.sendto(b'\x23' + b'\0' * 39 + struct.pack('!Q', nonce), addr)     # LI 0, version 4, mode 3 (client)
            while True:
                data, frm = s.recvfrom(512)
                t4 = time.time()
                if len(data) >= 48 and frm[:2] == addr[:2] and struct.unpack('!Q', data[24:32])[0] == nonce:
                    break
    except (OSError, IndexError, UnicodeError):
        return Reading(source, 'nothing', "no answer")
    li, mode, stratum = data[0] >> 6, data[0] & 7, data[1]
    if mode != 4 or li == 3 or not 1 <= stratum <= 15:
        return Reading(source, 'nothing', "answered as no synchronised server")

    def ts(at):
        sec, frac = struct.unpack('!II', data[at:at + 8])
        return sec - NTP_EPOCH + frac / 2 ** 32
    t2, t3 = ts(32), ts(40)
    root_delay, root_disp = (struct.unpack('!i', data[4:8])[0] / 2 ** 16, struct.unpack('!I', data[8:12])[0] / 2 ** 16)
    offset = ((t2 - t1) + (t3 - t4)) / 2
    delay = max(0.0, (t4 - t1) - (t3 - t2))
    bound = abs(offset) + delay / 2 + abs(root_delay) / 2 + root_disp
    said = f"this clock is {abs(offset):.3f} s {'behind' if offset > 0 else 'ahead'} (to within {bound - abs(offset):.3f} s)"
    return Reading(source, 'within' if bound <= TOLERANCE else 'beyond', said)


def readings():
    """What each of this machine's sources shows of its clock."""
    named = named_sources()
    if named is not None:
        servers, out = named, []
    else:
        k = kernel()
        out = [k] if k else []
        if any(r.shows == 'within' for r in out):
            return out
        servers = host_servers()
        if not servers:
            out.append(Reading('this host', 'nothing', "names no time server: its time daemon is configured with none"))
    servers = servers[:MOST]
    got = [None] * len(servers)

    def ask(i, s):
        got[i] = sntp(s)
    threads = [threading.Thread(target=ask, args=(i, s), daemon=True) for i, s in enumerate(servers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(WAIT + 1)
    return out + [g or Reading(s, 'nothing', "no answer") for g, s in zip(got, servers)]


def may_stamp(found=None):
    """(True when this clock may stamp, the readings): one source at least shows it within, and none beyond."""
    found = readings() if found is None else found
    return any(r.shows == 'within' for r in found) and not any(r.shows == 'beyond' for r in found), found


def keeper(root):
    """Who keeps this machine, as the garden at `root` says: (its host bean, who owns it) — None for what it does not say."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import where as dmwhere
        import garden as dmgarden
        hid = dmwhere.here()[0]
        if not hid or not dmgarden.runs_core(root):
            return hid, None
        b = dmgarden.core_garden(root).beans.get(hid)
        owners = [str(r.get('by')) for _i, v, r in (b.items if b else []) if v == 'own' and r.get('of') == 'self'
                  and isinstance(r.get('by'), str)]
        return hid, (', '.join(owners) or None)
    except Exception:   # noqa: BLE001 — who keeps it is said where the garden says it; a refusal never dies on it
        return None, None


def refusal(found, root):
    """Why nothing is stamped, what each source showed, and what sets it right — naming this machine and its keeper."""
    hid, owner = keeper(root)
    gardener = None
    try:
        import importlib
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        gardener = importlib.import_module('pass').gardener_of(root)    # `pass` is a keyword: imported by name
    except Exception:          # noqa: BLE001 — the gardener is said where GARDEN.md says it
        pass
    who = owner or gardener or 'its keeper'
    shown = '; '.join(f"{r.source}: {r.said}" for r in found) or "no source: this host names no time server"
    machine = f"{socket.gethostname()}" + (f" (bean {hid})" if hid else "")
    fix = ("`w32tm /resync` (and w32time's NtpServer set)" if os.name == 'nt' else
           "a time daemon with servers it can reach (chrony, ntpd or systemd-timesyncd), or the servers named in "
           "DAFTAR_TIME_SOURCES")
    return (f"NOT STAMPED: this machine's clock ({machine}) cannot be shown within {TOLERANCE:.0f} s of its time "
            f"sources — {shown}. A stamp from it could write the wrong minute into every bean it saves, so nothing "
            f"was written. {who} keeps this machine: set its clock right with {fix}, then save again; "
            f"`python3 bin/clock.py` shows what each source sees.")


def main(argv):
    if argv and argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    ok, found = may_stamp()
    for r in found:
        print(f"{r.shows:<8} {r.source}: {r.said}")
    if not found:
        print("nothing  this host names no time server, and no kernel discipline shows this clock")
    print(f"clock: {'may stamp' if ok else 'may NOT stamp'} — tolerance {TOLERANCE:.0f} s, half a minute's stamp")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
