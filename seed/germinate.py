#!/usr/bin/env python3
"""germinate — grow a new garden from this seed.

    python3 seed/germinate.py <target-directory>        # the directory must not exist yet
    python3 seed/germinate.py <target-directory> --gardener <id> [--gardener-name "<how they are called>"]
                                                 [--gardener-genos org]  # an organisation keeps it, not a person
                                                 [--name <garden-name>]  # a name other than the directory's

(`python` on Windows.) Name the directory for the garden — `garden-sam`, not `garden` — because its name is the
garden's name, which another garden and every proposal this one makes will show. The name is held to the form the
law's `manifest.garden` gives it (kebab-case), and a name out of that form is refused BEFORE anything is created;
`--name` gives the garden a name of its own where the directory's is not one. Anything that stops germination once
it has begun removes the directory it made, so a second try starts from nothing.

GROWN FROM INSIDE A GARDEN — a rehearsal, as seed/COOKBOOK.md grows one — the language is that garden's, and so is
the release it records: the one that garden's GARDEN.md names, never that garden's own last commit.

A garden is a git repository that carries the LANGUAGE — the vocabulary, the parser, the gate, the tools,
the templates — and no beans. WHAT TRAVELS IS DECLARED ONCE, in seed/LANGUAGE, and bin/dmupgrade.py reads
the same file, so a new garden and an upgraded one receive exactly the same set. The garden is given its
name, its vocabulary pin and the release it runs, its first commit as `germinate`, the gate as a pre-commit
hook, and it is checked: it passes its own gate with nothing in it.

A GARDEN IS KEPT BY SOMEONE. With `--gardener <id>` the second commit plants the gardener's bean — a person, or
with `--gardener-genos org` an organisation: a genos the law's `manifest.gardener` admits — and names it in GARDEN.md,
so the garden begins as someone's and the gardener is its first bean. Without it the closing message says that this
is the first thing to write — the gate asks for it as soon as the garden holds a bean.

Python, not shell, because a garden is grown on Windows too. `seed/germinate.sh` remains and hands over here.
"""
import glob
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys


def die(msg, code=2):
    print(f"germinate: {msg}", file=sys.stderr)
    sys.exit(code)


def shown(path):
    """A path as a command line takes it in a Unix shell, cmd.exe and PowerShell alike: bare where it is plain, else in
    double quotes, which all three read the same way for a path holding no `"`, `$`, `%` or backquote. A Windows
    user folder often holds a space, and `cd C:\\Users\\Sam Smith\\garden-sam` is two arguments to every shell."""
    s = str(path)
    if re.fullmatch(r'[\w./\\:-]+', s) and not s.startswith('-'):
        return s
    if not re.search(r'["$%`]', s):
        return f'"{s}"'
    return "'" + s.replace("'", "''") + "'" if os.name == 'nt' else shlex.quote(s)


def manifest_form(law, attr):
    """(pattern, refusal) that the law's `manifest.attrs.<attr>` holds a value to — its `in: { type: <value type> }`
    read through `value_types`, or its own `in: { pattern }` — or None where the law gives that attribute no form.
    Read from the law, so the form is never written here (bin/dmupgrade.py asks the same of a garden it upgrades)."""
    rec = ((law.get('manifest') or {}).get('attrs') or {}).get(attr) if isinstance(law.get('manifest'), dict) else None
    dom = rec.get('in') if isinstance(rec, dict) else None
    if not isinstance(dom, dict):
        return None
    if isinstance(dom.get('pattern'), str):
        return dom['pattern'], None
    row = next((t for t in law.get('value_types') or [] if isinstance(t, dict) and t.get('type') == dom.get('type')),
               None)
    return (row['pattern'], row.get('refusal')) if row and isinstance(row.get('pattern'), str) else None


def name_like(name, form, fallback='garden-sam'):
    """The nearest name to `name` in the form — lowercase, every run of other characters one hyphen — to offer in a
    refusal; `fallback` where nothing of it survives (a name in another script)."""
    import dmparse
    guess = re.sub(r'[^a-z0-9]+', '-', str(name).lower()).strip('-')
    return guess if guess and dmparse.law_match(form, guess) else fallback


