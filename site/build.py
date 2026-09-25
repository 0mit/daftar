#!/usr/bin/env python3
"""site/build.py — the site's pages, filled with what daftar's tools print on two demo gardens.

WHAT IT DOES. Clones this repository at the release `site/RELEASE` names and grows two gardens from the clone with
`seed/germinate.py`: garden-sam, kept by sam, and garden-ali, kept by ali. It commits the recipes of
`seed/COOKBOOK.md` into garden-sam one at a time, as `test/germinate.py` does, and runs the scenes the pages show —
the commands as they were run, and their output verbatim. Then it writes each output into the pages, between its
markers, and nothing outside them:

    <!-- daftar:<type> id="<id>" [steps="2,3"] [lines="1-3,7"] [match="<regex>"] [head="N"] [tail="N"] -->…<!-- /daftar:<type> -->

  out    a command block: `~/garden-sam$ <command>`, then what it printed      bean   a file of a garden
         (`steps` picks commands of a block; the line options pick lines of what each printed)
  file   an input the build wrote                                              doc    an extract of a release document
  svg    site/drawings/<id>.svg, inline                                        part   site/_parts/<id>.html
  drawn  the record of the machinery's drawing, site/machinery/drawn.json

The committed pages are the templates. A marker whose id nothing produces, or a capture no page uses, fails the build.

WHAT IT HOLDS STILL. Every tool reads its clock as 2026-10-27 09:00 UTC (`site/demo/clock/`), git's dates are pinned,
HOME is a temporary directory, and each garden commits as its gardener. What still differs in every build is a
garden's id — germination writes a random seed into the first commit — and every fingerprint and qualified name that
carries one: each is wrapped in `<span class="v">`, and a test compares the pages with those spans blanked. The
temporary root is shown as `~`. A capture that holds this machine's host name, the user's name or home fails the
build: nothing is scrubbed silently.

    python3 site/build.py [--out DIR] [--machinery CHECKOUT] [--keep DIR]

  --out DIR            write the whole site to DIR (empty or absent), and leave site/ untouched
  --machinery CHECKOUT after the scenes, run site/machinery/build.py CHECKOUT on the demo garden-sam; without it the
                       machinery page keeps the drawing committed with it, and says when that was drawn
  --keep DIR           grow the gardens in DIR (empty or absent) and leave them there, with captures.json

Exit 0 built; 1 a scene's expected result did not hold, a marker and a capture do not match, or a capture holds this
machine's name; 2 setup (no git, no PyYAML, or site/RELEASE is not a tag of this repository). Needs Python 3 with
PyYAML, and git. It takes a minute or two.
"""
import argparse, getpass, html, json, os, re, shlex, shutil, site as _site, socket, subprocess, sys, tempfile

SITE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SITE)
CLOCK = os.path.join(SITE, 'demo', 'clock')
DEMO_NOW = '2026-10-27T09:00:00+00:00'
DEMO_SHOWN = '2026-10-27 09:00 UTC'
PY = sys.executable
GITHUB = 'https://github.com/0mit/daftar'


class Refused(Exception):
    """A scene's expected result did not hold, or the pages and the captures do not match: exit 1."""


class Setup(Exception):
    """Something the build needs is missing: exit 2."""


def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=True)


# ─── the demo root ────────────────────────────────────────────────────────────────────────────────────────────────

def git_out(*a, cwd=REPO):
    r = subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout.strip()


def semver(tag):
    m = re.fullmatch(r'v(\d+)\.(\d+)\.(\d+)', tag)
    return tuple(int(x) for x in m.groups()) if m else None


def setup():
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        raise Setup('git is not on PATH')
    try:
        import yaml  # noqa: F401 — the tools need it; so does the machinery record
    except ImportError:
        raise Setup('PyYAML is required: pip install PyYAML')
    release = open(os.path.join(SITE, 'RELEASE'), encoding='utf-8').read().strip()
    if not semver(release):
        raise Setup(f'site/RELEASE says {release!r}, which is not a release tag (vMAJOR.MINOR.PATCH)')
    code, _ = git_out('rev-parse', '-q', '--verify', f'refs/tags/{release}^{{commit}}')
    if code != 0:
        raise Setup(f'site/RELEASE names {release}, which is not a tag of this repository (git fetch --tags?)')
    _, common = git_out('rev-parse', '--path-format=absolute', '--git-common-dir')
    _, tags = git_out('tag', '-l', 'v*')
    newer = sorted((t for t in tags.split() if semver(t) and semver(t) > semver(release)), key=semver)
    if newer:
        print(f'notice: {newer[-1]} is newer than site/RELEASE ({release}); bump site/RELEASE and build again')
    return release, common


def demo_env(T):
    """The environment every command of the demo runs in: nothing of the caller's git, daftar or Python settings."""
    home = os.path.join(T, '.home')
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('DAFTAR_', 'GIT_', 'PYTHON', 'XDG_')) and k not in ('LANGUAGE', 'LC_ALL', 'LANG')}
    env.update(HOME=home, XDG_CONFIG_HOME=os.path.join(home, '.config'), GIT_CONFIG_NOSYSTEM='1', TZ='UTC',
               LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1',
               PYTHONUSERBASE=_site.getuserbase(), PYTHONPATH=CLOCK, DAFTAR_DEMO_NOW=DEMO_NOW,
               GIT_AUTHOR_DATE=DEMO_NOW, GIT_COMMITTER_DATE=DEMO_NOW, TMPDIR=os.path.join(T, '.tmp'))
    os.makedirs(os.path.join(home, '.config'), exist_ok=True)
    os.makedirs(env['TMPDIR'], exist_ok=True)
    with open(os.path.join(home, '.gitconfig'), 'w', encoding='utf-8') as f:
        f.write('[init]\n\tdefaultBranch = master\n[advice]\n\tdetachedHead = false\n')
    return env


def q(s):
    """A shell word as a person would type it: bare, or in double quotes when that needs no escape."""
    if re.fullmatch(r'[A-Za-z0-9_./:@%+=,-]+', s) or re.fullmatch(r'~/[A-Za-z0-9_./-]*', s):
        return s
    if not re.search(r'["$`\\!]', s):
        return '"' + s + '"'
    return shlex.quote(s)


