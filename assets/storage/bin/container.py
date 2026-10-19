#!/usr/bin/env python3
"""container — an archive or a cabinet read as a volume: its members listed, each hashed by BLAKE3 as it streams, never
unpacked to disk, into an index of the shape a scan writes, which `daftar import file-tree` reads with the container's
content as the volume's carrier (core 2.18: a volume's carrier may be a content; assets/storage/README.md).

    python3 assets/storage/bin/container.py list <file> --index <out.sqlite> [--passphrase-stdin]

It reads through libarchive (python-libarchive-c): zip, with ZipCrypto and AES, tar and its compressions, 7z, rar
(rar 4), cab, iso 9660, cpio. A passphrase comes on standard input, from a pipe (a wallet's query), never on a command
line or in a file; it is held in memory for the reading and nowhere else. A member that needs a passphrase none was
given for is listed with no digest and says so (`err`); the exit code is then 3, so a caller asks the wallet and reads
it again. A member whose path climbs out of the container (`..`) or is absolute is listed by its name alone, its
error said. The digests are BLAKE3's (the `blake3` module, the reference implementation's).

The index: `entry(path, type, size, mtime_ns, ino, nlink, ext, hash, err)`, each folder of a member's path a `d` row
once, and `meta(k, v)`: files, bytes, hashed, unread, done, format, container (its BLAKE3) — what scan.py writes for a
volume. Exit: 0 read whole; 2 not a container this reader reads; 3 a passphrase is needed.
"""
import argparse
import os
import sqlite3
import sys
import time

SCHEMA = """
CREATE TABLE entry (path BLOB PRIMARY KEY, type TEXT, size INTEGER, mtime_ns INTEGER, ino INTEGER, nlink INTEGER,
                    ext TEXT, hash TEXT, err TEXT);
CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT);
"""


def ext_of(name):
    i = name.rfind(b'.')
    e = name[i + 1:].lower() if 0 < i < len(name) - 1 else b''
    return e.decode('utf-8', 'replace') if len(e) <= 16 else ''


def tidy(path):
    """A member's path as a tree names it, or (its last name, why) where it would climb out or is absolute."""
    if isinstance(path, str):
        path = path.encode('utf-8', 'surrogateescape')
    parts = [p for p in path.replace(b'\\', b'/').split(b'/') if p not in (b'', b'.')]
    if path.startswith((b'/', b'\\')) or b'..' in parts:
        return (parts[-1] if parts else b'unnamed'), 'its path climbs out of the container or is absolute'
    return b'/'.join(parts), None


def read(path, index, passphrase=None):
    import blake3
    import libarchive
    if os.path.exists(index):
        os.remove(index)
    db = sqlite3.connect(index)
    db.executescript(SCHEMA)
    dirs, stats = set(), {'files': 0, 'bytes': 0, 'hashed': 0, 'unread': 0, 'locked': 0}
    fmt = None
    try:
        with libarchive.file_reader(path, passphrase=passphrase) as arc:
            for e in arc:
                fmt = fmt or getattr(arc, 'format_name', None)
                p, why = tidy(e.pathname or b'')
                if not p:
                    continue
                parts = p.split(b'/')
                for i in range(1, len(parts) + (0 if not e.isdir else 1)):
                    d = b'/'.join(parts[:i])
                    if d not in dirs:
                        dirs.add(d)
                        db.execute("INSERT OR IGNORE INTO entry (path, type) VALUES (?, 'd')", (d,))
                if e.isdir:
                    continue
                if not e.isfile:
                    db.execute("INSERT OR IGNORE INTO entry (path, type, err) VALUES (?, 'o', ?)", (p, why))
                    continue
                stats['files'] += 1
                size, h, err = e.size, None, why
                try:
                    b = blake3.blake3()
                    n = 0
                    for block in e.get_blocks():
                        b.update(block)
                        n += len(block)
                    h, size = b.hexdigest(), n
                    stats['hashed'] += 1
                    stats['bytes'] += n
                except libarchive.ArchiveError as x:
                    msg = str(x)
                    locked = 'passphrase' in msg.lower() or 'encrypt' in msg.lower() or 'password' in msg.lower()
                    stats['locked' if locked else 'unread'] += 1
                    err = 'needs its passphrase' if locked else f'unread: {msg[:200]}'
                mt = int((e.mtime or 0) * 1e9) if e.mtime else None
                db.execute("INSERT OR REPLACE INTO entry VALUES (?, 'f', ?, ?, NULL, 1, ?, ?, ?)",
                           (p, size, mt, ext_of(p.rpartition(b'/')[2]), h, err))
    except libarchive.ArchiveError as x:
        db.close()
        os.remove(index)
        msg = str(x)
        if 'passphrase' in msg.lower() or 'encrypt' in msg.lower():
            return 3, f"needs its passphrase: {msg[:200]}"
        return 2, f"not read as a container: {msg[:200]}"
    meta = {'files': stats['files'], 'bytes': stats['bytes'], 'hashed': stats['hashed'],
            'unread': stats['unread'] + stats['locked'], 'done': time.time(), 'format': fmt or '',
            'container': os.path.basename(path)}
    db.executemany('INSERT OR REPLACE INTO meta VALUES (?, ?)', [(k, str(v)) for k, v in meta.items()])
    db.commit()
    db.close()
    return (3 if stats['locked'] else 0), (f"{stats['hashed']:,} of {stats['files']:,} members hashed, "
                                           f"{stats['bytes'] / 1e6:,.1f} MB" + (f"; {stats['locked']:,} need the "
                                           f"passphrase" if stats['locked'] else ''))


def main(argv):
    import locale
    locale.setlocale(locale.LC_ALL, '')                 # libarchive reads a member's name in the locale's encoding
    ap = argparse.ArgumentParser(prog='container.py', description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    x = sub.add_parser('list')
    x.add_argument('file')
    x.add_argument('--index', required=True)
    x.add_argument('--passphrase-stdin', action='store_true')
    a = ap.parse_args(argv)
    pw = sys.stdin.buffer.read().rstrip(b'\n') if a.passphrase_stdin else None
    code, said = read(a.file, a.index, pw.decode('utf-8', 'surrogateescape') if pw else None)
    del pw
    print(f"container: {a.file}: {said}", file=sys.stderr)
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
