#!/usr/bin/env python3
"""dmgeo — a position BY COORDINATES, on a named body, in a named reference system.

    python3 bin/dmgeo.py "EPSG:4326;35.6892,51.3890"                  # read it: body, kind, axes, its cells
    python3 bin/dmgeo.py "EPSG:4326;35.6892,51.3890" "EPSG:4326;41.0082,28.9784"    # and how far apart
    python3 bin/dmgeo.py "IAU_2015:49900;-4.5895,137.4417"            # the same machinery, on Mars
    python3 bin/dmgeo.py "EPSG:4326+5773;10.1,20.2,-3.5"              # a compound position: horizontal + vertical
    python3 bin/dmgeo.py "marker-a+3.2,-1.5"                           # a position from another being, resolved
    python3 bin/dmgeo.py --nearest "EPSG:4326;10.1,20.2"              # the fixed beings nearest a place

In a garden of the core (v1 part 7) the bodies and the reference systems are core/law/places.yaml's, and a being's
position is its `be` as location, its host and what it holds there (`placed`) read through bin/garden.py `terms`.

ISO 19111 and ISO 19112 divide spatial referencing in two, and the law follows them:

  BY COORDINATES (19111)   numbers in a COORDINATE REFERENCE SYSTEM: a datum fixed to a BODY, axes, units. This is
                           the root. Every other way of saying where something is RESOLVES THROUGH it.
  BY IDENTIFIER  (19112)   a name somebody maintains: a street address, a postal code, an administrative code, a map
                           database's element id, a grid cell's code. None of these IS a coordinate. "Third floor"
                           is a position in a frame that travels with its building.

A COORDINATE IS NEVER BARE. `35.69,51.39` names no datum, no axis order and no body; two readers can disagree by
hundreds of metres about where it is, and neither is wrong. The form is `<authority>:<code>;<coordinates>[@<epoch>]`.

A REFERENCE FRAME IS STATIC OR DYNAMIC. A plate-fixed frame (ETRS89) moves with its continent, so a coordinate in it
stays put. An earth-fixed frame (WGS 84, ITRF) does not, so a point on the ground DRIFTS in it by centimetres a
year, and a coordinate is only complete with the EPOCH it was measured at. The law's row says which (`frame`).

This tool reads a position, checks it against what its reference system declares, names the grid cells that contain
it, and measures a great-circle distance ON THE BODY THE SYSTEM NAMES. It does NOT transform between datums: that
needs the published transformation parameters (the PROJ project carries them), and an approximate transformation
presented as a position is the defect this whole design exists to refuse.

Pure: standard library only. It imports dmparse, which is too, for the one thing every tool shares: its output is
UTF-8 on every platform, so a position named in any script prints intact through a pipe on Windows.
"""
import functools, math, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse  # noqa: F401,E402 — its import sets UTF-8 on stdout and stderr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def runs_core(root=ROOT):
    """True in a garden that runs the core (GARDEN.md pins `core@…`, bin/check.py the one reader of the pin)."""
    try:
        import check
        return check.runs_core(check.pin(root))
    except Exception:
        return False


@functools.lru_cache(maxsize=None)
def _rows(root):
    """(bodies, reference_systems) as the law in `root` declares them. In a garden, the law is what the gate loaded —
    the standard and the garden's own additions; in the standard's own repository, the standard alone. No copy is held
    here: a tool that kept its own list of systems and radii was a second law, held equal to the first by a test."""
    if runs_core(root):                     # a garden of the core (v1 part 7): the places the release carries
        sys.path.insert(0, root)
        from core import standards
        t = standards.here(root).tables
        return list(t.get('bodies') or []), list(t.get('reference_systems') or [])
    if os.path.exists(os.path.join(root, 'VOCAB.md')):
        import dmcheck
        return list(dmcheck.registry('bodies') or []), list(dmcheck.registry('reference_systems') or [])
    with open(os.path.join(root, 'seed', 'std-vocab.md'), encoding='utf-8') as fh:
        fm = dmparse.loads(dmparse.split_front_matter(fh.read())[0])
    return list(fm.get('bodies') or []), list(fm.get('reference_systems') or [])


