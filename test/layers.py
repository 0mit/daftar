#!/usr/bin/env python3
"""The layer map: every file sits where the law says, or where its garden says, and nowhere a tool must guess.

The law's `layers` place what every garden has; a garden places the rest with `standing`; bin/dmpass.py is the one
reader of both, and this reads the map only through it. It holds:

  the map          the rows parse and have none of the faults the gate refuses, the chain read down `beneath` is
                   manifesto > law > reasoning > journal > history, and every `beneath` names a row the law has
  holds            only a layer of files holds a file; no file is held by two rows, among what a release ships or what
                   a new garden holds, and the check does see a file two rows hold; no pattern reaches into a hidden
                   directory, and every pattern names a file the release or a new garden has, but for the short list
                   of paths a garden grows — so no tool's own file enters the law, under any name
  one verdict      a pattern is matched case by case, `*` crossing `/`, and the map reads the same on every platform
  what ships       the one file a garden receives and no layer holds is the agent-door mirror; the journal the law
                   names is held by the journal row
  the changelog    journal, not law: gone from the law file, and every entry it held carried whole, word for word, in
                   the order it held them; what is new since sits in one run above the newest it held
  a new garden     `dmpass --layers` places its files, a file git would track and has not been given included, and
                   its gate is clean and says nothing of a file in no layer; `dmpass <path>` reads a path where the
                   person stands, and a garden copied into another repository is still read as itself
  a law's map      refused where it cannot be read: no `layers`, a row whose `holds` is not a list, two rows holding
                   one file, a chain with two tops, a `journal.path` the journal row does not hold
  standing         a garden places what the law does not, and never what it does; never one file in two layers; a
                   doc only in the one form a path is written in, and naming a file the garden has; the term, and the
                   rows, are the law's alone; a garden term that states again what a standard term states is warned of
  the review       dmreview reads as law prose what the map places in law, reasoning or guide, and not what it places
                   in work
  the duty         an edit to the law, to a file the release keeps, or to a file a garden's pattern places in law is a
                   RULE-CHANGE; the queue is not

Every name is neutral (sam), and the garden is grown in a temporary directory.
"""
import fnmatch, json, ntpath, os, re, shutil, subprocess, sys, tempfile, types
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmparse, dmpass
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)


def reader(root):
    def read(p):
        try:
            with open(os.path.join(root, *p.split("/")), encoding="utf-8") as fh:
                return fh.read()
        except (OSError, UnicodeDecodeError):
            return None
    return read


