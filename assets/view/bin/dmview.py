#!/usr/bin/env python3
"""dmview — draw a garden's page: its drawings at four lenses, with live values beside them and actions a host may run.

    python3 assets/view/bin/dmview.py check                        the page against the law and its drawings
    python3 assets/view/bin/dmview.py elements <view>              a drawing's elements: id, pattern, being
    python3 assets/view/bin/dmview.py report --out FILE            the offline page, with the author mode
    python3 assets/view/bin/dmview.py import <view-selection.json> an author-mode selection written into the page
    python3 assets/view/bin/dmview.py bundle --out DIR [--monitor <being>]   a monitor's deployment, by its adapter
    python3 assets/view/bin/dmview.py serve --config FILE          the served page and the action executor
    python3 assets/view/bin/dmview.py serve-init --config FILE --user NAME [--bean <person>] [--orgs "*"|org-a,org-b] [--shared] [--no-actions]
    python3 assets/view/bin/dmview.py render <view> --out DIR [--member <bean>] [--keep --who WHO]   its documents
    python3 assets/view/bin/dmview.py ics <view> --out FILE --config FILE [--user NAME]   its calendar, audited as a pass
    python3 assets/view/bin/dmview.py run-scheduled --config FILE [--at DAY]   the actions whose `every` falls on DAY

Every command takes `--garden PATH` (by default the garden this asset sits in, three directories up) and `--page <bean>`
(by default the one bean that carries `view`). (`python` on Windows.)

THIS IS THE `view` PROFILE'S ASSET. A garden receives it while it extends the profile, and leaving the profile takes it
away — both one act of bin/dmupgrade.py (`--extend view`, `--retract view`), or `seed/germinate.py --profile view` at
birth. Its files are the release's: an edit to one is a RULE-CHANGE, as an edit to any tool the release ships is. What it
reads is law the gate checks — the page's `view`, `views`, `view_bindings` and `view_monitors` — and what it cannot
check the gate cannot either, it checks here: that those terms sit on the page, that a drawing's elements are there,
that a race draws a procedure that does not branch, that a drawing shows no address. `assets/view/README.md` is the
guide.

Nothing it writes enters the ledger but through `import`, which writes the page's own terms through bin/dmsafe.py and
journals through bin/dmjournal.py, and `render --keep`, which adds each rendered document's `document` bean and saves it
through bin/dmsave.py; `report` (with a CSV beside it of each table), `render`, `ics` and `bundle` write where they are
asked to, never inside the garden unasked. `ics` is a pass out of the garden, the flow law's `served` (a calendar
that leaves it for a subscriber): the host's configuration names who asks and where its audit log is, and the export is
refused where the law grants that viewer no `read` of what an event carries (a member's title and its timing, or its
clauses), and audited either way. `run-scheduled` is what a host's timer calls.
Exit 0 done; 2 refused, with the reason and nothing written.
"""
import os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))           # the asset: assets/view
sys.path.insert(0, os.path.join(HERE, "lib"))
import view_model as vm


def die(msg, code=2):
    print("dmview: " + msg, file=sys.stderr)
    sys.exit(code)


