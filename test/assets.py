#!/usr/bin/env python3
"""The assets collection: what a release ships beside the law, read by one reader, and admitted only under rule 5.

An ASSET is a directory of the release named for a profile the law offers (`assets/<profile>/`): the code, the
templates and the guide that make the profile's facts useful. Opting into the profile is what brings the asset, and
leaving the profile takes it away. This holds:

  the one reader   seed/LANGUAGE is read by bin/pass.py alone: its lines without a profile give, over this release,
                   exactly the files the old per-line glob gave; a line naming `<profile>` gives an opted-in garden the
                   asset, takes it away from one that leaves, and never claims a garden's own file beside it; and every
                   tool and suite that opens seed/LANGUAGE hands its text to that reader
  rule 5           NO ASSET OPENS A CONCEPT OF ITS OWN, checked where it can be, for every profile that names an asset
                   (the core's profiles, core/law/profiles.yaml, v1 part 11; this suite in the core, v1 part 12):
                   1. every assets/<d>/ is a profile the core offers, whose row names it its `asset`;
                   2. in a garden of the core that takes the profile, a page of the smallest shape — the page's own
                      `draw` and one drawing's — is saved through the core's gate (what a profile gives, and where, is
                      the core's rule `profile`, held by test/core_view.py);
                   7. the asset's files sit in no hidden directory and name none a harness keeps, name nothing a garden
                      holds (the leak guard's own words, from a garden grown here and from the fixtures of test/view.py),
                      and write no word the law retired as a key (the upgrade's own finder of them). Which of its
                      modules open a network path is test/manifesto.py's, held there with the release's tools.
                   8. a technology daftar says it speaks has its adapter and its suite in the release.
                   Today's checks 3-6 (a profile's registries, its names' senses, its schema-language keys, its reasons
                   keyed by path) were of today's terms, which the core does not have: test/ported.yaml says where each
                   went. Whether a profile states a new kind of fact about the world is the ratifier's judgment.
"""
import glob, os, re, shutil, subprocess, sys, tempfile
import yaml
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import importlib
import parse as dmparse
dmpass = importlib.import_module('pass')
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)


