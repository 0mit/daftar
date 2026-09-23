#!/usr/bin/env python3
"""dmknowledge — read the knowledge the vocabulary points at (the `knowledge` profile, std-vocab 9.1).

Published classifications are UNIVERSAL ANCHORS: ISCED-F 2013 fields of knowledge, ISCO-08 occupations, and a
curated catalogue of established technologies, each row naming the project's own official documentation. They
live whole in seed/knowledge/, declared by `registry_files` in seed/std-vocab.md; this tool finds them the same
way the gate does, so it can never read a different file than the law declares.

    python3 bin/dmknowledge.py show isco-08 2522          # one code, its ancestry, and what it links to
    python3 bin/dmknowledge.py tree isced-f-2013 06       # a subtree
    python3 bin/dmknowledge.py find samba                 # search codes and titles in every scheme
    python3 bin/dmknowledge.py bean <bean-id>             # a bean's `knowledge:` entries, resolved
    python3 bin/dmknowledge.py crosswalk 2522             # the fields an occupation draws on

As a library, for a program built on a garden: `Knowledge(root)` with `.row(scheme, code)`,
`.ancestry(scheme, code)`, `.resolve(entry)` and `.for_bean(front_matter)`.
"""
import os, sys, csv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dmparse

SCHEMES = ("isced-f-2013", "isco-08", "technology")


class Knowledge:
    def __init__(self, root):
        self.root = root
        vocab = os.path.join(root, "seed", "std-vocab.md")
        fm = dmparse.loads(dmparse.read(vocab)[0]) or {}
        self.decl = {r["registry"]: r for r in (fm.get("registry_files") or [])}
        self.schemes = {r["scheme"]: r for r in (fm.get("knowledge_schemes") or [])}
        self._rows = {}

    def rows(self, registry):
        if registry not in self._rows:
            d = self.decl.get(registry)
            if not d:
                raise KeyError("no registry %r is declared in seed/std-vocab.md registry_files" % registry)
            with open(os.path.join(self.root, d["file"]), encoding="utf-8") as fh:
                self._rows[registry] = list(csv.DictReader(fh, delimiter="\t"))
        return self._rows[registry]

    def row(self, scheme, code):
        key = self.decl.get(scheme, {}).get("key", "code")
        return next((r for r in self.rows(scheme) if r.get(key) == str(code)), None)

    def ancestry(self, scheme, code):
        """[root, …, code] as rows, for a hierarchical scheme; [row] for a flat one."""
        out, r = [], self.row(scheme, code)
        while r:
            out.insert(0, r)
            r = self.row(scheme, r.get("parent")) if r.get("parent") else None
        return out

    def label(self, scheme, code, lang="en"):
        r = self.row(scheme, code)
        if not r:
            return None
        return r.get("name_%s" % lang) or r.get("name_en") or r.get("name")

    def resolve(self, entry):
        """A `knowledge:` entry -> {scheme, code, rel, topic, label, path, docs, homepage, fields, occupations}."""
        sch, code = entry.get("scheme"), str(entry.get("code"))
        r = self.row(sch, code) or {}
        out = {"scheme": sch, "code": code, "rel": entry.get("rel"), "topic": entry.get("topic", ""),
               "label": r.get("name_en") or r.get("name") or "",
               "path": [a.get("name_en") for a in self.ancestry(sch, code)] if sch != "technology" else [r.get("name", "")],
               "docs": r.get("docs", ""), "homepage": r.get("homepage", ""), "category": r.get("category", "")}
        if sch == "technology":
            out["fields"] = [{"code": c, "label": self.label("isced-f-2013", c)} for c in (r.get("isced_f_2013") or "").split(";") if c]
            out["occupations"] = [{"code": c, "label": self.label("isco-08", c)} for c in (r.get("isco_08") or "").split(";") if c]
        return out

    def for_bean(self, fm):
        return [self.resolve(e) for e in (fm.get("knowledge") or []) if isinstance(e, dict)]

    def crosswalk(self, isco):
        return [r for r in self.rows("crosswalk-isco-08-isced-f-2013") if r.get("isco_08") == str(isco)]


def main():
    root = os.path.dirname(HERE)
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return
    k = Knowledge(root)
    cmd = a[0]
    if cmd == "show" and len(a) >= 3:
        for r in k.ancestry(a[1], a[2]):
            print("%-6s %-10s %s%s" % (r.get("code"), r.get("level", r.get("category", "")), r.get("name_en") or r.get("name"),
                                       ("   docs: " + r["docs"]) if r.get("docs") else ""))
        if a[1] == "technology":
            e = k.resolve({"scheme": a[1], "code": a[2]})
            print("  draws on: " + "; ".join("%s %s" % (f["code"], f["label"]) for f in e["fields"]))
            print("  run by:   " + "; ".join("%s %s" % (o["code"], o["label"]) for o in e["occupations"]))
        if a[1] == "isco-08":
            for r in k.crosswalk(a[2])[:8]:
                print("  draws on %s %s  (core %s, common %s, specialist %s; %s)" % (r["isced_f_2013"], k.label("isced-f-2013", r["isced_f_2013"]),
                      r["core"], r["common"], r["specialist"], r["topics"]))
    elif cmd == "tree" and len(a) >= 2:
        pre = a[2] if len(a) > 2 else ""
        for r in k.rows(a[1]):
            if r.get("code", "").startswith(pre):
                print("%s%s  %s" % ("  " * (len(r["code"]) - len(pre)), r["code"], r.get("name_en") or r.get("name")))
    elif cmd == "find" and len(a) >= 2:
        q = " ".join(a[1:]).lower()
        for s in SCHEMES:
            for r in k.rows(s):
                if q in " ".join(str(v) for v in r.values()).lower():
                    print("%-13s %-8s %s" % (s, r.get("code"), r.get("name_en") or r.get("name")))
    elif cmd == "bean" and len(a) >= 2:
        p = os.path.join(root, "beans", a[1] + ".md")
        fm = dmparse.loads(dmparse.read(p)[0]) or {}
        for e in k.for_bean(fm):
            print("%-13s %-8s %-13s %s%s" % (e["scheme"], e["code"], e["rel"], e["label"], ("  docs: " + e["docs"]) if e["docs"] else ""))
    elif cmd == "crosswalk" and len(a) >= 2:
        for r in k.crosswalk(a[1]):
            print("%s %s  core %s common %s specialist %s  roles %s  %s" % (r["isced_f_2013"], k.label("isced-f-2013", r["isced_f_2013"]),
                  r["core"], r["common"], r["specialist"], r["roles"], r["topics"]))
    else:
        print(__doc__); sys.exit(2)


if __name__ == "__main__":
    main()
