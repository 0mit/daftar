#!/usr/bin/env python3
"""view_model — what the `view` asset knows, read from its garden: the page, the beings it draws, the lenses, shapes
and units the law declares, and the checks that keep the page and its drawings honest.

WHERE IT READS. The page is the one bean that carries `view` (the profile's head term); its `views`, `view_bindings`
and `view_monitors` sit on the same bean. A being is read as it states itself: its `genos`, its owner, its
`located_at`, its `endpoints`, its `knowledge`. The law is read through the garden's own tools — `bin/dmparse.py`
for a document, `bin/dmcheck.py` for the units and terms in force, `bin/dmknowledge.py` for the technologies — so the
asset carries no copy of the language and cannot disagree with it.

WHAT IT DERIVES, AND NEVER STORES. The patterns a drawing uses and its element ids are read from the drawing each
time; the organisation a being belongs to is read from its record; an address is chosen by the page and stated by
the being. Nothing derived is written back.

THE ORGANISATION, CLOSED BY DEFAULT. A being's organisation is the bean of genos `org` that owns it in law, or, for a
being owned `via` another, that other's; a bean of genos `org` is its own. Where none can be derived — an owner who is
a person, a being owned outside the garden, at the crown or through an agreement — the being has no organisation, and
a viewer scoped to organisations sees it only through a grant the host's configuration states (view_serve.Host.may).

Usage (through assets/view/bin/dmview.py):
  dmview check                   the page against the law and the drawings; writes nothing
  dmview elements <view>         a drawing's elements: id, pattern, being
  dmview import <file.json>      an author-mode selection written into the page, through dmsafe, and journalled
"""
import importlib.util, ipaddress, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import view_kit as kit

PROFILE = "view"        # the profile whose asset this is: its head term, and the directory the asset sits in
TERMS = ("view", "view_monitors", "views", "view_bindings")
ROOT = ""               # the garden this run serves: bound by init()
PAGE = None             # the page this run draws: the bean carrying `view`, chosen by init()
dmparse = None          # the garden's own parser: bound by init()
STEP_NONE = "not running"


class NoPage(Exception):
    """The garden has no page this asset can draw, or the page cannot be read: said, and nothing is written."""


# ---------------------------------------------------------------------------------------------------------------------
# the garden
# ---------------------------------------------------------------------------------------------------------------------
_FM = {}


def init(root, page=None):
    """Bind this run to a garden, and to its page. Returns the problems that stop it — none means it can draw."""
    global ROOT, dmparse, PAGE, _LAW, _K, _GARDEN
    ROOT = os.path.abspath(root)
    _FM.clear(); _LAW = None; _K = None; _GARDEN = None; PAGE = None
    b = os.path.join(ROOT, "bin")
    if b not in sys.path:
        sys.path.insert(0, b)
    try:
        import dmparse as _p
    except ImportError:
        return ["%s is not a daftar garden: it has no bin/dmparse.py" % ROOT]
    dmparse = _p
    vocab = fm_path(os.path.join(ROOT, "VOCAB.md"))
    if PROFILE not in (vocab.get("extends_profiles") or []):
        rel = fm_path(os.path.join(ROOT, "GARDEN.md")).get("daftar_release") or "<the release>"
        return ["this garden does not extend the `%s` profile, which this asset draws: extending it is a RULE-CHANGE, "
                "the gardener's to ratify — python3 bin/dmupgrade.py %s --extend %s" % (PROFILE, rel, PROFILE)]
    pages = [p for p in bean_ids() if PROFILE in fm(p)]
    if page:
        if page not in pages:
            return ["%s carries no `%s`: the pages here are %s" % (page, PROFILE, ", ".join(pages) or "none")]
        PAGE = page
    elif len(pages) == 1:
        PAGE = pages[0]
    elif not pages:
        return ["no bean of this garden carries `%s`: a page is the bean that does" % PROFILE]
    else:
        return ["%d beans carry `%s` (%s): name the one to draw with --page" % (len(pages), PROFILE, ", ".join(pages))]
    return []


def fm_path(path):
    if not os.path.isfile(path):
        return {}
    d = dmparse.loads(dmparse.read(path)[0] or "") or {}
    return d if isinstance(d, dict) else {}


def fm(bid, folder="beans"):
    """A bean's (or a mapping's) front matter; {} when it does not exist. Read once a run."""
    k = (folder, bid)
    if k not in _FM:
        _FM[k] = fm_path(os.path.join(ROOT, folder, "%s.md" % bid)) if isinstance(bid, str) and bid else {}
    return _FM[k]


def bean_ids(folder="beans"):
    d = os.path.join(ROOT, folder)
    return sorted(n[:-3] for n in os.listdir(d) if n.endswith(".md")) if os.path.isdir(d) else []


def page():
    if not PAGE:
        raise NoPage("no page is bound (init() first)")
    return fm(PAGE)


def page_view():
    v = page().get("view")
    return v if isinstance(v, dict) else {}


def entries(term):
    """A term of the page as its entries: an open map as (key, entry) in order, a list as (index, entry)."""
    n = page().get(term)
    if isinstance(n, dict):
        return [(k, e) for k, e in n.items() if isinstance(e, dict)]
    if isinstance(n, list):
        return [(i, e) for i, e in enumerate(n) if isinstance(e, dict)]
    return []


def garden_name():
    return str(fm_path(os.path.join(ROOT, "GARDEN.md")).get("garden") or os.path.basename(ROOT))


# ---------------------------------------------------------------------------------------------------------------------
# the law, as the garden's gate holds it
# ---------------------------------------------------------------------------------------------------------------------
_LAW = None


def law():
    """The garden's gate, imported: the units, terms and registries in force, a garden's additions among them."""
    global _LAW
    if _LAW is None:
        import dmcheck
        _LAW = dmcheck
    return _LAW


def registry(name):
    return [r for r in (law().registry(name) or []) if isinstance(r, dict)]


def lenses():
    """The lenses, in depth order: the law's `view_lenses` rows, as the runtime reads them."""
    return [{"id": r.get("lens"), "depth": r.get("depth"), "form": r.get("form"), "name": r.get("lens"),
             "question": r.get("meaning", ""), "max": r.get("max") or {}}
            for r in sorted(registry("view_lenses"), key=lambda r: (int(r.get("depth", 9)), str(r.get("lens"))))]


def lens_of_form(form):
    return next((l for l in lenses() if l["form"] == form), {})


def archetypes():
    return {r.get("archetype"): r for r in registry("view_archetypes")}


def proposed_archetype(v):
    """The operate shape the facts propose (`view_archetypes`: `frame` and `reads`): the first whose frame the drawing
    is laid out along, else the first whose terms the drawn being holds; the health chain where none does. The page may
    draw another; `dmview check` says when it does."""
    kk, target, folder = draws_of(v)
    f = fm(target, folder) if kk else {}
    rows = [r for r in registry("view_archetypes") if isinstance(r, dict)]
    for r in rows:
        if v.get("frame") and v.get("frame") in (r.get("frame") or []):
            return r.get("archetype")
    for r in rows:
        if any(f.get(x) for x in (r.get("reads") or [])):
            return r.get("archetype")
    return "health-chain"


def unit(u):
    """(quantity, [numerator, denominator]) of a unit the law, or the garden's additions, declare; (None, None) else."""
    row = law().UNITS.get(u) if u else None
    if not isinstance(row, dict):
        return None, None
    f = row.get("factor")
    return row.get("quantity"), ([int(f[0]), int(f[1])] if isinstance(f, list) and len(f) == 2 else None)


def seconds(extent):
    """A length on `time` — an extent's `measure`, or a recurrence's `every` — in seconds; None where it is none."""
    if not isinstance(extent, dict):
        return None
    m = extent.get("measure") or extent.get("every")
    if not isinstance(m, dict):
        return None
    q, f = unit(m.get("unit"))
    if q != "duration" or not f:
        return None
    try:
        return float(m.get("count")) * f[0] / f[1]
    except (TypeError, ValueError):
        return None