def listed(root):
    """The files a commit of this tree would hold: the tracked, and the new ones git does not ignore — so a file added
    to the release and not yet committed is judged before it ships, not after."""
    r = run("git", "-C", root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    return sorted({p for p in r.stdout.split("\0") if p and os.path.isfile(os.path.join(root, *p.split("/")))})


def hidden_dirs(path):
    """The hidden directories a path runs through: a segment that starts with '.' and that a '/' follows."""
    return [s for s in str(path).split("/")[:-1] if s.startswith(".")]


def said(out, kind, *words):
    """The findings of a gate's output of one kind (ERROR, WARN) that name every one of the words: a refusal is read by
    what it names, never by how it is worded. A finding is its first line and the indented lines that go on from it."""
    found = []
    for l in out.splitlines():
        if l.startswith(kind):
            found.append(l)
        elif found and found[-1] is not None and l[:1].isspace() and l.strip():
            found[-1] += "\n" + l
        else:
            found.append(None)
    return [f for f in found if f is not None and all(w in f for w in words)]


LAW_TEXT = reader(ROOT)(dmpass.LAW) or ""
_fm, BODY = dmparse.split_front_matter(LAW_TEXT)
LAW = dmparse.loads(_fm) if _fm else {}
RELEASE = listed(ROOT)
M = dmpass.Map(reader(ROOT), RELEASE)

# ------------------------------------------------------------------ the map
_rows = LAW.get("layers")
check("the law's `layers` parse: a list of rows, each naming its layer, once, and saying what it means",
      isinstance(_rows, list) and len(_rows) >= 5
      and all(isinstance(r, dict) and r.get("layer") and r.get("meaning") for r in _rows)
      and len({r["layer"] for r in _rows}) == len(_rows), _rows)
check("...and the map has none of the faults the gate refuses in a law (dmpass reads them)", not M.law_problems(),
      M.law_problems())
ROWS = M.rows
NAMES = set(M.layers)
CHAIN = ["manifesto", "law", "reasoning", "journal", "history"]
try:
    _chain = M.chain()
except ValueError as e:
    _chain = str(e)
check("the chain read down `beneath` is manifesto > law > reasoning > journal > history", _chain == CHAIN, _chain)
# ONE CHAIN, NOT A TREE: a row beside the chain that stood on one of it would be a second way down, and `chain()` refuses
# a map with two tops. Every row a `beneath` touches is in the chain.
_linked = {r["layer"] for r in ROWS if r.get("beneath")} | {r["beneath"] for r in ROWS if r.get("beneath")}
check("...and it is the only chain: every row that stands on another, or that another stands on, is in it",
      _linked == set(CHAIN), sorted(_linked - set(CHAIN)))
_dangling = [(r["layer"], r["beneath"]) for r in ROWS if r.get("beneath") and r["beneath"] not in NAMES]
check("every `beneath` names a row of the map", not _dangling, _dangling)
_link = [l for l in LAW.get("registry_links") or [] if isinstance(l, dict)
         and l.get("from") == "layers" and l.get("field") == "beneath"]
check("...and the law holds it so: a `registry_links` row takes `beneath` to a layer, and allows no cycle",
      len(_link) == 1 and _link[0].get("to") == "layers" and _link[0].get("take") == "layer"
      and _link[0].get("acyclic") is True, _link)

# ------------------------------------------------------------------ holds
_loose = [r["layer"] for r in ROWS if r.get("holds") and r.get("files") is not True]
check("every row that holds a file is a layer of files (`files: true`)", not _loose, _loose)

# A GARDEN IS GROWN HERE, once, and read by every section below.
T = tempfile.mkdtemp(prefix="dmlayers-")
G = os.path.join(T, "garden-a")
r = run(sys.executable, os.path.join(ROOT, "seed", "germinate.py"), G, "--gardener", "sam", cwd=T)
check("a garden germinates, kept by sam", r.returncode == 0 and os.path.isfile(os.path.join(G, "beans", "sam.md")),
      r.stdout + r.stderr)
if r.returncode != 0:                                  # every check below reads the garden: none can say anything true
    shutil.rmtree(T, ignore_errors=True)
    print("\nlayers: %d failed" % len(FAILS))
    sys.exit(1)
run("git", "config", "user.name", "probe", cwd=G)
run("git", "config", "user.email", "probe@example.org", cwd=G)
GM = dmpass.Map.here(G)

# WHAT A RELEASE SHIPS is read as the gate reads it: seed/LANGUAGE's patterns, through dmpass.
SHIPPED = [f for f in RELEASE if M.keeper_of(f) == "release"]
SHIP = dmpass.Map(reader(ROOT), SHIPPED)
check(f"no file a release ships is held by two of the law's rows ({len(SHIPPED)} shipped)",
      len(SHIPPED) > 30 and not SHIP.law_overlaps(), SHIP.law_overlaps())
check(f"...nor any file a new garden holds ({len(GM.files)} files)",
      len(GM.files) > 30 and not GM.law_overlaps(), GM.law_overlaps())


def law_of(*rows):
    """A reader of a tree whose law is these rows alone: the map's own mechanism, read apart from the law in force."""
    text = "---\nversion: '0.0'\nlayers:\n" + "".join(f"  - {r}\n" for r in rows) + "---\n"
    return lambda p: text if p == dmpass.LAW else None


# THE TWO CHECKS ABOVE ASK FOR NOTHING, and pass as well for a check that finds nothing ever. It must find one.
_two = dmpass.Map(law_of('{ layer: a, files: true, holds: ["x/*"] }', '{ layer: b, files: true, holds: ["x/*.md"] }'),
                  ["x/y.md", "x/z.txt"]).law_overlaps()
check("...and the check sees one where there is one: a file two rows hold is named with both rows, and a file one "
      "row holds is not", _two == [("x/y.md", ["a", "b"])], _two)

# NO HARNESS PATH IN THE LAW. A tool keeps its settings in a hidden directory of its own, or in a file under a name of
# its own; the law places what every garden has, whichever tools its writers use. So no pattern runs through a hidden
# directory or names one the trees hold, and EVERY PATTERN NAMES A FILE THE RELEASE OR A NEW GARDEN HAS — but for the
# paths a garden grows for itself, listed here and held to that — so a tool's own file enters the law under no name.
# The tools' directories are read from the trees themselves, so this names none of them and holds for one that
# arrives later.
PATTERNS = [(r["layer"], str(p)) for r in ROWS for p in (r.get("holds") if isinstance(r.get("holds"), list) else [])]
_dotted = [(l, p) for l, p in PATTERNS if hidden_dirs(p)]
check("NO HARNESS PATH IN THE LAW: no pattern a layer holds runs through a hidden directory", not _dotted, _dotted)
TREES = RELEASE + GM.files
TOOL_DIRS = sorted({d for f in TREES for d in hidden_dirs(f)})
_named = [(l, p, d) for l, p in PATTERNS for d in TOOL_DIRS
          if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(d.lstrip(".").lower()), p.lower())]
_reach = [(l, p, f) for l, p in PATTERNS for f in TREES if hidden_dirs(f) and dmpass.matches(p, f)]
check(f"...nor names a tool's directory, dotted or bare, nor matches a file inside one ({len(TOOL_DIRS)} such "
      f"directories, read from the release and the garden)", not _named and not _reach, _named + _reach)