class Demo:
    """Runs commands in the demo root and keeps what they print, by capture id."""

    def __init__(self, T, env, release):
        self.T, self.env, self.release = T, env, release
        self.real = {T, os.path.realpath(T)}
        self.caps = {}
        self.step = 'setup'
        self.ids = {}          # garden name -> id, as `dmpropose id` printed it
        self.fps = set()       # fingerprints of proposals
        self.ms = set()        # taken_at moments in milliseconds (read from the machine's clock)

    # paths
    def p(self, *parts):
        return os.path.join(self.T, *parts)

    def shown(self, path):
        rel = os.path.relpath(path, self.T)
        return '~' if rel == '.' else '~/' + rel.replace(os.sep, '/')

    def clean(self, text):
        for r in sorted(self.real, key=len, reverse=True):
            text = text.replace(r, '~')
        return text.strip('\n')                   # the blank lines around an output; every line of it is kept

    # running
    def sh(self, cwd, cmd, expect=0):
        """Run `cmd` as it is shown; `python3` is this Python, a leading `~` the demo root."""
        argv = [re.sub(r'^~(?=/|$)', lambda m: self.T, a) for a in shlex.split(cmd)]
        if argv[0] == 'python3':
            argv[0] = PY
        r = subprocess.run(argv, cwd=cwd, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, encoding='utf-8', errors='replace')
        if expect is not None and r.returncode != expect:
            raise Refused(f'{self.step}: `{cmd}` in {self.shown(cwd)} exited {r.returncode}, expected {expect}\n'
                          + self.clean(r.stdout)[-2500:])
        return r.returncode, self.clean(r.stdout)

    def put(self, cid, cap):
        if cid in self.caps:
            raise Refused(f'{self.step}: capture {cid!r} made twice')
        cap['step'] = self.step
        self.caps[cid] = cap
        return cap

    def out(self, cid, cwd, *cmds, expect=0):
        """A command block: each command with what it printed. `expect` is the last command's exit code."""
        steps = []
        for i, c in enumerate(cmds):
            wd, c = c if isinstance(c, tuple) else (cwd, c)
            code, text = self.sh(wd, c, expect=expect if i == len(cmds) - 1 else 0)
            steps.append({'cwd': self.shown(wd), 'cmd': c, 'out': text, 'exit': code})
        self.put(cid, {'type': 'out', 'steps': steps})
        return steps[-1]['out']

    def bean(self, cid, garden, rel):
        text = open(os.path.join(garden, rel), encoding='utf-8').read().rstrip('\n')
        return self.put(cid, {'type': 'bean', 'label': rel, 'text': text})

    def file(self, cid, label, text):
        return self.put(cid, {'type': 'file', 'label': 'input: ' + label, 'text': text.rstrip('\n')})

    def doc(self, cid, html_text):
        return self.put(cid, {'type': 'doc', 'html': html_text})

    def expect(self, cond, what):
        if not cond:
            raise Refused(f'{self.step}: {what}')

    # the way the cookbook commits
    def commit(self, g, who, what, body, cid=None, expect=0):
        """Journal, stage and commit, as the cookbook teaches; a commit expected to pass must pass clean."""
        cmds = [f'python3 bin/dmjournal.py {who} {q(what)} --body {q(body)}', 'git add -A', f'git commit -qm {q(what)}']
        if cid:
            text = self.out(cid, g, *cmds, expect=expect)
        else:
            for i, c in enumerate(cmds):
                code, text = self.sh(g, c, expect=expect if i == 2 else 0)
        if expect == 0:
            m = re.search(r'\): \d+ docs, (\d+) error\(s\), (\d+) warning\(s\)', text)
            self.expect(m and m.groups() == ('0', '0'), f'the commit "{what}" did not pass clean:\n{text[-800:]}')
        return text

    def gate_line(self, g):
        _, text = self.sh(g, 'python3 bin/dmcheck.py --all', expect=None)
        return text.splitlines()[-1] if text else ''

    def clean_gate(self, g):
        line = self.gate_line(g)
        self.expect(line.endswith('0 error(s), 0 warning(s)'), f'the gate of {self.shown(g)} is not clean: {line}')

    def write(self, path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text if text.endswith('\n') else text + '\n')

    def clone(self, src, dst, who):
        self.sh(self.T, f'git clone -q {self.shown(src)} {self.shown(dst)}')
        self.sh(dst, f'git config user.name {who}')
        self.sh(dst, f'git config user.email {who}@example.org')
        self.sh(dst, 'python3 bin/install.py')


# ─── the documents of the release ─────────────────────────────────────────────────────────────────────────────────

def md_sections(text):
    """{heading: body} for the `## ` sections of a Markdown document; the part before the first is ''."""
    out, cur, buf = {}, '', []
    fence = None
    for line in text.split('\n'):
        m = re.match(r'^(`{3,})', line)
        if m:
            fence = None if fence and m.group(1) == fence else (fence or m.group(1))
        if fence is None and line.startswith('## '):
            out[cur] = '\n'.join(buf)
            cur, buf = line[3:].strip(), []
            continue
        buf.append(line)
    out[cur] = '\n'.join(buf)
    return out


def md_blocks(body):
    """The blocks of a section, in order: (kind, lines). Kinds: para, list, table, fence, quote, code, head."""
    lines, i, blocks = body.split('\n'), 0, []
    while i < len(lines):
        line = lines[i]
        if not line.strip() or re.match(r'^<!--.*-->\s*$', line):
            i += 1
            continue
        m = re.match(r'^(`{3,})', line)
        if m:
            j = i + 1
            while j < len(lines) and not re.match(r'^%s\s*$' % m.group(1), lines[j]):
                j += 1
            blocks.append(('fence', lines[i:j + 1]))
            i = j + 1
            continue
        kind = ('table' if line.startswith('|') else 'quote' if line.startswith('>') else
                'list' if re.match(r'^(\s*)([-*]|\d+\.) ', line) else 'code' if line.startswith('    ') else
                'head' if line.startswith('#') else 'para')
        j = i + 1
        while j < len(lines) and lines[j].strip() and kind != 'head':
            nxt = lines[j]
            if re.match(r'^`{3,}', nxt):
                break
            if kind == 'para' and (nxt.startswith('|') or re.match(r'^([-*]|\d+\.) ', nxt)):
                break
            if kind in ('table', 'quote') and not nxt.startswith(kind == 'table' and '|' or '>'):
                break
            j += 1
        if kind == 'code':
            while j < len(lines) and (not lines[j].strip() or lines[j].startswith('    ')):
                j += 1
            while not lines[j - 1].strip():
                j -= 1
        blocks.append((kind, lines[i:j]))
        i = j
    return blocks


class Markdown:
    """Enough Markdown for the extracts the pages quote: paragraphs, lists, tables, fences, quotes, inline marks."""

    def __init__(self, release, doc):
        self.release, self.doc, self.doc_dir = release, doc, os.path.dirname(doc)

    def link(self, href):
        if re.match(r'^[a-z]+:', href):
            return href
        path, _, frag = href.partition('#')
        path = os.path.normpath(os.path.join(self.doc_dir, path)).replace(os.sep, '/') if path else self.doc
        return f'{GITHUB}/blob/{self.release}/{path}' + ('#' + frag if frag else '')

    def inline(self, s):
        keep = []

        def hold(h):
            keep.append(h)
            return '\x00%d\x00' % (len(keep) - 1)

        def code(m):
            c = m.group(2)
            if len(c) > 2 and c[0] == ' ' and c[-1] == ' ' and c.strip():
                c = c[1:-1]                        # CommonMark: one space either side of a span is padding
            return hold('<code>' + esc(c) + '</code>')

        def link(m):
            return hold('<a href="%s">%s</a>' % (attr(self.link(m.group(2))), self.inline(m.group(1))))

        s = re.sub(r'\[((?:[^\[\]]|`[^`]*`)+)\]\(([^)\s]+)\)', link, s)
        s = re.sub(r'(`+)(.+?)(?<!`)\1(?!`)', code, s)
        s = esc(s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'(?<![*\w])\*(?![\s*])(.+?)(?<![\s*])\*(?![*\w])', r'<em>\1</em>', s)
        s = re.sub(r'([؀-ۿ‌]+(?:[ ‌]+[؀-ۿ‌]+)*)', r'<span lang="fa" dir="rtl">\1</span>', s)
        while '\x00' in s:
            s = re.sub(r'\x00(\d+)\x00', lambda m: keep[int(m.group(1))], s)
        return s

    def block(self, kind, lines, label=''):
        if kind == 'para':
            return '<p>' + self.inline(' '.join(x.strip() for x in lines)) + '</p>'
        if kind == 'quote':
            return '<blockquote><p>' + self.inline(' '.join(re.sub(r'^>\s?', '', x).strip() for x in lines)) + '</p></blockquote>'
        if kind == 'list':
            items, ordered = [], bool(re.match(r'^\s*\d+\. ', lines[0]))
            for x in lines:
                m = re.match(r'^([-*]|\d+\.) (.*)$', x)
                if m:
                    items.append([m.group(2).strip()])
                else:
                    items[-1].append(x.strip())
            tag = 'ol' if ordered else 'ul'
            return '<%s>%s</%s>' % (tag, ''.join('<li>' + self.inline(' '.join(i)) + '</li>' for i in items), tag)
        if kind == 'table':
            rows = [[c.strip() for c in x.strip().strip('|').split('|')] for x in lines]
            head, body = rows[0], [r for r in rows[2:]]
            return ('<div class="table"><table><thead><tr>' + ''.join('<th scope="col">%s</th>' % self.inline(c) for c in head)
                    + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>%s</td>' % self.inline(c) for c in r) + '</tr>'
                                                     for r in body) + '</tbody></table></div>')
        if kind in ('fence', 'code'):
            text = '\n'.join(lines[1:-1]) if kind == 'fence' else '\n'.join(x[4:] for x in lines)
            lang = lines[0].strip('`').strip() if kind == 'fence' else ''
            return ('<pre class="doc" tabindex="0" aria-label="%s"><code>%s</code></pre>'
                    % (attr(label or (lang + ' from ' + self.doc if lang else 'from ' + self.doc)), esc(text)))
        raise ValueError(kind)