def bodies(root=ROOT):
    """{body: mean radius in metres}, the law's `bodies` rows."""
    return {b['body']: float(b['mean_radius_m']) for b in _rows(root)[0] if isinstance(b, dict) and b.get('body')}


def systems(root=ROOT):
    """{crs: {body, kind, axes, frame, ensemble_accuracy?, frame_epoch?}}, the law's `reference_systems` rows — the
    systems this tool can READ. Any `<authority>:<code>` is a legal position in the law; a system with no row is one
    this tool does not know the axes of, and it says so."""
    out = {}
    for r in _rows(root)[1]:
        if isinstance(r, dict) and r.get('crs'):
            out[r['crs']] = {k: (tuple(v) if k == 'axes' else v) for k, v in r.items() if k not in ('crs', 'meaning')}
    return out


# `<authority>:<code>[+<vertical code>];<one to three coordinates>[@<epoch>]` — the law's `geographic` pattern
FORM = re.compile(r'^([A-Z][A-Z0-9_]*:[0-9]+)(?:\+([0-9]+))?;(-?\d+(?:\.\d+)?(?:,-?\d+(?:\.\d+)?){0,2})(?:@(\d{4}(?:\.\d+)?))?$')
_B32 = '0123456789bcdefghjkmnpqrstuvwxyz'


def parse(position, root=ROOT):
    m = FORM.match(str(position).strip())
    if not m:
        raise ValueError(f"'{position}' is not `<authority>:<code>[+<vertical code>];<one to three coordinates>[@<epoch>]` — "
                         f"a coordinate is never bare")
    crs, vcode, coords, epoch = m.group(1), m.group(2), [float(x) for x in m.group(3).split(',')], m.group(4)
    known = systems(root)
    info = dict(known[crs]) if crs in known else None
    if vcode is not None:
        # A COMPOUND SYSTEM: a horizontal one and a vertical one of the same authority, their axes in that order
        vcrs = crs.split(':')[0] + ':' + vcode
        vinfo = known.get(vcrs)
        if info and vinfo:
            if vinfo.get('kind') != 'vertical' or not info.get('kind', '').startswith('geographic-2d') \
                    and info.get('kind') != 'projected':
                raise ValueError(f"{crs}+{vcode}: a compound position is a horizontal system and a vertical one — "
                                 f"{crs} is {info.get('kind')} and {vcrs} is {vinfo.get('kind')}")
            if info.get('body') != vinfo.get('body'):
                raise ValueError(f"{crs} is on {info.get('body')} and {vcrs} on {vinfo.get('body')}: one position is on one body")
            info = dict(info, kind='compound', axes=tuple(info['axes']) + tuple(vinfo['axes']), vertical=vcrs)
        else:
            info = None
        crs = f"{crs}+{vcode}"
    out = {'crs': crs, 'coordinates': coords, 'epoch': float(epoch) if epoch else None, 'known': info is not None}
    if info:
        out.update(info)
        if len(coords) != len(info['axes']):
            raise ValueError(f"{crs} has axes {info['axes']} and {len(coords)} coordinates were given")
        if info['kind'].startswith('geographic') or info['kind'] == 'compound' and info['axes'][:2] == ('lat', 'lon'):
            if not -90 <= coords[0] <= 90 or not -180 <= coords[1] <= 360:
                raise ValueError(f"{crs} is latitude then longitude: {coords[0]}, {coords[1]} is out of range")
    return out


def geohash(lat, lon, length=9):
    """The cell of the geohash grid that contains the point. A PREFIX of it is a coarser cell containing this one —
    a grid is LEVELS laid over coordinates, which is what the law means by them."""
    lat_r, lon_r, bits, ch, out, even = [-90.0, 90.0], [-180.0, 180.0], 0, 0, [], True
    while len(out) < length:
        r, v = (lon_r, lon) if even else (lat_r, lat)
        mid = (r[0] + r[1]) / 2
        if v >= mid:
            ch = ch * 2 + 1; r[0] = mid
        else:
            ch = ch * 2; r[1] = mid
        even = not even
        bits += 1
        if bits == 5:
            out.append(_B32[ch]); bits = ch = 0
    return ''.join(out)


