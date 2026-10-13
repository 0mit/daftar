"""What a suite names of the machine it runs on, so that its verdicts are never the machine's: a time source — an SNTP
server (RFC 4330) on the loopback answering with this machine's clock, moved by `offset` seconds, named in
DAFTAR_TIME_SOURCES, so that a save stamps (or refuses to) by a source the suite chose and never by the network or by how
the machine keeps its time (bin/clock.py) — and an empty cache of fetched standards (DAFTAR_STANDARDS_CACHE), so that a
scheme the law holds fetched is read from the release's copy, or from what the suite fetched, never from what this
machine's person fetched (bin/fetch.py), kept in a temporary folder of the suite's own (TMPDIR), which goes when the
suite ends, with whatever else the suite or a program it runs left there — a daftard state folder among it
(DAFTARD_STATE), where a hub's own key is made (bin/hub.py install), and never in this account's own."""
import atexit
import os
import shutil
import tempfile
import socket
import struct
import threading
import time

NTP_EPOCH = 2208988800


def _ntp(t):
    return struct.pack('!II', int(t) + NTP_EPOCH, int((t % 1) * 2 ** 32))


def time_source(offset=0.0, answer=True):
    """Serve this clock moved by `offset` seconds (or never answer); returns the source, `127.0.0.1:<port>`."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('127.0.0.1', 0))

    def serve():
        while True:
            try:
                data, frm = s.recvfrom(512)
            except OSError:
                return
            if not answer or len(data) < 48:
                continue
            now = time.time() + offset
            s.sendto(b'\x24\x02\x00\xec' + b'\0' * 8 + b'LOCL' + _ntp(now) + data[40:48] + _ntp(now) + _ntp(now), frm)
    threading.Thread(target=serve, daemon=True).start()
    return f"127.0.0.1:{s.getsockname()[1]}"


def ensure():
    """Name, for this process and what it runs, unless named already: a temporary folder of its own (TMPDIR), removed
    when the process that made it ends, so nothing the suite or a program it runs leaves there outlives it (a garden it
    grew, a browser's own leftovers, a hub's key); a daftard state folder in it, whatever the environment named, so no
    key a suite makes lands in this account's own; a true time source; and an empty standards cache, in that folder."""
    if not os.environ.get('DAFTAR_SUITE_TMP'):
        d = tempfile.mkdtemp(prefix='ds-')        # short: a browser's socket under it must stay within 107 bytes
        atexit.register(shutil.rmtree, d, True)
        os.environ['DAFTAR_SUITE_TMP'] = os.environ['TMPDIR'] = tempfile.tempdir = d
        os.environ['DAFTARD_STATE'] = os.path.join(d, 'daftard-state')
    if not os.environ.get('DAFTAR_TIME_SOURCES'):
        os.environ['DAFTAR_TIME_SOURCES'] = time_source()
    if not os.environ.get('DAFTAR_STANDARDS_CACHE'):
        os.environ['DAFTAR_STANDARDS_CACHE'] = tempfile.mkdtemp(prefix='standards-')
