"""commit — the rules only a commit can show, judged from the index against the last commit (core spec §12).

The engine judges a bean's statements wherever they stand. What a change says of itself is seen only between two
commits, and is judged here:

  knowing  Every bean the commit changes is named by the journal entry it adds, and the entry's heading is one the clock
           wrote (bin/dmjournal.py registers each heading it writes). A knowing act the commit adds carries that
           heading's moment, which the save (bin/dmsave.py, through dmjournal) writes in place of its `now`: a `now`
           left is a write not saved, and a moment typed there is refused, since only the clock supplies it. A
           statement the commit adds or changes is known by an act of this commit, because whoever wrote it now said it
           now: an old act's moment is older than the statement.
           THE ADOPTION, ONCE (ratified 2026-10-01): the commit that makes the core a garden's language — it moves
           GARDEN.md's `extends` from a std-vocab pin to the core's (`core@<version>`) — and says RULE-CHANGE, which a
           person ratifies, carries the garden's acts translated with the moments history recorded; the gate grants it
           those moments (a heading of the journal as committed, or a commit's own moment), and no other commit. A
           garden receives core/ itself from v0.49.0 on, beside today's gate, so receiving it adopts nothing.
           A MERGE (core/guide/MERGE.md §5, v1 part 3) brings the other side's entries, beans and acts, each judged when
           it was committed. What the merge commit adds of its own is judged: its own entry is the clock's, and names
           each bean the merge made (one that is neither parent's); a statement neither parent holds is known by an act
           at that entry's moment; and an act a parent held with no `of`, given one by the merge, is known as it was.
  ratify   A change to a file of the law (one the law's standing places in `law` or `manifesto`, the core's own law
           files, or one a release keeps by seed/LANGUAGE) is a RULE-CHANGE, ratified by a person, and the entry says
           so. A garden's first commit, its germination, has no HEAD and is exempt: it brings the law, decided by nobody
           here yet (v1 part 4, as today's gate held).
  harm     No private-key block in any file the commit stages, the whole file read; and a statement the commit seals or
           unseals is said in its entry, one line, `- held: <bean> <id> added` or `erased`.
  consent  A bean the commit writes places no person who is not the gardener somewhere in the future: a happening it
           holds wholly after the commit's moment, attended by such a person, keeps its location sealed.
  kept     The journal is appended, never rewritten, and a line the commit adds to it holds no character a reader takes
           for a line break and no template's `(fill in`; a part under series/ is written once; a header key or a
           statement the commit takes out of a bean is named in its entry, none it keeps is emptied, and every bean it
           writes keeps a body. (These were today's gate's, bin/dmcheck.py; v1 took them over, 2026-10-01.)
  layers   A SESSION'S PASS LOG (v1 part 10): a file under captures/passes/ is the log a session bean names in its
           `details` (`pass_log: { <name>: { holds: "file:<path>" } }`), and only grows. A commit that stages one claims
           that session, and owes: each pass the log gains is a pass in the core's form, `{from, to, through, as?,
           metadata}`, that the flow table grants (Law.decide); each said value the commit adds — a role of a statement a
           `say` knows, `<verb>#<id>.<role>` — has a granted pass into it; and a `say` by a person it adds has a pass
           from `words` or `instructions` into its bean. A commit that claims nothing owes none of it.

    findings(root, law, staged=None, garden=None) -> [(rule, where, message)]"""
import collections
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import engine, frame, read  # noqa: E402
from core.law import listed  # noqa: E402
import dmjournal  # noqa: E402 — the register of the headings the clock wrote
import dmpass     # noqa: E402 — the one reader of seed/LANGUAGE, and the one matcher of a path

