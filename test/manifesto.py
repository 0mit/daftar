#!/usr/bin/env python3
"""The manifesto is stated once, above the law, and everything else points to it.

MANIFESTO.md says what daftar holds to; the law, the tools and the guides carry it, and name the clause they carry.
This holds the separation: each clause is one sentence under a key of its own, in the present tense, naming nothing
beneath it; every cite names a clause that exists; every clause is carried where a gate or a step applies it, or says
why it is only stated; a clause's words appear elsewhere only as a marked quote held equal to it, or at a place that
must carry them; and the count of the rest may only go DOWN, release by release.
"""
import glob, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmparse, dmreview
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)


text = open(os.path.join(ROOT, "MANIFESTO.md"), encoding="utf-8").read()
GROUPS = ["The stance", "What daftar is for", "The principles", "What daftar never does", "Adherence"]
check("the manifesto has its five groups, in order", re.findall(r"(?m)^## (.+)$", text) == GROUPS,
      re.findall(r"(?m)^## (.+)$", text))

# ONE KEY, ONE SENTENCE. `### <key>` and one sentence beneath it: the key is what everything beneath cites, and what
# `dmwhy doc:MANIFESTO.md#<key>` resolves by the heading it already matches.
CLAUSES = dmreview.manifesto_clauses(text)
check("every clause has a key of its own, and no key is used twice",
      len(CLAUSES) == len(re.findall(r"(?m)^### ", text)) >= 30, sorted(CLAUSES))


def _sentences(s):
    s = re.sub(r'"[^"]*"|«[^»]*»', "q", s)               # a question quoted inside a clause is not a second sentence
    return len(re.findall(r"[.?!](?=\s|$)", s))


many = [k for k, v in CLAUSES.items() if _sentences(v) != 1 or not v.endswith(".")]
check("each clause is one sentence", not many, many)

# PRESENT TENSE, NO STORY: the one definition test/rationale.py and `dmreview --law` read.
told = dmreview.story_in({"clauses": [{"clause": k, "meaning": v} for k, v in CLAUSES.items()]})
check("the manifesto tells no story: no date, no release, no finding", not told, told)

# IT NAMES NOTHING BENEATH IT, so it is read alone and outlives every file it would have named.
BENEATH = re.compile(r"`|\b[\w./-]+\.(?:md|py|sh|tsv|yaml)\b|\b(?:bin|seed|log|test)/|RATIONALE|HISTORY|std-vocab|RULE-CHANGE")
down = [k for k, v in CLAUSES.items() if BENEATH.search(v)]
check("the manifesto names no file, tool or law item beneath it", not down, down)

# ------------------------------------------------------------------ what everything beneath says of it
files = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True, encoding="utf-8").stdout.split()
TEXT = {f: open(os.path.join(ROOT, f), encoding="utf-8", errors="replace").read() for f in files
        if os.path.isfile(os.path.join(ROOT, f))
        and (f.endswith((".md", ".py", ".sh", ".html", ".yaml", ".svg", ".template", ".toml"))
             or f in ("LICENSE", "NOTICE", "seed/LANGUAGE"))}
CITE = re.compile(r"\bmanifesto:\s*([a-z][a-z-]*(?:,\s*[a-z][a-z-]*)*)")
cites = {}
for f, t in TEXT.items():
    if f.startswith(dmreview.MANIFESTO_EXEMPT):
        continue
    for m in CITE.finditer(t):
        for k in re.split(r",\s*", m.group(1)):
            cites.setdefault(k, []).append(f"{f}:{t.count(chr(10), 0, m.start()) + 1}")
orphan = sorted(k for k in cites if k not in CLAUSES)
check("every cite names a clause the manifesto has", not orphan, [(k, cites[k][:2]) for k in orphan])

# CARRIED, OR SAID TO BE ONLY STATED — every position accounted for, as the law's own are.
OPERATIVE = ("MODEL.md", "CHECKLIST.md", "MERGE.md", "CONTRIBUTING.md", "CHARTER.md", "LICENSE", "AGENTS.md",
             "seed/WELCOME.md", "bin/", "test/")
STATED = {   # a clause no gate or step can apply, and why
    "serve":  "the stance every clause beneath carries, and none alone",
    "ground": "a stance toward states and registries; nothing in a garden can apply it",
    "safety": "carried in part by consent and dmpublic; where a person stands on the line is theirs to say, not a gate's",
    "lawful": "the law in force is outside every garden",
    "light":  "a way of working, not a rule",
}
uncarried = [k for k in CLAUSES if k not in STATED and not any(w.startswith(OPERATIVE) for w in cites.get(k, []))]
check("every clause is carried where a gate or a step applies it, or says why it is only stated", not uncarried,
      uncarried)
check("...and a clause said to be only stated is one the manifesto has",
      not [k for k in STATED if k not in CLAUSES], [k for k in STATED if k not in CLAUSES])

# ------------------------------------------------------------------ SECOND STATEMENTS of a clause
bad = [(f, k) for f, t in TEXT.items() for k, q in dmreview.MANIFESTO_QUOTE.findall(t)
       if " ".join(re.sub(r"<[^>]+>|[*>_]", " ", q).split()) != CLAUSES.get(k)]
