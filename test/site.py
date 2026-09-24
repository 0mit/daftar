#!/usr/bin/env python3
"""The site: the public pages under site/ show what the release's tools print, and link, load and ask as they should.

`site/` is published as it is committed (.github/workflows/pages.yml), and every output on it was printed by the tools
of the release `site/RELEASE` names, on demo gardens `site/build.py` grows. What can be COMPUTED about the pages is
checked here:
  1. every page parses: a doctype, `html lang`, `meta charset` and `viewport`, a title, and every element closed; each
     page of the site's own (all but the report the machinery page embeds) has one `main`, one `h1`, a `header`, a
     labelled `nav` and a `footer`, and carries a content security policy that allows nothing from outside;
  2. every link and source inside the site resolves to a PUBLISHED file (a page or an asset: never a source such as a
     `.py`, never `_parts/`), and every `#fragment` to an id in the page it names;
  3. nothing is loaded from outside the site: no script, stylesheet, image, font or frame by `http(s):` or `//`;
  4. every generated block is what the tools print NOW: `site/build.py --out <tmp>` writes every committed page back,
     byte for byte, once the values that differ in every build are blanked (`<span class="v" data-v="…">`: garden ids,
     the fingerprints that carry them, moments in milliseconds); a mismatch names the page and the block;
  5. the machinery's `drawn.json` has its keys, and its hash and size are the committed report's;
  6. every drawing is named for a reader who cannot see it (`role="img"`, a `title` and a `desc`), every image has
     alt text, every frame a title, and every block of output a place in the tab order;
  7. the issue forms parse as GitHub reads them, open with the warning against pasting from a garden, require the
     situation (or the change, the question, what was expected) and the neutral-names checkbox; blank issues are off;
  8. no file under site/ or .github/ISSUE_TEMPLATE/ names the estate of the garden `$DAFTAR_GARDEN` or
     `git config daftar.garden` names. It calls bin/dmpublic.py's own functions rather than `--text`, which cannot see
     a word seed/PUBLIC-ALLOW makes public in one file only. CI has no garden, and this says so;
  9. `site/RELEASE` names a tag of this repository.
Whether a page is clear, and true where no tool speaks, is still a reader's work.
"""
import hashlib, json, os, posixpath, re, shutil, subprocess, sys, tempfile, time
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
FORMS_DIR = os.path.join(ROOT, ".github", "ISSUE_TEMPLATE")
REPORT = "machinery/report.html"          # the one page the site does not write: the machinery's report, embedded
FAILS = []

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None, timeout=None, env=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                          timeout=timeout, env=env)


def read(path):
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        return fh.read()


def rel_of(path, base=SITE):
    return os.path.relpath(path, base).replace(os.sep, "/")


# ---------------------------------------------------------------------------------------------------------------------
# WHAT IS PUBLISHED. pages.yml copies every .html but `_parts/` (the chrome the build inlines) and all of `assets/`:
#     rsync -a --prune-empty-dirs --exclude '_parts/' --include '*/' --include '*.html' --include 'assets/***' --exclude '*'
# A link to anything else — a drawing's source, a .py, drawn.json — would be a link to nothing once published.

def published(base):
    out = set()
    for d, dirs, files in os.walk(base):
        dirs[:] = sorted(x for x in dirs if x != "_parts")
        for f in files:
            rel = rel_of(os.path.join(d, f), base)
            if f.endswith(".html") or "assets" in rel.split("/")[:-1]:
                out.add(rel)
    return out


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
FOREIGN = {"svg", "math"}                 # where `<x/>` closes an element, as it does not in HTML


