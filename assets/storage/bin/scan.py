#!/usr/bin/env python3
"""scan — a mounted tree read into an index, read-only on the tree: the listing `daftar import file-tree` reads as a
volume (core/law/formats.yaml, the reader `file-tree`).

    python3 assets/storage/bin/scan.py --root <mounted dir> --index <out.sqlite> [--progress <out.json>]
                                       [--exclude <absolute path> ...] [--walk-only]

Every entry under --root, never crossing into another filesystem, gets a row: its path beneath the root, as the
filesystem's own bytes; its type (`f` a file, `d` a folder, `l` a symbolic link, `o` anything else); its size,
modification time, inode and how many names it has; and, for a regular file, its lowercased extension and the BLAKE3 of
its content (the `blake3` module, the reference implementation's), read front to back by one reader. A file of size 0
has no digest; the names of one inode are read once.

RESUMABLE. A run walks the whole tree again, which is cheap beside reading every byte, keeps each digest whose file has
the same size, modification time and inode as before, and reads only what is left. So a disk unplugged mid-scan,
plugged in again, carries on where it stopped, and a second run over an unchanged tree reads nothing.

AT THE END it writes <index>.b3 beside the index: a BLAKE3 checklist of the tree, relative to its root, so `cd <root> &&
b3sum --check <index>.b3` checks the tree, or a copy of it, with no code of daftar's. A name that is not UTF-8 cannot
be written there, and is counted in `meta` instead.

The index: `entry(path, type, size, mtime_ns, ino, nlink, ext, hash, err)` and `meta(k, v)` — the shape container.py
writes for an archive. Then:

    python3 bin/import.py file-tree <out.sqlite> --volume <its id> --carrier <the disk that holds it> --into store:<name>

EXIT: 0 done; 3 too many read errors in a row (the disk may be failing: stop reading it); 4 the tree went away (it was
unplugged); 2 bad arguments. With --progress, a JSON file of how far it has come is written about once a second.
"""
import argparse, json, os, sqlite3, stat, sys, time

