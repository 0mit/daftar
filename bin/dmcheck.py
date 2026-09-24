#!/usr/bin/env python3
"""dmcheck — the gate: judges a garden against the law in force, and refuses what breaks it.

    python3 bin/dmcheck.py                  # the whole garden as the WORKING TREE holds it (`--all` says the same)
    python3 bin/dmcheck.py beans/<id>.md …  # those beans (a mapping's path, or a bare id, too), within the whole garden
    python3 bin/dmcheck.py --staged         # what a commit would hold: the INDEX. The pre-commit hook runs this.
    add -v (or DAFTAR_VERBOSE=1)            # with --staged: test/fast.py lists each check it passed, not only its count

(`python` on Windows.) Exit 0 = clean, 1 = errors, 2 = setup: no PyYAML, or an argument that names no bean here.

WHICH COPY IS JUDGED. By hand, the beans, the vocabulary and the manifest are read from the WORKING TREE, so a bean is
checked as it is written, before anything is staged; the commit-time rules (the journal duty, RULE-CHANGE, a document
destroyed, gutted or emptied) read the index, the one place a commit's contents exist. `--staged` reads EVERYTHING from
the index: it is copied whole into a temporary directory, and the gate and test/fast.py found there judge that copy —
what is checked is what is committed, the law and the gate included. A fix left unstaged is not in the commit, and a
refused commit names each file the working tree holds differently.

NAMED BEANS. With paths, every document is still read — a link resolves against the whole garden, an establishing
anchor is compared with every other — but only the findings about the named documents are printed, with those about
the law and the garden as a whole; what the others hold is counted in the last line. A path that is not a bean or a
mapping of this garden is refused, never passed.

A CLEAN RUN PRINTS ONE LINE, the verdict: `<garden> (daftar <release>, gardener <id>, garden <id>): N docs, 0 error(s),
0 warning(s)`. A finding is printed above it, on its own line, its reason beneath — and, for the refusals met most,
its fix: the form a tested example of seed/FORMS.md or the cookbook writes, or the values the law allows, and the
rule's name with `python3 bin/dmwhy.py <name>`, which says why — not a document to read whole.

Session/model-agnostic gate, in two halves (v2 P2 / plan D4):

  CORE        the bean GRAMMAR, which is not a per-term rule and so stays in code: front-matter shape,
              id == filename, kebab ids, required keys, provenance shape, the identity capsule +
              establishing-anchor dedup, vocab-driven ip dedup, the std-vocab `extends:` pin, link
              integrity over the generic ref sections, the acyclic check, journal<->commit binding.

  INTERPRETER ONE generic loop that enforces every vocabulary term from its `schema:` block. There are
              NO per-term blocks here. A type rule is changed by editing VOCAB.md — a human-ratified
              rule-change — never by editing this file. Terms are read from BOTH tiers (the skill's
              std-vocab and the garden's VOCAB); a term with no `schema:` is documentation only.
              The schema language is documented in VOCAB.md under `schema_language:`.
"""
import difflib, glob, json, math, os, re, sys, fnmatch, ipaddress, shutil, stat, subprocess, tempfile
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmform
import dmsafe          # the staged-state checks below run dmsafe's OWN comparison, not a copy of it
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def own_garden_id(root=None):
    """A GARDEN'S IDENTITY (std-vocab 21.0, `garden_id`): the first twelve hex digits of the root of its first-parent
    history — the commit it germinated from. Read from git, the one place it lives, and written in no document of the
    garden: the product version is read the same way and for the same reason. None outside a git repository, and for a
    shallow clone, which cannot see its root. One reader, in dmparse, shared with the merge and the proposals."""
    return dmparse.garden_id(root or ROOT)


def _product():
    """`daftar v<tag>` — DERIVED from git, because the version lives in an annotated tag and nowhere else.
    Every version this repo ever typed into prose rotted (four titles reading v1.0 over v2 bodies, two
    stale pins); the two that stayed correct were derived. A tag has no second copy to disagree with.

    IN A GARDEN, the garden's own name and the release it adopted: `GARDEN.md` names both (`garden:` and
    `daftar_release:`, written by germinate.sh and dmupgrade.py). A garden's git history carries no daftar
    tags, so describing it printed "daftar (untagged)" on every garden anyone grew."""
    _g = load(os.path.join(ROOT, 'GARDEN.md'))[0] if os.path.isfile(os.path.join(ROOT, 'GARDEN.md')) else None
    if isinstance(_g, dict) and _g.get('garden') and _g.get('daftar_release'):
        # WHOSE NOTEBOOK THIS IS, on the first line anyone reads (21.0): two gardens may share a machine and a name,
        # and the line an agent shows its person is where the gardener and the garden's identity belong.
        _who = [f"gardener {_g['gardener']}"] if _g.get('gardener') else []
        _gid = own_garden_id()
        return f"{_g['garden']} (daftar {_g['daftar_release']}" + ''.join(', ' + w for w in _who + ([f"garden {_gid}"] if _gid else [])) + ")"
    try:
        v = subprocess.run(['git', '-C', ROOT, 'describe', '--tags', '--always', '--dirty'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5).stdout.strip()
        return f"daftar {v}" if v else "daftar (untagged)"
    except Exception:
        return "daftar (untagged)"


# ============================== THE COMMAND LINE ==============================
# READ BEFORE THE LAW IS. Until v0.34.1 the gate read no argument at all: `dmcheck.py beans/x.md` judged every bean and
# failed on another's error, and `dmcheck.py beans/nonexistent.md` passed — a path nobody could have meant, answered
# with a clean verdict. An argument is now a flag the gate declares or a document it can name, and anything else is
# refused before a word of the law is read (exit 2).
_PY = 'python' if os.name == 'nt' else 'python3'


def _usage():
    return __doc__.split('\nSession/model-agnostic')[0].rstrip()


def _refuse(msg):
    print(f"dmcheck: {msg}", file=sys.stderr)
    sys.exit(2)


def _arguments(argv):
    """{staged, verbose, paths} from the command line. `--all` is the whole garden, as no argument is; beside a path it
    contradicts it, and is refused."""
    a = {'staged': False, 'paths': [], 'all': False,
         'verbose': os.environ.get('DAFTAR_VERBOSE', '').strip() not in ('', '0')}
    for x in argv:
        if x in ('-h', '--help'):
            print(_usage())
            sys.exit(0)
        elif x == '--all':
            a['all'] = True
        elif x == '--staged':
            a['staged'] = True
        elif x in ('-v', '--verbose'):
            a['verbose'] = True
        elif x.startswith('-'):
            _refuse(f"{x!r} is no option of the gate. It takes --all, --staged, -v and the paths of beans "
                    f"(`{_PY} bin/dmcheck.py --help` says what each does)")
        else:
            a['paths'].append(x)
    if a['all'] and a['paths']:
        _refuse(f"--all judges the whole garden, and {a['paths'][0]!r} names one document: give one or the other")
    return a


def _named(paths):
    """{(is_bean, id): its garden path} for each document the command line names, resolved in THIS garden: a path as the
    shell gives it, else as the gate writes it (from the garden's root), or a bare id as the gate's findings name one.
    Anything that is not a bean or a mapping here is refused by name, all of them at once."""
    out, bad = {}, []
    for p in paths:
        if not (p.endswith('.md') or '/' in p or os.sep in p or os.path.exists(p)):
            _hits = [((d == 'beans'), p, f"{d}/{p}.md") for d in ('beans', 'mappings')
                     if os.path.isfile(os.path.join(ROOT, d, p + '.md'))]
            if len(_hits) == 1:
                out[_hits[0][:2]] = _hits[0][2]
            else:
                bad.append(f"{p}: names both beans/{p}.md and mappings/{p}.md — give the path" if _hits else
                           f"{p}: no bean or mapping of this garden is called {p!r} (beans/{p}.md, mappings/{p}.md)")
            continue
        _at = next((c for c in [os.path.abspath(p)] + ([] if os.path.isabs(p) else [os.path.join(ROOT, p)])
                    if os.path.exists(c)), None)
        if _at is None:
            bad.append(f"{p}: no such file — a path is read from where you stand, then from the garden's root")
            continue
        if os.path.isdir(_at):
            bad.append(f"{p}: a directory — name the beans in it, or give no argument to judge the whole garden")
            continue
        _dir, _file = os.path.split(_at)
        _in = next((d for d in ('beans', 'mappings') if os.path.isdir(os.path.join(ROOT, d))
                    and os.path.samefile(_dir, os.path.join(ROOT, d))), None)
        if _in and _file.endswith('.md'):
            out[(_in == 'beans', _file[:-3])] = f"{_in}/{_file}"
        else:
            bad.append(f"{p}: not a bean or a mapping of this garden — the gate names beans/<id>.md and "
                       f"mappings/<id>.md one by one; with no argument it judges the whole garden, its law and manifest")
    if bad:
        for b in bad:
            print(f"dmcheck: {b}", file=sys.stderr)
        sys.exit(2)
    return out


def _rmtree(path):
    """A temporary copy, removed whole — on Windows too, where a read-only file stops a plain rmtree."""
    def again(fn, p, *_):
        os.chmod(p, stat.S_IWRITE)
        fn(p)
    try:
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=again)
        else:
            shutil.rmtree(path, onerror=again)
    except OSError:
        pass                                      # a copy left in the temp directory harms no garden


