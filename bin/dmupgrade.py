#!/usr/bin/env python3
"""dmupgrade — bring a garden's language up to a daftar release.

    python3 bin/dmupgrade.py <tag>                       # from https://github.com/0mit/daftar
    python3 bin/dmupgrade.py <tag> --from <url-or-path>  # from any clone that carries the tag
    DAFTAR_GARDENER=<id> python3 bin/dmupgrade.py <tag>  # into std-vocab 21.0, from a garden at any release
    python3 bin/dmupgrade.py <tag> --gardener <id>       # the same, where the garden's own tool knows the flag

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
     `local_terms` (bin/dmreform.py), the beans and the manifest when the vocabulary crosses into 21.0, the beans
     and VOCAB.md when it crosses into 22.0, and VOCAB.md and what a bean or a mapping places when it crosses into
     23.1 (all below);
  6. re-runs `bin/install.py`, because the hooks or the merge driver may have changed;
  7. appends a RULE-CHANGE journal entry naming the tag, its commit, the vocabulary move and every file;
  8. runs the gate — and if the garden no longer passes under the release (a profile or a value the release
     does not offer, say), puts every file back as it was and says why, unless --keep-on-failure. Anything that
     stops it between the first copy and the gate's verdict — a file another program holds open — puts every
     file back too, whatever the flags.
A file is written back with the line ends and the byte-order mark it was found with.

CROSSING INTO std-vocab 21.0 the law stopped saying five things a garden may still say, and began asking who keeps
the garden. What can be carried across without a person is carried, and each piece is PROVED before it is written
— the translated front matter must parse to exactly the old one with that one change, and the body be untouched:
  - `scope` leaves every anchor: nothing read it, so nothing is lost;
  - `seeds_from`, `created` and `models` leave GARDEN.md: the law reads none of them, and the journal entry quotes
    what each said — the gardens `seeds_from` named are a person's to record as `garden` beans, where still known;
  - a top-level `attributes:` becomes `details:`, or its keys join an existing `details:` — REFUSED, naming the
    keys, where the two hold one key with different values: which stands is a person's decision;
  - the GARDENER is named in GARDEN.md: DAFTAR_GARDENER (or `--gardener`) names an existing person or org bean, or
    with DAFTAR_GARDENER_NAME (or `--gardener-name`) plants a new bean exactly as `seed/germinate.py --gardener`
    does, qualified by this garden's id — a person, or with DAFTAR_GARDENER_GENOS=org (`--gardener-genos org`) an
    organisation, each in the form the release's law gives a gardener of that genos — and the planted text is parsed
    and refused unless it says that bean, that genos and that name. Without a gardener the upgrade refuses, touching
    nothing, with the line that fixes it. A garden whose own tool is older than the flags hands over to the release's
    tool (below) and cannot pass them; the environment passes through any tool, so every message names where each
    value came from and prints the form this garden's own tool accepts.
  What cannot be carried is REFUSED before anything is touched: a bean still carrying `between`, `agreement_ref`,
  `conflict_rule` or `balance` is an agreement a person re-expresses (seed/COOKBOOK.md shows how). With
  --keep-on-failure the rest is applied and those are left, named, for the person.

CROSSING INTO std-vocab 22.0 the law's words took their Greek roots, and every garden says them: nothing is a
person's to decide, so all of it is translated, each document PROVED as above and each rename checked first against the
release's own `retired:` list. What moves is structure — a key, or a value the law owns — found by the YAML node that
holds it, so comments, quoting, layout and a garden's own prose stay byte for byte:
  - in every BEAN: `kind:` -> `genos:` (and where the merge driver names it, in `merge_conflicts` and
    `provenance_of`); `nature:` physical / metaphysical / living -> soma / lekton / empsychon; and the crown its
    ownership ends in, `{ crown: love }` -> `{ crown: agape }` and `{ crown: nature }` -> `{ crown: physis }` (logos
    is logos). A MAPPING records no being and keeps its `kind`;
  - in VOCAB.md: `local_kinds` -> `local_gene`, a restated or added `kinds` -> `gene`, each such row's `kind` ->
    `genos` and its `of_nature` renamed; a restated or added row of `natures` or `crown`; `identity_policy.minted`'s
    `form_kind: kinds` -> `form_genos: gene`; in the garden's own terms `required_on_kinds`, `only_on_kinds`,
    `must_equal_kind_attr`, `entry_form_from_kind_attr` -> their `gene`/`genos` names, `bean_id: { kinds }` -> `{ gene }`,
    `registry: kinds` and `registry:kinds[].kind` -> `gene`, and natures a term names; a vacancy at `registry:kinds`, or
    of a renamed nature or crown branch, follows it;
  - in the garden's own reasoning beside VOCAB.md, a heading keyed by a path VOCAB.md renamed follows it — the
    heading line alone, re-keyed by bin/dmwhy.py, the one tool that opens the reasoning.
  A document that cannot be renamed without changing something else — a key written twice, `genos:` already beside
  `kind:` — is REFUSED before anything is touched, naming it; with --keep-on-failure it is left, named, for the person.
  The garden's OWN CODE — a tool, a test or a template it keeps beside the language — is never translated: each file
  that says a retired word as code reads or writes a bean's key is NAMED on the `translated:` line, with how many lines
  say one, for a person to read before relying on it.
  A garden that CROSSED ALREADY is translated by the same step wherever a document still says 21.0's words — a bean
  added on a branch or a clone still at 21.0 and merged in since, or written from 21.0's documents: run this tool again
  with the release GARDEN.md records. The law does not move, so its journal entry asks nothing, and says RULE-CHANGE
  only where VOCAB.md itself was translated. (A bean BOTH sides changed never needs it: bin/dmmerge.py reads each side
  in the words of the law its tree runs.)

CROSSING INTO std-vocab 23.1 the law began to say where every file sits (`layers`), and took into itself a term a garden
had kept of its own. What the law now says itself leaves the garden's words, each document PROVED as above — the
entries it takes out gone, and every other byte where it was. The step names no term: the terms are the ones the
release's law declares that the law the garden ran did not, and what the law places is read through bin/dmpass.py, the
one reader of the map.
  - a `local_terms` entry of VOCAB.md for a term the law now declares leaves it, where taking it out loses nothing:
    every value the garden's term allows the law's allows too — a closed list held value by value to the law's domain,
    its list or the rows of its registry that pass its `where:` (the garden's `registry_additions` among them) — and
    every other rule it states the law's states alike. An open domain, a pattern or a type, is not compared: the gate
    reads every bean against the law's term once the garden's is gone and puts everything back if one fails, and the
    journal says which were not compared, never that the law's allows every value. A term of another shape, read at a
    key the law's is not, anchoring identity where the law's does not, allowing a value the law's does not, or stating
    a rule the law's does not state alike — a schema key such as `required_on_gene`, an attribute it requires, how its
    entries merge — is REFUSED before anything is touched, naming it: which stands is a person's decision;
  - a vacancy VOCAB.md declares at a position of that term leaves with it; a heading of the garden's own reasoning
    that explained what left is NAMED, never edited — what a reason says is its writer's own words — as bin/dmwhy.py,
    the one tool that opens the reasoning, reads it;
  - an entry of a bean or a mapping that places a file where the law places it otherwise is taken out, where every
    file it places the law places: the law's placement then stands alone and nothing is left unplaced. A pattern
    that places other files too is REFUSED, naming them: narrowing it is a person's decision. So is an entry that put
    a file of the garden's own in `law` or `manifesto` where the law places it in a layer that carries no RULE-CHANGE
    duty: taking it out would let the next change to that file through unjournalled.
  Each part of the `translated:` line names the key it took entries from — VOCAB.md's `local_terms` and `vacancies`, a
  bean's own — so the hook, which refuses a key removed or emptied with nothing said of it, lets the commit through.
  A garden that CROSSED ALREADY is translated by the same step wherever a bean or a mapping merged in since still
  places a file where the law places it otherwise, and wherever the law moves on and declares another term the
  garden kept of its own; its journal entry is written as the 22.0 step's is. Where all it finds is a person's to do,
  it names that and exits non-zero, --keep-on-failure or not: nothing translated is not nothing to do.

THE RELEASE'S OWN TOOL DOES THE WORK. When the release carries a different bin/dmupgrade.py, this one hands
over to it (with --garden and --no-delegate) instead of applying a newer release with older logic: v0.4.0
added the release record and the downgrade guard, and a v0.3.1 garden running its own v0.3.1 tool received the
new files and neither of those behaviours. An argument this tool does not know is handed over with the rest, so
the next release's new flags reach the tool that knows them.

A GARDEN'S NAME IS HELD TO THE RELEASE'S FORM (`manifest.garden`) before anything is touched: a name the release's
law refuses is the gardener's to change, not a translation's, so the refusal prints the GARDEN.md line to write and
the RULE-CHANGE entry that goes with it.

IT DOES NOT COMMIT. Adopting a release changes the law this garden is judged by, which is a decision the
garden's own human ratifies: read `git diff`, then `git add -A` and `git commit` — two commands, as every command
this tool prints runs as printed in Windows PowerShell 5.1 too. The journal entry is already written, so the gate's
provenance duty is met by the commit that adopts it.
"""
import argparse, copy, datetime, glob, importlib.util, inspect, json, os, re, shlex, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmform
import dmparse
import dmpass
import dmreform
import dmsafe

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPSTREAM = 'https://github.com/0mit/daftar.git'
PIN = re.compile(r'^(extends: std-vocab@)(\S+)', re.M)
RELEASE = re.compile(r'^daftar_release:.*$', re.M)
SEMVER = re.compile(r'^v?(\d+)\.(\d+)\.(\d+)$')


# A CHILD WRITES UTF-8, AND IS READ AS UTF-8. On Windows a Python writing to a pipe uses the old code page, so the gate
# died mid-sentence (UnicodeEncodeError) on the first ERROR line quoting Persian, and the upgrade put everything back
# showing no reason. PYTHONIOENCODING overrides UTF-8 mode, so both are set; git's own output is UTF-8 already.
CHILD_ENV = {'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'}


def run(*args, cwd=None, check=True):
    r = subprocess.run(args, cwd=cwd or ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace',
                       env={**os.environ, **CHILD_ENV})
    if check and r.returncode:
        detail = '\n'.join(s.strip() for s in (r.stdout, r.stderr) if s.strip())
        sys.exit(f"{' '.join(args)} failed:\n{detail or '(no output)'}")
    return r


class Form(tuple):
    """How a file was written: its line end, and whether it opened with a byte-order mark. PowerShell 5.1 writes UTF-8
    with a BOM, the gate reads through one (dmparse.BOM), and a file is written back as it was found."""
    nl = property(lambda self: self[0])
    bom = property(lambda self: self[1])


LF = Form(('\n', ''))


def read_text(path):
    """(text with '\\n' line ends and no BOM, its Form) — a file is written back with the ends and the mark it had."""
    raw = open(path, encoding='utf-8', newline='').read()
    bom = dmparse.BOM if raw.startswith(dmparse.BOM) else ''
    raw = raw[len(bom):]
    return raw.replace('\r\n', '\n'), Form(('\r\n' if '\r\n' in raw else '\n', bom))


def write_text(path, text, form=LF):
    """Written whole beside the file, then swapped in: a failure leaves the file as it was, and no half-written copy."""
    try:
        with open(path + '.tmp', 'w', encoding='utf-8', newline=form.nl) as fh:
            fh.write(form.bom + text)
        os.replace(path + '.tmp', path)
    except BaseException:
        try:
            os.remove(path + '.tmp')
        except OSError:
            pass
        raise


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
        if q == '"':
            if c == '"':                              # closed unless escaped: an ODD run of backslashes before it
                n = 0
                while i - 1 - n >= 0 and s[i - 1 - n] == '\\':
                    n += 1
                if n % 2 == 0:
                    q = None
        elif q:
            if c == "'":                              # single-quoted YAML escapes a quote by doubling it, never by `\`
                if s[i + 1:i + 2] == "'":
                    i += 1
                else:
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
    one = re.escape(key) + r'[ \t]*:[ \t]*' + _VAL + r'[ \t]*(?:#[^\n]*)?\n'
    # `- key: value` OPENING a block anchor: the next key moves up onto the dash — only when it sits at the column the
    # mapping's keys share, so it is this anchor's and not the next item's
    blk = re.sub(r'(?m)^([ \t]*-[ \t]+)' + one + r'([ \t]*)(?=[^\s#-])',
                 lambda m: m.group(1) if len(m.group(2)) == len(m.group(1)) else m.group(0), blk)
    blk = re.sub(r'(?m)^[ \t]+' + one, '', blk)
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


