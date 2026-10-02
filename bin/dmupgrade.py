#!/usr/bin/env python3
"""dmupgrade — bring a garden's language up to a daftar release: the door every garden upgrades through.

    python3 bin/dmupgrade.py <tag>                       # from https://github.com/0mit/daftar
    python3 bin/dmupgrade.py <tag> --from <url-or-path>  # from any clone that carries the tag
    python3 bin/dmupgrade.py <tag> --extend <profile>    # opt into a profile the law offers, and receive its asset
    python3 bin/dmupgrade.py <tag> --retract <profile>   # leave it, and have its asset taken away

A release is a TAG on the public repository. What a garden receives from it is declared once, in the release's own
`seed/LANGUAGE` — the same file `seed/germinate.py` reads — so a new garden and an upgraded one cannot disagree about
what the language is.

THE DOOR KEEPS ITS NAME. Every other tool takes its verb's name (`bin/<verb>.py`); this one is still `bin/dmupgrade.py`
(v1 part 13), because a garden in today's words runs its own copy of it, which hands over to the release's own tool by
that path. This release's copy does two things: it ADOPTS the core into a garden in today's words, and it MOVES a garden
of the core to another release of the core. A garden in today's words moves between releases in today's words by its
own copy, which hands over to the release's; one older than the last of them (v0.49.0, std-vocab 32) is brought there
first, and adopts the core from there.

ADOPTING THE CORE (v1). A release gives a garden the law its seed/GARDEN.md.template pins, and a garden runs the law
its GARDEN.md pins. A garden in today's words (`std-vocab@…`) ADOPTS a release that gives the core (`core@<version>`):
once, in place, in one commit. It is planned first and touches nothing until it can be done whole — a profile moved in
the same run is refused, every bean must be committed, the garden must pass its own gate, and the RELEASE'S translator
(core/translate.py) must write the whole garden in the core's statements into a copy beside it, every value of every
bean given exactly one place and found there when the file is read back; it reads the words of the last std-vocab, and
refuses a garden in older ones, which first upgrades to the last release of today's language. Then the release's files
come in, the beans, VOCAB.md (the core's rows added, its pin gone) and GARDEN.md (pinning the core, the release
recorded) are the translation's, the hooks are installed again, a RULE-CHANGE entry is written — quoting the count and
naming every bean, with who ratified it and why left for a person — and the core's gate runs: a garden it refuses is
put back whole, today's hooks with it. The commit that follows is the one the core's gate grants the moments history
recorded, that once (core/commit.py). A garden that runs the core already is not moved back to today's words.

MOVING TO A LATER RELEASE OF THE CORE (v1 part 5). A garden that runs the core moves to another release of the core in
place, planned first as the adoption is: a profile moved in the same run is refused (a profile in a garden of the core is
v1's part 11), the working tree must be clean, and the garden must pass its own gate. The core's version is the release's
(its core/law/core.yaml `version`): a release whose core is older than the one the garden pins is refused unless
--allow-downgrade says so. Then the release's files come in, GARDEN.md pins the release's core (`core@<version>`) and
records the release, the hooks are installed again, and a RULE-CHANGE entry is written — the versions, what changed, and
who ratified it and why left for a person — and the release's gate judges the garden under the release's law: a garden
it refuses is put back whole. A core whose words change carries the step that rewrites a garden's statements into them,
here, beside this one, when it comes; none has yet. It does not commit: the person reads the diff, fills the entry, and
commits, and the core's gate judges that commit as any other.

OPTING INTO A PROFILE IS ONE ACT OF THIS TOOL. `--extend <profile>` (or `--retract <profile>`), each as often as
needed, with the release GARDEN.md records — or with a newer one, in the same run as the crossing: the profile is
written in, or taken out of, VOCAB.md's `profiles` (the edit PROVED as every other: the front matter parses to
exactly the old one with that list changed, and the body is untouched), what a garden extending the profiles receives
is copied — a profile's asset, `assets/<profile>/`, among it — and what it no longer receives is removed, read by
bin/pass.py, the one reader of seed/LANGUAGE; the journal entry says RULE-CHANGE and names the profiles; and the gate
runs, putting every file back when the garden does not pass — a garden that still writes a term of a profile it
leaves, say. A profile the release's law does not offer is refused before anything is touched.

A RELEASE IS AUTHENTICATED BEFORE ANY OF IT RUNS. Its own tool, its seed/germinate.py and the hooks it installs are
code, and the release is fetched from a network; so, between the fetch and the first line of it that runs:
  - a SIGNED tag must verify against the keys this garden's own release names (`seed/RELEASE-SIGNERS`, an
    allowed-signers file read by `ssh-keygen -Y verify`): a signature that does not verify, or one by a key the file
    does not name, is REFUSED. The file travels with each release, so a garden trusts the next release by the keys of
    the one it runs, and a key is changed only by a release signed by the key before it;
  - `--expect <commit>` (twelve hexadecimal digits or more) accepts the commit named and no other, signed or not:
    what a person checked against the release's own page;
  - otherwise a tag fetched from a network — unsigned, or signed where this machine cannot check it — is shown, with
    its commit, and run only when the person at the terminal types that commit's first twelve digits; with no
    terminal it is REFUSED, printing the `--expect` line to run once the commit is checked. A repository on this
    machine is the person's own copy, and is used with a line saying it was not authenticated, and why.

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
import argparse, copy, datetime, importlib.util, inspect, json, os, re, shlex, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import form as dmform
import parse as dmparse
import garden as dmgarden  # noqa: E402 — the one garden model: where its documents are
import importlib
dmpass = importlib.import_module('pass')
import reform as dmreform
import safe as dmsafe

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPSTREAM = 'https://github.com/0mit/daftar.git'
PIN = re.compile(r'^(extends: std-vocab@)(\S+)', re.M)
RELEASE = re.compile(r'^daftar_release:.*$', re.M)
SEMVER = re.compile(r'^v?(\d+)\.(\d+)\.(\d+)$')
SIGNERS = 'seed/RELEASE-SIGNERS'      # the keys a release is signed with, as `ssh-keygen -Y verify` reads them
PRINCIPAL = 'daftar-release'          # the one name those keys are given there


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


def local_source(src):
    """True for a repository on this machine: a directory, or a file:// URL."""
    return str(src).startswith('file://') or os.path.isdir(str(src))