def distance(a, b, root=ROOT):
    """Great-circle metres between two positions in the SAME geographic system, on the body that system names."""
    pa, pb = parse(a, root), parse(b, root)
    if pa['crs'] != pb['crs']:
        raise ValueError(f"{pa['crs']} and {pb['crs']} are different reference systems: this measures within one and "
                         f"does not transform between them")
    if not pa['known'] or not pa['kind'].startswith('geographic'):
        raise ValueError(f"{pa['crs']} is not a geographic system this tool knows the axes of")
    (la1, lo1), (la2, lo2) = [map(math.radians, p['coordinates'][:2]) for p in (pa, pb)]
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * bodies(root)[pa['body']] * math.asin(math.sqrt(h))


# ---- a position FROM ANOTHER BEING (24.0, step 7) and the beings nearest a place -------------------------------------
# `<bean>+<east>,<north>[,<up>]` in metres, the law's `relative` pattern
RELATIVE = re.compile(r'^([a-z0-9][a-z0-9-]*)\+(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)(?:,(-?\d+(?:\.\d+)?))?$')


def _beans(root):
    """{bean: front matter} — in a garden of the core, each bean as the terms its statements and `details` give
    (bin/garden.py `terms`): its locations, each with its host and its form (`placed`, v1 part 7)."""
    if runs_core(root):
        import dmgarden
        G = dmgarden.core_garden(root)
        return {bid: dmgarden.terms(b, G.beans) for bid, b in G.beans.items() if not b.unread}
    import dmpass
    return dmpass.beans_here(root)


def _current(entries, moment=None):
    """The being's entries that hold at `moment` — NOW where none is given: an entry with no `during` holds always; one
    whose window has closed holds only inside it. A transplant is two entries, and the being was at each in its own
    window. Place is read AT a time: that is the one mechanism, and a reader that dropped the time would say where a
    tree stands today about a survey taken before it was moved. Moments of one calendar compare as written."""
    out = []
    for e in entries if isinstance(entries, list) else []:
        if isinstance(e, dict) and e.get('at') is not None:
            d = e.get('during') if isinstance(e.get('during'), dict) else {}
            if moment is None:
                ok = d.get('to') is None
            else:
                ok = (d.get('from') is None or str(d['from']) <= str(moment)) and (d.get('to') is None or str(moment) < str(d['to']))
            if ok:
                out.append(e)
    return out


def position_of(bean, beans, root=ROOT, _path=(), moment=None):
    """(geographic position, mobility) where `bean` is now, resolving a `relative` one through the being it is stated
    from. None where it holds neither. A chain that returns to a being already on it is refused by name."""
    if bean in _path:
        raise ValueError(f"{' -> '.join(_path + (bean,))}: a relative position that returns to itself resolves nowhere")
    fm = beans.get(bean)
    if not isinstance(fm, dict):
        return None
    cur = _current(fm.get('located_at'), moment)
    for sysname in ('geographic', 'relative'):
        for e in cur:
            if e.get('system') == sysname:
                at = str(e['at']) if sysname == 'geographic' else resolve_relative(str(e['at']), beans=beans, root=root,
                                                                                   _path=_path + (bean,), moment=moment)
                return at, e.get('mobility')
    return None