_KEY = re.compile(r'''^("(?:[^"\\\n]|\\.)*"|'(?:[^'\n]|'')*'|[^\s#'"-][^:#\n]*?)[ \t]*:(?=[ \t]|$)''')


def _key_of(line):
    """The key an entry line opens, AS YAML READS IT (`"desk": 1` and `desk: 1` hold one key), or None."""
    m = _KEY.match(line.rstrip('\n'))
    if not m:
        return None
    try:
        return dmparse.loads(m.group(1))
    except Exception:
        return m.group(1)


def _without(kids, keys):
    """Entry lines with the entries for `keys` left out (an entry runs to the next line at its own indent)."""
    out, skip = [], False
    for l in kids:
        if l.strip() and not l.startswith((' ', '#')):
            k = _key_of(l)
            skip = any(k == x and type(k) is type(x) for x in keys)
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
    note = ac[0].split(':', 1)[1].strip()
    if note.startswith('#'):                                        # the comment `attributes:` carried comes with it
        kids = dc[1] + [note + '\n'] + kids[len(dc[1]):]
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
    """What the 21.0 step would write to one bean or mapping: (new text or None, its Form, facts, problems).
    Each change is PROVED before it is kept: the new front matter must parse to exactly the old one with that change,
    and the body be unchanged. A change that cannot be proved is not made; the problem says so."""
    text, form = read_text(path)
    rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
    try:
        fm, body = _parse(text)
    except Exception:
        return None, form, {}, []                  # a document that does not parse: the gate names it, not this
    if fm is None:
        return None, form, {}, []
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
                    lo, hi = _fm_region(cur)                # the front matter only: the body is prose, and left alone
                    new_text = cur[:lo] + re.sub(
                        r'(?m)([:\[,-][ \t]*)(["\']?)' + re.escape(BEAN_MOVED[0]) + r'\.(' + alt + r')\2'
                        r'(?=[ \t]*(?:[,}\]#]|$))', lambda m: f"{m.group(1)}{m.group(2)}{BEAN_MOVED[1]}."
                        f"{m.group(3)}{m.group(2)}", cur[lo:hi]) + cur[hi:]
                    if prove(new_text, exp, f"following the pointers to `{BEAN_MOVED[0]}.<key>` into `{BEAN_MOVED[1]}`"):
                        cur, want = new_text, exp
    held = [k for k in BEAN_BY_HAND if k in fm]
    if held:
        problems.append(f"{rel}: carries {', '.join(f'`{k}`' for k in held)} — an agreement between parties is "
                        f"re-expressed by a person, not by a translation: {AGREEMENT_RECIPE}")
    return (cur if cur != text else None), form, facts, problems


def path_of(gid):
    """Where the bean `gid` lives in this garden."""
    return os.path.join(ROOT, 'beans', gid + '.md')


def genos_of(path):
    """A bean's genos — or, in a garden the 22.0 step has not yet translated, its `kind`, which is the same fact under
    the name the law gave it before: this tool reads a garden as it is, at whatever release it runs."""
    try:
        fm = _parse(read_text(path)[0])[0] or {}
    except Exception:
        return None                              # a bean that does not parse: the gate names it
    return fm.get('genos') if fm.get('genos') is not None else fm.get('kind')


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
    line = f"gardener: {gardener}                      # who keeps this garden"
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


def gardener_gene(root):
    """The gene of bean that may keep a garden, as the release's law declares them — `manifest.attrs.gardener`,
    `in: { bean_id: { gene: [...] } }` — or None when it declares none. Read from the law and never written here: the
    list lived in this tool and in the gate, and in no law (std-vocab 21.0)."""
    rec = (((std_fm(root).get('manifest') or {}).get('attrs') or {}).get('gardener')) or {}
    dom = rec.get('in') if isinstance(rec, dict) else None
    ids = dom.get('bean_id') if isinstance(dom, dict) else None
    gene = ids.get('gene') if isinstance(ids, dict) else None
    return tuple(str(k) for k in gene) if isinstance(gene, list) and gene else None


def own_garden_id(root):
    """This garden's id as bin/dmcheck.py's own_garden_id() reads it (std-vocab 21.0 `garden_id`): the first twelve hex
    digits of the root of its first-parent history; None for a shallow clone, which cannot see its root. Read here as
    well, because the gate a garden still runs when it crosses into 21.0 is older than that function."""
    r = run('git', 'rev-list', '--first-parent', '--max-parents=0', 'HEAD', cwd=root, check=False)
    shallow = run('git', 'rev-parse', '--is-shallow-repository', cwd=root, check=False).stdout.strip()
    roots = r.stdout.split()
    return roots[-1][:12] if r.returncode == 0 and roots and shallow != 'true' else None


def _ps(s):
    """A PowerShell argument: as it is when plain, else single-quoted (a quote inside doubled)."""
    return s if re.fullmatch(r'[\w./\\:+=-]+', s) else "'" + s.replace("'", "''") + "'"


def _arg(s):
    """An argument for the shell this runs under: PowerShell's quoting on Windows, a Unix shell's elsewhere."""
    return _ps(s) if os.name == 'nt' else shlex.quote(s)


PY = 'python' if os.name == 'nt' else 'python3'           # what a person types: `python3` may be the Store's alias there

# WHERE THE GARDENER CAME FROM is named in everything said about it. A garden whose own tool is older than --gardener
# hands over to this one and cannot pass the flag, so the environment carries the gardener: told to pass a flag it never
# passed, the person runs a command their tool rejects.
ENV_ID, ENV_NAME, ENV_GENOS = 'DAFTAR_GARDENER', 'DAFTAR_GARDENER_NAME', 'DAFTAR_GARDENER_GENOS'
# the same variable under the name the law used before 22.0 — a line an older tool printed still sets it, and is read
ENV_KIND = 'DAFTAR_GARDENER_KIND'
# A PowerShell session KEEPS what `$env:` sets, and the next garden upgraded in it would take this gardener unasked.
PS_CLEAR = f'Remove-Item Env:{ENV_ID}, Env:{ENV_NAME}, Env:{ENV_GENOS}, Env:{ENV_KIND} -ErrorAction SilentlyContinue'


_GERMINATE = {}


def release_germinate(rel):
    """The release's own seed/germinate.py, as a module: how a garden's gardener is planted and how the law's manifest
    forms are read — one copy for a new garden and an upgraded one. None for a release that has none."""
    if rel not in _GERMINATE:
        gpy = os.path.join(rel, 'seed', 'germinate.py')
        mod = None
        if os.path.isfile(gpy):
            spec = importlib.util.spec_from_file_location('daftar_germinate', gpy)
            mod = importlib.util.module_from_spec(spec)
            sys.dont_write_bytecode = True       # the release's seed is read, not left with a cache beside it
            spec.loader.exec_module(mod)
        _GERMINATE[rel] = mod
    return _GERMINATE[rel]


def check_name(rel, tag, keep):
    """GARDEN.md's `garden:` in the form the release's law gives a garden's name (`manifest.garden`), or a refusal —
    before anything is touched — printing the line to write and the RULE-CHANGE entry that goes with it. A garden
    grown when no form was asked of its name (`Garden-Sam` grew under v0.32.0) could otherwise never cross: the release's
    gate refused it and every file was put back, with nothing saying which line to change."""
    mod = release_germinate(rel)
    form = mod.manifest_form(std_fm(rel), 'garden') if mod is not None and hasattr(mod, 'manifest_form') else None
    gpath = os.path.join(ROOT, 'GARDEN.md')
    if not form or not os.path.isfile(gpath):
        return
    name = (_parse(read_text(gpath)[0])[0] or {}).get('garden')
    if name is not None and dmparse.law_match(form[0], str(name)):
        return
    like = (mod.name_like(name if name is not None else os.path.basename(ROOT), form[0]) if hasattr(mod, 'name_like')
            else '<a-name-in-kebab-case>')
    said = form[1] or f"must match {form[0]}"
    journal = (f'  {PY} bin/dmjournal.py "<who>" "RULE-CHANGE: the garden named {like}" --body "- action: RULE-CHANGE: '
               f'GARDEN.md names the garden {like}, in the form {tag}\'s law gives a garden\'s name."'
               if os.path.isfile(os.path.join(ROOT, 'bin', 'dmjournal.py')) else
               "  a journal entry in log/journal.md saying RULE-CHANGE, and what the name became")
    msg = (f"under {tag} the law's `manifest.garden` {said}, and GARDEN.md "
           + (f"says `garden: {name}`." if name is not None else "names no garden.")
           + f" A garden's name is for people — its identity is its first commit, which a new name leaves as it is — so "
           f"the name is the gardener's to choose. Under the release the garden runs now, write in GARDEN.md\n"
           f"  garden: {like}\n"
           f"(or another name in that form), journal it as the RULE-CHANGE every change to the manifest is, and commit:\n"
           f"{journal}\n  git add -A\n  git commit\nthen run this again.")
    if not keep:
        refuse(msg)
    print(f"NOTE (--keep-on-failure): {msg}", flush=True)