GROWN = ("RATIONALE.md", "captures/*", "mappings/*")    # a garden's own reasons, its captures, its mappings: none at birth
_empty = [(l, p) for l, p in PATTERNS if p not in GROWN and not any(dmpass.matches(p, f) for f in TREES)]
check("...and every pattern a layer holds names a file the release or a new garden has, but for the paths a garden "
      f"grows ({', '.join(GROWN)})", not _empty, _empty)
_stale = [p for p in GROWN if p not in {q for _l, q in PATTERNS} or any(dmpass.matches(p, f) for f in TREES)]
check("...and each path a garden grows is one the law holds and no tree has yet: the list stays as short as it is true",
      not _stale, _stale)

# ------------------------------------------------------------------ one verdict
# ONE VERDICT ON EVERY PLATFORM. Python's fnmatch folds case, and reads `/` as `\`, where the platform does; the map may
# not, or a garden clean on one machine is refused on a clone of it on another. The matcher Windows would use is put in
# place for one reading, and every verdict must come out as it does here — and case must count in both.
_PROBES = ["README.md", "readme.md", "agents.md", "Beans/Notes.md", "log/journal.md", "LOG/journal.md", "notes/a.md"]


def _verdicts():
    m = dmpass.Map(reader(ROOT), _PROBES,
                   standing=[("beans/sam.md", 0, {"doc": "file:Notes/*", "standing": "work", "why": "a probe"})])
    return [(p, m.layer_of(p), m.keeper_of(p)) for p in _PROBES], m.law_overlaps(), m.standing_conflicts()


_here = _verdicts()
_os = fnmatch.os
fnmatch.os = types.SimpleNamespace(path=ntpath)
try:
    _there = _verdicts()
finally:
    fnmatch.os = _os
_none = [p for p, at, kept in _here[0] if p not in ("README.md", "log/journal.md") and (at != (None, None) or kept != "here")]
check("ONE VERDICT: the map reads the same with the matcher Windows uses, and case counts in both (readme.md, "
      "agents.md, Beans/Notes.md, LOG/journal.md and notes/a.md against Notes/* sit in no layer, kept here)",
      _here == _there and not _none, {"here": _here, "there": _there, "placed": _none})
check("...and a path written with a backslash is not in the one form a path is written in",
      bool(dmpass.unwritten("log\\*")) and not dmpass.unwritten("log/*"), dmpass.unwritten("log\\*"))

# ------------------------------------------------------------------ what ships
# THE AGENT-DOOR MIRROR is AGENTS.md again, under the front matter a tool reads, in the hidden directory that tool
# looks in. The law does not place it — it would be a harness path — so it is the one shipped file in no layer, found
# here by what it is. Any other shipped file in no layer is a file the law forgot, and fails here by name.
_agents = reader(ROOT)("AGENTS.md")


def _mirrors(p):
    t = reader(ROOT)(p)
    return (p != "AGENTS.md" and t is not None and bool(_agents)
            and re.sub(r"^---\n.*?\n---\n\s*", "", t, count=1, flags=re.S) == _agents)


MIRROR = sorted(f for f in SHIPPED if hidden_dirs(f) and _mirrors(f))
_unplaced = sorted(f for f in SHIPPED if SHIP.layer_of(f)[0] is None)
check("the one file a garden receives from a release and no layer holds is the agent-door mirror",
      len(MIRROR) == 1 and _unplaced == MIRROR, f"in no layer: {_unplaced}; the mirror: {MIRROR}")
_g_unplaced = GM.placed()[1]
check("...and a new garden holds no other file in no layer", _g_unplaced == MIRROR,
      f"in no layer: {_g_unplaced}; the mirror: {MIRROR}")
check("the journal the law names (`journal.path`) is held by the journal row, and by no other",
      bool(M.journal_path) and M.law_layers_of(M.journal_path) == ["journal"],
      (M.journal_path, M.law_layers_of(M.journal_path or "")))

# ------------------------------------------------------------------ the changelog
# A RECORD OF WHAT WAS IS JOURNAL. The law's changelog sat at the foot of the law file until the law's layers placed it;
# the move carries every entry as it was written, because a journal is appended and never rewritten. An entry is read
# WHOLE, from its `- **` line to the next one: an old entry found somewhere in a longer one, or in another order, is an
# entry rewritten.
check("the law file keeps no changelog: no changelog heading and no version entry in its body",
      not re.search(r"(?mi)^#+\s*change[\s-]*log\b", BODY) and not re.search(r"(?m)^- \*\*\d+\.\d+\*\*", BODY),
      re.findall(r"(?m)^#+ .*$", BODY))
CL_PATH = os.path.join(ROOT, "seed", "CHANGELOG.md")
check("seed/CHANGELOG.md exists, and the law places it in journal",
      os.path.isfile(CL_PATH) and M.law_layers_of("seed/CHANGELOG.md") == ["journal"],
      M.law_layers_of("seed/CHANGELOG.md"))
