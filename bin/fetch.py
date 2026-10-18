#!/usr/bin/env python3
"""fetch — bring a standard's table from its provider to this machine: a scheme the law holds `fetched`
(core/law/registries.yaml, `knowledge_schemes`), downloaded from where its row's `fetch.from` says, into a cache outside
git, and read into the rows its `registry_files` file holds.

    python3 bin/fetch.py <scheme>                 # download it from its provider, and read it
    python3 bin/fetch.py <scheme> --from <file>   # a copy at hand: one this machine's person downloaded from the
                                                  # provider, or a peer's unchanged copy where the scheme's licence
                                                  # allows unchanged copies to be handed on
    python3 bin/fetch.py <scheme> <part> [--from <file>]   # a scheme its provider serves in parts (`fetch.part`: a
                                                  # country, a region): each part fetched alone, read as one table
    python3 bin/fetch.py --list                   # what this machine has fetched, each copy by its SHA-256

DAFTAR SHIPS NO ONE ELSE'S TABLE where the provider's terms do not let it: each machine reaches the provider itself,
under the provider's terms, and keeps the provider's file unchanged beside the rows read from it. The cache is this
machine's, never the garden's: `DAFTAR_STANDARDS_CACHE`, else `%LOCALAPPDATA%\\daftar\\standards` on Windows, else
`$XDG_CACHE_HOME/daftar/standards` (`~/.cache/daftar/standards`). Each copy is kept under the SHA-256 of the provider's
file: `<scheme>/<sha-256>/source.<ext>`, `rows.tsv` and `fetched.json` (from where, when, how many rows, and the part
and the provider's release where it has them). A garden reads a fetched scheme's codes from the newest copy here — of a
scheme in parts, the newest of each part, as one table (bin/knowledge.py) — and from the release's copy while it carries
one.

Nothing is sent but the request for the provider's file. Print the line it prints into the save's entry: what was
read, from where, and its SHA-256, so the garden says which copy its codes were read against.
"""
import csv
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import parse as dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr


def cache_dir():
    """Where this machine keeps what it fetched — outside every garden."""
    if os.environ.get('DAFTAR_STANDARDS_CACHE'):
        return os.environ['DAFTAR_STANDARDS_CACHE']
    if os.name == 'nt' and os.environ.get('LOCALAPPDATA'):
        return os.path.join(os.environ['LOCALAPPDATA'], 'daftar', 'standards')
    return os.path.join(os.environ.get('XDG_CACHE_HOME') or os.path.join(os.path.expanduser('~'), '.cache'),
                        'daftar', 'standards')


# ------------------------------------------------------------------------------------------------ the readers
# Each provider's reader is a row of the law's one table of readers (core/law/formats.yaml `readers`), its code in
# core/readers.py beside every other reader's (2.13): this tool fetches, the reader reads.
from core import readers as _readers  # noqa: E402
from core.formats import Refused  # noqa: E402,F811 — one refusal for every reader

READERS = _readers.FETCHED


# ------------------------------------------------------------------------------------------------ the law's rows
def _law(root=ROOT):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core import read
    d = os.path.join(root, 'core', 'law')
    d = d if os.path.isfile(os.path.join(d, 'registries.yaml')) else os.path.join(ROOT, 'core', 'law')
    return read.data(os.path.join(d, 'registries.yaml'))


def scheme_row(scheme, root=ROOT):
    law = _law(root)
    row = next((r for r in law.get('knowledge_schemes') or [] if isinstance(r, dict) and r.get('scheme') == scheme), None)
    if row is None:
        raise Refused(f"{scheme!r} is no scheme of the knowledge tree")
    if row.get('holding') != 'fetched' or not isinstance(row.get('fetch'), dict):
        raise Refused(f"{scheme} is held `{row.get('holding') or 'shipped'}`, not fetched: its codes are read where "
                      f"the law holds them")
    columns = None
    f = next((r.get('file') for r in law.get('registry_files') or [] if isinstance(r, dict) and r.get('registry') == scheme),
             None)
    if f and os.path.isfile(os.path.join(ROOT, f)):
        with open(os.path.join(ROOT, f), encoding='utf-8') as fh:
            columns = next(csv.reader(fh, delimiter='\t'), None)
    return row, columns


