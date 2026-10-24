#!/usr/bin/env python3
"""knowledge — the one finder: read the knowledge the law points at, and the schemes a garden holds as its own.

Published classifications are UNIVERSAL ANCHORS: ISCED-F 2013 fields of knowledge, ISCO-08 occupations, a curated
catalogue of established technologies, and every scheme a garden declares in its VOCAB.md — shipped in seed/knowledge/,
held as the garden's own extract in extracts/, or held at its authority (`knowledge_scheme_form.holding`). The schemes
and their files are read from `knowledge_schemes` and `registry_files`, the law's and the garden's, exactly as the gate
reads them, so this tool can never read a different file than the law declares. It writes nothing: it offers
candidates, and a person picks the code (a model's pick is `inferred`).

    python3 bin/knowledge.py show isco-08 2522          # one code, its ancestry, and what it links to
    python3 bin/knowledge.py tree isced-f-2013 06       # a subtree, by `parent`
    python3 bin/knowledge.py find tile setter [--scheme S]   # candidates ranked, each with its ancestry
    python3 bin/knowledge.py label <scheme> <code> <language>   # a label in another language, with its attribution
    python3 bin/knowledge.py at <position>              # COMPUTED anchors (bin/where.py): the cells it is in, its nearest
    python3 bin/knowledge.py gold <file.tsv>            # recall@k of `find` against a gold set a person chose
    python3 bin/knowledge.py resolve <scheme> <code>    # a lookup at the authority — refused until the flow law grants it
    python3 bin/knowledge.py bean <bean-id>             # a bean's `knowledge:` entries, resolved
    python3 bin/knowledge.py crosswalk 2522             # the fields an occupation draws on
    python3 bin/knowledge.py propose <bean>             # codes for a being: by its kind's level, from its title
    python3 bin/knowledge.py propose --level organ heart [--wikidata <party>]   # … for words at a level; with
                                                        # --wikidata, Wikidata's items picked by their class too, sent
                                                        # only to a party the garden's flow law grants

`propose` reads only the schemes whose `at` names the being's level — no taxon is proposed for a host — and, of a
scheme of millions, streams its rows; `find` passes such schemes over unless one is named.

In a garden of the core (v1 part 7) the schemes are core/law/registries.yaml's and the garden's own rows `schemes` and
`files` in its VOCAB.md, and a bean's codes are its statements: each `classify`, and each `use` of a code.

As a library, for a program built on a garden: `Knowledge(root)` with `.schemes`, `.row(scheme, code)`,
`.ancestry(scheme, code)`, `.label(scheme, code, language)`, `.find(words, scheme=None)`, `.resolve(entry)` and
`.for_bean(front_matter)`.
"""
import os, re, sys, csv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse as dmparse

# The rows of the flow law this tool checks, and the fixture that shows it (`bin/pass.py --flows` computes the guard).
GUARDS = {
    'sent-out': {'checks': "a lookup at a remote authority is refused until the gardener grants that party",
                 'proof': 'test/observations.py', 'label': "O-5 a lookup at the authority is REFUSED until the flow law grants that party"},
}


class NotGranted(Exception):
    """A lookup at a scheme's authority leaves the garden: it is refused until the flow law grants that party."""


def _fm(path):
    """A document's front matter as a mapping: {} where it is absent or does not read as one — the gate says why."""
    try:
        fm = dmparse.loads(dmparse.read(path)[0]) or {}
    except Exception:                      # noqa: BLE001 — unread, not a value: the gate names the file and why
        return {}
    return fm if isinstance(fm, dict) else {}


def _words(text):
    return re.findall(r"[a-z0-9]+", str(text).lower())


def _listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def _said(text):
    """A name as it is compared whole: its case, its hyphens and its spacing aside, and its last word's English plural
    (`pulleys`, `ball bearings`, `assemblies` — never `brass`), as a catalogue of goods writes its names."""
    words = re.sub(r"[-_‐–]", " ", str(text)).lower().split()
    if words and len(words[-1]) > 3 and words[-1].endswith("s") and not words[-1].endswith(("ss", "us", "is")):
        w = words[-1]
        words[-1] = w[:-3] + "y" if w.endswith("ies") else w[:-1]
    return " ".join(words)


