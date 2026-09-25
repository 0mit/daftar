#!/usr/bin/env python3
"""dmingest — apply a bean that arrived from somewhere else, through the ONE write path.

WHAT THIS IS NOT. It is not a second gate. `bin/dmcheck.py` has no `main`, no `argparse` and no
event-level entry point: it validates the garden containing `bin/`, globbing `beans/*.md` and reading
the STAGED blobs. Running it "on an event" is not a thing that can be asked of it, and writing an
ingestor that restates the staged rules would be the forbidden second copy of the law — the exact shape
the one-path rule (MODEL.md, The journal and the gate) exists to prevent. So this materialises the event into a real
working tree and a real index, and then runs the gate UNCHANGED. The gate never learns it was fed by
anything.

WHAT IT DOES.
  1. reads an incoming bean document and, if this garden already knows that bean, MERGES the two through
     `bin/dmmerge.py` — which since 2026-08-03 carries provenance on the bean, so an incremental apply
     reaches the same result a one-shot merge of both gardens would;
  2. writes the result to the working tree and STAGES it, together with the journal entry the incoming
     event carries;
  3. runs `python3 bin/dmcheck.py` and believes it;
  4. on refusal, restores the working tree and the index exactly as they were, and exits non-zero.

WHY THE JOURNAL ENTRY IS NOT OPTIONAL. It is not enforced here: it is enforced by the gate, whose (K)
provenance duty refuses a staged bean whose change is not journalled. An event that arrives without one
is refused for that reason and by that rule, and this file contains no copy of it. Passing --no-journal
is therefore a way to watch the gate refuse, not a way around it.

Usage:
  python3 bin/dmingest.py --event <bean.md> --from <garden-id> [--journal <entry.md>] [--commit]
  python3 bin/dmingest.py --event <bean.md> --from <garden-id> --dry-run
"""
import argparse, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmmerge
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git(*args, check=True):
    r = subprocess.run(['git', '-C', ROOT, *args], capture_output=True, text=True, encoding='utf-8')
    if check and r.returncode != 0:
        sys.exit(f"dmingest: git {' '.join(args)} failed — {r.stderr.strip()}")
    return r


def snapshot():
    """Enough to put the tree and the index back exactly as they were."""
    return {'index': git('write-tree').stdout.strip(),
            'head': git('rev-parse', 'HEAD', check=False).stdout.strip() or None}


def restore(snap, touched):
    """Undo everything this run wrote. A refusal must leave no trace, or the next run starts from a
    state nobody chose."""
    for rel in touched:
        r = git('cat-file', '-e', f"{snap['index']}:{rel}", check=False)
        if r.returncode == 0:
            blob = git('cat-file', 'blob', f"{snap['index']}:{rel}").stdout
            with open(os.path.join(ROOT, rel), 'w', encoding='utf-8') as f:
                f.write(blob)
            git('update-index', '--add', rel)
        else:
            p = os.path.join(ROOT, rel)
            if os.path.exists(p):
                os.remove(p)
            git('update-index', '--force-remove', rel, check=False)


