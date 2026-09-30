#!/usr/bin/env python3
"""view_engrave — a drawing laid out from the facts it draws: the garden states, the engraver places.

A garden's drawing module may place every part by hand, and then the drawing is a second copy of the facts, which
drifts. Or it may hand the engraver the facts — the parts a being states and the pipes between them — and the engraver
lays them out, the way a music engraver lays out a score it did not compose. The drawing module keeps what only a
person can choose: which facts, which bands, which pipes carry the work and which only signal.

WHAT IT PLACES, AND HOW. A part stands in the band its fact names (a rail: inbound, outbound, reading, control) and in
the column of its step along the pipes: the longest walk to it from a part nothing feeds. Within a cell, parts are
ordered by where the parts feeding them stand. The same facts give the same drawing, byte for byte.

EVERY ELEMENT IS A FACT. A part's id is its fact's key and it records `of` — the bean, the field and the key — so a
binding sits on a fact and a renamed label breaks nothing.

TOTAL, AND SAID. A pipe that names an end no part states is not dropped and not guessed into a part: it is drawn as
IMPLIED (a part nothing feeds is outside the garden's hands, one that only receives files is a store), and every one is
listed in the report, so the gap in the facts is seen. A retired part or pipe is drawn disabled.

ZOOM IS A DIVISION. `group` divides the parts into wholes (a program the processes belong to); `engrave` at that level
draws the wholes and the pipes between them, each whole standing for the parts it holds.
"""
from view_kit import node, store, elbow, flow, band, figure, slug

W_NODE, H_NODE, COL_GAP, ROW_GAP, BAND_HEAD, BAND_GAP, X0, Y0 = 176, 46, 58, 16, 30, 18, 20, 12


def _parts_index(parts, key):
    """name -> part, and each alias token -> the parts it names (a part called `cleanup · qmgr` answers to `qmgr`)."""
    by, alias = {}, {}
    for p in parts:
        n = str(p[key])
        by[n] = p
        for tok in [t.strip() for t in n.replace(" (", " · (").split(" · ")] + [n.split(" (")[0].strip()]:
            if tok and tok != n:
                alias.setdefault(tok, []).append(n)
    return by, alias


def _resolve(end, by, alias):
    if end in by:
        return end
    names = alias.get(end) or []
    return names[0] if len(names) == 1 else None


def _layout(names, spine, calls, band_of, band_order):
    """Columns by the longest walk along the SPINE — the pipes that carry the work — from a part nothing feeds; cycles
    cut where the fact order first closes them. A part reached only by CALLS (a check, a lookup, a scan) is a satellite:
    it stands in the column of the first part that calls it, in the lane above the spine. Rows within a band and column
    follow where the feeding parts stand. Returns ({name: (band, col, lane, row)}, cut)."""
    succ = {n: [] for n in names}
    for a, b in spine:
        if a != b:
            succ[a].append(b)
    state, back = {}, set()

    def dfs(n):
        state[n] = 1
        for m in succ[n]:
            if state.get(m) == 1:
                back.add((n, m))
            elif m not in state:
                dfs(m)
        state[n] = 2
    for n in names:
        if n not in state:
            dfs(n)
    preds = {n: [a for a, b in spine if b == n and a != b and (a, b) not in back] for n in names}
    on_spine = {n for e in spine for n in e}
    col = {}

    def depth(n):
        if n not in col:
            col[n] = 0 if not preds[n] else 1 + max(depth(p) for p in preds[n])
        return col[n]
    for n in names:
        if n in on_spine:
            depth(n)
    callers = {}
    for a, b in calls:
        if b not in on_spine and a != b:
            callers.setdefault(b, []).append(a)
    lane = {n: "spine" for n in col}
    for _ in range(3):                                   # a satellite of a satellite follows its caller
        for n in names:
            if n in col:
                continue
            cs = [c for c in callers.get(n, []) if c in col]
            if cs:
                col[n] = col[cs[0]]
                lane[n] = "call"
    for n in names:                                      # a part joined to nothing, or only calling: in column 0
        if n not in col:
            targets = [b for a, b in calls if a == n and b in col]
            col[n] = col[targets[0]] if targets else 0
            lane[n] = "call" if targets else "spine"
    order = {n: i for i, n in enumerate(names)}
    pos = {}
    for c in range(max(col.values()) + 1 if col else 0):
        for b in band_order:
            for ln in ("call", "spine"):
                here = [n for n in names if col[n] == c and band_of[n] == b and lane[n] == ln]

                def bary(n):
                    ps = [pos[p] for p in preds.get(n, []) if p in pos]
                    return (sum(band_order.index(q[0]) * 100 + q[3] for q in ps) / len(ps) if ps else 1e9, order[n])
                for i, n in enumerate(sorted(here, key=bary)):
                    pos[n] = (b, c, ln, i)
    return pos, back