def tag_signature(rel, tag):
    """(payload, signature, kind) of an annotated tag in the clone at `rel` — the tag object without its signature, the
    signature, and 'ssh' or 'openpgp' — or None for a tag that carries none, or is no annotated tag at all."""
    r = subprocess.run(['git', 'cat-file', 'tag', tag], cwd=rel, capture_output=True)
    if r.returncode != 0:
        return None
    for marker, kind in ((b'-----BEGIN SSH SIGNATURE-----', 'ssh'), (b'-----BEGIN PGP SIGNATURE-----', 'openpgp')):
        i = r.stdout.find(marker)
        if i >= 0:
            return r.stdout[:i], r.stdout[i:], kind
    return None


def verify_signature(payload, signature, signers):
    """(True, how) when an SSH signature over `payload` verifies with a key the allowed-signers file `signers` gives
    the release's name; (False, why) when it does not; (None, why) when this machine cannot say."""
    if not shutil.which('ssh-keygen'):
        return None, "this machine has no ssh-keygen to check its signature"
    with tempfile.TemporaryDirectory(prefix='dmupgrade-sig-') as t:
        sig = os.path.join(t, 'tag.sig')
        with open(sig, 'wb') as fh:
            fh.write(signature)
        r = subprocess.run(['ssh-keygen', '-Y', 'verify', '-f', signers, '-I', PRINCIPAL, '-n', 'git', '-s', sig],
                           input=payload, capture_output=True)
    out = (r.stdout + r.stderr).decode('utf-8', 'replace').strip()
    if r.returncode == 0:
        return True, f"its tag is signed by a key {SIGNERS} names ({out.splitlines()[0][:120] if out else 'verified'})"
    if 'unknown option' in out or 'usage:' in out.lower():
        return None, "this machine's ssh-keygen cannot check a signature (`ssh-keygen -Y verify`, OpenSSH 8.2 and later)"
    return False, f"its tag's signature does not verify with a key {SIGNERS} names ({out[:200] or 'no reason given'})"


