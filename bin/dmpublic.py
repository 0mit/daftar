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
Nobody maintains a denylist, so a bean added tomorrow is covered tomorrow. Every id, not the ids of chosen gene:
a hand-kept list of the gene that are "beings" was a proxy for "what the estate calls its own", and the
proxy drifted — a design's id sat in the public law while its genos was not on the list. What an estate
names is estate, whatever its genos; a genos added to the law tomorrow needs no line here. Every anchor's value,
not the values of chosen keys, for the same reason: a list of three keys (hostname, fqdn, ip) let a person's
email, an agreement's id, a serial number and a session id through, and an anchor key the law adds tomorrow
names something a garden identifies — which is exactly what must not leave it.

WHAT ELSE A GARDEN SAYS OF ITSELF. A bean's title of three words or more (a phrase that long is a name), and every
network address and email address its front matter holds, anchor or not — a contact, an interface's address — except
the ranges and domains kept for documentation (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24, 2001:db8::/32,
example.org and its kind), which every page of this repository may use. A name of three letters is guarded (`nas`,
`vps`); shorter ones are found everywhere, and are not.

WHAT IS NOT A LEAK. A word that the PUBLISHED technology catalogue carries is public knowledge, not an estate fact:
`seed/knowledge/technology.tsv` names MikroTik, Samba and Docker, and a garden whose router bean is called
`mikrotik` must not make the word unsayable in a vocabulary that documents RouterOS. Those are subtracted
automatically, and so is an anchor value made ONLY of public words (`product:samba` says what the catalogue
already says). The other tables — occupations, fields of education — are thousands of ordinary words, `nurse` and
`manager` among them, and a host a garden calls `manager` is its own name: they are public only in their own files. Anything else that is genuinely public — the account name, the project name — goes in
`seed/PUBLIC-ALLOW`, one word per line, which is a decision recorded rather than a special case in code. A line
may name the files the word is public IN (`<word> <path> ...`): a consent given for one page is not a consent
given for every file, commit message and pull request.

    python3 bin/dmpublic.py --garden <path> [--repo <path>] [--range origin/master..HEAD] [--text FILE]

Checks, each only if asked for: every tracked file (default), the messages of the commits in `--range`, and
a text file such as a pull request body. Exit 0 = nothing found, 1 = something names the estate, 2 = setup.
"""
import functools, ipaddress, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dmparse
import dmgarden  # noqa: E402 — the one garden model: where its documents are

# The rows of the flow law this tool checks, and the fixture that shows it (`bin/dmpass.py --flows` computes the guard).
GUARDS = {
    'kept-private': {'checks': "a file, a commit message or a pull-request body naming a being of the garden is refused",
                     'proof': 'test/public.py', 'label': "a file that names a host bean is refused"},
    'release-public': {'checks': "a file that names no being of the garden passes",
                       'proof': 'test/public.py', 'label': "a file that names no being passes"},
}
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
                           capture_output=True, text=True, encoding='utf-8', timeout=10)
        shallow = subprocess.run(['git', '-C', garden, 'rev-parse', '--is-shallow-repository'],
                                 capture_output=True, text=True, encoding='utf-8', timeout=10).stdout.strip()
    except Exception:
        return None
    roots = r.stdout.split()
    return roots[-1][:12] if r.returncode == 0 and roots and shallow != 'true' else None


_EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+')
_ADDR = re.compile(r'(?<![\w.:])(?:\d{1,3}(?:\.\d{1,3}){3}|[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7})(?:/\d{1,3})?(?![\w.:])')
_DOC_NETS = [ipaddress.ip_network(n) for n in ('192.0.2.0/24', '198.51.100.0/24', '203.0.113.0/24', '2001:db8::/32',
                                                '127.0.0.0/8', '::1/128', '0.0.0.0/32', '::/128')]
_DOC_DOMAINS = ('example.org', 'example.com', 'example.net', 'example', 'invalid', 'localhost', 'test')


def _said(node):
    """Every text a front matter holds, keys and values, however deep."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield str(k)
            yield from _said(v)
    elif isinstance(node, list):
        for v in node:
            yield from _said(v)
    elif isinstance(node, str):
        yield node


