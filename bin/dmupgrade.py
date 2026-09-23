#!/usr/bin/env python3
"""dmupgrade — bring a garden's language up to a daftar release.

    python3 bin/dmupgrade.py <tag>                       # from https://github.com/0mit/daftar
    python3 bin/dmupgrade.py <tag> --from <url-or-path>  # from any clone that carries the tag
    python3 bin/dmupgrade.py <tag> --gardener <id> [--gardener-name "<how they are called>"]   # into std-vocab 21.0

A release is a TAG on the public repository. What a garden receives from it is declared once, in the
release's own `seed/LANGUAGE` — the same file `seed/germinate.py` reads — so a new garden and an upgraded
one cannot disagree about what the language is.

WHAT IT DOES, and nothing else:
  1. refuses a working tree with uncommitted changes, so the upgrade is the only thing in the diff;
  2. fetches the tag into a temporary clone;
  3. copies every file the release's LANGUAGE matches, and removes files the garden's copy of the same
     patterns matched that the release no longer has (a retired tool leaves, rather than lingering);
  4. moves the `extends: std-vocab@<ver>` pin in VOCAB.md and GARDEN.md to the release's vocabulary, and records
     the tag as `daftar_release:` in GARDEN.md — refusing a tag OLDER than the one recorded unless
     --allow-downgrade is given, because an older tag silently removes fixes;
  5. TRANSLATES what the law re-spelled, and says so on the journal entry's `translated:` line: a garden's own
     `local_terms` (bin/dmreform.py), and the beans and the manifest when the vocabulary crosses into 21.0 (below);
  6. re-runs `bin/install.py`, because the hooks or the merge driver may have changed;
  7. appends a RULE-CHANGE journal entry naming the tag, its commit, the vocabulary move and every file;
  8. runs the gate — and if the garden no longer passes under the release (a profile or a value the release
     does not offer, say), puts every file back as it was and says why, unless --keep-on-failure.

CROSSING INTO std-vocab 21.0 the law stopped saying five things a garden may still say, and began asking who keeps
the garden. What can be carried across without a person is carried, and each piece is PROVED before it is written
— the translated front matter must parse to exactly the old one with that one change, and the body be untouched:
  - `scope` leaves every anchor: nothing read it, so nothing is lost;
  - `seeds_from`, `created` and `models` leave GARDEN.md: nothing read them either;
  - a top-level `attributes:` becomes `details:`, or its keys join an existing `details:` — REFUSED, naming the
    keys, where the two hold one key with different values: which stands is a person's decision;
  - the GARDENER is named in GARDEN.md: `--gardener <id>` names an existing person or org bean, or with
    `--gardener-name` plants a new person bean exactly as `seed/germinate.py --gardener` does. Without either the
    upgrade refuses, touching nothing, with the line that fixes it. A garden whose own tool is older than these
    flags hands over to the release's tool (below) and cannot pass them: there the environment carries them,
    DAFTAR_GARDENER and DAFTAR_GARDENER_NAME, and the refusal prints that form.
  What cannot be carried is REFUSED before anything is touched: a bean still carrying `between`, `agreement_ref`,
  `conflict_rule` or `balance` is an agreement a person re-expresses (seed/COOKBOOK.md shows how). With
  --keep-on-failure the rest is applied and those are left, named, for the person.

THE RELEASE'S OWN TOOL DOES THE WORK. When the release carries a different bin/dmupgrade.py, this one hands
over to it (with --garden and --no-delegate) instead of applying a newer release with older logic: v0.4.0
added the release record and the downgrade guard, and a v0.3.1 garden running its own v0.3.1 tool received the
new files and neither of those behaviours. An argument this tool does not know is handed over with the rest, so
the next release's new flags reach the tool that knows them.

IT DOES NOT COMMIT. Adopting a release changes the law this garden is judged by, which is a decision the
garden's own human ratifies: read `git diff`, then `git add -A && git commit`. The journal entry is already
written, so the gate's provenance duty is met by the commit that adopts it.
"""
import argparse, copy, datetime, glob, importlib.util, os, re, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmsafe

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPSTREAM = 'https://github.com/0mit/daftar.git'
PIN = re.compile(r'^(extends: std-vocab@)(\S+)', re.M)
RELEASE = re.compile(r'^daftar_release:.*$', re.M)
SEMVER = re.compile(r'^v?(\d+)\.(\d+)\.(\d+)$')
PY = 'python' if os.name == 'nt' else 'python3'