class Step21:
    """The translation into std-vocab 21.0: planned, and refused if it must be, before any file is touched."""

    def __init__(self, rel, tag, source, gardener, keep, genos=(None, None)):
        """`gardener`: (the id, where it came from, the name, where that came from) — a flag, the environment, or none;
        `genos`: (the genos a planted gardener is, where that came from), or none — then germinate's own default."""
        self.rel, self.tag, self.source, self.keep = rel, tag, source, keep
        self.gardener, self.gsrc, self.gardener_name, self.nsrc = gardener
        self.gardener_genos, self.ksrc = genos
        self.plans, self.problems, self.plant, self.created, self.plant_genos = {}, [], None, [], None

    def _flags(self):
        """Whether THIS GARDEN'S OWN TOOL takes the gardener as flags: one that knows `--gardener` also hands over any
        flag it does not know (`--gardener-genos`) to the release's tool; an older one rejects a flag it does not know."""
        own = os.path.join(ROOT, 'bin', 'dmupgrade.py')
        return os.path.isfile(own) and '--gardener' in open(own, encoding='utf-8').read()

    def fix_line(self, gid='<id>', name=None, genos=None):
        """The command that names the gardener, in the form THIS GARDEN'S OWN TOOL can pass on — that tool runs first
        and hands over, and one older than --gardener rejects the flag, while the environment passes through any tool.
        A placeholder is shown as one; a value is quoted for the shell it is pasted into."""
        nt = os.name == 'nt'
        q = _ps if nt else shlex.quote
        val = lambda v: v if v.startswith('<') else q(v)
        txt = lambda v: f'"{v}"' if v.startswith('<') else q(v)
        cmd = (r'python bin\dmupgrade.py ' if nt else 'python3 bin/dmupgrade.py ') + q(self.tag) + \
            (f' --from {q(self.source)}' if self.source != UPSTREAM else '')
        if self._flags():
            return (cmd + f' --gardener {val(gid)}' + (f' --gardener-name {txt(name)}' if name else '')
                    + (f' --gardener-genos {val(genos)}' if genos else ''))
        if nt:
            return (f'$env:{ENV_ID} = {txt(gid)}; ' + (f'$env:{ENV_NAME} = {txt(name)}; ' if name else '')
                    + (f'$env:{ENV_GENOS} = {txt(genos)}; ' if genos else '') + cmd + f'; {PS_CLEAR}')
        return (f'{ENV_ID}={val(gid)} ' + (f'{ENV_NAME}={txt(name)} ' if name else '')
                + (f'{ENV_GENOS}={val(genos)} ' if genos else '') + cmd)

    def genos_asked(self):
        """The genos the gardener was asked to be planted as — where the release's law lets it keep a garden, else none,
        so a fix line never repeats a genos that was refused."""
        return self.gardener_genos if self.gardener_genos in (gardener_gene(self.rel) or ()) else None

    def genos_option(self):
        """How this garden's tool is told the genos of a gardener it plants: the flag, or the environment."""
        if self._flags():
            return '--gardener-genos <genos>'
        return f'$env:{ENV_GENOS} = "<genos>"' if os.name == 'nt' else f'{ENV_GENOS}=<genos>'

    def fixes(self, gid='<id>'):
        """Both lines: the gardener named alone, and named with how they are called, which plants their bean."""
        mod = release_germinate(self.rel)
        params = inspect.signature(mod.gardener_bean).parameters if mod is not None and hasattr(mod, 'gardener_bean') else {}
        default = params['genos'].default if 'genos' in params else None
        gene = gardener_gene(self.rel) or ()
        other = [k for k in gene if k != default]
        return (f"  {self.fix_line(gid)}\nor, to plant a new bean for them"
                + (f" — a {default}, or with {self.genos_option()} a bean of genos {' or '.join(other)}" if default and other
                   else '') + ":\n"
                f"  {self.fix_line(gid, '<how they are called>', self.genos_asked())}")

    @staticmethod
    def clear(*names):
        """How to clear variables the environment still holds — they may be left from another garden's upgrade."""
        if os.name == 'nt':
            return 'Remove-Item ' + ', '.join(f'Env:{n}' for n in names) + ' -ErrorAction SilentlyContinue'
        return 'unset ' + ' '.join(names)

    def plan(self):
        law = {(str(r.get('at')), str(r.get('name'))) for r in (std_fm(self.rel).get('retired') or []) if isinstance(r, dict)}
        said = ([('anchor', k) for k in ANCHOR_DROPPED] + [('manifest', k) for k in MANIFEST_DROPPED] +
                [('bean', BEAN_MOVED[0])] + [('bean', k) for k in BEAN_BY_HAND])
        if [s for s in said if s not in law]:
            refuse(f"{self.tag}'s law does not retire {', '.join(f'{a} `{n}`' for a, n in said if (a, n) not in law)}, "
                   f"which this tool's 21.0 step translates. The step and the law disagree; neither is guessed at.")
        self.plan_gardener()
        if self.gsrc == ENV_ID or self.ksrc in (ENV_GENOS, ENV_KIND):
            print(f"the gardener: '{self.gardener}'" + (f", taken from {ENV_ID}" if self.gsrc == ENV_ID else '')
                  + (f", planted with the name {ENV_NAME} gives" if self.plant and self.nsrc == ENV_NAME else '')
                  + (f", of the genos {self.ksrc} gives ({self.gardener_genos})" if self.plant and self.ksrc in (ENV_GENOS, ENV_KIND)
                     else ''), flush=True)
        for sub in DOCS:
            for path in sorted(glob.glob(os.path.join(ROOT, sub, '*.md'))):
                new, form, facts, problems = plan_doc(path)
                self.problems += problems
                if new is not None:
                    self.plans[path] = (new, form, facts)
        gtext, _form = read_text(os.path.join(ROOT, 'GARDEN.md'))
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
            refuse(f"GARDEN.md already names the gardener '{named}', and {self.gsrc} says '{gid}'. Changing who keeps "
                   f"a garden is the gardener's decision, never an upgrade's."
                   + (f" If {ENV_ID} is left from another garden, clear it ({self.clear(ENV_ID, ENV_NAME, ENV_GENOS, ENV_KIND)}) "
                      f"and run this again." if self.gsrc == ENV_ID else ''))
        if not gid and named:
            gid, self.gsrc = str(named), "GARDEN.md's `gardener:`"
        gene = gardener_gene(self.rel)
        if not gene:
            refuse(f"{self.tag}'s law does not say which gene of bean may keep a garden (`manifest.attrs.gardener`, "
                   f"`in: {{ bean_id: {{ gene }} }}`), and this tool does not guess it.")
        either = ' or '.join(gene)
        keepers = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ROOT, 'beans', '*.md'))
                         if genos_of(p) in gene)
        here = (f" (here: {', '.join(keepers[:12])}" + (', …' if len(keepers) > 12 else '') + ")") if keepers else ''
        if not gid:
            refuse(f"std-vocab 21.0 asks who keeps this garden — its GARDENER, a person or an organisation it holds, "
                   f"named in GARDEN.md — and this garden names none. Ask the person, then:\n{self.fixes()}\n"
                   f"<id> is an existing {either} bean{here}; with a name, a new bean is planted for them, as "
                   f"seed/germinate.py --gardener plants one.")
        if not GARDENER_ID.match(gid):
            refuse(f"{self.gsrc} names the gardener by a bean id — kebab-case, such as sam — and got '{gid}'. "
                   f"Name them so:\n{self.fixes()}")
        path = os.path.join(ROOT, 'beans', gid + '.md')
        if os.path.isfile(path):
            genos = genos_of(path)
            if genos not in gene:
                refuse(f"'{gid}' is a {genos} ({self.gsrc} names it); a garden is kept by a bean of genos {either}{here}. "
                       f"Name one:\n{self.fixes()}")
            if name:
                refuse(f"'{gid}' is already a bean of this garden, and {self.nsrc} plants a NEW one. Name them alone"
                       + (f" — clearing {ENV_NAME} first ({self.clear(ENV_NAME)})" if self.nsrc == ENV_NAME else '')
                       + f":\n  {self.fix_line(gid)}")
            if self.gardener_genos and self.gardener_genos != genos:
                refuse(f"'{gid}' is a {genos}, and {self.ksrc} says {self.gardener_genos}: a bean's genos is its own, and "
                       f"the genos is said only of a gardener planted here. Name them alone"
                       + (f" — clearing {self.ksrc} first ({self.clear(self.ksrc)})" if self.ksrc in (ENV_GENOS, ENV_KIND) else '')
                       + f":\n  {self.fix_line(gid)}")
        elif not name:
            refuse(f"'{gid}' is no bean of this garden ({self.gsrc} names it). Name an existing {either} bean{here}:\n"
                   f"  {self.fix_line()}\nor plant a new bean for them:\n"
                   f"  {self.fix_line(gid, '<how they are called>', self.genos_asked())}")
        else:
            self.plan_planting(gid, name, gene, either)
        self.gardener = gid

    def plan_planting(self, gid, name, gene, either):
        """The gardener's bean, EXACTLY as the release's seed/germinate.py --gardener plants one — its own function, not
        a second copy of its text: of the genos asked for (or germinate's own default), in the form the release's law
        gives a gardener of that genos, and qualified by this garden's id as a new garden's gardener is at birth."""
        mod = release_germinate(self.rel)
        if mod is None or not hasattr(mod, 'gardener_bean'):
            refuse(f"{self.tag}'s seed/germinate.py plants no gardener, so there is no bean to plant here the way a new "
                   f"garden plants one. Write the gardener's bean by hand, commit it, and name them alone:\n"
                   f"  {self.fix_line(gid)}")
        params = inspect.signature(mod.gardener_bean).parameters
        genos = self.gardener_genos or (params['genos'].default if 'genos' in params else None)
        if self.gardener_genos and 'genos' not in params:
            refuse(f"{self.tag}'s seed/germinate.py plants a gardener of one genos only, and {self.ksrc} asks for "
                   f"{self.gardener_genos}. Write the gardener's bean by hand, commit it, and name them alone:\n"
                   f"  {self.fix_line(gid)}")
        if genos is not None and genos not in gene:
            refuse(f"{self.ksrc or 'germinate'} would plant a gardener of genos '{genos}', and {self.tag}'s law lets a "
                   f"bean of genos {either} keep a garden"
                   + (f" — if {self.ksrc} is left from another garden, clear it ({self.clear(self.ksrc)})"
                      if self.ksrc in (ENV_GENOS, ENV_KIND) else '') + f". Name one:\n{self.fixes(gid)}")
        form = mod.gardener_form(std_fm(self.rel), genos) if genos and hasattr(mod, 'gardener_form') else None
        if genos and hasattr(mod, 'gardener_form') and form is None:
            refuse(f"{self.tag}'s law gives no form for a gardener of genos '{genos}' (a `<genos>_id` anchor term). Write "
                   f"the gardener's bean by hand, commit it, and name them alone:\n  {self.fix_line(gid)}")
        kw = {k: v for k, v in (('garden_id', own_garden_id(ROOT)), ('genos', genos), ('form', form))
              if k in params and v is not None}
        text = mod.gardener_bean(gid, name, datetime.date.today().isoformat(), **kw)
        # PROVED BEFORE IT IS WRITTEN, as every translated bean is: a name the function spelled wrongly (Python's repr
        # once turned a zero-width non-joiner into six characters of text) is refused, not planted — and so is a bean of
        # another genos than the one asked for, or of none the law lets keep a garden.
        try:
            pfm = _parse(text)[0]
        except Exception:
            pfm = None
        wrong = (['it does not parse as a bean'] if not pfm else
                 [f"`{k}` would read {pfm.get(k)!r}, not {v!r}" for k, v in (('bean', gid), ('genos', genos), ('title', name))
                  if v is not None and pfm.get(k) != v]
                 + ([f"`genos` would read {pfm.get('genos')!r}, which may not keep a garden ({either})"]
                    if pfm.get('genos') not in gene else []))
        if wrong:
            refuse(f"{self.tag}'s seed/germinate.py would plant a gardener that does not say what was asked — "
                   f"{'; '.join(wrong)}. Write the gardener's bean by hand, commit it, and name them alone:\n"
                   f"  {self.fix_line(gid)}")
        self.plant = (path_of(gid), text)
        self.plant_genos = pfm.get('genos')

    def apply(self):
        """Writes what was planned; returns the `translated:` text and the ids of the documents it touched."""
        touched, scope, with_scope, moved = [], 0, [], []
        for path, (new, form, facts) in self.plans.items():
            write_text(path, new, form)
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
            self.created.append(os.path.relpath(path, ROOT).replace(os.sep, '/'))   # before the write: put back if it fails
            write_text(path, text)
        gpath = os.path.join(ROOT, 'GARDEN.md')
        gtext, gform = read_text(gpath)
        gfm = _parse(gtext)[0] or {}
        gone = [(k, gfm[k]) for k in MANIFEST_DROPPED if k in gfm]
        new, why = plan_manifest(gtext, self.gardener)
        if new is not None:
            write_text(gpath, new, gform)
        elif why not in self.problems:
            self.problems.append(why)
        parts = []
        if scope:
            parts.append(f"`scope` removed from {scope} anchor(s) in {', '.join(with_scope)} (read by nothing, so nothing is lost)")
        if gone and new is not None:
            # WHAT WAS SAID IS QUOTED, so the journal holds it: the law reads none of these, and git's history is not a
            # place anyone looks. The gardens a garden took in are the ones a person may still want to know by name.
            said = [f"`{k}`" + (f" (was {json.dumps(v, ensure_ascii=False, default=str)})" if v not in (None, '', [], {}) else '')
                    for k, v in gone]
            parts.append(f"GARDEN.md: {', '.join(said)} removed (the law reads none of them)")
            if dict(gone).get('seeds_from'):
                parts.append("the gardens `seeds_from` named are each recorded, where still known, as a `garden` bean — "
                             "a person's to write")
        if moved:
            parts.append(f"`{BEAN_MOVED[0]}` moved into `{BEAN_MOVED[1]}` in {', '.join(moved)}")
        if new is not None:
            gid = f"[[{self.gardener}]]"
            parts.append(f"gardener {gid} " + (f"planted — a bean of genos {self.plant_genos}, as seed/germinate.py "
                                               f"--gardener plants one — and " if self.plant else "") + "named in GARDEN.md"
                         + (f" (given as {ENV_ID})" if self.gsrc == ENV_ID else ''))
            if self.plant:
                touched.append(gid)
        if self.problems:
            parts.append("LEFT FOR A PERSON: " + '; '.join(self.problems))
        return 'std-vocab 21.0 — ' + '; '.join(parts or ['nothing to translate']), touched

    @staticmethod
    def _id(path):
        base = os.path.basename(path)[:-3]
        return f"[[{base}]]" if os.path.basename(os.path.dirname(path)) == 'beans' else f"mappings/{base}"


