#!/usr/bin/env python3
"""daftard: the daemon in daftard/ held at this commit — built, vetted and tested by Go, its reader held to this tree's
core/read.py, and its worker's own tests run against this tree.

daftard reads a garden twice: its Go reader (daftard/internal/garden) for what it serves fast, and the garden's own
Python (daftard/python/garden_worker.py, through the garden's core) for everything a gate decides. The two must read
every bean alike, so this grows a garden of the core from this tree (test/grow.py), lays beside its beans the worked
beans this tree's guides print (seed/FORMS.md, seed/COOKBOOK.md, seed/README.md), and has Go's test read each file of it
both ways (DAFTARD_CONFORMANCE), and the reader's hard cases read by the same core (DAFTARD_CORE). Then it runs, in
daftard/:

  go build ./...      go vet ./...      go test ./...      every package, the conformance among them
  test/worker/*_test.py and test/importers/*_test.py, each given this tree, as daftard/README.md says

Needs Go, the version daftard/go.mod names, on PATH; nothing is fetched to build (daftard/vendor/). The tests in
daftard/README.md that need an Odoo instance, a place bundle, Node or a browser are not run here.

Run: python3 test/daftard.py   (0 = green)
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "test"))
import grow  # noqa: E402

D = os.path.join(ROOT, "daftard")
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-2000:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=D, env=None, timeout=900, last=False):
    """A command's exit code and what it printed, its output then its errors; with `last`, its output's last line too."""
    try:
        p = subprocess.run(list(a), cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
        out = (p.stdout or "") + (p.stderr or "")
        tail = (p.stdout or "").strip().splitlines()[-1:] or [""]
        return (p.returncode, out, tail[0]) if last else (p.returncode, out)
    except subprocess.TimeoutExpired as e:
        return (124, f"timed out after {timeout} s: {e}", "") if last else (124, f"timed out after {timeout} s: {e}")


def worked_beans():
    """The whole beans the guides print, each a fenced block that opens as a bean opens: {name: text}."""
    out = {}
    for doc in ("seed/FORMS.md", "seed/COOKBOOK.md", "seed/README.md"):
        text = open(os.path.join(ROOT, doc), encoding="utf-8").read()
        for n, block in enumerate(re.findall(r"(?ms)^```[a-z]*\n(---\nbean: .*?\n---\n.*?)^```", text)):
            out[f"{os.path.basename(doc).lower().replace('.md', '')}-{n}"] = block
    return out


T = tempfile.mkdtemp(prefix="dmdaftard-")
try:
    go = shutil.which("go")
    check("Go is on PATH", go is not None, "daftard is built by Go; install the version daftard/go.mod names")
    if go:
        want = re.search(r"(?m)^go (\S+)$", open(os.path.join(D, "go.mod"), encoding="utf-8").read()).group(1)
        r, out = run(go, "version")
        print(f"      {out.strip()} (daftard/go.mod: go {want})")

        G = os.path.join(T, "g")
        g = grow.garden(grow.release(os.path.join(T, "release")), G, "sam", "--zone", "Europe/Istanbul")  # a runner
        # may name its zone otherwise (`UTC`)
        check("a garden of the core grows from this tree", g.returncode == 0, g.out)
        beans = worked_beans()
        for name, text in beans.items():
            with open(os.path.join(G, "beans", f"zz-{name}.md"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        read = sorted(glob.glob(os.path.join(G, "beans", "*.md")) + glob.glob(os.path.join(G, "mappings", "*.md")))
        check(f"...and the guides' worked beans lie beside its own ({len(beans)} of them, {len(read)} files to read)",
              len(beans) >= 10, sorted(beans))

        env = dict(os.environ, DAFTARD_CONFORMANCE=G, DAFTARD_CORE=G, DAFTARD_NOTIFY="off")
        r, out = run(go, "build", "./...", env=env)
        check("go build ./... — daftard and every package of its module", r == 0, out)
        r, out = run(go, "vet", "./...", env=env)
        check("go vet ./...", r == 0, out)
        r, out = run(go, "test", "-count=1", "./...", env=env, timeout=1800)
        check("go test ./... — every package of daftard", r == 0, out)
        r, out = run(go, "test", "-count=1", "-v", "-run", "TestConformance|TestHardCases", "./internal/garden/",
                     env=env)
        alike = re.search(r"(\d+) files read alike", out)
        check("its reader reads every bean and mapping of that garden as this tree's core/read.py does "
              f"({alike.group(1) if alike else 'no'} files read alike), and the hard cases alike",
              r == 0 and alike and int(alike.group(1)) == len(read) and "--- SKIP" not in out, out)

    py = sys.executable
    tests = sorted(glob.glob(os.path.join(D, "test", "worker", "*_test.py"))
                   + glob.glob(os.path.join(D, "test", "importers", "*_test.py")))
    check(f"daftard's worker has its tests ({len(tests)})", len(tests) >= 20, tests)
    # run as daftard runs its Python (daftard/internal/worker): in UTF-8 mode, whatever the system's own encoding
    env = dict(os.environ, DAFTARD_NOTIFY="off", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for t in tests:
        r, out, last = run(py, t, ROOT, env=env, last=True)
        name = os.path.relpath(t, D).replace(os.sep, "/")
        failed = "\n".join(ln for ln in out.splitlines() if ln.startswith("FAIL"))
        check(f"{name} against this tree: {last[:140]}", r == 0, (failed + "\n…\n" if failed else "") + out[-1500:])
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check(f"the suite ran to its end ({type(e).__name__}: {e})", False)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ndaftard: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
