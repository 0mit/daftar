#!/usr/bin/env python3
"""The assets collection: what a release ships beside the law, read by one reader, and admitted only under rule 5.

An ASSET is a directory of the release named for a profile the law offers (`assets/<profile>/`): the code, the
templates and the guide that make the profile's facts useful. Opting into the profile is what brings the asset, and
leaving the profile takes it away. This holds:

  the one reader   seed/LANGUAGE is read by bin/dmpass.py alone: its lines without a profile give, over this release,
                   exactly the files the old per-line glob gave; a line naming `<profile>` gives an opted-in garden the
                   asset, takes it away from one that leaves, and never claims a garden's own file beside it; and every
                   tool and suite that opens seed/LANGUAGE hands its text to that reader
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

print("\nassets: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