def reachable(fm):
    """The network and email addresses a front matter holds anywhere, less those kept for documentation."""
    out = set()
    for text in _said(fm):
        for m in _ADDR.findall(text):
            try:
                a = ipaddress.ip_network(m, strict=False)
            except ValueError:
                continue
            if not any(a.version == n.version and a.subnet_of(n) for n in _DOC_NETS):
                out.add(m)
        for m in _EMAIL.findall(text):
            dom = m.rsplit('@', 1)[1].lower()
            if not any(dom == d or dom.endswith('.' + d) for d in _DOC_DOMAINS):
                out.add(m)
    return out


def estate_words(garden, public=frozenset()):
    """What a garden knows that this repository must never say. Derived from the garden itself: every name it gives
    (bean and mapping ids, root names, its own id) and every value it identifies something by (each identity
    anchor's value, whatever its key), less an anchor value every token of which is `public`."""
    names, values = set(), set()
    for f in dmgarden.paths(garden, 'beans'):
        head, _ = dmparse.read(f)
        try:
            fm = dmparse.loads(head) or {}
        except Exception:
            continue
        if not isinstance(fm, dict):
            continue
        if fm.get('bean'):
            names.add(str(fm['bean']))
        if isinstance(fm.get('title'), str) and len(fm['title'].split()) >= 3:
            values.add(' '.join(fm['title'].split()))
        values |= reachable(fm)
        ident = fm.get('identity') if isinstance(fm.get('identity'), dict) else {}
        for a in (ident.get('anchors') or []):
            # a yes/no is no one's identity, and `True` guarded as a word would make "true" unsayable
            if isinstance(a, dict) and a.get('value') not in (None, '') and not isinstance(a.get('value'), bool):
                values.add(str(a['value']))
        for name in (fm.get('roots') if isinstance(fm.get('roots'), dict) else {}):
            names.add(str(name))
    for f in dmgarden.paths(garden, 'mappings'):
        names.add(os.path.basename(f)[:-3])
        try:
            fm = dmparse.loads(dmparse.read(f)[0]) or {}
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
    return {w.lower() for w in names | values if len(w) >= 3}


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
    ok |= _table_words(os.path.join(HERE, '..', 'seed', 'knowledge', 'technology.tsv'))
    ok |= _law_words()
    ok |= {w for w, paths in _allow_lines() if not paths}
    return ok


@functools.lru_cache(maxsize=None)
def _law_words():
    """The law's own names for kinds of being and for the keys a being is identified by (`product` in `product:samba`):
    this repository publishes them."""
    try:
        law = dmparse.loads(dmparse.read(os.path.join(HERE, '..', 'seed', 'std-vocab.md'))[0]) or {}
    except Exception:
        return frozenset()
    names = [str(g.get('genos')) for g in law.get('gene') or [] if isinstance(g, dict) and g.get('genos')]
    names += [str(t.get('term')) for t in law.get('terms') or [] if isinstance(t, dict) and isinstance(t.get('anchor'), dict)]
    return frozenset(t for n in names for t in _tokens(n) if len(t) >= 3)


@functools.lru_cache(maxsize=None)
def _table_words(path):
    """The words of one published table's cells, four letters and more."""
    ok = set()
    try:
        with open(path, encoding='utf-8', errors='replace') as fh:
            for line in fh:
                for cell in line.rstrip('\n').split('\t'):
                    ok.update(t for t in _tokens(cell) if len(t) >= 4)
    except OSError:
        pass
    return frozenset(ok)


def allowed_in(path, repo=None):
    """The words PUBLIC-ALLOW makes public in one tracked file (a path as git spells it) and nowhere else — and every
    word it names, in PUBLIC-ALLOW itself: the line that records a decision has to be able to say the word. A published
    table under seed/knowledge/ may say its own words."""
    out = {w for w, paths in _allow_lines() if path in paths or path == 'seed/PUBLIC-ALLOW'}
    if path.startswith('seed/knowledge/') and path.endswith('.tsv') and repo:
        out |= _table_words(os.path.join(repo, *path.split('/')))
    return out


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
        # -z: a path holding a space is one path, not two that exist nowhere
        for f in [x for x in subprocess.run(['git', 'ls-files', '-z'], capture_output=True, text=True, encoding='utf-8',
                                            errors='replace', cwd=repo).stdout.split('\0') if x]:
            p = os.path.join(repo, f)
            try:
                body = open(p, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            for w, line in hits(body, words - allowed_in(f, repo)).items():
                bad.append((f"{f}:{line}", w))
    if rng:
        msgs = subprocess.run(['git', 'log', '--format=%H%n%B', rng], capture_output=True, text=True,
                              encoding='utf-8', errors='replace', cwd=repo).stdout
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