def run(*args, cwd=None, check=True):
    r = subprocess.run(args, cwd=cwd or ROOT, capture_output=True, text=True)
    if check and r.returncode:
        detail = '\n'.join(s.strip() for s in (r.stdout, r.stderr) if s.strip())
        sys.exit(f"{' '.join(args)} failed:\n{detail or '(no output)'}")
    return r


def read_text(path):
    """(text with '\\n' line ends, the file's own line end) — a file is written back with the ends it had."""
    raw = open(path, encoding='utf-8', newline='').read()
    return raw.replace('\r\n', '\n'), ('\r\n' if '\r\n' in raw else '\n')


def write_text(path, text, nl='\n'):
    with open(path + '.tmp', 'w', encoding='utf-8', newline=nl) as fh:
        fh.write(text)
    os.replace(path + '.tmp', path)


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


def std_fm(root):
    return dmparse.loads(dmparse.read(os.path.join(root, 'seed', 'std-vocab.md'))[0] or '') or {}


def vocab_version(root):
    return str(std_fm(root).get('version'))


def vtuple(v):
    """'21.0' -> (21, 0); an unreadable version reads as the oldest, so a step is never skipped for want of one."""
    n = re.findall(r'\d+', str(v or ''))
    return tuple(int(x) for x in n[:2]) if n else (0, 0)


# ==== THE 21.0 STEP =============================================================================================
# The names below are the OLD spelling, which the new law names only in its `retired:` list, so each is checked
# against the release's own list before anything is touched: a release whose law retired something else is refused,
# never guessed at. What 21.0 retired that no translation may carry (the manifest's other keys, `authority`, the
# facets overlay) is left to the gate, whose refusal says where each went.
STEP_21 = (21, 0)
ANCHOR_DROPPED = ('scope',)                               # read by nothing: dropping it loses nothing
MANIFEST_DROPPED = ('seeds_from', 'created', 'models')    # read by nothing: the journal and git hold what they meant
BEAN_MOVED = ('attributes', 'details')                    # into the one bag for a datum no term holds yet
BEAN_BY_HAND = ('between', 'agreement_ref', 'conflict_rule', 'balance')   # an agreement, re-expressed by a person
AGREEMENT_RECIPE = ("seed/COOKBOOK.md, the recipe for an agreement between people (`parties`, `words`, `clauses`, "
                    "`transactions`)")
GARDENER_ID = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')      # seed/germinate.py's rule for the gardener's id
GARDENER_KINDS = ('person', 'org')                        # "a garden is kept by a person or an organisation"
DOCS = ('beans', 'mappings')                              # where a bean or a mapping lives


def refuse(msg):
    sys.exit(f"REFUSING: {msg}\nNothing was touched.")


def _fm_region(text):
    """(start, end) offsets of the front matter between its two fences."""
    lines = text.splitlines(keepends=True)
    fences = [i for i, l in enumerate(lines) if l.rstrip('\r\n') == '---']
    if len(fences) < 2 or fences[0] != 0:
        return None
    return sum(map(len, lines[:fences[0] + 1])), sum(map(len, lines[:fences[1]]))


# A value in a YAML line: a quoted string, or a plain scalar that stops before `,` `}` `]` or a comment.
_VAL = r'(?:"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\n]|\'\')*\'|[^\s,{}\[\]#"\'][^,{}\[\]#\n]*?)'


def _flow_maps(s):
    """(start, end) of every flow mapping `{…}` in s, nested ones too, skipping what is quoted or a comment."""
    out, stack, q, i = [], [], None, 0
    while i < len(s):
        c = s[i]
        if q:
            if c == q and s[i - 1] != '\\':
                q = None
        elif c in '"\'' and (i == 0 or s[i - 1] in ' \t\n,[{:'):
            q = c
        elif c == '#' and (i == 0 or s[i - 1] in ' \t\n'):
            i = s.find('\n', i)                       # a comment runs to the line's end; its braces are prose
            if i < 0:
                break
        elif c == '{':
            stack.append(i)
        elif c == '}' and stack:
            out.append((stack.pop(), i + 1))
        i += 1
    return out