def _sorted_has(path, code):
    """True when `code` is a line of `path`, a file of lines sorted by their bytes: a binary search over the file, never
    a read of it."""
    import mmap
    key = str(code).encode("utf-8")
    with open(path, "rb") as fh:
        if os.fstat(fh.fileno()).st_size == 0:
            return False
        m = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            lo, hi = 0, len(m)
            while lo < hi:
                mid = (lo + hi) // 2
                start = m.rfind(b"\n", 0, mid) + 1
                end = m.find(b"\n", start)
                end = len(m) if end < 0 else end
                line = m[start:end]
                if line == key:
                    return True
                if line < key:
                    lo = end + 1
                else:
                    hi = start
            return False
        finally:
            m.close()


def _reads(k, scheme):
    """True when this machine can read `scheme`'s rows: its file, or a copy fetched from its provider."""
    if (k.schemes.get(scheme) or {}).get("holding") == "fetched":
        import fetch as dmfetch
        return bool(dmfetch.current(scheme))
    d = k.decl.get(scheme) or {}
    return bool(d.get("file")) and os.path.isfile(os.path.join(k.root, d["file"]))


BIG = 300000                                   # rows past which a scheme is streamed for a name, never held whole


def _big(k, scheme):
    """True when the copies of a fetched scheme read here hold more than BIG rows (their fetched.json)."""
    if (k.schemes.get(scheme) or {}).get("holding") != "fetched" or scheme in k._rows:
        return False
    import json
    import fetch as dmfetch
    n = 0
    for p in dmfetch.current(scheme):
        try:
            with open(os.path.join(os.path.dirname(p), "fetched.json"), encoding="utf-8") as fh:
                n += int(json.load(fh).get("rows") or 0)
        except (OSError, ValueError):
            return True
    return n > BIG


# ------------------------------------------------------------------------------------------------ Wikidata, an item a time
UA = "daftar-knowledge (the one finder, proposing a code for a person to pick; https://github.com/0mit/daftar)"
_LAST = [0.0]


def web_get(api):
    """A reader of the authority's API at `api`: a request at most once a second, its User-Agent naming daftar."""
    import json, time, urllib.parse, urllib.request

    def get(params):
        wait = 1.0 - (time.monotonic() - _LAST[0])
        if wait > 0:
            time.sleep(wait)
        url = api + "?" + urllib.parse.urlencode(sorted(dict(params, format="json").items()))
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                return json.load(r)
        finally:
            _LAST[0] = time.monotonic()
    return get


def _claims(entity, prop):
    out = []
    for c in ((entity or {}).get("claims") or {}).get(prop, []):
        v = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value")
        out.append(v.get("id") if isinstance(v, dict) else v)
    return [v for v in out if isinstance(v, str)]


