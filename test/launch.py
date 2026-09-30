#!/usr/bin/env python3
"""Leg 2 (24.0): daftar's own loop, the save's trace, and the hooks for another maker's loop.

Grows a garden, opens a session on its branch, and runs `bin/dmlaunch.py` against an endpoint served here, in this
process, replaying scripted turns in both wires: an unlisted party is refused before a request is sent; each piece is a
render pass before the send; a re-read, a file in no layer and a write outside are refused; a save is claimed and the
gate is green. Then the save's trace (SAVE) on an invented table, where it refuses and where it only hopes; POST by
content; `record --keep`; and bin/dmhook.py's install, its refusals, and its failing closed. Every name is invented.
"""
import http.server, json, os, shutil, subprocess, sys, tempfile, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmpass                                              # noqa: E402

PY = sys.executable
FAILS, RUN = [], [0]


def check(name, cond, detail=""):
    RUN[0] += 1
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None, stdin=None, env=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                          input=stdin, env=env)


T = tempfile.mkdtemp(prefix="dmlaunch-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates from the release", r.returncode == 0 and "0 error" in r.stdout, r.stdout + r.stderr)


def write(rel, text):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read(rel):
    with open(os.path.join(G, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read()


def save(what, body=None):
    names = sorted({os.path.basename(l[3:].strip())[:-3] for l in run("git", "status", "--porcelain", "-uall", "beans",
                                                                        cwd=G).stdout.splitlines() if l.endswith(".md")})
    body = body or "- action: " + (" ".join(f"[[{n}]]" for n in names) or "the garden") + " — " + what
    r = run(PY, "bin/dmsave.py", "keeper (test)", what, "--body", body, cwd=G)
    return r.returncode, r.stdout + r.stderr


def restore(to="HEAD"):
    run("git", "reset", "-q", "--hard", to, cwd=G)
    run("git", "clean", "-qfd", "-e", "captures/runs", cwd=G)


def passes(slug="lease-talk"):
    try:
        return [json.loads(l) for l in read(f"captures/passes/{slug}.jsonl").splitlines() if l.strip()]
    except OSError:
        return []


BEAN = """---
bean: %s
genos: org
title: "%s"
status: active
summary: "%s"
nature: lekton
owned_by: { legal: { owner: { bean: keeper } } }
responsibility: { legal: { holder: { bean: keeper } } }
identity: { status: provisional, anchors: [] }
provenance: { src: asserted-by-human, by: keeper, as_of: now }
---
%s
"""
KEEPER = read("beans/keeper.md")
write("words/offer.md", "Bea's offer, as she wrote it: the shop on the corner, let from the first of May.\n")
write("scratch/plan.txt", "The rent we would never say aloud: nine hundred a month, Mill Lane side.\n")
write("beans/keeper.md", KEEPER.replace("provenance:", """standing:
  - { doc: "file:words/*", standing: words, why: "what a person gave this garden, kept as they gave it" }
provenance:""", 1))
write("beans/bea.md", BEAN % ("bea", "Corner Lets", "The company that lets the shop.", "The company that lets the shop."))
write("beans/lab.md", BEAN % ("lab", "Hilltop Model Lab", "The lab whose model the keeper runs.", "An invented lab."))
write("beans/laptop.md", """---
bean: laptop
genos: host
title: "the shop's laptop"
status: active
summary: "the machine the shop's garden is kept on"
nature: soma
os: linux
identity: { status: confirmed, anchors: [ { key: hostname, value: "shop-laptop", class: network, establishing: false }, { key: serial, value: "SN-SHOP-1", class: hardware, establishing: true } ] }
provenance: { src: asserted-by-human, by: keeper, as_of: now }
owned_by: { legal: { owner: { bean: keeper } } }
responsibility: { legal: { holder: { bean: keeper } } }
---
The laptop in the back room of the shop.
""")
rc, out = save("words placed; Bea, a lab and a laptop")
check("the fixture is committed", rc == 0, out)
MASTER = run("git", "rev-parse", "HEAD", cwd=G).stdout.strip()

# ============================ a session's copy, and an endpoint served here ============================
run("git", "checkout", "-q", "-b", "session/lease-talk", cwd=G)
write("beans/session-lease-talk.md", """---
bean: session-lease-talk
genos: session
title: "a session taking the lease down"
status: active
summary: "An agent's session that takes Bea's offer into the garden."
nature: lekton
provenance: { src: generated-by-tool, by: "bin/dmsession.py", as_of: now }
owned_by: { legal: { owner: { bean: keeper } } }
responsibility: { legal: { holder: { bean: keeper } } }
timing: { start: { system: gregorian-civil, at: "2026-04-21 10:00+03:00", unit: minute } }
workspace: { host: { bean: laptop }, system: unix-filesystem, at: "shop-laptop:/home/keeper/garden", branch: "session/lease-talk" }
---
An agent's session that takes the lease down.
""")
rc, out = save("the session's bean")
check("the session's bean is committed on its branch", rc == 0, out)

SEEN, SCRIPT = [], []


class Fake(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["content-length"])).decode("utf-8"))
        SEEN.append((self.path, body))
        reply = SCRIPT.pop(0) if SCRIPT else {"text": "done", "calls": []}
        if self.path.endswith("/messages"):
            out = {"content": ([{"type": "text", "text": reply["text"]}] if reply["text"] else []) +
                   [{"type": "tool_use", "id": f"t{len(SEEN)}{i}", "name": n, "input": a}
                    for i, (n, a) in enumerate(reply["calls"])]}
        else:
            out = {"choices": [{"message": {"role": "assistant", "content": reply["text"] or None, "tool_calls": [
                {"id": f"c{len(SEEN)}{i}", "type": "function", "function": {"name": n, "arguments": json.dumps(a)}}
                for i, (n, a) in enumerate(reply["calls"])] or None}}]}
        data = json.dumps(out).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