def authenticate(rel, tag, sha, src, expect, garden):
    """How the release in the clone at `rel` is known to be the one meant, before anything in it runs — or exit,
    having run nothing of it and touched nothing of the garden. See `A RELEASE IS AUTHENTICATED` above."""
    if expect:
        e = expect.strip().lower()
        if not re.fullmatch(r'[0-9a-f]{12,40}', e):
            sys.exit(f"REFUSING: --expect takes the release's commit, twelve hexadecimal digits or more; {expect!r} "
                     f"is not one. Nothing from {tag} has run.")
        if not sha.startswith(e):
            sys.exit(f"REFUSING: {tag} from {src} is commit {sha}, not the {e} --expect names. Nothing from it has "
                     f"run, and nothing in this garden changed.")
        return f"the commit --expect names ({sha[:12]})"
    signed = tag_signature(rel, tag)
    signers = os.path.join(garden, *SIGNERS.split('/'))
    why = "its tag carries no signature" if signed is None else \
        "its tag is signed with OpenPGP, and a release is checked against SSH keys" if signed[2] != 'ssh' else \
        f"this garden's release names no keys ({SIGNERS} is not here)" if not os.path.isfile(signers) else None
    if why is None:
        ok, why = verify_signature(signed[0], signed[1], signers)
        if ok:
            return why
        if ok is False:
            sys.exit(f"REFUSING: {tag} from {src} (commit {sha}): {why}. Nothing from it has run, and nothing in this "
                     f"garden changed. If the release's keys changed, check {tag}'s commit against its own page and run "
                     f"again with --expect <commit>.")
    if local_source(src):
        return f"not authenticated — {why} — and taken as it stands, from a repository on this machine"
    head = (f"{tag} from {src} is commit {sha}, and is NOT AUTHENTICATED: {why}. Nothing from it has run yet. "
            f"Check the commit against the release's own page before running its code.")
    if sys.stdin is not None and sys.stdin.isatty():
        print(head, flush=True)
        try:
            said = input(f"Type the commit's first twelve digits to run {tag}, or anything else to stop: ")
        except EOFError:
            said = ''
        if said.strip().lower() == sha[:12]:
            return f"not authenticated — {why} — and confirmed at the terminal ({sha[:12]})"
        sys.exit("REFUSING: not confirmed. Nothing from the release ran, and nothing in this garden changed.")
    sys.exit(f"REFUSING: {head}\nOnce it is checked, run:\n  python3 bin/dmupgrade.py {tag} --expect {sha[:12]}"
             + (f" --from {src}" if src != UPSTREAM else ''))


class Form(tuple):
    """How a file was written: its line end, and whether it opened with a byte-order mark. PowerShell 5.1 writes UTF-8
    with a BOM, the gate reads through one (parse.BOM), and a file is written back as it was found."""
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
    return dmpass.language(open(path, encoding='utf-8').read())


def shipped(root, extends=None):
    """What the tree at `root` ships, read by bin/pass.py, the one reader of seed/LANGUAGE: with `extends` None, every
    file its release KEEPS (a line naming a profile's asset read for every profile its law offers); with a list of
    profiles, what a garden extending them RECEIVES. Paths are `/`-separated, as git and seed/LANGUAGE write them."""
    lines = patterns(root)
    offers = dmpass.offered_in(tree_reader(root))
    files = [f for f in dmpass.tracked(root) if os.path.isfile(os.path.join(root, *f.split('/')))]
    return set(dmpass.kept(files, lines, offers) if extends is None else dmpass.received(files, lines, extends, offers))


def set_profiles(text, profiles, key='extends_profiles'):
    """VOCAB.md's text with `extends_profiles` (a garden of the core: `profiles`) set to `profiles`, in order: the key's
    whole block written again as one line where there is one, else a line written above `local_terms` (or before the
    closing fence); with none left, the key taken out. Proved before it is written: the front matter parses to exactly
    the old one with that one key changed, and the body is untouched — or the edit is refused."""
    old_fm, body = _parse(text)
    line = f"{key}: [{', '.join(profiles)}]\n"
    try:
        s, e = dmsafe.top_level_span(text, key)
        new = text[:s] + (line if profiles else '') + text[e:]
    except dmsafe.UnsafeEdit:
        if not profiles:
            return text
        new = re.sub(r'(?m)^(local_terms:)', lambda m: line + m.group(1), text, count=1)
        if new == text:
            head, sep, rest = text.partition('\n---\n')
            new = head + '\n' + line.rstrip('\n') + sep + rest
    new_fm, new_body = _parse(new)
    want = copy.deepcopy(old_fm) if isinstance(old_fm, dict) else {}
    if profiles:
        want[key] = list(profiles)
    else:
        want.pop(key, None)
    if new_fm != want or new_body != body:
        refuse(f"VOCAB.md's `{key}` could not be written without changing something else — write it by hand: "
               f"`{line.strip()}`, journal it as a RULE-CHANGE, commit, and run this again.")
    return new


def garden_profiles(root=None):
    """The profiles the garden's VOCAB.md extends, as it states them."""
    path = os.path.join(root or ROOT, 'VOCAB.md')
    fm = dmparse.loads(dmparse.read(path)[0] or '') or {} if os.path.isfile(path) else {}
    return dmpass.extended(fm)


