#!/usr/bin/env python3
"""view_kit — the drawing kit of the `view` asset: the patterns a garden's drawings are made of, the recorder that
remembers what each drawing drew, the page's stylesheet, and the one runtime that mounts a drawing at a lens.

A GARDEN'S DRAWINGS ARE ITS OWN CODE. The page bean names them (`view.drawings`, a `file:` pointer), and they import
this kit: `from view_kit import node, store, gate, flow, ...`. Each drawing is a function that returns
(title, svg, caption, claim), listed in the module's `COMPOSERS = {key: function}` under the key its `views` entry has.

THE KIT RECORDS WHAT IT DRAWS. Every call records the element it drew — its pattern, its id (the slug of its label,
unique within the drawing), its box and the being it depicts (`bean=`) — so the page knows which patterns a drawing
uses and where a live value or a button sits, without the page storing either: element ids and patterns are read from
the drawing each time, never written down.

A DRAWING CARRIES NO ADDRESS. The understand lens draws parts by what they do; a being's addresses are its own facts,
shown on its card at the inspect lens to a viewer who may see them. `node()` still takes an address argument, so a
drawing written for it runs, and never draws it.

THE PATTERN LIBRARY IS THIS KIT'S: `PATTERNS` says what each pattern means, for the legend. It is code, not law — no
ledger value names a pattern — and the three kinds of live value a binding may be are the law's (`view_bindings.live`).

ONE RUNTIME. `view_runtime.js`, read here as RUNTIME_JS, mounts a drawing at a lens into any container — the offline
report and the served page run the same code. Its styles live under `.vw`, so a page it is dropped into keeps its own.
"""
import html, os, re


def esc(s):
    return html.escape(str(s), quote=True)


def slug(s):
    s = re.sub(r"<[^>]+>|&[a-z#0-9]+;", " ", str(s)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "el"


# ---------------------------------------------------------------------------------------------------------------------
# RECORDER — while a drawing runs, every kit call records the element it drew. An id is the label's slug, made unique
# within the drawing; an unlabelled flow is flow-<n>. Bindings and actions address elements by these ids.
# ---------------------------------------------------------------------------------------------------------------------
_REC = None
_NODE_MOD = {"ext": "external", "accent": "accent", "off": "disabled", "implied": "implied"}
_EDGE_PAT = {"": ["flow"], "sig": ["signal"], "accent": ["flow", "accent"], "off": ["flow", "disabled"]}   # accent/disabled MODIFY a flow
NATURE_OF = None        # set by the model: the nature of the being a node depicts, which colours its bar
ADDRESSES = False       # set by the model: True on a private page (`view.visibility: private`), whose parts show their address


def _rec(patterns, label="", box=None, bean=None, eid=None, of=None, ends=None):
    """Record one element; returns its id (or '' when not recording). `of` is the fact it stands for — a bean, or one
    entry of a bean's list, `{bean, field, key}` — and then the element's id is the fact's key, not its label's slug."""
    if _REC is None:
        return ""
    if of and not eid:
        eid = slug(of.get("key") or of.get("bean") or "") if isinstance(of, dict) else slug(of)
    base = eid or (slug(label) if label else "%s-%d" % (patterns[0], sum(1 for e in _REC if e["pattern"] == patterns[0]) + 1))
    eid, n = base, 2
    while any(e["id"] == eid for e in _REC):
        eid, n = "%s-%d" % (base, n), n + 1
    _REC.append({"id": eid, "pattern": patterns[0], "mods": patterns[1:], "label": re.sub(r"<[^>]+>", "", str(label)),
                 "box": [round(v, 1) for v in box] if box else None, "bean": bean, "of": of,
                 "ends": [[round(p[0], 1), round(p[1], 1)] for p in ends] if ends else None})
    return eid


def compose(fn):
    """Run one drawing with the recorder on. Returns (title, svg, caption, claim, elements)."""
    global _REC
    _REC = []
    try:
        title, svg, cap, claim = fn()
        return title, svg, cap, claim, _REC
    finally:
        _REC = None


def patterns_of(elements):
    return sorted({e["pattern"] for e in elements} | {m for e in elements for m in e["mods"]})


def _g(eid, pat, extra_cls="", bean=None):
    b = ' data-bean="%s"' % esc(bean) if bean else ""
    return '<g class="el %s %s" data-el="%s" data-pat="%s"%s>' % (pat, extra_cls, esc(eid), pat, b)


# ---------------------------------------------------------------------------------------------------------------------
# THE KIT. Coordinates are viewBox units. `bean` ties an element to the being it depicts: the runtime shows that being's
# facts on it, and a live-state binding may default to it.
# ---------------------------------------------------------------------------------------------------------------------
GLOSSARY = {}      # set by the model from the page's `view.glossary`: a word, and what it means on the page


def _terms_re():
    terms = sorted(GLOSSARY, key=len, reverse=True)
    return re.compile(r'(?<![\w-])(' + '|'.join(re.escape(t) for t in terms) + r')(?![\w-])') if terms else None


def gloss_html(s):
    """Wrap the FIRST occurrence of each glossary word with a tooltip, skipping HTML tags."""
    rx = _terms_re()
    if not rx:
        return s
    out, linked = [], set()
    for seg in re.split(r'(<[^>]+>)', s):
        if seg.startswith('<'):
            out.append(seg); continue
        res, pos = [], 0
        for m in rx.finditer(seg):
            t = m.group(1)
            if t in linked or m.start() < pos:
                continue
            res += [seg[pos:m.start()], '<span class="gloss" tabindex="0">' + t + '<span class="tip">' + esc(GLOSSARY[t]) + '</span></span>']
            pos = m.end(); linked.add(t)
        res.append(seg[pos:])
        out.append(''.join(res))
    return ''.join(out)


def _term_title(*texts):
    rx = _terms_re()
    for txt in texts:
        m = rx.search(txt) if (rx and txt) else None
        if m:
            return '<title>' + esc(m.group(1) + ' — ' + GLOSSARY[m.group(1)]) + '</title>'
    return ''


def node(x, y, w, h, title, sub="", ipv="", cls=None, bean=None, eid=None, of=None):
    """A part: a box with a bar coloured by what it is, its name and a one-line role. `cls` is `ext` (outside the
    garden's hands), `accent` (the point the drawing turns on) or `off` (wired, not running); otherwise the bar takes
    the nature of the being it depicts. `ipv` is the part's address: on a public page it is never drawn. On a private one
    (ADDRESSES) it is drawn beside the name, else beside the role line, else on a line of its own under it — the first
    that fits the box — marked with the being it belongs to, so that the host sends it only to a viewer who may see that
    being. One that fits nowhere is left out and recorded on the element, and `view check` names it: the card has it,
    and a wider box would draw it."""
    kind = cls or ((NATURE_OF(bean) if NATURE_OF and bean else None) or "lekton")
    eid = _rec(["node"] + ([_NODE_MOD[kind]] if kind in _NODE_MOD else []), title, (x, y, w, h), bean, eid, of)
    p = [_g(eid, "node", kind, bean), _term_title(title, sub),
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" class="nbox"/>',
         f'<rect x="{x}" y="{y}" width="5" height="{h}" rx="2.5" class="nbar"/>',
         f'<text x="{x+14}" y="{y+19}" class="ntitle">{esc(title)}</text>']
    if ADDRESSES and ipv:
        a, tag = str(ipv), f'class="nip" data-addr-of="{esc(bean or "")}"'
        aw = 12 + 6.6 * len(a)                      # mono 11px, ~6.6 a character, and the gap before it
        if 14 + 6.8 * len(title) + aw <= w - 4:      # beside the name (bold 13px, ~6.8 a character)
            p.append(f'<text x="{x+w-10}" y="{y+19}" text-anchor="end" {tag}>{esc(a)}</text>')
        elif not sub and h >= 40 and 14 + aw <= w:   # where the role line would be
            p.append(f'<text x="{x+14}" y="{y+35}" {tag}>{esc(a)}</text>')
        elif sub and 14 + 6.5 * len(sub) + aw <= w - 4:   # beside the role (12px, ~6.5 a character)
            p.append(f'<text x="{x+w-10}" y="{y+35}" text-anchor="end" {tag}>{esc(a)}</text>')
        elif h >= 52 and 14 + aw <= w:               # a line of its own, under the role
            p.append(f'<text x="{x+14}" y="{y+50}" {tag}>{esc(a)}</text>')
        elif _REC:
            _REC[-1]["unfit_address"] = a
    if sub:
        p.append(f'<text x="{x+14}" y="{y+35}" class="nsub" data-sub="1">{esc(sub)}</text>')
    p.append('</g>')
    return "".join(p)


def note(x, y, text, cls=""):
    """A free line of text inside a drawing (a second role line in a tall node)."""
    return f'<text x="{x}" y="{y}" class="nsub {cls}" data-sub="1">{esc(text)}</text>'


def store(x, y, w, h, title, sub="", bean=None, eid=None, of=None):
    """A store of data or of anything else, drawn as a cylinder."""
    eid = _rec(["store"], title, (x, y, w, h), bean, eid, of)
    ry = 7
    d = (f'M{x},{y+ry} A{w/2},{ry} 0 0 1 {x+w},{y+ry} L{x+w},{y+h-ry} A{w/2},{ry} 0 0 1 {x},{y+h-ry} Z')
    top = f'M{x},{y+ry} A{w/2},{ry} 0 0 0 {x+w},{y+ry}'
    p = [_g(eid, "store", "", bean), f'<path d="{d}" class="cyl"/>', f'<path d="{top}" class="cyltop"/>',
         f'<text x="{x+w/2}" y="{y+h/2+1}" text-anchor="middle" class="ntitle">{esc(title)}</text>']
    if sub:
        p.append(f'<text x="{x+w/2}" y="{y+h/2+16}" text-anchor="middle" class="nsub" data-sub="1">{esc(sub)}</text>')
    p.append('</g>')
    return "".join(p)


def gate(cx, cy, label, w=104, h=40, eid=None):
    """A decision or a condition, drawn as a diamond — the point the flow turns on."""
    eid = _rec(["gate"], label, (cx - w/2, cy - h/2, w, h), None, eid)
    pts = f"{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}"
    return (_g(eid, "gate") + f'<polygon points="{pts}" class="gbox"/>'
            f'<text x="{cx}" y="{cy+4}" text-anchor="middle" class="glabel">{esc(label)}</text></g>')


def flow(x1, y1, x2, y2, label="", cls="", lx=None, ly=None, eid=None, of=None):
    """A straight flow with an arrowhead and a label at the midpoint."""
    mx = lx if lx is not None else (x1 + x2) / 2
    my = ly if ly is not None else (y1 + y2) / 2
    pats = _EDGE_PAT[cls]; pat = pats[0]
    eid = _rec(pats, label, (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)), None, eid, of, ((x1, y1), (x2, y2)))
    t = f'<text x="{mx}" y="{my}" text-anchor="middle" class="flab {cls}">{esc(label)}</text>' if label else ""
    return (_g(eid, pat, "edgeg") + f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="edge {cls}" '
            f'marker-end="url(#ah-{cls or "d"})"/>{t}</g>')