JOURNAL = 'log/journal.md'
MANIFEST = 'GARDEN.md'             # its `extends` names the law a garden runs: moved to the core, the garden adopts it
RULED = ('law', 'manifesto')
# RULE-CHANGE said, and not denied: "not a RULE-CHANGE" says the opposite (as bin/dmcheck.py reads it)
RULE_CHANGE = re.compile(r'(?<!(?i:not a ))(?<!(?i:not an ))(?<!(?i:not ))(?<!(?i:no ))(?<!(?i:non-))\bRULE-CHANGE\b')


def git(root, *args):
    r = subprocess.run(['git', '-C', root, *args], capture_output=True)
    return r.stdout.decode('utf-8', 'replace') if r.returncode == 0 else None


def staged(root):
    """[(status, path)] the index changes against HEAD: A, M or D, renames read as a deletion and an addition."""
    out = git(root, 'diff', '--cached', '--name-status', '--no-renames', '-z') or ''
    parts = [p for p in out.split('\0') if p]
    return [(parts[i][0], parts[i + 1]) for i in range(0, len(parts) - 1, 2)]


def added_lines(root, path):
    raw = git(root, 'diff', '--cached', '--unified=0', '--', path) or ''
    return [ln[1:] for ln in raw.split('\n') if ln.startswith('+') and not ln.startswith('+++')]


def statements_of(root, ref, path):
    """[(index, verb, roles)] of the bean at `ref:path` (`HEAD` or the index, ''), [] where there is none or it does not
    read: the engine says why it does not."""
    text = git(root, 'show', f"{ref}:{path}")
    if text is None:
        return []
    import dmparse
    head, _body = dmparse.split_front_matter(text)
    try:
        fm = read.loads(head or '') or {}
    except read.Unread:
        return []
    out = []
    for i, s in enumerate(fm.get('statements') or [] if isinstance(fm, dict) else []):
        if isinstance(s, dict) and len(s) == 1 and isinstance(next(iter(s.values())), dict):
            (verb, roles), = s.items()
            out.append((i, verb, roles))
    return out


def pin(root, ref):
    """GARDEN.md's `extends` at `ref` (`HEAD`, or '' for the index), or ''."""
    text = git(root, 'show', f"{ref}:{MANIFEST}")
    if text is None:
        return ''
    import dmparse
    try:
        fm = read.loads(dmparse.split_front_matter(text)[0] or '') or {}
    except read.Unread:
        return ''
    return str(fm.get('extends') or '') if isinstance(fm, dict) else ''


def history(root):
    """The moments history holds: every heading of the journal as last committed, in the one form, and every commit's
    own moment (git's clock reading, `%cI`)."""
    j = git(root, 'show', f"HEAD:{JOURNAL}") or ''
    out = {frame.one_form(ln[3:].split(' · ', 1)[0].strip()) for ln in j.split('\n') if ln.startswith('## ')}
    return out | set((git(root, 'log', '--format=%cI', 'HEAD') or '').split())


def canon(verb, roles):
    return json.dumps({verb: roles}, sort_keys=True, ensure_ascii=False)


def kept_by_release(root, law):
    """The patterns of the files a release keeps: seed/LANGUAGE as staged, a profile's line read for every profile."""
    text = git(root, 'show', ':seed/LANGUAGE')
    if text is None:
        return []
    return dmpass.expand(dmpass.language(text), dmpass.offered(law.std.old))


def ruled(path, law, kept):
    if path.startswith('core/law/'):
        return True
    if any(dmpass.matches(p, path) for p in kept):
        return True
    return any(s.get('layer') in RULED and any(dmpass.matches(h, path) for h in listed(s.get('holds')))
               for s in law.standing)