# ==== THE 22.0 STEP =============================================================================================
# The law's words took their Greek roots: a bean's `kind` is its `genos` and the registry `kinds` is `gene`, the natures
# are soma, lekton and empsychon, and the crown's branches physis, logos and agape under theos. Each pair below is the
# OLD spelling and the name the release's own `retired:` list must say it went to — checked before anything is touched,
# so a release whose law says otherwise is refused, never guessed at. What moves is STRUCTURE: a key, or a value the law
# owns. Comments, prose and every value a garden wrote in its own words are left as they were — they are its own.
STEP_22 = (22, 0)
GREEK = {                                               # (where the law retired it, the old name): the new name
    ('bean', 'kind'): 'genos',
    ('law', 'kinds'): 'gene',
    ('vocab', 'local_kinds'): 'local_gene',
    ('bean_id', 'kinds'): 'gene',
    ('minted', 'form_kind'): 'form_genos',
    ('schema', 'required_on_kinds'): 'required_on_gene',
    ('schema', 'only_on_kinds'): 'only_on_gene',
    ('schema', 'must_equal_kind_attr'): 'must_equal_genos_attr',
    ('schema', 'entry_form_from_kind_attr'): 'entry_form_from_genos_attr',
    ('nature', 'physical'): 'soma', ('nature', 'metaphysical'): 'lekton', ('nature', 'living'): 'empsychon',
    ('crown', 'god'): 'theos', ('crown', 'nature'): 'physis', ('crown', 'love'): 'agape',
}
NATURE_22 = {o: n for (a, o), n in GREEK.items() if a == 'nature'}
CROWN_22 = {o: n for (a, o), n in GREEK.items() if a == 'crown'}
SCHEMA_22 = {o: n for (a, o), n in GREEK.items() if a == 'schema'}
GENE_ROWS = (('local_kinds',), ('kinds',), ('registry_additions', 'kinds'))    # where a garden writes rows of `kinds`


class CannotRename(Exception):
    pass


def renamed(text, rule):
    """(the new text, [(what, old, new)]) — the front matter of `text` with every KEY or VALUE `rule` renames replaced
    where it is written, found by the YAML node that holds it: its quotes kept, and everything else — comments, layout,
    every other value — byte for byte. `rule(path, role, name, parent)` answers the new name or None, for a key
    (`role` 'key', `path` the mapping's) or a text value (`role` 'value', `path` the value's own); `parent` is the mapping
    or list that holds it, as parsed, so a rule may read a sibling. PROVED before it is returned: the new front matter
    must parse to exactly the old one with those renames made, and the body is untouched. Raises CannotRename."""
    region = _fm_region(text)
    if not region:
        return text, []
    lo, hi = region
    head = text[lo:hi]
    y = dmparse._yaml
    try:
        root, data = y.compose(head, Loader=dmparse.LOADER), dmparse.loads(head)
    except Exception:
        return text, []                     # a document that does not parse is the gate's to name, not this step's
    edits, done = {}, []

    def swap(node, new, what, old):
        tok = head[node.start_mark.index:node.end_mark.index]
        q = tok[:1] if tok[:1] in ('"', "'") else ''
        edits[node.start_mark.index] = (node.end_mark.index, q + new + q)
        done.append((what, old, new))

    def walk(node, d, path):
        if isinstance(node, y.MappingNode) and isinstance(d, dict):
            if len(node.value) != len(d):
                raise CannotRename("a key is written twice in one mapping, or merged in with `<<`")
            out = {}
            for (kn, vn), (k, v) in zip(node.value, d.items()):
                nk = rule(path, 'key', k, d) if isinstance(k, str) and isinstance(kn, y.ScalarNode) else None
                if nk:
                    if nk in d:
                        raise CannotRename(f"`{'.'.join(map(str, path + (k,)))}` would become `{nk}`, which is "
                                           f"written beside it already — which of the two stands is a person's decision")
                    swap(kn, nk, 'key ' + '.'.join(map(str, path + (k,))), k)
                out[nk or k] = leaf(vn, v, path + (k,), d)
            return out
        if isinstance(node, y.SequenceNode) and isinstance(d, list) and len(node.value) == len(d):
            return [leaf(vn, v, path + (i,), d) for i, (vn, v) in enumerate(zip(node.value, d))]
        return d

    def leaf(vn, v, path, parent):
        if isinstance(vn, y.ScalarNode) and isinstance(v, str):
            nv = rule(path, 'value', v, parent)
            if nv:
                swap(vn, nv, 'value ' + '.'.join(map(str, path)), v)
                return nv
            return v
        return walk(vn, v, path)

    want = walk(root, data, ()) if root is not None else data
    if not edits:
        return text, []
    new_head = head
    for s in sorted(edits, reverse=True):
        e, new = edits[s]
        new_head = new_head[:s] + new + new_head[e:]
    new_text = text[:lo] + new_head + text[hi:]
    try:
        nfm, nbody = _parse(new_text)
    except Exception:
        nfm, nbody = None, None
    if nfm != want or nbody != _parse(text)[1]:
        raise CannotRename("the renames could not be made without changing something else")
    return new_text, done


def bean_rule_22(path, role, name, parent):
    """A bean in 22.0's words: `kind` -> `genos` (and where the merge driver names it: `merge_conflicts`,
    `provenance_of`), its `nature`, and the crown branch its ownership ends in. Nothing else of a bean is the law's."""
    if role == 'key':
        return 'genos' if name == 'kind' and path in ((), ('provenance_of',)) else None
    if path == ('nature',) or path[:2] == ('nature', 'conflict'):
        return NATURE_22.get(name)
    if len(path) == 3 and path[0] == 'owned_by' and path[2] == 'crown':
        return CROWN_22.get(name)
    if len(path) == 2 and path[0] == 'merge_conflicts' and name == 'kind':
        return 'genos'
    return None


def vocab_rule_22(path, role, name, parent):
    """A garden's VOCAB.md in 22.0's words: `local_kinds` -> `local_gene` and a restated or added `kinds` -> `gene`, each
    row's `kind` -> `genos` and its `of_nature` renamed; a restated or added row of `natures` or `crown`; the minted form's
    `form_kind`; and in its own terms, the schema keys named for kinds, `bean_id`'s `kinds`, and a registry or a nature a
    term names. A vacancy at a renamed registry, or of a renamed position, follows it."""
    if role == 'key':
        if path == ():
            return {'local_kinds': 'local_gene', 'kinds': 'gene'}.get(name)
        if path == ('registry_additions',):
            return 'gene' if name == 'kinds' else None
        if path == ('identity_policy', 'minted'):
            return 'form_genos' if name == 'form_kind' else None
        if len(path) >= 2 and path[:-1] in GENE_ROWS and isinstance(path[-1], int):
            return 'genos' if name == 'kind' else None
        if path[:1] == ('local_terms',):
            if len(path) == 3 and path[2] == 'schema':
                return SCHEMA_22.get(name)
            if path[-1] == 'bean_id' and name == 'kinds':
                return 'gene'
        return None
    row, attr = path[:-1], path[-1]
    if len(row) >= 2 and row[:-1] in GENE_ROWS and isinstance(row[-1], int):
        return NATURE_22.get(name) if attr == 'of_nature' else None
    if len(row) >= 2 and row[:-1] in (('natures',), ('registry_additions', 'natures')) and isinstance(row[-1], int):
        return NATURE_22.get(name) if attr == 'nature' else CROWN_22.get(name) if attr == 'crown' else None
    if len(row) >= 2 and row[:-1] in (('crown',), ('registry_additions', 'crown')) and isinstance(row[-1], int):
        return CROWN_22.get(name) if attr == 'branch' else None
    if path == ('identity_policy', 'minted', 'form_kind'):
        return 'gene' if name == 'kinds' else None
    if path[:1] == ('vacancies',) and len(path) == 3:
        at = parent.get('at') if isinstance(parent, dict) else None
        if attr == 'at':
            return 'registry:gene' if name == 'registry:kinds' else None
        if attr == 'position':
            return (NATURE_22.get(name) if at in ('registry:natures', 'nature.values') else
                    CROWN_22.get(name) if at == 'registry:crown' else None)
        return None
    if path[:1] == ('local_terms',):
        if attr in ('values_from', 'key_form') and 'registry:kinds[].kind' in name:
            return name.replace('registry:kinds[].kind', 'registry:gene[].genos')
        if isinstance(attr, int) and len(path) >= 2 and path[-2] == 'required_on_natures':
            return NATURE_22.get(name)
        if attr == 'registry' and name == 'kinds':
            return 'gene'
        if attr == 'take' and name == 'kind' and isinstance(parent, dict) and parent.get('registry') == 'kinds':
            return 'genos'
        if attr == 'keyed_by' and name == 'kind' and 'entry_must_match' in path:
            return 'genos'
    return None