def recorded_release():
    """The tag GARDEN.md records as `daftar_release:`, or None for a garden grown before v0.4.0 recorded one."""
    path = os.path.join(ROOT, 'GARDEN.md')
    fm = dmparse.loads(dmparse.read(path)[0] or '') or {} if os.path.isfile(path) else {}
    return str(fm['daftar_release']) if isinstance(fm, dict) and fm.get('daftar_release') else None


def tree_reader(root):
    """A reader of the files of the tree at `root`: a path's text, or None."""
    def read(p):
        try:
            with open(os.path.join(root, *p.split('/')), encoding='utf-8') as fh:
                return fh.read()
        except (OSError, UnicodeDecodeError):
            return None
    return read


def std_fm(root):
    return dmparse.loads(dmparse.read(os.path.join(root, 'seed', 'std-vocab.md'))[0] or '') or {}


def vocab_version(root):
    return str(std_fm(root).get('version'))


def vtuple(v):
    """'21.0' -> (21, 0); an unreadable version reads as the oldest, so a step is never skipped for want of one."""
    n = re.findall(r'\d+', str(v or ''))
    return tuple(int(x) for x in n[:2]) if n else (0, 0)


DOCS = ('beans', 'mappings')                              # where a bean or a mapping lives


def refuse(msg):
    sys.exit(f"REFUSING: {msg}\nNothing was touched.")


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


def path_of(gid):
    """Where the bean `gid` lives in this garden."""
    return os.path.join(ROOT, 'beans', gid + '.md')


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
    """This garden's id as bin/check.py's own_garden_id() reads it (std-vocab 21.0 `garden_id`): the first twelve hex
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tag', help='the release tag, e.g. v0.3.0')
    ap.add_argument('--from', dest='src', default=UPSTREAM, help=f'repository URL or path (default {UPSTREAM})')
    ap.add_argument('--allow-downgrade', action='store_true', help='adopt a tag older than the one GARDEN.md records')
    ap.add_argument('--garden', help='the garden to upgrade (default: the one this tool lives in)')
    ap.add_argument('--keep-on-failure', action='store_true', help='leave the files in place when the gate fails, to repair by hand')
    ap.add_argument('--zone', help='crossing into std-vocab 31.0: the civil time zone this garden reckons its days in, as the '
                                   'IANA database names it (e.g. Europe/Istanbul) — written as GARDEN.md `zone`')
    ap.add_argument('--gardener', help='crossing into std-vocab 21.0: the id of the person or org bean who keeps this garden '
                                       '(or DAFTAR_GARDENER in the environment)')
    ap.add_argument('--gardener-name', help='with --gardener, plants a new bean with this name '
                                            '(or DAFTAR_GARDENER_NAME in the environment)')
    ap.add_argument('--gardener-genos', '--gardener-kind', dest='gardener_genos',
                    help="with --gardener-name, the genos of the bean planted, one the law lets keep a garden: org for an "
                         "organisation (or DAFTAR_GARDENER_GENOS in the environment; default: a person, as "
                         "seed/germinate.py plants one). `--gardener-kind` and DAFTAR_GARDENER_KIND, the names before "
                         "22.0, are read the same")
    ap.add_argument('--extend', action='append', default=[], metavar='PROFILE',
                    help='opt into a profile the release\'s law offers: written in VOCAB.md, its asset received (again for another)')
    ap.add_argument('--retract', action='append', default=[], metavar='PROFILE',
                    help='leave a profile: taken out of VOCAB.md, its asset removed (again for another)')
    ap.add_argument('--expect', metavar='COMMIT',
                    help="the release's commit, checked against its own page: accept that commit and no other")
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
        # NOTHING THE RELEASE CARRIES RUNS BEFORE THIS: its tool, its germinate.py, its hooks
        print(f"{a.tag} ({sha[:12]}): {authenticate(rel, a.tag, sha, a.src, a.expect, ROOT)}", flush=True)
        tool = os.path.join(rel, 'bin', 'dmupgrade.py')
        if (not a.no_delegate and os.path.isfile(tool) and '--no-delegate' in open(tool, encoding='utf-8').read()
                and open(tool, 'rb').read() != open(os.path.abspath(__file__), 'rb').read()):
            print(f"handing over to {a.tag}'s own bin/dmupgrade.py — a release is applied by its own upgrade logic", flush=True)
            args = [sys.executable, tool, a.tag, '--from', rel, '--garden', ROOT, '--no-delegate', '--recorded-source', source]
            if "'--expect'" in open(tool, encoding='utf-8').read():
                args += ['--expect', sha]            # authenticated above; the release's tool is told which commit
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
            if getattr(a, 'zone', None) and "'--zone'" in open(tool, encoding='utf-8').read():
                args += ['--zone', a.zone]
            for _p in a.extend:
                args += ['--extend', _p]
            for _p in a.retract:
                args += ['--retract', _p]
            return subprocess.run(args + unknown).returncode
        if unknown:
            ap.error(f"unrecognized arguments: {' '.join(unknown)}")

        # THE LAW EACH SIDE RUNS (v1): a release gives a garden the law its GARDEN.md.template pins, and a garden runs the
        # law its GARDEN.md pins. A garden in today's words ADOPTS a release of the core, once and in place.
        gives, runs = law_of_release(rel), law_of_garden(ROOT)
        if gives == 'core' and runs == 'std-vocab':
            return adopt(a, rel, sha, source, current)
        if runs == 'core' and gives == 'core' and current == a.tag and not (a.extend or a.retract):
            print(f"nothing to do: this garden runs the core ({pin_of_garden(ROOT)}) of {a.tag} already.")
            return 0
        if runs == 'core' and gives == 'core':
            return move(a, rel, sha, source, current)
        if runs == 'core':
            refuse(f"this garden runs the core ({pin_of_garden(ROOT)}), and {a.tag} gives today's words: a garden of "
                   f"statements does not go back to them.")
        refuse(f"{a.tag} gives today's words, and this tool adopts the core or moves between releases of it: a garden in "
               f"today's words moves between their releases by its own bin/dmupgrade.py, which hands over to the "
               f"release's own (`{PY} bin/dmupgrade.py {a.tag}`).")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def plan_profiles(rel, tag, extend, retract):
    """The profiles the garden extends once this run is done: its own, with `--extend` added and `--retract` taken out,
    in the order it states them. A profile the release's law does not offer is refused before anything is touched; one
    both extended and retracted is a contradiction, refused too."""
    if not (extend or retract):
        return garden_profiles()
    offers = dmpass.offered_in(tree_reader(rel))
    both = sorted(set(extend) & set(retract))
    if both:
        refuse(f"{', '.join(both)} is both extended and retracted in one run: say which.")
    unknown = [p for p in extend if p not in offers]
    if unknown:
        refuse(f"{tag}'s law offers {', '.join(offers) or 'no profile'}; it does not offer {', '.join(unknown)}.")
    now = garden_profiles()
    out = [p for p in now if p not in retract] + [p for p in extend if p not in now]
    return out


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


def receive(rel, want, have, added):
    """Step 3: every file the garden receives from the release copied in, and every file it held that the release no
    longer gives taken out; (changed, removed). `added` is the caller's list, filled as files arrive."""
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
        # a directory the removal emptied goes with it — a profile's asset left behind as empty folders is still there
        # to a reader of the tree; git never held the folders, so taking them away is not a change it records
        d = os.path.dirname(os.path.join(ROOT, f))
        while os.path.realpath(d) != os.path.realpath(ROOT) and os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)
            d = os.path.dirname(d)
    return changed, removed