def remove_tree(path):
    """A directory germination made, removed whole — on Windows too, where git writes its objects read-only and a plain
    rmtree stops at the first one."""
    def again(fn, p, *_):
        os.chmod(p, stat.S_IWRITE)
        fn(p)
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=again)
    else:
        shutil.rmtree(path, onerror=again)


def run(*args, cwd=None, check=True):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if check and r.returncode != 0:
        die(f"`{' '.join(args)}` failed:\n{r.stdout}{r.stderr}", 1)
    return r


def language_files(root, seed):
    """Every file seed/LANGUAGE names, in order; a pattern that matches nothing is an error."""
    out = []
    for line in open(os.path.join(seed, 'LANGUAGE'), encoding='utf-8'):
        pat = line.strip()
        if not pat or pat.startswith('#'):
            continue
        hits = [f for f in sorted(glob.glob(os.path.join(root, pat))) if os.path.isfile(f)]
        if not hits and not any(os.path.isdir(f) for f in glob.glob(os.path.join(root, pat))):
            die(f"seed/LANGUAGE names '{pat}', which matches no file", 1)
        out += [os.path.relpath(f, root) for f in hits]
    return out


def gardener_gene(law):
    """The gene the law's `manifest.gardener` admits, wherever its `in:` lists them; None where it lists none."""
    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get('gene'), list):
                return [str(k) for k in node['gene']]
            for v in node.values():
                found = walk(v)
                if found is not None:
                    return found
        return None
    return walk(((law.get('manifest') or {}).get('attrs') or {}).get('gardener'))


def gardener_form(law, genos):
    """What the law says a gardener of this genos is written with: its nature, its anchor term and class, and whether
    the genos is pinned to the crown (and to which branch). Read from the law, so no genos is named here."""
    row = next((k for k in law.get('gene') or [] if isinstance(k, dict) and k.get('genos') == genos), None)
    if row is None:
        return None
    nature = row.get('of_nature')
    term = next((t for t in law.get('terms') or [] if isinstance(t, dict) and t.get('term') == f'{genos}_id'
                 and isinstance(t.get('anchor'), dict)), None)
    if term is None:
        return None
    forms = row.get('ownership_form')
    crown = next((n.get('crown') for n in law.get('natures') or [] if isinstance(n, dict) and n.get('nature') == nature),
                 None) if forms == 'crown' or forms == ['crown'] else None
    return {'nature': nature, 'key': term['term'], 'class': term['anchor'].get('class', 'logical'), 'crown': crown}


def gardener_bean(gid, name, when, garden_id=None, genos='person', form=None):
    """The gardener's bean — the garden's first. A person is owned by no being (the crown: agape) and answers for
    themself; an organisation is owned outside this garden, by whoever its own rules say, and answers for itself.
    Its anchor is a name this garden mints, `<genos>:<id>`, QUALIFIED at birth by the garden's own id when that is
    known — so the gardener can be named in another garden from the first proposal on, and no other garden's
    `<genos>:<id>` is them."""
    import json
    form = form or {'nature': 'empsychon', 'key': 'person_id', 'class': 'logical', 'crown': 'agape'}
    pid = f"{garden_id}/{genos}:{gid}" if garden_id else f"{genos}:{gid}"
    owner = (f"crown: {form['crown']}" if form['crown']
             else 'external: "its members, as its own rules say: outside this garden"')
    who = 'person who keeps' if genos == 'person' else 'organisation that keeps'
    return f"""---
bean: {gid}
genos: {genos}
title: {json.dumps(name, ensure_ascii=False)}
status: active
summary: "The gardener: the {who} this garden."
nature: {form['nature']}
owned_by: {{ legal: {{ {owner} }} }}
responsibility: {{ legal: {{ self: true }} }}
identity:
  status: confirmed
  anchors:
    - {{ key: {form['key']}, value: "{pid}", class: {form['class']}, establishing: true }}
provenance: {{ src: asserted-by-human, by: "{gid} (gardener)", as_of: {when} }}
---
{name} keeps this garden.
"""


