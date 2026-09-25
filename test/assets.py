#!/usr/bin/env python3
"""The assets collection: what a release ships beside the law, read by one reader, and admitted only under rule 5.

An ASSET is a directory of the release named for a profile the law offers (`assets/<profile>/`): the code, the
templates and the guide that make the profile's facts useful. Opting into the profile is what brings the asset, and
leaving the profile takes it away. This holds:

  the one reader   seed/LANGUAGE is read by bin/dmpass.py alone: its lines without a profile give, over this release,
                   exactly the files the old per-line glob gave; a line naming `<profile>` gives an opted-in garden the
                   asset, takes it away from one that leaves, and never claims a garden's own file beside it; and every
                   tool and suite that opens seed/LANGUAGE hands its text to that reader
  rule 5           NO ASSET OPENS A CONCEPT OF ITS OWN, checked where it can be, for every profile that names an asset:
                   1. every assets/<d>/ is a profile the law offers, whose head term is named <d>;
                   2. in a garden, every term of the profile sits on the bean that carries its head term — the one
                      thing the gate cannot refuse — and a term written anywhere else is found;
                   3. every registry only the profile reads is named <d>_*, is read by one of its terms, and shares no
                      key value with another registry of the law;
                   4. no name the profile adds is a name the law gives another sense — found by reading the law, and
                      each name used in the law's own sense said so, with why;
                   5. the profile adds no schema-language key and no domain the language does not offer;
                   6. every term and every registry of the profile has its reason in seed/RATIONALE.md, keyed by its
                      path, naming the constructs of the law it is built from.
                   Whether a term states a new kind of fact about the world is not mechanical: that is the ratifier's
                   judgment, made where every change to the law is made. These checks hand the ratifier each new name
                   and the construct it stands on.
"""
import glob, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmparse, dmpass
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)