check("a marked quote of a clause is the clause, word for word", not bad, bad)
# What a page draws from the seed is counted where the seed holds it, so the drawing is not a second statement of its own:
# the map's blocks are left out by bin/dmreview.py itself, and the terminology page a release before the one page drew
# is named here, so the ceiling read at that release counts it the same way.
MIRROR = ('site/terminology.html',)
here = dmreview.Tree()
hits = [h for h in dmreview.manifesto_restatements(here) if h[0] not in MIRROR]
_tag = subprocess.run(["git", "-C", ROOT, "describe", "--tags", "--abbrev=0", "--match", "v[0-9]*.[0-9]*.[0-9]*",
                       "--exclude", "*-*"], capture_output=True, text=True, encoding="utf-8").stdout.strip()
_then = dmreview.manifesto_restatements(dmreview.Tree(_tag)) if _tag else None
_then = [h for h in _then if h[0] not in MIRROR] if _then is not None else None
RESTATED_AT_START = 35       # measured on the commit that adds the manifesto; a release that carries it takes over
if _then is not None:
    ceiling, since = len(_then), _tag
else:
    ceiling, since = RESTATED_AT_START, "no release carries the manifesto yet: the constant"
check(f"second statements of the manifesto have not grown (now {len(hits)}, ceiling {ceiling} — {since})",
      len(hits) <= ceiling, [f"{f} {k}" for f, k in hits][:12])
print(f"      (the next release's ceiling is {len(hits)}; `python3 bin/dmreview.py --law` lists every one)")

# ------------------------------------------------------------------ one word, one sense; no verdict reads it
two = [f for f, t in TEXT.items() if not f.startswith(dmreview.MANIFESTO_EXEMPT + MIRROR)
       and re.search(r"\bMANIFEST\.md\b|\bthe manifesto\b[^.\n]*\bGARDEN\.md\b|\bGARDEN\.md\b[^.\n]*\bmanifesto\b", t)]
check("GARDEN.md is the law's `manifest`, MANIFESTO.md is the manifesto, and neither is called the other", not two, two)
readers = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "bin", "*.py"))
                 if "MANIFESTO" in open(f, encoding="utf-8").read())
check("no verdict reads the manifesto: the law carries it, and only the readers of keys open it",
      set(readers) <= {"why.py", "review.py"}, readers)
_NET = re.compile(r"^\s*(?:import|from)\s+(?:urllib|http|socket|requests|ftplib|smtplib)\b", re.M)
net = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "bin", "*.py"))
             if _NET.search(open(f, encoding="utf-8").read()))
TOOL_NET = {   # each with why: never-sells is "never … anywhere its gardener did not send it"
    "dmupgrade.py": "it fetches a release, from where the gardener's pin says",
    "dmlaunch.py": "it sends a request only to a party the gardener's own VOCAB.md row grants by name, on a basis",
}
check("a tool opens a network path only where it is declared to, each with why (manifesto: never-sells)",
      set(net) <= set(TOOL_NET), f"found {net}; declared {sorted(TOOL_NET)}")
# AN ASSET'S CODE IS HELD THE SAME WAY, and more closely: a network module imported anywhere in an import line is found,
# and the modules that open a network path are exactly the ones declared here, each with why — a module added that
# opens one, or one declared that no longer does, fails by name.
_NET_ANY = re.compile(r"^\s*(?:import\s+[^\n#]*\b(?:urllib|http|socket|requests|ftplib|smtplib)\b"
                      r"|from\s+(?:urllib|http|socket|requests|ftplib|smtplib)\b)", re.M)
ASSET_NET = {
    "assets/view/lib/view_serve.py": "the served page listens for its signed-in viewers, on the address the host gives",
    "assets/view/lib/sources/prometheus.py": "the adapter asks the monitor the host's configuration names for values",
    "assets/view/lib/sources/http.py": "the adapter reads the one document at the address the host's configuration names",
}
asset_net = sorted({os.path.relpath(f, ROOT).replace(os.sep, "/") for pat in ("assets/*/bin/*.py", "assets/*/lib/**/*.py")
                    for f in glob.glob(os.path.join(ROOT, pat), recursive=True) if _NET_ANY.search(open(f, encoding="utf-8").read())})
check("an asset opens a network path only in the modules declared to, each with why (manifesto: never-sells)",
      asset_net == sorted(ASSET_NET), f"found {asset_net}; declared {sorted(ASSET_NET)}")
import dmpass                            # the one reader of seed/LANGUAGE
lang = dmpass.language(open(os.path.join(ROOT, "seed", "LANGUAGE"), encoding="utf-8").read())
check("every garden receives the manifesto, so every cite resolves where it is read", "MANIFESTO.md" in lang, lang)
# THE LAW NAMES A CLAUSE ONLY BY STRUCTURE. The vocabulary's front matter carries no `(manifesto: …)` in its prose: a
# meaning that cites a clause is a second statement waiting to happen. When the law points up, it will be by a
# declared attribute, not by a sentence.
prose_up = [l.strip()[:90] for l in dmparse.split_front_matter(TEXT["seed/std-vocab.md"])[0].split("\n")
            if CITE.search(l)]
check("the vocabulary names no clause in its prose", not prose_up, prose_up)

print("\nmanifesto: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
