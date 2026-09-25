#!/usr/bin/env python3
"""dmview — draw a garden's page: its drawings at four lenses, with live values beside them and actions a host may run.

    python3 assets/view/bin/dmview.py check                        the page against the law and its drawings
    python3 assets/view/bin/dmview.py elements <view>              a drawing's elements: id, pattern, being
    python3 assets/view/bin/dmview.py report --out FILE            the offline page, with the author mode
    python3 assets/view/bin/dmview.py import <view-selection.json> an author-mode selection written into the page
    python3 assets/view/bin/dmview.py bundle --out DIR [--monitor <being>]   a monitor's deployment, by its adapter
    python3 assets/view/bin/dmview.py serve --config FILE          the served page and the action executor
    python3 assets/view/bin/dmview.py serve-init --config FILE --user NAME [--orgs "*"|org-a,org-b] [--shared] [--no-actions]

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
journals through bin/dmjournal.py; `report` and `bundle` write where they are asked to, never inside the garden unasked.
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
        pw = view_serve.serve_init(cfg, user, orgs, "--no-actions" not in rest, "--shared" in rest)
        print("dmview: %s is ready; the new password is in %s (0600) — it is not printed." % (cfg, pw))
        return 0
    die("unknown command %r — see `dmview --help`" % cmd)


if __name__ == "__main__":
    sys.exit(main())