CL = reader(ROOT)("seed/CHANGELOG.md") or ""
BASE = "0433435576bb70d8433c3e58058bd91a468762be"     # the last commit whose law file held the changelog
_old = run("git", "-C", ROOT, "show", f"{BASE}:{dmpass.LAW}")
_old_body = dmparse.split_front_matter(_old.stdout)[1] if _old.returncode == 0 else ""
_at = _old_body.find("\n## Changelog")
_ENTRY = re.compile(r"(?m)^(?=- \*\*)")


def _head(e):
    m = re.match(r"- \*\*([^*]+)\*\*", e)
    return m.group(1) if m else e[:40]


def _num(v):
    return tuple(int(x) for x in v.split("."))


_entries = _ENTRY.split(_old_body[_at:])[1:] if _at >= 0 else []
_versions = [_head(e) for e in _entries if re.fullmatch(r"\d+\.\d+", _head(e))]
_now = _ENTRY.split(CL)[1:]
_heads = {_head(e) for e in _entries}
_carried = [e for e in _now if _head(e) in _heads]
_first = next((f"entry {i + 1}: {_head(a)!r} was, {_head(b)!r} is" + ("" if _head(a) != _head(b) else
               " — rewritten") for i, (a, b) in enumerate(zip(_entries, _carried)) if a != b), None)
check(f"seed/CHANGELOG.md carries every entry the law file held ({len(_versions)} versions and "
      f"{len(_entries) - len(_versions)} note), each whole, word for word, and in the order it held them",
      _old.returncode == 0 and len(_versions) >= 30 and len(_carried) == len(_entries) and _first is None,
      _first or f"{len(_carried)} carried of {len(_entries)}" if _old.returncode == 0 else
      (_old.stderr.strip() or "no changelog found at the base commit")
      + " — the base commit must be in this clone (CI checks out with fetch-depth: 0)")
# WHAT IS NEW SINCE goes above the newest entry the law file held, newest first: the order the file's header states.
_newest = max(_versions, key=_num) if _versions else None
_new = [i for i, e in enumerate(_now) if _head(e) not in _heads]
_top = next((i for i, e in enumerate(_now) if _head(e) == _newest), -1)
_ver = str(LAW.get("version"))
_new_heads = [_head(_now[i]) for i in _new]
check(f"...and every entry since sits in one run directly above {_newest}, newest first, the law's current version "
      f"({_ver}) among them",
      _top > 0 and _new == list(range(_top - len(_new), _top)) and _ver in _new_heads
      and all(re.fullmatch(r"\d+\.\d+", h) for h in _new_heads)
      and _new_heads == sorted(_new_heads, key=_num, reverse=True), (_newest, _new_heads, _new, _top))

# ------------------------------------------------------------------ a new garden
TRACES = []


def gate():
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), cwd=G)
    out = r.stdout + r.stderr
    if "Traceback" in out:
        TRACES.append(out[-600:])
    return out, r.returncode