def elbow(pts, label="", cls="", lx=None, ly=None, eid=None, of=None):
    """An orthogonal flow through a list of (x, y) points, the arrow at the end."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pats = _EDGE_PAT[cls]; pat = pats[0]
    eid = _rec(pats, label, (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)), None, eid, of, (pts[0], pts[-1]))
    d = " ".join(f"{x},{y}" for x, y in pts)
    t = f'<text x="{lx}" y="{ly}" text-anchor="middle" class="flab {cls}">{esc(label)}</text>' if (label and lx is not None) else ""
    return (_g(eid, pat, "edgeg") + f'<polyline points="{d}" class="edge {cls}" fill="none" '
            f'marker-end="url(#ah-{cls or "d"})"/>{t}</g>')


def tag(x, y, text, cls="tag", eid=None):
    """A short fact pinned beside what it qualifies; `tag-warn` or `tag-off` makes it a warning."""
    w = 8 + len(text) * 6.4
    pat = "tag" if cls == "tag" else "warning"
    eid = _rec([pat], text, (x, y, w, 18), None, eid)
    return (_g(eid, pat, cls) + f'<rect x="{x}" y="{y}" width="{w:.0f}" height="18" rx="9" class="tbox"/>'
            f'<text x="{x+w/2:.0f}" y="{y+13}" text-anchor="middle" class="ttext">{esc(text)}</text></g>')


def action_btn(x, y, w, label, tip, h=34, eid=None):
    """Where a person acts: a button the page's `views.actions` binds to a tool the host names."""
    eid = _rec(["action"], label, (x, y, w, h), None, eid)
    return (_g(eid, "action", "actbtn") + f'<title>{esc(tip)}</title>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" class="abox"/>'
            f'<text x="{x+16}" y="{y+h/2+4}" class="atext">▶  {esc(label)}</text>'
            f'<text x="{x+w-10}" y="{y+h/2+4}" text-anchor="end" class="ahint">action</text></g>')


def band(x, y, w, text, eid=None):
    """A heading that groups the parts under it."""
    eid = _rec(["band"], text, (x, y, w, 22), None, eid)
    return (_g(eid, "band") + f'<rect x="{x}" y="{y}" width="{w}" height="22" rx="4" class="bandbox"/>'
            f'<text x="{x+10}" y="{y+15}" class="bandtext">{esc(text)}</text></g>')