def share(quantity):
    """A quantity of `ratio` as a percent of the whole; None where it is none."""
    if not isinstance(quantity, dict):
        return None
    q, f = unit(quantity.get("unit"))
    if q != "ratio" or not f:
        return None
    try:
        return float(quantity.get("count")) * f[0] / f[1] * 100
    except (TypeError, ValueError):
        return None


def count(v):
    """A count as the law writes one (a whole number, or a decimal as a string) as a number the runtime compares."""
    try:
        return float(v) if v is not None and str(v).strip() != "" else None
    except (TypeError, ValueError):
        return None


def live_meanings():
    """What each kind of live value is, as the law's `view_bindings.live` says it: `kind — meaning | …`."""
    t = law().TERMS.get("view_bindings") or {}
    m = str((((t.get("schema") or {}).get("attrs") or {}).get("live") or {}).get("meaning") or "")
    return {k.strip(): v.strip() for k, _, v in (p.partition(" — ") for p in m.split(" | ")) if v}


# ---------------------------------------------------------------------------------------------------------------------
# what a being states: its organisation, its addresses, its technologies
# ---------------------------------------------------------------------------------------------------------------------
def org_of(b, _seen=None):
    """The organisation a being belongs to, or None where none can be derived (see the module's docstring)."""
    seen = set() if _seen is None else _seen
    if not isinstance(b, str) or not b or b in seen:
        return None
    seen.add(b)
    f = fm(b)
    if not f:
        return None
    if f.get("genos") == "org":
        return b
    ob = f.get("owned_by") if isinstance(f.get("owned_by"), dict) else {}
    if isinstance(ob.get("via"), dict):
        return org_of(ob["via"].get("bean"), seen)
    owner = ((ob.get("legal") or {}) if isinstance(ob.get("legal"), dict) else {}).get("owner")
    ob_bean = owner.get("bean") if isinstance(owner, dict) else None
    return ob_bean if isinstance(ob_bean, str) and fm(ob_bean).get("genos") == "org" else None


def _ip_system(value):
    try:
        return "ipv%d" % ipaddress.ip_address(str(value).split("/")[0]).version
    except ValueError:
        return None


def _near(value):
    """True for an address that says nothing about where to reach a being: loopback, link-local."""
    try:
        a = ipaddress.ip_address(str(value).split("/")[0])
    except ValueError:
        return False
    return a.is_loopback or a.is_link_local


def positions(b):
    """[(system, position, what)] — every position the being states, in the order the page's `reference` reads them:
    its `located_at`, the anchors whose value is an address, its `endpoints`."""
    f, out = fm(b), []
    for e in f.get("located_at") or []:
        if isinstance(e, dict) and e.get("at") not in (None, "") and e.get("openness") != "unknown":
            out.append((e.get("system"), str(e.get("at")), "located at (%s)" % e.get("openness", "")))
    for a in ((f.get("identity") or {}).get("anchors") or []) if isinstance(f.get("identity"), dict) else []:
        if isinstance(a, dict) and _ip_system(a.get("value")):
            out.append((_ip_system(a.get("value")), str(a.get("value")), "anchor %s" % a.get("key")))
    for e in f.get("endpoints") or []:
        if isinstance(e, dict) and e.get("at") not in (None, ""):
            what = " ".join(str(x) for x in (("%s:%s" % (e.get("protocol", ""), e["port"])) if e.get("port") else e.get("protocol", ""),
                                            e.get("exposure", "")) if x).strip()
            out.append((e.get("system"), str(e.get("at")), what))
    return out


def address(b, system):
    """The position that stands for a being in one system: the first it states there. Chosen by the page, stated by
    the being; '' where it states none."""
    return next((p for s, p, _w in positions(b) if s == system and not _near(p)), "") if system else ""


def addresses(b):
    """Every address the being states, the page's choice first: [{address, what: [...]}]."""
    ref = next((r for _i, r in entries_of_view("reference") if r.get("being") == b), {})
    first = address(b, ref.get("system"))
    out = {}
    if first:
        out[first] = ["stands for it on this page"]
    for _s, p, w in positions(b):
        if _near(p):
            continue
        out.setdefault(p, [])
        if w and w not in out[p]:
            out[p].append(w)
    return [{"address": a, "what": w} for a, w in out.items()]


def entries_of_view(attr):
    v = page_view().get(attr)
    return [(i, e) for i, e in enumerate(v)] if isinstance(v, list) else []


def reference_row(b):
    return next((r for _i, r in entries_of_view("reference") if r.get("being") == b), {})


def role(b):
    return reference_row(b).get("what") or ""


_K = None


def knowledge():
    """The garden's own dmknowledge, or None where it cannot be read."""
    global _K
    if _K is None:
        try:
            import dmknowledge
            _K = dmknowledge.Knowledge(ROOT)
            _K.rows("technology")
        except Exception:
            _K = False
    return _K or None


def field_scheme():
    """The scheme the technology catalogue hangs from (its `within`), read from the law."""
    s = next((r for r in law().registry("knowledge_schemes") or [] if isinstance(r, dict) and r.get("scheme") == "technology"), {})
    w = s.get("within") or []
    return w[0] if w else None


def tech(code):
    k = knowledge()
    if not k:
        return {"code": code, "name": code}
    e = k.resolve({"code": "technology:%s" % code})
    r = k.row("technology", code) or {}
    return {"code": code, "name": r.get("name", code), "docs": r.get("docs", ""), "homepage": r.get("homepage", ""),
            "category": r.get("category", ""), "vendor": r.get("vendor", ""), "fields": e.get("fields", []),
            "occupations": e.get("occupations", [])}


def bean_tech(b):
    """The technologies a being says it runs or is (its `knowledge` entries in the technology scheme)."""
    return [tech(_tech_code(e)) for e in (fm(b).get("knowledge") or [])
            if _tech_code(e) and e.get("rel") in ("uses", "classified_as")]


def _tech_code(e):
    """The technology code of a `knowledge` entry, whose `code` is written with its scheme (`technology:samba`) — or None."""
    c = e.get("code") if isinstance(e, dict) else None
    return c.split(":", 1)[1] if isinstance(c, str) and c.startswith("technology:") else None


def _short(v, n=180):
    if isinstance(v, dict):
        if "bean" in v:
            return str(v["bean"])
        inner = [_short(x, 60) for x in v.values()]
        return ", ".join(i for i in inner if i)[:n]
    if isinstance(v, list):
        return ", ".join(_short(x, 60) for x in v[:4]) + (" …" if len(v) > 4 else "")
    s = re.sub(r"\s+", " ", str(v)).strip()
    return s if len(s) <= n else s[:n - 1] + "…"


def shown_fields(b, lens_depth=3):
    """[[term, value]] — which of a being's own facts its card shows, per the page's `view.fields`, up to a lens."""
    f = fm(b)
    depth = {l["id"]: int(l["depth"]) for l in lenses()}
    rows = []
    for _i, e in entries_of_view("fields"):
        if e.get("genos") == f.get("genos") and depth.get(e.get("shown_from"), 9) <= lens_depth \
                and f.get(e.get("term")) not in (None, "", [], {}):
            rows.append([e.get("term"), _short(f[e["term"]])])
    return rows


def facts(b):
    f = fm(b)
    if not f:
        return None
    return {"title": b, "address": address(b, reference_row(b).get("system")), "role": role(b) or _short(f.get("title", ""), 90),
            "rows": shown_fields(b), "addresses": addresses(b), "tech": bean_tech(b), "genos": f.get("genos", ""),
            "org": org_of(b)}


# ---------------------------------------------------------------------------------------------------------------------
# the garden's drawings
# ---------------------------------------------------------------------------------------------------------------------
_GARDEN = None


