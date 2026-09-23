#!/usr/bin/env python3
"""dmpublic — refuse to publish anything that names a garden's estate.

WHY THIS EXISTS. daftar's repository is public; a garden is not. The two are edited in the same session by
the same hands, and what leaks is never the beans — it is the PROSE AROUND THEM: an example path in a
comment, a measurement written as "host-a says 45 fresh and host-b says 10 stale", a commit message, a pull
request body. Those are the places nobody greps. On 2026-09-20 this repository carried five such names, every
one written the same night by an agent explaining a real measurement, and the operator found them in a pull
request rather than in a diff.

WHAT IT KNOWS. Nothing. The forbidden words are DERIVED from a garden: the id of EVERY bean and every
mapping, the logical root names each host declares, the garden's own id, and the VALUE of every identity anchor.
Nobody maintains a denylist, so a bean added tomorrow is covered tomorrow. Every id, not the ids of chosen kinds:
a hand-kept list of the kinds that are "beings" was a proxy for "what the estate calls its own", and the
proxy drifted — a design's id sat in the public law while its kind was not on the list. What an estate
names is estate, whatever its kind; a kind added to the law tomorrow needs no line here. Every anchor's value,
not the values of chosen keys, for the same reason: a list of three keys (hostname, fqdn, ip) let a person's
email, an agreement's id, a serial number and a session id through, and an anchor key the law adds tomorrow
names something a garden identifies — which is exactly what must not leave it.

WHAT IS NOT A LEAK. A word that the PUBLISHED knowledge carries is public knowledge, not an estate fact:
`seed/knowledge/technology.tsv` names MikroTik, Samba and Docker, and a garden whose router bean is called
`mikrotik` must not make the word unsayable in a vocabulary that documents RouterOS. Those are subtracted
automatically, and so is an anchor value made ONLY of public words (`product:samba` says what the catalogue
already says). Anything else that is genuinely public — the account name, the project name — goes in
`seed/PUBLIC-ALLOW`, one word per line, which is a decision recorded rather than a special case in code. A line
may name the files the word is public IN (`<word> <path> ...`): a consent given for one page is not a consent
given for every file, commit message and pull request.

    python3 bin/dmpublic.py --garden <path> [--repo <path>] [--range origin/master..HEAD] [--text FILE]

Checks, each only if asked for: every tracked file (default), the messages of the commits in `--range`, and
a text file such as a pull request body. Exit 0 = nothing found, 1 = something names the estate, 2 = setup.
"""
import functools, glob, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dmparse
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

_TOKEN = re.compile(r'[^A-Za-z0-9_.-]+')       # how a published catalogue's cells are cut into words


def _tokens(text):
    return [t for t in _TOKEN.split(text.lower()) if t]