# ==== THE ADOPTION OF THE CORE (v1 part 4) =========================================================================
# A release of the core gives a garden the core's statements in place of today's words. The garden is translated by the
# release's own translator (core/translate.py), into a copy beside it and then in place, in the one commit that adopts
# the core: a RULE-CHANGE a person ratifies, which the core's gate grants the moments history recorded, that once
# (core/commit.py, `knowing`; ratified 2026-10-01). Nothing is a person's to decide but the adoption itself, so nothing
# is asked: every value of every bean is given exactly one place, the written file read back finds it there, and the
# count is the proof, quoted in the entry.
MANIFEST_PIN = re.compile(r'^(extends:[ \t]*)(\S+)', re.M)


def law_of_release(root):
    """'core' where a garden grown from the release at `root` runs the core — its seed/GARDEN.md.template pins `core@` —
    else 'std-vocab': the release says which law it gives a garden in the one place it gives it."""
    try:
        with open(os.path.join(root, 'seed', 'GARDEN.md.template'), encoding='utf-8') as fh:
            text = fh.read()
    except OSError:
        return 'std-vocab'
    return 'core' if re.search(r'(?m)^extends:[ \t]*core@', text) else 'std-vocab'


def pin_of_garden(root):
    """GARDEN.md's `extends`, as written, or ''."""
    try:
        with open(os.path.join(root, 'GARDEN.md'), encoding='utf-8') as fh:
            m = MANIFEST_PIN.search(dmparse.split_front_matter(fh.read())[0] or '')
    except OSError:
        return ''
    return m.group(2) if m else ''


def law_of_garden(root):
    return 'core' if pin_of_garden(root).startswith('core@') else 'std-vocab'