def extract(clone, release, doc, heading, picks):
    """HTML for the blocks `picks` of `doc`'s section `heading`. A pick is (kind, n) — the n-th block of that kind,
    from 1 — or (kind, '^regex') — the first of that kind whose first line matches."""
    text = open(os.path.join(clone, doc), encoding='utf-8').read()
    secs = md_sections(text)
    body = secs.get(heading)
    if body is None:
        raise Refused(f'documents: {doc} has no section {heading!r}')
    blocks = md_blocks(body)
    md = Markdown(release, doc)
    out = []
    for kind, n in picks:
        of = [b for b in blocks if b[0] == kind]
        if isinstance(n, int):
            b = of[n - 1] if 0 < n <= len(of) else None
        else:
            b = next((x for x in of if re.search(n, x[1][0])), None)
        if b is None:
            raise Refused(f'documents: {doc} § {heading!r} has no {kind} {n!r}')
        out.append(md.block(*b, label=f'{doc}: {heading or "the opening"}'))
    return '\n'.join(out)


# ─── the scenes ────────────────────────────────────────────────────────────────────────────────────────────────────

RECIPES = [  # the cookbook's sections that commit something here, in page order, and how each is journalled
    ('A registered domain', 'the domain example.org',
     '- action: added [[example-org]]; RULE-CHANGE (VOCAB.md): this garden opts into the domain profile.'),
    ('A machine at home that other things run on', 'the NAS at home', '- action: added [[nas]].'),
    ('Third-party software, and a running copy of it that serves the website', 'nginx, and the website it serves',
     '- action: added [[nginx]] and [[website]], from the cookbook.'),
    ('A rented VPS', 'the rented VPS', '- action: added [[vps-a]].'),
    ('Another person, and the garden she keeps', 'first contact: garden-ali and ali',
     '- action: first contact: [[garden-ali]] and [[ali]], by the id ali read out (class F, sam ratified).'),
    ('A happening: an event', "the dinner at Sam's", '- action: added [[dinner-at-sams]].'),
    ('Money between two people', 'the camera sam and ali share', '- action: added [[shared-camera]].'),
    ('An agreement paid in instalments', 'the washing-machine loan', '- action: added [[washer-loan]].'),
    ('A statement: a document, and a capture of its lines', 'the September card statement',
     '- action: added [[card-statement-2026-09]], its capture redacted.'),
]
NOT_HERE = ('The gardener, first', 'A value the vocabulary does not have yet', 'A kind of fact the standard has no term for')


def cookbook(clone):
    page = open(os.path.join(clone, 'seed', 'COOKBOOK.md'), encoding='utf-8').read()
    recipes = []
    for sec in page.split('\n## '):
        title = sec.split('\n', 1)[0].lstrip('# ').strip()
        beans = re.findall(r'<!-- example: (beans/[a-z0-9-]+\.md) -->\n```markdown\n(.*?)\n```', sec, re.S)
        frags = re.findall(r'<!-- example-front-matter: VOCAB\.md -->\n```yaml\n(.*?)\n```', sec, re.S)
        if (beans or frags) and title not in NOT_HERE:
            recipes.append((title, beans, frags))
    got = [r[0] for r in recipes]
    want = [r[0] for r in RECIPES]
    if got != want:
        raise Refused(f'the cookbook: its recipes are {got}, and this build knows {want}')
    return page, recipes