def _staged(args):
    """THE PRE-COMMIT HOOK'S RUN: the gate and test/fast.py, judging a copy of the INDEX.

    The hook used to run the gate on the working tree while git committed the index. Under partial staging the two
    differ, and the difference let a refused bean through: staged broken, refused, fixed in the working tree and not
    staged again, the next `git commit` found nothing wrong — the gate read the fix — and committed the broken copy.
    So what the hook judges is now what git commits. `git checkout-index` copies every staged file into a temporary
    directory (git's own export of an index, which honours GIT_INDEX_FILE, so `commit -a` and `commit <path>` are
    judged by the index they build), and the gate FOUND THERE runs on it: the staged law, the staged manifest, the
    staged beans — and the staged gate, because a change to the gate is committed like any other. Its questions to git
    reach this repository through GIT_DIR and GIT_INDEX_FILE, with the copy as the work tree. Nothing here writes to
    the garden or its index; the copy is removed however the run ends.

    Git is asked here through `ask`, not `_git` below: this runs before the gate's own definitions are read."""
    def ask(*a):
        """(git's answer in ROOT, None), or (None, why) when the question went unanswered. Read as bytes and decoded
        here — as UTF-8 whatever the machine's code page, a path kept byte for byte (surrogateescape)."""
        try:
            r = subprocess.run(['git', '-C', ROOT, *a], capture_output=True, timeout=120,
                               env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
        except Exception as e:                    # git absent, or it hung
            return None, f"{e.__class__.__name__}: {e}"
        if r.returncode != 0:
            _e = r.stderr.decode('utf-8', 'replace').strip().splitlines()
            return None, _e[0] if _e else f"git exited {r.returncode}"
        return r.stdout.decode('utf-8', 'surrogateescape'), None

    def say(msg):
        print(dmparse.said(msg))

    _top, _why = ask('rev-parse', '--show-toplevel')
    _gitdir, _w2 = ask('rev-parse', '--absolute-git-dir')
    _index, _w3 = ask('rev-parse', '--git-path', 'index')
    _why = _why or _w2 or _w3
    if _why:
        say(f"ERROR NO INDEX at {ROOT} — this is not a readable git working copy ({_why}), so there is no staged state "
            f"to judge. This is a refusal, not a pass: run the gate in the garden's working copy.")
        return 1
    _top, _gitdir, _index = _top.strip(), _gitdir.strip(), _index.strip()
    _index = _index if os.path.isabs(_index) else os.path.join(ROOT, _index)
    _unmerged, _ = ask('ls-files', '--unmerged')
    if _unmerged:
        _paths = sorted({l.split('\t', 1)[-1] for l in _unmerged.splitlines() if l})
        say(f"ERROR the index holds unmerged paths ({', '.join(_paths[:4])}{', …' if len(_paths) > 4 else ''}) — git "
            f"commits none until each is resolved: settle them, `git add` them, and commit again")
        return 1
    # a path the command line names is handed on as a path inside the garden, which is where the copy is read
    passed = []
    for p in args['paths']:
        try:
            _r = os.path.relpath(os.path.abspath(p), ROOT)
        except ValueError:                        # another drive, on Windows
            _r = '..'
        _outside = _r == '..' or _r.startswith('..' + os.sep)
        _path_like = p.endswith('.md') or '/' in p or os.sep in p or os.path.exists(p)
        passed.append(_r.replace(os.sep, '/') if _path_like and not _outside else p)
    snap = tempfile.mkdtemp(prefix='dmcheck-staged-')
    rc = 1
    try:
        _, _why = ask('-C', _top, 'checkout-index', '--all', '--prefix=' + snap.replace(os.sep, '/').rstrip('/') + '/')
        if _why:
            say(f"ERROR the index could not be copied for judging ({_why}) — nothing was checked, so nothing may be "
                f"committed on this run")
            return 1
        here = os.path.normpath(os.path.join(snap, os.path.relpath(ROOT, _top)))
        env = dict(os.environ, GIT_DIR=_gitdir, GIT_WORK_TREE=snap, GIT_INDEX_FILE=_index, GIT_OPTIONAL_LOCKS='0',
                   PYTHONDONTWRITEBYTECODE='1')
        env.pop('GIT_PREFIX', None)
        missing = [f for f in ('bin/dmcheck.py',) + (() if args['paths'] else ('test/fast.py',))
                   if not os.path.isfile(os.path.join(here, f))]
        if missing:
            say(f"ERROR the index holds no {' and no '.join(missing)} — what is staged is judged by what is staged, "
                f"and a garden is not committed without {'it' if len(missing) == 1 else 'them'}. "
                f"Restore: git checkout HEAD -- {' '.join(missing)}")
            return 1
        # a document the command line names and the index does not hold is not staged, whatever the working tree has
        _absent = [p for p, q in zip(args['paths'], passed)
                   if not (os.path.isfile(os.path.join(here, q)) if ('/' in q or q.endswith('.md')) else
                           any(os.path.isfile(os.path.join(here, d, q + '.md')) for d in ('beans', 'mappings')))]
        if _absent:
            for p in _absent:
                print(dmparse.said(f"dmcheck: {p}: the index holds no such document — `git add` it to judge it as "
                                   f"staged, or leave out --staged to judge the working tree"), file=sys.stderr)
            return 2
        sys.stdout.flush()
        rc = subprocess.run([sys.executable, os.path.join(here, 'bin', 'dmcheck.py'), *passed],
                            cwd=here, env=env).returncode
        # test/fast.py judges the corpus whole, so it runs when the whole garden is judged, as the hook judges it
        if rc == 0 and not args['paths']:
            rc = subprocess.run([sys.executable, os.path.join(here, 'test', 'fast.py')]
                                + (['--verbose'] if args['verbose'] else []), cwd=here, env=env).returncode
    finally:
        _rmtree(snap)
    if rc == 1:
        # THE REFUSAL QUOTED THE STAGED COPY. A writer who fixed the file and did not stage it again sees a fix the
        # commit does not hold, so each file the working tree holds otherwise is named, with what to do.
        _changed, _ = ask('diff', '--name-only', '-z')
        _new, _ = ask('ls-files', '--others', '--exclude-standard', '-z', '--', 'beans', 'mappings')
        _held = [f"{p} (changed)" for p in (_changed or '').split('\0') if p] + \
                [f"{p} (new)" for p in (_new or '').split('\0') if p]
        if _held:
            sys.stdout.flush()
            say(f"\nThis judged what is STAGED. The working tree holds, unstaged: {', '.join(_held[:6])}"
                f"{', …' if len(_held) > 6 else ''}. A fix made there is not in the commit until it is staged: "
                f"git add it (git add -A stages everything), then commit again.")
    return rc


if __name__ == '__main__':
    # before the law is read: a refused argument costs nothing, and --staged judges the law the INDEX holds, not this one
    ARGS = _arguments(sys.argv[1:])
    if ARGS['staged']:
        sys.exit(_staged(ARGS))

# The sections a bean states its OWN facts in. Three checks ask this same question — the float scan, the
# IP collector and the single-owner duplicate scan — and each used to carry its own copy of the answer.
# `section_keys()` further down deliberately does NOT use this: it asks a different question.
_AUTHORITATIVE = ('owns', 'details')
# P4: `refs`, `depends_on` and `consumes` used to be hardcoded here. They are declared vocabulary terms
# now, so the gate no longer names a single relation — every edge it resolves comes from a schema.
errors, warns = [], []
LANGUAGE_PATTERNS = []

# ---- THE STATE THE PLIES SHARE, AND THE ONLY STATE THEY SHARE -------------------------------------
# Each name below is PUBLISHED by exactly one ply and READ by later ones; `PLIES` at the foot of the
# file states that dependency in the same order and says why each ply cannot move earlier.
#
#   docs, bean_ids, map_ids           <- build_docs
#   est_owner                         <- check_identity_capsule
#   ALL_FM, TARGETS_OF                <- build_all_fm_and_targets
#   VACANCY_REASONS                   <- check_vacancy_reasons_declared
#   DAG_TERMS, dep_graph              <- check_link_integrity
#   DOCUMENTISH, LAW_DOCS, FRONT_MATTER_DOCS
#                                     <- build_staged_constants
#
# They are deliberately NOT pre-bound to empty defaults: a ply that runs out of order must raise
# NameError rather than quietly judge an empty corpus and print `0 error(s)`, which is the same
# refusal-over-silence rule `law_carrier` and the no-index check already make. Everything ELSE a ply
# computes is its own local. These functions were carved out of top-level script code and the carve
# left every loop variable behind as a module global — 109 names, none with a second reader, any one
# of which could have been read across plies with nothing saying so.


def _row(reg, key):
    """A registry lookup keyed by BEAN DATA, which after a semantic merge may be a conflict record.

    `{'conflict': [...]}` is unhashable, and handing it to a dict lookup killed the gate outright —
    no verdict, none of the accumulated errors printed, and, because the pre-commit hook runs this
    file, no way to commit the edit that would resolve the merge. The gate stopped being a gate and
    became a wall. A non-scalar can never match a registry row, so it resolves to None and lands in
    the branch that already exists for a value the vocabulary does not declare.
    """
    return reg.get(key) if isinstance(key, (str, int, bool)) else None


def _is_conflict(v):
    return isinstance(v, dict) and isinstance(v.get('conflict'), list)


def _uncaptured(fm, path, v):
    """None when the conflict record `v` at `path` is one the merge driver CAPTURED and declared (`merge_conflicts`'
    meaning in the law), else what it lacks. MERGE.md §10 makes a captured conflict committable — lossless capture
    first, human choice after — so the per-term rules stand down on a value nobody has chosen yet, and the single
    unclean warning speaks for the bean. Only what the driver writes earns that: `merge_open: true`, the path named in
    `merge_conflicts`, and a record that is `{conflict: [...]}` and nothing else, holding two values or more that
    differ. A record short of any of them shielded values the gate refuses — a party nobody is, a day no calendar has,
    parts that do not add up — behind a warning, on nobody's say but the document's own."""
    if fm.get('merge_open') is not True:
        return "with no `merge_open: true`"
    _named = fm.get('merge_conflicts')
    if not (isinstance(_named, list) and path in [p for p in _named if isinstance(p, str)]):
        return "at a path `merge_conflicts` does not name"
    if set(v) != {'conflict'}:
        return f"that carries {sorted(map(str, set(v) - {'conflict'}))} beside `conflict`"
    if len({_canon(x) for x in v['conflict']}) < 2:
        return "with fewer than two different values — a disagreement has two sides"
    return None


def _captured(fm, path, v):
    """True when the value at `path` is a conflict the merge driver captured and declared (see _uncaptured)."""
    return _is_conflict(v) and _uncaptured(fm, path, v) is None


def _canon(x):
    """One spelling of a value, to tell two sides of a conflict apart — never a traceback on an odd key."""
    import json
    try:
        return json.dumps(x, sort_keys=True, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return repr(x)


def _member_path(term, prefix, i, v):
    """Where the merge driver says a conflict record in a LIST is. Each member of a list a term merges `multi` is keyed
    by the fields its `merge.order` names (bin/dmmerge.py `members`), and `merge_conflicts` names it `<term>.<key>`: the
    one field's value, or the fields' values as one canonical list. A list nobody merges member by member, or whose
    sides do not agree on their key, has no such path and is addressed by position, `<path>[<i>]`."""
    import json, unicodedata
    ident = dmparse.identity_fields((((TERMS.get(term) or {}).get('merge') or {}) if isinstance(term, str) else {}).get('order')) \
        if prefix == term else None
    sides = v.get('conflict') if _is_conflict(v) else None
    if not ident or not sides or not all(isinstance(x, dict) for x in sides):
        return f"{prefix}[{i}]"

    def norm(x):                            # the canonical form the driver keys by: text trimmed and composed, a date ISO
        if isinstance(x, str):
            x = unicodedata.normalize('NFC', x).strip()
            try:
                return str(ipaddress.ip_address(x))
            except ValueError:
                return x
        if hasattr(x, 'isoformat'):
            return x.isoformat()
        if isinstance(x, dict):
            return {norm(k): norm(y) for k, y in x.items()}
        return [norm(y) for y in x] if isinstance(x, (list, tuple)) else x
    keys = set()
    for side in sides:
        vals = [side.get(f) for f, _ in ident]
        keys.add(str(vals[0]) if len(ident) == 1 and not ident[0][1] else
                 json.dumps(norm(vals), sort_keys=True, ensure_ascii=False, separators=(',', ':'), default=str))
    return f"{prefix}.{keys.pop()}" if len(keys) == 1 else f"{prefix}[{i}]"


def load(f):
    # line-anchored fences (bin/dmparse.py) — a `---`/`----` inside a value or the body never truncates
    try:
        head, body = dmparse.read(f)
    except dmparse.NotUTF8 as e:
        # A FILE THAT IS NOT UTF-8 IS REFUSED BY NAME, never a traceback that names no file: the pre-commit hook runs
        # this gate, and a person with many beans must be told which one, and what to do with it.
        return {'__err__': str(e), '__not_utf8__': True}, ''
    if head is None:
        return None, ''
    try:
        return dmparse.loads(head), body
    except Exception as e:
        return {'__err__': str(e)}, ''


# ============================== VOCABULARY ==============================
# THE LAW HAS ONE PATH AND NO FALLBACK. A gate that cannot find the vocabulary must refuse, not quietly
# load a different copy: falling back substitutes a different law, which is worse than failing. This is
# not hypothetical — the fallback resolved to a sibling clone pinned two majors behind.
STD = os.path.join(ROOT, 'seed', 'std-vocab.md')
std_ver, ip_patterns = None, []
std_fm = {}
if os.path.exists(STD):
    std_fm = load(STD)[0] or {}
    std_ver = str(std_fm.get('version'))
    for t in std_fm.get('terms', []):
        if t.get('term') == 'ip':
            ip_patterns = t.get('context_keys', [])
else:
    errors.append(f"std-vocab not found at {STD} — the law has ONE path and there is no fallback")

vocab_fm = load(os.path.join(ROOT, 'VOCAB.md'))[0]
if vocab_fm is None:
    # empty fences say nothing, and are read as nothing; NO fences is no vocabulary read at all, and a garden that
    # meant one would never learn it was ignored
    vocab_fm = {} if dmparse.read(os.path.join(ROOT, 'VOCAB.md'))[0] is not None else {'__err__': 'no --- fences'}
if not isinstance(vocab_fm, dict) or '__err__' in vocab_fm:
    # the garden's own vocabulary is read as a mapping or not at all: a list or a word in its fences, or YAML that does
    # not parse, is refused by name — never read as an empty vocabulary, and never a traceback further down
    errors.append(f"VOCAB.md: its front matter does not read ("
                  f"{vocab_fm['__err__'] if isinstance(vocab_fm, dict) else 'not a mapping'}) — this garden's own "
                  f"vocabulary is a mapping of what it adds to the law")
    vocab_fm = {}
# ...and each block it adds, each ENTRY of a block and each row it adds to a registry, in its own shape or not at all:
# `local_terms: 5`, `local_terms: [{term: [x]}]`, a cell that says no verdict or a pattern that does not compile are
# refused by name and left unread, never a traceback and never passed. bin/dmparse.py holds the one reading, which
# bin/dmrules.py shares — so the rules it lists are the rules this gate reads.
errors.extend(dmparse.vocab_read(vocab_fm))


_FILE_REGISTRIES = {}
_ROWS_READ = set()            # the garden's own registries whose rows have been read in their shape

def _registry_file(name):
    """Rows of a registry kept in a DATA FILE rather than in the law's prose (9.1). A classification of four
    hundred occupations is data the law POINTS at, not text it restates: `registry_files: [{registry, file,
    key}]` in the vocabulary names a tab-separated file (relative to the garden root), whose header row gives
    the columns. The file must exist — a registry the law declares and cannot find is an error, never an
    empty list, for the same reason the vocabulary itself has no fallback."""
    if name in _FILE_REGISTRIES:
        return _FILE_REGISTRIES[name]
    decl = next((r for r in (list(vocab_fm.get('registry_files') or []) + list(std_fm.get('registry_files') or []))
                 if isinstance(r, dict) and r.get('registry') == name), None)
    if decl is None:
        _FILE_REGISTRIES[name] = None
        return None
    path = os.path.join(ROOT, decl.get('file', ''))
    rows = []
    try:
        with open(path, encoding='utf-8') as fh:
            head = fh.readline().rstrip('\n').split('\t')
            for line in fh:
                if line.strip():
                    rows.append(dict(zip(head, line.rstrip('\n').split('\t'))))
    except OSError:
        errors.append(f"registry_files: registry '{name}' is declared at {decl.get('file')} and that file is missing "
                      f"— a declared registry is never read as empty")
    except UnicodeDecodeError as e:
        errors.append(f"registry_files: registry '{name}' is declared at {decl.get('file')}, and that file is not UTF-8 "
                      f"(byte {e.start}) — save it as UTF-8; a declared registry is never read as empty")
    # a row a data file holds is judged as a row a garden writes is: a `pattern` it declares is one the gate can match
    # with, or the row is refused by name and left unread
    for _r in list(rows):
        if dmparse.pattern_problem(_r):
            errors.append(f"registry_files: registry '{name}' ({decl.get('file')}): the row "
                          f"'{_r.get(decl.get('key')) if isinstance(decl.get('key'), str) else ''}' "
                          f"{dmparse.pattern_problem(_r)} — it is left unread until it is one")
            rows.remove(_r)
    _FILE_REGISTRIES[name] = rows
    return rows

def registry(name):
    """A top-level registry, from the garden if it declares one, else from Tier-0 — plus any rows the garden
    ADDS under `registry_additions: {<name>: [...]}`. A registry may also live in a data file (`registry_files`, 9.1).

    Replacing a registry wholesale is still possible, and it is the wrong tool for adding one row: a garden
    that needed one operating system Tier-0 lacks had to copy the whole registry and then declare a vacancy
    for every row it had copied and did not use (found by the v0.3.1 cold-start drill). An addition names
    only what is new, so the garden accounts only for what it declared."""
    if not isinstance(name, str):
        return []                           # a list or a map where a registry's name belongs names none; its rule says so
    if vocab_fm.get(name) is not None and name not in _ROWS_READ:
        # a registry the garden restates is a list of rows, each in its shape, or it is not read: refused once, by
        # name, and the law's own rows stand in its place for the rest of the run
        _ROWS_READ.add(name)
        vocab_fm[name], _why = dmparse.restated_rows(vocab_fm, name)
        errors.extend(_why)
    base = vocab_fm.get(name) if vocab_fm.get(name) is not None else (std_fm.get(name) or [])
    if not base:
        base = _registry_file(name) or []
    # An added row the base already has is NOT added twice: `check_local_additions` reports it by name, and a
    # doubled row would otherwise surface as a misleading "exported enum has drifted".
    def _dup(row):
        return isinstance(row, dict) and row and any(
            isinstance(b, dict) and b.get(next(iter(row))) == row[next(iter(row))] for b in base)
    return list(base) + [r for r in ((vocab_fm.get('registry_additions') or {}).get(name) or []) if not _dup(r)]

# TERMS: every vocabulary term from both tiers, garden-local last so a garden may refine a std term.
def _overlay(base, over):
    """Garden-local overlay on a Tier-0 term: local keys win, `schema` merges key-by-key.

    `schema.values_add: [...]` APPENDS to the Tier-0 enum instead of replacing it, so a garden adds one value
    without restating (and then having to account for) every value Tier-0 already offers."""
    out = dict(base)
    for k, v in over.items():
        if k == 'schema' and isinstance(v, dict) and isinstance(base.get('schema'), dict):
            out['schema'] = {**base['schema'], **v}
            # `attrs` merges PER ATTRIBUTE (13.0): a garden that adds one attribute to a Tier-0 term, or gives one
            # a domain, must not thereby restate — and then own — every attribute the standard already declares.
            if isinstance(v.get('attrs'), dict) and isinstance(base['schema'].get('attrs'), dict):
                out['schema']['attrs'] = {**base['schema']['attrs'],
                                          **{a: {**(base['schema']['attrs'].get(a) or {}), **(r or {})}
                                             for a, r in v['attrs'].items()}}
            if isinstance(v.get('cells'), list) and isinstance(base['schema'].get('cells'), list):
                out['schema']['cells'] = list(base['schema']['cells']) + list(v['cells'])
        else:
            out[k] = v
    _s = out.get('schema')
    if isinstance(_s, dict) and _s.get('values_add'):
        _s['values'] = list(_s.get('values') or []) + [x for x in _s['values_add'] if x not in (_s.get('values') or [])]
    return out

# PROFILES (2.0/E4): Tier-0 terms a garden must OPT IN to. A garden that manages no code should not
# inherit code terms — and their vacancies come with them, so opting in never imports unexplained debt.
PROFILE_TERMS, PROFILE_VAC = [], []
for _pname in (vocab_fm.get('extends_profiles') or []):
    _prof = (std_fm.get('profiles') or {}).get(_pname)
    if _prof is None:
        errors.append(f"VOCAB extends_profiles: '{_pname}' is not a profile std-vocab@{std_ver} offers")
        continue
    PROFILE_TERMS += (_prof.get('terms') or [])
    PROFILE_VAC += (_prof.get('vacancies') or [])

class _Named(dict):
    """A table of the law looked up by a name a bean wrote. A name is text: a list or a map where a name belongs names
    nothing here — the entry's own check refuses it by name — and is never a traceback in a check that only asked."""
    def get(self, k, d=None):
        return dict.get(self, k, d) if isinstance(k, (str, int, bool, float, type(None))) else d

    def __contains__(self, k):
        return isinstance(k, (str, int, bool, float, type(None))) and dict.__contains__(self, k)


TERMS, TIER0_TERMS = _Named(), set()
for t in (std_fm.get('terms') or []) + PROFILE_TERMS:
    if isinstance(t, dict) and t.get('term'):
        TERMS[t['term']] = t
        TIER0_TERMS.add(t['term'])
for t in (vocab_fm.get('local_terms') or []):
    if isinstance(t, dict) and t.get('term'):
        TERMS[t['term']] = _overlay(TERMS[t['term']], t) if t['term'] in TERMS else t
SCHEMAS = {n: t['schema'] for n, t in TERMS.items() if isinstance(t.get('schema'), dict)}

# GENE registry (22.0; `kinds` until then): what each genos IS, including the nature it refines (P3/D1 `of_nature`).
GENE = _Named()
for k in (std_fm.get('gene') or []) + (registry('local_gene') or []):
    if isinstance(k, dict) and k.get('genos'):
        GENE[k['genos']] = k
# IDENTITY POLICY: which bean axis selects an identity/anchor policy row, and from which registry.
# Declared in VOCAB (`identity_policy`) so the gate names neither the axis nor the registry (P3/D1).
IDP = vocab_fm.get('identity_policy') or std_fm.get('identity_policy') or {}
# WHAT THE LAW RETIRED (21.0, `retired:`): a refusal of a retired name says where it went, and the gate keeps no list
# of its own — the hint for `authority` lived in this file for one release, a rule stated in the tool and not the law.
RETIRED = {(str(r.get('at')), str(r.get('name'))): r.get('instead') for r in (std_fm.get('retired') or [])
           if isinstance(r, dict) and r.get('name')}


def retired_hint(at, name):
    _i = RETIRED.get((at, str(name)))
    return f" — retired: {_i}" if _i else ""


def translate_hint():
    """The command that translates a word the law retired, as this garden runs it: bin/dmupgrade.py with the release
    GARDEN.md records. A garden crossing into that release runs it anyway; one that crossed already runs it again, and
    it translates whatever came in since — a bean from a branch or a clone still at the older release, or a proposal."""
    _g = load(os.path.join(ROOT, 'GARDEN.md'))[0] if os.path.isfile(os.path.join(ROOT, 'GARDEN.md')) else None
    _rel = _g.get('daftar_release') if isinstance(_g, dict) else None
    return (f"`{'python' if os.name == 'nt' else 'python3'} bin/dmupgrade.py {_rel or '<the release>'}` translates it — "
            f"in a garden crossing into the release, and in one that crossed already")


# ---- THE FIX IS SAID IN THE REFUSAL (v0.34.1) ------------------------------------------------------------------------
# A refusal ended "(VOCAB timing term)" or "(see seed/COOKBOOK.md)", and a coding agent keeping a garden did what it
# said: it opened seed/std-vocab.md — a quarter of a megabyte — and then MODEL.md, CHECKLIST.md and the cookbook.
# Driving a small open model on a PC, it read 85,000 to 165,000 characters of them and stalled, or never finished; told
# to read only a short page of forms, it read none and finished. So the refusals an agent meets most carry their fix:
# the form to write, one line of YAML as a tested example writes it, or the values the law allows — and, for WHY, the
# command that prints that one rule with its reason, never a document to read whole. The rule keeps its name.
# THE FORMS ARE THE GUIDES' OWN EXAMPLES — seed/FORMS.md's first, then the cookbook's and seed/README.md's — each
# committed in a fresh garden by test/germinate.py, so a form shown is a form that passes. They are read for the WORDS
# of a refusal and nothing else: no verdict depends on them, and a garden without them is judged the same, its
# refusals only saying less. An example marked `unsaid:` is a guide's form for what nobody said; it is shown, beside
# the other, for the terms its marker names.
_GUIDES = ('seed/FORMS.md', 'seed/COOKBOOK.md', 'seed/README.md')
_EXAMPLE = re.compile(r'<!-- (example|unsaid): beans/[a-z0-9-]+\.md(?:, for ([a-z0-9_, ]+))? -->\n'
                      r'```markdown\n(.*?)\n```', re.S)
_READ_ONCE = {}


def _examples():
    """[(front matter, the terms it is the unsaid form of — empty for a recipe's)] of every example bean the guides
    show, in the order they show them."""
    if 'examples' not in _READ_ONCE:
        _READ_ONCE['examples'] = []
        for _g in _GUIDES:
            try:
                _page = open(os.path.join(ROOT, _g), encoding='utf-8').read().replace('\r\n', '\n')
            except (OSError, UnicodeDecodeError):
                continue
            for _m in _EXAMPLE.finditer(_page):
                try:
                    _fm = dmparse.loads(dmparse.split_front_matter(_m.group(3) + '\n')[0] or '')
                except Exception:
                    continue
                if isinstance(_fm, dict):
                    _for = {t.strip() for t in (_m.group(2) or '').split(',') if t.strip()}
                    _READ_ONCE['examples'].append((_fm, _for if _m.group(1) == 'unsaid' else set()))
    return _READ_ONCE['examples']


def _flow(v):
    """A value as ONE line of YAML, spelt as the guides spell it — `{ key: value }`, `[a, b]` — a string bare only where
    YAML reads it back as that same string, so the line parses to exactly the value the example holds."""
    if isinstance(v, dict):
        return '{ ' + ', '.join(f"{k}: {_flow(x)}" for k, x in v.items()) + ' }' if v else '{}'
    if isinstance(v, list):
        return '[' + ', '.join(_flow(x) for x in v) + ']'
    if isinstance(v, bool) or v is None:
        return {True: 'true', False: 'false', None: 'null'}[v]
    if isinstance(v, int) or type(v).__name__ == 'date':
        return str(v)
    s = str(v)
    try:
        _bare = re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', s) is not None and dmparse.loads(s) == s
    except Exception:
        _bare = False
    return s if _bare else json.dumps(s, ensure_ascii=False)


def _held_at(path, genos=None):
    """[(value, unsaid-for)] the examples hold at `path`: a top-level key (`timing`), or an attribute further in
    (`transactions.amount`) — of a mapping, or of each entry of an open map or a list. With `genos`, only the examples
    of that genos."""
    out = []
    _head, *_rest = path.split('.')
    for _fm, _for in _examples():
        _vals = [_fm[_head]] if _head in _fm and genos in (None, _fm.get('genos')) else []
        for _seg in _rest:
            _next = []
            for _v in _vals:
                if isinstance(_v, dict) and _seg in _v:
                    _next.append(_v[_seg])
                    continue
                for _e in (_v.values() if isinstance(_v, dict) else _v if isinstance(_v, list) else []):
                    if isinstance(_e, dict) and _seg in _e:
                        _next.append(_e[_seg])
            _vals = _next
        out += [(_v, _for) for _v in _vals]
    return out


def _example_form(path, entry=False, genos=None):
    """The fix as the guides write it, in one line: `<key>: <value>` from the first recipe that holds `path` — with
    `entry`, one ENTRY of it, as it is keyed there; with `genos`, a recipe of that genos — and beside it the form a
    guide gives for when nobody said it, where one is marked for this term and differs. '' where no example holds it."""
    def _one(v):
        if not entry:
            return f"{path.split('.')[-1]}: {_flow(v)}"
        if isinstance(v, dict) and v:
            _k, _e = next(iter(v.items()))
            return f"{_k}: {_flow(_e)}"
        return _flow(v[0]) if isinstance(v, list) and v else ''
    _term = path.split('.')[0]
    _said = [_one(v) for v, f in _held_at(path, genos) if not f]
    _unsaid = [_one(v) for v, f in _held_at(path, genos) if _term in f]
    out = _said[0] if _said else ''
    if _unsaid and _unsaid[0] and _unsaid[0] != out:
        out += ('; when nobody said it, ' if out else 'when nobody said it, ') + _unsaid[0]
    return out


def _unsaid_form(term):
    """Only the form a guide gives for `term` when nobody said it — '' where none is marked."""
    return next((f"{term}: {_flow(v)}" for v, f in _held_at(term) if term in f), '')


def _rule(path, *names):
    """` (rule <path>; why: python3 bin/dmwhy.py <name>)`: the rule a refusal applies, by its name in the law, and the
    command that prints it with its reason — for the first of `names` (else the path, then its head) the reasoning
    explains. Without a reason to print, the name alone: never a document to read whole."""
    for _n in (names or (path, path.split('.')[0])):
        if ('why', _n) not in _READ_ONCE:
            try:
                import dmwhy
                _READ_ONCE[('why', _n)] = dmwhy.answers(_n)
            except Exception:
                _READ_ONCE[('why', _n)] = False
        if _READ_ONCE[('why', _n)]:
            return f" ({'' if _n == path else f'rule {path}; '}why: {_PY} bin/dmwhy.py {_n})"
    return f" (rule {path})"


def _by_nearness(word, among):
    """Every name in `among`, the nearest to `word` first: the whole list a refusal offers, in the order most useful."""
    return sorted({str(a) for a in among}, key=lambda t: (-difflib.SequenceMatcher(None, str(word), t).ratio(), t))


def _nearest(word, among, n=3, cutoff=0.6):
    """The names in `among` nearest to `word`, for a refusal to offer — a misspelling is named by what it misspells."""
    return difflib.get_close_matches(str(word), sorted({str(a) for a in among}), n=n, cutoff=cutoff)


PROV = std_fm.get('provenance_record') or {}
_axis, _reg = IDP.get('keyed_by'), IDP.get('registry')
POLICY = {}
if _axis and _reg:
    POLICY = {r[_axis]: r for r in (registry(_reg) or [])
              if isinstance(r, dict) and r.get(_axis)}


def _values_of(v):
    """A value rule's enum: written here (`values`), another term's (`values_from: <term>`), or a REGISTRY's own
    column (`values_from: "registry:<name>[].<field>"`) — the registry is then the enum's one owner, and no term
    keeps a copy of it to drift."""
    src = v.get('values_from')
    if src and str(src).startswith('registry:'):
        return [x for x in collect_path({}, str(src))]
    if src:
        return term_values(src)
    return list(v.get('values') or [])


def term_values(name):
    """The enum a term exports (for values_from / key_form: values_from:<term>)."""
    return _values_of(form_of(name)['value'])


def allowed_values(sch):
    return _values_of(dmform.attribute_form(None, sch)['value'])


# --- vocab self-consistency: an exported enum must not drift from its own definition -------------
# Declared by the term itself (`schema.values_consistent_with: [<path>...]`), so this names no term.
# A path is either `attr` (a list) or `attr[].sub` (a list of mappings, take each `sub`).
def collect_path(node, path):
    if path.startswith('registry:'):          # a top-level registry (either tier) rather than a path inside the term
        path = path[len('registry:'):]
        head0 = path.split('[].')[0]
        node = {head0: registry(head0)}
    head, _, sub = path.partition('[].')
    seq = node.get(head) or []
    if not sub:
        return [v for v in seq if not isinstance(v, (dict, list))]
    return [i.get(sub) for i in seq if isinstance(i, dict) and i.get(sub) is not None]

# --- the schema language must describe itself (std-vocab 11.3) -----------------------------------------------------
# The reverse gate holds every TERM to its occupants; nothing held the schema language to the gate. Measured
# 2026-09-20: four constructs were interpreted here and declared nowhere (`path`, `alt_form`, `attr_types`,
# `canonical_note`) — a cold-start drill found one of them by reading this file, which is not where a stranger
# should have to look. The other direction is the dangerous one: a key the language does not declare is a key no
# controller reads, so `entry_require_attrs` (one letter short) has always passed while enforcing nothing.
# AN ERROR since 12.0 (it was a warning for one release, 11.3, so that release could stay minor). The operator's
# ruling, 2026-09-20: a rule that silently enforces nothing is worse than a refusal, because the vocabulary SAYS it
# is in force. The same choice he made for an undeclared top-level key on a bean, one level up.
RETIRED_CONSTRUCTS = ('entry_required_attrs', 'required_attrs', 'entry_values', 'entry_types', 'attr_types',
                      'entry_pattern', 'entry_soft_pattern', 'entry_in_registry', 'entry_pattern_from_registry',
                      'on_aspect', 'entry_extents', 'attr_extents', 'entry_ref_fields', 'ref_fields',
                      'pointer_fields', 'cross_aspect', 'entry_required_if', 'entry_expect_if')


def check_schema_language():
    _declared = set(std_fm.get('schema_language') or {})
    if not _declared:
        return                      # the law did not load; the one-path refusal says so, once
    # THE SAME RULE ONE LEVEL IN: the domains `in:` may name are described in the law and implemented in dmform,
    # and the two lists are held equal — a domain the law offers and nothing reads is a rule that enforces nothing.
    _offered, _read = set((std_fm['schema_language'].get('attr_domains') or {})), set(dmform.DOMAINS)
    if _offered != _read:
        errors.append(f"VOCAB schema_language.attr_domains offers {sorted(_offered - _read) or 'nothing extra'} that "
                      f"bin/dmform.py does not read, and omits {sorted(_read - _offered) or 'nothing'} that it does")
    for _name, _sch in sorted(SCHEMAS.items()):
        for _a in attribute_form(_name, _sch)['unknown']:
            errors.append(f"VOCAB {_name}: attribute `{_a}` states no domain the language offers — every attribute "
                          f"says what it is a position `in:` (a list, a registry, an aspect, a type, a pattern, "
                          f"`extent`, `ref`, a pointer), or says `prose`, or owns up to `untyped`")
        for _k in sorted((set(_sch) - _declared) & set(RETIRED_CONSTRUCTS)):
            errors.append(f"VOCAB {_name}: schema key `{_k}` was RETIRED at std-vocab 13.0 — an attribute's law is "
                          f"stated once, in `schema.attrs.<name>: {{required, in, meaning}}`. Do not rewrite it by "
                          f"hand: `python3 bin/dmreform.py VOCAB.md` translates every term and proves it lost nothing")
        for _k in sorted(set(_sch) - _declared - set(RETIRED_CONSTRUCTS)):
            errors.append(f"VOCAB {_name}: schema key `{_k}` is not declared in schema_language" + (retired_hint('schema', _k) or
                         " — no controller reads an undeclared construct, so this rule enforces NOTHING. Check the "
                         "spelling against `schema_language` in seed/std-vocab.md"))


# --- a garden's local ADDITION that the standard now carries itself (v0.5.0) --------------------------------------
# The contribution path is: prove a value locally with values_add / registry_additions, propose it, and it lands in
# Tier-0. The garden that proved it then carried a duplicate, and the gate said only "the exported enum has drifted"
# (found by the second cold-start drill). This names the actual situation and the one-line fix.
def check_local_additions():
    _tier0 = {t['term']: (t.get('schema') or {}) for t in (std_fm.get('terms') or []) + PROFILE_TERMS
              if isinstance(t, dict) and t.get('term')}
    for _t in (vocab_fm.get('local_terms') or []):
        if not isinstance(_t, dict):
            continue
        for _v in ((_t.get('schema') or {}).get('values_add') or []):
            if _v in ((_tier0.get(_t.get('term')) or {}).get('values') or []):
                errors.append(f"VOCAB {_t.get('term')}: '{_v}' is in values_add, but std-vocab@{std_ver} already offers it — "
                              f"remove it from values_add in VOCAB.md (and its row from registry_additions, if any)")
    for _name, _rows in ((vocab_fm.get('registry_additions') or {}).items()):
        _base = std_fm.get(_name) or []
        for _row in (_rows or []):
            if not isinstance(_row, dict) or not _row:
                continue
            _k = next(iter(_row))
            if any(isinstance(_b, dict) and _b.get(_k) == _row[_k] for _b in _base):
                errors.append(f"VOCAB registry_additions.{_name}: the row {_k}={_row[_k]!r} is already in std-vocab@{std_ver} — "
                              f"remove it from registry_additions in VOCAB.md")


# --- a list's merge identity must name fields its entries actually carry (std-vocab@8.0) -----------------
# `merge.order: by-<field>[+<field>...]` is how dmmerge matches the members of a list across gardens. Three
# terms declared `by-key` over entries that have no `key`, and the merge silently matched each member by its
# whole content instead. Nothing could see it: the declaration was well-formed and no bean was wrong. Read
# from the declarations, so this names no term; the ref attrs are CORE (every self-ref entry is one).
REF_ATTRS = {'bean', 'mapping', 'field'}

def check_merge_identity():
    for _name, _term in TERMS.items():
        _m, _s = _term.get('merge') or {}, _term.get('schema') or {}
        if not isinstance(_m, dict) or _m.get('cardinality') != 'multi' or _s.get('shape') != 'list_of_entries':
            continue
        _ident = dmparse.identity_fields(_m.get('order'))
        if not _ident:
            errors.append(f"VOCAB {_name}: a list of entries merged member by member needs `order: by-<field>"
                          f"[+<field>...]`, not '{_m.get('order')}' — without one, members are matched by content")
            continue
        _form = dmform.attribute_form(_term, _s)
        _required = {n for n, _ in _facet(_form, 'required', 'entry')}
        _declared = (_required | {n for n, _ in _facet(_form, 'meaning')}
                     | {a for c in _form['cells'] if c['origin'] == 'required_if' for a in c['lacks']}
                     | (REF_ATTRS if _form['self_ref'] else set()))
        for _f, _may_lack in _ident:
            if _f not in _declared:
                errors.append(f"VOCAB {_name}: merge identity '{_m['order']}' names '{_f}', which no entry of this "
                              f"term declares")
            elif _may_lack and _f in _required:
                errors.append(f"VOCAB {_name}: merge identity marks '{_f}?' as possibly absent, but every entry "
                              f"must carry it — the `?` claims an absence the schema forbids")
            elif not _may_lack and _f not in _required:
                errors.append(f"VOCAB {_name}: merge identity '{_m['order']}' needs '{_f}' on every entry, but the "
                              f"schema does not require it — require it, or write '{_f}?' if its absence is a "
                              f"legitimate state")


# --- ASPECT SANITY RULES (2.1). An aspect is a CLOSED figure: its positions must exhaust it, each must
# know its complement, the complements must be mutual, and its poles must be a genuine contradictory pair.
# A figure with a loose end cannot say what a being is NOT, which is half of what a classification is for.
# VALUE TYPES (10.0): the patterns `entry_types` / `attr_types` name are rows of the law, not constants here.
VALUE_TYPES = {t['type']: t for t in (registry('value_types') or []) if isinstance(t, dict) and t.get('type')}
# No copy of a pattern lives here. Without the row, check_value_types reports the missing law ONCE, and the
# per-value checks stand down rather than refuse every id in the garden for a cause they cannot name.
# ONE FORM MEANS ONE SET OF DIGITS (std-vocab 16.0). In Python `\d` matches EVERY Unicode decimal digit, so until 16.0
# the gate accepted `۲۰۲۶-۰۹-۲۰` as an iso_date — a second spelling of a position, which nothing downstream can read
# as a date. The law's patterns are therefore matched ASCII-only, everywhere, through this one function — and to the end
# of the value: dmparse holds the one definition, which the merge's reading of a form shares.
def law_match(pattern, value):
    """dmparse's one matcher, and a form that does not compile is REFUSED BY NAME — once, and no value matches it —
    never a traceback. Every pattern a garden writes is read before this runs (`dmparse.vocab_read`); this stands
    behind a form reached some other way, such as the field of a registry row a `take:` names."""
    try:
        return dmparse.law_match(pattern, value)
    except (re.error, ValueError) as e:
        _m = f"the form '{pattern}' is not a regular expression ({e}) — no value is held to it until it is one"
        if _m not in errors:
            errors.append(_m)
        return None


KEBAB = re.compile(VALUE_TYPES['kebab']['pattern'], re.ASCII) if 'kebab' in VALUE_TYPES else None

def check_law_extents():
    """Extents written in the VOCABULARY, not on a bean — today, `expiry.notice`.

    A LAW THE GATE CANNOT SEE IS THE DEFECT THIS REPOSITORY KEEPS FINDING. `notice` is a region like any
    other, and if nothing checked it a term could declare a notice period in a unit that does not exist
    and no run would ever say so — the rule would be in force and unenforced, which is exactly what
    v0.14.0 and v0.15.0 were each spent undoing. It costs one function to judge the law by its own rule.
    """
    for _name, _term in (TERMS or {}).items():
        _n = ((_term or {}).get('schema') or {}).get('expiry') or {}
        if isinstance(_n, dict) and _n.get('notice') is not None:
            check_extent(f"VOCAB {_name}.schema.expiry.notice", _n['notice'])


def check_value_types():
    for _t in ('iso_date', 'kebab', 'count', 'text'):
        if _t not in VALUE_TYPES:
            errors.append(f"VOCAB: no `value_types` row for '{_t}' — the gate reads its type patterns from the law "
                          f"and has no copy of its own")
    _ex = (VALUE_TYPES.get('date') or {}).get('exists')
    if _ex is not None and not (isinstance(_ex, dict) and isinstance(_ex.get('reckoning'), list)
                                and all(isinstance(r, str) for r in _ex['reckoning'])):
        errors.append("VOCAB value_types[date].exists is a mapping { reckoning: [<reckoning>, ...] } — as written it "
                      "judges no day, and no day is judged until it is one")
# `journal` is one mapping, not a registry of rows, so it is read as the garden states it, else as the standard does.
JOURNAL = (vocab_fm.get('journal') if isinstance(vocab_fm.get('journal'), dict) else None) or \
          (std_fm.get('journal') if isinstance(std_fm.get('journal'), dict) else {})

def check_value_type(where, attr, val, typ):
    """A value against a declared value type. An undeclared type is itself an error: a schema naming a type
    the law does not define would otherwise check nothing and look as if it did."""
    t = VALUE_TYPES.get(typ)
    if not t and not VALUE_TYPES:
        return                      # the law itself is missing; check_value_types has said so once
    if not t:
        errors.append(f"{where}.{attr}: type '{typ}' is not declared in `value_types` {sorted(VALUE_TYPES)}")
    elif t.get('holds_no'):
        # text: its characters are held by check_text, over every key and string of the document; here, only that it
        # IS one text — a list or a map is not "characters a person reads"
        if not isinstance(val, (str, int, float)) or isinstance(val, bool):
            errors.append(f"{where}.{attr} is text, written as one string — not {type(val).__name__}")
        return
    elif t.get('any_system'):
        # A POSITION IN ANY SYSTEM OF THE TYPE'S DIMENSION, held to the type's unit (16.0): no system is the one a date
        # must be in. It must be in ONE system's own form, that system must HAVE the level, and a reading finer than
        # the level (a clock time on a date) is not the type.
        _held = [r for r in (registry('anchor_systems') or []) if isinstance(r, dict) and r.get('dimension') == t.get('dimension')
                 and isinstance(r.get('levels'), list) and any(l.get('level') == t.get('unit') for l in r['levels'])
                 and r.get('pattern') not in (None, 'none') and law_match(r['pattern'], val)]
        if not _held or re.search(r'[T ]\d{2}:\d{2}', str(val), re.ASCII):
            errors.append(f"{where}.{attr} '{val}' {t.get('refusal') or 'is in no system of dimension ' + str(t.get('dimension'))}")
        else:
            check_day_exists(f"{where}.{attr}", val, _held[0])
    elif not law_match(t['pattern'], val):
        errors.append(f"{where}.{attr}" + ("" if typ != 'kebab' else f" '{val}'") + f" {t.get('refusal') or 'does not match its type ' + typ}")
    elif t.get('system'):
        check_day_exists(f"{where}.{attr}", val, SYSTEMS.get(t['system']))


def day_unwritten(val, row):
    """None when the DAY a position names exists in its calendar — or when that calendar is not reckoned by rule, so no
    arithmetic can say — else what is wrong with it (`value_types[date].exists`).

    A pattern admits `persian:1404-12-30` and `2026-02-30` alike: two digits are two digits. Only the calendar knows that
    Esfand 1404 has twenty-nine days, and `bin/dmcal.py` carries each calendar that reckons by rule as its two functions,
    to the day and from it. So a position is judged by the ROUND TRIP: the day it names, written back in its own calendar,
    must be the position written. A day that does not exist moved silently to the next (persian:1405-01-01), and a year
    outside what a calendar can reckon raised in a reader; both are refused here, by name, and never a traceback. WHICH
    calendars are judged is the LAW's to say, not the tool's: the row's own `reckoning`, against the reckonings the date
    type's `exists` names. A calendar the tool happens to carry and the law says is observed is not judged by it."""
    if not isinstance(row, dict) or not row.get('calendar'):
        return None
    _exists = (VALUE_TYPES.get('date') or {}).get('exists')
    _judged = (_exists.get('reckoning') if isinstance(_exists, dict) else None) or []
    if not isinstance(_judged, list) or not isinstance(row.get('reckoning'), str) or row.get('reckoning') not in _judged:
        return None
    date = re.split(r'[T ]', str(val), maxsplit=1)[0]
    try:
        import dmcal
    except ImportError:
        return None
    if row['calendar'] not in dmcal.EVERY:
        return None                         # a calendar the tool does not write is one it cannot judge
    try:
        back = dmcal.from_day(dmcal.to_day(date), row['calendar'])
    except dmcal.NotByRule:
        return None
    except (ValueError, OverflowError) as ex:
        return f"is no day of {row.get('system')} ({ex})"
    # compared as numbers, so a year written `0999` and read back `999` is one year
    tokens = lambda s: [int(x) if x.isdigit() else x for x in re.findall(r'[0-9]+|[^0-9]', s)]
    if tokens(back) != tokens(date):
        return f"is no day of {row.get('system')}: the day it would name is {back}"
    return None


def check_day_exists(where, val, row):
    _why = day_unwritten(val, row)
    if _why:
        errors.append(f"{where} '{val}' {_why} — a date is a day its calendar has (VOCAB anchor_systems.{row.get('system')})")

ASPECTS = _Named({a['aspect']: a for a in (registry('aspects') or []) if isinstance(a, dict) and a.get('aspect')})
FIGURES = {f['figure']: f for f in (registry('figures') or []) if isinstance(f, dict) and f.get('figure')}

UNITS = {u['unit']: u for u in (registry('units') or []) if isinstance(u, dict) and u.get('unit')}
QUANTITIES = _Named({q['quantity']: q for q in (registry('quantities') or []) if isinstance(q, dict) and q.get('quantity')})
# A QUANTITY WHOSE UNITS ARE A REGISTRY'S ROWS (21.0): a currency is a unit of `money`, and the currencies are a list
# their publisher keeps, not rows the law restates. Each row becomes a unit with no factor — no factor joins two
# currencies; the quantity says so (`crosswalk: observed`) — and carries the decimal places its row publishes.
for _qn, _q in list(QUANTITIES.items()):
    _uf = _q.get('units_from') if isinstance(_q.get('units_from'), dict) else None
    if not _uf:
        continue
    for _r in (registry(_uf.get('registry')) or []):
        if isinstance(_r, dict) and _r.get(_uf.get('take')) and str(_r[_uf['take']]) not in UNITS:
            UNITS[str(_r[_uf['take']])] = {'unit': str(_r[_uf['take']]), 'quantity': _qn, 'from_registry': _uf['registry'],
                                          'digits': _r.get(_uf.get('digits')) if _uf.get('digits') else None}


def unit_powers(u):
    """What a unit measures, as powers of base dimensions: {length: 1, time: -1} for a speed. Read from the quantity the
    unit names, so nothing here knows a unit or a quantity by name."""
    return dict((QUANTITIES.get((u or {}).get('quantity')) or {}).get('of') or {})


def power_of(u, dimension):
    """k when the unit measures dimension**k and nothing else (a length, an area, a volume); else None."""
    p = unit_powers(u)
    return p[dimension] if list(p) == [dimension] and p[dimension] > 0 else None


def count_ok(c):
    """A COUNT AS THE LAW WRITES ONE (`value_types[count]`): a whole number, or a decimal string, in plain decimal digits
    and within the digits every reader can hold exactly. A whole number YAML read as an integer is held to the same form
    through its text, so a forty-one-digit integer is refused as surely as a forty-one-digit string. Never a float, never
    a boolean. Without the law's row nothing is a count: check_value_types has said so once."""
    t = VALUE_TYPES.get('count')
    if not t or isinstance(c, bool) or not isinstance(c, (int, str)):
        return False
    return bool(law_match(t['pattern'], c))


def _units_like(val, want):
    """For a unit the law does not know, the units it may have meant: the rows of a registry of units (the currencies
    are one) that hold it in any column — as their code, or in their name — the nearest names among the other units of
    the quantity, and the command that searches that registry's own file by name. Read from the law: no unit, quantity
    or registry is named here."""
    _v = str(val).strip().lower()
    _qs = [q for q in QUANTITIES if want in (None, 'any') or q == want]
    _rows, _files, _names = [], [], []
    for _q in _qs:
        _uf = (QUANTITIES.get(_q) or {}).get('units_from')
        if not isinstance(_uf, dict):
            _names += [n for n, r in UNITS.items() if r.get('quantity') == _q]
            continue
        _decl = next((r for r in (list(vocab_fm.get('registry_files') or []) + list(std_fm.get('registry_files') or []))
                      if isinstance(r, dict) and r.get('registry') == _uf.get('registry')), None)
        if _decl and _decl.get('file'):
            _files.append((_q, _uf.get('registry'), _uf.get('take'), _decl['file']))
        for _r in (registry(_uf.get('registry')) or []) if _v else []:
            _cols = [str(x) for x in _r.values() if isinstance(x, str) and x]
            _rank = (0 if any(x.lower() == _v for x in _cols) else 1 if any(w.lower().startswith(_v)
                     for x in _cols for w in x.split()) else 2 if any(_v in x.lower() for x in _cols) else None)
            if _rank is not None and _r.get(_uf.get('take')):
                _named = next((x for x in _cols if _v in x.lower() and x != str(_r[_uf['take']])), '')
                _rows.append((_rank, f"{_r[_uf['take']]}" + (f" ({_named})" if _named else '')))
    out = []
    _like = [x for _, x in sorted(_rows, key=lambda t: t[0])[:6]]
    if _like:
        out.append(f"the rows named like it: {', '.join(_like)}")
    _near = _nearest(val, _names, n=4, cutoff=0.6)
    if _near:
        out.append(f"the units nearest to it: {', '.join(_near)}")
    for _q, _reg, _take, _file in _files:
        out.append(f"a unit of {_q} is written by the {_take} of its row of `{_reg}` — find it by name with "
                   f"grep -i \"<its name>\" {_file}")
    return (' — ' + '; '.join(out) + _rule('units', *[f[1] for f in _files], 'units')) if out else ''


def check_quantity(where, node, want):
    if not isinstance(node, dict) or node.get('unit') is None or node.get('count') is None:
        errors.append(f"{where}: a quantity is written {{ count, unit }}")
        return
    u = UNITS.get(str(node['unit']))
    c = node['count']
    if not u:
        errors.append(f"{where}.unit '{node['unit']}' is not in the `units` registry" + _units_like(node['unit'], want))
    elif want not in (None, 'any') and u.get('quantity') != want:
        _of = sorted(n for n, r in UNITS.items() if r.get('quantity') == want)
        _reg = ((QUANTITIES.get(want) or {}).get('units_from') or {}).get('registry')
        errors.append(f"{where}.unit '{node['unit']}' measures {u.get('quantity')}, and this attribute is a {want} — "
                      + (f"a code of the `{_reg}` registry" if _reg else str(_of)))
    if not count_ok(c):
        errors.append(f"{where}.count {c!r} " + ((VALUE_TYPES.get('count') or {}).get('refusal') or
                      "must be a whole number, or a decimal written as a string (\"12.5\"): a float has no canonical form"))
    elif u and u.get('digits') not in (None, '') and isinstance(c, str) and '.' in c:
        _places = len(c.split('.', 1)[1])
        if str(u['digits']).isdigit() and _places > int(u['digits']):
            errors.append(f"{where}.count '{c}' has {_places} decimal places, and {node['unit']} is written with at most "
                          f"{u['digits']} ({u.get('from_registry')}) — a fraction of the smallest unit in use is not an amount "
                          f"anyone paid; if a share does not come out even, say who takes the remainder in a clause")
SYSTEMS = _Named({s['system']: s for s in (registry('anchor_systems') or []) if isinstance(s, dict) and s.get('system')})


def check_extent(where, node):
    """One EXTENT against the aspect it names (11.2). Returns nothing; appends what is wrong.

    Every rule here is read from the aspect and its figure rather than written down: whether a region is
    possible at all (`figures[].extent`), whether it may carry a length (`aspects[].metered`), which unit
    that length is in (the metered dimension), and which forms a boundary may take (`aspects[].domain`,
    then the anchor system's own pattern). So a new aspect gets extents with no change here, and an
    aspect that should not have them refuses them for its own stated reason.
    """
    if not isinstance(node, dict):
        errors.append(f"{where}: an extent is a mapping {{of, from?, to?, measure?}} (`extent_form`)")
        return
    an = node.get('of')
    asp = ASPECTS.get(an) if isinstance(an, str) else None      # a list or a map names no aspect, and is no dict key
    if not asp:
        errors.append(f"{where}: extent `of: {an!r}` names no aspect — {sorted(ASPECTS)}")
        return
    fig = FIGURES.get(asp.get('figure')) or {}
    if fig.get('extent') != 'possible':
        errors.append(f"{where}: aspect '{an}' is a {asp.get('figure')} and carries no region — "
                      f"{fig.get('extent_why') or 'its figure declares extent: ' + str(fig.get('extent'))}")
        return
    if not any(node.get(k) is not None for k in ('from', 'to', 'measure')):
        errors.append(f"{where}: an extent needs at least one of from / to / measure — "
                      f"a region with neither bound and no length is not a region (`extent_form.requires`)")
    _row = _system_of(where, node, asp, an)
    m = node.get('measure')
    if m is not None:
        metered = ((_row or {}).get('restrictions') or {}).get('metered') or asp.get('metered')
        if not metered or metered == 'none':
            errors.append(f"{where}: aspect '{an}' declares `metered: {metered}`, so a region on it has no "
                          f"length — drop `measure`, or bound it with from/to")
        elif not isinstance(m, dict) or m.get('count') is None or not m.get('unit'):
            errors.append(f"{where}.measure: must be {{count, unit}}")
        else:
            u = UNITS.get(str(m['unit']))
            if not u:
                errors.append(f"{where}.measure.unit '{m['unit']}' is not in the `units` registry "
                              f"{sorted(UNITS)}")
            elif power_of(u, metered) is None:
                errors.append(f"{where}.measure.unit '{m['unit']}' measures {u.get('quantity')}, but "
                              f"aspect '{an}' meters {metered}")
            else:
                _lines = ((_row or {}).get('restrictions') or {}).get('lines') or asp.get('lines')
                if isinstance(_lines, int) and power_of(u, metered) > _lines:
                    errors.append(f"{where}.measure.unit '{m['unit']}' spans {power_of(u, metered)} lines, and "
                                  f"{'system ' + repr(_row['system']) if _row else 'aspect ' + repr(an)} has {_lines} — "
                                  f"there is no such region there")
            if not isinstance(m.get('count'), int) or isinstance(m.get('count'), bool) or m['count'] <= 0:
                errors.append(f"{where}.measure.count must be a positive whole number of "
                              f"{m.get('unit')}s, not {m.get('count')!r}")
    # A BOUNDARY IS A POSITION, and which forms it may take is the aspect's domain, not this function's.
    dim = ((asp.get('domain') or {}).get('systems'))
    for side in ('from', 'to'):
        v = node.get(side)
        if v is None:
            continue
        ok = [s for s in SYSTEMS.values()
              if s.get('dimension') in (dim, 'any') and dmparse.in_form(s, v)]
        if not ok:
            errors.append(f"{where}.{side} '{v}' is not a position in any system of dimension "
                          f"'{dim}' — " + ', '.join(sorted(s['system'] for s in SYSTEMS.values()
                                                           if s.get('dimension') in (dim, 'any'))))
        else:
            check_day_exists(f"{where}.{side}", v, ok[0])


def _system_of(where, node, asp, an):
    """The system a region or a repetition names with `in:`, held to the aspect's own domain — or None when it names none."""
    sn = node.get('in')
    if sn is None:
        return None
    if not isinstance(sn, str):
        errors.append(f"{where}: `in:` names ONE positioning system, written as text — not {type(sn).__name__}")
        return False
    row = SYSTEMS.get(sn)
    dim = (asp.get('domain') or {}).get('systems')
    if not row:
        errors.append(f"{where}: `in: {sn!r}` names no positioning system")
    elif row.get('dimension') not in (dim, 'any'):
        errors.append(f"{where}: system '{sn}' positions in '{row.get('dimension')}', and aspect '{an}' holds '{dim}'")
    else:
        return row
    return False


def check_recurrence(where, node):
    """One RECURRENCE against the aspect — and the SYSTEM — it names. Appends what is wrong.

    A repetition is a sequence whose neighbours are given by a RULE instead of by listing: each occurrence is the one
    before it, shifted. There are three kinds of shift, and which a repetition may use is read from the law — from the
    aspect's figure, and from the shape the named system declares — never written down here:
      by NEIGHBOURS  every Nth position. Needs only that positions HAVE neighbours.
      by MEASURE     every N units. Needs the aspect, or the system, to be metered in that unit's dimension.
      by CELL        the same place in each cell of a LEVEL. Needs the system to have that level — and therefore needs a
                     system, because a level belongs to its system: "each month" is nobody's month until it says whose.
    """
    if not isinstance(node, dict):
        errors.append(f"{where}: a recurrence is a mapping {{of, in?, every | each, at?, from?, to?}} (`recurrence_form`)")
        return
    an = node.get('of')
    asp = ASPECTS.get(an) if isinstance(an, str) else None      # a list or a map names no aspect, and is no dict key
    if not asp:
        errors.append(f"{where}: recurrence `of: {an!r}` names no aspect — {sorted(ASPECTS)}")
        return
    if asp.get('figure') != 'sequence':
        errors.append(f"{where}: aspect '{an}' is a {asp.get('figure')}: its positions have no neighbours, so nothing "
                      f"on it repeats")
        return
    row = _system_of(where, node, asp, an)
    if row is False:
        return
    # WHERE IT STARTS AND ENDS ARE POSITIONS (`recurrence_form.from` / `.to`: "in the system's form"), and the readers
    # walk to them — so each is held as every other position is: to the system the repetition names, else to some
    # system of the aspect's dimension, and to a day its calendar has. `to: '2026-02-30'` ended a monthly clause on a
    # day no calendar holds, and `to: 'garbage'` passed as well; both were read by the walkers.
    dim = (asp.get('domain') or {}).get('systems')
    for side in ('from', 'to'):
        v = node.get(side)
        if v is None:
            continue
        if row:
            if dmparse.in_form(row, v) is False:
                errors.append(f"{where}.{side} '{v}' is not a position in the form system '{row['system']}' writes "
                              f"({dmparse.form_said(row) if row.get('checked_by') else row['pattern']})"
                              f"{' — ' + row['form_note'] if row.get('form_note') else ''} — the repetition is counted "
                              f"`in: {row['system']}`, and where it starts and ends is written in that system's form")
            else:
                check_day_exists(f"{where}.{side}", v, row)
            continue
        ok = [s for s in SYSTEMS.values() if s.get('dimension') in (dim, 'any') and dmparse.in_form(s, v)]
        if not ok:
            errors.append(f"{where}.{side} '{v}' is not a position in any system of dimension '{dim}' — "
                          + ', '.join(sorted(s['system'] for s in SYSTEMS.values() if s.get('dimension') in (dim, 'any'))))
        else:
            check_day_exists(f"{where}.{side}", v, ok[0])
    every, each = node.get('every'), node.get('each')
    _t = node.get('times')
    if _t is not None and (isinstance(_t, bool) or not isinstance(_t, int) or _t < 1):
        errors.append(f"{where}.times {_t!r} must be a positive whole number: how many occurrences in all, the first included")
    if (every is None) == (each is None):
        errors.append(f"{where}: a recurrence strides EITHER `every:` N neighbours or units OR `each:` cell of a level — "
                      f"exactly one")
        return
    if each is not None:
        if not row:
            errors.append(f"{where}: `each: {each}` names a LEVEL, and a level belongs to its system — say whose with "
                          f"`in: <system>`. The 15th of a Persian month and of a Gregorian one are different repetitions")
        else:
            lv = row.get('levels')
            names = [l.get('level') for l in lv] if isinstance(lv, list) else []
            if each not in names:
                errors.append(f"{where}: system '{row['system']}' has no level '{each}' — {names or 'it declares no named levels'}")
        return
    if not isinstance(every, dict) or not isinstance(every.get('count'), int) or isinstance(every.get('count'), bool) or every['count'] <= 0:
        errors.append(f"{where}.every: must be {{count}} (every Nth neighbour) or {{count, unit}} (every N units), count a positive whole number")
        return
    if every.get('unit') is None:
        nb = (row or {}).get('neighbours')
        if row and nb in (None, 'none'):
            errors.append(f"{where}: system '{row['system']}' declares `neighbours: {nb}` — its positions have no next one, "
                          f"so there is no Nth")
        return
    u = UNITS.get(str(every['unit']))
    metered = ((row or {}).get('restrictions') or {}).get('metered') or asp.get('metered')
    if not u:
        errors.append(f"{where}.every.unit '{every['unit']}' is not in the `units` registry {sorted(UNITS)}")
    elif not metered or metered == 'none':
        errors.append(f"{where}: neither aspect '{an}' nor the system it names is metered, so a stride has no length — "
                      f"stride by neighbours (`every: {{count}}`), or name a metered system with `in:`")
    elif power_of(u, metered) != 1:
        errors.append(f"{where}.every.unit '{every['unit']}' measures {u.get('quantity')}, and a stride here is measured in {metered}")


def walk_keys():
    """{schema key: aspect} for every SEQUENCE aspect that places terms on itself through a schema key (9.2).
    `dag: true` is read through this: the key is data in the vocabulary, and whether a cycle is refused is
    the aspect's `acyclic` restriction, not a rule written here."""
    return {a['term_key']: a for a in ASPECTS.values() if a.get('term_key')}

def on_walk(sch, acyclic_only=False):
    """True when a term's schema places its edges on a walk aspect (and, if asked, one declared acyclic)."""
    return any(sch.get(k) is True and (not acyclic_only or a.get('acyclic') is True) for k, a in walk_keys().items())

def check_sequence_figure(_an, _a, _fig):
    """A SEQUENCE is declared only by its restrictions (9.2): every one stated, each a value the figure
    offers. It has no positions and no poles, because it is not a closed set of modalities."""
    for _k in ('positions', 'poles'):
        if _a.get(_k):
            errors.append(f"aspect '{_an}': a sequence declares no `{_k}` — its positions are points in a domain, "
                          f"not a closed set of modalities")
    _lines = _a.get('lines')
    if not (_lines == 'open' or (isinstance(_lines, int) and not isinstance(_lines, bool) and _lines > 0)):
        errors.append(f"aspect '{_an}': lines '{_lines}' must be a positive integer or `open`")
    _dims = {d.get('dimension') for d in (registry('dimensions') or []) if isinstance(d, dict)}
    if _a.get('metered') != 'none' and _a.get('metered') not in _dims:
        errors.append(f"aspect '{_an}': metered '{_a.get('metered')}' is neither `none` nor a dimension in `units` {sorted(d for d in _dims if d)}")
    if _a.get('order') not in (_fig.get('order_values') or []):
        errors.append(f"aspect '{_an}': order '{_a.get('order')}' is not one of {_fig.get('order_values')}")
    if not isinstance(_a.get('acyclic'), bool):
        errors.append(f"aspect '{_an}': acyclic must be true or false, stated")
    if _a.get('ends') not in (_fig.get('ends_values') or []):
        errors.append(f"aspect '{_an}': ends '{_a.get('ends')}' is not one of {_fig.get('ends_values')}")
    _sys = (_a.get('domain') or {}).get('systems') if isinstance(_a.get('domain'), dict) else None
    _sdims = {s.get('dimension') for s in (registry('anchor_systems') or []) if isinstance(s, dict)}
    if _sys != 'none' and _sys not in _sdims:
        errors.append(f"aspect '{_an}': domain.systems '{_sys}' is neither `none` nor a dimension of `anchor_systems` {sorted(d for d in _sdims if d)}")

# --- a system knows its own shape (std-vocab 15.0) -----------------------------------------------------------------
# The gate checks the SHAPE a system declares, never its use: that what a row names exists, that nesting never loops,
# that a metric level names a real unit, and that a row's own restrictions are ones its figure offers and only NARROW
# its aspect's. Which registries hold systems is declared (`system_registries`), so none is named here.
def _systems():
    out = {}
    for _sr in (std_fm.get('system_registries') or []):
        for _row in (registry(_sr.get('registry')) or []):
            if isinstance(_row, dict) and _row.get(_sr.get('key')):
                out[_row[_sr['key']]] = (_sr['registry'], _row)
    return out


def check_system_structure():
    _sys = _systems()
    if not _sys:
        return
    _units = {u.get('unit'): u for u in (registry('units') or []) if isinstance(u, dict)}
    _seq = next((f for f in (registry('figures') or []) if isinstance(f, dict) and f.get('figure') == 'sequence'), {})
    _by_dim = {}
    for _a in (registry('aspects') or []):
        if isinstance(_a, dict) and isinstance(_a.get('domain'), dict) and _a['domain'].get('systems') not in (None, 'none'):
            _by_dim[_a['domain']['systems']] = _a
    _graph = {}
    for _name, (_reg, _row) in sorted(_sys.items()):
        _w = f"VOCAB {_reg}.{_name}"
        for _key in ('within', 'resolves_through'):
            _v = _row.get(_key)
            for _t in (_v if isinstance(_v, list) else [_v] if _v else []):
                if _t not in _sys:
                    errors.append(f"{_w}: `{_key}` names '{_t}', which is no declared system {sorted(_sys)[:6]}…")
                _graph.setdefault(_name, set()).add(_t)
        _lv = _row.get('levels')
        if isinstance(_lv, list):
            _names = [l.get('level') if isinstance(l, dict) else None for l in _lv]
            if None in _names or len(set(_names)) != len(_names):
                errors.append(f"{_w}: `levels` must be a list of {{level: <name>}} with no name twice — got {_lv}")
            for l in _lv:
                if isinstance(l, dict) and l.get('unit') is not None and l['unit'] not in _units:
                    errors.append(f"{_w}: level '{l.get('level')}' says it is metric in unit '{l['unit']}', which is no "
                                  f"row of `units` {sorted(_units)} — a level with no fixed length (a month) names no unit")
        elif isinstance(_lv, dict):
            if not (isinstance(_lv.get('from'), int) and isinstance(_lv.get('to'), int) and _lv['from'] <= _lv['to'] and _lv.get('by')):
                errors.append(f"{_w}: counted `levels` need {{by, from, to}} with from <= to — got {_lv}")
        elif _lv not in (None, 'open'):
            errors.append(f"{_w}: `levels` is a list of named levels, a counted range {{by, from, to}}, or `open` — got {_lv!r}")
        for _word, _offered in (std_fm.get('system_shape') or {}).items():
            if _row.get(_word) is not None and _row[_word] not in (_offered or []):
                errors.append(f"{_w}: `{_word}` is one of {_offered} — got {_row[_word]!r}")
        for _t in (_row.get('same_ground_as') or []):
            if _t not in _sys:
                errors.append(f"{_w}: `same_ground_as` names '{_t}', which is no declared system")
        if _row.get('same_ground_as') and not _row.get('crosswalk'):
            errors.append(f"{_w}: it shares its ground with {_row['same_ground_as']} and does not say how a position in "
                          f"one is found in the other — `crosswalk:` {(std_fm.get('system_shape') or {}).get('crosswalk')}")
        _ex = _row.get('example')
        if _row.get('checked_by') and _row['checked_by'] not in dmparse.FORM_CHECKS:
            errors.append(f"{_w}: `checked_by: {_row['checked_by']}` names no check the tools carry — {sorted(dmparse.FORM_CHECKS)}")
        if _row.get('checked_by') and _row.get('pattern') not in (None, 'none'):
            errors.append(f"{_w}: it states its form twice — `checked_by` AND `pattern`. One of them is a copy, and copies drift")
        if _ex and dmparse.in_form(_row, _ex) is False:
            errors.append(f"{_w}: its own `example` '{_ex}' is not in the form its `pattern` declares — a reader would be "
                          f"shown a spelling the gate refuses")
        _r, _asp = _row.get('restrictions') or {}, _by_dim.get(_row.get('dimension'))
        for _k, _val in _r.items():
            if _k not in ('lines', 'metered', 'order', 'ends'):
                errors.append(f"{_w}: restriction `{_k}` is not one the sequence figure offers (lines, metered, order, ends)")
            elif _k == 'order' and _val not in (_seq.get('order_values') or []):
                errors.append(f"{_w}: restrictions.order '{_val}' not in {_seq.get('order_values')}")
            elif _k == 'ends' and _val not in (_seq.get('ends_values') or []):
                errors.append(f"{_w}: restrictions.ends '{_val}' not in {_seq.get('ends_values')}")
            elif _k == 'metered' and _val != 'none' and _val not in {d.get('dimension') for d in (registry('dimensions') or []) if isinstance(d, dict)}:
                errors.append(f"{_w}: restrictions.metered '{_val}' is no dimension any unit measures")
            elif _k == 'lines' and not (_val == 'open' or (isinstance(_val, int) and _val > 0)):
                errors.append(f"{_w}: restrictions.lines is a positive integer or `open` — got {_val!r}")
        if _asp:
            # NARROW, NEVER WIDEN. A system may be more definite than its aspect; it may not contradict it.
            _widens = []
            if _asp.get('order') == 'total' and _r.get('order') not in (None, 'total'):
                _widens.append(f"order {_r['order']} under an aspect that is total")
            if _asp.get('order') == 'partial' and _r.get('order') == 'none':
                _widens.append("order none under an aspect that is at least partial")
            if _asp.get('ends') == 'bounded' and _r.get('ends') not in (None, 'bounded'):
                _widens.append(f"ends {_r['ends']} under an aspect that is bounded")
            if isinstance(_asp.get('lines'), int) and _r.get('lines') not in (None, _asp['lines']):
                _widens.append(f"lines {_r['lines']} under an aspect with exactly {_asp['lines']}")
            if _asp.get('metered') not in (None, 'none') and _r.get('metered') not in (None, _asp['metered']):
                _widens.append(f"metered {_r['metered']} under an aspect metered in {_asp['metered']}")
            for _m in _widens:
                errors.append(f"{_w}: its restrictions WIDEN aspect '{_asp.get('aspect')}' — {_m}. A system narrows its aspect")
    for _cyc in _cycles({k: sorted(v) for k, v in _graph.items()}):
        errors.append(f"VOCAB systems: nesting loops — {' -> '.join(_cyc)}. `within` and `resolves_through` are walked, so they end")


# --- a row of one registry names a row of another (std-vocab 15.0) ---------------------------------------------------
def check_registry_links():
    for _l in (std_fm.get('registry_links') or []) + (vocab_fm.get('registry_links') or []):
        _to = {str(r.get(_l.get('take'))) for r in (registry(_l.get('to')) or []) if isinstance(r, dict)}
        _edges = {}
        for _row in (registry(_l.get('from')) or []):
            if not isinstance(_row, dict) or _row.get(_l.get('field')) is None:
                continue
            _vals = _row[_l['field']] if isinstance(_row[_l['field']], list) else [_row[_l['field']]]
            for _v in _vals:
                if str(_v) not in _to:
                    errors.append(f"VOCAB {_l['from']}: a row's `{_l['field']}` names '{_v}', which is no "
                                  f"{_l['take']} of `{_l['to']}` — a link between registries is resolved like any other")
            _edges.setdefault(str(_row.get(_l.get('take'))), set()).update(str(v) for v in _vals)
        if _l.get('acyclic'):
            # A WALK THAT NEVER RETURNS (21.0): facets depend on facets, and a facet that depended on itself through
            # others would make "every other facet depends on legal" unanswerable.
            _seen, _done = set(), set()
            def _visit(n, path):
                if n in _done:
                    return
                if n in _seen:
                    errors.append(f"VOCAB {_l['from']}: `{_l['field']}` returns to '{n}' ({' -> '.join(path + [n])}) — "
                                  f"this link declares that its walk never does")
                    return
                _seen.add(n)
                for m in sorted(_edges.get(n, ())):
                    _visit(m, path + [n])
                _done.add(n)
            for n in sorted(_edges):
                _visit(n, [])
        if _l.get('rooted'):
            # ONE ROOT, AND EVERY ROW REACHES IT (21.0). "Every other facet depends on legal" was a sentence of the law
            # that nothing checked: a facet a garden added with `depends_on: []` stood beside `legal` as a second root.
            for _row in (registry(_l.get('from')) or []):          # a row that names no link at all is a root too
                if isinstance(_row, dict) and _row.get(_l.get('take')) is not None:
                    _edges.setdefault(str(_row[_l['take']]), set())
            _roots = sorted(n for n, e in _edges.items() if not e)
            if len(_roots) != 1:
                errors.append(f"VOCAB {_l['from']}: {len(_roots)} rows name no `{_l['field']}` ({', '.join(_roots) or 'none'}) — "
                              f"this link declares ONE root, which every other row reaches")
            else:
                def _reaches(n, seen=()):
                    return n == _roots[0] or any(m not in seen and _reaches(m, seen + (n,)) for m in _edges.get(n, ()))
                for n in sorted(_edges):
                    if not _reaches(n):
                        errors.append(f"VOCAB {_l['from']}: '{n}' does not reach '{_roots[0]}' through `{_l['field']}` — this "
                                      f"link declares that every row does")


def check_retired_terms():
    """A garden's local term, or an overlay, named for a term the standard RETIRED (21.0, `retired`, at: term or bean):
    it would come back as a local term meaning nothing, or overlay a term that is no longer there. Refused, with where
    the retired term went — the facet lattice is a registry now, and a garden adds a facet as a row."""
    for _t in (vocab_fm.get('local_terms') or []):
        if isinstance(_t, dict) and _t.get('term') and _t['term'] not in TIER0_TERMS \
                and (RETIRED.get(('term', str(_t['term']))) or RETIRED.get(('bean', str(_t['term'])))):
            errors.append(f"VOCAB local_terms '{_t['term']}': the standard retired this term" + (retired_hint('term', _t['term']) or retired_hint('bean', _t['term'])))


def check_retired_vocab():
    """A garden's VOCAB.md that still says a name the law RETIRED (22.0, `retired`: at vocab, law, minted, nature): a
    block the law no longer reads (`local_kinds`), a registry it no longer has (`kinds`, restated or added to), the
    minted form's `form_kind`, a genos row refining a nature the law renamed. Each is refused with where it went, never
    left unread: a block nobody reads would leave every bean of the garden's own gene refused, with nothing saying why."""
    for _k in sorted(map(str, vocab_fm)):
        if RETIRED.get(('vocab', _k)) or RETIRED.get(('law', _k)):
            errors.append(f"VOCAB.md: `{_k}` is a name the law retired" + (retired_hint('vocab', _k) or retired_hint('law', _k))
                          + ". " + translate_hint())
    for _k in sorted(map(str, vocab_fm.get('registry_additions') or {})):
        if RETIRED.get(('law', _k)):
            errors.append(f"VOCAB.md: `registry_additions.{_k}` adds to a registry the law retired" + retired_hint('law', _k))
    _mint = (vocab_fm.get('identity_policy') or {}).get('minted')
    for _k in sorted(map(str, _mint if isinstance(_mint, dict) else {})):
        if RETIRED.get(('minted', _k)):
            errors.append(f"VOCAB.md: identity_policy.minted.{_k} is a name the law retired" + retired_hint('minted', _k))
    _natures = {r.get('nature') for r in (registry('natures') or []) if isinstance(r, dict)}
    for _g in GENE.values():
        if _g.get('of_nature') is not None and _g['of_nature'] not in _natures:
            errors.append(f"VOCAB genos '{_g.get('genos')}': of_nature '{_g['of_nature']}' is no nature the law declares "
                          f"({', '.join(sorted(map(str, _natures)))})" + retired_hint('nature', _g['of_nature']))


def check_retired_owners():
    """A garden that overlaid one of the five retired enum-owner terms did so to restate a row it had added to the
    registry. The row is enough now; the overlay would otherwise come back as a term that means nothing."""
    import dmreform
    for _t in (vocab_fm.get('local_terms') or []):
        if isinstance(_t, dict) and _t.get('term') in dmreform.RETIRED_OWNERS:
            errors.append(f"VOCAB local_terms '{_t['term']}': this term was only a copy of the `{dmreform.RETIRED_OWNERS[_t['term']]}` "
                          f"registry's column and is retired (18.0) — delete the overlay; a row under "
                          f"`registry_additions.{dmreform.RETIRED_OWNERS[_t['term']]}` is stated once and is enough")


def check_units():
    """A unit's factor is a PAIR OF WHOLE NUMBERS, and a quantity's powers are whole numbers of declared dimensions. A
    factor written 0.277778 would make every conversion through it wrong by an amount nobody chose; [5, 18] is what it is."""
    _dims = {d.get('dimension') for d in (registry('dimensions') or []) if isinstance(d, dict)}
    for _n, _q in QUANTITIES.items():
        for _d, _k in (_q.get('of') or {}).items():
            if _d not in _dims or isinstance(_k, bool) or not isinstance(_k, int) or _k == 0:
                errors.append(f"VOCAB quantities '{_n}': `of.{_d}: {_k!r}` must be a non-zero whole power of a declared dimension {sorted(_dims)}")
    for _n, _q in QUANTITIES.items():
        if _q.get('units_from') is not None:
            _uf = _q['units_from']
            if not isinstance(_uf, dict) or not _uf.get('registry') or not _uf.get('take'):
                errors.append(f"VOCAB quantities '{_n}': `units_from` is {{registry, take, digits?}}")
            elif not registry(_uf['registry']):
                errors.append(f"VOCAB quantities '{_n}': `units_from.registry: {_uf['registry']}` names no registry the law holds")
            _sh = std_fm.get('system_shape') or {}
            if _q.get('crosswalk') not in (_sh.get('crosswalk') or []):
                errors.append(f"VOCAB quantities '{_n}': a quantity whose units come from a registry says how two of them "
                              f"meet — `crosswalk:` one of {_sh.get('crosswalk')}")
    for _n, _u in UNITS.items():
        if _u.get('from_registry'):
            continue                        # a registry's row: no factor, by the quantity's own `crosswalk`
        _f = _u.get('factor')
        if not (isinstance(_f, list) and len(_f) == 2 and all(isinstance(x, int) and not isinstance(x, bool) and x > 0 for x in _f)):
            errors.append(f"VOCAB units '{_n}': `factor: {_f!r}` must be [numerator, denominator], two positive whole numbers — "
                          f"an exact ratio to the quantity's coherent unit, never a rounded decimal")
        elif math.gcd(*_f) != 1:
            errors.append(f"VOCAB units '{_n}': `factor: {_f}` is not in lowest terms — one ratio has one spelling")


_TO_THE_MINUTE = r'^[^ T]+[T ][0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]{1,3})?)?([+-][0-9]{2}:[0-9]{2}|Z)$'


def journal_heading_ok(heading):
    """`## <when> · <who> · <what>`, where <when> is a position in a CALENDAR the law declares — in that system's own
    one form, held to the minute, with its offset. The journal owns no copy of any calendar's form: `journal.system`
    names the one this garden writes in, and when it names none, any declared calendar will do."""
    parts = str(heading)[3:].split(' · ')
    if not str(heading).startswith('## ') or len(parts) < 3 or not all(x.strip() for x in parts[:3]):
        return False
    when, want = parts[0], JOURNAL.get('system')
    rows = [r for r in SYSTEMS.values() if r.get('dimension') == 'time' and r.get('calendar')
            and r.get('pattern') not in (None, 'none') and want in (None, 'any', r.get('system'))]
    return bool(law_match(_TO_THE_MINUTE, when)) and any(law_match(r['pattern'], when) for r in rows)


def check_aspect_sanity():
    _keys = {}
    for _an, _a in ASPECTS.items():
        _fig = FIGURES.get(_a.get('figure'))
        if not _fig:
            errors.append(f"aspect '{_an}': figure '{_a.get('figure')}' is not declared in `figures` {sorted(FIGURES)}")
            continue
        for _req in _fig.get('requires') or []:
            if _a.get(_req) is None:
                errors.append(f"aspect '{_an}': a {_a['figure']} must state `{_req}` — an unstated restriction "
                              f"is how a model silently becomes narrower than the world")
        if _a.get('term_key'):
            if _a['term_key'] in _keys:
                errors.append(f"aspect '{_an}': term_key '{_a['term_key']}' is already claimed by aspect '{_keys[_a['term_key']]}'")
            _keys[_a['term_key']] = _an
        if _a['figure'] == 'sequence':
            check_sequence_figure(_an, _a, _fig)
            continue
        if _a['figure'] != 'opposition':
            errors.append(f"aspect '{_an}': the gate has no check for figure '{_a['figure']}' — a new figure is "
                          f"declared together with its checker, or its aspects would pass unexamined")
            continue
        _pos = {p['position']: p for p in (_a.get('positions') or []) if isinstance(p, dict) and p.get('position')}
        if not _pos:
            errors.append(f"aspect '{_an}': declares no positions — an aspect with no positions classifies nothing")
        for _pn, _p in _pos.items():
            _c = _p.get('complement')
            if not _c:
                errors.append(f"aspect '{_an}': position '{_pn}' names no complement — a position that cannot "
                              f"say what it is NOT leaves the figure open")
            elif _c not in _pos:
                errors.append(f"aspect '{_an}': position '{_pn}' complements '{_c}', which is not a position of "
                              f"this aspect (the figure does not close)")
            elif _pos[_c].get('complement') != _pn:
                errors.append(f"aspect '{_an}': '{_pn}' complements '{_c}' but '{_c}' complements "
                              f"'{_pos[_c].get('complement')}' — complements must be mutual")
        # ORIENTATION, dimension-agnostically. `poles` is ONE axis (a contradictory pair) or a LIST of axes.
        # The gate does not care HOW MANY: a figure may be 1-dimensional (a simple binary), 2 (a square), 3
        # (a cube) or more. What it requires is that EVERY declared axis is a genuine contradictory pair, so
        # that a position is addressable along it. The dimensionality is DERIVED from what is declared, never
        # assumed — assuming a count is what makes a square silently mis-model a cube.
        _raw = _a.get('poles') or []
        _axes = _raw if (_raw and isinstance(_raw[0], list)) else ([_raw] if _raw else [])
        if not _axes:
            errors.append(f"aspect '{_an}': declares no axis — without one, a position cannot be addressed "
                          f"by direction and the figure has no orientation")
        for _ax in _axes:
            if len(_ax) != 2:
                errors.append(f"aspect '{_an}': axis {_ax} must be a PAIR — an axis runs between two opposites, "
                              f"however many axes the figure has")
                continue
            for _p in _ax:
                if _p not in _pos:
                    errors.append(f"aspect '{_an}': pole '{_p}' is not one of its positions")
            if all(p in _pos for p in _ax) and _pos[_ax[0]].get('complement') != _ax[1]:
                errors.append(f"aspect '{_an}': axis {_ax} is not a contradictory pair — an orientation must "
                              f"run between opposites, or a position on the figure is ambiguous")



# --- extends pin (GARDEN.md / VOCAB.md) ---------------------------------------------------------
def check_extends_pin():
    for f in ('GARDEN.md', 'VOCAB.md'):
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        # a front matter that parses to a list or a word is no manifest at all: check_gardens refuses GARDEN.md by name
        # and the vocabulary's load refuses VOCAB.md, so here it simply names no pin — never a traceback that hides both
        _m = load(p)[0]
        if not isinstance(_m, dict) or '__err__' in _m:
            continue
        ext = _m.get('extends')
        if ext:
            m = re.match(r'std-vocab@(.+)', str(ext))
            if not m:
                errors.append(f"{f}: extends must be 'std-vocab@<version>'")
            elif std_ver and m.group(1) != std_ver:
                errors.append(f"{f}: pins std-vocab@{m.group(1)} but installed is @{std_ver} (bump is a logged rule-change)")
        elif f == 'VOCAB.md':
            warns.append("VOCAB.md: missing `extends: std-vocab@<ver>` pin")



# ============================== CORE — bean grammar ==============================
_GARDEN_ID = re.compile(r'^[0-9a-f]{12}$')
KNOWN_GARDENS = set()          # garden ids this garden knows: its own, and every `garden` bean's anchor
GARDEN_REFS = []               # (where, garden id) named by a provenance record — judged once the gardens are known


def check_provenance_record(where, rec):
    """THE RECORD EVERY FACT CARRIES, DECLARED (21.0, `provenance_record`). The merge engine has read `from` since
    12.0 and the law declared nothing about it; now the law states the record and the gate holds every record to it —
    on a bean, an anchor and an entry alike. `garden` names the garden a record was made in, where it is not this
    one, and must be a garden this garden knows: a fact taken in from a garden nobody recorded has no one to ask."""
    _attrs, _fattrs = PROV.get('attrs'), PROV.get('from_attrs')
    if not _attrs or not isinstance(rec, dict):
        return
    for _k in sorted(set(rec) - set(_attrs)):
        errors.append(f"{where} carries `{_k}`, which a provenance record may not (VOCAB provenance_record.attrs: "
                      f"{', '.join(_attrs)})")
    _from = rec.get('from')
    if _from is not None:
        _recs = list(_from.values()) if isinstance(_from, dict) else _from if isinstance(_from, list) else None
        if _recs is None:
            errors.append(f"{where}.from must be a map of name to record, or a list of records")
        else:
            for _r in _recs:
                if not isinstance(_r, dict) or (_fattrs and set(_r) - set(_fattrs)) or not _r.get('src'):
                    errors.append(f"{where}.from holds {_r!r} — each record is {{{', '.join(_fattrs or [])}}} with a `src`")
    _g = rec.get('garden')
    if _g is not None:
        if not _GARDEN_ID.match(str(_g)):
            errors.append(f"{where}.garden '{_g}' is not a garden id (twelve lowercase hexadecimal digits)")
        else:
            GARDEN_REFS.append((where, str(_g)))
def _odd_keys(x, path=''):
    """Keys YAML did not read as text: `on`, `off`, `yes`, `no` become booleans under YAML 1.1, and a bare number a
    number. Such a key cannot be compared, sorted or merged beside the others — the gate once crashed on one."""
    out = []
    if isinstance(x, dict):
        for k, v in x.items():
            if not isinstance(k, str):
                out.append(f"{path}{k!r}")
            out += _odd_keys(v, f"{path}{k}.")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            out += _odd_keys(v, f"{path}{i}.")
    return out


def _has_float(x):
    if isinstance(x, float): return True
    if isinstance(x, dict): return any(_has_float(v) for v in x.values())
    if isinstance(x, list): return any(_has_float(v) for v in x)
    return False


def build_docs():
    global docs, bean_ids, map_ids
    docs, bean_ids, map_ids = {}, set(), set()
    for f in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) + \
             sorted(glob.glob(os.path.join(ROOT, 'mappings', '*.md'))):
        base = os.path.basename(f)[:-3]
        is_bean = os.sep + 'beans' + os.sep in f
        idkey = 'bean' if is_bean else 'mapping'
        fm, body = load(f)
        if isinstance(fm, dict) and fm.get('__not_utf8__'):
            errors.append(f"{os.path.relpath(f, ROOT).replace(os.sep, '/')}: {fm['__err__']}")
            continue
        if not isinstance(fm, dict) or '__err__' in fm:
            _why = fm['__err__'] if isinstance(fm, dict) else ('no --- fences' if fm is None else 'not a mapping')
            errors.append(f"{base}: front-matter invalid ({_why})")
            continue
        if str(fm.get(idkey)) != base:
            errors.append(f"{base}: {idkey} '{fm.get(idkey)}' must equal filename (quote if numeric/reserved)")
        if KEBAB and not KEBAB.match(base):
            errors.append(f"{base}: id must be kebab-case")
        # a BEAN records a being, whose type is its `genos` (22.0); a MAPPING records no being and keeps its `kind`
        req = ['bean', 'genos', 'title', 'status', 'summary'] if is_bean else ['mapping', 'kind', 'summary']
        for k in req:
            if not fm.get(k):
                (warns if k == 'summary' else errors).append(f"{base}: missing '{k}'")
        if is_bean and not body.strip():
            warns.append(f"{base}: no human body (Rule 6 paper-durable)")
        prov = fm.get('provenance')
        if is_bean and not isinstance(prov, dict):
            warns.append(f"{base}: missing provenance {{src,by,as_of}}")
        elif isinstance(prov, dict) and not prov.get('src'):
            errors.append(f"{base}: provenance.src missing")
        elif isinstance(prov, dict):
            check_provenance_record(f"{base}: provenance", prov)
        for _ok in _odd_keys(fm):
            errors.append(f"{base}: key {_ok} is not text — YAML reads `on`, `off`, `yes`, `no` as true/false and a bare "
                          f"number as a number; quote the key or name it otherwise")
        for sect in _AUTHORITATIVE:
            if _has_float(fm.get(sect)):
                warns.append(f"{base}: {sect} has a float — breaks canonical determinism; use an integer or {{value,unit}}")
        (bean_ids if is_bean else map_ids).add(base)
        docs[(is_bean, base)] = (fm, body)

# ---- every top-level key is declared, and no key is written twice (2026-09-17, human-ratified) ----------
# A key no vocabulary declares IS a vocabulary proposal — it says a new kind of fact exists — and it passed
# the gate unnoticed: `runs_on` sat on a session bean for six weeks beside the `refs.host` that already said
# the same thing. What counts as declared is read from the vocabulary, not listed here: a term's own name,
# and the top-level head of each literal `context_keys` entry (`id` declares `bean` and `mapping`;
# `identity.status` declares `identity`). A glob or a file path in context_keys locates values, not keys.
def declared_top_level_keys():
    out = set(TERMS)
    for _t in TERMS.values():
        for _ck in (_t.get('context_keys') or []):
            if isinstance(_ck, str) and '*' not in _ck and '/' not in _ck:
                out.add(_ck.split('.')[0].split('[')[0])
    return out

def check_undeclared_keys():
    if not std_fm:
        return      # no law loaded: the refusal is already stated, and judging every key against nothing buries it
    _declared = declared_top_level_keys()
    for (_is_bean, _base), (_fm, _body) in sorted(docs.items()):
        for _k in _fm:
            _h = retired_hint('bean', _k)
            if _is_bean and _h and _k in _declared:
                # A NAME RETIRED ON A BEAN IS REFUSED ON A BEAN, whatever else still declares it: `kind` left the bean
                # for `genos` (22.0) and stays a mapping's. Never read in its new name's place.
                errors.append(f"{_base}: top-level key '{_k}' is one the law retired on a bean{_h}. {translate_hint()}")
            elif _k not in _declared:
                errors.append(f"{_base}: top-level key '{_k}' is declared by no vocabulary term" + (_h or
                              _undeclared_fix(_k, _fm[_k], _declared)))


def _undeclared_fix(key, value, declared):
    """What to write instead of a key no term declares: the fact kept under `details:` (ground rule 2), in the line that
    keeps it — or the declared key it misspells. A new KIND of fact is a change to the law, and not an agent's."""
    _v = _flow(value)
    _near = _nearest(key, declared, n=2, cutoff=0.75)
    return (f" — a fact no term names is kept under `details:` (ground rule 2): details: "
            f"{{ {key}: {_v if len(_v) <= 80 else '<its value>'} }}"
            + (f"; or it is {' or '.join(f'`{n}`' for n in _near)}, misspelt" if _near else '')
            + ". A new KIND of fact is a vocabulary proposal, which the gardener ratifies: park it in log/pending.md")

# YAML keeps the LAST of two equal keys and drops the first silently, so the loss happens before any check on
# the parsed document can see it. Read from the node graph instead — beans, mappings, and the law itself,
# where the first run of this check found two.
def check_duplicate_keys():
    _paths = (sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) + sorted(glob.glob(os.path.join(ROOT, 'mappings', '*.md')))
              + [STD, os.path.join(ROOT, 'VOCAB.md'), os.path.join(ROOT, 'GARDEN.md')])
    for _f in _paths:
        if not os.path.exists(_f):
            continue
        try:
            _head = dmparse.read(_f)[0]
        except dmparse.NotUTF8:
            continue                          # refused by name where the document is loaded
        if not _head:
            continue
        try:
            _dups = dmparse.duplicate_keys(_head)
        except Exception:
            continue                          # unparseable: build_docs reports it, with the parser's reason
        for _path, _first, _again in _dups:
            errors.append(f"{os.path.relpath(_f, ROOT)}: key '{_path}' is written twice (lines {_first} and "
                          f"{_again}) — YAML keeps the second and silently discards the first")