def adopt(a, rel, sha, source, current):
    """A garden in today's words adopts the core of the release at `rel`: planned first, touching nothing — its own gate
    passes, no bean is untracked, and the release's translator writes it whole into a copy with every value placed —
    then the release's files received, the translation brought in, the hooks installed, the entry written and the core's
    gate run; anything that fails puts every file back. It does not commit."""
    if a.extend or a.retract:
        refuse("a profile is extended or retracted in a run of its own, not in the one that adopts the core.")
    before = vocab_version(ROOT)
    # PLANNED FIRST: EVERY BEAN IS COMMITTED — an untracked one would be translated and adopted with nobody having saved it
    loose = dmgarden.untracked(ROOT)
    if loose:
        refuse(f"{len(loose)} bean(s) are not committed: {', '.join(loose[:8])}{' …' if len(loose) > 8 else ''}. Save them "
               f"(bin/save.py) or move them out, then adopt.")
    # ...AND THE GARDEN PASSES ITS OWN GATE, under the law it runs: the translator's map reads a garden that does
    own = os.path.join(ROOT, 'bin', 'dmcheck.py')           # its own gate, today's: v0.49.0's
    if os.path.isfile(own):
        g = run(sys.executable, own, '--all', check=False)
        if g.returncode != 0:
            errs = [ln for ln in g.stdout.splitlines() if ln.startswith('ERROR')]
            refuse(f"this garden does not pass its own gate (std-vocab {before}), and a translation reads a garden that "
                   f"does:\n" + '\n'.join(errs[:12]) + ('\n…' if len(errs) > 12 else '') +
                   "\nFix what these name and commit, then adopt.")
    tmp = tempfile.mkdtemp(prefix='dmadopt-')
    try:
        copy = os.path.join(tmp, 'garden')
        tr = run(sys.executable, os.path.join(rel, 'core', 'translate.py'), 'garden', ROOT, copy, check=False)
        said = (tr.stdout + tr.stderr).strip().splitlines()
        count = next((ln for ln in reversed(said) if ln.startswith('translate:')), '')
        if tr.returncode != 0 or not count:
            refuse(f"{a.tag}'s translator cannot write this garden in the core's statements:\n"
                   + '\n'.join('  ' + ln for ln in said[-14:]))
        return adopt_apply(a, rel, sha, source, current, before, copy, count)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def adopt_apply(a, rel, sha, source, current, before, copy, count):
    """The release's files, the translation, the pin, the hooks, the entry and the core's gate — or everything back."""
    profiles = garden_profiles()
    want = shipped(rel, profiles)
    have = shipped(ROOT) if os.path.isfile(os.path.join(ROOT, 'seed', 'LANGUAGE')) else set()
    added = []
    try:
        changed, removed = receive(rel, want, have, added)
        # THE TRANSLATION, IN PLACE: each bean and mapping as the translator wrote it, VOCAB.md with the core's rows and
        # without a pin, and GARDEN.md pinning the core — the release recorded as every upgrade records it
        beans = []
        for new in dmgarden.paths(copy):
            rel_ = os.path.relpath(new, copy)
            old = os.path.join(ROOT, rel_)
            if not os.path.isfile(old):
                sys.exit(f"REFUSING: the translation holds {rel_}, which the garden does not")
            if open(new, 'rb').read() != open(old, 'rb').read():
                shutil.copyfile(new, old)
                beans.append(os.path.basename(new)[:-3])
        law = []
        for f in ('VOCAB.md', 'GARDEN.md'):
            if os.path.isfile(os.path.join(copy, f)):
                shutil.copyfile(os.path.join(copy, f), os.path.join(ROOT, f))
                law.append(f)
        gpath = os.path.join(ROOT, 'GARDEN.md')
        gtext, gform = read_text(gpath)
        pin = pin_of_garden(ROOT)
        if not pin.startswith('core@'):
            sys.exit(f"REFUSING: the translation left GARDEN.md pinning {pin or 'nothing'}, not the core")
        gline = f'daftar_release: "{a.tag}"  # the daftar release this garden runs; bin/dmupgrade.py moves it'
        gtext = RELEASE.sub(gline, gtext, count=1) if RELEASE.search(gtext) else \
            re.sub(r'^extends:.*$', lambda m: m.group(0) + '\n' + gline, gtext, count=1, flags=re.M)
        write_text(gpath, gtext, gform)
        install()
        sys.path.insert(0, os.path.join(ROOT, 'bin')); import dmjournal          # the release's own tool, just applied
        _who = run('git', 'config', 'user.name', check=False).stdout.strip() or '(fill in who ran it)'
        lines = ['\n' + dmjournal.stamp(_who, f"RULE-CHANGE: language adopted: the core ({pin}), daftar {a.tag}", ROOT),
                 "- ratified_by: (fill in who ratified — the gardener's word, given here)",
                 f"- action: **RULE-CHANGE — `bin/dmupgrade.py {a.tag}`** from {source} at {sha}; std-vocab {before} -> "
                 f"{pin}; release {current or 'unrecorded'} -> {a.tag}. The garden adopts the core: its beans written in "
                 f"the core's statements by the release's translator, in place and in this one commit, which the core's "
                 f"gate grants the moments history recorded, this once (core/commit.py, `knowing`).",
                 f"- count: {count[len('translate: '):]}",
                 f"- changed: {', '.join(changed + law) or 'none'}",
                 f"- added: {', '.join(added) or 'none'}",
                 f"- removed: {', '.join(removed) or 'none'}",
                 "- why: (fill in — what adopting the core brings this garden)",
                 f"- beans: {', '.join(beans) or 'none'}"]
        jpath = os.path.join(ROOT, 'log', 'journal.md')
        with open(jpath, 'a', encoding='utf-8', newline=read_text(jpath)[1].nl) as j:
            j.write('\n'.join(lines) + '\n')
        gate = run(sys.executable, os.path.join(ROOT, 'bin', 'check.py'), check=False)
    except BaseException as e:
        put_back(added)
        print("NOT ADOPTED: the adoption stopped midway" + ('' if isinstance(e, SystemExit) else
              f" ({type(e).__name__}{': ' + str(e) if str(e) else ''})") + ", so every file was put back as it was.",
              file=sys.stderr, flush=True)
        raise
    last = (gate.stdout.strip().splitlines() or ['(the gate printed nothing)'])[-1]
    if gate.returncode != 0 and not a.keep_on_failure:
        put_back(added)
        errs = [ln for ln in gate.stdout.splitlines() if ln.strip() and not ln.startswith('core check')]
        print(f"NOT ADOPTED: in the core's statements this garden fails the core's gate, so every file was put back as "
              f"it was.\n" + '\n'.join(errs[:12]) + ('\n…' if len(errs) > 12 else '') + f"\n{last}\n"
              "Fix what these name in today's words (or pass --keep-on-failure to look at the translation in place), "
              "then run this again.")
        return 1
    print(f"adopted the core at {a.tag} ({sha[:12]}): std-vocab {before} -> {pin}; {len(beans)} bean(s) in statements, "
          f"{len(changed) + len(law)} changed, {len(added)} added, {len(removed)} removed.\n{count}\n{last}")
    print("\nNOT COMMITTED. Read `git diff`, complete the journal entry's two `fill in` fields, then\n"
          "  git add -A\n"
          "  git commit\n"
          "The commit is judged by the core's gate, which grants it the moments history recorded, this once.\n"
          "To abandon it instead:\n"
          "  git checkout -- ." + (f"\n  git clean -f -- {' '.join(_arg(f) for f in added)}" if added else ""))
    return 0 if gate.returncode == 0 else 1