def apply_fragment(vp, frag):
    v = open(vp, encoding='utf-8').read()
    for key in re.findall(r'^([a-z_]+):', frag, re.M):
        v = re.sub(rf'^{key}: \[\].*\n', '', v, count=1, flags=re.M)
    head, sep, rest = v.partition('\n---\n')
    with open(vp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(head + '\n' + frag + sep + rest)


def scenes(d):
    T, clone = d.T, d.p('daftar')
    SAM, ALI, REH = d.p('garden-sam'), d.p('garden-ali'), d.p('garden-sam-rehearsal')

    # S1 — grow ------------------------------------------------------------------------------------------------------
    d.step = 'S1 grow'
    grown = d.out('grow-sam', clone, 'python3 seed/germinate.py ~/garden-sam --gardener sam --gardener-name "Sam"')
    d.expect(re.search(r'^garden-sam \(daftar %s, gardener sam, garden [0-9a-f]{12}\): 1 docs, 0 error\(s\), 0 warning\(s\)'
                       % re.escape(d.release), grown, re.M), 'germinate did not print a clean first gate line')
    d.sh(clone, 'python3 seed/germinate.py ~/garden-ali --gardener ali --gardener-name "Ali"')
    for g, who in ((SAM, 'sam'), (ALI, 'ali')):
        d.sh(g, f'git config user.name {who}')
        d.sh(g, f'git config user.email {who}@example.org')
    for g, name in ((SAM, 'garden-sam'), (ALI, 'garden-ali')):
        _, idt = d.sh(g, 'python3 bin/dmpropose.py id')
        m = re.search(r'garden_id: "?([0-9a-f]{12})', idt)
        d.expect(m, f'`dmpropose id` in {name} printed no id:\n{idt}')
        d.ids[name] = m.group(1)
        d.clean_gate(g)
    AID = d.ids['garden-ali']

    page, recipes = cookbook(clone)
    how = {t: (what, body) for t, what, body in RECIPES}

    def recipe(title, cid=None):
        _, beans, frags = next(r for r in recipes if r[0] == title)
        for rel, text in beans:
            if rel == 'beans/sam.md':
                continue                          # the gardener was planted by germinate --gardener
            n = text.count('123456789abc')
            text = text.replace('123456789abc', AID)
            text, k = re.subn(r'[ \t]+# (?:replace with|her garden)[^\n]*', '', text)
            d.expect(k == n, f'{rel}: the stand-in id and its comments do not pair up ({n} ids, {k} comments)')
            d.write(os.path.join(SAM, rel), text)
        for f in frags:
            apply_fragment(os.path.join(SAM, 'VOCAB.md'), f)
        what, body = how[title]
        return d.commit(SAM, 'sam', what, body, cid=cid)

    # S2 — machines and a domain -------------------------------------------------------------------------------------
    d.step = 'S2 machines and a domain'
    recipe('A registered domain')
    recipe('A machine at home that other things run on')
    commit = recipe('Third-party software, and a running copy of it that serves the website', cid='machines-commit')
    for line in ('PASS every bean carries BOTH ownership arcs', 'PASS the two arcs agree on facets everywhere',
                 'PASS every ownership chain that is owed terminates at the crown or outside'):
        d.expect(line in commit, f'the website commit did not print {line!r}')
    recipe('A rented VPS')
    for b in ('example-org', 'nas', 'nginx', 'website', 'vps-a'):
        d.bean(b, SAM, f'beans/{b}.md')
    d.doc('cookbook-domain-profile', extract(clone, d.release, 'seed/COOKBOOK.md', 'A registered domain', [('fence', 1)]))
    cur = d.out('machines-cursor', SAM, 'python3 bin/dmcursor.py website')
    d.expect('living in nas' in cur or 'nas' in cur, 'dmcursor did not name the NAS the website lives in')
    stale = d.out('machines-stale', SAM, 'python3 bin/dmstale.py', expect=1)
    d.expect(re.search(r'EXPIRING\s+example-org\.registration', stale), 'dmstale did not warn about the domain')
    d.out('machines-check', SAM, 'python3 bin/dmcheck.py --all')
    d.clean_gate(SAM)

    # S3 — another person --------------------------------------------------------------------------------------------
    d.step = 'S3 another person'
    d.out('gardens-id-sam', SAM, 'python3 bin/dmpropose.py id')
    d.out('gardens-id-ali', ALI, 'python3 bin/dmpropose.py id')
    recipe('Another person, and the garden she keeps')
    d.bean('sam/garden-ali', SAM, 'beans/garden-ali.md')
    d.bean('sam/ali', SAM, 'beans/ali.md')
    d.expect(AID in open(os.path.join(SAM, 'beans', 'garden-ali.md'), encoding='utf-8').read(),
             "garden-ali's bean does not carry her garden's id")
    d.clean_gate(SAM)

    # S4 — a dinner --------------------------------------------------------------------------------------------------
    d.step = 'S4 a dinner'
    recipe('A happening: an event')
    d.bean('dinner-at-sams', SAM, 'beans/dinner-at-sams.md')
    cal = d.out('event-cal', SAM, 'python3 bin/dmcal.py 2026-09-12')
    d.expect('persian' in cal, 'dmcal did not show the day in the Persian calendar')
    d.clean_gate(SAM)

    # S5 — a cost shared ---------------------------------------------------------------------------------------------
    d.step = 'S5 a cost shared'
    recipe('Money between two people')
    d.bean('shared-camera', SAM, 'beans/shared-camera.md')
    led = d.out('money-ledger', SAM, 'python3 bin/dmledger.py shared-camera')
    d.expect('sam owes ali 60 XTS' in led, 'dmledger did not say `sam owes ali 60 XTS`')
    SCR = d.p('garden-sam-scratch')
    uneven = d.out('money-uneven', SAM,
                   (T, 'git clone -q ~/garden-sam ~/garden-sam-scratch'),
                   (SCR, 'python3 bin/dmsafe.py flow-set beans/shared-camera.md transactions.camera.amount.count \'"100.00"\' --expect 1'),
                   (SCR, 'python3 bin/dmledger.py shared-camera'))
    d.expect('sam owes ali 200/3 XTS' in uneven, 'dmledger did not say `sam owes ali 200/3 XTS`')
    shutil.rmtree(SCR)
    d.clean_gate(SAM)

    # S6 — a loan ----------------------------------------------------------------------------------------------------
    d.step = 'S6 a loan'
    recipe('An agreement paid in instalments')
    d.bean('washer-loan', SAM, 'beans/washer-loan.md')
    l1 = d.out('loan-ledger-1', SAM, 'python3 bin/dmledger.py washer-loan')
    d.expect('ali owes sam 120 XTS' in l1 and 'next 2026-11-01 (in 5 days), occurrence 2 of 6' in l1,
             'dmledger did not read the loan as owed and next due on 2026-11-01')
    import yaml
    loan = yaml.safe_load(open(os.path.join(SAM, 'beans', 'washer-loan.md'), encoding='utf-8').read().split('\n---\n')[0][4:])
    d.expect(list(loan['transactions']) == ['the-loan'], 'the loan does not hold the one transaction the cookbook gives it')
    block_text = open(os.path.join(SAM, 'beans', 'washer-loan.md'), encoding='utf-8').read()
    m = re.search(r'(?m)^transactions:\n(?:  .*\n)+', block_text)
    inst = (m.group(0) + '  instalment-1:\n    what: "Ali\'s first instalment"\n    amount: { count: "20.00", unit: XTS }\n'
            '    day: 2026-10-01\n    under: instalments\n    paid_by:\n      - { party: ali }\n    borne_by:\n'
            '      - { party: sam, share: 1 }\n')
    d.write(d.p('instalment.yaml'), inst)
    d.file('instalment-block', 'instalment.yaml', inst)
    d.out('loan-dmsafe', SAM, 'python3 bin/dmsafe.py replace-block beans/washer-loan.md transactions --block ../instalment.yaml')
    d.commit(SAM, 'sam', "Ali's first instalment", '- action: [[washer-loan]]: the first instalment, 20.00 XTS paid by ali on 2026-10-01.',
             cid='loan-commit')
    l2 = d.out('loan-ledger-2', SAM, 'python3 bin/dmledger.py washer-loan')
    d.expect('ali owes sam 100 XTS' in l2, 'dmledger did not say `ali owes sam 100 XTS` after the instalment')
    ls = d.out('loan-stale', SAM, 'python3 bin/dmstale.py', expect=1)
    d.expect(re.search(r'EXPIRING\s+washer-loan\.clauses\[instalments\]\s+due 2026-11-01 \(5 days\)', ls),
             'dmstale did not warn that the next instalment falls due on 2026-11-01')
    btw = d.out('loan-between', SAM, 'python3 bin/dmledger.py --between sam ali')
    d.expect(btw.rstrip().endswith('ali owes sam 40 XTS'), 'dmledger --between did not end with `ali owes sam 40 XTS`')
    d.clean_gate(SAM)

    # S7 — a statement, and the refusals made in throwaway clones -----------------------------------------------------
    d.step = 'S7 a statement'
    recipe('A statement: a document, and a capture of its lines')
    d.bean('card-statement-2026-09', SAM, 'beans/card-statement-2026-09.md')
    d.doc('cookbook-hash-commands', extract(clone, d.release, 'seed/COOKBOOK.md', 'A statement: a document, and a capture of its lines',
                                            [('para', r'^`content_hash` is')]))
    d.clean_gate(SAM)

    def refused(cid, edit, bean, what, body, error):
        d.clone(SAM, SCR, 'sam')
        cmds = ([edit] if isinstance(edit, str) else list(edit)) + [f'python3 bin/dmjournal.py sam {q(what)} --body {q(body)}', 'git add -A', f'git commit -qm {q(what)}']
        text = d.out(cid, SCR, *cmds, expect=1)
        d.expect(re.search(error, text), f'{cid}: the gate did not refuse with {error!r}:\n{text[-800:]}')
        shutil.rmtree(SCR)

    stmt = open(os.path.join(SAM, 'beans', 'card-statement-2026-09.md'), encoding='utf-8').read()
    h = re.search(r'value: "sha256:([0-9a-f]{64})"', stmt).group(1)
    d.write(d.p('anchor.yaml'), 'identity:\n  status: confirmed\n  anchors:\n    - { key: content_hash, value: "sha256:%s", '
            'class: logical, establishing: true }\n' % h.upper())
    d.file('anchor-capitals', 'anchor.yaml', open(d.p('anchor.yaml'), encoding='utf-8').read())
    refused('statement-refused', 'python3 bin/dmsafe.py replace-block beans/card-statement-2026-09.md identity --block ../anchor.yaml',
            'card-statement-2026-09', 'the statement hash, as Get-FileHash prints it',
            '- action: [[card-statement-2026-09]] content_hash in capitals.', r'not in canonical form')
    d.write(d.p('owner.yaml'), 'owned_by: { legal: { owner: { bean: sam } } }\n')
    d.file('owner-sam', 'owner.yaml', 'owned_by: { legal: { owner: { bean: sam } } }\n')
    refused('metaphysics-crown-refused', ('python3 bin/dmsafe.py remove-block beans/ali.md owned_by',
                                   'python3 bin/dmsafe.py insert-after beans/ali.md provenance --block ../owner.yaml'),
            'ali', 'ali, owned by sam', '- action: [[ali]] owned by [[sam]].', r"must use the 'crown' form")
    d.write(d.p('note.yaml'), 'renewal_note: "renews next January"\n')
    d.file('renewal-note', 'note.yaml', 'renewal_note: "renews next January"\n')
    refused('metaphysics-structure', 'python3 bin/dmsafe.py insert-after beans/vps-a.md provides_habitat --block ../note.yaml',
            'vps-a', 'a renewal note on the VPS', '- action: [[vps-a]] renewal note.', r"top-level key 'renewal_note' is declared by no")

    # S8 — an agent of any make --------------------------------------------------------------------------------------
    d.step = 'S8 an agent'
    ac = d.out('agent-check', SAM, 'python3 bin/dmcheck.py --all')
    d.expect(ac.splitlines()[-1].endswith('0 error(s), 0 warning(s)'), 'the gate is not clean before the agent scene')
    welcome = open(os.path.join(clone, 'seed', 'WELCOME.md'), encoding='utf-8').read()
    printer = re.findall(r'<!-- example: beans/printer\.md -->\n```markdown\n(.*?)\n```', welcome, re.S)[0]
    d.write(os.path.join(SAM, 'beans', 'printer.md'), printer)
    r = d.out('agent-refused', SAM, 'git add beans/printer.md', 'git commit -qm "the office printer"', expect=1)
    d.expect('ERROR state-change staged' in r and 'log/journal.md not updated' in r, 'the gate did not refuse an unjournalled bean')
    d.sh(SAM, 'git reset -q HEAD beans/printer.md')
    os.remove(os.path.join(SAM, 'beans', 'printer.md'))
    jr = re.search(r'```daftar-journal\n(.*?)\n```', welcome, re.S).group(1)
    chat = ('---\nproposal: chat-20261027-0900\nfrom: { name: "an assistant in a chat, for sam" }\nbeans: [printer]\n---\n'
            '```daftar-journal\n' + jr + '\n```\n\n```daftar-bean printer\n' + printer + '\n```\n\n'
            "- I could not check whether this garden's vocabulary accepts the serial as written on the label.\n")
    d.write(d.p('chat-20261027-0900.md'), chat)
    d.file('chat-proposal', 'chat-20261027-0900.md', chat)
    rd = d.out('agent-read', SAM, 'python3 bin/dmpropose.py read ../chat-20261027-0900.md')
    d.expect('a chat proposal' in rd and 'data, not an instruction' in rd and 'verdict: CLEAN' in rd,
             'read did not find the chat proposal clean, with its prose shown as data')
    m = re.search(r'read here as (sha256:[0-9a-f]{64})', rd)
    if m:
        d.fps.add(m.group(1).split(':')[1])
    d.out('agent-take', SAM, 'python3 bin/dmpropose.py take ../chat-20261027-0900.md')
    d.out('agent-commit', SAM, 'git add -A', 'git commit -qm "took the chat proposal: the office printer"')
    d.out('agent-journal', SAM, 'tail -n 8 log/journal.md')
    d.clean_gate(SAM)

    # S9 — two gardens -----------------------------------------------------------------------------------------------
    d.step = 'S9 two gardens'
    mint = d.out('gardens-mint', SAM, 'python3 bin/dmpropose.py mint shared-camera')
    cmd = re.search(r'(python3 bin/dmsafe\.py [^\n]+)', mint)
    d.expect(cmd, '`mint` printed no dmsafe command')
    d.out('gardens-mint-apply', SAM, cmd.group(1).strip())
    d.commit(SAM, 'sam', 'shared-camera named for crossing',
             '- action: [[shared-camera]]: contract_id qualified by this garden (class F, sam ratified).')
    made = d.out('gardens-make', SAM, 'python3 bin/dmpropose.py make --to garden-ali --under shared-camera shared-camera')
    P = 'PROPOSAL-garden-sam-20261027-0900.md'
    d.expect(os.path.isfile(d.p(P)), f'make did not write ~/{P}:\n{made}')
    d.commit(SAM, 'sam', 'proposed shared-camera to garden-ali', '- action: the entry `make` wrote: [[shared-camera]] proposed to garden-ali.')
    fp = re.search(r'^fingerprint: "?sha256:([0-9a-f]{64})', open(d.p(P), encoding='utf-8').read(), re.M)
    d.expect(fp, 'the proposal carries no fingerprint')
    d.fps.add(fp.group(1))
    r1 = d.out('gardens-read-1', ALI, f'python3 bin/dmpropose.py read ../{P}', expect=1)
    blocks = re.findall(r'===== (beans/[a-z0-9-]+\.md) =====\n(.*?)(?=\n===== )', r1, re.S)
    d.expect(sorted(b[0] for b in blocks) == ['beans/garden-sam.md', 'beans/sam.md'],
             f'the first read did not print garden-sam and sam: {[b[0] for b in blocks]}')
    for rel, text in blocks:
        d.write(os.path.join(ALI, rel), text)
    d.commit(ALI, 'ali', 'first contact: garden-sam and sam',
             '- action: first contact: [[garden-sam]] and [[sam]], as the proposal names them (class F, ali ratified).',
             cid='gardens-contact-commit')
    r2 = d.out('gardens-read-2', ALI, f'python3 bin/dmpropose.py read ../{P}')
    d.expect('verdict: CLEAN' in r2, 'the second read is not CLEAN')
    d.expect(re.search(r'(?m)^\s*NOTE .*accepted', r2), 'the second read did not note the acceptance it carries')
    d.out('gardens-take', ALI, f'python3 bin/dmpropose.py take ../{P}')
    d.out('gardens-status', ALI, 'git status --short')
    d.sh(ALI, 'git add -A')
    d.sh(ALI, 'git commit -qm "took garden-sam\'s proposal: shared-camera"')
    d.bean('ali/shared-camera', ALI, 'beans/shared-camera.md')
    la = d.out('gardens-ledger-ali', ALI, 'python3 bin/dmledger.py shared-camera')
    d.expect('sam owes ali 60 XTS' in la, "garden-ali's ledger does not read `sam owes ali 60 XTS`")
    gs = open(os.path.join(ALI, 'beans', 'garden-sam.md'), encoding='utf-8').read()
    d.ms.update(re.findall(r'taken_at: (\d{13})', gs))
    entry = re.findall(r'<!-- example-entry: beans/shared-camera\.md parties\.ali -->\n```yaml\n(.*?)\n```', page, re.S)
    d.expect(len(entry) == 1, "the cookbook's example of ali's own acceptance was not found")
    d.doc('cookbook-ali-entry', extract(clone, d.release, 'seed/COOKBOOK.md', 'Proposing to another garden', [('fence', r'^```yaml')]))
    sc = open(os.path.join(ALI, 'beans', 'shared-camera.md'), encoding='utf-8').read()
    pm = re.search(r'(?m)^parties:\n((?:  .*\n)+)', sc)
    d.expect(pm, 'the taken camera has no parties block')
    lines = pm.group(1).splitlines()
    d.expect(sum(1 for x in lines if x.startswith('  ali:')) == 1, "the parties block does not hold one line for ali")
    parties = 'parties:\n' + '\n'.join(entry[0] if x.startswith('  ali:') else x for x in lines) + '\n'
    d.write(d.p('parties.yaml'), parties)
    d.file('parties-block', 'parties.yaml', parties)
    d.out('gardens-accept', ALI, 'python3 bin/dmsafe.py replace-block beans/shared-camera.md parties --block ../parties.yaml',
          'python3 bin/dmjournal.py ali "my own yes to shared-camera" --body "- action: [[shared-camera]]: my acceptance, in my own words."',
          'git add -A', 'git commit -qm "my own yes to shared-camera"')
    r3 = d.out('gardens-read-3', ALI, f'python3 bin/dmpropose.py read ../{P}', expect=1)
    d.expect('already' in r3, 'the third read did not refuse a proposal taken already')
    d.clean_gate(ALI)
    d.clean_gate(SAM)

    # S10 — a rehearsal ----------------------------------------------------------------------------------------------
    d.step = 'S10 a rehearsal'
    bare = d.out('reh-make-bare', SAM, 'python3 bin/dmpropose.py make --to garden-ali --under washer-loan washer-loan dinner-at-sams',
                 expect=1)
    d.expect('BARE minted names' in bare and 'nothing was written' in bare, '`make` did not refuse the bare names')
    steps = []
    for b in ('washer-loan', 'dinner-at-sams'):
        _, mt = d.sh(SAM, f'python3 bin/dmpropose.py mint {b}')
        c = re.search(r'(python3 bin/dmsafe\.py [^\n]+)', mt)
        d.expect(c, f'`mint {b}` printed no dmsafe command')
        steps += [f'python3 bin/dmpropose.py mint {b}', c.group(1).strip()]
    d.out('reh-mint', SAM, *steps)
    d.commit(SAM, 'sam', 'the loan and the dinner named for crossing',
             '- action: [[washer-loan]] and [[dinner-at-sams]]: names qualified by this garden (class F, sam ratified).')
    d.out('reh-germinate', SAM, 'python3 seed/germinate.py ../garden-sam-rehearsal --gardener sam')
    d.sh(REH, 'git config user.name sam')
    d.sh(REH, 'git config user.email sam@example.org')
    _, idt = d.sh(REH, 'python3 bin/dmpropose.py id')
    d.ids['garden-sam-rehearsal'] = re.search(r'garden_id: "?([0-9a-f]{12})', idt).group(1)
    for b in ('sam', 'ali', 'garden-ali', 'washer-loan', 'dinner-at-sams'):
        shutil.copyfile(os.path.join(SAM, 'beans', b + '.md'), os.path.join(REH, 'beans', b + '.md'))
    d.write(os.path.join(REH, 'beans', 'garden-sam.md'),
            '---\nbean: garden-sam\ngenos: garden\ntitle: "garden-sam — the garden this one rehearses"\nstatus: active\n'
            'summary: "Sam\'s own garden; this garden rehearses what it will propose."\nnature: lekton\n'
            'identity:\n  status: confirmed\n  anchors:\n    - { key: garden_id, value: "%s", class: logical, establishing: true }\n'
            'provenance: { src: asserted-by-human, by: "sam", as_of: 2026-10-27 }\n'
            'owned_by: { legal: { owner: { bean: sam } } }\nresponsibility: { legal: { holder: { bean: sam } } }\n---\n'
            'The garden this rehearsal is for.\n' % d.ids['garden-sam'])
    gp = os.path.join(REH, 'GARDEN.md')
    g = open(gp, encoding='utf-8').read()
    g2 = g.replace('\n---\n# ', '\ntest: "a rehearsal of the washer loan"\n---\n# ', 1)
    d.expect(g2 != g, "the rehearsal's GARDEN.md has no front matter to mark")
    d.write(gp, g2)
    d.bean('reh/GARDEN.md', REH, 'GARDEN.md')
    d.commit(REH, 'sam', 'a rehearsal of the washer loan',
             '- action: RULE-CHANGE: GARDEN.md marks this garden a test garden; [[sam]], [[ali]], [[garden-ali]], [[washer-loan]] '
             'and [[dinner-at-sams]] copied from garden-sam, and [[garden-sam]] recorded as the garden it rehearses.')
    os.makedirs(d.p('rehearsals'), exist_ok=True)
    d.out('reh-make', REH, 'python3 bin/dmpropose.py make --to garden-ali --under washer-loan --out ../rehearsals washer-loan dinner-at-sams')
    RP = 'rehearsals/PROPOSAL-garden-sam-rehearsal-20261027-0900.md'
    d.expect(os.path.isfile(d.p(RP)), f'the rehearsal did not write ~/{RP}')
    fp = re.search(r'^fingerprint: "?sha256:([0-9a-f]{64})', open(d.p(RP), encoding='utf-8').read(), re.M)
    d.fps.add(fp.group(1))
    d.commit(REH, 'sam', 'proposed the loan to garden-ali', '- action: the entry `make` wrote: [[washer-loan]] and [[dinner-at-sams]] proposed.')
    rr1 = d.out('reh-read-1', ALI, f'python3 bin/dmpropose.py read ../{RP}', expect=1)
    blocks = re.findall(r'===== (beans/[a-z0-9-]+\.md) =====\n(.*?)(?=\n===== )', rr1, re.S)
    d.expect([b[0] for b in blocks] == ['beans/garden-sam-rehearsal.md'] and 'test:' in blocks[0][1],
             f'the first read of the rehearsal did not print its garden bean, marked test: {[b[0] for b in blocks]}')
    d.write(os.path.join(ALI, blocks[0][0]), blocks[0][1])
    d.commit(ALI, 'ali', 'the rehearsal of garden-sam, marked as one',
             '- action: recorded [[garden-sam-rehearsal]], a TEST garden (class F, ali ratified).')
    d.bean('ali/garden-sam-rehearsal', ALI, 'beans/garden-sam-rehearsal.md')
    rr2 = d.out('reh-read-2', ALI, f'python3 bin/dmpropose.py read ../{RP}', expect=1)
    d.expect('--as-test' in rr2, 'the second read of the rehearsal did not say take refuses it without --as-test')
    d.out('reh-take-refused', ALI, f'python3 bin/dmpropose.py take ../{RP}', expect=1)
    AS = d.p('garden-ali-scratch')
    d.out('reh-scratch', ALI, (T, 'git clone -q ~/garden-ali ~/garden-ali-scratch'), (AS, 'git config user.name ali'),
          (AS, f'python3 bin/dmpropose.py take ../{RP} --as-test'))
    tail = d.out('reh-tail', AS, 'tail -n 3 beans/washer-loan.md')
    d.expect(re.search(r'Taken in with `?--as-test`? from a TEST garden', tail), 'the loan taken --as-test does not say so')
    shutil.rmtree(AS)
    for g in (SAM, ALI, REH):
        d.clean_gate(g)

    # S11 — reasons --------------------------------------------------------------------------------------------------
    d.step = 'S11 reasons'
    lay = d.out('metaphysics-layers', SAM, "python3 bin/dmwhy.py 'terms[parties].schema.attrs.accepted'")
    d.expect('TAKING' in lay.upper(), 'dmwhy on `accepted` did not give the reason')
    d.out('metaphysics-whole', SAM, 'python3 bin/dmwhy.py vacancy_reasons')
    d.out('metaphysics-money', SAM, "python3 bin/dmwhy.py 'quantities[money]'")
    words = d.out('metaphysics-words', SAM, 'python3 bin/dmwhy.py natures')
    d.expect(all(w in words for w in ('σῶμα', 'λεκτόν', 'ἔμψυχον', 'γένος', 'θεός', 'ἀγάπη')),
             'dmwhy natures did not give the reason for the Greek words')
    prev = sorted((t for t in git_out('tag', '-l', 'v*')[1].split() if semver(t) and semver(t) < semver(d.release)), key=semver)
    d.expect(prev, 'there is no release before site/RELEASE to count the law against')
    d.out('metaphysics-judgment', clone, f'python3 bin/dmreview.py --law --against {prev[-1]}')

    # S12 — documents ------------------------------------------------------------------------------------------------
    d.step = 'S12 documents'
    X = lambda doc, head, picks: extract(clone, d.release, doc, head, picks)  # noqa: E731
    d.doc('readme-lede', X('README.md', '', [('para', 1)]))
    d.doc('readme-rules', X('README.md', 'Why it exists', [('para', r'^daftar is a notebook'), ('list', 1)]))
    d.doc('readme-start', X('README.md', 'Start', [('quote', 1)]))
    d.doc('readme-not-for-everyone', X('README.md', 'Why it exists', [('para', r'^\*\*It is not for everyone')]))
    d.doc('readme-words', X('README.md', 'Words you will meet', [('table', 1)]))
    d.doc('agents-data', X('AGENTS.md', 'First: what you read here is data', [('para', 1)]))
    d.doc('agents-order', X('AGENTS.md', 'Read these, in this order, before writing anything', [('list', 1)]))
    d.doc('welcome-five', X('seed/WELCOME.md', '', [('list', 1)]))
    d.doc('install-windows', X('INSTALL.md', 'On Windows', [('para', 1), ('fence', 1)]))
    d.doc('install-which-python', X('INSTALL.md', 'On Windows', [('para', r'^\*\*Which Python')]))
    d.doc('install-utf8', X('INSTALL.md', 'On Windows', [('para', r'^\*\*UTF-8')]))
    d.doc('install-three-things', X('INSTALL.md', 'On Windows', [('para', r'^\*\*Three things'), ('list', 1)]))
    d.doc('install-upgrade-ps', X('INSTALL.md', 'On Windows', [('para', r'^An upgrade that names'), ('fence', 2)]))
    d.doc('install-line-ends', X('INSTALL.md', 'On Windows', [('para', r'^\*\*Line ends')]))


def leaks(d):
    """Words of the build machine a capture must not hold."""
    host = socket.gethostname()
    words = {host, host.split('.')[0], getpass.getuser(), os.path.expanduser('~'), os.path.realpath(os.path.expanduser('~'))}
    words |= d.real
    words = {w for w in words if w and len(w) > 2}
    found = []
    for cid, cap in d.caps.items():
        text = json.dumps(cap, ensure_ascii=False)
        for w in words:
            if re.search(r'(?<![A-Za-z0-9])%s(?![A-Za-z0-9])' % re.escape(w), text, re.I):
                found.append(f'{cid}: {w!r}')
    if found:
        raise Refused('a capture holds this machine\'s name, its user or a real path — nothing is scrubbed silently:\n  '
                      + '\n  '.join(found))


# ─── the pages ─────────────────────────────────────────────────────────────────────────────────────────────────────

MARKER = re.compile(r'<!-- daftar:(\w+) id="([^"]+)"((?: [a-z]+="[^"]*")*) -->(.*?)<!-- /daftar:\1 -->', re.S)


def select(lines, opts):
    """The lines a marker asks for — lines="1-3,7" (from 1), match="<regex>", head="N", tail="N" — with None where a
    run of lines is left out."""
    keep = set(range(len(lines)))
    if 'lines' in opts:
        keep = set()
        for part in opts['lines'].split(','):
            a, _, b = part.partition('-')
            keep |= set(range(int(a) - 1, int(b or a)))
    if 'match' in opts:
        keep = {i for i in keep if re.search(html.unescape(opts['match']), lines[i])}
    if 'head' in opts:
        keep = {i for i in keep if i < int(opts['head'])}
    if 'tail' in opts:
        keep = {i for i in keep if i >= len(lines) - int(opts['tail'])}
    keep = sorted(i for i in keep if 0 <= i < len(lines))
    out, prev = [], -1
    for i in keep:
        if i != prev + 1:
            out.append(None)
        out.append(lines[i])
        prev = i
    if prev != len(lines) - 1:
        out.append(None)
    return out


class Pages:
    def __init__(self, d, release, root_in, root_out):
        self.d, self.release, self.src, self.dst = d, release, root_in, root_out
        self.used = set()
        v = [(i, 'id') for i in d.ids.values()] + [(f, 'fp') for f in d.fps] + [(m, 'ms') for m in d.ms]
        v.sort(key=lambda x: -len(x[0]))
        self.vary = dict(v)
        self.vary_re = re.compile('|'.join(re.escape(x) for x, _ in v)) if v else None

    TITLES = {'id': 'differs in every build: a garden id', 'fp': 'differs in every build: a fingerprint',
              'ms': 'differs in every build: a moment in milliseconds'}

    def spans(self, escaped):
        if not self.vary_re:
            return escaped
        return self.vary_re.sub(lambda m: '<span class="v" data-v="%s" title="%s">%s</span>'
                                % (self.vary[m.group(0)], self.TITLES[self.vary[m.group(0)]], m.group(0)), escaped)

    def lines_html(self, lines):
        return '\n'.join('<span class="el" title="lines left out">…</span>' if x is None else self.spans(esc(x))
                         for x in lines)

    def render(self, typ, cid, opts, page):
        if typ in ('out', 'bean', 'file', 'doc'):
            cap = self.d.caps.get(cid)
            if cap is None or cap['type'] != typ:
                raise Refused(f'{page}: marker {typ}:{cid} names nothing this build produces')
            self.used.add(cid)
            if typ == 'out':
                parts, steps = [], cap['steps']
                if 'steps' in opts:
                    steps = [steps[int(i) - 1] for i in opts['steps'].split(',')]
                for s in steps:
                    parts.append('<span class="cmd">%s$ %s</span>' % (esc(s['cwd']), self.spans(esc(s['cmd']))))
                    if s['out']:
                        parts.append(self.lines_html(select(s['out'].split('\n'), opts)))
                    if s['exit']:
                        parts.append('<span class="exit">exit %d</span>' % s['exit'])
                last = steps[-1]['cmd']
                label = re.sub(r'^python3 (?:bin|seed)/', '', last)
                label = label if len(label) <= 64 else label[:61] + '…'
                return ('<pre class="out" tabindex="0" aria-label="%s"><code>%s</code></pre>'
                        % (attr('output of ' + label), '\n'.join(parts)))
            if typ in ('bean', 'file'):
                body = self.lines_html(select(cap['text'].split('\n'), opts))
                return ('<pre class="file" tabindex="0" aria-label="%s"><span class="path">%s</span><code>%s</code></pre>'
                        % (attr(cap['label']), esc(cap['label']), body))
            return self.spans(cap['html'])
        if typ == 'svg':
            p = os.path.join(self.src, 'drawings', cid + '.svg')
            if not os.path.isfile(p):
                raise Refused(f'{page}: marker svg:{cid} names no drawing in site/drawings/')
            self.used.add('svg:' + cid)
            svg = open(p, encoding='utf-8').read().strip()
            return svg[svg.index('<svg'):]
        if typ == 'part':
            p = os.path.join(self.src, '_parts', cid + '.html')
            if not os.path.isfile(p):
                raise Refused(f'{page}: marker part:{cid} names no file in site/_parts/')
            text = open(p, encoding='utf-8').read().strip()
            root = '../' * page.count('/')
            here = page[:-len('.html')]

            def cur(m):
                if m.group(1) == here:
                    return ' aria-current="page"'
                if '/' in here and m.group(1).split('/')[0] == here.split('/')[0]:
                    return ' aria-current="true"'
                return ''
            text = re.sub(r'\{cur:([a-z/-]+)\}', cur, text)
            return (text.replace('{root}', root).replace('{release}', self.release).replace('{day}', DEMO_SHOWN)
                    .replace('{except}', self.drawn_elsewhere(root)))
        if typ == 'drawn':
            return self.drawn(cid, page)
        raise Refused(f'{page}: marker type {typ!r} is not one this build knows')

    def drawn_release(self):
        """The daftar release that grew the garden the machinery was drawn from, where it is not this build's: the
        drawing is kept from an earlier build unless --machinery draws it again."""
        p = os.path.join(self.dst, 'machinery', 'drawn.json')
        rel = json.load(open(p, encoding='utf-8')).get('daftar_release') if os.path.isfile(p) else None
        return rel if rel and rel != self.release else None

    def drawn_elsewhere(self, root):
        """What the footer's claim does not cover: the machinery's drawing, when it was made under another release."""
        rel = self.drawn_release()
        return ('' if not rel else ' — except <a href="%smachinery.html#drawn">the machinery\'s drawing</a>, its commands and its '
                'report, made from a garden grown by daftar <code>%s</code>' % (root, esc(rel)))

    def drawn(self, cid, page):
        self.used.add('drawn:' + cid)
        p = os.path.join(self.dst, 'machinery', 'drawn.json')
        if not os.path.isfile(p):
            return ('<p class="note">The drawing has not been made in this checkout: <code>site/machinery/drawn.json</code> '
                    'is not here. <code>python3 site/build.py --machinery &lt;checkout&gt;</code> makes it.</p>')
        rec = json.load(open(p, encoding='utf-8'))
        if cid == 'levels':
            rows = ''.join('<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>'
                           % (esc(lv.get('name', lv.get('id', ''))), esc(lv.get('audience', '')), esc(lv.get('question', '')))
                           for lv in rec.get('levels', []))
            return ('<div class="table"><table><thead><tr><th scope="col">level</th><th scope="col">for</th>'
                    '<th scope="col">the question it answers</th></tr></thead><tbody>%s</tbody></table></div>' % rows)
        if cid == 'mechanisms':
            rows = []
            for m in rec.get('mechanisms', []):
                qs = m.get('questions', {})
                rows.append('<tr><th scope="row">%s</th><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                            % (esc(m.get('title', m.get('key', ''))), esc(m.get('claim', '')), esc(qs.get('orient', '')),
                               esc(qs.get('understand', '')), esc(', '.join(m.get('parts', [])))))
            return ('<div class="table"><table><thead><tr><th scope="col">mechanism</th><th scope="col">its claim</th>'
                    '<th scope="col">orient asks</th><th scope="col">understand asks</th><th scope="col">the beans it shows</th>'
                    '</tr></thead><tbody>%s</tbody></table></div>' % ''.join(rows))
        if cid == 'cannot':
            items = []
            for m in rec.get('mechanisms', []):
                op = m.get('operate') or {}
                would = op.get('would_take')
                why = str(op.get('why_none', '')).strip()
                why = why[:1].upper() + why[1:] + ('' if not why or why.endswith('.') else '.')
                items.append('<li><strong>%s</strong>: %s%s</li>'
                             % (esc(m.get('title', m.get('key', ''))),
                                ('it would take the <em>%s</em> shape with live data. ' % esc(would)) if would else
                                'no shape of the drawing kit fits it. ', esc(why)))
            return '<ul>%s</ul>' % ''.join(items)
        if cid == 'transcript':
            parts = []
            for s in rec.get('transcript', []):
                parts.append('<span class="cmd">%s$ %s</span>' % (esc(s.get('cwd', '~')), esc(s.get('cmd', ''))))
                if s.get('out'):
                    parts.append(esc(s['out'].rstrip('\n')))
                if s.get('exit'):
                    parts.append('<span class="exit">exit %d</span>' % s['exit'])
            return ('<pre class="out" tabindex="0" aria-label="how the report was drawn"><code>%s</code></pre>'
                    % '\n'.join(parts))
        if cid == 'when':
            other = self.drawn_release()
            return ('<p>Drawn by %s %s on %s, from a clone of garden-sam grown by daftar %s. Its garden ids are those of the '
                    'build that drew it: each build of these pages grows the gardens again, with new ids.%s</p>'
                    % (esc(rec.get('tool', '')), esc(rec.get('tool_release', '')), esc(rec.get('drawn_at', '')),
                       esc(rec.get('daftar_release', '')),
                       '' if not other else
                       (' That is not the release every other output on these pages comes from, daftar %s: the drawing, its '
                        'commands and its report say what that garden said, in the words of the law daftar %s carried, and '
                        'a word the law has renamed since is in them as it was. <code>python3 bin/dmwhy.py retired</code> '
                        'lists what each old word became.' % (esc(self.release), esc(other)))))
        raise Refused(f'{page}: drawn:{cid} is not a part of the drawing this build knows')

    def page(self, rel):
        text = open(os.path.join(self.src, rel), encoding='utf-8').read()

        def fill(m):
            typ, cid, raw, _ = m.groups()
            opts = dict(re.findall(r' ([a-z]+)="([^"]*)"', raw))
            return '<!-- daftar:%s id="%s"%s -->%s<!-- /daftar:%s -->' % (typ, cid, raw, self.render(typ, cid, opts, rel), typ)
        text = MARKER.sub(fill, text)
        text = re.sub(r'(/(?:blob|tree)/)v\d+\.\d+\.\d+/', lambda m: m.group(1) + self.release + '/', text)
        out = os.path.join(self.dst, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)