def check_text():
    """TEXT HOLDS NO CONTROL CHARACTER (`value_types[text]`). A key or a value is read by a person, and printed by every
    tool: an escape character in a title moved the cursor up and wrote a debt the other way round on the line a reader
    trusted, and one in a path the gate itself quotes cleared the screen on every commit. So every key and every string
    of a bean, a mapping, GARDEN.md and VOCAB.md is held to the law's row: no character of the category it names, but
    the ones it lets through — and a line feed only in a block scalar, where a value's lines are lines on the page. Read
    from the NODE GRAPH, because only there is a scalar's style known; the character is named, never echoed."""
    t = VALUE_TYPES.get('text')
    if not t or not t.get('holds_no'):
        return                          # check_value_types has said the row is missing, once
    _paths = (sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) + sorted(glob.glob(os.path.join(ROOT, 'mappings', '*.md')))
              + [os.path.join(ROOT, 'VOCAB.md'), os.path.join(ROOT, 'GARDEN.md')])
    for _f in _paths:
        if not os.path.exists(_f):
            continue
        try:
            _head = dmparse.read(_f)[0]
            _found = dmparse.control_characters(_head, t['holds_no'], t.get('but') or [], t.get('lines_in')) if _head else []
        except dmparse.NotUTF8:
            continue                          # refused by name where the document is loaded
        except Exception:
            continue                          # unparseable: build_docs reports it, with the parser's reason
        _rel = os.path.relpath(_f, ROOT).replace(os.sep, '/')
        for _path, _ch, _style, _is_key in _found:
            _how = ''
            if _ch == '\n':
                _how = " — a value of several lines is written as a block scalar: `<key>: |`, and its lines beneath"
            elif _style == '"':
                _how = (" — in double quotes a backslash begins an escape (`\\0` is U+0000, `\\e` U+001B): a backslash that "
                        "is part of the value is written in single quotes, where it is a backslash")
            errors.append(f"{_rel}: {'the key ' if _is_key else ''}{_path} holds U+{ord(_ch):04X} — "
                          f"{t.get('refusal') or 'a character text does not hold'} (VOCAB value_types[text]){_how}")