def merging(root):
    """The other parents of the commit being made, [] where it has one: MERGE_HEAD's, for a merge committed by `git
    commit` (after a conflict, or `git merge --no-commit`); else the GITHEAD_<sha> git sets for the pre-merge-commit hook
    of a merge it commits itself, which runs before MERGE_HEAD is written."""
    p = (git(root, 'rev-parse', '--git-path', 'MERGE_HEAD') or '').strip()
    p = p if not p or os.path.isabs(p) else os.path.join(root, p)
    if p and os.path.isfile(p):
        with open(p, encoding='utf-8') as fh:
            return [ln.strip() for ln in fh if ln.strip()]
    env = [k[8:] for k in os.environ if k.startswith('GITHEAD_') and re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', k[8:])]
    return sorted(h for h in env if git(root, 'cat-file', '-e', h + '^{commit}') is not None)


def findings(root, law, changes=None, garden=None):
    out = []
    changes = staged(root) if changes is None else changes
    if not changes:
        return out
    added = added_lines(root, JOURNAL) if any(p == JOURNAL for _s, p in changes) else []
    # A MERGE (core/guide/MERGE.md §5) brings what the other side committed, judged when it was committed: its entries,
    # its beans, its statements and the acts that knew them. What the merge commit adds of its own is what neither parent
    # holds: its own entry, which is the clock's and names each bean the merge made, and what that bean holds new.
    others = merging(root)
    brought = set()
    for h in others:
        brought |= set((git(root, 'show', f"{h}:{JOURNAL}") or '').split('\n'))
    own = [ln for ln in added if ln not in brought]
    heads = [ln.rstrip() for ln in own if ln.startswith('## ')]
    entry = '\n'.join(added)
    named_by = '\n'.join(own)
    moments = {h[3:].split(' · ', 1)[0].strip() for h in heads}
    stamped = dmjournal.registered(root)
    for h in heads:
        if h not in stamped:
            out.append(('knowing', JOURNAL, f"the heading {h[:60]!r} was not written by the clock in this clone: a heading "
                                            f"is written by `bin/dmsave.py` (or bin/dmjournal.py), never typed"))
    said = ' or '.join(sorted(moments)) or 'none: this commit adds no entry'
    adopting = any(p == MANIFEST for _s, p in changes) and bool(RULE_CHANGE.search(entry)) \
        and pin(root, 'HEAD').startswith('std-vocab@') and pin(root, '').startswith('core@')
    past = history(root) if adopting else set()
    for status, path in changes:
        if not (path.startswith(tuple(d + '/' for d in engine.DOCUMENTS)) and path.endswith('.md')):
            continue
        bid = os.path.basename(path)[:-3]
        blob = (git(root, 'rev-parse', '-q', '--verify', f":{path}") or '').strip()
        if others and any((git(root, 'rev-parse', '-q', '--verify', f"{h}:{path}") or '').strip() == blob for h in others):
            continue                                        # the other side's bean, as it committed it
        if not re.search(r'(?<![\w-])' + re.escape(bid) + r'(?![\w-])', named_by):
            out.append(('knowing', path, (f"merged by this commit, and named by no entry of its own: the merge is "
                                          f"committed with the entry that names what it merged (MERGE.md §5) — "
                                          f"`git merge --no-commit`, then bin/dmsave.py, its entry naming `{bid}`")
                        if others else (f"changed by this commit, and named by no journal entry it adds: save it with "
                                        f"bin/dmsave.py, its entry naming `{bid}`")))
        if status == 'D':
            continue
        new = statements_of(root, '', path)
        old = collections.Counter(canon(v, r) for _i, v, r in statements_of(root, 'HEAD', path)) if status != 'A' \
            else collections.Counter()
        given = set()                                       # a parent's knowing act with no `of`, which a merge gives one
        for h in others:
            theirs = statements_of(root, h, path)
            old |= collections.Counter(canon(v, r) for _i, v, r in theirs)
        if others:
            given = {canon(v, r) for _i, v, r in statements_of(root, 'HEAD', path) + [x for h in others for x in
                     statements_of(root, h, path)] if v in law.knowing and 'of' not in r}
        fresh = []                                          # the statements this commit adds or changes
        # A STATEMENT SEALED is the statement it was, held off git (v1 part 8): its verb and id are HEAD's, and rule
        # harm judges the seal by the entry's `- held:` line; it asks no new act
        was_ids = {(v, r.get('id')) for _i, v, r in statements_of(root, 'HEAD', path) if isinstance(r.get('id'), str)
                   and 'held' not in r} if status != 'A' else set()
        for i, verb, r in new:
            c = canon(verb, r)
            if 'held' in r and (verb, r.get('id')) in was_ids:
                continue
            if old[c]:
                old[c] -= 1
            elif verb in law.knowing and 'of' in r and canon(verb, {k: x for k, x in r.items() if k != 'of'}) in given:
                continue                                    # the merge wrote its `of` (MERGE.md §3): known as it was
            else:
                fresh.append((i, verb, r))
        # THE ACTS OF THIS COMMIT are the knowing acts it adds. Not every act whose moment is this entry's: two saves in
        # one minute share a moment, and an act the last commit holds knows only what it knew then.
        acts = [r for _i, verb, r in fresh if verb in law.knowing]
        for i, verb, r in fresh:
            where = f"{bid}[{i}] {verb}"
            at = r.get('at')
            if at == 'now' or (isinstance(at, list) and 'now' in at):
                out.append(('knowing', where, "`at: now` is still `now`: the save writes the moment in its place — "
                                              "commit with bin/dmsave.py, its entry naming the bean"))
                continue
            if verb in law.knowing:
                # KNOWN IN ANOTHER GARDEN (v1 part 8): its moment is that garden's, and this commit takes it from there
                there = [x for x in listed(at) if isinstance(x, str) and garden is not None and x in garden.beans
                         and garden.beans[x].kind == 'garden']
                if there:
                    if not any(v == 'take' and rr.get('from') == there[0] for _j, v, rr in fresh):
                        out.append(('knowing', where, f"known in {there[0]}, another garden, at {at[0] if isinstance(at, list) else at}: "
                                                      f"what a garden knew comes here only taken from it, in the commit "
                                                      f"that takes it — `take: {{ by: <the gardener>, of: self, from: "
                                                      f"{there[0]}, through: <the proposal's fingerprint>, at: now }}` "
                                                      f"(python3 bin/propose.py take)"))
                    continue
                if at not in moments and not (adopting and at in past):
                    out.append(('knowing', where, f"`at: {at}` is no moment this commit's entry was written at ({said}): "
                                                  f"the moment of a knowing act is the save's — write `now`. Only the "
                                                  f"commit that adopts the core, a RULE-CHANGE, carries history's "
                                                  f"moments" + (", and history holds no such moment" if adopting else "")))
                continue
            sid = r.get('id') if isinstance(r.get('id'), str) else None
            if not any('of' not in rr or (sid is not None and sid in listed(rr.get('of'))) for rr in acts):
                out.append(('knowing', where, "added or changed by this commit, and known by no act it adds: whoever "
                                              "wrote it says, reads, makes or derives it now — a knowing act at `now` "
                                              "whose `of` names it, or one with no `of`, which covers the rest"))
    out += guarded(root, law, changes, entry, added, moments, garden, adopting, merge=bool(others))
    out += claimed(root, law, changes, garden)
    kept = kept_by_release(root, law)
    rc = [p for _s, p in changes if ruled(p, law, kept)]
    # A GARDEN'S FIRST COMMIT, its germination, has no HEAD: it brings the law, and nothing in it was decided by anyone
    # yet (as today's gate held). Its identity is that commit, so it carries no entry to say RULE-CHANGE in.
    germinating = git(root, 'rev-parse', '-q', '--verify', 'HEAD') is None
    if rc and not germinating and not RULE_CHANGE.search(entry):
        out.append(('ratify', ', '.join(rc[:4]) + (' …' if len(rc) > 4 else ''),
                    "a change to the law is a RULE-CHANGE, which a person ratifies: the journal entry this commit adds "
                    "says RULE-CHANGE, and who ratified it"))
    return out


PEM = re.compile('-----BEGIN ' + r'[A-Z0-9 ]*PRIVATE KEY-----')    # in two parts, so that this file never matches it
LINE_BREAKS = '\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029'               # what some readers take for the end of a line
SERIES = 'series/'


def _front(root, ref, path):
    """(front matter, body) of the document at `ref:path`, or (None, None) where there is none or it does not read."""
    text = git(root, 'show', f"{ref}:{path}")
    if text is None:
        return None, None
    import dmparse
    head, body = dmparse.split_front_matter(text)
    try:
        fm = read.loads(head or '') or {}
    except read.Unread:
        return None, None
    return (fm if isinstance(fm, dict) else None), body


def _named(word, entry):
    return re.search(r'(?<![\w-])' + re.escape(str(word)) + r'(?![\w-])', entry) is not None


def guarded(root, law, changes, entry, added, moments, garden=None, adopting=False, merge=False):
    """The commit's halves of `harm`, `consent` and `kept`. The adoption writes every bean anew in statements, and the
    translator's count is its proof that nothing was lost: what it takes out of a bean it need not name."""
    out = []
    for status, path in changes:                              # HARM: no private key, in any file, the whole of it
        if status != 'D':
            text = git(root, 'show', f":{path}")
            if text and PEM.search(text):
                out.append(('harm', path, "a private-key block is staged. Take it out and keep it in your vault, and "
                                          "ROTATE it: a key that reached a commit, even one never pushed, may already "
                                          "be copied. Journal the rotation, never the key"))
    for status, path in changes:                              # KEPT: the journal grows; a series' part stays
        if path == JOURNAL and status == 'M' and not merge:
            was, now = git(root, 'show', f"HEAD:{path}") or '', git(root, 'show', f":{path}") or ''
            if not (now.startswith(was) or (not was.endswith('\n') and now.startswith(was + '\n'))):
                line = next((n for n, (a, b) in enumerate(zip(was.split('\n'), now.split('\n')), 1) if a != b), 0)
                out.append(('kept', f"{path}:{line}", "a line the journal held is changed or taken out: a journal is "
                                                      "appended and never rewritten — restore it, and append what "
                                                      "corrects it as an entry of its own"))
        if path.startswith(SERIES) and status in ('M', 'D'):
            out.append(('kept', path, "a series' part this garden holds is changed or taken out: a part is written once, "
                                      "and what is new is a part of its own"))
    for ln in added:
        odd = sorted({repr(c) for c in ln.rstrip('\r') if c in LINE_BREAKS})
        if odd:
            out.append(('kept', JOURNAL, f"an added line holds {', '.join(odd)}, which some readers take for the end of "
                                         f"a line: a journal line ends only at a newline"))
        if '(fill in' in ln:
            out.append(('kept', JOURNAL, "the entry still holds a template's `(fill in`: say what was done"))
    g = (garden.gardener if garden is not None else None)
    when = None
    for m in moments:
        try:
            when = frame.read(frame.one_form(m), law.std.systems, None).moment
        except frame.Refused:
            pass
    for status, path in changes:
        if status == 'D' or not (path.startswith(tuple(d + '/' for d in engine.DOCUMENTS)) and path.endswith('.md')):
            continue
        bid = os.path.basename(path)[:-3]
        now, body = _front(root, '', path)
        if now is None:
            continue                                          # the engine says why it does not read
        was = _front(root, 'HEAD', path)[0] if status == 'M' else None
        st_now = [(i, v, r) for i, v, r in statements_of(root, '', path)]
        st_was = [(i, v, r) for i, v, r in statements_of(root, 'HEAD', path)] if was is not None else []
        if not (body or '').strip():                          # KEPT: a bean reads on paper
            out.append(('kept', path, "the bean has no body: a bean reads on paper — write what it is, in prose, below "
                                      "its front matter"))
        if was is not None and not adopting:
            for k in sorted(set(was) - set(now)):             # KEPT: what is taken out is said
                if not _named(k, entry):
                    out.append(('kept', path, f"`{k}` is taken out of the bean, and the entry does not say so: name it"))
            for k in sorted(set(was) & set(now)):
                if was[k] not in (None, '', [], {}) and now[k] in (None, '', [], {}):
                    out.append(('kept', path, f"`{k}` is emptied and kept: take it out and say so, or keep what it held"))
            ids_was = {r.get('id') for _i, _v, r in st_was if isinstance(r.get('id'), str)}
            ids_now = {r.get('id') for _i, _v, r in st_now if isinstance(r.get('id'), str)}
            for sid in sorted(ids_was - ids_now):
                if not _named(sid, entry):
                    out.append(('kept', path, f"the statement `{sid}` is taken out, and the entry does not say so: name "
                                              f"it"))
            count = lambda sts, v: sum(1 for _i, x, r in sts if x == v and not isinstance(r.get('id'), str))
            for v in sorted({x for _i, x, _r in st_was}):
                if count(st_now, v) < count(st_was, v) and not _named(v, entry):
                    out.append(('kept', path, f"a `{v}` statement is taken out, and the entry does not say so: name "
                                              f"the verb, or the statement's id"))
        sealed = lambda sts: {r.get('id') for _i, _v, r in sts if 'held' in r and isinstance(r.get('id'), str)}
        for sid, how in [(x, 'added') for x in sorted(sealed(st_now) - sealed(st_was))] + \
                        [(x, 'erased') for x in sorted(sealed(st_was) - sealed(st_now))]:
            if f"- held: {bid} {sid} {how}" not in [ln.strip() for ln in added]:   # HARM: sealing is journalled
                out.append(('harm', path, f"`{sid}` is {'sealed' if how == 'added' else 'unsealed or erased'} in this "
                                          f"commit, and the entry does not say so: add the line `- held: {bid} {sid} "
                                          f"{how}`"))
        if garden is None or when is None or bid not in garden.beans:
            continue
        b = garden.beans[bid]                                 # CONSENT: no future whereabouts of another person
        judge = engine.Judge(law, garden)
        times = [judge._span(x) for _i, v, r in b.items if v == 'be' and 'held' not in r for x in listed(r.get('at'))]
        times = [t for t in times if t]
        others = [x for _i, v, r in b.items if v in ('attend', 'concern') and 'held' not in r
                  for x in judge._beans_in(r.get('by') if v == 'attend' else r.get('of'), b)
                  if x != g and judge._is_person(x)]
        placed = [r for _i, v, r in b.items if v == 'be' and 'held' not in r and r.get('as') == 'location']
        if times and all(lo > when for lo, _hi in times) and others and placed:
            out.append(('consent', path, f"places {', '.join(sorted(set(others)))} somewhere in the future, in git: a "
                                         f"future whereabouts of a person who is not the gardener is held off git "
                                         f"whatever they agreed to — seal its location (bin/dmheld.py put)"))
    return out


# ------------------------------------------------------------------------------------------ a session's pass log (v1 10)
PASSES = 'captures/passes/'
PASS_KEYS = ('from', 'to', 'through', 'metadata')            # and `as`, where a pass into the estate names its act
OID = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})')
WORD = re.compile(r'[a-z][a-z0-9-]*')