SRV = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake)
threading.Thread(target=SRV.serve_forever, daemon=True).start()
for k, v in (("endpoint", f"http://127.0.0.1:{SRV.server_port}/v1"), ("wire", "messages"), ("model", "fake-model"),
             ("party", "lab")):
    run("git", "config", f"daftar.{k}", v, cwd=G)
ENV = dict(os.environ, DAFTAR_API_KEY="invented-key")
TASK = ("Take the shop lease down: Corner Lets accepted on 2026-04-20 and the keeper on 2026-04-21; it was agreed "
        "aloud, spoken, on 2026-04-21.")


def launch(*a):
    r = run(PY, "bin/dmlaunch.py", *a, cwd=G, env=ENV)
    return r.returncode, r.stdout + r.stderr


# the party is the gardener's to grant — a loopback endpoint too
rc, out = launch("run", TASK)
check("an endpoint whose party no row of VOCAB.md grants: refused, 0 requests sent",
      rc == 2 and "not granted" in out and not SEEN, out)
check("...and nothing was logged, nor a store opened", not passes() and not os.path.exists(
    os.path.join(G, ".git", "daftar", "current")), out)
_v = read("VOCAB.md")
write("VOCAB.md", _v.replace("---\n", """---
flows:
  - { flow: send-to-lab, from: request, to: remote, method: send, grant: granted, party: lab,
      basis: "the keeper's own choice of model, on the lab's published terms", why: "the gardener grants this party" }
""", 1) if _v.count("---\n") >= 2 else _v)
rc, out = save("RULE-CHANGE: the keeper grants requests to the lab", "- action: RULE-CHANGE — VOCAB.md grants `send` to [[lab]]")
check("the gardener's grant of the party is committed", rc == 0, out)

