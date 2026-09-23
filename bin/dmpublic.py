#!/usr/bin/env python3
"""dmpublic — refuse to publish anything that names a garden's estate.

WHY THIS EXISTS. daftar's repository is public; a garden is not. The two are edited in the same session by
the same hands, and what leaks is never the beans — it is the PROSE AROUND THEM: an example path in a
comment, a measurement written as "host-a says 45 fresh and host-b says 10 stale", a commit message, a pull
request body. Those are the places nobody greps. On 2026-09-20 this repository carried five such names, every
one written the same night by an agent explaining a real measurement, and the operator found them in a pull
request rather than in a diff.

WHAT IT KNOWS. Nothing. The forbidden words are DERIVED from a garden: the id of EVERY bean and every
mapping, the values of hostname / fqdn / ip anchors, and the logical root names each host declares. Nobody
maintains a denylist, so a bean added tomorrow is covered tomorrow. Every id, not the ids of chosen kinds:
a hand-kept list of the kinds that are "beings" was a proxy for "what the estate calls its own", and the
proxy drifted — a design's id sat in the public law while its kind was not on the list. What an estate
names is estate, whatever its kind; a kind added to the law tomorrow needs no line here.

WHAT IS NOT A LEAK. A word that the PUBLISHED knowledge carries is public knowledge, not an estate fact:
`seed/knowledge/technology.tsv` names MikroTik, Samba and Docker, and a garden whose router bean is called
`mikrotik` must not make the word unsayable in a vocabulary that documents RouterOS. Those are subtracted
automatically. Anything else that is genuinely public — the account name, the project name — goes in
`seed/PUBLIC-ALLOW`, one word per line, which is a decision recorded rather than a special case in code.

    python3 bin/dmpublic.py --garden <path> [--repo <path>] [--range origin/master..HEAD] [--text FILE]

Checks, each only if asked for: every tracked file (default), the messages of the commits in `--range`, and
a text file such as a pull request body. Exit 0 = nothing found, 1 = something names the estate, 2 = setup.
"""
import glob, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dmparse
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ANCHOR_KEYS = {'hostname', 'fqdn', 'ip'}


def estate_words(garden):
    """What a garden knows that this repository must never say. Derived from the garden itself."""
    words = set()
    for f in glob.glob(os.path.join(garden, 'beans', '*.md')):
        head, _ = dmparse.read(f)
        try:
            fm = yaml.safe_load(head) or {}
        except Exception:
            continue
        if not isinstance(fm, dict):
            continue
        if fm.get('bean'):
            words.add(str(fm['bean']))
        for a in ((fm.get('identity') or {}).get('anchors') or []):
            if a.get('key') in ANCHOR_KEYS:
                words.add(str(a.get('value', '')))
        for name in (fm.get('roots') or {}):
            words.add(str(name))
    for f in glob.glob(os.path.join(garden, 'mappings', '*.md')):
        words.add(os.path.basename(f)[:-3])
        try:
            fm = yaml.safe_load(dmparse.read(f)[0]) or {}
        except Exception:
            continue
        if isinstance(fm, dict) and fm.get('mapping'):
            words.add(str(fm['mapping']))
    return {w.lower() for w in words if len(w) >= 4}


def public_words(garden):
    """Words that are public knowledge even though a garden also uses them: the published classifications
    (a technology catalogue names MikroTik and Samba), plus this repository's own PUBLIC-ALLOW list."""
    ok = set()
    for tsv in glob.glob(os.path.join(HERE, '..', 'seed', 'knowledge', '*.tsv')):
        with open(tsv, encoding='utf-8', errors='replace') as fh:
            for line in fh:
                for cell in line.rstrip('\n').split('\t'):
                    for token in re.split(r'[^A-Za-z0-9_.-]+', cell):
                        if len(token) >= 4:
                            ok.add(token.lower())
    allow = os.path.join(HERE, '..', 'seed', 'PUBLIC-ALLOW')
    if os.path.exists(allow):
        for line in open(allow, encoding='utf-8'):
            line = line.split('#')[0].strip().lower()
            if line:
                ok.add(line)
    return ok


def hits(text, words):
    found = {}
    for w in words:
        for m in re.finditer(r'(?<![\w.-])' + re.escape(w) + r'(?![\w-])', text, re.I):
            found.setdefault(w, text.count('\n', 0, m.start()) + 1)
    return found


def main():
    a = sys.argv[1:]
    if '--garden' not in a:
        print(__doc__); return 2
    garden = a[a.index('--garden') + 1]
    if not os.path.isdir(os.path.join(garden, 'beans')):
        print(f"dmpublic: {garden} is not a garden (no beans/)"); return 2
    repo = a[a.index('--repo') + 1] if '--repo' in a else os.path.dirname(HERE)
    rng = a[a.index('--range') + 1] if '--range' in a else None
    text_file = a[a.index('--text') + 1] if '--text' in a else None
    quiet = '--quiet' in a
    words = estate_words(garden) - public_words(garden)
    bad = []
    if '--no-files' not in a:
        for f in subprocess.run(['git', 'ls-files'], capture_output=True, text=True,
                                cwd=repo).stdout.split():
            p = os.path.join(repo, f)
            try:
                body = open(p, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            for w, line in hits(body, words).items():
                bad.append((f"{f}:{line}", w))
    if rng:
        msgs = subprocess.run(['git', 'log', '--format=%H%n%B', rng], capture_output=True, text=True,
                              cwd=repo).stdout
        for w, _line in hits(msgs, words).items():
            bad.append((f"commit message in {rng}", w))
    if text_file:
        for w, line in hits(open(text_file, encoding='utf-8', errors='replace').read(), words).items():
            bad.append((f"{text_file}:{line}", w))
    if not bad:
        if not quiet:
            print(f"dmpublic: nothing names any of the {len(words)} estate names of {garden}")
        return 0
    print(f"dmpublic: REFUSING — this names the estate of {garden}. A public repository carries the "
          f"LANGUAGE, never a garden:")
    for where, w in sorted(bad):
        print(f"  {where}: '{w}'")
    print("Say it without the name — 'one host', 'another machine', '/home/user/tree' — or, if the word is "
          "genuinely public, add it to seed/PUBLIC-ALLOW with the reason.")
    return 1


if __name__ == '__main__':
    sys.exit(main())