def drop_anchor_key(text, key):
    """`key` out of every anchor, inside the `identity:` block only — a `scope:` elsewhere in a bean is another fact.
    A flow anchor `{ …, scope: global, … }` loses the pair, found by dmsafe's quote-aware reading of the mapping; a
    block anchor loses the line."""
    try:
        s, e = dmsafe.top_level_span(text, 'identity')
    except dmsafe.UnsafeEdit:
        return text
    blk, cuts = text[s:e], []
    for lo, hi in _flow_maps(blk):
        pairs = dmsafe._flow_pairs(blk, lo, hi)
        for n, (k, ks, vs) in enumerate(pairs):
            if k != key:
                continue
            if n:                                       # `, key: value` after the pair before it
                cuts.append((pairs[n - 1][2][1], vs[1]))
            elif len(pairs) > 1:                        # `key: value, ` before the pair after it
                cuts.append((ks[0], pairs[1][1][0]))
            else:
                cuts.append((ks[0], vs[1]))
    for a, b in sorted(cuts, reverse=True):
        blk = blk[:a] + blk[b:]
    blk = re.sub(r'(?m)^[ \t]+' + re.escape(key) + r'[ \t]*:[ \t]*' + _VAL + r'[ \t]*(?:#[^\n]*)?\n', '', blk)
    return text[:s] + blk + text[e:]


def _children(block, mapping):
    """A top-level mapping's block as (its key line, [its entries' lines, relative to their own indent], indent),
    or None for a form this translation does not rewrite. A block mapping's lines are kept verbatim, comments and
    all; a one-line flow mapping is spelled out as block lines, each value's own text kept."""
    lines = block.splitlines(keepends=True)
    m = re.match(r'^([A-Za-z_][\w-]*)[ \t]*:[ \t]*(.*?)[ \t]*$', lines[0].rstrip('\n'))
    if not m:
        return None
    rest = m.group(2)
    if rest == '' or rest.startswith('#'):
        kids = lines[1:]
        solid = [l for l in kids if l.strip()]
        ind = min((len(l) - len(l.lstrip(' ')) for l in solid), default=0)
        if solid and ind == 0:
            return None
        return lines[0].rstrip('\n'), [l[ind:] if l.strip() else l for l in kids], ind
    if rest.startswith('{') and len(lines) == 1 and '}' in rest:
        flow, trailing = rest[:rest.rfind('}') + 1], rest[rest.rfind('}') + 1:].strip()
        if trailing and not trailing.startswith('#'):
            return None
        pairs = dmsafe._flow_pairs(flow, 0, len(flow))
        if [p[0] for p in pairs] != [str(k) for k in mapping]:
            return None
        head = f"{m.group(1)}:" + (f"  {trailing}" if trailing else '')
        return head, [f"{k}: {flow[v[0]:v[1]]}\n" for k, _ks, v in pairs], None
    return None


def _without(kids, keys):
    """Entry lines with the entries for `keys` left out (an entry runs to the next line at its own indent)."""
    out, skip = [], False
    for l in kids:
        if l.strip() and not l.startswith((' ', '#')):
            skip = any(re.match(rf'^{re.escape(str(k))}[ \t]*:', l) for k in keys)
        if not skip:
            out.append(l)
    return out


def move_attributes(text, fm):
    """(new text, None), or (text, why not). `attributes:` is renamed `details:` where there is none; otherwise its
    entries join the existing `details:`. A key the two hold with different values is a person's decision."""
    old, new = BEAN_MOVED
    if new not in fm:
        lo_hi = _fm_region(text)
        head = text[lo_hi[0]:lo_hi[1]] if lo_hi else ''
        hits = re.findall(rf'(?m)^{old}[ \t]*:', head)
        if len(hits) != 1:
            return text, f"`{old}:` is written {len(hits)} times at the top level — move it into `{new}:` by hand"
        head = re.sub(rf'(?m)^{old}([ \t]*:)', rf'{new}\1', head, count=1)
        return text[:lo_hi[0]] + head + text[lo_hi[1]:], None
    a, d = fm.get(old), fm.get(new)
    if not isinstance(a, dict) or not isinstance(d, dict):
        return text, f"`{old}` and `{new}` are not both mappings — move the one into the other by hand"
    clash = sorted(str(k) for k in a if k in d and a[k] != d[k])
    if clash:
        return text, (f"`{old}` and `{new}` both hold {', '.join(clash)}, with different values — which stands is a "
                      f"person's decision: keep one in `{new}`, remove it from `{old}`, and run this again")
    try:
        a_s, a_e = dmsafe.top_level_span(text, old)
        d_s, d_e = dmsafe.top_level_span(text, new)
    except dmsafe.UnsafeEdit as e:
        return text, f"{e} — move `{old}` into `{new}` by hand"
    ac, dc = _children(text[a_s:a_e], a), _children(text[d_s:d_e], d)
    if not ac or not dc:
        return text, f"`{old}` or `{new}` is written in a form this translation does not rewrite — move it by hand"
    ind = dc[2] or ac[2] or 2
    kids = dc[1] + _without(ac[1], [k for k in a if k in d])       # a key said twice, alike, is kept once
    block = dc[0] + '\n' + ''.join((' ' * ind + l) if l.strip() else l for l in kids)
    if a_s < d_s:
        return text[:a_s] + text[a_e:d_s] + block + text[d_e:], None
    return text[:d_s] + block + text[d_e:a_s] + text[a_e:], None