LEASE = """---
bean: lease
genos: contract
title: "the shop lease"
status: active
summary: "Bea lets the shop to the keeper."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: identifier, value: "contract:lease", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: keeper, as_of: now }
owned_by: { legal: { crown: agape } }
responsibility: { legal: { parties: true } }
parties:
  bea: { who: { bean: bea }, accepted: %s }
  keeper: { who: { bean: keeper }, accepted: 2026-04-21 }
words: { form: spoken, agreed: 2026-04-21 }
---
The shop on the corner, let from the first of May.
"""
SCRIPT[:] = [
    {"text": "Reading the offer.", "calls": [("read", {"path": "words/offer.md"})]},
    {"text": "", "calls": [("read", {"path": "words/offer.md"}), ("read", {"path": "scratch/plan.txt"}),
                           ("write", {"path": "../outside.md", "content": "x"}),
                           ("write", {"path": "bin/dmcheck.py", "content": "x"})]},
    {"text": "", "calls": [("write", {"path": "beans/lease.md", "content": LEASE % "2026-04-20"}),
                           ("save", {"what": "the shop lease taken down", "body":
                                     "- action: [[lease]] taken down from the keeper's words; [[session-lease-talk]] logs its passes"})]},
    {"text": "The lease is taken down and saved.", "calls": []},
]
rc, out = launch("run", TASK)
check("a granted party: the loop runs to its end", rc == 0 and "saved and" not in out and len(SEEN) == 4, out)
_bodies = [b for _p, b in SEEN]
_tr = [blk for m in _bodies[-1]["messages"] for blk in m["content"] if blk.get("type") == "tool_result"]
check("a file read again, unchanged: refused (`again`)", any("in this request already" in t["content"] for t in _tr), _tr)
check("a file in no layer: refused (R4), and its words never sent",
      any("in no layer" in t["content"] for t in _tr) and not any("nine hundred" in json.dumps(b) for b in _bodies), _tr)
check("a write outside the session's copy, or into the gate: refused",
      sum("refused" in t["content"] and "writes inside its own copy" in t["content"] for t in _tr) == 2
      and read("bin/dmcheck.py") != "x", _tr)
_ps = passes()
_render = [p for p in _ps if p["method"] == "render"]
_sends = [p for p in _ps if p["method"] == "send"]
check("each request is preceded by its `send` pass, naming the party", len(_sends) == 4
      and all(p["metadata"]["party"] == "lab" for p in _sends), _sends)
check("each piece is one render pass, logged once: the task from `instructions`, the model's turns from `self`",
      len({p["metadata"]["seq"] for p in _render}) == len(_render)
      and any(p["from"] == {"layer": "instructions"} for p in _render)
      and sum(p["from"] == {"layer": "self"} for p in _render) == 4, _render)
_last = _bodies[-1]
check("the model's own earlier turns ride in the next request, by `composed-here`",
      [m["role"] for m in _last["messages"]][:3] == ["user", "assistant", "user"], _last["messages"][:3])
_log = run("git", "log", "-1", "--name-only", "--format=%s", cwd=G).stdout
check("a save made by the model is committed in the session's own garden, its log claimed and the gate green",
      "the shop lease taken down" in _log and "captures/passes/lease-talk.jsonl" in _log
      and "beans/lease.md" in _log, _log)
_take = [p for p in _ps if p["method"] == "take-down" and p["to"].get("bean") == "lease"]
check("the save traced each said value to the person's instructions, quoted as written",
      len(_take) == 6 and all(p["from"] == {"layer": "instructions"} and p["metadata"]["quoted"] >= 1 for p in _take),
      _take)
_by = {p["to"]["at"]: p["metadata"] for p in _take}
check("...each pass saying how many finds named one thing: a day is distinct, a short word (`spoken`) is found but "
      "proves little, and says so — `distinct: 0`",
      all(m.get("distinct", 0) >= 1 for a, m in _by.items() if "accepted" in a or "agreed" in a)
      and _by.get("words.form", {}).get("distinct") == 0 and _by.get("words.form", {}).get("quoted", 0) >= 1, _by)
check("...and the session's bean was given its pass_log", "captures/passes/lease-talk.jsonl" in read(
    "beans/session-lease-talk.md"))
check("the gate over the whole garden: 0 errors", " 0 error" in run(PY, "bin/dmcheck.py", "--all", cwd=G).stdout)

