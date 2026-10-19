"""storage — the storage profile's readings, pure (core/law/profiles.yaml `storage`; core/law/lines.yaml the operations
`keepings` and `datasets`, `group`'s `gap`, the groupings `events`, `datasets` and `keepings`; MODEL.md, Storage).

    from core import storage
    storage.gap_groups(spans, seconds)          # [(start, end, member)] -> groups, a new one after a longer gap
    storage.judge(keepings, risks, covers, within, now)   # what a content's keepings leave open, and what would close it
    storage.Trees(folders, files).fingerprint(f)          # equal trees, found cheaply; their manifest's BLAKE3 asked once

Offline, the same answer every time. Nothing here reads a store or a bean: bin/reckon.py gives it a garden's
statements, and assets/storage/ a store's rows at its scale.
"""
import hashlib

from core import formats

# ------------------------------------------------------------------------------------------------ events
def gap_groups(spans, gap):
    """The members in the order of their start, a new group wherever the time from the end of the group so far to the
    next member's start is longer than `gap` (seconds). `spans` is (start, end, member), each a count of seconds; a day
    alone spans the whole of it. Returns [[member, ...], ...], each group in order."""
    out, end = [], None
    for s, e, m in sorted(spans, key=lambda x: (x[0], x[1], str(x[2]))):
        if end is None or s - end > gap:
            out.append([])
            end = e
        out[-1].append(m)
        end = max(end, e)
    return out


def placed_between(series, moment_of):
    """{member: (before, after)} for each member of a run of names that holds no moment, where its dated neighbours in
    the run — the nearest before it and the nearest after it, by counter — both hold one. `series` is [(counter,
    member)], one camera's run; `moment_of(member)` its span or None."""
    ordered = sorted(series)
    out = {}
    for i, (_n, m) in enumerate(ordered):
        if moment_of(m) is not None:
            continue
        before = next((x for _k, x in reversed(ordered[:i]) if moment_of(x) is not None), None)
        after = next((x for _k, x in ordered[i + 1:] if moment_of(x) is not None), None)
        if before is not None and after is not None:
            out[m] = (before, after)
    return out


# ------------------------------------------------------------------------------------------------ keepings
class Keeping:
    """One keeping of a content: the volume that holds it, the carriers it is on (the disks, a container's carriers'
    disks), their places, whether every carrier is offline, when its bytes were last found whole (seconds, or None),
    and whether its key is held twice or none is needed."""
    __slots__ = ('volume', 'disks', 'places', 'offline', 'verified', 'key', 'array', 'immutable')

    def __init__(self, volume, disks=(), places=(), offline=False, verified=None, key=True, array=False,
                 immutable=False):
        self.volume, self.disks, self.places = volume, frozenset(disks), frozenset(places)
        self.offline, self.verified, self.key = offline, verified, key
        self.array, self.immutable = array, immutable


def held(keepings, prop, within=None, now=None):
    """How many of the property `prop` a content's keepings hold: distinct disks, volumes or places; keepings offline,
    found whole within `within` seconds of `now`, with their key held, on an array, immutable."""
    if prop == 'disk':
        return len(frozenset().union(*[k.disks for k in keepings])) if keepings else 0
    if prop == 'volume':
        return len({k.volume for k in keepings})
    if prop == 'place':
        return len(frozenset().union(*[k.places for k in keepings])) if keepings else 0
    if prop == 'offline':
        return sum(1 for k in keepings if k.offline)
    if prop == 'verified':
        return sum(1 for k in keepings if k.verified is not None and within is not None and now is not None
                   and now - k.verified <= within)
    if prop == 'key':
        return sum(1 for k in keepings if k.key)
    if prop in ('array', 'immutable'):
        return sum(1 for k in keepings if getattr(k, prop))
    raise ValueError(f"{prop!r} is no keeping property")