def items_at(get, row, words, level, limit=10, depth=12):
    """[(item, label, description, class)]: the items the authority's search gives for `words`, in its order, whose
    classes — `instance_of` once, then `subclass_of` any number of times (the scheme's `lookup`) — reach a code its
    `classes` names for `level`: an item is picked by its class, never by its label. Each with its claims, in
    `entity`."""
    look = row.get("lookup") or {}
    wanted = {c for x in _listed(row.get("classes")) if isinstance(x, dict) and x.get("level") == level
              for c in _listed(x.get("codes"))}
    hits = get({"action": "wbsearchentities", "search": words, "language": "en", "uselang": "en", "type": "item",
                "limit": limit}).get("search", [])
    cands = [h["id"] for h in hits if isinstance(h, dict) and h.get("id")]
    if not cands or not wanted:
        return []
    ents, classes = {}, {}

    def load(ids):
        need = sorted({i for i in ids if i not in classes})
        for k in range(0, len(need), 50):
            got = get({"action": "wbgetentities", "ids": "|".join(need[k:k + 50]), "props": "claims|labels|descriptions",
                       "languages": "en"}).get("entities", {})
            for i, e in got.items():
                ents[i] = e
                classes[i] = (_claims(e, look.get("instance_of")), _claims(e, look.get("subclass_of")))
        for i in need:
            classes.setdefault(i, ([], []))

    load(cands)
    reached = {}
    front = [(c, n) for c in cands for n in classes[c][0] + classes[c][1]]
    seen = {c: set() for c in cands}
    for _ in range(depth):
        front = [(c, n) for c, n in front if c not in reached and n not in seen[c]]
        if not front:
            break
        for c, n in front:
            seen[c].add(n)
        load([n for _c, n in front])
        nxt = []
        for c, n in front:
            if c in reached:
                continue
            if n in wanted:
                reached[c] = n
            else:
                nxt += [(c, m) for m in classes[n][1]]
        front = nxt
    out = []
    for c in cands:
        if c in reached:
            e = ents.get(c) or {}
            out.append({"item": c, "label": ((e.get("labels") or {}).get("en") or {}).get("value", ""),
                        "description": ((e.get("descriptions") or {}).get("en") or {}).get("value", ""),
                        "class": reached[c], "entity": e})
    return out


def _runs_core(root):
    """True in a garden that runs the core (GARDEN.md pins `core@…`, bin/check.py the one reader of the pin)."""
    import check
    return check.runs_core(check.pin(root))


def _core_law(root):
    """The schemes and the files of the core's law (core/law/registries.yaml): the garden's copy, else this release's."""
    for d in (root, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))):
        p = os.path.join(d, "core", "law", "registries.yaml")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                return dmparse.loads(fh.read()) or {}
    return {}


def core_entries(root, bean):
    """A bean of the core's codes as `knowledge:` entries: each `classify` (`classified_as`) and each `use` of a code
    (`uses`), read from its statements (v1 part 7)."""
    sys.path.insert(0, root)
    from core import engine
    G = engine.Garden.read(root)
    b = G.beans.get(bean)
    if b is None or b.unread:
        return []
    out = []
    for _i, verb, r in b.items:
        if "held" in r:
            continue
        if verb == "classify" and isinstance(r.get("as"), str):
            out.append({"code": r["as"], "rel": "classified_as"})
        elif verb == "use":
            for c in (r.get("of") if isinstance(r.get("of"), list) else [r.get("of")]):
                if isinstance(c, str) and dmparse.split_coding(c)[0]:
                    out.append({"code": c, "rel": "uses"})
    return out


