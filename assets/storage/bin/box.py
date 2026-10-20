#!/usr/bin/env python3
"""box — a storage box: one flat folder of blobs, each a content named by its BLAKE3 (`.blobs/<64 hex>`), read-only,
and the schemas of names its nodes give, each a hard link to its blob (core 2.21: the form `schema`, `links: true`;
assets/storage/README.md). A schema takes no room; adding or changing one links, and moves no byte.

    python3 assets/storage/bin/box.py plan --store S --of <volume or folder> --scheme <scheme> [--schema <code>]
                                           --out <plan.jsonl>              the names the box's schema gives, not held yet
    python3 assets/storage/bin/box.py link --plan <plan.jsonl> --root <the box's directory> [--store S --of <volume>]
                                           [--dry]                         make them, each a link to its blob
    python3 assets/storage/bin/box.py verify --root <the box's directory> [--sample N]   every blob's BLAKE3 its name

`link` writes into the box only: a blob where its content has none yet (a link of a name that holds it — never a
copy, so the box takes no more room), then each name its schema gives, a link to the blob. A name already there with
another content is never overwritten, and nothing is removed: a name no node gives is listed by the reading, and stays
until a person says. Each blob is made read-only (0444), so a program that writes in place is refused, and one that
saves anew breaks the link instead. With `--store`, each name made is kept in the store as a holding through the
volume's one holding of the blob's inode (`hold … through`), known by a `make` of this tool.
"""
import argparse
import json
import os
import stat
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GARDEN = os.environ.get('DAFTAR_GARDEN') or os.getcwd()
sys.path[:0] = [HERE, ROOT, os.path.join(ROOT, 'bin')]
from core import formats  # noqa: E402

BLOBS = b'.blobs'


def b3_of(path):
    import blake3
    h = blake3.blake3()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def plan(store, of, scheme, schema, out):
    import storage as ST
    S = ST.Store(ST.store_path(store, GARDEN))
    W = ST.Words(GARDEN)
    schema, box, res, rows = ST.layout(S, W, scheme, of, schema)
    if not box:
        raise SystemExit(f"box: the schema {scheme}:{schema} has no node of a box (`links: true`)")
    with open(out, 'w', encoding='utf-8') as fh:
        for p, b3, frm in rows:
            fh.write(json.dumps({'path': formats.escape(p), 'blob': b3, 'from': formats.escape(frm)}) + '\n')
    return schema, res, len(rows)