# ------------------------------------------------------------------------------------------------ the act
def part_of(row, part):
    """The part of a scheme its provider serves in parts, checked against the form its row gives one; None for a scheme
    in one piece. Refused where a part is wanted and none is named, or one is named that the scheme has not."""
    form = row['fetch'].get('part')
    if not form:
        if part:
            raise Refused(f"{row['scheme']} is served whole: it has no part {part!r}")
        return None
    if not part:
        raise Refused(f"{row['scheme']} is served in parts (a part is named as {form}): name the part — python3 "
                      f"bin/fetch.py {row['scheme']} <part>")
    if not re.fullmatch(str(form), part):
        raise Refused(f"{part!r} is no part of {row['scheme']}: a part is named as {form}")
    return part


def keep(scheme, data, source, *, part=None, root=ROOT, now=None):
    """Read the provider's file `data` (from `source`) by the scheme's reader, and keep it in this machine's cache.
    Returns (sha-256, rows, the directory kept in)."""
    row, columns = scheme_row(scheme, root)
    part = part_of(row, part)
    reader = READERS.get(str(row['fetch'].get('reader')))
    if reader is None:
        raise Refused(f"{scheme}'s reader `{row['fetch'].get('reader')}` is no reader of this release")
    rows, release = reader(data), None
    if isinstance(rows, dict):                     # a reader that says the provider's release beside its rows
        rows, release = rows['rows'], rows.get('release')
    if columns and set(columns) != set(rows[0]):
        raise Refused(f"the rows read have the columns {', '.join(rows[0])}, and {scheme}'s file has {', '.join(columns)}")
    sha = hashlib.sha256(data).hexdigest()
    d = os.path.join(cache_dir(), scheme, sha)
    tmp = d + '.part'
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    ext = os.path.splitext(str(row['fetch'].get('from')).split('?')[0])[1] or '.bin'
    with open(os.path.join(tmp, 'source' + ext), 'wb') as fh:
        fh.write(data)
    cols = columns or list(rows[0])
    with open(os.path.join(tmp, 'rows.tsv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    when = (now or datetime.datetime.now().astimezone()).isoformat(timespec='seconds')
    meta = {'scheme': scheme, 'from': source, 'at': when, 'sha256': sha, 'rows': len(rows)}
    meta.update({k: v for k, v in (('part', part), ('release', release)) if v})
    with open(os.path.join(tmp, 'fetched.json'), 'w', encoding='utf-8') as fh:
        json.dump(meta, fh, indent=1, ensure_ascii=False)
    shutil.rmtree(d, ignore_errors=True)
    os.replace(tmp, d)
    return sha, rows, d


def download(url):
    import urllib.request
    req = urllib.request.Request(url, headers={'User-Agent': 'daftar-fetch (a standard\'s table, for its reader)'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except OSError as e:
        raise Refused(f"the provider did not answer ({url}): {e}") from None


def _copies(scheme):
    """[(when, sha-256, rows.tsv, part)] of every whole copy of `scheme` this machine keeps."""
    d = os.path.join(cache_dir(), scheme)
    out = []
    for sha in os.listdir(d) if os.path.isdir(d) else []:
        meta = os.path.join(d, sha, 'fetched.json')
        rows = os.path.join(d, sha, 'rows.tsv')
        if not sha.endswith('.part') and os.path.isfile(meta) and os.path.isfile(rows):
            try:
                with open(meta, encoding='utf-8') as fh:
                    m = json.load(fh)
            except (OSError, ValueError):
                continue
            out.append((str(m.get('at') or ''), sha, rows, str(m.get('part') or '')))
    return out


def fetched(scheme):
    """The copies of `scheme` this machine keeps, newest first: [(when, sha-256, rows.tsv)]."""
    return sorted(((w, s, r) for w, s, r, _p in _copies(scheme)), reverse=True)


def current(scheme):
    """The rows.tsv files a garden reads `scheme` from: its newest copy — or, of a scheme in parts, the newest copy of
    each part this machine fetched, the parts in their names' order, read as one table."""
    newest = {}
    for when, sha, rows, part in sorted(_copies(scheme)):
        newest[part] = rows                        # oldest first: the newest of each part stays
    return [newest[p] for p in sorted(newest)]


def crossed(scheme, rows):
    """[line]: what the provider's rows, read, say of the scheme's crossing into the law's units and kinds (`units` on its
    row): how many of its codes cross (through every axis, where it names axes), each value on an axis no row names,
    and each crossed code it has not, or marks deprecated or deleted — a revision that moved what the law's crossing
    names. Nothing for a scheme with no crossing."""
    import units as dmunits
    try:
        n, missing, marked, unknown = dmunits.against(scheme, rows)
    except ValueError:
        return []
    out = [f"fetch: {n} of its {len(rows)} codes cross into the law's units and kinds (python3 bin/units.py --codes "
           f"{scheme})"]
    for axis, values in unknown.items():
        out.append(f"fetch: on its axis {axis}, values no row of the law's crossing names: {', '.join(values)}")
    if missing:
        out.append(f"fetch: crossed by the law, and not in this copy: {', '.join(missing)}")
    if marked:
        out.append(f"fetch: crossed by the law, and marked by the provider: "
                   f"{', '.join(f'{c} ({s})' for c, s in marked)}")
    return out


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0 if argv else 2
    if argv == ['--list']:
        base = cache_dir()
        for scheme in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            for when, sha, _rows, part in sorted(_copies(scheme), reverse=True):
                print(f"{scheme}{' ' + part if part else ''}\t{when}\tsha-256:{sha}")
        print(f"fetch: this machine's cache is {base}")
        return 0
    scheme, rest = argv[0], argv[1:]
    part = rest.pop(0) if rest[:1] and not rest[0].startswith('--') else None
    try:
        row, _cols = scheme_row(scheme)
        part = part_of(row, part)
        if rest[:1] == ['--from'] and len(rest) == 2:
            with open(rest[1], 'rb') as fh:
                data, source = fh.read(), os.path.abspath(rest[1])
        elif not rest:
            source = str(row['fetch'].get('from')).replace('{part}', part or '')
            try:
                data = download(source)
            except Refused as e:
                raise Refused(f"{e} — download it from there by hand, as its provider serves a person, and read that "
                              f"copy: python3 bin/fetch.py {scheme}{' ' + part if part else ''} --from <file>") from None
        else:
            print(__doc__)
            return 2
        try:
            sha, rows, d = keep(scheme, data, source, part=part)
        except Refused as e:
            if rest:
                raise
            raise Refused(f"{e} — what {source} answered is not the table its reader reads: a provider that serves its "
                          f"table to a person signed in is downloaded there by hand, and read with: python3 bin/fetch.py "
                          f"{scheme}{' ' + part if part else ''} --from <file>") from None
    except (Refused, OSError) as e:
        print(f"fetch: NOT FETCHED: {e}", file=sys.stderr)
        return 1
    with open(os.path.join(d, 'fetched.json'), encoding='utf-8') as fh:
        release = json.load(fh).get('release')
    named = f"{scheme}{' ' + part if part else ''}"
    print(f"fetch: {named}, {len(rows)} rows, kept in {d}")
    for line in crossed(scheme, rows):
        print(line)
    print(f"for the save's entry:\n  - read: {named} from {source}{', ' + release if release else ''}, sha-256 {sha}, "
          f"{len(rows)} rows")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