def check_gardens():
    """BETWEEN GARDENS (21.0). Three things, each a question only the whole garden can answer.

    WHOSE garden this is: `GARDEN.md` is judged AS ITSELF, by the `manifest` block of the law — at the scope of the
    mapping itself, by every rule an entry answers to: a key the law does not declare is refused (a retired one says
    where it went), a required one must be there, and each value is a position in what its attribute says. Until 21.0's
    fixes it was judged as one entry of a list, where its attributes — declared for the mapping itself — were read by
    nothing but the key check: `gardener:` could name no bean at all. Once the garden holds a bean it names its
    GARDENER, of a genos the law says may keep a garden. A garden whose keeper is written as an outside party in prose, in
    her own garden, is the case that asked for this.
    WHICH gardens it knows: its own id (read from git) and the `garden_id` of every `garden` bean — which is never its
    own: a garden's own id is read from its git, and a bean of it describing itself would be a second copy.
    WHAT NAMES CROSS: a qualified minted name must be qualified by a garden it knows, and a provenance record may name
    only a garden it knows — a fact from a garden nobody recorded has no one to ask."""
    _mf = std_fm.get('manifest') or {}
    _p = os.path.join(ROOT, _mf.get('path') or 'GARDEN.md')
    KNOWN_GARDENS.clear()
    _own = own_garden_id()
    if _own:
        KNOWN_GARDENS.add(_own)
    for (_is_bean, _base), (_fm, _b) in sorted(docs.items()):
        if _is_bean and _fm.get('genos') == 'garden':
            for _a in ((_fm.get('identity') or {}).get('anchors') or []):
                if isinstance(_a, dict) and _a.get('key') == 'garden_id' and _a.get('value'):
                    if _own and str(_a['value']) == _own:
                        errors.append(f"{_base}: a `garden` bean anchored by this garden's own id ({_own}) — a garden "
                                      f"bean records ANOTHER garden; this one's id is read from its git and its gardener "
                                      f"is named in GARDEN.md (VOCAB gene[garden]). A rehearsal is grown by germination, "
                                      f"never by clone, and so has an id of its own")
                    KNOWN_GARDENS.add(str(_a['value']))
    if _mf.get('attrs') and os.path.isfile(_p):
        _rel = os.path.relpath(_p, ROOT)
        _g = load(_p)[0]
        if not isinstance(_g, dict) or '__err__' in _g:
            _why = _g.get('__err__') if isinstance(_g, dict) else ('no --- fences' if _g is None else 'not a mapping')
            errors.append(f"{_rel}: its front matter does not read ({_why}) — the manifest says whose garden this is and "
                          f"which law governs it")
        else:
            for _k in sorted(set(_g) - set(_mf['attrs']), key=str):
                errors.append(f"{_rel}: `{_k}` is no key of the manifest (VOCAB manifest.attrs: {', '.join(_mf['attrs'])})"
                              + (retired_hint('manifest', _k) or " — a standing note for readers belongs in the body"))
            _sch = _NESTED.setdefault(('manifest', None), {'attrs': _mf['attrs']})
            _form = attribute_form('manifest', _sch)
            for _attr, _ in _facet(_form, 'required', 'self'):
                if _g.get(_attr) in (None, ''):
                    errors.append(f"{_rel}: `{_attr}:` is missing — the manifest requires it (VOCAB manifest.attrs.{_attr}: "
                                  f"{((_mf['attrs'].get(_attr) or {}).get('meaning') or 'required')})")
            _cell = _ECell(_rel, 'manifest', None, {k: v for k, v in _g.items() if k in _mf['attrs'] and v is not None},
                           _sch, scope='self')
            for _key, _controller in ENTRY_CONTROLLERS:
                if _key not in _NOT_FOR_A_VALUE:
                    _controller(_cell)
            if bean_ids and not _g.get('gardener'):
                errors.append(f"{_rel}: names no gardener — a garden is kept by someone: write their person bean first and "
                              f"name it here (`gardener: <bean id>`). An agent tends a garden; its gardener keeps it")
    for _where, _gid in GARDEN_REFS:
        if _gid not in KNOWN_GARDENS:
            errors.append(f"{_where}.garden '{_gid}' names a garden this one does not know — record it as a `garden` bean "
                          f"anchored by its `garden_id` before taking in what it said")
        elif _gid == _own:
            warns.append(f"{_where}.garden names this garden itself — a record made here carries no `garden`")
    _mint = IDP.get('minted') or {}
    if _mint.get('pattern'):
        for (_is_bean, _base), (_fm, _b) in sorted(docs.items()):
            for _a in ((_fm.get('identity') or {}).get('anchors') or []) if _is_bean else []:
                if not isinstance(_a, dict) or not ((TERMS.get(_a.get('key')) or {}).get('anchor') or {}).get('minted'):
                    continue
                _v = str(_a.get('value'))
                if law_match(_mint['pattern'], _v):
                    _pre, _, _rest = _v.partition('/')
                    if not minted_form(_rest):
                        # G1: a value is a name a garden gave only in the minted form. Anything else — a package name,
                        # a registry number, an invitation's UID — was assigned by someone else, and identifies wherever
                        # it is written: no garden may put its name on it.
                        errors.append(f"{_base}: anchor '{_a['key']}' '{_v}' puts a garden's id before '{_rest}', which is "
                                      f"not a name a garden gave — an identifier someone else assigned is not this garden's "
                                      f"to qualify. Write it as it was assigned ('{_rest}'); a name this garden mints is "
                                      f"`<genos>:<name>`, a genos this garden knows"
                                      + _rule('identity_policy.minted.form', 'identity_policy.minted'))
                    elif _pre not in KNOWN_GARDENS:
                        errors.append(f"{_base}: anchor '{_a['key']}' '{_v}' is a name minted by garden '{_pre}', which this "
                                      f"garden does not know" + (f" (its own id is {_own})" if _own else "") +
                                      " — a qualified name is this garden's own, or arrives with the `garden` bean of the "
                                      "garden that minted it")


def minted_form(value):
    """True when `value` is a NAME A GARDEN GAVE (std-vocab 21.0, `identity_policy.minted.form`): `<genos>:<name>`, the
    genos one this garden knows — a row of the registry `form_genos` names, which for `gene` is the law's gene and the
    garden's `local_gene`, exactly the gene a bean here may be. Any other value was assigned outside every garden."""
    _mint = IDP.get('minted') or {}
    if not _mint.get('form') or not law_match(_mint['form'], value):
        return False
    _reg = _mint.get('form_genos')
    if not _reg:
        return True
    _known = set(GENE) if _reg == 'gene' else {next(iter(r.values())) for r in (registry(_reg) or []) if isinstance(r, dict) and r}
    return str(value).split(':', 1)[0] in _known


def check_id_space_collision():
    for b in bean_ids & map_ids:
        errors.append(f"'{b}': same basename in beans/ AND mappings/ — ids unique per (space,base)")


# ---- identity capsule + establishing-anchor dedup ----
def check_identity_capsule():
    global est_owner
    est_owner = {}
    for (is_bean, base), (fm, body) in docs.items():
        if not is_bean:
            continue
        ident = fm.get('identity')
        if not isinstance(ident, dict):
            warns.append(f"{base}: no identity capsule (MERGE.md §4)")
            continue
        if not ident.get('status'):
            errors.append(f"{base}: identity.status missing")
        n_est = 0
        est_classes = []
        for a in (ident.get('anchors') or []):
            # D2/P4: the load-bearing distinction is `establishing` (establish vs corroborate), stated on the
            # anchor. `class` survives only as an optional hint at WHY it establishes — it no longer decides.
            if not isinstance(a, dict) or not all(k in a for k in ('key', 'value', 'establishing')):
                errors.append(f"{base}: each anchor needs key,value,establishing"); continue
            if not isinstance(a['key'], str):
                errors.append(f"{base}: an anchor's key is a term's name, written as text — not {a['key']!r}"); continue
            if not isinstance(a['establishing'], bool):
                errors.append(f"{base}: anchor '{a['key']}'.establishing must be true or false, not "
                              f"{a['establishing']!r} (VOCAB: establish vs corroborate is the load-bearing split)")
            # WHAT AN ANCHOR MAY CARRY IS DECLARED (20.0, `identity_policy.anchor_attrs`). Until then any key rode
            # along, which is how `authority` — a second vocabulary for how a value is known — lived beside
            # `provenance` for two months. An anchor says how it is known the way every entry does.
            _allowed = IDP.get('anchor_attrs')
            if _allowed:
                for _k in sorted(set(a) - set(_allowed)):
                    _hint = retired_hint('anchor', _k)
                    errors.append(f"{base}: anchor '{a['key']}' carries `{_k}`, which an anchor may not "
                                  f"(VOCAB identity_policy.anchor_attrs: {', '.join(_allowed)}){_hint}")
                _ap = a.get('provenance')
                if isinstance(_ap, dict):
                    check_provenance_record(f"{base}: anchor '{a['key']}'.provenance", _ap)
                if _ap is not None:
                    _srcs = ((TERMS.get('provenance_src') or {}).get('schema') or {}).get('values') or []
                    if not isinstance(_ap, dict) or not _ap.get('src') or not _ap.get('by') or not _ap.get('as_of'):
                        errors.append(f"{base}: anchor '{a['key']}'.provenance must be {{ src, by, as_of }} — the "
                                      f"same record a bean carries")
                    elif _srcs and _ap.get('src') not in _srcs:
                        errors.append(f"{base}: anchor '{a['key']}'.provenance.src '{_ap.get('src')}' is not one "
                                      f"of {_srcs} (VOCAB provenance_src)")
                    elif _ap.get('src') == (fm.get('provenance') or {}).get('src') and _ap.get('by') == (fm.get('provenance') or {}).get('by'):
                        warns.append(f"{base}: anchor '{a['key']}'.provenance repeats the bean's own — an anchor "
                                     f"carries a record only where its source differs")
            # a vocabulary term that declares an anchor policy OVERRULES the bean: this is what keeps a
            # role anchor (one that migrates between objects) corroborating-only, whatever a bean claims.
            pol = (TERMS.get(a['key']) or {}).get('anchor')
            if isinstance(pol, dict) and 'establishing' in pol and a.get('establishing') != pol['establishing']:
                _dir = ("promote a corroborating anchor to establishing" if a.get('establishing')
                        else "demote an establishing anchor to corroborating")
                errors.append(f"{base}: anchor '{a['key']}'.establishing is {a.get('establishing')} but the "
                              f"vocabulary declares {pol['establishing']} for that term — a bean may not "
                              f"{_dir}; write establishing: {str(pol['establishing']).lower()} (VOCAB {a['key']}.anchor)")
            # AN ANCHOR'S KEY IS A TERM (19.0, `identity_policy.anchor_key: term`): identity is matched by
            # (key, value), so a key no term declares is a merge key nobody agreed on. The term's `anchor:`
            # policy is what a garden declares; a local key is a local term with one.
            if IDP.get('anchor_key') == 'term' and not isinstance(pol, dict):
                _keys = _by_nearness(a['key'], [t for t, d in TERMS.items() if isinstance(d.get('anchor'), dict)])
                errors.append(f"{base}: anchor key '{a['key']}' is not a term that declares `anchor:` — write one "
                              f"that does, the nearest first: {', '.join(_keys)}. A key of this garden's own is a local "
                              f"term with `anchor: {{ class: …, establishing: … }}` in VOCAB.md: a RULE-CHANGE, which "
                              f"the gardener ratifies" + _rule('identity_policy.anchor_key'))
            if a.get('establishing') is True:
                n_est += 1
                est_owner.setdefault((a['key'], compare_value(a['key'], a['value'])), []).append(base)
                est_classes.append((a['key'], pol.get('class', a.get('class')) if isinstance(pol, dict) else a.get('class')))
        # min-anchor policy attaches to the root axis, not the genos (P3/D1) — read it from the declared registry.
        pol = _row(POLICY, fm.get(_axis)) if _axis else None
        need = (pol or {}).get('min_establishing_anchors')
        if need and ident.get('status') == IDP.get('applies_at_identity_status') and n_est < need:
            warns.append(f"{base}: {_axis} '{fm.get(_axis)}' requires {need} establishing anchor(s) when "
                         f"'{ident.get('status')}' but has {n_est} (VOCAB {_reg}.min_establishing_anchors)")
        # THE FAMILY IS ENFORCED (19.0, `identity_policy.establishing_family: enforced`): what establishes a
        # confirmed being is of its nature's family — matter for a body (soma), a logical id for the rest. The
        # class the term's policy declares wins over the class the bean wrote.
        fam = (pol or {}).get('establishing_anchor_family')
        if (IDP.get('establishing_family') == 'enforced' and fam
                and ident.get('status') == IDP.get('applies_at_identity_status')):
            for _k, _c in est_classes:
                if _c not in fam:
                    errors.append(f"{base}: establishing anchor '{_k}' is class '{_c}', outside the {_axis} "
                                  f"'{fm.get(_axis)}' family {fam} (VOCAB {_reg}.establishing_anchor_family) — "
                                  f"a being without an anchor of its family is `identity.status: provisional`, or "
                                  f"is of another nature (a virtual machine is a `virtual-host`, not a `host`)")

