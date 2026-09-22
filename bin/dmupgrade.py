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
  4. moves the `extends: std-vocab@<ver>` pin in VOCAB.md and GARDEN.md to the release's vocabulary, and records
     the tag as `daftar_release:` in GARDEN.md — refusing a tag OLDER than the one recorded unless
     --allow-downgrade is given, because an older tag silently removes fixes;
  5. re-runs `bin/install.sh`, because the hooks or the merge driver may have changed;
  6. appends a RULE-CHANGE journal entry naming the tag, its commit, the vocabulary move and every file;
  7. runs the gate — and if the garden no longer passes under the release (a profile or a value the release
     does not offer, say), puts every file back as it was and says why, unless --keep-on-failure.

THE RELEASE'S OWN TOOL DOES THE WORK. When the release carries a different bin/dmupgrade.py, this one hands
over to it (with --garden and --no-delegate) instead of applying a newer release with older logic: v0.4.0
added the release record and the downgrade guard, and a v0.3.1 garden running its own v0.3.1 tool received the
new files and neither of those behaviours.

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
RELEASE = re.compile(r'^daftar_release:.*$', re.M)
SEMVER = re.compile(r'^v?(\d+)\.(\d+)\.(\d+)$')


def run(*args, cwd=None, check=True):
    r = subprocess.run(args, cwd=cwd or ROOT, capture_output=True, text=True)
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


def recorded_release():
    """The tag GARDEN.md records as `daftar_release:`, or None for a garden grown before v0.4.0 recorded one."""
    path = os.path.join(ROOT, 'GARDEN.md')
    fm = dmparse.loads(dmparse.read(path)[0] or '') or {} if os.path.isfile(path) else {}
    return str(fm['daftar_release']) if isinstance(fm, dict) and fm.get('daftar_release') else None