def _logs_named(root, garden):
    """{path: session bean} of every log a session bean names in its `details.pass_log`, in the index."""
    beans = garden.beans.values() if garden is not None else []
    out = {}
    for b in beans:
        details = b.header.get('details') if isinstance(b.header.get('details'), dict) else {}
        log = details.get('pass_log') if isinstance(details.get('pass_log'), dict) else {}
        for e in log.values():
            h = e.get('holds') if isinstance(e, dict) else None
            if isinstance(h, str) and h.startswith('file:'):
                out[h[5:]] = b.id
    return out


def _endpoint(e, layer_of, files_held):
    """The layer a pass's `from` or `to` names — `{file}` by the map, `{bean, at?}` the estate, `{garden}` another
    garden, `{layer}` one that holds no files — or a str beginning `!`: why it is none."""
    if not isinstance(e, dict) or not e:
        return f"!{e!r} is none of a pass's ends: {{file}}, {{bean, at?}}, {{garden}} or {{layer}}"
    keys = set(e)
    if keys == {'file'} and isinstance(e['file'], str):
        return layer_of(e['file']) or f"!the file {e['file']!r} stands in no layer, and a pass from it cannot be judged"
    if 'bean' in keys and keys <= {'bean', 'at'} and isinstance(e['bean'], str):
        return 'estate'
    if keys == {'garden'} and isinstance(e['garden'], str):
        return 'other-garden'
    if keys == {'layer'} and isinstance(e['layer'], str):
        return e['layer'] if e['layer'] not in files_held else \
            f"!{e['layer']} holds files: a pass from it names the file, a bean or a garden"
    return f"!{e!r} is none of a pass's ends: {{file}}, {{bean, at?}}, {{garden}} or {{layer}}"


