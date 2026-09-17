#!/usr/bin/env python3
"""dmupgrade — bring a garden's language up to a daftar release.

    python3 bin/dmupgrade.py <tag>                       # from https://github.com/0mit/daftar
    python3 bin/dmupgrade.py <tag> --from <url-or-path>  # from any clone that carries the tag

A release is a TAG on the public repository. What a garden receives from it is declared once, in the
release's own `seed/LANGUAGE` — the same file `seed/germinate.sh` reads — so a new garden and an upgraded
one cannot disagree about what the language is.

WHAT IT DOES, and nothing else:
  1. refuses a working tree with uncommitted changes, so the upgrade is the only thing in the diff;
  2. fetches the tag into a temporary clone;
  3. copies every file the release's LANGUAGE matches, and removes files the garden's copy of the same
     patterns matched that the release no longer has (a retired tool leaves, rather than lingering);
  4. moves the `extends: std-vocab@<ver>` pin in VOCAB.md and GARDEN.md to the release's vocabulary;
  5. re-runs `bin/install.sh`, because the hooks or the merge driver may have changed;
  6. appends a RULE-CHANGE journal entry naming the tag, its commit, the vocabulary move and every file;
  7. runs the gate and reports it.

IT DOES NOT COMMIT. Adopting a release changes the law this garden is judged by, which is a decision the
garden's own human ratifies: read `git diff`, then `git add -A && git commit`. The journal entry is already
written, so the gate's provenance duty is met by the commit that adopts it.
"""
import argparse, datetime, glob, os, re, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPSTREAM = 'https://github.com/0mit/daftar.git'
PIN = re.compile(r'^(extends: std-vocab@)(\S+)', re.M)


def run(*args, cwd=ROOT, check=True):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        detail = '\n'.join(s.strip() for s in (r.stdout, r.stderr) if s.strip())
        sys.exit(f"{' '.join(args)} failed:\n{detail or '(no output)'}")
    return r


def patterns(root):
    path = os.path.join(root, 'seed', 'LANGUAGE')
    if not os.path.isfile(path):
        sys.exit(f"REFUSING: {path} does not exist — a release without seed/LANGUAGE does not say what it "
                 f"contains, and guessing would be a second, silent list.")
    return [l.strip() for l in open(path, encoding='utf-8') if l.strip() and not l.lstrip().startswith('#')]


def expand(root, pats):
    out = set()
    for p in pats:
        for f in glob.glob(os.path.join(root, p)):
            if os.path.isfile(f):
                out.add(os.path.relpath(f, root))
    return out


def vocab_version(root):
    fm = dmparse.loads(dmparse.read(os.path.join(root, 'seed', 'std-vocab.md'))[0] or '') or {}
    return str(fm.get('version'))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tag', help='the release tag, e.g. v0.3.0')
    ap.add_argument('--from', dest='src', default=UPSTREAM, help=f'repository URL or path (default {UPSTREAM})')
    a = ap.parse_args()

    dirty = run('git', 'status', '--porcelain', '--untracked-files=no').stdout.strip()   # untracked files are not in the diff
    if dirty:
        sys.exit("REFUSING: the working tree has uncommitted changes.\n" + dirty +
                 "\nCommit or stash them first, so that the upgrade is the only thing `git diff` shows.")

    tmp = tempfile.mkdtemp(prefix='dmupgrade-')
    try:
        rel = os.path.join(tmp, 'release')
        run('git', 'clone', '-q', '--depth', '1', '--branch', a.tag, a.src, rel, cwd=tmp)
        sha = run('git', 'rev-parse', 'HEAD', cwd=rel).stdout.strip()

        if vocab_version(rel) in ('None', ''):
            sys.exit(f"REFUSING: {a.tag} carries no readable `version:` in seed/std-vocab.md — nothing to pin to.")
        want = expand(rel, patterns(rel))
        have = expand(ROOT, patterns(ROOT)) if os.path.isfile(os.path.join(ROOT, 'seed', 'LANGUAGE')) else set()
        before = vocab_version(ROOT)

        changed, added = [], []
        for f in sorted(want):
            src, dst = os.path.join(rel, f), os.path.join(ROOT, f)
            if os.path.isfile(dst) and open(src, 'rb').read() == open(dst, 'rb').read():
                continue
            (changed if os.path.isfile(dst) else added).append(f)
            os.makedirs(os.path.dirname(dst) or ROOT, exist_ok=True)
            shutil.copy2(src, dst)
        removed = sorted(have - want)
        for f in removed:
            os.remove(os.path.join(ROOT, f))

        after = vocab_version(ROOT)
        repinned = []
        for doc in ('VOCAB.md', 'GARDEN.md'):
            path = os.path.join(ROOT, doc)
            text = open(path, encoding='utf-8').read()
            pins = PIN.findall(text)
            if len(pins) != 1:
                sys.exit(f"REFUSING to guess: {doc} carries {len(pins)} `extends: std-vocab@` pins, expected 1. "
                         f"The files above are already copied — `git checkout -- .` undoes them.")
            if pins[0][1] != after:
                open(path + '.tmp', 'w', encoding='utf-8').write(PIN.sub(rf'\g<1>{after}', text, count=1))
                os.replace(path + '.tmp', path)
                repinned.append(doc)

        if not (changed or added or removed or repinned):
            print(f"nothing to do: this garden's language already equals {a.tag} ({sha[:12]}).")
            return 0

        run('sh', os.path.join(ROOT, 'bin', 'install.sh'), check=False)
        now = datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %z')
        lines = [f"\n## {now} · (fill in who ratified) · RULE-CHANGE: language upgraded to daftar {a.tag}",
                 f"- action: **RULE-CHANGE — `bin/dmupgrade.py {a.tag}`** from {a.src} at {sha}; "
                 f"std-vocab {before} -> {after}.",
                 f"- changed: {', '.join(changed) or 'none'}",
                 f"- added: {', '.join(added) or 'none'}",
                 f"- removed: {', '.join(removed) or 'none'}",
                 f"- repinned: {', '.join(repinned) or 'none'}",
                 "- why: (fill in — what this release brings that this garden adopts)",
                 "- beans: none"]
        with open(os.path.join(ROOT, 'log', 'journal.md'), 'a', encoding='utf-8') as j:
            j.write('\n'.join(lines) + '\n')

        gate = run(sys.executable, os.path.join(ROOT, 'bin', 'dmcheck.py'), check=False)
        print(f"upgraded to {a.tag} ({sha[:12]}): std-vocab {before} -> {after}; "
              f"{len(changed)} changed, {len(added)} added, {len(removed)} removed, {len(repinned)} repinned.")
        print((gate.stdout.strip().splitlines() or ['(the gate printed nothing)'])[-1])
        print("\nNOT COMMITTED. Read `git diff`, complete the journal entry's two `fill in` fields, then\n"
              "  git add -A && git commit\n"
              "To abandon: git checkout -- ." + (f" && rm {' '.join(added)}" if added else ""))
        return 0 if gate.returncode == 0 else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