def _parse(text):
    head, body = dmparse.split_front_matter(text)
    fm = dmparse.loads(head) if head is not None else None
    return (fm, body) if isinstance(fm, dict) else (None, body)


def _swap_leaves(node, table):
    """The same structure with every string leaf found in `table` replaced by its value (keys are left alone)."""
    if isinstance(node, dict):
        return {k: _swap_leaves(v, table) for k, v in node.items()}
    if isinstance(node, list):
        return [_swap_leaves(v, table) for v in node]
    return table.get(node, node) if isinstance(node, str) else node


def plan_doc(path):
    """What the 21.0 step would write to one bean or mapping: (new text or None, line end, facts, problems).
    Each change is PROVED before it is kept: the new front matter must parse to exactly the old one with that change,
    and the body be unchanged. A change that cannot be proved is not made; the problem says so."""
    text, nl = read_text(path)
    rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
    try:
        fm, body = _parse(text)
    except Exception:
        return None, nl, {}, []                  # a document that does not parse: the gate names it, not this
    if fm is None:
        return None, nl, {}, []
    facts, problems, cur, want = {'scope': 0, 'moved': False}, [], text, copy.deepcopy(fm)

    def prove(new_text, expected, what):
        try:
            nfm, nbody = _parse(new_text)
        except Exception as e:
            nfm, nbody = None, f'{e}'
        if nfm == expected and nbody == body:
            return True
        problems.append(f"{rel}: {what} could not be done without changing something else, so it was not done — "
                        f"do it by hand")
        return False

    ident = fm.get('identity') if isinstance(fm.get('identity'), dict) else {}
    anchors = [x for x in (ident.get('anchors') or []) if isinstance(x, dict)]
    for key in ANCHOR_DROPPED:
        n = sum(1 for x in anchors if key in x)
        if n:
            exp = copy.deepcopy(want)
            for x in exp['identity']['anchors']:
                if isinstance(x, dict):
                    x.pop(key, None)
            new_text = drop_anchor_key(cur, key)
            if prove(new_text, exp, f"removing `{key}` from its {n} anchor(s)"):
                cur, want, facts['scope'] = new_text, exp, facts['scope'] + n
    if BEAN_MOVED[0] in fm:
        new_text, why = move_attributes(cur, want)
        if why:
            problems.append(f"{rel}: {why}")
        else:
            exp = copy.deepcopy(want)
            _a = exp.pop(BEAN_MOVED[0])
            exp[BEAN_MOVED[1]] = {**exp[BEAN_MOVED[1]], **_a} if BEAN_MOVED[1] in exp else _a
            if prove(new_text, exp, f"moving `{BEAN_MOVED[0]}` into `{BEAN_MOVED[1]}`"):
                cur, want, facts['moved'] = new_text, exp, True
                # A POINTER FOLLOWS WHAT IT POINTS AT. `<section>.<key>` names a field on this same bean, and the gate
                # resolves it, so a pointer left at `attributes.<key>` would dangle after the move.
                keys = list(_a) if isinstance(_a, dict) else []
                ptrs = {f"{BEAN_MOVED[0]}.{k}": f"{BEAN_MOVED[1]}.{k}" for k in keys}
                exp = _swap_leaves(copy.deepcopy(want), ptrs)
                if keys and exp != want:
                    alt = '|'.join(re.escape(str(k)) for k in keys)
                    new_text = re.sub(r'(?m)([:\[,-][ \t]*)(["\']?)' + re.escape(BEAN_MOVED[0]) + r'\.(' + alt + r')\2'
                                      r'(?=[ \t]*(?:[,}\]#]|$))', lambda m: f"{m.group(1)}{m.group(2)}{BEAN_MOVED[1]}."
                                      f"{m.group(3)}{m.group(2)}", cur)
                    if prove(new_text, exp, f"following the pointers to `{BEAN_MOVED[0]}.<key>` into `{BEAN_MOVED[1]}`"):
                        cur, want = new_text, exp
    held = [k for k in BEAN_BY_HAND if k in fm]
    if held:
        problems.append(f"{rel}: carries {', '.join(f'`{k}`' for k in held)} — an agreement between parties is "
                        f"re-expressed by a person, not by a translation: {AGREEMENT_RECIPE}")
    return (cur if cur != text else None), nl, facts, problems