# HOW AN ANCHOR IS COMPARED (std-vocab 9.0, human-ratified). A term that governs an anchor may declare
# `compare_form`; uniqueness is then judged on that form, so `SYN-0042` and `syn-0042 ` are one object. A
# cold-start drill committed exactly that typo duplicate with 0 errors. Read from the vocabulary; names no key.
COMPARE_FORMS = dmparse.COMPARE_FORMS      # one definition, shared with bin/dmmerge.py

def compare_value(key, value):
    return dmparse.compare_anchor(TERMS.values(), key, value)


def check_establishing_anchor_dedup():
    for (k, v), bs in sorted(est_owner.items()):
        bs = sorted(set(bs))       # one bean carrying two spellings of one anchor is not a duplicate of itself
        if len(bs) > 1:
            errors.append(f"establishing anchor {k}={v} on {bs} — same object in one garden. If they ARE one "
                          f"object, keep one bean and move the other's facts into it (MERGE.md); if they are "
                          f"two, one of the anchor values is wrong")



# ============================== THE INTERPRETER ==============================
# ONE loop, driven entirely by `schema:` blocks in the vocabulary. No term is named in this code.

_aspects_of = dmform.aspects_of


def path_values(fm, path):
    """Scalar values at a dotted path; a `[]` suffix iterates a list (e.g. identity.anchors[].class)."""
    nodes = [fm]
    for part in path.split('.'):
        listy = part.endswith('[]')
        key = part[:-2] if listy else part
        nxt = []
        for n in nodes:
            if not isinstance(n, dict):
                continue
            v = n.get(key)
            if listy:
                if isinstance(v, list):
                    nxt.extend(v)
            elif v is not None:
                nxt.append(v)
        nodes = nxt
    return [n for n in nodes if not isinstance(n, (dict, list))]


def entries_of(shape, node):
    """Normalize a term's value into [(label, entry)] pairs for per-entry rules."""
    if shape == 'list_of_entries' and isinstance(node, list):
        return [(str(i), e) for i, e in enumerate(node)]
    if shape in ('open_map_of_entries', 'mapping') and isinstance(node, dict):
        return [(str(k), v) for k, v in node.items()]
    return []


# --- the per-ENTRY rules, one controller per declared entry key ---------------------------------------
# Same split as the term controllers, one level down: named after the schema key, never after a term.
# ============================== THE ATTRIBUTE FORM (S1 of the figure grammar) ==============================
# `bin/dmform.py` turns a term's schema into ONE record per attribute, and everything below reads only that. The
# law's text is unchanged — rewriting it into this form is S2, and it may not start until every reader is here.
_NORM = {}


def attribute_form(term, sch):
    if term not in _NORM or _NORM[term][0] is not sch:
        _NORM[term] = (sch, dmform.attribute_form(TERMS.get(term), sch))
    return _NORM[term][1]


_facet = dmform.facet


def form_of(term):
    """The attribute form of a term in force."""
    return attribute_form(term, SCHEMAS.get(term) or {})


# The cell carries `eff` — each aspect's EFFECTIVE position, stated or defaulted — because `on_aspect`
# and `cross_aspect` used to compute that separately from the same inputs. Two derivations of one fact
# can disagree about what a default means, and the one that disagrees silently is the dangerous one.
class _ECell:
    """One entry under inspection."""
    __slots__ = ('base', 'term', 'label', 'entry', 'sch', 'form', 'ref', 'eff', 'scope')

    def __init__(self, base, term, label, entry, sch, scope='entry'):
        self.base, self.term, self.label = base, term, label
        self.entry, self.sch = entry, sch
        self.form = attribute_form(term, sch)
        self.scope = scope                  # 'entry', or 'self' when the mapping ITSELF is what is judged
        self.ref = f"{term}[{label}]" if scope == 'entry' else term
        self.eff = {}                       # filled by ectl_on_aspect, read by ectl_cross_aspect


# --- STRUCTURE BEFORE PROSE: an entry carries only the attributes its term declares (std-vocab 12.0) ------------------
# A bean's top-level keys have been closed since 2026-09-17: a key no term declares is refused. One level down the
# door was still open, and what came through it was free text wearing a key's clothes — measured in one garden,
# forty attributes no term knew, among them `what_this_does_NOT_establish:` and `instrument_lesson:`, a sentence
# promoted to a field name so that it would look like data. Nothing can read such a key, merge it by identity, or
# ask every bean for it. The rule: an attribute is DECLARED by its term — typed by a schema construct, or described
# in the term's `entry_attrs:` / `attrs:` — or it is refused. Prose is not forbidden; it goes in an attribute the
# term declares FOR prose (`note`, `why`), where a reader knows to look. A term that declares no attribute at all
# (`owns`, `details`, `attributes`) is a free container by declaration and is left alone.
_REF_FORM = ('bean', 'mapping', 'field')


def declared_attrs(term, sch):
    """Every attribute the term declares — which, since S1, is simply every attribute in its attribute form."""
    _form = attribute_form(term, sch)
    out = set(_form['attrs'])
    if _form['alt']:
        out.add(_form['alt']['key'])
    if _form['self_ref'] and out:
        out |= set(_REF_FORM)               # the value IS a ref, so the link form's own keys belong to it
    if out:
        out.add('provenance')               # MODEL.md: "a fact whose source differs from the bean's default
                                            # carries its own record" — any entry may, so no term restates it
    return out, _form['self_ref']


def undeclared_attrs(base, term, where, node, sch):
    _decl, _self = declared_attrs(term, sch)
    if not _decl or not isinstance(node, dict):
        return                              # a free container, or a pure ref: nothing is declared to hold it to
    for _k in node:
        if _k not in _decl:
            errors.append(f"{base}: {where} carries `{_k}`, which the term `{term}` does not declare — an entry "
                          f"holds only declared attributes {sorted(map(str, _decl - set(_REF_FORM) - {'provenance'}))}. Prose belongs in "
                          f"the attribute the term declares for it (`note`, `why`); a new kind of fact is "
                          f"proposed as a new attribute, not written as a new key")


def ectl_declared_attrs(e):
    undeclared_attrs(e.base, e.term, e.ref, e.entry, e.sch)
    if isinstance(e.entry.get('provenance'), dict) and e.scope == 'entry':
        check_provenance_record(f"{e.base}: {e.ref}.provenance", e.entry['provenance'])


def ectl_entry_required_attrs(e):
    # REQUIRED is said, not only spelt: `paid_by: []` or `what: ""` names the key and says nothing under it
    missing = [k for k, _ in _facet(e.form, 'required', 'entry')
               if k not in e.entry or e.entry[k] is None or e.entry[k] in ('', [], {})]
    if missing:
        _f = [f for f in (_example_form(f"{e.term}.{k}") for k in missing) if f]
        errors.append(f"{e.base}: {e.ref} missing {missing} — present, and not empty"
                      + (f"; the form a tested example writes: {'; '.join(_f)}" if _f else '')
                      + _rule(f"{e.term}.schema.attrs", e.term, e.term.split('.')[0]))


def unknown_value_hint(sch, rule=None, term=None):
    """The fix for a value the law does not list: one it does. A value that is real and that the law lacks is kept under
    `details:` meanwhile, and proposed: added for this garden it changes the law, which the gardener ratifies. A term
    that reads its values from a REGISTRY takes a row of it: `values_add` on such a term adds nothing, because the term
    holds no list of its own to add to."""
    src = str((sch or {}).get('values_from') or '')
    _how = (f"a row under `registry_additions: {{ {src[9:].split('[')[0]}: [...] }}` in VOCAB.md"
            if src.startswith('registry:') else "`schema: {values_add: [...]}` in a VOCAB.md local_terms entry")
    return (" — write one of those. A value that is real and missing from the law is kept under `details:` for now, "
            f"and proposed: added for this garden, as {_how}, it changes the law — a RULE-CHANGE the gardener "
            "ratifies" + (_rule(rule, *([term] if term else [])) if rule else ''))


def ectl_entry_values(e):
    for attr, allowed in _facet(e.form, 'values', e.scope):
        if e.entry.get(attr) is not None and e.entry[attr] not in allowed:
            errors.append(f"{e.base}: {e.ref}.{attr} '{e.entry[attr]}' not in {allowed} "
                          f"(VOCAB {e.term}.schema.attrs.{attr}.in)")


def ectl_entry_types(e):
    for attr, typ in _facet(e.form, 'type', e.scope):
        if e.entry.get(attr) is None:
            continue
        check_value_type(f"{e.base}: {e.ref}", attr, e.entry[attr], typ)


def ectl_prose(e):
    """`in: prose` — words: a reason, a description, a remark. Any text a person writes, and a number or a date YAML read
    from it; never a list or a map, which say several things where the law asks for one saying."""
    for attr, _t in _facet(e.form, 'prose', e.scope):
        v = e.entry.get(attr)
        if _t == 'named' and isinstance(v, dict):
            # `{ prose: named }`: each saying under a name, and each one text
            _odd = sorted((str(k) for k, x in v.items() if not isinstance(k, str) or isinstance(x, (list, dict))), key=str)
            if _odd:
                errors.append(f"{e.base}: {e.ref}.{attr} holds words under names, each one text written under a name "
                              f"that is text — not {', '.join(_odd)} (VOCAB {_law_path(e.term)}.attrs.{attr}.in)")
            continue
        if isinstance(v, (list, dict)):
            errors.append(f"{e.base}: {e.ref}.{attr} is words, written as one text — not a "
                          f"{'list' if isinstance(v, list) else 'mapping'}")
    return None


def ectl_entry_pattern(e):
    """`entry_pattern:` (11.0) — an entry attr must match a form the TERM owns (a position whose system owns
    its form uses `entry_pattern_from_registry` instead)."""
    for attr, pat in _facet(e.form, 'pattern', e.scope):
        v = e.entry.get(attr)
        if v is not None and not law_match(pat, v):
            errors.append(f"{e.base}: {e.ref}.{attr} '{v}' is not in the form this term declares ({pat})")
    return None


def ectl_entry_soft_pattern(e):
    """`entry_soft_pattern:` (11.0) — the same as a WARNING: the form a value SHOULD take while a corpus is
    migrated onto it. A warning says what to fix; an error would refuse a garden's next commit for a value it
    has carried for months."""
    for attr, rule in _facet(e.form, 'soft', e.scope):
        vals = e.entry.get(attr)
        for v in (vals if isinstance(vals, list) else [vals]):
            if v is not None and not law_match(rule.get('pattern', ''), v):
                warns.append(f"{e.base}: {e.ref}.{attr} '{v}' — {rule.get('why') or 'not in the form this term expects'}")
    return None


def ectl_entry_must_match(e):
    """An entry attr pinned to a registry row selected by a field on the bean (e.g. crown <- nature)."""
    for rule in e.form['matches']['entry']:
        val = e.entry.get(rule.get('attr'))
        if val is None:
            continue
        key = ALL_FM.get(e.base, {}).get(rule.get('keyed_by'))
        row = next((r for r in (registry(rule.get('registry')) or [])
                    if isinstance(r, dict) and r.get(rule.get('keyed_by')) == key), None)
        if row is None:
            errors.append(f"{e.base}: {e.ref}.{rule['attr']} cannot be checked — no {rule['registry']} "
                          f"row for {rule['keyed_by']} '{key}'" + retired_hint(rule.get('keyed_by'), key))
        elif val != row.get(rule.get('take')):
            errors.append(f"{e.base}: {e.ref}.{rule['attr']} '{val}' does not match {rule['keyed_by']} "
                          f"'{key}', which routes to '{row.get(rule.get('take'))}' "
                          f"(VOCAB {e.term}.schema.entry_must_match)" + retired_hint(rule.get('attr'), val))


def effective(e, attr):
    """What an attribute holds for the purpose of a CHECK: what the entry states, else what `default_from` reads
    off a registry row another attribute of the same entry selects. Never written back, never an occupant."""
    if e.entry.get(attr) is not None:
        return e.entry[attr]
    rule = dict(_facet(e.form, 'default_from', e.scope)).get(attr)
    if not rule:
        return None
    key = e.entry.get(rule.get('keyed_by'))
    row = next((r for r in (registry(rule.get('registry')) or [])
                if isinstance(r, dict) and r.get(rule.get('keyed_by')) == key), None)
    return (row or {}).get(rule.get('take'))


def ectl_entry_in_registry(e):
    """An entry attr whose value must be a row of a REGISTRY — so the registry is the enum's one owner.

    The alternative is restating the list in `entry_values`, which is a second copy that can disagree with
    the registry it was copied from. This is the argument `values_consistent_with` already makes for a
    term's own enum, applied one level down to an entry's.
    """
    for attr, rule in _facet(e.form, 'registry', e.scope):
        val = e.entry.get(attr)
        if val is None:
            continue
        # `registry_from: <attr>` (9.1): the registry is NAMED by another field of the same entry — a code is
        # checked against the scheme the entry says it is in, so one term serves every classification
        rname = str(e.entry.get(rule['registry_from'])) if rule.get('registry_from') else rule.get('registry')
        rows = [r for r in (registry(rname) or []) if isinstance(r, dict) and dmform.row_matches(r, rule.get('where'))]
        allowed = [r.get(rule.get('take')) for r in rows]
        if str(val) not in [str(a) for a in allowed]:
            if len(allowed) > 40:
                allowed = allowed[:12] + ['… %d more' % (len(allowed) - 12)]
            _narrow = (' where ' + ', '.join(f"{k} is {v}" for k, v in rule['where'].items())) if rule.get('where') else ''
            errors.append(f"{e.base}: {e.ref}.{attr} '{val}' is not a declared {rname}{_narrow} "
                          f"— known: {sorted(v for v in allowed if v)} "
                          f"(VOCAB {e.term}.schema.attrs.{attr}.in)")


def ectl_entry_pattern_from_registry(e):
    """A position must be written in the ONE form its own system declares.

    The system owns its format and nothing else may spell a position its own way — the failure this
    prevents is already in the corpus: `staleness_key` carries four unowned spellings (`git-head:`,
    `git-commit:`, `digest:`, `manual:`), and one analysis acquired two verdicts because of it.

    NB `keyed_by` selects the registry row using a field of the ENTRY, where `entry_must_match` selects it
    using a field of the BEAN. The two rules ask different questions — which system is this position in,
    versus which row does this bean route to — and conflating them would make a position's form depend on
    the document that happens to carry it.

    A system with genuinely no canonical form declares `pattern: none`, and that DELIBERATE absence is
    honoured rather than treated as an unstated one — the same distinction `enforced_by: none` draws.
    """
    # EVERY attribute that takes its form from a sibling's system, not just the first: since 14.0 an endpoint has
    # two — `at`, in the system `system` names, and `port`, in the port space its `transport` names.
    for _name, rule in _facet(e.form, 'system_from', e.scope):
        val = e.entry.get(rule.get('attr'))
        if val is None:
            continue
        key = effective(e, rule.get('keyed_by'))
        row = next((r for r in (registry(rule.get('registry')) or [])
                    if isinstance(r, dict) and r.get(rule.get('keyed_by')) == key), None)
        if row is None:
            errors.append(f"{e.base}: {e.ref}.{rule['attr']} cannot be checked — no "
                          f"{rule['registry']} row for {rule['keyed_by']} '{key}'")
            continue
        pat = row.get(rule.get('take'))
        if rule.get('take') == 'pattern' and row.get('checked_by'):
            if dmparse.in_form(row, val) is False:          # the row names a tool that checks the form completely
                errors.append(f"{e.base}: {e.ref}.{rule['attr']} '{val}' is not in the one canonical form "
                              f"'{key}' declares — {rule['registry']}.{key} is {dmparse.form_said(row)}"
                              f"{': ' + row['form_note'] if row.get('form_note') else ''}. A system "
                              f"owns its format so nothing invents a second spelling of it.")
            continue
        if pat is None or pat == 'none':
            continue
        if not law_match(pat, val):
            # the pattern as the law writes it, not as Python's repr doubles its backslashes, and the row's own
            # statement of its form — what a person needs in order to write the position again
            errors.append(f"{e.base}: {e.ref}.{rule['attr']} '{val}' is not in the one canonical form "
                          f"'{key}' declares — {rule['registry']}.{key}.{rule['take']} is {pat}"
                          f"{': ' + row['form_note'] if row.get('form_note') else ''}. A system "
                          f"owns its format so nothing invents a second spelling of it.")
        else:
            check_day_exists(f"{e.base}: {e.ref}.{rule['attr']}", val, row)


def ectl_entry_form_from_genos_attr(e):
    """A genos may PIN which form its entries must use — and pinning also RESERVES that form.

    Any form some genos pins is available ONLY to the gene that pin it, so no bean can short-circuit its
    ownership chain straight to the axiom: the crown is reachable through your chain, not instead of it.
    """
    _fk = e.form['matches']['form_from_genos']
    if not _fk:
        return
    _genos = ALL_FM.get(e.base, {}).get('genos')
    if _genos is None:
        return                      # a bean with no genos: the missing key is refused once, by name, where it is read
    _form = (_row(GENE, _genos) or {}).get(_fk)
    def _names(k):
        v = k.get(_fk) if isinstance(k, dict) else None
        return set(v) if isinstance(v, list) else ({v} if v else set())
    _reserved = set().union(*(_names(k) for k in GENE.values()))
    if isinstance(_form, str) and _form not in e.entry:
        errors.append(f"{e.base}: {e.ref} must use the '{_form}' form — genos '{_genos}' pins "
                      f"{e.term}.{_fk} to it (VOCAB gene.{_genos}.{_fk}){_termination_hint(e.term, e.base)}")
    _mine = _names(_row(GENE, _genos) or {})
    for _used in (_reserved & set(e.entry)):
        if _used not in _mine:
            _allowed = sorted(k['genos'] for k in GENE.values() if _used in _names(k))
            _f = _example_form(e.term, genos=_genos)
            errors.append(f"{e.base}: {e.ref} uses the '{_used}' form, which is RESERVED to the gene "
                          f"{_allowed} — genos '{_genos}' does not name it in `{_fk}`, so its chain goes through "
                          f"a being rather than ending at a form reserved to others"
                          + (f"; a tested {_genos} writes {_f}" if _f else '') + _rule(f"gene[].{_fk}", _fk, 'gene'))


def ectl_on_aspect(e):
    """`on_aspect:` — the entry's position must be ON the closed figure it claims.

    This also RECORDS each aspect's effective position on the cell, because `cross_aspect` needs exactly
    the same derivation and used to repeat it.
    """
    for _aattr, _asp in _facet(e.form, 'aspect', e.scope):
        _adef = ASPECTS.get(_asp['aspect']) or {}
        _apos = {p['position'] for p in (_adef.get('positions') or []) if isinstance(p, dict)}
        _val = e.entry.get(_aattr, _asp.get('default'))
        if isinstance(_val, (list, dict)):
            # ONE POSITION, before any lookup: a list or a map is no position and cannot be looked for among them — it
            # ended the gate in a traceback, and a clause another garden sent could carry one
            errors.append(f"{e.base}: {e.ref}.{_aattr} is one position on aspect '{_asp['aspect']}', not a "
                          f"{'list' if isinstance(_val, list) else 'mapping'} — one of {sorted(_apos)}")
            e.eff[_aattr] = None
            continue
        e.eff[_aattr] = _val
        if _apos and _val not in _apos:
            errors.append(f"{e.base}: {e.ref}.{_aattr} '{_val}' is not a position on aspect "
                          f"'{_asp['aspect']}' {sorted(_apos)}")


def _cell_holds(e, cell):
    """Does this entry sit IN the cell? EVERY attribute is visible (15.0): an aspect attribute at its effective
    position, any other as stated, else as `default_from` reads it. `when` names a value, a LIST of values, or a
    `{starts_with}`. Until 15.0 a verdict cell saw only aspect positions, which is why a cleartext-and-required
    surface on LOOPBACK warned for six weeks: the cell could not see `exposure`."""
    for attr, (how, want) in cell['when'].items():
        have = e.eff[attr] if attr in e.eff else effective(e, attr)
        if how == 'is' and (have not in want if isinstance(want, list) else have != want):
            return False
        if how == 'starts' and not str(have or '').startswith(str(want)):
            return False
    return bool(cell['when'])


def _cells(e, phase):
    """A CELL is a combination of what an entry holds that may not stand (an error) or should not (a warning).
    `cross_aspect`, `entry_required_if` and `entry_expect_if` were three constructs for this one idea. Two aspects
    span a GRID, and a grid has cells neither square sees; a form that implies an attribute is the same shape."""
    for cell in e.form['cells']:
        if cell['phase'] != phase or not _cell_holds(e, cell):
            continue
        lack = [k for k in cell['lacks'] if not e.entry.get(k)]
        if cell['lacks'] and not lack:
            continue
        sink = errors if cell['severity'] == 'error' else warns
        if phase == 'cross':
            sink.append(f"{e.base}: {e.ref} is {cell['origin'].upper().replace('_', ' ')} — "
                        + ', '.join(f"{k}:{e.eff[k] if k in e.eff else effective(e, k)}" for k in cell['when'])
                        + f" — {cell['why'] or 'the two positions do not sit together'}")
            continue
        if len(cell['when']) > 1:
            sink.append(f"{e.base}: {e.ref} is at "
                        + ', '.join(f"{k}:{e.eff[k] if k in e.eff else effective(e, k)}" for k in cell['when'])
                        + f" but states no {', '.join(lack)}" + (f" — {cell['why']}" if cell['why'] else ''))
            continue
        (attr, (_how, want)), = cell['when'].items()
        if cell['origin'] == 'required_if':
            sink.append(f"{e.base}: {e.ref} declares {attr}:{want} but carries no {', '.join(lack)}")
        else:
            sink.append(f"{e.base}: {e.ref} has a {attr} starting '{want}' "
                        f"but no {lack[0]} — {cell['why'] or 'unverifiable'}")


def ectl_cross_aspect(e):
    _cells(e, 'cross')


def ectl_entry_one_of(e):
    one_of = list(e.form['one_of'])
    if one_of and not any(k in e.entry for k in one_of):
        errors.append(f"{e.base}: {e.ref} needs one of {one_of} (VOCAB {e.term}.schema.entry_one_of)")


def ectl_entry_required_if(e):
    _cells(e, 'cond')


def ectl_pointer_fields(e):
    """`pointer_fields:` — '<section>.<key>' on this bean | {bean,field} elsewhere | 'file:<path>'."""
    for attr, ptype in _facet(e.form, 'pointer'):
        if ptype != 'bean_field_pointer':
            continue
        val = e.entry.get(attr)
        for ptr in (val if isinstance(val, list) else [val] if val is not None else []):
            if not isinstance(ptr, str):
                continue                       # {bean,field} pointers resolve in the link pass below
            if ptr.startswith('file:'):
                _fp = ptr[5:]
                if not os.path.exists(os.path.join(ROOT, _fp)):
                    errors.append(f"{e.base}: {e.ref}.{attr} '{ptr}' does not resolve — no "
                                  f"such file in this garden")
                continue
            sect, _, key = ptr.partition('.')
            node = ALL_FM[e.base].get(sect)
            if not key or not isinstance(node, dict) or key not in node:
                errors.append(f"{e.base}: {e.ref}.{attr} '{ptr}' does not resolve — use "
                              f"'<section>.<key>' on this bean, {{bean,field}} for another bean, or "
                              f"'file:<path>'")


# Declaration order IS execution order, and it is the order these rules ran in before. `on_aspect` must
# precede `cross_aspect`: the second reads what the first computed.
def ectl_entry_quantities(c):
    for attr, want in _facet(c.form, 'quantity', c.scope):
        if c.entry.get(attr) is not None:
            check_quantity(f"{c.base}: {c.ref}.{attr}", c.entry[attr], want)


def ectl_entry_recurrences(c):
    for attr, _ in _facet(c.form, 'recurrence', c.scope):
        v = c.entry.get(attr)
        if v is not None:
            check_recurrence(f"{c.base}: {c.ref}.{attr}", v)


def ectl_entry_extents(c):
    """`entry_extents:` — attrs INSIDE an entry that hold a region (11.2)."""
    for attr, _ in _facet(c.form, 'extent', c.scope):
        v = c.entry.get(attr)
        if v is not None:
            check_extent(f"{c.base}: {c.ref}.{attr}", v)


def ectl_in_system(e):
    """`in: { system }` — a position in ONE named system, in that system's one form. `form_of` asks a sibling which
    system; this names it, for an attribute that is only ever in one (a moment a tool stamps is always `unix-epoch`)."""
    for attr, name in _facet(e.form, 'system', e.scope):
        v, row = e.entry.get(attr), SYSTEMS.get(name)
        if v is None:
            continue
        if row is None:
            errors.append(f"VOCAB {e.term}.schema.attrs.{attr}.in: system '{name}' is not in `anchor_systems`")
        elif dmparse.in_form(row, v) is False:
            errors.append(f"{e.base}: {e.ref}.{attr} '{v}' is not in the one canonical form '{name}' declares "
                          f"({dmparse.form_said(row) if row.get('checked_by') else row['pattern']}){' — ' + row['form_note'] if row.get('form_note') else ''}")
        else:
            check_day_exists(f"{e.base}: {e.ref}.{attr}", v, row)


def ectl_key_of(e):
    """`in: { key_of: <term> }` — a key of that term's mapping on THIS bean, or `<bean>:<key>` on another. Not an
    edge: it names a part of a being, and the being is reached by the refs the bean already states."""
    for attr, term in _facet(e.form, 'key_of', e.scope):
        v = e.entry.get(attr)
        if v is None:
            continue
        # ONE key, in ONE spelling: a list would let one attribute name two parts (and a keyed list count one party
        # twice), and `<this bean>:<key>` is a second spelling of the bare key that nothing would compare with the first.
        if not isinstance(v, str):
            errors.append(f"{e.base}: {e.ref}.{attr} names one key of `{term}` — written as text, not {type(v).__name__}")
            continue
        owner, _, key = v.rpartition(':')
        if owner == e.base:
            errors.append(f"{e.base}: {e.ref}.{attr} '{v}' names this bean's own key — write it bare: '{key}'")
            continue
        fm = ALL_FM.get(owner or e.base)
        ckeys = (TERMS.get(term) or {}).get('context_keys') or [term]
        if fm is None:
            errors.append(f"{e.base}: {e.ref}.{attr} '{v}' names bean '{owner}', which this garden does not hold")
        elif not any(isinstance(fm.get(k), dict) and key in fm[k] for k in ckeys):
            # key=str: a map's keys may mix text with what YAML read as a boolean or a number, and a refusal that
            # cannot sort its own list is a traceback (the key itself is refused as not text, elsewhere).
            errors.append(f"{e.base}: {e.ref}.{attr} '{v}' is no key of `{term}` on {owner or 'this bean'} — "
                          f"{sorted((x for k in ckeys if isinstance(fm.get(k), dict) for x in fm[k]), key=str)}")


_NESTED = {}           # (term, attr) -> the schema of the entries inside it; held so the form cache sees one object


def ectl_nested_entries(e):
    """`in: { entries }` — entries INSIDE an entry (a datum's records, a cursor). Each is judged as an entry, by every
    controller here, so nothing about a nested entry is a second, weaker kind of rule. A ref inside one is RESOLVED
    (dangling = error) and draws no edge: the graph is made of what a bean states at its own level."""
    for attr, attrs in _facet(e.form, 'entries', e.scope):
        v = e.entry.get(attr)
        if v is None:
            continue
        sch = _NESTED.setdefault((e.term, attr), {'shape': 'list_of_entries', 'attrs': attrs})
        if not isinstance(v, (list, dict)):
            errors.append(f"{e.base}: {e.ref}.{attr} holds entries — a list of mappings, or one mapping")
            continue
        # `keyed_by` (21.0): ONE entry per value of that attribute, and their order carries nothing. Two payers named
        # `sam` are one payer written twice — a sum over them counts sam twice — so the second is refused, not added.
        _key = dict(_facet(e.form, 'keyed_by', e.scope)).get(attr)
        if _key and isinstance(v, list):
            _seen = {}
            for i, item in enumerate(v):
                k = item.get(_key) if isinstance(item, dict) else None
                if k is None or not isinstance(k, (str, int, bool)):
                    continue
                if k in _seen:
                    errors.append(f"{e.base}: {e.ref}.{attr} holds two entries for {_key} '{k}' ({_seen[k]} and {i}) — "
                                  f"one entry per {_key}; put what they say in one (VOCAB {_law_path(e.term)}.attrs.{attr}.in.keyed_by)")
                else:
                    _seen[k] = i
        for i, item in enumerate(v if isinstance(v, list) else [v]):
            label = f"{e.label}/{i}" if isinstance(v, list) else e.label
            check_entry(e.base, f"{e.term}.{attr}", label, item, sch)
            for rattr in dmform.ref_attrs(attribute_form(f"{e.term}.{attr}", sch), 'entry'):
                r = item.get(rattr) if isinstance(item, dict) else None
                if isinstance(r, dict):
                    tid = r.get('bean') or r.get('mapping')
                    if tid is not None and (not isinstance(tid, str) or (tid not in bean_ids and tid not in map_ids)):
                        errors.append(f"{e.base}: {e.term}.{attr}[{label}].{rattr} names '{tid}', which this garden does not "
                                      f"hold — write beans/{tid}.md first, or in the same commit")


