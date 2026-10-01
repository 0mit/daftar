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
        for i, verb, r in new:
            c = canon(verb, r)
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