# the completeness invariant: the body against the log read back
sys.path.insert(0, os.path.join(G, "bin"))
import dmlaunch                                            # noqa: E402
_L = dmlaunch.Log(G, "captures/passes/lease-talk.jsonl")
_since = _L.next_seq()
_L.append({"layer": "instructions"}, {"layer": "request"}, "render", characters=5, seq=_since, turn=9)
check("a body whose pieces and the log's render passes differ: refused",
      dmlaunch.unlogged([{"seq": _since, "characters": 5}, {"seq": _since + 1, "characters": 3}], _L, _since)
      and dmlaunch.unlogged([{"seq": _since, "characters": 6}], _L, _since)
      and not dmlaunch.unlogged([{"seq": _since, "characters": 5}], _L, _since))
restore()

# the chat wire, the same loop
run("git", "config", "daftar.wire", "chat", cwd=G)
SEEN.clear()
SCRIPT[:] = [{"text": "", "calls": [("read", {"path": "words/offer.md"})]}, {"text": "Read it.", "calls": []}]
rc, out = launch("run", "Read Bea's offer.")
_c = SEEN[-1][1]["messages"] if SEEN else []
check("the chat wire: a tool's result goes back as role `tool`, by the call's id",
      rc == 0 and SEEN[0][0].endswith("/chat/completions") and any(m["role"] == "tool" and "first of May" in m["content"]
                                                                    for m in _c), out)
restore()
run("git", "config", "daftar.wire", "messages", cwd=G)

# ============================ SAVE: the trace, on the session's material ============================
S = dmlaunch.Session.current(G)
check("the session's material is kept per clone, off git", S is not None and S.dir.startswith(os.path.join(G, ".git"))
      and not run("git", "ls-files", ".git", cwd=G).stdout)
S.add("Oak Street Lets, accepted on 2026-03-02. Price 12.", {"file": "README.md"}, "guide")
write("beans/lease.md", LEASE % "2026-03-02")
rc, out = save("a lease whose day came from a guide")
check("a said value found only in a guide: refused by the save, before a word is written",
      rc == 2 and "examples-are-not-facts" in out and "nothing written" in out
      and "2026-03-02" not in read("log/journal.md"), out)
restore()
write("beans/lease.md", LEASE % "2026-06-30")
rc, out = save("a lease whose day nobody gave")
_h = [p for p in passes() if p["to"] == {"bean": "lease", "at": "parties.bea.accepted"}]
check("a said value found nowhere: saved, HOPED, its pass logged with quoted 0",
      rc == 0 and "HOPED" in out and _h and _h[-1]["metadata"]["quoted"] == 0, out)
restore()
rc, out = launch("record", "--keep", "meter-read", "--", PY, "-c", "print('the meter read on 2026-07-14')")
_cap = [p for p in passes() if p["method"] == "capture"]
check("record --keep: a run's output captured, its `capture` pass logged from the world",
      rc == 0 and os.path.exists(os.path.join(G, "captures", "runs", "meter-read.log")) and _cap
      and _cap[-1]["from"] == {"layer": "world"} and len(_cap[-1]["metadata"]["oid"]) == 40, out)
write("beans/lease.md", LEASE % "2026-07-14")
rc, out = save("a lease whose day a run observed")
_rec = [p for p in passes() if p["to"] == {"bean": "lease", "at": "parties.bea.accepted"}]
check("...and a said value read from it is traced to it, by `record`, and committed",
      rc == 0 and _rec and _rec[-1]["method"] == "record"
      and _rec[-1]["from"] == {"file": "captures/runs/meter-read.log"}, out)
restore()