def main(argv):
    gid = gname = name = None
    ggenos = 'person'
    if '--name' in argv:
        i = argv.index('--name'); name = argv[i + 1] if i + 1 < len(argv) else ''; argv = argv[:i] + argv[i + 2:]
        if not name:
            die("--name takes the garden's name, in kebab-case: e.g. --name garden-sam")
    if '--gardener' in argv:
        i = argv.index('--gardener'); gid = argv[i + 1] if i + 1 < len(argv) else None; argv = argv[:i] + argv[i + 2:]
        if not gid or not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', gid):
            die("--gardener takes the id of whoever keeps the garden — a person, or with --gardener-genos org an "
                "organisation: kebab-case, e.g. --gardener sam")
    if '--gardener-name' in argv:
        i = argv.index('--gardener-name'); gname = argv[i + 1] if i + 1 < len(argv) else None; argv = argv[:i] + argv[i + 2:]
    # `--gardener-kind` is the same flag under the name the law used before 22.0, taken so a line written then still runs
    for _flag in ('--gardener-genos', '--gardener-kind'):
        if _flag in argv:
            i = argv.index(_flag); ggenos = argv[i + 1] if i + 1 < len(argv) else ''; argv = argv[:i] + argv[i + 2:]
            if not gid:
                die(f"{_flag} says what the gardener named by --gardener is: give --gardener <id> too")
    if len(argv) != 1 or argv[0] in ('-h', '--help'):
        print(__doc__); return 0 if argv else 2
    target = argv[0]
    if os.path.exists(target):
        die(f"{shown(target)} already exists — refusing to plant over it")
    parent = os.path.dirname(os.path.abspath(target))
    if not os.path.isdir(parent):
        die(f"{shown(parent)} does not exist — create it first")
    target = os.path.abspath(target)
    seed = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(seed)
    try:
        import yaml  # noqa: F401
    except ImportError:
        die("PyYAML is required (pip install PyYAML)")
    sys.path.insert(0, os.path.join(root, 'bin'))
    import dmparse, yaml
    law = yaml.safe_load(dmparse.read(os.path.join(seed, 'std-vocab.md'))[0])
    ver = str(law['version'])
    if not ver:
        die("could not read the vocabulary version", 1)
    # THE NAME IS JUDGED BEFORE ANYTHING IS CREATED. The gate judges the manifest as itself, so a name out of the law's
    # form was refused only at the first commit — after the directory was made, and a second try then met "already
    # exists". The form is the law's (`manifest.garden`), read, never written here.
    garden = name if name is not None else os.path.basename(target)
    form = manifest_form(law, 'garden')
    if form and not dmparse.law_match(form[0], garden):
        like = name_like(garden, form[0], f'garden-{gid}' if gid else 'garden-sam')
        said = f"the law's `manifest.garden` " + (form[1] if form[1] else f"must match {form[0]}")
        if name is not None:
            die(f"--name {garden!r} cannot be a garden's name: {said}. Name it in kebab-case, e.g. --name {like}. "
                f"Nothing was created.")
        die(f"{garden!r} cannot be this garden's name, which is its directory's: {said}.\n"
            f"  Name the directory in kebab-case, e.g. {like} — or keep it, and give the garden that name: "
            f"--name {like}\n"
            f"Nothing was created.")
    gform = None
    if gid:
        admitted = gardener_gene(law)
        gform = gardener_form(law, ggenos)
        if (admitted is not None and ggenos not in admitted) or gform is None:
            die(f"--gardener-genos {ggenos!r} is not a genos the law lets keep a garden"
                + (f" ({', '.join(admitted)})" if admitted else " (it needs a genos with a `<genos>_id` anchor term)"))
    # GROWN FROM INSIDE A GARDEN (a rehearsal, as the COOKBOOK grows one): the language is the garden's, and the release
    # is the one its GARDEN.md records. The garden's own commit names no daftar release — recorded as one, it put a
    # false `untagged <sha>` on the rehearsal and told the stranger to check out a tag in the real garden.
    grown_in = None
    if os.path.isfile(os.path.join(root, 'GARDEN.md')):
        try:
            _gm = dmparse.loads(dmparse.read(os.path.join(root, 'GARDEN.md'))[0] or '') or {}
        except Exception:
            _gm = {}
        _gm = _gm if isinstance(_gm, dict) else {}
        _rf = manifest_form(law, 'daftar_release')
        _said = str(_gm.get('daftar_release') or '')
        grown_in = str(_gm.get('garden') or os.path.basename(root))
        release = _said if _said and (not _rf or dmparse.law_match(_rf[0], _said)) else 'untagged unknown'
    else:
        # NO GIT HISTORY OF ITS OWN (a ZIP download, a `git archive`): no commit can be named, and the garden says so —
        # `untagged unknown`, which the law's `daftar_release` admits — rather than recording nothing, so the line the
        # gate ends with still names the garden, its gardener and its id. A copy unpacked inside some OTHER repository
        # has no history either: git would answer for that repository, so only a checkout whose top is this copy is
        # asked.
        top = run('git', '-C', root, 'rev-parse', '--show-toplevel', check=False)
        own = top.returncode == 0 and top.stdout.strip() and \
            os.path.normcase(os.path.realpath(top.stdout.strip())) == os.path.normcase(os.path.realpath(root))
        r = run('git', '-C', root, 'describe', '--tags', '--exact-match', check=False) if own else None
        if r is not None and r.returncode == 0:
            release = r.stdout.strip()
        else:
            sha = run('git', '-C', root, 'rev-parse', '--short', 'HEAD', check=False) if own else None
            release = f"untagged {sha.stdout.strip() if sha is not None and sha.returncode == 0 and sha.stdout.strip() else 'unknown'}"

    # FROM HERE ON THE DIRECTORY IS GERMINATE'S. Whatever stops the growing — a commit git refuses, a file it cannot
    # copy, an interrupt — removes it whole, so a stranger's second try starts from nothing rather than from "already
    # exists — refusing to plant over it".
    try:
        grow(target, root, seed, ver, garden, release, gid, gname, ggenos, gform)
    except BaseException:
        if os.path.isdir(target):
            try:
                remove_tree(target)
                print(f"germinate: removed {shown(target)}, which it had begun to grow; nothing is left behind",
                      file=sys.stderr)
            except OSError as e:
                print(f"germinate: could not remove {shown(target)} ({e}); delete it before trying again",
                      file=sys.stderr)
        raise
    return finish(target, root, ver, release, gid, ggenos, grown_in)