def apply_event(event_path, origin):
    """The incoming bean, merged with what this garden already knows. Returns (relpath, text, note)."""
    fm, body = dmmerge.parse_file(event_path)
    bid = fm.get('bean') or fm.get('mapping')
    if not bid:
        sys.exit("dmingest: the event carries no `bean:` or `mapping:` id")
    rel = os.path.join('beans' if fm.get('bean') else 'mappings', f"{bid}.md")
    local = os.path.join(ROOT, rel)
    if not os.path.exists(local):
        return rel, open(event_path, encoding='utf-8').read(), f"new bean '{bid}'", []

    lfm, lbody = dmmerge.parse_file(local)
    seed = dmmerge.merge_component([
        {'garden': os.path.basename(ROOT), 'id': bid, 'fm': lfm},
        {'garden': origin, 'id': bid, 'fm': fm}])
    merged = dmmerge.render_bean(seed, lfm, fm, lbody, body)
    conflicts = sorted(p for k, v in seed['facts'].items() for p in dmmerge.conflict_paths(v, k))
    note = f"merged '{bid}' with the local copy" + (f" — {len(conflicts)} conflict(s): "
                                                    f"{', '.join(conflicts)}" if conflicts else "")
    return rel, merged, note, conflicts


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('--event', required=True, help='the incoming bean document')
    ap.add_argument('--from', dest='origin', required=True, help='the garden the event came from')
    ap.add_argument('--journal', help='the journal entry that accompanies it')
    ap.add_argument('--commit', action='store_true', help='commit if the gate passes')
    ap.add_argument('--dry-run', action='store_true', help='stage, run the gate, then restore either way')
    ap.add_argument('--accept-conflicts', action='store_true',
                    help='land the event even if merging it leaves an unresolved conflict')
    a = ap.parse_args()

    if git('status', '--porcelain').stdout.strip():
        sys.exit("dmingest: REFUSING — the working tree is dirty. An ingest has to be able to put the "
                 "tree back exactly as it found it, and it cannot promise that over someone else's "
                 "uncommitted work.")

    snap = snapshot()
    rel, text, note, conflicts = apply_event(a.event, a.origin)
    if conflicts and not a.accept_conflicts:
        # NOT A COPY OF A GATE RULE — a policy about what an INGEST may do unattended. MERGE.md §10
        # makes a captured conflict committable, and it is right about the case it was written for: a
        # human ran `git merge` and is standing there to resolve it. An event arriving from elsewhere
        # has nobody standing there, and landing an unresolved disagreement unattended is how a garden
        # accumulates conflicts nobody chose to take on. The gate still decides what is VALID; this
        # decides whether to accept a capture with no one to resolve it.
        print(f"dmingest: REFUSING — merging this event leaves {len(conflicts)} unresolved "
              f"conflict(s): {', '.join(conflicts)}. §10 lets a capture commit because a human is "
              f"usually standing there; an ingest has nobody. Resolve it by hand, or pass "
              f"--accept-conflicts to take it on deliberately. The tree is untouched.", file=sys.stderr)
        return 1
    touched = [rel]

    with open(os.path.join(ROOT, rel), 'w', encoding='utf-8') as f:
        f.write(text)
    git('add', rel)

    if a.journal:
        jrel = os.path.join('log', 'journal.md')
        entry = open(a.journal, encoding='utf-8').read().rstrip('\n')
        with open(os.path.join(ROOT, jrel), encoding='utf-8') as f:
            cur = f.read()
        with open(os.path.join(ROOT, jrel), 'w', encoding='utf-8') as f:
            f.write((cur if cur.endswith('\n') else cur + '\n') + '\n' + entry + '\n')
        git('add', jrel)
        touched.append(jrel)

    # THE GATE, UNCHANGED. Not imported, not reimplemented, not passed an event — invoked as a program
    # against a garden, exactly as the pre-commit hook invokes it.
    gate = subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'dmcheck.py')],
                          capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=ROOT)
    print(gate.stdout.rstrip())
    if gate.stderr.strip():
        print(gate.stderr.rstrip(), file=sys.stderr)

    if gate.returncode != 0 or a.dry_run:
        restore(snap, touched)
        if gate.returncode != 0:
            print(f"dmingest: REFUSED — the gate did not pass. {note}. The tree is as it was.",
                  file=sys.stderr)
            return 1
        print(f"dmingest: dry run — the gate passed. {note}. Nothing kept.", file=sys.stderr)
        return 0

    if a.commit:
        git('-c', 'user.name=dmingest', '-c', 'user.email=dmingest@localhost',
            'commit', '-q', '-m', f"ingest: {note} (from {a.origin})")
        print(f"dmingest: committed — {note}", file=sys.stderr)
    else:
        print(f"dmingest: staged — {note}. Commit it, or `git reset` to drop it.", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