def put(rel, text):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def get(rel):
    with open(os.path.join(G, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read()


def clean():
    """The garden as its last commit left it: every probe's file taken back out."""
    run("git", "reset", "-q", "--hard", cwd=G)
    run("git", "clean", "-qfd", cwd=G)


def dmpass_cli(*args, cwd=None):
    r = run(sys.executable, os.path.join(G, "bin", "dmpass.py"), *args, cwd=cwd or G)
    out = r.stdout + r.stderr
    if "Traceback" in out:
        TRACES.append(out[-600:])
    return out


def layers_json():
    r = run(sys.executable, os.path.join(G, "bin", "dmpass.py"), "--layers", "--json", cwd=G)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"layers": {}, "error": (r.stdout + r.stderr)[-400:]}


r = run(sys.executable, os.path.join(G, "bin", "dmpass.py"), "--layers", cwd=G)
check("`dmpass --layers` runs in a new garden and reads the chain from its law",
      r.returncode == 0 and "manifesto > law > reasoning > journal > history" in r.stdout, (r.stdout + r.stderr)[-400:])
_at = {e["path"]: layer for layer, es in layers_json()["layers"].items() for e in es}
_want = {"GARDEN.md": "law", "VOCAB.md": "law", "log/pending.md": "queue", "log/journal.md": "journal",
         "beans/sam.md": "estate"}
check("...and places the manifest and the garden's terms in law, the queue in queue, the journal in journal, and a "
      "bean in estate", {p: _at.get(p) for p in _want} == _want, {p: _at.get(p) for p in _want})
# SHOWN, NEVER REFUSED — and not shown by the gate at all: a garden that has not placed a file has broken nothing, and
# whatever the gate prints stays in an agent's context for the rest of its session.
_UNPLACED = re.compile(r"no layer|unplaced|not placed|placed by no", re.I)
out, rc = gate()
check("the new garden's gate is clean, 0 errors and 0 warnings, and says nothing of a file in no layer",
      rc == 0 and " 0 error(s), 0 warning(s)" in out and not _UNPLACED.search(out), out[-500:])

# A GARDEN COPIED WITHOUT ITS .git into another repository's tree is still itself: its files are read from the disk,
# not from the repository around it, which tracks none of them — and here ignores them all.
OUTER = os.path.join(T, "outer")
run("git", "init", "-q", OUTER)
with open(os.path.join(OUTER, ".gitignore"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("garden-a/\n")
shutil.copytree(G, os.path.join(OUTER, "garden-a"), ignore=shutil.ignore_patterns(".git"))
_nest = dmpass.Map.here(os.path.join(OUTER, "garden-a"))
check("a garden copied without its .git into a repository that ignores it is read as itself: its files, MODEL.md in law",
      set(GM.files) <= set(_nest.files) and _nest.layer_of("MODEL.md") == ("law", "law"),
      (sorted(set(GM.files) - set(_nest.files))[:5], _nest.layer_of("MODEL.md")))

# EVERY FILE, THE NEW ONES TOO. A file written and not yet added — a handover, what an upgrade just brought — is in the
# tree a person reads, and the map shows it; a file git ignores is not the garden's.
put("HANDOVER.md", "An agent's handover, not yet added.\n")
put("notes/probe.pyc", "a compiled probe\n")
_ignored = run("git", "check-ignore", "-q", "notes/probe.pyc", cwd=G).returncode == 0
_text, _js = dmpass_cli("--layers"), layers_json()
check("`dmpass --layers` shows a file git would track and has not been given (HANDOVER.md, in no layer), and not one "
      "git ignores", _ignored and "HANDOVER.md" in _text and "HANDOVER.md" in (_js.get("in_no_layer") or [])
      and "notes/probe.pyc" not in _text, (_ignored, _text[-400:]))
os.remove(os.path.join(G, "notes", "probe.pyc"))              # ignored, so `clean()` leaves it; the probe takes it back
clean()

# A PATH IS READ WHERE THE PERSON STANDS: each spelling of a file gets that file's answer, and one outside the tree is
# said to be outside it. The canonical answer is the one given for the path as the tree spells it.
_model = dmpass_cli("MODEL.md")
_spelt = {a: dmpass_cli(a) for a in ("./MODEL.md", os.path.join(G, "MODEL.md"), "log/../MODEL.md")}
check("`dmpass <path>` reads ./MODEL.md, its absolute path and log/../MODEL.md as MODEL.md, which sits in law",
      "law" in _model and all(v == _model for v in _spelt.values()), {"MODEL.md": _model, **_spelt})
_sub = dmpass_cli("std-vocab.md", cwd=os.path.join(G, "seed"))
check("...and a path given from a subdirectory: std-vocab.md, given in seed/, is seed/std-vocab.md",
      _sub == dmpass_cli("seed/std-vocab.md") and "law" in _sub, _sub)
_far = dmpass_cli(os.path.join(T, "elsewhere.md"))
check("...and a path outside the tree is said to be outside it, never placed or said to sit in no layer",
      "outside" in _far and "no layer" not in _far, _far)

# ------------------------------------------------------------------ a law's map
# A MAP THE GATE CANNOT READ IS REFUSED, before any file is judged by it. Each probe edits the garden's copy of the law
# alone, and nothing is staged: the refusal is the map's, not the journal duty's.
LAW_G = get("seed/std-vocab.md")


def in_row(text, layer, line):
    """The law's text with one line added to the row of `layer`, under its name."""
    return re.sub(r"(?m)^(  - layer: %s\n)" % re.escape(layer), lambda m: m.group(1) + "    " + line + "\n", text,
                  count=1)


LAW_CASES = [
    ("no `layers`", re.sub(r"(?ms)^layers:\n.*?(?=^[^\s#])", "", LAW_G, count=1), ("layers",)),
    ("a row whose `holds` is one path, not a list", in_row(LAW_G, "words", "holds: notes/a.md"), ("words", "holds")),
    ("two rows that hold one file", in_row(in_row(LAW_G, "words", 'holds: ["notes/*"]'), "work", 'holds: ["notes/*.md"]'),
     ("notes/a.md", "words", "work")),
    ("a chain with two tops", in_row(LAW_G, "queue", "beneath: journal"), ("manifesto", "queue")),
    ("a `journal.path` the journal row does not hold",
     re.sub(r"(?m)^(journal:\n(?:  .*\n)*?  path: )\S+", r"\1notes/journal.md", LAW_G, count=1), ("notes/journal.md",)),
]
for _name, _text, _words in LAW_CASES:
    put("notes/a.md", "A note of the gardener's.\n")
    put("seed/std-vocab.md", _text)
    out, rc = gate()
    check(f"a law with {_name} is refused, the refusal naming {', '.join(_words)}",
          _text != LAW_G and rc == 1 and bool(said(out, "ERROR", *_words)),
          out[-600:] if _text != LAW_G else "the probe could not be written: the law's text has another form")
    clean()
# THE PATH IN FORCE IS THE LAW'S. No tool reads a journal's path from a garden's VOCAB.md, so a path there that differs
# is WARNED as unread, never taken in silence — and never refused: a garden that passed with it before 23.1 passes still,
# which is what keeps 23.1 minor.
VOCAB = get("VOCAB.md")
_jlines = re.search(r"(?m)^journal:\n(?:  .*\n)+", LAW_G)
put("VOCAB.md", re.sub(r"(?m)^local_terms:", lambda _m: re.sub(r"(?m)^(  path: )\S+", r"\1notes/journal.md",
                                                                _jlines.group(0)) + "local_terms:", VOCAB, count=1)
    if _jlines else VOCAB)
out, rc = gate()
check("a VOCAB.md `journal` whose path differs from the law's is warned as read by no tool, and not refused",
      bool(_jlines) and rc == 0 and " 0 error(s)" in out and bool(said(out, "WARN", "notes/journal.md"))
      and not said(out, "ERROR", "notes/journal.md"), out[-600:])
clean()

# ------------------------------------------------------------------ standing
SAM = get("beans/sam.md")


def standing(*entries):
    put("beans/sam.md", re.sub(r"(?m)^provenance:", lambda _m: "standing:\n" + "".join(f"  - {e}\n" for e in entries)
                               + "provenance:", SAM, count=1))


# A FILE THE LAW PLACES, THE LAW PLACES. A garden's entry that says otherwise would make one file two things, and every
# flow judged from it would be judged twice.
standing('{ doc: "file:log/pending.md", standing: journal, why: "a probe" }')
out, rc = gate()
check("a bean whose `standing` places log/pending.md in journal is refused, naming the file and the layer the law gives it",
      rc == 1 and "log/pending.md" in out and "queue" in out, out[-600:])
_gm = dmpass.Map.here(G)
check("...and while the entry is there, the map reads the law first: log/pending.md is still queue, the conflict named",
      _gm.layer_of("log/pending.md") == ("queue", "law")
      and [c[3:] for c in _gm.standing_conflicts()] == [("journal", "queue", "log/pending.md")],
      (_gm.layer_of("log/pending.md"), _gm.standing_conflicts()))
standing('{ doc: "file:notes/*.md", standing: world, why: "a probe" }')
out, rc = gate()
check("a `standing` naming a layer that holds no file (world) is refused: only a layer of files is a file's place",
      rc == 1 and "standing[0].standing 'world'" in out, out[-600:])
# ONE FILE, ONE LAYER — among a garden's own entries too: which of two it sat in would depend on the order they were read.
# A DOC IS WRITTEN IN THE ONE FORM a path is written in here, and a doc that names one file names a file the garden has:
# a spelling no file has places nothing, and would say nothing about it.
put("notes/a.md", "A note of the gardener's.\n")
STANDING_CASES = [
    ("one file placed in two layers by two entries (notes/a.md in work, and by notes/*.md in words)",
     ('{ doc: "file:notes/a.md", standing: work, why: "a probe" }',
      '{ doc: "file:notes/*.md", standing: words, why: "a probe" }'), ("notes/a.md", "work", "words")),
    ("a doc written ./notes/a.md", ("{ doc: 'file:./notes/a.md', standing: work, why: 'a probe' }",), ("./notes/a.md",)),
    ("a doc written notes/ (a directory is notes/*)", ("{ doc: 'file:notes/', standing: work, why: 'a probe' }",),
     ("notes/",)),
    ("a doc written with a backslash (a\\b)", ("{ doc: 'file:a\\b', standing: work, why: 'a probe' }",), ("a\\",)),
    ("a doc naming no file the garden has (notes/nothere.md)",
     ("{ doc: 'file:notes/nothere.md', standing: work, why: 'a probe' }",), ("notes/nothere.md",)),
]
for _name, _entries_, _words in STANDING_CASES:
    standing(*_entries_)
    out, rc = gate()
    check(f"{_name} is refused, the refusal naming the bean and {', '.join(_words)}",
          rc == 1 and bool(said(out, "ERROR", "sam", *_words)), out[-600:])
# AN ENTRY WHOSE LAYER IS NOT ONE NAME — two layers, as a merge of two clones can leave them — is the term's to refuse,
# and places nothing meanwhile: the map's reader files every path under one layer, and must not fail on it.
standing('{ doc: "file:notes/a.md", standing: [work, words], why: "a probe" }')
out, rc = gate()
_pass = dmpass_cli("--layers")
check("an entry placing notes/a.md in [work, words] is refused by name, and dmpass shows the file in no layer, unfailed",
      rc == 1 and bool(said(out, "ERROR", "sam", "standing")) and "Traceback" not in _pass
      and dmpass.Map.here(G).layer_of("notes/a.md") == (None, None), out[-600:] + _pass[-400:])
put("beans/sam.md", SAM)
# THE ROWS ARE THE LAW'S: a garden adding a row of its own would draw a layer the one reader of the map never reads.
put("VOCAB.md", re.sub(r"(?m)^local_terms:", lambda _m: 'registry_additions:\n  layers:\n'
                       '    - { layer: scratch, files: true, meaning: "a layer of the garden\'s own" }\nlocal_terms:',
                       VOCAB, count=1))
out, rc = gate()
check("a layer a garden adds through `registry_additions` is refused: the rows are the law's, and no garden redraws them",
      rc == 1 and bool(said(out, "ERROR", "registry_additions", "layers")), out[-600:])
clean()
# THE TERM IS THE LAW'S. A garden that kept `standing` as a local term before the law promoted it would, by the overlay
# every local term gets, redraw the map for itself — here a `doc` of any form, and any layer, a layer of no file
# included — and the gate reads the map from it. The probe is otherwise well formed: an enum of its own would be
# refused already, for its values no bean occupies, and would pass this check for the wrong reason.
put("VOCAB.md", re.sub(r"(?m)^local_terms:.*$", lambda _m:
                       'local_terms:\n  - { term: standing, meaning: "what a document is for", context_keys: [standing], '
                       'schema: { shape: list_of_entries, attrs: { doc: { required: true }, '
                       'standing: { required: true, in: { registry: layers, take: layer } }, '
                       'why: { required: true, in: prose } } } }', VOCAB, count=1))
out, rc = gate()
check("a local term named `standing` in VOCAB.md is refused: the map is the law's, and no garden redraws it",
      rc == 1 and any("standing" in l for l in out.splitlines() if l.startswith("ERROR")), out[-600:])
# A TERM THE STANDARD HAS, STATED AGAIN BY A GARDEN, is warned of and not refused: a garden that passed before the
# standard promoted its term still passes, and is told that its copy stands where the standard's would.
_T = next((t for t in LAW.get("terms") or [] if isinstance(t, dict) and t.get("term") != "standing"
           and isinstance(t.get("schema"), dict) and t["schema"].get("shape") == "scalar"), {})
put("VOCAB.md", re.sub(r"(?m)^local_terms:.*$", lambda _m:
                       f'local_terms:\n  - {{ term: {_T.get("term")}, meaning: "a reading of the term of this garden\'s '
                       f'own", schema: {{ shape: scalar }} }}', VOCAB, count=1))
out, rc = gate()
check(f"a local term stating again what the standard's `{_T.get('term')}` states is warned of, with 0 errors",
      bool(_T) and rc == 0 and " 0 error(s)" in out and bool(said(out, "WARN", str(_T.get("term")))), out[-600:])
# ...and so is one that EMPTIES what the standard's term states: an overlay's `schema: ~` or `cells: ~` replaces the
# standard's rather than merging onto it, and a refusal the standard makes would go with nothing said.
_C = next((t for t in LAW.get("terms") or [] if isinstance(t, dict) and isinstance(t.get("schema"), dict)
           and isinstance(t["schema"].get("cells"), list) and t["schema"]["cells"]), {})
_nulls = {}
for _over, _key in (("schema: ~", "schema"), ("schema: { cells: ~ }", "schema.cells")):
    _name = (_T if _key == "schema" else _C).get("term")
    put("VOCAB.md", re.sub(r"(?m)^local_terms:.*$", lambda _m: f'local_terms:\n  - {{ term: {_name}, {_over} }}', VOCAB,
                           count=1))
    out, rc = gate()
    if not (_name and bool(said(out, "WARN", str(_name), _key))):
        _nulls[_over] = out[-400:]
check("...and one that empties it (`schema: ~`, `cells: ~`) is warned of too, naming what it empties", not _nulls, _nulls)
put("VOCAB.md", VOCAB)
standing('{ doc: "file:notes/*.md", standing: work, why: "the gardener\'s own notes" }')
put("notes/a.md", "A note of the gardener's.\n")
r = run(sys.executable, os.path.join(G, "bin", "dmsave.py"), "sam", "the notes placed in work",
        "--body", "- action: [[sam]] places notes/*.md in work.", cwd=G)
check("the gardener's bean placing notes/*.md in work is accepted, and saved through the gate",
      r.returncode == 0 and " 0 error(s), 0 warning(s)" in r.stdout + r.stderr, (r.stdout + r.stderr)[-600:])
_work = layers_json()["layers"].get("work") or []
check("...and dmpass places notes/a.md in work, placed by the gardener's bean",
      {"path": "notes/a.md", "kept": "here", "placed_by": "beans/sam.md"} in _work, _work)
SAVED = get("beans/sam.md")

# ------------------------------------------------------------------ the review
# THE REVIEW READS WHAT THE MAP SAYS IS LAW PROSE: a document a pattern entry places in guide is read, and one placed in
# work — an agent's own notes — is not, whether or not some other entry marks a document as guide.
put("guide/a.md", "A way in, of the gardener's.\n")
put("drafts/b.md", "An agent's draft.\n")
run("git", "add", "guide/a.md", "drafts/b.md", cwd=G)
PROSE = ("import json, sys; sys.path.insert(0, 'bin'); import dmreview; "
         "print(json.dumps([f for f, _t, _s in dmreview._prose_documents(dmreview.Tree())]))")


def prose():
    r = run(sys.executable, "-c", PROSE, cwd=G)
    try:
        return json.loads(r.stdout)
    except ValueError:
        TRACES.append((r.stdout + r.stderr)[-600:])
        return []


put("beans/sam.md", re.sub(r"(?m)^standing:\n", lambda _m: "standing:\n"
                           '  - { doc: "file:guide/*.md", standing: guide, why: "a probe" }\n'
                           '  - { doc: "file:drafts/*.md", standing: work, why: "a probe" }\n', SAVED, count=1))
_read = prose()
check("dmreview reads as law prose a document a pattern entry places in guide, and not one it places in work",
      "guide/a.md" in _read and "drafts/b.md" not in _read, _read)
put("beans/sam.md", re.sub(r"(?m)^standing:\n", lambda _m: "standing:\n"
                           '  - { doc: "file:drafts/*.md", standing: work, why: "a probe" }\n', SAVED, count=1))
_read = prose()
check("...and a document placed in work is not read though no entry marks a document as law, reasoning or guide",
      bool(_read) and "drafts/b.md" not in _read, _read)
clean()

# ------------------------------------------------------------------ the duty
# THE RULE-CHANGE DUTY IS UNCHANGED. Where a file sits and who keeps it are two axes: the law's own files, and every
# file a release keeps — its changelog and its gate among them — are a RULE-CHANGE whichever layer holds them, and a
# file kept here that is no law (the queue) is not.
_missed = {}
for rel in ("MODEL.md", "VOCAB.md", "GARDEN.md", "seed/std-vocab.md", "seed/CHANGELOG.md", "bin/dmcheck.py"):
    with open(os.path.join(G, *rel.split("/")), "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n# a local edit\n" if rel.endswith(".py") else "\nA local edit.\n")
    run("git", "add", rel, cwd=G)
    out, rc = gate()
    if not (rc == 1 and f"RULE-CHANGE staged ({rel})" in out):
        _missed[rel] = out[-300:]
    run("git", "reset", "-q", "--hard", cwd=G)
check("THE RULE-CHANGE DUTY IS UNCHANGED: an edit to MODEL.md, VOCAB.md, GARDEN.md, seed/std-vocab.md, "
      "seed/CHANGELOG.md or bin/dmcheck.py staged with no journal entry is refused as a RULE-CHANGE", not _missed, _missed)
with open(os.path.join(G, "log", "pending.md"), "a", encoding="utf-8", newline="\n") as fh:
    fh.write("\nA local note in the queue.\n")
run("git", "add", "log/pending.md", cwd=G)
out, rc = gate()
check("...and log/pending.md staged alone is not: the queue is kept here, and is no law",
      rc == 0 and "RULE-CHANGE" not in out, out[-400:])
run("git", "reset", "-q", "--hard", cwd=G)
# A GARDEN'S LAW IS LAW, however its entry is written: a pattern entry placing notes/*.md in law places notes/a.md there,
# and the duty is read from the same map every other tool reads.
standing('{ doc: "file:notes/*.md", standing: law, why: "the gardener\'s own rules" }')
r = run(sys.executable, os.path.join(G, "bin", "dmsave.py"), "sam", "RULE-CHANGE: the gardener's notes placed in law",
        "--body", "- action: [[sam]] places notes/*.md in law.", cwd=G)
with open(os.path.join(G, "notes", "a.md"), "a", encoding="utf-8", newline="\n") as fh:
    fh.write("\nA local edit.\n")
run("git", "add", "notes/a.md", cwd=G)
out, rc = gate()
check("...and an edit to notes/a.md, which the gardener's pattern entry places in law, staged alone is a RULE-CHANGE",
      r.returncode == 0 and rc == 1 and bool(said(out, "ERROR", "RULE-CHANGE", "notes/a.md")),
      (r.stdout + r.stderr)[-300:] + " | " + out[-400:])
# WHAT IS LAW DOES NOT MOVE UNSAID: the entry moved out of `law` and the file edited in one commit, journalled with no
# RULE-CHANGE, was judged by the map it staged — where notes/a.md was law no longer. The entry's own move carries it.
run("git", "reset", "-q", "--hard", cwd=G)
standing('{ doc: "file:notes/*.md", standing: words, why: "the gardener\'s own words now" }')
with open(os.path.join(G, "notes", "a.md"), "a", encoding="utf-8", newline="\n") as fh:
    fh.write("\nAnother local edit.\n")
r = run(sys.executable, os.path.join(G, "bin", "dmjournal.py"), "sam", "the notes are words now",
        "--body", "- action: [[sam]] places notes/*.md in words.", cwd=G)
run("git", "add", "-A", cwd=G)
out, rc = gate()
check("...and moving that entry out of law while editing the file, journalled with no RULE-CHANGE, is refused: the "
      "entry's own move carries the duty", r.returncode == 0 and rc == 1
      and bool(said(out, "ERROR", "RULE-CHANGE", "beans/sam.md")), (r.stdout + r.stderr)[-300:] + " | " + out[-500:])
clean()

check("NOTHING above ended in a traceback: every case is a refusal or a pass", not TRACES, TRACES[:2])
shutil.rmtree(T, ignore_errors=True)
print("\nlayers: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
