#!/usr/bin/env python3
"""germinate — grow a new garden from this seed.

    python3 seed/germinate.py <target-directory>        # the directory must not exist yet

A garden is a git repository that carries the LANGUAGE — the vocabulary, the parser, the gate, the tools,
the templates — and no beans. WHAT TRAVELS IS DECLARED ONCE, in seed/LANGUAGE, and bin/dmupgrade.py reads
the same file, so a new garden and an upgraded one receive exactly the same set. The garden is given its
name, its vocabulary pin and the release it runs, its first commit as `germinate`, the gate as a pre-commit
hook, and it is checked: it passes its own gate with nothing in it.

Python, not shell, because a garden is grown on Windows too. `seed/germinate.sh` remains and hands over here.
"""
import glob
import os
import re
import shutil
import subprocess
import sys


def die(msg, code=2):
    print(f"germinate: {msg}", file=sys.stderr)
    sys.exit(code)


def run(*args, cwd=None, check=True):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
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


def main(argv):
    if len(argv) != 1 or argv[0] in ('-h', '--help'):
        print(__doc__); return 0 if argv else 2
    target = argv[0]
    if os.path.exists(target):
        die(f"{target} already exists — refusing to plant over it")
    parent = os.path.dirname(os.path.abspath(target))
    if not os.path.isdir(parent):
        die(f"{parent} does not exist — create it first")
    target = os.path.abspath(target)
    seed = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(seed)
    try:
        import yaml  # noqa: F401
    except ImportError:
        die("PyYAML is required (pip install PyYAML)")
    sys.path.insert(0, os.path.join(root, 'bin'))
    import dmparse, yaml
    ver = str(yaml.safe_load(dmparse.read(os.path.join(seed, 'std-vocab.md'))[0])['version'])
    if not ver:
        die("could not read the vocabulary version", 1)
    r = run('git', '-C', root, 'describe', '--tags', '--exact-match', check=False)
    if r.returncode == 0:
        release = r.stdout.strip()
    else:
        sha = run('git', '-C', root, 'rev-parse', '--short', 'HEAD', check=False)
        release = f"untagged {sha.stdout.strip() or 'unknown'}"

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

    garden = os.path.basename(target)
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
    run('git', '-C', target, '-c', 'user.name=germinate', '-c', 'user.email=germinate@localhost',
        'commit', '-q', '-m', f"germinate: {garden} — the language, at std-vocab@{ver}. No beans.")
    gate = subprocess.run([sys.executable, os.path.join(target, 'bin', 'dmcheck.py')], cwd=target)
    py = 'python' if os.name == 'nt' else 'python3'
    print(f"""
germinated: {target}  (std-vocab@{ver}, daftar {release})

The garden is empty and it passes its own gate. To plant the first bean:
  1. write {os.path.join(target, 'beans', '<id>.md')}   (bean: <id> must equal the filename)
  2. append an entry to {os.path.join(target, 'log', 'journal.md')}  — the gate REFUSES a bean staged without one.
     Its heading is a POSITION IN TIME and the gate checks the form, so a tool reads the clock and writes it:
       {py} bin/dmjournal.py "your-name" "what you did" --body "- action: added [[<id>]]."
  3. git add -A && git commit

  {py} bin/dmrules.py   prints every rule in force, derived from the vocabulary.
  seed/README.md           a first person, a first host and a first journal entry, passing as written.
  seed/COOKBOOK.md         a domain, a service on a machine, a rented server, and adding a missing value.
  MODEL.md, CHECKLIST.md   what the rules mean, and how a write is made.

WORKING WITH AN AGENT? AGENTS.md came with the garden, and .claude/skills/daftar/ holds the same text.
An agent with a shell reads it and loads the law from THIS garden rather than guessing — which is the
point of the whole thing: one language, both parties writing in it, neither able to corrupt it quietly.
An assistant in a chat window, with no shell, cannot run the gate: paste it seed/WELCOME.md, and what
it gives you back is a proposal for you to check and commit.""")
    # AN UNTAGGED CLONE MAKES AN UNPINNABLE GARDEN, and this is said LAST, where it is still on the screen.
    if release.startswith('untagged'):
        print(f"""
NOTE: this clone is not on a release tag, so the garden records
  daftar_release: "{release}"
which names no release anybody else can fetch. Fine for a look around. To pin one:
  git -C {root} tag -l                    # the releases this clone knows
  git -C {root} checkout <tag>            # the newest, usually
and grow again — or, in this garden as it stands, adopt one deliberately with
  cd {target} && {py} bin/dmupgrade.py <tag>""")
    # WHO COMMITS. germinate commits as "germinate"; every later commit is yours, and git refuses one with no identity.
    name = run('git', '-C', target, 'config', 'user.name', check=False).stdout.strip()
    email = run('git', '-C', target, 'config', 'user.email', check=False).stdout.strip()
    if not name or not email:
        print(f"""
BEFORE YOUR FIRST COMMIT: git has no identity here, and will refuse it. Set one for this garden:
  git -C {target} config user.name  "Your Name"
  git -C {target} config user.email "you@example.org"
An agent working in the garden should commit under its own name (e.g. "agent (model, session)"), so the journal's
"who" and git's author agree.""")
    return gate.returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