class Knowledge:
    def __init__(self, root, law=None):
        """`law`: the law's `registry_files` and `knowledge_schemes` where a caller has read them already (the core
        reads them from core/law/registries.yaml); else they are read there."""
        self.root = root
        if law is None:
            law = _core_law(root)
        garden = _fm(os.path.join(root, "VOCAB.md"))
        adds = garden.get("registry_additions") or {}
        # A GARDEN'S OWN SCHEMES AND THEIR FILES: today's `registry_additions.knowledge_schemes` and `registry_files`, or
        # the core's rows `schemes` and `files` (v1 part 7) — one row a name, as the law reads them
        self.decl = {r["registry"]: r for r in list(law.get("registry_files") or []) + list(garden.get("registry_files") or [])
                     + list(garden.get("files") or []) if isinstance(r, dict) and r.get("registry")}
        self.schemes = {r["scheme"]: r for r in list(law.get("knowledge_schemes") or []) + list(adds.get("knowledge_schemes") or [])
                        + list(garden.get("schemes") or []) if isinstance(r, dict) and r.get("scheme")}
        self._rows = {}

    def rows(self, registry):
        if registry not in self._rows:
            d = self.decl.get(registry)
            if not d:
                raise KeyError("no registry %r is declared in registry_files, the law's or this garden's" % registry)
            path = os.path.join(self.root, d["file"]) if d.get("file") else None   # none: no release carries a copy
            if path and not os.path.isfile(path):          # a table of the law this tree carries none of (a garden in
                mine = os.path.join(os.path.dirname(HERE), d["file"])   # today's words, read by this release's law):
                path = mine if os.path.isfile(mine) else path           # the release's own, beside this tool
            paths = [path]
            if (self.schemes.get(registry) or {}).get("holding") == "fetched":     # this machine's newest copy of the
                import fetch as dmfetch                                            # provider's own — of each part, for a
                got = dmfetch.current(registry)                                    # scheme in parts — else the release's
                host = ((self.schemes.get(registry) or {}).get("fetch") or {}).get("host")
                if got:
                    paths = got
                elif (not path or not os.path.isfile(path)) and host and os.path.isfile(host):
                    # THE PROVIDER'S FILE AS THE MACHINE INSTALLED IT (`fetch.host`): read by the scheme's reader,
                    # unchanged and kept nowhere, where this machine has fetched none
                    self._rows[registry] = dmfetch.read_host(registry, host)
                    return self._rows[registry]
                elif not path or not os.path.isfile(path):
                    raise KeyError("%s is fetched from its provider, and this machine has fetched none: python3 "
                                   "bin/fetch.py %s" % (registry, registry))
            elif not path:
                raise KeyError("the registry %s names no file, and is no scheme fetched from its provider" % registry)
            self._rows[registry] = []
            for path in paths:
                with open(path, encoding="utf-8") as fh:
                    if d.get("format") == "yaml":
                        self._rows[registry] += [r for r in (dmparse.loads(fh.read()) or []) if isinstance(r, dict)]
                    else:
                        self._rows[registry] += list(csv.DictReader(fh, delimiter="\t"))
        return self._rows[registry]

    def held(self, scheme):
        """The schemes whose codes this garden can read: shipped or extracted, with a file declared."""
        return scheme in self.schemes and scheme in self.decl and self.schemes[scheme].get("holding") != "at-authority"

    def row(self, scheme, code):
        key = self.decl.get(scheme, {}).get("key", "code")
        return next((r for r in self.rows(scheme) if r.get(key) == str(code)), None)

    def has(self, scheme, code):
        """True when `code` is a code of `scheme`. Of a fetched scheme whose every copy read here keeps its codes sorted
        (bin/fetch.py, `codes.txt`), by a binary search in them, never by reading its rows; else among its rows."""
        if (self.schemes.get(scheme) or {}).get("holding") == "fetched" and scheme not in self._rows:
            import fetch as dmfetch
            files = [os.path.join(os.path.dirname(p), "codes.txt") for p in dmfetch.current(scheme)]
            if files and all(os.path.isfile(f) for f in files):
                return any(_sorted_has(f, code) for f in files)
        return self.row(scheme, code) is not None

    # ------------------------------------------------------------------------------------------ the beings' finder
    def at_level(self, level):
        """The schemes whose codes classify beings at `level` (their `at`), by name."""
        return [s for s, r in sorted(self.schemes.items()) if level in [str(x) for x in _listed(r.get("at"))]]

    def _stream(self, scheme):
        """Each row of `scheme`, as it is read: a fetched scheme's copies line by line, never held whole."""
        if (self.schemes.get(scheme) or {}).get("holding") == "fetched" and scheme not in self._rows:
            import fetch as dmfetch
            paths = dmfetch.current(scheme)
            if paths:
                for p in paths:
                    with open(p, encoding="utf-8", newline="") as fh:
                        head = fh.readline().rstrip("\r\n").split("\t")
                        for line in fh:
                            cells = line.rstrip("\r\n").split("\t")
                            yield dict(zip(head, cells))
                return
        yield from self.rows(scheme)

    def named(self, queries, schemes):
        """{query: [(scheme, row, how)]}: the rows of `schemes` whose name (`how` = `name`), an exact synonym
        (`synonym`) or another synonym (`related`) is a query as a whole, its case, hyphens and spacing aside — each
        scheme read once for every query, row by row. A scheme this machine cannot read is passed over."""
        want = {_said(q): q for q in queries}
        out = {q: [] for q in queries}
        for s in schemes:
            if not self.held(s):
                continue
            try:
                for r in self._stream(s):
                    for how, cell in (("name", "name"), ("name", "name_en"), ("synonym", "synonyms"),
                                      ("related", "related")):
                        text = r.get(cell)
                        if not text:
                            continue
                        for one in (text.split(" | ") if how != "name" else [text]):
                            q = want.get(_said(one))
                            if q is not None:
                                out[q].append((s, r, how))
            except KeyError:                       # a scheme fetched from its provider, which this machine has not
                continue
        rank = {"name": 0, "synonym": 1, "related": 2}
        for q in out:
            seen, kept = set(), []
            for s, r, how in sorted(out[q], key=lambda t: (rank[t[2]], t[1].get("status") not in ("", "accepted"))):
                key = (s, r.get(self.decl.get(s, {}).get("key", "code")))
                if key not in seen:
                    seen.add(key)
                    kept.append((s, r, how))
            out[q] = kept
        return out

    def code_in(self, scheme, value):
        """The code of `scheme` a value another scheme names it by is (`UBERON:0000948`, `42141500-6`): the value as it
        is, else without a prefix of letters and `:` or `_`, else without a check digit after `-`, the first in the
        form its `code_pattern` gives; None where none is."""
        pat = (self.schemes.get(scheme) or {}).get("code_pattern")
        v = str(value).strip()
        forms = [v, re.sub(r"^[A-Za-z]+[:_]", "", v)]
        forms += [re.sub(r"-[0-9]$", "", f) for f in forms]
        for f in forms:
            if not pat or dmparse.law_match(pat, f):
                return f
        return None

    def propose(self, words, level, get=None, authority="wikidata"):
        """[{coding, name, scheme, how, ...}]: the codes proposed for a being at `level` named by `words` — from each
        scheme held here whose `at` names the level, by its names; and, with `get` (a reader of the authority's API, which
        the caller has been granted), the authority's items picked by their class for the level, and through each the
        codes of the schemes it names (`named_in`), where their `at` names the level. Nothing is written: a person picks."""
        out, seen = [], set()

        def add(p):
            if p["coding"] not in seen:
                seen.add(p["coding"])
                out.append(p)

        for s, r, how in self.named([words], self.at_level(level))[words]:
            key = self.decl.get(s, {}).get("key", "code")
            add({"coding": "%s:%s" % (s, r.get(key)), "name": self.name(r), "scheme": s, "how": how,
                 "level": r.get("level", ""), "status": r.get("status", "")})
        arow = self.schemes.get(authority) or {}
        if get is None or arow.get("holding") != "at-authority":
            return out
        for it in items_at(get, arow, words, level):
            add({"coding": "%s:%s" % (authority, it["item"]), "name": it["label"], "scheme": authority,
                 "how": "class %s" % it["class"], "level": "", "status": it["description"]})
            for s in self.at_level(level):
                for n in _listed(self.schemes[s].get("named_in")):
                    if not isinstance(n, dict) or n.get("scheme") != authority:
                        continue
                    for v in _claims(it["entity"], n.get("property")):
                        code = self.code_in(s, v)
                        if code is None:
                            continue
                        held = self.held(s) and _reads(self, s)
                        if held and not self.has(s, code):
                            continue
                        r = (self.row(s, code) if held and not _big(self, s) else None) or {}
                        add({"coding": "%s:%s" % (s, code), "name": self.name(r), "scheme": s,
                             "how": "%s %s %s" % (authority, it["item"], n.get("property")),
                             "level": r.get("level", ""), "status": "" if held else "not held here"})
        return out

    def ancestry(self, scheme, code):
        """[root, …, code] as rows, following `parent`; [row] for a flat scheme."""
        out, r, seen = [], self.row(scheme, code), set()
        while r and id(r) not in seen:
            seen.add(id(r))
            out.insert(0, r)
            r = self.row(scheme, r.get("parent")) if r.get("parent") else None
        return out

    def name(self, row):
        return (row or {}).get("name_en") or (row or {}).get("name") or ""

    def label(self, scheme, code, lang="en"):
        """(label, attribution): the code's label in `lang` — from a `labels` registry the scheme declares, or a
        `name_<lang>` column — with the words its publisher asks to be printed beside it, verbatim."""
        for l in self.schemes.get(scheme, {}).get("labels") or []:
            if isinstance(l, dict) and l.get("language") == lang and l.get("registry") in self.decl:
                r = next((x for x in self.rows(l["registry"]) if x.get("code") == str(code)), None)
                if r:
                    return r.get("name"), l.get("attribution")
        r = self.row(scheme, code)
        if not r:
            return None, None
        return (r.get("name_%s" % lang) or self.name(r)), None

    def find(self, words, scheme=None, k=None):
        """Candidates for words, ranked: every word found in a code's name or its code, as a word's beginning, first;
        then the share of the words found; then the finer level (a unit before its group); then the shorter name.
        [(score, scheme, row)]."""
        q = _words(words)
        out = []
        for s in ([scheme] if scheme else sorted(self.schemes)):
            if not self.held(s) or (not scheme and self.schemes[s].get("at")):
                continue                           # a scheme of beings at a level is `propose`'s, by its level
            key = self.decl[s].get("key", "code")
            try:
                rows = self.rows(s)
            except KeyError:                       # a scheme fetched from its provider, which this machine has not
                continue
            for r in rows:
                hay = _words(self.name(r)) + _words(r.get(key, ""))
                hit = sum(1 for w in q if any(h.startswith(w) or (len(w) > 3 and h.startswith(w.rstrip("s"))) for h in hay))
                if not hit:
                    continue
                depth = len(self.ancestry(s, r.get(key)))
                out.append(((hit == len(q), hit / len(q), depth, -len(self.name(r))), s, r))
        out.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return out[:k] if k else out

    def resolve(self, entry):
        """A `knowledge:` entry -> {scheme, code, rel, topic, label, path, docs, homepage, fields, occupations}."""
        sch, code = dmparse.split_coding(entry.get("code"))
        r = self.row(sch, code) or {}
        out = {"scheme": sch, "code": code, "rel": entry.get("rel"), "topic": entry.get("topic", ""),
               "label": r.get("name_en") or r.get("name") or "",
               "path": [a.get("name_en") for a in self.ancestry(sch, code)] if sch != "technology" else [r.get("name", "")],
               "docs": r.get("docs", ""), "homepage": r.get("homepage", ""), "category": r.get("category", "")}
        if sch == "technology":
            out["fields"] = [{"code": c, "label": self.label("isced-f-2013", c)[0]} for c in (r.get("isced_f_2013") or "").split(";") if c]
            out["occupations"] = [{"code": c, "label": self.label("isco-08", c)[0]} for c in (r.get("isco_08") or "").split(";") if c]
        return out

    def for_bean(self, fm):
        return [self.resolve(e) for e in (fm.get("knowledge") or []) if isinstance(e, dict)]

    def crosswalk(self, isco):
        return [r for r in self.rows("crosswalk-isco-08-isced-f-2013") if r.get("isco_08") == str(isco)]