class Step22:
    """The translation into std-vocab 22.0: planned, and refused if it must be, before any file is touched — and made
    again at apply time on each file as the steps before it left it, so nothing written before is written over."""

    def __init__(self, rel, tag, keep):
        self.rel, self.tag, self.keep = rel, tag, keep
        self.problems, self.facts, self.reasons = [], {}, None
        self.leftover = False           # True: the garden had crossed already, and this translates what came in since

    def left(self):
        """Whether a garden that crossed into 22.0 already still holds a document in 21.0's words — which only something
        that came in afterwards can be — and so is translated again. A document this step would refuse counts: the
        refusal is then said, as it is on a crossing."""
        for path in self.docs():
            if os.path.isfile(path):
                text = read_text(path)[0]
                try:
                    if renamed(text, vocab_rule_22 if os.path.basename(path) == 'VOCAB.md' else bean_rule_22)[1]:
                        self.leftover = True
                except CannotRename:
                    self.leftover = True
            if self.leftover:
                return True
        return False

    def plan(self):
        law = {(str(r.get('at')), str(r.get('name'))): str(r.get('instead') or '')
               for r in (std_fm(self.rel).get('retired') or []) if isinstance(r, dict)}
        wrong = [f"{a} `{o}` -> `{n}`" for (a, o), n in GREEK.items() if not law.get((a, o), '').startswith(f"`{n}`")]
        if wrong:
            refuse(f"{self.tag}'s law does not retire, as this tool's 22.0 step translates them, "
                   f"{', '.join(wrong)}. The step and the law disagree; neither is guessed at.")
        for path in self.docs():
            self.one(path, dry=True)
        if self.problems and not self.keep:
            refuse(f"crossing into std-vocab 22.0, {len(self.problems)} thing(s) are a person's to do, not a "
                   f"translation's:\n" + '\n'.join('  - ' + p for p in self.problems) +
                   "\nDo them and commit, then run this again — or pass --keep-on-failure to apply the rest and "
                   "leave these, named, for the person.")

    @staticmethod
    def docs():
        """Every bean, and VOCAB.md. A mapping records no being and keeps its `kind`; GARDEN.md says nothing renamed."""
        return sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) + [os.path.join(ROOT, 'VOCAB.md')]

    def one(self, path, dry=False):
        """Plan (dry) or make the renames in one document; what was renamed is kept in `facts`, a refusal in `problems`."""
        if not os.path.isfile(path):
            return
        text, form = read_text(path)
        rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
        rule = vocab_rule_22 if rel == 'VOCAB.md' else bean_rule_22
        try:
            new, done = renamed(text, rule)
        except CannotRename as e:
            why = f"{rel}: {e} — translate it by hand"
            if why not in self.problems:
                self.problems.append(why)
            return
        if not dry and done:
            write_text(path, new, form)
            self.facts[rel] = done

    def apply(self, vocab_only=False):
        """Writes what was planned — VOCAB.md alone, before the garden's own terms are read by bin/dmreform.py, or the
        beans. Returns the `translated:` text and the ids of the beans it touched."""
        for path in self.docs():
            if (os.path.basename(path) == 'VOCAB.md') == vocab_only:
                self.one(path)
        if vocab_only:
            self.rekey_reasons()
            return None, []
        return self.report()

    # A garden's own reasons are keyed by the PATH of what they explain in its VOCAB.md, so a key that names a renamed
    # block, registry, row attribute, schema key, nature or crown branch follows it — the heading alone, re-keyed by
    # bin/dmwhy.py, the one tool that opens the reasoning; what a reason SAYS is the garden's own words.
    _SEGMENT = r'(?=$|[.\[])'
    REKEY_22 = (
        (re.compile(r'^local_kinds' + _SEGMENT), 'local_gene'),
        (re.compile(r'^kinds' + _SEGMENT), 'gene'),
        (re.compile(r'^(registry_additions\.)kinds' + _SEGMENT), lambda m: m.group(1) + 'gene'),
        (re.compile(r'^((?:local_gene|gene|registry_additions\.gene)\[[^\]]*\]\.)kind' + _SEGMENT),
         lambda m: m.group(1) + 'genos'),
        (re.compile(r'^(identity_policy\.minted\.)form_kind$'), lambda m: m.group(1) + 'form_genos'),
        (re.compile(r'^((?:registry_additions\.)?natures\[)(physical|metaphysical|living)\]'),
         lambda m: m.group(1) + NATURE_22[m.group(2)] + ']'),
        (re.compile(r'^((?:registry_additions\.)?crown\[)(god|nature|love)\]'), lambda m: m.group(1) + CROWN_22[m.group(2)] + ']'),
        (re.compile(r'^(local_terms\[[^\]]*\]\.schema\.)(' + '|'.join(SCHEMA_22) + ')' + _SEGMENT),
         lambda m: m.group(1) + SCHEMA_22[m.group(2)]),
    )

    def rekey_reasons(self):
        """The garden's own reasons, re-keyed where they name what the 22.0 step renamed in VOCAB.md — and only once
        VOCAB.md says the new names, so a reason is never pointed at a path its law does not yet have."""
        if any(p.startswith('VOCAB.md:') for p in self.problems):
            return
        sys.path.insert(0, os.path.join(ROOT, 'bin'))
        import dmwhy
        self.reasons, done = dmwhy.rekey(ROOT, self.REKEY_22)
        if done:
            self.facts[self.reasons] = [('heading', o, n) for o, n in done]
        else:
            self.reasons = None

    # THE GARDEN'S OWN CODE IS NEVER TRANSLATED, AND IS NAMED. A garden may keep tools, tests and templates of its own
    # beside the language; one that reads a bean's `kind` reads nothing from a crossed garden, and says nothing about it —
    # a leak guard that chose its words by `kind` stopped seeing most of them, and a filter by organisation showed every
    # row. A word in code has other senses (a network entry's `kind`), so this names files for a person to read: it
    # refuses nothing and changes nothing. Code is a file with a code extension or a `#!` line, and what it says is a
    # retired word as code reads a key — a quoted literal, `'kind'` — or as a bean writes one, which a test's fixture
    # does inside a string: `kind: `, `nature: physical`, `crown: love`. A Markdown file outside the beans counts where it
    # is shaped like a bean (a template, an example) and this step would rename something in it.
    CODE_WORD = re.compile(r"""(['"])(?:kind|kinds|local_kinds|form_kind|physical|metaphysical|living)\1"""
                           r"""|\b(?:kind|kinds|local_kinds|form_kind):\s|\bnature:\s*['"]?(?:physical|metaphysical|living)\b"""
                           r"""|\bcrown:\s*['"]?(?:love|nature|god)\b""")
    CODE_EXT = ('.py', '.js', '.mjs', '.cjs', '.ts', '.sh', '.ps1', '.psm1', '.rb', '.go', '.pl', '.php', '.lua')
    RECORDS = ('beans', 'mappings', 'log', 'captures')

    def code_left(self):
        """[(path, how many lines)] of the garden's own files, outside the language and its records, that say a word
        22.0 retired — for a person to read before relying on them."""
        own = {p.replace(os.sep, '/') for p in expand(self.rel, patterns(self.rel))}
        out = []
        for f in sorted(x for x in run('git', 'ls-files', '-z', check=False).stdout.split('\0') if x):
            if f in own or f in ('VOCAB.md', 'GARDEN.md') or f.split('/')[0] in self.RECORDS:
                continue
            try:
                text = read_text(os.path.join(ROOT, *f.split('/')))[0]
            except (OSError, UnicodeDecodeError):
                continue
            n, fm = 0, _parse(text)[0] if f.endswith('.md') else None
            if f.endswith('.md'):
                if isinstance(fm, dict) and 'bean' in fm:
                    try:
                        n = len(renamed(text, bean_rule_22)[1])
                    except CannotRename:
                        n = 1
            elif f.endswith(self.CODE_EXT) or text.startswith('#!'):
                n = sum(1 for line in text.split('\n') if self.CODE_WORD.search(line))
            if n:
                out.append((f, n))
        return out

    def report(self):
        """What was translated, as the journal's `translated:` line says it: each rename with how often it was made, the
        beans it was made in, what VOCAB.md became, what is left for a person, and — on the crossing — the garden's own
        code that says a retired word, which is never translated."""
        from collections import Counter

        def said(what, old, new):
            place = what.split(' ', 1)[1]
            if place == 'nature' or place.startswith('nature.'):
                return f"nature {old} -> {new}"
            if place.startswith('owned_by.'):
                return f"crown {old} -> {new}"
            return f"`{old}` -> `{new}`"
        beans = sorted(r for r in self.facts if r.startswith('beans/'))
        parts = []
        if beans:
            tally = Counter(said(*x) for r in beans for x in self.facts[r])
            parts.append(f"{len(beans)} bean(s): " + ', '.join(f"{k} ×{c}" for k, c in sorted(tally.items(), key=lambda x: (
                not x[0].startswith('`'), x[0]))) + " — " + ', '.join(f"[[{os.path.basename(r)[:-3]}]]" for r in beans))
        if 'VOCAB.md' in self.facts:
            vt = Counter(f"`{o}` -> `{n}`" for _w, o, n in self.facts['VOCAB.md'])
            parts.append("VOCAB.md: " + ', '.join(k + (f" ×{c}" if c > 1 else '') for k, c in sorted(vt.items())))
        if self.reasons:
            parts.append(f"{self.reasons}, the garden's own reasons re-keyed: " + ', '.join(
                f"`## {o}` -> `## {n}`" for _w, o, n in self.facts[self.reasons]))
        if self.problems:
            parts.append("LEFT FOR A PERSON: " + '; '.join(self.problems))
        code = [] if self.leftover else self.code_left()
        if code:
            parts.append(f"NOT TRANSLATED, for a person to read: {len(code)} file(s) of the garden's own code say a word "
                         f"22.0 retired, and may read a bean by it — " + ', '.join(f"{f} ({n})" for f, n in code[:20])
                         + (f" and {len(code) - 20} more" if len(code) > 20 else ''))
        return ('std-vocab 22.0, the Greek names — ' + '; '.join(parts or ['nothing to translate']),
                [f"[[{os.path.basename(r)[:-3]}]]" for r in beans])


# ==== THE 23.1 STEP =============================================================================================
# The law says where every file sits (`layers`), and took into itself the term a garden had placed its files with. What a
# garden said in its own words that the law now says itself leaves the garden's words — WHERE NOTHING IS LOST: its term
# only where the law's allows every value the garden's did and states alike every rule the garden's stated, a placement
# only where the law's places every file the garden's did and none leaves the RULE-CHANGE duty by it. The rest is a
# person's. No term is named here; which terms moved is read from the two laws, and what the law places from
# bin/dmpass.py.
STEP_23_1 = (23, 1)
NOT_A_DOMAIN = ('scope', 'required', 'meaning', 'keyed_by', 'default_from', 'one_of')   # what else an attribute's form says
VALUE_DOMAIN = ('values', 'values_from', 'pattern', 'form', 'in_registry')         # a term's own value, as dmform reads it
# A SCHEMA KEY IS A RULE, and one the garden's term states that the law's does not state alike is lost with the garden's
# term. These are held by the VALUES they allow instead — the shape, each attribute's domain, the term's own value — so a
# law that allows more than the garden's did is taken for what it is; every other key is held to the law's as written.
BY_VALUE = ('shape', 'attrs', 'values', 'values_add', 'values_from', 'value_pattern', 'value_form', 'value_in_registry')


def without_entries(text, cuts, empty='drop'):
    """The front matter of `text` with entries taken out of the lists its top-level keys hold — `cuts` {key: {index}} —
    each found by the YAML node that holds it: the entry's own lines go, with a comment on its last line, and everything
    else — comments between entries, layout, every other entry — stays byte for byte. A list left with no entry leaves
    with its key, the comments between its entries with it, or with `empty='keep'` is written `key: []`, as a garden's
    VOCAB.md holds an empty block. PROVED before it is returned: the new front matter must parse to exactly the old one
    without those entries, and the body is untouched. Raises CannotRename."""
    y = dmparse._yaml
    try:
        data, body = _parse(text)
    except Exception:
        data, body = None, None
    if data is None:
        raise CannotRename("its front matter does not parse")
    want = copy.deepcopy(data)
    for key, idx in cuts.items():
        items = want.get(key)
        if not isinstance(items, list) or not idx or max(idx) >= len(items):
            raise CannotRename(f"`{key}` is not the list it was read as")
        rest = [x for i, x in enumerate(items) if i not in idx]
        if rest or empty == 'keep':
            want[key] = rest
        else:
            del want[key]
    cur = text
    for key, idx in cuts.items():
        whole = len(set(idx)) == len(data[key])             # the whole list: its key goes, or says it is empty
        for i in ((None,) if whole else sorted(set(idx), reverse=True)):   # the last first: an index before it still names its entry
            lo, hi = _fm_region(cur)
            head = cur[lo:hi]
            try:
                root = y.compose(head, Loader=dmparse.LOADER)
            except Exception:
                raise CannotRename("its front matter does not parse")
            kn, seq = next(((k, v) for k, v in root.value if isinstance(k, y.ScalarNode) and k.value == key), (None, None))
            if not isinstance(seq, y.SequenceNode) or (i is not None and i >= len(seq.value)):
                raise CannotRename(f"`{key}` is not written as the list it was read as")
            spans = [_list_span(head, kn, seq, empty)] if whole else _entry_span(head, seq.value, i, seq.flow_style)
            for a, b, new in sorted(spans, reverse=True):
                cur = cur[:lo + a] + new + cur[lo + b:]
    try:
        nfm, nbody = _parse(cur)
    except Exception:
        nfm, nbody = None, None
    if nfm != want or nbody != body:
        raise CannotRename("the entries could not be taken out without changing something else")
    return cur


def _content_end(node):
    """Where a node's own text ends: after its last scalar, or after the bracket that closes a flow collection. A block
    collection's end runs on over the comments and blank lines after it, which are not its own; a block scalar's line that
    opens with `#` is the scalar's, and is inside it."""
    y = dmparse._yaml
    if isinstance(node, y.ScalarNode) or getattr(node, 'flow_style', False):
        return node.end_mark.index
    kids = [n for kv in node.value for n in kv] if isinstance(node, y.MappingNode) else list(node.value)
    return max((_content_end(n) for n in kids), default=node.start_mark.index)


def _line_end(head, i):
    """Just past the line that `head[:i]` ends on — the rest of that line, a comment on it included."""
    if i > 0 and head[i - 1] == '\n':
        return i
    nl = head.find('\n', i)
    return nl + 1 if nl >= 0 else len(head)


def _list_span(head, key_node, seq, empty):
    """(start, end, what is written there) for a whole list and its key: from the key's line to the end of the line the
    list's last entry ends on, found by the nodes as an entry is — a comment between its entries, in column 0 too, is
    inside it — and the indented comments after it, written inside its block; a blank line before what follows stays.
    With `empty='keep'` the key stays, written as it was, with `[]` and the comment its line carried."""
    ls = head.rfind('\n', 0, key_node.start_mark.index) + 1
    end = _line_end(head, _content_end(seq))
    tail = re.match(r'(?:[ \t]*\n|[ \t]+#[^\n]*\n)*', head[end:]).group(0).splitlines(keepends=True)
    while tail and not tail[-1].strip():
        tail.pop()
    end += sum(map(len, tail))
    if empty != 'keep':
        return ls, end, ''
    note = (re.match(r'([ \t]+#[^\n]*)?', head[seq.end_mark.index:]) if seq.flow_style else
            re.match(r'[ \t]*:([ \t]+#[^\n]*)?', head[key_node.end_mark.index:]))
    note = (note.group(1) if note else None) or ''
    return ls, end, f"{head[ls:key_node.end_mark.index]}: []{note}\n"