def resolve_relative(position, *, root=ROOT, beans=None, _path=(), moment=None):
    """A `relative` position as the geographic one it resolves to, in the system the being it is stated from is
    placed in. The offset is laid on the plane that touches the body there (EPSG method 9837), on the body's MEAN
    SPHERE: the law gives a body its mean radius and no flattening, so for an offset of length L the result carries
    an error below L/100 — a centimetre over a metre, a metre over a hundred. The being must hold a position now."""
    m = RELATIVE.match(str(position).strip())
    if not m:
        raise ValueError(f"'{position}' is not `<bean>+<east>,<north>[,<up>]` in metres")
    bean, east, north, up = m.group(1), float(m.group(2)), float(m.group(3)), m.group(4)
    beans = _beans(root) if beans is None else beans
    if bean not in beans:
        raise ValueError(f"{position} is stated from {bean}, which is no bean of this garden")
    base = position_of(bean, beans, root, _path, moment)
    if base is None:
        raise ValueError(f"{position} is stated from {bean}, which holds no geographic position to resolve through")
    p = parse(base[0], root)
    if not p['known'] or not (p['kind'].startswith('geographic') or p['kind'] == 'compound'):
        raise ValueError(f"{position}: {bean} is at {base[0]}, not in a geographic system this tool knows the axes of")
    r = bodies(root)[p['body']]
    lat, lon = p['coordinates'][0], p['coordinates'][1]
    c = [lat + math.degrees(north / r), lon + math.degrees(east / (r * math.cos(math.radians(lat))))]
    if up is not None:
        if len(p['coordinates']) < 3:
            raise ValueError(f"{position} states UP, and {bean}'s position {base[0]} has no height to add it to")
        c.append(p['coordinates'][2] + float(up))
    elif len(p['coordinates']) > 2:
        c.append(p['coordinates'][2])
    return f"{p['crs']};{','.join(f'{x:.8f}'.rstrip('0').rstrip('.') for x in c)}" + (
        f"@{base[0].split('@', 1)[1]}" if '@' in base[0] else '')


def nearest(position, *, root=ROOT, k=5, fixed_only=True, beans=None, moment=None):
    """[(bean, metres)] — the `k` beings nearest a position, nearest first, each where it was at `moment` (now) (a relative position
    resolved). Linear in the beings. `fixed_only`: only those whose entry says `mobility: fixed` — a set mark, a
    rooted tree — since a being that moves is no mark to measure from. A being in another reference system than
    the position is not measured: nothing here transforms between them. The metres are great-circle, and ≈."""
    beans = _beans(root) if beans is None else beans
    at = resolve_relative(position, root=root, beans=beans, moment=moment) if RELATIVE.match(str(position)) else str(position)
    here = parse(at, root)
    out = []
    for b in sorted(beans):
        try:
            got = position_of(b, beans, root, moment=moment)
        except ValueError:
            continue
        if got is None or (fixed_only and got[1] != 'fixed') or got[0] == at:
            continue
        if parse(got[0], root)['crs'] != here['crs']:
            continue
        out.append((b, distance(at, got[0], root)))
    return sorted(out, key=lambda x: (x[1], x[0]))[:k]


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 0
    try:
        if argv[0] == '--nearest' and len(argv) > 1:
            for b, m in nearest(argv[1], root=ROOT):
                print(f"{b:28s} ≈ {m:.1f} m")
            return 0
        if RELATIVE.match(argv[0]):
            at = resolve_relative(argv[0], root=ROOT)
            print(f"{argv[0]}  resolves to  {at}  (≈: laid on the body's mean sphere)")
            argv = [at] + argv[1:]
        p = parse(argv[0])
        print(f"{p['crs']}  coordinates {p['coordinates']}" + (f"  epoch {p['epoch']}" if p['epoch'] else ""))
        if not p['known']:
            print("  a legal position; this tool does not know that system's axes, so it reads no further")
            return 0
        print(f"  body {p['body']} · {p['kind']} · axes {', '.join(p['axes'])} · {p['frame']} frame")
        _acc = p.get('ensemble_accuracy')
        if isinstance(_acc, dict):
            print(f"  accurate to {_acc.get('count')} {_acc.get('unit')}: {p['crs'].split('+')[0]} is an ensemble of "
                  f"realisations, and no motion finer than that is read from a position in it")
        if p['frame'] == 'dynamic' and p['epoch'] is None:
            print("  NOTE a dynamic frame and no epoch: the ground moves in this frame; say when this was measured")
        if p['kind'].startswith('geographic') and p['body'] == 'earth':
            g = geohash(p['coordinates'][0], p['coordinates'][1])
            print(f"  geohash cells, coarse to fine: {', '.join(g[:k] for k in (2, 4, 6, 9))}")
        if len(argv) > 1:
            print(f"  to {argv[1]}: {distance(argv[0], argv[1]) / 1000:.3f} km on {p['body']}")
        return 0
    except ValueError as e:
        print(f"dmgeo: {e}"); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