def gauge(x, y, w, frac, label, note_text, bean=None, eid=None):
    """A fill against its limit, with a note saying where the value comes from — an observation says so, because the
    live page must not pass it off as a measured value."""
    eid = _rec(["gauge"], label, (x, y, w, 12), bean, eid)
    return (_g(eid, "gauge", "", bean) + f'<rect x="{x}" y="{y}" width="{w}" height="12" rx="6" class="gauge-bg"/>'
            f'<rect x="{x}" y="{y}" width="{w*frac:.0f}" height="12" rx="6" class="gauge-fill"/>'
            f'<text x="{x+w}" y="{y+26}" text-anchor="end" class="nsub">{esc(note_text)}</text></g>')


def ribbon(x, y, w, text, eid=None):
    """A join key that runs through every stage — the thread to follow. `text` may carry entities."""
    eid = _rec(["ribbon"], "ribbon", (x, y, w, 28), None, eid)
    return (_g(eid, "ribbon") + f'<rect x="{x}" y="{y}" width="{w}" height="28" rx="14" class="ribbonbox"/>'
            f'<text x="{x+w/2}" y="{y+19}" text-anchor="middle" class="ribbon-t">{text}</text></g>')


def boundary(x, y, w, h, caption, eid=None):
    """A dashed region with a caption: a site, a provider, an organisation — where responsibility or a network changes.
    Drawn FIRST in a drawing, so the parts sit on top of it."""
    eid = _rec(["boundary"], caption, (x, y, w, h), None, eid)
    return (_g(eid, "boundary") + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" class="bnd"/>'
            f'<text x="{x+12}" y="{y+16}" class="bndtext">{esc(caption)}</text></g>')


def figure(vb_w, vb_h, body, aria):
    defs = ''.join('<marker id="ah-%s" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">'
                   '<path d="M0,0 L7,3 L0,6 Z" class="ah %s"/></marker>' % (k, c)
                   for k, c in (("d", ""), ("accent", "ah-accent"), ("sig", "ah-sig"), ("off", "ah-off")))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb_w} {vb_h}" role="img" aria-label="{esc(aria)}" '
            f'preserveAspectRatio="xMidYMid meet" class="schema"><defs>{defs}</defs>{body}</svg>')


# ---------------------------------------------------------------------------------------------------------------------
# THE PATTERN LIBRARY — what each drawing pattern means, for the legend. The kit's own: the functions above draw these
# patterns and nothing else, so the list and the code are kept in one file.
# ---------------------------------------------------------------------------------------------------------------------
PATTERNS = {
    "node": "a part — a machine, a service, a person or a process: a box with a bar for what it is, its name and a "
            "one-line role",
    "external": "a part outside the garden's hands: a dashed outline",
    "store": "a store, of data or of anything else: a cylinder",
    "gate": "a decision or a condition the flow turns on: a diamond",
    "flow": "what moves from one part to the next: a solid arrow",
    "signal": "a trigger, a poll or a control path rather than what moves itself: a dashed arrow",
    "accent": "THE point the drawing turns on — one per drawing, in the accent colour",
    "disabled": "wired but not running: greyed and dashed",
    "implied": "named by a flow and stated nowhere as a part: the facts' own gap, drawn so it is seen, never guessed into a part",
    "tag": "a short fact pinned beside the part it qualifies",
    "warning": "a pinned fact that is a gap, a risk or a manual step: an accent-outlined tag",
    "band": "a heading that groups the parts under it",
    "gauge": "a fill against its limit; says where the value comes from when it is an observation",
    "ribbon": "a join key that runs through every stage — the thread to follow",
    "action": "where a person acts: a button bound to a tool the host names, which the served page runs only when the "
              "host enables it",
    "boundary": "a dashed region: where responsibility or a network changes",
}
SWATCH = {"node": '<i class="sw soma"></i>', "external": '<i class="sw ext"></i>', "store": '<i class="sw store"></i>',
          "accent": '<i class="sw accent"></i>', "disabled": '<i class="sw off"></i>',
          "flow": '<svg width="30" height="10"><line x1="0" y1="5" x2="26" y2="5" style="stroke:var(--muted);stroke-width:1.6"/></svg>',
          "signal": '<svg width="30" height="10"><line x1="0" y1="5" x2="26" y2="5" style="stroke:var(--muted);stroke-width:1.6;stroke-dasharray:5 3"/></svg>',
          "live-state": '<i class="sw up"></i>', "live-value": '<i class="sw pat" style="background:var(--warn)"></i>'}


def legend_rows(patterns, live=None):
    """[[pattern, meaning, swatch-html]] for the patterns a drawing uses: the kit's meanings, and for a kind of live
    value the law's (`live`, read by the model from `view_bindings.live`)."""
    means = dict(PATTERNS, **(live or {}))
    return [[p, means.get(p, ""), SWATCH.get(p, '<i class="sw pat"></i>')] for p in patterns]