def _entry_span(head, items, i, flow):
    """[(start, end, '')] to cut for the i-th entry of a list in `head`. A block entry is its own lines, from its dash to
    the end of the line its last value ends on, a comment there with it; the comments and blank lines after that line
    belong to what follows, and a node's end runs over them, so they are left where they are."""
    if flow:
        return _flow_span(head, items, i)
    node = items[i]
    start = node.start_mark.index
    ls = head.rfind('\n', 0, start) + 1
    if not re.fullmatch(r'[ \t]*-[ \t]+', head[ls:start]):
        raise CannotRename("an entry that does not open its own line after its dash")
    return [(ls, _line_end(head, _content_end(node)), '')]


def _flow_span(head, items, i):
    """[(start, end, '')] to cut for the i-th entry of a flow list `[a, b]`: the entry and the comma that parts it from a
    neighbour — its whole line where it stands alone on one, a comment after it there its own — and never a comment on a
    line it shares with another, nor one between entries."""
    def comma_after(k):
        j = items[k].end_mark.index
        while j < len(head) and head[j] in ' \t\n':
            j += 1
        if head[j:j + 1] != ',':
            raise CannotRename("a flow list with a comment before a comma, which this step does not cut")
        return j

    def alone(a, b):
        ls = head.rfind('\n', 0, a) + 1
        m = re.match(r'[ \t]*(?:#[^\n]*)?(?:\n|$)', head[b:])
        return (ls, b + m.end(), '') if m and not head[ls:a].strip() else None

    s, e = items[i].start_mark.index, items[i].end_mark.index
    if i < len(items) - 1:
        c = comma_after(i) + 1
        gap = re.match(r'[ \t]*', head[c:]).end()
        return [alone(s, c) or (s, c + gap if head[c + gap:c + gap + 1] not in ('#', '\n', '') else c, '')]
    c = comma_after(i - 1)
    if not head[c + 1:s].strip(' \t'):                     # the comma and the entry on one line: cut together
        return [(c, e, '')]
    return [(c, c + 1, ''), alone(s, e) or (s, e, '')]


def declared_terms(law, profiles):
    """{name: term} a law declares for a garden extending `profiles` — its own terms, and those profiles' — read as the
    gate reads them, a profile's term standing over the law's own."""
    out = {}
    own = list(law.get('terms') or [])
    for p in (profiles if isinstance(profiles, list) else []):
        prof = (law.get('profiles') or {}).get(p) if isinstance(p, str) else None
        own += list((prof or {}).get('terms') or []) if isinstance(prof, dict) else []
    for t in own:
        if isinstance(t, dict) and isinstance(t.get('term'), str):
            out[t['term']] = t
    return out


def _attr_form(t):
    """A term's law keyed by attribute, through bin/dmform.py — or, for a term still spelled as before 13.0, through
    bin/dmreform.py's reader of that spelling, the only one there is."""
    sch = t.get('schema') if isinstance(t.get('schema'), dict) else {}
    return dmreform.legacy_form(t, sch) if dmreform.uses_old_term(t) else dmform.attribute_form(t, sch)


def _said(v):
    return json.dumps(v, ensure_ascii=False, default=str)