def drawings_path():
    """The drawing module the page names, as a path inside the garden — or None where it names none, or names a file
    that is not a Python module inside it. The module is code the view host RUNS: a `file:` that climbed out of the
    garden (`..`, an absolute path, a link) would run whatever that path holds."""
    d = page_view().get("drawings")
    if not (isinstance(d, str) and d.startswith("file:")):
        return None
    rel = d[5:]
    if not rel or rel.startswith("/") or "\\" in rel or any(x in ("", ".", "..") for x in rel.split("/")) \
            or not rel.endswith(".py"):
        return None
    path = os.path.join(ROOT, *rel.split("/"))
    top = os.path.realpath(ROOT)
    return path if os.path.commonpath([top, os.path.realpath(path)]) == top else None


def garden():
    """The garden's own drawing module, loaded from the file the page names; the kit's names are importable from it."""
    global _GARDEN
    if _GARDEN is None:
        path = drawings_path()
        if not path or not os.path.isfile(path):
            raise NoPage("the page names no drawing module that exists inside the garden (`view.drawings`: "
                         "file:<path>.py, a path in the garden, with no `..`)")
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        spec = importlib.util.spec_from_file_location("garden_drawings", path)
        _GARDEN = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_GARDEN)
    return _GARDEN


def private():
    """Whether the page is read only by the viewers its host signs in (`view.visibility: private`); absent, it is public."""
    return page_view().get("visibility") == "private"


def ip(b, system="ipv4"):
    """The address the page's reference chooses for a being, for a drawing module to pass to `node`: drawn in the
    part's box on a private page, and never on a public one."""
    return address(b, reference_row(b).get("system") or system)


def compose_all():
    """{key: (title, svg, caption, claim, elements)} for every drawing the garden's module has."""
    kit.GLOSSARY.clear()
    g = page_view().get("glossary")
    kit.GLOSSARY.update({str(k): str(v) for k, v in g.items()} if isinstance(g, dict) else {})
    kit.NATURE_OF = lambda b: fm(b).get("nature")
    kit.ADDRESSES = private()
    comps = getattr(garden(), "COMPOSERS", None)
    if not isinstance(comps, dict):
        raise NoPage("the drawing module defines no COMPOSERS = {key: function}")
    return {k: kit.compose(fn) for k, fn in comps.items()}


# ---------------------------------------------------------------------------------------------------------------------
# the monitors, and the adapter each is read through
# ---------------------------------------------------------------------------------------------------------------------
SOURCES = os.path.join(HERE, "sources")
_ADAPTERS = {}