def kind_of(path):
    try:
        return (_parse(read_text(path)[0])[0] or {}).get('kind')
    except Exception:
        return None                              # a bean that does not parse: the gate names it


def plan_manifest(text, gardener):
    """GARDEN.md in 21.0's spelling — the retired keys out, the gardener named — or (None, why not)."""
    fm, body = _parse(text)
    if fm is None:
        return None, "GARDEN.md has no readable front matter"
    exp, cur = copy.deepcopy(fm), text
    for k in MANIFEST_DROPPED:
        if k in fm:
            try:
                s, e = dmsafe.top_level_span(cur, k)
            except dmsafe.UnsafeEdit as err:
                return None, f"GARDEN.md: {err}"
            cur = cur[:s] + cur[e:]
            exp.pop(k)
    line = f"gardener: {gardener}                      # the person who keeps this garden: its first bean"
    if not _fm_region(cur):
        return None, "GARDEN.md does not open with its `---` fence — name the gardener by hand"
    lo, hi = _fm_region(cur)
    head = cur[lo:hi]
    if re.search(r'(?m)^gardener[ \t]*:', head):
        head = re.sub(r'(?m)^gardener[ \t]*:.*$', line, head, count=1)
    elif re.search(r'(?m)^daftar_release[ \t]*:', head):
        head = re.sub(r'(?m)^daftar_release[ \t]*:.*$', lambda m: m.group(0) + '\n' + line, head, count=1)
    else:
        head = re.sub(r'(?m)^extends[ \t]*:.*$', lambda m: m.group(0) + '\n' + line, head, count=1)
    cur = cur[:lo] + head + cur[hi:]
    exp['gardener'] = gardener
    nfm, nbody = _parse(cur)
    if nfm != exp or nbody != body:
        return None, "GARDEN.md could not be rewritten without changing something else — name the gardener by hand"
    return cur, None