def _exact(x):
    """A fraction EXACTLY, as a reader writes it: a terminating decimal in full, else n/d. Never through a float."""
    n, d = x.numerator, x.denominator
    if d == 1:
        return str(n)
    r = d
    for p in (2, 5):
        while r % p == 0:
            r //= p
    if r != 1:
        return f"{n}/{d}"
    k = 0
    while (10 ** k) % d:
        k += 1
    digits = str(abs(n) * (10 ** k) // d).rjust(k + 1, '0')
    return ('-' if n < 0 else '') + digits[:-k] + '.' + digits[-k:].rstrip('0')


def ectl_sums(e):
    """`sums: {whole, parts}` (21.0) — the PARTS of a quantity add up to its WHOLE: what each payer paid adds up to what
    was paid. Checked EXACTLY, in fractions, never floats — the rule that closed truncation for units closes it for money
    — and only when every part's count is known, since an unknown part is a question and not a contradiction. A single
    part that states no amount holds the whole."""
    rule = e.sch.get('sums') if e.scope == 'entry' else None
    if not isinstance(rule, dict):
        return
    wholes = rule.get('whole') if isinstance(rule.get('whole'), list) else [rule.get('whole')]
    wattr = next((w for w in wholes if w and e.entry.get(w) is not None), None)
    pattr, _, pfield = str(rule.get('parts') or '').partition('.')
    parts = e.entry.get(pattr)
    if isinstance(parts, dict):
        parts = [parts]                     # the entries domain takes one mapping as one entry
    if not wattr or not isinstance(parts, list) or not parts:
        return
    whole = e.entry[wattr]
    if not isinstance(whole, dict):
        return                              # its form is check_quantity's to refuse
    if not all(isinstance(p, dict) for p in parts):
        return                              # a part that is not an entry is ectl_nested_entries' to refuse, by name
    stated = [p.get(pfield) for p in parts]
    if len(parts) == 1 and stated[0] is None:
        return
    if any(x is None for x in stated):
        return

    def _count(q):
        """A quantity's count as a Fraction, or None when it is not a count the law reads exactly."""
        c = q.get('count') if isinstance(q, dict) else None
        return Fraction(str(c)) if count_ok(c) else None
    units = {str(q.get('unit')) for q in stated if isinstance(q, dict)}
    if units != {str(whole.get('unit'))}:
        errors.append(f"{e.base}: {e.ref}.{pattr} is in {sorted(units)} and {wattr} in {whole.get('unit')} — the parts of an "
                      f"amount are in its own currency; a payment in another is a transaction of its own, or `charged`")
        return
    total, w = [_count(q) for q in stated], _count(whole)
    if w is None or any(x is None for x in total):
        return
    if sum(total) != w:
        errors.append(f"{e.base}: {e.ref}.{pattr} adds up to {_exact(sum(total))} {whole.get('unit')}, and {wattr} is "
                      f"{_exact(w)} {whole.get('unit')} — the parts of a whole add up to it exactly (VOCAB {e.term}.schema.sums)")


def _law_path(term):
    """Where a term's attributes are written in the law: `<term>.schema` for a term, the block itself for the manifest."""
    return f"{term}.schema" if term in TERMS else term


def ectl_bean_id(e):
    """`in: bean_id` — the id of a bean this garden holds; `in: { bean_id: { gene } }` — of one of those gene. The gene
    are the law's to say: which beings may keep a garden was written in two tools and nowhere in the law."""
    for attr, rule in _facet(e.form, 'bean_id', e.scope):
        v = e.entry.get(attr)
        if v is None:
            continue
        if not isinstance(v, str) or v not in bean_ids:
            errors.append(f"{e.base}: {e.ref}.{attr} '{v}' is not the id of a bean this garden holds — write "
                          f"beans/{v}.md first, or in the same commit")
            continue
        _gene = rule.get('gene') if isinstance(rule, dict) else None
        _genos = (docs.get((True, v)) or ({}, ''))[0].get('genos')
        if _gene and _genos not in _gene:
            errors.append(f"{e.base}: {e.ref}.{attr} '{v}' is a {_genos}, and this attribute names a bean of genos "
                          f"{' or '.join(map(str, _gene))} (VOCAB {_law_path(e.term)}.attrs.{attr}.in)")


ENTRY_CONTROLLERS = (
    ('declared_attrs', ectl_declared_attrs),
    ('attr: required', ectl_entry_required_attrs),
    ('in: values', ectl_entry_values),
    ('in: type', ectl_entry_types),
    ('in: prose', ectl_prose),
    ('in: pattern', ectl_entry_pattern),
    ('in: pattern, soft', ectl_entry_soft_pattern),
    ('entry_must_match', ectl_entry_must_match),
    ('in: registry', ectl_entry_in_registry),
    ('in: form_of', ectl_entry_pattern_from_registry),
    ('in: system', ectl_in_system),
    ('in: key_of', ectl_key_of),
    ('in: bean_id', ectl_bean_id),
    ('in: entries', ectl_nested_entries),
    ('entry_form_from_genos_attr', ectl_entry_form_from_genos_attr),
    ('in: aspect', ectl_on_aspect),
    ('cells: verdict', ectl_cross_aspect),
    ('entry_one_of', ectl_entry_one_of),
    ('cells: requires / expects', ectl_entry_required_if),
    ('in: extent', ectl_entry_extents),
    ('in: recurrence', ectl_entry_recurrences),
    ('in: quantity', ectl_entry_quantities),
    ('sums', ectl_sums),
    ('in: pointer', ectl_pointer_fields),
)


def check_entry(base, term, label, entry, sch):
    """Every per-entry rule the schema language can express."""
    if not isinstance(entry, dict):
        req = [n for n, _ in _facet(attribute_form(term, sch), 'required', 'entry')]
        _f = _example_form(term, entry=True)
        errors.append(f"{base}: {term}[{label}] must be a mapping with {req}"
                      + (f" — one entry, one mapping, in the form a tested example writes: {_f}" if _f else '')
                      + _rule(f"{term}.schema", term, term.split('.')[0]))
        return
    cell = _ECell(base, term, label, entry, sch)
    for _key, _controller in ENTRY_CONTROLLERS:
        _controller(cell)


def build_all_fm_and_targets():
    global ALL_FM, TARGETS_OF
    ALL_FM = {base: fm for (_ib, base), (fm, _) in docs.items()}   # mappings included: they carry terms too
    # `required_on_targets_of: <term>` — a bean POINTED AT by that relation must carry the declaring term.
    TARGETS_OF = {}
    for (_is_bean, _base), (_fm, _b) in docs.items():
        for _t, _s in SCHEMAS.items():
            _n = _fm.get(_t)
            if isinstance(_n, dict) and isinstance(_n.get('bean'), str) and _n['bean']:
                # a target is an id, written as text; one written otherwise is the link pass's to refuse, by name
                TARGETS_OF.setdefault(_t, set()).add(_n['bean'])

# --- the interpreter, as controllers dispatched by schema key ----------------------------------------
# One controller per key the schema language defines, named after the KEY and never after a term, so a
# new key is a new controller and a new TERM is no code at all. A controller returns STOP when the term
# needs no further plies; before this those were seven bare `continue`s, which is the same control flow
# with nothing saying so. Two of them are load-bearing rather than tidy:
#   * alt_form  — the inherited `via` form legitimately carries no facet keys, so the per-key rules must
#                 not ask it for any. 6 of 61 documents use that form; drop this and every one fails.
#   * required  — a term that is missing has nothing for the shape, key and entry rules to judge, and
#                 reporting all four for one absence buries the one that matters.
STOP = 'stop'


class _Cell:
    """One (document, term) pair under inspection — the state every controller shares."""
    __slots__ = ('base', 'fm', 'is_bean', 'term', 'sch', 'node')

    def __init__(self, base, fm, is_bean, term, sch):
        self.base, self.fm, self.is_bean = base, fm, is_bean
        self.term, self.sch = term, sch
        self.node = fm.get(term)


def ctl_path(c):
    """`path:` — a nested field addressed by path rather than by its own name."""
    if not c.sch.get('path'):
        return None
    allowed = allowed_values(c.sch)
    for val in path_values(c.fm, c.sch['path']):
        if allowed and val not in allowed:
            errors.append(f"{c.base}: {c.sch['path']} '{val}' not in {sorted(allowed)}"
                          + unknown_value_hint(c.sch, f"{c.term}.schema.values", c.term))
    return STOP


def ctl_governs_anchor(c):
    """`governs_anchor:` — a term may govern the FORMAT of the anchor values carrying its name."""
    _ga = form_of(c.term)['value'].get('governs_anchor')
    if not _ga:
        return None
    for _a in ((c.fm.get('identity') or {}).get('anchors') or []):
        if not isinstance(_a, dict) or _a.get('key') != _ga:
            continue
        _v = str(_a.get('value', ''))
        _pat = form_of(c.term)['value'].get('pattern')
        if _pat and not law_match(_pat, _v):
            _left = _unsaid_form('identity')
            errors.append(f"{c.base}: anchor {_ga}='{_v}' is not in canonical form "
                          f"({form_of(c.term)['value'].get('canonical_note', _pat)}) — write it as it was given, in "
                          f"that form. One nobody gave you is left out, never made up"
                          + (f": {_left}" if _left else '') + _rule(f"{c.term}.schema.value_pattern", c.term))
        _cf = form_of(c.term)['value'].get('compare_form')
        if _cf in COMPARE_FORMS and COMPARE_FORMS[_cf](_v) != _v:
            warns.append(f"{c.base}: anchor {_ga}='{_v}' is compared as '{COMPARE_FORMS[_cf](_v)}' — store it in that "
                         f"form (VOCAB {c.term}.schema.compare_form: {_cf})")
        _vr = form_of(c.term)['value'].get('in_registry')
        if _vr:
            # (9.1) an anchor that IS a code of a published classification must be one of its codes
            _known = {str(r.get(_vr.get('take'))) for r in (registry(_vr.get('registry')) or []) if isinstance(r, dict)}
            if _v not in _known:
                errors.append(f"{c.base}: anchor {_ga}='{_v}' is not a {_vr.get('registry')} code "
                              f"(VOCAB {c.term}.schema.value_in_registry)")
        if form_of(c.term)['value'].get('form') == 'ip':
            try:
                ipaddress.ip_address(_v)
            except ValueError:
                errors.append(f"{c.base}: anchor {_ga}='{_v}' is not a valid IP "
                              f"(VOCAB {c.term}.schema.value_form)")
    return STOP


def ctl_required(c):
    """`required:` / `required_on_<axis>s:` / `required_on_targets_of:` — must this term be here at all?

    The AXIS comes from the vocabulary key, not from this code, so `required_on_gene` and
    `required_on_natures` (and any future axis) need no interpreter change.

    MULTI-VALUED AXES (2026-08-07, human-ratified, std-vocab@7.0). The loop below read the axis as a
    SCALAR, which is the whole reason `router` had to be a genos (then a kind) rather than a role: a machine holds one
    genos and one nature, but it holds SEVERAL roles — a mail server may have five — and `x in vals` cannot express that.
    Rather than add a bespoke `required_on_roles`, the axis mechanism itself is generalised, so an axis may
    now be carried three ways and any future one inherits it:
      · a scalar          — `genos: host`
      · a list of scalars — `roles: [router, mail]`
      · a list of entries — `roles: [{role: router, why: ...}]`, each naming the axis
    The requirement fires if ANY held value matches, which is the only reading that makes sense for a
    collection: a machine that is a router among other things is still a router.
    """
    sch, fm, base, term, is_bean, node = c.sch, c.fm, c.base, c.term, c.is_bean, c.node
    why = "every bean" if (is_bean and sch.get('required') is True) else None
    _rt = sch.get('required_on_targets_of')
    if is_bean and _rt and base in TARGETS_OF.get(_rt, set()):
        why = f"being the target of a {_rt} edge"
    for key, vals in sch.items():
        if is_bean and key.startswith('required_on_') and isinstance(vals, list):
            axis, hit = _on_axis(fm, key[len('required_on_'):], vals)
            if hit:
                why = f"{axis} " + " / ".join(f"'{h}'" for h in hit)
    if why and (node is None or node == [] or node == {} or node == ''):
        _f = _example_form(term)
        errors.append(f"{base}: {why} requires a non-empty {term}"
                      + (f" — the form a tested example writes: {_f}" if _f else '') + _rule(term))
        return STOP                 # DECLARED: one absence, one finding — not four
    if node is None:
        return STOP                 # not required and not present: nothing to judge
    if _captured(fm, term, node):
        return STOP                 # a value nobody has chosen yet is not checkable (MERGE.md §10)
    return None


def _axis_of(plural):
    """The bean attribute a `required_on_<registry>` / `only_on_<registry>` key is keyed on: the field each row of that
    registry is named by (`gene` -> genos, `natures` -> nature, `roles` -> role). Read from the law's registry, so a
    registry whose plural is not its row's name and an `s` (γένη, of γένος) needs no rule here; a name no registry has
    reads as it always did, the plural less its `s`."""
    _first = next((r for r in (registry(plural) or []) if isinstance(r, dict) and r), None)
    return str(next(iter(_first))) if _first else plural[:-1]


def _on_axis(fm, plural, vals):
    """(axis, the values of it this document holds that are among `vals`). The axis is named by the schema key —
    `required_on_gene` / `only_on_gene` -> genos (`_axis_of`) — and may be held as a scalar, a list of scalars, or a list
    of entries each naming it (`roles: [{role: router}]`); the term carrying it may be plural."""
    axis = _axis_of(plural)
    held = fm.get(axis) if fm.get(axis) is not None else fm.get(plural)
    held = held if isinstance(held, list) else [held]
    hit = [h.get(axis) if isinstance(h, dict) else h for h in held]
    return axis, [h for h in hit if h is not None and h in vals]


def ctl_only_on(c):
    """`only_on_<axis>s:` (21.0) — ONLY a document holding one of these may carry the term. A garden's record that
    another garden is a rehearsal (`test`) is a fact about a garden; on a person it would say nothing anyone reads."""
    for key, vals in c.sch.items():
        if key.startswith('only_on_') and isinstance(vals, list):
            axis, hit = _on_axis(c.fm, key[len('only_on_'):], vals)
            if not hit:
                errors.append(f"{c.base}: {c.term} is carried only by a bean of {axis} {' or '.join(map(str, vals))}, "
                              f"and this one is {axis} '{c.fm.get(axis)}' (VOCAB {c.term}.schema.{key})")
                return STOP
    return None


def ctl_must_equal_genos_attr(c):
    """`must_equal_genos_attr:` — the value must agree with the registry row for this bean's genos."""
    mk = form_of(c.term)['matches']['equal_genos_attr']
    if not mk or not c.is_bean:
        return None
    _g = c.fm.get('genos')
    if _g is None:
        return None                 # a bean with no genos: the missing key is refused once, by name, where it is read
    kreg = _row(GENE, _g)
    if kreg is None and _captured(c.fm, 'genos', _g):
        return STOP                 # genos is mid-merge; the unclean warning already names it
    if kreg is None:
        errors.append(f"{c.base}: genos '{_g}' is not declared in the vocabulary, so its "
                      f"{c.term} cannot be checked (every bean's genos needs a `gene` row with {mk}) — write one the "
                      f"law declares, the nearest first: {', '.join(_by_nearness(_g, GENE))}" + _rule('gene'))
    elif kreg.get(mk) is None:
        errors.append(f"VOCAB genos '{_g}': missing '{mk}' (required to check {c.term})")
    elif c.node != kreg[mk]:
        errors.append(f"{c.base}: {c.term} '{c.node}' contradicts genos '{_g}' which refines "
                      f"{mk} '{kreg[mk]}' (VOCAB {c.term}.schema.must_equal_genos_attr)" + retired_hint(c.term, c.node))
    return None


def ctl_shape(c):
    """`shape:` — scalar, list_of_entries, mapping, open_map_of_entries."""
    shape = c.sch.get('shape')
    def _f():
        _e = _example_form(c.term)
        return f" — the form a tested example writes: {_e}" if _e else ''
    if shape == 'scalar':
        if isinstance(c.node, (list, dict)):
            errors.append(f"{c.base}: {c.term} is ONE value, not a {'list' if isinstance(c.node, list) else 'mapping'}"
                          + _f() + _rule(f"{c.term}.schema.shape", c.term))
            return STOP
        allowed = allowed_values(c.sch)
        if allowed and c.node not in allowed:
            _r = retired_hint(c.term, c.node)
            errors.append(f"{c.base}: {c.term} '{c.node}' not in {sorted(allowed)}"
                          + (_r + _rule(f"{c.term}.schema.values", c.term) if _r else
                             unknown_value_hint(c.sch, f"{c.term}.schema.values", c.term)))
        return STOP
    if shape == 'list_of_entries' and not isinstance(c.node, list):
        errors.append(f"{c.base}: {c.term} must be a LIST of entries" + _f() + _rule(f"{c.term}.schema.shape", c.term))
        return STOP
    if shape in ('mapping', 'open_map_of_entries') and not isinstance(c.node, dict):
        errors.append(f"{c.base}: {c.term} must be a MAPPING" + (", one entry per key, never a list" if shape ==
                      'open_map_of_entries' and isinstance(c.node, list) else '') + _f()
                      + _rule(f"{c.term}.schema.shape", c.term))
        return STOP
    return None


def ctl_alt_form(c):
    """`alt_form:` — an alternative single-key form (e.g. `owned_by: {via: ...}`)."""
    alt = form_of(c.term)['alt'] or {}
    if alt.get('key') and isinstance(c.node, dict) and alt['key'] in c.node:
        return STOP                 # DECLARED: the inherited form carries no facet keys to check
    return None


def ctl_required_attrs(c):
    """`required_attrs:` — attributes the mapping itself must carry. And, since 12.0, ONLY declared ones."""
    if c.sch.get('shape') == 'mapping' and not c.sch.get('key_form') and not form_of(c.term)['one_of']:
        undeclared_attrs(c.base, c.term, c.term, c.node, c.sch)
    for attr, _ in _facet(attribute_form(c.term, c.sch), 'required', 'self'):
        if isinstance(c.node, dict) and attr not in c.node:
            _f = _example_form(f"{c.term}.{attr}")
            errors.append(f"{c.base}: {c.term} requires '{attr}'" + (f" — the form a tested example writes: {_f}"
                          if _f else '') + _rule(f"{c.term}.schema.attrs.{attr}", c.term))
    return None


# The entry-only constructs: what they say is about an ENTRY among entries, or is stated for a value in its own words.
_NOT_FOR_A_VALUE = ('declared_attrs', 'attr: required', 'entry_must_match', 'entry_form_from_genos_attr', 'entry_one_of')


def ctl_value_as_entry(c):
    """A mapping that is not a list of entries is ONE entry, and is judged by the same controllers. Until 18.0 the
    value scope had its own copies of four of them and none of the rest, so a `pattern` or a closed list declared
    on a mapping's attribute was a rule nothing read."""
    if form_of(c.term)['scope'] != 'self' or not isinstance(c.node, dict):
        return None
    cell = _ECell(c.base, c.term, None, c.node, c.sch, scope='self')
    for _key, _controller in ENTRY_CONTROLLERS:
        if _key not in _NOT_FOR_A_VALUE:
            _controller(cell)
    return None


def ctl_key_form(c):
    """`key_form:` — what the mapping's keys must look like when the key set is open."""
    kf = str(c.sch.get('key_form') or '')
    if not (kf and isinstance(c.node, dict)):
        return None
    for k in c.node:
        if kf == 'kebab' and KEBAB and not KEBAB.match(str(k)):
            errors.append(f"{c.base}: {c.term} key '{k}' must be kebab-case "
                          f"(the key is open, but still paper-durable)")
        elif kf.startswith('values_from:'):
            _src = kf.split(':', 1)[1]
            allowed = _values_of({'values_from': _src}) if _src.startswith('registry:') else term_values(_src)
            if not allowed:
                errors.append(f"{c.base}: {c.term} keys are `{kf}`, and that names no values — a key form that allows "
                              f"anything checks nothing")
                break
            if k not in allowed:
                errors.append(f"{c.base}: {c.term} key '{k}' not in declared {kf.split(':', 1)[1]} "
                              f"{sorted(allowed)}")
        elif kf == 'values':
            allowed = allowed_values(c.sch)
            if allowed and k not in allowed:
                errors.append(f"{c.base}: {c.term} key '{k}' not in {sorted(allowed)}")
    return None


def ctl_on_sequence(c):
    """`on_sequence:` (10.1, T4) — the value is a walk on a SEQUENCE aspect: prose lines in list order, or step
    entries whose `next` lists are CLOSED neighbourhoods (these branches and no others). The aspect's own
    restrictions decide the rest: whether a loop is allowed is its `acyclic`, whether an end is owed is `ends`."""
    _asp = c.sch.get('on_sequence')
    if not _asp or c.node is None:
        return None
    _a = ASPECTS.get(_asp) or {}
    if _a.get('figure') != 'sequence':
        errors.append(f"VOCAB {c.term}: on_sequence '{_asp}' is not a sequence aspect")
        return None
    where = f"{c.base}: {c.term}"
    if not isinstance(c.node, list):
        errors.append(f"{where} must be a list — prose lines, or step entries {{id, do, next}}"); return None
    _prose = [x for x in c.node if isinstance(x, str)]
    _steps = [x for x in c.node if isinstance(x, dict)]
    if _prose and _steps or len(_prose) + len(_steps) != len(c.node):
        errors.append(f"{where} mixes prose lines and step entries — write one form: a routine read half by list "
                      f"order and half by `next` has no single order"); return None
    if not _steps:
        return None                                   # prose: the list order IS the sequence, as before
    ids, nexts = [], {}
    for i, st in enumerate(_steps):
        sid = st.get('id')
        if not sid or not (KEBAB is None or KEBAB.match(str(sid))):
            errors.append(f"{where}[{i}] needs a kebab-case `id`"); continue
        if sid in nexts:
            errors.append(f"{where}: two steps are '{sid}' — a step is named once"); continue
        if not isinstance(st.get('do'), str) or not st['do'].strip():
            errors.append(f"{where}.{sid} needs `do`: what the step does")
        _n = st.get('next') or []
        if not isinstance(_n, list) or not all(isinstance(x, dict) and x.get('to') for x in _n):
            errors.append(f"{where}.{sid}.next must be a list of {{to, when?}}"); _n = []
        if len(_n) > 1:
            for x in _n:
                if not str(x.get('when') or '').strip():
                    errors.append(f"{where}.{sid}: a branch to '{x.get('to')}' names no `when` — with two or more "
                                  f"ways on, each must say when it is taken")
        ids.append(sid); nexts[sid] = [x['to'] for x in _n]
    for sid, tos in nexts.items():
        for t in tos:
            if t not in nexts:
                errors.append(f"{where}.{sid}: next '{t}' names no step of this routine (a branch to nowhere)")
    if not ids:
        return None
    seen, todo = set(), [ids[0]]
    while todo:
        n = todo.pop()
        if n in seen or n not in nexts:
            continue
        seen.add(n); todo.extend(nexts[n])
    for sid in ids:
        if sid not in seen:
            errors.append(f"{where}.{sid}: no step reaches it from '{ids[0]}', where the routine starts")
    if _a.get('ends') in ('bounded', 'open-start') and not any(not nexts[s] for s in ids):
        errors.append(f"{where}: no step ends the routine — give at least one step no `next`")
    if _a.get('acyclic') is True and _cycles({k: v for k, v in nexts.items()}):
        errors.append(f"{where}: loops, and '{_asp}' declares acyclic")
    return None


def ctl_entries(c):
    """The per-ENTRY rules, for any shape that has entries at all."""
    shape = c.sch.get('shape')
    _form = form_of(c.term)
    if shape in ('list_of_entries', 'open_map_of_entries') or _form['one_of'] \
            or _facet(_form, 'required', 'entry'):
        for label, entry in entries_of(shape, c.node):
            _at = _member_path(c.term, c.term, label, entry) if isinstance(c.node, list) else f"{c.term}.{label}"
            if _captured(c.fm, _at, entry):
                continue            # an entry two gardens hold two ways, both kept: nobody has chosen yet (MERGE.md §10)
            if _is_conflict(entry):
                continue            # a conflict record nothing captured: refused by name, at its path, below
            check_entry(c.base, c.term, label, entry, c.sch)
    return None


# The order is the order the rules ran in before, written down. A key that is absent from a schema costs
# its controller one `return None`, which is why adding a key never touches any other controller.
CONTROLLERS = (
    ('path', ctl_path),
    ('governs_anchor', ctl_governs_anchor),
    ('required', ctl_required),
    ('only_on', ctl_only_on),
    ('must_equal_genos_attr', ctl_must_equal_genos_attr),
    ('shape', ctl_shape),
    ('alt_form', ctl_alt_form),
    ('attr: required (value)', ctl_required_attrs),
    ('every other domain (value)', ctl_value_as_entry),
    ('key_form', ctl_key_form),
    ('entries', ctl_entries),
    ('on_sequence', ctl_on_sequence),
)


def check_terms():
    """Every document, against every term the vocabulary declares."""
    for (is_bean, base), (fm, body) in docs.items():
        for term, sch in SCHEMAS.items():
            cell = _Cell(base, fm, is_bean, term, sch)
            for _key, _controller in CONTROLLERS:
                if _controller(cell) is STOP:
                    break


# --- facet parity: two arcs of one loop must carry the same facets (schema `facet_parity_with`; P7) ---
# Ownership is meaningful only where responsibility covers it on the opposite aspect. A facet owned but
# unanswered-for is a loose end; a facet answered for but unowned is orphaned.
def _facet_shape(node, alt):
    """The set of facets a node carries, or the INHERITED form's key when it uses that form instead.

    `alt` comes from the term's own `alt_form.key`, never from a literal here: the interpreter reads
    that declaration generically everywhere else, and this check was the one place that knew the name
    by heart — a second copy of a declared datum, sitting three functions from where it is read.
    """
    if not isinstance(node, dict):
        return None
    return alt if (alt and alt in node) else frozenset(node)


def _alt_key(term):
    return (form_of(term)['alt'] or {}).get('key')


def _shape_str(shape, alt):
    # key=str: a key YAML read as a number or a boolean (`1:`, `yes:`) sits beside the facet names, and the shape is
    # printed, never compared — the refusal of that key by name is the answer, not a traceback in sorting it
    return alt if shape == alt else sorted(shape, key=str)

def check_facet_parity():
    for _term, _sch in SCHEMAS.items():
        _par = form_of(_term)['mirror']['parity_with'] if _term in SCHEMAS else None
        if not _par:
            continue
        for (_is_bean, _base), (_fm, _b) in docs.items():
            if not _is_bean:
                continue
            _a, _o = _fm.get(_term), _fm.get(_par)
            if _a is None and _o is None:
                continue
            if _a is None:
                errors.append(f"{_base}: has {_par} but no {_term} — an ownership claim nothing answers for "
                              f"is a loose end (VOCAB {_term}.rules.parity)")
            elif _o is None:
                errors.append(f"{_base}: has {_term} but no {_par} — a duty nobody owns is orphaned "
                              f"(VOCAB {_term}.rules.parity)")
            else:
                _ka, _ko = _alt_key(_term), _alt_key(_par)
                _sa, _so = _facet_shape(_a, _ka), _facet_shape(_o, _ko)
                if _sa is None or _so is None:
                    # One of the two is not a mapping at all, so it has no facet SHAPE to compare. The
                    # `must be a MAPPING` rule owns that error; comparing anyway crashed the gate on
                    # `sorted(None)` — reachable since this check was written, and reached for the first
                    # time by the coverage pass that was measuring what the suite never fires.
                    continue
                if _sa != _so:
                    errors.append(f"{_base}: {_term} and {_par} disagree on facets "
                                  f"({_shape_str(_sa, _ka)} vs {_shape_str(_so, _ko)}) — "
                                  f"the two arcs must close (VOCAB {_term}.rules.parity)")



# --- declared inverse relations must agree (schema `inverse_of`; P4/D3) ----------------------------
# A convenience edge that mirrors a fact must not be able to drift from the fact it mirrors.
def _inverse_of(sch):
    """(term, cardinality) from `inverse_of`, which is a bare name or a mapping.

    A bare name means one-to-one and the mirror is enforced both ways — that is what it always meant,
    and it was wrong for `runtime`, whose type side cannot point back at three instances through one
    mapping. Declaring the cardinality is the fix; reading it in one place is what stops the two plies
    from disagreeing about what was declared.
    """
    inv = dmform.attribute_form(None, sch)['mirror']['inverse_of']
    if isinstance(inv, dict):
        return inv.get('term'), inv.get('cardinality', 'one-to-one')
    return inv, 'one-to-one'


def check_inverse_relations():
    for _term, _sch in SCHEMAS.items():
        _inv, _card = _inverse_of(_sch)
        if not _inv:
            continue
        for (_is_bean, _base), (_fm, _b) in docs.items():
            if not _is_bean or not isinstance(_fm.get(_term), dict):
                continue
            _tgt = _fm[_term].get('bean')
            if not isinstance(_tgt, str) or (True, _tgt) not in docs:
                continue                                  # a dangling or malformed target is reported by link integrity
            _back = docs[(True, _tgt)][0].get(_inv)
            if not (isinstance(_back, dict) and _back.get('bean') == _base):
                errors.append(f"{_base}: {_term} -> '{_tgt}', but {_tgt}.{_inv} does not point back to "
                              f"'{_base}' (VOCAB {_term}.schema.inverse_of: {_inv})")



# ============================== THE REVERSE GATE (P3.5) ==============================
# The interpreter above asks whether each OBJECT is passed by the rules. This asks the converse:
# whether each RULE is passed by the objects. A declared position with no occupant is a blind region —
# it may be a prediction, an impossibility, or simply out of context, but it must SAY WHICH. Silence is
# how a vocabulary quietly accumulates possibilities nothing is looking for. Positions are derived from
# the schemas themselves, so this names no term (rule: the machinery never names an aspect).
def check_vacancy_reasons_declared():
    global VACANCY_REASONS
    VACANCY_REASONS = set(std_fm.get('vacancy_reasons') or ())
    if not VACANCY_REASONS:
        # No fallback, deliberately, and for the reason law_carrier already gives: a gate that cannot load
        # the law must ERROR rather than substitute one of its own. A default set here would silently accept
        # whatever this file happened to believe on a garden whose vocabulary says something else.
        errors.append("seed/std-vocab.md declares no `vacancy_reasons:` — the gate will not check a "
                      "vacancy's reason against a list of its own invention. Declare them in the "
                      "vocabulary (law_carrier: there is exactly one path to the law).")

LOCAL_ADDED = set()      # (source, position) a garden added with `values_add` — the garden accounts for exactly these


def _declared_positions():
    """Every position the VOCABULARY offers: {source: {position}}, and which sources are the garden's.

    A source is `<term>.values`, `<term>.<entry attr>`, `aspect:<name>` or `<term>.entry_one_of` — the
    address a vacancy is declared `at`. The second return is the subset this garden DECLARED itself.
    """
    declared_pos, local_pos = {}, set()
    LOCAL_ADDED.clear()
    # WHOEVER DECLARES A POSITION ACCOUNTS FOR IT (P6/B2). A garden's occupancy claim covers only the
    # positions IT declared: Tier-0 positions are Tier-0's to account for, in its own vacancies block.
    # Without this a fresh garden fails its first gate run, ordered to justify `nature: soma` before it
    # has written a bean — which is precisely the debt promotion must not export.
    LOCAL_SCHEMA = {t['term']: (t.get('schema') or {})
                    for t in (vocab_fm.get('local_terms') or []) if isinstance(t, dict) and t.get('term')}

    def _declare(src, vals, local):
        declared_pos.setdefault(src, set()).update(v for v in (vals or []) if not isinstance(v, (dict, list)))
        if local:
            local_pos.add(src)

    for term, sch in SCHEMAS.items():
        _loc = LOCAL_SCHEMA.get(term, {})
        _form, _lform = form_of(term), dmform.attribute_form(None, _loc)
        if _form['value'].get('values'):
            if 'values' not in _lform['value'] and _loc.get('values_add'):
                # ONLY the added values are the garden's to account for; the rest stay Tier-0's.
                _t0 = next((t.get('schema') or {} for t in (std_fm.get('terms') or []) + PROFILE_TERMS
                            if isinstance(t, dict) and t.get('term') == term), {})
                _added = set(_loc['values_add']) - set(_t0.get('values') or [])   # already Tier-0's: not the garden's
                _declare(f"{term}.values", [v for v in _form['value']['values'] if v not in _added], False)
                declared_pos[f"{term}.values"].update(_added)
                LOCAL_ADDED.update((f"{term}.values", v) for v in _added)
            else:
                _declare(f"{term}.values", _form['value']['values'], 'values' in _lform['value'])
        elif str(_form['value'].get('values_from') or '').startswith('registry:'):
            _declare(f"{term}.values", term_values(term), False)     # the registry's rows; the garden's own are below
            _reg, _, _fld = str(_form['value']['values_from'])[len('registry:'):].partition('[].')
            for _r in ((vocab_fm.get('registry_additions') or {}).get(_reg) or []):   # a row this garden ADDED is its own
                if isinstance(_r, dict) and _r.get(_fld) is not None:
                    LOCAL_ADDED.add((f"{term}.values", _r[_fld]))
        # A closed list on an attribute offers its positions whether the attribute is each ENTRY's or the mapping's
        # ITSELF (a `shape: mapping` term is one entry): `words.form` offered three positions and none was counted, so
        # nothing asked whether `written` or `unstated` was ever taken, and no vacancy for either could be declared.
        for _scope in ('entry', 'self'):
            for attr, vals in _facet(_form, 'values', _scope):
                _declare(f"{term}.{attr}", vals, 'values' in _lform['attrs'].get(attr, {}))
        # A REGISTRY IS ITS OWN ENUM OWNER (18.0). An attribute that takes a row of a registry takes a position AT
        # that registry, addressed `registry:<name>`. Tier-0's rows are Tier-0's to account for; a row this garden
        # ADDED is the garden's, and it is stated once — no owner term to restate it on.
        for _scope in ('entry', 'self'):
            for attr, _rule in _facet(_form, 'registry', _scope):
                if _rule.get('registry') and _rule.get('take'):
                    _src = f"registry:{_rule['registry']}"
                    _declare(_src, [r.get(_rule['take']) for r in (registry(_rule['registry']) or []) if isinstance(r, dict)], False)
                    for _r in ((vocab_fm.get('registry_additions') or {}).get(_rule['registry']) or []):
                        if isinstance(_r, dict) and _r.get(_rule['take']) is not None:
                            LOCAL_ADDED.add((_src, _r[_rule['take']]))
        for _aattr, _asp in _facet(_form, 'aspect', 'entry') + _facet(_form, 'aspect', 'self'):
            if _asp['aspect'] in ASPECTS:
                _declare(f"aspect:{_asp['aspect']}",
                         [p['position'] for p in (ASPECTS[_asp['aspect']].get('positions') or [])
                          if isinstance(p, dict)], False)
        # `entry_one_of` forms are positions too. The law offers a shape — `owner`, `contract`,
        # `external`, `crown` — and a shape nothing takes is the same blind region as an enum value
        # nobody occupies. Nothing counted them until 2026-08-03, and all three that turned out to be
        # empty are genuinely empty rather than overlooked.
        if _form['one_of']:
            _declare(f"{term}.entry_one_of", list(_form['one_of']), bool(_lform['one_of']))
    return declared_pos, local_pos


def _occupied_positions():
    """Every position the CORPUS takes, addressed the same way `_declared_positions` addresses them."""
    occupied_pos = {}

    def _occupy(src, vals):
        # a value that is not a scalar takes no position (and cannot be held in a set): its form is refused elsewhere
        occupied_pos.setdefault(src, set()).update(v for v in vals if v is not None and not isinstance(v, (dict, list)))

    for (is_bean, base), (fm, _body) in docs.items():
        for term, sch in SCHEMAS.items():
            if sch.get('path'):
                _occupy(f"{term}.values", path_values(fm, sch['path']))
                continue
            node = fm.get(term)
            if node is None:
                continue
            _form = form_of(term)
            if sch.get('shape') == 'scalar' and term_values(term):
                _occupy(f"{term}.values", [node])
            kf = str(sch.get('key_form') or '')
            if kf.startswith('values_from:') and isinstance(node, dict):
                alt = (_form['alt'] or {}).get('key')             # the inherited form is not a position
                # addressed as `_declared_positions` addresses it: a key that is a row of a REGISTRY takes a position AT
                # that registry (`registry:facets`), a key that is a term's value at `<term>.values`. The registry form
                # was recorded at `registry:facets[].facet.values`, which nothing declares — so no facet key ever counted
                # as used, a garden's own facet in use was refused as unoccupied, and a vacancy for one never went stale.
                _src = kf.split(':', 1)[1]
                _occupy(f"registry:{_src[len('registry:'):].split('[')[0]}" if _src.startswith('registry:') else f"{_src}.values",
                        [k for k in node if k != alt])
            if _form['scope'] == 'self' and isinstance(node, dict):          # a mapping is one entry
                for attr, _rule in _facet(_form, 'registry', 'self'):
                    if _rule.get('registry') and node.get(attr) is not None:
                        _occupy(f"registry:{_rule['registry']}", [node[attr]])
                for attr, _vals in _facet(_form, 'values', 'self'):
                    if node.get(attr) is not None:
                        _occupy(f"{term}.{attr}", [node[attr]])
                for _aattr, _asp in _facet(_form, 'aspect', 'self'):
                    if node.get(_aattr) is not None:                         # a default does not occupy
                        _occupy(f"aspect:{_asp['aspect']}", [node[_aattr]])
            _asps = _facet(_form, 'aspect', 'entry')
            _alt_k = (_form['alt'] or {}).get('key')
            _forms = list(_form['one_of'])
            if _forms and not (isinstance(node, dict) and _alt_k and _alt_k in node):
                # the INHERITED form carries no facets and therefore takes no position. The entries are a mapping's
                # values or a LIST's members: `over` is a list whose entries take `thing` or `what`, and reading only
                # mappings left a list-shaped term's forms forever unoccupied — a garden's own would be refused.
                for _fnode in (node.values() if isinstance(node, dict) else node if isinstance(node, list) else []):
                    if isinstance(_fnode, dict):
                        _occupy(f"{term}.entry_one_of", [f for f in _forms if f in _fnode])
            for _lbl, entry in entries_of(sch.get('shape'), node):
                if isinstance(entry, dict):
                    for attr, _vals in _facet(_form, 'values', 'entry'):
                        if entry.get(attr) is not None:
                            _occupy(f"{term}.{attr}", [entry[attr]])
                    # An attribute that takes a row of a registry occupies a position AT that registry.
                    for attr, _rule in _facet(_form, 'registry', 'entry'):
                        if _rule.get('registry') and entry.get(attr) is not None:
                            _occupy(f"registry:{_rule['registry']}", [entry[attr]])
                    for _aattr, _asp in _asps:
                        # A DEFAULT DOES NOT OCCUPY (ratified 2026-08-03). This read `entry.get(attr,
                        # default)`, so a position nothing ever stated looked exercised because the gate's
                        # own default landed on it — the reverse gate believing itself. Occupancy is now
                        # STATEMENT: only a value an entry actually carries takes the position. What that
                        # leaves empty is a vacancy like any other, declared in `vacancies:` with a reason,
                        # and anti-rot then warns the day something really occupies it.
                        if entry.get(_aattr) is not None:
                            _occupy(f"aspect:{_asp['aspect']}", [entry[_aattr]])
    return occupied_pos


def _vacancy_index():
    """The declared vacancies, {(at, position): entry}, CHECKED for reason and why as they are indexed.

    Checked here rather than in the comparison below because these two rules are about the vacancy
    RECORD itself — a reason off the declared list, a missing why — and hold whether or not the
    position turns out to be occupied. The second return is the subset this garden declared, which is
    the only subset anti-rot may raise as an error.
    """
    vac_index, local_vac = {}, set()
    for _tier, _vs in (('tier0', (std_fm.get('vacancies') or []) + PROFILE_VAC),
                       ('local', vocab_fm.get('vacancies') or [])):
        for v in _vs:
            if not isinstance(v, dict):
                continue
            _key = (str(v.get('at')), v.get('position'))
            vac_index[_key] = v
            if _tier == 'local':
                local_vac.add(_key)
            if v.get('reason') not in VACANCY_REASONS:
                errors.append(f"{_tier} vacancies: {v.get('at')} = '{v.get('position')}' has reason "
                              f"'{v.get('reason')}' not in {sorted(VACANCY_REASONS)}")
            if not str(v.get('why') or '').strip():
                errors.append(f"{_tier} vacancies: {v.get('at')} = '{v.get('position')}' needs a 'why' — "
                              f"a vacancy is information only when it carries its reason")
    return vac_index, local_vac


def check_reverse_gate():
    """Offered, taken, and accounted for — the three sets, compared.

    The three are built by the helpers above rather than in one 100-line pass, because they answer
    three separate questions and only the comparison needs all three at once. Their ORDER is still
    load-bearing: `_vacancy_index` reports on the vacancy records themselves and must do so before
    this loop reports on the positions, or a garden with a malformed vacancy reads its consequences
    before its cause.
    """
    declared_pos, local_pos = _declared_positions()
    occupied_pos = _occupied_positions()
    vac_index, local_vac = _vacancy_index()

    for src, decl in sorted(declared_pos.items()):
        occ = occupied_pos.get(src, set())
        for pos in sorted(decl - occ, key=str):
            if src not in local_pos and (src, pos) not in LOCAL_ADDED:
                continue
            if (src, pos) not in vac_index:
                errors.append(f"VOCAB {src}: position '{pos}' is declared but NO bean occupies it — give it "
                              f"an occupant, or declare it in `vacancies:` with a reason")
        for pos in sorted(decl & occ, key=str):
            # A Tier-0 vacancy that this garden OCCUPIES is a prediction coming true. It cannot be an error —
            # the garden may not edit Tier-0 — but silence would let Tier-0 vacancies rot unnoticed, which is
            # the very failure anti-rot exists to prevent. So: warn, addressed to whoever maintains Tier-0.
            # A `universal` one is no prediction: it was declared because the mechanism is whole, for every garden
            # that does not stand on it, and one garden standing on it withdraws nothing.
            if (src, pos) in vac_index and (src, pos) not in local_vac \
                    and (vac_index[(src, pos)] or {}).get('reason') != 'universal':
                warns.append(f"{src}: position '{pos}' is declared vacant at TIER-0 but is OCCUPIED here — "
                             f"the prediction came true; whoever maintains std-vocab should withdraw it")
            if (src, pos) in local_vac:      # anti-rot: only a vacancy THIS garden declared can be an error
                errors.append(f"VOCAB vacancies: {src} = '{pos}' is declared vacant but IS occupied — "
                              f"remove the stale vacancy")
    for at, pos in sorted(vac_index, key=str):
        if pos not in declared_pos.get(at, set()):
            errors.append(f"VOCAB vacancies: {at} = '{pos}' is not a declared position (stale or misspelt)")



# ============================== link integrity + acyclic check ==============================
def schema_edges(fm):
    """Ref edges declared by the vocabulary (schema ref_fields / entry_ref_fields / pointer_fields).

    EVERY edge the gate resolves comes from here (P4) — there is no second source, and no relation is
    named in this file. A one-line `edges()` wrapper used to sit in front of it saying exactly that,
    which left two names for one generator and let a reader think the two differed.
    """
    for term, sch in SCHEMAS.items():
        node = fm.get(term)
        if node is None:
            continue
        _form = form_of(term)
        alt = _form['alt'] or {}
        if alt.get('key') and isinstance(node, dict) and alt['key'] in node:
            for attr in alt['refs']:
                it = node.get(attr)
                if isinstance(it, dict) and 'bean' in it:
                    yield 'bean', it.get('bean'), None, term
            continue
        for attr in dmform.ref_attrs(_form, 'self'):
            it = node if attr == 'self' else (node.get(attr) if isinstance(node, dict) else None)
            if isinstance(it, dict) and 'bean' in it:
                yield 'bean', it.get('bean'), it.get('field'), term
        for label, entry in entries_of(sch.get('shape'), node):
            if not isinstance(entry, dict):
                continue
            for attr in dmform.ref_attrs(_form, 'entry'):
                it = entry if attr == 'self' else entry.get(attr)
                if isinstance(it, dict):
                    for space in ('bean', 'mapping'):
                        if space in it:
                            yield space, it.get(space), it.get('field'), term
            for attr, ptype in _facet(_form, 'pointer'):
                if ptype != 'bean_field_pointer':
                    continue
                val = entry.get(attr)
                for ptr in (val if isinstance(val, list) else [val] if val is not None else []):
                    if isinstance(ptr, dict) and 'bean' in ptr:
                        yield 'bean', ptr.get('bean'), ptr.get('field'), f"{term}[{label}].{attr}"


def section_keys(fm):
    # DELIBERATELY WIDER THAN _AUTHORITATIVE, and not an oversight. This answers "what key names does
    # this document use", so that a `{bean: X, field: K}` ref can be resolved — and a ref may legitimately
    # point into `refs` or `access`, which carry no authoritative values of their own. Stated because an
    # undeclared difference between two nearly-identical lists reads as a bug and invites a tidy-up.
    s = set(fm.keys())
    for sect in ('owns', 'attributes', 'refs', 'access', 'details'):
        if isinstance(fm.get(sect), dict):
            s |= set(fm[sect].keys())
    return s


def _cycles(graph):
    """Every back edge in `graph`, as the trail of ids that reaches it.

    ONE walk with two callers: `check_acyclic` runs it over the graph MERGED from every dag-declared
    relation, and `check_acyclic_per_relation` runs it over each relation alone. Same algorithm, same
    order, different graph and different sink — so it is written once rather than twice, which is the
    rule this file applies to derived facts applied to the derivation itself. Colour 2 marks a node
    already finished: reaching it again is a diamond, not a cycle.
    """
    colour, trails = {}, []

    def walk(n, trail):
        colour[n] = 1
        for m in graph.get(n, []):
            if colour.get(m, 0) == 1:
                trails.append(trail + [n, m])
            elif colour.get(m, 0) == 0:
                walk(m, trail + [n])
        colour[n] = 2

    for n in list(graph):
        if colour.get(n, 0) == 0:
            walk(n, [])
    return trails


def check_link_integrity():
    global DAG_TERMS, dep_graph
    DAG_TERMS = {n for n, s in SCHEMAS.items() if on_walk(s, acyclic_only=True)}
    dep_graph = {}
    for (is_bean, base), (fm, body) in docs.items():
        for space, tgt, field, sect in schema_edges(fm):
            pool = bean_ids if space == 'bean' else map_ids
            if not isinstance(tgt, str):
                errors.append(f"{base}: {sect} target not a string id ({tgt!r}) — quote it"); continue
            if tgt not in pool:
                # WHAT TO DO NEXT, not only what is wrong: a party or a ref named before its bean is the commonest case,
                # and the bean may be written in the same commit as what names it.
                _near = _nearest(tgt, pool, n=3, cutoff=0.7)
                errors.append(f"{base}: {sect} -> {space} '{tgt}' does not exist (dangling) — write "
                              f"{'beans' if space == 'bean' else 'mappings'}/{tgt}.md first, or in the same commit; a "
                              f"link that was said is not dropped to pass the gate"
                              + (f". The {space}s here named like it: {', '.join(_near)}" if _near else '')); continue
            tgt_fm = docs[(space == 'bean', tgt)][0]
            if field is not None and not isinstance(field, str):
                errors.append(f"{base}: {sect} -> {tgt}.field names one key, written as text — not {type(field).__name__}")
                continue
            if field and field not in section_keys(tgt_fm):
                errors.append(f"{base}: {sect} -> {tgt}.{field} — field not present in '{tgt}'")
            if field and isinstance(tgt_fm.get('refs'), dict) and field in tgt_fm['refs']:
                warns.append(f"{base}: {sect} -> {tgt}.{field} points at a ref (ref-to-ref)")
            if sect in DAG_TERMS and space == 'bean':
                dep_graph.setdefault(base, []).append(tgt)


def check_acyclic():
    for trail in _cycles(dep_graph):
        errors.append(f"cycle ({'/'.join(sorted(DAG_TERMS))}): {' -> '.join(trail)}")



# ============================== ip dedup (vocab-driven, std-vocab 'ip' context_keys) ==============================
def collect_ips(fm):
    out = []
    def consider(kp, val):
        # str(kp): a year written as a key (`details: { 2026: ... }`) is read by YAML as a number, and fnmatch takes text
        if any(fnmatch.fnmatch(str(kp), p) for p in ip_patterns):
            for v in (val if isinstance(val, list) else [val]):
                if isinstance(v, str):
                    out.append(v)
    for sect in _AUTHORITATIVE:
        d = fm.get(sect)
        if isinstance(d, dict):
            for k, v in d.items():
                consider(k, v)
                if k == 'identifiers' and isinstance(v, dict):
                    for k2, v2 in v.items():
                        consider(f'identifiers.{k2}', v2)
    return out


def check_duplicate_authoritative_ip():
    owner = {}
    for (is_bean, base), (fm, body) in docs.items():
        if not is_bean:
            continue
        shared = set(fm.get('shared_identifiers') or [])
        scope = fm.get('scope') or fm.get('network') or ''
        for v in collect_ips(fm):
            if v in shared:
                continue
            try:
                norm = str(ipaddress.ip_address(v))
            except ValueError:
                warns.append(f"{base}: value '{v}' under an ip key is not a valid IP"); continue
            owner.setdefault((norm, scope), []).append(base)
    for (ip, scope), bs in sorted(owner.items()):
        if len(bs) > 1:
            errors.append(f"duplicate authoritative IP {ip}{'@'+scope if scope else ''} owned by {bs} "
                          f"(ref it, or shared_identifiers/scope per VOCAB 'ip')")



# ---- single owner of a fact: the same long value stated authoritatively in two beans ----------------


def _long_values(fm):
    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                yield from walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and len(node.strip()) > 60:
            yield path, node.strip()
    for sect in _AUTHORITATIVE:
        if isinstance(fm.get(sect), dict):
            yield from walk(fm[sect], sect)


def check_single_owner_of_a_fact():
    _value_owner = {}
    for (is_bean, base), (fm, _b) in docs.items():
        for path, val in _long_values(fm):
            _value_owner.setdefault(val, []).append(f"{base}.{path}")
    for _val, _where in sorted(_value_owner.items()):
        if len({w.split('.')[0] for w in _where}) > 1:
            warns.append(f"the same authoritative value is stated in {sorted({w.split('.')[0] for w in _where})} "
                         f"({', '.join(_where[:3])}) — one owner of a fact: keep it in one bean and `ref` it "
                         f"from the others. Value begins: {_val[:70]}…")



# ============================== pre-commit: the staged state must be sound ==============================
# Everything above reads the WORKING TREE. What gets committed is the INDEX, and they are not the same
# thing under partial staging. These two checks read the staged blobs, so what is committed is what was
# checked. The second closes the edit->gate window that text surgery kept slipping through: an edit that
# destroys a document, or silently drops a whole top-level key, cannot reach history.
# Both go through `_git` below: it is the one place that knows how to run git in ROOT and how to report
# an unanswered question. These two used to call subprocess directly, so a third reading of the same
# index went through a second, slightly different code path — and the callers here genuinely do not care
# WHY a blob is absent (a path not staged and a path deleted in the index are both "nothing to read"),
# which is exactly the distinction `_git` returns and these two discard on purpose.
def _staged_text(p):
    return _git('show', f':{p}')[0]


def _head_text(p):
    return _git('show', f'HEAD:{p}')[0]


def build_staged_constants():
    global DOCUMENTISH, LAW_DOCS, FRONT_MATTER_DOCS
    DOCUMENTISH = ('beans/', 'mappings/')

    # WHICH DOCUMENTS ARE LAW — DERIVED, never listed. This was a hardcoded tuple of three filenames while
    # `beans/daftar.md` declared FIVE documents `standing: law`, so MODEL.md, CHECKLIST.md and MERGE.md could
    # each be committed with no journal entry at all — the most consequential writes in the system, and the
    # only ones exempt from logging. Two lists that can disagree did disagree, in both directions.
    # The gate names no document now, exactly as it names no term: a garden says what its law is, and the
    # duty follows automatically when a document's standing changes.
    _STRUCTURAL_LAW = {os.path.relpath(STD, ROOT), 'VOCAB.md', 'GARDEN.md'}
    # Structural because the gate reads all three as law on EVERY run, in every garden, including one with no
    # beans at all to declare anything. GARDEN.md earns it for a different reason than the other two: it
    # carries the `extends:` pin, and moving a pin adopts a different law wholesale.
    LAW_DOCS = set(_STRUCTURAL_LAW)
    for _fm in ALL_FM.values():
        for _e in (_fm.get('standing') or []):
            if isinstance(_e, dict) and _e.get('standing') == 'law' and isinstance(_e.get('doc'), str):
                LAW_DOCS.add(_e['doc'][5:] if _e['doc'].startswith('file:') else _e['doc'])
    # THE RELEASE'S OWN FILES ARE LAW TOO (v0.5.0, human-ratified). Everything seed/LANGUAGE lists arrived from a
    # daftar release — the model, the checklist, the tools, the gate itself. A garden may still patch one
    # locally, but never silently: a cold-start drill committed an edit to bin/dmcheck.py with no journal entry.
    global LANGUAGE_PATTERNS
    _lang = os.path.join(ROOT, 'seed', 'LANGUAGE')
    LANGUAGE_PATTERNS = ([l.strip() for l in open(_lang, encoding='utf-8')
                          if l.strip() and not l.lstrip().startswith('#')] if os.path.isfile(_lang) else [])

    # NOT the same set, and deliberately so. The integrity check below parses front matter and refuses a
    # document that has lost it; MODEL.md and CHECKLIST.md are prose and carry none, so holding them to it
    # would refuse them as "destroyed" on every commit. Law is about what a change MEANS; this is about what
    # a file must still BE.
    FRONT_MATTER_DOCS = ('VOCAB.md', 'GARDEN.md', 'std-vocab.md')

# The commit-time half of this gate reads the STAGED blobs, so it needs an index to read them from.
# Being unable to ASK is not the same as being told the index is empty, and until 2026-08-03 this code
# could not tell those apart: the whole block sat inside a bare `except Exception: pass`. In any tree
# with no .git — a `cp -r`, an unpacked tarball, a copy carried to another machine — five Part-A rules
# silently did not run and the gate still printed `0 error(s)`. Reproduced before the fix: a copy of
# this garden with .git removed and the entire `owns:` block deleted from beans/daftar.md — the block
# carrying `invariant_no_silent_fallback` itself — reported `58 docs, 0 error(s)`, exit 0. The hole was
# not unknown: test/germinate.py's own docstring names it, and that test was built AROUND it.
# A gate that cannot verify must REFUSE. That is not a new rule — it is what `law_carrier` already says
# about the vocabulary, applied to the transport the other half of the law arrives on.
def _git(*args):
    """Run git in ROOT. Returns (stdout, None) on success, (None, why) when the question went unanswered.

    Read as UTF-8, a byte that is not replaced rather than fatal. Strict, a staged blob that is not UTF-8 failed inside
    subprocess's reader thread on Windows — a traceback above the verdict, and the blob read as absent, so unchecked.
    Replaced, it is still judged: a UTF-16 blob has no fences and is refused as a destroyed document."""
    try:
        r = subprocess.run(['git', '-C', ROOT, *args], capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=5)
    except Exception as e:                    # git absent, or it hung — still an unanswered question
        return None, f"{e.__class__.__name__}: {e}"
    if r.returncode != 0:
        _lines = (r.stderr or '').strip().splitlines()
        return None, _lines[0] if _lines else f"git exited {r.returncode}"
    return r.stdout, None


def _git_bytes(*args):
    """git's output as it wrote it — decoded as UTF-8, with no newline translated. '' when the question went unanswered
    (`_git` has already said why, for the questions that must be answered)."""
    try:
        r = subprocess.run(['git', '-C', ROOT, *args], capture_output=True, timeout=5)
    except Exception:
        return ''
    return r.stdout.decode('utf-8', 'replace') if r.returncode == 0 else ''


# What `str.splitlines()` ends a line at, beside the newline itself. A journal line holds none of them.
_LINE_BOUNDARIES = frozenset('\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029')


def _journal_command(body='- action: <what was done, and why>'):
    """The command that writes a journal entry, as it works in every shell a garden is kept from — cmd, PowerShell 5.1,
    a POSIX shell: `--body` rather than `< entry.md` (PowerShell reserves `<`), and the interpreter by the name this
    platform gives it (`python` on Windows, where `python3` may be the Store's placeholder), as seed/germinate.py does."""
    py = 'python' if os.name == 'nt' else 'python3'
    return f'{py} bin/dmjournal.py "<who>" "<what>" --body "{body}"'


def _save_command(body):
    """The ONE command that finishes a commit refused for want of any entry: bin/dmsave.py writes the entry as the
    journal tool writes it, stages everything and commits (v0.34.1). A garden whose tools predate it is given the
    journal tool's command."""
    if not os.path.isfile(os.path.join(ROOT, 'bin', 'dmsave.py')):
        return _journal_command(body)
    py = 'python' if os.name == 'nt' else 'python3'
    return f'{py} bin/dmsave.py "<who>" "<what>" --body "{body}"'


# Probe with rev-parse rather than with the diff itself: outside a repository `git diff` silently becomes
# `--no-index` and complains about the FLAG, which names the wrong problem to whoever reads the error.
def check_staged_state():
    _out, _why = _git('rev-parse', '--git-dir')
    if not _why:
        _out, _why = _git('diff', '--cached', '--name-only')

    if _why:
        errors.append(f"NO INDEX at {ROOT} — this is not a readable git working copy ({_why}). The five "
                      f"commit-time rules (provenance duty, "
                      f"RULE-CHANGE duty, undeclared top-level removal, gutted subtree, emptied body) "
                      f"CANNOT run here, so this run has NOT checked what a commit would contain. This is a "
                      f"refusal, not a pass: a garden is a git-backed ledger, and a tree with no index is a "
                      f"copy of one. Run the gate in the working copy, or `git init` this tree.")
        staged = []
    else:
        staged = _out.split()

    if staged:
        # (K) provenance duty — a state-change must be logged
        sc = [p for p in staged if p.startswith(DOCUMENTISH)]
        if sc and 'log/journal.md' not in staged:
            errors.append(f"state-change staged ({', '.join(sc[:3])}…) but log/journal.md not updated — provenance duty. "
                          f"Append an entry naming what changed and why. Its heading is read from the clock by the tool, "
                          f"never typed; this writes it, stages everything and commits:"
                          f"\n      {_save_command(f'- action: <what was done to {sc[0]}>')}")
        # ...and a RULE-CHANGE all the more so: it is human-ratified and must be logged DISTINCTLY.
        rc = [p for p in staged if p in LAW_DOCS or any(fnmatch.fnmatch(p, _pat) for _pat in LANGUAGE_PATTERNS)]
        if rc and 'log/journal.md' not in staged:
            errors.append(f"RULE-CHANGE staged ({', '.join(rc)}) but log/journal.md not updated — a change "
                          f"to the vocabulary or the law is human-ratified and must be logged distinctly, "
                          f"more than an ordinary state-change, not less")

        # ONLY the ADDED lines count as the declaration. Matching the whole diff would match its context
        # lines too, so on an append-only journal any common word would look "mentioned" — a false
        # negative that quietly disarms the rule. (Found by AB3: `tags` appeared in nearby context.)
        # SPLIT WHERE GIT SPLITS, AND NOWHERE ELSE. A diff line ends at '\n'. Read as text, the diff's '\r' became a line
        # end, and `splitlines()` also ends a line at \x0b \x0c \x1c \x1d \x1e \x85 U+2028 U+2029 — so an added line
        # holding `\x1c## <a date> · <someone> · …` gave up its tail as a line with no '+', which was dropped before the
        # heading checks ever saw it, while every reader that splits the journal the same way saw a heading nobody wrote.
        _jraw = _git_bytes('diff', '--cached', '--unified=0', '--', 'log/journal.md')
        _added = [l[1:] for l in _jraw.split('\n') if l.startswith('+') and not l.startswith('+++')]
        jdiff = '\n'.join(_added)
        for _l in _added:
            _l = _l[:-1] if _l.endswith('\r') else _l          # a CRLF line end is a line end
            _odd = sorted({repr(ch) for ch in _l if ch in _LINE_BOUNDARIES})
            if _odd:
                errors.append(f"log/journal.md: an added line holds {', '.join(_odd)} — a character some readers take as "
                              f"the end of a line, so what follows it would read as a line of its own (a heading nobody "
                              f"wrote). A journal line ends only at a newline: remove it — "
                              f"'{''.join(repr(c)[1:-1] if c in _LINE_BOUNDARIES else c for c in _l[:80])}'")

        # THE ENTRY MUST SAY WHAT IT RECORDS (2026-09-17, human-ratified). Until v0.4.0 these three duties were
        # satisfied by ANY byte added to the journal: a cold-start drill appended the single line `x` and
        # committed a bean change, and committed a vocabulary change whose entry never said RULE-CHANGE, while
        # MODEL.md, the journal template and dmrules all described both as enforced. A garden's FIRST commit —
        # germination, which has no HEAD to compare against — is exempt: nothing in it was decided by anyone yet.
        if 'log/journal.md' in staged and _git('rev-parse', '--verify', '-q', 'HEAD')[0]:
            if rc and 'RULE-CHANGE' not in jdiff:
                errors.append(f"RULE-CHANGE staged ({', '.join(rc)}) but the staged journal entry never says RULE-CHANGE — "
                              f"a change to the law is logged DISTINCTLY. Put the word RULE-CHANGE in the entry.")
            for _p in sc:
                _id = os.path.basename(_p)[:-3] if _p.endswith('.md') else _p
                if not re.search(r'(?<![\w-])' + re.escape(_id) + r'(?![\w-])', jdiff):
                    errors.append(f"{_p}: staged, but the staged journal entry never names it — write '{_id}' "
                                  f"(or [[{_id}]]) in the entry, so the record says WHICH bean changed; an entry that "
                                  f"names it: {_journal_command(f'- action: [[{_id}]] <what changed>')}")
            if '(fill in' in jdiff:
                errors.append("the staged journal entry still contains '(fill in' — a template field was left "
                              "unfilled; say who ratified the change and why before committing")
            # THE HEADING IS A POSITION IN TIME (10.0). Only headings this commit ADDS: history is never rewritten.
            _stamped = None
            for _h in (l for l in _added if l.startswith('## ')):
                if not journal_heading_ok(_h):
                    errors.append(f"journal heading '{_h}' is not a position in time — "
                                  + ("a heading is the tool's, read from the clock and never typed: remove it and its "
                                     f"lines, then {_journal_command()}" if JOURNAL.get('heading') == 'stamped' else
                                     f"write {JOURNAL.get('heading_form')}, read from the clock: {_journal_command()} "
                                     f"writes it") + _rule('journal.heading_form', 'journal.heading'))
                    continue
                # THE MOMENT IS MEASURED, NOT REMEMBERED (20.0, `journal.heading: stamped`). The gate cannot tell
                # a clock reading from a typed one by its form; it can tell whether bin/dmjournal.py wrote it,
                # because the tool registers every heading it writes in this clone's git directory.
                if JOURNAL.get('heading') == 'stamped':
                    if _stamped is None:
                        try:
                            import dmjournal
                            _stamped = dmjournal.registered(ROOT)
                        except Exception:
                            _stamped = set()
                    if _h.rstrip() not in _stamped:
                        errors.append(f"journal heading '{_h[:80]}' was not written by bin/dmjournal.py — a heading "
                                      f"is read from the clock by the tool, never typed: remove the typed heading and "
                                      f"its lines, then {_journal_command()}" + _rule('journal.heading'))
        for p in staged:
            if not (p.startswith(DOCUMENTISH) or p.endswith(FRONT_MATTER_DOCS)):
                continue
            cur = _staged_text(p)
            if cur is None:
                continue                              # deleted in the index
            head_fm, _hb = dmparse.split_front_matter(cur)
            if head_fm is None:
                errors.append(f"{p}: STAGED content has no front-matter fences — refusing to commit a "
                              f"destroyed document"); continue
            try:
                now = dmparse.loads(head_fm)
                assert isinstance(now, dict)
            except Exception as e:
                errors.append(f"{p}: STAGED content does not parse ({e}) — refusing to commit a broken "
                              f"document"); continue
            prev_text = _head_text(p)
            if prev_text is None:
                continue                              # new file: nothing to lose
            prev_head, _pb = dmparse.split_front_matter(prev_text)
            try:
                prev = dmparse.loads(prev_head) if prev_head else None
            except Exception:
                prev = None
            if not isinstance(prev, dict):
                continue
            lost = [k for k in prev if k not in now]
            unmentioned = [k for k in lost if k not in jdiff]
            if unmentioned:
                errors.append(f"{p}: staged edit REMOVES top-level {unmentioned} and the staged journal "
                              f"entry does not mention {'it' if len(unmentioned) == 1 else 'them'} — "
                              f"say why in log/journal.md, or restore what the edit dropped")
            # ...and the case a top-level check CANNOT see: the key survives while its SUBTREE is gutted.
            # This is what dmsafe catches at write time, and dmsafe is opt-in — it protects only the
            # writes someone remembered to route through it. Measured over 35 commits: flat leaf-loss is
            # routine (61 edits, median 6% of leaves) and would be noise, while a gutted subtree occurred
            # ZERO times. So that is the signal, and the comparison is dmsafe's own rather than a copy.
            for k in prev:
                if k not in now:
                    continue
                la, lb = dmsafe.leaf_paths(prev[k]), dmsafe.leaf_paths(now[k])
                gutted = (len(la) >= 3 and not (lb - {''})) or (len(la) >= 6 and len(lb) <= len(la) * 0.2)
                if gutted and k not in jdiff:
                    errors.append(f"{p}: staged edit GUTS '{k}' — {len(la)} recorded value(s) reduced to "
                                  f"{len(lb)}, while the key itself survives so a top-level check cannot "
                                  f"see it. Name '{k}' in the staged journal entry if that is intended.")
            # a bean whose human body was emptied is unreadable on paper (Rule 6), and no commit in this
            # garden's history has ever done it — so requiring it costs nothing and closes the last gap.
            if p.startswith('beans/'):
                _sb = dmparse.split_front_matter(cur)[1]
                if not (_sb or '').strip():
                    errors.append(f"{p}: staged edit leaves the bean with NO human body (Rule 6: it must "
                                  f"read on paper). Restore it, or the document is only machine-legible.")


# ---- a bean the semantic merge left UNCLEAN (MERGE.md §10) ------------------------------------------
# "an unresolved conflict COMMITS (lossless capture) but the seed is marked unclean — the gate WARNS,
# never hard-fails." It never warned: nothing outside dmmerge.py had ever mentioned `merge_open`, so a
# merge that captured a real disagreement landed in history with no signal but a `status:` value. That
# was harmless while the driver was unarmed and is not now. A warning, deliberately — blocking would
# violate the losslessness rule that lets the conflict be committed in the first place.
def _conflicted(node, prefix=''):
    """[(path, record)] for every conflict record in a document — a top-level key, a key inside a map (an agreement's
    `transactions.<key>` when two gardens recorded one transaction with two amounts), or a member of a list — dotted as
    the driver writes `merge_conflicts`. A record's own sides are not searched: they are the values it keeps."""
    out = []
    items = node.items() if isinstance(node, dict) else enumerate(node) if isinstance(node, list) else ()
    for k, v in items:
        if isinstance(node, list):
            at = _member_path(prefix if prefix.count('.') == 0 and '[' not in prefix else None, prefix, k, v)
        else:
            at = f"{prefix}.{k}" if prefix else str(k)
        out += [(at, v)] if _is_conflict(v) else _conflicted(v, at)
    return sorted(out, key=lambda x: x[0])


def check_unclean_merge():
    for _b, _fm in ALL_FM.items():
        _held = _conflicted(_fm)
        _named = _fm.get('merge_conflicts')
        if _named is not None and not (isinstance(_named, list) and all(isinstance(p, str) for p in _named)):
            errors.append(f"{_b}: merge_conflicts is the list of dotted paths that hold a captured disagreement, each "
                          f"written as text — not {_named!r}")
        if _fm.get('merge_open') is not None and _fm['merge_open'] is not True:
            errors.append(f"{_b}: merge_open is `true` while a merge is unsettled, and absent otherwise — not "
                          f"{_fm['merge_open']!r}")
        _bad = [(p, _uncaptured(_fm, p, v)) for p, v in _held]
        _bad = [(p, why) for p, why in _bad if why]
        if _fm.get('merge_open') is True:
            _paths = _named if isinstance(_named, list) else []
            _at = ', '.join(map(str, _paths)) or 'an unrecorded path'
            _still = [p for p, _v in _held if p not in dict(_bad)]
            warns.append(f"{_b}: left UNCLEAN by a semantic merge — {len(_paths)} unresolved conflict(s) at "
                         f"{_at}. Both values are kept; a human picks one, then clears merge_open and "
                         f"merge_conflicts."
                         + (f" The value is still a conflict record at: {', '.join(_still)}." if _still else ""))
        for _p, _why in _bad:
            # Nothing CAPTURED this record: either the marker was cleared while the values were left, the document was
            # mangled, or it was written to stand the gate down. MERGE.md §10 protects a capture the driver declared,
            # and only that.
            errors.append(f"{_b}: holds an unresolved merge at {_p} {_why}. A captured conflict — "
                          f"`{{conflict: [<one value>, <another>]}}` at a path `merge_conflicts` names, with `merge_open: "
                          f"true` — warns and may commit; any other is a document nobody is answering for, and its values "
                          f"are judged by nothing. Pick a value, or restore what the merge wrote (VOCAB merge_conflicts)")


def drawn_edges():
    """term -> {(space, target id)} over EVERY edge the vocabulary declares.

    Deliberately WIDER than `TARGETS_OF`, which sees only a term whose own value is a mapping with a
    `bean`: this walks `schema_edges()`, so an edge reached through an entry or a pointer field counts
    too, and one drawn under `owned_by[legal].owner` is credited to `owned_by`.

    The two phase-3 plies that need it want DIFFERENT slices — one wants bean targets to look up, the
    other only wants to know which relations were drawn at all, mappings included — so each filters
    here at its own call site. Building the walk twice, once per slice, is what let the difference sit
    unstated in two loops that looked like copies of each other.

    A relation with a MALFORMED target still registers its key: it was drawn, whatever it hit. Its
    target is left out of the set, because a non-string id is unhashable and the link pass owns that
    error already — the same reason `_row` refuses to hand a conflict record to a dict lookup.
    """
    out = {}
    for (_is_bean, _base), (_fm, _b) in docs.items():
        for _space, _tgt, _field, _sect in schema_edges(_fm):
            _drawn = out.setdefault(_sect.split('[')[0], set())
            if isinstance(_tgt, str):
                _drawn.add((_space, _tgt))
    return out


# ============================== PHASE 3 — the plies the corpus already justifies ==============================
# Seven checks the vocabulary declares and the gate did not run. Each is a WARNING for one cycle: Part B
# says a signal earns enforcement with evidence, and this garden has already promoted one on fixture
# evidence and had to withdraw it. The journal entry that promotes any of these must carry what it found.


def check_acyclic_per_relation():
    """`schema.dag` per relation — the merged walk cannot say WHICH relation cycled.

    `check_acyclic` walks one graph merged from every dag-declared relation, so its error has to name
    all five. A cycle inside ONE relation is a different and more serious fact than a cycle that only
    exists once five relations are superimposed, and the merged walk cannot tell them apart.
    """
    for _rel in sorted(DAG_TERMS):
        _g = {}
        for (_ib, _base), (_fm, _b) in docs.items():
            for _space, _tgt, _field, _sect in schema_edges(_fm):
                if _sect == _rel and _space == 'bean' and isinstance(_tgt, str):
                    _g.setdefault(_base, []).append(_tgt)
        for _trail in _cycles(_g):
            warns.append(f"cycle in '{_rel}' alone: {' -> '.join(_trail)} — a relation "
                         f"declared acyclic (VOCAB {_rel}.schema.dag) contains a cycle by itself")


def check_inverse_completeness():
    """`inverse_of` in BOTH directions — the existing ply only walks one.

    It checks that A.term -> B implies B.inv -> A. The mirror case, B.inv -> A with no A.term -> B, is
    the same drift seen from the other end and nothing looked for it.
    """
    for _term, _sch in SCHEMAS.items():
        _inv, _card = _inverse_of(_sch)
        if not _inv or _card != 'one-to-one':
            # MANY-TO-ONE HAS NO MIRROR TO CHECK. Many instances point at one type, and the type cannot
            # point back at all of them through a single mapping. Enforcing it warned nine times about a
            # rule that was unsatisfiable from the day it was written (log/pending.md,
            # `inverse-of-assumes-a-bijection`, operator-ratified 2026-08-03).
            continue
        for (_is_bean, _base), (_fm, _b) in docs.items():
            if not _is_bean or not isinstance(_fm.get(_inv), dict):
                continue
            _tgt = _fm[_inv].get('bean')
            if not isinstance(_tgt, str) or (True, _tgt) not in docs:
                continue                              # a dangling or malformed target is reported by link integrity
            _fwd = docs[(True, _tgt)][0].get(_term)
            if not (isinstance(_fwd, dict) and _fwd.get('bean') == _base):
                warns.append(f"{_base}: {_inv} -> '{_tgt}', but {_tgt}.{_term} does not point back to "
                             f"'{_base}' — the mirror of VOCAB {_term}.schema.inverse_of, unchecked "
                             f"until now")


def check_target_obligation_widened():
    """`required_on_targets_of` over EVERY declared edge, not only direct mapping refs.

    `TARGETS_OF` is built from `fm[term]` being a mapping with a `bean` — which misses every edge that
    lives inside an ENTRY or a pointer field. `schema_edges()` already yields all of them, and it is the
    same graph the link pass resolves, so the narrow set was a second and smaller answer to one question.
    """
    _wide = {_rel: {_t for _s, _t in _e if _s == 'bean'} for _rel, _e in drawn_edges().items()}
    for _term, _sch in SCHEMAS.items():
        _rt = _sch.get('required_on_targets_of')
        if not _rt:
            continue
        for _tgt in sorted(_wide.get(_rt, set()) - TARGETS_OF.get(_rt, set())):
            if (True, _tgt) not in docs:
                continue
            if not docs[(True, _tgt)][0].get(_term):
                warns.append(f"{_tgt}: is the target of a {_rt} edge and carries no {_term} — reached "
                             f"through an entry or pointer field, which the narrow target set never saw "
                             f"(VOCAB {_term}.schema.required_on_targets_of)")


def _termination_hint(term, bean):
    """The line that would terminate a chain at `bean`, when the vocabulary pins that bean's form — read from
    the genos's `ownership_form`, the nature's crown branch, and the term's own terminal forms, naming none."""
    fm = ALL_FM.get(bean) or {}
    if (GENE.get(fm.get('genos')) or {}).get('ownership_form') != 'crown':
        return ''
    one_of = form_of(term)['one_of']
    if 'crown' in one_of:
        branch = next((r.get('crown') for r in (registry('natures') or [])
                       if isinstance(r, dict) and r.get('nature') == fm.get('nature')), None)
        return f". A genos:{fm.get('genos')} bean states its own: {term}: {{ legal: {{ crown: {branch} }} }}" if branch else ''
    if 'self' in one_of:
        return f". A genos:{fm.get('genos')} bean answers for itself: {term}: {{ legal: {{ self: true }} }}"
    return ''


def check_chain_termination():
    """MODEL.md: "every chain terminates there". The gate only checked that no chain LOOPS.

    A chain that simply stops — a bean whose owner names a bean that carries no ownership of its own —
    is neither a cycle nor a termination. It is a dangling claim, and it read as fine.

    AN ERROR SINCE 2026-09-17 (human-ratified). It was a warning here while the pre-commit hook's
    test/fast.py refused the same chain, so a new garden was told "0 error(s)" and then had its commit
    refused. One rule, one severity: the gate now says what the hook always enforced, and names the line to
    write when the bean the chain stops at is of a genos whose form is pinned (a person states the crown).
    """
    for _term, _sch in SCHEMAS.items():
        _form = form_of(_term)
        if not on_walk(_sch) or not _form['one_of']:
            continue
        # THE TERM SAYS WHICH FORMS END A CHAIN: `entry_one_of` offers the forms and `entry_ref_fields`
        # names the ones that point at another bean, so the difference IS the terminal set. Listed by hand
        # here (as ('external','crown','self')) and differently in the hook's fast subset (which accepted
        # `contract`), one rule had two answers, and the vocabulary's — `contract` is a ref, so a chain
        # through it continues — was neither of them.
        _terminal = set(_form['one_of']) - set(dmform.ref_attrs(_form, 'entry'))
        if not _terminal:
            continue
        _alt = (_form['alt'] or {}).get('key')
        for (_is_bean, _base), (_fm, _b) in docs.items():
            if not _is_bean:
                continue
            _seen, _at, _hops = set(), _base, 0
            while _at and _hops < 50:
                _node = ALL_FM.get(_at, {}).get(_term)
                if not isinstance(_node, dict):
                    if _at != _base:
                        errors.append(f"{_base}: its {_term} chain reaches '{_at}', which carries no "
                                      f"{_term} at all — the chain neither terminates nor loops "
                                      f"(MODEL.md: every chain terminates){_termination_hint(_term, _at)}")
                    break
                if _alt and _alt in _node:
                    _nxt = (_node[_alt] or {}).get('bean') if isinstance(_node[_alt], dict) else None
                elif any(f in _terminal for _facet in _node.values()
                         if isinstance(_facet, dict) for f in _facet):
                    break                                        # a facet terminates outside or at the axiom
                else:
                    # WHICH FIELD CARRIES THE CHAIN ONWARD is the term's `entry_ref_fields`, not two facet
                    # key names written here — the same declaration the terminal set above is derived from.
                    _refs = dmform.ref_attrs(_form, 'entry')
                    _nxt = next((( _f.get(_r) or {}).get('bean')
                                 for _f in _node.values() if isinstance(_f, dict)
                                 for _r in _refs if isinstance(_f.get(_r), dict)), None)
                if _at in _seen:
                    break                                        # the acyclic ply owns cycles
                _seen.add(_at)
                # a next link that is not an id is the link pass's to refuse, by name; the walk ends there
                _at, _hops = (_nxt if isinstance(_nxt, str) else None), _hops + 1


def check_relation_occupancy():
    """A declared relation no bean instantiates is a blind region, exactly as an unoccupied enum is.

    The reverse gate accounts for every VALUE a term declares. It does not account for the terms that
    ARE relations: the vocabulary can offer an edge nothing has ever drawn, and nothing asks why.

    ONLY THE GARDEN'S OWN RELATIONS (2026-09-17, human-ratified). A garden accounts for the positions IT
    declares — the rule already recorded for Tier-0 vacancies. Warning about every Tier-0 relation a garden
    has not drawn yet greeted a newly germinated garden with nine warnings about edges a small estate may
    never need, and taught it on day one that warnings are noise. Those are information, and
    `bin/dmreview.py` lists them.
    """
    _used = set(drawn_edges())        # every space, mappings included: an edge drawn is an edge drawn
    for _term, _sch in SCHEMAS.items():
        _form = form_of(_term)
        if not (dmform.ref_attrs(_form, 'self') or dmform.ref_attrs(_form, 'entry')):
            continue
        if _term in TIER0_TERMS:
            continue
        if _term not in _used:
            warns.append(f"declared relation '{_term}' is drawn by no bean — either it wants an "
                         f"occupant or it wants a vacancy with a reason (the reverse gate's rule, "
                         f"applied to relations rather than to values)")


# `check_asserted_vs_defaulted_occupancy` STOOD HERE and is deleted (ratified 2026-08-03). It existed to
# report the gap between stated and defaulted occupancy while the reverse gate still counted defaults as
# occupants — a second mechanism watching the first one be wrong. Now that occupancy IS statement, the gap
# it reported cannot open: a position nothing states is simply unoccupied, and `vacancies:` is where an
# unoccupied position accounts for itself. Keeping both would be the two-mechanisms-for-one-rule that the
# entry-form change on 2026-08-03 already deleted a ply for.


# ============================== THE PLIES, IN ORDER ==============================
# Execution order used to be wherever a paragraph happened to sit in this file, and it was correct BY
# ACCIDENT: `ALL_FM` was assigned at line 487 and read at 369, so any reordering raised NameError and the
# dependency was discovered rather than declared. This is the same order, written down, with the reason
# each ply cannot move earlier. A new ply is added here, not wedged between two paragraphs.
PLIES = (
    (check_local_additions,
     "a local addition the standard already carries — named as that, before anything else reads the enum"),
    (check_schema_language,
     "a construct the language does not declare is a rule nothing reads — said before any term is interpreted"),
    (check_merge_identity,
     "a list term's merge identity must name fields its entries carry — the same self-agreement, for merging"),
    (check_value_types,
     "the value types the schemas name are declared in the law"),
    (check_law_extents,
     "an extent the LAW itself writes is judged by the same rule as one on a bean"),
    (check_system_structure,
     "a system's declared shape: what it names exists, nesting ends, a metric level has a unit, restrictions narrow"),
    (check_registry_links,
     "a row that names a row of another registry is resolved, like any other link"),
    (check_retired_terms,
     "a local term named for a retired one says where the retired one went, before anything reads it"),
    (check_retired_owners,
     "a registry is its own enum owner: an overlay of a retired owner term is named, not silently re-declared"),
    (check_retired_vocab,
     "a block, a registry or a value of VOCAB.md the law retired says where it went, before a bean is judged by it"),
    (check_units,
     "a unit's factor is an exact ratio of whole numbers — a rounded one would bend every conversion through it"),
    (check_aspect_sanity,
     "an aspect is a closed figure — check the figure before using its positions"),
    (check_extends_pin,
     "which law is in force; everything downstream is judged under it"),
    (build_docs,
     "loads every document — `docs`, `bean_ids`, `map_ids`. Every ply below reads them"),
    (check_duplicate_keys,
     "reads the raw node graph, because the parsed `docs` above have already lost the first value"),
    (check_text,
     "reads the raw node graph too, where a scalar's style is known: text holds no control character"),
    (check_undeclared_keys,
     "needs `docs`; judged under the terms the pin put in force"),
    (check_id_space_collision,
     "needs both id spaces built"),
    (check_identity_capsule,
     "builds `est_owner` for the ply after it"),
    (check_establishing_anchor_dedup,
     "consumes `est_owner`"),
    (build_all_fm_and_targets,
     "`ALL_FM` and `TARGETS_OF` — read by check_entry and by the term loop"),
    (check_terms,
     "the interpreter: every schema rule, per document"),
    (check_gardens,
     "whose garden, which gardens it knows, what names cross — needs every bean, and the provenance records the terms read"),
    (check_facet_parity,
     "the two arcs of the ownership loop must carry the same facets"),
    (check_inverse_relations,
     "a convenience edge may not drift from the fact it mirrors"),
    (check_vacancy_reasons_declared,
     "sets `VACANCY_REASONS`, which the reverse gate below reads"),
    (check_reverse_gate,
     "every rule must be passed by the objects, or declared vacant with a reason"),
    (check_link_integrity,
     "builds `dep_graph` while resolving every edge"),
    (check_acyclic,
     "walks the `dep_graph` the ply above built"),
    (check_duplicate_authoritative_ip,
     "one owner per address"),
    (check_single_owner_of_a_fact,
     "the same long value stated authoritatively in two beans"),
    (build_staged_constants,
     "`DOCUMENTISH`, `LAW_DOCS`, `FRONT_MATTER_DOCS` — LAW_DOCS is derived from `standing`, so it needs ALL_FM"),
    (check_staged_state,
     "the commit-time half: it reads the index, and refuses if it cannot"),
    (check_unclean_merge,
     "reports a captured conflict, or refuses an undeclared one"),
    (check_acyclic_per_relation,
     "PHASE 3 (warn): names WHICH relation cycled; the merged walk above cannot"),
    (check_inverse_completeness,
     "PHASE 3 (warn): the mirror direction of inverse_of, which the ply above does not walk"),
    (check_target_obligation_widened,
     "PHASE 3 (warn): needs TARGETS_OF built, and widens it to every declared edge"),
    (check_chain_termination,
     "a chain that stops is neither a cycle nor a termination (an error since 2026-09-17: the hook refused it already)"),
    (check_relation_occupancy,
     "PHASE 3 (warn): the reverse gate's rule applied to the relations the GARDEN declares"),
)

def _shaped(msg, width=110):
    """THE FINDING ON ITS OWN LINE, THE REASON BENEATH IT. A finding and its reason were one 300-character line,
    so every narrow view — a terminal, a grep, a quotation in a report — cut it mid-sentence, and the fourth
    cold-start drill quoted a heading the gate had truncated. The text is unchanged: it is broken only at the
    ` — ` that already separates what is wrong from why, and only where the line would not fit."""
    if len(msg) <= width or ' — ' not in msg:
        return msg
    head, _, rest = msg.partition(' — ')
    return head + '\n      — ' + rest


def _about(msg, labels):
    """The documents a finding is reported ON, or an empty set for one about the law or the garden as a whole. Every
    finding about a document begins with what names it — its id, or its path in the garden — and a colon, which is
    where the gate puts the fix; only what a finding begins with is read, never an id it merely mentions."""
    return labels.get(msg.split(':', 1)[0], frozenset()) if ':' in msg else frozenset()


def main(args=None):
    """Run every ply in the declared order, report, and set the exit status.

    Under `if __name__ == '__main__'` so that IMPORTING this file cannot run the gate or kill the
    process: `test/golden.py` spawns it as a subprocess for every negative case it checks, which is
    the only way to observe a gate whose verdict is `sys.exit`, and a suite that wanted to call one
    ply directly had no way to do it. (The vocabulary above still loads at import — it is what the
    module IS, and the same refusal-over-fallback rule governs it either way.)
    """
    args = args or _arguments([])
    named = _named(args['paths']) if args['paths'] else {}
    for _ply, _why in PLIES:
        _ply()
    # ONE FINDING, ONE LINE. Several plies can reach the same fact by different walks — one broken ownership edge
    # printed the same cycle four times — and a repeated line reads as four problems.
    warns[:] = list(dict.fromkeys(warns))
    errors[:] = list(dict.fromkeys(errors))
    shown_w, shown_e, tail = warns, errors, ''
    if named:
        # EVERY DOCUMENT WAS JUDGED, and the findings about the named ones are shown: what names each document in a
        # finding is its id and its path, including a document too broken to load, which `docs` does not hold.
        labels = {}
        for _d, _is_bean in (('beans', True), ('mappings', False)):
            for _f in glob.glob(os.path.join(ROOT, _d, '*.md')):
                _k = (_is_bean, os.path.basename(_f)[:-3])
                for _l in {_k[1], os.path.relpath(_f, ROOT), os.path.relpath(_f, ROOT).replace(os.sep, '/')}:
                    labels[_l] = labels.get(_l, frozenset()) | {_k}
        _mine = lambda m: not _about(m, labels) or bool(_about(m, labels) & set(named))
        shown_w, shown_e = [w for w in warns if _mine(w)], [e for e in errors if _mine(e)]
        _ow, _oe = len(warns) - len(shown_w), len(errors) - len(shown_e)
        _others = len({k for m in warns + errors for k in _about(m, labels)} - set(named))
        tail = (f" — and {_oe} error(s), {_ow} warning(s) in {_others} other document(s), not shown "
                f"(`{_PY} bin/dmcheck.py` shows all)" if _oe or _ow else '')
    # WHAT A DOCUMENT SAID IS PRINTED SPELT OUT. A finding quotes values a bean wrote, and a garden that already holds a
    # control character — or one this run refuses — must not drive the terminal of the person reading the refusal.
    for w in shown_w:  print("WARN ", _shaped(dmparse.said(w)))
    for e in shown_e: print("ERROR", _shaped(dmparse.said(e)))
    # A CLEAN RUN IS ONE LINE. The verdict is set apart from findings above it, and has nothing to be set apart from
    # when there are none: every commit's output stays in an agent's context for the rest of its session.
    _gap = '\n' if shown_w or shown_e else ''
    if named:
        _which = ', '.join(sorted(named.values())[:3]) + (', …' if len(named) > 3 else '')
        print(f"{_gap}{dmparse.said(_product())}: {dmparse.said(_which)} ({len(named)} of {len(docs)} docs), "
              f"{len(shown_e)} error(s), {len(shown_w)} warning(s){tail}")
        return 1 if shown_e else 0
    print(f"{_gap}{dmparse.said(_product())}: {len(docs)} docs, {len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(ARGS))
