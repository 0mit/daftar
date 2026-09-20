#!/usr/bin/env python3
"""dmgeo — a position BY COORDINATES, on a named body, in a named reference system.

    python3 bin/dmgeo.py "EPSG:4326;35.6892,51.3890"                  # read it: body, kind, axes, its cells
    python3 bin/dmgeo.py "EPSG:4326;35.6892,51.3890" "EPSG:4326;41.0082,28.9784"    # and how far apart
    python3 bin/dmgeo.py "IAU_2015:49900;-4.5895,137.4417"            # the same machinery, on Mars

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

Pure: standard library only.
"""
import math, re, sys

# mean radii in metres (IAU). A body is a row of the law's `bodies` registry; this is the copy a tool can compute
# with, held equal to it by test/calendars_and_coordinates.py.
BODIES = {'earth': 6371008.8, 'moon': 1737400.0, 'mars': 3389500.0}

# the reference systems this tool can READ. Any `<authority>:<code>` is a legal position in the law; a system not
# listed here is simply one this tool does not know the axes of, and it says so.
SYSTEMS = {
    'EPSG:4326':      {'body': 'earth', 'kind': 'geographic-2d', 'axes': ('lat', 'lon'),      'frame': 'dynamic'},
    'EPSG:4979':      {'body': 'earth', 'kind': 'geographic-3d', 'axes': ('lat', 'lon', 'h'), 'frame': 'dynamic'},
    'EPSG:4258':      {'body': 'earth', 'kind': 'geographic-2d', 'axes': ('lat', 'lon'),      'frame': 'static'},
    'EPSG:3857':      {'body': 'earth', 'kind': 'projected',     'axes': ('x', 'y'),          'frame': 'dynamic'},
    'IAU_2015:30100': {'body': 'moon',  'kind': 'geographic-2d', 'axes': ('lat', 'lon'),      'frame': 'static'},
    'IAU_2015:49900': {'body': 'mars',  'kind': 'geographic-2d', 'axes': ('lat', 'lon'),      'frame': 'static'},
}
FORM = re.compile(r'^([A-Z][A-Z0-9_]*:[0-9]+);(-?\d+(?:\.\d+)?(?:,-?\d+(?:\.\d+)?){1,2})(?:@(\d{4}(?:\.\d+)?))?$')
_B32 = '0123456789bcdefghjkmnpqrstuvwxyz'


def parse(position):
    m = FORM.match(str(position).strip())
    if not m:
        raise ValueError(f"'{position}' is not `<authority>:<code>;<coordinates>[@<epoch>]` — a coordinate is never bare")
    crs, coords, epoch = m.group(1), [float(x) for x in m.group(2).split(',')], m.group(3)
    info = SYSTEMS.get(crs)
    out = {'crs': crs, 'coordinates': coords, 'epoch': float(epoch) if epoch else None, 'known': info is not None}
    if info:
        out.update(info)
        if len(coords) != len(info['axes']):
            raise ValueError(f"{crs} has axes {info['axes']} and {len(coords)} coordinates were given")
        if info['kind'].startswith('geographic'):
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


def distance(a, b):
    """Great-circle metres between two positions in the SAME geographic system, on the body that system names."""
    pa, pb = parse(a), parse(b)
    if pa['crs'] != pb['crs']:
        raise ValueError(f"{pa['crs']} and {pb['crs']} are different reference systems: this measures within one and "
                         f"does not transform between them")
    if not pa['known'] or not pa['kind'].startswith('geographic'):
        raise ValueError(f"{pa['crs']} is not a geographic system this tool knows the axes of")
    (la1, lo1), (la2, lo2) = [map(math.radians, p['coordinates'][:2]) for p in (pa, pb)]
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * BODIES[pa['body']] * math.asin(math.sqrt(h))


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 0
    try:
        p = parse(argv[0])
        print(f"{p['crs']}  coordinates {p['coordinates']}" + (f"  epoch {p['epoch']}" if p['epoch'] else ""))
        if not p['known']:
            print("  a legal position; this tool does not know that system's axes, so it reads no further")
            return 0
        print(f"  body {p['body']} · {p['kind']} · axes {', '.join(p['axes'])} · {p['frame']} frame")
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
