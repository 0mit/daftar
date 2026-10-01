"""commit — the rules only a commit can show, judged from the index against the last commit (core spec §12).

The engine judges a bean's statements wherever they stand. What a change says of itself is seen only between two
commits, and is judged here:

  knowing  Every bean the commit changes is named by the journal entry it adds, and the entry's heading is one the clock
           wrote (bin/dmjournal.py registers each heading it writes). A knowing act the commit adds carries that
           heading's moment, which the save (bin/dmsave.py, through dmjournal) writes in place of its `now`: a `now`
           left is a write not saved, and a moment typed there is refused, since only the clock supplies it. A
           statement the commit adds or changes is known by an act of this commit, because whoever wrote it now said it
           now: an old act's moment is older than the statement.
  ratify   A change to a file of the law (one the law's standing places in `law` or `manifesto`, the core's own law
           files, or one a release keeps by seed/LANGUAGE) is a RULE-CHANGE, ratified by a person, and the entry says
           so.

    findings(root, law, staged=None) -> [(rule, where, message)]"""
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
from core import read  # noqa: E402
from core.law import listed  # noqa: E402
import dmjournal  # noqa: E402 — the register of the headings the clock wrote
import dmpass     # noqa: E402 — the one reader of seed/LANGUAGE, and the one matcher of a path

JOURNAL = 'log/journal.md'
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


def findings(root, law, changes=None):
    out = []
    changes = staged(root) if changes is None else changes
    if not changes:
        return out
    added = added_lines(root, JOURNAL) if any(p == JOURNAL for _s, p in changes) else []
    heads = [ln.rstrip() for ln in added if ln.startswith('## ')]
    entry = '\n'.join(added)
    moments = {h[3:].split(' · ', 1)[0].strip() for h in heads}
    stamped = dmjournal.registered(root)
    for h in heads:
        if h not in stamped:
            out.append(('knowing', JOURNAL, f"the heading {h[:60]!r} was not written by the clock in this clone: a heading "
                                            f"is written by `bin/dmsave.py` (or bin/dmjournal.py), never typed"))
    said = ' or '.join(sorted(moments)) or 'none: this commit adds no entry'
    for status, path in changes:
        if not (path.startswith('beans/') and path.endswith('.md')):
            continue
        bid = os.path.basename(path)[:-3]
        if not re.search(r'(?<![\w-])' + re.escape(bid) + r'(?![\w-])', entry):
            out.append(('knowing', path, f"changed by this commit, and named by no journal entry it adds: save it with "
                                         f"bin/dmsave.py, its entry naming `{bid}`"))
        if status == 'D':
            continue
        new = statements_of(root, '', path)
        old = collections.Counter(canon(v, r) for _i, v, r in statements_of(root, 'HEAD', path)) if status != 'A' \
            else collections.Counter()
        fresh = []                                          # the statements this commit adds or changes
        for i, verb, r in new:
            c = canon(verb, r)
            if old[c]:
                old[c] -= 1
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
                if at not in moments:
                    out.append(('knowing', where, f"`at: {at}` is no moment this commit's entry was written at ({said}): "
                                                  f"the moment of a knowing act is the save's — write `now`"))
                continue
            sid = r.get('id') if isinstance(r.get('id'), str) else None
            if not any('of' not in rr or (sid is not None and sid in listed(rr.get('of'))) for rr in acts):
                out.append(('knowing', where, "added or changed by this commit, and known by no act it adds: whoever "
                                              "wrote it says, reads, makes or derives it now — a knowing act at `now` "
                                              "whose `of` names it, or one with no `of`, which covers the rest"))
    kept = kept_by_release(root, law)
    rc = [p for _s, p in changes if ruled(p, law, kept)]
    if rc and not RULE_CHANGE.search(entry):
        out.append(('ratify', ', '.join(rc[:4]) + (' …' if len(rc) > 4 else ''),
                    "a change to the law is a RULE-CHANGE, which a person ratifies: the journal entry this commit adds "
                    "says RULE-CHANGE, and who ratified it"))
    return out