class Page(HTMLParser):
    """One HTML file, read as a browser's tokenizer reads it, with what the checks below need."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.doctype = None
        self.stack = []                    # [(tag, line)]
        self.unbalanced = []
        self.elements = []                 # [(tag, attrs, line, ancestors, svg)]: svg = the outermost svg's index
        self.ids = {}                      # id -> (tag, svg)
        self.duplicate_ids = []
        self.title = ""
        self.css = []                      # [(line, text)]: <style> blocks and style="" attributes
        self.svgs = 0
        self._svg = None
        self._text = None

    def handle_decl(self, decl):
        if decl.lower().startswith("doctype"):
            self.doctype = decl

    def handle_starttag(self, tag, attrs):
        self._element(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self._element(tag, attrs, True)

    def _element(self, tag, attrs, selfclosing):
        a = {k: ("" if v is None else v) for k, v in attrs}
        line = self.getpos()[0]
        ancestors = tuple(t for t, _ in self.stack)
        if tag == "svg" and self._svg is None:
            self._svg = self.svgs
            self.svgs += 1
        self.elements.append((tag, a, line, ancestors, self._svg))
        if "id" in a:
            if a["id"] in self.ids:
                self.duplicate_ids.append(f"id=\"{a['id']}\" at line {line}")
            self.ids.setdefault(a["id"], (tag, self._svg))
        if "style" in a:
            self.css.append((line, a["style"]))
        if selfclosing and tag not in VOID and not (FOREIGN & (set(ancestors) | {tag})):
            self.unbalanced.append(f"<{tag}/> at line {line}: HTML does not close an element by its slash")
        if selfclosing or tag in VOID:
            if tag == "svg" and ancestors.count("svg") == 0:
                self._svg = None
            return
        self.stack.append((tag, line))
        if tag == "title" and "head" in ancestors:
            self._text = "title"
        elif tag == "style":
            self._text = "style"

    def handle_endtag(self, tag):
        line = self.getpos()[0]
        if tag in VOID:
            return
        if tag in ("title", "style"):
            self._text = None
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        elif any(t == tag for t, _ in self.stack):
            while self.stack[-1][0] != tag:
                t, at = self.stack.pop()
                self.unbalanced.append(f"<{t}> at line {at} is not closed before </{tag}> at line {line}")
            self.stack.pop()
        else:
            self.unbalanced.append(f"</{tag}> at line {line} closes nothing open")
            return
        if tag == "svg" and not any(t == "svg" for t, _ in self.stack):
            self._svg = None

    def handle_data(self, data):
        if self._text == "title":
            self.title += data
        elif self._text == "style":
            self.css.append((self.getpos()[0], data))

    def finish(self):
        self.close()
        self.unbalanced += [f"<{t}> at line {at} is never closed" for t, at in self.stack]
        return self

    def all(self, *tags):
        return [(a, line) for t, a, line, _anc, _svg in self.elements if t in tags]


def parse(path):
    p = Page()
    p.feed(read(path))
    return p.finish()


EXTERNAL = re.compile(r"^(?://|[A-Za-z][A-Za-z0-9+.-]*:)")
NAVIGATION_RELS = {"canonical", "alternate", "author", "license", "help", "me", "next", "prev", "search", "bookmark"}


def refs(page):
    """Every (tag, attribute, value, line, attributes) that names a file: a link to follow or a resource to load."""
    out = []
    for tag, a, line, _anc, _svg in page.elements:
        for k in ("href", "src", "xlink:href", "poster", "data"):
            if k in a and not (k == "data" and tag != "object"):
                out.append((tag, k, a[k].strip(), line, a))
        for k in ("srcset", "imagesrcset"):
            if k in a:
                out += [(tag, k, c.strip().split()[0], line, a) for c in a[k].split(",") if c.strip()]
    return out


def loads(tag, attr, a):
    """True when the reference is fetched with the page rather than followed by a reader: everything but a link out."""
    if tag in ("a", "area"):
        return False
    if tag == "link":
        return not (set(a.get("rel", "").lower().split()) <= NAVIGATION_RELS and a.get("rel"))
    return True


CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I | re.S)
CSS_IMPORT = re.compile(r"@import\s+(?:url\(\s*)?(['\"]?)([^'\")\s;]+)", re.I)
MARK = re.compile(r"<!--\s*(/?)daftar:([a-z]+)\b(.*?)-->", re.S)
V_SPAN = re.compile(r"(<span(?=[^>]*\sclass=\"v\")(?=[^>]*\sdata-v=\"[^\"]*\")[^>]*>)[^<]*(</span>)")


def normal(text):
    """A page as the comparison sees it: its line ends as LF, and the contents of every varying value blanked."""
    return V_SPAN.sub(r"\1\2", text.replace("\r\n", "\n"))


def block_at(text, pos):
    """The innermost generated block that holds a position: 'type:id', or None outside every block."""
    stack = []
    for m in MARK.finditer(text):
        if m.start() > pos:
            break
        if m.group(1):
            if stack and m.end() <= pos:
                stack.pop()
        else:
            ident = re.search(r'\bid="([^"]*)"', m.group(3))
            stack.append(f"{m.group(2)}:{ident.group(1) if ident else '?'}")
    return stack[-1] if stack else None


def line_at(text, pos):
    return text.count("\n", 0, pos) + 1


# ---- 1. every page parses -------------------------------------------------------------------------------------------
def pages_parse(parsed, own):
    bad = []
    for p, pg in parsed.items():
        miss = []
        if not (pg.doctype and pg.doctype.lower().split() == ["doctype", "html"]):
            miss.append("<!doctype html>")
        html = pg.all("html")
        if not (html and html[0][0].get("lang", "").strip()):
            miss.append("<html lang>")
        if not any(a.get("charset", "").lower() == "utf-8" for a, _ in pg.all("meta")):
            miss.append('<meta charset="utf-8">')
        if not any(a.get("name", "").lower() == "viewport" and a.get("content") for a, _ in pg.all("meta")):
            miss.append('<meta name="viewport">')
        if not pg.title.strip():
            miss.append("a <title> in <head>")
        miss += pg.unbalanced[:5]
        if miss:
            bad.append(f"{p}: " + ", ".join(miss))
    check(f"every page parses: a doctype, html lang, meta charset and viewport, a title, every element closed "
          f"({len(parsed)} pages)", not bad, "; ".join(bad))

    bad = []
    for p in own:
        pg, miss = parsed[p], []
        for tag in ("main", "h1"):
            if len(pg.all(tag)) != 1:
                miss.append(f"{len(pg.all(tag))} <{tag}>")
        miss += [f"no <{tag}>" for tag in ("header", "nav", "footer") if not pg.all(tag)]
        miss += [f"a <nav> at line {line} with no aria-label" for a, line in pg.all("nav")
                 if not (a.get("aria-label", "").strip() or a.get("aria-labelledby", "").strip())]
        if miss:
            bad.append(f"{p}: " + ", ".join(miss))
    check(f"every page of the site's own has one main and one h1, a header, a labelled nav and a footer "
          f"({len(own)} pages)", not bad, "; ".join(bad))

    bad = []
    for p in own:
        csp = [a.get("content", "") for a, _ in parsed[p].all("meta")
               if a.get("http-equiv", "").lower() == "content-security-policy"]
        if not csp:
            bad.append(f"{p}: no Content-Security-Policy")
            continue
        rules = {r.split()[0].lower(): r.split()[1:] for r in csp[0].split(";") if r.split()}
        loose = [x for srcs in rules.values() for x in srcs if x == "*" or re.match(r"^(https?:|wss?:|//)", x)]
        if rules.get("default-src") != ["'self'"] or rules.get("script-src") != ["'none'"] or loose:
            bad.append(f"{p}: {csp[0]}")
    check("...and carries a content security policy: default-src 'self', script-src 'none', no source outside the site",
          not bad, "; ".join(bad))


# ---- 2. every link inside the site resolves -------------------------------------------------------------------------
def links_resolve(parsed):
    bad, frag_bad, n_links, n_frags = [], [], 0, 0
    for p, pg in parsed.items():
        for tag, attr, url, line, _a in refs(pg):
            if not url or EXTERNAL.match(url):
                continue
            parts = urlsplit(url)
            target = p
            if parts.path:
                n_links += 1
                path = posixpath.normpath(posixpath.join(posixpath.dirname(p), unquote(parts.path)))
                if path == ".." or path.startswith("../"):
                    bad.append(f"{p}:{line}: {url} leaves the site")
                    continue
                if parts.path.endswith("/") or os.path.isdir(os.path.join(SITE, *path.split("/"))):
                    path = "index.html" if path == "." else path + "/index.html"
                if path not in PUBLISHED:
                    there = os.path.isfile(os.path.join(SITE, *path.split("/")))
                    bad.append(f"{p}:{line}: {url} " + ("is not published (a source, or _parts/)" if there
                                                         else "names no file"))
                    continue
                target = path
            if parts.fragment and target.endswith(".html"):
                n_frags += 1
                if unquote(parts.fragment) not in parsed[target].ids:
                    frag_bad.append(f"{p}:{line}: {url} — no id=\"{unquote(parts.fragment)}\" in {target}")
    check(f"every link and source inside the site resolves to a published page or asset ({n_links} links)",
          not bad, "; ".join(bad))
    check(f"...and every #fragment to an id in the page it names ({n_frags} fragments)", not frag_bad,
          "; ".join(frag_bad))
    dup = [f"{p}: " + ", ".join(pg.duplicate_ids[:5]) for p, pg in parsed.items() if pg.duplicate_ids]
    check("...and no page gives one id to two elements, which would make a fragment or a drawing's name ambiguous",
          not dup, "; ".join(dup))


# ---- 3. nothing is loaded from outside ------------------------------------------------------------------------------
def outside(url):
    return bool(EXTERNAL.match(url)) and not url.lower().startswith("data:")


def nothing_outside(parsed):
    bad = []
    for p, pg in parsed.items():
        bad += [f"{p}:{line}: <{tag} {attr}=\"{url}\">" for tag, attr, url, line, a in refs(pg)
                if outside(url) and loads(tag, attr, a)]
        for line, css in pg.css:
            bad += [f"{p}:{line}: url({m.group(2)})" for m in CSS_URL.finditer(css) if outside(m.group(2).strip())]
            bad += [f"{p}:{line}: @import {m.group(2)}" for m in CSS_IMPORT.finditer(css) if outside(m.group(2))]
    sheets = sorted(x for x in PUBLISHED if x.endswith(".css"))
    for c in sheets:
        css = read(os.path.join(SITE, *c.split("/")))
        for m in list(CSS_URL.finditer(css)) + list(CSS_IMPORT.finditer(css)):
            u, at = m.group(2).strip(), f"{c}:{line_at(css, m.start())}"
            if outside(u):
                bad.append(f"{at}: {u}")
            elif u and not EXTERNAL.match(u) and not u.startswith("#"):
                path = posixpath.normpath(posixpath.join(posixpath.dirname(c), unquote(urlsplit(u).path)))
                if path not in PUBLISHED:
                    bad.append(f"{at}: {u} names no published file")
    for s in sorted(x for x in PUBLISHED if x.endswith(".svg")):
        bad += [f"{s}:{line}: <{tag} {attr}=\"{url}\">" for tag, attr, url, line, a in refs(parse(os.path.join(SITE, *s.split("/"))))
                if outside(url) and tag != "a"]
    check(f"no page loads anything from outside the site: no script, stylesheet, image, font or frame by http(s) or // "
          f"({len(parsed)} pages, {len(sheets)} stylesheets)", not bad, "; ".join(dict.fromkeys(bad)))


# ---- 6. every drawing is named; every image, frame and block of output can be reached --------------------------------
def named_for_every_reader(parsed, own):
    bad, n = [], 0
    for p in own:
        pg = parsed[p]
        for tag, a, line, anc, svg in pg.elements:
            if tag != "svg" or "svg" in anc or a.get("aria-hidden") == "true":
                continue
            n += 1
            named = [pg.ids.get(i) for i in a.get("aria-labelledby", "").split()]
            kinds = {t for t, owner in (x for x in named if x) if owner == svg}
            if a.get("role") != "img" or not {"title", "desc"} <= kinds or None in named:
                bad.append(f"{p}:{line}: <svg role=\"{a.get('role', '')}\" "
                           f"aria-labelledby=\"{a.get('aria-labelledby', '')}\">")
        bad += [f"{p}:{line}: <img> with no alt" for a, line in pg.all("img") if "alt" not in a]
        bad += [f"{p}:{line}: <iframe> with no title" for a, line in pg.all("iframe") if not a.get("title", "").strip()]
        bad += [f"{p}:{line}: <pre> not in the tab order" for a, line in pg.all("pre") if a.get("tabindex") != "0"]
    check(f"every drawing in a page is role=img, named by its own title and desc; every img has alt, every iframe a "
          f"title, every pre tabindex=0 ({n} drawings)", not bad, "; ".join(bad))


# ---- 5. the machinery's record of its drawing -----------------------------------------------------------------------
KEYS = {"tool": str, "tool_release": str, "tool_contract": int, "daftar_release": str, "demo_day": str, "garden": str,
        "drawn_at": str, "report": str, "report_bytes": int, "report_sha256": str, "title": str, "levels": list,
        "mechanisms": list, "transcript": list}
ITEM_KEYS = {"levels": {"id", "depth", "name", "audience", "question"},
             "mechanisms": {"key", "title", "claim", "questions", "parts", "patterns", "operate"},
             "transcript": {"cwd", "cmd", "out", "exit"}}


def drawn_record():
    try:
        drawn = json.loads(read(os.path.join(SITE, "machinery", "drawn.json")))
    except Exception as e:                                                          # absent, or not JSON
        check("site/machinery/drawn.json parses", False, e)
        return
    wrong = [f"{k}: not a {t.__name__}" for k, t in KEYS.items()
             if not isinstance(drawn.get(k), t) or (t is int and isinstance(drawn.get(k), bool))]
    for k, want in ITEM_KEYS.items():
        for i, item in enumerate(drawn.get(k) or []):
            if not (isinstance(item, dict) and want <= set(item)):
                wrong.append(f"{k}[{i}] lacks {sorted(want - set(item)) if isinstance(item, dict) else sorted(want)}")
    levels = {x.get("id") for x in drawn.get("levels") or [] if isinstance(x, dict)}
    for m in (x for x in drawn.get("mechanisms") or [] if isinstance(x, dict)):
        if set(m.get("questions") or {}) != levels:
            wrong.append(f"mechanism {m.get('key')}: its questions {sorted(m.get('questions') or {})} are not one "
                         f"for each level {sorted(levels)}")
        if not (isinstance(m.get("operate"), dict) and {"archetype", "would_take", "why_none"} <= set(m["operate"])):
            wrong.append(f"mechanism {m.get('key')}: operate lacks archetype, would_take or why_none")
    check("site/machinery/drawn.json parses and has every key the machinery page reads", not wrong, "; ".join(wrong))
    path = os.path.join(SITE, *str(drawn.get("report", "")).split("/"))
    body = None
    if drawn.get("report") == REPORT and os.path.isfile(path):
        with open(path, "rb") as fh:
            body = fh.read()
    check(f"...and the report it records is the committed {REPORT}: its sha256 and its size",
          body is not None and hashlib.sha256(body).hexdigest() == drawn.get("report_sha256")
          and len(body) == drawn.get("report_bytes"),
          f"it records {drawn.get('report')!r}, which is not {REPORT} or is absent" if body is None else
          f"sha256 {hashlib.sha256(body).hexdigest()} vs {drawn.get('report_sha256')}, "
          f"{len(body)} bytes vs {drawn.get('report_bytes')}")


# ---- 7. the issue forms ---------------------------------------------------------------------------------------------
WARNING = ("Write the situation in your own words. Do not paste anything from your garden — no host names, addresses, "
           "paths, people's names, ids, serials or findings. Use neutral names: sam, ali, host-a, example.org, "
           "203.0.113.10, /home/user/….")
CHECKBOX = "Nothing here comes from my garden that I have not replaced with a neutral name."
REQUIRED = {"need": "situation", "use-case": "situation", "suggestion": "change", "question": "question",
            "bug": "expected"}
FIELD_TYPES = {"markdown", "textarea", "input", "dropdown", "checkboxes"}


def flat(s):
    return " ".join(str(s).split())


def form_problems(stem, form):
    """What GitHub's issue-form schema, or this project's way of asking, would refuse in one form."""
    if not isinstance(form, dict):
        return ["not a mapping"]
    out = [f"no {k}" for k in ("name", "description") if not (isinstance(form.get(k), str) and form[k].strip())]
    body = form.get("body")
    if not (isinstance(body, list) and body and all(isinstance(el, dict) for el in body)):
        return out + ["no body, or an element of it that is not a mapping"]
    ids, labels = [], []
    for i, el in enumerate(body):
        at, attrs = f"body[{i}]", el.get("attributes") if isinstance(el.get("attributes"), dict) else {}
        if el.get("type") not in FIELD_TYPES:
            out.append(f"{at}: type {el.get('type')!r} is none GitHub knows")
            continue
        if el["type"] == "markdown":
            if "id" in el or "validations" in el:
                out.append(f"{at}: a markdown element takes no id and no validations")
            if not str(attrs.get("value", "")).strip():
                out.append(f"{at}: markdown with no value")
            continue
        if not re.fullmatch(r"[A-Za-z0-9_-]+", str(el.get("id", ""))):
            out.append(f"{at}: no id, or one GitHub refuses")
        if not str(attrs.get("label", "")).strip():
            out.append(f"{at}: no attributes.label")
        ids.append(str(el.get("id")))
        labels.append(flat(attrs.get("label", "")))
        if "render" in attrs and el["type"] != "textarea":
            out.append(f"{at}: render is for a textarea")
        opts = attrs.get("options")
        if el["type"] in ("dropdown", "checkboxes") and not (isinstance(opts, list) and opts):
            out.append(f"{at}: a {el['type']} with no options")
        elif el["type"] == "dropdown" and (len(set(map(str, opts))) != len(opts) or "None" in map(str, opts)):
            out.append(f"{at}: dropdown options repeat, or one is the reserved None")
        elif el["type"] == "checkboxes" and not all(isinstance(o, dict) and str(o.get("label", "")).strip()
                                                      for o in opts):
            out.append(f"{at}: a checkbox with no label")
        v = el.get("validations")
        if v is not None and not (isinstance(v, dict) and isinstance(v.get("required", False), bool)):
            out.append(f"{at}: validations.required is not true or false")
    out += [f"two fields share one {what}" for what, seen in (("id", ids), ("label", labels))
            if len(set(seen)) != len(seen)]
    first = body[0]
    if not (first.get("type") == "markdown" and flat(WARNING) in flat((first.get("attributes") or {}).get("value", ""))):
        out.append("it does not open with the warning against pasting from a garden")
    want = REQUIRED.get(stem)
    field = next((el for el in body if el.get("id") == want), None)
    if want and not (field and isinstance(field.get("validations"), dict) and field["validations"].get("required") is True):
        out.append(f"no required `{want}` field")
    opts = (body[-1].get("attributes") or {}).get("options") or []
    if not (body[-1].get("type") == "checkboxes" and any(isinstance(o, dict) and flat(o.get("label", "")) == CHECKBOX
                                                         and o.get("required") is True for o in opts)):
        out.append("it does not end with the required neutral-names checkbox")
    tags = form.get("labels") or []
    tags = [t.strip() for t in (tags.split(",") if isinstance(tags, str) else map(str, tags))]
    if stem in REQUIRED and stem not in tags:
        out.append(f"it does not carry the label `{stem}`")
    return out


def issue_forms():
    forms = sorted(f for f in os.listdir(FORMS_DIR) if f.endswith((".yml", ".yaml")) and f != "config.yml") \
        if os.path.isdir(FORMS_DIR) else []
    check("the five issue forms are here: " + ", ".join(f"{s}.yml" for s in REQUIRED),
          {f"{s}.yml" for s in REQUIRED} <= set(forms), f"found {forms}")
    for f in forms:
        try:
            form = yaml.safe_load(read(os.path.join(FORMS_DIR, f)))
        except yaml.YAMLError as e:
            check(f"{f} parses as YAML", False, e)
            continue
        problems = form_problems(f.rsplit(".", 1)[0], form)
        check(f"{f} is an issue form GitHub reads: the warning first, the situation required, the neutral-names "
              f"checkbox last", not problems, "; ".join(problems))
        if f == "use-case.yml" and isinstance(form, dict):
            related = [el for el in form.get("body") or [] if isinstance(el, dict) and el.get("id") == "related"]
            check("...and use-case.yml has the `related` input that a use-case page's link fills",
                  bool(related) and related[0].get("type") == "input", related)
    try:
        config = yaml.safe_load(read(os.path.join(FORMS_DIR, "config.yml")))
    except Exception as e:                                                          # absent, or not YAML
        config = e
    links = config.get("contact_links") if isinstance(config, dict) else None
    check("config.yml turns blank issues off, and each contact link has a name, an https url and a line about it",
          isinstance(config, dict) and config.get("blank_issues_enabled") is False and isinstance(links, list)
          and all(isinstance(x, dict) and x.get("name") and str(x.get("url", "")).startswith("https://")
                  and x.get("about") for x in links), config)


# ---- 8. the leak guard ----------------------------------------------------------------------------------------------
def leak_guard():
    garden = os.environ.get("DAFTAR_GARDEN", "").strip() or \
        run("git", "-C", ROOT, "config", "--get", "daftar.garden").stdout.strip()
    if not garden:
        check("no garden to derive estate names from (CI has none): the leak check runs where a garden is — "
              "git config daftar.garden <path>", True)
        return
    if not os.path.isdir(os.path.join(garden, "beans")):
        check("the garden $DAFTAR_GARDEN or git config daftar.garden names is a garden", False,
              "it has no beans/, so no estate names can be derived from it")
        return
    sys.path.insert(0, os.path.join(ROOT, "bin"))
    import dmpublic
    pub = dmpublic.public_words(garden)
    words = dmpublic.estate_words(garden, pub) - pub
    r = run("git", "-C", ROOT, "ls-files", "-z", "-co", "--exclude-standard", "--", "site", ".github/ISSUE_TEMPLATE")
    files = sorted({x for x in r.stdout.split("\0") if x}) if r.returncode == 0 else \
        sorted(rel_of(os.path.join(d, f), ROOT) for top in (SITE, FORMS_DIR) for d, _, fs in os.walk(top) for f in fs)
    bad, n = [], 0
    for f in files:
        path = os.path.join(ROOT, *f.split("/"))
        if not os.path.isfile(path) or "__pycache__" in f.split("/"):
            continue
        n += 1
        here = words - dmpublic.allowed_in(f)
        bad += [f"{f}:{line}: {w}" for w, line in dmpublic.hits(read(path), here).items()]
        bad += [f"{f} (its name): {w}" for w in dmpublic.hits(f, here)]
    check(f"no file under site/ or .github/ISSUE_TEMPLATE/ names the estate of the configured garden ({n} files, "
          f"{len(words)} names; a word seed/PUBLIC-ALLOW makes public in one file is public there only)",
          not bad, "; ".join(sorted(bad)))


# ---- 9. the release the site documents ------------------------------------------------------------------------------
def release_tag():
    try:
        release = read(os.path.join(SITE, "RELEASE")).strip()
    except OSError:
        release = ""
    tagged = bool(re.fullmatch(r"v\d+\.\d+\.\d+", release)) and \
        run("git", "-C", ROOT, "rev-parse", "-q", "--verify", f"refs/tags/{release}^{{commit}}").returncode == 0
    check(f"site/RELEASE names a tag of this repository ({release or 'nothing'})", tagged,
          "no such tag here (a shallow clone has none: git fetch --tags)" if release else "site/RELEASE is absent or empty")


# ---- 4. every generated block is what the tools print now -----------------------------------------------------------
def blocks_closed(pages):
    bad = []
    for p in pages:
        text, stack = read(os.path.join(SITE, *p.split("/"))), []
        for m in MARK.finditer(text):
            ident, at = re.search(r'\bid="([^"]*)"', m.group(3)), line_at(text, m.start())
            if not m.group(1):
                stack.append((m.group(2), ident.group(1) if ident else None, at))
                if not ident:
                    bad.append(f"{p}:{at}: daftar:{m.group(2)} with no id")
            elif stack and stack[-1][0] == m.group(2):
                stack.pop()
            else:
                bad.append(f"{p}:{at}: /daftar:{m.group(2)} closes "
                           + (f"daftar:{stack.pop()[0]}" if stack else "nothing open"))
        bad += [f"{p}:{at}: daftar:{t} id={i} is never closed" for t, i, at in stack]
    check("every generated block of every page opens with its type and id, and closes with its own type",
          not bad, "; ".join(bad))


def snapshot(base):
    out = {}
    for d, dirs, files in os.walk(base):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            with open(os.path.join(d, f), "rb") as fh:
                out[rel_of(os.path.join(d, f), base)] = hashlib.sha256(fh.read()).hexdigest()
    return out


def first_difference(p, a, b):
    pos = len(os.path.commonprefix([a, b]))
    where, ln = block_at(a, pos), line_at(a, pos)
    was, now = a.split("\n")[ln - 1], (b.split("\n") + [""])[ln - 1]
    return (f"{p}: first differs at line {ln}, " + (f"in the block {where}" if where else "outside every block")
            + f" — committed {was.strip()[:160]!r}, built {now.strip()[:160]!r}")


def rebuilt_equals_committed(pages):
    build = os.path.join(SITE, "build.py")
    if not os.path.isfile(build):
        check("site/build.py is here to rebuild the pages from", False, "no site/build.py")
        return
    out = tempfile.mkdtemp(prefix="dmsite-")
    before, started = snapshot(SITE), time.time()
    try:
        r = run(sys.executable, build, "--out", out, cwd=ROOT, timeout=1800, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        built, said = r.returncode == 0, (r.stdout + r.stderr)[-1200:]
    except subprocess.TimeoutExpired:
        built, said = False, "it ran for 30 minutes and was stopped"
    check(f"site/build.py --out <tmp> grows the demo gardens, runs the scenes and writes the site "
          f"({time.time() - started:.0f} s)", built, said)
    after = snapshot(SITE)
    check("...and leaves site/ as it found it", after == before,
          sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k)))
    if built:
        bad = []
        for p in pages:
            q = os.path.join(out, *p.split("/"))
            if not os.path.isfile(q):
                bad.append(f"{p}: the build wrote no such page")
                continue
            a, b = normal(read(os.path.join(SITE, *p.split("/")))), normal(read(q))
            if a != b:
                bad.append(first_difference(p, a, b))
        check(f"every committed page is what the build writes now, the values that differ in every build aside "
              f"({len(pages)} pages; when a tool's output or site/RELEASE changes, run python3 site/build.py and "
              f"commit the pages)", not bad, "\n        ".join(bad))
        extra = sorted(set(x for x in published(out) if x.endswith(".html")) - set(pages))
        check("...and the build writes no page that is not committed", not extra, extra)
    shutil.rmtree(out, ignore_errors=True)


# =====================================================================================================================
HAVE_SITE = os.path.isfile(os.path.join(SITE, "index.html"))
check("site/ holds the pages, site/index.html the first of them", HAVE_SITE, "no site/index.html here")
PUBLISHED = published(SITE) if HAVE_SITE else set()
if HAVE_SITE:
    PAGES = sorted(p for p in PUBLISHED if p.endswith(".html"))
    OWN = [p for p in PAGES if p != REPORT]
    PARSED = {p: parse(os.path.join(SITE, *p.split("/"))) for p in PAGES}
    pages_parse(PARSED, OWN)
    links_resolve(PARSED)
    nothing_outside(PARSED)
    named_for_every_reader(PARSED, OWN)
    drawn_record()
issue_forms()
leak_guard()
release_tag()
if HAVE_SITE:
    blocks_closed(PAGES)
    rebuilt_equals_committed(PAGES)

print("\nsite: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