def vocab_version(root):
    fm = dmparse.loads(dmparse.read(os.path.join(root, 'seed', 'std-vocab.md'))[0] or '') or {}
    return str(fm.get('version'))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tag', help='the release tag, e.g. v0.3.0')
    ap.add_argument('--from', dest='src', default=UPSTREAM, help=f'repository URL or path (default {UPSTREAM})')
    ap.add_argument('--allow-downgrade', action='store_true', help='adopt a tag older than the one GARDEN.md records')
    ap.add_argument('--garden', help='the garden to upgrade (default: the one this tool lives in)')
    ap.add_argument('--keep-on-failure', action='store_true', help='leave the files in place when the gate fails, to repair by hand')
    ap.add_argument('--no-delegate', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('--recorded-source', help=argparse.SUPPRESS)
    a = ap.parse_args()
    global ROOT
    if a.garden:
        ROOT = os.path.abspath(a.garden)
    source = a.recorded_source or a.src

    dirty = run('git', 'status', '--porcelain', '--untracked-files=no').stdout.strip()   # untracked files are not in the diff
    if dirty:
        sys.exit("REFUSING: the working tree has uncommitted changes.\n" + dirty +
                 "\nCommit or stash them first, so that the upgrade is the only thing `git diff` shows.")

    current = recorded_release()
    cur_v, new_v = SEMVER.match(current or ''), SEMVER.match(a.tag)
    if cur_v and new_v and tuple(map(int, new_v.groups())) < tuple(map(int, cur_v.groups())) and not a.allow_downgrade:
        sys.exit(f"REFUSING: {a.tag} is OLDER than the release this garden records ({current}). Adopting it would "
                 f"remove whatever changed since. Pass --allow-downgrade if that is really what you mean.")

    tmp = tempfile.mkdtemp(prefix='dmupgrade-')
    try:
        rel = os.path.join(tmp, 'release')
        run('git', 'clone', '-q', '--depth', '1', '--branch', a.tag, a.src, rel, cwd=tmp)
        sha = run('git', 'rev-parse', 'HEAD', cwd=rel).stdout.strip()
        tool = os.path.join(rel, 'bin', 'dmupgrade.py')
        if (not a.no_delegate and os.path.isfile(tool) and '--no-delegate' in open(tool, encoding='utf-8').read()
                and open(tool, 'rb').read() != open(os.path.abspath(__file__), 'rb').read()):
            print(f"handing over to {a.tag}'s own bin/dmupgrade.py — a release is applied by its own upgrade logic", flush=True)
            args = [sys.executable, tool, a.tag, '--from', rel, '--garden', ROOT, '--no-delegate', '--recorded-source', source]
            if a.allow_downgrade:
                args.append('--allow-downgrade')
            if a.keep_on_failure:
                args.append('--keep-on-failure')
            return subprocess.run(args).returncode

        if vocab_version(rel) in ('None', ''):
            sys.exit(f"REFUSING: {a.tag} carries no readable `version:` in seed/std-vocab.md — nothing to pin to.")
        want = expand(rel, patterns(rel))
        have = expand(ROOT, patterns(ROOT)) if os.path.isfile(os.path.join(ROOT, 'seed', 'LANGUAGE')) else set()
        before = vocab_version(ROOT)

        changed, added = [], []
        for f in sorted(want):
            src, dst = os.path.join(rel, f), os.path.join(ROOT, f)
            same_bytes = os.path.isfile(dst) and open(src, 'rb').read() == open(dst, 'rb').read()
            # THE MODE IS PART OF THE FILE. Comparing bytes alone left a hook the release had made executable
            # non-executable in the garden (found adopting v0.4.2).
            if same_bytes and (os.stat(src).st_mode & 0o111) == (os.stat(dst).st_mode & 0o111):
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

        # THE GARDEN'S OWN TERMS ARE TRANSLATED, NEVER REWRITTEN BY HAND (13.0). When a release changes how the law
        # is SPELLED, a garden's `local_terms` are in the old spelling and the new gate refuses them. The release
        # ships the translator; it is a pure function of each term, it proves per term that the form it reads is
        # unchanged, and it leaves the file alone when it cannot. A refusal surfaces through the gate below, which
        # then puts everything back.
        translated, reform = 'none', os.path.join(ROOT, 'bin', 'dmreform.py')
        if os.path.isfile(reform):
            _r = run(sys.executable, reform, os.path.join(ROOT, 'VOCAB.md'), check=False)
            _out = (_r.stdout + _r.stderr).strip()
            if _r.returncode != 0:
                translated = 'REFUSED — ' + _out.replace(ROOT + os.sep, '')
            elif 'term(s) rewritten' in _out and ': 0 term' not in _out and 'rewritten —' in _out:
                translated = 'VOCAB.md local_terms — ' + _out.split('rewritten —', 1)[1].strip()
                if 'VOCAB.md' not in changed:
                    changed.append('VOCAB.md (translated)')

        gpath = os.path.join(ROOT, 'GARDEN.md')
        gtext = open(gpath, encoding='utf-8').read()
        gline = f'daftar_release: "{a.tag}"  # the daftar release this garden runs; bin/dmupgrade.py moves it'
        if recorded_release() != a.tag:
            if RELEASE.search(gtext):
                gtext = RELEASE.sub(gline, gtext, count=1)
            else:
                # after the WHOLE pin line: inserting after the match split the line and moved its comment
                gtext = re.sub(r'^extends: std-vocab@.*$', lambda m: m.group(0) + '\n' + gline, gtext, count=1, flags=re.M)
            open(gpath + '.tmp', 'w', encoding='utf-8').write(gtext)
            os.replace(gpath + '.tmp', gpath)
            repinned.append('GARDEN.md daftar_release')

        if not (changed or added or removed or repinned):
            print(f"nothing to do: this garden's language already equals {a.tag} ({sha[:12]}).")
            return 0

        # "applied" when either side is unknown: a garden that records no release cannot be told which way it moved.
        verb = ('applied' if not (cur_v and new_v) else
                'downgraded' if tuple(map(int, new_v.groups())) < tuple(map(int, cur_v.groups())) else 'upgraded')
        run('sh', os.path.join(ROOT, 'bin', 'install.sh'), check=False)
        sys.path.insert(0, os.path.join(ROOT, 'bin')); import dmjournal          # the release's own tool, just applied
        _who = run('git', 'config', 'user.name', check=False).stdout.strip() or '(fill in who ran it)'
        lines = ['\n' + dmjournal.stamp(_who, f"RULE-CHANGE: language {verb} to daftar {a.tag}", ROOT),
                 "- ratified_by: (fill in who ratified — merging the release's pull request, or the word given here)",
                 f"- action: **RULE-CHANGE — `bin/dmupgrade.py {a.tag}`** from {source} at {sha}; "
                 f"std-vocab {before} -> {after}; release {current or 'unrecorded'} -> {a.tag}.",
                 f"- changed: {', '.join(changed) or 'none'}",
                 f"- added: {', '.join(added) or 'none'}",
                 f"- removed: {', '.join(removed) or 'none'}",
                 f"- repinned: {', '.join(repinned) or 'none'}",
                 f"- translated: {translated}",
                 "- why: (fill in — what this release brings that this garden adopts)",
                 "- beans: none"]
        with open(os.path.join(ROOT, 'log', 'journal.md'), 'a', encoding='utf-8') as j:
            j.write('\n'.join(lines) + '\n')

        gate = run(sys.executable, os.path.join(ROOT, 'bin', 'dmcheck.py'), check=False)
        if gate.returncode != 0 and not a.keep_on_failure:
            # PUT IT ALL BACK. The tree was clean before we started, so git holds every file as it was. A cold-start
            # drill downgraded a garden that used a profile the older release lacks, and was left half-applied.
            run('git', 'checkout', '--', '.', check=False)
            for f in added:
                try:
                    os.remove(os.path.join(ROOT, f))
                except OSError:
                    pass
            run('sh', os.path.join(ROOT, 'bin', 'install.sh'), check=False)
            errs = [l for l in gate.stdout.splitlines() if l.startswith('ERROR')]
            if translated.startswith('REFUSED'):
                errs.insert(0, 'dmreform ' + translated)
            print(f"NOT {verb.upper()}: under {a.tag} this garden fails its own gate, so every file was put back as it was.\n"
                  + '\n'.join(errs[:12]) + ('\n…' if len(errs) > 12 else '') +
                  "\nFix what these name (or pass --keep-on-failure to repair by hand), then run this again.")
            return 1
        print(f"{verb} to {a.tag} ({sha[:12]}): std-vocab {before} -> {after}; "
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