class Step21:
    """The translation into std-vocab 21.0: planned, and refused if it must be, before any file is touched."""

    def __init__(self, rel, tag, source, gardener, gardener_name, keep, delegated):
        self.rel, self.tag, self.source, self.keep = rel, tag, source, keep
        self.gardener, self.gardener_name, self.delegated = gardener, gardener_name, delegated
        self.plans, self.problems, self.plant, self.created = {}, [], None, []

    def fix_line(self):
        """The one line that names the gardener, in the form the garden's own tool can pass on."""
        frm = f" --from {self.source}" if self.source != UPSTREAM else ''
        own = os.path.join(ROOT, 'bin', 'dmupgrade.py')
        # this garden's own tool is older than the flags and hands over to this one: the environment carries them
        old = self.delegated and os.path.isfile(own) and '--gardener' not in open(own, encoding='utf-8').read()
        if not old:
            return f'{PY} bin/dmupgrade.py {self.tag}{frm} --gardener <id> [--gardener-name "<how they are called>"]'
        if os.name == 'nt':
            return (f'$env:DAFTAR_GARDENER = "<id>"; [$env:DAFTAR_GARDENER_NAME = "<how they are called>";] '
                    f'python bin\\dmupgrade.py {self.tag}{frm}')
        return f'DAFTAR_GARDENER=<id> [DAFTAR_GARDENER_NAME="<how they are called>"] python3 bin/dmupgrade.py {self.tag}{frm}'

    def plan(self):
        law = {(str(r.get('at')), str(r.get('name'))) for r in (std_fm(self.rel).get('retired') or []) if isinstance(r, dict)}
        said = ([('anchor', k) for k in ANCHOR_DROPPED] + [('manifest', k) for k in MANIFEST_DROPPED] +
                [('bean', BEAN_MOVED[0])] + [('bean', k) for k in BEAN_BY_HAND])
        if [s for s in said if s not in law]:
            refuse(f"{self.tag}'s law does not retire {', '.join(f'{a} `{n}`' for a, n in said if (a, n) not in law)}, "
                   f"which this tool's 21.0 step translates. The step and the law disagree; neither is guessed at.")
        self.plan_gardener()
        for sub in DOCS:
            for path in sorted(glob.glob(os.path.join(ROOT, sub, '*.md'))):
                new, nl, facts, problems = plan_doc(path)
                self.problems += problems
                if new is not None:
                    self.plans[path] = (new, nl, facts)
        gtext, _nl = read_text(os.path.join(ROOT, 'GARDEN.md'))
        _g, why = plan_manifest(gtext, self.gardener)
        if why:
            self.problems.append(why)
        if self.problems and not self.keep:
            refuse(f"crossing into std-vocab 21.0, {len(self.problems)} thing(s) are a person's to do, not a "
                   f"translation's:\n" + '\n'.join('  - ' + p for p in self.problems) +
                   "\nDo them and commit, then run this again — or pass --keep-on-failure to apply the rest and "
                   "leave these, named, for the person.")

    def plan_gardener(self):
        gpath = os.path.join(ROOT, 'GARDEN.md')
        named = (_parse(read_text(gpath)[0])[0] or {}).get('gardener') if os.path.isfile(gpath) else None
        gid, name = self.gardener, self.gardener_name
        if named and gid and str(named) != gid:
            refuse(f"GARDEN.md already names the gardener '{named}', and --gardener says '{gid}'. Changing who keeps "
                   f"a garden is the gardener's decision, never an upgrade's.")
        gid = gid or (str(named) if named else None)
        keepers = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ROOT, 'beans', '*.md'))
                         if kind_of(p) in GARDENER_KINDS)
        if not gid:
            refuse(f"std-vocab 21.0 asks who keeps this garden — its GARDENER, a person or an organisation it holds, "
                   f"named in GARDEN.md — and this garden names none. Ask the person, then:\n  {self.fix_line()}\n"
                   f"<id> is an existing person or org bean" + (f" (here: {', '.join(keepers[:12])}"
                   + (', …' if len(keepers) > 12 else '') + ")" if keepers else '') +
                   "; with a name, a new person bean is planted for them, as seed/germinate.py --gardener plants one.")
        if not GARDENER_ID.match(gid):
            refuse(f"--gardener takes a bean id: kebab-case, e.g. --gardener sam (got '{gid}')")
        path = os.path.join(ROOT, 'beans', gid + '.md')
        if os.path.isfile(path):
            kind = kind_of(path)
            if kind not in GARDENER_KINDS:
                refuse(f"'{gid}' is a {kind}; a garden is kept by a person or an organisation"
                       + (f" (here: {', '.join(keepers[:12])})" if keepers else ''))
            if name:
                refuse(f"'{gid}' is already a bean of this garden, and --gardener-name plants a NEW one. "
                       f"Pass --gardener {gid} alone.")
        elif not name:
            refuse(f"'{gid}' is no bean of this garden. Name an existing person or org bean"
                   + (f" ({', '.join(keepers[:12])})" if keepers else '') +
                   f", or add --gardener-name \"<how they are called>\" to plant a new person bean for them.")
        else:
            gpy = os.path.join(self.rel, 'seed', 'germinate.py')
            spec = importlib.util.spec_from_file_location('daftar_germinate', gpy)
            mod = importlib.util.module_from_spec(spec)
            sys.dont_write_bytecode = True       # the release's seed is read, not left with a cache beside it
            spec.loader.exec_module(mod)
            if not hasattr(mod, 'gardener_bean'):
                refuse(f"{self.tag}'s seed/germinate.py plants no gardener, so there is no bean to plant here the way "
                       f"a new garden plants one. Write the person bean by hand and pass --gardener alone.")
            # EXACTLY as germinate plants one: the release's own function, not a second copy of its text.
            self.plant = (path, mod.gardener_bean(gid, name, datetime.date.today().isoformat()))
        self.gardener = gid

    def apply(self):
        """Writes what was planned; returns the `translated:` text and the ids of the documents it touched."""
        touched, scope, with_scope, moved = [], 0, [], []
        for path, (new, nl, facts) in self.plans.items():
            write_text(path, new, nl)
            ident = self._id(path)
            touched.append(ident)
            if facts['scope']:
                scope += facts['scope']
                with_scope.append(ident)
            if facts['moved']:
                moved.append(ident)
        if self.plant:
            path, text = self.plant
            os.makedirs(os.path.dirname(path), exist_ok=True)
            write_text(path, text)
            self.created.append(os.path.relpath(path, ROOT).replace(os.sep, '/'))
        gpath = os.path.join(ROOT, 'GARDEN.md')
        gtext, gnl = read_text(gpath)
        gone = [k for k in MANIFEST_DROPPED if k in (_parse(gtext)[0] or {})]
        new, why = plan_manifest(gtext, self.gardener)
        if new is not None:
            write_text(gpath, new, gnl)
        elif why not in self.problems:
            self.problems.append(why)
        parts = []
        if scope:
            parts.append(f"`scope` removed from {scope} anchor(s) in {', '.join(with_scope)} (read by nothing, so nothing is lost)")
        if gone and new is not None:
            parts.append(f"GARDEN.md: {', '.join(f'`{k}`' for k in gone)} removed (read by nothing)")
        if moved:
            parts.append(f"`{BEAN_MOVED[0]}` moved into `{BEAN_MOVED[1]}` in {', '.join(moved)}")
        if new is not None:
            gid = f"[[{self.gardener}]]"
            parts.append(f"gardener {gid} " + ("planted — a person bean, as seed/germinate.py --gardener plants one — and "
                                              if self.plant else "") + "named in GARDEN.md")
            if self.plant:
                touched.append(gid)
        if self.problems:
            parts.append("LEFT FOR A PERSON: " + '; '.join(self.problems))
        return 'std-vocab 21.0 — ' + '; '.join(parts or ['nothing to translate']), touched

    @staticmethod
    def _id(path):
        base = os.path.basename(path)[:-3]
        return f"[[{base}]]" if os.path.basename(os.path.dirname(path)) == 'beans' else f"mappings/{base}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tag', help='the release tag, e.g. v0.3.0')
    ap.add_argument('--from', dest='src', default=UPSTREAM, help=f'repository URL or path (default {UPSTREAM})')
    ap.add_argument('--allow-downgrade', action='store_true', help='adopt a tag older than the one GARDEN.md records')
    ap.add_argument('--garden', help='the garden to upgrade (default: the one this tool lives in)')
    ap.add_argument('--keep-on-failure', action='store_true', help='leave the files in place when the gate fails, to repair by hand')
    ap.add_argument('--gardener', help='crossing into std-vocab 21.0: the id of the person or org bean who keeps this garden '
                                       '(or DAFTAR_GARDENER in the environment)')
    ap.add_argument('--gardener-name', help='with --gardener, plants a new person bean with this name '
                                            '(or DAFTAR_GARDENER_NAME in the environment)')
    ap.add_argument('--no-delegate', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('--recorded-source', help=argparse.SUPPRESS)
    a, unknown = ap.parse_known_args()
    global ROOT
    if a.garden:
        ROOT = os.path.abspath(a.garden)
    source = a.recorded_source or a.src
    gardener = a.gardener or os.environ.get('DAFTAR_GARDENER') or None
    gardener_name = a.gardener_name or os.environ.get('DAFTAR_GARDENER_NAME') or None

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
            if a.gardener:
                args += ['--gardener', a.gardener]
            if a.gardener_name:
                args += ['--gardener-name', a.gardener_name]
            return subprocess.run(args + unknown).returncode
        if unknown:
            ap.error(f"unrecognized arguments: {' '.join(unknown)}")

        if vocab_version(rel) in ('None', ''):
            sys.exit(f"REFUSING: {a.tag} carries no readable `version:` in seed/std-vocab.md — nothing to pin to.")
        before = vocab_version(ROOT)
        # THE 21.0 STEP IS PLANNED FIRST, while every file is still as it was, so a refusal touches nothing.
        step21 = None
        if vtuple(before) < STEP_21 <= vtuple(vocab_version(rel)):
            step21 = Step21(rel, a.tag, source, gardener, gardener_name, a.keep_on_failure, a.no_delegate)
            step21.plan()
        want = expand(rel, patterns(rel))
        have = expand(ROOT, patterns(ROOT)) if os.path.isfile(os.path.join(ROOT, 'seed', 'LANGUAGE')) else set()

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
            text, nl = read_text(path)
            pins = PIN.findall(text)
            if len(pins) != 1:
                sys.exit(f"REFUSING to guess: {doc} carries {len(pins)} `extends: std-vocab@` pins, expected 1. "
                         f"The files above are already copied — `git checkout -- .` undoes them.")
            if pins[0][1] != after:
                write_text(path, PIN.sub(rf'\g<1>{after}', text, count=1), nl)
                repinned.append(doc)

        # THE GARDEN'S OWN TERMS ARE TRANSLATED, NEVER REWRITTEN BY HAND (13.0). When a release changes how the law
        # is SPELLED, a garden's `local_terms` are in the old spelling and the new gate refuses them. The release
        # ships the translator; it is a pure function of each term, it proves per term that the form it reads is
        # unchanged, and it leaves the file alone when it cannot. A refusal surfaces through the gate below, which
        # then puts everything back.
        translated, reform = [], os.path.join(ROOT, 'bin', 'dmreform.py')
        if os.path.isfile(reform):
            _r = run(sys.executable, reform, os.path.join(ROOT, 'VOCAB.md'), check=False)
            _out = (_r.stdout + _r.stderr).strip()
            if _r.returncode != 0:
                translated.append('REFUSED — ' + _out.replace(ROOT + os.sep, ''))
            elif 'term(s) rewritten' in _out and ': 0 term' not in _out and 'rewritten —' in _out:
                translated.append('VOCAB.md local_terms — ' + _out.split('rewritten —', 1)[1].strip())
                if 'VOCAB.md' not in changed:
                    changed.append('VOCAB.md (translated)')

        gpath = os.path.join(ROOT, 'GARDEN.md')
        gtext, gnl = read_text(gpath)
        gline = f'daftar_release: "{a.tag}"  # the daftar release this garden runs; bin/dmupgrade.py moves it'
        if recorded_release() != a.tag:
            if RELEASE.search(gtext):
                gtext = RELEASE.sub(gline, gtext, count=1)
            else:
                # after the WHOLE pin line: inserting after the match split the line and moved its comment
                gtext = re.sub(r'^extends: std-vocab@.*$', lambda m: m.group(0) + '\n' + gline, gtext, count=1, flags=re.M)
            write_text(gpath, gtext, gnl)
            repinned.append('GARDEN.md daftar_release')

        beans = []
        if step21:
            _t, beans = step21.apply()
            translated.append(_t)
            added += step21.created

        if not (changed or added or removed or repinned):
            print(f"nothing to do: this garden's language already equals {a.tag} ({sha[:12]}).")
            return 0

        # "applied" when either side is unknown: a garden that records no release cannot be told which way it moved.
        verb = ('applied' if not (cur_v and new_v) else
                'downgraded' if tuple(map(int, new_v.groups())) < tuple(map(int, cur_v.groups())) else 'upgraded')
        install()
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
                 f"- translated: {'; '.join(translated) or 'none'}",
                 "- why: (fill in — what this release brings that this garden adopts)",
                 f"- beans: {', '.join(beans) or 'none'}"]
        jpath = os.path.join(ROOT, 'log', 'journal.md')
        with open(jpath, 'a', encoding='utf-8', newline=read_text(jpath)[1]) as j:
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
            install()
            errs = [l for l in gate.stdout.splitlines() if l.startswith('ERROR')]
            errs[:0] = ['dmreform ' + t for t in translated if t.startswith('REFUSED')]
            print(f"NOT {verb.upper()}: under {a.tag} this garden fails its own gate, so every file was put back as it was.\n"
                  + '\n'.join(errs[:12]) + ('\n…' if len(errs) > 12 else '') +
                  "\nFix what these name (or pass --keep-on-failure to repair by hand), then run this again.")
            return 1
        print(f"{verb} to {a.tag} ({sha[:12]}): std-vocab {before} -> {after}; "
              f"{len(changed)} changed, {len(added)} added, {len(removed)} removed, {len(repinned)} repinned.")
        if step21:
            print(f"translated: {translated[-1]}")
        print((gate.stdout.strip().splitlines() or ['(the gate printed nothing)'])[-1])
        print("\nNOT COMMITTED. Read `git diff`, complete the journal entry's two `fill in` fields, then\n"
              "  git add -A && git commit\n"
              "To abandon: git checkout -- ." + (f" && rm {' '.join(added)}" if added else ""))
        return 0 if gate.returncode == 0 else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def install():
    """The release's installer, run by this interpreter: hooks and the merge driver may have changed. `sh` is not a
    given on Windows; bin/install.py is the one installer, and install.sh only hands over to it."""
    if os.path.isfile(os.path.join(ROOT, 'bin', 'install.py')):
        run(sys.executable, os.path.join(ROOT, 'bin', 'install.py'), check=False)
    elif shutil.which('sh'):
        run('sh', os.path.join(ROOT, 'bin', 'install.sh'), check=False)   # a release from before install.py


if __name__ == '__main__':
    sys.exit(main())