def core_version(root):
    """The version of the core a tree carries — its core/law/core.yaml `version` — or ''."""
    try:
        with open(os.path.join(root, 'core', 'law', 'core.yaml'), encoding='utf-8') as fh:
            m = re.search(r'(?m)^version:[ \t]*["\']?([0-9][0-9.]*)', fh.read())
    except OSError:
        return ''
    return m.group(1) if m else ''


def move(a, rel, sha, source, current):
    """A garden of the core moves to another release of the core, in place: planned first, touching nothing; then the
    release's files, the pin and the release recorded, the hooks, the entry and the release's gate — or everything back.
    It does not commit."""
    pin = pin_of_garden(ROOT)
    have, gives = pin.split('@', 1)[1], core_version(rel)
    if not gives:
        refuse(f"{a.tag} carries no readable core version (core/law/core.yaml `version`) — nothing to pin to.")
    if vtuple(gives) < vtuple(have) and not a.allow_downgrade:
        refuse(f"{a.tag} gives the core {gives}, older than the core {have} this garden runs; pass --allow-downgrade "
               f"to go back to it.")
    dirty = run('git', 'status', '--porcelain', check=False).stdout.strip()
    if dirty:
        refuse("the working tree is not clean: commit or put aside what it holds, so a refusal can put every file back:\n"
               + dirty[:600])
    g = run(sys.executable, os.path.join(ROOT, 'bin', 'check.py'), '--all', check=False)
    if g.returncode != 0:
        errs = [ln for ln in g.stdout.splitlines() if ln.strip() and not ln.startswith('core check')]
        refuse(f"this garden does not pass its own gate ({pin}):\n" + '\n'.join(errs[:12]) +
               ('\n…' if len(errs) > 12 else '') + "\nFix what these name and commit, then move.")
    # THE PROFILES IT TAKES (v1 part 11): VOCAB.md `profiles`, one taken up (`--extend`) or put down (`--retract`) in
    # the same act, which brings the profile's asset or takes it away; a line of the law, so the entry is a RULE-CHANGE
    before = garden_profiles()
    profiles = plan_profiles(rel, a.tag, a.extend, a.retract)
    want = shipped(rel, profiles)
    held = shipped(ROOT) if os.path.isfile(os.path.join(ROOT, 'seed', 'LANGUAGE')) else set()
    added = []
    try:
        changed, removed = receive(rel, want, held, added)
        if profiles != before:
            vpath = os.path.join(ROOT, 'VOCAB.md')
            vtext, vform = read_text(vpath)
            write_text(vpath, set_profiles(vtext, profiles, key='profiles'), vform)
            changed = changed + ['VOCAB.md']
        gpath = os.path.join(ROOT, 'GARDEN.md')
        gtext, gform = read_text(gpath)
        new_pin = f"core@{gives}"
        gtext = MANIFEST_PIN.sub(lambda m: m.group(1) + new_pin, gtext, count=1)
        gline = f'daftar_release: "{a.tag}"  # the daftar release this garden runs; bin/dmupgrade.py moves it'
        gtext = RELEASE.sub(gline, gtext, count=1) if RELEASE.search(gtext) else \
            re.sub(r'^extends:.*$', lambda m: m.group(0) + '\n' + gline, gtext, count=1, flags=re.M)
        write_text(gpath, gtext, gform)
        install()
        sys.path.insert(0, os.path.join(ROOT, 'bin')); import journal as _journal   # the release's own tool, just applied
        _who = run('git', 'config', 'user.name', check=False).stdout.strip() or '(fill in who ran it)'
        title = f"RULE-CHANGE: language upgraded to daftar {a.tag}, the core {have} -> {gives}" if current != a.tag else \
            f"RULE-CHANGE: the profiles this garden takes, {', '.join(before) or 'none'} -> {', '.join(profiles) or 'none'}"
        lines = ['\n' + _journal.stamp(_who, title, ROOT),
                 "- ratified_by: (fill in who ratified — the gardener's word, given here)",
                 f"- action: **RULE-CHANGE — `bin/dmupgrade.py {a.tag}`** from {source} at {sha}; the core {pin} -> "
                 f"{new_pin}; release {current or 'unrecorded'} -> {a.tag}. The beans are as they were: no step rewrites "
                 f"them between these versions of the core."
                 + (f" The profiles it takes: {', '.join(before) or 'none'} -> {', '.join(profiles) or 'none'}"
                    f" (VOCAB.md `profiles`)." if profiles != before else ''),
                 f"- changed: {', '.join(changed + ['GARDEN.md']) or 'none'}",
                 f"- added: {', '.join(added) or 'none'}",
                 f"- removed: {', '.join(removed) or 'none'}",
                 "- why: (fill in — what this release brings the garden)"]
        jpath = os.path.join(ROOT, 'log', 'journal.md')
        with open(jpath, 'a', encoding='utf-8', newline=read_text(jpath)[1].nl) as j:
            j.write('\n'.join(lines) + '\n')
        gate = run(sys.executable, os.path.join(ROOT, 'bin', 'check.py'), check=False)
    except BaseException as e:
        put_back(added)
        print("NOT UPGRADED: the move stopped midway" + ('' if isinstance(e, SystemExit) else
              f" ({type(e).__name__}{': ' + str(e) if str(e) else ''})") + ", so every file was put back as it was.",
              file=sys.stderr, flush=True)
        raise
    last = (gate.stdout.strip().splitlines() or ['(the gate printed nothing)'])[-1]
    if gate.returncode != 0 and not a.keep_on_failure:
        put_back(added)
        errs = [ln for ln in gate.stdout.splitlines() if ln.strip() and not ln.startswith('core check')]
        print(f"NOT UPGRADED: under {a.tag}'s law this garden fails the gate, so every file was put back as it was.\n"
              + '\n'.join(errs[:12]) + ('\n…' if len(errs) > 12 else '') + f"\n{last}")
        return 1
    print(f"upgraded to {a.tag} ({sha[:12]}): the core {have} -> {gives}; {len(changed) + 1} changed, {len(added)} added, "
          f"{len(removed)} removed.\n{last}")
    print("\nNOT COMMITTED. Read `git diff`, complete the journal entry's two `fill in` fields, then\n"
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