def option(args, name):
    """The value of `--name VALUE`, taken out of args; None where it is absent."""
    if name not in args:
        return None
    i = args.index(name)
    if i + 1 >= len(args):
        die("%s needs a value" % name)
    v = args[i + 1]
    del args[i:i + 2]
    return v


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__); return 0
    cmd, rest = args[0], args[1:]
    garden = option(rest, "--garden") or os.path.dirname(os.path.dirname(HERE))
    page = option(rest, "--page")
    if not os.path.isfile(os.path.join(garden, "GARDEN.md")):
        die("%s is not a garden (no GARDEN.md): run the copy of this tool a garden holds, or pass --garden" % garden)
    probs = vm.init(garden, page)
    if probs:
        die("nothing done:\n  - " + "\n  - ".join(probs))
    if cmd == "check":
        errs, warns = vm.check()
        for w in warns:
            print("  warn: " + w)
        for e in errs:
            print("  - " + e)
        print("dmview: %s" % ("the page and its drawings agree" if not errs else "%d disagreement(s)" % len(errs)))
        return 2 if errs else 0
    if cmd == "elements":
        if not rest:
            die("elements needs the key of a drawing")
        try:
            els = vm.elements(rest[0])
        except vm.NoPage as e:
            die(str(e))
        for e in els:
            print("%-28s %-9s %-18s %s" % (e["id"], e["pattern"], e["bean"] or "", e["label"][:50]))
        return 0
    if cmd == "import":
        who = option(rest, "--who")
        if not rest:
            die("import needs a selection file (the author mode's view-selection.json)")
        print("dmview: " + vm.import_selection(rest[0], who=who))
        return 0
    if cmd == "report":
        import view_report
        view_report.main(rest)
        return 0
    if cmd == "bundle":
        out, mon = option(rest, "--out"), option(rest, "--monitor")
        if not out:
            die("bundle needs --out DIR — a bundle is written where it is asked for; nothing written")
        errs, _w = vm.check()
        if errs:
            die("the page and its drawings disagree — nothing written:\n  - " + "\n  - ".join(errs))
        ms = [m for m in vm.monitors() if m["adapter"] and (mon is None or m["bean"] == mon)]
        if not ms:
            die("no monitor of the page%s has an adapter that writes a bundle" % (" named %s" % mon if mon else ""))
        if len(ms) > 1 and mon is None:
            die("the page has %d monitors (%s): name one with --monitor" % (len(ms), ", ".join(m["bean"] for m in ms)))
        m = ms[0]
        if not hasattr(m["adapter"], "bundle"):
            die("the %s adapter writes no bundle" % m["technology"])
        n, counts, pages = m["adapter"].bundle(m, vm.views(), out)
        print("dmview bundle: %s (%s): %d probe targets, %d drawing pages and an index -> %s  %s"
              % (m["bean"], m["technology"], n, pages, out, counts))
        return 0
    if cmd in ("serve", "serve-init"):
        import view_serve
        cfg = option(rest, "--config")
        if not cfg:
            die("%s needs --config FILE (the host's own configuration, outside git)" % cmd)
        if cmd == "serve":
            view_serve.serve(cfg, list(sys.argv))
            return 0
        user = option(rest, "--user")
        if not user:
            die("serve-init needs --user NAME")
        orgs = option(rest, "--orgs") or "*"
        bean = option(rest, "--bean")
        if bean and not vm.fm(bean):
            die("serve-init: the garden holds no bean %r to name as this viewer" % bean)
        pw = view_serve.serve_init(cfg, user, orgs, "--no-actions" not in rest, "--shared" in rest, bean)
        print("dmview: %s is ready; the new password is in %s (0600) — it is not printed." % (cfg, pw))
        return 0
    if cmd == "render":
        return render(rest)
    if cmd == "ics":
        return ics(rest)
    if cmd == "run-scheduled":
        import view_serve
        cfg, at = option(rest, "--config"), option(rest, "--at")
        if not cfg:
            die("run-scheduled needs --config FILE (the host's, whose viewers answer for the schedules)")
        import datetime
        at = at or datetime.date.today().isoformat()
        rows = view_serve.Host(cfg).run_scheduled(at)
        for key, el, code, obj in rows:
            print("  %s.%s: %s %s" % (key, el, code, obj.get("mode") or obj.get("error")))
        print("dmview run-scheduled: %s — %d action(s) due" % (at, len(rows)))
        return 0 if all(c == 200 for _k, _e, c, _o in rows) else 1
    die("unknown command %r — see `dmview --help`" % cmd)


