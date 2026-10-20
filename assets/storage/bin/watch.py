#!/usr/bin/env python3
"""watch — the storage watcher of a live directory (core 2.21, the form `schema`; assets/storage/README.md): between two
readings of it, what was added, what changed under its name, what is gone; each content kept the first time it is seen,
as a blob of the schema's history box on another disk, and each name's earlier contents kept as its versions, capped as
the node its name belongs at says (`versions`, `age`). A live directory is edited in place, so nothing in it is ever
linked or moved: the watcher reads it, and writes only into the history box.

    python3 assets/storage/bin/watch.py pass --before <index> --after <index> --root <the live directory>
                                             --history <the history box's directory> [--versions N] [--age "90 d"]
                                             [--prune]

`--before` and `--after` are two readings of the directory (a scan's index: path, type, hash). A content not in the
history box yet is copied there from the live directory, checked by its BLAKE3 against the reading, and made read-only;
a content whose bytes changed between the reading and the copy is said, never kept under a wrong name. Each version of
a name is a link in the box, `Versions/<its path>/<the moment it was first seen> <eight of its BLAKE3>`, to its blob.
Versions past the cap are listed; with `--prune` their names are removed, and a blob no name links any more with them
(its last name) — nothing else is ever removed.
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import stat
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path[:0] = [HERE, ROOT, os.path.join(ROOT, 'bin')]
from core import formats  # noqa: E402

BLOBS, VERSIONS = b'.blobs', b'Versions'


def reading(index):
    """{path: BLAKE3} of the files of a reading (an index of a scan's shape); a file of size 0 the empty digest."""
    db = sqlite3.connect(f'file:{index}?mode=ro', uri=True)
    cols = {r[1] for r in db.execute('PRAGMA table_info(entry)')}
    q = "SELECT path, hash" + (", size" if 'size' in cols else ", NULL") + " FROM entry WHERE type = 'f'"
    out = {}
    for p, h, size in db.execute(q):
        p = bytes(p) if isinstance(p, (bytes, bytearray, memoryview)) else os.fsencode(p)
        out[p] = h or (formats.EMPTY_BLAKE3 if size == 0 else None)
    return out


def secs(text):
    m = re.fullmatch(r'\s*(\d+(?:\.\d+)?) ?(s|min|h|d|wk)\s*', str(text or ''))
    if not m:
        raise SystemExit(f"watch: {text!r} is no length of time: a count and a unit of s, min, h, d, wk")
    return float(m.group(1)) * {'s': 1, 'min': 60, 'h': 3600, 'd': 86400, 'wk': 604800}[m.group(2)]


def pass_(before, after, root, history, versions=None, age=None, prune=False, now=None):
    """One pass. Returns {'added', 'changed', 'gone', 'kept', 'unkept', 'past the cap', 'pruned'}."""
    import blake3
    now = time.time() if now is None else now
    old, new = reading(before), reading(after)
    out = {'added': sorted(p for p in new if p not in old), 'gone': sorted(p for p in old if p not in new),
           'changed': sorted(p for p in new if p in old and new[p] != old[p]), 'kept': 0, 'unkept': [],
           'past the cap': [], 'pruned': 0}
    root, history = os.fsencode(root), os.fsencode(history)
    blobs = os.path.join(history, BLOBS)
    os.makedirs(blobs, exist_ok=True)
    stamp = time.strftime('%Y-%m-%dT%H%M%S', time.localtime(now)).encode()
    for p, h in sorted(new.items()):
        if not h:
            continue
        blob = os.path.join(blobs, h.encode())
        if not os.path.exists(blob):                       # a content first seen: copied, checked, made read-only
            tmp = blob + b'.part'
            try:
                b = blake3.blake3()
                with open(os.path.join(root, p), 'rb') as src, open(tmp, 'wb') as dst:
                    for block in iter(lambda: src.read(1 << 20), b''):
                        b.update(block)
                        dst.write(block)
            except OSError as e:
                out['unkept'].append((formats.escape(p), f'not read: {e.strerror}'))
                continue
            if b.hexdigest() != h:
                os.remove(tmp)
                out['unkept'].append((formats.escape(p), 'its bytes changed since the reading: kept at the next pass'))
                continue
            os.replace(tmp, blob)
            os.chmod(blob, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            out['kept'] += 1
        vdir = os.path.join(history, VERSIONS, p)
        have = sorted(os.listdir(vdir)) if os.path.isdir(vdir) else []
        if not any(v.endswith(b' ' + h[:8].encode()) for v in have):
            os.makedirs(vdir, exist_ok=True)
            os.link(blob, os.path.join(vdir, stamp + b' ' + h[:8].encode()))
    for vdir_rel in _version_dirs(history):                # the cap: the latest `versions`, none older than `age`
        vdir = os.path.join(history, VERSIONS, vdir_rel)
        names = sorted(os.listdir(vdir), reverse=True)
        for i, v in enumerate(names):
            when = time.mktime(time.strptime(v.split(b' ')[0].decode(), '%Y-%m-%dT%H%M%S'))
            past = (versions is not None and i >= versions) or (age is not None and i > 0 and now - when > age)
            if not past:
                continue
            out['past the cap'].append(formats.escape(os.path.join(vdir_rel, v)))
            if prune:
                os.remove(os.path.join(vdir, v))
                out['pruned'] += 1
    if prune:                                              # a blob no name links any more: its last name went
        for bn in os.listdir(blobs):
            bp = os.path.join(blobs, bn)
            if os.stat(bp).st_nlink == 1 and not bn.endswith(b'.part'):
                os.chmod(bp, stat.S_IWUSR | stat.S_IRUSR)
                os.remove(bp)
    return out


def _version_dirs(history):
    base = os.path.join(history, VERSIONS)
    for d, _dirs, files in os.walk(base):
        if files:
            yield os.path.relpath(d, base)


def main(argv):
    ap = argparse.ArgumentParser(prog='watch.py', description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    x = sub.add_parser('pass')
    x.add_argument('--before', required=True)
    x.add_argument('--after', required=True)
    x.add_argument('--root', required=True)
    x.add_argument('--history', required=True)
    x.add_argument('--versions', type=int)
    x.add_argument('--age')
    x.add_argument('--prune', action='store_true')
    a = ap.parse_args(argv)
    out = pass_(a.before, a.after, a.root, a.history, a.versions, secs(a.age) if a.age else None, a.prune)
    print(json.dumps({k: (v if isinstance(v, int) else len(v)) for k, v in out.items()}))
    for k in ('changed', 'added', 'gone'):
        for p in out[k][:10]:
            print(f"  {k}: {formats.escape(p)}")
    for p in out['past the cap'][:10]:
        print(f"  past the cap{' (pruned)' if a.prune else ''}: {p}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
