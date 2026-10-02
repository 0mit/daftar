#!/usr/bin/env python3
"""The gate's cost per 10,000 series rows (SCALE, 24.0: machinery step 0), measured before anything population-sized
moves (N34: the changed-part gate is judged, and not built, until this is read).

    python3 test/cost.py [--rows 10000,100000,350000] [--repeat 3] [--no-record]

A garden of the core is grown from this tree as a release (test/grow.py, v1 part 12), and one invented bench rig added
to it; the core's gate (`core/check.py`) is timed on the garden without a series, then with the rig's `record` of a grid
series of N rows × 2 channels written as one part (`series/<bean>/<id>/<part>.tsv`, core/lines.py's form), each
with libyaml's loader and with the pure-Python one (dmparse falls back to it where PyYAML has no libyaml; a
`sitecustomize` hides libyaml from the child). The best of `--repeat` runs is kept. Each is appended to
test/timings.tsv as `date	cost:<loader>:<rows>	seconds	1|0	0|1` (the gate passed, or not), and the cost
per 10,000 rows printed: (with − without) / N × 10,000.
"""
import datetime, os, re, shutil, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSV = os.path.join(ROOT, "test", "timings.tsv")
PY = sys.executable
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmparse  # noqa: F401 — on the path for the loader probe below


def run(*a, cwd=None, env=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                          env=dict(os.environ, **(env or {})))


def main(argv):
    sizes, repeat, record = [10000, 100000, 350000], 3, True
    if "--rows" in argv:
        sizes = [int(x) for x in argv[argv.index("--rows") + 1].split(",")]
    if "--repeat" in argv:
        repeat = int(argv[argv.index("--repeat") + 1])
    record = "--no-record" not in argv
    T = tempfile.mkdtemp(prefix="dmcost-")
    try:
        sys.path.insert(0, os.path.join(ROOT, "test"))
        import grow                       # a garden of the core, grown from a release made of this tree (v1 part 12)
        g = os.path.join(T, "g")
        r = grow.garden(grow.release(os.path.join(T, "release")), g, "keeper")
        if r.returncode:
            print(r.out)
            return 1
        rig = ("---\nbean: bench-rig\nkind: host\ntitle: \"bench-rig — an invented rig\"\n"
               "summary: \"An invented bench rig whose flow and outlet temperature are logged each minute.\"\n"
               "statements:\n  - read: { by: keeper, at: \"2026-09-26 10:00+00:00\" }\n  - own: { by: keeper, of: self }\n"
               "  - record:\n      id: log\n      of: self\n      series:\n"
               "        grid: { of: time, in: gregorian-civil, every: { count: \"1\", unit: min }, from: \"2026-01-01 00:00+00:00\" }\n"
               "        unit: min\n        holds:\n"
               "          - { name: flow, quantity: volume-flow, unit: l/min, stands_for: point }\n"
               "          - { name: outlet, quantity: ratio, unit: \"%%\", stands_for: point }\n"
               "%s---\nAn invented rig.\n")
        part = os.path.join(g, "series", "bench-rig", "log", "0.tsv")
        shim = os.path.join(T, "pure")
        os.makedirs(shim)
        open(os.path.join(shim, "sitecustomize.py"), "w").write("import yaml\ntry:\n    del yaml.CSafeLoader\nexcept AttributeError:\n    pass\n")
        loaders = {"libyaml": {}, "pure": {"PYTHONPATH": shim}}
        probe = run(PY, "-c", "import sys; sys.path.insert(0, 'bin'); import dmparse; print(dmparse.FAST)", cwd=g, env=loaders["pure"])
        if probe.stdout.strip() != "False":
            print("cost: the pure-Python loader could not be forced (%s)" % (probe.stdout + probe.stderr).strip())
            return 1

        def gate(env):
            best, ok = None, False
            for _ in range(repeat):
                t0 = time.perf_counter()
                r = run(PY, os.path.join(g, "core", "check.py"), ".", cwd=g, env=env)
                s = time.perf_counter() - t0
                best = s if best is None else min(best, s)
                ok = r.returncode == 0 and re.search(r" 0 error\(s\)", r.stdout + r.stderr) is not None
                if not ok:
                    print((r.stdout + r.stderr)[-1200:])
            return best, ok

        lines, day = [], datetime.date.today().isoformat()
        for name, env in loaders.items():
            open(os.path.join(g, "beans", "bench-rig.md"), "w").write(rig % "        rows: |\n          flow\toutlet\n          0\t10\n")
            if os.path.exists(part):
                os.remove(part)
            base, ok = gate(env)
            print("%-8s %8s rows: %7.2f s%s" % (name, 0, base, "" if ok else "  (the gate refused)"))
            lines.append((day, "cost:%s:0" % name, base, ok))
            for n in sizes:
                open(os.path.join(g, "beans", "bench-rig.md"), "w").write(rig % "")
                os.makedirs(os.path.dirname(part), exist_ok=True)
                with open(part, "w", newline="\n") as fh:
                    fh.write("flow\toutlet\n")
                    fh.writelines("%d.%d\t%d\n" % (i % 7, i % 10, 10 + i % 60) for i in range(n))
                s, ok = gate(env)
                print("%-8s %8d rows: %7.2f s   %.2f s per 10,000 rows%s" % (name, n, s, (s - base) / n * 10000,
                                                                           "" if ok else "  (the gate refused)"))
                lines.append((day, "cost:%s:%d" % (name, n), s, ok))
        if record:
            new = not os.path.isfile(TSV)
            with open(TSV, "a", encoding="utf-8", newline="\n") as fh:
                if new:
                    fh.write("date\tsuite\tseconds\tpassed\tfailed\n")
                for d, k, s, ok in lines:
                    fh.write("%s\t%s\t%.2f\t%d\t%d\n" % (d, k, s, 1 if ok else 0, 0 if ok else 1))
            print("cost: %d line(s) added to test/timings.tsv" % len(lines))
        return 0 if all(ok for *_x, ok in lines) else 1
    finally:
        shutil.rmtree(T, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