def page_list(root):
    """Every page the build fills: the site's HTML, less the shared parts and the machinery's own report."""
    out = []
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = sorted(x for x in dirnames if x not in ('_parts', '__pycache__', 'demo', 'drawings', 'machinery'))
        out += [os.path.relpath(os.path.join(dirpath, f), root).replace(os.sep, '/') for f in files if f.endswith('.html')]
    return sorted(out)


def fresh_dir(path, what):
    path = os.path.abspath(path)
    if os.path.exists(path) and (not os.path.isdir(path) or os.listdir(path)):
        raise Setup(f'{what} {path} is not empty')
    os.makedirs(path, exist_ok=True)
    return path


def main():
    ap = argparse.ArgumentParser(description='Grow the demo gardens and fill the pages with what the tools print.')
    ap.add_argument('--out', help='write the whole site to this directory and leave site/ untouched')
    ap.add_argument('--machinery', metavar='CHECKOUT', help='draw the machinery with the drawing tool at CHECKOUT')
    ap.add_argument('--keep', metavar='DIR', help='grow the gardens here and leave them')
    a = ap.parse_args()
    try:
        release, common = setup()
        out = fresh_dir(a.out, '--out') if a.out else SITE
        T = fresh_dir(a.keep, '--keep') if a.keep else tempfile.mkdtemp(prefix='daftar-site-')
        try:
            env = demo_env(T)
            d = Demo(T, env, release)
            d.sh(T, f'git clone -q --branch {release} {common} {T}/daftar')
            d.sh(d.p('daftar'), f'git remote set-url origin {GITHUB}.git')
            scenes(d)
            if a.keep:
                with open(os.path.join(T, 'captures.json'), 'w', encoding='utf-8') as f:
                    json.dump(d.caps, f, ensure_ascii=False, indent=1)
            leaks(d)
            if out != SITE:
                shutil.copytree(SITE, out, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
            if a.machinery:
                mb = os.path.join(SITE, 'machinery', 'build.py')
                r = subprocess.run([PY, mb, os.path.abspath(a.machinery), '--garden', d.p('garden-sam'), '--site', out],
                                   env=env) if os.path.isfile(mb) else None
                if r is None or r.returncode != 0:
                    print('the machinery was not drawn (%s); the machinery page keeps its committed drawing'
                          % ('site/machinery/build.py is not here' if r is None else f'exit {r.returncode}'))
            else:
                p = os.path.join(out, 'machinery', 'drawn.json')
                when = json.load(open(p, encoding='utf-8')).get('drawn_at') if os.path.isfile(p) else None
                print(f'the machinery page keeps its drawing of {when}' if when else
                      'the machinery page has no drawing in this checkout (site/machinery/drawn.json)')
            pages = Pages(d, release, SITE, out)
            for rel in page_list(SITE):
                pages.page(rel)
            made = {c for c in d.caps}
            unused = sorted(made - pages.used)
            if unused:
                raise Refused('captures no page uses: ' + ', '.join(unused))
            drawings = {'svg:' + f[:-4] for f in os.listdir(os.path.join(SITE, 'drawings')) if f.endswith('.svg')}
            if drawings - pages.used:
                raise Refused('drawings no page uses: ' + ', '.join(sorted(drawings - pages.used)))
            print(f'built {len(page_list(SITE))} pages from {len(d.caps)} captures, daftar {release}, the day held at {DEMO_SHOWN}'
                  + ('' if out == SITE else f', into {out}'))
        finally:
            if not a.keep:
                shutil.rmtree(T, ignore_errors=True)
    except Setup as e:
        print(f'site/build.py: {e}', file=sys.stderr)
        return 2
    except Refused as e:
        print(f'site/build.py: REFUSED — {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