CHUNK = 8 << 20
IO_ERRORS_IN_A_ROW = 50

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS entry (
  path BLOB PRIMARY KEY, type TEXT NOT NULL, size INTEGER, mtime_ns INTEGER, ino INTEGER, nlink INTEGER,
  ext TEXT, hash TEXT, err TEXT
) WITHOUT ROWID;
"""


class Gone(Exception):
    """The tree is not there any more."""


class Failing(Exception):
    """Too many reads failed in a row."""


class Progress:
    """How far the scan has come, rewritten about once a second where a file is named for it; nothing where none is."""

    def __init__(self, path):
        self.path, self.p, self.last = path, {'phase': 'start', 'started': time.time(), 'pid': os.getpid()}, 0
        self.rates = []                                       # (time, bytes read) over the last minute

    def set(self, force=False, **kw):
        self.p.update(kw)
        now = time.time()
        if 'hashed_bytes' in kw:
            self.rates.append((now, kw['hashed_bytes']))
            while self.rates and now - self.rates[0][0] > 60:
                self.rates.pop(0)
            if len(self.rates) > 1 and self.rates[-1][0] > self.rates[0][0]:
                rate = (self.rates[-1][1] - self.rates[0][1]) / (self.rates[-1][0] - self.rates[0][0])
                self.p['rate_bps'] = rate
                left = self.p.get('to_hash_bytes', 0) - kw['hashed_bytes']
                self.p['eta_s'] = left / rate if rate > 0 else None
        if self.path and (force or now - self.last >= 1):
            self.p['updated'] = now
            tmp = self.path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.p, f)
            os.replace(tmp, self.path)
            self.last = now


def ext_of(name):
    i = name.rfind(b'.')
    if i <= 0 or i == len(name) - 1:
        return ''
    e = name[i + 1:].lower()
    return e.decode('utf-8', 'replace') if len(e) <= 16 else ''


def walk(root, excludes, db, prog):
    """Every entry under root into the table `walk`; never into another filesystem."""
    db.execute('DROP TABLE IF EXISTS walk')
    db.execute('CREATE TABLE walk (path BLOB PRIMARY KEY, type TEXT NOT NULL, size INTEGER, mtime_ns INTEGER, '
               'ino INTEGER, nlink INTEGER, ext TEXT, hash TEXT, err TEXT) WITHOUT ROWID')
    root_b = os.fsencode(root)
    try:
        dev = os.lstat(root_b).st_dev
    except OSError as e:
        raise Gone(str(e))
    rows, n, nfiles, nbytes = [], 0, 0, 0
    stack = [(root_b, b'')]
    while stack:
        absd, reld = stack.pop()
        try:
            it = list(os.scandir(absd))
        except OSError as e:
            if not os.path.isdir(root_b):
                raise Gone(str(e))
            rows.append((reld or b'.', 'd', None, None, None, None, '', None, f'scandir: {e.strerror}'))
            continue
        for d in it:
            rel = reld + b'/' + d.name if reld else d.name
            if d.path in excludes:
                continue
            try:
                st = d.stat(follow_symlinks=False)
            except OSError as e:
                rows.append((rel, 'o', None, None, None, None, '', None, f'stat: {e.strerror}'))
                continue
            m = st.st_mode
            if stat.S_ISREG(m):
                t = 'f'
                nfiles += 1
                nbytes += st.st_size
            elif stat.S_ISDIR(m):
                t = 'd'
            elif stat.S_ISLNK(m):
                t = 'l'
            else:
                t = 'o'
            err = None
            if t == 'd':
                if st.st_dev != dev:
                    err = 'another filesystem: not entered'
                else:
                    stack.append((d.path, rel))
            rows.append((rel, t, st.st_size, st.st_mtime_ns, st.st_ino, st.st_nlink,
                         ext_of(d.name) if t == 'f' else '', None, err))
        n += len(it)
        if len(rows) >= 5000:
            db.executemany('INSERT OR REPLACE INTO walk VALUES (?,?,?,?,?,?,?,?,?)', rows)
            rows = []
            prog.set(phase='walk', entries=n, files=nfiles, bytes=nbytes)
    db.executemany('INSERT OR REPLACE INTO walk VALUES (?,?,?,?,?,?,?,?,?)', rows)
    prog.set(force=True, phase='walk', entries=n, files=nfiles, bytes=nbytes)
    return n, nfiles, nbytes


def merge(db):
    """Keep each digest whose file did not change; the walk becomes the entries."""
    db.execute("UPDATE walk SET hash = (SELECT e.hash FROM entry e WHERE e.path = walk.path AND e.type = 'f' "
               "AND e.size = walk.size AND e.mtime_ns = walk.mtime_ns AND e.ino = walk.ino) WHERE type = 'f'")
    db.execute('DELETE FROM entry')
    db.execute('INSERT INTO entry SELECT * FROM walk')
    db.execute('DROP TABLE walk')
    db.commit()


def digest(path, on_bytes):
    """(BLAKE3 hex, None), or (None, why): the file read front to back, its bytes counted as they are read."""
    import blake3
    h = blake3.blake3()
    try:
        with open(path, 'rb', buffering=0) as f:
            while True:
                b = f.read(CHUNK)
                if not b:
                    break
                h.update(b)
                on_bytes(len(b))
    except OSError as e:
        return None, f'read: {e.strerror or e}'
    return h.hexdigest(), None


def alive(root_b):
    """The tree is still there to read: its root lists."""
    try:
        with os.scandir(root_b) as it:
            next(it, None)
        return True
    except OSError:
        return False


def hash_all(root, db, prog):
    root_b = os.fsencode(root)
    todo = db.execute("SELECT count(*), coalesce(sum(size), 0) FROM entry WHERE type = 'f' AND size > 0 "
                      "AND hash IS NULL").fetchone()
    st = {'bytes': 0, 'hashed': 0, 'errors': 0, 'io_in_a_row': 0, 'last_ino': None, 'last_hash': None}
    prog.set(force=True, phase='hash', to_hash_files=todo[0], to_hash_bytes=todo[1], hashed_files=0, hashed_bytes=0,
             errors=0)

    def counted(n):
        st['bytes'] += n
        prog.set(hashed_bytes=st['bytes'], hashed_files=st['hashed'])

    key = (-1, b'')
    while True:
        # by inode, near enough to the order the data lies in on a disk that seeks; the names of one inode together
        chunk = db.execute("SELECT ino, path, size, nlink FROM entry WHERE type = 'f' AND size > 0 AND hash IS NULL "
                           "AND (ino, path) > (?, ?) ORDER BY ino, path LIMIT 20000", key).fetchall()
        if not chunk:
            break
        key = (chunk[-1][0], chunk[-1][1])
        for ino, path, size, nlink in chunk:
            if nlink > 1 and ino == st['last_ino'] and st['last_hash']:
                db.execute('UPDATE entry SET hash = ? WHERE path = ?', (st['last_hash'], path))
                st['bytes'] += size
                continue
            h, e = digest(os.path.join(root_b, path), counted)
            db.execute('UPDATE entry SET hash = ?, err = ? WHERE path = ?', (h, e, path))
            if h:
                st['hashed'] += 1
                st['io_in_a_row'] = 0
                st['last_ino'], st['last_hash'] = ino, h
                continue
            st['errors'] += 1
            if not alive(root_b):                       # unplugged, or the mount went: stop, carry on later
                db.commit()
                raise Gone(e or 'the tree went away')
            st['io_in_a_row'] = st['io_in_a_row'] + 1 if e and 'Input/output error' in e else 0
            if st['io_in_a_row'] >= IO_ERRORS_IN_A_ROW:
                db.commit()
                prog.set(force=True, errors=st['errors'], phase='io-errors')
                raise Failing()
        db.commit()
        prog.set(hashed_files=st['hashed'], hashed_bytes=st['bytes'], errors=st['errors'])
    db.commit()
    prog.set(force=True, hashed_files=st['hashed'], hashed_bytes=st['bytes'], errors=st['errors'])
    return st['hashed'], st['errors']


def manifest(db, out):
    """A BLAKE3 checklist relative to the root, as b3sum writes one; a name that is not UTF-8 cannot be in one, and is
    counted."""
    skipped = 0
    tmp = out + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        for h, p in db.execute("SELECT hash, path FROM entry WHERE type = 'f' AND hash IS NOT NULL ORDER BY path"):
            try:
                name = p.decode('utf-8')
            except UnicodeDecodeError:
                skipped += 1
                continue
            if '\\' in name or '\n' in name:              # b3sum's own escaping
                f.write('\\' + h + '  ' + name.replace('\\', '\\\\').replace('\n', '\\n') + '\n')
            else:
                f.write(h + '  ' + name + '\n')
    os.replace(tmp, out)
    return skipped


def give_back(paths):
    """Files made under sudo belong to the person who ran it."""
    uid, gid = os.environ.get('SUDO_UID'), os.environ.get('SUDO_GID')
    if uid and gid and hasattr(os, 'chown'):
        for p in paths:
            for q in (p, p + '-wal', p + '-shm'):
                if q and os.path.exists(q):
                    os.chown(q, int(uid), int(gid))


def space(root):
    """(size, free) of the filesystem the root is on, where the system says."""
    if hasattr(os, 'statvfs'):
        v = os.statvfs(root)
        return v.f_blocks * v.f_frsize, v.f_bavail * v.f_frsize
    import shutil
    u = shutil.disk_usage(root)
    return u.total, u.free


def put_meta(db, values):
    for k, v in values.items():
        db.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', (k, str(v)))
    db.commit()


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('--root', required=True)
    a.add_argument('--index', required=True)
    a.add_argument('--progress')
    a.add_argument('--exclude', action='append', default=[])
    a.add_argument('--walk-only', action='store_true',
                   help='the entries without their digests, then stop: a failing disk listed before it is read whole; '
                        'a later run without it reads them, keeping what the walk kept')
    a = a.parse_args(argv)
    if not os.path.isdir(a.root):
        print(f'scan: {a.root}: no folder to read', file=sys.stderr)
        return 2
    if not a.walk_only:
        try:
            import blake3  # noqa: F401
        except ImportError:
            print('scan: the `blake3` module is not installed (pip install blake3)', file=sys.stderr)
            return 2
    prog = Progress(a.progress)
    db = sqlite3.connect(a.index)
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript(SCHEMA)
    meta = dict(db.execute('SELECT k, v FROM meta'))
    size, free = space(a.root)
    put_meta(db, {'root': os.path.abspath(a.root), 'runs': int(meta.get('runs', 0)) + 1, 'run_started': time.time(),
                  'fs_size': size, 'fs_free': free, 'python': sys.version.split()[0], 'done': ''})
    give_back([a.index, a.progress])
    excludes = {os.fsencode(os.path.abspath(x)) for x in a.exclude}
    try:
        n, nf, nb = walk(a.root, excludes, db, prog)
        prog.set(force=True, phase='merge')
        merge(db)
        if a.walk_only:
            errs = db.execute('SELECT count(*) FROM entry WHERE err IS NOT NULL').fetchone()[0]
            put_meta(db, {'walked': time.time(), 'entries': n, 'files': nf, 'bytes': nb, 'errors': errs})
            db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            db.close()
            prog.set(force=True, phase='walked', errors=errs)
            give_back([a.index, a.progress])
            return 0
        hash_all(a.root, db, prog)
    except Gone as e:
        prog.set(force=True, phase='gone', note=str(e)[:300])
        db.close()
        give_back([a.index, a.progress])
        return 4
    except Failing:
        db.close()
        give_back([a.index, a.progress])
        return 3
    prog.set(force=True, phase='manifest')
    out = os.path.splitext(a.index)[0] + '.b3'
    skipped = manifest(db, out)
    errs = db.execute('SELECT count(*) FROM entry WHERE err IS NOT NULL').fetchone()[0]
    put_meta(db, {'done': time.time(), 'entries': n, 'files': nf, 'bytes': nb, 'errors': errs,
                  'manifest': os.path.basename(out), 'manifest_skipped_non_utf8': skipped})
    db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    db.close()
    prog.set(force=True, phase='done', errors=errs)
    give_back([a.index, a.progress, out])
    return 0


if __name__ == '__main__':
    sys.exit(main())