# the trace on an invented table: where it refuses, against where a reader would
FL = dmpass.flows(G)
ORIGIN = FL.origin_at("parties.bea.accepted")
GOLD = [  # (value, [(layer, source, text)], skip, refused?)
    ("2026-03-02", [("guide", {"file": "README.md"}, "accepted 2026-03-02")], (), True),
    ("2026-03-02", [("guide", {"file": "README.md"}, "2026-03-02"), ("instructions", {"layer": "instructions"},
                                                                       "on 2026-03-02")], (), False),
    ("12", [("guide", {"file": "README.md"}, "price 12")], (), False),
    ("spoken", [("guide", {"file": "README.md"}, "spoken")], (), False),
    ("Oak Street Lets", [("self", {"layer": "self"}, "Oak Street Lets")], (), False),
    ("Oak Street Lets", [("estate", {"file": "beans/bea.md"}, "title: Oak Street Lets")], (), True),
    ("Oak Street Lets", [("estate", {"file": "beans/bea.md"}, "Oak Street Lets")], ("beans/bea.md",), False),
    ("48213", [("history", {"file": "captures/runs/m.log"}, "meter 48213")], (), False),
    ("the corner shop on Mill Lane", [("work", {"file": "notes/p.md"}, "the corner shop on Mill Lane")], (), True),
    ("Mill Lane", [("work", {"file": "notes/p.md"}, "Mill Lane"), ("words", {"file": "words/offer.md"}, "Mill Lane")],
     (), False),
    ("2026-03-02", [("guide", {"file": "README.md"}, "2026-03-020")], (), False),
]
_tp = _fp = _fn = 0
for v, ms, skip, want in GOLD:
    t = dmpass.trace(FL, v, ORIGIN, [({"layer": l, "from": s}, x) for l, s, x in ms], skip=set(skip))
    got = t.verdict == "refused"
    _tp, _fp, _fn = _tp + (got and want), _fp + (got and not want), _fn + (want and not got)
_prec, _rec = _tp / max(1, _tp + _fp), _tp / max(1, _tp + _fn)
check(f"the trace's refusals on {len(GOLD)} invented cases: precision {_prec:.2f}, recall {_rec:.2f} (floor 1.00)",
      _prec == 1 and _rec == 1, (_tp, _fp, _fn))

# ============================ POST: by content ============================
M = dmpass.Map.here(G)
IDX = dmpass.denied_lines(G, M, FL)
check("POST's index holds the lines of a file in no layer, and none of a file a request may carry",
      "scratch/plan.txt" in IDX.values() and "words/offer.md" not in IDX.values())
check("...and finds such a line whole in a tool's output",
      dmpass.post_hits("grep:\nThe rent we would never say aloud: nine hundred a month, Mill Lane side.\n", IDX)
      == {"scratch/plan.txt": 1})

# ============================ dmhook: advisory, failing closed ============================
run("git", "checkout", "-q", "master", cwd=G)
rc = run(PY, "bin/dmhook.py", "install", "claude-code", cwd=G)
_set = json.loads(read(".claude/settings.local.json"))
check("dmhook install: the harness's hooks in this clone's own settings, kept off git",
      rc.returncode == 0 and set(_set["hooks"]) == {"UserPromptSubmit", "PreToolUse", "PostToolUse", "SessionEnd"}
      and not run("git", "status", "--porcelain", cwd=G).stdout.strip(), rc.stdout + rc.stderr)


def hook(verb, ev):
    r = run(PY, os.path.join(G, "bin", "dmhook.py"), verb, cwd=G, stdin=json.dumps(dict(ev, session_id="abc123def456",
                                                                                              cwd=G)))
    return r.returncode, r.stdout + r.stderr


rc, out = hook("prompt", {"prompt": "Note Corner Lets accepted on 2026-04-20."})
check("prompt: the person's prompt kept as the session's instructions", rc == 0 and any(
    e["layer"] == "instructions" for e in dmlaunch.Session(G, "hook-abc123def456").index()), out)
rc, out = hook("pre", {"tool_name": "Bash", "tool_input": {"command": "git commit -qm 'by hand'"}})
check("pre: a commit past the save: refused", rc == 2 and "dmsave.py" in out, out)
rc, out = hook("pre", {"tool_name": "Bash", "tool_input": {"command": "git -c user.name=x commit --no-verify -m y"}})
check("pre: --no-verify: refused", rc == 2 and "--no-verify" in out, out)
rc, out = hook("pre", {"tool_name": "Bash", "tool_input": {"command": f'{PY} bin/dmsave.py "k" "w" --body "- action: x"'}})
rc2, out2 = hook("pre", {"tool_name": "Bash", "tool_input": {"command": "git log -n 3"}})
check("...and the save, or git's other verbs, go through", rc == 0 and rc2 == 0, out + out2)
_denied = []
for _c in ("git commit -nm 'quick'", "git commit --no-ver -m y", "git -c core.hooksPath=/dev/null commit -m y",
           "echo dmsave.py && git commit -m 'by hand'"):
    rc, out = hook("pre", {"tool_name": "Bash", "tool_input": {"command": _c}})
    _denied.append((_c, rc))