class Step23_1:
    """The translation into std-vocab 23.1: planned, and refused if it must be, before any file is touched — and made
    again at apply time on each file as the steps before it left it."""

    def __init__(self, rel, tag, keep, moves):
        """`moves`: the law the garden runs is older than the release's, so a term may have come into it since."""
        self.rel, self.tag, self.keep, self.moves = rel, tag, keep, moves
        self.law, self.problems = std_fm(rel), []
        self.leftover = False           # True: the garden crossed already, and this translates what came in since
        self.terms, self.open = [], {}  # the garden's own terms the law now declares, and what of each was not compared
        self.said = []                  # the `translated:` line's parts, as apply() makes them

    # -- what the garden holds that the law now says
    @staticmethod
    def vocab():
        """VOCAB.md's front matter as it is now — empty where it does not parse, which the gate names, not this step."""
        path = os.path.join(ROOT, 'VOCAB.md')
        try:
            return (_parse(read_text(path)[0])[0] if os.path.isfile(path) else None) or {}
        except Exception:
            return {}

    def candidates(self, vocab):
        """[(the garden's entry, the law's term)] — each `local_terms` entry for a term the release's law declares
        and the law the garden runs did not. None where the garden's own law cannot be read: every term would then look
        new, and an overlay a garden keeps on purpose would be taken for one."""
        if not self.moves:
            return []
        before = std_fm(ROOT)
        if not before.get('terms'):
            return []
        profiles = vocab.get('extends_profiles')
        now, then = declared_terms(self.law, profiles), declared_terms(before, profiles)
        return [(t, now[t['term']]) for t in (vocab.get('local_terms') or [])
                if isinstance(t, dict) and isinstance(t.get('term'), str) and t['term'] in now and t['term'] not in then]

    def closed(self, dom, vocab):
        """The values a CLOSED domain allows — its list, or the column its registry takes from the rows that pass its
        `where:`, the garden's own rows among them — or None for a domain that is no list of values."""
        if 'values' in dom:
            return list(dom['values'] or [])
        r = dom.get('registry')
        if len(dom) == 1 and isinstance(r, dict) and r.get('registry') and r.get('take') and not r.get('registry_from'):
            rows = list(self.law.get(r['registry']) or []) + list(
                ((vocab.get('registry_additions') or {}).get(r['registry']) or []) if isinstance(vocab.get('registry_additions'), dict) else [])
            return [row.get(r['take']) for row in rows if isinstance(row, dict) and dmform.row_matches(row, r.get('where'))]
        return None

    def allows(self, dom, value, vocab):
        """Whether the law's domain `dom` allows `value`, as far as the law alone can say: a closed domain by its values, a
        pattern by the law's own match; anything else is not shown to, and so is not taken to."""
        if not dom:
            return True                                     # untyped, or any: the law's leaves it open
        vals = self.closed(dom, vocab)
        if vals is not None:
            return value in vals
        if set(dom) == {'pattern'}:
            return isinstance(value, str) and bool(dmparse.law_match(dom['pattern'], value))
        return False

    @staticmethod
    def said_of(dom):
        """A domain, as a person reads it in a refusal."""
        if 'values' in dom:
            return 'one of ' + ', '.join(map(str, dom['values'] or []))
        r = dom.get('registry')
        if isinstance(r, dict) and r.get('registry'):
            where = ' and '.join(f"{k} is {json.dumps(v, default=str)}" for k, v in (r.get('where') or {}).items())
            return f"a row of `{r['registry']}`" + (f" whose {where}" if where else '')
        return ', '.join(f"{k}: {_said(v)}" for k, v in dom.items()) or 'any value'

    def beyond(self, mine, law_term, vocab):
        """What taking the garden's term out would lose — [why], none where the law's allows every value the garden's did
        and states alike every rule it stated. A closed list is held value by value; an open domain (a pattern, a type, a
        pointer) is noted in `open`, and held by the gate, which reads every bean against the law's term once the garden's
        is gone; every other rule, as written (stricter())."""
        out, name = [], mine['term']
        try:
            mine = dmreform.translate_term(mine) or mine    # a term still spelled as before 13.0, read in today's spelling
        except Exception as e:
            return [f"it could not be read ({type(e).__name__}: {e})"]
        ms = mine.get('schema') if isinstance(mine.get('schema'), dict) else {}
        ls = law_term.get('schema') if isinstance(law_term.get('schema'), dict) else {}
        if ms.get('shape') and ms.get('shape') != ls.get('shape'):
            out.append(f"it is a {ms['shape']}, and the law's a {ls.get('shape') or 'term of no shape'}")
        keys = [str(k) for k in (mine.get('context_keys') or []) if k not in (law_term.get('context_keys') or [])]
        if keys:
            out.append(f"it is read at {', '.join(f'`{k}`' for k in keys)}, where the law's is not")
        if mine.get('anchor') is not None and mine.get('anchor') != law_term.get('anchor'):
            out.append("it anchors identity as the law's does not — an anchor is ratified, never translated")
        try:
            mf, lf = _attr_form(mine), _attr_form(law_term)
        except Exception as e:
            return out + [f"it could not be read ({type(e).__name__}: {e})"]
        # THE TERM'S OWN VALUE: a closed list, its `values_add` with it as the gate reads a garden's term, value by value
        mv = {k: v for k, v in mf['value'].items() if k in VALUE_DOMAIN}
        if ms.get('values_add'):
            mv['values'] = list(mv.get('values') or []) + [v for v in ms['values_add'] if v not in (mv.get('values') or [])]
        lv = {k: v for k, v in lf['value'].items() if k in VALUE_DOMAIN}
        if mv != lv:
            if set(mv) == {'values'}:
                bad = [v for v in mv['values'] if not self.allows(lv, v, vocab)]
                if bad:
                    out.append(f"its value may be {', '.join(map(str, bad))}, which is not {self.said_of(lv)}")
            else:
                self.open.setdefault(name, []).append(None)
        # EACH ATTRIBUTE, by its domain
        for a, rec in mf['attrs'].items():
            lrec = lf['attrs'].get(a)
            if lrec is None:
                out.append(f"it has `{a}`, which the law's does not")
                continue
            md = {k: v for k, v in rec.items() if k not in NOT_A_DOMAIN}
            ld = {k: v for k, v in lrec.items() if k not in NOT_A_DOMAIN}
            if md == ld:
                continue
            mine_vals = self.closed(md, vocab)
            if mine_vals is not None:
                bad = [v for v in mine_vals if not self.allows(ld, v, vocab)]
                if bad:
                    out.append(f"`{a}` may be {', '.join(map(str, bad))}, which is not {self.said_of(ld)}")
                continue
            if set(md) & {'aspect', 'entries', 'bean_id'} or set(ld) & {'aspect', 'entries', 'bean_id'}:
                out.append(f"`{a}` is {self.said_of(md)}, and the law's {self.said_of(ld)}: which of them a value may be "
                           f"is no list this step can hold one to the other")
                continue
            self.open.setdefault(name, []).append(a)
        return out + self.stricter(mine, law_term)

    @staticmethod
    def stricter(mine, law_term):
        """[why] — each rule the garden's term states that the law's does not state alike, which taking the garden's out
        would lose: a schema key no value holds (`required_on_gene`, `only_on_gene`, a cell), a field of an attribute
        besides its domain (`required`, where the law's attribute is not), and how its entries merge."""
        out = []
        ms = mine.get('schema') if isinstance(mine.get('schema'), dict) else {}
        ls = law_term.get('schema') if isinstance(law_term.get('schema'), dict) else {}
        for k, v in ms.items():
            if k not in BY_VALUE and ls.get(k) != v:
                out.append(f"it says `{k}: {_said(v)}`, " + (f"and the law's `{k}: {_said(ls[k])}`" if k in ls else
                                                             "which the law's does not"))
        la = ls.get('attrs') if isinstance(ls.get('attrs'), dict) else {}
        for a, rec in (ms.get('attrs') if isinstance(ms.get('attrs'), dict) else {}).items():
            lrec = la.get(a)
            if not isinstance(rec, dict) or not isinstance(lrec, dict):
                continue                                    # an attribute the law's lacks is named with the domains
            for f, v in rec.items():
                if f in ('in', 'meaning') or lrec.get(f) == v or (f == 'required' and v is not True):
                    continue
                out.append(f"`{a}` is required, and the law's is not" if f == 'required' else
                           f"`{a}` says `{f}: {_said(v)}`, " + (f"and the law's `{f}: {_said(lrec[f])}`" if f in lrec else
                                                                "which the law's does not"))
        if mine.get('merge') is not None and mine.get('merge') != law_term.get('merge'):
            out.append(f"its entries merge as `{_said(mine['merge'])}`, and the law's as `{_said(law_term.get('merge'))}`")
        return out

    # -- where the law places a file the garden placed otherwise
    def map(self):
        """The layer map of the release's law over this garden's files and the entries its beans and mappings carry."""
        def read(p):
            base = self.rel if p in (dmpass.LAW, dmpass.LANGUAGE) else ROOT
            path = os.path.join(base, *p.split('/'))
            try:
                return read_text(path)[0]
            except (OSError, UnicodeDecodeError):
                return None
        try:
            return dmpass.Map(read, dmpass.tracked(ROOT))
        except ValueError as e:
            refuse(f"{self.tag}'s law gives no layer map to place this garden's files by: {e}")

    def placements(self):
        """({document: [(index, key, doc, the garden's layer, the law's layer, path)]}, [problem]) — each entry of a bean or
        a mapping that places a file where the law places it otherwise: to take out where the law places every file it
        places and none of them leaves the RULE-CHANGE duty by it, and a person's where it does, or where it places files
        the law does not. The key that holds the entry is read from the document, as the entry bin/dmpass.py read there:
        the step names no term."""
        m, cuts, problems = self.map(), {}, []
        held = {(f, i): e for f, i, e in m.standing}
        for f, i, doc, mine, law, path in m.standing_conflicts():
            places = [p for p in m.files if (f, i) in [(g, j) for _l, g, j in m.garden_layers_of(p)]] or [path]
            unplaced = [p for p in places if not m.law_layer_of(p)]
            if unplaced:
                problems.append(f"{f}: the entry {doc} places {path} in {mine}, where the law places it in {law}, and "
                                f"also places {len(unplaced)} file(s) the law does not ({', '.join(unplaced[:5])}"
                                f"{', …' if len(unplaced) > 5 else ''}) — narrowing it is a person's decision")
                continue
            # A FILE THE GARDEN RULED STAYS RULED, or a person decides it: a change to a file in `law` or `manifesto` is a
            # RULE-CHANGE, so an entry that put one there, taken out where the law places the file in no such layer and
            # the release does not keep it, would let the next change to it through unjournalled.
            freed = [p for p in places if mine in dmpass.RULED and m.law_layer_of(p) not in dmpass.RULED
                     and m.keeper_of(p) != 'release']
            if freed:
                problems.append(f"{f}: the entry {doc} places {', '.join(freed[:5])}{', …' if len(freed) > 5 else ''} in "
                                f"{mine}, where the law places {'it' if len(freed) == 1 else 'them'} in "
                                f"{', '.join(sorted({m.law_layer_of(p) for p in freed}))} — taking it out would take "
                                f"{'that file' if len(freed) == 1 else 'those files'} off the RULE-CHANGE duty a file in "
                                f"{mine} carries, which is a person's decision: take the entry out, or keep the file "
                                f"ruled by proposing its place to the law")
                continue
            fm = _parse(read_text(os.path.join(ROOT, *f.split('/')))[0])[0] or {}
            keys = [k for k, v in fm.items() if isinstance(v, list) and i < len(v) and v[i] == held[(f, i)]]
            if len(keys) != 1:
                problems.append(f"{f}: the entry {doc} could not be found where it was read — take it out by hand")
                continue
            cuts.setdefault(f, []).append((i, keys[0], doc, mine, law, path))
        return cuts, problems

    def left(self):
        """Whether there is anything for this step where the garden does not cross into 23.1: an entry merged in after it
        crossed that places a file where the law places it otherwise, or — where the law moves on — another term of the
        garden's own it now declares."""
        cuts, problems = self.placements()
        self.leftover = bool(cuts or problems or self.candidates(self.vocab()))
        return self.leftover

    def plan(self):
        vocab = self.vocab()
        for mine, law_term in self.candidates(vocab):
            why = self.beyond(mine, law_term, vocab)
            if why:
                self.problems.append(f"VOCAB.md: `local_terms` `{mine['term']}` is a term {self.tag}'s law now declares, "
                                     f"and taking the garden's out would lose what the law's does not say — "
                                     f"{'; '.join(why)}. Which stands is a person's decision: take the garden's out and "
                                     f"keep the law's; or keep only what it adds, as an overlay on the law's term once "
                                     f"the garden has crossed (--keep-on-failure crosses and leaves it for that); or "
                                     f"propose what it adds to the law")
            else:
                self.terms.append(mine['term'])
        cuts, problems = self.placements()
        self.problems += problems
        # EACH DOCUMENT IS PROVED NOW, while nothing is touched: a list this step cannot take an entry out of is refused
        for path, cut, empty in self.edits(vocab, cuts):
            try:
                without_entries(read_text(path)[0], cut, empty)
            except CannotRename as e:
                self.problems.append(f"{os.path.relpath(path, ROOT).replace(os.sep, '/')}: {e} — take them out by hand")
        if self.problems and not self.keep:
            refuse(f"{'at' if self.leftover else 'crossing into'} std-vocab {vocab_version(self.rel)}, "
                   f"{len(self.problems)} thing(s) are a person's to do, not a translation's:\n"
                   + '\n'.join('  - ' + p for p in self.problems) +
                   "\nDo them and commit, then run this again — or pass --keep-on-failure to apply the rest and "
                   "leave these, named, for the person.")

    def gone_vacancies(self, vocab):
        """The indexes of the vacancies VOCAB.md declares at a position of a term this step takes out: `at` the term, or
        a path under it."""
        return [i for i, v in enumerate(vocab.get('vacancies') or []) if isinstance(v, dict)
                and any(str(v.get('at')) == t or str(v.get('at')).startswith(t + '.') for t in self.terms)]

    def edits(self, vocab, cuts):
        """[(path, {key: {index}}, what an emptied list becomes)] — VOCAB.md's, and each bean's or mapping's."""
        out = []
        idx = {i for i, t in enumerate(vocab.get('local_terms') or []) if isinstance(t, dict) and t.get('term') in self.terms}
        if idx:
            vcut = {'local_terms': idx}
            if self.gone_vacancies(vocab):
                vcut['vacancies'] = set(self.gone_vacancies(vocab))
            out.append((os.path.join(ROOT, 'VOCAB.md'), vcut, 'keep'))
        for f, entries in sorted(cuts.items()):
            by = {}
            for i, key, *_rest in entries:
                by.setdefault(key, set()).add(i)
            out.append((os.path.join(ROOT, *f.split('/')), by, 'drop'))
        return out

    def compared(self, t):
        """What the `translated:` line says of what the law's term allows: everything, where every domain was compared,
        and otherwise which of them were not — held by the gate, never claimed."""
        gone = self.open.get(t)
        if not gone:
            return f"`{t}`: the law's allows every value the garden's allowed"
        names = ', '.join('its own value' if a is None else f"`{a}`" for a in gone)
        return (f"`{t}`: {names} not compared, the law's own domain holding {'it' if len(gone) == 1 else 'them'} now, "
                f"which the gate held every bean to; every other value the garden's allowed, the law's allows")

    def apply(self):
        """Writes what was planned, on each file as the steps before it left it. Returns the `translated:` text, the ids of
        the beans and mappings it touched, and whether VOCAB.md was written. Each part names the KEY it took entries from,
        as a person reading the journal — and the hook, which refuses a key emptied with nothing said of it — reads it."""
        vocab, touched, wrote = self.vocab(), [], False
        vac = [vocab['vacancies'][i] for i in self.gone_vacancies(vocab)]
        cuts, _problems = self.placements()
        for path, cut, empty in self.edits(vocab, cuts):
            rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
            text, form = read_text(path)
            try:
                new = without_entries(text, cut, empty)
            except CannotRename as e:
                why = f"{rel}: {e} — take them out by hand"
                if why not in self.problems:
                    self.problems.append(why)
                continue
            if rel == 'VOCAB.md':
                orphans = self.orphaned(_parse(text)[0], _parse(new)[0])
                write_text(path, new, form)
                wrote, it = True, 'them' if len(self.terms) > 1 else 'it'
                self.said.append(
                    f"VOCAB.md `local_terms`: the garden's own {'terms' if len(self.terms) > 1 else 'term'} "
                    + ', '.join(f"`{t}`" for t in self.terms) + f" taken out — {self.tag}'s law declares {it} now; "
                    + '; '.join(self.compared(t) for t in self.terms))
                if vac:
                    self.said.append(f"VOCAB.md `vacancies`: the {'vacancies' if len(vac) > 1 else 'vacancy'} declared on "
                                     f"{it} taken out with {it}: " + ', '.join(f"{v.get('at')} = {v.get('position')}" for v in vac))
                if orphans[1]:
                    self.said.append(f"{orphans[0]}, the garden's own reasons, NOT EDITED: "
                                     + ', '.join(f"`## {k}`" for k in orphans[1])
                                     + f" {'explain' if len(orphans[1]) > 1 else 'explains'} what VOCAB.md no longer "
                                     "holds — for a person to move to the journal, or remove")
                continue
            write_text(path, new, form)
            ident = Step21._id(path)
            touched.append(ident)
            for key in sorted(cut):
                self.said.append(f"{ident} `{key}`: " + '; '.join(
                    f"the entry {doc} ({mine}) taken out — the law places {placed} in {law}"
                    for _i, k, doc, mine, law, placed in sorted(cuts[rel]) if k == key))
        if self.problems:
            self.said.append("LEFT FOR A PERSON: " + '; '.join(self.problems))
        return (f"std-vocab {vocab_version(self.rel)}, what the law now says itself — "
                + '; '.join(self.said or ['nothing to translate'])), touched, wrote

    @staticmethod
    def orphaned(before, after):
        """(the garden's reasoning file, [the keys of its headings that named something VOCAB.md held before this step and
        no longer does]) — read by bin/dmwhy.py, the one tool that opens the reasoning; (None, []) where there is none."""
        sys.path.insert(0, os.path.join(ROOT, 'bin'))
        import dmwhy
        for law, why in dmwhy.each_pair():
            if law != 'VOCAB.md':
                continue
            out = []
            for key in dmwhy.rationale():
                try:
                    dmwhy.resolve(before or {}, key)
                except KeyError:
                    continue
                try:
                    dmwhy.resolve(after or {}, key)
                except KeyError:
                    out.append(key)
            return why.replace(os.sep, '/'), out
        return None, []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tag', help='the release tag, e.g. v0.3.0')
    ap.add_argument('--from', dest='src', default=UPSTREAM, help=f'repository URL or path (default {UPSTREAM})')
    ap.add_argument('--allow-downgrade', action='store_true', help='adopt a tag older than the one GARDEN.md records')
    ap.add_argument('--garden', help='the garden to upgrade (default: the one this tool lives in)')
    ap.add_argument('--keep-on-failure', action='store_true', help='leave the files in place when the gate fails, to repair by hand')
    ap.add_argument('--gardener', help='crossing into std-vocab 21.0: the id of the person or org bean who keeps this garden '
                                       '(or DAFTAR_GARDENER in the environment)')
    ap.add_argument('--gardener-name', help='with --gardener, plants a new bean with this name '
                                            '(or DAFTAR_GARDENER_NAME in the environment)')
    ap.add_argument('--gardener-genos', '--gardener-kind', dest='gardener_genos',
                    help="with --gardener-name, the genos of the bean planted, one the law lets keep a garden: org for an "
                         "organisation (or DAFTAR_GARDENER_GENOS in the environment; default: a person, as "
                         "seed/germinate.py plants one). `--gardener-kind` and DAFTAR_GARDENER_KIND, the names before "
                         "22.0, are read the same")
    ap.add_argument('--no-delegate', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('--recorded-source', help=argparse.SUPPRESS)
    a, unknown = ap.parse_known_args()
    global ROOT
    if a.garden:
        ROOT = os.path.abspath(a.garden)
    source = a.recorded_source or a.src
    # each value with WHERE IT CAME FROM, which is what every message about it names
    gardener = ((a.gardener, '--gardener') if a.gardener else
                (os.environ[ENV_ID], ENV_ID) if os.environ.get(ENV_ID) else (None, None))
    gardener += ((a.gardener_name, '--gardener-name') if a.gardener_name else
                 (os.environ[ENV_NAME], ENV_NAME) if os.environ.get(ENV_NAME) else (None, None))
    ggenos = ((a.gardener_genos, '--gardener-genos') if a.gardener_genos else
              (os.environ[ENV_GENOS], ENV_GENOS) if os.environ.get(ENV_GENOS) else
              (os.environ[ENV_KIND], ENV_KIND) if os.environ.get(ENV_KIND) else (None, None))

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
            if a.gardener_genos:
                args += ['--gardener-genos', a.gardener_genos]
            return subprocess.run(args + unknown).returncode
        if unknown:
            ap.error(f"unrecognized arguments: {' '.join(unknown)}")

        if vocab_version(rel) in ('None', ''):
            sys.exit(f"REFUSING: {a.tag} carries no readable `version:` in seed/std-vocab.md — nothing to pin to.")
        before = vocab_version(ROOT)
        check_name(rel, a.tag, a.keep_on_failure)
        # THE 21.0 AND 22.0 STEPS ARE PLANNED FIRST, while every file is still as it was, so a refusal touches nothing.
        step21 = step22 = None
        if vtuple(before) < STEP_21 <= vtuple(vocab_version(rel)):
            step21 = Step21(rel, a.tag, source, gardener, a.keep_on_failure, ggenos)
            step21.plan()
        # ...and a garden that crossed already is translated again where a document still says 21.0's words: a bean a
        # branch or a clone still at 21.0 added, merged in afterwards, or a proposal written from 21.0's documents.
        if STEP_22 <= vtuple(vocab_version(rel)):
            _s22 = Step22(rel, a.tag, a.keep_on_failure)
            if vtuple(before) < STEP_22 or _s22.left():
                step22 = _s22
                step22.plan()
        # ...and so is one where a bean still places a file the law places otherwise, or the law declares a term the garden
        # kept of its own: the terms are read from the two laws, so the step is planned while the garden's own is here.
        step23 = None
        if STEP_23_1 <= vtuple(vocab_version(rel)):
            _s23 = Step23_1(rel, a.tag, a.keep_on_failure, vtuple(before) < vtuple(vocab_version(rel)))
            if vtuple(before) < STEP_23_1 or _s23.left():
                step23 = _s23
                step23.plan()
        want = expand(rel, patterns(rel))
        have = expand(ROOT, patterns(ROOT)) if os.path.isfile(os.path.join(ROOT, 'seed', 'LANGUAGE')) else set()
        # "applied" when either side is unknown: a garden that records no release cannot be told which way it moved.
        verb = ('applied' if not (cur_v and new_v) else
                'downgraded' if tuple(map(int, new_v.groups())) < tuple(map(int, cur_v.groups())) else 'upgraded')
        added = []
        # FROM THE FIRST COPY TO THE GATE'S VERDICT, A FAILURE OF ANY KIND PUTS EVERYTHING BACK — not only the gate's.
        # An exception midway (a file an editor, the indexer or antivirus holds open on Windows, where os.replace then
        # fails) once left release files copied, both pins moved, beans half translated and no journal entry.
        try:
            return apply_release(a, rel, sha, source, current, before, verb, want, have, added, step21, step22, step23)
        except BaseException as e:
            put_back(added + (step21.created if step21 else []))
            print(f"NOT {verb.upper()}: the upgrade stopped midway"
                  + ('' if isinstance(e, SystemExit) else f" ({type(e).__name__}{': ' + str(e) if str(e) else ''})")
                  + ", so every file was put back as it was.", file=sys.stderr, flush=True)
            raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def put_back(added):
    """Every file as it was: the tree was clean when the upgrade began, so git holds each one, and what the upgrade
    added is removed. Then the garden's own hooks and merge driver again, from the release it still runs."""
    run('git', 'checkout', '--', '.', check=False)
    for f in added:
        for p in (os.path.join(ROOT, f), os.path.join(ROOT, f) + '.tmp'):
            try:
                os.remove(p)
            except OSError:
                pass
    install()


def apply_release(a, rel, sha, source, current, before, verb, want, have, added, step21, step22=None, step23=None):
    """Steps 3 to 8: the files, the pins, the translations, the installer, the journal and the gate. `added` is the
    caller's list, filled as files arrive, so that whatever stops this midway is put back whole."""
    changed = []
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
        text, form = read_text(path)
        pins = PIN.findall(text)
        if len(pins) != 1:
            sys.exit(f"REFUSING to guess: {doc} carries {len(pins)} `extends: std-vocab@` pins, expected 1.")
        if pins[0][1] != after:
            write_text(path, PIN.sub(rf'\g<1>{after}', text, count=1), form)
            repinned.append(doc)

    # THE GARDEN'S OWN TERMS ARE TRANSLATED, NEVER REWRITTEN BY HAND (13.0). When a release changes how the law
    # is SPELLED, a garden's `local_terms` are in the old spelling and the new gate refuses them. The release
    # ships the translator; it is a pure function of each term, it proves per term that the form it reads is
    # unchanged, and it leaves the file alone when it cannot. A refusal surfaces through the gate below, which
    # then puts everything back.
    translated, reform = [], os.path.join(ROOT, 'bin', 'dmreform.py')
    # 22.0's names go into VOCAB.md FIRST: the terms dmreform reads are then in the spelling the release's reader knows.
    if step22:
        step22.apply(vocab_only=True)
        if 'VOCAB.md' in step22.facts and 'VOCAB.md' not in changed:
            changed.append('VOCAB.md (translated)')
        if step22.reasons:
            changed.append(f'{step22.reasons} (re-keyed)')
    if os.path.isfile(reform):
        _r = run(sys.executable, reform, os.path.join(ROOT, 'VOCAB.md'), check=False)
        _out = (_r.stdout + _r.stderr).strip()
        if _r.returncode != 0:
            translated.append('REFUSED — ' + _out.replace(ROOT + os.sep, ''))
        elif 'term(s) rewritten' in _out and ': 0 term' not in _out and 'rewritten —' in _out:
            translated.append('VOCAB.md local_terms — ' + _out.split('rewritten —', 1)[1].strip())
            if 'VOCAB.md' not in changed and 'VOCAB.md (translated)' not in changed:
                changed.append('VOCAB.md (translated)')

    gpath = os.path.join(ROOT, 'GARDEN.md')
    gtext, gform = read_text(gpath)
    gline = f'daftar_release: "{a.tag}"  # the daftar release this garden runs; bin/dmupgrade.py moves it'
    if recorded_release() != a.tag:
        if RELEASE.search(gtext):
            gtext = RELEASE.sub(gline, gtext, count=1)
        else:
            # after the WHOLE pin line: inserting after the match split the line and moved its comment
            gtext = re.sub(r'^extends: std-vocab@.*$', lambda m: m.group(0) + '\n' + gline, gtext, count=1, flags=re.M)
        write_text(gpath, gtext, gform)
        repinned.append('GARDEN.md daftar_release')

    beans, steps = [], []
    if step21:
        _t, beans = step21.apply()
        translated.append(_t); steps.append(_t)
        added += step21.created
    if step22:
        # AFTER the 21.0 step, on each bean as that step left it: a gardener it planted is in 22.0's words already
        _t, _b = step22.apply()
        translated.append(_t); steps.append(_t)
        beans += [b for b in _b if b not in beans]
    if step23:
        # LAST, on each file as every step before it left it, and on VOCAB.md after bin/dmreform.py read the garden's terms
        _t, _b, _vocab = step23.apply()
        translated.append(_t); steps.append(_t)
        beans += [b for b in _b if b not in beans]
        if _vocab and 'VOCAB.md' not in changed and 'VOCAB.md (translated)' not in changed:
            changed.append('VOCAB.md (translated)')

    if not (changed or added or removed or repinned or beans):
        # NOTHING MOVED IS NOT NOTHING TO DO. With --keep-on-failure a step that could translate nothing still names what
        # it left for a person, and the gate still refuses the garden for it: saying "nothing to do" hid both.
        left = [p for s in (step22, step23) if s for p in s.problems]
        if left:
            print(f"NOTHING TRANSLATED: this garden runs {a.tag} ({sha[:12]}) already, and {len(left)} thing(s) are a "
                  f"person's to do, not a translation's:\n" + '\n'.join('  - ' + p for p in left) +
                  "\nDo them and commit, then run this again. Nothing was touched.")
            return 1
        print(f"nothing to do: this garden's language already equals {a.tag} ({sha[:12]}).")
        return 0
    # ONLY WORDS MOVED: the garden runs this release already, and what changed is the translation of what came in since it
    # crossed. The law did not move and nothing is a person's to decide — the translation is the one the garden adopted
    # when it crossed — so the entry asks nothing, and says RULE-CHANGE only where VOCAB.md itself was translated.
    ran = [s for s in (step22, step23) if s]
    words_only = bool(ran and all(s.leftover for s in ran) and not (added or removed or repinned)
                      and all(c.endswith(('(translated)', '(re-keyed)')) for c in changed))
    since = ' and '.join(w for s, w in ((step22, "into std-vocab 22.0 still in 21.0's words"),
                                        (step23, "into std-vocab 23.1 still placing a file where the law places it "
                                                 "otherwise")) if s)
    if words_only:
        verb = 'translated'

    install()
    sys.path.insert(0, os.path.join(ROOT, 'bin')); import dmjournal          # the release's own tool, just applied
    _who = run('git', 'config', 'user.name', check=False).stdout.strip() or '(fill in who ran it)'
    if words_only:
        lines = ['\n' + dmjournal.stamp(_who, ("RULE-CHANGE: " if changed else '') + f"translated into the words of "
                                        f"daftar {a.tag}, which this garden runs", ROOT),
                 f"- action: `bin/dmupgrade.py {a.tag}` from {source} at {sha}; the language is unchanged (std-vocab "
                 f"{after}, release {a.tag}). What came in after the garden crossed {since} — from a branch or a clone "
                 f"merged since, or a proposal — is translated as the crossing translated the rest.",
                 f"- changed: {', '.join(changed) or 'none'}",
                 f"- translated: {'; '.join(translated) or 'none'}",
                 f"- beans: {', '.join(beans) or 'none'}"]
    else:
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
    with open(jpath, 'a', encoding='utf-8', newline=read_text(jpath)[1].nl) as j:
        j.write('\n'.join(lines) + '\n')

    gate = run(sys.executable, os.path.join(ROOT, 'bin', 'dmcheck.py'), check=False)
    if gate.returncode != 0 and not a.keep_on_failure:
        # PUT IT ALL BACK. The tree was clean before we started, so git holds every file as it was. A cold-start
        # drill downgraded a garden that used a profile the older release lacks, and was left half-applied.
        put_back(added)
        errs = [l for l in gate.stdout.splitlines() if l.startswith('ERROR')]
        if not errs:        # the gate stopped without a verdict (a crash): what it said on the way out is the reason
            errs = ['the gate stopped without naming an error; the last it said:'] + \
                   ['  ' + l for l in (gate.stderr.strip() or gate.stdout.strip() or '(nothing)').splitlines()[-8:]]
        errs[:0] = ['dmreform ' + t for t in translated if t.startswith('REFUSED')]
        print(f"NOT {verb.upper()}: under {a.tag} this garden fails its own gate, so every file was put back as it was.\n"
              + '\n'.join(errs[:12]) + ('\n…' if len(errs) > 12 else '') +
              "\nFix what these name (or pass --keep-on-failure to repair by hand), then run this again.")
        return 1
    print(f"translated into the words of {a.tag} ({sha[:12]}), which this garden runs: std-vocab {after}, the language "
          f"unchanged." if words_only else f"{verb} to {a.tag} ({sha[:12]}): std-vocab {before} -> {after}; "
          f"{len(changed)} changed, {len(added)} added, {len(removed)} removed, {len(repinned)} repinned.")
    for _t in steps:
        print(f"translated: {_t}")
    print((gate.stdout.strip().splitlines() or ['(the gate printed nothing)'])[-1])
    # TWO COMMANDS, NOT ONE JOINED BY `&&`, and no `rm`: Windows PowerShell 5.1 parses neither `&&` nor `rm a b`, and
    # git runs alike in every shell — `git clean` removes exactly the files the upgrade added, which git has never held.
    print("\nNOT COMMITTED. Read `git diff`" + (", then\n" if words_only else ", complete the journal entry's two `fill in` fields, then\n") +
          "  git add -A\n"
          "  git commit\n"
          "To abandon it instead:\n"
          "  git checkout -- ." + (f"\n  git clean -f -- {' '.join(_arg(f) for f in added)}" if added else ""))
    return 0 if gate.returncode == 0 else 1


def install():
    """The release's installer, run by this interpreter: hooks and the merge driver may have changed. `sh` is not a
    given on Windows; bin/install.py is the one installer, and install.sh only hands over to it."""
    if os.path.isfile(os.path.join(ROOT, 'bin', 'install.py')):
        run(sys.executable, os.path.join(ROOT, 'bin', 'install.py'), check=False)
    elif shutil.which('sh'):
        run('sh', os.path.join(ROOT, 'bin', 'install.sh'), check=False)   # a release from before install.py


if __name__ == '__main__':
    for _s in (sys.stdout, sys.stderr):      # what the console's code page lacks is shown escaped, never a crash
        try:
            _s.reconfigure(errors='backslashreplace')
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