def read(rel):
    with open(os.path.join(ROOT, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read()


LAW = dmparse.loads(dmparse.split_front_matter(read("seed/std-vocab.md"))[0]) or {}
LINES = dmpass.language(read("seed/LANGUAGE"))
OFFERED = dmpass.offered(LAW)
FILES = [f for f in dmpass.tracked(ROOT) if os.path.isfile(os.path.join(ROOT, *f.split("/")))]

# ------------------------------------------------------------------ the one reader
# THE SAME FILES AS BEFORE. The lines that name no profile were read with a glob by germination and the upgrade, and
# matched with `*` crossing `/` by the keeper and the gate; the one reader matches every line the second way. Over this
# release both give one set, so moving every reader onto it changes nothing a garden receives.
_plain = [l for l in LINES if dmpass.PLACE not in l]
_globbed = sorted({os.path.relpath(f, ROOT).replace(os.sep, "/") for p in _plain for f in glob.glob(os.path.join(ROOT, p))
                   if os.path.isfile(f)} & set(FILES))
_read = dmpass.received(FILES, _plain, (), OFFERED)
check(f"the one reader gives, for the lines that name no profile, exactly the files a glob of each gave "
      f"({len(_read)} files)", len(_read) > 60 and _read == _globbed,
      f"only glob: {sorted(set(_globbed) - set(_read))[:5]}; only the reader: {sorted(set(_read) - set(_globbed))[:5]}")

# A PROFILE'S LINE, read both ways, on a tree built for the purpose: the asset of a profile the garden extends arrives;
# leaving the profile takes it away (what the release keeps, less what the garden now receives); a garden's own file
# beside the assets is never the release's; a profile the law does not offer brings nothing.
_lines = ["bin/dm*.py", "assets/%s/*" % dmpass.PLACE]
_tree = ["bin/dmcheck.py", "assets/alpha/bin/tool.py", "assets/alpha/lib/deep/part.py", "assets/beta/README.md",
         "assets/logo.png", "assets/gamma/x.py"]
_offer = ["alpha", "beta"]
_in = dmpass.received(_tree, _lines, ["alpha"], _offer)
_out = dmpass.received(_tree, _lines, [], _offer)
_have = dmpass.kept(_tree + ["assets/logo.png"], _lines, _offer)
check("a garden extending a profile receives its asset, `*` crossing `/`, and no other profile's",
      _in == ["assets/alpha/bin/tool.py", "assets/alpha/lib/deep/part.py", "bin/dmcheck.py"], _in)
check("...and leaving it, the asset is what the release keeps and the garden no longer receives: it is taken away",
      sorted(set(_have) - set(_out)) == ["assets/alpha/bin/tool.py", "assets/alpha/lib/deep/part.py",
                                         "assets/beta/README.md"], sorted(set(_have) - set(_out)))
check("...a garden's own assets/logo.png, and the directory of a profile the law does not offer, are never the release's",
      "assets/logo.png" not in _have and "assets/gamma/x.py" not in _have
      and "assets/gamma/x.py" not in dmpass.received(_tree, _lines, ["gamma"], _offer), _have)
check("...and the keeper of the layer map reads the same line: a file of a profile's asset is kept by the release",
      dmpass.expand(_lines, _offer) == ["bin/dm*.py", "assets/alpha/*", "assets/beta/*"], dmpass.expand(_lines, _offer))

# EVERY READER ASKS IT. A file of the release that opens seed/LANGUAGE hands the text to dmpass.language; none splits it,
# and none globs its lines, on its own.
_opens = re.compile(r"""join\([^\n]*['"]LANGUAGE['"]|open\([^\n]*seed/LANGUAGE""")
_own = [f for f in FILES if f.endswith(".py") and f != "bin/dmpass.py" and _opens.search(read(f))
        and not re.search(r"\b_?dmpass\.language\(", read(f))]
check("every tool and suite that opens seed/LANGUAGE reads it through bin/dmpass.py, and none on its own", not _own, _own)

# ------------------------------------------------------------------ rule 5
import dmform, dmwhy
ASSETS = sorted(d for d in os.listdir(os.path.join(ROOT, "assets"))
                if os.path.isdir(os.path.join(ROOT, "assets", d))) if os.path.isdir(os.path.join(ROOT, "assets")) else []
PROFILES = LAW.get("profiles") or {}
# THE PROFILES THAT BRING AN ASSET: a directory under assets/, or a profile whose meaning says it has one. Read from the
# release and the law; no profile is named here.
NAMING = sorted(p for p, v in PROFILES.items() if isinstance(v, dict) and f"`assets/{p}/`" in str(v.get("meaning") or ""))
ASSETED = sorted(set(ASSETS) | set(NAMING))


def terms_of(p):
    return [t for t in (PROFILES.get(p) or {}).get("terms") or [] if isinstance(t, dict) and t.get("term")]


# 1. EVERY ASSET IS A PROFILE'S, AND BEARS ITS NAME.
_bad1 = [d for d in ASSETS if d not in OFFERED or d not in {t["term"] for t in terms_of(d)}]
check(f"1. every assets/<d>/ is a profile the law offers, whose head term is named <d> ({', '.join(ASSETS) or 'none yet'})",
      not _bad1, _bad1)
check("...and the profiles that bring an asset are found: at least one names it", len(ASSETED) >= 1, ASSETED)


def keys_of(t):
    return {str(t["term"])} | {str(c).split(".")[0].split("[")[0] for c in (t.get("context_keys") or [])
                               if isinstance(c, str) and "*" not in c and "/" not in c}


def off_head(docs, profile):
    """[(document, key)] — a key of the profile's terms written on a document that does not carry the head term."""
    keys = set().union(*(keys_of(t) for t in terms_of(profile))) - {profile}
    return [(name, k) for name, fm in sorted(docs.items()) if isinstance(fm, dict) and profile not in fm
            for k in sorted(keys & set(fm))]


# 2. IN A GARDEN, THE PROFILE'S TERMS SIT ON THE BEAN THAT CARRIES ITS HEAD TERM. The schema language cannot say "only on
# the bean that carries another term", so the gate passes a term written elsewhere; this finds it, in a garden grown
# here with a page of the smallest shape each asset's profile accepts, and then with one term moved onto a being.
import shutil, tempfile


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)


def front(path):
    return dmparse.loads(dmparse.split_front_matter(open(path, encoding="utf-8").read())[0] or "") or {}


def documents(g):
    return {f"{d}/{n}": front(os.path.join(g, d, n)) for d in ("beans", "mappings")
            for n in sorted(os.listdir(os.path.join(g, d))) if n.endswith(".md")}


_T = tempfile.mkdtemp(prefix="dmassets-")
_G = os.path.join(_T, "garden-a")
_r = run(sys.executable, os.path.join(ROOT, "seed", "germinate.py"), _G, "--gardener", "sam", cwd=_T)
_v = os.path.join(_G, "VOCAB.md")
with open(_v, encoding="utf-8") as fh:
    _vt = fh.read()
with open(_v, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(_vt.replace("local_terms: []", "extends_profiles: [%s]\nlocal_terms: []" % ", ".join(ASSETED), 1))
_PAGE = """---
bean: sam-page
genos: service
title: "Sam's page"
status: active
summary: "A page of one drawing."
nature: lekton
identity: { status: confirmed, anchors: [ { key: service_id, value: "service:sam-page", class: logical, establishing: true } ] }
provenance: { src: asserted-by-human, by: "sam (gardener)", as_of: 2026-01-01 }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
view:
  drawings: file:bin/drawings.py
views:
  kept:
    draws: { bean: sam }
    purpose: "Keeps the garden."
    outcome: "The garden is kept."
    stages: [ { label: "keep it", doer: "sam" } ]
    questions: [ { lens: orient, ask: "Who keeps it?" } ]
    archetype: health-chain
    blind: [ { what: "nothing is measured", why: "no monitor is recorded" } ]
---
A page of one drawing.
"""
os.makedirs(os.path.join(_G, "bin"), exist_ok=True)
with open(os.path.join(_G, "bin", "drawings.py"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("COMPOSERS = {}\n")
with open(os.path.join(_G, "beans", "sam-page.md"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(_PAGE)
_gate = run(sys.executable, os.path.join(_G, "bin", "dmcheck.py"), "--all", cwd=_G)
_off = [x for p in ASSETED for x in off_head(documents(_G), p)]
check("2. in a garden, a page of the smallest shape passes the gate, and every term of the profile sits on the bean "
      "that carries its head term", _r.returncode == 0 and _gate.returncode == 0 and not _off,
      (_gate.stdout + _gate.stderr)[-500:] + str(_off))
_sam = os.path.join(_G, "beans", "sam.md")
with open(_sam, encoding="utf-8") as fh:
    _st = fh.read()
_moved = _PAGE.split("views:\n", 1)[1].split("---", 1)[0]
with open(_sam, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(_st.replace("provenance:", "views:\n" + _moved + "provenance:", 1))
_gate = run(sys.executable, os.path.join(_G, "bin", "dmcheck.py"), "--all", cwd=_G)
_off = [x for p in ASSETED for x in off_head(documents(_G), p)]
check("...and a term moved onto a being passes the gate, and is found here, named", _gate.returncode == 0
      and ("beans/sam.md", "views") in _off, (_gate.stdout + _gate.stderr)[-300:] + str(_off))
shutil.rmtree(_T, ignore_errors=True)


# 3. A REGISTRY ONLY THE PROFILE READS IS THE PROFILE'S, AND SAYS SO.
def registries_read(terms):
    out = set()

    def walk(attrs):
        for rec in (attrs or {}).values():
            if not isinstance(rec, dict):
                continue
            f, rule = dmform._domain(rec.get("in"))
            if f == "registry" and isinstance(rule, dict) and rule.get("registry"):
                out.add(rule["registry"])
            if f == "entries":
                walk(rule)
    for t in terms:
        walk(((t.get("schema") or {}).get("attrs")))
    return out


_core = list(LAW.get("terms") or [])


def key_column(rows):
    first = next((r for r in rows if isinstance(r, dict)), None)
    return next(iter(first), None) if first else None


def registry_keys():
    """{registry: {key values}} — every registry of the law: its top-level tables and the data files it points at."""
    out = {}
    for k, v in LAW.items():
        if isinstance(v, list) and v and all(isinstance(r, dict) for r in v):
            col = key_column(v)
            out[k] = {str(r.get(col)) for r in v if r.get(col) is not None}
    for rf in LAW.get("registry_files") or []:
        path = os.path.join(ROOT, *str(rf.get("file")).split("/"))
        if os.path.isfile(path):
            lines = [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8") if l.strip()]
            head = lines[0] if lines else []
            i = head.index(rf.get("key")) if rf.get("key") in head else 0
            out[rf["registry"]] = {row[i] for row in lines[1:] if len(row) > i}
    return out


import json
REG_KEYS = registry_keys()


def used_elsewhere(name, profile):
    """True when the law names the table anywhere but in the profile and in the table itself: as a registry an attribute
    takes, the rows a name is looked up in, a data file, a link between tables."""
    rest = {k: v for k, v in LAW.items() if k not in (name, "profiles")}
    rest["profiles"] = {q: v for q, v in PROFILES.items() if q != profile}
    return re.search(r'(?<![\w-])%s(?![\w-])' % re.escape(name), json.dumps(rest, default=str)) is not None


_bad3 = []
for _p in ASSETED:
    _mine = registries_read(terms_of(_p))
    _own = sorted(r for r in LAW if r.startswith(_p + "_") and isinstance(LAW[r], list))
    for _r in sorted(_mine):
        if not _r.startswith(_p + "_") and not used_elsewhere(_r, _p):
            _bad3.append(f"{_p}: {_r} is a table the law uses nowhere else, and is not named {_p}_*")
    for _r in _own:
        if _r not in _mine:
            _bad3.append(f"{_p}: {_r} is read by none of its terms")
        _shared = {q: REG_KEYS[_r] & REG_KEYS[q] for q in REG_KEYS if q != _r and REG_KEYS[_r] & REG_KEYS[q]}
        if _shared:
            _bad3.append(f"{_p}: {_r} shares key values with {_shared}")
check("3. every registry only the profile reads is named <d>_*, is read by one of its terms, and shares no key value "
      "with another registry of the law", not _bad3, _bad3)
# ...and the check sees one where there is one: a registry of technologies kept by the profile shares `prometheus`.
_probe = dict(REG_KEYS, **{"x_sources": {"prometheus"}})
check("...and it sees one: a profile's own list of sources, keyed by a technology the catalogue has, shares a key",
      bool(_probe["x_sources"] & _probe.get("technology", set())), sorted(_probe.get("technology", set()))[:5])


# 4. NO NAME IS GIVEN A SECOND SENSE. The names the law uses, read from it: its terms, its tables, the rows of the tables
# a name is looked up in, the names it retired, and the sense each attribute name has in every term outside the profile.
def senses_of(terms):
    out = {}

    def dom(rec):
        f, r = dmform._domain(rec.get("in")) if isinstance(rec, dict) else (None, None)
        return ("registry:" + str(r.get("registry") or r.get("registry_from"))) if f == "registry" else \
               ("type:" + str(r)) if f == "type" else str(f)

    def walk(attrs, where):
        for n, rec in (attrs or {}).items():
            out.setdefault(str(n), set()).add((dom(rec), where))
            i = rec.get("in") if isinstance(rec, dict) else None
            if isinstance(i, dict) and isinstance(i.get("entries"), dict):
                walk(i["entries"], where)
    for t in terms:
        walk((t.get("schema") or {}).get("attrs"), t["term"])
    return out


def law_names(except_profile):
    names = {str(t["term"]) for t in _core + [t for q in PROFILES if q != except_profile for t in terms_of(q)]}
    names |= {k for k, v in LAW.items() if isinstance(v, list) and v and isinstance(v[0], dict)}
    for reg, col in (("quantities", "quantity"), ("units", "unit"), ("aspects", "aspect"), ("figures", "figure"),
                     ("gene", "genos"), ("roles", "role")):
        names |= {str(r.get(col)) for r in LAW.get(reg) or [] if isinstance(r, dict)}
    names |= {str(r.get("name")) for r in LAW.get("retired") or [] if isinstance(r, dict)}
    return names


# A NAME USED IN THE LAW'S OWN SENSE, and why — the ratifier's judgment, written down. Found by reading the law; listed
# here only once judged, and a judgment the law no longer calls for fails as stale.
SAME_SENSE = {
    "title": "prose: the name a reader sees, as a bean's `title` is",
    "tool": "the executable a host runs, named by the host, as a mapping's `tool` is",
}


def findings(p):
    other = senses_of(_core + [t for q in PROFILES if q != p for t in terms_of(q)])
    names = law_names(p)
    mine = senses_of(terms_of(p))
    out = []
    for t in terms_of(p):
        if t["term"] in names:
            out.append((t["term"], "a term the law already declares"))
    for n, ss in sorted(mine.items()):
        doms = {d for d, _w in ss}
        lawdoms = {d for d, _w in other.get(n, set())}
        taken = {d[len("registry:"):] for d in doms if d.startswith("registry:")}
        if n in names and n not in other:
            # a name the law uses for a table, a term or a row: the same sense only where this attribute takes a row of
            # that very table, or of the table whose rows the name is the key of
            if not any(n == r or n == key_column(REG_ROWS.get(r, [])) for r in taken):
                out.append((n, "a name the law uses (a term, a table or a row)"))
        elif lawdoms and not doms <= lawdoms:
            out.append((n, f"the law has it as {sorted(lawdoms)}, the profile as {sorted(doms)}"))
    return out


REG_ROWS = {k: v for k, v in LAW.items() if isinstance(v, list)}
for rf in LAW.get("registry_files") or []:
    REG_ROWS.setdefault(rf["registry"], [{rf.get("key"): None}])
_bad4, _judged = [], set()
for _p in ASSETED:
    for _n, _why in findings(_p):
        if _n in SAME_SENSE:
            _judged.add(_n)
        else:
            _bad4.append(f"{_p}.{_n}: {_why}")
check("4. no name a profile with an asset adds is a name the law gives another sense", not _bad4, _bad4)
check("...and every name judged to be used in the law's own sense is still a finding: no judgment outlives its cause",
      _judged == set(SAME_SENSE) if ASSETED else True, sorted(set(SAME_SENSE) - _judged))
_probe_terms = [{"term": "x_page", "schema": {"attrs": {"level": {"in": "prose"}, "of": {"in": "bean_id"},
                                                         "source": {"in": {"registry": "x_sources", "take": "x"}}}}}]
_saved = PROFILES.get("x")
PROFILES["x"] = {"terms": _probe_terms}
_pf = [n for n, _w in findings("x")]
if _saved is None:
    del PROFILES["x"]
check("...and it sees one: `level` (a quantity), `of` (prose in the law) and `source` (prose in the law) are found",
      set(_pf) >= {"level", "of", "source"}, _pf)

# 5. NO SCHEMA-LANGUAGE KEY AND NO DOMAIN OF ITS OWN.
_lang = set(LAW.get("schema_language") or {})
_bad5 = []
for _p in ASSETED:
    for _t in terms_of(_p):
        _s = _t.get("schema") or {}
        _bad5 += [f"{_p}.{_t['term']}: schema key `{k}`" for k in sorted(set(_s) - _lang)]
        _bad5 += [f"{_p}.{_t['term']}: attribute `{a}` states a domain the language does not offer"
                  for a in dmform.attribute_form(_t["term"], _s)["unknown"]]
check("5. a profile with an asset adds no schema-language key and no domain the language does not offer", not _bad5, _bad5)

# 6. EVERY TERM AND REGISTRY HAS ITS REASON, KEYED BY ITS PATH, NAMING WHAT IT IS BUILT FROM.
_why = dmwhy.rationale()
_constructs = _lang | set((LAW.get("schema_language") or {}).get("attr_domains") or {}) | set(LAW) | \
              {str(t["term"]) for t in _core}
_bad6 = []
for _p in ASSETED:
    _paths = [f"profiles.{_p}.terms[{t['term']}]" for t in terms_of(_p)] + \
             sorted(r for r in LAW if r.startswith(_p + "_") and isinstance(LAW[r], list))
    for _k in _paths:
        _hit = [v for k, v in _why.items() if k == _k or k.startswith(_k + ".")]
        if not _hit:
            _bad6.append(f"{_k}: no reason keyed by its path")
        elif not any(set(re.findall(r"`([a-z][a-z0-9_:-]*)`", v)) & _constructs for v in _hit):
            _bad6.append(f"{_k}: its reason names no construct of the law")
check("6. every term and registry of a profile with an asset has its reason in seed/RATIONALE.md, keyed by its path, "
      "naming the law's constructs it is built from", not _bad6 and not dmwhy.orphans(), _bad6 + dmwhy.orphans())

print("\nassets: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