def read(rel):
    with open(os.path.join(ROOT, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read()


LAW = yaml.safe_load(read("core/law/profiles.yaml")) or {}          # the core's profiles (v1 part 11)
LINES = dmpass.language(read("seed/LANGUAGE"))
OFFERED = dmpass.offered(LAW)                                       # a list of rows, each its `profile`
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
_lines = ["bin/tool.py", "assets/%s/*" % dmpass.PLACE]
_tree = ["bin/tool.py", "assets/alpha/bin/tool.py", "assets/alpha/lib/deep/part.py", "assets/beta/README.md",
         "assets/logo.png", "assets/gamma/x.py"]
_offer = ["alpha", "beta"]
_in = dmpass.received(_tree, _lines, ["alpha"], _offer)
_out = dmpass.received(_tree, _lines, [], _offer)
_have = dmpass.kept(_tree + ["assets/logo.png"], _lines, _offer)
check("a garden extending a profile receives its asset, `*` crossing `/`, and no other profile's",
      _in == ["assets/alpha/bin/tool.py", "assets/alpha/lib/deep/part.py", "bin/tool.py"], _in)
check("...and leaving it, the asset is what the release keeps and the garden no longer receives: it is taken away",
      sorted(set(_have) - set(_out)) == ["assets/alpha/bin/tool.py", "assets/alpha/lib/deep/part.py",
                                         "assets/beta/README.md"], sorted(set(_have) - set(_out)))
check("...a garden's own assets/logo.png, and the directory of a profile the law does not offer, are never the release's",
      "assets/logo.png" not in _have and "assets/gamma/x.py" not in _have
      and "assets/gamma/x.py" not in dmpass.received(_tree, _lines, ["gamma"], _offer), _have)
check("...and the keeper of the layer map reads the same line: a file of a profile's asset is kept by the release",
      dmpass.expand(_lines, _offer) == ["bin/tool.py", "assets/alpha/*", "assets/beta/*"], dmpass.expand(_lines, _offer))

# EVERY READER ASKS IT. A file of the release that opens seed/LANGUAGE hands the text to pass.language; none splits it,
# and none globs its lines, on its own.
_opens = re.compile(r"""join\([^\n]*['"]LANGUAGE['"]|open\([^\n]*seed/LANGUAGE""")
_own = [f for f in FILES if f.endswith(".py") and f != "bin/pass.py" and _opens.search(read(f))
        and not re.search(r"\b(_?|dm)pass\.language\(", read(f))]
check("every tool and suite that opens seed/LANGUAGE reads it through bin/pass.py, and none on its own", not _own, _own)

# ------------------------------------------------------------------ rule 5
ASSETS = sorted(d for d in os.listdir(os.path.join(ROOT, "assets"))
                if os.path.isdir(os.path.join(ROOT, "assets", d))) if os.path.isdir(os.path.join(ROOT, "assets")) else []
PROFILES = {str(r["profile"]): r for r in LAW.get("profiles") or [] if isinstance(r, dict) and r.get("profile")}
NAMING = sorted(p for p, r in PROFILES.items() if r.get("asset"))
ASSETED = sorted(set(ASSETS) | set(NAMING))

# 1. EVERY ASSET IS A PROFILE'S, AND BEARS ITS NAME.
_bad1 = [d for d in ASSETS if d not in OFFERED or PROFILES[d].get("asset") != f"assets/{d}"]
check(f"1. every assets/<d>/ is a profile the core offers, whose row names it its asset ({', '.join(ASSETS) or 'none yet'})",
      not _bad1, _bad1)
check("...and every profile whose row names an asset has it, and at least one does",
      len(ASSETS) >= 1 and all(os.path.isdir(os.path.join(ROOT, *str(PROFILES[p]["asset"]).split("/"))) for p in NAMING),
      f"named: {NAMING}; present: {ASSETS}")

# 2. IN A GARDEN OF THE CORE THAT TAKES THE PROFILE, A PAGE OF THE SMALLEST SHAPE IS SAVED THROUGH THE CORE'S GATE.
sys.path.insert(0, os.path.join(ROOT, "test"))
import grow  # noqa: E402
_T = tempfile.mkdtemp(prefix="dmassets-")
_G = os.path.join(_T, "garden-a")
_r = grow.garden(grow.release(os.path.join(_T, "release")), _G, "sam", *[x for p in ASSETED for x in ("--profile", p)])
with open(os.path.join(_G, "beans", "sam-page.md"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("""---
bean: sam-page
kind: service
title: "Sam's page"
summary: "A page of one drawing."
statements:
  - say: { by: sam, at: now }
  - own: { by: sam, of: self }
  - draw: { id: kept, by: self, of: [sam], drawing: { purpose: Keeps the garden., outcome: The garden is kept., stages: [ { label: keep it, doer: sam } ], questions: [ { lens: orient, ask: 'Who keeps it?' } ], archetype: health-chain, blind: [ { what: nothing is measured, why: no monitor is recorded } ] } }
  - draw: { id: page, by: self, of: [kept], page: { drawings: 'file:bin/drawings.py' } }
---
A page of one drawing.
""")
os.makedirs(os.path.join(_G, "bin"), exist_ok=True)
with open(os.path.join(_G, "bin", "drawings.py"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("COMPOSERS = {}\n")
_save = grow.run(sys.executable, "bin/save.py", "sam", "a page", "--body", "- action: wrote [[sam-page]]", cwd=_G)
check(f"2. in a garden of the core taking {', '.join(ASSETED)}, a page of the smallest shape is saved through the core's "
      "gate", _r.returncode == 0 and _save.returncode == 0 and "— 0 error(s)" in _save.out, _r.out[-300:] + _save.out[-500:])
# 7. NO HARNESS, NO ESTATE, NO RETIRED WORD in an asset's files — asked of the garden grown for check 2 while it stands.
import public as dmpublic  # noqa: E402
# a word today's law retired as a key, in code (the 22.0 step's own list, which v0.49.0's bin/dmupgrade.py keeps)
CODE_WORD = re.compile(r"""(['"])(?:kind|kinds|local_kinds|form_kind|physical|metaphysical|living)\1"""
                       r"""|\b(?:kind|kinds|local_kinds|form_kind):\s|\bnature:\s*['"]?(?:physical|metaphysical|living)\b"""
                       r"""|\bcrown:\s*['"]?(?:love|nature|god)\b""")
CODE_EXT = ('.py', '.js', '.mjs', '.cjs', '.ts', '.sh', '.ps1', '.psm1', '.rb', '.go', '.pl', '.php', '.lua')
_AFILES = [f for f in FILES if f.startswith("assets/")]
_hidden = sorted({s for f in FILES for s in f.split("/")[:-1] if s.startswith(".")})
_harness = [(f, d) for f in _AFILES for d in _hidden if re.search(r"(?<![\w.])%s/" % re.escape(d), read(f))] + \
           [(f, "a hidden directory") for f in _AFILES if any(s.startswith(".") for s in f.split("/")[:-1])]
_fixture_ids = set(re.findall(r'(?m)^    "([a-z0-9][a-z0-9-]*)": \'\'\'(?:bean|mapping): ', read("test/view.py")))
_words = (dmpublic.estate_words(_G, dmpublic.public_words(_G)) | {w for w in _fixture_ids if len(w) >= 4}) \
         - dmpublic.public_words(_G)
_leak = [(f, w) for f in _AFILES for w in dmpublic.hits(read(f), _words)]
_retired = [(f, n) for f in _AFILES if f.endswith(CODE_EXT)
            and not f.endswith("_core.py")     # an asset's reader of the core (v1 part 11) writes the core's words, and
            # `kind` is the core's name of today's genos (core/law/kinds.yaml), not the word 22.0 retired
            for n, line in enumerate(read(f).split("\n"), 1) if CODE_WORD.search(line)]
check(f"7. an asset's {len(_AFILES)} files name no harness directory and sit in no hidden one, name nothing a garden "
      f"holds ({len(_words)} words: the grown garden's and the fixtures'), and write no retired word as a key",
      _AFILES and len(_fixture_ids) >= 5 and not _harness and not _leak and not _retired,
      {"harness": _harness, "estate": _leak, "retired": _retired, "fixture ids": sorted(_fixture_ids)})
shutil.rmtree(_T, ignore_errors=True)


# 8. WHAT DAFTAR SPEAKS (31.0): a technology is spoken only where its adapter is a file of this release and the suite it
# names is one of this release's; planned otherwise, naming neither; and every code is a row of the technology catalogue.
def _tsv(rel):
    with open(os.path.join(ROOT, *rel.split("/")), encoding="utf-8") as fh:
        rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
    return [dict(zip(rows[0], r)) for r in rows[1:]]
_tech = {r["code"] for r in _tsv("seed/knowledge/technology.tsv")}
_bad7 = []
for r in _tsv("seed/knowledge/technology-daftar.tsv"):
    if r.get("code") not in _tech:
        _bad7.append(f"{r.get('code')}: no row of the technology catalogue")
    if r.get("role") not in ("source", "surface", "carrier"):
        _bad7.append(f"{r.get('code')}: role {r.get('role')!r} is not source, surface or carrier")
    if r.get("status") == "spoken":
        if not os.path.isfile(os.path.join(ROOT, *str(r.get("adapter")).split("/"))):
            _bad7.append(f"{r.get('code')}: spoken, and its adapter {r.get('adapter')} is no file of the release")
        if not os.path.isfile(os.path.join(ROOT, *str(r.get("passed")).split("/"))):
            _bad7.append(f"{r.get('code')}: spoken, and the suite it names, {r.get('passed')}, is none of the release's")
    elif r.get("status") == "planned":
        if r.get("adapter") != "-" or r.get("passed") != "-":
            _bad7.append(f"{r.get('code')}: planned, and it names an adapter or a suite")
    else:
        _bad7.append(f"{r.get('code')}: status {r.get('status')!r} is neither spoken nor planned")
for r in _tsv("seed/knowledge/signals.tsv"):
    if r.get("instrument") not in ("histogram", "counter", "updowncounter", "gauge") or not r.get("unit"):
        _bad7.append(f"signal {r.get('signal')}: instrument {r.get('instrument')!r} and unit {r.get('unit')!r}")
check("8. a technology daftar says it speaks has its adapter and its suite in the release, one it plans names neither, "
      "every one is a row of the catalogue, and every signal has an instrument and a unit", not _bad7, _bad7)

print("\nassets: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