def grow(target, root, seed, ver, garden, release, gid, gname, ggenos, gform):
    """The language copied, the templates filled, the first commit made, and the gardener planted."""
    for d in ('beans', 'mappings', 'log', 'seed'):
        os.makedirs(os.path.join(target, d), exist_ok=True)
    for rel in language_files(root, seed):
        dst = os.path.join(target, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(root, rel), dst)
    for dp, dns, _ in os.walk(target):
        for dn in list(dns):
            if dn == '__pycache__':
                shutil.rmtree(os.path.join(dp, dn)); dns.remove(dn)

    subst = {'@@VERSION@@': ver, '@@GARDEN@@': garden, '@@RELEASE@@': release}
    def fill(src, dst):
        text = open(src, encoding='utf-8').read()
        for k, v in subst.items():
            text = text.replace(k, v)
        with open(dst, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
    for f in ('VOCAB', 'GARDEN'):
        fill(os.path.join(seed, f + '.md.template'), os.path.join(target, f + '.md'))
    fill(os.path.join(seed, 'journal.md.template'), os.path.join(target, 'log', 'journal.md'))
    fill(os.path.join(seed, 'pending.md.template'), os.path.join(target, 'log', 'pending.md'))

    run('git', 'init', '-q', target)
    sys.path.insert(0, os.path.join(target, 'bin'))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('install', os.path.join(target, 'bin', 'install.py'))
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        mod.install(target, quiet=True)                  # hooks + merge driver; harmless if it cannot
    except Exception:
        pass
    run('git', '-C', target, 'add', '-A')
    # THE FIRST COMMIT IS THE GARDEN'S IDENTITY (21.0, `garden_id`), so it must be one no other germination makes:
    # the same release, the same folder name and the same second would otherwise make the same commit, and two
    # gardens would be taken for one. A seed drawn at random makes it this garden's — assigned by no one.
    import uuid
    run('git', '-C', target, '-c', 'user.name=germinate', '-c', 'user.email=germinate@localhost',
        'commit', '-q', '-m', f"germinate: {garden} — the language, at std-vocab@{ver}. No beans.\n\nseed {uuid.uuid4().hex}")
    if gid:
        today = 'now'            # the entry below stamps it: one reading of the clock for the heading and the bean (23.0)
        with open(os.path.join(target, 'beans', gid + '.md'), 'w', encoding='utf-8', newline='\n') as fh:
            _root = run('git', '-C', target, 'rev-list', '--first-parent', '--max-parents=0', 'HEAD', check=False).stdout.split()
            fh.write(gardener_bean(gid, gname or gid, today, _root[-1][:12] if _root else None, ggenos, gform))
        gpath = os.path.join(target, 'GARDEN.md')
        gtext = open(gpath, encoding='utf-8').read()
        gtext = re.sub(r'(?m)^gardener:[^\n]*$', f'gardener: {gid}                      # who keeps this garden: its first bean', gtext, count=1)
        with open(gpath, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(gtext)
        import importlib.util as _iu
        _sp = _iu.spec_from_file_location('dmjournal', os.path.join(target, 'bin', 'dmjournal.py'))
        _dj = _iu.module_from_spec(_sp); _sp.loader.exec_module(_dj)
        _dj.ROOT = target; _dj.JOURNAL = os.path.join(target, 'log', 'journal.md')
        _dj.append('germinate', f'the gardener: [[{gid}]]',
                   f"- action: planted [[{gid}]], the {'person who keeps' if ggenos == 'person' else 'organisation that keeps'} this garden,"
                   f" and named them in GARDEN.md `gardener:` — a RULE-CHANGE, as every change to the manifest is.\n")
        run('git', '-C', target, 'add', '-A')
        run('git', '-C', target, '-c', 'user.name=germinate', '-c', 'user.email=germinate@localhost',
            'commit', '-q', '-m', f"germinate: {gid} keeps this garden")


def identity_set(target):
    """True when git has an identity to commit under in `target` that someone SET — in a git configuration or in the
    environment — rather than one git would guess from the machine, or refuse to guess."""
    return all(run('git', '-C', target, '-c', 'user.useConfigOnly=true', 'var', v, check=False).returncode == 0
               for v in ('GIT_AUTHOR_IDENT', 'GIT_COMMITTER_IDENT'))


def finish(target, root, ver, release, gid, ggenos, grown_in):
    """The garden's own gate, and what to do next."""
    gate = subprocess.run([sys.executable, os.path.join(target, 'bin', 'dmcheck.py')], cwd=target)
    py = 'python' if os.name == 'nt' else 'python3'
    # EVERY COMMAND PRINTED HERE RUNS AS PRINTED in a Unix shell, cmd.exe and Windows PowerShell 5.1 alike: `python`
    # on Windows, where `python3` may be the Store's alias; no `&&`, which PowerShell 5.1 cannot parse; no `<`, which
    # no PowerShell redirects — the journal's body goes in `--body`; and every path through shown(), quoted where it
    # holds a space.
    passes = ('The garden passes its own gate.' if gate.returncode == 0
              else 'The garden does NOT pass its own gate: read the errors above before anything else.')
    if gid:
        who = 'person who keeps' if ggenos == 'person' else 'organisation that keeps'
        opening = f"{passes} Its gardener, {gid}, is planted: the {who} it, named in GARDEN.md."
        forms = "the forms the gate accepts, and what to write when nobody said"
    else:
        opening = (f"{passes} Its FIRST bean is its gardener — the person or organisation who keeps it — named in "
                   f"GARDEN.md `gardener:`.")
        forms = "the forms the gate accepts, the gardener's first"
    # ONE NEXT STEP FOR EACH READER, and no reading list. The closing text named four documents to read, and a coding
    # agent driving a small open model read them — 85,000 characters and more of the law — before writing a bean, and
    # stalled; told to read one short page of forms, it read that and finished. The law is read when a question needs
    # it, and AGENTS.md says where it is. The save is ONE command, bin/dmsave.py: journal, stage and commit were three.
    print(f"""
germinated: {shown(target)}  (std-vocab@{ver}, daftar {release})

{opening}

AN AGENT reads seed/FORMS.md — {forms} — writes beans/<id>.md,
and saves it with its journal entry, in one command:
  cd {shown(target)}
  {py} bin/dmsave.py "<who>" "<what you did>" --body "- action: added [[<id>]]."
A PERSON tells their agent to read AGENTS.md in the garden. An assistant in a chat window, with no shell, cannot run
the gate: paste it seed/WELCOME.md, and what it gives back is a proposal to check and commit.""")
    # AN UNTAGGED CLONE MAKES AN UNPINNABLE GARDEN, and this is said LAST, where it is still on the screen. A copy with
    # no git history is no clone: `git -C` on it fails, so the way to a release is a clone of the repository. A garden
    # grown from inside another runs what that garden runs, and neither NOTE is its to follow: that garden is no clone
    # of the repository, and checking out a tag in it would move a garden, not a release.
    if grown_in is not None:
        print(f"""
GROWN FROM THE GARDEN {grown_in}: its language, and the release its GARDEN.md records — daftar {release}."""
              + ('' if not release.startswith('untagged') else
                 f"""
That names no release anybody else can fetch; adopt one deliberately, in this garden as in that one, with
  cd {shown(target)}
  {py} bin/dmupgrade.py <tag>"""))
    elif release == 'untagged unknown':
        try:
            from dmupgrade import UPSTREAM         # where bin/dmupgrade.py fetches a release from: one copy of the URL
        except Exception:
            UPSTREAM = 'https://github.com/0mit/daftar.git'
        print(f"""
NOTE: the language was copied without its git history (a ZIP download, a `git archive`), so the garden records
  daftar_release: "{release}"
which names no release anybody else can fetch. Fine for a look around. To pin one, clone the repository and grow
the garden from a release tag:
  git clone {UPSTREAM} daftar-release
  git -C daftar-release tag -l            # the releases it carries
  git -C daftar-release checkout <tag>    # the newest, usually
  {py} daftar-release/seed/germinate.py <a-new-directory> --gardener <id>
— or, in this garden as it stands, adopt one deliberately (bin/dmupgrade.py fetches the tag itself) with
  cd {shown(target)}
  {py} bin/dmupgrade.py <tag>""")
    elif release.startswith('untagged'):
        print(f"""
NOTE: this clone is not on a release tag, so the garden records
  daftar_release: "{release}"
which names no release anybody else can fetch. Fine for a look around. To pin one:
  git -C {shown(root)} tag -l                    # the releases this clone knows
  git -C {shown(root)} checkout <tag>            # the newest, usually
and grow again — or, in this garden as it stands, adopt one deliberately with
  cd {shown(target)}
  {py} bin/dmupgrade.py <tag>""")
    # WHO COMMITS. germinate commits as "germinate"; every later commit is yours, and git needs an identity to make one.
    # Said only where none is SET — in a configuration, or in the environment, where a harness running an agent sets
    # GIT_AUTHOR_NAME and the rest — and asked of git itself, strictly (`git var`, guessing forbidden), so every place
    # git reads an identity from is read. An agent told to set one where the harness had set it spent its turns on it.
    if not identity_set(target):
        print(f"""
BEFORE THE FIRST COMMIT: no git identity is set here, and git would refuse the commit or guess a name from the machine.
Set one for this garden:
  git -C {shown(target)} config user.name  "Your Name"
  git -C {shown(target)} config user.email "you@example.org"
An agent commits under its own name (e.g. "agent (model, session)"), so the journal's "who" and git's author agree.""")
    return gate.returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
