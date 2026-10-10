#!/usr/bin/env python3
"""The site: the one public page under site/ is what the release's tools print, and it links, loads and asks as it should.

`site/index.html` is published with the style and script it links (.github/workflows/pages.yml), and `site/board.py`
writes it from the release `site/RELEASE` names: the law's meanings and reasons, the catalogue, and the forms and
refusals of site/garden.yaml, proved in a garden grown from that release. What can be COMPUTED about the page is
checked here:
  1. the page parses: a doctype, `html lang`, `meta charset` and `viewport`, a title, every element closed; it carries a content security policy that runs no script and loads no style but the site's
     own, and holds no style and no script of its own but its data, a JSON block;
  2. every link and source inside the site resolves to a PUBLISHED file (the page, or a file under assets/);
  3. nothing is loaded from outside: no script, stylesheet, image, font or frame by `http(s):` or `//`, in the page or
     in the style it links;
  4. the page is what the build writes NOW: `site/board.py --out <tmp>` writes it back byte for byte — so every form it
     shows passed the release's gate and every refusal is the line that gate printed;
  5. its data holds a board for every crossing: every lens, every mechanism, each with its words, its proved form and
     refusal, and the parts of the law it names — and every word of the page in each of its languages, with the same
     places to fill;
  6. the pages workflow publishes the page and its assets, and nothing else of site/;
  7. the issue forms parse as GitHub reads them, open with the warning against pasting from a garden, require the
     situation (or the change, the question, what was expected) and the neutral-names checkbox; blank issues are off;
  8. no file under site/ or .github/ISSUE_TEMPLATE/ names the estate of the garden `$DAFTAR_GARDEN` or
     `git config daftar.garden` names. It calls bin/public.py's own functions rather than `--text`, which cannot see
     a word seed/PUBLIC-ALLOW makes public in one file only. CI has no garden, and this says so;
  9. `site/RELEASE` names a tag of this repository;
 10. the page is the blend (site/blend.py): its four movements — a sentence, the ladder, a garden's time, yours — every
     step of the release's ladder, every word of site/blend.yaml in each language with the same places to fill, the
     law's `orientations` rows as the release has them, and site/assets/direction.js the release's own widget, byte
     for byte, so the page's keys and arrows are the view's.
Whether the page is clear, and true where no tool speaks, is still a reader's work.
"""
import json, os, re, shutil, subprocess, sys, tempfile
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
FORMS_DIR = os.path.join(ROOT, ".github", "ISSUE_TEMPLATE")
PAGE = os.path.join(SITE, "index.html")
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


def published():
    """What the pages workflow publishes of site/: the page, and every file under assets/."""
    out = {"index.html"}
    for d, _, fs in os.walk(os.path.join(SITE, "assets")):
        out |= {rel_of(os.path.join(d, f)) for f in fs if "__pycache__" not in d}
    return out


PLACE = re.compile(r"\{(\w+)\}")          # a place a word of the page leaves to be filled: {name}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.unclosed, self.tags, self.data_of = [], [], [], {}
        self.decl, self._in = None, None

    def handle_decl(self, decl):
        self.decl = decl

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag not in VOID:
            self.stack.append(tag)
        if tag in ("script", "style", "title"):
            self._in = (tag, a)
            self.data_of.setdefault(tag, []).append([a, ""])

    def handle_startendtag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.unclosed.append(f"</{tag}> closes {self.stack[-1] if self.stack else 'nothing'}")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        self._in = None

    def handle_data(self, data):
        if self._in:
            self.data_of[self._in[0]][-1][1] += data


def outside(url):
    u = url.strip().lower()
    return u.startswith(("http:", "https:", "//", "data:text", "javascript:"))


# ---- 1. the page parses, under a policy that runs nothing the site does not hold -------------------------------------
def page_parses(p, text):
    check("site/index.html opens with <!doctype html>", (p.decl or "").lower() == "doctype html", p.decl)
    html_tag = next((a for t, a in p.tags if t == "html"), {})
    metas = [a for t, a in p.tags if t == "meta"]
    titles = p.data_of.get("title") or []
    check("...has `html lang`, `meta charset`, a `viewport` and one non-empty title",
          html_tag.get("lang") and any("charset" in m for m in metas)
          and any(m.get("name") == "viewport" for m in metas) and len(titles) == 1 and titles[0][1].strip(),
          (html_tag, len(titles)))
    check("...and closes every element it opens", not p.unclosed and not p.stack, p.unclosed + p.stack)
    csp = next((m.get("content", "") for m in metas if (m.get("http-equiv") or "").lower() == "content-security-policy"), "")
    rules = {r.split()[0]: r.split()[1:] for r in (x.strip() for x in csp.split(";")) if r}
    check("...carries a content security policy that runs no script and loads no style but the site's own",
          rules.get("default-src") == ["'self'"] and rules.get("script-src") == ["'self'"]
          and rules.get("style-src") == ["'self'"] and rules.get("base-uri") == ["'none'"], csp or "no policy")
    inline = [a for a, body in p.data_of.get("script") or [] if not a.get("src") and a.get("type") != "application/json"]
    styled = [t for t, a in p.tags if "style" in a] + (["<style>"] if p.data_of.get("style") else [])
    check("...and holds no script and no style of its own: its data is a JSON block, its code and style are linked",
          not inline and not styled, (inline, styled))
    return rules