def _metadata_problems(md, law, garden):
    out = []
    for k, v in md.items():
        kind = (law.pass_metadata.get(k) or {}).get('in')
        ok = (kind == 'count' and isinstance(v, int) and not isinstance(v, bool) and v >= 0
              or kind == 'oid' and isinstance(v, str) and OID.fullmatch(v)
              or kind == 'form' and isinstance(v, str) and WORD.fullmatch(v)
              or kind == 'bean' and isinstance(v, str) and (garden is None or v in garden.beans))
        if kind is None:
            out.append(f"metadata `{k}` is no key a logged pass carries (core/law/flows.yaml `metadata`): counts, "
                       f"locators and object ids, never the material")
        elif not ok:
            out.append(f"metadata `{k}`: {v!r} is not a{'n' if kind == 'oid' else ''} {kind}")
    return out


def claimed(root, law, changes, garden=None):
    """LAYERS at a commit: a session's pass log only grows, and a commit that stages one owes what the claim owes."""
    out = []
    logs = [(s, p) for s, p in changes if p.startswith(PASSES)]
    if not logs:
        return out
    named = _logs_named(root, garden)
    m = dmpass.Map.here(root)
    layer_of = lambda p: m.layer_of(p)[0]                                             # noqa: E731
    files_held = {s.get('layer') for s in law.standing if isinstance(s, dict)}     # a layer some file stands in
    methods = set(law.methods) | set(law.knowing) | {'take', 'serve', 'hold'}
    granted = []                                              # (source's layer, its `to`)
    for status, p in logs:
        if p not in named:
            out.append(('layers', p, "a pass log no session bean names: a log is a session's, and says whose — its bean "
                                     "names it in `details`, `pass_log: { requests: { holds: \"file:" + p + "\" } }`"))
            continue
        was, now = git(root, 'show', f"HEAD:{p}") or '', git(root, 'show', f":{p}") or ''
        if status == 'D' or not now.startswith(was):
            out.append(('layers', p, f"the log does not extend its copy at HEAD — a session's pass log only grows: "
                                     f"restore it (`git checkout HEAD -- {p}`) and append"))
            continue
        n0 = was.count('\n')
        for i, line in enumerate(now[len(was):].split('\n')):
            if not line.strip():
                continue
            at = f"{p}:{n0 + i + 1}"
            try:
                ps = json.loads(line)
            except ValueError:
                out.append(('layers', at, "not one JSON object: a log holds one pass to a line"))
                continue
            if not isinstance(ps, dict) or not set(PASS_KEYS) <= set(ps) <= set(PASS_KEYS) | {'as'}:
                out.append(('layers', at, f"a pass is `{{from, to, through, as?, metadata}}` and nothing else"
                                          + (f"; this one holds {sorted(ps)}" if isinstance(ps, dict) else '')
                                          + (" — today's `method` is the core's `through`" if isinstance(ps, dict)
                                             and 'method' in ps else '')))
                continue
            bad = [] if ps['through'] in methods else [f"`through: {ps['through']}` is no method of the flow law and "
                                                        f"no knowing verb"]
            if 'as' in ps and ps['as'] not in law.knowing:
                bad.append(f"`as: {ps['as']}` is no knowing act")
            md = ps['metadata'] if isinstance(ps['metadata'], dict) else None
            bad += ["`metadata` is not a map"] if md is None else _metadata_problems(md, law, garden)
            src, dst = (_endpoint(ps[k], layer_of, files_held) for k in ('from', 'to'))
            bad += [f"{k}: {e[1:]}" for k, e in (('from', src), ('to', dst)) if e.startswith('!')]
            if bad:
                out.append(('layers', at, "not a pass — " + '; '.join(bad)))
                continue
            keeper = 'release' if 'file' in ps['from'] and m.keeper_of(ps['from']['file']) == 'release' else None
            ok, grant, rows = law.decide(src, dst, ps['through'], ps.get('as'), keeper, md.get('party'))
            if not ok:
                why = next((r.get('why') for r in law.flows if r.get('flow') in rows), None)
                out.append(('layers', at, f"{src} → {dst} through {ps['through']}"
                                          + (f" as {ps['as']}" if 'as' in ps else '')
                                          + (f": {', '.join(rows)} {'refuses' if grant != 'ratified' else 'asks a party a garden row grants, and none does for'} it"
                                             if rows else ": no row of the flow table holds it, so it is refused")
                                          + (f" — {why}" if why else '')))
                continue
            granted.append((src, ps['to']))
    if not any(p in named for _s, p in logs):
        return out
    into = {(str(d.get('bean')), str(d.get('at'))) for _s, d in granted if 'at' in d}
    from_person = {str(d.get('bean')) for s, d in granted if s in ('words', 'instructions') and 'bean' in d}
    flows = dmpass.CoreFlows(law)
    ids = set(garden.beans) if garden is not None else set()
    person = lambda x: garden is not None and x in garden.beans and \
        (law.kinds.get(garden.beans[x].kind) or {}).get('rung') == 'reason'                # noqa: E731
    for status, path in changes:                              # what the claim owes, of every bean the commit stages
        if status == 'D' or not (path.startswith(tuple(d + '/' for d in engine.DOCUMENTS)) and path.endswith('.md')):
            continue
        bid = os.path.basename(path)[:-3]
        new = _front(root, '', path)[0] or {}
        old = (_front(root, 'HEAD', path)[0] or {}) if status != 'A' else {}
        for vat, v in sorted(flows.said_values(new, ids) - flows.said_values(old, ids)):
            if (bid, vat) not in into:
                out.append(('layers', path, f"{vat} = {v[:60]} is a said value this claimed commit adds, and no granted "
                                            f"pass in its log has it for destination — a said value is someone's words: "
                                            f"log the pass {{from, to: {{bean: {bid}, at: {vat}}}, through: say, as: say, "
                                            f"metadata}} (the save traces it, bin/save.py)"))
        says = lambda fm: collections.Counter(canon(v, r) for v, r in                                  # noqa: E731
                                              ((next(iter(x)), next(iter(x.values()))) for x in fm.get('statements') or []
                                               if isinstance(x, dict) and len(x) == 1) if v == 'say' and isinstance(r, dict)
                                              and person(r.get('by')))
        if +(says(new) - says(old)) and bid not in from_person:
            out.append(('layers', path, f"a `say` by a person this claimed commit adds has no pass from `words` or "
                                        f"`instructions` into {bid} — a person's word is shown by the pass that "
                                        f"carried it"))
    return out