def judge(keepings, risks, covers, within=None, now=None):
    """What a content's keepings leave open. `risks` is {risk: [way, ...]}, each way {property: least count}; `covers`
    the risks its policy names (None: judged against nothing, and every risk is read for what its keepings resolve).
    Returns {'resolved': [risk], 'open': [{'risk', 'way', 'lacks': {property: how many more}}]}: for an open risk, the
    way nearest to met — the fewest keepings it still lacks, then the first in its row."""
    resolved, open_ = [], []
    for risk in (covers if covers is not None else sorted(risks)):
        ways = risks.get(risk) or []
        best = None
        for i, way in enumerate(ways):
            lacks = {p: int(n) - held(keepings, p, within, now) for p, n in way.items()}
            lacks = {p: d for p, d in lacks.items() if d > 0}
            key = (sum(lacks.values()), i)
            if best is None or key < best[0]:
                best = (key, way, lacks)
        if best is not None and not best[2]:
            resolved.append(risk)
        elif covers is not None:
            open_.append({'risk': risk, 'way': best[1] if best else {}, 'lacks': best[2] if best else {}})
    return {'resolved': resolved, 'open': open_}


def lacking(entry):
    """An open risk's line: what it lacks, in words a reader reads without the table."""
    words = {'disk': 'on another disk', 'volume': 'on another volume', 'place': 'at another place',
             'offline': 'offline', 'verified': 'found whole within the policy', 'key': 'with its key held twice',
             'array': 'on an array', 'immutable': 'that nothing can write'}
    parts = [f"{n} more keeping{'s' if n > 1 else ''} {words.get(p, p)}" for p, n in entry['lacks'].items()]
    return f"{entry['risk']}: " + (', '.join(parts) or 'no way to resolve it is said')


# ------------------------------------------------------------------------------------------------ datasets
class Trees:
    """Every folder's tree, from its folders and files: `folders` {folder: parent or None}, `files` [(folder, name in
    bytes, BLAKE3 or None, size)]. A tree's FINGERPRINT (SHA-256 over its files' names and digests and its folders'
    fingerprints, an empty folder none) finds equal trees cheaply; equal trees have one manifest, whose BLAKE3 names
    the dataset (`manifest`). A tree holding a file whose content nobody read has neither."""

    def __init__(self, folders, files, names=None):
        self.parent = dict(folders)
        self.names = names or {}                # {folder: its name in bytes}
        self.files = {}
        for f, name, h, size in files:
            h = h or (formats.EMPTY_BLAKE3 if str(size) == '0' else None)
            self.files.setdefault(f, []).append((name, h))
        self.children = {}
        for f, p in self.parent.items():
            if p is not None:
                self.children.setdefault(p, []).append(f)
        self._fp = {}

    def fingerprint(self, folder):
        """The fingerprint of a folder's tree, or None (an empty tree, or a file in it whose content nobody read)."""
        stack, order = [folder], []
        while stack:                            # every folder beneath, children before their parents
            f = stack.pop()
            if f in self._fp:
                continue
            order.append(f)
            stack.extend(c for c in self.children.get(f, ()) if c not in self._fp)
        for f in reversed(order):
            unread, parts = False, []
            for name, h in self.files.get(f, ()):
                if h is None:
                    unread = True
                parts.append(b'f\0' + bytes(name) + b'\0' + str(h).encode())
            for c in self.children.get(f, ()):
                fp = self._fp.get(c)
                if fp == 'unread':
                    unread = True
                elif fp is not None:
                    parts.append(b'd\0' + bytes(self.names.get(c, c.encode() if isinstance(c, str) else c)) + b'\0'
                                 + fp.encode())
            self._fp[f] = 'unread' if unread else (hashlib.sha256(b'\n'.join(sorted(parts))).hexdigest()
                                                   if parts else None)
        fp = self._fp.get(folder)
        return None if fp == 'unread' else fp

    def walk(self, folder, prefix=b''):
        """(path beneath `folder`, BLAKE3) of every file in its tree."""
        for name, h in self.files.get(folder, ()):
            yield prefix + bytes(name), h
        for c in self.children.get(folder, ()):
            yield from self.walk(c, prefix + bytes(self.names.get(c, c.encode() if isinstance(c, str) else c)) + b'/')

    def manifest(self, folder):
        """The manifest of a folder's tree (core/law/formats.yaml `checksums`), or None where it has none."""
        if self.fingerprint(folder) is None:
            return None
        return formats.manifest((p, h, None) for p, h in self.walk(folder))