def own_garden_id(garden):
    """The garden's own id: the first twelve hex digits of the root of its first-parent history, as the gate reads
    it (`dmcheck.own_garden_id`, std-vocab `garden_id`). Read here rather than imported, because the gate cannot be
    imported outside a garden and this runs from the language's repository. None when git cannot say."""
    try:
        r = subprocess.run(['git', '-C', garden, 'rev-list', '--first-parent', '--max-parents=0', 'HEAD'],
                           capture_output=True, text=True, timeout=10)
        shallow = subprocess.run(['git', '-C', garden, 'rev-parse', '--is-shallow-repository'],
                                 capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return None
    roots = r.stdout.split()
    return roots[-1][:12] if r.returncode == 0 and roots and shallow != 'true' else None


def estate_words(garden, public=frozenset()):
    """What a garden knows that this repository must never say. Derived from the garden itself: every name it gives
    (bean and mapping ids, root names, its own id) and every value it identifies something by (each identity
    anchor's value, whatever its key), less an anchor value every token of which is `public`."""
    names, values = set(), set()
    for f in glob.glob(os.path.join(garden, 'beans', '*.md')):
        head, _ = dmparse.read(f)
        try:
            fm = yaml.safe_load(head) or {}
        except Exception:
            continue
        if not isinstance(fm, dict):
            continue
        if fm.get('bean'):
            names.add(str(fm['bean']))
        ident = fm.get('identity') if isinstance(fm.get('identity'), dict) else {}
        for a in (ident.get('anchors') or []):
            # a yes/no is no one's identity, and `True` guarded as a word would make "true" unsayable
            if isinstance(a, dict) and a.get('value') not in (None, '') and not isinstance(a.get('value'), bool):
                values.add(str(a['value']))
        for name in (fm.get('roots') if isinstance(fm.get('roots'), dict) else {}):
            names.add(str(name))
    for f in glob.glob(os.path.join(garden, 'mappings', '*.md')):
        names.add(os.path.basename(f)[:-3])
        try:
            fm = yaml.safe_load(dmparse.read(f)[0]) or {}
        except Exception:
            continue
        if isinstance(fm, dict) and fm.get('mapping'):
            names.add(str(fm['mapping']))
    gid = own_garden_id(garden)
    if gid:
        names.add(gid)
    # A value is subtracted only when EVERY token of it is public: `product:samba` names nothing the catalogue does
    # not, while `a@example.org` keeps its guard because `a` is nobody's public word — and a MAC address, cut into
    # two-letter tokens that no catalogue carries, keeps its guard too.
    values = {v for v in values if not (_tokens(v) and all(t in public for t in _tokens(v)))}
    return {w.lower() for w in names | values if len(w) >= 4}


@functools.lru_cache(maxsize=None)
def _allow_lines():
    """seed/PUBLIC-ALLOW as [(word, [path, ...])]: a line with no path is public everywhere."""
    allow = os.path.join(HERE, '..', 'seed', 'PUBLIC-ALLOW')
    if not os.path.exists(allow):
        return ()
    out = []
    with open(allow, encoding='utf-8') as fh:
        for line in fh:
            cells = line.split('#')[0].split()
            if cells:
                out.append((cells[0].lower(), tuple(c.replace('\\', '/') for c in cells[1:])))
    return tuple(out)


def public_words(garden):
    """Words that are public knowledge even though a garden also uses them: the published classifications
    (a technology catalogue names MikroTik and Samba), plus the lines of this repository's PUBLIC-ALLOW that name
    no file. A line that names files is public only in those (`allowed_in`)."""
    ok = set()
    for tsv in glob.glob(os.path.join(HERE, '..', 'seed', 'knowledge', '*.tsv')):
        with open(tsv, encoding='utf-8', errors='replace') as fh:
            for line in fh:
                for cell in line.rstrip('\n').split('\t'):
                    for token in _tokens(cell):
                        if len(token) >= 4:
                            ok.add(token)
    ok |= {w for w, paths in _allow_lines() if not paths}
    return ok


def allowed_in(path):
    """The words PUBLIC-ALLOW makes public in one tracked file (a path as git spells it) and nowhere else — and every
    word it names, in PUBLIC-ALLOW itself: the line that records a decision has to be able to say the word."""
    return {w for w, paths in _allow_lines() if path in paths or path == 'seed/PUBLIC-ALLOW'}


def _pattern(w):
    return r'(?<![\w.-])' + re.escape(w) + r'(?![\w-])'


@functools.lru_cache(maxsize=8)
def _any_of(words):
    """One pattern that matches wherever ANY of the words would: if a word matches at a position, the alternation
    matches there too, so a text it does not match holds none of them. Longest first, only for tidiness."""
    return re.compile(r'(?<![\w.-])(?:' + '|'.join(re.escape(w) for w in sorted(words, key=len, reverse=True))
                      + r')(?![\w-])', re.I) if words else None


def hits(text, words):
    found = {}
    # MOST FILES NAME NOTHING, and one scan says so: a word per scan cost seven seconds over this repository with the
    # author's garden, one alternation a second. It only skips texts it cannot match, so it moves no finding; a text
    # it does match is read word by word, so every word it holds is reported with its first line.
    words = frozenset(words)
    if not words or not _any_of(words).search(text):
        return found
    for w in words:
        for m in re.finditer(_pattern(w), text, re.I):
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
    public = public_words(garden)
    words = estate_words(garden, public) - public
    bad = []
    if '--no-files' not in a:
        for f in subprocess.run(['git', 'ls-files'], capture_output=True, text=True,
                                cwd=repo).stdout.split():
            p = os.path.join(repo, f)
            try:
                body = open(p, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            for w, line in hits(body, words - allowed_in(f)).items():
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
    print("Say it without the name — 'one host', 'another machine', '/home/user/tree'. If the word is meant in its "
          "ordinary sense and a garden also names something by it, rephrase: allowing the word would unguard the "
          "name. If it is genuinely public, add it to seed/PUBLIC-ALLOW with the reason — with the files it is "
          "public in, when the consent was given for those.")
    return 1


if __name__ == '__main__':
    sys.exit(main())
