#!/usr/bin/env python3
"""The suites' timings (SCALE, 24.0: machinery step 0): run each suite CI runs, and append one line per suite to
test/timings.tsv — `date	suite	seconds	passed	failed` — which `python3 bin/dmreckon.py order tests` reads beside
test/weighing.yaml to order the working loop (D41).

    python3 test/timings.py [test/x.py ...] [-j N] [--status FILE] [--no-record]

Every suite but test/site.py builds its own temporary gardens and writes nothing in the checkout, so they run N at a
time (default 6); test/site.py rebuilds the pages inside the checkout, so it runs first, alone. The slowest measured
start first, so the longest does not start last. A suite passes when it exits 0 and its last line says `0 failed` or
`N/N checks passed`; `passed` and `failed` count its PASS and FAIL lines (or the last line's own counts).

`--status FILE` keeps FILE, as each suite ends, one JSON document of the run in progress — `total`, `done`, `passed`,
`failed` (suites), `elapsed` and `left` (seconds; `left` estimated from the last measured line of each suite still to
run), `suites` ({suite: seconds}) and `verdicts` ({suite: passed|failed}) — which a page reads through the view asset's
`http` adapter as a `race` (test/viewcap.py draws one). This file is the maintainer's measurement, in the gate layer: it
names no garden and no person.
"""
import concurrent.futures, datetime, json, os, re, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSV = os.path.join(ROOT, "test", "timings.tsv")
HEAD = "date\tsuite\tseconds\tpassed\tfailed\n"


def listed():
    return re.findall(r"python3 (test/[a-z_]+\.py)", open(os.path.join(ROOT, ".github", "workflows", "ci.yml"), encoding="utf-8").read())


def last_seconds():
    """{suite: seconds} of each suite's last measured line."""
    out = {}
    if os.path.isfile(TSV):
        for ln in open(TSV, encoding="utf-8").read().splitlines()[1:]:
            c = ln.split("\t")
            if len(c) == 5 and c[1].startswith("test/"):
                try:
                    out[c[1]] = float(c[2])
                except ValueError:
                    pass
    return out


def counts(out, rc):
    lines = out.strip().splitlines()
    last = lines[-1] if lines else ""
    m = re.search(r"(\d+)/(\d+) checks passed", last)
    p = sum(1 for ln in lines if ln.startswith("PASS"))
    f = sum(1 for ln in lines if ln.startswith("FAIL"))
    if m:
        p, f = int(m.group(1)), int(m.group(2)) - int(m.group(1))
    n = re.search(r"\b(\d+) failed", last)
    if n:
        f = max(f, int(n.group(1)))
    ok = rc == 0 and ((n is not None and n.group(1) == "0") or (m is not None and m.group(1) == m.group(2)))
    return ok, p, f, last


def one(t):
    t0 = time.time()
    r = subprocess.run([sys.executable, t], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok, p, f, last = counts(r.stdout, r.returncode)
    return t, ok, time.time() - t0, p, f, last or (r.stderr.strip().splitlines() or ["(no output)"])[-1]


def main(argv):
    args, jobs, status, record = list(argv), 6, None, True
    if "-j" in args:
        i = args.index("-j"); jobs = int(args[i + 1]); del args[i:i + 2]
    if "--status" in args:
        i = args.index("--status"); status = os.path.abspath(args[i + 1]); del args[i:i + 2]
    if "--no-record" in args:
        args.remove("--no-record"); record = False
    tests = args or listed()
    before = last_seconds()
    start, results, lock = time.time(), [], threading.Lock()

    def said(res):
        with lock:
            results.append(res)
            t, ok, s, p, f, last = res
            print("%s  %-22s %6.0fs  %s" % ("PASS" if ok else "FAIL", t, s, last), flush=True)
            if status:
                todo = [x for x in tests if x not in {r[0] for r in results}]
                known = [before[x] for x in todo if x in before]
                doc = {"total": len(tests), "done": len(results), "passed": sum(1 for r in results if r[1]),
                       "failed": sum(1 for r in results if not r[1]), "elapsed": round(time.time() - start, 1),
                       "left": round(sum(known) / max(1, min(jobs, len(todo))), 1) if len(known) == len(todo) else None,
                       "suites": {r[0]: round(r[2], 1) for r in results},
                       "verdicts": {r[0]: "passed" if r[1] else "failed" for r in results}}
                tmp = status + ".tmp"
                with open(tmp, "w", encoding="utf-8") as fh:
                    json.dump(doc, fh)
                os.replace(tmp, status)            # a reader never meets half a document

    if "test/site.py" in tests:
        said(one("test/site.py"))
    rest = sorted((t for t in tests if t != "test/site.py"), key=lambda t: -before.get(t, 0))
    with concurrent.futures.ThreadPoolExecutor(jobs) as ex:
        for fut in concurrent.futures.as_completed([ex.submit(one, t) for t in rest]):
            said(fut.result())
    bad = [r[0] for r in results if not r[1]]
    if record:
        day = datetime.date.today().isoformat()
        new = not os.path.isfile(TSV)
        with open(TSV, "a", encoding="utf-8", newline="\n") as fh:
            if new:
                fh.write(HEAD)
            for t, ok, s, p, f, _l in sorted(results):
                fh.write("%s\t%s\t%.1f\t%d\t%d\n" % (day, t, s, p, f))
    print("\n%d suites in %.0fs: %s%s" % (len(results), time.time() - start,
                                          ("%d FAILED: %s" % (len(bad), ", ".join(bad))) if bad else "all green",
                                          ("; %d line(s) added to test/timings.tsv" % len(results)) if record else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
