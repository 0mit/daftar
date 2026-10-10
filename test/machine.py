"""What a suite names of the machine it runs on, so that its verdicts are never the machine's: a time source — an SNTP
server (RFC 4330) on the loopback answering with this machine's clock, moved by `offset` seconds, named in
DAFTAR_TIME_SOURCES, so that a save stamps (or refuses to) by a source the suite chose and never by the network or by how
the machine keeps its time (bin/clock.py) — and an empty cache of fetched standards (DAFTAR_STANDARDS_CACHE), so that a
scheme the law holds fetched is read from the release's copy, or from what the suite fetched, never from what this
machine's person fetched (bin/fetch.py)."""
import os
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
    """Name a true time source and an empty standards cache for this process and what it runs, unless named already."""
    if not os.environ.get('DAFTAR_TIME_SOURCES'):
        os.environ['DAFTAR_TIME_SOURCES'] = time_source()
    if not os.environ.get('DAFTAR_STANDARDS_CACHE'):
        os.environ['DAFTAR_STANDARDS_CACHE'] = tempfile.mkdtemp(prefix='daftar-suite-standards-')