def link(plan_path, root, dry=False, store=None, of=None):
    """Make the plan's names in the box at `root`. Returns {'blobs': n, 'names': n, 'refused': [(path, why)]}."""
    root = os.fsencode(root)
    made = {'blobs': 0, 'names': 0, 'refused': []}
    kept, relinked = [], []
    blobs = os.path.join(root, BLOBS)
    if not dry:
        os.makedirs(blobs, exist_ok=True)
    for line in open(plan_path, encoding='utf-8'):
        r = json.loads(line)
        path, b3, frm = formats.unescape(r['path']), r['blob'], formats.unescape(r['from'])
        blob = os.path.join(blobs, b3.encode())
        src = os.path.join(root, frm)
        if not os.path.exists(blob):
            if not os.path.isfile(src):
                made['refused'].append((r['path'], 'its blob is missing and the name it was to be linked from is not there'))
                continue
            if not dry:
                os.link(src, blob)
                os.chmod(blob, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                ino = os.stat(blob).st_ino
                kept.append((BLOBS + b'/' + b3.encode(), b3, ino))
                relinked.append((frm, b3, ino))
            made['blobs'] += 1
        dest = os.path.join(root, path)
        if os.path.lexists(dest):
            same = os.path.exists(blob) and os.path.samefile(dest, blob)
            if not same:
                made['refused'].append((r['path'], 'a name is there already, of another content: left as it is'))
            continue
        if not dry:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            os.link(blob, dest)
            kept.append((path, b3, os.stat(dest).st_ino))
        made['names'] += 1
    if kept and store and of:
        keep(store, of, kept, relinked)
    return made


def keep(store, of, kept, relinked=()):
    """Each name made, kept in the store: its folder (made where new) holds the content through the volume's one
    holding of the blob's inode, known by a `make` of this tool."""
    import store as dmstore
    import storage as ST
    S = dmstore.Store(ST.store_path(store, GARDEN), root=GARDEN)
    lt = time.localtime()
    off = lt.tm_gmtoff // 60
    at = time.strftime('%Y-%m-%dT%H:%M:%S', lt) + f"{'+' if off >= 0 else '-'}{abs(off) // 60:02d}:{abs(off) % 60:02d}"
    act = f"made-{time.strftime('%Y%m%d-%H%M%S')}"
    with S.batch():
        S.put(of, 'make', {'id': act, 'by': os.uname().nodename.split('.')[0].lower() if hasattr(os, 'uname') else 'host',
                           'at': at, 'note': 'names of a box linked to its blobs by box.py'}, judge=False)
        for path, b3, ino in kept:
            parent, _, name = path.rpartition(b'/')
            folder = of
            acc = b''
            for part in parent.split(b'/') if parent else []:
                up = folder
                acc = acc + b'/' + part if acc else part
                folder = formats.folder_id(of, acc)
                if not S.kind_of(folder):
                    S.being(folder, 'folder')
                    S.put(folder, 'part', {'by': folder, 'of': up}, act=f'{of}#{act}', judge=False)
                    S.put(folder, 'name', {'by': up, 'of': folder, 'as': formats.escape(part)}, act=f'{of}#{act}',
                          judge=False)
            c = formats.content_id(b3)
            if not S.kind_of(c):
                S.being(c, 'content')
            S.put(of, 'hold', {'id': f'i{ino}', 'by': of, 'of': c}, act=f'{of}#{act}', judge=False)
            S.put(folder, 'hold', {'by': folder, 'of': c, 'as': formats.escape(name), 'through': f'{of}#i{ino}'},
                  act=f'{of}#{act}', judge=False)
        for path, b3, ino in relinked:                 # the name a blob was linked from: one inode now, held through it
            parent, _, name = path.rpartition(b'/')
            folder = formats.folder_id(of, parent) if parent else of
            c = formats.content_id(b3)
            fr, cr = S._being_row(folder), S._being_row(c)
            if not (fr and cr):
                continue
            for (sid,) in S.db.execute("SELECT id FROM v_hold WHERE being = ? AND b_of = ? AND t_as = ? AND t_through "
                                       "IS NULL", (fr[0], cr[0], formats.escape(name))).fetchall():
                S.gone(folder, sid, by=f'{of}#{act}', why='linked to its blob in the box: one inode with the blob, held '
                                                          'through the volume\'s holding of it')
            S.put(folder, 'hold', {'by': folder, 'of': c, 'as': formats.escape(name), 'through': f'{of}#i{ino}'},
                  act=f'{of}#{act}', judge=False)
    S.close()


def verify(root, sample=None):
    """[(blob, what it holds)] of every blob whose bytes are not the content its name says, and how many were read."""
    root = os.fsencode(root)
    blobs = os.path.join(root, BLOBS)
    bad, n = [], 0
    for name in sorted(os.listdir(blobs)) if os.path.isdir(blobs) else []:
        if sample and n >= sample:
            break
        n += 1
        got = b3_of(os.path.join(blobs, name))
        if got != name.decode():
            bad.append((name.decode(), got))
    return bad, n


def main(argv):
    ap = argparse.ArgumentParser(prog='box.py', description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    x = sub.add_parser('plan')
    x.add_argument('--store')
    x.add_argument('--of', required=True)
    x.add_argument('--scheme', required=True)
    x.add_argument('--schema')
    x.add_argument('--out', required=True)
    x = sub.add_parser('link')
    x.add_argument('--plan', required=True)
    x.add_argument('--root', required=True)
    x.add_argument('--dry', action='store_true')
    x.add_argument('--store')
    x.add_argument('--of')
    x = sub.add_parser('verify')
    x.add_argument('--root', required=True)
    x.add_argument('--sample', type=int)
    a = ap.parse_args(argv)
    if a.cmd == 'plan':
        schema, res, n = plan(a.store, a.of, a.scheme, a.schema, a.out)
        print(f"{a.of}: the box's schema {a.scheme}:{schema}: {n:,} names to link, in {a.out}")
        for node, g in res.items():
            print(f"  {node:24} in place {g['in place']:>8,}  to link {g['to link']:>8,}  out of place {g['out of place']:>8,}")
    elif a.cmd == 'link':
        made = link(a.plan, a.root, a.dry, a.store, a.of)
        print(json.dumps({'blobs': made['blobs'], 'names': made['names'], 'refused': len(made['refused']),
                          'dry': a.dry}))
        for p, why in made['refused'][:20]:
            print(f"  refused {p}: {why}")
    else:
        bad, n = verify(a.root, a.sample)
        print(f"{n:,} blobs read: {len(bad)} not the content their name says")
        for name, got in bad[:20]:
            print(f"  {name} holds {got}")
        return 1 if bad else 0
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