# ---- 2. every link and source resolves; 3. nothing is loaded from outside ----------------------------------------------
def links_and_loads(p):
    pub, bad, loads = published(), [], []
    for t, a in p.tags:
        for attr in ("href", "src"):
            v = a.get(attr)
            if not v:
                continue
            load = t in ("script", "img", "iframe", "source") or (t == "link" and a.get("rel") in ("stylesheet", "icon", "preload"))
            if outside(v):
                if load:
                    loads.append(f"<{t} {attr}={v}>")
                continue
            path = unquote(urlsplit(v).path)
            if v.startswith("#") or not path:
                continue
            if path not in pub:
                bad.append(f"<{t} {attr}={v}>: {'no such file' if not os.path.exists(os.path.join(SITE, path)) else 'not published'}")
    check("every link and source inside the site resolves to a published file (the page, or a file under assets/)",
          not bad, "; ".join(bad))
    css = "".join(read(os.path.join(SITE, f)) for f in pub if f.endswith(".css"))
    loads += re.findall(r"@import[^;]*|url\(\s*['\"]?(?:https?:|//)[^)]*\)", css)
    check("nothing is loaded from outside the site: no script, stylesheet, image, font or frame, in the page or its style",
          not loads, loads)


# ---- 4. the page is what the build writes now ---------------------------------------------------------------------
def rebuilt_equals_committed(text):
    tmp = tempfile.mkdtemp(prefix="site-")
    try:
        out = os.path.join(tmp, "index.html")
        r = run(sys.executable, os.path.join(SITE, "board.py"), "--out", out, cwd=ROOT, timeout=900)
        check("site/board.py builds the page: every form passes the release's gate, every break is refused as the "
              "board says", r.returncode == 0 and os.path.isfile(out), (r.stdout + r.stderr)[-1500:])
        if r.returncode == 0 and os.path.isfile(out):
            again = read(out)
            first = next((i for i, (x, y) in enumerate(zip(text, again)) if x != y), min(len(text), len(again)))
            check("the committed page is what the build writes now (when site/RELEASE or site/ changes, run "
                  "python3 site/board.py and commit the page)", again == text,
                  f"they differ at character {first}: committed {text[first - 60:first + 60]!r} / built {again[first - 60:first + 60]!r}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---- 5. a board for every crossing ----------------------------------------------------------------------------------
def every_crossing(p):
    blocks = [body for a, body in p.data_of.get("script") or [] if a.get("type") == "application/json"]
    try:
        data = json.loads(blocks[0])
    except (IndexError, ValueError) as e:
        check("the page's data block parses as JSON", False, e)
        return
    L, M = data.get("lenses") or [], data.get("mechanisms") or []
    ids = {m.get("id") for m in M}
    lacking = [f"{m.get('id')}.{k}" for m in M for k in ("name", "glyph", "person", "gardener", "agent_note", "form", "rule", "error")
               if not str(m.get(k) or "").strip()]
    lacking += [f"{m.get('id')}: no part of the law" for m in M if not m.get("keeper")]
    lacking += [f"lens {l.get('id')}" for l in L if not (l.get("label") and l.get("who"))]
    check(f"the data holds a board for every crossing ({len(L)} lenses × {len(M)} mechanisms), each with its words, "
          f"its proved form and refusal (the rule that refused it, and its line), and the parts of the law it is made of",
          len(L) >= 2 and len(M) >= 2 and len(ids) == len(M) and not lacking, lacking)
    stray = [f"{m['id']} → {t}" for m in M for t in (m.get("staples") or {}) if t not in ids or t == m["id"]]
    stray += [f"rope {r.get('a')}–{r.get('b')}" for r in data.get("ropes") or [] if not {r.get("a"), r.get("b")} <= ids]
    check("every staple and every rope joins two mechanisms the page has", not stray, stray)
    langs = [x.get("id") for x in data.get("languages") or []]
    ui = data.get("ui") or {}
    missing = [f"ui.{lg}" for lg in langs if lg not in ui]
    if langs and langs[0] in ui:
        base = ui[langs[0]]
        for lg in langs[1:]:
            got = ui.get(lg) or {}
            missing += [f"ui.{lg}.{k}" for k in base if not str(got.get(k) or "").strip()]
            missing += [f"ui.{lg}.{k}: its places {sorted(set(PLACE.findall(got[k])))} are not "
                        f"{sorted(set(PLACE.findall(v)))}" for k, v in base.items()
                        if k in got and set(PLACE.findall(got[k])) != set(PLACE.findall(v))]
            missing += [f"lens {x.get('id')}.{lg}.{k}" for x in L for k in ("label", "who")
                        if not str((x.get(lg) or {}).get(k) or "").strip()]
            missing += [f"{m.get('id')}.{lg}.{k}" for m in M for k in ("name", "short", "person", "gardener", "agent_note")
                        if not str((m.get(lg) or {}).get(k) or "").strip()]
            missing += [f"{m.get('id')}.{lg}.staples" for m in M
                        if set((m.get(lg) or {}).get("staples") or {}) != set(m.get("staples") or {})]
    check(f"every word of the page is written in each of its languages ({', '.join(langs) or 'none'}), with the same "
          f"places to fill", len(langs) >= 1 and not missing, missing)
    check("...and every word the template names is filled in: no `{{` is left in the page",
          "{{" not in TEXT.split('id="data"')[0], re.findall(r"\{\{\w+\}\}", TEXT)[:5])
    board = yaml.safe_load(read(os.path.join(ROOT, "site", "boards.yaml")))
    named = sum(len(m.get("items") or []) for m in board.get("mechanisms") or [])
    have = sum(len(m.get("keeper") or []) for m in M)
    check(f"every part of the law a board names is one the release's catalogue has ({have} of {named})", have == named,
          "site/board.py leaves out a part the catalogue does not hold: name it as `python3 bin/daftar.py catalog` does")


# ---- 6. the workflow publishes the page and its assets, and nothing else of site/ -----------------------------------
def workflow_publishes():
    wf = read(os.path.join(ROOT, ".github", "workflows", "pages.yml"))
    line = " ".join(re.findall(r"rsync[^\n]*(?:\n\s+--[^\n]*)*", wf))
    check("the pages workflow publishes site/index.html and site/assets/, and nothing else of site/",
          "--include 'index.html'" in line and "--include 'assets/***'" in line and line.rstrip().endswith("site/ _site/")
          and "--exclude '*'" in line and "*.html" not in line, line or "no rsync step")


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
    import public as dmpublic
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


# ---- 10. the blend: its movements, its ladder, its words, and the direction module the release holds ----------------
def blend(p, text):
    release = read(os.path.join(SITE, "RELEASE")).strip()
    show = lambda path: run("git", "-C", ROOT, "show", f"{release}:{path}")
    ids = {a.get("id") for t, a in p.tags if a.get("id")}
    check("the page's four movements are here: a sentence, the ladder, a garden's time, yours",
          {"sentence", "ladder", "time", "yours"} <= ids, sorted({"sentence", "ladder", "time", "yours"} - ids))
    core = yaml.safe_load(show("core/law/core.yaml").stdout or "{}")
    levels = yaml.safe_load(show("core/law/levels.yaml").stdout or "{}").get("levels") or []
    want = [lv["level"] for lv in (core.get("levels") or []) + levels]
    lack = [x for x in want if f"lv-{x}" not in ids]
    check(f"every step of the release's ladder is on the page ({len(want)}), each in its place", want and not lack, lack)
    words = yaml.safe_load(read(os.path.join(SITE, "blend.yaml")))
    ui, miss = words.get("ui") or {}, []
    for k, v in (ui.get("en") or {}).items():
        f = (ui.get("fa") or {}).get(k)
        if not str(f or "").strip():
            miss.append(f"ui.fa.{k}")
        elif set(PLACE.findall(f)) != set(PLACE.findall(v)):
            miss.append(f"ui.fa.{k}: its places {sorted(set(PLACE.findall(f)))} are not {sorted(set(PLACE.findall(v)))}")
    for mo in words.get("moments") or []:
        for k, v in (mo.get("en") or {}).items():
            if not str((mo.get("fa") or {}).get(k) or "").strip():
                miss.append(f"moments.{mo.get('id')}.fa.{k}")
    check("every word of site/blend.yaml is written in each language, with the same places to fill", not miss, miss)
    blocks = {a.get("id"): body for a, body in p.data_of.get("script") or [] if a.get("type") == "application/json"}
    prof = yaml.safe_load(show("core/law/profiles.yaml").stdout or "{}")
    law = [{k: r[k] for k in ("order", "axis", "sense", "follows", "commands") if k in r} for r in prof.get("orientations") or []]
    try:
        got = json.loads(blocks.get("orientations") or "null")
    except ValueError:
        got = None
    check("the page carries the law's `orientations` rows as the release has them", law and got == law, (got, law))
    widget = show("assets/view/lib/widgets/direction.js").stdout
    mine = read(os.path.join(SITE, "assets", "direction.js")) if os.path.isfile(os.path.join(SITE, "assets", "direction.js")) else ""
    check("site/assets/direction.js is the release's own widget, byte for byte: the page's keys and arrows are the view's",
          widget and mine == widget, "site/board.py copies it from the release; run it again")


# =====================================================================================================================
HAVE_PAGE = os.path.isfile(PAGE)
check("site/index.html is here: the page site/board.py writes", HAVE_PAGE, "run python3 site/board.py")
if HAVE_PAGE:
    TEXT = read(PAGE)
    P = Page()
    P.feed(TEXT)
    P.close()
    page_parses(P, TEXT)
    links_and_loads(P)
    every_crossing(P)
    blend(P, TEXT)
workflow_publishes()
issue_forms()
leak_guard()
release_tag()
if HAVE_PAGE:
    rebuilt_equals_committed(TEXT)

print("\nsite: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