def engrave(parts, pipes, *, key, rail, of_bean, parts_field, pipes_field, sub=None, carries=None, group=None,
            regions=None, aria="", accent=None):
    """(svg, report) — the parts and pipes of one being, laid out. `key` and `rail` name the fields of a part that hold
    its name and its band; `sub` a field for its one-line role; `carries(pipe)` says whether a pipe carries the work
    (the spine: a solid flow) or is a call (a dashed one); `group(part)` draws the wholes the parts belong to instead of
    the parts; `regions(part)` draws those wholes as regions around their parts; `accent` the one part the drawing turns
    on."""
    by, alias = _parts_index(parts, key)
    report = {"implied": [], "cut": [], "parts": len(parts), "pipes": len(pipes)}
    nodes, band_of = {}, {}
    for p in parts:
        n = str(p[key])
        nodes[n] = {"part": p, "look": "off" if p.get("state") == "retired" else None}
        band_of[n] = str(p.get(rail) or "")
    edges = []
    for e in pipes:
        ends = []
        for end in (str(e.get("from")), str(e.get("to"))):
            r = _resolve(end, by, alias)
            if r is None:
                r = end
                if r not in nodes:
                    nodes[r] = {"part": None, "look": "implied"}
                    band_of[r] = str(e.get(rail) or "")
                    report["implied"].append(r)
            ends.append(r)
        edges.append((ends[0], ends[1], [e]))
    fed = {b for _a, b, _e in edges}
    for n, v in nodes.items():                     # an implied end nothing feeds is outside; one given only files, a store
        if v["look"] == "implied":
            ins = [e for _a, b, es in edges if b == n for e in es]
            v["look"] = "ext" if n not in fed else ("store" if ins and all(str(e.get("channel")) == "file" for e in ins)
                                                     else "implied")
    if group:
        def g_of(n):
            v = nodes[n]
            if v["part"]:
                return str(group(v["part"]))
            tok = n.split(" ")[0]                  # an implied listener (`smtpd :10025`) belongs with the part it names
            return str(group(by[tok])) if tok in by else n
        members = {}
        for n in nodes:
            members.setdefault(g_of(n), []).append(n)
        gnodes, gband = {}, {}
        for g, ns in members.items():
            live = [n for n in ns if nodes[n]["look"] != "off"]
            one = nodes[ns[0]]
            gnodes[g] = {"part": None if len(ns) > 1 or one["part"] is None else one["part"], "members": ns,
                         "look": one["look"] if len(ns) == 1 else (None if live else "off")}
            gband[g] = band_of[ns[0]]
        gedges, seen = [], {}
        for a, b, es in edges:
            ga, gb = g_of(a), g_of(b)
            if ga == gb:
                continue
            if (ga, gb) in seen:
                seen[(ga, gb)].extend(es)
            else:
                seen[(ga, gb)] = list(es)
                gedges.append((ga, gb, seen[(ga, gb)]))
        nodes, band_of, edges = gnodes, gband, gedges
    names = list(nodes)
    band_order = list(dict.fromkeys(band_of[n] for n in names))

    def is_off(a, b, es):
        return all(e.get("state") == "retired" for e in es) or nodes[a]["look"] == "off" or nodes[b]["look"] == "off"
    spine = [(a, b) for a, b, es in edges if not is_off(a, b, es) and (any(carries(e) for e in es) if carries else True)]
    calls = [(a, b) for a, b, es in edges if (a, b) not in spine]
    pos, back = _layout(names, spine, calls, band_of, band_order)
    report["cut"] = sorted("%s → %s" % c for c in back)
    ncols = max(c for _b, c, _l, _i in pos.values()) + 1 if pos else 1
    rows = {}
    for (b, c, ln, i) in pos.values():
        rows[(b, ln)] = max(rows.get((b, ln), 0), i + 1)
    band_y, lane_y, y = {}, {}, Y0
    for b in band_order:
        band_y[b] = y
        y += BAND_HEAD
        for ln in ("call", "spine"):
            lane_y[(b, ln)] = y
            y += rows.get((b, ln), 0) * (H_NODE + ROW_GAP)
        y += BAND_GAP
    col_w = [W_NODE] * ncols                    # a column is as wide as its longest name: a name is never cut
    for n, (_b, c, _l, _i) in pos.items():
        col_w[c] = max(col_w[c], int(24 + 6.8 * len(n) + 0.999))    # bold 13px, ~6.8 a character, and the bar's inset
    col_x = [X0 + sum(col_w[:c]) + c * COL_GAP for c in range(ncols)]
    width = X0 * 2 + sum(col_w) + (ncols - 1) * COL_GAP
    height = y
    box = {n: (col_x[c], lane_y[(b, ln)] + i * (H_NODE + ROW_GAP), col_w[c], H_NODE) for n, (b, c, ln, i) in pos.items()}
    body = [band(X0 - 8, band_y[b], width - 2 * X0 + 16, b, eid="rail-" + slug(b)) for b in band_order]
    if regions and not group:                      # each whole, a region around its parts in each band
        whole = {}
        for n, v in nodes.items():
            if v["part"]:
                whole.setdefault((str(regions(v["part"])), band_of[n]), []).append(n)
        from view_kit import boundary
        for (g, b), ns in whole.items():
            if len(ns) < 2:
                continue
            xs = [box[n][0] for n in ns]; ys = [box[n][1] for n in ns]
            x0, y0 = min(xs) - 8, min(ys) - 20
            x1 = max(box[n][0] + box[n][2] for n in ns)
            body.insert(len(band_order), boundary(x0, y0, x1 + 8 - x0, max(ys) + H_NODE + 8 - y0, g,
                                                  eid="region-%s-%s" % (slug(g), slug(b))))
    lanes = {}
    for a, b, es in edges:
        if a == b:
            continue
        xa, ya, wa, ha = box[a]
        xb, yb, wb, hb = box[b]
        off = is_off(a, b, es)
        on = (a, b) in spine
        cls = "off" if off else ("accent" if accent and accent in (a, b) and on else ("" if on else "sig"))
        label = " · ".join(dict.fromkeys(str(e.get("channel")) for e in es))
        of = {"bean": of_bean, "field": pipes_field, "key": "%s→%s" % (a, b)}
        if xb > xa:                                   # forward: out of the right side, into the left
            def clear(y, x0, x1):                     # no other part stands on this line between the two
                return not any(bx < x1 and bx + bw > x0 and by <= y <= by + bh
                               for m, (bx, by, bw, bh) in box.items() if m not in (a, b))
            if clear(yb + hb / 2, xa + wa, xb) or not clear(ya + ha / 2, xa + wa, xb):
                k = lanes.get((xa, "f"), 0); lanes[(xa, "f")] = k + 1
                mx = xa + wa + 12 + (k % 5) * 7       # turn at once, and run along the target's row
            else:                                     # a part stands on the target's row: run along the source's
                k = lanes.get((xb, "i"), 0); lanes[(xb, "i")] = k + 1
                mx = xb - 12 - (k % 5) * 7
            pts = [(xa + wa, ya + ha / 2), (mx, ya + ha / 2), (mx, yb + hb / 2), (xb, yb + hb / 2)]
        elif xb == xa:                                # the same column: a call straight up or down
            k = lanes.get((xa, "v"), 0); lanes[(xa, "v")] = k + 1
            cx = xa + wa / 2 + (k % 3) * 10 - 10
            pts = [(cx, ya), (cx, yb + hb)] if yb < ya else [(cx, ya + ha), (cx, yb)]
        else:                                         # back: out of the bottom, round beneath, into the bottom
            k = lanes.get((xb, "b"), 0); lanes[(xb, "b")] = k + 1
            my = max(ya + ha, yb + hb) + 8 + (k % 3) * 5
            pts = [(xa + wa / 2, ya + ha), (xa + wa / 2, my), (xb + wb / 2, my), (xb + wb / 2, yb + hb)]
        body.append(elbow(pts, label, cls, of=of))
    for n in names:
        v = nodes[n]
        x, y0, w, h = box[n]
        p = v["part"]
        if v.get("members") and len(v["members"]) > 1:
            role = "%d parts: %s" % (len(v["members"]), " · ".join(v["members"][:3]) + (" …" if len(v["members"]) > 3 else ""))
            of = {"bean": of_bean, "field": parts_field, "key": n, "holds": v["members"]}
        else:
            role = str(p.get(sub) or "") if (p and sub) else ("implied: no part states it" if v["look"] == "implied" else "")
            of = {"bean": of_bean, "field": parts_field, "key": n} if p else None
        role = role if len(role) <= 30 else role[:29].rstrip() + "…"
        kind = "accent" if accent == n else v["look"]
        if kind == "store":
            body.append(store(x, y0, w, h, n, "", eid=slug(n), of=of))
        else:
            body.append(node(x, y0, w, h, n, role, "", kind or "lekton", eid=slug(n), of=of))
    return figure(width, height, "".join(body), aria), report