check("pre: `-n`, `--no-verify` abbreviated, a hooks path of its own, and a commit beside a word that only mentions the "
      "save: each refused", all(rc == 2 for _c, rc in _denied), _denied)
rc, out = hook("pre", {"tool_name": "Bash", "tool_input": {"command":
                f'{PY} bin/dmsave.py "k" "fix: git commit was by hand" --body "- action: git commit -n undone"'}})
check("...while a save whose words say `git commit` goes through: what a quoted argument says is not what runs",
      rc == 0, out)
import shlex
_r = run(PY, "-c", "import sys; sys.path.insert(0, 'bin'); import dmhook; "
         "print(dmhook._q('/opt/my python/bin/python3') + ' ' + dmhook._q('/home/sam/my garden/bin/dmhook.py') + ' pre')", cwd=G)
check("the hook's command quotes its Python and its script, so a path with a space is one word to the shell",
      os.name == "nt" or shlex.split(_r.stdout.strip()) == ["/opt/my python/bin/python3", "/home/sam/my garden/bin/dmhook.py", "pre"],
      _r.stdout + _r.stderr)
O = os.path.join(T, "other")
os.makedirs(os.path.join(O, "bin"))
run("git", "init", "-q", O)
for f in ("bin/dmcheck.py", "VOCAB.md"):
    open(os.path.join(O, f), "w").close()
rc, out = hook("pre", {"tool_name": "Write", "tool_input": {"file_path": os.path.join(O, "beans", "x.md")}})
check("pre: a write into another garden: refused, a proposal named", rc == 2 and "Part F" in out, out)
rc, out = hook("pre", {"tool_name": "Read", "tool_input": {"file_path": os.path.join(G, "scratch", "plan.txt")}})
check("pre: a read of a file in no layer: refused (R4)", rc == 2 and "no layer" in out, out)
rc, out = hook("post", {"tool_name": "Read", "tool_input": {"file_path": os.path.join(G, "words", "offer.md")},
                        "tool_response": {"file": {"content": read("words/offer.md")}}})
rc2, out2 = hook("pre", {"tool_name": "Read", "tool_input": {"file_path": os.path.join(G, "words", "offer.md")}})
check("post keeps a read as material; a read again only warns", rc == 0 and rc2 == 0 and "read before" in out2, out + out2)
rc, out = hook("post", {"tool_name": "Bash", "tool_input": {"command": "cat scratch/plan.txt"},
                        "tool_response": {"stdout": read("scratch/plan.txt"), "stderr": ""}})
check("post: a shell's output holding a line a request may not carry: warned to the model and recorded, not refused",
      rc == 0 and "additionalContext" in out and dmlaunch.Session(G, "hook-abc123def456").posts(), out)
rc, out = run(PY, os.path.join(G, "bin", "dmhook.py"), "pre", cwd=G, stdin="{not json").returncode, ""
check("a hook that cannot read its event fails closed (exit 2)", rc == 2)
rc, out = hook("end", {})
check("end: a save here is no longer traced against the session", rc == 0 and dmlaunch.Session.current(G) is None, out)
rc = run(PY, "bin/dmhook.py", "uninstall", "claude-code", cwd=G)
check("dmhook uninstall: its hooks taken out", "hooks" not in json.loads(read(".claude/settings.local.json")),
      rc.stdout + rc.stderr)

SRV.shutdown()
shutil.rmtree(T, ignore_errors=True)
print(f"\nlaunch: {RUN[0] - len(FAILS)}/{RUN[0]} checks passed, {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