# ---------------------------------------------------------------------------------------------------------------------
# SCHEMA_CSS — every rule lives under `.vw`, so a drawing dropped into a host page styles itself and nothing else. Dark
# by default; `.vw.light` is the light palette.
# ---------------------------------------------------------------------------------------------------------------------
SCHEMA_CSS = """
.vw{--bg:#0f1319;--panel:#161c24;--line:#2a3644;--fg:#e8edf3;--muted:#93a1b2;--accent:#ff9d4a;
 --host:#4aa3ff;--svc:#7ee0a1;--ext:#c9a3ff;--store:#6fd6d6;--off:#5a6675;--nfill:#1c2530;--gauge:#ff9d4a;
 --up:#3fb950;--down:#f85149;--nd:#5a6675;--warn:#d29922;color:var(--fg);font:14px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.vw.light{--bg:#eef2f6;--panel:#fff;--line:#cfd8e2;--fg:#17202b;--muted:#5a6a7b;--nfill:#f5f8fb;--off:#9aa7b5}
.vw *{box-sizing:border-box}
.vw .vw-head h3{margin:0;font-size:19px;font-weight:650}.vw .vw-claim{margin:2px 0 0;font-size:14.5px}
.vw .vw-rel{margin:6px 0 0;color:var(--muted);font-size:12px}.vw .vw-rel b{color:var(--fg);font-weight:600}
.vw .vw-rel a{color:var(--accent)}
.vw .vw-fig{margin:12px 0 0;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px;overflow-x:auto}
.vw svg.schema{width:100%;height:auto;display:block;min-width:620px;color:var(--fg)}
.vw .vw-cap{margin:12px 0 0;font-size:13.5px;line-height:1.6;max-width:95ch}.vw .vw-cap b{font-weight:700}
.vw .k-accent{color:var(--accent)}.vw .k-off{color:var(--off)}
.vw .nbox{fill:var(--nfill);stroke:var(--line);stroke-width:1}
.vw .node.soma .nbar{fill:var(--host)}.vw .node.ext .nbar{fill:var(--ext)}
.vw .node.lekton .nbar{fill:var(--store)}.vw .node.accent .nbar{fill:var(--accent)}
.vw .node.accent .nbox{stroke:var(--accent);stroke-width:1.6}.vw .node.off .nbox{stroke-dasharray:4 3;opacity:.6}
.vw .node.off .nbar{fill:var(--off)}.vw .node.ext .nbox{stroke-dasharray:5 3}
.vw .node.implied .nbox{stroke-dasharray:1.5 3}.vw .node.implied .nbar{fill:none;stroke:var(--muted);stroke-dasharray:1.5 2}
.vw .ntitle{fill:var(--fg);font:700 13px system-ui}.vw .nip{fill:var(--muted);font:600 11px ui-monospace,monospace}
.vw .nsub{fill:var(--muted);font:12px system-ui}
.vw .cyl{fill:var(--nfill);stroke:var(--store);stroke-width:1.2}.vw .cyltop{fill:none;stroke:var(--store);stroke-width:1.2}
.vw .edge{stroke:var(--muted);stroke-width:1.6;fill:none}.vw .ah{fill:var(--muted)}
.vw .edge.sig{stroke-dasharray:5 3;opacity:.85}
.vw .edge.accent{stroke:var(--accent);stroke-width:2.2}.vw .ah-accent{fill:var(--accent)}
.vw .edge.off{stroke:var(--off);stroke-dasharray:4 3;opacity:.7}.vw .ah-off{fill:var(--off)}
.vw .flab{fill:var(--fg);font:11px system-ui;paint-order:stroke;stroke:var(--panel);stroke-width:4px;stroke-linejoin:round}
.vw .flab.accent{fill:var(--accent);font-weight:600}.vw .flab.sig{fill:var(--muted)}
.vw .gbox{fill:var(--nfill);stroke:var(--accent);stroke-width:1.6}.vw .glabel{fill:var(--fg);font:600 11px system-ui}
.vw .tbox{fill:var(--nfill);stroke:var(--line)}.vw .ttext{fill:var(--muted);font:11px system-ui}
.vw .tag-warn .tbox,.vw .tag-off .tbox{stroke:var(--accent)}.vw .tag-warn .ttext,.vw .tag-off .ttext{fill:var(--accent)}
.vw .bandbox{fill:none;stroke:var(--line);stroke-dasharray:3 3}.vw .bandtext{fill:var(--muted);font:600 11px system-ui;letter-spacing:.03em}
.vw .gauge-bg{fill:var(--nfill);stroke:var(--line)}.vw .gauge-fill{fill:var(--gauge)}
.vw .ribbonbox{fill:none;stroke:var(--accent);stroke-width:1.4;stroke-dasharray:2 3}
.vw .ribbon-t{fill:var(--accent);font:600 12px ui-monospace,monospace}
.vw .actbtn .abox{fill:var(--accent);stroke:var(--accent)}.vw .actbtn .atext{fill:#1a1206;font:700 13px system-ui}
.vw .actbtn .ahint{fill:#1a1206;opacity:.6;font:9px ui-monospace,monospace;text-transform:uppercase}.vw .actbtn{cursor:pointer}
/* the sheet: a title block of facts, in hairlines; pens by what they draw — a part's contour, a flow, a boundary's
   thin line (ISO 128's thick, medium and thin) — and a revision cloud around what the last commit changed */
.vw .vw-tblock{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));margin:12px 0 0;border:1px solid var(--line);
 border-radius:4px;font:11px/1.35 ui-monospace,SFMono-Regular,Menlo,monospace}
.vw .tb-c{padding:6px 9px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);min-width:0}
.vw .tb-c:nth-child(4n){border-right:0}.vw .tb-c:nth-last-child(-n+4){border-bottom:0}
.vw .tb-k{display:block;color:var(--muted);font-size:9.5px;letter-spacing:.06em;text-transform:uppercase}
.vw .tb-v{display:block;color:var(--fg);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@media(max-width:640px){.vw .vw-tblock{grid-template-columns:repeat(2,minmax(0,1fr))}.vw .tb-c:nth-child(4n){border-right:1px solid var(--line)}
 .vw .tb-c:nth-child(2n){border-right:0}.vw .tb-c:nth-last-child(-n+4){border-bottom:1px solid var(--line)}.vw .tb-c:nth-last-child(-n+2){border-bottom:0}}
.vw .nbox{stroke-width:1.2}.vw .edge{stroke-width:1.4}.vw .bnd{stroke-width:.7}
.vw .revcloud{fill:none;stroke:var(--accent);stroke-width:1.4;stroke-dasharray:1 5;stroke-linecap:round}
.vw .revmark{fill:var(--accent);font:700 12px system-ui}
.vw .vw-closed{fill:var(--muted);font:600 12px system-ui;letter-spacing:.02em}
.vw .vw-open-hint{font:400 11px system-ui;letter-spacing:0}
.vw .vw-detail-of{margin:0 0 8px;font-size:12.5px;color:var(--muted)}.vw .vw-detail-of a{color:var(--accent)}
/* zoom: a part that opens a drawing of its own carries a callout mark on its corner */
.vw .el.opens .nbox,.vw .el.opens .bnd{stroke-width:1.6}.vw .el.opens:hover .nbox{stroke:var(--accent)}
/* an element a lens hides */
.vw .vw-hide{display:none}
/* live: the element itself changes, in the drawing's own stroke and font */
.vw .el.live-up .nbox,.vw .el.live-up .cyl,.vw .el.live-up .gbox{stroke:var(--up);stroke-width:2.6}
.vw .el.live-down .nbox,.vw .el.live-down .cyl,.vw .el.live-down .gbox{stroke:var(--down);stroke-width:3}
.vw .el.live-down .ntitle{fill:var(--down)}
.vw .vw-chip rect{stroke:var(--panel);stroke-width:2}.vw .vw-chip text{font:700 10.5px system-ui;fill:#fff}
.vw .vw-chip.up rect{fill:var(--up)}.vw .vw-chip.down rect{fill:var(--down)}.vw .vw-chip.nd rect{fill:var(--nd)}
.vw .vw-chip.warn rect{fill:var(--warn)}.vw .vw-chip.val text{fill:#0b0f14}.vw .vw-chip.nd text{fill:#e8edf3}
.vw .el[data-bean]{cursor:help}
.vw .nip.nip-more{text-decoration:underline dotted;cursor:help}.vw .nip{pointer-events:all}
/* legend */
.vw .vw-legend{display:flex;gap:14px;flex-wrap:wrap;margin-top:12px;color:var(--muted);font-size:12px;align-items:center}
.vw .vw-legend span{display:flex;align-items:center;gap:5px}.vw .sw{width:12px;height:12px;border-radius:3px;display:inline-block}
.vw .sw.soma{background:var(--host)}.vw .sw.ext{background:var(--ext)}
.vw .sw.store{background:var(--store)}.vw .sw.accent{background:var(--accent)}.vw .sw.off{background:var(--off)}
.vw .sw.pat{border:1px solid var(--muted)}.vw .sw.up{background:var(--up)}.vw .sw.down{background:var(--down)}
.vw .vw-legend svg{vertical-align:middle}
/* inspect: facts and steps */
.vw .vw-detail{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;margin-top:14px}
.vw .vw-card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px;font-size:12.5px}
.vw .vw-card h4{margin:0 0 4px;font-size:13px}.vw .vw-card .mono{font-family:ui-monospace,monospace;color:var(--accent)}
.vw .vw-card dl{margin:4px 0 0;display:grid;grid-template-columns:auto 1fr;gap:2px 8px}
.vw .vw-card dt{color:var(--muted)}.vw .vw-card dd{margin:0;overflow-wrap:anywhere}
.vw .vw-steps{margin:14px 0 0;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 14px 10px 30px;font-size:12.5px}
.vw .vw-steps li{margin:3px 0}.vw .vw-sub{color:var(--muted);font-size:12px;margin:14px 0 0;font-weight:600;letter-spacing:.03em;text-transform:uppercase}
/* a hover card for a being */
.vw{position:relative}.vw .vw-tip{position:absolute;z-index:40;max-width:340px;background:var(--panel);border:1px solid var(--accent);
 border-radius:9px;padding:9px 11px;font-size:12px;line-height:1.5;box-shadow:0 8px 28px rgba(0,0,0,.35);pointer-events:none}
.vw .vw-tip b{display:block;margin-bottom:2px}
/* glossary */
.vw .gloss{border-bottom:1px dotted var(--accent);cursor:help;position:relative;outline:none}
.vw .gloss .tip{position:absolute;left:0;bottom:150%;z-index:30;width:300px;max-width:78vw;background:var(--panel);color:var(--fg);
 border:1px solid var(--accent);border-radius:9px;padding:9px 11px;font:12px/1.55 system-ui;box-shadow:0 8px 28px rgba(0,0,0,.35);
 opacity:0;visibility:hidden;transition:opacity .12s;text-align:left;font-weight:400}
.vw .gloss:hover .tip,.vw .gloss:focus .tip{opacity:1;visibility:visible}

/* ===== lenses: four forms, one inspector ===== */
.vw .vw-lv{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;margin-bottom:4px}
.vw .lvname{font:700 11px ui-monospace,monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--accent)}
.vw .lvq{color:var(--muted);font-size:12.5px;font-style:italic}
.vw .vw-empty{color:var(--muted)}
.vw svg.schema .el[data-ins]{cursor:pointer;outline:none}
.vw svg.schema .el[data-ins]:hover .nbox,.vw svg.schema .el[data-ins]:focus .nbox{stroke:var(--accent);stroke-width:2}
.vw .bnd{fill:none;stroke:var(--line);stroke-width:1.2;stroke-dasharray:6 4}.vw .bndtext{fill:var(--muted);font:600 10.5px system-ui;letter-spacing:.05em;text-transform:uppercase}
/* story */
.vw .vw-purpose{font-size:18px;line-height:1.45;margin:10px 0 18px;max-width:62ch;font-weight:500}
.vw .vw-story{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(var(--n,4),minmax(0,1fr));gap:26px 30px}
.vw .vw-stage{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px 16px 14px;outline:none;
 transition:border-color .15s,transform .15s}
.vw .vw-stage:hover,.vw .vw-stage:focus{border-color:var(--accent);transform:translateY(-2px)}
.vw .vw-stage:not(:last-child)::after{content:"";position:absolute;right:-24px;top:34px;width:16px;height:16px;border-top:3px solid var(--line);border-right:3px solid var(--line);transform:rotate(45deg);border-radius:2px}
.vw .vw-stage .num{position:absolute;top:-13px;left:14px;width:26px;height:26px;border-radius:50%;background:var(--accent);color:#1a1206;font:800 13px system-ui;display:grid;place-items:center}
.vw .vw-stage .lbl{font:650 15.5px/1.3 system-ui;margin-top:4px}
.vw .vw-stage .doer{color:var(--muted);font-size:13px;line-height:1.45;margin-top:6px}
.vw .vw-outcome{display:flex;gap:14px;align-items:flex-start;margin-top:22px;border:1px solid var(--up);border-radius:16px;padding:14px 16px;background:var(--panel)}
.vw .vw-outcome .num{flex:none;width:26px;height:26px;border-radius:50%;background:var(--up);color:#06120a;font:800 13px system-ui;display:grid;place-items:center}
.vw .vw-outcome .lbl{font:650 15px system-ui}.vw .vw-outcome .doer{color:var(--muted);font-size:13.5px;margin-top:2px}
.vw .techs{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.vw .vw-tech{display:inline-flex;align-items:center;gap:6px;padding:3px 10px 3px 3px;border:1px solid var(--line);border-radius:99px;color:var(--fg);text-decoration:none;font:600 12px system-ui;background:var(--nfill);outline:none}
.vw .vw-tech i{width:20px;height:20px;border-radius:50%;background:var(--accent);color:#1a1206;display:grid;place-items:center;font:800 11px system-ui;font-style:normal}
.vw .vw-tech:hover,.vw .vw-tech:focus{border-color:var(--accent)}.vw .vw-tech .ext{color:var(--muted);font-weight:400}
.vw .vw-learn{margin-top:22px;display:flex;flex-wrap:wrap;gap:8px;align-items:center;color:var(--muted);font-size:12.5px}
.vw .vw-learn>span:first-child{text-transform:uppercase;letter-spacing:.06em;font-size:11px;margin-right:4px}
.vw .vw-field{border:1px dashed var(--line);border-radius:8px;padding:2px 9px;cursor:help;outline:none}.vw .vw-field:hover{border-color:var(--accent);color:var(--fg)}
/* health chain */
.vw .vw-chain{display:flex;flex-wrap:wrap;align-items:stretch;gap:0;margin-top:14px}
.vw .vw-tile{position:relative;min-width:170px;max-width:240px;flex:1 1 170px;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px 14px 12px 20px;margin:6px 0;outline:none;cursor:pointer}
.vw .vw-tile .bar{position:absolute;left:0;top:0;bottom:0;width:6px;border-radius:14px 0 0 14px;background:var(--nd)}
.vw .vw-tile.up .bar{background:var(--up)}.vw .vw-tile.down .bar{background:var(--down)}.vw .vw-tile.warn .bar{background:var(--warn)}
.vw .vw-tile.down{border-color:var(--down)}.vw .vw-tile:hover,.vw .vw-tile:focus{border-color:var(--accent)}
.vw .vw-tile .tname{font:650 14px system-ui}.vw .vw-tile .tstate{font:700 11px ui-monospace,monospace;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin-top:2px}
.vw .vw-tile.up .tstate{color:var(--up)}.vw .vw-tile.down .tstate{color:var(--down)}.vw .vw-tile.warn .tstate{color:var(--warn)}
.vw .vw-tile .tsub{color:var(--muted);font-size:12px;margin-top:6px}
.vw .vw-tile.blind{background:repeating-linear-gradient(135deg,var(--panel) 0 8px,var(--nfill) 8px 16px);opacity:.85}
.vw .meas{margin-top:8px}.vw .meas .v{font:700 24px/1.1 system-ui;display:block}.vw .meas .mn{color:var(--muted);font-size:11.5px}
.vw .spark{display:block;width:100%;height:22px;margin-top:4px}.vw .spark polyline{fill:none;stroke:var(--accent);stroke-width:1.6;vector-effect:non-scaling-stroke}
.vw .vw-link{align-self:center;width:18px;height:2px;background:var(--line)}
.vw .vw-act{margin-top:10px;width:100%;background:var(--accent);color:#1a1206;border:0;border-radius:8px;padding:6px 8px;font:700 12.5px system-ui;cursor:pointer}
.vw .vw-alerts{margin-top:14px;display:flex;flex-wrap:wrap;gap:6px;align-items:center;color:var(--muted);font-size:12px}
.vw .vw-alerts>span:first-child{text-transform:uppercase;letter-spacing:.06em;font-size:11px}.vw .vw-alerts .al{border:1px solid var(--line);border-radius:6px;padding:1px 7px}
/* anatomy */
.vw .vw-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-top:12px}
.vw .vw-card2{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:12.5px}
.vw .vw-card2 header{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}.vw .vw-card2 header b{font:700 14px ui-monospace,monospace;cursor:help;outline:none}
.vw .vw-card2 .genos,.vw .vw-card2 .org{font:11px ui-monospace,monospace;color:var(--muted);border:1px solid var(--line);border-radius:6px;padding:0 6px}
.vw .vw-card2 .role{color:var(--muted);margin:4px 0 2px}
.vw .vw-card2 section{margin-top:8px;line-height:1.55}.vw .vw-card2 section>span{display:block;font:600 10.5px system-ui;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.vw .vw-card2 code{font:11.5px ui-monospace,monospace;color:var(--accent)}.vw .vw-card2 code.est{font-weight:700}.vw .vw-card2 i{color:var(--muted);font-style:normal}
.vw .vw-card2 section.open{color:var(--warn)}
.vw .vw-card2 .vw-tech{margin:2px 4px 2px 0}
.vw .vw-steps2{margin:10px 0 0;padding-left:22px;font-size:12.5px}.vw .vw-steps2 li{margin:6px 0}.vw .touch{margin-top:3px}
.vw .pchip{font:11px ui-monospace,monospace;border:1px solid var(--line);border-radius:6px;padding:0 6px;margin-right:4px;color:var(--muted)}
/* the inspector — one card, fixed, never clipped */
.vw-ins{position:fixed;z-index:1000;display:none;max-width:380px;min-width:220px;background:var(--panel,#161c24);color:var(--fg,#e8edf3);
 border:1px solid var(--accent,#ff9d4a);border-radius:12px;padding:10px 12px;font:12.5px/1.55 system-ui;box-shadow:0 12px 36px rgba(0,0,0,.4);pointer-events:auto}
.vw-ins.pinned{box-shadow:0 0 0 2px var(--accent,#ff9d4a),0 12px 36px rgba(0,0,0,.4)}.vw-ins b{font-size:13.5px}.vw-ins a{color:var(--accent,#ff9d4a)}
.vw-ins .ins-sub{color:var(--muted,#93a1b2);margin:1px 0 4px}.vw-ins .ins-row{margin-top:6px}.vw-ins .ins-row>span{display:block;font:600 10px system-ui;letter-spacing:.06em;text-transform:uppercase;color:var(--muted,#93a1b2)}
.vw-ins code{font:11.5px ui-monospace,monospace;color:var(--accent,#ff9d4a)}.vw-ins .ins-q{font:10.5px ui-monospace,monospace;color:var(--muted,#93a1b2);word-break:break-all;margin-top:2px}
.vw-ins .ins-foot{margin-top:8px;font-size:10.5px;color:var(--muted,#93a1b2);text-align:right}

/* ===== operate archetypes: each drawing's own question, in its native shape ===== */
.vw .bl{color:var(--muted);font-size:11.5px;letter-spacing:.04em;text-transform:uppercase;margin:12px 0 4px}
.vw .big{display:flex;flex-direction:column;gap:2px}.vw .big .bv{font:750 34px/1.05 system-ui;letter-spacing:-.01em}
.vw .big.down .bv{color:var(--down)}.vw .big.warn .bv{color:var(--warn)}
.vw .dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--nd);margin-right:6px;vertical-align:middle}
.vw .dot.up{background:var(--up)}.vw .dot.down{background:var(--down)}.vw .dot.warn{background:var(--warn)}
.vw .op-ev{display:flex;flex-wrap:wrap;gap:6px}.vw .ev{border:1px solid var(--line);border-radius:99px;padding:3px 10px;font-size:12.5px;background:var(--panel);cursor:help;outline:none}
.vw .ev b{margin-left:4px}.vw .ev.down{border-color:var(--down)}
.vw .op-acts{margin-top:16px;display:flex;gap:8px}.vw .op-acts .vw-act{width:auto;padding:8px 14px}
.vw .op-notes{margin:14px 0 0;padding-left:18px;color:var(--fg);font-size:13px}.vw .op-notes li{margin:3px 0}
.vw .op-blind{margin-top:14px;border:1px dashed var(--line);border-radius:12px;padding:8px 14px;background:repeating-linear-gradient(135deg,transparent 0 10px,var(--nfill) 10px 20px)}
.vw .op-blind>span{font:600 10.5px system-ui;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}.vw .op-blind ul{margin:4px 0 0;padding-left:18px;font-size:12.5px;color:var(--muted)}
/* reservoir */
.vw .op-res{display:flex;gap:28px;align-items:center;flex-wrap:wrap;margin-top:10px}
.vw .tank{width:250px;height:auto}.vw .tank-shell{fill:var(--nfill);stroke:var(--line);stroke-width:2}
.vw .tank-fill{fill:var(--up);opacity:.85}.vw .tank-fill.warn{fill:var(--warn)}.vw .tank-fill.down{fill:var(--down)}
.vw .gate-line{stroke:var(--fg);stroke-width:1.5;stroke-dasharray:6 4}.vw .gate-t{fill:var(--muted);font:600 11px system-ui}
.vw .tank-v{fill:var(--fg);font:800 30px system-ui;paint-order:stroke;stroke:var(--panel);stroke-width:5px}
.vw .op-side{flex:1;min-width:260px}.vw .op-side .spark{height:46px}
/* lanes */
.vw .op-lanes{display:flex;flex-direction:column;gap:12px;margin-top:10px}
.vw .lane{display:grid;grid-template-columns:190px 1fr 170px;align-items:center;gap:14px;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.vw .lane.down{border-color:var(--down)}.vw .ln-name{font:650 14px system-ui}
.vw .ln-hops{display:flex;align-items:center}.vw .hop{display:flex;flex-direction:column;align-items:center;gap:4px;outline:none;cursor:help}
.vw .hop i{width:22px;height:22px;border-radius:50%;background:var(--nd);border:3px solid var(--panel);box-shadow:0 0 0 2px var(--line)}
.vw .hop.up i{background:var(--up)}.vw .hop.down i{background:var(--down)}.vw .hop em{font:12px system-ui;font-style:normal;color:var(--muted);white-space:nowrap}
.vw .ln-link{flex:1;height:3px;min-width:30px;background:var(--line);margin:0 4px 18px}.vw .ln-link.up{background:var(--up)}.vw .ln-link.down{background:var(--down)}
.vw .ln-verdict{font:700 13px system-ui;text-align:right}.vw .lane.up .ln-verdict{color:var(--up)}.vw .lane.down .ln-verdict{color:var(--down)}
/* roster */
.vw .op-roster{margin-top:10px;max-width:760px}.vw .ro-head{display:flex;align-items:baseline;gap:10px}.vw .ro-head .bv{font:750 34px system-ui}
.vw .ro-row{display:grid;grid-template-columns:200px 1fr 110px;gap:12px;align-items:center;padding:5px 0;border-bottom:1px solid var(--line);font-size:13.5px}
.vw .fun{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px 16px 14px;margin:12px 0}
.vw .fun-h{display:flex;gap:12px;align-items:baseline;margin-bottom:8px}.vw .fun-h b{font:700 15px system-ui}.vw .fun-h span{color:var(--muted);font-size:12px}
.vw .fun-row{display:flex;align-items:flex-start;gap:6px;overflow-x:auto}.vw .fun-arrow{color:var(--muted);font-size:20px;padding-top:44px}
.vw .fun-st{flex:1 1 0;min-width:120px;display:flex;flex-direction:column;gap:3px;cursor:help;outline:none}
.vw .fun-bar{height:74px;display:flex;align-items:flex-end;background:linear-gradient(var(--nfill),var(--nfill)) bottom/100% 1px no-repeat}
.vw .fun-bar i{display:block;width:100%;background:var(--accent);border-radius:6px 6px 0 0;opacity:.85}
.vw .fun-n{font:800 22px system-ui}.vw .fun-l{font-size:12.5px;font-weight:600}.vw .fun-u{font-size:11px;color:var(--muted)}
.vw .fun-stop{font-size:12px;color:var(--muted);border-left:2px solid var(--line);padding-left:6px;cursor:help}.vw .fun-stop.hit{color:var(--down);border-left-color:var(--down);font-weight:600}
.vw .fun-mark{font-size:12px;color:var(--warn);font-weight:600;cursor:help}
.vw .rc{margin:8px 0}.vw .rc-row{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
.vw .rc-c{display:inline-flex;align-items:center;gap:5px;font:12px ui-monospace,monospace;border:1px solid var(--line);border-radius:99px;padding:2px 9px;background:var(--panel);cursor:help}
.vw .rc-c.down{border-color:var(--down);color:var(--down)}.vw .rc-c.idle{border-style:dashed;color:var(--muted)}
.vw .wr{display:flex;flex-direction:column;gap:14px;margin:8px 0 18px}.vw .wr-rail h4{margin:0 0 6px;font:700 11px ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
.vw .wr-t{width:100%;border-collapse:collapse;font-size:12.5px}.vw .wr-t td{padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top}
.vw .wr-t tr{cursor:help}.vw .wr-t tr:hover{background:var(--nfill)}.vw .wr-t tr.idle{opacity:.6}.vw .wr-t tr.idle .wr-ft b{text-decoration:line-through}
.vw .wr-ft{white-space:nowrap}.vw .wr-t code{font-size:11.5px}.vw .wr-c{color:var(--muted)}
.vw .wr-k{display:inline-block;font:700 10px ui-monospace,monospace;text-transform:uppercase;letter-spacing:.04em;border-radius:4px;padding:1px 5px;margin:0 4px;background:var(--nfill);color:var(--fg)}
.vw .wr-procs{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.vw .wr-p{border:1px solid var(--line);border-radius:8px;padding:3px 8px;font-size:12px;background:var(--panel);cursor:help}.vw .wr-p i{color:var(--muted);font-style:normal;font-size:11px}.vw .wr-p.idle{border-style:dashed;opacity:.7}

.vw .ro-row.idle{opacity:.55}.vw .ro-row.idle .ro-bar i{background:var(--muted)}
.vw .op-gates{display:flex;flex-direction:column;gap:6px;margin-bottom:10px}.vw .op-gates .gt{display:grid;grid-template-columns:48px 1fr auto;gap:10px;align-items:baseline;font-size:13px;border-left:3px dashed var(--line);padding-left:8px}
.vw .op-gates .gt b{font:700 14px system-ui}.vw .op-gates .gt em{font-style:normal;color:var(--muted);font-size:12px}.vw .op-gates .gt.past{border-left-color:var(--warn)}.vw .op-gates .gt.past em{color:var(--warn);font-weight:700}
.vw .ro-bar{height:8px;background:var(--nfill);border-radius:99px;overflow:hidden}.vw .ro-bar i{display:block;height:100%;background:var(--accent);border-radius:99px}
.vw .ro-v{text-align:right;font:600 12.5px ui-monospace,monospace;color:var(--muted)}
/* gauges */
.vw .op-gauges{display:flex;flex-wrap:wrap;gap:18px;margin-top:10px}.vw .gauge{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:10px 12px;width:180px;outline:none;cursor:help}
.vw .arc{width:100%;height:auto}.vw .arc path{fill:none;stroke-width:10;stroke-linecap:round}.vw .arc-ok{stroke:var(--up);opacity:.55}.vw .arc-warn{stroke:var(--warn);opacity:.7}.vw .arc-crit{stroke:var(--down);opacity:.7}
.vw .needle{stroke:var(--fg);stroke-width:3;stroke-linecap:round}.vw .hub{fill:var(--fg)}.vw .arc-v{fill:var(--fg);font:800 15px system-ui}.vw .arc-n{text-align:center;font:600 12.5px system-ui;color:var(--muted)}
/* race: the step, the verdict, the time bar against the deadline */
.vw .op-race{display:flex;flex-direction:column;gap:8px;margin-top:10px;max-width:980px}
.vw .rc-ph{font:750 34px/1.05 system-ui;letter-spacing:-.01em}.vw .rc-ph.idle{color:var(--muted)}
.vw .rc-ph.ph1{color:var(--host)}.vw .rc-ph.ph2{color:var(--accent)}.vw .rc-ph.ph3{color:var(--svc)}
.vw .rc-verdict{font:600 16px system-ui;display:flex;align-items:center;gap:8px}.vw .rc-verdict.down{color:var(--down)}.vw .rc-verdict.warn{color:var(--warn)}
.vw .rc-bar{position:relative;height:16px;background:var(--nfill);border:1px solid var(--line);border-radius:99px;margin-top:6px}
.vw .rc-bar i{position:absolute;top:0;bottom:0;display:block}
.vw .rc-el{left:0;border-radius:99px;background:var(--host)}.vw .rc-el.ph2{background:var(--accent)}.vw .rc-el.ph3{background:var(--svc)}
.vw .rc-eta{background:repeating-linear-gradient(90deg,var(--host) 0 3px,transparent 3px 7px);opacity:.55;border-radius:0 99px 99px 0}
.vw .rc-dl{width:0;top:-6px!important;bottom:-6px!important;border-left:3px solid var(--down)}
.vw .rc-gate{width:0;top:-4px!important;bottom:-4px!important;border-left:2px dashed var(--warn)}
.vw .rc-scale{display:flex;justify-content:space-between;font:12px ui-monospace,monospace;color:var(--muted)}
.vw .rc-gates{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:12.5px;color:var(--muted)}.vw .rc-gates b{color:var(--warn);font-weight:700}.vw .rc-gates .past{color:var(--fg)}
/* correlate: values on one time axis, a step band behind them, aggregated beneath */
.vw .op-corr{margin-top:18px;border-top:1px solid var(--line);padding-top:12px;max-width:1100px}
.vw .corr-h{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}.vw .corr-h b{font:700 15px system-ui}.vw .corr-h span{color:var(--muted);font-size:12px}
.vw .corr-wrap{overflow-x:auto}.vw .corr{width:100%;min-width:640px;height:auto;display:block;cursor:crosshair}
.vw .corr-band{opacity:.16}.vw .corr-ax{stroke:var(--line)}.vw .corr-line{fill:none;stroke:var(--fg);stroke-width:1.6}
.vw .corr-l{fill:var(--fg);font:600 12px system-ui}.vw .corr-max{fill:var(--muted);font:10.5px ui-monospace,monospace}
.vw .corr-now{fill:var(--fg);font:700 12.5px ui-monospace,monospace}.vw .corr-t{fill:var(--muted);font:11px ui-monospace,monospace}
.vw .corr-cur{stroke:var(--fg);stroke-width:1;stroke-dasharray:3 3}
.vw .corr-read{min-height:20px;font:12.5px ui-monospace,monospace;color:var(--muted)}.vw .corr-read b{color:var(--fg)}
.vw .corr-key{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:var(--muted);margin:4px 0}
.vw .corr-key i,.vw .corr-agg th i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;opacity:.6;vertical-align:-1px}
.vw .corr-sub{margin:14px 0 4px;font:600 11.5px system-ui;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.vw .corr-aggw{overflow-x:auto}.vw .corr-agg{border-collapse:collapse;font-size:13px;min-width:420px}
.vw .corr-agg th,.vw .corr-agg td{padding:6px 12px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
.vw .corr-agg th:first-child,.vw .corr-agg td:first-child{text-align:left;font-weight:600}
.vw .corr-agg th{font:600 12px system-ui}.vw .corr-agg th em{display:block;font:400 11px ui-monospace,monospace;color:var(--muted);font-style:normal}
.vw .corr-agg td{font:12.5px ui-monospace,monospace}
.vw .rel{width:100%;max-width:620px;height:auto;display:block}.vw .rel-bar{fill:var(--accent);opacity:.75}.vw .rel-v{fill:var(--fg);font:600 11px ui-monospace,monospace}
/* board + scoreboard */
.vw .op-facts{display:flex;flex-wrap:wrap;gap:34px;margin:10px 0 6px}
.vw .op-table{overflow-x:auto;margin:10px 0}.vw .op-table table{border-collapse:collapse;font-size:13px;min-width:100%}.vw .op-table th,.vw .op-table td{text-align:left;padding:4px 10px;border-bottom:1px solid rgba(128,128,128,.25);white-space:nowrap}.vw .op-table th{font-weight:600}
.vw .op-board{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-top:12px}
.vw .dev{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 12px;display:flex;flex-direction:column;gap:2px;outline:none;cursor:help}
.vw .dev.down{border-color:var(--down)}.vw .dev.blind{background:repeating-linear-gradient(135deg,var(--panel) 0 8px,var(--nfill) 8px 16px)}
.vw .dv-n{font:650 14px system-ui}.vw .dv-s{font:700 10.5px ui-monospace,monospace;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}.vw .dv-f{font-size:12px;color:var(--muted)}
.vw .dev.up .dv-s{color:var(--up)}.vw .dev.down .dv-s{color:var(--down)}
.vw .op-firing{margin-top:12px}.vw .fire{padding:6px 0;border-bottom:1px solid var(--line);font-weight:600}.vw .calm{font:600 15px system-ui;color:var(--up)}
@media (max-width:640px){.vw .lane{grid-template-columns:1fr}.vw .ln-verdict{text-align:left}.vw .ro-row{grid-template-columns:1fr 90px}.vw .ro-bar{grid-column:1/3}}
@media (max-width:900px){.vw .vw-story{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:640px){.vw .vw-story{grid-template-columns:1fr}.vw .vw-stage:not(:last-child)::after{display:none}.vw .vw-link{display:none}.vw .vw-tile{max-width:none}}
"""

# ONE RUNTIME, read once at import: view_runtime.js beside this file.
RUNTIME_JS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "view_runtime.js"), encoding="utf-8").read()