def adapter(code):
    """The adapter for a technology: `sources/<code>.py` beside this file, or None. The file is named by the code of the
    technology catalogue it reads; no technology is named in this file."""
    if code in _ADAPTERS:
        return _ADAPTERS[code]
    path = os.path.join(SOURCES, "%s.py" % code) if isinstance(code, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]*", code) else None
    mod = None
    if path and os.path.isfile(path):
        spec = importlib.util.spec_from_file_location("view_source_" + code.replace("-", "_"), path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    _ADAPTERS[code] = mod
    return mod


SURFACES = os.path.join(HERE, "surfaces")
_SURFACES = {}


def surface(code):
    """The surface for a technology: `surfaces/<code>.py` beside this file, or None — named, as a source adapter is, by
    the code of the technology catalogue it speaks: static HTML, daftar's own server, a framework's pages."""
    if code in _SURFACES:
        return _SURFACES[code]
    path = os.path.join(SURFACES, "%s.py" % code) if isinstance(code, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]*", code) else None
    mod = None
    if path and os.path.isfile(path):
        if SURFACES not in sys.path:
            sys.path.insert(0, SURFACES)
        spec = importlib.util.spec_from_file_location("view_surface_" + code.replace("-", "_"), path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    _SURFACES[code] = mod
    return mod


def where_shown():
    """(svg, places) — the page's own chain to the eye, engraved from its facts: each place it states it is shown at
    (`located_at`), the being that holds it there (`host`) and where that being runs (`lives_in`). On a public page a
    place whose position is an address is drawn by its system alone."""
    import view_engrave
    title = str(page().get("title") or PAGE)
    parts, pipes, seen, places = [{"proc": title, "rail": "the page", "role": "this page"}], [], {title}, []

    def part(name, rail, role):
        if name not in seen:
            seen.add(name)
            parts.append({"proc": name, "rail": rail, "role": role})
    for e in fm(PAGE).get("located_at") or []:
        if not isinstance(e, dict):
            continue
        at = str(e.get("at") or "")
        if not private() and _ADDRESS.search(at):
            at = ""
        where = ("%s %s" % (e.get("system"), at)).strip()
        rail = "shown at: %s" % e.get("system")
        part(where, rail, "open %s" % e.get("openness", "") if e.get("openness") else "")
        pipes.append({"from": title, "to": where, "channel": "shown at", "rail": rail})
        hb = e["host"].get("bean") if isinstance(e.get("host"), dict) else None
        places.append({"system": e.get("system"), "at": at, "host": hb, "openness": e.get("openness")})
        if hb and fm(hb):
            part(hb, rail, "%s · %s" % (fm(hb).get("genos", ""), fm(hb).get("nature", "")))
            pipes.append({"from": where, "to": hb, "channel": "held by", "rail": rail})
            lb = (fm(hb).get("lives_in") or {}).get("bean") if isinstance(fm(hb).get("lives_in"), dict) else None
            if lb and fm(lb):
                part(lb, rail, "%s · %s" % (fm(lb).get("genos", ""), fm(lb).get("nature", "")))
                pipes.append({"from": hb, "to": lb, "channel": "runs on", "rail": rail})
    if len(parts) < 2:
        return "", places
    svg, _rep = view_engrave.engrave(parts, pipes, key="proc", rail="rail", of_bean=PAGE, parts_field="located_at",
                                     pipes_field="located_at", sub="role", aria="where this page is shown")
    return svg, places


def surfaces_here():
    return sorted(n[:-3] for n in os.listdir(SURFACES) if n.endswith(".py")) if os.path.isdir(SURFACES) else []


def adapters_here():
    return sorted(n[:-3] for n in os.listdir(SOURCES) if n.endswith(".py")) if os.path.isdir(SOURCES) else []


def pointer(p, on=None):
    """What a `bean_field_pointer` points at: `{bean, field}` a field of that bean, `<section>.<key>` a field of the bean
    carrying the pointer, `file:<path>` a file of the garden read as YAML."""
    if isinstance(p, dict) and p.get("bean"):
        f = fm(p["bean"])
        for sect in ("details", "owns", "attributes"):
            if isinstance(f.get(sect), dict) and p.get("field") in f[sect]:
                return f[sect][p["field"]]
        return f.get(p.get("field"))
    if isinstance(p, str) and p.startswith("file:"):
        path = os.path.join(ROOT, *p[5:].split("/"))
        return dmparse.loads(open(path, encoding="utf-8").read()) if os.path.isfile(path) else None
    if isinstance(p, str) and "." in p:
        sect, _, key = p.partition(".")
        node = fm(on or PAGE).get(sect)
        return node.get(key) if isinstance(node, dict) else None
    return None


def monitors():
    """[{bean, technology, adapter, settings, reaches}] — the page's monitors, each with the technology it uses that an
    adapter here reads (the first such of its `knowledge` entries), or None."""
    out = []
    for _i, e in entries("view_monitors"):
        b = e.get("monitor")
        f = fm(b)
        uses = [_tech_code(k) for k in (f.get("knowledge") or [])
                if _tech_code(k) and k.get("rel") == "uses"]
        code = next((c for c in uses if adapter(c)), None)
        reaches = f.get("reaches") if isinstance(f.get("reaches"), dict) else {}
        out.append({"bean": b, "technology": code, "uses": uses, "adapter": adapter(code) if code else None,
                    "settings": pointer(e.get("settings")) if e.get("settings") is not None else None,
                    "reaches": {k: r for k, r in reaches.items() if isinstance(r, dict)}})
    return out


def reached(being):
    """The first monitor that reaches a being (its own `reaches`, targeting it)."""
    return next((m for m in monitors() if m["adapter"] and any(
        (r.get("to") or {}).get("bean") == being for r in m["reaches"].values())), None)


def computing(b):
    """The monitor that computes a binding: for a live-state, the first that reaches its being; else the first whose
    technology the binding gives a query for."""
    if b.get("live") == "live-state":
        return reached(b.get("probe"))
    m = next((m for m in monitors() if m["adapter"] and m["technology"] in (b.get("query") or {})), None)
    if m is None and b.get("signal"):     # a published signal: the first monitor whose adapter asks signals in its language
        m = next((m for m in monitors() if m["adapter"] and hasattr(m["adapter"], "signal_query")), None)
    return m


# ---------------------------------------------------------------------------------------------------------------------
# drawings, bindings and the operate shapes
# ---------------------------------------------------------------------------------------------------------------------
def views_raw():
    return entries("views")


def view_entry(key):
    return next((e for k, e in views_raw() if k == key), {})


def draws_of(v):
    d = v.get("draws") if isinstance(v, dict) else None
    for k, folder in (("mapping", "mappings"), ("bean", "beans")):
        if isinstance(d, dict) and d.get(k):
            return k, d[k], folder
    return None, None, None


def draws_label(v):
    k, i, _f = draws_of(v)
    return "%s %s" % (k, i) if k else "?"


def bindings(key, elements):
    """(binds, problems): the page's `view_bindings` that sit on the drawing `key`, resolved against its elements. A
    binding's id is its key on the page."""
    by = {e["id"]: e for e in elements}
    out, probs = [], []
    for bk, b in entries("view_bindings"):
        if b.get("view") != key:
            continue
        r, p = _binding(key, bk, b, by)
        probs += p
        if r:
            out.append(r)
    return out, probs


def page_bindings(figs):
    """{binding key: its record} — every binding of the page, each resolved against the drawing it sits on."""
    out = {}
    for k, v in views_raw():
        if k in figs:
            out.update({b["id"]: b for b in bindings(k, figs[k][4])[0]})
    return out


def _binding(key, bk, b, by):
    """(record, problems) for one binding, resolved against the elements of the drawing it sits on."""
    probs = []
    el = b.get("element")
    if el not in by:
        return None, ["%s: binding %s sits on element %r, which the drawing does not have" % (key, bk, el)]
    q, f = unit(b.get("unit"))
    queries = {str(x.get("technology")): x.get("says") for x in (b.get("query") or []) if isinstance(x, dict)}
    items_by = {str(x.get("technology")): x.get("items_by") for x in (b.get("query") or []) if isinstance(x, dict)}
    r = {"id": bk, "el": el, "live": b.get("live"), "name": b.get("label") or by[el]["label"], "short": b.get("short", ""),
         "unit": b.get("unit") or "", "q": q, "f": f, "warn": count(b.get("warn")), "crit": count(b.get("crit")),
         "item_names": b.get("item_names") if isinstance(b.get("item_names"), dict) else {},
         "query": queries, "items_by": items_by, "probe": b.get("being") or by[el]["bean"],
         "signal": next((dict(s) for s in registry("signals") if isinstance(s, dict) and s.get("signal") == b.get("signal")), None)
         if b.get("signal") else None}
    if r["live"] == "live-state" and not r["probe"]:
        return None, ["%s: %s is a live-state on %r, which depicts no being — give the binding `being`" % (key, bk, el)]
    m = computing(r)
    r["monitor"] = m["bean"] if m else None
    r["technology"] = m["technology"] if m else None
    r["source"] = ((m["adapter"].describe(r) if m else "") or "")
    if not m:
        probs.append(("%s: %s is a live-state on %r, and no monitor of the page reaches it" % (key, bk, r["probe"]))
                     if r["live"] == "live-state" else
                     ("%s: %s gives a query for %s, and no monitor of the page runs one with an adapter here (%s)"
                      % (key, bk, ", ".join(sorted(queries)) or "no technology", ", ".join(adapters_here()) or "none")))
    elif hasattr(m["adapter"], "check_binding"):
        probs += ["%s: %s: %s" % (key, bk, p) for p in m["adapter"].check_binding(r)]
    return r, probs


def actions(key, v, elements):
    by = {e["id"]: e for e in elements}
    out, probs = [], []
    for a in v.get("actions") or []:
        if not isinstance(a, dict):
            continue
        at, tool = a.get("element"), a.get("tool")
        if at not in by or by[at]["pattern"] != "action":
            probs.append("%s: action %r sits on %r, which is not an action element of the drawing" % (key, tool, at)); continue
        out.append({"el": at, "tool": tool, "confirm": a.get("confirm") or ("Run %s?" % tool),
                    "bean": a.get("acts_on") or by[at]["bean"], "label": by[at]["label"],
                    "inputs": [dict(i) for i in a.get("inputs") or [] if isinstance(i, dict)],
                    "reason": a.get("reason") == "asked", "every": a.get("every"), "answered_by": a.get("answered_by")})
    return out, probs


def members(sel):
    """The members of one of the page's readings (`selections`), by the one grammar (bin/dmreckon.py)."""
    import dmreckon
    return dmreckon.select("%s:%s" % (PAGE, sel), root=ROOT)


def writes(v):
    """A drawing's entry forms (24.0, N37): for each `writes`, the term, whether its entries are keyed, and each attribute
    the form asks for — the ones it names, or all the term's — with the law's own `required` and meaning."""
    out = []
    for n, w in enumerate(v.get("writes") or []):
        if not isinstance(w, dict) or not w.get("term"):
            continue
        sch = law().SCHEMAS.get(w["term"]) or {}
        rec = sch.get("attrs") or {}
        names = [a.get("attr") for a in w.get("attrs") or [] if isinstance(a, dict)] or list(rec)
        out.append({"w": n, "term": w["term"], "keyed": sch.get("shape") == "open_map_of_entries",
                    "attrs": [{"attr": a, "required": (rec.get(a) or {}).get("required") is True,
                               "meaning": str((rec.get(a) or {}).get("meaning") or "")} for a in names]})
    return out


def _cell(x):
    if isinstance(x, (list, tuple)):
        return ", ".join(_cell(y) for y in x)
    return "" if x is None else x if isinstance(x, (int, float, str)) and not isinstance(x, bool) else str(x)


def table(v):
    """A table's lines (24.0, N36): {columns, rows}. From a reading, one line per member, each column the values at its
    path; from a series (`{bean, field}`, or `<section>.<key>` on the page), one line per row, each column a channel —
    or `at`, the row's position. Each line names the being it shows, for the host to send it only where it may."""
    cols = [c for c in v.get("columns") or [] if isinstance(c, dict)]
    out = {"columns": [str(c.get("label") or c.get("path")) for c in cols], "rows": [],
           # the top-level terms the columns read: a line is sent where the viewer may see these parts of its being
           "reads": sorted({re.split(r"[.\[]", str(c.get("path")))[0] for c in cols if c.get("path") not in (None, "at", "position")})}
    if v.get("selection"):
        import dmreckon
        for m in members(v["selection"]):
            out["rows"].append({"bean": m, "cells": [_cell(dmreckon.path_values(fm(m), c["path"], root=ROOT)) for c in cols]})
        return out
    p = v.get("series")
    bean, key = (p.get("bean"), p.get("field")) if isinstance(p, dict) else (PAGE, str(p).partition(".")[2])
    out["reads"] = ["series"]
    import dmseq
    for r in dmseq.rows(ROOT, bean, key):
        pos = r.get("position")
        at = "%s – %s" % pos if isinstance(pos, tuple) else pos
        out["rows"].append({"bean": bean, "cells": [_cell(at if c["path"] in ("at", "position") else r["cells"].get(c["path"]))
                                                    for c in cols]})
    return out


def steps_of(v):
    """The steps of the procedure a drawing draws, as plain lines: a prose step as written, an entry by its `do`."""
    k, i, folder = draws_of(v)
    st = fm(i, folder).get("steps") if k else None
    out = []
    for s in st or []:
        out.append(str(s.get("do") or s.get("id")) if isinstance(s, dict) else str(s))
    return out


def branches(v):
    """The steps of the drawn procedure that branch: a step with more than one `next`, or a `next` that is not the step
    after it. A race counts steps in order, so it reads a procedure that does not branch."""
    k, i, folder = draws_of(v)
    st = fm(i, folder).get("steps") if k == "mapping" else None
    out = []
    for n, s in enumerate(st or []):
        if isinstance(s, dict):
            nx = [x.get("to") for x in (s.get("next") or []) if isinstance(x, dict)]
            after = st[n + 1].get("id") if n + 1 < len(st) and isinstance(st[n + 1], dict) else None
            if len(nx) > 1 or (nx and nx[0] != after):
                out.append(str(s.get("id")))
    return out


def _ids(lst):
    return [x.get("bind") for x in (lst or []) if isinstance(x, dict) and x.get("bind")]


def operate(key, v):
    """The operate shape of a drawing, as the runtime reads it: binding keys, thresholds as percents of the whole,
    lengths of time in seconds, a race's steps from the procedure it draws."""
    op = {"archetype": v.get("archetype"),
          "notes": [n.get("note") for n in (v.get("notes") or []) if isinstance(n, dict)],
          "blind": ["%s%s" % (b.get("what"), (" — " + b["why"]) if b.get("why") else "") for b in (v.get("blind") or [])
                    if isinstance(b, dict)]}
    for k in ("fill", "forecast", "per_item", "list", "step_at", "elapsed", "deadline_from", "eta", "progress"):
        if v.get(k):
            op[k] = v[k]
    for k in ("also", "parts", "facts", "numbers"):
        if v.get(k):
            op[k] = _ids(v[k])
    for k in ("active_over", "top", "min", "max"):
        if v.get(k) is not None:
            op[k] = count(v[k])
    if v.get("window"):
        op["window"] = v["window"]
    if v.get("thresholds"):
        op["thresholds"] = [{"at": share(t.get("fullness")), "label": t.get("label", "")} for t in v["thresholds"]
                            if isinstance(t, dict) and share(t.get("fullness")) is not None]
    if v.get("lanes"):
        op["lanes"] = [{"name": ln.get("label", ""), "hops": [{"label": h.get("label", ""), "bind": h.get("bind")}
                                                          for h in (ln.get("hops") or []) if isinstance(h, dict)]}
                       for ln in v["lanes"] if isinstance(ln, dict)]
    if v.get("members"):
        op["items"] = [{"label": it.get("label", ""), "binds": _ids(it.get("binds")), "fact": it.get("fact"),
                        "why": it.get("why", ""), "bean": it.get("being")} for it in v["members"] if isinstance(it, dict)]
    if v.get("funnels"):
        op["funnels"] = [{"name": f.get("label", ""), "stages": [
            {"label": s.get("label", ""), "count": s.get("tally"), "counts": s.get("counts", ""), "what": s.get("what", ""),
             "members": members(s["selection"]) if s.get("selection") else None,
             "stops": [{"label": x.get("label", ""), "bind": x.get("bind"), "what": x.get("what", "")} for x in s.get("stops") or []],
             "marks": [{"label": x.get("label", ""), "bind": x.get("bind"), "what": x.get("what", "")} for x in s.get("marks") or []]}
            for s in (f.get("stages") or []) if isinstance(s, dict)]} for f in v["funnels"] if isinstance(f, dict)]
        for f in op["funnels"]:
            for st in f["stages"]:
                st["static"] = len(st["members"]) if st["members"] is not None else None
    if v.get("rollcall"):
        op["rollcall"] = [{"label": r.get("label", ""), "per_item": r.get("per_item"),
                           "idle": [str(x.get("member")) for x in (r.get("idle") or []) if isinstance(x, dict)],
                           "notes": r.get("notes") if isinstance(r.get("notes"), dict) else {}}
                          for r in v["rollcall"] if isinstance(r, dict)]
    if v.get("archetype") == "table":
        op["table"] = table(v)
    steps = steps_of(v)
    if v.get("archetype") == "race" or v.get("correlate"):
        op["steps"] = steps
    if v.get("deadline") is not None:
        op["deadline"] = seconds(v["deadline"])
    if v.get("checkpoints"):
        op["checkpoints"] = [{"at": seconds(c.get("after")), "label": c.get("label", "")} for c in v["checkpoints"]
                             if isinstance(c, dict) and seconds(c.get("after")) is not None]
    op["correlate"] = [{"title": c.get("title", ""), "rows": _ids(c.get("traces")), "band": c.get("band"),
                        "bands": [STEP_NONE] + steps if c.get("band") else [],
                        "relate": _relate(c.get("relate"))} for c in correlates(v)]
    return op


def correlates(v):
    c = v.get("correlate")
    return [x for x in (c if isinstance(c, list) else [c] if isinstance(c, dict) else []) if isinstance(x, dict)]


def _relate(r):
    r = r[0] if isinstance(r, list) and r else r
    if not isinstance(r, dict):
        return None
    return {"across": r.get("across"), "measure": r.get("measure"), "bins": int(count(r.get("bins")) or 8),
            "at_step": int(count(r["at_step"])) if r.get("at_step") is not None else None, "keep": r.get("keep") or "all"}


CORRELATE_MAX_POINTS = 11000     # a range read of more points than this is refused by the monitor the adapter asks


def window(v):
    """(hours, step in seconds) of a drawing's history: its correlate blocks' longest `span` and finest `every`, bounded
    to between a quarter of an hour and two days, a step of at least ten seconds, and at most CORRELATE_MAX_POINTS
    points; six hours at five minutes where it states neither."""
    spans = [seconds(c.get("span")) for c in correlates(v) if seconds(c.get("span"))]
    steps = [seconds(c.get("every")) for c in correlates(v) if seconds(c.get("every"))]
    hours = min(max((max(spans) / 3600.0) if spans else 6.0, 0.25), 48.0)
    step = max(int(min(steps)) if steps else 300, 10)
    while hours * 3600 / step > CORRELATE_MAX_POINTS:
        step *= 2
    return hours, step


def references_in(v):
    """Every binding key a drawing's operate shape names, with where it names it."""
    out = []
    for k in ("fill", "forecast", "per_item", "list", "step_at", "elapsed", "deadline_from", "eta", "progress"):
        if v.get(k):
            out.append((k, v[k]))
    for k in ("also", "parts", "facts", "numbers"):
        out += [(k, b) for b in _ids(v.get(k))]
    for ln in v.get("lanes") or []:
        out += [("lanes.hops", h.get("bind")) for h in (ln.get("hops") or []) if isinstance(h, dict)]
    for it in v.get("members") or []:
        out += [("members.binds", b) for b in _ids(it.get("binds"))] + ([("members.fact", it["fact"])] if it.get("fact") else [])
    for f in v.get("funnels") or []:
        for s in f.get("stages") or []:
            out += [("funnels.stages.tally", s.get("tally"))] + [("funnels.stages.stops", x.get("bind")) for x in s.get("stops") or []] + \
                   [("funnels.stages.marks", x.get("bind")) for x in s.get("marks") or []]
    for r in v.get("rollcall") or []:
        out.append(("rollcall.per_item", r.get("per_item")))
    for c in correlates(v):
        out += [("correlate.traces", b) for b in _ids(c.get("traces"))] + ([("correlate.band", c["band"])] if c.get("band") else [])
        r = _relate(c.get("relate"))
        if r:
            out += [("correlate.relate.across", r["across"]), ("correlate.relate.measure", r["measure"])]
    return out


def wiring(key, v):
    """inspect: the processes and pipes of what a drawing draws, read from the being that states them."""
    spec = {k: v.get(k) for k in ("processes", "pipes") if v.get(k) is not None}
    if not spec:
        return None, []
    probs = []
    if "pipes" not in spec:
        probs.append("%s: `processes` is stated without `pipes` — a process is drawn with the pipes that join it, so the "
                     "two come as a pair; pipes alone are wiring enough" % key)
    beans = {p.get("bean") if isinstance(p, dict) else PAGE for p in spec.values()}
    out = {"bean": sorted(b for b in beans if b)[0] if beans else PAGE, "processes": [], "pipes": []}
    need = {"processes": ("proc", "user", "role", "config"), "pipes": ("from", "to", "channel", "at", "config")}
    for k, p in spec.items():
        rows = pointer(p)
        if not isinstance(rows, list):
            probs.append("%s: `%s` points at %r, which is not a list of rows" % (key, k, p)); continue
        for i, r in enumerate(rows):
            if not isinstance(r, dict) or any(not r.get(n) for n in need[k][:2]):
                probs.append("%s: %s[%d] needs at least %s" % (key, k, i, " and ".join(need[k][:2]))); continue
            out[k].append({n: str(r.get(n, "")) for n in need[k] + ("rail", "note", "state")})
    return out, probs


def resolve_story(v):
    """orient: the drawing's story, with every technology resolved to its own documentation, and the fields of
    knowledge its technologies stand in."""
    stages, fields, scheme = [], {}, field_scheme()
    k = knowledge()
    for x in v.get("stages") or []:
        if not isinstance(x, dict):
            continue
        ts = [tech(str(u.get("technology"))) for u in (x.get("uses") or []) if isinstance(u, dict)]
        for t in ts:
            for f in t.get("fields", []):
                fields.setdefault(f["code"], {"scheme": scheme or "", "code": f["code"], "label": f["label"], "techs": []})
                if t["name"] not in fields[f["code"]]["techs"]:
                    fields[f["code"]]["techs"].append(t["name"])
        stages.append({"label": x.get("label", ""), "doer": x.get("doer", ""), "tech": ts,
                       "parts": [{"title": b.get("being"), "role": role(b.get("being"))} for b in (x.get("beings") or [])
                                 if isinstance(b, dict)]})
    for f in fields.values():
        f["path"] = [a.get("name_en") for a in k.ancestry(scheme, f["code"])] if (k and scheme) else [f["label"]]
    return {"purpose": v.get("purpose", ""), "outcome": v.get("outcome", ""), "stages": stages,
            "fields": sorted(fields.values(), key=lambda f: f["code"])}


def health_tiles(els, binds):
    """operate, the fallback: one tile per bound element, in the drawing's reading order, then a BLIND SPOT for every
    depicted part that has no signal at all — shown, never hidden."""
    by = {e["id"]: e for e in els}

    def order(e):
        b = e.get("box") or [0, 0, 0, 0]
        return (round(b[1] / 120), b[0])
    bound = {}
    for b in binds:
        if not b.get("elsewhere"):
            bound.setdefault(b["el"], []).append(b["id"])
    tiles = [{"el": el, "label": by[el]["label"], "bean": by[el]["bean"], "binds": ids}
             for el, ids in sorted(bound.items(), key=lambda kv: order(by[kv[0]]))]
    seen = {by[el]["bean"] for el in bound if by[el]["bean"]} | {b.get("probe") for b in binds if not b.get("elsewhere")}
    blind = []
    for e in sorted(els, key=order):
        if e["pattern"] not in ("node", "store") or e["id"] in bound:
            continue
        if e["bean"] and e["bean"] in seen:
            continue
        if e["bean"]:
            seen.add(e["bean"])
        blind.append({"el": e["id"], "label": e["label"], "bean": e["bean"], "blind": True,
                      "why": ("no monitor reports on %s" % e["bean"]) if e["bean"]
                             else "not a being of the garden — nothing measures it"})
    return tiles + blind


def anatomy_parts(els, v):
    """inspect: a card of each part's own facts, for every being the drawing depicts or its story names."""
    order = []
    for e in els:
        if e["bean"] and e["bean"] not in order:
            order.append(e["bean"])
    for x in v.get("stages") or []:
        for b in (x.get("beings") or []) if isinstance(x, dict) else []:
            if isinstance(b, dict) and b.get("being") not in order:
                order.append(b.get("being"))
    out = []
    for b in order:
        f = fm(b)
        if not f:
            continue
        pv = f.get("provenance") if isinstance(f.get("provenance"), dict) else {}
        out.append({"bean": b, "genos": f.get("genos", ""), "org": org_of(b), "role": role(b) or _short(f.get("title", ""), 110),
                    "anchors": [{"key": a.get("key"), "value": str(a.get("value")), "establishing": bool(a.get("establishing"))}
                                for a in ((f.get("identity") or {}).get("anchors") or []) if isinstance(a, dict)]
                    if isinstance(f.get("identity"), dict) else [],
                    "addresses": addresses(b), "tech": bean_tech(b), "rows": shown_fields(b),
                    "provenance": " · ".join(str(x) for x in (pv.get("src"), pv.get("by"), pv.get("as_of")) if x),
                    "open": [_short(o, 220) for o in (f.get("open") or [])][:3]})
    return out


def bound_steps(v, beans):
    """inspect: the drawn procedure's steps, each bound to the parts it names — by id, or by an address the part states."""
    addr = {}
    for b in beans:
        for a in addresses(b):
            addr[a["address"]] = b
    out = []
    for text in steps_of(v) or ([_short(fm(draws_of(v)[1], draws_of(v)[2]).get("summary", ""), 600)] if draws_of(v)[0] else []):
        hit = [b for b in beans if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(b), text)]
        hit += [b for a, b in addr.items() if a in text and b not in hit]
        out.append({"text": text, "parts": hit})
    return out


def alert_names(beans, binds):
    """The alert rules a monitor's settings state that concern a drawing, as its adapter reads them."""
    out = []
    for m in monitors():
        a = m["adapter"]
        if a and hasattr(a, "alerts"):
            out += [n for n in a.alerts(m["settings"], beans, binds) if n not in out]
    return out


def views(figs=None):
    """One view per drawing, in the page's order: what every renderer mounts."""
    figs = figs or compose_all()
    lv = lenses()
    live = live_meanings()
    every = page_bindings(figs)
    out = []
    for k, v in views_raw():
        if k not in figs:
            continue
        title, svg, cap, claim, els = figs[k]
        binds, _ = bindings(k, els)
        # a value the shape reads may sit on another drawing of the page: it is carried beside this drawing's own
        binds += [dict(every[ref], elsewhere=True) for ref in dict.fromkeys(r for _w, r in references_in(v))
                  if ref in every and ref not in {b["id"] for b in binds}]
        pats = kit.patterns_of(els)
        kinds = sorted({b["live"] for b in binds if b.get("live")})
        beans = [e["bean"] for e in els if e["bean"]]
        beans = sorted(set(beans), key=beans.index)
        parts = anatomy_parts(els, v)
        w, _ = wiring(k, v)
        hours, step = window(v)
        rel = ("drawing of <b>%s</b> · drawn with <b>%s</b> · live <b>%s</b>"
               % (kit.esc(draws_label(v)), kit.esc(", ".join(pats)), kit.esc(", ".join(kinds) or "—")))
        out.append({"key": k, "title": kit.esc(v.get("label") or title), "claim": kit.gloss_html(claim),
                    "caption": kit.gloss_html(cap), "rel": rel, "svg": svg, "uid": "view-%s" % k,
                    "source": draws_label(v), "draws_bean": draws_of(v)[1] if draws_of(v)[0] == "bean" else None,
                    "elements": [{a: x for a, x in e.items() if a != "unfit_address"} for e in els], "binds": binds,
                    "facts": {b: facts(b) for b in beans if facts(b)},
                    "steps": bound_steps(v, [p["bean"] for p in parts]),
                    "legend": kit.legend_rows(pats + kinds, live), "patterns": pats, "live_patterns": kinds,
                    "actions": actions(k, v, els)[0], "writes": writes(v), "levels": lv, "story": resolve_story(v),
                    "tiles": health_tiles(els, binds), "parts": parts,
                    "questions": {q.get("lens"): q.get("ask") for q in (v.get("questions") or []) if isinstance(q, dict)},
                    "operate": operate(k, v), "wiring": w, "window": {"hours": hours, "step": step},
                    "patternMeaning": {p: kit.PATTERNS.get(p, "") for p in pats},
                    "opens": [{"el": o.get("element"), "view": o.get("view")} for o in (v.get("opens") or []) if isinstance(o, dict)],
                    "frame": v.get("frame"), "proposed": proposed_archetype(v),
                    "alerts": alert_names([p["bean"] for p in parts], binds)})
    return out


# ---------------------------------------------------------------------------------------------------------------------
# check — the page against the law and the drawings; errors refuse, warnings inform
# ---------------------------------------------------------------------------------------------------------------------
_ADDRESS = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])|(?<![\w:])(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{0,4}(?![\w:])")


def svg_text(svg):
    return " ".join(re.findall(r">([^<]+)<", svg or ""))


def addresses_drawn(svg):
    """The addresses a drawing's own text shows: on a public page, what a lens that shows no address would show every
    viewer. A part's own address, drawn on a private page, is not among them: the host sends it only to a viewer who may
    see that being."""
    return sorted({m for m in _ADDRESS.findall(svg_text(svg)) if _ip_system(m)})


def check(figs=None):
    errs, warns = [], []
    try:
        figs = figs or compose_all()
    except NoPage as e:
        return [str(e)], []
    except Exception as e:                       # the garden's own code: its failure is named, never a traceback
        return ["the drawing module %s failed: %s: %s" % (page_view().get("drawings"), type(e).__name__, e)], []
    # THE PAGE'S TERMS SIT ON THE PAGE. The schema language cannot say "only on the bean that carries another term", so
    # the gate passes a `views` written on a being; this refuses it.
    for b in bean_ids():
        if b != PAGE:
            stray = [t for t in TERMS if t in fm(b)]
            if stray:
                errs.append("%s carries %s, which sit on the page, the bean that carries `%s` (%s)"
                            % (b, ", ".join("`%s`" % t for t in stray), PROFILE, PAGE))
    for m in bean_ids("mappings"):
        stray = [t for t in TERMS if t in fm(m, "mappings")]
        if stray:
            errs.append("mappings/%s carries %s, which sit on the page (%s)" % (m, ", ".join("`%s`" % t for t in stray), PAGE))
    keys = [k for k, _v in views_raw()]
    for k in sorted(set(figs) - set(keys)):
        errs.append("the drawing module draws %r, which the page does not list in `views`" % k)
    story_lens, und, op_lens, ins = lens_of_form("story"), lens_of_form("schematic"), lens_of_form("health-chain"), lens_of_form("anatomy")
    every = page_bindings(figs)
    known_terms = set(law().TERMS)
    for k, v in views_raw():
        if k not in figs:
            errs.append("%s: listed in `views`, and the drawing module has no drawing for it" % k); continue
        els = figs[k][4]
        kk, target, folder = draws_of(v)
        if not kk or not fm(target, folder):
            errs.append("%s: draws %r, which is no bean or mapping of the garden" % (k, v.get("draws")))
        mx = story_lens.get("max") or {}
        st = [s for s in (v.get("stages") or []) if isinstance(s, dict)]
        if mx.get("stages") is not None and len(st) > int(mx["stages"]):
            errs.append("%s: the story has %d stages, and the %s lens holds at most %s" % (k, len(st), story_lens["id"], mx["stages"]))
        if mx.get("words_per_stage") is not None:
            for i, s in enumerate(st):
                n = len(("%s %s" % (s.get("label", ""), s.get("doer", ""))).split())
                if n > int(mx["words_per_stage"]):
                    errs.append("%s: story stage %d says %d words, and the %s lens holds %s a stage"
                                 % (k, i + 1, n, story_lens["id"], mx["words_per_stage"]))
        if (und.get("max") or {}).get("elements") is not None and len(els) > int(und["max"]["elements"]):
            errs.append("%s: the drawing has %d elements, and the %s lens holds %s — open a part as a drawing of its own "
                        "(`views.opens`) rather than crowd it" % (k, len(els), und["id"], und["max"]["elements"]))
        for e in els:
            if e.get("unfit_address"):
                warns.append("%s: %s's address %s fits nowhere in its box (%s wide): it is on the part's card, and a wider "
                             "box would draw it" % (k, e["id"], e["unfit_address"], int(e["box"][2]) if e.get("box") else "?"))
        drawn = addresses_drawn(figs[k][1])
        if drawn and not private():
            errs.append("%s: the drawing shows %s — a public page's drawing carries no address: a being's addresses are "
                        "on its card, for a viewer who may see them; a page read only behind its host's sign-in says "
                        "`view.visibility: private`" % (k, ", ".join(drawn)))
        binds, e = bindings(k, els)
        errs += e
        errs += actions(k, v, els)[1]
        for where, ref in references_in(v):
            if ref and ref not in every:
                errs.append("%s: `%s` names %r, which is no binding the page resolves" % (k, where, ref))
        w, e = wiring(k, v)
        errs += e
        if v.get("archetype") == "race":
            if kk != "mapping" or not steps_of(v):
                errs.append("%s: a race draws a procedure with `steps`, and it draws %s" % (k, draws_label(v)))
            elif branches(v):
                errs.append("%s: a race counts the steps of what it draws in order, and %s branches at %s"
                            % (k, draws_label(v), ", ".join(branches(v))))
        n_steps = len(steps_of(v))
        for c in correlates(v):
            r = _relate(c.get("relate"))
            if r and r["at_step"] is not None and not 0 <= r["at_step"] <= n_steps:
                warns.append("%s: correlate relates at step %s, and %s has %d" % (k, r["at_step"], draws_label(v), n_steps))
        tiles = health_tiles(els, binds)
        if v.get("archetype") == "health-chain" and (op_lens.get("max") or {}).get("tiles") is not None \
                and len(tiles) > int(op_lens["max"]["tiles"]):
            errs.append("%s: %d tiles, and the %s lens holds %s" % (k, len(tiles), op_lens["id"], op_lens["max"]["tiles"]))
        parts = anatomy_parts(els, v)
        if (ins.get("max") or {}).get("cards") is not None and len(parts) > int(ins["max"]["cards"]):
            errs.append("%s: %d cards, and the %s lens holds %s" % (k, len(parts), ins["id"], ins["max"]["cards"]))
        # ZOOM: an element that opens a drawing of its own is one the drawing draws, and the drawing it opens is the page's
        by_id = {e["id"]: e for e in els}
        for o in v.get("opens") or []:
            if not isinstance(o, dict):
                continue
            if o.get("element") not in by_id:
                errs.append("%s: opens %r from element %r, which the drawing does not have" % (k, o.get("view"), o.get("element")))
            elif by_id[o["element"]]["pattern"] in ("flow", "signal"):
                errs.append("%s: opens %r from %r, a flow — a drawing opens from a part it depicts" % (k, o.get("view"), o["element"]))
            if o.get("view") == k:
                errs.append("%s: element %r opens the drawing it is in" % (k, o.get("element")))
        _prop = proposed_archetype(v)
        if v.get("archetype") and _prop not in ("health-chain", v.get("archetype")):
            warns.append("%s: the facts propose the %s shape, and the page draws %s" % (k, _prop, v.get("archetype")))
        for el in els:
            if el["bean"] and not fm(el["bean"]):
                errs.append("%s: element %r depicts %r, which is no bean of the garden" % (k, el["id"], el["bean"]))
    # THE PAGE STATES WHERE IT IS SHOWN: a URI where it is served, a path where a copy is kept — its own `located_at`
    if not [e for e in (fm(PAGE).get("located_at") or []) if isinstance(e, dict)]:
        errs.append("%s: the page states nowhere it is shown — its `located_at`: a `uri` where it is served, a path where a "
                    "copy of it is kept (`unix-filesystem`), each with the `host` that holds it" % PAGE)
    for m in monitors():
        if not fm(m["bean"]):
            continue                                 # the gate refuses a monitor the garden does not hold
        if not m["technology"]:
            errs.append("monitor %s uses %s, and no adapter here reads it (assets/%s/lib/sources: %s)"
                        % (m["bean"], ", ".join(m["uses"]) or "no technology (its `knowledge` states none it `uses`)",
                           PROFILE, ", ".join(adapters_here()) or "none"))
        elif hasattr(m["adapter"], "check_monitor"):
            p_, w_ = m["adapter"].check_monitor(m)
            errs += ["monitor %s: %s" % (m["bean"], x) for x in p_]
            warns += ["monitor %s: %s" % (m["bean"], x) for x in w_]
    for _i, r in entries_of_view("reference"):
        b = r.get("being")
        if fm(b) and r.get("system") and not address(b, r["system"]):
            warns.append("reference: %s states no position in %s, so the page shows no address for it" % (b, r["system"]))
    for _i, f in entries_of_view("fields"):
        if f.get("term") and f["term"] not in known_terms:
            errs.append("view.fields: %r is no term the law declares" % f["term"])
    return errs, warns


# ---------------------------------------------------------------------------------------------------------------------
# import — an author-mode selection written into the page, through dmsafe, and journalled
# ---------------------------------------------------------------------------------------------------------------------
_PLAIN = re.compile(r"^[A-Za-z_][A-Za-z0-9_./-]*$")
_YAML_WORDS = {"true", "false", "yes", "no", "on", "off", "null", "none", "~", "y", "n"}


def yflow(v):
    """One line of YAML for a value, in flow style: a key or a string quoted where YAML would read it as something else."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return json.dumps(repr(v) if v != int(v) else str(int(v)))
    if isinstance(v, dict):
        return "{ " + ", ".join("%s: %s" % (_key(k), yflow(x)) for k, x in v.items()) + " }" if v else "{}"
    if isinstance(v, list):
        return "[" + ", ".join(yflow(x) for x in v) + "]"
    s = str(v)
    return s if (_PLAIN.match(s) and s.lower() not in _YAML_WORDS) else json.dumps(s, ensure_ascii=False)


def _key(k):
    s = str(k)
    return s if (_PLAIN.match(s) and s.lower() not in _YAML_WORDS) else json.dumps(s, ensure_ascii=False)


def _attr_order(term):
    t = law().TERMS.get(term) or {}
    return list(((t.get("schema") or {}).get("attrs") or {}))


def yaml_views(vs):
    order = _attr_order("views")
    out = ["views:"]
    for k, v in vs.items():
        out.append("  %s:" % _key(k))
        for a in order + [a for a in v if a not in order]:
            if a in v:
                out.append("    %s: %s" % (_key(a), yflow(v[a])))
    return "\n".join(out) + "\n"


def yaml_bindings(bs):
    return "view_bindings:\n" + "".join("  %s: %s\n" % (_key(k), yflow(b)) for k, b in bs.items())


def yaml_view(v):
    out = ["view:"]
    for a in _attr_order("view") + [a for a in v if a not in _attr_order("view")]:
        if a not in v:
            continue
        if isinstance(v[a], list):
            out.append("  %s:" % a)
            out += ["    - %s" % yflow(x) for x in v[a]]
        else:
            out.append("  %s: %s" % (a, yflow(v[a])))
    return "\n".join(out) + "\n"


def _plain_data(x):
    return json.loads(json.dumps(x, default=str))


EDITABLE = ("label", "purpose", "outcome", "stages", "questions", "actions")


def import_selection(path, who=None):
    """Validate an author-mode selection and write it into the page. Returns the journal line it wrote, or says there
    was nothing to write. Only the page's own terms are written; a drawing, its archetype and what the shape reads stay
    as the page states them — the selection edits the story, the questions, the actions, the bindings, the reference
    and which facts a card shows."""
    import dmsafe
    sel = json.load(open(path, encoding="utf-8"))
    cur = dict(views_raw())
    figs = compose_all()
    problems = []
    order = [k for k in (sel.get("order") or list(cur)) if k in cur]
    order += [k for k in cur if k not in order]                      # a selection never drops a drawing
    new_views = {}
    for k in order:
        v = dict(cur[k])
        s = (sel.get("views") or {}).get(k) or {}
        for a in EDITABLE:
            if a in s:
                if s[a] in (None, "", [], {}):
                    v.pop(a, None)
                else:
                    v[a] = s[a]
        new_views[k] = v
    for k in (sel.get("views") or {}):
        if k not in cur:
            problems.append("views: %r is no drawing of the page — a drawing is added in the drawing module first" % k)
    new_binds = sel.get("bindings") if isinstance(sel.get("bindings"), dict) else dict(entries("view_bindings"))
    for bk, b in new_binds.items():
        if not isinstance(b, dict) or b.get("view") not in new_views:
            problems.append("bindings: %s sits on no drawing of the page" % bk)
        elif b.get("element") not in {e["id"] for e in figs.get(b["view"], (None,) * 5)[4] or []}:
            problems.append("bindings: %s sits on element %r, which the drawing %s does not have" % (bk, b.get("element"), b.get("view")))
    new_view = dict(page_view())
    for a in ("reference", "fields"):
        if a in sel:
            if sel[a]:
                new_view[a] = sel[a]
            else:
                new_view.pop(a, None)
    for r in new_view.get("reference") or []:
        if not fm((r or {}).get("being")):
            problems.append("reference: %r is no bean of the garden" % (r or {}).get("being"))
    if problems:
        raise SystemExit("dmview: selection refused — nothing written:\n  - " + "\n  - ".join(problems))
    bean = os.path.join(ROOT, "beans", "%s.md" % PAGE)
    before = open(bean, encoding="utf-8").read()
    changed = []
    for key, data, text in (("view", new_view, yaml_view(new_view)), ("views", new_views, yaml_views(new_views)),
                            ("view_bindings", new_binds, yaml_bindings(new_binds))):
        if _plain_data(data) == _plain_data(page().get(key)):
            continue
        allow = sorted(dmsafe.leaf_paths({key: _plain_data(page().get(key))}))
        dmsafe.replace_block(bean, key, text, allow_remove=allow)
        changed.append(key)
    _FM.clear()
    got = page()
    for key, data in (("view", new_view), ("views", new_views), ("view_bindings", new_binds)):
        if key in changed and _plain_data(got.get(key)) != _plain_data(data):
            open(bean, "w", encoding="utf-8", newline="\n").write(before)     # the file as it was, byte for byte
            raise SystemExit("dmview: `%s` did not read back as the selection intended — restored, nothing written" % key)
    if not changed:
        return "nothing to write: the selection says what the page already says"
    e, _w = check()
    if e:
        print("dmview: WARNING — the written page does not pass check:\n  - " + "\n  - ".join(e), file=sys.stderr)
    who = who or subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT).stdout.strip() or "dmview"
    what = "the page [[%s]] written from an author-mode selection" % PAGE
    body = ("- action: `dmview import %s` wrote %s of [[%s]] through dmsafe, read back as intended.\n"
            "- order: %s" % (os.path.basename(path), ", ".join("`%s`" % c for c in changed), PAGE, " → ".join(order)))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "bin", "dmjournal.py"), who, what, "--body", body],
                       capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit("dmview: written, and the journal refused the entry: %s" % (r.stdout + r.stderr).strip())
    return r.stdout.strip() or what


def elements(key):
    figs = compose_all()
    if key not in figs:
        raise NoPage("the drawing module has no drawing %r (it has %s)" % (key, ", ".join(sorted(figs))))
    return figs[key][4]