def _gold(k, path, at=5):
    """recall@k of `find` against a gold set: rows `query<TAB>scheme<TAB>code` a person chose, `#` lines are comments."""
    rows = [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")]
    rows = [r for r in rows if len(r) >= 3 and r[0] != "query"]
    hit = 0
    for q, s, c in (r[:3] for r in rows):
        top = [(x[1], x[2].get(k.decl[x[1]].get("key", "code"))) for x in k.find(q, k=at)]
        ok = (s, c) in top
        hit += ok
        print("%s  %-32s %s %s%s" % ("hit " if ok else "MISS", q, s, c, "" if ok else "   got: " + ", ".join("%s %s" % t for t in top[:3])))
    print("recall@%d = %d/%d" % (at, hit, len(rows)))


def _at(k, root, position):
    """COMPUTED anchors for a position, never stored — read by bin/where.py, the one reader of a position in either
    dimension: the cells it is in (an age's ICS units, a coordinate's grid cells), what fixes the nearest boundaries,
    and the fixed beings nearest a place."""
    import where as dmwhere
    try:
        a = dmwhere.anchors(position, root=root)
    except ValueError as e:
        print("where: %s" % e); return 1
    print(dmwhere.show(a))
    return 0

def _level_of(root, kind):
    """The level of the law a being of `kind` is at: its row of core/law/kinds.yaml (the garden's copy, else this
    release's), or the garden's own (VOCAB.md `kinds`); None for a sayable."""
    rows = []
    for d in (root, os.path.dirname(HERE)):
        p = os.path.join(d, "core", "law", "kinds.yaml")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                rows = list((dmparse.loads(fh.read()) or {}).get("kinds") or [])
            break
    rows += _listed(_fm(os.path.join(root, "VOCAB.md")).get("kinds"))
    r = next((x for x in rows if isinstance(x, dict) and x.get("kind") == kind), None)
    return (r or {}).get("level")


def _propose(k, root, args, get=None):
    """`propose <bean> | --level <level> <words…> [--wikidata <party>]`: the codes proposed, one a line. A lookup at
    Wikidata sends the words out of the garden: only to a party the garden's flow law grants (`sent-out`, through
    `send`), named by its bean; refused, the held schemes' proposals alone are shown."""
    level, party, words = None, None, []
    it = iter(args)
    for w in it:
        if w == "--level":
            level = next(it, None)
        elif w == "--wikidata":
            party = next(it, None)
        else:
            words.append(w)
    src = "request"
    if level is None:
        if len(words) != 1:
            print(__doc__)
            return 2
        p = os.path.join(root, "beans", words[0] + ".md")
        if not os.path.isfile(p):
            print("knowledge: no bean %s here" % words[0])
            return 1
        fm = _fm(p)
        level = _level_of(root, fm.get("kind"))
        if not level:
            print("knowledge: %s is a %s, at no level of the law: a sayable is classed by no scheme of beings"
                  % (words[0], fm.get("kind")))
            return 1
        words, src = [str(fm.get("title") or words[0])], "estate"
    text, refused = " ".join(words), False
    if party and get is None:
        import importlib
        dmpass = importlib.import_module("pass")
        d = dmpass.flows(root).decide(src, "remote", "send", party=party) \
            if os.path.isfile(os.path.join(root, "beans", party + ".md")) else None
        if d is None or not d.granted:
            refused = True
            print("NotGranted: looking %r up at Wikidata sends it to %s, and %s — nothing sent. The gardener grants a party "
                  "in VOCAB.md, by name and on a basis:\n  flows:\n    - { flow: sent-out, from: %s, to: remote, through: "
                  "send, grant: granted, party: %s, basis: \"<why>\" }" % (
                      text, party, "no bean here names that party" if d is None else
                      "this garden's flow law does not grant it (%s: %s)" % (", ".join(d.rows) or "closed", d.grant),
                      src, party))
        else:
            get = web_get(((k.schemes.get("wikidata") or {}).get("lookup") or {}).get("api"))
    found = k.propose(text, level, get=get)
    print("proposed for %r at the level %s (%d) — nothing is written: a person picks" % (text, level, len(found)))
    for p in found:
        print("%-24s %-40s %-10s %s%s" % (p["coding"], p["name"][:40], p["level"], p["how"],
                                          ("   (" + p["status"] + ")") if p["status"] else ""))
    return 1 if refused else 0


def main():
    root = os.path.dirname(HERE)
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return
    k = Knowledge(root)
    cmd = a[0]
    if cmd == "show" and len(a) >= 3:
        for r in k.ancestry(a[1], a[2]):
            print("%-6s %-10s %s%s" % (r.get("code"), r.get("level", r.get("category", "")), k.name(r),
                                       ("   docs: " + r["docs"]) if r.get("docs") else ""))
        if a[1] == "technology":
            e = k.resolve({"code": "%s:%s" % (a[1], a[2])})
            print("  draws on: " + "; ".join("%s %s" % (f["code"], f["label"]) for f in e["fields"]))
            print("  run by:   " + "; ".join("%s %s" % (o["code"], o["label"]) for o in e["occupations"]))
        if a[1] == "isco-08":
            for r in k.crosswalk(a[2])[:8]:
                print("  draws on %s %s  (core %s, common %s, specialist %s; %s)" % (r["isced_f_2013"], k.label("isced-f-2013", r["isced_f_2013"])[0],
                      r["core"], r["common"], r["specialist"], r["topics"]))
    elif cmd == "tree" and len(a) >= 2:
        key = k.decl.get(a[1], {}).get("key", "code")
        rows = k.rows(a[1])
        codes = {r.get(key) for r in rows}
        kids = {}
        for r in rows:
            kids.setdefault(r.get("parent") if r.get("parent") in codes else None, []).append(r)
        def walk(parent, depth):
            for r in kids.get(parent, []):
                print("%s%s  %s" % ("  " * depth, r.get(key), k.name(r)))
                walk(r.get(key), depth + 1)
        if len(a) > 2:
            r = k.row(a[1], a[2])
            if r:
                print("%s  %s" % (r.get(key), k.name(r))); walk(r.get(key), 1)
        else:
            walk(None, 0)
    elif cmd == "find" and len(a) >= 2:
        words, scheme = [], None
        it = iter(a[1:])
        for w in it:
            if w == "--scheme":
                scheme = next(it, None)
            else:
                words.append(w)
        for _score, s, r in k.find(" ".join(words), scheme=scheme, k=20):
            key = k.decl[s].get("key", "code")
            path = " › ".join(k.name(x) for x in k.ancestry(s, r.get(key))[:-1])
            print("%-13s %-10s %s%s" % (s, r.get(key), k.name(r), ("   (" + path + ")") if path else ""))
    elif cmd == "label" and len(a) >= 4:
        text, attribution = k.label(a[1], a[2], a[3])
        if text is None:
            print("no code %s in %s" % (a[2], a[1])); sys.exit(1)
        print(text + (("   — " + attribution) if attribution else ""))
    elif cmd == "at" and len(a) >= 2:
        sys.exit(_at(k, root, a[1]))
    elif cmd == "gold" and len(a) >= 2:
        _gold(k, a[1])
    elif cmd == "propose" and len(a) >= 2:
        sys.exit(_propose(k, root, a[1:]))
    elif cmd == "resolve" and len(a) >= 3:
        # A LOOKUP AT THE AUTHORITY SENDS A CODE OUT OF THE GARDEN, to a party the garden has not granted: the flow law
        # (the Leviathan's Body 3) is what grants it, and until it is built nothing is granted (draft §10)
        print("NotGranted: looking %s up at %s's authority sends it to %s, and the flow law grants that party nothing yet "
              "— a person reads the code at the authority and writes it here" %
              (a[2], a[1], k.schemes.get(a[1], {}).get("publisher", "its publisher")))
        sys.exit(1)
    elif cmd == "bean" and len(a) >= 2:
        if _runs_core(root):
            fm = {"knowledge": core_entries(root, a[1])}
        else:
            p = os.path.join(root, "beans", a[1] + ".md")
            fm = dmparse.loads(dmparse.read(p)[0]) or {}
        for e in k.for_bean(fm):
            print("%-13s %-8s %-13s %s%s" % (e["scheme"], e["code"], e["rel"], e["label"], ("  docs: " + e["docs"]) if e["docs"] else ""))
    elif cmd == "crosswalk" and len(a) >= 2:
        for r in k.crosswalk(a[1]):
            print("%s %s  core %s common %s specialist %s  roles %s  %s" % (r["isced_f_2013"], k.label("isced-f-2013", r["isced_f_2013"])[0],
                  r["core"], r["common"], r["specialist"], r["roles"], r["topics"]))
    else:
        print(__doc__); sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except KeyError as e:                  # a registry this machine cannot read: a fetched scheme none fetched, say
        print("knowledge: %s" % (e.args[0] if e.args else e))
        sys.exit(1)