def render(rest):
    """Each render the drawing declares, from each member, into DIR; with --keep, each document kept as a bean."""
    import subprocess, view_export
    out, member, who = option(rest, "--out"), option(rest, "--member"), option(rest, "--who")
    keep = "--keep" in rest
    rest = [a for a in rest if a != "--keep"]
    if not rest or not out:
        die("render needs the key of a drawing and --out DIR — a document is written where it is asked for")
    if keep and not who:
        die("render --keep needs --who: the one the save names, as every save does")
    if not vm.view_entry(rest[0]):
        die("the page has no drawing %r" % rest[0])
    done = []
    for entry, members in view_export.renders(rest[0]):
        try:
            tpath, template = view_export.template_of(entry)
        except ValueError as e:
            die(str(e))
        ext = os.path.splitext(tpath)[1] or ".txt"
        for m in members:
            if member and m != member:
                continue
            text = view_export.render_text(template, m)
            os.makedirs(out, exist_ok=True)
            path = os.path.join(out, "%s-%s%s" % (os.path.splitext(os.path.basename(tpath))[0], m, ext))
            open(path, "w", encoding="utf-8", newline="\n").write(text)
            done.append((m, path, text))
    if not done:
        die("nothing to render: the drawing declares no `renders`%s" % (", or %s is not among its members" % member if member else ""))
    for m, path, _t in done:
        print("  %s -> %s" % (m, path))
    if keep:
        kept = []
        for m, path, text in done:
            digest = view_export.sha256(text)
            bid = "doc-%s-%s" % (m.split("-")[0][:24], digest[7:15])
            open(os.path.join(vm.ROOT, "beans", bid + ".md"), "w", encoding="utf-8", newline="\n").write(
                view_export.document_bean(bid, "%s, rendered" % (vm.fm(m).get("title") or m), digest,
                                          "%s:%s" % (_host(), os.path.abspath(path)), _gardener(), m))
            kept.append("[[%s]] from [[%s]]" % (bid, m))
        r = subprocess.run([sys.executable, os.path.join(vm.ROOT, "bin", "dmsave.py"), who,
                            "%d document(s) rendered from drawing %s and kept" % (len(done), rest[0]), "--body",
                            "- action: rendered by `dmview render %s --keep`, each kept by its content_hash: %s" % (rest[0], "; ".join(kept))],
                           cwd=vm.ROOT)
        if r.returncode != 0:
            die("the save was refused (above): the document beans stand as written, for the fix and `dmsave.py --again`", r.returncode)
    print("dmview render: %d document(s)%s" % (len(done), ", kept" if keep else ""))
    return 0


def _host():
    """This machine's name as a unix-filesystem position names a host: lower case, letters, digits, dots and dashes."""
    import platform, re
    return re.sub(r"[^a-z0-9.-]", "-", platform.node().lower()).strip("-.") or "localhost"


def _gardener():
    sys.path.insert(0, os.path.join(vm.ROOT, "bin"))
    import dmpass
    return dmpass.gardener_of(vm.ROOT)


def ics(rest):
    """The drawing's `feed` as one calendar, written to FILE: a pass out of the garden, asked and audited by the host."""
    import view_export, view_serve
    out, cfg, user = option(rest, "--out"), option(rest, "--config"), option(rest, "--user")
    if not rest or not out or not cfg:
        die("ics needs the key of a drawing, --out FILE and --config FILE (the host's: who asks, and its audit log)")
    key = rest[0]
    if not vm.view_entry(key).get("feed"):
        die("the drawing %r declares no `feed`" % key)
    host = view_serve.Host(cfg)
    users = list((host.cfg.get("users") or {}))
    user = user or (users[0] if len(users) == 1 else None)
    if user not in users:
        die("ics needs --user NAME, one of the host's viewers (%s)" % ", ".join(users))
    evs = view_export.feed_events(key)
    # each event asks only for what it carries: the member's title and the timing, or the clauses, it is read from
    refused = sorted({m for m, name, *_ in evs
                      if not host.may(user, m, positions=["title", "timing" if name in (vm.fm(m).get("timing") or {}) else "clauses"])[0]})
    entry = {"user": user, "actor": host.cfg["users"][user].get("bean"), "act": "pass", "view": key, "mode": "ics",
             "pass": {"source": {"layer": "estate"}, "destination": {"layer": "remote"}, "method": "serve"}, "flow": "served",
             "members": sorted({m for m, *_ in evs}), "head": (host.head or "")[:12]}
    if refused:
        host.audit(dict(entry, granted=False, why="no read of %s" % ", ".join(refused)))
        die("refused: the law grants %s no read of %s — nothing written, the refusal audited" % (user, ", ".join(refused)))
    open(out, "w", encoding="utf-8", newline="").write(view_export.ics_text(evs, vm.fm_path(os.path.join(vm.ROOT, "GARDEN.md")).get("garden_id") or vm.garden_name()))
    host.audit(dict(entry, granted=True, events=len(evs), out=os.path.abspath(out)))
    print("dmview ics: %d event(s) of drawing %s -> %s (audited as a pass)" % (len(evs), key, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
